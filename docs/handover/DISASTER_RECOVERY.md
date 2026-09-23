# BYS360 Disaster Recovery

Audience: an operator dealing with a cutover that failed partway, a candidate that never
became ready, or a decision about whether recovering the previous state is actually safe.
Read this before retrying anything.

## Every phase's failure receipt names what happened and what state the system is in

Both the historical monolithic script and the new prepare/cutover/rollback scripts are built
around the same fail-closed receipt pattern: on any failure, a receipt file is written (the
historical script's `FAILURE_RECEIPT.txt`, under
`C:\bys360\deploy_logs\<run-specific-dir>\`) naming:

- **Phase** — exactly which named phase failed (e.g. `SHADOW_REHEARSAL_FAILED`,
  `LIVE_MIGRATION_FAILED`, `SERVICE_START_FAILED`, `LOCAL_HEALTH_FAILED`,
  `PUBLIC_HEALTH_FAILED`, `SMOKE_FAILED`, `POST_DEPLOY_SECURITY_FAILED`, and others — the
  full historical phase-name list is in the header comment of
  `scripts/windows/deploy_bys360_ec4e56b_production_v4.ps1`; the new split
  prepare/cutover/rollback scripts are expected to use an equivalent, verifiably
  non-overlapping set of phase names each scoped to their own script).
- **Timestamp**.
- **Reason** — a specific, human-readable description of what failed (never just an exit
  code with no context).
- **Log path** and **deploy log dir** — where to find the full, unredacted log for this run.
- An explicit statement that no further phases ran after this failure.

**Read the receipt first, always.** It tells you which of the two fundamentally different
situations you are actually in: a failure during candidate preparation (the live service was
never touched — see below) or a failure during cutover (the live service may be stopped, may
be partially replaced, or may be running a new tree against an unmigrated or
partially-migrated database, depending on exactly which of the 20 cutover steps failed —
see `CUTOVER.md` for the full step list).

## If a candidate never becomes ready

If `CANDIDATE_READY.json` was never produced (see `CANDIDATE_PREPARATION.md`), the live
service was never touched, by construction — there is nothing to recover on the live side.
The correct response is:

1. Read the preparation failure receipt to identify the phase (dependency install, shadow
   rehearsal, health boot) and reason.
2. Fix the underlying cause on the host or in the release artifacts (a missing wheel in the
   offline bundle, a migration that doesn't apply cleanly against a real copy of production
   data, an application that doesn't start under the candidate's actual configuration).
3. Re-run candidate preparation from scratch. There is no partial candidate state worth
   preserving — a fresh `C:\bys360\candidate\<SOURCE_SHA>\` directory is the expected
   starting point for a retry.

Do not attempt cutover against a candidate directory that never produced a valid, matching
`CANDIDATE_READY.json` — cutover's hard gate is expected to refuse this outright (see
`CUTOVER.md`), and there is no legitimate reason to work around that gate.

## If cutover fails partway

Consult the failure receipt's **Phase** field against the 20-step flow in `CUTOVER.md` to
determine what actually happened:

- **Failure before step 6 (stop task)**: the live service was never stopped. Nothing to
  recover — fix the cause, re-verify the candidate is still valid (its receipt may need to
  be re-checked if any time has passed), and retry cutover from the start.
- **Failure between steps 6 and 11 (stop task through re-verify identity, before live
  migration)**: the live service is stopped and the tree-swap may be partially or fully
  done, but the **database was never migrated** — this is still the trivial,
  PRE-MIGRATION rollback case (see `ROLLBACK.md`). Run rollback to restore the previous tree
  from `C:\bys360\previous\<timestamp_SHA>\` and restart the task; the database needs no
  attention.
- **Failure at step 12 (live migration) itself**: this is the highest-stakes failure mode.
  **Do not assume the database is in any particular state without checking.** A migration
  can fail partway through applying its DDL, or fail immediately before applying anything, or
  (rarely, depending on how the failure occurred) partially commit depending on transaction
  boundaries inside the specific migration script. Query the live database's actual current
  Alembic revision directly (`flask db current`, run against the real `DATABASE_URL`, with
  the real application credentials, from a working Python environment — not necessarily the
  now-possibly-broken promoted tree) before deciding anything. See "When NOT to retry" below.
- **Failure between steps 13 and 19 (verify revision through smoke/security scan, after
  live migration succeeded)**: the database **has** already been migrated. This is the
  POST-MIGRATION case — see `ROLLBACK.md`'s distinction, including the requirement to
  actually diff the previous and candidate source before deciding an app-tree-only rollback
  is safe. Do not reflexively roll back the application tree without doing that check first;
  depending on what failed (e.g., a smoke check catching a genuine incompatibility) rolling
  the code back while leaving the schema migrated could turn a caught problem into an
  uncaught one.
- **Failure at step 20 (receipt) only, everything else already passed**: the application is
  actually up and healthy; only the receipt-writing step itself failed. This is a low-risk
  bookkeeping failure — verify health manually, and write the receipt by hand or re-run just
  that step if the tooling supports it, rather than treating this as a service-level
  incident.

## Recovering the previous app tree from `previous\<timestamp_SHA>\`

Cutover step 8 moves (not deletes) the pre-cutover tree to
`C:\bys360\previous\<timestamp_SHA>\`. As long as a subsequent cutover attempt hasn't since
overwritten that specific directory, it is a complete, working copy of the previous release
— including its own `.venv`, once cutover step 10 has restored `.env`/`instance\` onto
whichever tree is currently promoted (note: those two items travel with the *promotion*, not
statically with the previous tree — see `ROLLBACK.md` for the exact swap-back mechanics).
If the `previous\` directory for the release you want to recover no longer exists (for
example, it was superseded by a later cutover), fall back to the retained release ZIP for
that source SHA under `C:\bys360\releases\` and treat it as a full candidate-preparation
input again — do not attempt to reconstruct a tree from partial fragments.

## Recovering the database from the pre-cutover backup

The `pg_dump` backup written during cutover step 4 lives under `C:\bys360\backups\` and is
never deleted by any part of this tooling, including rollback (see `ROLLBACK.md`). Restoring
it is a manual, deliberate operation:

1. Confirm which backup file corresponds to the failed cutover attempt (the receipt/log for
   that run names the exact backup path — do not guess based on file timestamps alone if
   multiple recent backups exist).
2. Restoring over a live database that has already received partial migration writes is
   itself a destructive operation against whatever state currently exists — treat it with
   the same seriousness as the original migration, not as a routine undo. Take a fresh backup
   of the *current* (possibly partially-migrated) state first, even if you intend to discard
   it, so that if the restore itself goes wrong there is still something to fall back to.
3. Restore using `pg_restore` under the same `--no-owner --no-privileges` discipline
   documented in `DATABASE_MIGRATION.md`, verifying `exit_code == 0` strictly.
4. Re-verify the restored database's Alembic revision matches what you expect before
   considering recovery complete.

## When NOT to retry

- **Do not blindly retry a cutover after a live-migration failure (step 12) without first
  determining what state the database is actually in.** A retry that assumes the previous
  pre-migration revision and re-runs the same migration against a database that already
  received some of that migration's DDL can fail in confusing new ways, or in the worst case
  succeed in a way that leaves the schema in an inconsistent state relative to what the
  migration script assumed as its starting point. Query the actual current revision first,
  always.
- **Do not retry cutover against a candidate whose `CANDIDATE_READY.json` is now stale**
  (for example, if the live database's revision has changed since the candidate was
  prepared, due to a different operation entirely) without re-running candidate preparation.
  A ready receipt describes a specific pairing of candidate + expected starting DB state; if
  that starting state has moved, the receipt's guarantees no longer hold.
- **Do not perform a post-migration application-tree rollback without the diff-and-verify
  step in `ROLLBACK.md`.** Assuming compatibility because a previous release happened to be
  compatible is exactly the kind of unverified assumption this whole document exists to warn
  against.
- **Do not run an Alembic downgrade against the live database as a recovery mechanism.**
  This deployment model deliberately never does this automatically (see `ROLLBACK.md`); if a
  human operator decides a manual downgrade is genuinely necessary after independently
  reviewing the specific migration involved, that is a distinct, deliberate action outside
  the scope of any script here — not a step in this recovery procedure.
