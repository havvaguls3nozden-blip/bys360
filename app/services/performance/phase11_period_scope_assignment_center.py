"""BYS360 Performans Tamamlama Faz 11: Çoklu dönem, özel kapsam ve görev üretimi final merkezi.

Bu merkez, performans dönemlerinin yıllık/6 aylık/3 aylık/aylık/özel dönem
mantığıyla açılmasını; tüm kurum, birim, üst birim, kategori/grup veya seçili
personel kapsamına göre gerçek personel listesinin çıkarılmasını ve görev
üretiminden önce son kontrolün yapılmasını sağlar.

Kritik sınırlar:
- Dönem oluşturmak tek başına değerlendirmeyi başlatmaz; kriter/ağırlık/görev üretimi kontrolü gerekir.
- Kapsam dışı personele sahte görev üretilmez.
- Aynı personel için aynı tarih aralığında çakışan aktif dönem uyarısı üretilir.
- Kullanıcı ekranına teknik faz, workflow, endpoint, debug dili taşınmaz.
"""
from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

logger = logging.getLogger(__name__)

BYS360_PERFORMANCE_COMPLETION_PHASE11_PERIOD_SCOPE_ASSIGNMENT_FINAL = True
BYS360_PERFORMANCE_COMPLETION_PHASE11_VERSION = "performance-completion-phase11-period-scope-assignment-final-v1"
BYS360_PERFORMANCE_COMPLETION_PHASE11_MULTI_PERIOD = True
BYS360_PERFORMANCE_COMPLETION_PHASE11_SCOPE_TYPES = True
BYS360_PERFORMANCE_COMPLETION_PHASE11_OVERLAP_CONTROL = True
BYS360_PERFORMANCE_COMPLETION_PHASE11_NO_FAKE_ASSIGNMENT = True
BYS360_PERFORMANCE_COMPLETION_PHASE11_ASSIGNMENT_PRECHECK = True
BYS360_PERFORMANCE_COMPLETION_PHASE11_TECHNICAL_LANGUAGE_CLEAN = True

PHASE11_TABLE_NAME = "performance_period_scope_audit_logs"

PERIOD_TYPE_LABELS = {
    "annual": "Yıllık Dönem",
    "yearly": "Yıllık Dönem",
    "semiannual": "6 Aylık Dönem",
    "six_months": "6 Aylık Dönem",
    "quarterly": "3 Aylık Dönem",
    "three_months": "3 Aylık Dönem",
    "monthly": "Aylık Dönem",
    "special": "Özel Dönem",
}

SCOPE_TYPE_LABELS = {
    "all": "Tüm Kurum",
    "institution": "Tüm Kurum",
    "unit": "Birim Kapsamı",
    "parent_unit": "Üst Birim Kapsamı",
    "category": "Kategori / Grup Kapsamı",
    "group": "Kategori / Grup Kapsamı",
    "selected_personnel": "Seçili Personel Kapsamı",
    "selected_users": "Seçili Personel Kapsamı",
}

PERIOD_STATUS_LABELS = {
    "draft": "Taslak",
    "ready": "Görev Üretimine Hazır",
    "active": "Aktif Dönem",
    "locked": "Kilitleme Aşamasında",
    "closed": "Kapalı Dönem",
    "cancelled": "İptal Edildi",
    "overlap_warning": "Çakışma Uyarısı Var",
    "assignment_blocked": "Görev Üretimi Kontrol Bekliyor",
}

ASSIGNMENT_STATUS_LABELS = {
    "precheck_required": "Görev Üretimi Ön Kontrol Gerekli",
    "scope_empty": "Kapsamda Personel Bulunamadı",
    "scope_ready": "Kapsam Görev Üretimine Hazır",
    "overlap_found": "Çakışan Dönem Tespit Edildi",
    "missing_criteria": "Değerlendirme Kriteri Eksik",
    "missing_weight": "Ağırlık Ayarı Eksik",
    "missing_manager_chain": "Amir Zinciri Kontrolü Gerekli",
    "generated": "Görevler Oluşturuldu",
}

PHASE11_SETTING_ROWS = [
    ("performance_phase11", "period_scope_final_enabled", "Çoklu dönem ve kapsam final kontrolü aktif", "bool", "true", "Performans dönemi görev üretiminden önce dönem/kapsam/çakışma kontrolünü çalıştırır."),
    ("performance_phase11", "allow_multiple_periods_same_year", "Aynı yıl içinde birden fazla dönem açılabilir", "bool", "true", "Yıllık, 6 aylık, 3 aylık, aylık ve özel dönemler desteklenir."),
    ("performance_phase11", "allow_category_period", "Kategori/grup özel dönemleri aktif", "bool", "true", "Güvenlik, Temizlik gibi kategorilere özel dönem açılmasını destekler."),
    ("performance_phase11", "allow_selected_personnel_period", "Seçili personele özel dönem aktif", "bool", "true", "Deneme süreli veya ayrılacak personel için özel değerlendirme dönemi açılabilir."),
    ("performance_phase11", "overlap_control_enabled", "Dönem çakışma kontrolü aktif", "bool", "true", "Aynı personel için aynı tarih aralığında aktif dönem çakışması uyarı üretir."),
    ("performance_phase11", "assignment_precheck_required", "Görev üretimi ön kontrolü zorunlu", "bool", "true", "Kriter, ağırlık, kapsam ve amir zinciri doğrulanmadan görev üretimi tamamlanmış sayılmaz."),
    ("performance_phase11", "no_fake_assignment", "Kapsam dışı sahte görev engeli", "bool", "true", "Yalnızca dönem kapsamına giren gerçek personel için görev üretimi yapılır."),
    ("performance_phase11", "technical_language_clean", "Dönem/görev ekranlarında teknik dil temizliği aktif", "bool", "true", "Workflow/debug/endpoint gibi teknik ifadeler kullanıcıya gösterilmez."),
]

TECHNICAL_WORDS = [
    "workflow", "endpoint", "debug", "traceback", "exception", "authorized_scope", "raw json", "json", "stacktrace", "phase sync", "sync", "assignment_builder",
]

@dataclass(frozen=True)
class Phase11ValidationResult:
    ok: bool
    errors: list[str]
    warnings: list[str]
    normalized: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "errors": list(self.errors), "warnings": list(self.warnings), "normalized": dict(self.normalized)}

@dataclass(frozen=True)
class Phase11AssignmentPrecheck:
    ok: bool
    status: str
    status_label: str
    eligible_personnel_count: int
    blocked_reason: str
    warnings: list[str]
    required_actions: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "status": self.status,
            "status_label": self.status_label,
            "eligible_personnel_count": self.eligible_personnel_count,
            "blocked_reason": self.blocked_reason,
            "warnings": list(self.warnings),
            "required_actions": list(self.required_actions),
        }

@dataclass(frozen=True)
class Phase11OverlapResult:
    has_overlap: bool
    overlapping_period_ids: list[Any]
    message: str

    def as_dict(self) -> dict[str, Any]:
        return {"has_overlap": self.has_overlap, "overlapping_period_ids": list(self.overlapping_period_ids), "message": self.message}


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    text = _as_text(value).lower()
    if text in {"1", "true", "yes", "evet", "aktif", "on"}:
        return True
    if text in {"0", "false", "no", "hayır", "hayir", "pasif", "off"}:
        return False
    return default


def _as_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = _as_text(value)
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            continue
    return None


def _row_get(row: Any, key: str, default: Any = None) -> Any:
    if row is None:
        return default
    if isinstance(row, dict):
        return row.get(key, default)
    return getattr(row, key, default)


def _normalize_period_type(value: Any) -> str:
    key = _as_text(value).lower()
    aliases = {"yearly": "annual", "six_months": "semiannual", "6_months": "semiannual", "three_months": "quarterly", "3_months": "quarterly"}
    return aliases.get(key, key or "annual")


def _normalize_scope_type(value: Any) -> str:
    key = _as_text(value).lower()
    aliases = {"institution": "all", "group": "category", "selected_users": "selected_personnel", "personnel": "selected_personnel"}
    return aliases.get(key, key or "all")


def phase11_period_type_label(period_type: Any) -> str:
    key = _normalize_period_type(period_type)
    return PERIOD_TYPE_LABELS.get(key, _as_text(period_type) or "Dönem")


def phase11_scope_type_label(scope_type: Any) -> str:
    key = _normalize_scope_type(scope_type)
    return SCOPE_TYPE_LABELS.get(key, _as_text(scope_type) or "Kapsam")


def phase11_period_status_label(status: Any) -> str:
    key = _as_text(status).lower()
    return PERIOD_STATUS_LABELS.get(key, _as_text(status) or "Dönem Durumu")


def phase11_assignment_status_label(status: Any) -> str:
    key = _as_text(status).lower()
    return ASSIGNMENT_STATUS_LABELS.get(key, _as_text(status) or "Görev Üretimi Durumu")


def phase11_clean_text(value: Any) -> str:
    text = _as_text(value)
    replacements = {
        "workflow state": "süreç durumu",
        "workflow": "süreç",
        "endpoint": "bağlantı",
        "debug": "teknik kayıt",
        "exception": "hata kaydı",
        "traceback": "hata izi",
        "authorized_scope": "yetki kapsamı",
        "phase sync": "süreç eşleşmesi",
        "assignment_builder": "görev üretimi",
        "raw json": "ham veri",
        "json": "veri",
        "stacktrace": "hata izi",
        "sync": "eşleşme",
    }
    for old, new in replacements.items():
        text = text.replace(old, new).replace(old.upper(), new).replace(old.title(), new)
    return text.strip()


def phase11_contains_visible_technical_language(value: Any) -> bool:
    lower = _as_text(value).lower()
    return any(word in lower for word in TECHNICAL_WORDS)


def phase11_scope_requires_selector(scope_type: Any) -> bool:
    return _normalize_scope_type(scope_type) in {"unit", "parent_unit", "category", "selected_personnel"}


def phase11_validate_period_scope(payload: dict[str, Any]) -> Phase11ValidationResult:
    errors: list[str] = []
    warnings: list[str] = []
    name = _as_text(payload.get("name") or payload.get("period_name") or payload.get("title"))
    period_type = _normalize_period_type(payload.get("period_type") or payload.get("type"))
    scope_type = _normalize_scope_type(payload.get("scope_type") or payload.get("scope"))
    start_date = _as_date(payload.get("start_date") or payload.get("start"))
    end_date = _as_date(payload.get("end_date") or payload.get("end"))
    selector = payload.get("scope_value") or payload.get("scope_id") or payload.get("category") or payload.get("unit_id") or payload.get("selected_personnel_ids")

    if not name:
        errors.append("Dönem adı zorunludur.")
    if period_type not in {"annual", "semiannual", "quarterly", "monthly", "special"}:
        errors.append("Desteklenmeyen dönem türü seçildi.")
    if scope_type not in {"all", "unit", "parent_unit", "category", "selected_personnel"}:
        errors.append("Desteklenmeyen kapsam tipi seçildi.")
    if not start_date or not end_date:
        errors.append("Başlangıç ve bitiş tarihi zorunludur.")
    elif end_date < start_date:
        errors.append("Bitiş tarihi başlangıç tarihinden önce olamaz.")

    if phase11_scope_requires_selector(scope_type):
        empty_selector = selector in (None, "", [], (), set())
        if empty_selector:
            errors.append(f"{phase11_scope_type_label(scope_type)} için kapsam seçimi zorunludur.")
    if scope_type == "selected_personnel" and selector and len(selector if isinstance(selector, (list, tuple, set)) else [selector]) == 1:
        warnings.append("Seçili personel kapsamı tek kişiyle oluşturuluyor; görev üretimi ön kontrolü önerilir.")

    normalized = {
        "name": name,
        "period_type": period_type,
        "period_type_label": phase11_period_type_label(period_type),
        "scope_type": scope_type,
        "scope_type_label": phase11_scope_type_label(scope_type),
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "scope_requires_selector": phase11_scope_requires_selector(scope_type),
    }
    return Phase11ValidationResult(ok=not errors, errors=errors, warnings=warnings, normalized=normalized)


def phase11_dates_overlap(start_a: Any, end_a: Any, start_b: Any, end_b: Any) -> bool:
    a_start, a_end, b_start, b_end = _as_date(start_a), _as_date(end_a), _as_date(start_b), _as_date(end_b)
    if not a_start or not a_end or not b_start or not b_end:
        return False
    return a_start <= b_end and b_start <= a_end


def phase11_detect_period_overlap(candidate: dict[str, Any], existing_periods: Iterable[Any]) -> Phase11OverlapResult:
    c_start = candidate.get("start_date") or candidate.get("start")
    c_end = candidate.get("end_date") or candidate.get("end")
    c_personnel = set(candidate.get("personnel_ids") or candidate.get("selected_personnel_ids") or [])
    overlaps: list[Any] = []
    for period in existing_periods or []:
        status = _as_text(_row_get(period, "status", "active")).lower()
        if status in {"closed", "cancelled", "passive", "pasif"}:
            continue
        if not phase11_dates_overlap(c_start, c_end, _row_get(period, "start_date") or _row_get(period, "start"), _row_get(period, "end_date") or _row_get(period, "end")):
            continue
        p_personnel = set(_row_get(period, "personnel_ids", []) or _row_get(period, "selected_personnel_ids", []) or [])
        if not c_personnel or not p_personnel or c_personnel.intersection(p_personnel):
            overlaps.append(_row_get(period, "id", _row_get(period, "period_id", "bilinmeyen")))
    if overlaps:
        return Phase11OverlapResult(True, overlaps, "Aynı tarih aralığında çakışan aktif dönem bulundu.")
    return Phase11OverlapResult(False, [], "Çakışan aktif dönem bulunmadı.")


def phase11_filter_personnel_by_scope(personnel_rows: Iterable[Any], scope: dict[str, Any]) -> list[Any]:
    scope_type = _normalize_scope_type(scope.get("scope_type") or scope.get("scope"))
    rows = list(personnel_rows or [])
    if scope_type == "all":
        return rows
    if scope_type == "unit":
        unit_id = scope.get("unit_id") or scope.get("scope_value") or scope.get("scope_id")
        return [row for row in rows if _as_text(_row_get(row, "unit_id")) == _as_text(unit_id)]
    if scope_type == "parent_unit":
        parent_unit_id = scope.get("parent_unit_id") or scope.get("scope_value") or scope.get("scope_id")
        return [row for row in rows if _as_text(_row_get(row, "parent_unit_id")) == _as_text(parent_unit_id)]
    if scope_type == "category":
        category = scope.get("category") or scope.get("scope_value") or scope.get("scope_id")
        return [row for row in rows if _as_text(_row_get(row, "performance_category") or _row_get(row, "category")).lower() == _as_text(category).lower()]
    if scope_type == "selected_personnel":
        selected = set(str(x) for x in (scope.get("selected_personnel_ids") or scope.get("personnel_ids") or scope.get("scope_value") or []))
        return [row for row in rows if str(_row_get(row, "id") or _row_get(row, "user_id") or _row_get(row, "personnel_id")) in selected]
    return []


def phase11_assignment_precheck(
    period_payload: dict[str, Any],
    personnel_rows: Iterable[Any] | None = None,
    *,
    criteria_ok: bool = True,
    weights_ok: bool = True,
    manager_chain_ok: bool = True,
    existing_periods: Iterable[Any] | None = None,
) -> Phase11AssignmentPrecheck:
    validation = phase11_validate_period_scope(period_payload)
    warnings = list(validation.warnings)
    required_actions: list[str] = []
    if not validation.ok:
        required_actions.extend(validation.errors)
        return Phase11AssignmentPrecheck(False, "precheck_required", phase11_assignment_status_label("precheck_required"), 0, "Dönem/kapsam bilgisi tamamlanmalı.", warnings, required_actions)

    eligible = phase11_filter_personnel_by_scope(personnel_rows or [], period_payload)
    if not eligible:
        return Phase11AssignmentPrecheck(False, "scope_empty", phase11_assignment_status_label("scope_empty"), 0, "Seçilen kapsamda aktif personel bulunamadı.", warnings, ["Kapsam seçimini ve personel kategori/birim bilgilerini kontrol edin."])

    overlap = phase11_detect_period_overlap({**period_payload, "personnel_ids": [(_row_get(row, "id") or _row_get(row, "user_id") or _row_get(row, "personnel_id")) for row in eligible]}, existing_periods or [])
    if overlap.has_overlap:
        warnings.append(overlap.message)
        required_actions.append("Çakışan dönemler kontrol edilmelidir.")
        return Phase11AssignmentPrecheck(False, "overlap_found", phase11_assignment_status_label("overlap_found"), len(eligible), overlap.message, warnings, required_actions)

    if not criteria_ok:
        required_actions.append("Değerlendirme kriterlerini tamamlayın.")
    if not weights_ok:
        required_actions.append("Amir ağırlık ayarlarını tamamlayın.")
    if not manager_chain_ok:
        required_actions.append("Amir zinciri eksiklerini kontrol edin.")

    if required_actions:
        status = "missing_criteria" if not criteria_ok else "missing_weight" if not weights_ok else "missing_manager_chain"
        return Phase11AssignmentPrecheck(False, status, phase11_assignment_status_label(status), len(eligible), "Görev üretimi öncesi zorunlu kontroller tamamlanmalı.", warnings, required_actions)

    return Phase11AssignmentPrecheck(True, "scope_ready", phase11_assignment_status_label("scope_ready"), len(eligible), "", warnings, [])


def phase11_safe_assignment_rows(personnel_rows: Iterable[Any], scope: dict[str, Any]) -> list[dict[str, Any]]:
    eligible = phase11_filter_personnel_by_scope(personnel_rows, scope)
    rows: list[dict[str, Any]] = []
    for row in eligible:
        rows.append({
            "personnel_id": _row_get(row, "id") or _row_get(row, "user_id") or _row_get(row, "personnel_id"),
            "sicil_no": _row_get(row, "sicil_no", ""),
            "name": _row_get(row, "name", _row_get(row, "full_name", "")),
            "scope_type": _normalize_scope_type(scope.get("scope_type") or scope.get("scope")),
            "fake_assignment": False,
        })
    return rows


def phase11_period_scope_contract() -> dict[str, Any]:
    return {
        "version": BYS360_PERFORMANCE_COMPLETION_PHASE11_VERSION,
        "markers": {
            "multi_period": BYS360_PERFORMANCE_COMPLETION_PHASE11_MULTI_PERIOD,
            "scope_types": BYS360_PERFORMANCE_COMPLETION_PHASE11_SCOPE_TYPES,
            "overlap_control": BYS360_PERFORMANCE_COMPLETION_PHASE11_OVERLAP_CONTROL,
            "no_fake_assignment": BYS360_PERFORMANCE_COMPLETION_PHASE11_NO_FAKE_ASSIGNMENT,
            "assignment_precheck": BYS360_PERFORMANCE_COMPLETION_PHASE11_ASSIGNMENT_PRECHECK,
            "technical_language_clean": BYS360_PERFORMANCE_COMPLETION_PHASE11_TECHNICAL_LANGUAGE_CLEAN,
        },
        "period_types": PERIOD_TYPE_LABELS,
        "scope_types": SCOPE_TYPE_LABELS,
        "assignment_status_labels": ASSIGNMENT_STATUS_LABELS,
        "settings": [
            {"module_key": module_key, "setting_key": setting_key, "label": label, "value_type": value_type, "default_value": default_value, "description": description}
            for module_key, setting_key, label, value_type, default_value, description in PHASE11_SETTING_ROWS
        ],
        "rules": [
            "Aynı yıl içinde birden fazla dönem desteklenir.",
            "Dönem kapsamı tüm kurum, birim, üst birim, kategori/grup veya seçili personel olabilir.",
            "Kapsam dışı personele sahte görev üretilmez.",
            "Aynı personel ve tarih aralığında çakışan aktif dönem uyarı üretir.",
            "Kriter, ağırlık ve amir zinciri kontrolü tamamlanmadan görev üretimi kapandı sayılmaz.",
        ],
    }


def ensure_phase11_tables(db: Any | None = None) -> dict[str, Any]:
    try:
        if db is None:
            from app import db as flask_db
            db = flask_db
        from sqlalchemy import text
        db.session.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {PHASE11_TABLE_NAME} (
                id SERIAL PRIMARY KEY,
                period_id INTEGER NULL,
                action_key VARCHAR(120) NOT NULL,
                scope_type VARCHAR(80) NULL,
                scope_label VARCHAR(255) NULL,
                affected_personnel_count INTEGER DEFAULT 0,
                status_key VARCHAR(80) NOT NULL DEFAULT 'logged',
                status_label VARCHAR(255) NULL,
                message TEXT NULL,
                created_by INTEGER NULL,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
            )
        """))
        db.session.commit()
        return {"ok": True, "table": PHASE11_TABLE_NAME}
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        try:
            if db is not None:
                db.session.rollback()
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            logging.getLogger(__name__).exception("BYS360 suppressed exception captured in app/services/performance/phase11_period_scope_assignment_center.py:434")
        return {"ok": False, "error": str(exc), "table": PHASE11_TABLE_NAME}


def seed_phase11_settings(db: Any | None = None) -> dict[str, Any]:
    try:
        if db is None:
            from app import db as flask_db
            db = flask_db
        from sqlalchemy import inspect, text
        table_result = ensure_phase11_tables(db)
        bind = db.session.get_bind()
        inspector = inspect(bind)
        if "module_settings" not in inspector.get_table_names():
            return {"ok": False, "error": "module_settings tablosu bulunamadı", "table": table_result}
        columns = {col["name"] for col in inspector.get_columns("module_settings")}
        if not {"module_key", "setting_key"}.issubset(columns):
            return {"ok": False, "error": "module_settings tablo kolonları eksik", "columns": sorted(columns), "table": table_result}
        created: list[str] = []
        updated: list[str] = []
        for module_key, setting_key, label, value_type, default_value, description in PHASE11_SETTING_ROWS:
            existing = db.session.execute(
                text("SELECT id FROM module_settings WHERE module_key=:module_key AND setting_key=:setting_key LIMIT 1"),
                {"module_key": module_key, "setting_key": setting_key},
            ).mappings().first()
            payload: dict[str, Any] = {}
            if "module_key" in columns:
                payload["module_key"] = module_key
            if "setting_key" in columns:
                payload["setting_key"] = setting_key
            if "label" in columns:
                payload["label"] = label
            if "value_type" in columns:
                payload["value_type"] = value_type
            if "description" in columns:
                payload["description"] = description
            if "is_active" in columns:
                payload["is_active"] = True
            if "value_text" in columns:
                payload["value_text"] = str(default_value)
            if "value" in columns:
                payload["value"] = str(default_value)
            if "default_value" in columns:
                payload["default_value"] = str(default_value)
            if existing:
                update_cols = [key for key in payload if key not in {"module_key", "setting_key"}]
                if update_cols:
                    set_sql = ", ".join(f"{col}=:{col}" for col in update_cols)
                    params = {col: payload[col] for col in update_cols}
                    params["row_id"] = existing["id"]
                    db.session.execute(text(f"UPDATE module_settings SET {set_sql} WHERE id=:row_id"), params)
                updated.append(f"{module_key}.{setting_key}")
            else:
                insert_cols = list(payload.keys())
                col_sql = ", ".join(insert_cols)
                val_sql = ", ".join(f":{col}" for col in insert_cols)
                db.session.execute(text(f"INSERT INTO module_settings ({col_sql}) VALUES ({val_sql})"), payload)
                created.append(f"{module_key}.{setting_key}")
        db.session.commit()
        return {"ok": bool(table_result.get("ok", False)), "created": created, "updated": updated, "table": table_result}
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        try:
            if db is not None:
                db.session.rollback()
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            logging.getLogger(__name__).exception("BYS360 suppressed exception captured in app/services/performance/phase11_period_scope_assignment_center.py:498")
        return {"ok": False, "error": str(exc)}
