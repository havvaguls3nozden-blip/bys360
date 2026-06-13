# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))

from app import create_app
from app.services.performance.v2_1_3_personnel_category_card import category_card_summary, get_personnel_category_rows
from app.services.performance.v2_1_3_personnel_category_card_gate import run_v2_1_3_personnel_category_card_gate

app = create_app()
with app.app_context():
    payload = {
        "summary": category_card_summary(),
        "sample_rows": [row.__dict__ for row in get_personnel_category_rows(limit=3)],
        "gate": run_v2_1_3_personnel_category_card_gate(),
    }
print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
