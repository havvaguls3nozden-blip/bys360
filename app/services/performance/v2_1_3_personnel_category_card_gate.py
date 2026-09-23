from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import inspect, text

from app.services.performance.v2_1_2_category_engine import (
    ASSIGNMENT_TABLE,
    CATEGORY_TABLE,
    canonical_category_key,
)
from app.services.performance.v2_1_3_personnel_category_card import (
    AUDIT_TABLE,
    RULE_VERSION,
    category_card_summary,
    ensure_v2_1_3_schema,
    get_personnel_category_rows,
    parse_user_ids,
    template_get_user_category,
)

logger = logging.getLogger(__name__)


def _check(name: str, ok: bool, message: str) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "message": message}


def run_v2_1_3_personnel_category_card_gate() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    try:
        from app.extensions import db
        ensure_v2_1_3_schema()
        inspector = inspect(db.engine)
        base_tables = inspector.has_table(CATEGORY_TABLE) and inspector.has_table(ASSIGNMENT_TABLE)
        checks.append(_check("v2_1_2_tables", base_tables, "V2.1.2 kategori tabloları mevcut." if base_tables else "V2.1.2 kategori tabloları eksik."))
        audit_ok = inspector.has_table(AUDIT_TABLE)
        checks.append(_check("audit_table", audit_ok, "V2.1.3 audit tablosu mevcut." if audit_ok else "Audit tablosu eksik."))
        categories_count = db.session.execute(text(f"SELECT COUNT(*) FROM {CATEGORY_TABLE}")).scalar() if inspector.has_table(CATEGORY_TABLE) else 0
        checks.append(_check("default_categories", int(categories_count or 0) >= 6, f"Kategori sayısı: {int(categories_count or 0)}"))
        rows = get_personnel_category_rows(limit=5)
        checks.append(_check("personnel_rows", isinstance(rows, list), f"Personel satırı servisi çalışıyor. Örnek kayıt: {len(rows)}"))
        parse_ok = parse_user_ids("1, 2\n3") == [1, 2, 3]
        checks.append(_check("bulk_parser", parse_ok, "Toplu kullanıcı ID ayrıştırma çalışıyor."))
        alias_ok = canonical_category_key("Deneme Süreli Personel") == "deneme_sureli_personel"
        checks.append(_check("category_alias", alias_ok, "Kategori Türkçe anahtar dönüşümü çalışıyor."))
        helper = template_get_user_category(None)
        checks.append(_check("template_helper", helper.get("display_name") == "Kategori Atanmamış", "Personel kartı Jinja helper güvenli çalışıyor."))
        summary = category_card_summary()
        checks.append(_check("summary", "visible_personnel_count" in summary, "Kategori kart özeti çalışıyor."))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        checks.append(_check("exception", False, "Kalite kapısı kontrolü sırasında beklenmeyen bir hata oluştu."))
    return {"ok": all(item.get("ok") for item in checks), "checks": checks, "rule_version": RULE_VERSION}
