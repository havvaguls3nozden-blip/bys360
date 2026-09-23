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

## Canonical evidence vs. local diagnostics

Portability and version-checking (above) solve "did this machine run the
right tool?" They do not solve a related but different problem: **the same
repository commit, scored on two different developer machines with two
different local toolchain states, could previously produce two different
LIVE_READINESS/TRANSFERABILITY numbers** -- e.g. a commit whose GitHub
Actions CI genuinely passed every gate could still score lower on a
developer's laptop purely because that laptop's shared venv has an
off-pin Ruff, even though nothing about the *commit* changed.

This methodology therefore distinguishes two concepts, computed
separately and never silently merged:

- **CANONICAL_PROJECT_EVIDENCE** answers *"what is the verified
  quality/readiness state of this exact repository commit?"* This is what
  LIVE_READINESS and TRANSFERABILITY are computed from.
- **LOCAL_ENVIRONMENT_DIAGNOSTICS** answers *"can THIS machine reproduce
  that state?"* This is informative only -- it helps a developer fix their
  own toolchain, but it is never itself the official project score, and a
  bad local diagnostic (wrong tool version, tool not installed) must never
  lower CANONICAL_PROJECT_EVIDENCE when valid commit-bound proof exists
  that the gate actually passed on that exact commit.

The calculator's report always contains both, clearly labeled:
`LIVE_READINESS`/`TRANSFERABILITY` (canonical; each carries
`"label": "CANONICAL_PROJECT_SCORE"`), `CANONICAL_PROJECT_EVIDENCE` (per
gate: canonical status, source, commit SHA, provenance, precedence
reason), `LOCAL_ENVIRONMENT_DIAGNOSTICS` (per gate: tool, expected vs.
actual version, local status, interpreter used), and
`LOCAL_ENVIRONMENT_SCORE_NON_CANONICAL` (what the composites would be
using *only* this machine's raw local results, ignoring the manifest
entirely -- explicitly labeled non-canonical, shown only as a diagnostic
delta).

## Evidence precedence

For every gate, `resolve_evidence()` in
`scripts/quality/bys360_score_reconcile_v1.py` decides canonical status in
this order:

1. **Commit-bound `REMOTE_CI_VERIFIED` evidence** (see "Commit binding"
   below) for the *exact* commit being scored wins unconditionally --
   including over a disagreeing local result. A local `VERSION_MISMATCH`
   never invalidates valid matching remote evidence, and this is
   unconditional in the other direction too: **a matching canonical remote
   FAIL is never overridden by a local PASS** ("remote failure
   precedence" -- see below). Remote evidence for a gate that this machine
   cannot even execute locally (e.g. the PostgreSQL migration-integrity
   gate, which needs a live PostgreSQL 15 service) is exactly how that
   gate can still contribute real, non-`UNKNOWN` canonical credit on a
   laptop with no PostgreSQL installed at all.
2. **`LOCAL_VERIFIED` evidence.** When no matching-commit remote evidence
   exists for a gate, a deterministically-correct local execution (right
   interpreter, and the correct pinned tool version if the gate declares
   one) may itself serve as canonical evidence. This is what makes an
   ordinary local run with no manifest at all still fully functional --
   it reproduces exactly the pre-this-wave scoring behavior when the
   manifest has nothing to say.
3. **`UNKNOWN`.** Neither of the above applies. No unsupported points are
   ever awarded -- unchanged from the pre-existing missing-evidence
   policy above, just now reached through an explicit precedence chain
   instead of implicitly.

Local-only diagnostic statuses (`VERSION_MISMATCH`, `LOCAL_TOOL_MISSING`,
`LOCAL_EXECUTION_FAILURE`, and the pre-existing structurally-unverifiable
`UNKNOWN`) are never, by themselves, eligible for tier 2 -- only a clean
local `PASS` or `FAIL` (i.e. the gate genuinely ran, with the right tool
version) can serve as canonical in the absence of remote evidence.
`LOCAL_TOOL_MISSING` (the subprocess could not even launch -- e.g. the
tool is not installed) and `LOCAL_EXECUTION_FAILURE` (e.g. a timeout) are
new, more precise diagnostics added by this wave; previously both cases
were folded indistinguishably into a plain gate `FAIL`, which risked
looking like a genuine quality-check failure rather than an environment
problem.

## Commit binding

A remote evidence entry's `commit_sha` must exactly match the commit
currently being scored (`scored_commit`, resolved via `--scored-commit` >
`git rev-parse HEAD` in `--root` > `UNKNOWN_COMMIT` if git is unavailable)
before it is granted canonical credit. Evidence recorded for a *different*
commit is never reused -- it is rejected with precedence reason
`STALE_COMMIT_EVIDENCE_REJECTED_LOCAL_FALLBACK` (if a valid local result
is available to fall back to) or `STALE_COMMIT_EVIDENCE_REJECTED_NO_LOCAL_FALLBACK`
(if not). Branch name is deliberately not part of this check -- commit SHA
is authoritative; a branch rename after the fact must not invalidate
evidence that is still correct for that commit's content. Freshness in v1
is exact-SHA-match only, with no time-based expiry: commit-bound evidence
is a historical fact about that commit and does not go stale with the
passage of time, only by no longer matching the commit being scored.

Multiple manifest entries for the same gate at the same commit that
*disagree* on status is an `EVIDENCE_CONFLICT` -- resolved to canonical
`UNKNOWN`, never an arbitrary pick between the two. This is checked both
by `validate_evidence_manifest()` (fails the whole run fast, before any
scoring happens, if the manifest itself is internally inconsistent) and
defensively again inside `resolve_evidence()` at scoring time.

## Remote failure precedence

Deliberately restated as its own rule because it is the one direction
this wave's design is easiest to get backwards: if commit-bound remote
evidence says a gate **FAILED**, that is canonical, full stop -- a local
`PASS` on the same commit does not override it, does not average with it,
and does not get separately reported as if it were equally credible. The
local PASS is still visible in `LOCAL_ENVIRONMENT_DIAGNOSTICS` (so the
discrepancy itself is never hidden -- it is worth investigating why local
and remote disagree), but `CANONICAL_PROJECT_EVIDENCE` and the composites
it feeds only ever reflect the remote FAIL.

## Self-attestation and the bootstrap problem

An earlier version of this methodology stored actual, live remote CI
evidence directly in a version-controlled repository file
(`config/quality/bys360_canonical_evidence.json`, committed with real
entries for a specific commit). This has a fatal defect for scoring the
*current* commit specifically:

1. Commit `A` is pushed; remote CI produces evidence for `A`.
2. Recording that evidence means editing the committed manifest file --
   which creates a new commit, `B`.
3. `HEAD` is now `B`. The manifest's evidence is still for `A`.
4. `A != B`, so by the strict commit-binding rule (below), that evidence
   is correctly rejected as `STALE_COMMIT_EVIDENCE` when scoring `B`.

A version-controlled file describing commit `A` can therefore **never**
itself describe the commit that contains the file's own addition or edit
-- there is no version of the file, committed at any point, that can
correctly claim "this is the verified state of the commit I am part of."
This was confirmed as a real, not speculative, defect in this repository's
own history: the manifest committed in `4bf249f` held evidence for
`9def579` (three commits earlier), and `4bf249f` itself had, and could
have, no matching evidence of its own -- adding some would only have
produced a `5th` commit with the same unsolvable problem one commit later.

**The fix separates two things that were previously conflated in one
file:** the evidence *schema/policy/resolver/validator* (which legitimately
belongs in version control, since it doesn't describe any one commit) from
the actual *evidence instances* for a specific commit (which must not).
Concretely:

- `config/quality/bys360_canonical_evidence.example.json` remains
  committed, but is explicitly marked `"sample_type":
  "HISTORICAL_SAMPLE_NON_RUNTIME"` and is **never auto-loaded** by the
  calculator under any default configuration -- it exists only as a
  schema-valid worked example and an honestly-labeled historical record.
- Actual current-commit remote evidence is supplied **at runtime**, via
  `--evidence-file <path>` pointing at a file that lives outside the
  commit being scored (a CI artifact, a locally-saved copy of CI output,
  anything not tracked by this repository). Recording it never requires,
  and must never require, a new source commit.

## Recording remote evidence

Actual remote evidence is external and runtime-supplied, not committed.
The operational flow after a push:

1. Push commit `ABC`.
2. Wait for remote CI to run against `ABC`.
3. Collect the exact remote gate results (job/step names and pass/fail
   status) -- manually, in this wave; no GitHub API call is made by this
   tooling (see "No automated ingestion" below).
4. Write an evidence JSON file tied to `ABC` (see
   `config/quality/bys360_canonical_evidence.example.json` for the exact
   shape) -- anywhere outside the repository, or as an untracked file
   inside it. **No source commit is required for this step.**
5. Validate it (`validate_evidence_manifest()`, or just run the calculator
   -- it validates on load and fails fast on a broken file).
6. Run the score calculator with `--evidence-file <path>
   --scored-commit ABC` (the latter defaults to `git rev-parse HEAD`, so
   it is only needed explicitly when scoring a commit other than the one
   currently checked out).
7. Read the resulting `CANONICAL_PROJECT_SCORE`.
8. If `LOCAL_ENVIRONMENT_DIAGNOSTICS` disagrees with the canonical result
   (e.g. a local `VERSION_MISMATCH`), fix the local environment
   separately -- it never blocks or changes the canonical score once valid
   matching remote evidence exists.

Each gate entry requires `id` (matching the methodology's gate `name`),
`commit_sha` (a 40-hex-char SHA), `status` (`PASS`/`FAIL`),
`evidence_type`, and `provenance`; `validate_evidence_manifest()` rejects
the file (the whole run fails fast, whether reached via
`--evidence-file`/`BYS360_CANONICAL_EVIDENCE_FILE` or a direct call) if
any of these are missing or malformed, or if `evidence_type` is
`REMOTE_CI_VERIFIED` without a `provenance` value. A CI job name that does
not correspond 1:1 to a single scored gate ID (e.g. an umbrella "run
tests" step) is never force-mapped to a gate just to look more complete --
it belongs in the file's `non_gate_context_only` array instead, for human
audit trail, and is never consulted by the resolver. Evidence whose
*scope* does not match a gate's scope (e.g. a CI job that type-checks only
the service layer, when `mypy_full_scope` scores mypy across the whole
repository) must likewise not be mapped -- recorded honestly as unmapped
context instead, with the mismatch stated explicitly. A mapping supported
only by an *inferred* correlation (e.g. a job name that merely shares a
substring with a test filename, with no stated identity between the two)
is not sufficient grounds for `REMOTE_CI_VERIFIED` credit either -- see
`config/quality/bys360_canonical_evidence.example.json`'s
`handover_docs_contract` entry in `deliberately_unmapped_gates` for a
worked example of a mapping that was removed on exactly this basis during
a provenance re-audit.

## No automated ingestion

This wave adds no GitHub API integration, no `gh` CLI dependency, and no
network requirement anywhere in the evidence path. Evidence ingestion is
explicit and file-based: a human (or, in a later, separately-approved
CI-integration wave, an automated step) produces the JSON file; this
calculator only ever reads a local path. `provenance: "AUTOMATED_INGESTION"`
is a reserved schema value for that future wave -- it is valid input to
the validator today, but nothing in this repository currently produces
it, and no default behavior assumes it exists.

## Trust and honesty limits

`REMOTE_CI_VERIFIED` records an *asserted* verification -- what a human
reported having observed in CI -- not a cryptographically signed
attestation. There is no signature, no hash-chain, no tamper-proofing
beyond ordinary JSON schema validation and the exact-commit-SHA binding.
This is a deliberate, disclosed limitation for v1, not an oversight: a
malformed or logically-inconsistent file is rejected (`EVIDENCE_FILE_INVALID`),
but a file that is well-formed and simply *asserts something untrue* would
be accepted, exactly as `USER_SUPPLIED_REMOTE_PROOF` already discloses.
Do not read `REMOTE_CI_VERIFIED` as a stronger guarantee than "a human
transcribed this from an actual CI run."

## How to score a historical commit

Pass `--scored-commit <sha>` together with `--evidence-file <path>`
pointing at that commit's evidence to score any commit, current or past,
identically -- there is no special-casing between "the currently checked
out commit" and "an older commit." Note this replays the *evidence file's*
claims against whatever registry/methodology content is currently on
disk, not the historical commit's own file tree -- literally checking out
and re-scoring an old commit is not generally meaningful for this
repository's governance files specifically, since the scoring system
itself (the registry, the methodology config, this calculator) did not
exist before it was introduced; there is nothing to replay for a commit
that predates the files being replayed.

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

**Canonical evidence example.** The 66/74 above reflects HEAD (`4bf249f`
at time of writing) scored with **no** `--evidence-file` supplied -- by
design, this repository has no committed file that could apply to the
current commit (see "Self-attestation and the bootstrap problem" above),
so canonical falls back to local execution everywhere, identically to
having no evidence mechanism at all. Running the same registry/methodology
with `--scored-commit 9def579247637390b7635c02f606449a2692ef99
--evidence-file config/quality/bys360_canonical_evidence.example.json`
(pointing explicitly at the historical-sample file, which is never loaded
by default) instead produces `LIVE_READINESS = 89`, `TRANSFERABILITY = 85`
on the *same* machine with the *same* off-pin local Ruff --
`ruff_syntax_import_sanity`, `postgres_migration_integrity_gate`,
`coverage_ratchet`, `dependency_audit`, `ops_audit`, and `quality9_gate`
resolve to canonical `PASS` via `COMMIT_BOUND_REMOTE_VERIFIED` regardless
of the local Ruff mismatch, while `ruff_full_select` (for which no remote
evidence was ever reported) stays honestly `UNKNOWN`.
`LOCAL_ENVIRONMENT_SCORE_NON_CANONICAL` in that same run stays at 66/74
throughout -- proving the 89/85 uplift comes entirely from commit-bound
canonical evidence, never from the local machine quietly getting more
lenient.

`handover_docs_contract` is deliberately **not** in that list: a strict
remote-gate provenance re-audit found its earlier `REMOTE_CI_VERIFIED`
mapping rested only on an inferred filename correlation (a CI job named
"BYS360 Score 100 Quality Gate V1" was assumed to be this gate purely
because the gate's underlying test file contains "score100" in its name),
not a stated identity match -- the mapping was removed. This particular
removal happens not to move either composite number: `handover_docs_contract`
is a version-unpinned `pytest` invocation, so it still resolves to
canonical `PASS` via `LOCAL_VERIFIED` (tier 2) instead of
`REMOTE_CI_VERIFIED` (tier 1) -- same status, different, more honest,
`canonical_source`/`precedence_reason` in the trace. A provenance
correction is applied regardless of whether it happens to move a score;
in this instance it did not.

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
could previously earn full credit; CANONICAL_PROJECT_SCORE is resolved
through commit-bound evidence precedence (see "Evidence precedence"
above), closing a different, subtler gap where the *same* commit could
previously score differently depending on which developer's machine
happened to compute it -- a developer can no longer inflate their own
canonical score by running on a machine with a stale/lenient toolchain
(local results only ever count as canonical when deterministically
correct), nor can a genuinely broken commit's canonical FAIL be
laundered into a PASS by simply computing it locally on a machine that
disagrees with CI.

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
