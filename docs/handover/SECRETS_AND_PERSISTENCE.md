# BYS360 Secrets and Persistence Contract

## The persistent-vs-application-state contract

The following are **external, persistent state**. A candidate build, a cutover, or a
rollback must never overwrite, recreate, or delete any of them:

| Item | What it is | Why it must never come from the package/candidate |
|---|---|---|
| `.env` | Real `DATABASE_URL`, `SECRET_KEY`, mail/SMTP credentials, third-party API tokens (Instagram, weather, etc. — see the full variable list in `.env.example`, values blank) | Contains live secrets; the release builder (`scripts/release/build_bys360_safe_release.py`) explicitly refuses to package any file matching an `.env*` name pattern except the two allowlisted templates (`ALLOWED_ENV_TEMPLATE_BASENAMES = {".env.example", ".env.docker.example"}`) |
| `instance\` | Flask's instance-relative runtime directory | Host/environment-specific runtime data, not source |
| `C:\bys360\storage` | File Center and other persistent on-disk artifacts | User-uploaded content; not reproducible from source |
| `C:\bys360\local_storage` | Persistent local/on-host storage | Same as above |
| The PostgreSQL database itself | All application data | The entire point of this deployment model is to change code without losing or corrupting data |

Everything else — `app/`, `migrations/`, `requirements.txt`, `wsgi.py`, `run_server.py`,
`config.py`, `DEPLOYMENT.md`, templates, static assets — is **application source**, fully
reproducible from the release package, and is exactly what candidate preparation and
cutover are allowed to replace wholesale.

## The release package must never contain

Enforced today by `scripts/release/build_bys360_safe_release.py`'s own filtering rules
(`FORBIDDEN_DIR_PARTS`, `FORBIDDEN_SUFFIXES`, `_is_forbidden_env_file`,
`FORBIDDEN_NAME_PATTERNS`, `FORBIDDEN_EXACT_NAMES`), independently re-checked by this
wave's own scanner (`scripts/release/scan_bys360_release_secrets.py` — see below):

- A real `.env` file (only `.env.example` / `.env.docker.example` are allowed; there is
  currently no `.env.production.example` in this repository — if one is ever added, it must
  also be genuinely value-free, and the release builder's allowlist would need to be
  updated to include it explicitly, not broadened by a looser pattern match).
- A real `SECRET_KEY`, DB passwords, or API secrets, in any file.
- Production database dumps (`.sqlite3`, `.sqlite`, `.db`, `.dump`, `.bak`, `.backup`, `.old`,
  `.orig` are all forbidden suffixes).
- Storage contents (`instance`, `logs`, `uploads`, `reports`, `backups`, `backup`,
  `releases` are all forbidden directory-name segments).
- Private key material of any kind (`.key`, `.pem`, `.p12`, `.pfx`, `.ppk`, `.jks`,
  `.keystore` are all forbidden suffixes).

## Where `.env` values come from, at each phase

`.env` is **never** copied as a plaintext file into a candidate directory, and it is never
part of the release package. Instead:

- **On the live host, today**: the production `.env` file lives at
  `C:\bys360\project\.env`, and `config.py`'s `DOTENV_PATH` resolves to
  `Path(BASE_DIR)/'.env'`, where `BASE_DIR` is `config.py`'s own directory — i.e., whichever
  tree is currently active reads its own adjacent `.env`. `load_dotenv(DOTENV_PATH)` is
  called with the default `override=False`, meaning any OS-level environment variable set
  **before** that call always wins over whatever is (or isn't) in the `.env` file.
- **During candidate preparation (shadow rehearsal)**: the production `.env`'s values are
  read from the live host's actual `.env` file using the real `python-dotenv` library
  (`python-dotenv==1.2.2`, a pinned requirement — the exact same parser `config.py` itself
  uses, not a hand-rolled re-implementation) and injected as **process-local environment
  variables** for the shadow migration's child process only. The historical script's
  `Get-Bys360ProductionEnvValues` (runs a small inline Python script calling
  `dotenv_values()`, transported back as JSON, logging only a variable-count summary, never
  the values) and `Invoke-WithBys360RuntimeEnvironment` (applies the resulting hashtable for
  the duration of one scriptblock, then restores every variable to its exact prior state —
  original value, or fully removed if it was previously absent — in a `finally` block,
  success or failure alike) are the direct model for how the new candidate-preparation
  tooling is expected to do the same thing. Two narrow overrides are layered on top for the
  rehearsal child process only: `REQUIRE_DOTENV_FILE=false` (this flag's only job is
  asserting a literal `.env` file exists on disk — orthogonal to whether the config values
  themselves are present) and `BYS360_FEEDBACK_FOLLOWUP_SCHEDULER=0` (pinning the
  application's own already-default-off background-scheduler switch, defense-in-depth, not
  a new/invented flag).
- **During cutover**: the live `.env` file's actual bytes are read into memory/a safe
  temporary holding location immediately before the current tree is moved aside (`CUTOVER.md`
  step 5), and written back onto the promoted candidate tree immediately after promotion
  (`CUTOVER.md` step 10). The candidate tree, as built during preparation, never contained a
  real `.env` at all — it is only ever placed there, once, at this exact point in cutover,
  directly from the live host's own existing file. `instance\` is handled the same way.
- **`SECRET_KEY` validation** (`config.py`, roughly lines 524–541 as of this writing):
  non-empty, not a known placeholder value (`''`, `CHANGE_ME`, `change-me`, `changeme`,
  `bys360-dev-session-key-change-me-before-production`), and at least 32 characters —
  enforced with a hard `RuntimeError` whenever `APP_ENV` is `production` or `staging`. This
  validation is never weakened, bypassed, or given a dummy value by any part of this
  deployment model; the correct fix for a `SECRET_KEY` validation failure during a
  rehearsal or cutover is always "the real `.env` value isn't reaching this process
  correctly," never "relax the check."

## What must be supplied externally, restated for this document's scope

- The real production `.env` file's contents (on the live host already — this document
  describes how those existing values flow through candidate prep and cutover, not how they
  are first created).
- The real PostgreSQL role credentials, both the application role (used throughout normal
  operation and almost all of shadow rehearsal) and the admin role (used only, interactively,
  for shadow database CREATE/DROP — see `LIVE_INSTALLATION.md` and `DATABASE_MIGRATION.md`).
- Any `instance\` runtime contents the current live host actually has.

None of these are ever expected to exist inside a release ZIP, a candidate directory
(before cutover writes them in), or this repository's own tracked source.
