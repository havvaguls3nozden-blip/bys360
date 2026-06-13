from __future__ import annotations

import argparse
import json
import py_compile
from pathlib import Path

REQUIRED = [
    "app/services/corporate_information_center.py",
    "app/communication/corporate_information_center_routes.py",
    "app/templates/corporate_information_center/celebrations.html",
    "app/static/css/corporate_information_center_v4_0_celebrations.css",
]
MARKERS = [
    "BYS360_CIC_V4_0_SMART_CELEBRATIONS_BEGIN",
    "BYS360_CIC_V4_0_SMART_CELEBRATIONS_ROUTES_BEGIN",
    "/dashboard/kurumsal-bilgilendirme/kutlamalar",
    "birth_date = db.Column(db.Date",
    "hire_date = db.Column(db.Date",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root)
    missing = [p for p in REQUIRED if not (root / p).exists()]
    texts = "\n".join((root / p).read_text(encoding="utf-8", errors="ignore") for p in REQUIRED if (root / p).exists())
    model_text = (root / "app/models/core_models.py").read_text(encoding="utf-8", errors="ignore") if (root / "app/models/core_models.py").exists() else ""
    all_text = texts + "\n" + model_text
    missing_markers = [m for m in MARKERS if m not in all_text]
    compile_errors = []
    for rel in ["app/services/corporate_information_center.py", "app/communication/corporate_information_center_routes.py", "app/models/core_models.py"]:
        path = root / rel
        if path.exists():
            try:
                py_compile.compile(str(path), doraise=True)
            except Exception as exc:
                compile_errors.append(f"{rel}: {exc}")
    result = {"ok": not missing and not missing_markers and not compile_errors, "missing_files": missing, "missing_markers": missing_markers, "compile_errors": compile_errors}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["ok"]:
        print("BYS360_CIC_V4_0_SMART_CELEBRATIONS_CHECK_OK")
        return 0
    print("BYS360_CIC_V4_0_SMART_CELEBRATIONS_CHECK_FAIL")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
