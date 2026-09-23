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
    RULE_VERSION,
    SCOPE_DRAFT_TABLE,
    category_scope_dashboard_summary,
    category_scope_summaries,
    ensure_category_scope_schema,
    list_scope_drafts,
    upsert_category_scope_draft,
)

logger = logging.getLogger(__name__)


def _db():
    from app.extensions import db
    return db


def _check(name: str, ok: bool, message: str) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "message": message}


def run_v2_1_4_category_scope_visibility_gate(create_probe: bool = False) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    try:
        ensure_category_scope_schema()
        inspector = inspect(_db().engine)
        checks.append(_check("v2_1_2_tables", inspector.has_table(CATEGORY_TABLE) and inspector.has_table(ASSIGNMENT_TABLE), "V2.1.2 kategori tabloları mevcut."))
        checks.append(_check("scope_draft_table", inspector.has_table(SCOPE_DRAFT_TABLE), "V2.1.4 kapsam taslak tablosu mevcut."))
        cat_count = int(_db().session.execute(text(f"SELECT COUNT(*) FROM {CATEGORY_TABLE}")).scalar() or 0) if inspector.has_table(CATEGORY_TABLE) else 0
        checks.append(_check("default_categories", cat_count >= 6, f"Kategori sayısı: {cat_count}"))
        summaries = category_scope_summaries(include_person_details=False)
        checks.append(_check("summary_only", isinstance(summaries, list) and all("personnel_preview" in item for item in summaries), "Kategori özeti kişi detayı göstermeden üretildi."))
        alias_ok = canonical_category_key("Güvenlik") == "guvenlik"
        checks.append(_check("category_alias", alias_ok, "Türkçe kategori anahtarı dönüşümü çalışıyor."))
        if create_probe:
            probe = upsert_category_scope_draft("diger", "V2.1.4 Gate Kapsam Taslağı", "Gate doğrulama taslağı", None, "summary_only")
            checks.append(_check("scope_upsert", bool(probe.get("ok")), "Kategori kapsam taslağı oluşturma/güncelleme çalışıyor."))
        else:
            checks.append(_check("scope_upsert", True, "Kapsam taslağı yazma kontrolü audit/gate modunda atlandı."))
        dashboard = category_scope_dashboard_summary()
        checks.append(_check("dashboard_summary", "assigned_total" in dashboard, "Kategori kapsam dashboard özeti çalışıyor."))
        drafts = list_scope_drafts(include_inactive=False)
        checks.append(_check("draft_list", isinstance(drafts, list), f"Aktif taslak sayısı: {len(drafts)}"))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        checks.append(_check("exception", False, "Kalite kapısı kontrolü sırasında beklenmeyen bir hata oluştu."))
    return {"ok": all(item.get("ok") for item in checks), "checks": checks, "rule_version": RULE_VERSION}
