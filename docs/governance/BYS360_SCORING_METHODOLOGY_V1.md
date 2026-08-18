# BYS360 Scoring Methodology V1

Canonical source: `config/quality/bys360_scoring_methodology_v1.json`
Calculator: `python scripts/quality/bys360_score_reconcile_v1.py`
Tests: `tests/quality/test_bys360_score_reconcile_v1.py`

## Purpose

Before this document, BYS360 tracked two composite scores --
`LIVE_READINESS` (68) and `TRANSFERABILITY` (61) -- built from 7 category
scores, that could not be traced to any formula, weighting scheme, or
rounding rule anywhere in this repository or its git history (confirmed
by an exhaustive, independently-repeated search: zero matches for
"TRANSFERABILITY" anywhere in the repo; the category names themselves
appear nowhere as scoring labels; the specific numbers appear nowhere in
repo content). This document and its accompanying config/script define a
genuinely new, reproducible methodology from scratch.

**This is methodology version 1.0.0, effective 2026-08-18 onward. It is
not a reconstruction of whatever produced 68/61.** The legacy numbers are
preserved below as a fixed historical snapshot and nowhere else --
methodology v1's weights and formulas were derived from first principles
(what is actually measurable in this repo, and what plausibly matters for
production-readiness vs. new-maintainer-transferability), not reverse-fit
to reproduce 68 or 61. On the evidence present when this methodology was
authored, methodology v1 in fact produces different numbers from the
legacy snapshot for both composites -- that is expected, not a bug to
"fix" by adjusting weights.

## Versioning

`methodology_version` lives in `config/quality/bys360_scoring_methodology_v1.json`.
A future methodology v1.1.0/v2.0.0 should be a new, separately-versioned
config file (or an explicit version bump inside this one, with a changelog
entry below) -- never a silent edit to v1.0.0's already-published formulas.
Changing a published methodology's formula retroactively would make every
prior score report using it non-reproducible.

## Categories

Code Quality, Test Assurance, Security, CI-Release, Operations,
Documentation-Handover, Maintainability -- retained from the legacy
snapshot's category set for continuity, since no evidence argued strongly
enough for a different set to justify breaking that continuity.

## Model family: hybrid gate-score + rubric-evidence − debt-penalty

Considered and rejected two simpler alternatives during design:

- **Weighted category rubric** (many independently-weighted sub-metrics
  per category): reproducible but high-maintenance (~25 knobs across 7
  categories) and each sub-metric weight is itself a small subjective
  judgment call.
- **Base ceiling (100) minus explicit debt penalties only**: demonstrated,
  numerically, to have a structural flaw -- "no evidence of a penalty" is
  mathematically indistinguishable from "verified zero debt" in a purely
  subtractive design. On this repo's real (at-authoring-time absent)
  debt registry, this model gave Operations and Documentation-Handover
  an unearned, evidence-free 100/100, purely because nothing had been
  logged against them yet.

The adopted hybrid avoids both failure modes: 70-80% of each category's
ceiling comes from **literal, re-runnable gate commands** (not prose
descriptions -- see each category's `gates[]` list in the JSON config,
every command including the exact canonical Python interpreter path,
specifically because this environment was found, during methodology
authoring, to have an unrelated, unpinned `ruff`/`mypy` shadowing the
project's pinned toolchain on bare `PATH` lookup -- a real reproducibility
bug this methodology exists to prevent, not a hypothetical one), the
remaining 20-30% is a small, bounded rubric component, and open debt-registry
items subtract a severity-weighted, per-category-capped penalty on top.

## Per-category formula

```
gate_component  = category.gate_component_weight * 100 * (gates_passed / gates_applicable)
rubric_component = sum of this category's rubric sub-metrics (each bounded to its own share of category.rubric_component_weight * 100)
raw_before_penalty = gate_component + rubric_component
debt_penalty = min(penalty_cap_per_category, sum(severity_weight[item.severity] for item in registry.items if item.status=="OPEN" and item.category==this_category))
final_score = clamp(0, 100, raw_before_penalty - debt_penalty)
```

Severity weights: `{P0: 40, P1: 20, P2: 8, P3: 3, UNCLASSIFIED: 5}`.
`penalty_cap_per_category = 30` (a category cannot be wiped to 0 by debt
penalties alone; see "Score ceilings" below for how a fully-measured-but-
weak category is still bounded separately, by its own gate/rubric math).
UNCLASSIFIED costs 5 -- deliberately more than P3's 3 -- so leaving an
item permanently unclassified in the debt registry is never a free way to
dodge a penalty.

### Gate assignment per category (no double counting)

| Category | Gates |
|---|---|
| Code Quality | Ruff full-select, mypy full scope, Quality9 |
| Test Assurance | Coverage ratchet |
| Security | Secret-repo gate, dependency audit (pip-audit) |
| CI-Release | Ruff syntax/import sanity, PostgreSQL migration integrity gate |
| Operations | Ops audit |
| Documentation-Handover | Handover docs contract (11 required docs, character-floor enforced) |
| Maintainability | Whole-registry "no OPEN P0/P1 anywhere" boolean, plus its own rubric |

Every gate command appears in exactly one category's list. Ruff/mypy are
deliberately **not** in Security's gate list (adversarial review found
this would dilute genuine security signal, e.g. a real open CVE, behind
several unrelated green code-hygiene gates) -- they live only in Code
Quality.

## Missing-evidence policy

**UNKNOWN contributes 0 to its gate/rubric component and is never
excluded from the denominator.** Two gates are structurally impossible to
verify in an ordinary local run: the PostgreSQL migration-integrity gate
(needs a live PostgreSQL 15 service) and the dependency audit
(slow/network-dependent). These score UNKNOWN by default, contributing 0
-- the same numeric effect as a measured FAIL -- unless a fresh result is
explicitly supplied via `--evidence path/to/evidence.json` (e.g. from a
real, user-supplied remote CI proof). Every UNKNOWN is recorded distinctly
from FAIL in the calculator's trace output, and counted in a top-level
`unverified_evidence_count`; the report's `fully_verified` flag is `true`
only when that count is 0.

Rejected alternatives and why: a neutral/50-point contribution treats an
unverified claim as half-credible, which a production-readiness score
should never do. Silent exclusion from the denominator would let
unmeasurability itself inflate every other gate's share -- the single
most important thing this policy exists to prevent, since it would
otherwise reward *not* wiring up a hard-to-verify gate.

## Score ceilings

**Evidence-completeness ceiling (89):** applies to the two composites
(never to an individual category score) whenever any category has an
UNKNOWN gate/rubric signal, or the debt registry's
`reconciliation_status` is not `FULLY_RECONCILED`. This is a confidence
gate on the headline number when the underlying evidence set is
incomplete -- it does not, by itself, suppress a category that happens to
be fully and honestly measured.

**Measured (not missing) weakness is bounded separately**, by each
category's own gate+rubric math -- a category with all its gates
genuinely measured and genuinely failing scores low on its own terms,
independent of the 89 ceiling. Worked example: if Test Assurance's
coverage rubric sub-metric is `20 * min(combined_pct/50, 1)` and
`combined_pct` is the current ~28-30%, that alone caps the rubric
contribution near 11-12/20 regardless of whether every other category is
fully measured and the 89 ceiling never engages.

## Debt penalty policy

See "Per-category formula" above for the exact weights/cap. Debt only
affects the single category recorded on the item (`primary category` --
this methodology has no secondary/global penalty mechanism in v1.0.0,
per the registry's one-category-per-item design).

## Double-counting policy

Every gate command is assigned to exactly one category (see the gate
table above). Every debt-registry item has exactly one `category` field,
and its penalty applies only there. A cross-cutting improvement (e.g. the
settings_page complexity reduction, TD-008) is recorded under one primary
category (Maintainability) in the registry -- it is not manually
double-entered under Code Quality as well, even though it plausibly
touches both, because the registry schema does not currently support a
capped secondary-category contribution. This is a deliberate v1
simplification, not an oversight.

## LIVE_READINESS formula

```
weights = {Security: 0.22, Test Assurance: 0.21, CI-Release: 0.21, Operations: 0.20,
           Code Quality: 0.10, Maintainability: 0.03, Documentation-Handover: 0.03}
LIVE_READINESS_raw = sum(category_final_score * weight)
LIVE_READINESS = round_half_up(min(LIVE_READINESS_raw, ceiling_if_applicable))
```

Reasoning: ranked by "would a failure here hurt if this ran in production
today." Security, Test Assurance, and CI-Release are weighted closely
together (0.21-0.22) rather than Security dominating alone -- an earlier
draft weighted Security at 0.25 with a full 0.05-0.10 gap over the
others, but adversarial review argued Security's own sub-score already
leans on gates (secret-scan, dependency audit) that overlap in spirit
with CI-Release, and "can this ship and run right now" is arguably
CI-Release's and Test Assurance's job as much as Security's -- the
weights were narrowed accordingly. Operations sits close behind at 0.20.
Code Quality, Maintainability, and Documentation-Handover matter for
production readiness but a lint finding or a stale doc rarely alone
causes an outage -- weighted lowest.

## TRANSFERABILITY formula

```
weights = {Documentation-Handover: 0.22, Maintainability: 0.22, Test Assurance: 0.18,
           Code Quality: 0.15, CI-Release: 0.10, Operations: 0.06, Security: 0.07}
TRANSFERABILITY_raw = sum(category_final_score * weight)
TRANSFERABILITY = round_half_up(min(TRANSFERABILITY_raw, ceiling_if_applicable))
```

Reasoning: ranked by "could a new maintainer safely take over without the
original team." An earlier draft weighted Documentation-Handover alone at
0.25 with Maintainability meaningfully lower; adversarial review pointed
out that this repository's own recent TD-008 closure history (4 commits,
all substantial runtime-behavior/maintainability work) touched **zero**
documentation files, i.e. docs demonstrably go stale here even during
well-tested work -- so Documentation-Handover and Maintainability were
brought to near-parity (0.22 each) rather than letting potentially-stale
prose outweigh currently-true code structure. Test Assurance and Code
Quality follow (tests are executable documentation and a safety net for a
newcomer's first change; lint/type cleanliness reduces the risk of
copying bad patterns forward). CI-Release, Operations, and Security are
weighted lowest for this specific composite -- not because they're
unimportant, but because they are the least differentiating factor for
*onboarding* specifically (a secure, well-operated repo is not
necessarily an *easier* repo to learn).

## Rounding

Category scores: 2 decimal places (kept in the trace so nothing compounds
silently). Composite scores: **round-half-up to the nearest integer**,
applied once at the final step. Round-half-up (not banker's rounding) was
chosen because the audience is a single headline number read by humans --
it must mean the same thing every time it is recomputed, with no
floating-point tie-breaking surprise.

## Legacy-score handling

The calculator's JSON/Markdown report always includes an unmodified
`legacy_snapshot` block with the exact 68/61/70/79/64/55/65 values,
labeled explicitly as historical and methodologically unrelated. It is
never read as an input to the v1.0.0 calculation, and the report does not
claim a like-for-like trend against it -- the measurement basis, category
definitions, and debt registry are all different from whatever produced
those numbers.

## Example calculation (from methodology-authoring time, HEAD `9def579`)

With the debt registry containing 5 OPEN items (mostly UNCLASSIFIED
severity) and 9 CLOSED items, all locally-runnable gates passing (Ruff,
mypy, Quality9, coverage ratchet, secret-repo gate, ruff syntax sanity,
ops audit, handover-docs contract), and the two CI-only gates (PostgreSQL
migration integrity, dependency audit) UNKNOWN:

| Category | Final score |
|---|---|
| Code Quality | 86.0 |
| Test Assurance | 91.05 |
| Security | 53.0 |
| CI-Release | 60.0 |
| Operations | 100.0 |
| Documentation-Handover | 85.0 |
| Maintainability | 84.0 |

`LIVE_READINESS_raw ≈ 77.05` (ceiling not binding, both UNKNOWN gates'
0-contribution already reflected in Security/CI-Release above, and 77.05
is below the 89 ceiling regardless) → **LIVE_READINESS = 77**.
`TRANSFERABILITY_raw ≈ 82.18` → **TRANSFERABILITY = 82**.

Re-run `python scripts/quality/bys360_score_reconcile_v1.py` at any time
to get the current, live numbers -- the values above are a point-in-time
worked example, not a fixed constant.

## Anti-gaming notes

**Implemented in v1:** the coverage rubric uses combined (line+branch)
coverage, materially harder to inflate with tautological line-only tests
than a line-count metric alone; the handover-docs gate reuses the
pre-existing `tests/test_score100_handover_docs_contract_v1.py` character-
floor contract rather than checking mere file existence; UNCLASSIFIED
debt costs real points (5), so it is never a free way to avoid scoring
impact; every gate is a literal, versioned command string, so two
independent runs against the same commit must produce the same category
scores.

**Known v1 gaps, deferred to v2 (disclosed, not hidden):**
- Suppression-comment tracking (`# noqa`, `# type: ignore` deltas) is not
  yet a tracked sub-metric -- a finding could in principle be silenced
  rather than fixed without this methodology detecting it.
- `broad_except` counting (inside the ops-audit/Quality9 gates) is
  except-block-count based, not statement-count based -- merging many
  small `except` blocks into one large one could reduce the count without
  reducing actual defensive-coding sloppiness.
- No independent AST-based same-name-multiple-definition detector;
  duplicate-code discovery currently relies on the debt registry being
  kept manually current (see `TD-CAND-001`/`TD-CAND-002`/`TD-CAND-003`),
  not on automated re-discovery on every score run.

## Changelog

- **1.0.0** (2026-08-18): Initial canonical methodology. Legacy snapshot
  (68/61/etc.) preserved as historical reference only.
