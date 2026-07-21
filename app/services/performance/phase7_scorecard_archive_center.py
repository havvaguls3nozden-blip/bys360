"""BYS360 Performans Tamamlama Faz 7: Geçmiş yıl karne / puan arşivi merkezi.

Bu modül idari karar üretmez. Eski dönem puanlarını, kaynak notlarını ve
karne özetlerini yetki kontrollü ve denetlenebilir bir arşiv sözleşmesine bağlar.
"""
from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

logger = logging.getLogger(__name__)

BYS360_PERFORMANCE_COMPLETION_PHASE7_SCORECARD_ARCHIVE_CENTER = True
BYS360_PERFORMANCE_COMPLETION_PHASE7_VERSION = "performance-completion-phase7-scorecard-archive-center-v1"
BYS360_PERFORMANCE_COMPLETION_PHASE7_OWN_HISTORY_ONLY = True
BYS360_PERFORMANCE_COMPLETION_PHASE7_SCOPE_VISIBILITY = True
BYS360_PERFORMANCE_COMPLETION_PHASE7_IMPORT_VALIDATION = True
BYS360_PERFORMANCE_COMPLETION_PHASE7_NO_PERSON_DETAIL_IN_AVERAGE = True
BYS360_PERFORMANCE_COMPLETION_PHASE7_AUDIT_SOURCE_REQUIRED = True

PHASE7_ARCHIVE_TABLE_NAME = "performance_scorecard_archives"

PHASE7_SETTING_ROWS = [
    ("performance_phase7", "scorecard_archive_enabled", "Geçmiş yıl karne/puan arşivi aktif", "bool", "true", "Geçmiş dönem puanlarının kontrollü arşivlenmesini sağlar."),
    ("performance_phase7", "manual_archive_entry_enabled", "Manuel geçmiş puan girişi aktif", "bool", "true", "Yetkili kullanıcılar eski dönem puanlarını manuel ekleyebilir."),
    ("performance_phase7", "excel_archive_import_enabled", "Excel ile geçmiş puan aktarımı aktif", "bool", "true", "Örnek formatla geçmiş dönem puanlarının toplu aktarımını destekler."),
    ("performance_phase7", "person_own_history_only", "Personel yalnızca kendi geçmişini görür", "bool", "true", "Personel rolü kendi geçmiş karnesi dışında kişi detayı göremez."),
    ("performance_phase7", "manager_scope_limited_history", "Yönetici geçmiş arşivi kapsamla sınırlı", "bool", "true", "Koordinatör ve Grup Başkanı yalnızca yetkili organizasyon kapsamını görebilir."),
    ("performance_phase7", "archive_source_required", "Arşiv kaydı kaynak bilgisi zorunlu", "bool", "true", "Manuel/Excel/kaynak belge bilgisi olmadan kayıt kesin arşiv sayılmaz."),
    ("performance_phase7", "archive_average_no_person_detail", "Arşiv ortalamalarında kişi detayı gizli", "bool", "true", "Kategori/grup ortalaması kişi bazlı puan listesi göstermeden hesaplanır."),
]

STATUS_LABELS = {
    "draft": "Taslak Arşiv Kaydı",
    "imported": "İçe Aktarıldı",
    "verified": "Kontrol Edildi",
    "published": "Arşivde Görünür",
    "rejected": "İade Edildi",
    "missing_source": "Kaynak Bilgisi Eksik",
    "invalid_score": "Puan Bilgisi Hatalı",
    "duplicate": "Mükerrer Arşiv Kaydı",
}

REQUIRED_IMPORT_COLUMNS = [
    "sicil_no",
    "ad_soyad",
    "yil",
    "donem",
    "puan",
    "kaynak",
]

@dataclass(frozen=True)
class Phase7ArchiveValidation:
    ok: bool
    errors: list[str]
    warnings: list[str]
    normalized: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "normalized": dict(self.normalized),
        }

@dataclass(frozen=True)
class Phase7ArchiveVisibilityDecision:
    can_view: bool
    scope: str
    reason: str
    show_person_detail: bool
    can_import: bool
    can_edit: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "can_view": self.can_view,
            "scope": self.scope,
            "reason": self.reason,
            "show_person_detail": self.show_person_detail,
            "can_import": self.can_import,
            "can_edit": self.can_edit,
        }


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_int(value: Any, default: int | None = None) -> int | None:
    text = _as_text(value)
    if not text:
        return default
    try:
        return int(float(text.replace(",", ".")))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _as_score(value: Any) -> float | None:
    text = _as_text(value).replace(",", ".")
    if not text:
        return None
    try:
        number = Decimal(text)
    except (InvalidOperation, ValueError):
        return None
    if number < 0 or number > 100:
        return None
    return float(number.quantize(Decimal("0.01")))


def phase7_status_label(status: Any) -> str:
    text = _as_text(status)
    return STATUS_LABELS.get(text, text or "Arşiv Durumu Belirtilmedi")


def phase7_score_band(score: Any) -> str:
    value = _as_score(score)
    if value is None:
        return "Puan Bilgisi Hatalı"
    if value < 70:
        return "Düşük Performans"
    if value >= 90:
        return "Çok Başarılı"
    return "Başarılı"


def normalize_phase7_archive_record(row: dict[str, Any]) -> dict[str, Any]:
    """Excel/manüel giriş satırını tek arşiv formatına dönüştürür."""
    normalized = {
        "registry_no": _as_text(row.get("sicil_no") or row.get("registry_no") or row.get("sicil") or row.get("Sicil No")),
        "full_name": _as_text(row.get("ad_soyad") or row.get("full_name") or row.get("personel") or row.get("Ad Soyad")),
        "year": _as_int(row.get("yil") or row.get("year") or row.get("Yıl")),
        "period_label": _as_text(row.get("donem") or row.get("period_label") or row.get("Dönem")),
        "score": _as_score(row.get("puan") or row.get("score") or row.get("Puan")),
        "source_type": _as_text(row.get("kaynak_tipi") or row.get("source_type") or "manual"),
        "source_file": _as_text(row.get("kaynak") or row.get("source_file") or row.get("Kaynak")),
        "note": _as_text(row.get("not") or row.get("note") or row.get("Açıklama")),
        "status": _as_text(row.get("durum") or row.get("status") or "imported"),
    }
    normalized["score_band"] = phase7_score_band(normalized["score"])
    return normalized


def validate_phase7_archive_record(row: dict[str, Any]) -> Phase7ArchiveValidation:
    normalized = normalize_phase7_archive_record(row)
    errors: list[str] = []
    warnings: list[str] = []
    if not normalized["registry_no"]:
        errors.append("Sicil No zorunludur.")
    if not normalized["full_name"]:
        warnings.append("Ad Soyad alanı boş; personel kartından tamamlanmalıdır.")
    if not normalized["year"]:
        errors.append("Yıl zorunludur.")
    elif normalized["year"] < 2000 or normalized["year"] > datetime.now().year + 1:
        errors.append("Yıl bilgisi geçerli aralıkta değildir.")
    if not normalized["period_label"]:
        errors.append("Dönem bilgisi zorunludur.")
    if normalized["score"] is None:
        errors.append("Puan 0-100 aralığında sayısal olmalıdır.")
    if not normalized["source_file"]:
        errors.append("Kaynak bilgisi zorunludur.")
    return Phase7ArchiveValidation(ok=not errors, errors=errors, warnings=warnings, normalized=normalized)


def phase7_required_import_columns() -> list[str]:
    return list(REQUIRED_IMPORT_COLUMNS)


def resolve_phase7_archive_visibility(
    *,
    role: str | None = None,
    current_user_id: Any = None,
    record_user_id: Any = None,
    same_scope: bool = False,
    is_admin: bool = False,
    is_president: bool = False,
    is_hr: bool = False,
    is_group_president: bool = False,
    is_coordinator: bool = False,
    action: str = "view",
) -> Phase7ArchiveVisibilityDecision:
    """Arşiv görünürlüğünü kişi/rol/kapsam düzeyinde çözer."""
    role_text = _as_text(role).lower()
    admin_like = is_admin or is_president or is_hr or role_text in {"admin", "sistem yöneticisi", "sistem_yoneticisi", "başkan", "baskan", "ik", "insan kaynakları", "performans yetkilisi", "personel yetkilisi"}
    manager_like = is_group_president or is_coordinator or role_text in {"grup başkanı", "grup baskani", "koordinatör", "koordinator"}
    own_record = current_user_id is not None and record_user_id is not None and str(current_user_id) == str(record_user_id)
    wants_import = action in {"import", "edit", "create", "manual_entry"}

    if admin_like:
        return Phase7ArchiveVisibilityDecision(True, "genel", "Genel arşiv yetkisi", True, True, True)
    if manager_like and same_scope:
        return Phase7ArchiveVisibilityDecision(True, "yetkili_kapsam", "Yalnızca yetkili organizasyon kapsamı", True, False, False)
    if own_record and not wants_import:
        return Phase7ArchiveVisibilityDecision(True, "kendi_gecmisi", "Personel yalnızca kendi geçmişini görür", False, False, False)
    if wants_import:
        return Phase7ArchiveVisibilityDecision(False, "yetkisiz", "Geçmiş puan aktarımı için Admin/İK/Performans Yetkilisi yetkisi gerekir", False, False, False)
    return Phase7ArchiveVisibilityDecision(False, "yetkisiz", "Bu arşiv kaydını görme yetkiniz bulunmamaktadır", False, False, False)


def filter_phase7_archive_records(
    records: Iterable[dict[str, Any]],
    *,
    current_user_id: Any = None,
    role: str | None = None,
    is_admin: bool = False,
    is_president: bool = False,
    is_hr: bool = False,
    allowed_user_ids: set[Any] | None = None,
) -> list[dict[str, Any]]:
    allowed = {str(x) for x in (allowed_user_ids or set())}
    output: list[dict[str, Any]] = []
    for record in records:
        record_user_id = record.get("user_id") or record.get("employee_id")
        same_scope = bool(record_user_id is not None and str(record_user_id) in allowed)
        decision = resolve_phase7_archive_visibility(
            role=role,
            current_user_id=current_user_id,
            record_user_id=record_user_id,
            same_scope=same_scope,
            is_admin=is_admin,
            is_president=is_president,
            is_hr=is_hr,
        )
        if decision.can_view:
            item = dict(record)
            if not decision.show_person_detail:
                item.pop("full_name", None)
                item.pop("registry_no", None)
            output.append(item)
    return output


def calculate_phase7_archive_summary(records: Iterable[dict[str, Any]], *, hide_person_detail: bool = True) -> dict[str, Any]:
    scores: list[float] = []
    years: set[int] = set()
    bands = {"Düşük Performans": 0, "Başarılı": 0, "Çok Başarılı": 0, "Puan Bilgisi Hatalı": 0}
    for record in records:
        score = _as_score(record.get("score") or record.get("puan"))
        year = _as_int(record.get("year") or record.get("yil"))
        if year:
            years.add(year)
        band = phase7_score_band(score)
        bands[band] = bands.get(band, 0) + 1
        if score is not None:
            scores.append(score)
    avg = round(sum(scores) / len(scores), 2) if scores else None
    return {
        "record_count": len(scores),
        "year_count": len(years),
        "average_score": avg,
        "bands": bands,
        "person_details_included": not hide_person_detail,
        "visibility_note": "Ortalama kişi detayı göstermeden hesaplandı." if hide_person_detail else "Yetkili kapsamda kişi detayı gösterilebilir.",
    }


def phase7_archive_contract() -> dict[str, Any]:
    return {
        "version": BYS360_PERFORMANCE_COMPLETION_PHASE7_VERSION,
        "table": PHASE7_ARCHIVE_TABLE_NAME,
        "required_import_columns": phase7_required_import_columns(),
        "rules": [
            "Geçmiş yıl puanları manuel veya Excel aktarımıyla arşivlenebilir.",
            "Sicil No, yıl, dönem, puan ve kaynak bilgisi zorunludur.",
            "Personel yalnızca kendi geçmiş karne/puan arşivini görür.",
            "Koordinatör ve Grup Başkanı yalnızca yetkili kapsamın geçmişini görür.",
            "Başkan, Admin ve yetkili İK genel arşiv görünürlüğü alabilir.",
            "Kategori/grup ortalamaları kişi detayı göstermeden hesaplanır.",
        ],
        "status_labels": dict(STATUS_LABELS),
        "markers": {
            "own_history_only": BYS360_PERFORMANCE_COMPLETION_PHASE7_OWN_HISTORY_ONLY,
            "scope_visibility": BYS360_PERFORMANCE_COMPLETION_PHASE7_SCOPE_VISIBILITY,
            "import_validation": BYS360_PERFORMANCE_COMPLETION_PHASE7_IMPORT_VALIDATION,
            "no_person_detail_in_average": BYS360_PERFORMANCE_COMPLETION_PHASE7_NO_PERSON_DETAIL_IN_AVERAGE,
            "audit_source_required": BYS360_PERFORMANCE_COMPLETION_PHASE7_AUDIT_SOURCE_REQUIRED,
        },
    }


def phase7_archive_schema_sql() -> str:
    return f"""
CREATE TABLE IF NOT EXISTS {PHASE7_ARCHIVE_TABLE_NAME} (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NULL,
    employee_id INTEGER NULL,
    registry_no VARCHAR(64) NOT NULL,
    full_name VARCHAR(255) NULL,
    year INTEGER NOT NULL,
    period_label VARCHAR(120) NOT NULL,
    score NUMERIC(5,2) NOT NULL,
    score_band VARCHAR(80) NULL,
    source_type VARCHAR(40) NOT NULL DEFAULT 'manual',
    source_file VARCHAR(255) NULL,
    note TEXT NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'imported',
    created_by_id INTEGER NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (registry_no, year, period_label)
);
""".strip()


def ensure_phase7_archive_schema() -> dict[str, Any]:
    try:
        from sqlalchemy import text

        from app import db
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return {"ok": False, "error": str(exc), "table": PHASE7_ARCHIVE_TABLE_NAME}
    try:
        db.session.execute(text(phase7_archive_schema_sql()))
        db.session.commit()
        return {"ok": True, "table": PHASE7_ARCHIVE_TABLE_NAME}
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        try:
            db.session.rollback()
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            logging.getLogger(__name__).exception("BYS360 suppressed exception captured in app/services/performance/phase7_scorecard_archive_center.py:326")
        return {"ok": False, "error": str(exc), "table": PHASE7_ARCHIVE_TABLE_NAME}


def seed_phase7_scorecard_archive_settings() -> dict[str, Any]:
    changed: list[str] = []
    schema = {"ok": False, "skipped": True}
    try:
        from app import db
        try:
            from app.models import ModuleSetting
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            from app.models.settings_models import ModuleSetting  # type: ignore
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return {"ok": False, "error": str(exc), "settings": changed, "schema": schema}

    schema = ensure_phase7_archive_schema()
    for module_key, setting_key, label, value_type, default_value, description in PHASE7_SETTING_ROWS:
        try:
            row = ModuleSetting.query.filter_by(module_key=module_key, setting_key=setting_key).first()
            if row is None:
                row = ModuleSetting(module_key=module_key, setting_key=setting_key)
                db.session.add(row)
            if hasattr(row, "label"):
                row.label = label
            if hasattr(row, "value_type"):
                row.value_type = value_type
            if hasattr(row, "default_value"):
                row.default_value = default_value
            if hasattr(row, "value_text") and not getattr(row, "value_text", None):
                row.value_text = default_value
            if hasattr(row, "description"):
                row.description = description
            if hasattr(row, "is_active"):
                row.is_active = True
            changed.append(f"{module_key}.{setting_key}")
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            continue
    try:
        db.session.commit()
        return {"ok": True, "settings": changed, "schema": schema}
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        try:
            db.session.rollback()
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            logging.getLogger(__name__).exception("BYS360 suppressed exception captured in app/services/performance/phase7_scorecard_archive_center.py:371")
        return {"ok": False, "error": str(exc), "settings": changed, "schema": schema}
