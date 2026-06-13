# -*- coding: utf-8 -*-
from __future__ import annotations
import json
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
from app import create_app
from app.services.performance.v2_1_4_category_scope_visibility import category_scope_dashboard_summary, category_scope_summaries, list_scope_drafts
from app.services.performance.v2_1_4_category_scope_visibility_gate import run_v2_1_4_category_scope_visibility_gate
app = create_app()
with app.app_context():
    payload = {
        "summary": category_scope_dashboard_summary(),
        "categories": category_scope_summaries(include_person_details=False),
        "drafts": list_scope_drafts(),
        "gate": run_v2_1_4_category_scope_visibility_gate(create_probe=False),
    }
print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
