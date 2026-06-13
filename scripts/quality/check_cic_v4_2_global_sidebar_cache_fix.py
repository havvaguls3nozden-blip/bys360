from __future__ import annotations
import argparse
from pathlib import Path

CSS_NAME = "corporate_information_center_v4_2_global_sidebar_cache_fix.css"
JS_NAME = "corporate_information_center_v4_2_global_sidebar_cache_fix.js"
URL = "/dashboard/kurumsal-bilgilendirme/kutlamalar"

parser = argparse.ArgumentParser()
parser.add_argument("--project-root", required=True)
args = parser.parse_args()
root = Path(args.project_root).resolve()
errors = []

for rel in [f"app/static/css/{CSS_NAME}", f"app/static/js/{JS_NAME}"]:
    if not (root / rel).exists():
        errors.append(f"missing {rel}")

base = root / "app/templates/base.html"
if base.exists():
    t = base.read_text(encoding="utf-8", errors="ignore")
    if CSS_NAME not in t:
        errors.append("base.html missing v4.2 css ref")
    if JS_NAME not in t:
        errors.append("base.html missing v4.2 js ref")
else:
    errors.append("app/templates/base.html missing")

cic_base = root / "app/templates/corporate_information_center/base.html"
if cic_base.exists():
    t = cic_base.read_text(encoding="utf-8", errors="ignore")
    if URL not in t:
        errors.append("corporate_information_center/base.html missing Kutlamalar link")
    if "pilot" in t.lower():
        errors.append("corporate_information_center/base.html still contains pilot")
else:
    errors.append("corporate_information_center/base.html missing")

if errors:
    print("BYS360_CIC_V4_2_GLOBAL_SIDEBAR_CACHE_FIX_CHECK_FAIL")
    for e in errors:
        print("ERROR=", e)
    raise SystemExit(1)
print("BYS360_CIC_V4_2_GLOBAL_SIDEBAR_CACHE_FIX_CHECK_OK")
