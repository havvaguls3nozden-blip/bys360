# BYS360 Governance Policy: Formal Historical Gap Acceptance Policy V1

```text
policy_id                = FORMAL_HISTORICAL_GAP_ACCEPTANCE_POLICY_V1
policy_status             = APPROVED
approval_mode             = HUMAN_EXPLICIT_TOKEN
approval_summary          = "HUMAN_POLICY_APPROVAL = APPROVED / APPROVED_POLICY =
                             FORMAL_HISTORICAL_GAP_ACCEPTANCE_POLICY_V1 / APPROVAL BASIS =
                             READY_FOR_EXPLICIT_HUMAN_POLICY_APPROVAL", supplied in chat
approver_role             = HUMAN_PROJECT_OWNER
approval_date             = 2026-08-22
ratified_by               = BYS360 Historical Gap Acceptance Policy Design Ratification Wave
                             (docs/governance basis: the ratification report's 16-section
                             specification, Section 11)
```

This record documents approval and implementation of a **mechanism**, not activation of any
specific commit's ceiling waiver. See Section 4 below for the precise distinction and current
activation state.

## 1. What This Policy Is

`reconciliation_status` describes a historical FACT: whether the legacy-38 ledger has been
item-by-item reconciled. It remains, and this policy can never change it to, anything other
than exactly what independent forensic evidence supports. As of this policy's approval it is
`HISTORICAL_UNRECONSTRUCTABLE`, set under `BYS360-GOV-LEGACY-001`, unaltered by this policy.

This policy introduces a second, orthogonal, optional field —
`reconciliation_ceiling_waiver_decision` — that records a separate GOVERNANCE TREATMENT
decision: given that historical fact, has an authorized decision been made that the
composite-score ceiling no longer needs to apply to a specific, fully-verified commit. The
second field never reads for write, sets, or aliases the first. `reconciliation_status` is
never rewritten to `FULLY_RECONCILED` by this mechanism, under any circumstance.

## 2. Eligibility (all mandatory, enforced by code, not merely documented)

A `reconciliation_ceiling_waiver_decision` object can only waive the ceiling for a specific
commit when ALL of the following hold simultaneously (`scripts/quality/bys360_score_reconcile_v1.py`,
`compute_report()`, `waiver_active` computation):

1. `fully_verified == True` — zero UNKNOWN evidence signals across every category.
2. `validate_registry(registry, current_commit=scored_commit).ok == True` — the registry
   passes its own full structural validation (schema, item shape, legacy-ledger invariants,
   AND this decision object's own drift/commit-binding checks below).
3. The decision object's `decision_status == "APPROVED"`.
4. `registry.reconciliation_status == "HISTORICAL_UNRECONSTRUCTABLE"` exactly — re-checked
   live at scoring time, never trusted from a cached or prior value.
5. The decision object's `target_scored_commit` equals the exact commit being scored — a
   waiver approved for one commit never silently carries forward to a later, unreviewed one.
6. `REGISTRY_ACTIVE_COUNT == 0` — zero currently-open technical debt of any severity. Real
   open risk must always be closed the honest way, never hidden behind this mechanism.
7. Independently-verified, commit-bound, `REMOTE_CI_VERIFIED` PASS evidence for the Score100
   CI workflow (`.github/workflows/bys360-score100-quality-gate-v1.yml`) exists in the
   evidence manifest under gate id `score100_quality_gate_v1_workflow` — never inferred from
   Quality CI passing (`_score100_evidence_verified()`).

The decision object itself (validated in `scripts/quality/bys360_technical_debt_registry_gate.py`)
additionally requires, whenever `decision_status == "APPROVED"`: a distinct `decision_id` that
is never `BYS360-GOV-LEGACY-001` (that decision's own text affirmatively preserves the
ceiling and cannot authorize lifting it); `preserved_legacy_total`/`preserved_legacy_priority_split`
byte-identical to the live `legacy_ledger` (drift-checked, exactly mirroring GOV-LEGACY-001's
own discipline); and `target_scored_commit` verified against the real current commit (resolved
via `git rev-parse HEAD` in the registry gate's own `main()`, or passed explicitly by a caller
such as the calculator) — never assumed absent verification.

Absence of the `reconciliation_ceiling_waiver_decision` field entirely (the default, and the
current real state of the committed registry) is unconditionally safe: every check above is
skipped, `waiver_active` is `False`, and behavior is byte-for-byte identical to before this
policy existed.

## 3. What Never Changes

```text
reconciliation_status can become FULLY_RECONCILED under this mechanism        = NEVER
legacy_total / legacy_ledger priority split altered by this mechanism         = NEVER
registry_reconciliation_transparency rubric (Documentation-Handover) altered
  by waiver_active                                                            = NEVER
```

`registry_reconciliation_transparency` (`scripts/quality/bys360_score_reconcile_v1.py`,
~lines 614-634) continues to key exclusively off `reconciliation_status`/`reconciliation_note`
— completely untouched by this wave. An active waiver changes only whether the ceiling clamp
applies to the two composite scores; it does not and cannot manufacture the appearance that
missing historical documentation now exists. Verified by
`test_ceiling_waiver_active_does_not_change_documentation_handover` (see Section 7).

## 4. Current Activation State: NONE

```text
active_waiver_for_any_commit = NO
reconciliation_ceiling_waiver_decision present in the committed registry = NO
```

This wave implements the mechanism only. It does **not** add a live, `APPROVED`
`reconciliation_ceiling_waiver_decision` object to the committed registry, and therefore does
**not** waive the ceiling for commit `17be109d66dfb5f91554b28e7573f01c1572c73b` or any other
commit today. The reason is Eligibility Gate 7: this project does not yet possess real,
commit-bound, `REMOTE_CI_VERIFIED` Score100 evidence for any specific commit (the existing
frozen evidence manifest for `17be109` covers Quality CI gates only — ruff, mypy, quality9,
coverage, postgres-migration-integrity, dependency-audit, ops-audit, secret-repo-gate — never
Score100, which runs as a fully separate CI workflow). Fabricating that evidence, or approving
a decision object without it, would violate this session's evidence-integrity discipline and
this policy's own Gate 7. Activation for a specific commit is deferred to a future, separately
controlled wave (Section 8) that first gathers real Score100 CI proof, then authors its own
decision record (e.g. `BYS360-GOV-CEILING-WAIVER-001`) bound to that exact evidence.

## 5. Anti-Gaming Statement

```text
This policy does not erase or reduce the historical total of 38.
It does not assert that item-level reconciliation occurred.
It does not classify the system as FULLY_RECONCILED.
It does not raise Documentation-Handover.
It does not change the ceiling value (89) in the methodology config.
It does not activate any waiver for any commit as part of this wave.
It requires a distinct, non-reusable decision_id per activation (never BYS360-GOV-LEGACY-001).
It requires independently-verified, commit-bound Score100 evidence -- never inferred, never assumed.
It fails closed: every term in waiver_active must independently and affirmatively hold; no field
  is ever read with a truthy default.

SCORE_GAIN_FROM_THIS_WAVE_ALONE = 0 (no active waiver exists yet)
HISTORICAL_REFERENCE_ERASED = NO
```

## 6. Safety Correction Applied Symmetrically (not scoped only to the new mechanism)

The pre-existing `FULLY_RECONCILED` ceiling-removal path was, before this wave, a bare string
comparison (`registry.get("reconciliation_status") == "FULLY_RECONCILED"`) with no registry
structural validation at the calculator level at all. This wave fixes that generally: **both**
the `FULLY_RECONCILED` path and the new waiver path now require
`validate_registry(registry, current_commit=scored_commit).ok == True`. A registry claiming
`FULLY_RECONCILED` while failing its own gate invariants (e.g. a drifted or inconsistent
`unmapped_legacy_open_count`) can no longer lift the ceiling. This is a safety correction, not
a score-relevant change for this repository today — the real registry has never used
`FULLY_RECONCILED`.

## 7. Required Test Matrix (implemented and verified this wave)

`tests/quality/test_bys360_technical_debt_registry_gate.py` (13 new tests): waiver absent is
still valid; waiver accepted with valid metadata and matching commit; rejected on wrong
decision_id; rejected on reused `BYS360-GOV-LEGACY-001` id; rejected on invalid
`decision_status`; a `REVOKED` decision is inert but not itself a validation failure; rejected
when `reconciliation_status` is not `HISTORICAL_UNRECONSTRUCTABLE`; rejected on preserved-total
drift; rejected on preserved-split drift; rejected on commit mismatch; rejected when commit is
unverified (`current_commit=None`); rejected on non-object type; the real committed registry
has no waiver object and validates cleanly.

`tests/quality/test_bys360_score_reconcile_v1.py` (16 new tests): ceiling waived when fully
eligible; registry/legacy_ledger never mutated by the mechanism; Documentation-Handover
provably unchanged between waiver-absent and waiver-active runs of the same registry; blocked
when decision missing; blocked when not `APPROVED`; blocked when bound to the wrong commit;
blocked when evidence is incomplete (`fully_verified=False`); blocked when Score100 evidence is
missing entirely; blocked when Score100 evidence is `FAIL`; blocked when active debt is
present; blocked when registry structural validation fails (e.g. drifted total); blocked when
`reconciliation_status` is not `HISTORICAL_UNRECONSTRUCTABLE`; the `FULLY_RECONCILED` path is
now also blocked when structurally invalid; the `FULLY_RECONCILED` path is unaffected when
genuinely valid (regression guard on the pre-existing behavior); a registry with the waiver
field entirely absent reproduces pre-policy behavior exactly; the real committed registry has
no active waiver and the ceiling still applies.

## 8. Next Controlled Wave (not authorized by this one)

Gather real, commit-bound, `REMOTE_CI_VERIFIED` Score100 CI evidence (exact-head dispatch of
`.github/workflows/bys360-score100-quality-gate-v1.yml`, verified via genuine, personally
inspected screenshots/artifacts per this project's evidence-integrity discipline — never
asserted or fabricated) for a specific, currently-canonical commit, combine it with equally
fresh Quality CI evidence, author a new, separately-approved decision record (e.g.
`BYS360-GOV-CEILING-WAIVER-001`) bound to that exact commit and evidence, add the live
`reconciliation_ceiling_waiver_decision` object to the registry with `decision_status="APPROVED"`,
run the real calculator, and lock the resulting canonical score. That wave requires its own
explicit human approval token; this document does not pre-authorize it.

## 9. Implementation Scope (this wave)

| File | Change | Status |
|---|---|---|
| `config/quality/bys360_technical_debt_registry.json` | Untouched — no `reconciliation_ceiling_waiver_decision` added; `reconciliation_status`, `legacy_ledger`, `reconciliation_governance_decision`, all 14 items byte-identical | UNCHANGED |
| `scripts/quality/bys360_technical_debt_registry_gate.py` | New constants `GOV_CEILING_WAIVER_001_DECISION_ID`, `VALID_CEILING_WAIVER_DECISION_STATUSES`; new optional-field validation block; `validate_registry()` gains keyword-only `current_commit` parameter (backward compatible, defaults to `None`); `main()` resolves it via `git rev-parse HEAD` | DONE |
| `scripts/quality/bys360_score_reconcile_v1.py` | New `SCORE100_WORKFLOW_GATE_ID` constant and `_score100_evidence_verified()` helper; imports `validate_registry` (dual-mode package/sibling import); `compute_report()`'s ceiling section extended with `registry_structurally_valid`/`waiver_active`; `reconciled` (FULLY_RECONCILED path) now also requires `registry_structurally_valid`; `registry_reconciliation_transparency` rubric completely untouched; report now exposes `registry_structurally_valid`, `registry_validation_findings`, `reconciliation_ceiling_waiver_active` | DONE |
| `tests/quality/test_bys360_technical_debt_registry_gate.py` | 13 new tests (Section 7) | DONE |
| `tests/quality/test_bys360_score_reconcile_v1.py` | 16 new tests (Section 7) | DONE |
| `docs/governance/BYS360_GOV_HISTORICAL_GAP_ACCEPTANCE_POLICY_V1.md` | This file — new | DONE |

See the accompanying implementation report for full command output and verification.
