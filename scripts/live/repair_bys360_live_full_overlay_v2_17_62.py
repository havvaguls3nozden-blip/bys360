from __future__ import annotations

import argparse
import json
import py_compile
import re
import shutil
from datetime import datetime
from pathlib import Path

VERSION = "V2.17.62"
PREV = "V2.17.61"
KNOWN_BOM_FILES = [
    Path("app/communication/daily_weather_mail_routes.py"),
    Path("app/services/executive_mail_center_v2.py"),
    Path("scripts/executive/seed_executive_summary_menu_v2_14_8.py"),
    Path("scripts/performance_mail_automation_runner.py"),
    Path("scripts/scheduled/run_cic_staff_noon.py"),
]


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def project_backup_root(root: Path, stamp: str) -> Path:
    if root.name.lower() == "project":
        return root.parent / "backups" / f"BYS360_LIVE_FULL_{VERSION}_{stamp}"
    return root / "_backups" / f"BYS360_LIVE_FULL_{VERSION}_{stamp}"


def rel_s(rel: Path) -> str:
    return str(rel).replace("\\", "/")


def read_text(path: Path) -> str:
    data = path.read_bytes()
    for enc in ("utf-8-sig", "utf-8", "cp1254", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def backup_file(root: Path, backup_root: Path, rel: Path, changed: list[str]) -> None:
    src = root / rel
    if not src.exists() or src.is_dir():
        return
    dst = backup_root / rel
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    s = rel_s(rel)
    if s not in changed:
        changed.append(s)


def normalize_bom(root: Path, backup_root: Path, changed: list[str]) -> list[str]:
    fixed: list[str] = []
    candidates: list[Path] = list(KNOWN_BOM_FILES)
    for folder in (root / "app", root / "scripts"):
        if folder.exists():
            for path in folder.rglob("*.py"):
                try:
                    data = path.read_bytes()
                except OSError:
                    continue
                if data.startswith(b"\xef\xbb\xbf"):
                    rel = path.relative_to(root)
                    if rel not in candidates:
                        candidates.append(rel)
    for rel in candidates:
        path = root / rel
        if not path.exists():
            continue
        data = path.read_bytes()
        if data.startswith(b"\xef\xbb\xbf") or read_text(path).startswith("\ufeff"):
            backup_file(root, backup_root, rel, changed)
            write_text(path, read_text(path).lstrip("\ufeff"))
            fixed.append(rel_s(rel))
    return fixed


def has_real_split_body(text: str) -> bool:
    """Sadece gerçekten bölünmüş </bo\n dy> kapanışını yakalar; normal </body> false döner."""
    if re.search(r"</bo\s*(?:\r?\n\s*)+dy\s*>", text, flags=re.I):
        return True
    if re.search(r"^\s*dy>\s*$", text, flags=re.M | re.I):
        return True
    return False


def patch_v21761_checker_bug(root: Path, backup_root: Path, changed: list[str]) -> dict:
    """17.61 scriptindeki yanlış '</bo' kontrolünü düzeltir; böylece eski check de tekrar çalışır."""
    rel = Path("scripts/live/repair_bys360_live_full_overlay_v2_17_61.py")
    path = root / rel
    if not path.exists():
        return {"changed": False, "detail": "17.61 repair script bulunamadı; sorun yok"}

    original = read_text(path)
    text = original

    new_condition = 'add("base_no_split_body", re.search(r"</bo\\s*(?:\\r?\\n\\s*)+dy\\s*>", text, re.I) is None and re.search(r"^\\s*dy>\\s*$", text, re.M | re.I) is None, "Bölünmüş body etiketi yok")'
    # 17.61 paketinde bu satır iki farklı biçimde üretilebildi; satırın tamamını güvenli koşulla değiştir.
    text = re.sub(
        r'^\s*add\("base_no_split_body",.*?"Bölünmüş body etiketi yok"\)\s*$',
        "        " + new_condition,
        text,
        count=1,
        flags=re.M,
    )

    # Python 3.14'te görülen SyntaxWarning: invalid escape sequence '\/' uyarısını da temizle.
    # JS regex çıktısı korunur; sadece Python kaynak içinde slash kaçışları geçerli hale gelir.
    text = text.replace('replace(/\\/+$/, "")', 'replace(/\\\\/+$/, "")')
    text = text.replace('/\\/logout\\/?$', '/\\\\/logout\\\\/?$')
    text = text.replace('value === "/logout" || /\\/logout\\/?$/.test', 'value === "/logout" || /\\\\/logout\\\\/?$/.test')

    if text != original:
        backup_file(root, backup_root, rel, changed)
        write_text(path, text)
        return {"changed": True, "detail": "17.61 check koşulu düzeltildi"}
    return {"changed": False, "detail": "17.61 check koşulu zaten düzeltilmiş görünüyor"}


def check_project(root: Path) -> dict:
    report: dict = {"version": VERSION, "ok": True, "checks": []}

    def add(name: str, ok: bool, detail: str = "") -> None:
        report["checks"].append({"name": name, "ok": bool(ok), "detail": detail})
        if not ok:
            report["ok"] = False

    base = root / "app/templates/base.html"
    if base.exists():
        text = read_text(base)
        add("base_exists", True, "app/templates/base.html bulundu")
        add("base_no_real_split_body", not has_real_split_body(text), "Gerçek bölünmüş body etiketi yok")
        add(
            "base_has_live_marker",
            "BYS360_LIVE_FULL_OVERLAY_V2_17_61_BODY_BEGIN" in text or "BYS360_LIVE_FULL_OVERLAY_V2_17_62_BODY_BEGIN" in text,
            "Canlı temiz kuyruk marker var",
        )
        add("base_single_final_html", re.search(r"</body>\s*</html>\s*\Z", text, re.S | re.I) is not None, "Temiz </body></html> kapanışı")
        add("base_no_after_html", re.search(r"</html>\s*\S", text, re.S | re.I) is None, "</html> sonrası içerik yok")
        add("base_has_csrf_meta", "meta name=\"csrf-token\"" in text, "CSRF meta token var")
    else:
        add("base_exists", False, "app/templates/base.html bulunamadı")

    eh = root / "app/error_handlers.py"
    if eh.exists():
        et = read_text(eh)
        add("csrf_recovery_handler", "_handle_expired_csrf_response" in et and "X-BYS360-CSRF-Recover" in et, "CSRF recovery handler var")
        try:
            py_compile.compile(str(eh), doraise=True)
            add("error_handlers_compile", True, "error_handlers.py compile OK")
        except Exception as exc:
            add("error_handlers_compile", False, str(exc))
    else:
        add("error_handlers_exists", False, "app/error_handlers.py bulunamadı")

    for rel in KNOWN_BOM_FILES:
        path = root / rel
        if path.exists():
            add("bom_clean:" + rel_s(rel), not path.read_bytes().startswith(b"\xef\xbb\xbf"), "UTF-8 BOM kontrolü")

    # 17.61 assetleri canlıda kalabilir; bu hotfix check mantığını düzeltir, asset isimlerini gereksiz değiştirmez.
    for rel in [Path("app/static/css/bys360_live_full_v2_17_61.css"), Path("app/static/js/bys360_form_csrf_guard_v2_17_61.js")]:
        add("asset_exists:" + rel_s(rel), (root / rel).exists(), "Canlı asset kontrolü")

    for rel in [
        Path("scripts/live/repair_bys360_live_full_overlay_v2_17_61.py"),
        Path("scripts/live/repair_bys360_live_full_overlay_v2_17_62.py"),
        Path("scripts/quality/check_bys360_live_full_overlay_v2_17_62.py"),
    ]:
        path = root / rel
        if path.exists():
            try:
                py_compile.compile(str(path), doraise=True)
                add("script_compile:" + rel_s(rel), True, "script compile OK")
            except Exception as exc:
                add("script_compile:" + rel_s(rel), False, str(exc))
    return report


def write_report(root: Path, report: dict) -> None:
    out = root / "reports/quality"
    out.mkdir(parents=True, exist_ok=True)
    (out / "bys360_live_full_overlay_v2_17_62_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    rows = [
        "# BYS360 Live Full Overlay V2.17.62 CheckFix Kontrol Raporu",
        "",
        f"overall_ok: `{report.get('ok')}`",
        "",
        "| Kontrol | Sonuç | Detay |",
        "|---|---:|---|",
    ]
    for item in report.get("checks", []):
        detail = str(item.get("detail", "")).replace("|", "/")
        rows.append(f"| `{item.get('name')}` | `{item.get('ok')}` | {detail} |")
    (out / "bys360_live_full_overlay_v2_17_62_report.md").write_text("\n".join(rows) + "\n", encoding="utf-8")


def write_docs(root: Path, backup_root: Path, changed: list[str]) -> None:
    rel = Path("docs/BYS360_LIVE_FULL_OVERLAY_V2_17_62_CHECKFIX_README.md")
    text = """# BYS360 LIVE FULL OVERLAY V2.17.62 CHECKFIX

Bu paket V2.17.61 içinde kalan hatalı `base_no_split_body` kontrolünü düzeltir.
Sorunun nedeni: check koşulu normal `</body>` kapanışını da `</bo` içerdiği için yanlışlıkla başarısız sayıyordu.

Bu paket canlı güvenliği kapatmaz, `.env` veya şifre içermez, veritabanına müdahale etmez.

## Uygulama

```powershell
cd C:\\bys360\\project
Expand-Archive -LiteralPath "$env:USERPROFILE\\Downloads\\BYS360_LIVE_FULL_OVERLAY_V2_17_62_CHECKFIX.zip" -DestinationPath "C:\\bys360\\project" -Force
powershell -ExecutionPolicy Bypass -File .\\scripts\\windows\\repair_bys360_live_full_overlay_v2_17_62.ps1 -ProjectRoot "C:\\bys360\\project" -Mode all
```

## Kontrol

```powershell
powershell -ExecutionPolicy Bypass -File .\\scripts\\windows\\check_bys360_live_full_overlay_v2_17_62.ps1 -ProjectRoot "C:\\bys360\\project"
```
"""
    backup_file(root, backup_root, rel, changed)
    write_text(root / rel, text)


def apply(root: Path) -> dict:
    stamp = now_stamp()
    backup_root = project_backup_root(root, stamp)
    backup_root.mkdir(parents=True, exist_ok=True)
    changed: list[str] = []
    result = {"version": VERSION, "applied_at": stamp, "backup_root": str(backup_root), "changed_files": changed, "actions": []}
    result["actions"].append({"name": "normalize_bom", "fixed": normalize_bom(root, backup_root, changed)})
    result["actions"].append({"name": "patch_v21761_checker_bug", **patch_v21761_checker_bug(root, backup_root, changed)})
    write_docs(root, backup_root, changed)
    report = check_project(root)
    write_report(root, report)
    result["check"] = report
    return result


def rollback(root: Path, backup_root: Path) -> dict:
    if not backup_root.exists():
        raise SystemExit(f"BackupRoot bulunamadı: {backup_root}")
    restored: list[str] = []
    for src in backup_root.rglob("*"):
        if src.is_file():
            rel = src.relative_to(backup_root)
            dst = root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            restored.append(rel_s(rel))
    return {"version": VERSION, "rollback_from": str(backup_root), "restored": restored, "ok": True}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=f"BYS360 Live Full Overlay {VERSION} CheckFix")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["apply", "check", "all", "rollback"], default="all")
    parser.add_argument("--backup-root", default="")
    args = parser.parse_args(argv)
    root = Path(args.project_root).resolve()
    if not root.exists():
        raise SystemExit(f"ProjectRoot bulunamadı: {root}")
    if args.mode == "rollback":
        if not args.backup_root:
            raise SystemExit("Rollback için --backup-root zorunlu")
        result = rollback(root, Path(args.backup_root).resolve())
    elif args.mode == "check":
        result = check_project(root)
        write_report(root, result)
    else:
        result = apply(root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.mode == "check" and not result.get("ok"):
        return 2
    if args.mode in {"apply", "all"} and not result.get("check", {}).get("ok", False):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
