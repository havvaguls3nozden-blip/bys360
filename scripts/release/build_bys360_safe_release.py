from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from datetime import UTC, datetime
from pathlib import Path

# scan_bys360_release_secrets.py is a sibling module in this same directory
# (scripts/release/) -- imported directly rather than re-implemented, for
# the same reason WheelhouseIntegrityError's docstring gives for not
# re-implementing wheelhouse verification here: a second, potentially-
# diverging copy of secret-scanning logic is worse than importing the one
# real implementation. sys.path is adjusted explicitly (not relying on
# "python <script.py>" auto-inserting the script's own directory) so this
# import also works when the module is imported rather than run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import scan_bys360_release_secrets as secret_scanner  # noqa: E402

PACKAGE = "BYS360_SAFE_RELEASE_BUILDER_PHASE2_V3_DETERMINISTIC"
SCHEMA_VERSION = 2

# Handover-grade "FULL" build mode (candidate/cutover/rollback architecture
# wave, 2026-08-25): an opt-in extension, triggered only when --wheelhouse-dir
# is supplied. Legacy callers that never pass the new flags get byte-for-byte
# the same schema_version=2 manifest/behavior as before -- see main() and
# write_manifest(). VALID_SCHEMA_VERSIONS is what verify_package() accepts.
SCHEMA_VERSION_FULL = 3
VALID_SCHEMA_VERSIONS = (SCHEMA_VERSION, SCHEMA_VERSION_FULL)
FULL_BUILD_PYTHON_REQUIREMENT = "3.12"
FULL_BUILD_PLATFORM_TARGET = "win_amd64"
FULL_BUILD_ARCHITECTURE = "x86_64"

FORBIDDEN_DIR_PARTS = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".idea", ".vscode", ".dart_tool",
    "instance", "logs", "uploads", "reports", "backups", "backup", "releases",
    "payload", "overlay_payload", "_security_quarantine", "_cleanup_quarantine", "_local_secrets",
    # BYS360 deterministic-package-builder hardening (2026-08-23): forensically
    # confirmed zero app/-import dependency before being added -- see
    # scripts/release/build_bys360_safe_release.py test suite and the wave's
    # forensic-comparison + include/exclude-contract agent findings.
    ".github", "tests", "mobile_flutter", ".codex", ".claude",
    # NOTE: "archive" is intentionally NOT a bare entry here -- see
    # _is_forbidden_archive_directory_segment() below. A flat membership
    # check on this set would have matched ANY path segment literally named
    # "archive", including the real, git-tracked Flask template directory
    # app/templates/performance/archive/ (a live feature, not backup/
    # release-archive storage) -- confirmed by the FINAL package required-
    # content audit (2026-08-24): 5 legitimate template files were silently
    # dropped from every package this builder produced.
}

# "archive" is forbidden everywhere EXCEPT under app/ -- repository-grounded:
# app/ is pure application source (routes/models/services/templates/static),
# never backup/release-archive storage, and a full-repo forensic scan found
# exactly one legitimate exception (app/templates/performance/archive/, 5
# files) against three genuinely-historical roots that must stay excluded
# (docs/archive/, reports/archive/, scripts/archive/ -- 501 files total).
def _is_forbidden_archive_directory_segment(parts: list[str]) -> bool:
    if not parts:
        return False
    if parts[0].lower() == "app":
        return False
    return "archive" in (p.lower() for p in parts)


# Real secret environment files (.env, .env.local, .env.production, ...)
# remain forbidden. Operator-safe example/template files are explicitly
# allowlisted by exact basename -- an allowlist, not a broadened regex, so
# no other real secret variant can ever be accidentally permitted alongside
# them. Confirmed exhaustive against this repository's full tracked tree:
# these are the only two `.env*` files tracked anywhere (2026-08-24 scan).
ALLOWED_ENV_TEMPLATE_BASENAMES = {".env.example", ".env.docker.example"}
_ENV_FILE_PATTERN = re.compile(r"(^|/|\\)\.env($|\.)", re.I)


def _is_forbidden_env_file(n: str) -> bool:
    if not _ENV_FILE_PATTERN.search(n):
        return False
    basename = n.rsplit("/", 1)[-1]
    return basename.lower() not in ALLOWED_ENV_TEMPLATE_BASENAMES
FORBIDDEN_SUFFIXES = {
    ".sqlite3", ".sqlite", ".db", ".dump", ".bak", ".backup", ".old", ".orig",
    ".log", ".pyc", ".pyo", ".key", ".pem", ".p12", ".pfx", ".ppk", ".jks", ".keystore",
    # Ported from scripts/security/build_bys360_secure_release_v1_5.py (now
    # deprecated in favor of this builder) -- an accidentally-committed
    # archive blob has no legitimate reason to ship inside a release package.
    ".zip", ".7z", ".rar",
}
FORBIDDEN_NAME_PATTERNS = (
    # .env handling lives in _is_forbidden_env_file() (allowlist-based), not here.
    re.compile(r"\.gitignore\.bak", re.I),
    re.compile(r"\.bak_", re.I),
    re.compile(r"disabled_by_rollback", re.I),
    re.compile(r"clean_package_manifest.*\.json$", re.I),
)
# OS-metadata artifacts: zero legitimate production purpose, ported from the
# same forensic comparison (secure_release_v1_5 already blocked .DS_Store).
FORBIDDEN_EXACT_NAMES = {".ds_store", "thumbs.db"}

REQUIRED_PACKAGE_PATH_PREFIXES = (
    "app/", "migrations/", "requirements.txt", "wsgi.py", "run_server.py", "config.py", "DEPLOYMENT.md",
)

# Fixed, uniform zip metadata applied to every packaged entry -- see
# _fixed_date_time()/build_filtered_zip(): archive bytes must not depend on
# the build machine's OS, timezone, or on-disk file permissions.
ZIP_EXTERNAL_ATTR = (0o100644 & 0xFFFF) << 16
ZIP_CREATE_SYSTEM = 0


class GitDiscoveryError(RuntimeError):
    """Git-based source discovery could not be established.

    BYS360 deterministic-package-builder hardening (2026-08-23): the
    production FULL builder must never silently fall back to an arbitrary
    filesystem walk (Path.rglob) when git is unavailable or fails -- that
    fallback is non-deterministic (OS-dependent iteration order) and not
    provably symlink-safe. If deterministic git source discovery cannot be
    established, the build must fail closed, not degrade quietly.
    """


class DirtySourceError(RuntimeError):
    """The requested source commit does not match HEAD, or the tracked
    working tree is not clean. A production release package must never be
    built from state that could silently differ from its claimed source SHA."""


class WheelhouseIntegrityError(RuntimeError):
    """The offline wheelhouse directory does not match its own build report
    (missing wheel, extra/unexpected wheel, or a wheel whose live SHA256
    differs from what the report recorded). A FULL package must never bundle
    a wheelhouse that cannot be proven identical to the one that actually
    passed offline-install acceptance -- see
    scripts/release/build_bys360_wheelhouse.py, which produces the report
    this class validates against, and never re-implement that validation
    here as a second, potentially-diverging copy."""


class MigrationHeadError(RuntimeError):
    """The migrations/ tree does not resolve to exactly one Alembic head."""


class SecretScanError(RuntimeError):
    """The assembled FULL release tree failed its own secret gate.

    Coordinator addition (2026-08-25, schema-contract-drift wave close-out,
    section 5: "SECRET SCANNING MUST NOT REMAIN MANUAL ONLY"). Raised when
    scan_bys360_release_secrets.py finds one or more real-looking secrets in
    the fully assembled release tree (extracted from the just-built zip, so
    this is exactly what would ship -- not a proxy check against source
    files that might differ from the final archive). A FULL package must
    never be finalized if its own contents fail this gate; see main()'s
    handling, which deletes the just-built zip and returns non-zero rather
    than writing a success manifest/report."""


def normalize(name: str) -> str:
    return name.replace("\\", "/").lstrip("/")


def is_forbidden_archive_name(name: str) -> tuple[bool, str]:
    n = normalize(name)
    parts = [p for p in n.split("/") if p]
    lower_parts = [p.lower() for p in parts]
    for part in lower_parts:
        if part in FORBIDDEN_DIR_PARTS:
            return True, f"yasak klasor parcasi: {part}"
    if _is_forbidden_archive_directory_segment(parts):
        return True, "yasak klasor parcasi: archive (app/ disinda)"
    base = parts[-1] if parts else n
    if base.lower() in FORBIDDEN_EXACT_NAMES:
        return True, f"yasak dosya adi: {base}"
    suffix = Path(base).suffix.lower()
    if suffix in FORBIDDEN_SUFFIXES:
        return True, f"yasak dosya uzantisi: {suffix}"
    if _is_forbidden_env_file(n):
        return True, "yasak dosya adi deseni: gercek .env dosyasi (sablon degil)"
    for pattern in FORBIDDEN_NAME_PATTERNS:
        if pattern.search(n):
            return True, f"yasak dosya adi deseni: {pattern.pattern}"
    return False, ""


def is_unsafe_archive_path(name: str) -> bool:
    """Defensive path-traversal / unsafe-name check, used both when building
    (defense in depth on top of git-tracked-only discovery) and in --verify
    (where entries come from an arbitrary, potentially tampered zip)."""
    n = name.replace("\\", "/")
    if not n or n != normalize(n):
        return True
    if n.startswith("/") or n.startswith("../") or "/../" in n or n.endswith("/..") or n == "..":
        return True
    if re.match(r"^[A-Za-z]:", n):
        return True
    return "\x00" in n


def _run_git(args: list[str], root: Path, *, binary: bool = False) -> subprocess.CompletedProcess:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            capture_output=True,
            text=not binary,
        )
    except FileNotFoundError as exc:
        raise GitDiscoveryError(f"git bulunamadi: {exc}") from exc
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", "replace")
        raise GitDiscoveryError(f"git {' '.join(args)} basarisiz (exit={exc.returncode}): {stderr.strip()}") from exc


def resolve_source_sha(root: Path, requested_sha: str | None) -> str:
    """Resolves and validates the commit this build claims to be from.

    No filesystem fallback: any git failure here is fatal (GitDiscoveryError).
    If requested_sha is given it must equal actual HEAD exactly -- a
    production release must never silently package a commit different from
    the one it claims (see CRITICAL DESIGN CORRECTION #2). If omitted, HEAD
    is auto-resolved and used directly; it is never hardcoded or accepted
    from an untrusted, unverified override.
    """
    actual_head = _run_git(["rev-parse", "HEAD"], root).stdout.strip()
    if not re.fullmatch(r"[0-9a-f]{40}", actual_head):
        raise GitDiscoveryError(f"git rev-parse HEAD beklenmeyen deger dondurdu: {actual_head!r}")
    if requested_sha is not None:
        if not re.fullmatch(r"[0-9a-f]{40}", requested_sha.lower()):
            raise DirtySourceError(f"--source-sha gecersiz format: {requested_sha!r}")
        if requested_sha.lower() != actual_head.lower():
            raise DirtySourceError(
                f"--source-sha ({requested_sha}) mevcut HEAD ile eslesmiyor ({actual_head}); "
                "paket yalnizca gercekten checkout edilmis commit'ten uretilebilir."
            )
    return actual_head


def assert_clean_tracked_worktree(root: Path) -> None:
    """Fails closed if any tracked file is staged or modified.

    Untracked files are explicitly allowed here (status code '??') and have
    zero effect on build output -- discovery is git-ls-files-based, so an
    untracked file is never a build candidate regardless of worktree state.
    A tracked file with uncommitted changes, however, could make the on-disk
    bytes diverge from the claimed source SHA's committed tree -- that must
    always fail the build, with no override flag.
    """
    status = _run_git(["status", "--porcelain=v1"], root).stdout
    dirty = [line for line in status.splitlines() if line and not line.startswith("??")]
    if dirty:
        raise DirtySourceError(
            "tracked working tree temiz degil (staged/degistirilmis dosyalar var), "
            f"build FAIL_CLOSED: {dirty[:10]}"
        )


def resolve_commit_epoch(root: Path, sha: str) -> int:
    out = _run_git(["show", "-s", "--format=%ct", sha], root).stdout.strip()
    return int(out)


def _fixed_date_time(epoch: int) -> tuple[int, int, int, int, int, int]:
    t = time.gmtime(epoch)
    year = max(t.tm_year, 1980)
    return (year, t.tm_mon, t.tm_mday, t.tm_hour, t.tm_min, t.tm_sec)


def _git_ls_files(root: Path) -> list[str]:
    """Sole source-of-truth file list: git-tracked files only. Raises
    GitDiscoveryError on any failure -- see GitDiscoveryError docstring."""
    _run_git(["rev-parse", "--is-inside-work-tree"], root)
    result = _run_git(["ls-files", "-z"], root, binary=True)
    return sorted(
        item.decode("utf-8", errors="replace")
        for item in result.stdout.split(b"\0")
        if item
    )


def iter_source_files(root: Path) -> tuple[str, list[tuple[Path, str]], list[dict[str, str]]]:
    git_files = _git_ls_files(root)
    included: list[tuple[Path, str]] = []
    excluded: list[dict[str, str]] = []

    for rel in git_files:
        rel = normalize(rel)
        forbidden, reason = is_forbidden_archive_name(rel)
        if forbidden:
            excluded.append({"path": rel, "reason": reason})
            continue
        if is_unsafe_archive_path(rel):
            excluded.append({"path": rel, "reason": "yasak: guvensiz/traversal yolu"})
            continue
        path = root / rel
        if not path.is_file() or path.is_symlink():
            excluded.append({"path": rel, "reason": "yasak: dosya degil veya sembolik link"})
            continue
        included.append((path, rel))

    included.sort(key=lambda item: item[1])
    return "git-ls-files-filtered", included, excluded


def sha256_of_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_wheelhouse_report(report_path: Path) -> dict:
    if not report_path.is_file():
        raise WheelhouseIntegrityError(
            f"wheelhouse build raporu bulunamadi: {report_path} -- once "
            "scripts/release/build_bys360_wheelhouse.py --clean calistirin."
        )
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise WheelhouseIntegrityError(f"wheelhouse raporu gecersiz JSON: {exc}") from exc
    if report.get("ok") is not True:
        raise WheelhouseIntegrityError(
            f"wheelhouse raporu basarisiz derlemeyi gosteriyor (ok={report.get('ok')!r}): {report_path}"
        )
    if "manifest" not in report or not isinstance(report["manifest"], list):
        raise WheelhouseIntegrityError(f"wheelhouse raporunda 'manifest' listesi yok: {report_path}")
    return report


def verify_and_collect_wheelhouse_files(
    wheelhouse_dir: Path, report: dict
) -> list[tuple[Path, str]]:
    """Cross-checks the live wheelhouse directory against its own build
    report (not against requirements.lock a second time -- the wheelhouse
    builder already did that verification; this re-detects drift/tampering
    of the directory *since* that report was written). Fails closed on any
    missing wheel, any unexpected extra .whl file, or any hash mismatch."""
    if not wheelhouse_dir.is_dir():
        raise WheelhouseIntegrityError(f"wheelhouse dizini bulunamadi: {wheelhouse_dir}")

    expected: dict[str, dict] = {entry["filename"]: entry for entry in report["manifest"]}
    actual_files = sorted(p for p in wheelhouse_dir.iterdir() if p.is_file())
    actual_names = {p.name for p in actual_files}

    missing = sorted(set(expected) - actual_names)
    if missing:
        raise WheelhouseIntegrityError(f"wheelhouse'ta eksik wheel dosyalari: {missing}")

    unexpected = sorted(n for n in actual_names if n not in expected)
    if unexpected:
        raise WheelhouseIntegrityError(f"wheelhouse'ta beklenmeyen ekstra dosyalar: {unexpected}")

    collected: list[tuple[Path, str]] = []
    for path in actual_files:
        entry = expected[path.name]
        live_digest = sha256_of_file(path)
        if live_digest != entry["sha256"]:
            raise WheelhouseIntegrityError(
                f"wheelhouse dosyasi rapor sonrasi degismis (SHA256 uyusmuyor): {path.name}"
            )
        collected.append((path, f"wheelhouse/{path.name}"))

    if len(collected) != len(expected):
        raise WheelhouseIntegrityError(
            f"wheelhouse dosya sayisi rapor ile eslesmiyor: beklenen={len(expected)} bulunan={len(collected)}"
        )
    collected.sort(key=lambda item: item[1])
    return collected


def scan_assembled_tree_for_secrets(zip_path: Path) -> dict:
    """Extracts the just-built FULL package zip to a disposable temp
    directory and runs scan_bys360_release_secrets.scan_path() against it --
    the actual assembled tree (application, migrations, runtime/release
    scripts, operator docs, manifest/checksum inventory, wheelhouse
    filenames/metadata, allowlisted example/template files), not a proxy
    check against the source tree that might diverge from what actually
    landed in the archive. Raises SecretScanError on any finding; the temp
    directory is always removed, success or failure. Returns a small,
    secret-free summary dict (never the actual findings' redacted text --
    scan_bys360_release_secrets.py already redacts values, but this
    function's return value is what ends up in the release manifest, so it
    is deliberately kept to counts/status only)."""
    temp_dir = Path(tempfile.mkdtemp(prefix="bys360_full_release_secret_scan_"))
    try:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(temp_dir)
        findings, files_scanned = secret_scanner.scan_path(temp_dir)
        if findings:
            by_category: dict[str, int] = {}
            for f in findings:
                by_category[f.category] = by_category.get(f.category, 0) + 1
            summary = ", ".join(f"{k}={v}" for k, v in sorted(by_category.items()))
            raise SecretScanError(
                f"assembled FULL release tree failed secret gate: {len(findings)} finding(s) "
                f"across {files_scanned} file(s) scanned ({summary}). First finding: "
                f"[{findings[0].severity}] [{findings[0].category}] {findings[0].file} -- {findings[0].detail}"
            )
        return {
            "secret_scan_status": "PASS",
            "secret_scan_findings": 0,
            "secret_scan_files_scanned": files_scanned,
            "secret_scan_scope": "assembled_release_tree",
        }
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def resolve_migration_head(root: Path) -> str:
    """Uses Alembic's own ScriptDirectory against migrations/ -- the same
    mechanism scripts/windows/prepare_bys360_candidate.ps1's
    Test-CandidateMigrationHead uses -- rather than parsing revision/
    down_revision out of migration files by hand. Requires alembic to be
    importable in whatever Python runs this builder."""
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory
    except ImportError as exc:
        raise MigrationHeadError(f"alembic import edilemedi: {exc}") from exc

    migrations_dir = root / "migrations"
    cfg = Config()
    cfg.set_main_option("script_location", str(migrations_dir))
    script = ScriptDirectory.from_config(cfg)
    heads = script.get_heads()
    if len(heads) != 1:
        raise MigrationHeadError(f"migrations/ tek bir head'e cozulmuyor: {heads!r}")
    return heads[0]


def build_filtered_zip(
    root: Path, output: Path, source_sha: str, extra_files: list[tuple[Path, str]] | None = None
) -> tuple[str, list[tuple[Path, str]], list[dict[str, str]]]:
    source, included, excluded = iter_source_files(root)
    if extra_files:
        tracked_names = {rel for _, rel in included}
        collided = [rel for _, rel in extra_files if rel in tracked_names]
        if collided:
            raise DirtySourceError(f"extra_files git-tracked yollarla catisiyor: {collided}")
        included = sorted(included + list(extra_files), key=lambda item: item[1])
    epoch = resolve_commit_epoch(root, source_sha)
    date_time = _fixed_date_time(epoch)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path, rel in included:
            info = zipfile.ZipInfo(filename=rel, date_time=date_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = ZIP_EXTERNAL_ATTR
            info.create_system = ZIP_CREATE_SYSTEM
            zf.writestr(info, path.read_bytes())
    return source, included, excluded


def scan_zip(zip_path: Path) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            forbidden, reason = is_forbidden_archive_name(info.filename)
            if forbidden:
                findings.append({"path": normalize(info.filename), "reason": reason})
            if is_unsafe_archive_path(normalize(info.filename)):
                findings.append({"path": normalize(info.filename), "reason": "yasak: guvensiz/traversal yolu"})
    return findings


def compute_sha256_manifest(zip_path: Path) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            digest = hashlib.sha256(zf.read(info)).hexdigest()
            pairs.append((normalize(info.filename), digest))
    pairs.sort(key=lambda item: item[0])
    return pairs


def sha256sums_text(pairs: list[tuple[str, str]]) -> str:
    return "".join(f"{digest}  {path}\n" for path, digest in pairs)


def write_manifest(
    *,
    manifest_path: Path,
    source_sha: str,
    included: list[tuple[Path, str]],
    excluded: list[dict[str, str]],
    sha256sums_filename: str,
    full_build: dict | None = None,
) -> dict:
    files = sorted(rel for _, rel in included)
    manifest = {
        "schema_version": SCHEMA_VERSION if full_build is None else SCHEMA_VERSION_FULL,
        "package": PACKAGE,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "source_sha": source_sha,
        "included_count": len(files),
        "files": files,
        "excluded_count": len(excluded),
        "excluded_sample": excluded[:200],
        "sha256sums_file": sha256sums_filename,
    }
    if full_build is not None:
        manifest["source_short_sha"] = source_sha[:12]
        manifest.update(full_build)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def verify_package(
    zip_path: Path,
    manifest_path: Path,
    sha256sums_path: Path,
    expected_source_sha: str | None = None,
) -> dict:
    findings: list[str] = []

    if not zip_path.is_file():
        return {"ok": False, "findings": [f"paket bulunamadi: {zip_path}"]}
    if not manifest_path.is_file():
        return {"ok": False, "findings": [f"manifest bulunamadi: {manifest_path}"]}
    if not sha256sums_path.is_file():
        return {"ok": False, "findings": [f"SHA256SUMS bulunamadi: {sha256sums_path}"]}

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": False, "findings": [f"manifest gecersiz JSON: {exc}"]}

    if manifest.get("schema_version") not in VALID_SCHEMA_VERSIONS:
        findings.append(f"beklenmeyen manifest schema_version: {manifest.get('schema_version')!r}")

    manifest_files = set(manifest.get("files", []))

    if manifest.get("schema_version") == SCHEMA_VERSION_FULL:
        wheelhouse_files_in_manifest = [f for f in manifest_files if f.startswith("wheelhouse/") and f.endswith(".whl")]
        expected_wheel_count = manifest.get("wheelhouse_file_count")
        if expected_wheel_count is None:
            findings.append("FULL paket manifest'inde wheelhouse_file_count alani yok")
        elif len(wheelhouse_files_in_manifest) != expected_wheel_count:
            findings.append(
                f"wheelhouse dosya sayisi manifest alanindan farkli: "
                f"wheelhouse_file_count={expected_wheel_count} pakette bulunan={len(wheelhouse_files_in_manifest)}"
            )
        if "requirements.lock" not in manifest_files:
            findings.append("FULL paket icin gerekli icerik eksik: requirements.lock")
        if manifest.get("secret_scan_status") != "PASS" or manifest.get("secret_scan_findings") != 0:
            findings.append(
                f"FULL paket secret gate temiz degil: secret_scan_status={manifest.get('secret_scan_status')!r} "
                f"secret_scan_findings={manifest.get('secret_scan_findings')!r}"
            )

    recorded_hashes: dict[str, str] = {}
    for line in sha256sums_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split("  ", 1)
        if len(parts) != 2:
            findings.append(f"SHA256SUMS satiri gecersiz format: {line!r}")
            continue
        digest, path = parts
        recorded_hashes[path] = digest

    if set(recorded_hashes) != manifest_files:
        findings.append("SHA256SUMS icerigi manifest dosya kumesiyle eslesmiyor")

    try:
        with zipfile.ZipFile(zip_path) as zf:
            zip_names = set(normalize(n) for n in zf.namelist())
            for info in zf.infolist():
                rel = normalize(info.filename)
                if is_unsafe_archive_path(rel):
                    findings.append(f"guvensiz/traversal yolu: {rel}")
                forbidden, reason = is_forbidden_archive_name(rel)
                if forbidden:
                    findings.append(f"yasak yol pakette bulundu ({reason}): {rel}")
                actual_digest = hashlib.sha256(zf.read(info)).hexdigest()
                expected_digest = recorded_hashes.get(rel)
                if expected_digest is None:
                    findings.append(f"beklenmeyen ekstra dosya (manifest disi): {rel}")
                elif actual_digest != expected_digest:
                    findings.append(f"SHA256 uyusmuyor: {rel}")
    except zipfile.BadZipFile as exc:
        return {"ok": False, "findings": [f"paket acilamadi: {exc}"]}

    missing = manifest_files - zip_names
    for rel in sorted(missing):
        findings.append(f"gerekli dosya eksik (manifest'te var, pakette yok): {rel}")

    for prefix in REQUIRED_PACKAGE_PATH_PREFIXES:
        if not any(f == prefix or f.startswith(prefix) for f in manifest_files):
            findings.append(f"gerekli icerik eksik: {prefix}")

    for excluded_root in ("tests/", "mobile_flutter/", ".codex/", ".claude/"):
        if any(f.startswith(excluded_root) for f in manifest_files):
            findings.append(f"yasak dizin pakette bulundu: {excluded_root}")

    source_sha = manifest.get("source_sha")
    if expected_source_sha is not None and source_sha != expected_source_sha:
        findings.append(
            f"source SHA metadata uyusmuyor: manifest={source_sha!r} beklenen={expected_source_sha!r}"
        )

    return {
        "ok": len(findings) == 0,
        "findings": findings,
        "source_sha": source_sha,
        "included_count": manifest.get("included_count"),
        "checked_file_count": len(zip_names),
    }


def _default_sidecar_paths(output: Path) -> tuple[Path, Path]:
    stem = output.name
    if stem.lower().endswith(".zip"):
        stem = stem[: -len(".zip")]
    manifest_path = output.parent / f"{stem}.manifest.json"
    sha256sums_path = output.parent / f"{stem}.sha256sums.txt"
    return manifest_path, sha256sums_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default=None, help="Build mode: zip cikti yolu.")
    parser.add_argument("--source-sha", default=None, help="Beklenen kaynak commit SHA (verilirse HEAD ile birebir eslesmeli).")
    parser.add_argument("--audit-only", action="store_true", help="Paketi yine uretir ve sadece paket icindeki yasakli dosyalari denetler.")
    parser.add_argument("--verify", default=None, help="Verify mode: dogrulanacak zip yolu.")
    parser.add_argument("--expected-source-sha", default=None, help="Verify mode: manifest source_sha bu deger ile eslesmeli.")
    parser.add_argument(
        "--wheelhouse-dir", default=None,
        help="FULL build mode tetikleyicisi: build/wheelhouse gibi bir dizin. Verilirse manifest "
             "schema_version=3 olur ve wheelhouse pakete dahil edilir.",
    )
    parser.add_argument("--wheelhouse-report", default=None, help="FULL build: wheelhouse build raporu yolu (varsayilan: reports/quality/BYS360_WHEELHOUSE_BUILD_REPORT.json).")
    parser.add_argument("--requirements-lock", default=None, help="FULL build: requirements.lock yolu (varsayilan: <root>/requirements.lock).")
    parser.add_argument("--candidate-script", default=None, help="FULL build: prepare_bys360_candidate.ps1 yolu.")
    parser.add_argument("--cutover-script", default=None, help="FULL build: cutover_bys360_candidate.ps1 yolu.")
    parser.add_argument("--rollback-script", default=None, help="FULL build: rollback_bys360_candidate.ps1 yolu.")
    parser.add_argument("--secret-scanner", default=None, help="FULL build: scan_bys360_release_secrets.py yolu.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()

    if args.verify:
        zip_path = Path(args.verify).resolve()
        manifest_path, sha256sums_path = _default_sidecar_paths(zip_path)
        result = verify_package(zip_path, manifest_path, sha256sums_path, args.expected_source_sha)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 1

    if not args.output:
        parser.error("--output gereklidir (build mode) veya --verify kullanin")

    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()

    full_build_extras: dict | None = None
    extra_files: list[tuple[Path, str]] = []

    try:
        source_sha = resolve_source_sha(root, args.source_sha)
        assert_clean_tracked_worktree(root)

        if args.wheelhouse_dir:
            wheelhouse_dir = Path(args.wheelhouse_dir).resolve()
            wheelhouse_report_path = (
                Path(args.wheelhouse_report).resolve() if args.wheelhouse_report
                else root / "reports" / "quality" / "BYS360_WHEELHOUSE_BUILD_REPORT.json"
            )
            requirements_lock_path = (
                Path(args.requirements_lock).resolve() if args.requirements_lock
                else root / "requirements.lock"
            )
            candidate_script_path = Path(args.candidate_script).resolve() if args.candidate_script else root / "scripts" / "windows" / "prepare_bys360_candidate.ps1"
            cutover_script_path = Path(args.cutover_script).resolve() if args.cutover_script else root / "scripts" / "windows" / "cutover_bys360_candidate.ps1"
            rollback_script_path = Path(args.rollback_script).resolve() if args.rollback_script else root / "scripts" / "windows" / "rollback_bys360_candidate.ps1"
            secret_scanner_path = Path(args.secret_scanner).resolve() if args.secret_scanner else root / "scripts" / "release" / "scan_bys360_release_secrets.py"

            for label, p in (
                ("requirements.lock", requirements_lock_path),
                ("candidate-script", candidate_script_path),
                ("cutover-script", cutover_script_path),
                ("rollback-script", rollback_script_path),
                ("secret-scanner", secret_scanner_path),
            ):
                if not p.is_file():
                    raise WheelhouseIntegrityError(f"FULL build icin gerekli dosya bulunamadi ({label}): {p}")

            wheelhouse_report = load_wheelhouse_report(wheelhouse_report_path)
            wheelhouse_files = verify_and_collect_wheelhouse_files(wheelhouse_dir, wheelhouse_report)
            extra_files = list(wheelhouse_files)

            migration_head = resolve_migration_head(root)

            full_build_extras = {
                "migration_head": migration_head,
                "python_requirement": FULL_BUILD_PYTHON_REQUIREMENT,
                "platform_target": FULL_BUILD_PLATFORM_TARGET,
                "architecture": FULL_BUILD_ARCHITECTURE,
                "requirements_lock_sha256": sha256_of_file(requirements_lock_path),
                "wheelhouse_file_count": wheelhouse_report["wheel_count"],
                "wheelhouse_total_bytes": wheelhouse_report["total_bytes"],
                "wheelhouse_identity_sha256": wheelhouse_report["wheelhouse_identity_sha256"],
                "candidate_script_sha256": sha256_of_file(candidate_script_path),
                "cutover_script_sha256": sha256_of_file(cutover_script_path),
                "rollback_script_sha256": sha256_of_file(rollback_script_path),
                "secret_scanner_sha256": sha256_of_file(secret_scanner_path),
            }

        source, included, excluded = build_filtered_zip(output=output, root=root, source_sha=source_sha, extra_files=extra_files)
    except (GitDiscoveryError, DirtySourceError, WheelhouseIntegrityError, MigrationHeadError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2

    findings = scan_zip(output)

    if full_build_extras is not None:
        try:
            secret_scan_result = scan_assembled_tree_for_secrets(output)
        except SecretScanError as exc:
            output.unlink(missing_ok=True)
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
            return 2
        full_build_extras.update(secret_scan_result)

    manifest_path, sha256sums_path = _default_sidecar_paths(output)
    sha_pairs = compute_sha256_manifest(output)
    sha256sums_path.write_text(sha256sums_text(sha_pairs), encoding="utf-8", newline="\n")

    if full_build_extras is not None:
        full_build_extras["package_file_count"] = len(included)
        full_build_extras["package_integrity_identity_sha256"] = hashlib.sha256(
            sha256sums_text(sha_pairs).encode("utf-8")
        ).hexdigest()

    manifest = write_manifest(
        manifest_path=manifest_path,
        source_sha=source_sha,
        included=included,
        excluded=excluded,
        sha256sums_filename=sha256sums_path.name,
        full_build=full_build_extras,
    )

    report_dir = root / "reports" / "quality"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "BYS360_SAFE_RELEASE_BUILDER_PHASE1_REPORT.json"
    legacy_manifest_path = report_dir / "BYS360_SAFE_RELEASE_BUILDER_PHASE1_MANIFEST.json"
    result = {
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "output": str(output),
        "source": source,
        "source_sha": source_sha,
        "included_count": manifest["included_count"],
        "excluded_count": len(excluded),
        "excluded_sample": excluded[:200],
        "ok": not findings,
        "finding_count": len(findings),
        "findings": findings[:200],
        "manifest": str(manifest_path),
        "sha256sums": str(sha256sums_path),
        "rule": "Release paketinde instance, sqlite/db/dump/log/bak/env/keystore gibi local veya hassas dosyalar bulunamaz.",
    }
    report_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    legacy_manifest_path.write_text(
        json.dumps({"included_count": manifest["included_count"], "excluded": excluded}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({
        "ok": result["ok"],
        "output": str(output),
        "finding_count": len(findings),
        "excluded_count": len(excluded),
        "source_sha": source_sha,
        "report": str(report_path),
        "manifest": str(manifest_path),
        "sha256sums": str(sha256sums_path),
    }, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
