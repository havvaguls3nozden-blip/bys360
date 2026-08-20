from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PACKAGE = "BYS360_SECRET_REPO_GATE_V2_PHASE1"

TEXT_EXTS = {
    ".py", ".ps1", ".sh", ".bat", ".cmd", ".yml", ".yaml", ".toml", ".ini",
    ".cfg", ".conf", ".json", ".txt", ".md", ".env", ".example", ".dockerignore",
}

SECRET_KEYS = (
    "SECRET_KEY", "DATABASE_URL", "SQLALCHEMY_DATABASE_URI", "POSTGRES_PASSWORD",
    "DB_PASSWORD", "PASSWORD", "TCKN_ENCRYPTION_KEY", "SENTRY_DSN", "AI_API_KEY",
    "API_KEY", "ACCESS_TOKEN", "INSTAGRAM_ACCESS_TOKEN", "TOKEN",
    # BYS360 Phase 10J: config.py reads FLASK_SECRET (a real runtime env var,
    # used as the Flask secret-key fallback, loaded at app-factory startup)
    # whose name ends in bare SECRET, not SECRET_KEY -- previously invisible
    # to this list. Kept here for documentation only; SENSITIVE_KEY_ALTERNATION
    # below is what actually drives detection.
    "SECRET",
)

# BYS360 Phase 5 secret-gate scope correction (2026-07-26): the leading ""
# sentinel here made `any(word in lower for word in PLACEHOLDER_WORDS)`
# unconditionally True (an empty string is a substring of every string),
# which silently classified every real secret value as a placeholder and
# made the hardcoded-secret/database-url finding paths permanently
# unreachable. Removed; an empty value is still caught separately by the
# `len(v) < 16` check below.
PLACEHOLDER_WORDS = (
    "none", "null", "false", "true", "change_me", "changeme", "placeholder", "example",
    "dummy", "redacted", "your_", "buraya", "degistir", "değiştir", "not_set", "unset",
    "local", "localhost", "127.0.0.1", "test", "testing", "dev", "development", "bys_pass",
    "secret_key_from_env", "database_url_from_env", "sentry_dsn_from_env",
    # BYS360 Phase 10I unquoted-.env-assignment hardening: this is the exact
    # instructional-placeholder phrase used in the tracked .env.docker.example
    # (SECRET_KEY=replace-with-a-strong-random-value / POSTGRES_PASSWORD=...).
    # It matched no prior word here, so once unquoted assignments started
    # being scanned it would have false-positived on that already-safe file.
    "replace-with",
)

ENV_REFERENCE_MARKERS = (
    "os.environ", "os.getenv", "getenv(", "environ.get", "current_app.config", "config.get(",
    "${", "%", "env:", "Environment.GetEnvironmentVariable", "load_dotenv", "from_env",
)

REGEX_OR_SCANNER_MARKERS = (
    "re.compile", "regex", "pattern", "SECRET_KEYS", "PLACEHOLDER", "secret scanner",
    "secret_repo_gate", "database_url_with_password", "hardcoded_secret", "SENTRY_DSN i",
    "SECRET_KEY i", "DATABASE_URL i", "SQLALCHEMY_DATABASE_URI i",
)

# BYS360 Phase 5 secret-gate closure (2026-08-02): raw PEM/OpenSSH/PGP private
# key material pasted directly into a file (not wrapped in a `KEY = "value"`
# assignment) was invisible to every scan path above -- ASSIGN_RE/DICT_ASSIGN_RE/
# UNQUOTED_ASSIGN_RE only ever look at a value following a sensitive KEY name
# and an assignment operator on the same line, and a PEM block's header line
# has neither. Confirmed by direct reproduction: a tracked file containing only
# a "-----BEGIN PRIVATE KEY-----" header produced finding_count=0 before this
# addition. The header line alone is a reliable, low-false-positive signal --
# real key material is essentially the only thing that legitimately starts a
# line this way -- so it is matched independently of the KEY=value machinery.
PRIVATE_KEY_HEADER_RE = re.compile(r"-----BEGIN (?:[A-Z0-9]+ )?PRIVATE KEY(?: BLOCK)?-----")

DB_URL_RE = re.compile(r"(?:postgresql|postgres|mysql|mariadb)://([^\s:'\"/@]+):([^\s'\"/@]+)@", re.I)
# BYS360 Phase 5 secret-gate false-positive fix (2026-07-26): DB_URL_RE above
# already deliberately excludes the sqlite scheme from its embedded-
# credential check, because a `sqlite:///...` DSN is structurally a file
# path or `:memory:` -- it has no `user:password@host` component to leak.
# DATABASE_URL_KEY_ASSIGN_RE / DICT_ASSIGN_RE below match on the DATABASE_URL
# / SQLALCHEMY_DATABASE_URI *key name* regardless of scheme, so they lacked
# that same scheme-awareness. SQLITE_DSN_RE lets the DATABASE_URL/
# SQLALCHEMY_DATABASE_URI handling in scan_file() apply the identical,
# pre-existing precedent -- scoped only to those two connection-string keys,
# not to PASSWORD/SECRET_KEY/TOKEN/API_KEY.
SQLITE_DSN_RE = re.compile(r"^sqlite:///", re.I)
DATABASE_URL_KEYS = frozenset({"DATABASE_URL", "SQLALCHEMY_DATABASE_URI"})
# BYS360 Phase 10I: shared across the quoted (ASSIGN_RE/DICT_ASSIGN_RE) and
# unquoted (UNQUOTED_ASSIGN_RE) patterns below so the set of sensitive key
# names can't drift between them.
SENSITIVE_KEY_ALTERNATION = (
    r"SECRET_KEY|DATABASE_URL|SQLALCHEMY_DATABASE_URI|POSTGRES_PASSWORD|DB_PASSWORD|"
    r"PASSWORD|TCKN_ENCRYPTION_KEY|SENTRY_DSN|AI_API_KEY|API_KEY|ACCESS_TOKEN|"
    r"INSTAGRAM_ACCESS_TOKEN|TOKEN|"
    # BYS360 Phase 10J: bare SECRET, added specifically because config.py's
    # FLASK_SECRET (real runtime env var, Flask secret-key fallback read at
    # app-factory startup) ends in SECRET, not SECRET_KEY, and was invisible
    # to every scan path. A bare word here is precedented by PASSWORD/TOKEN
    # above; the required immediate `\s*[:=]\s*`/`\s*=\s*` adjacency in
    # ASSIGN_RE/DICT_ASSIGN_RE/UNQUOTED_ASSIGN_RE means a metadata suffix
    # like _NAME/_PATH/_ID sitting between the matched word and the
    # assignment operator still breaks the match -- e.g. CLIENT_SECRET_NAME
    # or SECRET_ROTATION_ID are not affected by this addition.
    r"SECRET"
)
ASSIGN_RE = re.compile(
    rf"(?P<key>{SENSITIVE_KEY_ALTERNATION})\s*[:=]\s*(?P<quote>[\"'])(?P<value>.*?)(?P=quote)",
    re.I,
)
DICT_ASSIGN_RE = re.compile(
    rf"(?P<quote>[\"'])(?P<key>{SENSITIVE_KEY_ALTERNATION})(?P=quote)\s*:\s*(?P<vquote>[\"'])(?P<value>.*?)(?P=vquote)",
    re.I,
)
# BYS360 Phase 10I unquoted-.env-assignment hardening: ASSIGN_RE/DICT_ASSIGN_RE
# above only match a value wrapped in a quote character, so a standard,
# unquoted .env-format line (KEY=value -- the actual shape of every real
# .env/.env.example/.env.docker.example line in this repo) was never even
# considered for placeholder-vs-real classification. Anchored to the whole
# (stripped) line, with an optional shell-style `export ` prefix, and only
# tried in scan_file() when neither quoted pattern already matched -- quoted
# assignments keep going through the exact path they always did. The
# `[A-Z0-9_]*` prefix before the named `key` group (matching, not captured)
# mirrors ASSIGN_RE's own unanchored `.finditer()` behavior, which already
# lets a compound name ending in a sensitive suffix (SMTP_PASSWORD,
# STRIPE_API_KEY, REFRESH_TOKEN, ...) match today when quoted -- without it,
# the unquoted path would cover a narrower set of key names than the quoted
# path already does.
UNQUOTED_ASSIGN_RE = re.compile(
    rf"^(?:export\s+)?[A-Z0-9_]*(?P<key>{SENSITIVE_KEY_ALTERNATION})\s*=\s*(?P<value>.*)$",
    re.I,
)
# Splits a trailing ` # comment` off an unquoted value. Requires a preceding
# whitespace character before `#` so a `#` with no leading space -- e.g. a
# URL fragment like `https://example.com/path#section` -- is never mistaken
# for a comment marker and truncated.
INLINE_COMMENT_RE = re.compile(r"\s#")


# BYS360_PHASE1_BLOCKED_REPO_ARTIFACTS
# Bu kontrol secret taramasindan ayridir: gerçek DB, local runtime, yedek ve paket kalintilari
# kaynak agacinda veya release paketinde bulunmamalidir.
BLOCKED_REPO_DIR_NAMES = {
    "instance", "_local_secrets", "_security_quarantine", "_cleanup_quarantine", "payload", "overlay_payload",
}
BLOCKED_REPO_SUFFIXES = {
    ".sqlite3", ".sqlite", ".db", ".dump", ".bak", ".backup", ".old", ".orig",
    ".log", ".key", ".pem", ".p12", ".pfx", ".ppk", ".jks", ".keystore",
}
ENV_FILE_BLOCK_RE = re.compile(r"(^|/|\\)\.env($|\.)", re.I)
BLOCKED_REPO_NAME_PATTERNS = (
    ENV_FILE_BLOCK_RE,
    re.compile(r"\.gitignore\.bak", re.I),
    re.compile(r"\.bak_", re.I),
    re.compile(r"disabled_by_rollback", re.I),
    re.compile(r"clean_package_manifest.*\.json$", re.I),
)


class GitCandidateListError(RuntimeError):
    """Git tabanlı repository aday dosya listesi üretilemediğini belirtir.

    BYS360 Phase 5 kapsam düzeltmesi: gate artık kendi elle yazdığı dizin/uzantı
    hariç-tutma listeleriyle fiziksel dosya sistemini taramaz; Git'in tracked/
    staged/untracked-non-ignored sınıflandırmasını kaynak kabul eder. Bu
    sınıflandırma üretilemezse (ör. `.git` yok, git PATH'te değil, komut
    başarısız) gate sessizce fiziksel köke düşüp sahte bir PASS üretmek yerine
    açıkça başarısız olmalıdır.
    """


def _git_lines(args: list[str], root: Path) -> list[str]:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(root),
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        raise GitCandidateListError(f"git {' '.join(args)} çalıştırılamadı: {exc}") from exc
    if proc.returncode != 0:
        raise GitCandidateListError(
            f"git {' '.join(args)} başarısız (exit={proc.returncode}): {proc.stderr.strip()}"
        )
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def _resolve_candidate(root: Path, rel: str) -> Path | None:
    """Bir git yol dizesini repo köküne göre normalize eder.

    Repo dışına çıkan (path traversal veya repo dışına işaret eden symlink
    hedefi) veya artık var olmayan/dizin olan girdiler için None döner.
    """
    normalized = rel.replace("\\", "/").strip()
    if not normalized:
        return None
    candidate = (root / normalized).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    if not candidate.is_file():
        return None
    return candidate


def collect_repository_candidate_files(root: Path) -> dict[str, Any]:
    """Secret taraması için gerçek repository yüzeyini Git'ten türetir.

    Aday kapsamı: tracked dosyalar + stage edilmiş yeni/değiştirilmiş dosyalar +
    untracked ama `.gitignore` kapsamına girmeyen dosyalar. `.gitignore`
    kapsamındaki runtime log/cache/venv/coverage çalışma dosyaları bu üç
    listenin hiçbirinde görünmez, dolayısıyla asla taranmaz. Aynı yol birden
    fazla listede görünüyorsa tek kez taranır.
    """
    root = root.resolve()

    tracked = _git_lines(["ls-files"], root)
    staged = _git_lines(["diff", "--cached", "--name-only", "--diff-filter=ACMR"], root)
    untracked = _git_lines(["ls-files", "--others", "--exclude-standard"], root)

    candidates: dict[str, Path] = {}
    for rel in (*tracked, *staged, *untracked):
        normalized = rel.replace("\\", "/").strip()
        if not normalized or normalized in candidates:
            continue
        resolved = _resolve_candidate(root, normalized)
        if resolved is None:
            continue
        candidates[normalized] = resolved

    return {
        "tracked_candidate_count": len(set(tracked)),
        "staged_candidate_count": len(set(staged)),
        "untracked_non_ignored_candidate_count": len(set(untracked)),
        "unique_scanned_candidate_count": len(candidates),
        "candidates": candidates,
    }


def _count_ignored_files_best_effort(root: Path) -> int | None:
    """Bilgi amaçlı: `.gitignore` nedeniyle atlanan dosya sayısı.

    Bu metrik yalnız raporlama amaçlıdır (section 6: "mümkünse yalnız toplam
    sayı olarak"); üretilemezse gate'i kırmızı yapmaz, None döner.
    """
    try:
        ignored = _git_lines(["ls-files", "--others", "--ignored", "--exclude-standard"], root)
    except GitCandidateListError:
        return None
    return len(set(ignored))


def is_env_file(path: Path) -> bool:
    name = path.name.lower()
    return name == ".env" or name.startswith(".env.")


def is_allowed_env_example(path: Path) -> bool:
    name = path.name.lower()
    return name.endswith(".example") or ".example." in name or name in {".env.template", ".env.sample", ".env.docker.example", ".env.production.example"}


def is_probably_text(path: Path) -> bool:
    if path.suffix.lower() in TEXT_EXTS:
        return True
    return path.name.lower().startswith(".env") or path.name.lower() in {"docker-compose.yml", "dockerfile", "makefile"}


def safe_read(path: Path) -> str | None:
    try:
        data = path.read_bytes()
    except Exception:
        return None
    if b"\x00" in data[:4096]:
        return None
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            return data.decode("cp1254")
        except UnicodeDecodeError:
            return data.decode("utf-8", errors="ignore")


def looks_placeholder(value: str) -> bool:
    v = value.strip().strip('"\'').strip()
    lower = v.lower()
    if any(word in lower for word in PLACEHOLDER_WORDS):
        return True
    if lower.startswith("${") or lower.startswith("%") or lower.startswith("os.environ"):
        return True
    if "<" in v and ">" in v:
        return True
    # BYS360 Phase 5 secret-gate false-positive fix (2026-07-26): real API
    # keys/tokens/passwords/DB URLs are conventionally a single unbroken
    # token and never contain literal whitespace. A value with a space or
    # tab is far more likely to be natural-language documentation/glossary
    # text (e.g. a UI-terminology dictionary entry) than a credential; this
    # mirrors the existing "<...>" placeholder-bracket check above rather
    # than targeting any specific word, key, or file path.
    if " " in v or "\t" in v:
        return True
    return len(v) < 16 and not ("://" in v and "@" in v)


def is_non_sensitive_database_url(value: str) -> bool:
    v = value.strip().strip('"\'').strip()
    return bool(SQLITE_DSN_RE.match(v))


def looks_env_reference(line: str, value: str = "") -> bool:
    hay = f"{line} {value}"
    return any(marker in hay for marker in ENV_REFERENCE_MARKERS)


def looks_regex_or_scanner(line: str, path: Path) -> bool:
    lower_path = str(path).replace("\\", "/").lower()
    if ("/scripts/security/" in lower_path or "/scripts/quality/" in lower_path) and any(marker.lower() in line.lower() for marker in REGEX_OR_SCANNER_MARKERS):
        return True
    return any(marker.lower() in line.lower() for marker in REGEX_OR_SCANNER_MARKERS)


def add_warning(warnings: list[dict[str, Any]], item: dict[str, Any]) -> None:
    """Always records the warning. Report-readability truncation (if any) is
    applied once, at serialization time in run() -- see TD-CAND-007: this
    function used to silently cap at 80 entries here, which froze the
    reported warning_count at exactly 80 forever once the true match count
    grew past that threshold, masking the real (and fully reproducible,
    given a fixed working tree) total instead of reporting it."""
    warnings.append(item)


def strip_inline_comment(value: str) -> str:
    """See INLINE_COMMENT_RE: cuts a value at the first whitespace-preceded
    `#`, leaving a bare trailing `#fragment` (no preceding space) intact."""
    m = INLINE_COMMENT_RE.search(value)
    if m is None:
        return value.strip()
    return value[: m.start()].strip()


def classify_assignment_value(
    *,
    key: str,
    value: str,
    line: str,
    lineno: int,
    rel: str,
    path: Path,
    findings: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
) -> None:
    """Shared classification for a sensitive KEY's extracted value, used by
    both the quoted (ASSIGN_RE/DICT_ASSIGN_RE) and unquoted
    (UNQUOTED_ASSIGN_RE) assignment paths in scan_file() so the two never
    drift apart (BYS360 Phase 10I)."""
    if key in DATABASE_URL_KEYS:
        if is_non_sensitive_database_url(value):
            add_warning(warnings, {
                "type": "database_url_reference_or_placeholder",
                "path": rel,
                "line": lineno,
                "detail": f"{key} bir sqlite DSN'i; kullanıcı adı/parola içermez, uyarı olarak izlendi.",
            })
            return
        if "://" in value:
            # A connection-string-shaped DATABASE_URL/SQLALCHEMY_DATABASE_URI
            # value is already fully classified by the dedicated DB_URL_RE
            # scan earlier in scan_file(), which extracts and evaluates the
            # actual embedded password. Re-evaluating the whole URL string
            # here would either double-report the same real secret or
            # false-positive on a safe placeholder URL such as
            # postgresql://user:password@db:5432/bys360 (BYS360 Phase 10I).
            return
    if looks_placeholder(value) or looks_env_reference(line, value) or looks_regex_or_scanner(line, path):
        add_warning(warnings, {
            "type": "secret_reference_or_placeholder",
            "path": rel,
            "line": lineno,
            "detail": f"{key} için referans/placeholder değer bulundu.",
        })
        return
    # Local test defaults are warnings, not production secret findings.
    lower_path = rel.lower()
    if lower_path.startswith("tests/") and ("localhost" in value.lower() or "127.0.0.1" in value.lower() or "test" in value.lower()):
        add_warning(warnings, {
            "type": "test_secret_like_default",
            "path": rel,
            "line": lineno,
            "detail": f"{key} için test/local varsayılan değer bulundu.",
        })
        return
    findings.append({
        "type": "hardcoded_secret_value",
        "path": rel,
        "line": lineno,
        "detail": f"{key} için kaynak kodda gömülü değer bulundu; değer rapora yazılmadı.",
    })


def scan_file(path: Path, root: Path, findings: list[dict[str, Any]], warnings: list[dict[str, Any]]) -> None:
    rel = str(path.relative_to(root)).replace("\\", "/")
    if is_env_file(path) and not is_allowed_env_example(path):
        findings.append({
            "type": "runtime_env_file_in_source_tree",
            "path": rel,
            "line": 1,
            "detail": "Gerçek .env dosyası kaynak klasöründe bulunmamalıdır; değer rapora yazılmadı.",
        })
        return

    if not is_probably_text(path):
        return
    text = safe_read(path)
    if text is None:
        return

    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("//"):
            continue

        # Raw PEM/OpenSSH/PGP private-key header, independent of the KEY=value
        # assignment machinery above (see PRIVATE_KEY_HEADER_RE definition).
        # Scanner/test code that merely documents or matches this pattern as a
        # string (e.g. a regex literal in another quality-gate script, or a
        # fixture line marked with the pre-existing "hardcoded_secret" comment
        # convention used throughout tests/quality/test_bys360_secret_repo_gate.py)
        # is excluded via the same looks_regex_or_scanner() used elsewhere.
        if PRIVATE_KEY_HEADER_RE.search(line) and not looks_regex_or_scanner(line, path):
            findings.append({
                "type": "hardcoded_private_key_material",
                "path": rel,
                "line": lineno,
                "detail": "Kaynak kodda gömülü özel anahtar (private key) materyali bulundu; değer rapora yazılmadı.",
            })

        # Database URLs with embedded password. Regex/test/scanner placeholders are warnings, real values are findings.
        for m in DB_URL_RE.finditer(line):
            password = m.group(2)
            if looks_placeholder(password) or looks_env_reference(line, password) or looks_regex_or_scanner(line, path):
                add_warning(warnings, {
                    "type": "database_url_reference_or_placeholder",
                    "path": rel,
                    "line": lineno,
                    "detail": "Veritabanı URL ifadesi gerçek secret gibi görünmüyor; uyarı olarak izlendi.",
                })
            else:
                findings.append({
                    "type": "database_url_with_password",
                    "path": rel,
                    "line": lineno,
                    "detail": "Veritabanı bağlantısında gömülü parola bulundu; değer rapora yazılmadı.",
                })

        # Literal assignments/dicts for sensitive keys (quoted Python/JSON
        # style: KEY = "value" / "KEY": "value").
        quoted_match_found = False
        for regex in (ASSIGN_RE, DICT_ASSIGN_RE):
            for m in regex.finditer(line):
                quoted_match_found = True
                classify_assignment_value(
                    key=m.group("key").upper(),
                    value=m.group("value"),
                    line=line,
                    lineno=lineno,
                    rel=rel,
                    path=path,
                    findings=findings,
                    warnings=warnings,
                )

        # Standard unquoted .env-format assignments (KEY=value, optionally
        # `export`-prefixed) -- scoped to .env/.env.* files only, where a
        # bare unquoted word is the actual valid (and only) syntax for a
        # value. Every other text type this scanner reads (.py, .yml,
        # .json, ...) legitimately contains countless unquoted `key = expr`
        # constructs -- Python variable assignments, dict keys with
        # variable values, YAML mappings -- that are not, and structurally
        # cannot be, a literal secret value the way an unquoted .env line
        # is; a real embedded secret in source code requires a quoted
        # string literal, which ASSIGN_RE/DICT_ASSIGN_RE already cover.
        # Also only attempted when no quoted assignment already matched
        # this line, so a well-formed quoted .env-style line (unusual but
        # not invalid) keeps going through the path above (BYS360 Phase 10I).
        if is_env_file(path) and not quoted_match_found:
            unquoted_match = UNQUOTED_ASSIGN_RE.match(stripped)
            if unquoted_match:
                raw_value = unquoted_match.group("value")
                if raw_value[:1] not in ("\"", "'"):
                    classify_assignment_value(
                        key=unquoted_match.group("key").upper(),
                        value=strip_inline_comment(raw_value),
                        line=line,
                        lineno=lineno,
                        rel=rel,
                        path=path,
                        findings=findings,
                        warnings=warnings,
                    )

def scan_blocked_repo_artifacts(candidates: dict[str, Path], findings: list[dict[str, Any]]) -> None:
    """Kaynak agacinda bulunmamasi gereken local/hassas artefaktlari yakalar.

    Tarama kapsamı repository aday dosya listesidir (bkz. `collect_repository_
    candidate_files`) -- fiziksel dizin rglob taraması yapılmaz. Bir dosya bu
    listede görünüyorsa (tracked/staged/untracked-non-ignored) hijyen kuralları
    uygulanır; `.gitignore` kapsamındaki dosyalar zaten bu listeye hiç girmez.
    """
    reported_dirs: set[str] = set()
    for rel, path in candidates.items():
        parts = rel.split("/")
        lower_parts = [p.lower() for p in parts]

        blocked_parent = next((p for p in lower_parts[:-1] if p in BLOCKED_REPO_DIR_NAMES), None)
        if blocked_parent:
            idx = lower_parts.index(blocked_parent)
            parent = "/".join(parts[: idx + 1])
            if parent not in reported_dirs:
                reported_dirs.add(parent)
                findings.append({
                    "type": "blocked_repo_directory",
                    "path": parent,
                    "line": 0,
                    "detail": "Kaynak paketinde bulunmamasi gereken local/runtime klasor tespit edildi.",
                })
            continue

        suffix = path.suffix.lower()
        if suffix in BLOCKED_REPO_SUFFIXES:
            findings.append({
                "type": "blocked_repo_file",
                "path": rel,
                "line": 0,
                "detail": f"Kaynak paketinde bulunmamasi gereken dosya uzantisi tespit edildi: {suffix}",
            })
            continue

        for pattern in BLOCKED_REPO_NAME_PATTERNS:
            if pattern is ENV_FILE_BLOCK_RE and is_allowed_env_example(path):
                # .env.example / .env.sample / diger izinli sablon dosyalari gercek
                # secret icermez; bu blok yalnizca gercek .env* dosyalarini hedefler.
                continue
            if pattern.search(rel):
                findings.append({
                    "type": "blocked_repo_file_name",
                    "path": rel,
                    "line": 0,
                    "detail": "Kaynak paketinde bulunmamasi gereken dosya adi/deseni tespit edildi.",
                })
                break


def run(root: Path) -> dict[str, Any]:
    root = root.resolve()
    findings: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    candidate_info = collect_repository_candidate_files(root)
    candidates: dict[str, Path] = candidate_info["candidates"]

    scan_blocked_repo_artifacts(candidates, findings)

    for path in candidates.values():
        scan_file(path, root, findings, warnings)

    # TD-CAND-007: warning_count must always be the TRUE total match count,
    # fully reproducible given a fixed working tree (see bys360_secret_repo_gate
    # tests: test_warning_count_reports_true_total_not_display_cap). Only the
    # DISPLAYED warning list (report readability) is truncated -- the count
    # itself is never capped, so it can no longer silently freeze at the old
    # 80-item display limit once the true match count grows past it.
    warning_count_real = len(warnings)
    display_limit = 80
    if warning_count_real > display_limit:
        displayed_warnings = warnings[:display_limit]
        displayed_warnings.append({
            "type": "warning_output_truncated",
            "path": "-",
            "line": 0,
            "detail": f"Uyarı listesi rapor okunabilirliği için {display_limit} kayıtla sınırlandı. Toplam uyarı: {warning_count_real}",
        })
    else:
        displayed_warnings = warnings

    reports_dir = root / "reports" / "quality"
    reports_dir.mkdir(parents=True, exist_ok=True)
    report_path = reports_dir / "BYS360_SECRET_REPO_GATE_V1_REPORT.json"
    result: dict[str, Any] = {
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "ok": len(findings) == 0,
        "scanned_file_count": candidate_info["unique_scanned_candidate_count"],
        "finding_count": len(findings),
        "warning_count": warning_count_real,
        "git_candidate_classification": {
            "tracked_candidate_count": candidate_info["tracked_candidate_count"],
            "staged_candidate_count": candidate_info["staged_candidate_count"],
            "untracked_non_ignored_candidate_count": candidate_info["untracked_non_ignored_candidate_count"],
            "unique_scanned_candidate_count": candidate_info["unique_scanned_candidate_count"],
            "skipped_ignored_file_count": _count_ignored_files_best_effort(root),
        },
        "findings": findings,
        "warnings": displayed_warnings,
        "report": str(report_path),
        "next_actions": [
            "finding_count 0 ise P0 güvenlik/repo hijyen gate tamamlanmış kabul edilebilir.",
            "Gerçek secret dosyaları kaynak klasöründe tutulmamalı; .env sadece local/canlı ortamda dışarıdan sağlanmalıdır.",
            "warning_count kalite kapısını düşürmez; örnek dosya/env referansı/regex tarama kalıbı olarak izlenir.",
            "Tarama kapsamı Git'in tracked/staged/untracked-non-ignored siniflandirmasidir; "
            ".gitignore kapsamındaki runtime/cache/venv/coverage dosyaları asla taranmaz.",
        ],
    }
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main(argv: list[str]) -> int:
    root = Path.cwd()
    if "--root" in argv:
        idx = argv.index("--root")
        if idx + 1 < len(argv):
            root = Path(argv[idx + 1])
    try:
        result = run(root)
    except GitCandidateListError as exc:
        # Git tabanli aday listesi uretilemedi: sahte bir PASS/ok:true JSON'u
        # BASMADAN, acikca ve non-zero exit ile basarisiz ol.
        print(f"SECRET REPO GATE HATA: repository aday dosya listesi uretilemedi: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({
        "ok": result["ok"],
        "finding_count": result["finding_count"],
        "warning_count": result["warning_count"],
        "report": result["report"],
    }, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
