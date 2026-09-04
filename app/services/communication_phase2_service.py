from __future__ import annotations

import logging
from collections import Counter, defaultdict
from collections.abc import Iterable
from datetime import datetime
from typing import Any

from app.core.datetime_utils import utc_now
from app.extensions import db
from app.models import (
    Notification,
    OrganizationUnit,
    Survey,
    SurveyAssignment,
    SurveyQuestion,
    SurveyQuestionOption,
    SurveyResponse,
    User,
)
from app.models.communication_phase1_models import (
    CommunicationBulletin,
    CommunicationBulletinAudience,
    CommunicationBulletinReceipt,
)
from app.models.communication_phase2_models import (
    CommunicationBulletinRevision,
    CommunicationSurveyTemplate,
    CommunicationSurveyTemplateQuestion,
)
from app.models.communication_phase3_models import CommunicationSurveyReminderLog

logger = logging.getLogger(__name__)


MANAGER_ROLES = {
    "admin",
    "baskan",
    "baskan_yardimcisi",
    "grup_baskani",
    "mali_musavir",
    "birim_sorumlusu",
}

SURVEY_QUESTION_TYPE_LABELS = {
    "single_choice": "Tek seçim",
    "multi_choice": "Çoklu seçim",
    "text": "Açık uçlu",
    "yes_no": "Evet / Hayır",
    "score": "Puan",
    "likert": "Likert",
}

SURVEY_STATUS_LABELS = {
    "draft": "Taslak",
    "published": "Yayında",
    "closed": "Kapatıldı",
    "archived": "Arşiv",
}

SURVEY_TYPE_LABELS = {
    "kurum_ici": "Kurum İçi",
    "memnuniyet": "Memnuniyet",
    "egitim": "Eğitim",
    "nabiz": "Nabız",
    "geri_bildirim": "Geri Bildirim",
}

SURVEY_TARGET_TYPE_LABELS = {
    "all": "Tüm Personel",
    "user": "Kullanıcı",
    "role": "Rol",
    "unit": "Birim",
}

BULLETIN_STATUS_LABELS = {
    "draft": "Taslak",
    "published": "Yayında",
    "archived": "Arşiv",
}

BULLETIN_PRIORITY_LABELS = {
    "low": "Düşük",
    "normal": "Normal",
    "high": "Yüksek",
    "critical": "Kritik",
}


class CommunicationPhase2Error(RuntimeError):
    pass


def _now() -> datetime:
    return utc_now()


def safe_str(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return safe_str(value).lower() in {"1", "true", "on", "yes", "evet"}


def user_role_slug(user: Any) -> str:
    return safe_str(getattr(user, "role", "")).lower()


def is_manager(user: Any) -> bool:
    return user_role_slug(user) in MANAGER_ROLES


def _active_user_query():
    query = User.query
    if hasattr(User, "is_active"):
        query = query.filter(User.is_active.is_(True))
    return query


def _user_display_name(user: Any) -> str:
    if not user:
        return "-"
    for attr in ("full_name", "full_name_cache"):
        value = safe_str(getattr(user, attr, ""))
        if value:
            return value
    ad = safe_str(getattr(user, "ad", ""))
    soyad = safe_str(getattr(user, "soyad", ""))
    merged = f"{ad} {soyad}".strip()
    return merged or safe_str(getattr(user, "email", "")) or "-"


def manager_filter_options() -> dict[str, list[dict[str, Any]]]:
    units = []
    try:
        if OrganizationUnit is not None:
            rows = OrganizationUnit.query.order_by(OrganizationUnit.name.asc()).all()
            units = [{"value": str(row.id), "label": safe_str(getattr(row, "name", "-"))} for row in rows]
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/communication_phase2_service.py | line=126")
        units = []

    roles = [
        {"value": "personel", "label": "Personel"},
        {"value": "birim_sorumlusu", "label": "Birim Sorumlusu"},
        {"value": "koordinator", "label": "Koordinatör"},
        {"value": "grup_baskani", "label": "Grup Başkanı"},
        {"value": "mali_musavir", "label": "Mali Müşavir"},
        {"value": "baskan_yardimcisi", "label": "Başkan Yardımcısı"},
        {"value": "baskan", "label": "Başkan"},
        {"value": "admin", "label": "Sistem Yöneticisi"},
    ]

    users = []
    try:
        rows = _active_user_query().order_by(User.ad.asc(), User.soyad.asc()).all()
        users = [
            {"value": str(row.id), "label": f"{_user_display_name(row)} · {safe_str(getattr(row, 'sicil_no', '')) or '-'}"}
            for row in rows
        ]
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/communication_phase2_service.py | line=147")
        users = []

    return {"roles": roles, "units": units, "users": users}


def _normalize_target_values(target_type: str, raw_text: str | None) -> list[str]:
    values = [safe_str(part) for part in (raw_text or "").replace("\n", ",").split(",")]
    clean_values = [value for value in values if value]
    if target_type == "all":
        return ["all"]
    return list(dict.fromkeys(clean_values))


def _resolve_users_for_audience(target_type: str, raw_values: Iterable[str]) -> list[Any]:
    query = _active_user_query()
    target_type = safe_str(target_type).lower() or "all"
    values = [safe_str(v) for v in raw_values if safe_str(v)]

    if target_type == "all" or not values:
        return query.all()

    matched_ids: set[int] = set()

    if target_type == "role":
        for value in values:
            if hasattr(User, "role"):
                rows = query.filter(User.role == value).all()
                matched_ids.update(row.id for row in rows)
    elif target_type == "unit":
        if hasattr(User, "organization_unit_id"):
            numeric_values = [int(v) for v in values if v.isdigit()]
            if numeric_values:
                rows = query.filter(User.organization_unit_id.in_(numeric_values)).all()
                matched_ids.update(row.id for row in rows)
        if hasattr(User, "birim"):
            for value in values:
                rows = query.filter(User.birim == value).all()
                matched_ids.update(row.id for row in rows)
    elif target_type == "user":
        numeric_values = [int(v) for v in values if v.isdigit()]
        if numeric_values:
            rows = query.filter(User.id.in_(numeric_values)).all()
            matched_ids.update(row.id for row in rows)
    else:
        return query.all()

    return query.filter(User.id.in_(sorted(matched_ids))).all() if matched_ids else []


def _notification_create(user_id: int, title: str, body: str, notification_type: str, source_type: str, source_id: int | None, link_url: str | None = None):
    row = Notification(
        user_id=user_id,
        title=title,
        body=body or None,
        notification_type=notification_type,
        source_type=source_type,
        source_id=source_id,
        link_url=link_url,
        priority="normal",
        is_read=False,
    )
    db.session.add(row)
    return row


def _survey_link_url(survey_id: int) -> str:
    return f"/communication/faz3/surveys/{survey_id}/take"


def _parse_datetime_value(raw_value: Any) -> datetime | None:
    value = safe_str(raw_value)
    if not value:
        return None
    for pattern in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, pattern)
        except ValueError:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/communication_phase2_service.py:224)")
            continue
    raise CommunicationPhase2Error("Tarih alanları geçerli bir tarih/saat formatında olmalıdır.")


def _assignment_rows_for_survey(survey: Any) -> list[tuple[str, str | None]]:
    rows: list[tuple[str, str | None]] = []
    for assignment in survey.assignments.order_by(SurveyAssignment.id.asc()).all():
        rows.append((safe_str(getattr(assignment, "target_type", "")) or "all", safe_str(getattr(assignment, "target_value", "")) or None))
    return rows


def _resolved_target_users_from_rows(rows: Iterable[tuple[str, str | None]]) -> list[Any]:
    matched: dict[int, Any] = {}
    for target_type, target_value in rows:
        raw_values = [target_value] if target_value else ["all"]
        for user in _resolve_users_for_audience(target_type, raw_values):
            matched[int(user.id)] = user
    return list(matched.values())


def _survey_completion_summary(survey: Any) -> dict[str, Any]:
    target_rows = _assignment_rows_for_survey(survey)
    target_users = _resolved_target_users_from_rows(target_rows)
    target_total = len(target_users)
    responses = survey.responses.all()
    completed_total = sum(1 for row in responses if bool(getattr(row, "is_completed", False)))
    draft_total = max(len(responses) - completed_total, 0)
    pending_total = max(target_total - completed_total, 0)
    completion_rate = round((completed_total / target_total) * 100.0, 2) if target_total else 0.0
    return {
        "target_total": target_total,
        "response_total": len(responses),
        "completed_total": completed_total,
        "draft_total": draft_total,
        "pending_total": pending_total,
        "completion_rate": completion_rate,
    }


def _question_payloads_from_survey(survey: Any) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for question in survey.questions.order_by(SurveyQuestion.sort_order.asc(), SurveyQuestion.id.asc()).all():
        options = [
            safe_str(getattr(option, "option_text", ""))
            for option in question.options.order_by(SurveyQuestionOption.sort_order.asc(), SurveyQuestionOption.id.asc()).all()
            if safe_str(getattr(option, "option_text", ""))
        ]
        payloads.append({
            "question_text": safe_str(getattr(question, "question_text", "")),
            "question_type": safe_str(getattr(question, "question_type", "")) or "single_choice",
            "is_required": bool(getattr(question, "is_required", False)),
            "options": options,
            "options_text": "\n".join(options),
        })
    return payloads


def _replace_survey_questions(survey: Any, questions_payload: list[dict[str, Any]]) -> None:
    survey.questions.delete()
    db.session.flush()
    _create_survey_questions(survey.id, questions_payload)


def _replace_survey_assignments(survey: Any, assignment_rows: list[tuple[str, str | None]]) -> None:
    survey.assignments.delete()
    db.session.flush()
    for assignment_type, assignment_value in assignment_rows:
        db.session.add(
            SurveyAssignment(
                survey_id=survey.id,
                target_type=assignment_type,
                target_value=assignment_value,
            )
        )


def survey_builder_payload(survey_id: int) -> dict[str, Any]:
    survey = db.session.get(Survey, survey_id)
    if not survey:
        raise CommunicationPhase2Error("Anket bulunamadı.")
    first_assignment = survey.assignments.order_by(SurveyAssignment.id.asc()).first()
    target_values = [
        safe_str(getattr(row, "target_value", ""))
        for row in survey.assignments.order_by(SurveyAssignment.id.asc()).all()
        if safe_str(getattr(row, "target_value", ""))
    ]
    start_at = getattr(survey, "start_at", None)
    end_at = getattr(survey, "end_at", None)
    return {
        "survey": survey,
        "form_state": {
            "title": safe_str(getattr(survey, "title", "")),
            "description": safe_str(getattr(survey, "description", "")),
            "survey_type": safe_str(getattr(survey, "survey_type", "")) or "kurum_ici",
            "target_type": safe_str(getattr(first_assignment, "target_type", "")) or "all",
            "target_values": ", ".join(target_values),
            "is_anonymous": bool(getattr(survey, "is_anonymous", False)),
            "allow_multiple_submissions": bool(getattr(survey, "allow_multiple_submissions", False)),
            "publish_now": safe_str(getattr(survey, "status", "")) == "published",
            "start_at": start_at.strftime("%Y-%m-%dT%H:%M") if start_at else "",
            "end_at": end_at.strftime("%Y-%m-%dT%H:%M") if end_at else "",
            "questions": _question_payloads_from_survey(survey),
        },
    }


def _next_bulletin_version(bulletin_id: int) -> int:
    latest = (
        CommunicationBulletinRevision.query
        .filter_by(bulletin_id=bulletin_id)
        .order_by(CommunicationBulletinRevision.version_no.desc())
        .first()
    )
    return int(getattr(latest, "version_no", 0) or 0) + 1


def record_bulletin_revision(bulletin: CommunicationBulletin, changed_by_user_id: int | None, change_note: str | None = "") -> CommunicationBulletinRevision:
    revision = CommunicationBulletinRevision(
        bulletin_id=bulletin.id,
        version_no=_next_bulletin_version(bulletin.id),
        title=bulletin.title,
        summary=bulletin.summary,
        content=bulletin.content,
        bulletin_type=bulletin.bulletin_type,
        priority=bulletin.priority,
        status=bulletin.status,
        changed_by_user_id=changed_by_user_id,
        change_note=safe_str(change_note) or None,
    )
    db.session.add(revision)
    db.session.flush()
    return revision


def update_bulletin(
    *,
    bulletin_id: int,
    actor_user_id: int | None,
    title: str | None,
    summary: str | None,
    content: str | None,
    bulletin_type: str | None,
    priority: str | None,
    target_type: str | None,
    target_values_text: str | None,
    is_pinned: bool,
    require_ack: bool,
    change_note: str | None,
) -> CommunicationBulletin:
    bulletin = db.session.get(CommunicationBulletin, bulletin_id)
    if not bulletin:
        raise CommunicationPhase2Error("Duyuru kaydı bulunamadı.")

    title = safe_str(title)
    content = safe_str(content)
    if not title or not content:
        raise CommunicationPhase2Error("Başlık ve içerik zorunludur.")

    record_bulletin_revision(bulletin, actor_user_id, change_note)

    bulletin.title = title
    bulletin.summary = safe_str(summary) or None
    bulletin.content = content
    bulletin.bulletin_type = safe_str(bulletin_type) or "duyuru"
    bulletin.priority = safe_str(priority) or "normal"
    bulletin.is_pinned = bool(is_pinned)
    bulletin.require_ack = bool(require_ack)

    bulletin.audiences.delete()
    target_type = safe_str(target_type).lower() or "all"
    target_values = _normalize_target_values(target_type, target_values_text)
    for value in target_values:
        db.session.add(
            CommunicationBulletinAudience(
                bulletin_id=bulletin.id,
                target_type=target_type,
                target_value=None if target_type == "all" else value,
            )
        )

    db.session.add(bulletin)
    db.session.commit()
    return bulletin


def archive_bulletin(bulletin_id: int, actor_user_id: int | None, note: str | None = "") -> CommunicationBulletin:
    bulletin = db.session.get(CommunicationBulletin, bulletin_id)
    if not bulletin:
        raise CommunicationPhase2Error("Duyuru kaydı bulunamadı.")
    record_bulletin_revision(bulletin, actor_user_id, note or "Arşive alındı")
    bulletin.status = "archived"
    db.session.add(bulletin)
    db.session.commit()
    return bulletin


def bulletin_history_payload(bulletin_id: int) -> dict[str, Any]:
    bulletin = db.session.get(CommunicationBulletin, bulletin_id)
    if not bulletin:
        raise CommunicationPhase2Error("Duyuru kaydı bulunamadı.")
    revisions = bulletin.revisions.all()
    return {
        "bulletin": bulletin,
        "revisions": revisions,
        "receipts": bulletin.receipts.order_by(CommunicationBulletinReceipt.created_at.desc()).limit(50).all(),
        "audiences": bulletin.audiences.order_by(CommunicationBulletinAudience.id.asc()).all(),
    }


def list_survey_templates() -> list[CommunicationSurveyTemplate]:
    return CommunicationSurveyTemplate.query.order_by(CommunicationSurveyTemplate.updated_at.desc(), CommunicationSurveyTemplate.id.desc()).all()


def upsert_survey_template(
    *,
    template_id: int | None,
    actor_user_id: int | None,
    title: str | None,
    description: str | None,
    survey_type: str | None,
    is_active: bool,
    questions_payload: list[dict[str, Any]],
) -> CommunicationSurveyTemplate:
    title = safe_str(title)
    if not title:
        raise CommunicationPhase2Error("Şablon başlığı zorunludur.")

    clean_questions: list[dict[str, Any]] = []
    for index, item in enumerate(questions_payload, start=1):
        question_text = safe_str(item.get("question_text"))
        if not question_text:
            continue
        clean_questions.append(
            {
                "question_text": question_text,
                "question_type": safe_str(item.get("question_type")) or "single_choice",
                "is_required": bool(item.get("is_required", True)),
                "sort_order": index,
                "options_text": safe_str(item.get("options_text")) or None,
            }
        )
    if not clean_questions:
        raise CommunicationPhase2Error("Şablonda en az bir soru bulunmalıdır.")

    template = db.session.get(CommunicationSurveyTemplate, template_id) if template_id else None
    if not template:
        template = CommunicationSurveyTemplate(created_by_user_id=actor_user_id)
        db.session.add(template)
        db.session.flush()

    template.title = title
    template.description = safe_str(description) or None
    template.survey_type = safe_str(survey_type) or "kurum_ici"
    template.is_active = bool(is_active)
    template.updated_by_user_id = actor_user_id

    template.questions.delete()
    db.session.flush()

    for item in clean_questions:
        db.session.add(
            CommunicationSurveyTemplateQuestion(
                template_id=template.id,
                question_text=item["question_text"],
                question_type=item["question_type"],
                is_required=item["is_required"],
                sort_order=item["sort_order"],
                options_text=item["options_text"],
            )
        )

    db.session.add(template)
    db.session.commit()
    return template


def _create_survey_questions(survey_id: int, questions_payload: list[dict[str, Any]]) -> None:
    for index, item in enumerate(questions_payload, start=1):
        question_text = safe_str(item.get("question_text"))
        if not question_text:
            continue
        question = SurveyQuestion(
            survey_id=survey_id,
            question_text=question_text,
            question_type=safe_str(item.get("question_type")) or "single_choice",
            is_required=bool(item.get("is_required", True)),
            sort_order=index,
        )
        db.session.add(question)
        db.session.flush()

        for option_index, option_text in enumerate([safe_str(x) for x in (item.get("options") or []) if safe_str(x)], start=1):
            db.session.add(
                SurveyQuestionOption(
                    question_id=question.id,
                    option_text=option_text,
                    sort_order=option_index,
                )
            )


def _assignment_rows_from_target_text(target_type: str | None, target_values_text: str | None) -> list[tuple[str, str | None]]:
    target_type = safe_str(target_type).lower() or "all"
    values = _normalize_target_values(target_type, target_values_text)
    if target_type == "all":
        return [("all", None)]
    return [(target_type, value) for value in values]


def create_survey_from_template_or_builder(
    *,
    actor_user_id: int,
    title: str | None,
    description: str | None,
    survey_type: str | None,
    is_anonymous: bool,
    allow_multiple_submissions: bool,
    target_type: str | None,
    target_values_text: str | None,
    publish_now: bool,
    start_at_raw: Any = None,
    end_at_raw: Any = None,
    template_id: int | None = None,
    questions_payload: list[dict[str, Any]] | None = None,
) -> Survey:
    title = safe_str(title)
    if not title:
        raise CommunicationPhase2Error("Anket başlığı zorunludur.")

    start_at = _parse_datetime_value(start_at_raw)
    end_at = _parse_datetime_value(end_at_raw)
    if start_at and end_at and end_at <= start_at:
        raise CommunicationPhase2Error("Bitiş tarihi başlangıç tarihinden sonra olmalıdır.")

    survey = Survey(
        title=title,
        description=safe_str(description) or None,
        survey_type=safe_str(survey_type) or "kurum_ici",
        created_by_user_id=actor_user_id,
        is_anonymous=bool(is_anonymous),
        allow_multiple_submissions=bool(allow_multiple_submissions),
        status="published" if publish_now else "draft",
        start_at=start_at or (_now() if publish_now else None),
        end_at=end_at,
    )
    db.session.add(survey)
    db.session.flush()

    if template_id:
        template = db.session.get(CommunicationSurveyTemplate, template_id)
        if not template:
            raise CommunicationPhase2Error("Seçilen anket şablonu bulunamadı.")
        temp_questions = template.questions.order_by(CommunicationSurveyTemplateQuestion.sort_order.asc()).all()
        questions_payload = [
            {
                "question_text": row.question_text,
                "question_type": row.question_type,
                "is_required": row.is_required,
                "options": row.parsed_options(),
            }
            for row in temp_questions
        ]

    if not questions_payload:
        raise CommunicationPhase2Error("Anket için en az bir soru gereklidir.")

    _create_survey_questions(survey.id, questions_payload)

    assignment_rows = _assignment_rows_from_target_text(target_type, target_values_text)
    for assignment_type, assignment_value in assignment_rows:
        db.session.add(
            SurveyAssignment(
                survey_id=survey.id,
                target_type=assignment_type,
                target_value=assignment_value,
            )
        )

    if publish_now:
        for assignment_type, assignment_value in assignment_rows:
            target_values = [assignment_value] if assignment_value else ["all"]
            target_users = _resolve_users_for_audience(assignment_type, target_values)
            for user in target_users:
                _notification_create(
                    user_id=user.id,
                    title=f"Yeni anket: {survey.title}",
                    body="Yanıtlamanız beklenen yeni bir anket yayımlandı.",
                    notification_type="survey",
                    source_type="survey",
                    source_id=survey.id,
                    link_url=_survey_link_url(survey.id),
                )

    db.session.commit()
    return survey


def publish_survey(survey_id: int, actor_user_id: int | None = None) -> Survey:
    survey = db.session.get(Survey, survey_id)
    if not survey:
        raise CommunicationPhase2Error("Anket bulunamadı.")
    survey.status = "published"
    if not survey.start_at:
        survey.start_at = _now()
    db.session.add(survey)
    db.session.flush()

    assignments = survey.assignments.all()
    notified_user_ids: set[int] = set()
    for assignment in assignments:
        raw_values = [assignment.target_value] if assignment.target_value else ["all"]
        for user in _resolve_users_for_audience(assignment.target_type, raw_values):
            if user.id in notified_user_ids:
                continue
            notified_user_ids.add(user.id)
            _notification_create(
                user_id=user.id,
                title=f"Yeni anket: {survey.title}",
                body="Yanıtlamanız beklenen yeni bir anket yayımlandı.",
                notification_type="survey",
                source_type="survey",
                source_id=survey.id,
                link_url=_survey_link_url(survey.id),
            )
    db.session.commit()
    return survey


def close_survey(survey_id: int) -> Survey:
    survey = db.session.get(Survey, survey_id)
    if not survey:
        raise CommunicationPhase2Error("Anket bulunamadı.")
    survey.status = "closed"
    if not survey.end_at:
        survey.end_at = _now()
    db.session.add(survey)
    db.session.commit()
    return survey


def update_survey_from_builder(
    *,
    survey_id: int,
    actor_user_id: int,
    title: str | None,
    description: str | None,
    survey_type: str | None,
    is_anonymous: bool,
    allow_multiple_submissions: bool,
    target_type: str | None,
    target_values_text: str | None,
    publish_now: bool,
    start_at_raw: Any = None,
    end_at_raw: Any = None,
    questions_payload: list[dict[str, Any]] | None = None,
) -> Survey:
    survey = db.session.get(Survey, survey_id)
    if not survey:
        raise CommunicationPhase2Error("Anket bulunamadı.")
    if safe_str(getattr(survey, "status", "")) == "archived":
        raise CommunicationPhase2Error("Arşivdeki anket doğrudan düzenlenemez.")
    if survey.responses.count() > 0:
        raise CommunicationPhase2Error("Yanıt almaya başlayan anket düzenlenemez. Kopyasını oluşturup yeni sürüm üzerinden devam edin.")

    title = safe_str(title)
    if not title:
        raise CommunicationPhase2Error("Anket başlığı zorunludur.")
    if not questions_payload:
        raise CommunicationPhase2Error("Anket için en az bir soru gereklidir.")

    start_at = _parse_datetime_value(start_at_raw)
    end_at = _parse_datetime_value(end_at_raw)
    if start_at and end_at and end_at <= start_at:
        raise CommunicationPhase2Error("Bitiş tarihi başlangıç tarihinden sonra olmalıdır.")

    survey.title = title
    survey.description = safe_str(description) or None
    survey.survey_type = safe_str(survey_type) or "kurum_ici"
    survey.is_anonymous = bool(is_anonymous)
    survey.allow_multiple_submissions = bool(allow_multiple_submissions)
    survey.start_at = start_at
    survey.end_at = end_at
    survey.status = "published" if publish_now else "draft"
    if publish_now and not survey.start_at:
        survey.start_at = _now()

    assignment_rows = _assignment_rows_from_target_text(target_type, target_values_text)
    _replace_survey_questions(survey, questions_payload)
    _replace_survey_assignments(survey, assignment_rows)

    db.session.add(survey)
    db.session.commit()
    return survey


def duplicate_survey(survey_id: int, actor_user_id: int) -> Survey:
    survey = db.session.get(Survey, survey_id)
    if not survey:
        raise CommunicationPhase2Error("Anket bulunamadı.")

    copy_row = Survey(
        title=f"{safe_str(getattr(survey, 'title', 'Anket'))} (Kopya)",
        description=safe_str(getattr(survey, 'description', '')) or None,
        survey_type=safe_str(getattr(survey, 'survey_type', '')) or 'kurum_ici',
        created_by_user_id=actor_user_id,
        is_anonymous=bool(getattr(survey, 'is_anonymous', False)),
        allow_multiple_submissions=bool(getattr(survey, 'allow_multiple_submissions', False)),
        status='draft',
        start_at=None,
        end_at=None,
    )
    db.session.add(copy_row)
    db.session.flush()

    _create_survey_questions(copy_row.id, _question_payloads_from_survey(survey))
    for target_type, target_value in _assignment_rows_for_survey(survey):
        db.session.add(
            SurveyAssignment(
                survey_id=copy_row.id,
                target_type=target_type,
                target_value=target_value,
            )
        )

    db.session.commit()
    return copy_row


def archive_survey(survey_id: int) -> Survey:
    survey = db.session.get(Survey, survey_id)
    if not survey:
        raise CommunicationPhase2Error("Anket bulunamadı.")
    survey.status = 'archived'
    db.session.add(survey)
    db.session.commit()
    return survey


def reopen_survey(survey_id: int) -> Survey:
    survey = db.session.get(Survey, survey_id)
    if not survey:
        raise CommunicationPhase2Error("Anket bulunamadı.")
    survey.status = 'draft'
    survey.end_at = None
    db.session.add(survey)
    db.session.commit()
    return survey


def survey_manager_snapshot(limit: int = 50) -> dict[str, Any]:
    rows = Survey.query.order_by(Survey.updated_at.desc(), Survey.id.desc()).limit(limit).all()
    counts = Counter((safe_str(getattr(row, "status", "draft")) or "draft") for row in rows)
    enriched = []
    for row in rows:
        summary = _survey_completion_summary(row)
        enriched.append(
            {
                "survey": row,
                "question_count": row.questions.count() if hasattr(row.questions, "count") else len(row.questions),
                "assignment_count": row.assignments.count() if hasattr(row.assignments, "count") else len(row.assignments),
                "response_count": row.responses.count() if hasattr(row.responses, "count") else len(row.responses),
                "summary": summary,
            }
        )
    return {"rows": enriched, "counts": counts}


def survey_detail_payload(survey_id: int) -> dict[str, Any]:
    survey = db.session.get(Survey, survey_id)
    if not survey:
        raise CommunicationPhase2Error("Anket bulunamadı.")
    reminders = CommunicationSurveyReminderLog.query.filter_by(survey_id=survey.id).order_by(CommunicationSurveyReminderLog.sent_at.desc(), CommunicationSurveyReminderLog.id.desc()).limit(20).all()
    return {
        "survey": survey,
        "questions": survey.questions.order_by(SurveyQuestion.sort_order.asc()).all(),
        "assignments": survey.assignments.order_by(SurveyAssignment.id.asc()).all(),
        "responses": survey.responses.order_by(SurveyResponse.submitted_at.desc().nullslast(), SurveyResponse.id.desc()).limit(25).all(),
        "summary": _survey_completion_summary(survey),
        "reminders": reminders,
        "can_edit": survey.responses.count() == 0 and safe_str(getattr(survey, "status", "")) != "archived",
    }


def survey_results_snapshot(survey_id: int) -> dict[str, Any]:
    survey = db.session.get(Survey, survey_id)
    if not survey:
        raise CommunicationPhase2Error("Anket bulunamadı.")

    responses = survey.responses.all()
    completed = [row for row in responses if bool(getattr(row, "is_completed", False))]
    summary = _survey_completion_summary(survey)
    reminder_count = CommunicationSurveyReminderLog.query.filter_by(survey_id=survey.id).count()

    question_summaries = []
    for question in survey.questions.order_by(SurveyQuestion.sort_order.asc()).all():
        answers = question.answers.all()
        option_counter: dict[str, int] = defaultdict(int)
        text_answers: list[str] = []

        for answer in answers:
            selected_option = getattr(answer, "selected_option", None)
            if selected_option is not None:
                option_counter[safe_str(getattr(selected_option, "option_text", "-"))] += 1
            else:
                raw = safe_str(getattr(answer, "answer_text", "")) or safe_str(getattr(answer, "answer_value", ""))
                if raw:
                    text_answers.append(raw)
                    option_counter[raw] += 1

        question_summaries.append(
            {
                "question": question,
                "answer_count": len(answers),
                "distribution": sorted(option_counter.items(), key=lambda item: (-item[1], item[0].lower())),
                "text_answers": text_answers[:20],
            }
        )

    return {
        "survey": survey,
        "response_total": len(responses),
        "completed_total": len(completed),
        "completion_rate": summary["completion_rate"],
        "target_total": summary["target_total"],
        "pending_total": summary["pending_total"],
        "reminder_count": reminder_count,
        "question_summaries": question_summaries,
    }


def phase2_dashboard_snapshot() -> dict[str, Any]:
    survey_rows = Survey.query.order_by(Survey.updated_at.desc()).limit(6).all()
    template_count = CommunicationSurveyTemplate.query.count()
    revision_count = CommunicationBulletinRevision.query.count()
    published_surveys = Survey.query.filter_by(status="published").count()
    draft_surveys = Survey.query.filter_by(status="draft").count()

    return {
        "stats": {
            "templates": template_count,
            "bulletin_revisions": revision_count,
            "published_surveys": published_surveys,
            "draft_surveys": draft_surveys,
        },
        "latest_surveys": survey_rows,
        "latest_templates": CommunicationSurveyTemplate.query.order_by(CommunicationSurveyTemplate.updated_at.desc()).limit(6).all(),
        "latest_revisions": CommunicationBulletinRevision.query.order_by(CommunicationBulletinRevision.created_at.desc()).limit(8).all(),
        "survey_status_labels": SURVEY_STATUS_LABELS,
        "survey_type_labels": SURVEY_TYPE_LABELS,
        "bulletin_status_labels": BULLETIN_STATUS_LABELS,
        "bulletin_priority_labels": BULLETIN_PRIORITY_LABELS,
    }
