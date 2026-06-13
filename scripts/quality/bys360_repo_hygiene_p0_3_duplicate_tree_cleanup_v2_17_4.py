#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BYS360 Repo Hijyeni P0.3 - Duplicate Project Tree Cleanup V2.17.4

Amaç:
- C:\\bys360\\project altında yanlışlıkla oluşmuş iç içe project/ kopyasını aktif çekirdekten ayırmak.
- Aktif app/config.py/scripts yapısına dokunmadan duplicate tree'i _local_quarantine altına taşımak.
- İşlem öncesi/sonrası compileall ve app factory sağlık kontrolü yapmak.

Bu script gerçek secret değerlerini rapora yazmaz. Sadece sayısal özet ve dosya yolu verir.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

VERSION = "V2.17.4"
REPORT_BASENAME = "bys360_repo_hygiene_p0_3_duplicate_tree_cleanup_v2_17_4"

EXCLUDE_DIR_NAMES = {
    ".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache", ".mypy_cache",
    "node_modules", "build", "dist", ".dart_tool", ".gradle", ".idea", ".vscode",
    "_local_quarantine", "reports",
}

SECRET_KEYWORDS = [
    "PASSWORD", "PASS", "SECRET", "TOKEN", "KEY", "DATABASE_URL", "SMTP", "SENTRY_DSN",
    "API_KEY", "PRIVATE", "CREDENTIAL", "JWT", "SESSION_COOKIE", "REDIS_URL",
]

RISKY_EXTS = {".env", ".bak", ".backup", ".old", ".orig", ".tmp"}


def rel(root: Path, p: Path) -> str:
    try:
        return p.relative_to(root).as_posix()
    except Exception:
        return str(p)


def now_stamp() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_report_dirs(root: Path) -> Path:
    d = root / "reports" / "quality"
    d.mkdir(parents=True, exist_ok=True)
    return d


def is_excluded_dir(path: Path) -> bool:
    parts = set(path.parts)
    return bool(parts.intersection(EXCLUDE_DIR_NAMES))


def iter_files(root: Path):
    for base, dirs, files in os.walk(root):
        base_path = Path(base)
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIR_NAMES]
        if is_excluded_dir(base_path):
            continue
        for name in files:
            yield base_path / name


def count_tree(root: Path, tree: Path) -> Dict[str, Any]:
    info: Dict[str, Any] = {
        "exists": tree.exists(),
        "path": rel(root, tree),
        "file_count": 0,
        "py_count": 0,
        "html_count": 0,
        "risky_path_count": 0,
        "possible_secret_hit_count": 0,
        "sample_risky_paths": [],
        "sample_secret_paths": [],
    }
    if not tree.exists():
        return info

    for p in iter_files(tree):
        info["file_count"] += 1
        if p.suffix.lower() == ".py":
            info["py_count"] += 1
        if p.suffix.lower() in {".html", ".htm"}:
            info["html_count"] += 1
        name_lower = p.name.lower()
        suffix_lower = p.suffix.lower()
        if suffix_lower in RISKY_EXTS or ".bak" in name_lower or "backup" in name_lower or name_lower.startswith("tmp_"):
            info["risky_path_count"] += 1
            if len(info["sample_risky_paths"]) < 30:
                info["sample_risky_paths"].append(rel(root, p))
        try:
            if p.stat().st_size <= 2_000_000 and p.suffix.lower() in {".py", ".txt", ".env", ".ini", ".cfg", ".yaml", ".yml", ".json", ".ps1", ".md"}:
                text = p.read_text(encoding="utf-8", errors="replace")
                upper = text.upper()
                if any(k in upper for k in SECRET_KEYWORDS):
                    info["possible_secret_hit_count"] += 1
                    if len(info["sample_secret_paths"]) < 30:
                        info["sample_secret_paths"].append(rel(root, p))
        except Exception:
            pass
    return info


def discover_duplicate_trees(root: Path) -> List[Dict[str, Any]]:
    candidates: List[Path] = []
    direct = root / "project"
    if direct.exists() and direct.is_dir():
        candidates.append(direct)

    # Extra defensive scan: nested project dirs outside quarantine/cache.
    for base, dirs, _files in os.walk(root):
        base_path = Path(base)
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIR_NAMES]
        if is_excluded_dir(base_path):
            continue
        for d in list(dirs):
            p = base_path / d
            if d.lower() == "project" and p != root and p not in candidates:
                candidates.append(p)

    results: List[Dict[str, Any]] = []
    for tree in candidates:
        has_app = (tree / "app").exists()
        has_scripts = (tree / "scripts").exists()
        has_config = (tree / "config.py").exists()
        looks_like_bys360 = has_app or has_scripts or has_config
        item = count_tree(root, tree)
        item.update({
            "has_app": has_app,
            "has_scripts": has_scripts,
            "has_config_py": has_config,
            "looks_like_duplicate_bys360_tree": looks_like_bys360,
            "eligible_for_quarantine": looks_like_bys360 and tree.resolve() != root.resolve(),
        })
        results.append(item)
    return results


def run_cmd(root: Path, args: List[str], timeout: int = 120) -> Dict[str, Any]:
    try:
        cp = subprocess.run(
            args,
            cwd=str(root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return {
            "ok": cp.returncode == 0,
            "returncode": cp.returncode,
            "stdout_tail": cp.stdout[-5000:],
            "stderr_tail": cp.stderr[-5000:],
        }
    except subprocess.TimeoutExpired as e:
        return {"ok": False, "returncode": "timeout", "stdout_tail": str(e.stdout)[-2000:], "stderr_tail": str(e.stderr)[-2000:]}
    except Exception as e:
        return {"ok": False, "returncode": "exception", "stdout_tail": "", "stderr_tail": repr(e)}


def health(root: Path) -> Dict[str, Any]:
    compile_res = run_cmd(root, [sys.executable, "-m", "compileall", "app", "config.py", "scripts"], timeout=180)
    factory_code = "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"
    factory_res = run_cmd(root, [sys.executable, "-c", factory_code], timeout=180)
    app_factory_ok = factory_res.get("ok") and "BYS360_APP_CREATE_OK" in (factory_res.get("stdout_tail") or "")
    return {
        "compileall_ok": bool(compile_res.get("ok")),
        "app_factory_ok": bool(app_factory_ok),
        "overall_ok": bool(compile_res.get("ok") and app_factory_ok),
        "compileall": compile_res,
        "app_factory": factory_res,
    }


def update_gitignore(root: Path) -> Dict[str, Any]:
    gi = root / ".gitignore"
    existing = ""
    if gi.exists():
        existing = gi.read_text(encoding="utf-8", errors="replace")
    additions = [
        "",
        "# BYS360 local quarantine and duplicate tree cleanup",
        "_local_quarantine/",
        "/project/",
        "reports/quality/*.json",
        "reports/quality/*.md",
    ]
    changed = False
    out = existing
    for line in additions:
        if line and line not in out:
            out += ("\n" if not out.endswith("\n") else "") + line
            changed = True
    if changed:
        gi.write_text(out, encoding="utf-8")
    return {"path": ".gitignore", "changed": changed}


def quarantine_duplicate_trees(root: Path, duplicate_trees: List[Dict[str, Any]]) -> Dict[str, Any]:
    qroot = root / "_local_quarantine" / f"bys360_repo_hygiene_p0_3_duplicate_tree_{now_stamp()}"
    qroot.mkdir(parents=True, exist_ok=True)
    moved: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []
    for item in duplicate_trees:
        if not item.get("eligible_for_quarantine"):
            continue
        src = root / item["path"]
        if not src.exists():
            continue
        try:
            # Preserve relative layout under quarantine.
            dest = qroot / item["path"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                dest = qroot / f"{item['path'].replace('/', '_')}_{now_stamp()}"
            shutil.move(str(src), str(dest))
            moved.append({"path": item["path"], "status": "moved", "to": rel(root, dest)})
        except Exception as e:
            errors.append({"path": item["path"], "error": repr(e)})
    return {"quarantine_root": rel(root, qroot), "moved": moved, "errors": errors}


def write_reports(root: Path, data: Dict[str, Any]) -> None:
    report_dir = ensure_report_dirs(root)
    json_path = report_dir / f"{REPORT_BASENAME}_report.json"
    md_path = report_dir / f"{REPORT_BASENAME}_report.md"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = []
    lines.append(f"# BYS360 Repo Hijyeni P0.3 Duplicate Tree Cleanup {VERSION}")
    lines.append("")
    lines.append(f"Mode: `{data.get('mode')}`")
    lines.append(f"ProjectRoot: `{data.get('project_root')}`")
    lines.append("")
    lines.append("## Sağlık Özeti")
    hs = data.get("health_summary", {})
    if hs:
        lines.append(f"- compileall_ok: `{hs.get('compileall_ok')}`")
        lines.append(f"- app_factory_ok: `{hs.get('app_factory_ok')}`")
        lines.append(f"- overall_ok: `{hs.get('overall_ok')}`")
    else:
        lines.append("- Bu modda sağlık kontrolü çalıştırılmadı.")
    lines.append("")
    lines.append("## Duplicate Project Tree Özeti")
    dups = data.get("duplicate_trees", [])
    if not dups:
        lines.append("- İç içe duplicate `project/` ağacı bulunmadı.")
    else:
        for d in dups:
            lines.append(f"- `{d.get('path')}` | files={d.get('file_count')} | py={d.get('py_count')} | risky={d.get('risky_path_count')} | secrets={d.get('possible_secret_hit_count')} | eligible={d.get('eligible_for_quarantine')}")
    lines.append("")
    if data.get("apply"):
        lines.append("## Uygulama")
        app = data["apply"]
        lines.append(f"- quarantine_root: `{app.get('quarantine_root')}`")
        lines.append(f"- moved_count: `{len(app.get('moved', []))}`")
        if app.get("errors"):
            lines.append("- errors:")
            for e in app["errors"]:
                lines.append(f"  - `{e.get('path')}`: {e.get('error')}")
    lines.append("")
    lines.append("## Not")
    lines.append("Bu işlem aktif `app/`, `config.py` ve `scripts/` çekirdeğine dokunmaz; yalnızca iç içe duplicate proje kopyasını karantinaya taşır.")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    data["json_report"] = rel(root, json_path)
    data["md_report"] = rel(root, md_path)
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--mode", choices=["audit", "apply", "health", "all"], default="audit")
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    if not root.exists():
        print(f"ProjectRoot bulunamadi: {root}", file=sys.stderr)
        return 2
    if not (root / "app").exists():
        print(f"Aktif app klasoru bulunamadi; yanlis ProjectRoot olabilir: {root}", file=sys.stderr)
        return 2

    data: Dict[str, Any] = {
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(root),
        "duplicate_trees": [],
        "health_summary": {},
    }

    duplicate_trees = discover_duplicate_trees(root)
    data["duplicate_trees"] = duplicate_trees
    data["gitignore"] = update_gitignore(root) if args.mode in {"apply", "all"} else {"path": ".gitignore", "changed": False, "applied": False}

    before_health = None
    after_health = None
    if args.mode in {"health", "all"}:
        before_health = health(root)
        data["health_summary"] = before_health

    if args.mode in {"apply", "all"}:
        # If health was requested and failed before apply, do not touch tree.
        if before_health is not None and not before_health.get("overall_ok"):
            data["apply"] = {"skipped": True, "reason": "pre_apply_health_failed"}
        else:
            data["apply"] = quarantine_duplicate_trees(root, duplicate_trees)
            # Re-discover after move.
            data["duplicate_trees_after_apply"] = discover_duplicate_trees(root)
            after_health = health(root)
            data["post_apply_health_summary"] = after_health
            data["health_summary"] = after_health

    write_reports(root, data)
    print(json.dumps({
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(root),
        "duplicate_tree_count": len(duplicate_trees),
        "eligible_duplicate_tree_count": sum(1 for d in duplicate_trees if d.get("eligible_for_quarantine")),
        "health_summary": data.get("health_summary", {}),
        "apply": data.get("apply", {}),
        "json_report": data.get("json_report"),
        "md_report": data.get("md_report"),
    }, ensure_ascii=False, indent=2))

    if args.mode in {"health", "all"} and not data.get("health_summary", {}).get("overall_ok"):
        return 1
    if data.get("apply", {}).get("errors"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
