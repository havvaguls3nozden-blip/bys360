from __future__ import annotations

import logging
import re
from typing import Any

from sqlalchemy import inspect, text

from app.services.performance.v2_1_2_category_engine import (
    ASSIGNMENT_TABLE,
    CATEGORY_TABLE,
    canonical_category_key,
    ensure_category_schema,
    list_categories,
)

"""BYS360 V2.1.6A kurumsal arayüz ve güvenli kategori silme yardımcıları."""

logger = logging.getLogger(__name__)

RULE_VERSION = "performance_v2_1_6a_corporate_ui_category_delete"


def _db():
    from app.extensions import db
    return db


def _dialect_name() -> str:
    try:
        return _db().engine.dialect.name
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return "unknown"


def _bool_true_sql() -> str:
    return "1" if _dialect_name() == "sqlite" else "TRUE"


def _bool_false_sql() -> str:
    return "0" if _dialect_name() == "sqlite" else "FALSE"


def _has_table(table: str) -> bool:
    try:
        return bool(inspect(_db().engine).has_table(table))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return False


def _safe_key(value: Any) -> str:
    key = canonical_category_key(value)
    key = key.replace("ı", "i").replace("ğ", "g").replace("ü", "u").replace("ş", "s").replace("ö", "o").replace("ç", "c")
    key = re.sub(r"[^a-z0-9_]+", "_", key.lower()).strip("_")
    return key or "diger"


def _normalize_key_from_display(value: Any) -> str:
    raw = str(value or "").strip().lower()
    raw = raw.replace("ı", "i").replace("ğ", "g").replace("ü", "u").replace("ş", "s").replace("ö", "o").replace("ç", "c")
    raw = re.sub(r"[^a-z0-9]+", "_", raw).strip("_")
    return raw or "diger"


def active_categories() -> list[Any]:
    ensure_category_schema()
    return list_categories(include_inactive=False)


def all_categories_with_usage() -> list[dict[str, Any]]:
    ensure_category_schema()
    cats = list_categories(include_inactive=True)
    output: list[dict[str, Any]] = []
    for cat in cats:
        usage = category_usage_summary(cat.category_key)
        data = cat.__dict__.copy()
        data.update(usage)
        data["can_hard_delete"] = usage["total_links"] == 0
        data["delete_label"] = "Sil" if data["can_hard_delete"] else "Pasife Al"
        data["status_label"] = "Aktif" if cat.is_active else "Pasif"
        output.append(data)
    return output


def category_usage_summary(category_key: str) -> dict[str, int]:
    ensure_category_schema()
    key = _safe_key(category_key)
    db = _db()
    counts = {
        "active_assignments": 0,
        "all_assignments": 0,
        "scope_drafts": 0,
        "period_plans": 0,
        "period_integrations": 0,
    }
    if _has_table(ASSIGNMENT_TABLE):
        counts["active_assignments"] = int(db.session.execute(text(f"SELECT COUNT(*) FROM {ASSIGNMENT_TABLE} WHERE category_key=:key AND is_active={_bool_true_sql()}"), {"key": key}).scalar() or 0)
        counts["all_assignments"] = int(db.session.execute(text(f"SELECT COUNT(*) FROM {ASSIGNMENT_TABLE} WHERE category_key=:key"), {"key": key}).scalar() or 0)
    if _has_table("performance_category_scope_drafts"):
        counts["scope_drafts"] = int(db.session.execute(text(f"SELECT COUNT(*) FROM performance_category_scope_drafts WHERE category_key=:key AND is_active={_bool_true_sql()}"), {"key": key}).scalar() or 0)
    if _has_table("performance_category_period_scope_plans"):
        counts["period_plans"] = int(db.session.execute(text(f"SELECT COUNT(*) FROM performance_category_period_scope_plans WHERE category_key=:key AND is_active={_bool_true_sql()}"), {"key": key}).scalar() or 0)
    if _has_table("performance_category_period_scope_integrations"):
        counts["period_integrations"] = int(db.session.execute(text("SELECT COUNT(*) FROM performance_category_period_scope_integrations WHERE category_key=:key"), {"key": key}).scalar() or 0)
    counts["total_links"] = sum(counts.values())
    return counts


def create_or_update_category(display_name: str, description: str | None = None, category_key: str | None = None) -> dict[str, Any]:
    ensure_category_schema()
    name = str(display_name or "").strip()
    if not name:
        return {"ok": False, "message": "Kategori adı boş olamaz."}
    key = _safe_key(category_key or _normalize_key_from_display(name))
    db = _db()
    exists = db.session.execute(text(f"SELECT id FROM {CATEGORY_TABLE} WHERE category_key=:key"), {"key": key}).mappings().first()
    if exists:
        db.session.execute(text(f"""
            UPDATE {CATEGORY_TABLE}
               SET display_name=:display_name,
                   description=:description,
                   is_active={_bool_true_sql()},
                   updated_at=CURRENT_TIMESTAMP
             WHERE category_key=:key
        """), {"display_name": name, "description": description or "", "key": key})
        action = "updated"
    else:
        max_order = int(db.session.execute(text(f"SELECT COALESCE(MAX(display_order), 0) FROM {CATEGORY_TABLE}")).scalar() or 0)
        db.session.execute(text(f"""
            INSERT INTO {CATEGORY_TABLE} (category_key, display_name, description, display_order, is_active)
            VALUES (:key, :display_name, :description, :display_order, {_bool_true_sql()})
        """), {"key": key, "display_name": name, "description": description or "", "display_order": max_order + 10})
        action = "created"
    db.session.commit()
    return {"ok": True, "action": action, "category_key": key, "display_name": name, "rule_version": RULE_VERSION}


def delete_category_safely(category_key: str) -> dict[str, Any]:
    ensure_category_schema()
    key = _safe_key(category_key)
    db = _db()
    cat = db.session.execute(text(f"SELECT id, display_name, is_active FROM {CATEGORY_TABLE} WHERE category_key=:key"), {"key": key}).mappings().first()
    if not cat:
        return {"ok": False, "message": "Kategori bulunamadı.", "category_key": key}
    usage = category_usage_summary(key)
    if usage["total_links"] == 0:
        db.session.execute(text(f"DELETE FROM {CATEGORY_TABLE} WHERE category_key=:key"), {"key": key})
        db.session.commit()
        return {"ok": True, "action": "deleted", "message": f"{cat['display_name']} kategorisi silindi.", "usage": usage, "category_key": key}
    db.session.execute(text(f"UPDATE {CATEGORY_TABLE} SET is_active={_bool_false_sql()}, updated_at=CURRENT_TIMESTAMP WHERE category_key=:key"), {"key": key})
    db.session.commit()
    return {
        "ok": True,
        "action": "archived",
        "message": f"{cat['display_name']} kategorisi bağlı kayıtlar bulunduğu için pasife alındı. Geçmiş kayıtlar korunur; yeni ekranlarda kategori seçeneklerinden çıkarılır.",
        "usage": usage,
        "category_key": key,
    }


def restore_category(category_key: str) -> dict[str, Any]:
    ensure_category_schema()
    key = _safe_key(category_key)
    _db().session.execute(text(f"UPDATE {CATEGORY_TABLE} SET is_active={_bool_true_sql()}, updated_at=CURRENT_TIMESTAMP WHERE category_key=:key"), {"key": key})
    _db().session.commit()
    return {"ok": True, "category_key": key, "message": "Kategori yeniden aktifleştirildi."}


def label_status(value: Any) -> str:
    raw = str(value or "").strip().lower()
    mapping = {
        "period_linked": "Dönem Bağlantısı Hazır",
        "not_started": "Henüz Başlamadı",
        "ready": "Hazır",
        "needs_review": "Kontrol Gerekli",
        "gorev_uretimi_on_hazir": "Görev Üretimine Hazır",
        "amir_kontrol_gerekiyor": "Amir Bilgisi Kontrol Edilmeli",
        "kapsam_uyumsuz": "Kapsam Uyumsuz",
        "summary_only": "Sadece Özet",
        "detail_allowed": "Yetkili Detay",
        "assignment_precheck_status": "Ön Kontrol Durumu",
    }
    return mapping.get(raw, str(value or "-").replace("_", " ").title())


def corporate_gate_label(value: Any) -> str:
    raw = str(value or "").strip().lower()
    mapping = {
        "v2_1_5_tables": "Dönem planı altyapısı",
        "v2_1_6_tables": "Dönem bağlantı altyapısı",
        "plan_service": "Plan listesi",
        "period_scope_columns": "Dönem kapsam alanları",
        "assignment_safe": "Görev üretimi güvenliği",
        "summary": "Özet bilgisi",
        "v2_1_2_tables": "Kategori altyapısı",
        "v2_1_3_card": "Personel kartı bağlantısı",
        "scope_draft_table": "Kapsam taslağı altyapısı",
        "default_categories": "Kategori listesi",
        "visibility_policy": "Görünürlük politikası",
        "period_table": "Dönem tablosu",
        "plan_table": "Plan tablosu",
        "plan_items_table": "Plan personel listesi",
        "preview_service": "Ön izleme",
    }
    return mapping.get(raw, str(value or "-").replace("_", " ").title())
