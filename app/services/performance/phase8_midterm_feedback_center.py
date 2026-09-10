"""BYS360 Performans Tamamlama Faz 8: Dönem içi notlar ve ara geri bildirim merkezi.

Bu merkez, dönem içinde oluşan olumlu/olumsuz gözlem, başarı, gelişim ihtiyacı
ve ara geri bildirim kayıtlarını performans sürecine güvenli biçimde bağlar.
Kritik sınır: Dönem içi notlar otomatik puan üretmez; yalnızca amire hatırlatma,
karneye kontrollü bilgi ve gelişim takibi desteği sağlar.
"""
from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

logger = logging.getLogger(__name__)

BYS360_PERFORMANCE_COMPLETION_PHASE8_MIDTERM_FEEDBACK_CENTER = True
BYS360_PERFORMANCE_COMPLETION_PHASE8_VERSION = "performance-completion-phase8-midterm-feedback-center-v1"
BYS360_PERFORMANCE_COMPLETION_PHASE8_NO_AUTO_SCORE = True
BYS360_PERFORMANCE_COMPLETION_PHASE8_EVALUATOR_REMINDER = True
BYS360_PERFORMANCE_COMPLETION_PHASE8_SCORECARD_CONTROLLED_VISIBILITY = True
BYS360_PERFORMANCE_COMPLETION_PHASE8_SCOPE_VISIBILITY = True
BYS360_PERFORMANCE_COMPLETION_PHASE8_NOTE_TYPES = True
BYS360_PERFORMANCE_COMPLETION_PHASE8_TECHNICAL_LANGUAGE_CLEAN = True

PHASE8_TABLE_NAME = "performance_midterm_notes"

NOTE_TYPE_LABELS = {
    "positive": "Olumlu Gözlem",
    "negative": "Gelişim İhtiyacı",
    "achievement": "Başarı Notu",
    "development": "Gelişim Önerisi",
    "warning": "Dikkat Gerektiren Durum",
    "general": "Genel Gözlem",
}

VISIBILITY_LABELS = {
    "private_manager": "Yalnızca Yetkili Amir/İK Görür",
    "evaluation_reminder": "Değerlendirme Sırasında Amire Hatırlatılır",
    "scorecard_summary": "Karne Özetinde Kontrollü Gösterilir",
    "employee_visible": "Personel Görünürlüğüne Açılmıştır",
}

STATUS_LABELS = {
    "draft": "Taslak Not",
    "active": "Aktif Not",
    "reminder_ready": "Değerlendirmede Hatırlatılacak",
    "scorecard_ready": "Karne Özetine Hazır",
    "published": "Personel Görünürlüğüne Açıldı",
    "archived": "Arşivlendi",
    "rejected": "İade Edildi",
}

PHASE8_SETTING_ROWS = [
    ("performance_phase8", "midterm_notes_enabled", "Dönem içi notlar aktif", "bool", "true", "Dönem boyunca gözlem, başarı ve gelişim notu tutulmasını sağlar."),
    ("performance_phase8", "interim_feedback_enabled", "Ara geri bildirim aktif", "bool", "true", "Puanlama dönemi gelmeden gelişim ve gözlem kaydı girilebilir."),
    ("performance_phase8", "evaluation_reminder_enabled", "Puanlamada amire hatırlatma aktif", "bool", "true", "Dönem içi notların değerlendirme ekranında amire özetlenmesini sağlar."),
    ("performance_phase8", "scorecard_summary_enabled", "Karne kontrollü özet alanı aktif", "bool", "true", "Yayın aşamasında uygun notların karne özetine alınmasını sağlar."),
    ("performance_phase8", "employee_visibility_requires_publish", "Personel görünürlüğü yayınla açılır", "bool", "true", "Personel dönem içi notları ancak yetkili yayın sonrası görür."),
    ("performance_phase8", "midterm_notes_no_auto_score", "Dönem içi not otomatik puan üretmez", "bool", "true", "Notlar amire karar desteği verir; nihai puanı otomatik değiştirmez."),
    ("performance_phase8", "scope_limited_midterm_notes", "Dönem içi not görünürlüğü kapsamla sınırlı", "bool", "true", "Yöneticiler yalnızca kendi kapsamındaki notları görebilir."),
]

REQUIRED_NOTE_FIELDS = ["employee_id", "period_id", "note_type", "note_text", "event_date"]
TECHNICAL_WORDS = ["workflow", "endpoint", "debug", "traceback", "exception", "phase sync", "authorized_scope", "raw", "json"]

@dataclass(frozen=True)
class Phase8NoteValidation:
    ok: bool
    errors: list[str]
    warnings: list[str]
    normalized: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "errors": list(self.errors), "warnings": list(self.warnings), "normalized": dict(self.normalized)}

@dataclass(frozen=True)
class Phase8VisibilityDecision:
    can_view: bool
    scope: str
    reason: str
    show_person_detail: bool
    can_create: bool
    can_publish: bool
    can_remind_evaluator: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "can_view": self.can_view,
            "scope": self.scope,
            "reason": self.reason,
            "show_person_detail": self.show_person_detail,
            "can_create": self.can_create,
            "can_publish": self.can_publish,
            "can_remind_evaluator": self.can_remind_evaluator,
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
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/phase8_midterm_feedback_center.py | line=122")
        return default


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
            logger.exception("BYS360 V6C guarded exception | file=app/services/performance/phase8_midterm_feedback_center.py | line=139")
            continue
    return text


def phase8_note_type_label(note_type: Any) -> str:
    text = _as_text(note_type).lower()
    return NOTE_TYPE_LABELS.get(text, _as_text(note_type) or "Genel Gözlem")


def phase8_status_label(status: Any) -> str:
    text = _as_text(status).lower()
    return STATUS_LABELS.get(text, _as_text(status) or "Not Durumu Belirtilmedi")


def phase8_visibility_label(visibility: Any) -> str:
    text = _as_text(visibility).lower()
    return VISIBILITY_LABELS.get(text, _as_text(visibility) or "Görünürlük Belirtilmedi")


def phase8_clean_text(value: Any) -> str:
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
    }
    for old, new in replacements.items():
        text = text.replace(old, new).replace(old.upper(), new).replace(old.title(), new)
    return text


def phase8_contains_technical_language(value: Any) -> bool:
    text = _as_text(value).lower()
    return any(word in text for word in TECHNICAL_WORDS)


def normalize_phase8_midterm_note(row: dict[str, Any]) -> dict[str, Any]:
    note_type = _as_text(row.get("note_type") or row.get("tur") or row.get("not_turu") or "general").lower()
    if note_type not in NOTE_TYPE_LABELS:
        note_type = "general"
    include_in_scorecard = _as_bool(row.get("include_in_scorecard"), False)
    remind_evaluator = _as_bool(row.get("remind_evaluator"), True)
    employee_visible = _as_bool(row.get("employee_visible"), False)
    status = _as_text(row.get("status") or row.get("durum") or "active").lower()
    visibility = _as_text(row.get("visibility") or row.get("gorunurluk") or "private_manager").lower()
    if include_in_scorecard and visibility == "private_manager":
        visibility = "scorecard_summary"
    if remind_evaluator and visibility == "private_manager":
        visibility = "evaluation_reminder"
    if employee_visible:
        visibility = "employee_visible"
        status = "published"
    return {
        "employee_id": _as_int(row.get("employee_id") or row.get("user_id") or row.get("personel_id")),
        "period_id": _as_int(row.get("period_id") or row.get("performance_period_id") or row.get("donem_id")),
        "created_by_id": _as_int(row.get("created_by_id") or row.get("creator_id") or row.get("olusturan_id")),
        "note_type": note_type,
        "note_type_label": phase8_note_type_label(note_type),
        "title": phase8_clean_text(row.get("title") or row.get("baslik") or phase8_note_type_label(note_type)),
        "note_text": phase8_clean_text(row.get("note_text") or row.get("note") or row.get("aciklama") or row.get("not") or ""),
        "event_date": _as_date_text(row.get("event_date") or row.get("date") or row.get("tarih")),
        "visibility": visibility,
        "visibility_label": phase8_visibility_label(visibility),
        "status": status,
        "status_label": phase8_status_label(status),
        "remind_evaluator": remind_evaluator,
        "include_in_scorecard": include_in_scorecard,
        "employee_visible": employee_visible,
        "auto_score_effect": 0,
    }


def validate_phase8_midterm_note(row: dict[str, Any]) -> Phase8NoteValidation:
    normalized = normalize_phase8_midterm_note(row)
    errors: list[str] = []
    warnings: list[str] = []
    if not normalized["employee_id"]:
        errors.append("Personel bilgisi zorunludur.")
    if not normalized["period_id"]:
        errors.append("Performans dönemi zorunludur.")
    if normalized["note_type"] not in NOTE_TYPE_LABELS:
        errors.append("Not türü geçerli değildir.")
    if not normalized["note_text"]:
        errors.append("Dönem içi not açıklaması zorunludur.")
    if not normalized["event_date"]:
        warnings.append("Olay/gözlem tarihi boş; kayıt tarihi kullanılabilir.")
    if normalized["auto_score_effect"] != 0:
        errors.append("Dönem içi notlar otomatik puan etkisi üretemez.")
    if phase8_contains_technical_language(normalized["note_text"]):
        warnings.append("Not metninde teknik ifade temizliği önerilir.")
    return Phase8NoteValidation(ok=not errors, errors=errors, warnings=warnings, normalized=normalized)


def resolve_phase8_midterm_visibility(
    *,
    role: str | None = None,
    current_user_id: Any = None,
    employee_id: Any = None,
    created_by_id: Any = None,
    same_scope: bool = False,
    is_admin: bool = False,
    is_president: bool = False,
    is_hr: bool = False,
    is_group_president: bool = False,
    is_coordinator: bool = False,
    is_evaluator: bool = False,
    note_status: str | None = None,
    action: str = "view",
) -> Phase8VisibilityDecision:
    role_text = _as_text(role).lower()
    status = _as_text(note_status).lower()
    admin_like = is_admin or is_president or is_hr or role_text in {"admin", "sistem yöneticisi", "sistem_yoneticisi", "başkan", "baskan", "ik", "insan kaynakları", "performans yetkilisi", "personel yetkilisi"}
    manager_like = is_group_president or is_coordinator or is_evaluator or role_text in {"grup başkanı", "grup baskani", "koordinatör", "koordinator", "amir", "değerlendirici", "degerlendirici"}
    own_employee = current_user_id is not None and employee_id is not None and str(current_user_id) == str(employee_id)
    creator = current_user_id is not None and created_by_id is not None and str(current_user_id) == str(created_by_id)
    wants_create = action in {"create", "edit", "delete", "manual_entry"}
    wants_publish = action in {"publish", "scorecard_publish"}

    if admin_like:
        return Phase8VisibilityDecision(True, "genel", "Genel dönem içi not yetkisi", True, True, True, True)
    if wants_publish:
        return Phase8VisibilityDecision(False, "yetkisiz", "Dönem içi not yayın yetkisi Admin/İK/Performans Yetkilisi kapsamındadır", False, False, False, False)
    if manager_like and same_scope:
        return Phase8VisibilityDecision(True, "yetkili_kapsam", "Yalnızca yetkili organizasyon kapsamı", True, True, False, True)
    if creator and not wants_publish:
        return Phase8VisibilityDecision(True, "olusturdugu_not", "Kullanıcı kendi oluşturduğu notu görebilir", True, True, False, True)
    if own_employee and status == "published" and not wants_create:
        return Phase8VisibilityDecision(True, "kendi_yayinlanmis_notu", "Personel yalnızca yayınlanmış kendi dönem içi notunu görür", False, False, False, False)
    return Phase8VisibilityDecision(False, "yetkisiz", "Bu dönem içi not kaydını görme yetkiniz bulunmamaktadır", False, False, False, False)


def filter_phase8_midterm_notes(
    notes: Iterable[dict[str, Any]],
    *,
    current_user_id: Any = None,
    role: str | None = None,
    is_admin: bool = False,
    is_president: bool = False,
    is_hr: bool = False,
    allowed_employee_ids: set[Any] | None = None,
) -> list[dict[str, Any]]:
    allowed = {str(x) for x in (allowed_employee_ids or set())}
    output: list[dict[str, Any]] = []
    for note in notes:
        normalized = normalize_phase8_midterm_note(note)
        employee_id = normalized.get("employee_id")
        same_scope = bool(employee_id is not None and str(employee_id) in allowed)
        decision = resolve_phase8_midterm_visibility(
            role=role,
            current_user_id=current_user_id,
            employee_id=employee_id,
            created_by_id=normalized.get("created_by_id"),
            same_scope=same_scope,
            is_admin=is_admin,
            is_president=is_president,
            is_hr=is_hr,
            note_status=normalized.get("status"),
        )
        if not decision.can_view:
            continue
        safe = dict(normalized)
        if not decision.show_person_detail:
            safe.pop("created_by_id", None)
        safe["visibility_decision"] = decision.as_dict()
        output.append(safe)
    return output


def build_phase8_evaluator_reminders(notes: Iterable[dict[str, Any]], *, max_items: int = 5) -> dict[str, Any]:
    reminders: list[dict[str, Any]] = []
    for note in notes:
        normalized = normalize_phase8_midterm_note(note)
        if not normalized.get("remind_evaluator"):
            continue
        reminders.append({
            "title": normalized["title"],
            "note_type": normalized["note_type_label"],
            "event_date": normalized["event_date"],
            "summary": normalized["note_text"][:240],
            "score_effect": 0,
            "warning": "Bu kayıt otomatik puan üretmez; yalnızca değerlendirme sırasında hatırlatma sağlar.",
        })
    return {
        "ok": True,
        "count": len(reminders),
        "items": reminders[:max_items],
        "message": "Dönem içi notlar amire hatırlatma olarak sunulur; nihai puanı otomatik değiştirmez.",
    }


def build_phase8_scorecard_summary(notes: Iterable[dict[str, Any]], *, include_private: bool = False) -> dict[str, Any]:
    grouped: dict[str, int] = {label: 0 for label in NOTE_TYPE_LABELS.values()}
    visible_items: list[dict[str, Any]] = []
    for note in notes:
        normalized = normalize_phase8_midterm_note(note)
        if not include_private and not (normalized.get("include_in_scorecard") or normalized.get("employee_visible")):
            continue
        label = normalized["note_type_label"]
        grouped[label] = grouped.get(label, 0) + 1
        visible_items.append({
            "title": normalized["title"],
            "note_type": label,
            "event_date": normalized["event_date"],
            "summary": normalized["note_text"][:220],
            "status": normalized["status_label"],
        })
    return {
        "ok": True,
        "summary_counts": grouped,
        "visible_count": len(visible_items),
        "items": visible_items,
        "auto_score_effect": 0,
        "message": "Karne özeti kontrollü görünürlükle hazırlanır; dönem içi notlar puanı otomatik değiştirmez.",
    }


def phase8_midterm_contract() -> dict[str, Any]:
    return {
        "version": BYS360_PERFORMANCE_COMPLETION_PHASE8_VERSION,
        "table": PHASE8_TABLE_NAME,
        "required_fields": list(REQUIRED_NOTE_FIELDS),
        "note_types": dict(NOTE_TYPE_LABELS),
        "visibility_labels": dict(VISIBILITY_LABELS),
        "status_labels": dict(STATUS_LABELS),
        "rules": [
            "Dönem içi notlar olumlu gözlem, gelişim ihtiyacı, başarı, gelişim önerisi ve genel gözlem olarak tutulabilir.",
            "Dönem içi notlar otomatik performans puanı üretmez ve nihai puanı kendiliğinden değiştirmez.",
            "Puanlama ekranında yetkili amire hatırlatma olarak gösterilebilir.",
            "Karneye yalnızca kontrollü görünürlük/yayın kuralıyla özet olarak yansıtılabilir.",
            "Personel yalnızca yayınlanmış kendi dönem içi notlarını görebilir.",
            "Yönetici görünürlüğü kendi yetkili organizasyon kapsamıyla sınırlıdır.",
        ],
        "markers": {
            "no_auto_score": BYS360_PERFORMANCE_COMPLETION_PHASE8_NO_AUTO_SCORE,
            "evaluator_reminder": BYS360_PERFORMANCE_COMPLETION_PHASE8_EVALUATOR_REMINDER,
            "scorecard_controlled_visibility": BYS360_PERFORMANCE_COMPLETION_PHASE8_SCORECARD_CONTROLLED_VISIBILITY,
            "scope_visibility": BYS360_PERFORMANCE_COMPLETION_PHASE8_SCOPE_VISIBILITY,
            "note_types": BYS360_PERFORMANCE_COMPLETION_PHASE8_NOTE_TYPES,
            "technical_language_clean": BYS360_PERFORMANCE_COMPLETION_PHASE8_TECHNICAL_LANGUAGE_CLEAN,
        },
    }


# BYS360 DEFECT AR: ensure_phase8_schema()/seed_phase8_midterm_feedback_settings()
# (ve phase8_schema_sql() DDL ureticisi) kaldirildi -- repo genelinde
# (app/, tests/, scripts/) hicbir gercek cagirani yoktu. Canli "Faz 8
# Midterm Feedback" ozelligi app/services/performance/midterm_feedback_service.py
# uzerinden calisir; bu dosyanin geri kalani degismedi.
