from __future__ import annotations

import argparse
import ast
import compileall
import datetime as _dt
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any

VERSION = "V2.17.69"

EXCLUDE_DIR_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".dart_tool",
    "build",
    "backups",
    "_cleanup_quarantine",
    "archive",
    "node_modules",
}

EXCLUDE_FILE_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".bak",
    ".tmp",
    ".log",
    ".jks",
    ".keystore",
}

EXCLUDE_FILE_NAMES = {
    ".env",
    "key.properties",
    "local.properties",
    "google-services.json",
    "GoogleService-Info.plist",
}

ALLOW_ENV_EXAMPLES = {
    ".env.example",
    ".env.production.example",
    ".env.sample",
}

TEXT_EXTS = {
    ".py", ".html", ".css", ".js", ".ts", ".json", ".md", ".txt",
    ".yaml", ".yml", ".toml", ".ini", ".cfg", ".dart", ".ps1",
    ".sql", ".env", ".example"
}

SECRET_PATTERNS = [
    ("private_key", re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("generic_secret_assignment", re.compile(r"(?i)\b(secret|password|passwd|token|api[_-]?key)\b\s*[:=]\s*['\"]?([^\s'\"#]{12,})")),
    ("database_url_with_password", re.compile(r"(?i)(postgres(?:ql)?|mysql|mssql|redis)://[^:\s]+:[^@\s]+@")),
]

PLACEHOLDER_WORDS = {
    "changeme", "change_me", "placeholder", "example", "your_", "dummy",
    "xxx", "xxxx", "test", "dev", "local", "buraya", "giriniz", "replace"
}


def rel_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def should_exclude(path: Path, root: Path) -> tuple[bool, str | None]:
    rel_parts = path.relative_to(root).parts
    for part in rel_parts[:-1] if path.is_file() else rel_parts:
        if part in EXCLUDE_DIR_NAMES:
            return True, f"excluded_dir:{part}"

    name = path.name
    suffix = path.suffix.lower()
    if name in ALLOW_ENV_EXAMPLES:
        return False, None
    if name in EXCLUDE_FILE_NAMES:
        return True, f"excluded_file:{name}"
    if suffix in EXCLUDE_FILE_SUFFIXES:
        return True, f"excluded_suffix:{suffix}"
    if name.endswith(".bak") or name.endswith(".backup"):
        return True, "excluded_backup_suffix"
    if ".keystore" in name.lower():
        return True, "excluded_keystore_name"
    return False, None


def iter_source_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        excluded, _ = should_exclude(p, root)
        if excluded:
            continue
        files.append(p)
    return files


def scan_bom_ast_pycompile(root: Path) -> dict[str, Any]:
    py_files = [p for p in iter_source_files(root) if p.suffix == ".py"]
    bom: list[str] = []
    ast_errors: list[dict[str, Any]] = []
    py_compile_errors: list[dict[str, Any]] = []

    for p in py_files:
        rel = rel_posix(p, root)
        try:
            data = p.read_bytes()
            if data.startswith(b"\xef\xbb\xbf"):
                bom.append(rel)
            text = data.decode("utf-8")
        except Exception as exc:
            ast_errors.append({"file": rel, "error": f"decode:{exc}"})
            continue

        try:
            ast.parse(text, filename=str(p))
        except Exception as exc:
            ast_errors.append({"file": rel, "error": str(exc)})

        try:
            py_compile.compile(str(p), doraise=True)
        except Exception as exc:
            py_compile_errors.append({"file": rel, "error": str(exc)})

    return {
        "py_file_count": len(py_files),
        "bom_count": len(bom),
        "bom_files": bom[:200],
        "ast_error_count": len(ast_errors),
        "ast_errors": ast_errors[:200],
        "py_compile_error_count": len(py_compile_errors),
        "py_compile_errors": py_compile_errors[:200],
        "ok": not bom and not ast_errors and not py_compile_errors,
    }


def run_compileall(root: Path) -> dict[str, Any]:
    targets = [root / "app", root / "config.py", root / "scripts"]
    existing = [str(t) for t in targets if t.exists()]
    if not existing:
        return {"ran": False, "ok": False, "reason": "compileall target bulunamadi"}
    proc = subprocess.run(
        [sys.executable, "-m", "compileall", "-q", *existing],
        cwd=str(root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return {
        "ran": True,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-3000:],
        "stderr_tail": proc.stderr[-3000:],
    }


def parse_alembic(root: Path) -> dict[str, Any]:
    candidates = [
        root / "migrations" / "versions",
        root / "alembic" / "versions",
    ]
    versions_dir = next((d for d in candidates if d.exists()), None)
    if not versions_dir:
        return {"found": False, "ok": False, "reason": "Alembic versions klasoru bulunamadi"}

    revisions: dict[str, dict[str, Any]] = {}
    used_down: set[str] = set()
    errors: list[dict[str, str]] = []

    for p in sorted(versions_dir.glob("*.py")):
        text = p.read_text(encoding="utf-8", errors="replace")
        rev_match = re.search(r"^revision\s*=\s*['\"]([^'\"]+)['\"]", text, re.M)
        down_match = re.search(r"^down_revision\s*=\s*(.+)$", text, re.M)
        if not rev_match:
            errors.append({"file": rel_posix(p, root), "error": "revision bulunamadi"})
            continue
        revision = rev_match.group(1)
        down_raw = down_match.group(1).strip() if down_match else "None"
        down_values: list[str] = []
        if down_raw not in {"None", "null"}:
            for q in re.findall(r"['\"]([^'\"]+)['\"]", down_raw):
                down_values.append(q)
                used_down.add(q)
        revisions[revision] = {
            "file": rel_posix(p, root),
            "down_revision": down_values,
        }

    missing_parents = sorted([d for d in used_down if d not in revisions])
    heads = sorted([r for r in revisions if r not in used_down])
    return {
        "found": True,
        "versions_dir": rel_posix(versions_dir, root),
        "revision_count": len(revisions),
        "head_count": len(heads),
        "heads": heads,
        "missing_parent_count": len(missing_parents),
        "missing_parents": missing_parents,
        "parse_error_count": len(errors),
        "parse_errors": errors,
        "ok": len(revisions) > 0 and len(heads) == 1 and not missing_parents and not errors,
    }


def secret_scan(root: Path) -> dict[str, Any]:
    workspace_env_files: list[str] = []
    excluded_sensitive_files: list[dict[str, str]] = []
    content_hits: list[dict[str, Any]] = []

    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = rel_posix(p, root)
        if p.name.startswith(".env") and p.name not in ALLOW_ENV_EXAMPLES:
            workspace_env_files.append(rel)

        excluded, reason = should_exclude(p, root)
        if excluded and (p.name in EXCLUDE_FILE_NAMES or p.suffix.lower() in {".jks", ".keystore"} or ".keystore" in p.name.lower()):
            excluded_sensitive_files.append({"file": rel, "reason": reason or "excluded"})

        if excluded:
            continue

        suffix = p.suffix.lower()
        if suffix not in TEXT_EXTS and p.name not in ALLOW_ENV_EXAMPLES:
            continue

        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        # Example files are scanned but placeholder-looking values are ignored.
        is_example = p.name in ALLOW_ENV_EXAMPLES or rel.endswith(".example")
        for name, pat in SECRET_PATTERNS:
            for m in pat.finditer(text):
                value = m.group(0)
                low = value.lower()
                if is_example and any(w in low for w in PLACEHOLDER_WORDS):
                    continue
                # Ignore documented environment variable names without value.
                if name == "generic_secret_assignment":
                    candidate = m.group(2).lower()
                    if any(w in candidate for w in PLACEHOLDER_WORDS):
                        continue
                content_hits.append({
                    "file": rel,
                    "pattern": name,
                    "line": text.count("\n", 0, m.start()) + 1,
                    "sample": value[:80],
                })
                if len(content_hits) >= 200:
                    break
            if len(content_hits) >= 200:
                break
        if len(content_hits) >= 200:
            break

    # Existing local .env is a release exclusion warning, not a project failure by itself.
    return {
        "workspace_env_file_count": len(workspace_env_files),
        "workspace_env_files": workspace_env_files[:50],
        "excluded_sensitive_file_count": len(excluded_sensitive_files),
        "excluded_sensitive_files": excluded_sensitive_files[:100],
        "content_hit_count": len(content_hits),
        "content_hits": content_hits[:100],
        "ok": len(content_hits) == 0,
        "note": "Yerel .env dosyasi varsa release zip'e dahil edilmemelidir; varligi tek basina gate hatasi sayilmadi.",
    }


def release_inventory(root: Path) -> dict[str, Any]:
    total_count = 0
    total_size = 0
    excluded_count = 0
    excluded_size = 0
    included_count = 0
    included_size = 0
    forbidden_included: list[dict[str, str]] = []

    for p in root.rglob("*"):
        if not p.is_file():
            continue
        size = p.stat().st_size
        total_count += 1
        total_size += size
        excluded, reason = should_exclude(p, root)
        if excluded:
            excluded_count += 1
            excluded_size += size
        else:
            included_count += 1
            included_size += size
            rel = rel_posix(p, root)
            lower = rel.lower()
            if (
                "/.venv/" in lower or "\\.venv\\" in lower or
                "__pycache__" in lower or lower.endswith(".pyc") or
                lower.endswith(".bak") or lower.endswith(".jks") or
                lower.endswith(".keystore") or
                p.name == ".env" or
                "/backups/" in lower or "/archive/" in lower or "_cleanup_quarantine" in lower
            ):
                forbidden_included.append({"file": rel, "reason": "forbidden_release_artifact"})

    return {
        "total_file_count": total_count,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "included_file_count": included_count,
        "included_size_mb": round(included_size / (1024 * 1024), 2),
        "excluded_file_count": excluded_count,
        "excluded_size_mb": round(excluded_size / (1024 * 1024), 2),
        "forbidden_included_count": len(forbidden_included),
        "forbidden_included": forbidden_included[:200],
        "ok": len(forbidden_included) == 0,
    }


def build_release_zip(root: Path, output_root: Path) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = output_root / f"BYS360_CLEAN_RELEASE_V2_17_69_{stamp}.zip"
    manifest_path = output_root / f"BYS360_CLEAN_RELEASE_V2_17_69_{stamp}_MANIFEST.json"

    included: list[dict[str, Any]] = []
    excluded_reasons: dict[str, int] = {}

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for p in sorted(root.rglob("*")):
            if not p.is_file():
                continue
            # Do not include generated release zip if OutputRoot is under ProjectRoot.
            try:
                if output_root.resolve() in p.resolve().parents or p.resolve() == zip_path.resolve():
                    continue
            except Exception:
                pass

            excluded, reason = should_exclude(p, root)
            if excluded:
                excluded_reasons[reason or "excluded"] = excluded_reasons.get(reason or "excluded", 0) + 1
                continue
            rel = rel_posix(p, root)
            zf.write(p, arcname=f"bys360/project/{rel}")
            included.append({"file": rel, "size": p.stat().st_size})

    manifest = {
        "version": VERSION,
        "created_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "zip_path": str(zip_path),
        "included_file_count": len(included),
        "included_size_mb": round(sum(i["size"] for i in included) / (1024 * 1024), 2),
        "excluded_reasons": excluded_reasons,
        "policy": {
            "excluded": [
                ".env", ".venv", "__pycache__", ".pyc", "backups",
                "_cleanup_quarantine", "archive", ".bak", ".jks", ".keystore",
                "key.properties", "local.properties",
            ],
            "allowed_examples": sorted(ALLOW_ENV_EXAMPLES),
        },
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "built": True,
        "zip_path": str(zip_path),
        "manifest_path": str(manifest_path),
        "included_file_count": manifest["included_file_count"],
        "included_size_mb": manifest["included_size_mb"],
        "excluded_reasons": excluded_reasons,
        "ok": zip_path.exists() and zip_path.stat().st_size > 0,
    }


def run_dart_analyze(root: Path) -> dict[str, Any]:
    mobile_root = root / "mobile_flutter" / "bys360_mobile_native"
    if not mobile_root.exists():
        return {"ran": False, "ok": True, "reason": "mobile Flutter klasoru bulunamadi"}
    proc = subprocess.run(
        ["flutter", "analyze"],
        cwd=str(mobile_root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return {
        "ran": True,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-6000:],
        "stderr_tail": proc.stderr[-3000:],
    }


def run_smoke_test(root: Path) -> dict[str, Any]:
    code = """
from __future__ import annotations
import importlib
result = {"import_app": False, "create_app": False, "test_client": False, "status_code": None}
try:
    app_mod = importlib.import_module("app")
    result["import_app"] = True
    create_app = getattr(app_mod, "create_app", None)
    if create_app:
        app = create_app()
        result["create_app"] = True
        client = app.test_client()
        resp = client.get("/login")
        result["test_client"] = True
        result["status_code"] = getattr(resp, "status_code", None)
    print(result)
except Exception as exc:
    print({"error": str(exc), **result})
    raise
"""
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    return {
        "ran": True,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-3000:],
        "stderr_tail": proc.stderr[-3000:],
    }


def write_reports(root: Path, report: dict[str, Any]) -> tuple[str, str]:
    reports_dir = root / "reports"
    reports_dir.mkdir(exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = reports_dir / f"bys360_final_gate_v2_17_69_{stamp}.json"
    md_path = reports_dir / f"bys360_final_gate_v2_17_69_{stamp}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = []
    lines.append("# BYS360 Final Gate V2.17.69")
    lines.append("")
    lines.append(f"- ProjectRoot: `{report['project_root']}`")
    lines.append(f"- Overall OK: `{report['ok']}`")
    lines.append("")
    checks = report.get("checks", {})
    for key, val in checks.items():
        ok = val.get("ok") if isinstance(val, dict) else None
        lines.append(f"## {key}")
        lines.append("")
        lines.append(f"- OK: `{ok}`")
        if isinstance(val, dict):
            for small_key in [
                "py_file_count", "bom_count", "ast_error_count", "py_compile_error_count",
                "revision_count", "head_count", "missing_parent_count", "content_hit_count",
                "included_size_mb", "included_file_count", "compileall_ok", "returncode"
            ]:
                if small_key in val:
                    lines.append(f"- {small_key}: `{val[small_key]}`")
            if "heads" in val:
                lines.append(f"- heads: `{val['heads']}`")
            if "zip_path" in val:
                lines.append(f"- zip_path: `{val['zip_path']}`")
        lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return rel_posix(json_path, root), rel_posix(md_path, root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", default="audit")
    parser.add_argument("--output-root", default=r"C:\bys360\releases")
    parser.add_argument("--compileall", action="store_true")
    parser.add_argument("--dart-analyze", action="store_true")
    parser.add_argument("--smoke-test", action="store_true")
    parser.add_argument("--build-release-zip", action="store_true")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    output_root = Path(args.output_root).resolve()

    checks: dict[str, Any] = {}
    checks["bom_ast_pycompile"] = scan_bom_ast_pycompile(root)

    if args.compileall:
        checks["compileall"] = run_compileall(root)
    else:
        checks["compileall"] = {"ran": False, "ok": True}

    checks["alembic"] = parse_alembic(root)
    checks["secret_scan"] = secret_scan(root)
    checks["release_inventory"] = release_inventory(root)

    if args.dart_analyze:
        checks["dart_analyze"] = run_dart_analyze(root)
    else:
        checks["dart_analyze"] = {"ran": False, "ok": True}

    if args.smoke_test:
        checks["smoke_test"] = run_smoke_test(root)
    else:
        checks["smoke_test"] = {"ran": False, "ok": True}

    if args.build_release_zip:
        checks["release_zip"] = build_release_zip(root, output_root)
    else:
        checks["release_zip"] = {"built": False, "ok": True}

    ok = all(bool(v.get("ok", False)) for v in checks.values() if isinstance(v, dict))

    report = {
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(root),
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "checks": checks,
        "ok": ok,
    }

    json_report, md_report = write_reports(root, report)
    report["json_report"] = json_report
    report["md_report"] = md_report
    # Re-write with report paths included.
    (root / json_report).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
