# -*- coding: utf-8 -*-
"""
BYS360 Repo Hijyeni P1B Syntax Probe V2.17.54
Kod değiştirmez. P1 sonrası syntax_ok=False kaynağını dosya bazlı bulur.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

VERSION = "V2.17.54"
REPORT_STEM = "bys360_repo_hygiene_p1b_syntax_probe_v2_17_54_report"

EXCLUDE_DIR_NAMES = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "__pycache__",
    ".mypy_cache", ".ruff_cache", ".pytest_cache", "node_modules",
    "build", "dist", "site-packages", "_security_quarantine", "_cleanup_quarantine",
    "_local_quarantine", "archive", "logs", "reports",
}
EXCLUDE_PREFIX_PARTS = {
    "mobile_flutter", "payload", "overlay_payload", "phase7_2_overlay",
}
INCLUDE_ROOTS = ["app", "scripts"]
INCLUDE_FILES = ["config.py", "wsgi.py", "run_server.py", "manage.py"]


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("/", "\\")
    except Exception:
        return str(path).replace("/", "\\")


def should_skip_dir(path: Path, root: Path) -> bool:
    parts = set(path.relative_to(root).parts) if path != root else set()
    return bool(parts & EXCLUDE_DIR_NAMES) or bool(parts & EXCLUDE_PREFIX_PARTS)


def iter_python_files(root: Path) -> List[Path]:
    files: List[Path] = []
    for name in INCLUDE_ROOTS:
        base = root / name
        if not base.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            d = Path(dirpath)
            # mutate dirnames to prune excluded dirs early
            dirnames[:] = [dn for dn in dirnames if not should_skip_dir(d / dn, root)]
            if should_skip_dir(d, root):
                continue
            for fn in filenames:
                if fn.endswith(".py"):
                    files.append(d / fn)
    for name in INCLUDE_FILES:
        p = root / name
        if p.exists() and p.suffix == ".py":
            files.append(p)
    return sorted(set(files), key=lambda p: rel(p, root).lower())


def read_text_best_effort(path: Path) -> str:
    data = path.read_bytes()
    for enc in ("utf-8", "utf-8-sig", "cp1254", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def syntax_probe(root: Path) -> Dict[str, Any]:
    files = iter_python_files(root)
    errors: List[Dict[str, Any]] = []
    ok_count = 0
    for p in files:
        try:
            text = read_text_best_effort(p)
            ast.parse(text, filename=str(p))
            ok_count += 1
        except SyntaxError as e:
            errors.append({
                "path": rel(p, root),
                "lineno": e.lineno,
                "offset": e.offset,
                "msg": e.msg,
                "text": (e.text or "").strip(),
            })
        except Exception as e:
            errors.append({
                "path": rel(p, root),
                "lineno": None,
                "offset": None,
                "msg": f"{type(e).__name__}: {e}",
                "text": "",
            })
    return {
        "scanned_py_count": len(files),
        "syntax_ok_count": ok_count,
        "syntax_error_count": len(errors),
        "syntax_ok": len(errors) == 0,
        "errors": errors,
    }


def run_cmd(root: Path, cmd: List[str], timeout: int = 120) -> Dict[str, Any]:
    try:
        cp = subprocess.run(
            cmd,
            cwd=str(root),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        return {
            "ok": cp.returncode == 0,
            "returncode": cp.returncode,
            "stdout_tail": cp.stdout[-4000:],
            "stderr_tail": cp.stderr[-4000:],
        }
    except Exception as e:
        return {"ok": False, "returncode": None, "stdout_tail": "", "stderr_tail": f"{type(e).__name__}: {e}"}


def health_probe(root: Path) -> Dict[str, Any]:
    compileall = run_cmd(root, [sys.executable, "-m", "compileall", "app", "config.py", "scripts"], timeout=240)
    app_factory = run_cmd(root, [sys.executable, "-c", "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"], timeout=120)
    return {
        "compileall_ok": compileall["ok"],
        "app_factory_ok": app_factory["ok"],
        "compileall": compileall,
        "app_factory": app_factory,
    }


def git_probe(root: Path) -> Dict[str, Any]:
    git_dir = root / ".git"
    res: Dict[str, Any] = {"git_repo": git_dir.exists()}
    if git_dir.exists():
        pycache = run_cmd(root, ["git", "ls-files", "**/__pycache__", "**/*.pyc"], timeout=30)
        bak = run_cmd(root, ["git", "ls-files", "*.bak", "*.bak.*", "*.backup*", "*.backup_before*"], timeout=30)
        res["tracked_pycache_stdout"] = pycache.get("stdout_tail", "")
        res["tracked_bak_stdout"] = bak.get("stdout_tail", "")
        res["tracked_pycache_count"] = len([x for x in res["tracked_pycache_stdout"].splitlines() if x.strip()])
        res["tracked_bak_count"] = len([x for x in res["tracked_bak_stdout"].splitlines() if x.strip()])
    else:
        res["tracked_pycache_count"] = 0
        res["tracked_bak_count"] = 0
    return res


def write_reports(root: Path, report: Dict[str, Any]) -> Dict[str, str]:
    out_dir = root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{REPORT_STEM}.json"
    md_path = out_dir / f"{REPORT_STEM}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    syntax = report["syntax_probe"]
    health = report["health_probe"]
    git = report["git_probe"]
    lines = []
    lines.append(f"# BYS360 Repo Hijyeni P1B Syntax Probe {VERSION}")
    lines.append("")
    lines.append("Bu rapor kod değiştirmez. P1 temizlik sonrası `syntax_ok=False` kaynağını dosya bazlı tespit eder.")
    lines.append("")
    lines.append("## Özet")
    lines.append("")
    lines.append("| Alan | Değer |")
    lines.append("|---|---:|")
    lines.append(f"| mode | `{report['mode']}` |")
    lines.append(f"| generated_at | `{report['generated_at']}` |")
    lines.append(f"| scanned_py_count | {syntax['scanned_py_count']} |")
    lines.append(f"| syntax_error_count | {syntax['syntax_error_count']} |")
    lines.append(f"| syntax_ok | {syntax['syntax_ok']} |")
    lines.append(f"| compileall_ok | {health['compileall_ok']} |")
    lines.append(f"| app_factory_ok | {health['app_factory_ok']} |")
    lines.append(f"| git_repo | {git['git_repo']} |")
    lines.append(f"| tracked_pycache_count | {git['tracked_pycache_count']} |")
    lines.append(f"| tracked_bak_count | {git['tracked_bak_count']} |")
    lines.append(f"| overall_ok | {report['overall_ok']} |")
    lines.append("")
    lines.append("## Syntax Hataları")
    lines.append("")
    if syntax["errors"]:
        lines.append("| Dosya | Satır | Hata | Satır İçeriği |")
        lines.append("|---|---:|---|---|")
        for e in syntax["errors"][:100]:
            text = str(e.get("text", "")).replace("|", "\\|")[:160]
            msg = str(e.get("msg", "")).replace("|", "\\|")
            lines.append(f"| `{e['path']}` | {e.get('lineno') or ''} | {msg} | `{text}` |")
        if len(syntax["errors"]) > 100:
            lines.append(f"\nİlk 100 hata gösterildi. Toplam: {len(syntax['errors'])}")
    else:
        lines.append("Syntax hatası bulunmadı.")
    lines.append("")
    lines.append("## Sağlık Kontrolü")
    lines.append("")
    lines.append(f"- compileall_ok: {health['compileall_ok']}")
    lines.append(f"- app_factory_ok: {health['app_factory_ok']}")
    lines.append(f"- overall_ok: {report['overall_ok']}")
    lines.append("")
    lines.append("## Yorum")
    lines.append("")
    if syntax["errors"] and health["app_factory_ok"]:
        lines.append("Uygulama factory temiz açılıyor; syntax hatası büyük ihtimalle aktif import zincirinde olmayan bir yardımcı/repair scriptindedir. İlgili dosya düzeltilmeden final kalite raporu kapatılmamalıdır.")
    elif report["overall_ok"]:
        lines.append("Syntax ve uygulama sağlığı temizdir. P1 hijyen sonrası final temiz paket üretilebilir.")
    else:
        lines.append("Rapor uyarı içeriyor. Yukarıdaki syntax veya sağlık hataları incelenmelidir.")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return {"json_report": str(json_path.relative_to(root)), "md_report": str(md_path.relative_to(root))}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--mode", default="all")
    args = ap.parse_args()
    root = Path(args.project_root).resolve()
    if not root.exists():
        print(f"ProjectRoot bulunamadi: {root}", file=sys.stderr)
        return 2
    syntax = syntax_probe(root)
    health = health_probe(root)
    git = git_probe(root)
    overall_ok = syntax["syntax_ok"] and health["compileall_ok"] and health["app_factory_ok"]
    report: Dict[str, Any] = {
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(root),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "syntax_probe": syntax,
        "health_probe": health,
        "git_probe": git,
        "overall_ok": overall_ok,
    }
    paths = write_reports(root, report)
    report.update(paths)
    summary = {
        "version": VERSION,
        "mode": args.mode,
        "syntax_error_count": syntax["syntax_error_count"],
        "syntax_ok": syntax["syntax_ok"],
        "compileall_ok": health["compileall_ok"],
        "app_factory_ok": health["app_factory_ok"],
        "overall_ok": overall_ok,
        "json_report": paths["json_report"],
        "md_report": paths["md_report"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("BYS360_REPO_HYGIENE_P1B_SYNTAX_PROBE_V2_17_54_REPORT_OK")
    if overall_ok:
        print("BYS360_REPO_HYGIENE_P1B_SYNTAX_PROBE_V2_17_54_HEALTH_OK")
    else:
        print("BYS360_REPO_HYGIENE_P1B_SYNTAX_PROBE_V2_17_54_NEEDS_REVIEW")
    print("BYS360_REPO_HYGIENE_P1B_SYNTAX_PROBE_V2_17_54_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
