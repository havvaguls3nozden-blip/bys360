# -*- coding: utf-8 -*-
"""
BYS360 Repo Hygiene P0.2 Active Audit & Health V2.17.2

Amaç:
- P0/P0.1 temizlikten sonra aktif proje ağacını karantina/yedek klasörlerini saymadan ölçmek.
- compileall ve application factory import testini tek raporda toplamak.
- Kalan teknik borcu P1 route refactor öncesi netleştirmek.

Bu script canlı uygulama kodunu değiştirmez; yalnızca rapor üretir.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, List, Tuple

VERSION = "V2.17.2"
MARKER_OK = "BYS360_REPO_HYGIENE_P0_2_ACTIVE_AUDIT_HEALTH_V2_17_2_OK"
MARKER_REPORT = "BYS360_REPO_HYGIENE_P0_2_ACTIVE_AUDIT_HEALTH_V2_17_2_REPORT_OK"
MARKER_HEALTH = "BYS360_REPO_HYGIENE_P0_2_ACTIVE_AUDIT_HEALTH_V2_17_2_HEALTH_OK"

REPORT_JSON = "reports/quality/bys360_repo_hygiene_p0_2_active_audit_health_v2_17_2_report.json"
REPORT_MD = "reports/quality/bys360_repo_hygiene_p0_2_active_audit_health_v2_17_2_report.md"

SAFE_ENV_EXAMPLES = {
    ".env.example",
    ".env.production.example",
    ".env.template",
    ".env.sample",
    ".env.local.example",
}

# Bu klasörler aktif proje borcuna dahil edilmez; karantina/geçici/generator/cachedir.
SKIP_DIRS = {
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
    ".cache",
    "node_modules",
    ".dart_tool",
    "build",
    "dist",
    "htmlcov",
    "_local_quarantine",
    "_local_secrets",
}

# Bunlar aktif ağaçta kalırsa risk olarak raporlanır; traversal yapılmaz.
RISK_DIR_NAMES = {
    ".backup",
    ".quality_backup",
    "_backup",
    "_bys360_backups",
}

TEXT_EXTS = {
    ".py", ".ps1", ".txt", ".md", ".yml", ".yaml", ".json", ".ini", ".cfg",
    ".env", ".example", ".html", ".css", ".js", ".dart", ".sql", ".toml"
}

SECRET_KEY_RE = re.compile(
    r"(?i)(secret|password|passwd|pwd|token|apikey|api_key|access[_-]?token|dsn|database_url|sqlalchemy_database_uri|private[_-]?key|encryption[_-]?key|smtp|mail_.*pass|redis_url)"
)
PHASE_RE = re.compile(r"(?i)(phase\d+|_phase\d+|ai_phase\d+|phase\d+[a-z]?_routes|p\d+_|v\d+_\d+)")


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


def is_risky_path(rel: str, is_dir: bool = False) -> bool:
    p = PurePosixPath(rel)
    parts = {x.lower() for x in p.parts}
    name = p.name.lower()
    low = rel.lower()

    if is_env_file(rel) and not is_safe_env_example(rel):
        return True
    if name in RISK_DIR_NAMES or bool(parts & {x.lower() for x in RISK_DIR_NAMES}):
        return True
    if name.endswith((".bak", ".backup", ".old", ".orig")):
        return True
    if name.startswith("tmp_") or name.endswith("_tmp.py"):
        return True
    if name.endswith((".dump", ".db", ".sqlite", ".sqlite3", ".log")):
        return True
    if "/backups/" in f"/{low}/" or low.startswith("backups/"):
        return True
    if low.startswith("project/") and ("/app/" in f"/{low}/" or "/scripts/" in f"/{low}/"):
        return True
    return False


def iter_active_files(root: Path) -> Tuple[List[Path], List[str], List[str]]:
    """Return files, skipped dirs, risky dirs from active tree."""
    files: List[Path] = []
    skipped_dirs: List[str] = []
    risky_dirs: List[str] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dpath = Path(dirpath)
        rel_dir = norm_rel(dpath, root)
        if rel_dir == ".":
            rel_dir = ""

        keep_dirs = []
        for d in dirnames:
            full = dpath / d
            rel = norm_rel(full, root)
            low = d.lower()
            if low in {x.lower() for x in SKIP_DIRS}:
                skipped_dirs.append(rel)
                continue
            if low in {x.lower() for x in RISK_DIR_NAMES}:
                risky_dirs.append(rel)
                # Risk klasörün içini tarama; aktif kodu şişirmesin.
                continue
            keep_dirs.append(d)
        dirnames[:] = keep_dirs

        for name in filenames:
            full = dpath / name
            files.append(full)

    return files, skipped_dirs, risky_dirs


def safe_read_text(path: Path, limit: int = 700_000) -> str:
    try:
        if path.stat().st_size > limit:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def scan_active_tree(root: Path) -> Dict[str, object]:
    files, skipped_dirs, risky_dirs = iter_active_files(root)

    risky_paths: List[str] = []
    large_py: List[Dict[str, object]] = []
    large_route_py: List[Dict[str, object]] = []
    phase_py: List[str] = []
    possible_secret_hits: List[Dict[str, str]] = []
    duplicate_project_tree: List[str] = []
    env_files: List[str] = []

    for rel in risky_dirs:
        risky_paths.append(rel)

    for path in files:
        rel = norm_rel(path, root)
        p = PurePosixPath(rel)
        suffix = path.suffix.lower()
        name = p.name.lower()

        if is_risky_path(rel, is_dir=False):
            risky_paths.append(rel)
        if is_env_file(rel):
            env_files.append(rel)
        if rel.startswith("project/") and ("/app/" in f"/{rel}/" or "/scripts/" in f"/{rel}/"):
            duplicate_project_tree.append(rel)

        try:
            size = path.stat().st_size
        except Exception:
            size = 0

        if suffix == ".py" and size >= 50_000:
            item = {"path": rel, "size_kb": round(size / 1024, 1)}
            large_py.append(item)
            if name == "routes.py" or name.endswith("_routes.py") or "/routes/" in rel.lower():
                large_route_py.append(item)

        if suffix == ".py" and PHASE_RE.search(rel):
            phase_py.append(rel)

        # Secret taraması değer göstermeden sadece dosya/satır anahtarı raporlar.
        if suffix in TEXT_EXTS or name.startswith(".env"):
            text = safe_read_text(path)
            if text:
                for idx, line in enumerate(text.splitlines(), start=1):
                    if SECRET_KEY_RE.search(line):
                        stripped = line.strip()
                        if not stripped or stripped.startswith("#"):
                            continue
                        # değer yerine sadece anahtar/bağlam
                        key = stripped.split("=", 1)[0].strip()[:80] if "=" in stripped else stripped[:80]
                        possible_secret_hits.append({"path": rel, "line": str(idx), "key_or_context": key})
                        break

    large_py.sort(key=lambda x: x["size_kb"], reverse=True)
    large_route_py.sort(key=lambda x: x["size_kb"], reverse=True)

    return {
        "total_active_files_scanned": len(files),
        "skipped_dir_count": len(skipped_dirs),
        "skipped_dirs_sample": skipped_dirs[:30],
        "risky_path_count": len(sorted(set(risky_paths))),
        "risky_paths_sample": sorted(set(risky_paths))[:80],
        "env_files": sorted(set(env_files)),
        "large_py_count": len(large_py),
        "large_py_top": large_py[:30],
        "large_route_py_count": len(large_route_py),
        "large_route_py_top": large_route_py[:30],
        "phase_py_count": len(set(phase_py)),
        "phase_py_sample": sorted(set(phase_py))[:80],
        "possible_secret_hit_count": len(possible_secret_hits),
        "possible_secret_hits_sample": possible_secret_hits[:80],
        "duplicate_project_tree_count": len(set(duplicate_project_tree)),
        "duplicate_project_tree_sample": sorted(set(duplicate_project_tree))[:80],
    }


def run_command(root: Path, cmd: List[str], timeout: int = 120) -> Dict[str, object]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
        )
        output = proc.stdout or ""
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "cmd": cmd,
            "output_tail": output[-12000:],
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "returncode": "timeout",
            "cmd": cmd,
            "output_tail": (exc.stdout or "")[-12000:] if isinstance(exc.stdout, str) else "",
        }
    except Exception as exc:
        return {"ok": False, "returncode": "error", "cmd": cmd, "output_tail": repr(exc)}


def run_health(root: Path, skip_compile: bool = False) -> Dict[str, object]:
    health: Dict[str, object] = {}

    if skip_compile:
        health["compileall"] = {"ok": True, "skipped": True, "note": "--skip-compile kullanildi."}
    else:
        health["compileall"] = run_command(root, [sys.executable, "-m", "compileall", "app", "config.py", "scripts"], timeout=180)

    # create_app önce, yoksa create_bys360_application dene.
    create_app_code = (
        "import sys\n"
        "from app import create_app\n"
        "app=create_app()\n"
        "print('BYS360_APP_CREATE_OK', len(app.blueprints), 'routes', len(list(app.url_map.iter_rules())))\n"
    )
    res = run_command(root, [sys.executable, "-c", create_app_code], timeout=120)
    if not res.get("ok"):
        alt_code = (
            "from app import create_bys360_application\n"
            "app=create_bys360_application()\n"
            "print('BYS360_APP_CREATE_OK', len(app.blueprints), 'routes', len(list(app.url_map.iter_rules())))\n"
        )
        alt = run_command(root, [sys.executable, "-c", alt_code], timeout=120)
        health["app_factory"] = {"primary": res, "fallback": alt, "ok": bool(alt.get("ok"))}
    else:
        health["app_factory"] = {"primary": res, "ok": True}

    # Raporlar klasörünün yazılabilirliği.
    try:
        out_dir = root / "reports" / "quality"
        out_dir.mkdir(parents=True, exist_ok=True)
        probe = out_dir / ".p0_2_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        health["reports_writeable"] = {"ok": True, "path": str(out_dir)}
    except Exception as exc:
        health["reports_writeable"] = {"ok": False, "error": repr(exc)}

    all_ok = bool(health.get("compileall", {}).get("ok")) and bool(health.get("app_factory", {}).get("ok")) and bool(health.get("reports_writeable", {}).get("ok"))
    health["overall_ok"] = all_ok
    return health


def classify_next_step(active: Dict[str, object], health: Dict[str, object] | None) -> Dict[str, object]:
    suggestions: List[str] = []
    if health and not health.get("overall_ok"):
        suggestions.append("P0 saglik kontrolu tam gecmeden P1 refactor'a gecmeyin.")
    if int(active.get("possible_secret_hit_count", 0)) > 0:
        suggestions.append("Secret hit sayisi tek tek incelenmeli; gercek degerler varsa parola/token rotasyonu yapilmali.")
    if int(active.get("large_route_py_count", 0)) > 0:
        suggestions.append("P1 icin once en buyuk route dosyalari servis katmanina ayrilmali.")
    if int(active.get("phase_py_count", 0)) > 100:
        suggestions.append("Phase dosyalari icin manifest/kullanim envanteri cikarilmali; aktif olmayanlar karantinaya alinmali.")
    if int(active.get("duplicate_project_tree_count", 0)) > 0:
        suggestions.append("Kok dizin icindeki project/ kopyasi aktif proje degilse ayri klasore alinmali veya ignore edilmeli.")
    if int(active.get("risky_path_count", 0)) == 0 and (not health or health.get("overall_ok")):
        suggestions.append("P0 aktif agac temiz gorunuyor; P1 route refactor planina gecilebilir.")
    return {"next_step_suggestions": suggestions}


def write_reports(root: Path, payload: Dict[str, object]) -> Tuple[str, str]:
    json_path = root / REPORT_JSON
    md_path = root / REPORT_MD
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    active = payload.get("active_audit", {})
    health = payload.get("health", {})
    suggestions = payload.get("classification", {}).get("next_step_suggestions", [])

    def top_lines(items: Iterable[object], limit: int = 20) -> str:
        lines: List[str] = []
        for i, item in enumerate(items):
            if i >= limit:
                break
            if isinstance(item, dict):
                lines.append(f"- `{item}`")
            else:
                lines.append(f"- `{item}`")
        return "\n".join(lines) if lines else "- Yok"

    compile_ok = health.get("compileall", {}).get("ok") if isinstance(health, dict) else None
    app_ok = health.get("app_factory", {}).get("ok") if isinstance(health, dict) else None
    overall_ok = health.get("overall_ok") if isinstance(health, dict) else None

    md = f"""# BYS360 P0.2 Aktif Ağaç Audit ve Sağlık Raporu — {VERSION}

Üretim zamanı: `{payload.get('generated_at')}`  
Proje kökü: `{payload.get('project_root')}`  
Mod: `{payload.get('mode')}`

## Sağlık Özeti

| Kontrol | Sonuç |
|---|---:|
| compileall | `{compile_ok}` |
| application factory | `{app_ok}` |
| genel sağlık | `{overall_ok}` |

## Aktif Ağaç Özeti

| Gösterge | Değer |
|---|---:|
| Aktif taranan dosya | {active.get('total_active_files_scanned')} |
| Atlanan karantina/cache dizini | {active.get('skipped_dir_count')} |
| Riskli aktif yol | {active.get('risky_path_count')} |
| Büyük Python dosyası | {active.get('large_py_count')} |
| Büyük route dosyası | {active.get('large_route_py_count')} |
| Phase isimli Python dosyası | {active.get('phase_py_count')} |
| Olası secret anahtarı | {active.get('possible_secret_hit_count')} |
| İç içe project kopyası göstergesi | {active.get('duplicate_project_tree_count')} |

## En Büyük Route Dosyaları

{top_lines(active.get('large_route_py_top', []), 30)}

## Riskli Aktif Yol Örnekleri

{top_lines(active.get('risky_paths_sample', []), 80)}

## Olası Secret Hit Örnekleri

Değerler rapora yazılmaz; yalnızca dosya/satır/anahtar bağlamı gösterilir.

{top_lines(active.get('possible_secret_hits_sample', []), 80)}

## Phase Dosyası Örnekleri

{top_lines(active.get('phase_py_sample', []), 80)}

## Önerilen Sonraki Adımlar

{top_lines(suggestions, 20)}

## Not

Bu rapor `_local_quarantine`, `.venv`, cache ve build klasörlerini aktif teknik borç sayımından hariç tutar. Bu nedenle P0/P0.1 sonrası gerçek aktif ağaç durumunu görmek için eski P0 raporundan daha sağlıklı bir ölçümdür.
"""
    md_path.write_text(md, encoding="utf-8")
    return str(json_path.relative_to(root)), str(md_path.relative_to(root))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--mode", choices=["audit", "health", "all"], default="all")
    parser.add_argument("--skip-compile", action="store_true")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    if not root.exists():
        print(json.dumps({"ok": False, "error": f"Proje kok dizini bulunamadi: {root}"}, ensure_ascii=False, indent=2))
        return 2

    active = scan_active_tree(root) if args.mode in {"audit", "all"} else {}
    health = run_health(root, skip_compile=args.skip_compile) if args.mode in {"health", "all"} else {}
    payload: Dict[str, object] = {
        "version": VERSION,
        "mode": args.mode,
        "generated_at": _dt.datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "active_audit": active,
        "health": health,
    }
    payload["classification"] = classify_next_step(active, health if health else None)
    json_report, md_report = write_reports(root, payload)
    payload["json_report"] = json_report
    payload["md_report"] = md_report

    # Konsola kısa özet ver.
    console = {
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(root),
        "active_summary": {
            "total_active_files_scanned": active.get("total_active_files_scanned"),
            "risky_path_count": active.get("risky_path_count"),
            "large_py_count": active.get("large_py_count"),
            "large_route_py_count": active.get("large_route_py_count"),
            "phase_py_count": active.get("phase_py_count"),
            "possible_secret_hit_count": active.get("possible_secret_hit_count"),
            "duplicate_project_tree_count": active.get("duplicate_project_tree_count"),
        } if active else {},
        "health_summary": {
            "compileall_ok": health.get("compileall", {}).get("ok") if health else None,
            "app_factory_ok": health.get("app_factory", {}).get("ok") if health else None,
            "overall_ok": health.get("overall_ok") if health else None,
        } if health else {},
        "json_report": json_report,
        "md_report": md_report,
    }
    print(json.dumps(console, ensure_ascii=False, indent=2))
    print(MARKER_REPORT)
    if health and health.get("overall_ok"):
        print(MARKER_HEALTH)
    print(MARKER_OK)
    return 0 if (not health or health.get("overall_ok")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
