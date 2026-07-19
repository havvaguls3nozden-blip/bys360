# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import inspect, text

from app.services.performance.v2_1_2_category_engine import (
    ASSIGNMENT_TABLE,
    CATEGORY_TABLE,
    DEFAULT_CATEGORIES,
    RULE_VERSION,
    canonical_category_key,
    category_scope_summary,
    ensure_category_schema,
    infer_category_from_import_row,
)

logger = logging.getLogger(__name__)


def _check(name: str, ok: bool, message: str) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "message": message}


def run_v2_1_2_category_quality_gate() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    try:
        from app.extensions import db
        ensure_category_schema()
        inspector = inspect(db.engine)
        tables_ok = inspector.has_table(CATEGORY_TABLE) and inspector.has_table(ASSIGNMENT_TABLE)
        checks.append(_check("category_tables", tables_ok, "Kategori ve atama tabloları mevcut." if tables_ok else "Kategori tabloları eksik."))
        count = db.session.execute(text(f"SELECT COUNT(*) FROM {CATEGORY_TABLE}")).scalar() if inspector.has_table(CATEGORY_TABLE) else 0
        checks.append(_check("default_categories", int(count or 0) >= len(DEFAULT_CATEGORIES), f"Kategori sayısı: {int(count or 0)}"))
        alias_ok = canonical_category_key("Güvenlik") == "guvenlik"
        checks.append(_check("category_alias", alias_ok, "Türkçe kategori adı güvenli anahtara çevriliyor."))
        inferred = infer_category_from_import_row({"Kategori": "Temizlik", "Unvan": "Personel"})
        checks.append(_check("import_helper", inferred == "temizlik", "Import kategori yardımcı fonksiyonu çalışıyor."))
        summary = category_scope_summary()
        checks.append(_check("summary", summary.get("category_count", 0) >= len(DEFAULT_CATEGORIES), "Kategori özet servisi çalışıyor."))
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        checks.append(_check("exception", False, str(exc)))
    return {"ok": all(item.get("ok") for item in checks), "checks": checks, "rule_version": RULE_VERSION}
