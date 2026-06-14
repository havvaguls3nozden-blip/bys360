from __future__ import annotations

from datetime import datetime, timezone
from statistics import mean
from typing import Any

from flask import current_app
from sqlalchemy.exc import IntegrityError

# BYS360 V1E: emergency runtime recovery for the Phase2Y wildcard-import regression.
# This deliberately restores the shared mobile contract first; explicit imports can be
# reintroduced later only after a per-file F821 gate and smoke test.
from app.api.mobile.shared import (
    datetime,
    timezone,
    hashlib,
    wraps,
    mean,
    Any,
    current_app,
    jsonify,
    make_response,
    request,
    BadSignature,
    SignatureExpired,
    URLSafeTimedSerializer,
    func,
    or_,
    IntegrityError,
    db,
    notify_support_ticket_comment,
    notify_support_ticket_created,
    get_default_first_login_password,
    AIRecommendation,
    AIRequestLog,
    EvaluationAssignment,
    FeedbackCampaign,
    MessageThread,
    MessageThreadParticipant,
    ModuleSetting,
    Notification,
    PerformanceEvaluation,
    PerformancePeriod,
    PerformancePresidentApproval,
    PerformanceResultSnapshot,
    RoleMenuDefault,
    SupportTicket,
    SupportTicketAttachment,
    SupportTicketMessage,
    SupportTicketStatusHistory,
    Survey,
    SurveyAnswer,
    SurveyAssignment,
    SurveyQuestion,
    SurveyQuestionOption,
    SurveyResponse,
    SystemSetting,
    User,
    mobile_api_bp,
    mobile_login_response,
    mobile_refresh_response,
    mobile_me_response,
    _TOKEN_SALT,
    _REFRESH_TOKEN_SALT,
    _MOBILE_ACCESS_MAX_AGE_SECONDS,
    _MOBILE_REFRESH_MAX_AGE_SECONDS,
    _GLOBAL_ROLES,
    _serializer,
    _role_key,
    _has_global_scope,
    _full_name,
    _safe_count,
    _safe_scalar,
    _as_int,
    _item,
    _metric,
    _module_payload,
    _dt_label,
    _size_label,
    _clean_mobile_text,
    _generate_mobile_ticket_no,
    _user_unit_name,
    _user_org_unit_id,
    _can_mobile_view_ticket,
    _can_mobile_reply_ticket,
    _ticket_detail_payload,
    _SURVEY_ACTIVE_STATUSES,
    _SURVEY_QUESTION_TYPE_LABELS,
    _survey_status_label,
    _survey_is_active,
    _survey_user_target_values,
    _mobile_survey_assignments_for_user,
    _mobile_survey_assignment_for_user,
    _mobile_survey_visible,
    _mobile_survey_anonymous_token,
    _mobile_survey_completed,
    _mobile_survey_options,
    _mobile_survey_questions,
    _mobile_survey_question_payload,
    _mobile_survey_detail_payload,
    _mobile_survey_answer_value,
    _mobile_survey_validate_answers,
    _issue_token,
    _issue_refresh_token,
    _load_refresh_token_user,
    _load_token_user,
    require_mobile_user,
    _bys360_mobile_preview_allowed_origin,
    _bys360_mobile_preview_apply_cors,
    _bys360_mobile_preview_preflight,
    _bys360_mobile_preview_after_request,
    PerformanceTarget,
)

@mobile_api_bp.get("/dashboard/summary")
@require_mobile_user
def mobile_dashboard_summary(*args, **kwargs):
    """P1.4C service delegate wrapper; URL/endpoint/decorator korunur."""
    from app.api.mobile.services.dashboard_service import mobile_dashboard_summary_delegate
    return mobile_dashboard_summary_delegate(_bys360_legacy_mobile_dashboard_summary, *args, **kwargs)

def _bys360_legacy_mobile_dashboard_summary(user: User):
    from app.api.mobile.services.dashboard_service import delegate_mobile_dashboard_summary
    return delegate_mobile_dashboard_summary(_bys360_legacy_mobile_dashboard_summary, user)

def _bys360_legacy_mobile_dashboard_summary(user: User):
    global_scope = _has_global_scope(user)
    pending_assignments_q = EvaluationAssignment.query.filter(EvaluationAssignment.evaluator_id == user.id)
    try:
        pending_assignments_q = pending_assignments_q.filter(~EvaluationAssignment.status.in_(["tamamlandi", "tamamlandı", "completed", "done"]))
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/api/mobile/routes.py:687)")

    open_tickets_q = SupportTicket.query
    if not global_scope:
        open_tickets_q = open_tickets_q.filter(SupportTicket.created_by_user_id == user.id)
    try:
        open_tickets_q = open_tickets_q.filter(~SupportTicket.status.in_(["closed", "kapali", "kapalı", "resolved"]))
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/api/mobile/routes.py:695)")

    unread_messages = 0
    try:
        unread_messages = MessageThreadParticipant.query.filter(
            MessageThreadParticipant.user_id == user.id,
            MessageThreadParticipant.left_at.is_(None),
        ).count()
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/api/mobile/domains/dashboard.py:44")
        unread_messages = 0

    active_goals = 0
    kpi_success_rate = 0
    if PerformanceTarget is not None:
        try:
            target_q = PerformanceTarget.query
            active_goals = target_q.filter(PerformanceTarget.status.in_(["active", "ongoing", "devam", "devam_ediyor"])).count()
            rates = [float(x[0] or 0) for x in db.session.query(PerformanceTarget.completion_rate).filter(PerformanceTarget.completion_rate.isnot(None)).limit(200).all()]
            kpi_success_rate = int(mean(rates)) if rates else 0
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/api/mobile/domains/dashboard.py:55")
            active_goals = 0
            kpi_success_rate = 0

    return jsonify({
        "user_name": _full_name(user),
        "pending_performance": _safe_count(pending_assignments_q),
        "unread_notifications": _safe_count(Notification.query.filter_by(user_id=user.id, is_read=False)),
        "open_tickets": _safe_count(open_tickets_q),
        "assigned_surveys": _survey_count_for_user(user),
        "kpi_success_rate": kpi_success_rate,
        "pending_approvals": _safe_count(PerformancePresidentApproval.query.filter_by(status="pending")) if global_scope else 0,
        "active_personnel": _safe_count(User.query.filter_by(is_active=True)) if global_scope else 1,
        "unread_messages": unread_messages,
        "ai_alerts": _safe_count(AIRecommendation.query.filter(AIRecommendation.status.in_(["open", "pending", "active"]))) if global_scope else 0,
        "active_goals": active_goals,
        "certificates": 0,
    })


def _survey_count_for_user(user: User) -> int:
    try:
        count = 0
        seen: set[int] = set()
        for assignment in _mobile_survey_assignments_for_user(user):
            survey = getattr(assignment, "survey", None)
            if not survey:
                continue
            sid = int(getattr(survey, "id", 0) or 0)
            if not sid or sid in seen:
                continue
            seen.add(sid)
            if _survey_is_active(survey) and (bool(getattr(survey, "allow_multiple_submissions", False)) or not _mobile_survey_completed(user, survey)):
                count += 1
        return count
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/api/mobile/domains/dashboard.py:90")
        return 0

