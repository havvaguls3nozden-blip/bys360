from __future__ import annotations

from app.core.datetime_utils import utc_now

import secrets
from collections import defaultdict
from copy import deepcopy
from datetime import date, datetime, timedelta
from typing import Any

from flask import current_app, has_app_context
from sqlalchemy import func

from app.extensions import db
from app.models import (
    FeedbackActionPlan,
    FeedbackAnswer,
    FeedbackCampaign,
    FeedbackCampaignAssignment,
    FeedbackMeeting,
    FeedbackPulseEntry,
    FeedbackQuestion,
    FeedbackQuestionOption,
    FeedbackRequest,
    FeedbackSubmission,
    MailLog,
    PerformanceEvaluation,
    User,
)
from app.services.bys360_notification_bridge import (
    notify_feedback_action_plan_created,
    notify_feedback_action_plan_status_changed,
    notify_feedback_campaign_created,
    notify_feedback_campaign_status_changed,
    notify_feedback_submission_received,
)
from app.services.shared_cache_store import delete_prefix as _shared_cache_delete_prefix
from app.services.shared_cache_store import get_json as _shared_cache_get_json
from app.services.shared_cache_store import set_json as _shared_cache_set_json

"""BYS360 feedback service.

Bu dosya iki farkli geri bildirim katmanini ayni yerde yasar halde tutar:
1) Performans modülündeki klasik geri bildirim talebi / randevu akisi
2) Kurumsal Geri Bildirim modülündeki kampanya / nabiz / aksiyon akisi

Faz paketleri kurulduktan sonra eski import yüzeyini korumak icin
uyumluluk fonksiyonlari bilerek ayni dosyada tutuldu.
"""

# ---------------------------------------------------------------------------
# Legacy performance feedback request helpers
# ---------------------------------------------------------------------------

OPEN_FEEDBACK_STATUSES = {
    "bekliyor",
    "beklemede",
    "incelendi",
    "randevulandi",
    "randevu_ertelendi",
    "randevu_iptal",
    "gorusme_tamamlandi",
    "cevaplandi",
}


def get_feedback_evaluation(period_id: int, employee_id: int):
    return (
        PerformanceEvaluation.query
        .filter_by(period_id=period_id, employee_id=employee_id)
        .first()
    )


def get_open_feedback_request(period_id: int, employee_id: int):
    return (
        FeedbackRequest.query
        .filter(
            FeedbackRequest.period_id == period_id,
            FeedbackRequest.employee_id == employee_id,
            FeedbackRequest.status.in_(tuple(OPEN_FEEDBACK_STATUSES)),
        )
        .order_by(FeedbackRequest.requested_at.desc(), FeedbackRequest.id.desc())
        .first()
    )


def get_feedback_meeting(feedback_request_id: int):
    return FeedbackMeeting.query.filter_by(feedback_request_id=feedback_request_id).first()


def can_create_feedback_request(period: Any, evaluation: Any) -> tuple[bool, str | None]:
    if period is None:
        return False, "Dönem bulunamadı."
    deadline = getattr(period, "feedback_request_deadline", None)
    if deadline and deadline < utc_now().date():
        return False, "Geri bildirim talep süresi sona ermiş."
    if evaluation is None:
        return False, "Bu dönem için değerlendirmeniz bulunamadı."
    if getattr(evaluation, "evaluation_exempted", False):
        return False, "Muaf bırakılmış değerlendirme için geri bildirim talebi açılamaz."
    if hasattr(evaluation, "feedback_request_allowed") and not bool(getattr(evaluation, "feedback_request_allowed", True)):
        return False, "Bu değerlendirme için geri bildirim talebi kapalı."

    is_employee_visible = bool(
        getattr(evaluation, "is_published_to_employee", False)
        and getattr(evaluation, "published_to_employee_at", None)
    ) or bool(getattr(evaluation, "is_published_to_employee", False))
    if not is_employee_visible:
        return False, "Geri bildirim talebi yalnızca personele açılmış sonuçlar için oluşturulabilir."

    return True, None


def persist_feedback_response(req: FeedbackRequest, response_text: str, actor_user_id: int | None, recipient_email: str | None = None):
    cleaned = (response_text or "").strip()
    if not cleaned:
        return None
    log = (
        MailLog.query
        .filter_by(related_feedback_request_id=req.id, mail_type="feedback_response")
        .order_by(MailLog.sent_at.desc(), MailLog.id.desc())
        .first()
    )
    if not log:
        log = MailLog(
            mail_type="feedback_response",
            related_period_id=req.period_id,
            related_user_id=req.employee_id,
            related_feedback_request_id=req.id,
            recipient_email=(recipient_email or "").strip() or "-",
        )
        db.session.add(log)
    log.subject = "BYS360 Geri Bildirim Talebinize Yanıt"
    log.body_preview = cleaned
    log.sent_by_id = actor_user_id
    log.sent_at = utc_now()
    return log


def get_feedback_response_text(req: FeedbackRequest) -> str:
    text = getattr(req, "response", None)
    return (text or "").strip()


def count_feedback_statuses():
    statuses = [
        "bekliyor",
        "beklemede",
        "incelendi",
        "randevulandi",
        "gorusme_tamamlandi",
        "cevaplandi",
        "kapatildi",
        "randevu_ertelendi",
        "randevu_iptal",
    ]
    return {status: FeedbackRequest.query.filter_by(status=status).count() for status in statuses}


# ---------------------------------------------------------------------------
# Corporate feedback campaign / pulse / action helpers
# ---------------------------------------------------------------------------

MANAGER_ROLES = {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"}

MOOD_CHOICES = {
    1: "Desteğe ihtiyacım var",
    2: "Zorlanıyorum",
    3: "Nötr",
    4: "İyi",
    5: "Çok iyi",
}

CAMPAIGN_TYPE_LABELS = {
    "survey": "Anket",
    "pulse": "Nabız",
    "training_feedback": "Eğitim Geri Bildirimi",
    "survey_with_pulse": "Anket + Nabız",
    "training_feedback_with_pulse": "Eğitim + Nabız",
}


def is_manager_family(user) -> bool:
    return (getattr(user, "role", "") or "").strip().lower() in MANAGER_ROLES


def parse_datetime_local(value: str | None):
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


def get_campaign_type_label(campaign_or_type: FeedbackCampaign | str | None) -> str:
    if isinstance(campaign_or_type, str):
        raw = campaign_or_type
    else:
        raw = getattr(campaign_or_type, "campaign_type", "")
    key = (raw or "survey").strip().lower()
    return CAMPAIGN_TYPE_LABELS.get(key, key.replace("_", " ").title())


def campaign_includes_pulse(campaign: FeedbackCampaign | None) -> bool:
    key = (getattr(campaign, "campaign_type", "") or "").strip().lower()
    return key in {"pulse", "survey_with_pulse", "training_feedback_with_pulse"} or key.endswith("_with_pulse")


def campaign_is_open(campaign: FeedbackCampaign) -> bool:
    now = utc_now()
    if not campaign or not campaign.is_active:
        return False
    if (campaign.status or "").lower() not in {"published", "active"}:
        return False
    if campaign.start_at and campaign.start_at > now:
        return False
    return not (campaign.end_at and campaign.end_at < now)


def _matches_assignment(user, assignment: FeedbackCampaignAssignment) -> bool:
    target_type = (assignment.target_type or "all").strip().lower()
    target_value = (assignment.target_value or "").strip()
    if target_type == "all":
        return True
    if target_type == "user":
        return str(getattr(user, "id", "")) == target_value or str(getattr(user, "sicil_no", "")) == target_value
    if target_type == "role":
        return (getattr(user, "role", "") or "").strip().lower() == target_value.lower()
    if target_type == "unit":
        unit_candidates = {
            str(getattr(user, "organization_unit_id", "") or ""),
            (getattr(user, "birim", "") or "").strip().lower(),
        }
        return target_value.lower() in {value.lower() for value in unit_candidates if value}
    return False


def user_can_see_campaign(user, campaign: FeedbackCampaign) -> bool:
    assignments = campaign.assignments.all()
    if not assignments:
        return True
    return any(_matches_assignment(user, assignment) for assignment in assignments)


def has_user_submitted_campaign(user, campaign: FeedbackCampaign) -> bool:
    if campaign.is_anonymous:
        return False
    return (
        FeedbackSubmission.query
        .filter_by(campaign_id=campaign.id, user_id=user.id, is_completed=True)
        .first()
        is not None
    )


def list_visible_campaigns_for_user(user):
    campaigns = (
        FeedbackCampaign.query
        .filter(FeedbackCampaign.is_active.is_(True))
        .order_by(FeedbackCampaign.created_at.desc(), FeedbackCampaign.id.desc())
        .all()
    )
    return [
        campaign for campaign in campaigns
        if campaign_is_open(campaign) and user_can_see_campaign(user, campaign)
    ]


def list_manageable_campaigns():
    return (
        FeedbackCampaign.query
        .order_by(FeedbackCampaign.created_at.desc(), FeedbackCampaign.id.desc())
        .all()
    )


def get_campaign_or_404(campaign_id: int):
    return FeedbackCampaign.query.get_or_404(campaign_id)


def get_today_pulse_entry(user):
    return FeedbackPulseEntry.query.filter_by(user_id=user.id, entry_date=date.today()).first()


def get_pulse_history(user, days: int = 30):
    safe_days = max(1, min(int(days or 30), 120))
    start_date = date.today() - timedelta(days=safe_days - 1)
    return (
        FeedbackPulseEntry.query
        .filter(FeedbackPulseEntry.user_id == user.id)
        .filter(FeedbackPulseEntry.entry_date >= start_date)
        .order_by(FeedbackPulseEntry.entry_date.desc(), FeedbackPulseEntry.id.desc())
        .all()
    )


def save_pulse_entry(*, user, mood_value: int, short_note: str = "", is_anonymous: bool = False):
    mood_value = max(1, min(5, int(mood_value)))
    entry = get_today_pulse_entry(user)
    if not entry:
        entry = FeedbackPulseEntry(user_id=user.id, organization_unit_id=user.organization_unit_id, entry_date=date.today())
        db.session.add(entry)
    entry.mood_value = mood_value
    entry.mood_label = MOOD_CHOICES.get(mood_value, "Nötr")
    entry.short_note = (short_note or "").strip()[:1000] or None
    entry.is_anonymous = bool(is_anonymous)
    db.session.commit()
    unit_id = getattr(user, "organization_unit_id", None)
    _clear_pulse_cache_for_unit(unit_id)
    _enqueue_pulse_analytics_refresh(unit_id, days=30)
    return entry

# ---------------------------------------------------------------------------
# Pulse analytics privacy/performance helpers
# ---------------------------------------------------------------------------

_PULSE_ANALYTICS_CACHE_KEY = "feedback_pulse_analytics_cache"
_PULSE_ANALYTICS_CACHE_TTL_SECONDS = 60


def _pulse_cache_enabled() -> bool:
    if not has_app_context():
        return False
    return bool(current_app.config.get("FEEDBACK_PULSE_ANALYTICS_CACHE_ENABLED", True))


def _pulse_cache_key(*, unit_id: int | None, days: int, minimum_group_size: int) -> str:
    today_key = date.today().isoformat()
    return f"unit:{unit_id}|days:{int(days)}|min:{int(minimum_group_size or 5)}|date:{today_key}"


def _legacy_local_cache_get(cache_key: str):
    cache = current_app.extensions.setdefault(_PULSE_ANALYTICS_CACHE_KEY, {})
    entry = cache.get(cache_key)
    if not entry:
        return None
    expires_at, payload = entry
    if expires_at <= utc_now().timestamp():
        cache.pop(cache_key, None)
        return None
    return deepcopy(payload)


def _legacy_local_cache_set(cache_key: str, payload: dict[str, Any], ttl: int) -> None:
    cache = current_app.extensions.setdefault(_PULSE_ANALYTICS_CACHE_KEY, {})
    cache[cache_key] = (utc_now().timestamp() + max(5, int(ttl or 60)), deepcopy(payload))


def _get_pulse_cache(cache_key: str):
    if not _pulse_cache_enabled():
        return None
    shared_key = f"feedback:pulse:{cache_key}"
    shared_payload = _shared_cache_get_json(shared_key)
    if shared_payload is not None:
        return deepcopy(shared_payload)
    return _legacy_local_cache_get(cache_key)


def _set_pulse_cache(cache_key: str, payload: dict[str, Any]) -> None:
    if not _pulse_cache_enabled():
        return
    ttl = int(current_app.config.get("FEEDBACK_PULSE_ANALYTICS_CACHE_TTL_SECONDS", _PULSE_ANALYTICS_CACHE_TTL_SECONDS) or _PULSE_ANALYTICS_CACHE_TTL_SECONDS)
    shared_key = f"feedback:pulse:{cache_key}"
    if not _shared_cache_set_json(shared_key, payload, ttl_seconds=max(5, ttl)):
        _legacy_local_cache_set(cache_key, payload, ttl)


def _clear_pulse_cache_for_unit(unit_id: int | None = None) -> None:
    if not _pulse_cache_enabled():
        return
    if unit_id is None:
        _shared_cache_delete_prefix("feedback:pulse:")
        current_app.extensions.setdefault(_PULSE_ANALYTICS_CACHE_KEY, {}).clear()
        return
    prefix = f"unit:{unit_id}|"
    _shared_cache_delete_prefix(f"feedback:pulse:{prefix}")
    cache = current_app.extensions.setdefault(_PULSE_ANALYTICS_CACHE_KEY, {})
    for key in list(cache.keys()):
        if str(key).startswith(prefix):
            cache.pop(key, None)


def _enqueue_pulse_analytics_refresh(unit_id: int | None, *, days: int = 30):
    """Nabız analitiği cache yenilemeyi gerçek asenkron kuyruğa bağla.

    Redis/RQ yoksa bu fonksiyon isteği yavaşlatmaz; inline fallback kapalıdır.
    Böylece altyapı üretimde gerçekten kullanılır, geliştirme ortamında ise güvenli
    şekilde atlanır.
    """
    if not unit_id or not has_app_context():
        return None
    try:
        if not bool(current_app.config.get("FEEDBACK_PULSE_ASYNC_REFRESH_ENABLED", True)):
            return None
        from app.services.async_job_queue import enqueue_job
        queue_name = current_app.config.get("ASYNC_TASK_QUEUE_DEFAULT", "bys360-default")
        return enqueue_job(
            "app.tasks.feedback_tasks.refresh_pulse_analytics_for_unit",
            unit_id=int(unit_id),
            days=max(7, min(int(days or 30), 120)),
            queue_name=queue_name,
            timeout=300,
            result_ttl=900,
            allow_inline_fallback=False,
        )
    except Exception as exc:  # pragma: no cover - koruyucu; kullanıcı akışı asla bozulmasın
        try:
            current_app.logger.warning("Nabız analitiği async yenileme kuyruğa alınamadı: %s", exc)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/feedback_service.py")
        return None


def _build_pulse_risk_users_from_rows(rows, users_by_id: dict[int, Any], *, minimum_streak: int = 3) -> list[dict[str, Any]]:
    """Build named pulse risk rows without ever de-anonymising anonymous entries."""
    identified_rows = [
        row for row in rows
        if getattr(row, "user_id", None) and not bool(getattr(row, "is_anonymous", False))
    ]

    streak_map: dict[int, int] = defaultdict(int)
    max_streak_map: dict[int, int] = defaultdict(int)
    last_seen_date: dict[int, date] = {}

    for row in identified_rows:
        uid = int(row.user_id)
        previous_date = last_seen_date.get(uid)
        if int(getattr(row, "mood_value", 0) or 0) <= 2:
            if previous_date and row.entry_date == previous_date + timedelta(days=1):
                streak_map[uid] += 1
            else:
                streak_map[uid] = 1
            max_streak_map[uid] = max(max_streak_map[uid], streak_map[uid])
        else:
            streak_map[uid] = 0
        last_seen_date[uid] = row.entry_date

    risk_users: list[dict[str, Any]] = []
    for uid, max_streak in max_streak_map.items():
        if max_streak < max(1, int(minimum_streak or 3)):
            continue
        user_row = users_by_id.get(uid)
        risk_users.append({
            "user_id": uid,
            "name": (
                getattr(user_row, "full_name", None)
                or f"{getattr(user_row, 'ad', '')} {getattr(user_row, 'soyad', '')}".strip()
                or f"Kullanıcı #{uid}"
            ),
            "max_streak": max_streak,
        })

    risk_users.sort(key=lambda item: (-item["max_streak"], item["name"]))
    return risk_users

def _daily_average_buckets(rows, start_date: date, end_date: date):
    buckets = defaultdict(list)
    for row in rows:
        buckets[row.entry_date].append(float(row.mood_value or 0))
    labels = []
    values = []
    spark_points = []
    cursor = start_date
    while cursor <= end_date:
        labels.append(cursor.isoformat())
        values.append(round(sum(buckets[cursor]) / len(buckets[cursor]), 2) if buckets.get(cursor) else None)
        cursor += timedelta(days=1)
    max_value = max([value for value in values if value is not None] or [5])
    for label, value in zip(labels, values, strict=False):
        if value is None:
            spark_points.append({"label": label, "value": None, "height": 8})
        else:
            spark_points.append({"label": label, "value": value, "height": max(12, int((value / max_value) * 100))})
    return labels, values, spark_points


def build_pulse_analytics(user, days: int = 30, minimum_group_size: int = 5):
    safe_days = max(7, min(int(days or 30), 120))
    unit_id = getattr(user, "organization_unit_id", None)
    if not unit_id:
        return {
            "eligible": False,
            "reason": "Birim bilgisi bulunmuyor.",
            "participant_count": 0,
            "minimum_group_size": minimum_group_size,
            "daily_labels": [],
            "daily_values": [],
            "spark_points": [],
            "distribution": [],
            "average": None,
            "delta": None,
            "coverage_rate": None,
            "risk_user_count": 0,
            "risk_users": [],
        }

    cache_key = _pulse_cache_key(unit_id=unit_id, days=safe_days, minimum_group_size=minimum_group_size)
    cached_payload = _get_pulse_cache(cache_key)
    if cached_payload is not None:
        return cached_payload

    start_date = date.today() - timedelta(days=safe_days - 1)
    rows = (
        FeedbackPulseEntry.query
        .filter(FeedbackPulseEntry.organization_unit_id == unit_id)
        .filter(FeedbackPulseEntry.entry_date >= start_date)
        .order_by(FeedbackPulseEntry.entry_date.asc(), FeedbackPulseEntry.id.asc())
        .all()
    )
    participant_ids = sorted({row.user_id for row in rows if row.user_id})
    participant_count = len(participant_ids)
    daily_labels, daily_values, spark_points = _daily_average_buckets(rows, start_date, date.today())
    average = round(sum(row.mood_value for row in rows) / len(rows), 2) if rows else None

    distribution = []
    for value in range(5, 0, -1):
        count = sum(1 for row in rows if row.mood_value == value)
        distribution.append({
            "value": value,
            "label": MOOD_CHOICES.get(value, str(value)),
            "count": count,
        })

    last_7 = [row.mood_value for row in rows if row.entry_date >= date.today() - timedelta(days=6)]
    prev_start = date.today() - timedelta(days=13)
    prev_end = date.today() - timedelta(days=7)
    prev_7 = [row.mood_value for row in rows if prev_start <= row.entry_date <= prev_end]
    delta = None
    if last_7 and prev_7:
        delta = round((sum(last_7) / len(last_7)) - (sum(prev_7) / len(prev_7)), 2)

    active_user_count = (
        User.query
        .filter(User.organization_unit_id == unit_id)
        .filter(User.is_active.is_(True) if hasattr(User, "is_active") else True)
        .count()
    ) or 0
    coverage_rate = round((participant_count / active_user_count) * 100, 2) if active_user_count else None

    # Gizlilik sınırı: anonim nabız kayıtları genel ortalamaya katılabilir,
    # ancak asla kişi bazlı risk listesine dönüştürülmez.
    identified_user_ids = sorted({
        int(row.user_id)
        for row in rows
        if getattr(row, "user_id", None) and not bool(getattr(row, "is_anonymous", False))
    })
    user_rows = {
        user_row.id: user_row
        for user_row in User.query.filter(User.id.in_(tuple(identified_user_ids))).all()
    } if identified_user_ids else {}
    risk_users = _build_pulse_risk_users_from_rows(rows, user_rows, minimum_streak=3)

    eligible = participant_count >= int(minimum_group_size or 5)
    reason = None if eligible else "Gizlilik eşiği için yeterli katılımcı yok."

    payload = {
        "eligible": eligible,
        "reason": reason,
        "participant_count": participant_count,
        "minimum_group_size": minimum_group_size,
        "daily_labels": daily_labels,
        "daily_values": daily_values,
        "spark_points": spark_points,
        "distribution": distribution,
        "average": average,
        "delta": delta,
        "coverage_rate": coverage_rate,
        "risk_user_count": len(risk_users),
        "risk_users": risk_users,
    }
    _set_pulse_cache(cache_key, payload)
    return payload


def build_campaign_pulse_context(campaign: FeedbackCampaign | None):
    if not campaign:
        return {
            "available": False,
            "labels": [],
            "values": [],
            "spark_points": [],
            "average": None,
            "delta": None,
            "pulse_count": 0,
            "window_label": "",
        }

    end_date = campaign.end_at.date() if getattr(campaign, "end_at", None) else date.today()
    start_date = campaign.start_at.date() if getattr(campaign, "start_at", None) else end_date - timedelta(days=13)
    if start_date > end_date:
        start_date = end_date - timedelta(days=13)
    if (end_date - start_date).days > 45:
        start_date = end_date - timedelta(days=45)

    query = FeedbackPulseEntry.query.filter(FeedbackPulseEntry.entry_date >= start_date).filter(FeedbackPulseEntry.entry_date <= end_date)
    if getattr(campaign, "organization_unit_id", None):
        query = query.filter(FeedbackPulseEntry.organization_unit_id == campaign.organization_unit_id)
    rows = query.order_by(FeedbackPulseEntry.entry_date.asc(), FeedbackPulseEntry.id.asc()).all()
    labels, values, spark_points = _daily_average_buckets(rows, start_date, end_date)

    average = round(sum(row.mood_value for row in rows) / len(rows), 2) if rows else None
    midpoint = start_date + timedelta(days=((end_date - start_date).days // 2))
    first_half = [row.mood_value for row in rows if row.entry_date <= midpoint]
    second_half = [row.mood_value for row in rows if row.entry_date > midpoint]
    delta = None
    if first_half and second_half:
        delta = round((sum(second_half) / len(second_half)) - (sum(first_half) / len(first_half)), 2)

    return {
        "available": bool(rows),
        "labels": labels,
        "values": values,
        "spark_points": spark_points,
        "average": average,
        "delta": delta,
        "pulse_count": len(rows),
        "window_label": f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}",
    }


def create_campaign_from_form(*, form, actor):
    title = (form.get("title") or "").strip()
    if not title:
        raise ValueError("Kampanya başlığı zorunludur.")

    question_lines = [line.strip() for line in (form.get("question_texts") or "").splitlines() if line.strip()]
    if not question_lines:
        raise ValueError("En az bir soru girmelisiniz.")

    question_type = (form.get("question_type") or "scale_1_5").strip().lower()
    if question_type not in {"scale_1_5", "single_choice", "text"}:
        question_type = "scale_1_5"

    campaign_type = (form.get("campaign_type") or "survey").strip().lower() or "survey"
    if campaign_type not in {"survey", "pulse", "training_feedback", "survey_with_pulse", "training_feedback_with_pulse"}:
        campaign_type = "survey"

    campaign = FeedbackCampaign(
        title=title,
        description=(form.get("description") or "").strip() or None,
        campaign_type=campaign_type,
        target_scope=(form.get("target_scope") or "all").strip().lower() or "all",
        organization_unit_id=getattr(actor, "organization_unit_id", None),
        is_anonymous=bool(form.get("is_anonymous")),
        allow_multiple_submissions=bool(form.get("allow_multiple_submissions")),
        allow_comment=bool(form.get("allow_comment", True)),
        status="draft",
        start_at=parse_datetime_local(form.get("start_at")),
        end_at=parse_datetime_local(form.get("end_at")),
        created_by_user_id=actor.id,
    )
    db.session.add(campaign)
    db.session.flush()

    for idx, question_text in enumerate(question_lines, start=1):
        question = FeedbackQuestion(
            campaign_id=campaign.id,
            question_text=question_text,
            question_type=question_type,
            is_required=True,
            sort_order=idx,
        )
        db.session.add(question)
        db.session.flush()

        if question_type == "single_choice":
            options_raw = [part.strip() for part in (form.get("option_values") or "").split(",") if part.strip()]
            if not options_raw:
                options_raw = ["Çok iyi", "İyi", "Nötr", "Zorlanıyorum", "Desteğe ihtiyacım var"]
            for opt_idx, option_text in enumerate(options_raw, start=1):
                db.session.add(FeedbackQuestionOption(
                    question_id=question.id,
                    option_text=option_text,
                    option_value=option_text,
                    sort_order=opt_idx,
                ))

    target_scope = campaign.target_scope
    target_value = (form.get("target_value") or "").strip()
    if target_scope == "all":
        db.session.add(FeedbackCampaignAssignment(campaign_id=campaign.id, target_type="all", target_value=None))
    elif target_scope in {"user", "role", "unit"}:
        if not target_value:
            raise ValueError("Seçilen hedef kapsamı için hedef değeri zorunludur.")
        db.session.add(FeedbackCampaignAssignment(campaign_id=campaign.id, target_type=target_scope, target_value=target_value))
    else:
        db.session.add(FeedbackCampaignAssignment(campaign_id=campaign.id, target_type="all", target_value=None))

    notify_feedback_campaign_created(campaign, actor)
    db.session.commit()
    return campaign


def change_campaign_status(*, campaign: FeedbackCampaign, target_status: str):
    target = (target_status or "").strip().lower()
    if target not in {"draft", "published", "closed", "archived"}:
        raise ValueError("Geçersiz kampanya durumu.")
    campaign.status = target
    campaign.is_active = target != "archived"
    if target == "published":
        campaign.published_at = utc_now()
    notify_feedback_campaign_status_changed(campaign, getattr(campaign, "created_by", None), target_status=target)
    db.session.commit()
    return campaign


def submit_campaign_answers(*, user, campaign: FeedbackCampaign, form):
    if not campaign_is_open(campaign):
        raise ValueError("Bu kampanya şu anda yanıtlamaya açık değil.")
    if not user_can_see_campaign(user, campaign):
        raise ValueError("Bu kampanyaya erişim yetkiniz yok.")
    if not campaign.allow_multiple_submissions and has_user_submitted_campaign(user, campaign):
        raise ValueError("Bu kampanyayı daha önce yanıtladınız.")

    submission = FeedbackSubmission(
        campaign_id=campaign.id,
        user_id=None if campaign.is_anonymous else user.id,
        organization_unit_id=user.organization_unit_id,
        is_completed=True,
        anonymous_token=secrets.token_hex(12) if campaign.is_anonymous else None,
    )
    db.session.add(submission)
    db.session.flush()

    for question in campaign.questions.order_by(FeedbackQuestion.sort_order.asc(), FeedbackQuestion.id.asc()).all():
        field_name = f"question_{question.id}"
        raw_value = form.get(field_name)
        if question.is_required and not raw_value:
            raise ValueError(f"'{question.question_text[:60]}' sorusu zorunludur.")

        answer = FeedbackAnswer(submission_id=submission.id, question_id=question.id)
        if question.question_type == "scale_1_5":
            answer.answer_number = float(raw_value) if raw_value not in {None, ""} else None
        elif question.question_type == "single_choice":
            try:
                answer.selected_option_id = int(raw_value) if raw_value else None
            except (TypeError, ValueError):
                answer.selected_option_id = None
        else:
            answer.answer_text = (raw_value or "").strip()[:2000] or None
        db.session.add(answer)

    notify_feedback_submission_received(campaign, user, submission)
    db.session.commit()

    pulse_mood_value = form.get("pulse_mood_value")
    if campaign_includes_pulse(campaign) and pulse_mood_value not in {None, ""}:
        try:
            save_pulse_entry(
                user=user,
                mood_value=int(pulse_mood_value),
                short_note=(form.get("pulse_short_note") or "").strip(),
                is_anonymous=bool(form.get("pulse_is_anonymous")) or bool(campaign.is_anonymous),
            )
        except Exception:
            db.session.rollback()
            raise

    return submission


def build_dashboard_data(user):
    visible_campaigns = list_visible_campaigns_for_user(user)
    today_pulse = get_today_pulse_entry(user)
    open_actions_count = (
        FeedbackActionPlan.query
        .filter(FeedbackActionPlan.status.in_(["open", "in_progress"]))
        .filter(
            (FeedbackActionPlan.assigned_manager_id == user.id)
            | (FeedbackActionPlan.created_by_user_id == user.id)
        )
        .count()
    ) if is_manager_family(user) else 0

    thirty_days_ago = date.today() - timedelta(days=29)
    pulse_rows = (
        FeedbackPulseEntry.query
        .filter(FeedbackPulseEntry.entry_date >= thirty_days_ago)
        .filter(FeedbackPulseEntry.organization_unit_id == user.organization_unit_id)
        .all()
    )
    pulse_avg = round(sum(row.mood_value for row in pulse_rows) / len(pulse_rows), 2) if pulse_rows else None
    pulse_history = get_pulse_history(user, 7)

    return {
        "visible_campaign_count": len(visible_campaigns),
        "today_pulse": today_pulse,
        "open_actions_count": open_actions_count,
        "pulse_avg": pulse_avg,
        "recent_campaigns": visible_campaigns[:5],
        "pulse_history_preview": pulse_history[:5],
        "manager_pulse_analytics": build_pulse_analytics(user, 30) if is_manager_family(user) else None,
    }


def build_campaign_results(campaign: FeedbackCampaign):
    results = []
    submission_count = campaign.submissions.count()
    for question in campaign.questions.order_by(FeedbackQuestion.sort_order.asc(), FeedbackQuestion.id.asc()).all():
        row = {
            "question": question,
            "submission_count": submission_count,
            "average": None,
            "option_counts": [],
            "text_samples": [],
        }
        if question.question_type == "scale_1_5":
            avg = (
                db.session.query(func.avg(FeedbackAnswer.answer_number))
                .filter(FeedbackAnswer.question_id == question.id)
                .scalar()
            )
            row["average"] = round(float(avg), 2) if avg is not None else None
        elif question.question_type == "single_choice":
            counts = []
            for option in question.options.order_by(FeedbackQuestionOption.sort_order.asc(), FeedbackQuestionOption.id.asc()).all():
                count = FeedbackAnswer.query.filter_by(question_id=question.id, selected_option_id=option.id).count()
                counts.append((option.option_text, count))
            row["option_counts"] = counts
        else:
            samples = (
                FeedbackAnswer.query
                .filter(FeedbackAnswer.question_id == question.id)
                .filter(FeedbackAnswer.answer_text.isnot(None))
                .order_by(FeedbackAnswer.created_at.desc(), FeedbackAnswer.id.desc())
                .limit(8)
                .all()
            )
            row["text_samples"] = [sample.answer_text for sample in samples if sample.answer_text]
        results.append(row)
    return results


def build_manager_summary(user):
    thirty_days_ago = date.today() - timedelta(days=29)
    unit_id = getattr(user, "organization_unit_id", None)
    if not unit_id:
        return {"pulse_counts": {}, "pulse_average": None, "campaign_completion": [], "analytics": build_pulse_analytics(user, 30)}

    pulse_rows = (
        FeedbackPulseEntry.query
        .filter(FeedbackPulseEntry.organization_unit_id == unit_id)
        .filter(FeedbackPulseEntry.entry_date >= thirty_days_ago)
        .all()
    )
    pulse_counts = defaultdict(int)
    for row in pulse_rows:
        pulse_counts[row.mood_label] += 1
    pulse_average = round(sum(row.mood_value for row in pulse_rows) / len(pulse_rows), 2) if pulse_rows else None

    completion = []
    campaigns = FeedbackCampaign.query.order_by(FeedbackCampaign.created_at.desc(), FeedbackCampaign.id.desc()).limit(10).all()
    for campaign in campaigns:
        if not campaign.is_active:
            continue
        total_submissions = campaign.submissions.count()
        completion.append({
            "campaign": campaign,
            "submission_count": total_submissions,
        })

    return {
        "pulse_counts": dict(pulse_counts),
        "pulse_average": pulse_average,
        "campaign_completion": completion,
        "analytics": build_pulse_analytics(user, 30),
    }


def list_action_plans_for_user(user):
    query = FeedbackActionPlan.query.order_by(FeedbackActionPlan.created_at.desc(), FeedbackActionPlan.id.desc())
    if is_manager_family(user):
        return query.all()
    return query.filter(FeedbackActionPlan.assigned_manager_id == user.id).all()


def create_action_plan(*, actor, form):
    title = (form.get("title") or "").strip()
    if not title:
        raise ValueError("Aksiyon başlığı zorunludur.")
    campaign_id = form.get("campaign_id") or None
    plan = FeedbackActionPlan(
        campaign_id=int(campaign_id) if campaign_id else None,
        organization_unit_id=getattr(actor, "organization_unit_id", None),
        assigned_manager_id=int(form.get("assigned_manager_id")) if (form.get("assigned_manager_id") or "").strip().isdigit() else actor.id,
        created_by_user_id=actor.id,
        title=title,
        description=(form.get("description") or "").strip()[:2000] or None,
        priority=(form.get("priority") or "medium").strip().lower() or "medium",
        status=(form.get("status") or "open").strip().lower() or "open",
    )
    due_raw = (form.get("due_date") or "").strip()
    if due_raw:
        try:
            plan.due_date = date.fromisoformat(due_raw)
        except ValueError:
            plan.due_date = None
    db.session.add(plan)
    db.session.flush()
    notify_feedback_action_plan_created(plan, actor)
    db.session.commit()
    return plan


def update_action_status(*, action_plan: FeedbackActionPlan, status: str, resolution_note: str = ""):
    status = (status or "").strip().lower()
    if status not in {"open", "in_progress", "resolved", "cancelled"}:
        raise ValueError("Geçersiz aksiyon durumu.")
    action_plan.status = status
    if status == "resolved":
        action_plan.resolved_at = utc_now()
        action_plan.resolution_note = (resolution_note or "").strip()[:2000] or None
    notify_feedback_action_plan_status_changed(action_plan, getattr(action_plan, "assigned_manager", None), status=status)
    db.session.commit()
    return action_plan