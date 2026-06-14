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
)

@mobile_api_bp.post("/auth/login")
def mobile_login():
    from app.api.mobile.services.auth_service import delegate_mobile_login
    return delegate_mobile_login(_bys360_legacy_mobile_login)

def _bys360_legacy_mobile_login():
    return mobile_login_response(_issue_token, _issue_refresh_token, _full_name)


@mobile_api_bp.post("/auth/refresh")
def mobile_refresh():
    from app.api.mobile.services.auth_service import delegate_mobile_refresh
    return delegate_mobile_refresh(_bys360_legacy_mobile_refresh)

def _bys360_legacy_mobile_refresh():
    data = request.get_json(silent=True) or {}
    refresh_token = data.get("refresh_token") or data.get("refreshToken")
    return mobile_refresh_response(refresh_token, _load_refresh_token_user, _issue_token, _issue_refresh_token, _full_name)


@mobile_api_bp.get("/me")
@require_mobile_user
def mobile_me(user: User):
    from app.api.mobile.services.auth_service import delegate_mobile_me
    return delegate_mobile_me(_bys360_legacy_mobile_me, user)

def _bys360_legacy_mobile_me(user: User):
    return mobile_me_response(user, _module_payload, _metric, _item, _full_name)

