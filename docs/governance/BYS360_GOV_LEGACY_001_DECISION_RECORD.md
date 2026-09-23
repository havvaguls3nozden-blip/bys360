# BYS360 Governance Decision Record: BYS360-GOV-LEGACY-001

```text
decision_id            = BYS360-GOV-LEGACY-001
decision_status         = APPROVED
approval_mode            = HUMAN_EXPLICIT_TOKEN
approval_token          = APPROVE BYS360-GOV-LEGACY-001
approval_date            = 2026-08-21
approver_role            = HUMAN_PROJECT_OWNER
target_baseline_commit  = 846a9e08f67db6f8aa665b6355e2af4ef529440c
```

This record documents a **governance reclassification only**. It changes how the
repository *labels* a pre-existing epistemic fact; it does not create new engineering
evidence, does not alter the historical 38-item legacy reference, and does not change
the canonical composite ceiling. See `score_effect_disclosure` below for the exact,
verified score consequence: zero.

## 1. Previous / Approved State

```text
previous_state  = PARTIALLY_RECONCILED
approved_state  = HISTORICAL_UNRECONSTRUCTABLE
```

**Semantic definition of the approved state:**
> Historical debt reference exists and is preserved, but its underlying itemized source
> is no longer recoverable at a level that permits evidence-based reconciliation.

`HISTORICAL_UNRECONSTRUCTABLE != FULLY_RECONCILED` (no item-level reconciliation is
claimed to have occurred) and `HISTORICAL_UNRECONSTRUCTABLE != PARTIALLY_RECONCILED`
(no active, resolvable-in-principle reconciliation process is implied).

## 2. Historical Reference Preservation

```text
historical_legacy_total    = 38
historical_priority_split  = { P0: 0, P1: 0, P2: 17, P3: 21 }
```
These values are unchanged, unmodified, byte-for-byte identical to their state before
this decision, in `config/quality/bys360_technical_debt_registry.json`'s `legacy_ledger`
block. This decision does not recompute, reset, or reclassify them.

## 3. Provenance Classification & Forensic Basis

```text
provenance_classification  = HISTORICALLY_REFERENCED_BUT_SOURCE_UNRECOVERABLE
reconstructability_verdict = FORENSIC_LEGACY_LEDGER_UNRECONSTRUCTABLE
```

**forensic_basis:**
1. `38 / P2=17 / P3=21` appears in this repository's reachable git history exactly once — in the technical-debt registry's own creation commit (`bff39ed`, 2026-08-18), citing "prior working sessions." No earlier or independent occurrence exists.
2. No itemized 38-entry ledger has been found anywhere in this repository, in any form.
3. Full reachable git history was searched: `git log --all --oneline` (977 commits, all branches/tags); `git log --all --reverse` confirms `d8b50c4` (2026-06-13) is genuinely the earliest reachable commit — the documented squash baseline holds.
4. A pickaxe search (`git log --all -S"P2=17"` / `-S"P3=21"`) across all reachable history returned only the single self-referential hit described above.
5. `git fsck --full --no-reflogs --unreachable` found 139 dangling commits; every one is dated 2026-06-13 or later (none predate the baseline); sampled entries are routine WIP/index/stash artifacts of ordinary post-baseline work.
6. Four historical debt-tracking schemes referenced by the registry's own `legacy_ledger.note` were independently located and verified genuine, and each individually shown by direct content inspection to be structurally incapable of producing `38 / P2=17 / P3=21`:
   - A10R compat/quarantine report — quarantine/compat status counts, no P0-P3 severity tiers.
   - Phase2 P0/P1/P2-only audit tool (commit `e88a17a`, a genuine ancestor of current HEAD) — its code literally defines `priority_rank = {"P0": 0, "P1": 1, "P2": 2}`, no P3 key exists at all.
   - Architecture debt map — a route/blueprint inventory, not a severity-tiered debt ledger.
   - `STATUS.md`'s "Faz N" PASS/FAIL journal — confirmed real, contains no "38" debt-count reference.
7. Defensible item-level legacy mapping count under this registry's own evidentiary standard: **0**.
8. `UNRESOLVED_ENGINEERING_DEBT != UNRECONSTRUCTABLE_HISTORICAL_REFERENCE` — two structurally different problem classes previously routed through the identical ceiling mechanism.
9. TD-CAND-006 (the sole currently-OPEN registry item) does not control `reconciliation_status` in any code path.

```text
evidence_search_scope = Full reachable git history (all refs, pickaxe search), git fsck
  dangling-object dating, direct content inspection of all 4 claimed historical schemes,
  the one external path referenced in surviving evidence (C:\bys360\releases\, confirmed
  absent on this machine). Local filesystem search bounded/targeted, not an exhaustive
  crawl of every old BYS360 backup folder on this machine (explicitly disclosed as a
  scope limitation, not claimed as exhaustive).
```

## 4. Approved Ceiling Policy

```text
approved_ceiling_policy = 89-point composite ceiling REMAINS ACTIVE, unchanged
```
`HISTORICAL_UNRECONSTRUCTABLE` is treated identically to `PARTIALLY_RECONCILED` for
ceiling purposes: `LIVE_READINESS` and `TRANSFERABILITY` composites remain capped at 89.
This is the central anti-gaming safeguard of this decision — the label changes, the
score-relevant behavior does not.

## 5. Score Effect Disclosure

```text
Before (846a9e0, PARTIALLY_RECONCILED):
  Documentation-Handover = 85
  LIVE_RAW    = 97.4605
  LIVE_FINAL  = 89
  TRANSFER_RAW    = 93.549
  TRANSFER_FINAL  = 89

After (this decision implemented, HISTORICAL_UNRECONSTRUCTABLE, ceiling unchanged):
  Documentation-Handover = 85
  LIVE_RAW    = 97.4605
  LIVE_FINAL  = 89
  TRANSFER_RAW    = 93.549
  TRANSFER_FINAL  = 89

governance_only_final_score_delta = 0
```
Verified against the real canonical calculator, not asserted by hand (see the
implementation report accompanying this record for the exact command and output).

`SCORE CONSEQUENCE != GOVERNANCE JUSTIFICATION`. The justification for this decision is
that `PARTIALLY_RECONCILED` no longer truthfully described the repository's state — not
that it changes any score. It provably does not.

## 6. Anti-Gaming Statement

```text
This governance decision does not create new engineering evidence.
It does not erase or reduce the historical total of 38.
It does not assert that item-level reconciliation occurred.
It does not classify the system as FULLY_RECONCILED.
It does not remove the existing 89 composite ceiling.
It produces zero canonical final-score increase by itself.

SCORE_GAIN_PRIMARY_MOTIVE = NO
SCORE_CHANGE_FROM_DECISION = 0
HISTORICAL_REFERENCE_ERASED = NO
```

## 7. TD-CAND-006 Independence

```text
td_cand_006_independence:
  status = OPEN / P3
  ceiling_effect = NONE
  scope_of_this_decision = EXCLUDES TD-CAND-006 entirely
```
TD-CAND-006 is untouched by this decision and this implementation wave. Its closure
remains a fully separate, independent future engineering wave.

## 8. Governance Authority

```text
proposer                    = forensic/governance analysis author (this session)
technical_reviewer          = independent technical reviewer (role required by this
                               record's own governance model; not separately named at
                               time of approval -- see note below)
governance_approver         = HUMAN_PROJECT_OWNER (approved via explicit token, see above)
implementer                 = this controlled implementation wave
post_implementation_auditor = independent re-run of the required test matrix (Section 9),
                               to be performed after this wave
```
`AI_ASSISTANT_CANNOT_SELF_APPROVE_GOVERNANCE_CHANGE` — approval for this record was
supplied by the human project owner via the explicit token above, not generated or
self-certified by the assistant that proposed it.

**Note on technical_reviewer:** no separately-named independent technical reviewer signed
off between proposal and approval in this session; the approval token was applied
directly to the proposed record. This is disclosed here rather than silently omitted.

## 9. Required Test Matrix (implemented and verified this wave — see implementation report)

1. Historical total remains 38.
2. Priority split remains P0=0/P1=0/P2=17/P3=21.
3. Validator accepts `HISTORICAL_UNRECONSTRUCTABLE` with valid decision metadata.
4. Decision ID matches `BYS360-GOV-LEGACY-001`.
5. Approved state still applies the 89 ceiling.
6. Documentation-Handover remains 85 (not 100).
7. LIVE raw remains 97.4605.
8. LIVE final remains 89.
9. TRANSFER raw remains 93.549.
10. TRANSFER final remains 89.
11. Evidence completeness behavior is unchanged.
12. TD-CAND-006 remains OPEN/P3, Maintainability remains 93.
13. Unknown reconciliation state fails.
14. Bare manual `HISTORICAL_UNRECONSTRUCTABLE` without valid decision record fails.
15. Wrong decision ID fails.
16. Unapproved decision status fails.
17. Changing historical total while using this governance decision fails.
18. Changing P2/P3 split fails.
19. `HISTORICAL_UNRECONSTRUCTABLE` cannot behave as `FULLY_RECONCILED`.
20. Attempting to remove the ceiling for the new state fails canonical score assertions.
21. Documentation-Handover cannot rise to 100 solely through this state change.
22. Fabricated `legacy_mapping.status = CONFIRMED` continues to be rejected.
23. This governance change does not affect TD-CAND-006 scoring.

## 10. Future Evidence Policy / Rollback Condition

```text
future_evidence_policy:
If, in the future, any of the following are found -- the original itemized 38-item
ledger, a verified institutional archive, an identifiable subset of the ledger, or
affirmative item-level legacy-mapping evidence for any specific item -- then
BYS360-GOV-LEGACY-001's classification MUST be reopened for review.

rollback_condition:
This decision record is never deleted or overwritten. A new decision record is created
that explicitly states "SUPERSEDES BYS360-GOV-LEGACY-001" and documents the newly-found
evidence. reconciliation_status is then updated to reflect the new evidence honestly --
reverting toward PARTIALLY_RECONCILED with real mappings, or progressing toward genuine
FULLY_RECONCILED, as the new evidence actually supports -- never assumed in advance.
```

## 11. Implementation Scope (this wave)

| File | Change | Status |
|---|---|---|
| `config/quality/bys360_technical_debt_registry.json` | `reconciliation_status` → `HISTORICAL_UNRECONSTRUCTABLE`; added `reconciliation_governance_decision` metadata block; appended (not replaced) `reconciliation_note`; `legacy_ledger` byte-identical | DONE |
| `scripts/quality/bys360_technical_debt_registry_gate.py` | Extended valid-enum set; added `HISTORICAL_UNRECONSTRUCTABLE` invariant requiring matching, approved, drift-checked decision metadata; `FULLY_RECONCILED` invariant unchanged | DONE |
| `config/quality/bys360_scoring_methodology_v1.json` | Not touched — the Documentation-Handover rubric's *behavior* was extended in the calculator, not the methodology config itself (see next row) | UNCHANGED |
| `scripts/quality/bys360_score_reconcile_v1.py` | Extended `registry_reconciliation_transparency` rubric to award the same 0.5-weight credit to a documented `HISTORICAL_UNRECONSTRUCTABLE` as to a documented `PARTIALLY_RECONCILED`; ceiling logic (`reconciled = ... == "FULLY_RECONCILED"`) intentionally left untouched — it already correctly keeps the ceiling active for the new state | DONE |
| `tests/quality/test_bys360_technical_debt_registry_gate.py` | Added positive + negative tests for the new state | DONE |
| `tests/quality/test_bys360_score_reconcile_v1.py` | Added tests confirming Documentation-Handover/LIVE/TRANSFER behavior for the new state, and confirming ceiling remains active | DONE |
| `docs/governance/BYS360_GOV_LEGACY_001_DECISION_RECORD.md` | This file — new | DONE |

See the accompanying implementation report for full command output and verification.
