# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))

from app import create_app
from app.services.performance.v2_1_2_category_engine import category_scope_summary, infer_category_from_import_row
from app.services.performance.v2_1_2_category_quality_gate import run_v2_1_2_category_quality_gate

app = create_app()
with app.app_context():
    payload = {
        "summary": category_scope_summary(),
        "import_infer_sample": infer_category_from_import_row({"Kategori": "Güvenlik", "Unvan": "Personel"}),
        "gate": run_v2_1_2_category_quality_gate(),
    }
print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
