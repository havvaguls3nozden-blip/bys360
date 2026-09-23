# BYS360 Governance Policy: Formal Historical Gap Acceptance Policy V1

```text
policy_id                = FORMAL_HISTORICAL_GAP_ACCEPTANCE_POLICY_V1
policy_status             = APPROVED
approval_mode             = HUMAN_EXPLICIT_TOKEN
approval_summary          = "HUMAN_POLICY_APPROVAL = APPROVED / APPROVED_POLICY =
                             FORMAL_HISTORICAL_GAP_ACCEPTANCE_POLICY_V1 / APPROVAL BASIS =
                             READY_FOR_EXPLICIT_HUMAN_POLICY_APPROVAL"
approver_role             = HUMAN_PROJECT_OWNER
approval_date             = 2026-08-22
ratified_by               = BYS360 Historical Gap Acceptance Policy Design Ratification Wave
                             (docs/governance basis: the ratification report's 16-section
                             specification, Section 11)
```

This record documents approval and implementation of a **mechanism**, not activation of any
specific commit's ceiling waiver. See Section 4 below for the precise distinction and current
activation state.

**Binding-model hardening note (2026-08-23):** the commit-binding design described below was
corrected before any waiver was ever activated for any commit (Section 4 confirms none has
been). The original design required the decision object's commit-binding field to equal
`scored_commit` exactly, which (a) made a decision-adding commit unable to correctly reference
its own not-yet-computed SHA, and (b) permitted genuine, unforged CI evidence for one
already-attested commit to be paired with a *different* commit's registry content under a
shared `scored_commit` claim -- nothing tied the registry dict's actual provenance to that
claim. The corrected design (documented below, as currently implemented) separates a purely
documentary `approval_baseline_commit` (never compared to the commit being scored) from a new,
actively-enforced `registry_commit_verified` check that cryptographically confirms, via
`git show <scored_commit>:<registry_path>`, that the registry content being scored genuinely
came from that commit's own tree. See Section 10 below for the full forensic basis. No
historical fact, ceiling value, or already-locked score is affected by this correction -- see
Section 4.

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
2. `validate_registry(registry).ok == True` — the registry passes its own full structural
   validation (schema, item shape, legacy-ledger invariants, AND this decision object's own
   drift/shape checks below). `validate_registry()` is a pure, I/O-free function -- it never
   accepts or needs a current-commit parameter (see the binding-hardening note above).
3. `registry_commit_verified == True` — a boolean resolved at the CLI/git boundary
   (`_registry_matches_scored_commit_tree()`), never inside `compute_report()` itself, that
   cryptographically confirms the registry CONTENT being scored genuinely came from
   `scored_commit`'s own git tree (`git show <scored_commit>:<registry_path>`, byte-compared).
   This is the actual fix for the commit-binding gap; see Section 10.
4. The decision object's `decision_status == "APPROVED"`.
5. `registry.reconciliation_status == "HISTORICAL_UNRECONSTRUCTABLE"` exactly — re-checked
   live at scoring time, never trusted from a cached or prior value.
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
own discipline); and a well-formed `approval_baseline_commit` (a 40-hex-character SHA, checked
for shape only -- purely documentary, never compared to any notion of "the current commit";
see Section 10).

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
the `FULLY_RECONCILED` path and the new waiver path now require `validate_registry(registry).ok
== True`. A registry claiming `FULLY_RECONCILED` while failing its own gate invariants (e.g. a
drifted or inconsistent `unmapped_legacy_open_count`) can no longer lift the ceiling. This is a
safety correction, not a score-relevant change for this repository today — the real registry has
never used `FULLY_RECONCILED`.

## 7. Required Test Matrix (implemented and verified; updated 2026-08-23 for the binding hardening)

`tests/quality/test_bys360_technical_debt_registry_gate.py` (14 tests as of the hardening):
waiver absent is still valid; waiver accepted with valid metadata; rejected on wrong
decision_id; rejected on reused `BYS360-GOV-LEGACY-001` id; rejected on invalid
`decision_status`; a `REVOKED` decision is inert but not itself a validation failure; rejected
when `reconciliation_status` is not `HISTORICAL_UNRECONSTRUCTABLE`; rejected on preserved-total
drift; rejected on preserved-split drift; rejected when `approval_baseline_commit` is missing
or malformed; **`approval_baseline_commit` is proven NOT compared against any current-commit
notion** (accepts an all-zero placeholder SHA, since it is purely documentary); rejected on
non-object type; the real committed registry has no waiver object and validates cleanly.

`tests/quality/test_bys360_score_reconcile_v1.py` (19 tests as of the hardening): ceiling
waived when fully eligible; registry/legacy_ledger never mutated by the mechanism;
Documentation-Handover provably unchanged between waiver-absent and waiver-active runs;
blocked when decision missing; blocked when not `APPROVED`; **blocked when
`registry_commit_verified` is False even with an otherwise fully-eligible decision** (the
central hardening property); `registry_commit_verified` proven to default to `False` (no
truthy default); blocked when evidence is incomplete; blocked when Score100 evidence is
missing or `FAIL`; blocked when active debt is present; blocked when registry structural
validation fails; blocked when `reconciliation_status` is not `HISTORICAL_UNRECONSTRUCTABLE`;
the `FULLY_RECONCILED` path blocked when structurally invalid and unaffected when genuinely
valid; a registry with the waiver field entirely absent reproduces pre-policy behavior exactly;
the real committed registry has no active waiver. Plus 6 tests against
`_registry_matches_scored_commit_tree()` using a **real, disposable git repository** (not
mocked): accepts a commit's own genuine content; **rejects the exact parent-scored-child-
registry substitution attack** (a real baseline commit and a real child commit that only adds
a waiver decision -- claiming the baseline's SHA while reading the child's registry content is
rejected, and the reverse direction too); fails closed for a non-git directory, a malformed
commit SHA, and a path missing at the given commit; and a sanity check against this
repository's own real history (`17be109`) proving the check rejects tampered content even
under the exact SHA that produced the genuine original.

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

## 9. Implementation Scope

| File | Change | Status |
|---|---|---|
| `config/quality/bys360_technical_debt_registry.json` | Untouched — no `reconciliation_ceiling_waiver_decision` added; `reconciliation_status`, `legacy_ledger`, `reconciliation_governance_decision`, all 14 items byte-identical | UNCHANGED |
| `scripts/quality/bys360_technical_debt_registry_gate.py` | 2026-08-22: new constants, optional-field validation block, `current_commit` parameter. 2026-08-23 (hardening): the `current_commit`-vs-`target_scored_commit` equality check and the `current_commit` parameter/subprocess-based `git rev-parse HEAD` resolution in `main()` **removed entirely**; replaced with a shape-only check on a renamed `approval_baseline_commit` field (well-formed 40-hex SHA, never compared to anything) | DONE |
| `scripts/quality/bys360_score_reconcile_v1.py` | 2026-08-22: `SCORE100_WORKFLOW_GATE_ID`, `_score100_evidence_verified()`, `waiver_active`/`registry_structurally_valid`. 2026-08-23 (hardening): new `_registry_matches_scored_commit_tree()` helper (real `git show <sha>:<path>` verification, resolved at the CLI boundary in `main()`, never inside `compute_report()`); `compute_report()` gains a `registry_commit_verified: bool = False` parameter, now a required term in `waiver_active`; `validate_registry()` calls no longer pass `current_commit`; report now also exposes `registry_commit_verified`; `registry_reconciliation_transparency` rubric still completely untouched | DONE |
| `tests/quality/test_bys360_technical_debt_registry_gate.py` | 14 waiver-related tests as of the hardening (Section 7) | DONE |
| `tests/quality/test_bys360_score_reconcile_v1.py` | 19 waiver/binding-related tests as of the hardening, including 6 against a real disposable git repository (Section 7) | DONE |
| `docs/governance/BYS360_GOV_HISTORICAL_GAP_ACCEPTANCE_POLICY_V1.md` | This file — updated for the hardening | DONE |

See the accompanying implementation reports (2026-08-22 and 2026-08-23) for full command output and verification.

## 10. Binding-Model Hardening Forensic Basis (2026-08-23)

A subsequent read-only forensic review, conducted in two independent passes, examined
whether the original `target_scored_commit == scored_commit` design (Section 2 as it read on
2026-08-22) was safe for a real future activation. The initial pass concluded no
defect existed, reasoning that `_score100_evidence_verified()`'s exact `commit_sha ==
scored_commit` match already prevented evidence substitution. A second, independent pass
identified a **critical gap that survives that check**: the evidence-manifest match constrains
only which commit's *evidence* may be cited -- it says nothing about which commit's *registry
content* is actually being read. Concretely: an operator could run the calculator with
`--scored-commit <BASELINE>` (a real, already exact-head-attested commit, e.g. `8529ca5`)
while `--registry` pointed at a *different* commit `E`'s registry file (one that adds a
ceiling-waiver decision). `target_scored_commit=<BASELINE>` would equal `scored_commit=
<BASELINE>` (true). Genuine, unforged Score100/Quality evidence for `<BASELINE>` would
correctly match `commit_sha == scored_commit` (also true, because that evidence really was
issued for `<BASELINE>`). Every other term (`REGISTRY_ACTIVE_COUNT==0`,
`reconciliation_status`, drift-checks) would read from `E`'s registry content and could easily
be made to pass. `waiver_active` would become `True` under a run labeled `scored_commit=
<BASELINE>`, using entirely genuine evidence -- but the registry state that actually produced
that result exists only in `E`'s tree, which was never itself CI-verified. This traces directly
to a structural fact confirmed in both `resolve_scored_commit()`'s own docstring and by reading
`compute_report()`/`validate_registry()` in full: neither function has ever verified that the
`registry: dict` argument's content actually originated from `scored_commit`'s git tree -- that
binding was, before this hardening, purely a caller-honesty convention, not a code-enforced
guarantee.

The correction implemented separates two previously-conflated concepts cleanly: (1)
`approval_baseline_commit`, purely documentary, modeled directly on
`reconciliation_governance_decision.target_baseline_commit`'s own precedent (confirmed via
`git show ac8561e:config/quality/bys360_technical_debt_registry.json` to already point at its
own parent commit, `846a9e0`, and confirmed via repo-wide grep to never be code-compared
anywhere) -- never checked against `scored_commit`, so no commit ever needs to declare its own
not-yet-computed SHA; and (2) `registry_commit_verified`, a newly-added, actively-enforced
boolean that closes the actual gap by cryptographically tying the registry CONTENT under
evaluation to `scored_commit`'s real git tree via `git show`, resolved once at the CLI/git
boundary (mirroring `resolve_scored_commit()`'s own architecture) and threaded into
`compute_report()` as an explicit, no-truthy-default parameter. A `git merge-base
--is-ancestor`-style lineage/ancestry check between the approval baseline and the current
scored commit was considered as an additional safeguard but deliberately **not implemented**
in this wave (it narrows *which* commits may even attempt eligibility, but does not by itself
close the registry-content-provenance gap that `registry_commit_verified` closes) -- left as a
disclosed, optional future hardening, not required to close the confirmed vulnerability.
