# -*- coding: utf-8 -*-
"""BYS360 Anasayfa Prestij SAFE V1A geri alma aracı.

Amaç:
- Maintenance/Prestij SAFE V1/V1A tasarım kaplamasını kaldırmak.
- Mevcut home.html omurgasını, portal sekmelerini, hava durumu, feed ve diğer alanları korumak.
- Yalnızca home.html içindeki prestij CSS/JS bağlantı bloklarını kaldırmak.
- Uygulamadan önce otomatik yedek almak.

Not:
Bu script basın hero şablonunu zorla geri döndürmez. Çünkü son projede basın hero alanı
V4 ile bilinçli kaldırılmış olabilir. Eski tasarım görünümüne dönmek için CSS/JS linklerini
kaldırmak yeterlidir.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import py_compile
import re
from pathlib import Path

PACKAGE = "BYS360_HOME_PRESTIGE_SAFE_V1A_ROLLBACK"
HOME_REL = Path("app/templates/home.html")
CSS_FILES = [
    Path("app/static/css/bys360_home_prestige_safe_v1a.css"),
    Path("app/static/css/bys360_home_prestige_safe_v1.css"),
    Path("app/static/css/bys360_home_prestige_v1.css"),
]
JS_FILES = [
    Path("app/static/js/bys360_home_prestige_safe_v1a.js"),
    Path("app/static/js/bys360_home_prestige_safe_v1.js"),
    Path("app/static/js/bys360_home_prestige_v1.js"),
]

# Marker blokları varsa onları temizler.
BLOCK_PATTERNS = [
    r"\n?\s*<!--\s*BYS360_HOME_PRESTIGE_SAFE_V1A_CSS\s*-->.*?<!--\s*/BYS360_HOME_PRESTIGE_SAFE_V1A_CSS\s*-->\s*\n?",
    r"\n?\s*<!--\s*BYS360_HOME_PRESTIGE_SAFE_V1A_JS\s*-->.*?<!--\s*/BYS360_HOME_PRESTIGE_SAFE_V1A_JS\s*-->\s*\n?",
    r"\n?\s*<!--\s*BYS360_HOME_PRESTIGE_SAFE_V1_CSS\s*-->.*?<!--\s*/BYS360_HOME_PRESTIGE_SAFE_V1_CSS\s*-->\s*\n?",
    r"\n?\s*<!--\s*BYS360_HOME_PRESTIGE_SAFE_V1_JS\s*-->.*?<!--\s*/BYS360_HOME_PRESTIGE_SAFE_V1_JS\s*-->\s*\n?",
    r"\n?\s*<!--\s*BYS360_HOME_PRESTIGE_V1_CSS\s*-->.*?<!--\s*/BYS360_HOME_PRESTIGE_V1_CSS\s*-->\s*\n?",
    r"\n?\s*<!--\s*BYS360_HOME_PRESTIGE_V1_JS\s*-->.*?<!--\s*/BYS360_HOME_PRESTIGE_V1_JS\s*-->\s*\n?",
]

# Marker blokları bozulduysa veya yarım kaldıysa link/script satırını da temizler.
LINE_PATTERNS = [
    r"^.*bys360_home_prestige_safe_v1a\.css.*$\n?",
    r"^.*bys360_home_prestige_safe_v1a\.js.*$\n?",
    r"^.*bys360_home_prestige_safe_v1\.css.*$\n?",
    r"^.*bys360_home_prestige_safe_v1\.js.*$\n?",
    r"^.*bys360_home_prestige_v1\.css.*$\n?",
    r"^.*bys360_home_prestige_v1\.js.*$\n?",
]

HOME_CORE_HINTS = [
    "home-faz1-shell",
    "home-faz1-hero",
    "home-faz1-weather-card",
    "home-faz1-quick-grid",
    "portal/_home_feed.html",
    "BYS360_CORPORATE_PORTAL_V1_HOME_FEED",
    "home-faz1-ai-decision-wrap",
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _backup(path: Path, label: str) -> Path:
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = path.parent / "_backup_home_prestige_safe_v1a_rollback"
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / f"{path.name}.bak_{label}_{stamp}"
    backup.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    return backup


def patch_home(root: Path) -> list[dict]:
    home = root / HOME_REL
    if not home.exists():
        raise FileNotFoundError(f"home.html bulunamadı: {home}")

    text = _read(home)
    original = text
    actions: list[dict] = []

    for pattern in BLOCK_PATTERNS:
        text, count = re.subn(pattern, "\n", text, flags=re.S | re.I)
        if count:
            actions.append({"type": "remove_block", "count": count, "pattern": pattern[:80]})

    for pattern in LINE_PATTERNS:
        text, count = re.subn(pattern, "", text, flags=re.M | re.I)
        if count:
            actions.append({"type": "remove_line", "count": count, "pattern": pattern})

    # Aşırı boşlukları sadeleştir ama template yapısını bozma.
    text = re.sub(r"\n{3,}", "\n\n", text)

    if text != original:
        backup = _backup(home, "home_before_rollback")
        _write(home, text)
        actions.append({"type": "backup", "file": str(HOME_REL), "backup": str(backup.relative_to(root))})
        actions.append({"type": "patch", "file": str(HOME_REL), "status": "prestige_links_removed"})
    else:
        actions.append({"type": "noop", "file": str(HOME_REL), "reason": "prestige_links_not_found"})

    return actions


def remove_static_files(root: Path, delete_files: bool) -> list[dict]:
    actions: list[dict] = []
    if not delete_files:
        return actions
    for rel in CSS_FILES + JS_FILES:
        target = root / rel
        if target.exists():
            # Silmek yerine .disabled yapıyoruz; yanlış dosya silme riski daha düşük.
            disabled = target.with_suffix(target.suffix + ".disabled_by_rollback")
            if disabled.exists():
                disabled.unlink()
            target.rename(disabled)
            actions.append({"type": "disable_static", "file": str(rel), "renamed_to": str(disabled.relative_to(root))})
    return actions


def audit(root: Path) -> dict:
    home = root / HOME_REL
    text = _read(home) if home.exists() else ""
    prestige_terms = [
        "bys360_home_prestige_safe_v1a.css",
        "bys360_home_prestige_safe_v1a.js",
        "bys360_home_prestige_safe_v1.css",
        "bys360_home_prestige_safe_v1.js",
        "bys360_home_prestige_v1.css",
        "bys360_home_prestige_v1.js",
    ]
    return {
        "package": PACKAGE,
        "home_exists": home.exists(),
        "home_core_hits": [m for m in HOME_CORE_HINTS if m in text],
        "prestige_links_present": [t for t in prestige_terms if t in text],
        "static_files_present": [str(rel) for rel in CSS_FILES + JS_FILES if (root / rel).exists()],
    }


def check(root: Path, compile_scripts: bool = False) -> dict:
    findings: list[dict] = []
    home = root / HOME_REL
    if not home.exists():
        findings.append({"type": "missing_file", "file": str(HOME_REL)})
    else:
        text = _read(home)
        if not any(m in text for m in HOME_CORE_HINTS):
            findings.append({"type": "home_core_not_detected", "hints": HOME_CORE_HINTS})
        for term in [
            "bys360_home_prestige_safe_v1a.css",
            "bys360_home_prestige_safe_v1a.js",
            "bys360_home_prestige_safe_v1.css",
            "bys360_home_prestige_safe_v1.js",
            "bys360_home_prestige_v1.css",
            "bys360_home_prestige_v1.js",
        ]:
            if term in text:
                findings.append({"type": "prestige_link_still_present", "term": term})

    if compile_scripts:
        script = root / "scripts/portal/rollback_bys360_home_prestige_safe_v1a.py"
        if script.exists():
            try:
                py_compile.compile(str(script), doraise=True)
            except Exception as exc:
                findings.append({"type": "python_compile_error", "file": str(script.relative_to(root)), "error": str(exc)})

    return {"package": PACKAGE, "ok": not findings, "finding_count": len(findings), "findings": findings}


def main() -> int:
    parser = argparse.ArgumentParser(description=f"{PACKAGE} repair/check")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["audit", "rollback", "check", "all"], default="all")
    parser.add_argument("--delete-static", action="store_true", help="Prestij CSS/JS dosyalarını silmek yerine .disabled olarak yeniden adlandırır.")
    parser.add_argument("--compile", action="store_true", dest="compile_scripts")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    result: dict = {"package": PACKAGE, "project_root": str(root), "mode": args.mode}

    if args.mode == "audit":
        result.update(audit(root))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.mode in {"rollback", "all"}:
        actions: list[dict] = []
        actions.extend(patch_home(root))
        actions.extend(remove_static_files(root, args.delete_static))
        result["actions"] = actions

    if args.mode in {"check", "all"}:
        result["check"] = check(root, compile_scripts=args.compile_scripts)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("check", {"ok": True}).get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
