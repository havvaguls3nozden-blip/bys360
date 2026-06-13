
# -*- coding: utf-8 -*-
"""
BYS360 Repo Hijyeni P1 V2.17.53
- __pycache__ / *.pyc temizliği
- *.bak / backup dosyası temizliği
- geçici backup klasörlerini karantinaya alma
- scripts envanteri çıkarma
- .gitignore güçlendirme

Bu script uygulama iş mantığını değiştirmez.
"""
from __future__ import annotations

import argparse
import ast
import datetime as _dt
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

VERSION = "V2.17.53"
REPORT_NAME = "bys360_repo_hygiene_p1_v2_17_53_report"

SKIP_DIR_NAMES = {
    ".git", ".venv", "venv", "env", "node_modules",
    "_cleanup_quarantine", "_security_quarantine", "_local_quarantine",
    "archive", "backups", "releases", "logs",
    ".mypy_cache", ".pytest_cache", ".ruff_cache",
}

GITIGNORE_LINES = [
    "# BYS360 hygiene generated rules",
    "__pycache__/",
    "*.py[cod]",
    "*$py.class",
    "*.bak",
    "*.bak.*",
    "*.backup",
    "*.backup*",
    "*.backup_before*",
    "*.before_*",
    ".mypy_cache/",
    ".pytest_cache/",
    ".ruff_cache/",
    "htmlcov/",
    ".coverage",
    "coverage.xml",
    "payload/",
    "overlay_payload/",
    "phase*_overlay/",
    "_cleanup_quarantine/",
    "_security_quarantine/",
    "_local_quarantine/",
]


def rel(p: Path, root: Path) -> str:
    try:
        return str(p.relative_to(root)).replace("/", "\\")
    except Exception:
        return str(p)


def should_skip_dir(path: Path, root: Path) -> bool:
    # Skip any path containing one of the quarantine/cache/env directories.
    parts = {part.lower() for part in path.relative_to(root).parts} if path != root else set()
    return bool(parts & {x.lower() for x in SKIP_DIR_NAMES})


def iter_project(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        # mutate dirnames to prune traversal
        keep = []
        for name in dirnames:
            child = d / name
            if should_skip_dir(child, root):
                continue
            keep.append(name)
        dirnames[:] = keep
        for name in filenames:
            yield d / name
        for name in dirnames:
            # yield dirs too for explicit directory matches
            yield d / name


def collect(root: Path) -> Dict[str, object]:
    pycache_dirs: List[str] = []
    pyc_files: List[str] = []
    bak_files: List[str] = []
    backup_dirs: List[str] = []
    scripts_files: List[str] = []
    large_files: List[Dict[str, object]] = []
    git_tracked_pycache: List[str] = []
    git_tracked_bak: List[str] = []

    seen_dirs = set()
    for p in iter_project(root):
        if p.is_dir():
            if p.name == "__pycache__":
                r = rel(p, root)
                if r not in seen_dirs:
                    pycache_dirs.append(r); seen_dirs.add(r)
            lname = p.name.lower()
            # Only flag backup dirs under project, not official C:\bys360\backups outside.
            if lname in {".backup", ".quality_backup", "quality_backup"} or lname.endswith("_backup") or lname.startswith("backup_"):
                rr = rel(p, root)
                if rr not in backup_dirs:
                    backup_dirs.append(rr)
            continue
        low = p.name.lower()
        rr = rel(p, root)
        if low.endswith((".pyc", ".pyo")):
            pyc_files.append(rr)
        if low.endswith(".bak") or ".bak." in low or low.endswith(".backup") or ".backup" in low or ".backup_before" in low or ".before_" in low:
            bak_files.append(rr)
        if rr.startswith("scripts\\") and p.is_file():
            scripts_files.append(rr)
        try:
            size = p.stat().st_size
            if size >= 75 * 1024 and p.suffix.lower() in {".py", ".js", ".html", ".css"}:
                large_files.append({"path": rr, "kb": round(size/1024, 1)})
        except Exception:
            pass

    git_root = root / ".git"
    git_repo = git_root.exists()
    if git_repo:
        try:
            out = subprocess.run(["git", "ls-files"], cwd=str(root), text=True, capture_output=True, timeout=30)
            if out.returncode == 0:
                for line in out.stdout.splitlines():
                    low = line.lower().replace("/", "\\")
                    if "__pycache__" in low or low.endswith((".pyc", ".pyo")):
                        git_tracked_pycache.append(line)
                    if low.endswith(".bak") or ".bak." in low or ".backup" in low or ".before_" in low:
                        git_tracked_bak.append(line)
        except Exception:
            pass

    return {
        "pycache_dir_count": len(pycache_dirs),
        "pyc_file_count": len(pyc_files),
        "bak_file_count": len(bak_files),
        "backup_dir_count": len(backup_dirs),
        "scripts_file_count": len(scripts_files),
        "large_file_count": len(large_files),
        "git_repo": git_repo,
        "git_tracked_pycache_count": len(git_tracked_pycache),
        "git_tracked_bak_count": len(git_tracked_bak),
        "pycache_dirs": pycache_dirs[:200],
        "pyc_files_sample": pyc_files[:200],
        "bak_files": bak_files[:300],
        "backup_dirs": backup_dirs[:200],
        "large_files": sorted(large_files, key=lambda x: x["kb"], reverse=True)[:50],
        "git_tracked_pycache_sample": git_tracked_pycache[:200],
        "git_tracked_bak_sample": git_tracked_bak[:200],
    }


def unique_dest(dest: Path) -> Path:
    if not dest.exists():
        return dest
    stem = dest.stem
    suffix = dest.suffix
    parent = dest.parent
    for i in range(1, 1000):
        cand = parent / f"{stem}__{i}{suffix}"
        if not cand.exists():
            return cand
    return parent / f"{stem}__{_dt.datetime.now().strftime('%H%M%S%f')}{suffix}"


def move_path(src: Path, root: Path, qroot: Path) -> Tuple[bool, str]:
    if not src.exists():
        return False, "missing"
    try:
        dest = qroot / src.relative_to(root)
        dest = unique_dest(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dest))
        return True, rel(dest, root)
    except Exception as exc:
        return False, str(exc)


def cleanup(root: Path) -> Dict[str, object]:
    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    qroot = root / "_cleanup_quarantine" / f"repo_hygiene_p1_{ts}"
    qroot.mkdir(parents=True, exist_ok=True)
    before = collect(root)
    moved: List[Dict[str, object]] = []
    errors: List[Dict[str, str]] = []

    # Move pycache dirs first; this also captures contained .pyc files.
    for rr in sorted(before.get("pycache_dirs", []), key=lambda x: len(x.split("\\")), reverse=True):
        src = root / rr
        ok, info = move_path(src, root, qroot)
        (moved if ok else errors).append({"path": rr, "to" if ok else "error": info})

    # Move pyc files not already inside moved dirs.
    fresh = collect(root)
    for rr in fresh.get("pyc_files_sample", []):
        src = root / rr
        ok, info = move_path(src, root, qroot)
        (moved if ok else errors).append({"path": rr, "to" if ok else "error": info})

    # Move bak files.
    fresh = collect(root)
    for rr in fresh.get("bak_files", []):
        src = root / rr
        ok, info = move_path(src, root, qroot)
        (moved if ok else errors).append({"path": rr, "to" if ok else "error": info})

    # Move backup dirs.
    fresh = collect(root)
    for rr in sorted(fresh.get("backup_dirs", []), key=lambda x: len(x.split("\\")), reverse=True):
        src = root / rr
        ok, info = move_path(src, root, qroot)
        (moved if ok else errors).append({"path": rr, "to" if ok else "error": info})

    return {
        "quarantine_root": rel(qroot, root),
        "moved_count": len(moved),
        "error_count": len(errors),
        "moved_sample": moved[:200],
        "errors": errors[:100],
    }


def ensure_gitignore(root: Path) -> Dict[str, object]:
    path = root / ".gitignore"
    old = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
    lines = old.splitlines()
    existing = {line.strip() for line in lines}
    added = []
    for line in GITIGNORE_LINES:
        if line and line not in existing:
            added.append(line)
    if added:
        new = old.rstrip() + "\n\n" + "\n".join(added) + "\n"
        path.write_text(new, encoding="utf-8")
    return {"changed": bool(added), "added": added}


def syntax_scan(root: Path) -> Dict[str, object]:
    files = []
    errors = []
    for base in ["app", "scripts"]:
        d = root / base
        if not d.exists():
            continue
        for p in d.rglob("*.py"):
            if should_skip_dir(p.parent, root):
                continue
            files.append(p)
            try:
                ast.parse(p.read_text(encoding="utf-8", errors="ignore"), filename=str(p))
            except Exception as exc:
                errors.append({"path": rel(p, root), "error": str(exc)})
    cfg = root / "config.py"
    if cfg.exists():
        try:
            ast.parse(cfg.read_text(encoding="utf-8", errors="ignore"), filename=str(cfg))
        except Exception as exc:
            errors.append({"path": rel(cfg, root), "error": str(exc)})
    return {"syntax_file_count": len(files), "syntax_ok": not errors, "syntax_errors": errors[:50]}


def app_factory_check(root: Path) -> Dict[str, object]:
    # Try project venv first, then current interpreter. This can fail if dependencies are not installed; report only.
    candidates = [root / ".venv" / "Scripts" / "python.exe", Path(sys.executable)]
    code = "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"
    for py in candidates:
        if not py.exists():
            continue
        try:
            env = os.environ.copy()
            env.setdefault("PYTHONUTF8", "1")
            env.setdefault("PYTHONIOENCODING", "utf-8")
            out = subprocess.run([str(py), "-c", code], cwd=str(root), text=True, capture_output=True, timeout=45, env=env)
            return {
                "attempted": True,
                "python": str(py),
                "ok": out.returncode == 0,
                "returncode": out.returncode,
                "stdout_tail": out.stdout[-1500:],
                "stderr_tail": out.stderr[-1500:],
            }
        except Exception as exc:
            last = {"attempted": True, "python": str(py), "ok": False, "error": str(exc)}
            return last
    return {"attempted": False, "ok": None, "reason": "python_not_found"}


def write_reports(root: Path, data: Dict[str, object]) -> Dict[str, str]:
    rdir = root / "reports" / "quality"
    rdir.mkdir(parents=True, exist_ok=True)
    json_path = rdir / f"{REPORT_NAME}.json"
    md_path = rdir / f"{REPORT_NAME}.md"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = data.get("after", data.get("before", {}))
    apply = data.get("apply", {})
    gitignore = data.get("gitignore", {})
    health = data.get("health", {})
    md = []
    md.append(f"# BYS360 Repo Hijyeni P1 {VERSION}\n")
    md.append("Bu rapor `__pycache__`, `*.pyc`, `*.bak` ve geçici backup kalıntılarını temizlemek için üretilmiştir. Uygulama iş mantığı değiştirilmez.\n")
    md.append("## Özet\n")
    md.append("| Alan | Değer |\n|---|---:|\n")
    for k in ["mode", "generated_at"]:
        md.append(f"| {k} | `{data.get(k)}` |\n")
    for k in ["pycache_dir_count", "pyc_file_count", "bak_file_count", "backup_dir_count", "scripts_file_count", "large_file_count", "git_repo", "git_tracked_pycache_count", "git_tracked_bak_count"]:
        md.append(f"| {k} | {summary.get(k)} |\n")
    md.append(f"| gitignore_changed | {gitignore.get('changed')} |\n")
    md.append(f"| moved_count | {apply.get('moved_count', 0)} |\n")
    md.append(f"| error_count | {apply.get('error_count', 0)} |\n")
    md.append(f"| syntax_ok | {health.get('syntax',{}).get('syntax_ok')} |\n")
    md.append(f"| app_factory_ok | {health.get('app_factory',{}).get('ok')} |\n")
    md.append(f"| overall_hygiene_ok | {data.get('overall_hygiene_ok')} |\n")

    md.append("\n## Apply\n")
    if data.get("mode") == "audit":
        md.append("Audit modu; dosya taşınmadı.\n")
    else:
        md.append(f"- quarantine_root: `{apply.get('quarantine_root')}`\n")
        md.append(f"- moved_count: `{apply.get('moved_count')}`\n")
        md.append(f"- error_count: `{apply.get('error_count')}`\n")

    def table(title, rows, col="Dosya/Klasör"):
        md.append(f"\n## {title}\n")
        if not rows:
            md.append("Kayıt yok.\n"); return
        md.append(f"| {col} |\n|---|\n")
        for x in rows[:80]:
            md.append(f"| `{x}` |\n")
        if len(rows) > 80:
            md.append(f"\n_İlk 80 kayıt gösterildi. Toplam: {len(rows)}_\n")

    table("__pycache__ Klasörleri", summary.get("pycache_dirs", []), "Klasör")
    table(".pyc Dosya Örneği", summary.get("pyc_files_sample", []))
    table(".bak / backup Dosyaları", summary.get("bak_files", []))
    table("Backup Klasörleri", summary.get("backup_dirs", []), "Klasör")

    md.append("\n## Büyük Dosya Sinyalleri\n")
    large = summary.get("large_files", [])
    if large:
        md.append("| Dosya | KB |\n|---|---:|\n")
        for item in large[:30]:
            md.append(f"| `{item.get('path')}` | {item.get('kb')} |\n")
    else:
        md.append("Büyük dosya sinyali yok.\n")

    md.append("\n## Git İçin Elle Yapılabilecekler\n")
    md.append("Bu proje klasörü Git repo ise aşağıdaki komutlar geçmiş/index temizliği için ayrıca değerlendirilebilir. Git repo değilse çalıştırılmaz.\n\n")
    md.append("```powershell\n")
    md.append("git rm -r --cached --ignore-unmatch **/__pycache__ **/*.pyc\n")
    md.append("git rm --cached --ignore-unmatch $(git ls-files '*.bak' '*.bak.*' '*.backup*' '*.backup_before*')\n")
    md.append("git commit -m \"chore: purge pycache and backup artifacts from tracking\"\n")
    md.append("```\n")

    md.append("\n## Scripts Dizini Notu\n")
    md.append("Bu paket scripts klasörünü taşımaz; yalnızca envanter üretir. Eski repair scriptleri daha sonra ayrı bir arşivleme planıyla ele alınmalıdır.\n")

    md_path.write_text("".join(md), encoding="utf-8")
    return {"json_report": rel(json_path, root), "md_report": rel(md_path, root)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--mode", choices=["audit", "all"], default="audit")
    ns = ap.parse_args(argv)
    root = Path(ns.project_root).resolve()
    if not root.exists():
        print(json.dumps({"error": "project_root_not_found", "project_root": str(root)}, ensure_ascii=False, indent=2))
        return 2

    before = collect(root)
    data: Dict[str, object] = {
        "version": VERSION,
        "mode": ns.mode,
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "before": before,
    }
    apply_result: Dict[str, object] = {}
    if ns.mode == "all":
        data["gitignore"] = ensure_gitignore(root)
        apply_result = cleanup(root)
        data["apply"] = apply_result
        # Final post-clean scan.
        data["after"] = collect(root)
    else:
        data["gitignore"] = {"changed": False, "added": []}
        data["apply"] = {"moved_count": 0, "error_count": 0}

    health = {"syntax": syntax_scan(root), "app_factory": app_factory_check(root)}
    data["health"] = health

    active = data.get("after", before)
    data["overall_hygiene_ok"] = (
        int(active.get("pycache_dir_count", 0)) == 0 and
        int(active.get("pyc_file_count", 0)) == 0 and
        int(active.get("bak_file_count", 0)) == 0 and
        health["syntax"].get("syntax_ok") is True and
        int(apply_result.get("error_count", 0)) == 0
    ) if ns.mode == "all" else (health["syntax"].get("syntax_ok") is True)

    data.update(write_reports(root, data))
    print(json.dumps({
        "version": VERSION,
        "mode": ns.mode,
        "project_root": str(root),
        "before_summary": {k: before.get(k) for k in ["pycache_dir_count", "pyc_file_count", "bak_file_count", "backup_dir_count", "scripts_file_count", "large_file_count", "git_repo", "git_tracked_pycache_count", "git_tracked_bak_count"]},
        "after_summary": {k: data.get("after", {}).get(k) for k in ["pycache_dir_count", "pyc_file_count", "bak_file_count", "backup_dir_count"]} if ns.mode == "all" else {},
        "apply": data.get("apply"),
        "syntax_ok": health["syntax"].get("syntax_ok"),
        "app_factory_ok": health["app_factory"].get("ok"),
        "overall_hygiene_ok": data.get("overall_hygiene_ok"),
        "json_report": data.get("json_report"),
        "md_report": data.get("md_report"),
    }, ensure_ascii=False, indent=2))

    if ns.mode == "all":
        if data.get("overall_hygiene_ok"):
            print(f"BYS360_REPO_HYGIENE_P1_{VERSION}_CLEAN_OK")
        else:
            print(f"BYS360_REPO_HYGIENE_P1_{VERSION}_NEEDS_REVIEW")
    print(f"BYS360_REPO_HYGIENE_P1_{VERSION}_REPORT_OK")
    print(f"BYS360_REPO_HYGIENE_P1_{VERSION}_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
