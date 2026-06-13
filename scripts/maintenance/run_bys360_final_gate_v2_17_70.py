from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

VERSION = "V2.17.70"
EXCLUDE_DIR_NAMES = {
    ".git", ".venv", "venv", "env", "__pycache__", "backups", "backup", "_cleanup_quarantine",
    "archive", ".dart_tool", "build", ".gradle", ".idea", ".vscode", "node_modules",
}
EXCLUDE_FILE_SUFFIXES = {".pyc", ".pyo", ".bak", ".tmp", ".log", ".jks", ".keystore"}
EXCLUDE_FILE_NAMES = {".env", "key.properties", "local.properties"}
SECRET_PATTERNS = [
    ("env_file", re.compile(r"(^|[\\/])\.env$", re.I)),
    ("private_key", re.compile(r"BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY")),
    ("hardcoded_password_assignment", re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key)\s*=\s*['\"][^'\"]{8,}['\"]")),
]
MOJIBAKE_MARKERS = ["Ã", "Ä", "Å", "Â", "�", "ï¿½", "GÃ", "Ä±", "ÅŸ", "ÄŸ", "Ã§", "Ã¶", "Ã¼"]
PERSONAL_MARKERS = ["Havva", "Miley", "kahve", "kafam", "ters ters", "yorgun", "gece 02", "saat 21", "saat 20", "insan gibi", "15 Subat 2026", "22 Mart 2026"]


def rel(root: Path, p: Path) -> str:
    try:
        return str(p.relative_to(root)).replace("/", "\\")
    except Exception:
        return str(p)


def should_exclude(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except Exception:
        parts = path.parts
    for part in parts:
        if part in EXCLUDE_DIR_NAMES:
            return True
    if path.is_file():
        if path.name in EXCLUDE_FILE_NAMES:
            return True
        if path.suffix.lower() in EXCLUDE_FILE_SUFFIXES:
            return True
    return False


def iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        dirnames[:] = [x for x in dirnames if x not in EXCLUDE_DIR_NAMES]
        for name in filenames:
            p = d / name
            if not should_exclude(p, root):
                yield p


def read_text_safe(path: Path):
    try:
        return path.read_text(encoding="utf-8"), None
    except UnicodeDecodeError as exc:
        try:
            return path.read_text(encoding="utf-8-sig"), None
        except Exception:
            return "", str(exc)
    except Exception as exc:
        return "", str(exc)


def check_bom_ast_pycompile(root: Path) -> dict[str, Any]:
    bom = []
    ast_errors = []
    py_compile_errors = []
    py_count = 0
    for p in iter_files(root):
        if p.suffix.lower() != ".py":
            continue
        py_count += 1
        try:
            raw = p.read_bytes()
        except Exception as exc:
            ast_errors.append({"file": rel(root, p), "error": f"read_error: {exc}"})
            continue
        if raw.startswith(b"\xef\xbb\xbf"):
            bom.append(rel(root, p))
        try:
            text = raw.decode("utf-8")
            ast.parse(text, filename=str(p))
        except Exception as exc:
            ast_errors.append({"file": rel(root, p), "error": str(exc)})
        try:
            subprocess.run([sys.executable, "-m", "py_compile", str(p)], cwd=str(root), capture_output=True, text=True, timeout=60, check=True)
        except subprocess.CalledProcessError as exc:
            py_compile_errors.append({"file": rel(root, p), "stderr": exc.stderr[-2000:]})
        except Exception as exc:
            py_compile_errors.append({"file": rel(root, p), "stderr": str(exc)})
    return {
        "python_file_count": py_count,
        "bom_count": len(bom),
        "bom_files": bom[:50],
        "ast_error_count": len(ast_errors),
        "ast_errors": ast_errors[:50],
        "py_compile_error_count": len(py_compile_errors),
        "py_compile_errors": py_compile_errors[:50],
        "ok": not bom and not ast_errors and not py_compile_errors,
    }


def run_compileall(root: Path) -> dict[str, Any]:
    targets = [x for x in ["app", "config.py", "scripts", "wsgi.py", "run.py"] if (root / x).exists()]
    try:
        proc = subprocess.run([sys.executable, "-m", "compileall", "-q", *targets], cwd=str(root), capture_output=True, text=True, timeout=300)
        return {"ran": True, "ok": proc.returncode == 0, "returncode": proc.returncode, "stdout_tail": proc.stdout[-4000:], "stderr_tail": proc.stderr[-4000:]}
    except Exception as exc:
        return {"ran": True, "ok": False, "error": str(exc)}


def resolve_flutter_command() -> tuple[list[str] | None, str]:
    candidates = []
    env_flutter = os.environ.get("FLUTTER_BIN") or os.environ.get("FLUTTER_EXE")
    if env_flutter:
        candidates.append(env_flutter)
    for name in ["flutter.bat", "flutter.cmd", "flutter.exe", "flutter"]:
        found = shutil.which(name)
        if found:
            candidates.append(found)
    common = [
        r"C:\src\flutter\bin\flutter.bat",
        r"C:\flutter\bin\flutter.bat",
        r"C:\tools\flutter\bin\flutter.bat",
        str(Path.home() / "flutter" / "bin" / "flutter.bat"),
    ]
    candidates.extend(common)
    seen = set()
    for candidate in candidates:
        if not candidate:
            continue
        c = str(candidate)
        key = c.lower()
        if key in seen:
            continue
        seen.add(key)
        if Path(c).exists() or shutil.which(c):
            return [c], c
    return None, "flutter command not found. PATH icinde flutter.bat bulunamadi."


def run_dart_analyze(root: Path) -> dict[str, Any]:
    mobile_root = root / "mobile_flutter" / "bys360_mobile_native"
    if not mobile_root.exists():
        return {"ran": False, "ok": True, "skipped": "mobile_flutter/bys360_mobile_native bulunamadi"}
    cmd, resolved = resolve_flutter_command()
    if not cmd:
        return {"ran": True, "ok": False, "tool_error": resolved, "hint": "PowerShell icinde `flutter --version` calisiyorsa final gate icin FLUTTER_BIN ortam degiskenine flutter.bat tam yolunu verebilirsiniz."}
    try:
        proc = subprocess.run([*cmd, "analyze"], cwd=str(mobile_root), capture_output=True, text=True, timeout=300, shell=False)
        return {
            "ran": True,
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "resolved_flutter": resolved,
            "stdout_tail": proc.stdout[-6000:],
            "stderr_tail": proc.stderr[-6000:],
        }
    except FileNotFoundError as exc:
        return {"ran": True, "ok": False, "tool_error": str(exc), "resolved_flutter": resolved}
    except Exception as exc:
        return {"ran": True, "ok": False, "error": str(exc), "resolved_flutter": resolved}


def check_migrations(root: Path) -> dict[str, Any]:
    versions = root / "migrations" / "versions"
    if not versions.exists():
        return {"exists": False, "ok": True, "skipped": "migrations/versions bulunamadi"}
    revisions: dict[str, list[str]] = {}
    parents: set[str] = set()
    errors = []
    for p in versions.glob("*.py"):
        text, err = read_text_safe(p)
        if err:
            errors.append({"file": rel(root, p), "error": err})
            continue
        rev_m = re.search(r"^revision\s*=\s*['\"]([^'\"]+)['\"]", text, re.M)
        down_m = re.search(r"^down_revision\s*=\s*(.+)$", text, re.M)
        if not rev_m:
            continue
        rev = rev_m.group(1)
        downs: list[str] = []
        if down_m:
            raw = down_m.group(1).strip()
            if raw not in {"None", "None  # type: ignore"}:
                downs = re.findall(r"['\"]([^'\"]+)['\"]", raw)
        revisions[rev] = downs
        parents.update(downs)
    missing_parents = sorted([x for x in parents if x not in revisions])
    heads = sorted([rev for rev in revisions if rev not in parents])
    return {
        "exists": True,
        "revision_count": len(revisions),
        "head_count": len(heads),
        "heads": heads,
        "missing_parent_count": len(missing_parents),
        "missing_parents": missing_parents,
        "parse_error_count": len(errors),
        "parse_errors": errors[:20],
        "ok": len(heads) == 1 and not missing_parents and not errors,
    }


def scan_text_quality(root: Path) -> dict[str, Any]:
    mojibake = []
    personal = []
    for p in iter_files(root):
        if p.suffix.lower() not in {".py", ".html", ".css", ".js", ".dart", ".md", ".txt", ".yaml", ".yml"}:
            continue
        text, err = read_text_safe(p)
        if err:
            continue
        m_count = sum(text.count(x) for x in MOJIBAKE_MARKERS)
        if m_count:
            mojibake.append({"file": rel(root, p), "count": m_count})
        p_hits = {m: text.count(m) for m in PERSONAL_MARKERS if m in text}
        if p_hits:
            personal.append({"file": rel(root, p), "markers": p_hits, "count": sum(p_hits.values())})
    return {
        "mojibake_marker_count": sum(x["count"] for x in mojibake),
        "mojibake_files": mojibake[:100],
        "personal_marker_count": sum(x["count"] for x in personal),
        "personal_files": personal[:100],
        "ok": not mojibake and not personal,
    }


def scan_for_packaging_risks(root: Path) -> dict[str, Any]:
    risky = []
    total_size = 0
    file_count = 0
    excluded_size = 0
    excluded_count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        for name in filenames:
            p = d / name
            try:
                size = p.stat().st_size
            except Exception:
                size = 0
            total_size += size
            file_count += 1
            if should_exclude(p, root):
                excluded_size += size
                excluded_count += 1
                risky.append({"file": rel(root, p), "size": size})
    return {
        "total_file_count": file_count,
        "total_size_mb": round(total_size / 1024 / 1024, 2),
        "excluded_candidate_count": excluded_count,
        "excluded_candidate_size_mb": round(excluded_size / 1024 / 1024, 2),
        "examples": risky[:100],
        "ok": True,
        "note": "Bu adaylar temiz release zip disinda birakilir; calisma klasorunde bulunmasi tek basina gate hatasi sayilmadi.",
    }


def scan_secrets(root: Path) -> dict[str, Any]:
    findings = []
    for p in iter_files(root):
        if p.suffix.lower() not in {".py", ".html", ".js", ".dart", ".md", ".txt", ".yaml", ".yml", ".json", ".ini", ".cfg", ".toml", ".example"}:
            continue
        text, err = read_text_safe(p)
        if err:
            continue
        # Allow example placeholders but flag obviously sensitive assignments outside example files.
        for name, rx in SECRET_PATTERNS:
            for m in rx.finditer(text):
                if p.name.endswith(".example") or "example" in p.name.lower():
                    continue
                findings.append({"file": rel(root, p), "pattern": name, "line": text.count("\n", 0, m.start()) + 1})
                break
    return {"finding_count": len(findings), "findings": findings[:100], "ok": len(findings) == 0}


def build_release_zip(root: Path, output_root: Path) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = output_root / f"BYS360_CLEAN_RELEASE_V2_17_70_{stamp}.zip"
    added = 0
    size = 0
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for p in iter_files(root):
            # Also do not package previous generated reports/backups? reports are allowed but can be bulky. Exclude generated gate reports? Keep reports not necessary. Exclude all reports to keep clean source.
            r = rel(root, p).replace("\\", "/")
            if r.startswith("reports/"):
                continue
            zf.write(p, arcname=f"bys360/project/{r}")
            added += 1
            try:
                size += p.stat().st_size
            except Exception:
                pass
    return {"built": True, "path": str(zip_path), "file_count": added, "source_size_mb": round(size / 1024 / 1024, 2), "zip_size_mb": round(zip_path.stat().st_size / 1024 / 1024, 2), "ok": True}


def write_reports(root: Path, report: dict[str, Any]) -> tuple[str, str]:
    reports = root / "reports"
    reports.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = reports / f"bys360_final_gate_v2_17_70_{report['mode']}_{stamp}.json"
    md_path = reports / f"bys360_final_gate_v2_17_70_{report['mode']}_{stamp}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [f"# BYS360 Final Gate {VERSION}", "", f"Mode: `{report['mode']}`", f"OK: `{report['ok']}`", ""]
    for key, value in report.get("checks", {}).items():
        lines.append(f"## {key}")
        if isinstance(value, dict):
            lines.append(f"OK: `{value.get('ok')}`")
            for k in ["bom_count", "ast_error_count", "py_compile_error_count", "head_count", "missing_parent_count", "mojibake_marker_count", "personal_marker_count", "finding_count", "compileall_ok", "returncode", "tool_error", "resolved_flutter"]:
                if k in value:
                    lines.append(f"- {k}: `{value[k]}`")
        lines.append("")
    if report.get("release_zip"):
        rz = report["release_zip"]
        lines.extend(["## Release Zip", f"- path: `{rz.get('path')}`", f"- zip_size_mb: `{rz.get('zip_size_mb')}`", ""])
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return rel(root, json_path), rel(root, md_path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--mode", choices=["audit", "release"], default="audit")
    ap.add_argument("--compileall", action="store_true")
    ap.add_argument("--dart-analyze", action="store_true")
    ap.add_argument("--build-release-zip", action="store_true")
    ap.add_argument("--output-root", default=r"C:\bys360\releases")
    args = ap.parse_args()
    root = Path(args.project_root).resolve()
    checks: dict[str, Any] = {}
    checks["bom_ast_pycompile"] = check_bom_ast_pycompile(root)
    checks["migrations"] = check_migrations(root)
    checks["text_quality"] = scan_text_quality(root)
    checks["packaging_risks"] = scan_for_packaging_risks(root)
    checks["secret_scan"] = scan_secrets(root)
    if args.compileall:
        checks["compileall"] = run_compileall(root)
    if args.dart_analyze:
        checks["dart_analyze"] = run_dart_analyze(root)

    ok = all(v.get("ok", False) for k, v in checks.items() if k != "packaging_risks")
    release_zip = None
    if args.mode == "release" and args.build_release_zip:
        if ok:
            release_zip = build_release_zip(root, Path(args.output_root))
        else:
            release_zip = {"built": False, "ok": False, "reason": "gate checks failed"}
            ok = False

    report = {"version": VERSION, "mode": args.mode, "project_root": str(root), "checks": checks, "release_zip": release_zip, "ok": bool(ok)}
    jp, mp = write_reports(root, report)
    report["json_report"] = jp
    report["md_report"] = mp
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 2

if __name__ == "__main__":
    raise SystemExit(main())
