"""BYS360 Performans Tamamlama Faz 9: Gelişim önerisi ve rehber alanı merkezi.

Bu merkez, performans sürecinde oluşan gelişim önerisi, güçlü yön, eğitim/takip
önerisi ve rehber notlarını güvenli biçimde yönetir.
Kritik sınır: Gelişim önerisi otomatik puan, ceza, disiplin sonucu veya idari
karar üretmez; yalnızca gelişim ve takip amacıyla rehber bilgi sağlar.
"""
from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

logger = logging.getLogger(__name__)

BYS360_PERFORMANCE_COMPLETION_PHASE9_DEVELOPMENT_GUIDANCE_CENTER = True
BYS360_PERFORMANCE_COMPLETION_PHASE9_VERSION = "performance-completion-phase9-development-guidance-center-v1"
BYS360_PERFORMANCE_COMPLETION_PHASE9_NO_AUTO_SCORE = True
BYS360_PERFORMANCE_COMPLETION_PHASE9_NO_ADMIN_DECISION = True
BYS360_PERFORMANCE_COMPLETION_PHASE9_SCORECARD_GUIDANCE = True
BYS360_PERFORMANCE_COMPLETION_PHASE9_EVALUATOR_CONTEXT = True
BYS360_PERFORMANCE_COMPLETION_PHASE9_EMPLOYEE_PUBLISHED_ONLY = True
BYS360_PERFORMANCE_COMPLETION_PHASE9_SCOPE_VISIBILITY = True
BYS360_PERFORMANCE_COMPLETION_PHASE9_TECHNICAL_LANGUAGE_CLEAN = True

PHASE9_TABLE_NAME = "performance_development_guidance_notes"

GUIDANCE_TYPE_LABELS = {
    "strong_side": "Güçlü Yön",
    "development_need": "Gelişim İhtiyacı",
    "education_suggestion": "Eğitim Önerisi",
    "coaching": "Rehberlik / Koçluk Notu",
    "follow_up": "Takip Önerisi",
    "general_guidance": "Genel Gelişim Önerisi",
}

PRIORITY_LABELS = {
    "low": "Düşük Öncelik",
    "medium": "Orta Öncelik",
    "high": "Yüksek Öncelik",
    "critical": "Öncelikli Takip Gerektirir",
}

STATUS_LABELS = {
    "draft": "Taslak Gelişim Notu",
    "active": "Aktif Gelişim Notu",
    "scorecard_ready": "Karne Rehber Alanına Hazır",
    "published": "Personel Görünürlüğüne Açıldı",
    "follow_up_required": "Takip Gerektiriyor",
    "completed": "Takip Tamamlandı",
    "archived": "Arşivlendi",
    "rejected": "İade Edildi",
}

SOURCE_LABELS = {
    "scorecard": "Karne Sonucu",
    "midterm_note": "Dönem İçi Not",
    "manager_review": "Amir Değerlendirmesi",
    "president_review": "Üst Onay İncelemesi",
    "manual": "Manuel Rehber Not",
    "ai_summary": "AI Destekli Özet",
}

PHASE9_SETTING_ROWS = [
    ("performance_phase9", "development_guidance_enabled", "Gelişim önerisi alanı aktif", "bool", "true", "Karne ve puanlama sürecinde gelişim önerisi/rehber not alanını etkinleştirir."),
    ("performance_phase9", "guidance_no_auto_score", "Gelişim önerisi puan üretmez", "bool", "true", "Gelişim önerileri nihai performans puanını otomatik değiştirmez."),
    ("performance_phase9", "guidance_no_admin_decision", "Gelişim önerisi idari karar üretmez", "bool", "true", "Rehber notlar ceza, disiplin veya işten çıkarma kararı oluşturmaz."),
    ("performance_phase9", "scorecard_guidance_enabled", "Karne rehber alanı aktif", "bool", "true", "Yayınlanan karnede güçlü yön ve gelişim önerisi özetini gösterir."),
    ("performance_phase9", "employee_guidance_requires_publish", "Personel görünürlüğü yayınla açılır", "bool", "true", "Personel gelişim önerisini yalnızca yetkili yayın sonrası görür."),
    ("performance_phase9", "evaluator_guidance_context_enabled", "Amire gelişim bağlamı göster", "bool", "true", "Puanlama/karne incelemede amire önceki gelişim notlarını bağlam olarak sunar."),
    ("performance_phase9", "scope_limited_guidance", "Gelişim önerisi görünürlüğü kapsamla sınırlı", "bool", "true", "Yöneticiler yalnızca yetkili oldukları kapsamın rehber notlarını görür."),
]

REQUIRED_GUIDANCE_FIELDS = ["employee_id", "guidance_type", "guidance_text", "source"]
TECHNICAL_WORDS = ["workflow", "endpoint", "debug", "traceback", "exception", "phase sync", "authorized_scope", "raw", "json", "stack"]

@dataclass(frozen=True)
class Phase9GuidanceValidation:
    ok: bool
    errors: list[str]
    warnings: list[str]
    normalized: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "errors": list(self.errors), "warnings": list(self.warnings), "normalized": dict(self.normalized)}

@dataclass(frozen=True)
class Phase9VisibilityDecision:
    can_view: bool
    scope: str
    reason: str
    show_person_detail: bool
    can_create: bool
    can_publish: bool
    can_follow_up: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "can_view": self.can_view,
            "scope": self.scope,
            "reason": self.reason,
            "show_person_detail": self.show_person_detail,
            "can_create": self.can_create,
            "can_publish": self.can_publish,
            "can_follow_up": self.can_follow_up,
        }


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
        score = float(text)
        return max(0.0, min(100.0, score))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return None


def _as_date_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    text = _as_text(value)
    if not text:
        return ""
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            continue
    return text


def phase9_guidance_type_label(guidance_type: Any) -> str:
    text = _as_text(guidance_type).lower()
    return GUIDANCE_TYPE_LABELS.get(text, _as_text(guidance_type) or "Genel Gelişim Önerisi")


def phase9_priority_label(priority: Any) -> str:
    text = _as_text(priority).lower()
    return PRIORITY_LABELS.get(text, _as_text(priority) or "Orta Öncelik")


def phase9_status_label(status: Any) -> str:
    text = _as_text(status).lower()
    return STATUS_LABELS.get(text, _as_text(status) or "Gelişim Notu Durumu Belirtilmedi")


def phase9_source_label(source: Any) -> str:
    text = _as_text(source).lower()
    return SOURCE_LABELS.get(text, _as_text(source) or "Manuel Rehber Not")


def phase9_clean_text(value: Any) -> str:
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
        "raw json": "ham veri",
        "json": "veri",
        "stack trace": "hata izi",
    }
    for old, new in replacements.items():
        text = text.replace(old, new).replace(old.upper(), new).replace(old.title(), new)
    return text


def phase9_contains_technical_language(value: Any) -> bool:
    text = _as_text(value).lower()
    return any(word in text for word in TECHNICAL_WORDS)


def normalize_phase9_guidance(row: dict[str, Any]) -> dict[str, Any]:
    guidance_type = _as_text(row.get("guidance_type") or row.get("type") or row.get("tur") or "general_guidance").lower()
    if guidance_type not in GUIDANCE_TYPE_LABELS:
        guidance_type = "general_guidance"
    priority = _as_text(row.get("priority") or row.get("oncelik") or "medium").lower()
    if priority not in PRIORITY_LABELS:
        priority = "medium"
    source = _as_text(row.get("source") or row.get("kaynak") or "manual").lower()
    if source not in SOURCE_LABELS:
        source = "manual"
    include_in_scorecard = _as_bool(row.get("include_in_scorecard"), True)
    employee_visible = _as_bool(row.get("employee_visible"), False)
    follow_up_required = _as_bool(row.get("follow_up_required"), priority in {"high", "critical"})
    status = _as_text(row.get("status") or row.get("durum") or "active").lower()
    if include_in_scorecard and status == "active":
        status = "scorecard_ready"
    if employee_visible:
        status = "published"
    if follow_up_required and status not in {"published", "completed"}:
        status = "follow_up_required"
    text = phase9_clean_text(row.get("guidance_text") or row.get("note_text") or row.get("aciklama") or "")
    strong_side = phase9_clean_text(row.get("strong_side") or row.get("guclu_yon") or "")
    development_need = phase9_clean_text(row.get("development_need") or row.get("gelisim_ihtiyaci") or "")
    return {
        "employee_id": _as_int(row.get("employee_id") or row.get("user_id") or row.get("personel_id")),
        "period_id": _as_int(row.get("period_id") or row.get("performance_period_id") or row.get("donem_id")),
        "scorecard_id": _as_int(row.get("scorecard_id") or row.get("karne_id")),
        "created_by_id": _as_int(row.get("created_by_id") or row.get("creator_id") or row.get("olusturan_id")),
        "guidance_type": guidance_type,
        "guidance_type_label": phase9_guidance_type_label(guidance_type),
        "guidance_text": text,
        "strong_side": strong_side,
        "development_need": development_need,
        "suggested_action": phase9_clean_text(row.get("suggested_action") or row.get("onerilen_aksiyon") or ""),
        "priority": priority,
        "priority_label": phase9_priority_label(priority),
        "source": source,
        "source_label": phase9_source_label(source),
        "status": status,
        "status_label": phase9_status_label(status),
        "score_snapshot": _as_score(row.get("score_snapshot") or row.get("final_score") or row.get("puan")),
        "follow_up_required": follow_up_required,
        "include_in_scorecard": include_in_scorecard,
        "employee_visible": employee_visible,
        "guidance_date": _as_date_text(row.get("guidance_date") or row.get("created_at") or row.get("tarih")),
        "auto_score_effect": 0,
        "admin_decision_effect": False,
    }


def validate_phase9_guidance(row: dict[str, Any]) -> Phase9GuidanceValidation:
    normalized = normalize_phase9_guidance(row)
    errors: list[str] = []
    warnings: list[str] = []
    if not normalized.get("employee_id"):
        errors.append("Personel bilgisi zorunludur.")
    if normalized.get("guidance_type") not in GUIDANCE_TYPE_LABELS:
        errors.append("Gelişim önerisi türü geçerli değildir.")
    if not normalized.get("guidance_text") and not normalized.get("strong_side") and not normalized.get("development_need"):
        errors.append("Gelişim önerisi, güçlü yön veya gelişim ihtiyacı alanlarından en az biri doldurulmalıdır.")
    if normalized.get("source") not in SOURCE_LABELS:
        errors.append("Kaynak bilgisi geçerli değildir.")
    if phase9_contains_technical_language(normalized.get("guidance_text")):
        warnings.append("Gelişim önerisi metninde teknik ifade temizlenmelidir.")
    if normalized.get("priority") in {"high", "critical"} and not normalized.get("suggested_action"):
        warnings.append("Yüksek öncelikli gelişim notlarında önerilen takip adımı yazılması önerilir.")
    if normalized.get("auto_score_effect") != 0:
        errors.append("Gelişim önerisi otomatik puan etkisi üretemez.")
    if normalized.get("admin_decision_effect"):
        errors.append("Gelişim önerisi idari karar etkisi üretemez.")
    return Phase9GuidanceValidation(ok=not errors, errors=errors, warnings=warnings, normalized=normalized)


def resolve_phase9_guidance_visibility(*, role: Any, current_user_id: Any = None, employee_id: Any = None, same_scope: bool = False, guidance_status: Any = "active", employee_visible: Any = False, action: str = "view") -> Phase9VisibilityDecision:
    role_text = _as_text(role).lower()
    status = _as_text(guidance_status).lower()
    current_id = _as_int(current_user_id)
    emp_id = _as_int(employee_id)
    is_own = current_id is not None and emp_id is not None and current_id == emp_id
    published = status == "published" or _as_bool(employee_visible, False)
    admin_roles = {"admin", "sistem_yoneticisi", "sistem yöneticisi", "başkan", "baskan", "ik", "insan_kaynaklari", "performans_yetkilisi"}
    manager_roles = {"koordinatör", "koordinator", "grup_baskani", "grup başkanı", "amir", "yonetici", "yönetici"}
    if role_text in admin_roles:
        return Phase9VisibilityDecision(True, "global", "Yetkili yönetim görünürlüğü", True, True, True, True)
    if role_text in manager_roles and same_scope:
        return Phase9VisibilityDecision(True, "authorized_scope", "Yetkili organizasyon kapsamı", True, True, False, True)
    if role_text in {"personel", "employee", "user"} and is_own and published:
        return Phase9VisibilityDecision(True, "own_published", "Personelin yayınlanmış kendi gelişim önerisi", False, False, False, False)
    if role_text in {"personel", "employee", "user"} and is_own and not published:
        return Phase9VisibilityDecision(False, "own_unpublished", "Gelişim önerisi henüz personel görünürlüğüne açılmamış", False, False, False, False)
    if action in {"create", "follow_up"} and role_text in manager_roles and same_scope:
        return Phase9VisibilityDecision(True, "authorized_scope", "Yetkili amir gelişim önerisi oluşturabilir", True, True, False, True)
    return Phase9VisibilityDecision(False, "blocked", "Bu gelişim önerisi için yetkiniz bulunmamaktadır.", False, False, False, False)


def filter_phase9_guidance_items(items: Iterable[dict[str, Any]], *, current_user_id: Any, role: Any, same_scope: bool = False) -> list[dict[str, Any]]:
    visible: list[dict[str, Any]] = []
    for item in items:
        normalized = normalize_phase9_guidance(item)
        decision = resolve_phase9_guidance_visibility(role=role, current_user_id=current_user_id, employee_id=normalized.get("employee_id"), same_scope=same_scope, guidance_status=normalized.get("status"), employee_visible=normalized.get("employee_visible"))
        if decision.can_view:
            if not decision.show_person_detail:
                normalized.pop("created_by_id", None)
            visible.append(normalized)
    return visible


def build_phase9_scorecard_guidance_summary(items: Iterable[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, int] = {}
    visible_items: list[dict[str, Any]] = []
    for item in items:
        normalized = normalize_phase9_guidance(item)
        if not (normalized.get("include_in_scorecard") or normalized.get("employee_visible") or normalized.get("status") == "published"):
            continue
        label = normalized["guidance_type_label"]
        grouped[label] = grouped.get(label, 0) + 1
        visible_items.append({
            "type": label,
            "priority": normalized["priority_label"],
            "strong_side": normalized.get("strong_side") or "",
            "development_need": normalized.get("development_need") or "",
            "guidance": normalized.get("guidance_text") or "",
            "suggested_action": normalized.get("suggested_action") or "",
            "status": normalized["status_label"],
        })
    return {
        "ok": True,
        "summary_counts": grouped,
        "visible_count": len(visible_items),
        "items": visible_items,
        "auto_score_effect": 0,
        "admin_decision_effect": False,
        "message": "Gelişim önerileri karne rehber alanında kontrollü gösterilir; otomatik puan veya idari karar üretmez.",
    }


def build_phase9_evaluator_guidance_context(items: Iterable[dict[str, Any]]) -> dict[str, Any]:
    context: list[dict[str, Any]] = []
    for item in items:
        normalized = normalize_phase9_guidance(item)
        if normalized.get("status") in {"rejected", "archived"}:
            continue
        context.append({
            "type": normalized["guidance_type_label"],
            "priority": normalized["priority_label"],
            "guidance": normalized.get("guidance_text") or normalized.get("development_need") or normalized.get("strong_side") or "",
            "follow_up_required": normalized.get("follow_up_required"),
            "score_effect": 0,
        })
    return {"ok": True, "count": len(context), "items": context, "auto_score_effect": 0, "admin_decision_effect": False}


def phase9_guidance_contract() -> dict[str, Any]:
    return {
        "version": BYS360_PERFORMANCE_COMPLETION_PHASE9_VERSION,
        "table": PHASE9_TABLE_NAME,
        "required_fields": list(REQUIRED_GUIDANCE_FIELDS),
        "guidance_types": dict(GUIDANCE_TYPE_LABELS),
        "priority_labels": dict(PRIORITY_LABELS),
        "status_labels": dict(STATUS_LABELS),
        "source_labels": dict(SOURCE_LABELS),
        "rules": [
            "Gelişim önerisi güçlü yön, gelişim ihtiyacı, eğitim önerisi, rehberlik veya takip notu olarak tutulabilir.",
            "Gelişim önerileri otomatik performans puanı üretmez ve nihai puanı kendiliğinden değiştirmez.",
            "Gelişim önerileri ceza, disiplin işlemi veya idari karar üretmez.",
            "Karneye yalnızca kontrollü/yayınlı rehber alan olarak yansıtılır.",
            "Personel yalnızca yayınlanmış kendi gelişim önerilerini görebilir.",
            "Yönetici görünürlüğü kendi yetkili organizasyon kapsamıyla sınırlıdır.",
        ],
        "markers": {
            "no_auto_score": BYS360_PERFORMANCE_COMPLETION_PHASE9_NO_AUTO_SCORE,
            "no_admin_decision": BYS360_PERFORMANCE_COMPLETION_PHASE9_NO_ADMIN_DECISION,
            "scorecard_guidance": BYS360_PERFORMANCE_COMPLETION_PHASE9_SCORECARD_GUIDANCE,
            "evaluator_context": BYS360_PERFORMANCE_COMPLETION_PHASE9_EVALUATOR_CONTEXT,
            "employee_published_only": BYS360_PERFORMANCE_COMPLETION_PHASE9_EMPLOYEE_PUBLISHED_ONLY,
            "scope_visibility": BYS360_PERFORMANCE_COMPLETION_PHASE9_SCOPE_VISIBILITY,
            "technical_language_clean": BYS360_PERFORMANCE_COMPLETION_PHASE9_TECHNICAL_LANGUAGE_CLEAN,
        },
    }


def phase9_schema_sql() -> str:
    return f"""
CREATE TABLE IF NOT EXISTS {PHASE9_TABLE_NAME} (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL,
    user_id INTEGER NULL,
    performance_period_id INTEGER NULL,
    period_id INTEGER NULL,
    scorecard_id INTEGER NULL,
    created_by_id INTEGER NULL,
    guidance_type VARCHAR(50) NOT NULL DEFAULT 'general_guidance',
    source VARCHAR(50) NOT NULL DEFAULT 'manual',
    priority VARCHAR(30) NOT NULL DEFAULT 'medium',
    strong_side TEXT NULL,
    development_need TEXT NULL,
    guidance_text TEXT NULL,
    suggested_action TEXT NULL,
    score_snapshot NUMERIC(5,2) NULL,
    status VARCHAR(40) NOT NULL DEFAULT 'active',
    follow_up_required BOOLEAN NOT NULL DEFAULT FALSE,
    include_in_scorecard BOOLEAN NOT NULL DEFAULT TRUE,
    employee_visible BOOLEAN NOT NULL DEFAULT FALSE,
    auto_score_effect NUMERIC(5,2) NOT NULL DEFAULT 0,
    admin_decision_effect BOOLEAN NOT NULL DEFAULT FALSE,
    guidance_date DATE NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""".strip()


def ensure_phase9_schema() -> dict[str, Any]:
    try:
        from sqlalchemy import text

        from app import db
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return {"ok": False, "error": str(exc), "table": PHASE9_TABLE_NAME}
    try:
        db.session.execute(text(phase9_schema_sql()))
        db.session.commit()
        return {"ok": True, "table": PHASE9_TABLE_NAME}
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        try:
            db.session.rollback()
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            logging.getLogger(__name__).exception("BYS360 suppressed exception captured in app/services/performance/phase9_development_guidance_center.py:435")
        return {"ok": False, "error": str(exc), "table": PHASE9_TABLE_NAME}


def seed_phase9_development_guidance_settings() -> dict[str, Any]:
    changed: list[str] = []
    schema = {"ok": False, "skipped": True}
    try:
        from app import db
        try:
            from app.models import ModuleSetting
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            from app.models.settings_models import ModuleSetting
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return {"ok": False, "error": str(exc), "settings": changed, "schema": schema}
    schema = ensure_phase9_schema()
    for module_key, setting_key, label, value_type, default_value, description in PHASE9_SETTING_ROWS:
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
            logging.getLogger(__name__).exception("BYS360 suppressed exception captured in app/services/performance/phase9_development_guidance_center.py:479")
        return {"ok": False, "error": str(exc), "settings": changed, "schema": schema}
