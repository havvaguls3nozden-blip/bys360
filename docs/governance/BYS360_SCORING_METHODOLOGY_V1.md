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
descriptions -- see each category's `gates[]` list in the JSON config),
declared as portable `{kind, module|script, args}` structures rather than
a hardcoded interpreter path, with the interpreter resolved at run time
(see "Portability and interpreter resolution" below), and version-checked
where the pin matters -- specifically because this environment was found,
during methodology authoring, to have an unrelated, unpinned `ruff`/`mypy`
shadowing the project's pinned toolchain on bare `PATH` lookup (and,
separately, the project's own canonical shared venv was found to have an
*off-pin* Ruff installed -- 0.15.21 vs. the documented 0.16.0 pin) -- real
reproducibility bugs this methodology exists to prevent, not hypothetical
ones), the
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

**`VERSION_MISMATCH` is a fourth gate status, treated identically to
UNKNOWN for scoring** (0 contribution, counted in `unverified_evidence_count`),
distinct from both PASS and FAIL. A gate with a declared `expected_version`
(currently `ruff`==0.16.0 and `mypy`==2.3.0, matching `requirements-dev.txt`)
runs a `<tool> --version` pre-flight check before the real gate command; if
the installed version doesn't match, the gate is reported `VERSION_MISMATCH`
rather than trusting whatever the wrong-version tool reported. This is not
a hypothetical safeguard: it was found, during this methodology's own
correction, that the project's canonical shared venv (`C:\bys360\project\.venv`)
had Ruff 0.15.21 installed, off-pin from the documented 0.16.0 -- a prior
version of this calculator was silently scoring that gate's result as PASS
with no indication the tool that produced it was off-pin. Scoring a
version-mismatched result as PASS-with-a-warning was considered and
rejected: a result from the wrong tool version is not verified evidence of
the *intended* gate, so crediting it at all -- even with an asterisk --
would be the exact "treat unverified evidence as credible" mistake this
whole missing-evidence policy exists to forbid, just applied to a
different cause (wrong version instead of unmeasurable).

## Portability and interpreter resolution

Gate commands are declared in the methodology config as structured
`{"kind": "python_module", "module": "...", "args": [...]}` or
`{"kind": "python_script", "script": "...", "args": [...]}` entries, never
as a hardcoded shell-string command containing an absolute interpreter
path. The calculator builds an explicit argument list (`[python, "-m",
module, *args]` or `[python, script, *args]`) and executes it with
`shell=False` -- no shell-quoting fragility, no reliance on `$PATH`/`%PATH%`
inside a spawned shell.

The interpreter itself is resolved once per run, in this order:
1. `--python <path>` CLI flag (explicit; fails closed if the path doesn't exist).
2. `BYS360_QUALITY_PYTHON` environment variable (same fail-closed behavior).
3. `sys.executable` -- the interpreter currently running the calculator itself (default).

The resolved interpreter's path and source (`explicit` / `env` /
`default-sys.executable`) are always included in the report's top-level
`interpreter` field, so a reader never has to guess which Python actually
produced a given score. Defaulting to `sys.executable` makes the
calculator runnable anywhere out of the box (no hardcoded machine-specific
path required); pointing `--python`/`BYS360_QUALITY_PYTHON` at the
project's canonical pinned venv (`AGENTS.md`'s documented convention) is
one flag away when guaranteed-pinned execution is required. The
`expected_version` check above is what actually enforces the pin is
honored, regardless of which interpreter path was used to get there --
interpreter identity alone (i.e., "I ran the venv's own `python.exe`")
does not, by itself, guarantee that venv's installed tool versions still
match the repository's pins; venvs can and do drift out of pin silently
over time, which is exactly what was found for Ruff during this
correction.

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

## Example calculation (governance-corrective wave, post-`bff39ed`)

With the debt registry containing 5 OPEN items (mostly UNCLASSIFIED
severity) and 9 CLOSED items, most locally-runnable gates passing (mypy,
Quality9, coverage ratchet, secret-repo gate, ops audit, handover-docs
contract), the two CI-only gates (PostgreSQL migration integrity,
dependency audit) UNKNOWN, and -- newly detected by the
`expected_version` pre-flight check -- both Ruff-based gates
(`ruff_full_select`, `ruff_syntax_import_sanity`) reported `VERSION_MISMATCH`
because the default-resolved interpreter's installed Ruff is `0.15.21`
against a pinned `0.16.0`:

| Category | Final score |
|---|---|
| Code Quality | 59.33 |
| Test Assurance | 91.05 |
| Security | 53.0 |
| CI-Release | 20.0 |
| Operations | 100.0 |
| Documentation-Handover | 85.0 |
| Maintainability | 84.0 |

`LIVE_READINESS` weighted contributions: Security 53.0×0.22=11.66,
Test Assurance 91.05×0.21=19.1205, CI-Release 20.0×0.21=4.2,
Operations 100.0×0.20=20.0, Code Quality 59.33×0.10=5.933,
Maintainability 84.0×0.03=2.52, Documentation-Handover 85.0×0.03=2.55.
Sum → `LIVE_READINESS_raw = 65.9835`. The evidence-completeness ceiling
(89) applies (`unverified_evidence_count = 4`: two VERSION_MISMATCH, two
UNKNOWN) but is not binding since 65.9835 < 89 → **LIVE_READINESS = 66**.

`TRANSFERABILITY` weighted contributions: Documentation-Handover
85.0×0.22=18.7, Maintainability 84.0×0.22=18.48, Test Assurance
91.05×0.18=16.389, Code Quality 59.33×0.15=8.8995, CI-Release
20.0×0.10=2.0, Operations 100.0×0.06=6.0, Security 53.0×0.07=3.71. Sum →
`TRANSFERABILITY_raw = 74.1785` → **TRANSFERABILITY = 74**.

These are lower than an earlier point-in-time example (`LIVE_READINESS =
77`, `TRANSFERABILITY = 82`, recorded when this document was first
authored) purely because the version-mismatch check above did not exist
yet at that time and both Ruff gates were being scored as PASS against an
unverified tool version. No methodology weight, ceiling, or penalty value
changed between the two examples -- the entire delta is attributable to
scoring the same underlying evidence more correctly (see "Portability and
interpreter resolution" above).

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
impact; every gate is a structured, argument-list command
(`{kind, module|script, args}`, executed with `shell=False`), so two
independent runs against the same commit and the same pinned tool
versions must produce the same category scores; gates with an
`expected_version` are pre-flight version-checked and scored
`VERSION_MISMATCH` (not PASS) when the installed tool is off-pin, closing
the gap where simply having *a* copy of a tool on `PATH` -- any version --
could previously earn full credit.

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
