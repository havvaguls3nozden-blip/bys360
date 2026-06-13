# -*- coding: utf-8 -*-
from __future__ import annotations
import json
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
from app import create_app
from app.services.performance.v2_1_5_category_period_scope import category_period_scope_summary, list_category_period_scope_plans, preview_category_period_scope
from app.services.performance.v2_1_5_category_period_scope_gate import run_v2_1_5_category_period_scope_gate
app = create_app()
with app.app_context():
    payload = {
        "summary": category_period_scope_summary(),
        "preview_guvenlik": preview_category_period_scope("guvenlik", include_person_details=False),
        "plans": list_category_period_scope_plans(),
        "gate": run_v2_1_5_category_period_scope_gate(create_probe=False),
    }
print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
