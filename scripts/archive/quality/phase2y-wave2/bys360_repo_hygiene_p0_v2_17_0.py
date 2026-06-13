# -*- coding: utf-8 -*-
"""
BYS360 Repo Hygiene P0 V2.17.0

Amaç:
- Repo hijyeni ve teknik borç risklerini raporlamak.
- .gitignore ve .git/info/exclude dosyalarını güvenli şekilde güçlendirmek.
- .env içindeki anahtarları değer göstermeden .env.example dosyasına dönüştürmek.
- Backup/.bak/tmp dosyalarını canlı koddan ayırmak için karantinaya almak.
- İsteğe bağlı olarak riskli dosyaları Git index'ten kaldırmak; çalışma kopyasında bırakır.

Bu script bilinçli olarak canlı uygulama kodunu değiştirmez.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, List, Sequence, Tuple

VERSION = "V2.17.0"
MARKER_OK = "BYS360_REPO_HYGIENE_P0_V2_17_0_OK"
MARKER_REPORT = "BYS360_REPO_HYGIENE_P0_V2_17_0_REPORT_OK"
MARKER_APPLY = "BYS360_REPO_HYGIENE_P0_V2_17_0_APPLY_OK"

SAFE_ENV_EXAMPLES = {
    ".env.example",
    ".env.production.example",
    ".env.template",
    ".env.sample",
    ".env.local.example",
}

GITIGNORE_BLOCK = """
# --- BYS360 P0 repo hygiene V2.17.0 ---
# Local secrets / environment files
.env
.env.*
!.env.example
!.env.production.example
!.env.template
!.env.sample
!.env.local.example

# Python virtual environments / caches
.venv/
venv/
env/
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.mypy_cache/
.ruff_cache/
.cache/

# Runtime logs / generated files
logs/
*.log
*.dump
*.db
*.sqlite
*.sqlite3
instance/
uploads/
_upload_parts/
reports/runtime/

# Local backup / repair artifacts
.backup/
.quality_backup/
_local_quarantine/
_local_secrets/
*.bak
*.backup
tmp_*
*_tmp.py
*_before_*.py
*_before_*.html

# Build artifacts
dist/
build/
*.egg-info/
htmlcov/
.coverage
coverage.xml

# Node / frontend caches if created later
node_modules/
.npm/
.yarn/

# Flutter / mobile generated artifacts
.dart_tool/
.flutter-plugins
.flutter-plugins-dependencies
.packages
build/
mobile_flutter/**/build/
mobile_flutter/**/.dart_tool/
mobile_flutter/**/*.apk
mobile_flutter/**/*.aab
# --- /BYS360 P0 repo hygiene V2.17.0 ---
""".strip() + "\n"

SECRET_KEY_RE = re.compile(
    r"(?i)(secret|password|passwd|pwd|token|apikey|api_key|access[_-]?token|dsn|database_url|sqlalchemy_database_uri|private[_-]?key|encryption[_-]?key|tckn)"
)
ENV_LINE_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$")
PHASE_RE = re.compile(r"(?i)(phase\d+|_phase\d+|ai_phase\d+|phase\d+[a-z]?_routes|p\d+_|v\d+_\d+)")

EXCLUDED_DIRS_FOR_SCAN = {
    ".git",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".cache",
    "_local_quarantine",
    "_local_secrets",
}

# .venv is NOT excluded from summary because we want to detect it. For content scanning we skip it later.
CONTENT_SCAN_SKIP_DIRS = EXCLUDED_DIRS_FOR_SCAN | {".venv", "venv", "env", ".quality_backup", ".backup"}
TEXT_EXTS = {".py", ".ps1", ".txt", ".md", ".yml", ".yaml", ".json", ".ini", ".cfg", ".env", ".example", ".html", ".css", ".js", ".dart"}


def norm_rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def is_safe_env_example(rel: str) -> bool:
    return PurePosixPath(rel).name in SAFE_ENV_EXAMPLES


def is_env_file(rel: str) -> bool:
    name = PurePosixPath(rel).name
    return name == ".env" or name.startswith(".env.")


def is_risky_path(rel: str) -> bool:
    p = PurePosixPath(rel)
    parts = set(p.parts)
    name = p.name.lower()
    low = rel.lower()
    if is_env_file(rel) and not is_safe_env_example(rel):
        return True
    if ".venv" in parts or "venv" in parts or "env" in parts:
        return True
    if ".backup" in parts or ".quality_backup" in parts:
        return True
    if name.endswith((".bak", ".backup", ".pyc", ".pyo")):
        return True
    if name.startswith("tmp_") or name.endswith("_tmp.py"):
        return True
    if "/logs/" in f"/{low}/" or low.startswith("logs/") or name.endswith(".log"):
        return True
    if name.endswith((".dump", ".db", ".sqlite", ".sqlite3")):
        return True
    if "__pycache__" in parts:
        return True
    return False


def should_quarantine_path(path: Path, root: Path, quarantine_env: bool, quarantine_venv: bool) -> bool:
    rel = norm_rel(path, root)
    p = PurePosixPath(rel)
    parts = set(p.parts)
    name = p.name.lower()
    if ".git" in parts or "_local_quarantine" in parts or "_local_secrets" in parts:
        return False
    if is_env_file(rel) and not is_safe_env_example(rel):
        return quarantine_env
    if ".venv" in parts or "venv" in parts or "env" in parts:
        return quarantine_venv
    if ".backup" in parts or ".quality_backup" in parts:
        return True
    if name.endswith((".bak", ".backup")):
        return True
    if name.startswith("tmp_") or name.endswith("_tmp.py"):
        return True
    return False


def append_block_once(file_path: Path, block: str, title_token: str) -> bool:
    existing = ""
    if file_path.exists():
        existing = file_path.read_text(encoding="utf-8", errors="ignore")
    if title_token in existing:
        return False
    file_path.parent.mkdir(parents=True, exist_ok=True)
    sep = "" if not existing or existing.endswith("\n") else "\n"
    file_path.write_text(existing + sep + block, encoding="utf-8")
    return True


def placeholder_for_key(key: str, current_value: str) -> str:
    k = key.upper()
    if k in {"FLASK_ENV", "APP_ENV", "SENTRY_ENVIRONMENT"}:
        return "production"
    if k == "FLASK_DEBUG":
        return "0"
    if k.endswith("_ENABLED") or k.endswith("_SECURE") or k.endswith("_HTTPONLY") or k.endswith("_PRE_PING") or k.endswith("_USE_LIFO"):
        return "true"
    if k in {"SESSION_COOKIE_SAMESITE"}:
        return "Lax"
    if k in {"DB_SSLMODE"}:
        return "require"
    if "URL" in k and "DATABASE" in k:
        return "DB_CONNECTION_STRING_SUPPLIED_BY_ENVIRONMENT"
    if k in {"DATABASE_URL", "SQLALCHEMY_DATABASE_URI"}:
        return "DB_CONNECTION_STRING_SUPPLIED_BY_ENVIRONMENT"
    if "REDIS" in k or "BROKER" in k or "BACKEND" in k:
        return "redis://127.0.0.1:6379/0"
    if "SECRET" in k or "PASSWORD" in k or "TOKEN" in k or "KEY" in k or "DSN" in k:
        return "CHANGE_ME"
    if "EMAIL" in k or "MAIL" in k:
        return "name@example.gov.tr"
    if k.endswith("PORT"):
        return "8000"
    if "HOST" in k:
        return "127.0.0.1"
    if "TIMEOUT" in k or "TTL" in k or "SECONDS" in k or "MINUTES" in k:
        return "60"
    if "COUNT" in k or "SIZE" in k or "LENGTH" in k or "LIMIT" in k or "THREAD" in k or "WORKER" in k or "POOL" in k or "MAX" in k:
        return "10"
    if current_value and current_value.lower() in {"true", "false", "0", "1"}:
        return current_value.lower()
    return ""


def generate_env_example(root: Path) -> Tuple[bool, int, str]:
    env_path = root / ".env"
    out_path = root / ".env.example"
    if not env_path.exists():
        if not out_path.exists():
            out_path.write_text(
                "# BYS360 environment example\n# Gerçek değerleri bu dosyaya yazmayın. Yerelde .env kullanın.\n",
                encoding="utf-8",
            )
            return True, 0, norm_rel(out_path, root)
        return False, 0, norm_rel(out_path, root)

    lines = env_path.read_text(encoding="utf-8", errors="ignore").splitlines()
    output = [
        "# BYS360 .env.example",
        "# Bu dosyada gerçek parola, token, secret veya bağlantı bilgisi bulunmamalıdır.",
        "# Yerel/üretim gerçek değerleri sadece sunucudaki .env veya güvenli secret yönetiminde tutulmalıdır.",
        "",
    ]
    count = 0
    seen = set()
    for line in lines:
        m = ENV_LINE_RE.match(line)
        if not m:
            if line.strip().startswith("#"):
                output.append(line)
            continue
        key, value = m.group(1), m.group(2).strip().strip('"').strip("'")
        if key in seen:
            continue
        seen.add(key)
        output.append(f"{key}={placeholder_for_key(key, value)}")
        count += 1
    out_path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")
    return True, count, norm_rel(out_path, root)


def iter_files(root: Path) -> Iterable[Path]:
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        # Do not descend into huge/external generated dirs for normal scan, but keep .venv existence counted separately.
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS_FOR_SCAN]
        for f in files:
            yield current_path / f


def collect_audit(root: Path) -> Dict[str, object]:
    files = list(iter_files(root))
    ext_counts: Dict[str, int] = {}
    risky: List[str] = []
    large_py: List[Dict[str, object]] = []
    large_route_py: List[Dict[str, object]] = []
    phase_py: List[str] = []
    backup_dirs: List[str] = []
    env_files: List[str] = []
    possible_secret_hits: List[Dict[str, object]] = []

    for dname in [".backup", ".quality_backup", ".venv", "venv", "env"]:
        p = root / dname
        if p.exists():
            backup_dirs.append(norm_rel(p, root))

    for path in files:
        rel = norm_rel(path, root)
        ext = path.suffix.lower() or "<no_ext>"
        ext_counts[ext] = ext_counts.get(ext, 0) + 1
        if is_risky_path(rel):
            risky.append(rel)
        if is_env_file(rel):
            env_files.append(rel)
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        low = rel.lower()
        if path.suffix.lower() == ".py" and size >= 50_000:
            item = {"path": rel, "bytes": size}
            large_py.append(item)
            if "routes" in path.name.lower() or "/routes" in low or "route" in low:
                large_route_py.append(item)
        if path.suffix.lower() == ".py" and PHASE_RE.search(rel):
            phase_py.append(rel)

        # Content-level secret scan, path/key only; never records values.
        parts = set(PurePosixPath(rel).parts)
        if parts.intersection(CONTENT_SCAN_SKIP_DIRS):
            continue
        if path.suffix.lower() not in TEXT_EXTS and path.name != ".env":
            continue
        if size > 1_500_000:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for line_no, line in enumerate(content.splitlines(), start=1):
            m = ENV_LINE_RE.match(line)
            if not m:
                continue
            key, value = m.group(1), m.group(2).strip().strip('"').strip("'")
            if SECRET_KEY_RE.search(key) and value and value.upper() not in {"CHANGE_ME", "TODO", "NONE", "NULL", ""}:
                possible_secret_hits.append({"path": rel, "line": line_no, "key": key})
                if len(possible_secret_hits) >= 250:
                    break

    ext_top = sorted(ext_counts.items(), key=lambda kv: kv[1], reverse=True)[:25]
    return {
        "version": VERSION,
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "total_files_scanned": len(files),
        "top_extensions": ext_top,
        "risky_path_count": len(risky),
        "risky_path_sample": risky[:200],
        "env_files": env_files[:100],
        "backup_dirs_present": backup_dirs,
        "large_py_count": len(large_py),
        "large_py_top": sorted(large_py, key=lambda x: x["bytes"], reverse=True)[:50],
        "large_route_py_count": len(large_route_py),
        "large_route_py_top": sorted(large_route_py, key=lambda x: x["bytes"], reverse=True)[:50],
        "phase_py_count": len(phase_py),
        "phase_py_sample": phase_py[:200],
        "possible_secret_hit_count": len(possible_secret_hits),
        "possible_secret_hits": possible_secret_hits[:250],
    }


def write_reports(root: Path, audit: Dict[str, object]) -> Tuple[Path, Path]:
    reports_dir = root / "reports" / "quality"
    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = reports_dir / "bys360_repo_hygiene_p0_v2_17_0_report.json"
    md_path = reports_dir / "bys360_repo_hygiene_p0_v2_17_0_report.md"
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    def md_table(items: Sequence[Dict[str, object]], limit: int = 20) -> str:
        rows = ["| Dosya | Boyut |", "|---|---:|"]
        for item in items[:limit]:
            rows.append(f"| `{item.get('path')}` | {int(item.get('bytes', 0)):,} bytes |".replace(",", "."))
        return "\n".join(rows)

    risky_sample = audit.get("risky_path_sample", [])
    secret_hits = audit.get("possible_secret_hits", [])
    md = f"""# BYS360 Repo Hijyeni P0 Raporu — {VERSION}

Üretim zamanı: `{audit.get('generated_at')}`  
Proje kökü: `{audit.get('project_root')}`

## Özet

| Başlık | Değer |
|---|---:|
| Taranan dosya | {audit.get('total_files_scanned')} |
| Riskli yerel/backup/env yolu | {audit.get('risky_path_count')} |
| 50KB+ Python dosyası | {audit.get('large_py_count')} |
| 50KB+ route/route benzeri Python dosyası | {audit.get('large_route_py_count')} |
| Phase/P/V isimli Python dosyası | {audit.get('phase_py_count')} |
| Olası secret anahtarı | {audit.get('possible_secret_hit_count')} |

## Kritik yorum

Bu rapor değer göstermez; yalnızca dosya yolu ve anahtar adlarını gösterir. Gerçek parola/token/secret değerleri asla rapora yazılmaz.

## Bulunan env dosyaları

"""
    env_files = audit.get("env_files", [])
    if env_files:
        md += "\n".join(f"- `{x}`" for x in env_files[:100]) + "\n"
    else:
        md += "Env dosyası bulunamadı.\n"

    md += "\n## Backup / sanal ortam klasörleri\n\n"
    backup_dirs = audit.get("backup_dirs_present", [])
    if backup_dirs:
        md += "\n".join(f"- `{x}`" for x in backup_dirs) + "\n"
    else:
        md += "Backup veya sanal ortam klasörü görünmüyor.\n"

    md += "\n## En büyük route dosyaları\n\n"
    md += md_table(audit.get("large_route_py_top", [])) + "\n"

    md += "\n## Riskli dosya örnekleri\n\n"
    if risky_sample:
        md += "\n".join(f"- `{x}`" for x in risky_sample[:80]) + "\n"
    else:
        md += "Riskli yol bulunamadı.\n"

    md += "\n## Olası secret anahtarları\n\n"
    if secret_hits:
        md += "| Dosya | Satır | Anahtar |\n|---|---:|---|\n"
        for hit in secret_hits[:80]:
            md += f"| `{hit.get('path')}` | {hit.get('line')} | `{hit.get('key')}` |\n"
    else:
        md += "Olası secret anahtarı bulunamadı.\n"

    md += f"\n## Sonuç\n\n{MARKER_REPORT}\n"
    md_path.write_text(md, encoding="utf-8")
    return json_path, md_path


def quarantine_items(root: Path, quarantine_env: bool, quarantine_venv: bool) -> Dict[str, object]:
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    quarantine_root = root / "_local_quarantine" / f"bys360_repo_hygiene_p0_{stamp}"
    moved: List[str] = []
    errors: List[Dict[str, str]] = []

    # Top-level risky dirs first.
    candidate_dirs = [root / ".backup", root / ".quality_backup"]
    if quarantine_venv:
        candidate_dirs += [root / ".venv", root / "venv", root / "env"]
    if quarantine_env:
        candidate_dirs += [p for p in root.iterdir() if p.is_file() and is_env_file(p.name) and not is_safe_env_example(p.name)]

    for path in candidate_dirs:
        if not path.exists():
            continue
        rel = norm_rel(path, root)
        dest = quarantine_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(path), str(dest))
            moved.append(rel)
        except Exception as exc:
            errors.append({"path": rel, "error": str(exc)})

    # Individual bak/tmp files after dirs moved.
    for path in list(iter_files(root)):
        if not path.exists() or not path.is_file():
            continue
        if not should_quarantine_path(path, root, quarantine_env=quarantine_env, quarantine_venv=quarantine_venv):
            continue
        rel = norm_rel(path, root)
        dest = quarantine_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.move(str(path), str(dest))
            moved.append(rel)
        except Exception as exc:
            errors.append({"path": rel, "error": str(exc)})

    return {"quarantine_root": norm_rel(quarantine_root, root), "moved": moved, "errors": errors}


def git_is_repo(root: Path) -> bool:
    try:
        r = subprocess.run(["git", "-C", str(root), "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True, timeout=20)
        return r.returncode == 0 and r.stdout.strip() == "true"
    except Exception:
        return False


def git_tracked_files(root: Path) -> List[str]:
    r = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True, timeout=60)
    if r.returncode != 0:
        return []
    return [x.decode("utf-8", errors="ignore") for x in r.stdout.split(b"\0") if x]


def git_rm_cached(root: Path, files: Sequence[str]) -> Dict[str, object]:
    removed: List[str] = []
    errors: List[str] = []
    chunk: List[str] = []

    def flush(items: List[str]) -> None:
        nonlocal removed, errors
        if not items:
            return
        cmd = ["git", "-C", str(root), "rm", "--cached", "--ignore-unmatch", "--"] + items
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if r.returncode == 0:
            removed.extend(items)
        else:
            errors.append((r.stderr or r.stdout or "git rm cached failed").strip())

    for f in files:
        chunk.append(f)
        if len(chunk) >= 100:
            flush(chunk)
            chunk = []
    flush(chunk)
    return {"removed_from_index": removed, "errors": errors}


def update_git_index(root: Path) -> Dict[str, object]:
    if not git_is_repo(root):
        return {"git_repo": False, "removed_from_index": [], "errors": ["Git reposu bulunamadı veya git komutu çalışmadı."]}
    tracked = git_tracked_files(root)
    risky_tracked = [f for f in tracked if is_risky_path(f)]
    res = git_rm_cached(root, risky_tracked)
    res["git_repo"] = True
    res["risky_tracked_count"] = len(risky_tracked)
    return res


def write_apply_log(root: Path, payload: Dict[str, object]) -> Path:
    reports_dir = root / "reports" / "quality"
    reports_dir.mkdir(parents=True, exist_ok=True)
    path = reports_dir / "bys360_repo_hygiene_p0_v2_17_0_apply_log.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BYS360 Repo Hygiene P0 V2.17.0")
    parser.add_argument("--project-root", required=True, help="BYS360 proje kökü, örn: C:\\bys360\\project")
    parser.add_argument("--mode", choices=["audit", "apply"], default="audit")
    parser.add_argument("--update-git-index", action="store_true", help="Riskli dosyaları Git index'ten kaldırır, çalışma kopyasında bırakır.")
    parser.add_argument("--quarantine-env", action="store_true", help=".env dosyalarını karantinaya taşır. Varsayılan: taşımaz.")
    parser.add_argument("--quarantine-venv", action="store_true", help=".venv/venv/env klasörlerini karantinaya taşır. Varsayılan: taşımaz.")
    args = parser.parse_args(argv)

    root = Path(args.project_root).resolve()
    if not root.exists() or not root.is_dir():
        print(f"Proje kökü bulunamadı: {root}", file=sys.stderr)
        return 2

    audit = collect_audit(root)
    json_report, md_report = write_reports(root, audit)
    result: Dict[str, object] = {
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(root),
        "json_report": norm_rel(json_report, root),
        "md_report": norm_rel(md_report, root),
        "audit_summary": {
            "total_files_scanned": audit.get("total_files_scanned"),
            "risky_path_count": audit.get("risky_path_count"),
            "large_py_count": audit.get("large_py_count"),
            "large_route_py_count": audit.get("large_route_py_count"),
            "phase_py_count": audit.get("phase_py_count"),
            "possible_secret_hit_count": audit.get("possible_secret_hit_count"),
        },
    }

    if args.mode == "apply":
        gitignore_changed = append_block_once(root / ".gitignore", GITIGNORE_BLOCK, "BYS360 P0 repo hygiene V2.17.0")
        git_exclude_changed = False
        if (root / ".git").exists():
            git_exclude_changed = append_block_once(root / ".git" / "info" / "exclude", GITIGNORE_BLOCK, "BYS360 P0 repo hygiene V2.17.0")
        env_changed, env_count, env_example_rel = generate_env_example(root)
        quarantine = quarantine_items(root, quarantine_env=args.quarantine_env, quarantine_venv=args.quarantine_venv)
        git_result = update_git_index(root) if args.update_git_index else {"skipped": True}
        result["apply"] = {
            "gitignore_changed": gitignore_changed,
            "git_info_exclude_changed": git_exclude_changed,
            "env_example_changed": env_changed,
            "env_example_key_count": env_count,
            "env_example": env_example_rel,
            "quarantine": quarantine,
            "git_index_cleanup": git_result,
            "notes": [
                ".env ve .venv varsayılan olarak fiziksel taşınmaz; sadece .gitignore ve istenirse git index temizlenir.",
                "Gerçek secret değerleri rotasyon yapılmadan güvenli sayılmaz.",
                "Git geçmişinde secret varsa ayrıca git-filter-repo/BFG ile tarihçe temizliği gerekir.",
            ],
        }
        log_path = write_apply_log(root, result)
        result["apply_log"] = norm_rel(log_path, root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print(MARKER_APPLY)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print(MARKER_REPORT)

    print(MARKER_OK)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
