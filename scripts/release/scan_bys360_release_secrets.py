"""BYS360 independent release secret scanner.

Standalone, reusable secret-scanning tool. This is deliberately NOT part of
`scripts/release/build_bys360_safe_release.py` (the release builder) -- it is a
second, independent check with its own heuristics, meant to be run separately
against:

  - a built release ZIP's extracted contents
  - an offline dependency wheelhouse (build/wheelhouse/)
  - a docs tree (docs/handover/, etc.)
  - a deploy-log directory (C:\\bys360\\deploy_logs\\...)

or any other directory tree an operator wants checked before trusting it.

WHAT THIS SCANS FOR
  1. Literal ".env"-shaped files that are not one of the explicitly allowed,
     value-free template basenames.
  2. Real-looking SECRET_KEY / SESSION_SECRET / JWT_SECRET / APP_SECRET
     assignments (non-placeholder, long enough to plausibly be a real key).
  3. DATABASE_URL / generic connection strings embedding non-placeholder
     user:password credentials (postgres/postgresql/mysql/mongodb/redis).
  4. Password-shaped assignments (any *PASSWORD*/*PASSWD*/*PWD* key with a
     non-placeholder, non-trivial value).
  5. Well-known API token / key formats (AWS access key IDs, GitHub tokens,
     Slack tokens, Google API keys, Stripe keys, generic Bearer tokens, JWTs).
  6. Private key material ("-----BEGIN ... PRIVATE KEY-----" and PGP private
     key blocks).
  7. Generic high-entropy values sitting next to a secret-shaped keyword
     (catches secrets that don't match any of the specific patterns above).

DESIGN / HEURISTIC NOTES (read before trusting the output blindly)
  This is a heuristic scanner, not a proof. Patterns 1, 2 (basename check) and
  6 (private key headers) are exact/structural and have effectively no false
  positives. Patterns 2-5 and 7 combine keyword proximity with a placeholder
  denylist and a Shannon-entropy floor -- this WILL have some false-positive
  rate on real repositories (a long non-secret hash, a minified JS blob, a
  base64-encoded test fixture, a lock-file digest, or a legitimately-named
  variable like "PASSWORD_MIN_LENGTH=8" that merely contains the substring
  "PASSWORD"). Every finding should be individually reviewed, not bulk-
  dismissed or bulk-trusted. This tradeoff is intentional and documented here
  rather than overclaimed: a scanner that only matched exact, well-known
  formats would miss most real secrets (arbitrary internal API keys, ad hoc
  passwords), and a scanner that flagged every long string would be useless
  noise. Entropy + keyword proximity is the standard middle ground; tune
  --min-entropy and the placeholder list below if your environment's
  false-positive rate is too high or too low.

OUTPUT SAFETY
  This scanner never prints a full matched secret value if it is a long,
  high-entropy string. Long matches are shown redacted (first/last couple of
  characters plus a length + entropy summary) so a human can confirm *that*
  something matched a shape without the real secret ever appearing in scan
  output, logs, or anything piped from this tool. Short, well-known
  structural markers (e.g. a PEM header line, a variable name) are shown in
  full since they carry no secret material themselves.

CLI
  python scan_bys360_release_secrets.py <path> [<path> ...] [--json]
      [--min-entropy 3.5] [--max-file-bytes 5000000] [--quiet]

  Exit code 0  : no findings.
  Exit code 1  : one or more findings (scan itself completed normally).
  Exit code 2  : usage error (bad path, etc.) -- distinct from "found secrets"
                 so calling scripts/CI can tell the two failure modes apart.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Allowlists / skip lists
# ---------------------------------------------------------------------------

# Exact basenames (case-insensitive) that are allowed to look like an .env
# file because they are genuinely value-free templates. Kept as an allowlist,
# not a broadened regex, deliberately mirroring the same allowlist-not-regex
# principle used by scripts/release/build_bys360_safe_release.py -- but
# reimplemented independently here rather than imported, since this tool is
# meant to be usable standalone against arbitrary directories, including ones
# that have nothing to do with that builder (a wheelhouse, a docs tree, a
# deploy-log directory).
ALLOWED_ENV_TEMPLATE_BASENAMES = {
    ".env.example",
    ".env.docker.example",
    ".env.production.example",
    ".env.sample",
    ".env.template",
}

# Any path segment named one of these is skipped entirely -- build tooling,
# VCS metadata, and caches have no secret-scanning value and can be very
# large (wheelhouse .whl contents in particular).
SKIP_DIR_NAMES = {
    ".git", ".hg", ".svn", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", "node_modules", ".venv", "venv", ".idea", ".vscode",
}

# Extensions skipped for CONTENT scanning (binary / not meaningfully
# text-searchable). The filename itself is still checked against the .env
# rule and these extensions are still counted in the files-scanned total.
BINARY_SKIP_SUFFIXES = {
    ".whl", ".zip", ".7z", ".rar", ".gz", ".tar", ".pyc", ".pyo", ".pyd",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".bmp", ".webp", ".pdf",
    ".exe", ".dll", ".so", ".dylib", ".woff", ".woff2", ".ttf", ".eot",
    ".mp3", ".mp4", ".avi", ".mov",
}

# Values that look secret-shaped but are known placeholders / non-secrets.
# Checked case-insensitively, both as an exact match and as a substring for
# the more generic markers.
PLACEHOLDER_EXACT = {
    "", "change_me", "changeme", "change-me", "xxx", "xxxx", "todo",
    "placeholder", "dummy", "example", "none", "null", "n/a", "na",
    "your_password", "yourpassword", "password", "secret", "test",
    "test123", "admin", "postgres", "root",
    "bys360-dev-session-key-change-me-before-production",
    "bys360-local-dev-only-secret",
}
PLACEHOLDER_SUBSTRINGS = (
    "change_me", "changeme", "change-me", "your_", "your-", "<your",
    "example", "placeholder", "dummy", "insert_", "insert-", "replace_me",
    "replace-me", "xxxxxxxx", "0000000000", "1111111111",
    # Coordinator fix (2026-08-25, schema-contract-drift wave, real-worktree
    # false-positive audit): "replace-with-a-strong-random-value" is this
    # project's own tracked .env.docker.example instructional placeholder,
    # used for both its SECRET_KEY and its POSTGRES_PASSWORD entries --
    # already documented and allowlisted by the sibling
    # scripts/quality/bys360_secret_repo_gate.py gate (its own "replace-with"
    # marker), which this scanner had not yet matched.
    "replace-with", "replace_with",
)

MIN_SECRET_LENGTH = 12          # below this, not worth flagging as a "real" secret
MAX_SECRET_LENGTH_FOR_LINE_SCAN = 4096
DEFAULT_MIN_ENTROPY = 3.3       # bits/char floor for the generic high-entropy rule
DEFAULT_MAX_FILE_BYTES = 5_000_000  # 5 MB cap per file read, documented below


# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

PRIVATE_KEY_RE = re.compile(
    r"-----BEGIN (?:[A-Z0-9 ]*PRIVATE KEY|PGP PRIVATE KEY BLOCK)-----"
)

# user:password@host portion of a connection URL. Deliberately permissive on
# the scheme (postgres/postgresql/mysql/mongodb(+srv)/redis/rediss) since a
# real production DATABASE_URL is the primary target here.
DATABASE_URL_RE = re.compile(
    r"\b(?P<scheme>postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|rediss)"
    r"(?:\+[a-zA-Z0-9_]+)?://(?P<user>[^:@/\s'\"]+):(?P<password>[^@\s'\"]+)@"
    r"(?P<host>[^/\s'\"]+)",
)

SECRET_KEY_ASSIGN_RE = re.compile(
    r"(?im)^\s*(?P<key>SECRET_KEY|SESSION_SECRET|JWT_SECRET|APP_SECRET|"
    r"FLASK_SECRET)\s*[:=]\s*['\"]?(?P<value>[^\s'\";,]+)"
)

GENERIC_PASSWORD_RE = re.compile(
    r"(?im)^\s*(?P<key>[A-Za-z0-9_]*(?:PASSWORD|PASSWD|PWD)[A-Za-z0-9_]*)\s*"
    r"[:=]\s*['\"]?(?P<value>[^\s'\";,]+)"
)

GENERIC_TOKEN_KEYWORD_RE = re.compile(
    r"(?im)^\s*(?P<key>[A-Za-z0-9_]*(?:API[_-]?KEY|ACCESS[_-]?TOKEN|AUTH[_-]?"
    r"TOKEN|CLIENT[_-]?SECRET|PRIVATE[_-]?TOKEN)[A-Za-z0-9_]*)\s*[:=]\s*"
    r"['\"]?(?P<value>[^\s'\";,]+)"
)

# Coordinator fix (2026-08-25, schema-contract-drift wave, real-worktree
# false-positive audit): explicit, word-bounded keyword allowlist for the
# generic high-entropy catch-all rule below -- replaces a bare case-
# insensitive substring match on SECRET|TOKEN|KEY|CRED, which matched ANY
# identifier merely *containing* one of those substrings anywhere
# (permission_key, primary_key, foreign_key, key_name, access_token in
# unrelated contexts, etc.). Verified against this project's own real,
# fully-assembled release tree: this was the root cause of 741 of 825
# findings in a real scan (BYS360 schema-contract-drift wave FULL-build
# validation, 2026-08-25) -- every one traced to a plain "key"/"token"
# substring in an ordinary template/JS/Python identifier, not a secret.
# \b...\b boundaries mean "secret_key_name" or "openai_api_key_id" do NOT
# match SECRET_KEY/API_KEY (the trailing "_name"/"_id" continues the word,
# so there is no boundary right after the keyword) -- only an exact,
# complete keyword token matches.
GENERIC_SECRET_KEYWORDS = (
    "SECRET_KEY", "API_KEY", "API_TOKEN", "ACCESS_TOKEN", "AUTH_TOKEN",
    "CLIENT_SECRET", "PRIVATE_KEY", "PASSWORD", "PASSWD", "DATABASE_URL",
    "DB_PASSWORD", "MAIL_PASSWORD", "SMTP_PASSWORD", "OPENAI_API_KEY",
    "GITHUB_TOKEN", "GH_TOKEN", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
)
GENERIC_SECRET_KEYWORD_RE_FRAGMENT = "|".join(GENERIC_SECRET_KEYWORDS)

# Well-known structural token/key formats -- exact-pattern detection, minimal
# false-positive rate by construction.
KNOWN_TOKEN_PATTERNS: dict[str, re.Pattern[str]] = {
    "aws_access_key_id": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "aws_secret_hint": re.compile(
        r"(?i)aws_secret_access_key\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{40}\b"
    ),
    "github_token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,255}\b"),
    "slack_token": re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,72}\b"),
    # Real Google API keys are exactly "AIza" + 35 chars, but matching an
    # exact length is brittle (found during this scanner's own fixture
    # testing -- a synthetic test value one character short of 35 silently
    # missed this pattern and only got caught by the generic entropy
    # fallback below). Widened to a bounded range on the same AIza prefix.
    "google_api_key": re.compile(r"\bAIza[0-9A-Za-z\-_]{20,40}\b"),
    "stripe_key": re.compile(r"\bsk_(?:live|test)_[0-9a-zA-Z]{16,}\b"),
    "generic_bearer_token": re.compile(r"(?i)\bBearer\s+[A-Za-z0-9\-_.=]{20,}"),
    "jwt_like": re.compile(
        r"\beyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\b"
    ),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def shannon_entropy(s: str) -> float:
    """Shannon entropy in bits/char. Higher = more random-looking."""
    if not s:
        return 0.0
    freq: dict[str, int] = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    length = len(s)
    return -sum((c / length) * math.log2(c / length) for c in freq.values())


def is_placeholder(value: str) -> bool:
    v = value.strip().strip("'\"")
    lv = v.lower()
    if lv in PLACEHOLDER_EXACT:
        return True
    if any(marker in lv for marker in PLACEHOLDER_SUBSTRINGS):
        return True
    # Angle-bracket instructional placeholders, e.g.
    # SECRET_KEY=<local-development-random-value-here> -- a documentation
    # convention for "put your own value here", not a literal secret. Found
    # via this scanner's own real-repo test run against
    # docs/handover/BYS360_FINAL_HANDOVER_AND_SUSTAINABILITY.md.
    if v.startswith("<") and v.endswith(">"):
        return True
    # PowerShell/shell variable references and expressions
    # ($m.Groups['pass'].Value, $($DbConn.Password), $env:FOO, ${bar}) are
    # CODE building a value at runtime, never a literal secret sitting in
    # source. Found via this scanner's own real-repo test run against
    # scripts/windows/deploy_bys360_ec4e56b_production_v*.ps1, where regex
    # capture-group plumbing and runtime DATABASE_URL string interpolation
    # were being misread as hardcoded credentials.
    if v.startswith("$"):
        return True
    # Coordinator fix (2026-08-25, schema-contract-drift wave, real-worktree
    # false-positive audit): a value ending in an unclosed "(" is a
    # truncated function-call expression (os.environ.get(, os.getenv(,
    # self.get_config(), never a literal credential -- the capture regexes
    # stop at the first quote/comma/semicolon/whitespace, so
    # `SECRET_KEY = os.environ.get("SECRET_KEY")` captures exactly
    # "os.environ.get(" as the "value". Confirmed against this project's own
    # real config.py (line 541: `SECRET_KEY = os.environ.get("FLASK_SECRET")
    # or "..."`) during the FULL-build validation that found this class of
    # false positive.
    return bool(v.endswith("("))


# Any of these punctuation characters appearing in a captured "secret
# value" is treated as unambiguous proof of CODE (attribute access,
# function/method calls -- possibly nested, e.g.
# `_clean_text(_form_get(form,` -- subscript access, dict/set/list
# literals), never a literal credential. Deliberately a simple containment
# check rather than a regex trying to model call/subscript nesting depth:
# real secret formats (base64, hex, JWT segments, AWS/GitHub/Stripe/Slack
# token formats, arbitrary API keys) never legitimately contain a literal
# ``(``/``)``/``[``/``]``/``{``/``}``/``.`` character in the token itself
# (JWTs use exactly two ``.`` separators, but those are matched by the
# separate, exact `jwt_like` KNOWN_TOKEN_PATTERNS entry, independent of
# this keyword-proximity path).
CODE_REFERENCE_PUNCTUATION = ".()[]{}"


def is_code_reference(value: str) -> bool:
    """True for a captured 'secret value' containing attribute-access,
    call, or subscript/literal punctuation (os.environ.get(, self.foo.bar,
    secrets.token_urlsafe(32), generate_password(16),
    response.json()["access_token"], db.Column(db.String(255))) --
    unambiguous CODE, never a literal credential. Confirmed against this
    project's own real config.py, app/admin/routes.py, app/models/
    core_models.py, and app/services/cic/mail_service.py during the
    schema-contract-drift wave's FULL-build validation (2026-08-25)."""
    v = value.strip().strip("'\"")
    return any(ch in v for ch in CODE_REFERENCE_PUNCTUATION)


# A pure letters-and-underscores token (at least two underscore-separated
# segments, zero digits) -- i.e. it reads as a snake_case variable/field
# name (current_password, force_password_change, _raw_secret_key,
# password_hasher), not a generated credential. Deliberately narrow: real
# secrets/tokens/passwords virtually always include at least one digit
# and/or genuinely mixed/random casing (that is what gives a generator
# enough entropy in the first place); a value that is ENTIRELY letters and
# underscores with zero digits is far more likely to be a readable
# identifier. A value with even one digit does not match, so this cannot
# suppress a realistic generated secret -- confirmed against every
# fixture in tests/release/test_scan_bys360_release_secrets.py's "must
# still catch" section, none of which are digit-free.
READABLE_IDENTIFIER_RE = re.compile(r"_?[A-Za-z]+(?:_[A-Za-z]+)+")


def is_readable_identifier(value: str) -> bool:
    """True when the value reads as a snake_case variable/field name
    rather than a generated credential -- see READABLE_IDENTIFIER_RE."""
    v = value.strip().strip("'\"")
    return bool(READABLE_IDENTIFIER_RE.fullmatch(v))


def redact(value: str) -> str:
    """Never echo a long high-entropy value in full. Short structural
    markers (variable names, PEM headers) are not passed through this
    function at all -- only actual candidate-secret VALUES are."""
    v = value.strip().strip("'\"")
    length = len(v)
    ent = shannon_entropy(v)
    shown = "*" * length if length <= 6 else f"{v[:2]}{'*' * min(length - 4, 24)}{v[-2:]}"
    return f"{shown} (len={length}, entropy={ent:.2f} bits/char)"


def is_env_like_basename(name: str) -> bool:
    lname = name.lower()
    return lname == ".env" or lname.startswith(".env.") or lname.endswith(".env")


# ---------------------------------------------------------------------------
# Finding model
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    category: str
    severity: str  # "critical" | "high" | "medium"
    file: str
    line: int | None
    detail: str
    rule_id: str

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------

def iter_scan_files(root: Path):
    if root.is_file():
        yield root
        return
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        yield path


def scan_filename(path: Path, findings: list[Finding]) -> None:
    name = path.name
    if is_env_like_basename(name) and name.lower() not in {
        b.lower() for b in ALLOWED_ENV_TEMPLATE_BASENAMES
    }:
        findings.append(
            Finding(
                category="env_file",
                severity="critical",
                file=str(path),
                line=None,
                detail=(
                    f"literal env-shaped file present: '{name}' is not in the "
                    f"allowed template basename list {sorted(ALLOWED_ENV_TEMPLATE_BASENAMES)}"
                ),
                rule_id="ENV_FILE_NOT_ALLOWLISTED",
            )
        )


def scan_text_content(
    path: Path, text: str, min_entropy: float, findings: list[Finding]
) -> None:
    lines = text.splitlines()

    for lineno, line in enumerate(lines, start=1):
        if len(line) > MAX_SECRET_LENGTH_FOR_LINE_SCAN:
            line = line[:MAX_SECRET_LENGTH_FOR_LINE_SCAN]

        pk_match = PRIVATE_KEY_RE.search(line)
        # Coordinator fix (2026-08-25, schema-contract-drift wave, real-
        # worktree false-positive audit): a real PEM header line IS the
        # header (plus surrounding whitespace) and nothing else -- require
        # the stripped line to actually START WITH the matched text, so a
        # comment/docstring merely quoting the header as documentation
        # (confirmed real repro: scripts/quality/bys360_secret_repo_gate.py's
        # own comment describing this exact detection rule) does not match.
        if pk_match and line.strip().startswith(pk_match.group(0)):
            findings.append(
                Finding(
                    category="private_key",
                    severity="critical",
                    file=str(path),
                    line=lineno,
                    detail="private key header found (body not shown/scanned further)",
                    rule_id="PRIVATE_KEY_HEADER",
                )
            )

        m = DATABASE_URL_RE.search(line)
        if m:
            password = m.group("password")
            if not is_placeholder(password) and len(password) >= 3:
                findings.append(
                    Finding(
                        category="database_url",
                        severity="critical",
                        file=str(path),
                        line=lineno,
                        detail=(
                            f"{m.group('scheme')}:// connection string with non-placeholder "
                            f"credentials -- password {redact(password)}"
                        ),
                        rule_id="DATABASE_URL_CREDENTIALS",
                    )
                )

        m = SECRET_KEY_ASSIGN_RE.search(line)
        if m:
            value = m.group("value")
            if (
                not is_placeholder(value)
                and not is_code_reference(value)
                and not is_readable_identifier(value)
                and len(value) >= MIN_SECRET_LENGTH
                and shannon_entropy(value) >= min_entropy
            ):
                findings.append(
                    Finding(
                        category="secret_key",
                        severity="critical",
                        file=str(path),
                        line=lineno,
                        detail=f"{m.group('key')} assignment looks real -- {redact(value)}",
                        rule_id="SECRET_KEY_LIKE_VALUE",
                    )
                )

        m = GENERIC_PASSWORD_RE.search(line)
        if m:
            value = m.group("value")
            if (
                not is_placeholder(value)
                and not is_code_reference(value)
                and not is_readable_identifier(value)
                and len(value) >= 6
                and shannon_entropy(value) >= min_entropy
            ):
                findings.append(
                    Finding(
                        category="password",
                        severity="high",
                        file=str(path),
                        line=lineno,
                        detail=f"{m.group('key')} assignment looks real -- {redact(value)}",
                        rule_id="PASSWORD_LIKE_VALUE",
                    )
                )

        m = GENERIC_TOKEN_KEYWORD_RE.search(line)
        if m:
            value = m.group("value")
            if (
                not is_placeholder(value)
                and not is_code_reference(value)
                and not is_readable_identifier(value)
                and len(value) >= MIN_SECRET_LENGTH
                and shannon_entropy(value) >= min_entropy
            ):
                findings.append(
                    Finding(
                        category="api_token",
                        severity="high",
                        file=str(path),
                        line=lineno,
                        detail=f"{m.group('key')} assignment looks real -- {redact(value)}",
                        rule_id="TOKEN_KEYWORD_LIKE_VALUE",
                    )
                )

        for rule_id, pattern in KNOWN_TOKEN_PATTERNS.items():
            km = pattern.search(line)
            if km:
                matched = km.group(0)
                # Coordinator fix (2026-08-25, schema-contract-drift wave,
                # real-worktree false-positive audit): generic_bearer_token's
                # format is intentionally loose (any 20+ char token after
                # "Bearer "), which matched obviously-fake test/gate fixture
                # values shaped like "Bearer bys360.invalid.test.token" --
                # real bearer tokens (excluding JWTs, which the separate,
                # exact `jwt_like` entry below already covers independently)
                # never legitimately contain a literal "." character.
                if rule_id == "generic_bearer_token" and "." in matched:
                    continue
                findings.append(
                    Finding(
                        category="api_token",
                        severity="critical",
                        file=str(path),
                        line=lineno,
                        detail=f"known token format matched ({rule_id}) -- {redact(matched)}",
                        rule_id=f"KNOWN_FORMAT_{rule_id.upper()}",
                    )
                )

        # Generic high-entropy-near-keyword catch-all: only fires on tokens
        # that look assignment-shaped (KEY=VALUE / KEY: VALUE), where KEY is
        # one of an explicit, word-bounded list of real secret-indicator
        # keywords (GENERIC_SECRET_KEYWORDS) -- NOT a bare case-insensitive
        # substring match on SECRET/TOKEN/KEY/CRED, which used to match ANY
        # identifier merely containing one of those substrings anywhere
        # (permission_key, primary_key, foreign_key, key_name, etc. -- see
        # GENERIC_SECRET_KEYWORDS' docstring for the real-repo false-positive
        # audit this fixes).
        for gm in re.finditer(
            rf"(?i)\b({GENERIC_SECRET_KEYWORD_RE_FRAGMENT})\b\s*[:=]\s*"
            r"['\"]?([A-Za-z0-9+/_\-\.=]{16,})['\"]?",
            line,
        ):
            key, value = gm.group(1), gm.group(2)
            # This regex's value character class deliberately excludes
            # "(", ")", "[", "]" (unlike the other three assignment regexes
            # above, which capture them) -- so a code expression like
            # `_cic_v11_get_setting_value(["MAIL_PASSWORD", ...` gets cut
            # off at the "(" instead of continuing to capture it, and
            # is_code_reference() never sees the punctuation that would
            # identify it as code. Peeking at the very next character in
            # the line catches this: if the match stopped right at an
            # open paren/bracket, the "value" is a truncated call/subscript
            # expression, not a literal. Confirmed real repro:
            # app/services/cic/mail_service.py's
            # `password = _cic_v11_get_setting_value([...], "")`.
            next_char = line[gm.end(2) : gm.end(2) + 1]
            if (
                is_placeholder(value)
                or is_code_reference(value)
                or is_readable_identifier(value)
                or next_char in "(["
                or len(value) < MIN_SECRET_LENGTH
            ):
                continue
            ent = shannon_entropy(value)
            if ent >= min_entropy:
                findings.append(
                    Finding(
                        category="generic_high_entropy",
                        severity="medium",
                        file=str(path),
                        line=lineno,
                        detail=f"{key} has a high-entropy value -- {redact(value)}",
                        rule_id="HIGH_ENTROPY_NEAR_KEYWORD",
                    )
                )


def scan_path(
    root: Path,
    min_entropy: float = DEFAULT_MIN_ENTROPY,
    max_file_bytes: int = DEFAULT_MAX_FILE_BYTES,
) -> tuple[list[Finding], int]:
    findings: list[Finding] = []
    files_scanned = 0

    for path in iter_scan_files(root):
        files_scanned += 1
        scan_filename(path, findings)

        if path.suffix.lower() in BINARY_SKIP_SUFFIXES:
            continue

        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size == 0:
            continue

        try:
            with path.open("rb") as fh:
                raw = fh.read(max_file_bytes)
        except OSError:
            continue

        # Best-effort binary sniff: a NUL byte in the first chunk means this
        # is very unlikely to be meaningful text content.
        if b"\x00" in raw:
            continue

        text = raw.decode("utf-8", errors="replace")
        scan_text_content(path, text, min_entropy, findings)

    return findings, files_scanned


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Independent BYS360 release secret scanner. Scans a directory tree "
            "(extracted release ZIP, wheelhouse, docs tree, deploy-log directory) "
            "for real-looking secrets. Never prints a full long/high-entropy "
            "secret value -- findings are redacted. Exits non-zero on any finding."
        )
    )
    parser.add_argument("paths", nargs="+", help="File(s)/directory(ies) to scan.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--min-entropy",
        type=float,
        default=DEFAULT_MIN_ENTROPY,
        help=f"Shannon-entropy floor (bits/char) for the generic catch-all rule (default: {DEFAULT_MIN_ENTROPY}).",
    )
    parser.add_argument(
        "--max-file-bytes",
        type=int,
        default=DEFAULT_MAX_FILE_BYTES,
        help=f"Max bytes read per file (default: {DEFAULT_MAX_FILE_BYTES}).",
    )
    parser.add_argument("--quiet", action="store_true", help="Only print the final summary line.")
    args = parser.parse_args(argv)

    all_findings: list[Finding] = []
    total_files = 0
    for raw_path in args.paths:
        p = Path(raw_path)
        if not p.exists():
            print(f"error: path does not exist: {p}", file=sys.stderr)
            return 2
        findings, files_scanned = scan_path(
            p, min_entropy=args.min_entropy, max_file_bytes=args.max_file_bytes
        )
        all_findings.extend(findings)
        total_files += files_scanned

    if args.json:
        result = {
            "ok": len(all_findings) == 0,
            "files_scanned": total_files,
            "finding_count": len(all_findings),
            "findings": [f.to_dict() for f in all_findings],
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if not all_findings else 1

    if not args.quiet:
        for f in all_findings:
            loc = f"{f.file}:{f.line}" if f.line is not None else f.file
            print(f"[{f.severity.upper()}] [{f.category}] {loc} -- {f.detail} ({f.rule_id})")

    if all_findings:
        by_category: dict[str, int] = {}
        for f in all_findings:
            by_category[f.category] = by_category.get(f.category, 0) + 1
        summary = ", ".join(f"{k}={v}" for k, v in sorted(by_category.items()))
        print(f"\nFAIL: {len(all_findings)} finding(s) across {total_files} file(s) scanned. ({summary})")
        return 1

    print(f"OK: 0 findings across {total_files} file(s) scanned.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
