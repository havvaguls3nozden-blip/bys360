from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import time
import zipfile
from datetime import UTC, datetime
from pathlib import Path

PACKAGE = "BYS360_SAFE_RELEASE_BUILDER_PHASE2_V3_DETERMINISTIC"
SCHEMA_VERSION = 2

FORBIDDEN_DIR_PARTS = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".idea", ".vscode", ".dart_tool",
    "instance", "logs", "uploads", "reports", "backups", "backup", "archive", "releases",
    "payload", "overlay_payload", "_security_quarantine", "_cleanup_quarantine", "_local_secrets",
    # BYS360 deterministic-package-builder hardening (2026-08-23): forensically
    # confirmed zero app/-import dependency before being added -- see
    # scripts/release/build_bys360_safe_release.py test suite and the wave's
    # forensic-comparison + include/exclude-contract agent findings.
    ".github", "tests", "mobile_flutter", ".codex", ".claude",
}
FORBIDDEN_SUFFIXES = {
    ".sqlite3", ".sqlite", ".db", ".dump", ".bak", ".backup", ".old", ".orig",
    ".log", ".pyc", ".pyo", ".key", ".pem", ".p12", ".pfx", ".ppk", ".jks", ".keystore",
    # Ported from scripts/security/build_bys360_secure_release_v1_5.py (now
    # deprecated in favor of this builder) -- an accidentally-committed
    # archive blob has no legitimate reason to ship inside a release package.
    ".zip", ".7z", ".rar",
}
FORBIDDEN_NAME_PATTERNS = (
    re.compile(r"(^|/|\\)\.env($|\.)", re.I),
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


def normalize(name: str) -> str:
    return name.replace("\\", "/").lstrip("/")


def is_forbidden_archive_name(name: str) -> tuple[bool, str]:
    n = normalize(name)
    parts = [p for p in n.split("/") if p]
    lower_parts = [p.lower() for p in parts]
    for part in lower_parts:
        if part in FORBIDDEN_DIR_PARTS:
            return True, f"yasak klasor parcasi: {part}"
    base = parts[-1] if parts else n
    if base.lower() in FORBIDDEN_EXACT_NAMES:
        return True, f"yasak dosya adi: {base}"
    suffix = Path(base).suffix.lower()
    if suffix in FORBIDDEN_SUFFIXES:
        return True, f"yasak dosya uzantisi: {suffix}"
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


def build_filtered_zip(
    root: Path, output: Path, source_sha: str
) -> tuple[str, list[tuple[Path, str]], list[dict[str, str]]]:
    source, included, excluded = iter_source_files(root)
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
) -> dict:
    files = sorted(rel for _, rel in included)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "package": PACKAGE,
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "source_sha": source_sha,
        "included_count": len(files),
        "files": files,
        "excluded_count": len(excluded),
        "excluded_sample": excluded[:200],
        "sha256sums_file": sha256sums_filename,
    }
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

    if manifest.get("schema_version") != SCHEMA_VERSION:
        findings.append(f"beklenmeyen manifest schema_version: {manifest.get('schema_version')!r}")

    manifest_files = set(manifest.get("files", []))

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

    try:
        source_sha = resolve_source_sha(root, args.source_sha)
        assert_clean_tracked_worktree(root)
        source, included, excluded = build_filtered_zip(output=output, root=root, source_sha=source_sha)
    except (GitDiscoveryError, DirtySourceError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2

    findings = scan_zip(output)
    manifest_path, sha256sums_path = _default_sidecar_paths(output)
    sha_pairs = compute_sha256_manifest(output)
    sha256sums_path.write_text(sha256sums_text(sha_pairs), encoding="utf-8", newline="\n")

    manifest = write_manifest(
        manifest_path=manifest_path,
        source_sha=source_sha,
        included=included,
        excluded=excluded,
        sha256sums_filename=sha256sums_path.name,
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
