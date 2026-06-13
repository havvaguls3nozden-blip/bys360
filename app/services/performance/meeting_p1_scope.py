# -*- coding: utf-8 -*-
from __future__ import annotations


import logging

"""BYS360 Toplantı Kararları — Faz 7 P1 geliştirme servisi."""

from dataclasses import dataclass
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
logger = logging.getLogger(__name__)

P1_SCOPE_VERSION = "2026-04-30-meeting-p1-faz7"

P1_REQUIRED_SETTINGS = {
    "performance_period_scope_enabled": {"label": "Dönem kapsamı aktif", "value": "true", "description": "Dönemler tüm kurum, birim/grup, kategori veya seçili personel kapsamıyla açılabilir."},
    "performance_multiple_periods_enabled": {"label": "Birden fazla dönem desteği", "value": "true", "description": "Aynı yıl içinde farklı amaç ve kapsamlarda birden fazla performans dönemi oluşturulabilir."},
    "performance_category_periods_enabled": {"label": "Kategori bazlı dönem desteği", "value": "true", "description": "Güvenlik, Temizlik, Deneme Süreli Personel gibi kategorilere özel dönem açma altyapısını etkinleştirir."},
    "performance_selected_person_periods_enabled": {"label": "Seçilmiş personel dönemi desteği", "value": "true", "description": "Belirli personel listesine özel dönem açma altyapısını etkinleştirir."},
    "performance_third_reviewer_column_optional": {"label": "3. amir sütunu opsiyonel", "value": "true", "description": "3. amir olmayan dönemlerde boş sütun ve sahte bekleme durumu gösterilmez."},
    "performance_third_reviewer_status_language": {"label": "3. amir görev dili kurumsal", "value": "true", "description": "Yorum modunda görev dili puan bekliyor değil, yorum/görüş bekliyor olarak gösterilir."},
    "performance_scorecard_readability_enabled": {"label": "Karne okunabilirliği aktif", "value": "true", "description": "Karne, değerlendirme formu ve puanlama geçmişi okunabilir kurumsal kart/tipografi düzeniyle gösterilir."},
    "performance_scorecard_large_text_enabled": {"label": "Karne yazı puntosu güçlendirildi", "value": "true", "description": "Karne ana puan, kriter, amir görüşü ve süreç geçmişi alanlarında okunabilirlik artırılır."},
    "performance_scorecard_technical_terms_hidden": {"label": "Teknik ifade temizliği", "value": "true", "description": "Kullanıcı ekranlarında teknik durum kodları yerine Türkçe kurumsal ifadeler gösterilir."},
}

P1_PERIOD_SCOPE_COLUMNS = {
    "scope_type": "VARCHAR(40)",
    "scope_unit_label": "VARCHAR(255)",
    "scope_category_label": "VARCHAR(255)",
    "scope_personnel_filter": "TEXT",
    "level_3_column_visible": "BOOLEAN DEFAULT FALSE",
    "scorecard_readability_mode": "VARCHAR(40) DEFAULT 'kurumsal'",
}

P1_SCORECARD_READABILITY_TOKENS = [
    "Puan okunabilirliği",
    "Amir görüşleri ayrı kartlarda gösterilir",
    "Teknik ifadeler yerine Türkçe süreç dili kullanılır",
]

P1_SCOPE_TYPES = [
    {"value": "all", "label": "Tüm kurum", "description": "Dönem kurum genelinde uygulanır."},
    {"value": "unit", "label": "Birim / grup", "description": "Dönem belirli bir birim veya çalışma grubuyla sınırlıdır."},
    {"value": "category", "label": "Personel kategorisi", "description": "Dönem Güvenlik, Temizlik gibi kategoriyle sınırlıdır."},
    {"value": "selected_personnel", "label": "Seçilmiş personel", "description": "Dönem belirli sicil/personel listesiyle sınırlıdır."},
]

P1_CATEGORY_LABELS = ["Güvenlik", "Temizlik", "İdari Personel", "Teknik Personel", "Deneme Süreli Personel", "Diğer"]

@dataclass(slots=True)
class P1ScopeResult:
    ok: bool
    version: str
    settings_seeded: int = 0
    columns_ready: int = 0
    p1_checks_passed: int = 0
    message: str = ""
    warnings: list[str] | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "version": self.version,
            "settings_seeded": self.settings_seeded,
            "columns_ready": self.columns_ready,
            "p1_checks_passed": self.p1_checks_passed,
            "message": self.message,
            "warnings": list(self.warnings or []),
        }


def _has_table(table_name: str) -> bool:
    try:
        return bool(inspect(db.engine).has_table(table_name))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return False


def _columns(table_name: str) -> set[str]:
    try:
        return {col["name"] for col in inspect(db.engine).get_columns(table_name)}
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return set()


def _scalar(sql: str, params: dict[str, Any] | None = None, default: Any = None) -> Any:
    try:
        return db.session.execute(text(sql), params or {}).scalar()
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _rows(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    try:
        return [dict(row) for row in db.session.execute(text(sql), params or {}).mappings().all()]
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return []


def _setting_exists(setting_key: str) -> bool:
    if not _has_table("module_settings"):
        return False
    return bool(_scalar("""
        SELECT id FROM module_settings
        WHERE module_key='performance' AND setting_key=:setting_key
        LIMIT 1
        """, {"setting_key": setting_key}))


def ensure_p1_settings() -> int:
    if not _has_table("module_settings"):
        return 0
    seeded = 0
    for key, payload in P1_REQUIRED_SETTINGS.items():
        if _setting_exists(key):
            continue
        db.session.execute(text("""
            INSERT INTO module_settings
                (module_key, setting_key, label, value_text, value_type, description, is_active, created_at, updated_at)
            VALUES
                ('performance', :key, :label, :value, 'boolean', :description, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """), {"key": key, "label": payload["label"], "value": payload["value"], "description": payload["description"]})
        seeded += 1
    return seeded


def ensure_p1_period_scope_columns() -> tuple[int, list[str]]:
    warnings: list[str] = []
    if not _has_table("performance_periods"):
        return 0, ["performance_periods tablosu bulunamadı; kapsam kolonları canlı DB'de eklenemedi."]
    existing = _columns("performance_periods")
    added = 0
    for name, ddl_type in P1_PERIOD_SCOPE_COLUMNS.items():
        if name in existing:
            continue
        try:
            db.session.execute(text(f"ALTER TABLE performance_periods ADD COLUMN {name} {ddl_type}"))
            added += 1
        except SQLAlchemyError as exc:
            db.session.rollback()
            warnings.append(f"{name} kolonu eklenemedi: {exc.__class__.__name__}")
        except Exception as exc:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            db.session.rollback()
            warnings.append(f"{name} kolonu eklenemedi: {exc}")
    try:
        db.session.commit()
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        db.session.rollback()
        warnings.append(f"Kapsam kolonları commit edilemedi: {exc}")
    return added, warnings


def p1_status_checks() -> list[dict[str, Any]]:
    period_columns = _columns("performance_periods") if _has_table("performance_periods") else set()
    columns_ready = all(name in period_columns for name in P1_PERIOD_SCOPE_COLUMNS)
    p0_ready = _setting_exists("low_score_president_approval_required") and _setting_exists("employee_can_see_own_group_average")
    checks = [
        ("p1_period_scope_enabled", "Dönem kapsam tipi ayarları hazır.", _setting_exists("performance_period_scope_enabled")),
        ("p1_multiple_periods", "Birden fazla dönem desteği ayara bağlandı.", _setting_exists("performance_multiple_periods_enabled")),
        ("p1_category_periods", "Kategori bazlı dönem altyapısı hazır.", _setting_exists("performance_category_periods_enabled")),
        ("p1_selected_personnel", "Seçilmiş personele özel dönem altyapısı hazır.", _setting_exists("performance_selected_person_periods_enabled")),
        ("p1_period_columns", "Dönem kapsam kolonları veritabanı tarafında hazır.", columns_ready),
        ("p1_level3_optional", "3. amir sütunu opsiyonel ayara bağlı.", _setting_exists("performance_third_reviewer_column_optional")),
        ("p1_level3_language", "3. amir yorum/puan görev dili ayrımı desteklenir.", _setting_exists("performance_third_reviewer_status_language")),
        ("p1_scorecard_readability", "Karne okunabilirliği ve yazı puntosu güçlendirme ayarı hazır.", _setting_exists("performance_scorecard_readability_enabled")),
        ("p1_technical_terms_hidden", "Teknik ifadelerin kullanıcıya sızmaması P1 kapsamına alındı.", _setting_exists("performance_scorecard_technical_terms_hidden")),
        ("p1_p0_dependency", "P0 düşük performans ve görünürlük kuralları korunuyor.", p0_ready),
    ]
    return [{"code": code, "title": title, "ok": bool(ok), "status": "Hazır" if ok else "Kontrol gerekli"} for code, title, ok in checks]


def p1_summary_cards() -> list[dict[str, Any]]:
    checks = p1_status_checks()
    period_columns = _columns("performance_periods") if _has_table("performance_periods") else set()
    return [
        {"label": "P1 Kontrol", "value": f"{sum(1 for item in checks if item['ok'])}/10", "note": "Hazır olan P1 başlığı"},
        {"label": "Kapsam Tipi", "value": str(len(P1_SCOPE_TYPES)), "note": "Tüm kurum, birim, kategori, seçili personel"},
        {"label": "Dönem Kolonu", "value": f"{sum(1 for name in P1_PERIOD_SCOPE_COLUMNS if name in period_columns)}/{len(P1_PERIOD_SCOPE_COLUMNS)}", "note": "DB kapsam alanı"},
        {"label": "3. Amir", "value": "Opsiyonel", "note": "Sütun ve görev dili ayara bağlı"},
    ]


def build_p1_scope_context(viewer: Any | None = None) -> dict[str, Any]:
    return {
        "title": "P1 Geliştirme",
        "version": P1_SCOPE_VERSION,
        "cards": p1_summary_cards(),
        "checks": p1_status_checks(),
        "scope_types": P1_SCOPE_TYPES,
        "category_labels": P1_CATEGORY_LABELS,
        "settings": _rows("SELECT setting_key, label, value_text, description FROM module_settings WHERE module_key='performance' ORDER BY setting_key") if _has_table("module_settings") else [],
        "viewer": viewer,
    }


def run_p1_scope(actor_user_id: int | None = None) -> P1ScopeResult:
    warnings: list[str] = []
    seeded = 0
    try:
        seeded = ensure_p1_settings()
        _, column_warnings = ensure_p1_period_scope_columns()
        warnings.extend(column_warnings)
        db.session.commit()
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        db.session.rollback()
        warnings.append(f"P1 geliştirme hazırlığı tamamlanamadı: {exc}")
    checks = p1_status_checks()
    passed = sum(1 for item in checks if item["ok"])
    period_columns = _columns("performance_periods") if _has_table("performance_periods") else set()
    columns_ready = sum(1 for name in P1_PERIOD_SCOPE_COLUMNS if name in period_columns)
    ok = passed == len(checks)
    return P1ScopeResult(ok=ok, version=P1_SCOPE_VERSION, settings_seeded=seeded, columns_ready=columns_ready, p1_checks_passed=passed, message="P1 toplantı geliştirme kontrolleri tamamlandı." if ok else "P1 geliştirme kontrollerinde eksik başlık var.", warnings=warnings)
