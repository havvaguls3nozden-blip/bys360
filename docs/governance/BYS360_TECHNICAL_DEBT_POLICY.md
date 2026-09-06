# BYS360 Technical Debt Policy

Canonical source: `config/quality/bys360_technical_debt_registry.json`
Validator: `python scripts/quality/bys360_technical_debt_registry_gate.py`
Tests: `tests/quality/test_bys360_technical_debt_registry_gate.py`

## Why this document exists

Before this policy, BYS360 tracked technical debt informally, across
ad-hoc notes and reports, using a working ledger
(`P0=0, P1=0, P2=17, P3=21, TOTAL=38`) that could not be traced to any
persisted, reconstructable set of individual items anywhere in this
repository or its git history. That figure is preserved, unmodified, in
the registry's `legacy_ledger` block, explicitly labeled
`LEGACY_UNMAPPED_WORKING_LEDGER` -- it is historical reference only, never
a target to fabricate items against.

This policy exists so that a new maintainer, handed only this repository,
can answer: how many debts are open, which are P0/P1/P2/P3, why, what
closes them, and how to add or close one -- without needing any unwritten
context from earlier work.

## What counts as technical debt

An item belongs in the registry if it is a **concrete, evidence-backed**
gap between the code/process as it exists today and how it should exist,
where the evidence is a specific file:line, commit, or gate-report
reference -- not a vague impression. "This module feels messy" is not a
registry item; "these two functions are defined twice, at these four line
numbers, and the second definition is a known compiler-suppressed shadow"
is.

## Status semantics

| Status | Meaning |
|---|---|
| `OPEN` | Identified, evidenced, not yet closed. |
| `BLOCKED` | Identified, but closure depends on something outside this repo's control (e.g., an external decision, an upstream fix). |
| `IN_PROGRESS` | A closure attempt is actively underway. |
| `CLOSED` | Closed, with `closure_commit` and/or `closure_reason` set, and a non-empty `evidence` list. |
| `ACCEPTED_RISK` | Identified, deliberately not closed, with a documented rationale for accepting the risk. |
| `DEFERRED` | Identified, deliberately postponed, with a documented reason and (ideally) a trigger condition for revisiting. |

An item can never be both `OPEN` and carry closure evidence
(`closure_commit`/`closure_reason`) at the same time -- the validator
rejects this as `open_falsely_claims_closure`.

## Severity definitions (calibrated to this repository's own history)

These are not generic textbook definitions. They are calibrated against
real, evidenced items already in this registry, so two reviewers reading
a new candidate item alongside this policy usually reach the same tier.

**P0 -- production is down right now, actively losing data, or actively
exploitable right now.** No item in this registry's current history
qualifies. Reserve for: confirmed active exploitation, confirmed live
data corruption in progress, or a currently-down production service. Do
not loosen this bar to make the registry look more urgent than it is --
an honestly-empty P0 tier is itself meaningful signal.

**P1 -- a proven functional break in a real workflow, OR a structural gap
that guarantees a class of future breaks even without a live incident
(yet).** Calibration anchors: TD-008 (a `NameError`-class break a real
user hit, in production, for every non-personnel role-matrix domain);
TD-032 and TD-036 (no live incident, but an unguarded migration-integrity
gap / absent rollback procedure means the *next* deploy could be
unrecoverable -- deploy-blocking / data-integrity blast radius); TD-016 /
TD-017 (0-41% test coverage on auth/RBAC/rate-limit/captcha code, and a
whole test directory silently excluded from CI -- structural gaps that
guarantee future regressions in that surface ship undetected). Rule of
thumb: if you can point to either (a) an error/wrong-output a real user
or CI run actually hit, or (b) a completely absent safety net around
auth, migrations, or rollback -- call it P1.

**P2 -- a real, currently-contained maintainability or operational gap
that could plausibly drift into a P1-class break but has not (yet).**
Calibration anchor: `TD-CAND-002` (a duplicated, independently-drifting
implementation of the same subsystem across two files -- exactly the
class of duplication that produced TD-008's P1 production bug when a
prior refactor deleted "obviously dead" code that turned out to matter).
Rule of thumb: if the item is "this will probably bite someone
eventually, and the mechanism by which it would bite someone is already
visible in this registry's own P1 history" -- P2.

**P3 -- lint/type/documentation debt confined to non-production code
paths, or single-instance markers, where the failure mode is review
friction, not wrong behavior.** Calibration anchors: `TD-041`
(documentation mojibake -- zero runtime risk once fixed); `TD-CAND-004`
and `TD-CAND-005` (Ruff/mypy findings that were entirely confined to
`tests/`/`scripts/`, zero in `app/`). Rule of thumb: if every instance of
the finding lives in `tests/`, `scripts/`, or a `.md` file, and none reach
`app/` at runtime -- P3, regardless of how large the raw count is.

**UNCLASSIFIED -- the default for anything not yet checked against the
rules above.** This is not a scoring loophole: the scoring methodology
(`docs/governance/BYS360_SCORING_METHODOLOGY_V1.md`) charges UNCLASSIFIED
items a real, non-zero penalty (5 points, between P3's 3 and P2's 8), so
leaving an item permanently unclassified is never free. Assign a real
severity as soon as the calibration work above has actually been done for
that item -- do not force a tier without a specific, stated reason.

Genuinely ambiguous calls (see `TD-034` vs `TD-036` in the registry for a
real example) should be recorded with a `severity_reasoning` field
explaining the ambiguity, rather than silently picking a side.

## Evidence requirements

Every item, `OPEN` or `CLOSED`, requires a non-empty `evidence` list:
file:line references, commit SHAs, or specific gate-report paths. A
`CLOSED` item additionally requires `closure_commit` and/or
`closure_reason` to be set. The validator enforces both mechanically
(`closed_without_evidence`, `missing_evidence` findings).

Prefer citing the closing **commit**, not merely "verified live today" --
a live-verification timestamp only proves "still true as of this
moment," not *when* or *how* it became true, or whether it is protected
from silently regressing (see `TD-CAND-004`/`TD-CAND-005` in the registry
for a worked example of exactly this distinction, discovered during this
policy's own authoring when a stale debt-inventory report was found still
claiming 41/541 open findings that had actually been closed by real
commits weeks earlier).

## Remote-proof requirements

Set `remote_verified: true` only when you have actual remote CI evidence
(a passing GitHub Actions run, or user-supplied screenshot/log evidence)
for the specific commit being cited -- not merely "the workflow file looks
correct" or "it passed locally." `remote_verified: false` does not mean
an item is invalid or unclosed; it means the closure evidence is
local/commit-based only, which the scoring methodology treats
differently (see the CI-Release category's gate list).

## How to add a debt item

1. Gather concrete evidence (file:line, commit, or gate report).
2. Decide `category` from: Code Quality, Test Assurance, Security,
   CI-Release, Operations, Documentation-Handover, Maintainability. An
   item has exactly one `category` -- no automatic secondary/global
   penalty across categories (see the scoring methodology's
   double-counting policy).
3. Mint an ID:
   - If you intend to formally track it as a numbered, promoted debt
     item: increment `next_available_td_id` and use `TD-0NN`.
   - If you are recording a candidate/newly-identified issue that has not
     yet had a human decide it deserves a formal `TD-NNN` slot: increment
     `next_available_td_cand_id` and use `TD-CAND-NNN`. This is the
     default for anything found during routine forensic/audit work.
   - **Never guess a `TD-NNN` number without checking the registry
     first.** This repository's history is a single squashed baseline
     commit (`d8b50c4`, 2026-06-13); real `TD-NNN` IDs already exist in
     commit messages and code comments for numbers as high as `TD-041`,
     several of which were only discovered by deliberately searching full
     commit *bodies*, not just subject lines. A naive "start from TD-001"
     or "fill the gaps" approach will silently collide with real history.
4. Fill every schema field (see the registry file's own items for the
   full field list); leave `severity: "UNCLASSIFIED"` unless you have
   applied the calibration rules above and can state your reasoning.
5. Run the validator (`python scripts/quality/bys360_technical_debt_registry_gate.py`)
   and fix any findings before committing.

## How to close a debt item

1. Do the actual work; get real evidence (a commit, a test, a gate
   report going green).
2. Set `status: "CLOSED"`, `closure_commit` and/or `closure_reason`,
   `updated_at`, and set `remote_verified: true` only if you actually
   have remote CI evidence for that specific change.
3. Do not delete the item or renumber it -- closed items are permanent,
   auditable history.
4. Run the validator to confirm the item passes `closed_without_evidence`
   checks.

## Promoting a `TD-CAND-NNN` item to a formal `TD-NNN`

This is a human decision, not an automated one. When promoting:

1. Increment `next_available_td_id` and assign that value.
2. Set `promoted_to: "TD-0NN"` on the `TD-CAND-NNN` record.
3. Set `promoted_from: "TD-CAND-NNN"` on the new `TD-0NN` record.
4. Keep both records in the registry -- do not delete the candidate
   record; it is part of the audit trail.

## How legacy unmapped counts are handled

**Corrected accounting model (registry_version >= 1.1.0).** An earlier
version of this registry computed an ambiguous `reconciliation_gap` as
`legacy_ledger.TOTAL - (count of ALL registry items, including CLOSED
ones)`. That formula was wrong and has been removed: it let closing an
item, or discovering-and-immediately-closing a brand-new item with no
proven relationship to the historical 38, silently shrink the reported
gap -- unrelated hygiene work could masquerade as progress on a specific
backlog it was never shown to be part of. Concretely, 8 of this
registry's 9 `CLOSED` items were independently discovered and closed
*before* this registry (or the TD-008 work session) even existed, with no
mechanism ever proposed to match them against a specific legacy-ledger
entry -- yet the old formula let their mere presence in `items[]` count
against the legacy gap.

The corrected model:

- The legacy ledger represents **current OPEN debt only** (it has no
  closed-count field in its own schema) -- it must only ever be
  reconciled against currently-**active** (unresolved) registry items,
  **never** against a count that includes `CLOSED` items.
- Every item -- open or closed -- carries a `legacy_mapping` field:
  `{"status": "CONFIRMED" | "UNCONFIRMED" | "NOT_LEGACY_MEMBER", "note": "..."}`.
  `CONFIRMED` requires affirmative, checkable evidence that this specific
  item corresponds to a specific entry in the historical ledger --
  something that does not exist anywhere in this repository today, so
  every item currently reads `UNCONFIRMED`. This is the honest default
  for anything found via forensic audit rather than matched against a
  surviving legacy document.
- `MAPPED_LEGACY_OPEN_COUNT` = count of **active** items with
  `legacy_mapping.status == "CONFIRMED"`.
- `UNMAPPED_LEGACY_OPEN_COUNT` = `legacy_ledger.TOTAL - MAPPED_LEGACY_OPEN_COUNT`
  -- the only place `legacy_ledger.TOTAL` participates in a subtraction,
  and only against a quantity that itself only ever grows through
  affirmative evidence, never through unrelated closure work.
- `REGISTRY_OPEN_UNLINKED_COUNT` = `REGISTRY_ACTIVE_COUNT - MAPPED_LEGACY_OPEN_COUNT`
  -- real, evidenced, currently-open debt that is tracked in this
  registry but is NOT a confirmed member of the legacy backlog (i.e.
  newly-discovered debt, distinct from the historical count).

**Invariant** (validator-enforced): `legacy_ledger.TOTAL ==
MAPPED_LEGACY_OPEN_COUNT + UNMAPPED_LEGACY_OPEN_COUNT`, always, with
`REGISTRY_CLOSED_COUNT` never appearing on either side. A `CLOSED` item
*may* carry `legacy_mapping.status: CONFIRMED` -- that is valuable audit
history ("this now-fixed item was later confirmed to have been part of
the legacy backlog") and is deliberately allowed, not rejected; it is
simply excluded from `MAPPED_LEGACY_OPEN_COUNT` because that count is
active-only by definition.

`reconciliation_status` stays `PARTIALLY_RECONCILED` until
`UNMAPPED_LEGACY_OPEN_COUNT` reaches exactly 0 (every one of the 38
legacy slots affirmatively confirmed against an active registry item) --
a very high bar that may never be reached, given the squashed
pre-2026-06-13 history is structurally invisible to this repository.
That is an honest, permanent state to be in, not a defect to paper over.

## Next migration step for remaining unmapped legacy debt

To make real progress on `UNMAPPED_LEGACY_OPEN_COUNT` (currently 38, with
`MAPPED_LEGACY_OPEN_COUNT` at 0), a future session would need to, for
each candidate item:
1. Establish **affirmative** evidence (not plausibility, not chronology,
   not "it's the right kind of issue") that a specific registry item
   corresponds to a specific legacy-ledger entry -- e.g. a surviving
   fragment of the original ledger document naming this exact issue. No
   such document is known to exist; if one is ever recovered, that is
   the only legitimate path to `legacy_mapping.status: CONFIRMED`.
2. Until then, forensic discoveries (of the kind that surfaced
   `TD-016`/`TD-017`/`TD-034`/`TD-036`/`TD-041` in this policy's own
   authoring pass) should be added as new registry items with
   `legacy_mapping.status: UNCONFIRMED` -- real, valuable, tracked debt,
   but explicitly NOT claimed as progress against the specific historical
   38-item backlog.
3. Apply the severity-calibration rules above and record the reasoning.
4. Assign a `TD-CAND-NNN` ID (see numbering rules above) and add it via
   the "How to add a debt item" procedure.
5. Only after a human reviews and agrees, promote to a formal `TD-NNN`.

Given the pre-2026-06-13 history is unrecoverable, it is expected and
acceptable that `UNMAPPED_LEGACY_OPEN_COUNT` may never reach exactly 0.
What matters is that every item that *is* in the registry is real, and
the gap is disclosed rather than hidden or artificially closed by
unrelated work.
