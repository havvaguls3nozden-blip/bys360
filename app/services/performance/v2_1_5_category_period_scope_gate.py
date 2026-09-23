from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import inspect, text

from app.services.performance.v2_1_2_category_engine import (
    ASSIGNMENT_TABLE,
    CATEGORY_TABLE,
    canonical_category_key,
)
from app.services.performance.v2_1_4_category_scope_visibility import (
    SCOPE_DRAFT_TABLE as V214_SCOPE_DRAFT_TABLE,
)
from app.services.performance.v2_1_5_category_period_scope import (
    PLAN_ITEM_TABLE,
    PLAN_TABLE,
    RULE_VERSION,
    assignment_precheck_for_plan,
    category_period_scope_summary,
    ensure_category_period_scope_schema,
    list_category_period_scope_plans,
    preview_category_period_scope,
    upsert_category_period_scope_plan,
)

logger = logging.getLogger(__name__)


def _db():
    from app.extensions import db
    return db


def _check(name: str, ok: bool, message: str) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "message": message}


def run_v2_1_5_category_period_scope_gate(create_probe: bool = False) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    try:
        schema = ensure_category_period_scope_schema()
        inspector = inspect(_db().engine)
        checks.append(_check("v2_1_2_tables", inspector.has_table(CATEGORY_TABLE) and inspector.has_table(ASSIGNMENT_TABLE), "V2.1.2 kategori tabloları mevcut."))
        checks.append(_check("v2_1_4_scope_table", inspector.has_table(V214_SCOPE_DRAFT_TABLE), "V2.1.4 kategori kapsam tablosu mevcut."))
        checks.append(_check("v2_1_5_plan_tables", inspector.has_table(PLAN_TABLE) and inspector.has_table(PLAN_ITEM_TABLE), "V2.1.5 plan ve plan kalem tabloları mevcut."))
        cat_count = int(_db().session.execute(text(f"SELECT COUNT(*) FROM {CATEGORY_TABLE}")).scalar() or 0) if inspector.has_table(CATEGORY_TABLE) else 0
        checks.append(_check("default_categories", cat_count >= 6, f"Kategori sayısı: {cat_count}"))
        alias_ok = canonical_category_key("Güvenlik") == "guvenlik"
        checks.append(_check("category_alias", alias_ok, "Türkçe kategori anahtarı dönüşümü çalışıyor."))
        preview = preview_category_period_scope("guvenlik", include_person_details=False)
        checks.append(_check("category_preview", "active_personnel_count" in preview, "Kategori dönem kapsam ön izleme servisi çalışıyor."))
        if create_probe:
            result = upsert_category_period_scope_plan(
                "diger",
                "V2.1.5 Gate Özel Dönem Kapsamı",
                "special",
                "2026-01-01",
                "2026-12-31",
                "Gate doğrulama planı.",
                None,
                "summary_only",
            )
            checks.append(_check("plan_upsert", bool(result.get("ok")), "Kategori dönem kapsam planı oluşturma/güncelleme çalışıyor."))
            precheck = assignment_precheck_for_plan(str(result.get("plan_key") or ""))
            checks.append(_check("assignment_precheck", isinstance(precheck.get("checks"), list), "Görev üretimi ön kontrol servisi çalışıyor."))
        else:
            checks.append(_check("plan_upsert", True, "Plan yazma kontrolü audit modunda atlandı."))
            checks.append(_check("assignment_precheck", True, "Ön kontrol yazma gerektirmeyen modda atlandı."))
        summary = category_period_scope_summary()
        checks.append(_check("summary", "plan_count" in summary, "Kategori dönem kapsam özeti çalışıyor."))
        plans = list_category_period_scope_plans(include_inactive=False)
        checks.append(_check("plan_list", isinstance(plans, list), f"Aktif plan sayısı: {len(plans)}"))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        checks.append(_check("exception", False, "Kalite kapısı kontrolü sırasında beklenmeyen bir hata oluştu."))
        schema = {"ok": False, "error": "Kalite kapısı kontrolü sırasında beklenmeyen bir hata oluştu."}
    return {"ok": all(item.get("ok") for item in checks), "schema": schema, "checks": checks, "rule_version": RULE_VERSION}
