from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import inspect, text

from app.services.performance.v2_1_5_category_period_scope import (
    PLAN_ITEM_TABLE,
    PLAN_TABLE,
    list_category_period_scope_plans,
)
from app.services.performance.v2_1_6_category_period_integration import (
    INTEGRATION_TABLE,
    PRECHECK_TABLE,
    RULE_VERSION,
    ensure_category_period_integration_schema,
    integration_summary,
)

logger = logging.getLogger(__name__)


def _db():
    from app.extensions import db
    return db


def _check(name: str, ok: bool, message: str) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "message": message}


def run_v2_1_6_category_period_integration_gate() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    try:
        schema = ensure_category_period_integration_schema()
        inspector = inspect(_db().engine)
        checks.append(_check("v2_1_5_tables", inspector.has_table(PLAN_TABLE) and inspector.has_table(PLAN_ITEM_TABLE), "V2.1.5 plan tabloları mevcut."))
        checks.append(_check("v2_1_6_tables", inspector.has_table(INTEGRATION_TABLE) and inspector.has_table(PRECHECK_TABLE), "V2.1.6 entegrasyon ve ön kontrol tabloları mevcut."))
        plans = list_category_period_scope_plans(include_inactive=False)
        checks.append(_check("plan_service", isinstance(plans, list), f"V2.1.5 plan servisi çalışıyor. Aktif plan: {len(plans)}"))
        period_cols = {c["name"] for c in inspector.get_columns("performance_periods")} if inspector.has_table("performance_periods") else set()
        checks.append(_check("period_scope_columns", {"scope_type", "scope_category_label"}.issubset(period_cols), "performance_periods kategori kapsam kolonları mevcut."))
        before_assignments = int(_db().session.execute(text("SELECT COUNT(*) FROM evaluation_assignments")).scalar() or 0) if inspector.has_table("evaluation_assignments") else 0
        summary = integration_summary()
        after_assignments = int(_db().session.execute(text("SELECT COUNT(*) FROM evaluation_assignments")).scalar() or 0) if inspector.has_table("evaluation_assignments") else 0
        checks.append(_check("assignment_safe", before_assignments == after_assignments, "Gate sırasında evaluation_assignments tablosuna görev yazılmadı."))
        checks.append(_check("summary", "integration_count" in summary, "V2.1.6 entegrasyon özeti çalışıyor."))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        schema = {"ok": False, "error": "Kalite kapısı kontrolü sırasında beklenmeyen bir hata oluştu."}
        summary = {}
        checks.append(_check("exception", False, "Kalite kapısı kontrolü sırasında beklenmeyen bir hata oluştu."))
    return {"ok": all(c["ok"] for c in checks), "schema": schema, "summary": summary, "checks": checks, "rule_version": RULE_VERSION}
