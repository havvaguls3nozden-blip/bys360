# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse
from pathlib import Path

def read_text(path: Path) -> str:
    for enc in ("utf-8","utf-8-sig","cp1254","latin-1"):
        try: return path.read_text(encoding=enc)
        except UnicodeDecodeError: continue
    return path.read_text(encoding="utf-8", errors="ignore")

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--project-root", required=True); a=p.parse_args()
    root=Path(a.project_root).resolve()
    missing=[]
    template=root/"app"/"templates"/"dashboard"/"executive_summary.html"
    if not template.exists(): missing.append(str(template))
    else:
        t=read_text(template)
        for token in ["Yönetici Özeti","Manuel gönderim","Otomatik rapor alıcıları","Mail gönderim logları"]:
            if token not in t: missing.append("template:"+token)
    cfg=root/"data"/"executive_summary"/"recipients.json"
    if not cfg.exists(): missing.append(str(cfg))
    routes_found=False
    for py in (root/"app").rglob("*.py"):
        if "BYS360_EXECUTIVE_SUMMARY_ADVANCED_V2_14_20_ROUTES_START" in read_text(py):
            routes_found=True; break
    if not routes_found: missing.append("advanced routes marker")
    send_script=root/"scripts"/"executive"/"send_daily_executive_summary.py"
    if send_script.exists() and "BYS360_EXECUTIVE_SUMMARY_RECIPIENT_JSON_V2_14_20_START" not in read_text(send_script):
        missing.append("send script JSON recipient patch")
    if missing:
        print({"ok":False,"missing":missing}); return 1
    print({"ok":True,"message":"Yönetici Özeti gelişmiş ekran, alıcı yönetimi ve manuel gönderim altyapısı hazır."}); return 0
if __name__=="__main__": raise SystemExit(main())
