from __future__ import annotations
import argparse, json, py_compile
from pathlib import Path
VERSION = "BYS360_EXECUTIVE_SUMMARY_V3_LOCAL_PRO_UI"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", default=".")
    args = ap.parse_args()
    root = Path(args.project_root).resolve()
    errors = []
    route = root / "app/dashboard/executive_summary_routes.py"
    tpl = root / "app/templates/dashboard/executive_summary.html"
    for p in [route, tpl]:
        if not p.exists(): errors.append(f"Eksik dosya: {p}")
    if route.exists():
        try: py_compile.compile(str(route), doraise=True)
        except Exception as e: errors.append(f"Route compile hatası: {e}")
        text = route.read_text(encoding="utf-8", errors="ignore")
        for needle in ["system_admin_required", "_v3_enrich_context", "BYS360_EXECUTIVE_SUMMARY_V3_LOCAL_PRO_UI"]:
            if needle not in text: errors.append(f"Route içinde beklenen ifade yok: {needle}")
    if tpl.exists():
        text = tpl.read_text(encoding="utf-8", errors="ignore")
        for needle in ["execv3", "otomatik-epostalar", "mail-loglari", "zamanlanmis-isler", "test-gonderimi", "Yönetici Özeti Alıcıları"]:
            if needle not in text: errors.append(f"Template içinde beklenen ifade yok: {needle}")
    ok = not errors
    print(json.dumps({"ok": ok, "version": VERSION, "errors": errors}, ensure_ascii=False, indent=2))
    if ok:
        print(f"{VERSION}_CHECK_OK")
    raise SystemExit(0 if ok else 1)
if __name__ == "__main__": main()
