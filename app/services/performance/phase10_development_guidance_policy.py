"""
BYS360 Performans Tamamlama Faz 10
Dönem İçi Notlar + Gelişim Önerisi Bağı Politika Merkezi

Amaç:
- Dönem içi notlar karne altındaki gelişim önerisi alanına güvenli şekilde bağlanabilsin.
- Gelişim önerisi teknik kod/dil içermeden kurumsal Türkçe ile gösterilsin.
- Personel, gelişim önerisini yalnızca karne yayınlandıktan ve gerekli onaylar tamamlandıktan sonra görsün.
- Grup Başkanı/Yetkili yönetici onay akışı desteklensin.
- Dönem içi not detay metni kaybolduğunda kullanıcıya teknik olmayan boş durum mesajı gösterilsin.
"""
from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


PHASE10_POLICY_MARKER = "BYS360_PERFORMANCE_COMPLETION_PHASE10_INTERIM_GUIDANCE_POLICY"

GUIDANCE_STATUS_DRAFT = "draft"
GUIDANCE_STATUS_PENDING_APPROVAL = "pending_approval"
GUIDANCE_STATUS_APPROVED = "approved"
GUIDANCE_STATUS_PUBLISHED = "published"
GUIDANCE_STATUS_RETURNED = "returned"

GUIDANCE_STATUS_LABELS = {
    GUIDANCE_STATUS_DRAFT: "Taslak",
    GUIDANCE_STATUS_PENDING_APPROVAL: "Grup Başkanı Onayı Bekliyor",
    GUIDANCE_STATUS_APPROVED: "Yayın Öncesi Kontrole Hazır",
    GUIDANCE_STATUS_PUBLISHED: "Personele Yayınlandı",
    GUIDANCE_STATUS_RETURNED: "Düzenleme İçin İade Edildi",
}

TECHNICAL_REPLACEMENTS = {
    "draft": "Taslak",
    "authorized_scope": "Yetkili Kapsam",
    "scorecard_pending": "Karne Yayın Süreci Bekliyor",
    "president_pending": "Başkan/Üst Onay Bekliyor",
    "blocked_president_pending": "Başkan/Üst Onay Yayın Kilidi",
    "phase": "süreç",
    "sync": "süreç güncellemesi",
    "recommendation_text": "gelişim önerisi",
    "interim_note": "dönem içi not",
    "p4_p8_dependency": "önceki süreç bağı",
}

HIDDEN_TECHNICAL_TERMS = [
    "authorized_scope",
    "scorecard_pending",
    "president_pending",
    "blocked_president_pending",
    "recommendation_text",
    "interim_note",
    "p4_p8_dependency",
    "phase10",
    "Aşama 10",
    "Asama 10",
]


@dataclass(frozen=True)
class GuidanceVisibilityDecision:
    visible_to_personnel: bool
    editable_by_manager: bool
    approval_required: bool
    approval_label: str
    publish_blocked: bool
    label: str
    reason: str


@dataclass(frozen=True)
class GuidanceRecordNormalized:
    employee_id: int | None
    period_id: int | None
    scorecard_id: int | None
    interim_note_id: int | None
    guidance_text: str
    source_summary: str
    status: str
    status_label: str
    valid: bool
    errors: tuple[str, ...]


def _to_int(value: Any, default: int | None = None) -> int | None:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "evet", "on", "aktif", "enabled"}


def normalize_guidance_status(value: Any) -> str:
    raw = str(value or GUIDANCE_STATUS_DRAFT).strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "taslak": GUIDANCE_STATUS_DRAFT,
        "draft": GUIDANCE_STATUS_DRAFT,
        "pending": GUIDANCE_STATUS_PENDING_APPROVAL,
        "pending_approval": GUIDANCE_STATUS_PENDING_APPROVAL,
        "approval": GUIDANCE_STATUS_PENDING_APPROVAL,
        "approved": GUIDANCE_STATUS_APPROVED,
        "onaylandi": GUIDANCE_STATUS_APPROVED,
        "onaylandı": GUIDANCE_STATUS_APPROVED,
        "published": GUIDANCE_STATUS_PUBLISHED,
        "yayinlandi": GUIDANCE_STATUS_PUBLISHED,
        "yayınlandı": GUIDANCE_STATUS_PUBLISHED,
        "returned": GUIDANCE_STATUS_RETURNED,
        "iade": GUIDANCE_STATUS_RETURNED,
    }
    return aliases.get(raw, GUIDANCE_STATUS_DRAFT)


def guidance_status_label(status: Any) -> str:
    normalized = normalize_guidance_status(status)
    return GUIDANCE_STATUS_LABELS.get(normalized, "Gelişim Önerisi Durumu")


def sanitize_guidance_text(text: Any) -> str:
    value = "" if text is None else str(text)
    for old, new in TECHNICAL_REPLACEMENTS.items():
        value = value.replace(old, new)
    return " ".join(value.split())


def contains_visible_technical_language(text: Any) -> bool:
    value = "" if text is None else str(text)
    lower = value.lower()
    return any(term.lower() in lower for term in HIDDEN_TECHNICAL_TERMS)


def empty_interim_note_message() -> str:
    return "Bu kayıt için dönem içi not detayı henüz girilmemiş. Detay eklendiğinde gelişim önerisiyle birlikte gösterilecektir."


def empty_guidance_message() -> str:
    return "Bu karne için gelişim önerisi henüz oluşturulmamış. Yetkili yönetici öneri eklediğinde bu alanda gösterilecektir."


def normalize_guidance_record(row: Mapping[str, Any]) -> GuidanceRecordNormalized:
    errors: list[str] = []

    employee_id = _to_int(row.get("employee_id") or row.get("personel_id") or row.get("user_id"))
    period_id = _to_int(row.get("period_id") or row.get("donem_id"))
    scorecard_id = _to_int(row.get("scorecard_id") or row.get("karne_id"))
    interim_note_id = _to_int(row.get("interim_note_id") or row.get("note_id") or row.get("donem_ici_not_id"))

    if employee_id is None:
        errors.append("Personel bilgisi eksik.")
    if period_id is None:
        errors.append("Dönem bilgisi eksik.")

    raw_guidance = row.get("guidance_text") or row.get("recommendation") or row.get("recommendation_text") or row.get("gelisim_onerisi")
    guidance_text = sanitize_guidance_text(raw_guidance)
    if not guidance_text:
        errors.append("Gelişim önerisi metni eksik.")

    source_summary = sanitize_guidance_text(row.get("source_summary") or row.get("note_summary") or row.get("interim_note_summary") or "")
    status = normalize_guidance_status(row.get("status"))

    return GuidanceRecordNormalized(
        employee_id=employee_id,
        period_id=period_id,
        scorecard_id=scorecard_id,
        interim_note_id=interim_note_id,
        guidance_text=guidance_text,
        source_summary=source_summary,
        status=status,
        status_label=guidance_status_label(status),
        valid=not errors,
        errors=tuple(errors),
    )


def build_guidance_from_interim_note(
    note: Mapping[str, Any],
    *,
    default_status: str = GUIDANCE_STATUS_DRAFT,
) -> GuidanceRecordNormalized:
    note_text = note.get("detail") or note.get("note_text") or note.get("description") or note.get("aciklama") or ""
    recommendation = note.get("guidance_text") or note.get("recommendation") or note.get("recommendation_text")
    if not recommendation:
        recommendation = f"Dönem içi not dikkate alınarak gelişim alanı planlanmalıdır: {note_text}"

    return normalize_guidance_record(
        {
            "employee_id": note.get("employee_id") or note.get("personel_id"),
            "period_id": note.get("period_id") or note.get("donem_id"),
            "scorecard_id": note.get("scorecard_id") or note.get("karne_id"),
            "interim_note_id": note.get("id") or note.get("note_id"),
            "guidance_text": recommendation,
            "source_summary": note_text,
            "status": default_status,
        }
    )


def resolve_guidance_visibility(
    *,
    scorecard_published: Any = False,
    guidance_status: Any = GUIDANCE_STATUS_DRAFT,
    group_head_approved: Any = False,
    low_score_publish_blocked: Any = False,
    viewer_is_personnel: Any = False,
    settings: Mapping[str, Any] | None = None,
) -> GuidanceVisibilityDecision:
    settings = settings or {}
    approval_required = _bool(settings.get("performance.phase10.group_head_approval_required", True), True)
    personnel_visible_only_after_publish = _bool(settings.get("performance.phase10.personnel_visible_after_scorecard_publish", True), True)

    status = normalize_guidance_status(guidance_status)
    published = _bool(scorecard_published, False)
    approved = _bool(group_head_approved, False) or status in {GUIDANCE_STATUS_APPROVED, GUIDANCE_STATUS_PUBLISHED}
    low_blocked = _bool(low_score_publish_blocked, False)
    is_personnel = _bool(viewer_is_personnel, False)

    if low_blocked:
        return GuidanceVisibilityDecision(
            visible_to_personnel=False,
            editable_by_manager=True,
            approval_required=approval_required,
            approval_label="Yayın Kilidi Aktif",
            publish_blocked=True,
            label="Gelişim Önerisi Yayın Kilidinde",
            reason="Karne yayın kilidi kalkmadan gelişim önerisi personele gösterilemez.",
        )

    if approval_required and not approved:
        return GuidanceVisibilityDecision(
            visible_to_personnel=False,
            editable_by_manager=True,
            approval_required=True,
            approval_label=GUIDANCE_STATUS_LABELS[GUIDANCE_STATUS_PENDING_APPROVAL],
            publish_blocked=True,
            label="Grup Başkanı Onayı Bekliyor",
            reason="Gelişim önerisi Grup Başkanı onayı tamamlanmadan personele açılmaz.",
        )

    if personnel_visible_only_after_publish and not published:
        return GuidanceVisibilityDecision(
            visible_to_personnel=False,
            editable_by_manager=True,
            approval_required=approval_required,
            approval_label="Onay Tamam",
            publish_blocked=True,
            label="Karne Yayını Bekleniyor",
            reason="Karne yayınlanmadan gelişim önerisi personele gösterilmez.",
        )

    return GuidanceVisibilityDecision(
        visible_to_personnel=True,
        editable_by_manager=not is_personnel,
        approval_required=approval_required,
        approval_label="Yayınlanabilir",
        publish_blocked=False,
        label="Personele Gösterilebilir",
        reason="Gerekli onaylar ve karne yayın koşulları tamamlanmıştır.",
    )


def filter_guidance_for_personnel(rows: Iterable[Mapping[str, Any]], *, employee_id: Any) -> list[dict[str, Any]]:
    target = _to_int(employee_id)
    result: list[dict[str, Any]] = []
    for row in rows or []:
        item = dict(row)
        row_employee = _to_int(item.get("employee_id") or item.get("personel_id") or item.get("user_id"))
        if target is not None and row_employee == target:
            item["guidance_text"] = sanitize_guidance_text(item.get("guidance_text") or item.get("recommendation") or "")
            item["status_label"] = guidance_status_label(item.get("status"))
            result.append(item)
    return result


def build_scorecard_guidance_payload(
    guidance_rows: Iterable[Mapping[str, Any]],
    *,
    employee_id: Any,
    scorecard_published: Any,
    group_head_approved: Any,
    low_score_publish_blocked: Any = False,
) -> dict[str, Any]:
    rows = filter_guidance_for_personnel(guidance_rows, employee_id=employee_id)
    visibility = resolve_guidance_visibility(
        scorecard_published=scorecard_published,
        group_head_approved=group_head_approved,
        low_score_publish_blocked=low_score_publish_blocked,
        viewer_is_personnel=True,
    )

    if not visibility.visible_to_personnel:
        return {
            "visible": False,
            "label": visibility.label,
            "message": visibility.reason,
            "items": [],
        }

    return {
        "visible": True,
        "label": "Gelişim Önerileri",
        "message": empty_guidance_message() if not rows else "",
        "items": rows,
    }


def phase10_guidance_contract() -> dict[str, Any]:
    return {
        "interim_notes_to_guidance_link": True,
        "guidance_write_area_required": True,
        "group_head_approval_required": True,
        "personnel_visible_after_scorecard_publish": True,
        "low_score_publish_lock_respected": True,
        "technical_language_hidden": True,
        "empty_note_message_corporate": True,
        "scorecard_guidance_payload": True,
        "phase_marker": PHASE10_POLICY_MARKER,
    }

# BYS360_PERFORMANCE_COMPLETION_PHASE10_INTERIM_GUIDANCE_BOUND
# Dönem içi not + gelişim önerisi bağı phase10_development_guidance_policy sözleşmesini kullanır.
