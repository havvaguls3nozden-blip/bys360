from __future__ import annotations
import json
from app import create_app
from app.services.performance.v2_1_6_category_period_integration_gate import run_v2_1_6_category_period_integration_gate

app = create_app()
with app.app_context():
    result = run_v2_1_6_category_period_integration_gate()
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    print("BYS360_PERFORMANCE_V2_1_6_CATEGORY_PERIOD_INTEGRATION_OK" if result.get("ok") else "BYS360_PERFORMANCE_V2_1_6_CATEGORY_PERIOD_INTEGRATION_FAIL")
    raise SystemExit(0 if result.get("ok") else 1)
