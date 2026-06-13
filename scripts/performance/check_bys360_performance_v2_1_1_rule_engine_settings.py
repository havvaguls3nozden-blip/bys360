# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))

from app import create_app
from app.services.performance.v2_1_rule_engine import build_rule_snapshot_dict, validate_score_comment_rules, status_label
from app.services.performance.v2_1_quality_gate import run_v2_1_1_quality_gate

app = create_app()
with app.app_context():
    payload = {
        "snapshot": build_rule_snapshot_dict(),
        "score_1_issues": validate_score_comment_rules(raw_score=1, criterion_comment=""),
        "low_score_issues": validate_score_comment_rules(score_100=69, general_comment=""),
        "status_label": status_label("president_pending"),
        "gate": run_v2_1_1_quality_gate(),
    }
print(json.dumps(payload, ensure_ascii=False, indent=2))
