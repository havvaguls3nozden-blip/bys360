"""BYS360 Assistant V2 -- thin read adapters.

One function per "NO EXISTING SERVICE" capability registered in
`app.services.assistant_v2.capability_registry`. Every function here follows
the same shared conventions (Phase 19 / Phase 20 mandates referenced in the
task brief this package was built from):

  - Takes the current authenticated `user` object as its first argument
    (even when the read is not self-scoped) plus whatever narrow input
    fields the capability needs. This keeps every adapter's call signature
    uniform for a future router/dispatcher layer.
  - Does NOT perform its own authorization check. The router/handler layer
    (not built in this slice) is responsible for calling
    `app.route_support.can_access_menu(user, capability.permission_key)` (or
    the documented `auth_override` for the three exceptions) BEFORE calling
    any function here. A function here only self-scopes a query to the
    given `user` where the capability is inherently "my own data" (comment
    on each such function says so explicitly).
  - Every query is wrapped in a narrow `try/except Exception` that logs via
    `current_app.logger.exception(...)` and returns a controlled, typed
    empty/None result on failure. No bare `except Exception: pass` anywhere
    in this file (explicitly forbidden -- Phase 19).
  - Every LIST/SEARCH/SUMMARIZE-over-a-window function applies a bounded
    LIMIT via `_clamp_limit(...)` -- never an unbounded query (Phase 20).
  - Returns a plain dict or list-of-dicts (JSON-safe: no live model
    instances, no lazy-loaded relationships left un-evaluated) unless noted
    otherwise.

Every model field referenced here was verified against the real model
definitions in `app/models/*.py` before being used (see
`app.services.assistant_v2.capability_registry`'s per-capability `evidence`
field for the exact file:line citations).
"""
from __future__ import annotations

import os
from datetime import date, datetime
from typing import Any

from flask import current_app
from sqlalchemy import func, or_

from app.extensions import db

_DEFAULT_LIMIT = 25
_MAX_LIMIT = 100


def _clamp_limit(limit: Any, default: int = _DEFAULT_LIMIT, max_limit: int = _MAX_LIMIT) -> int:
    """Coerce a caller-supplied limit into a safe, bounded integer.

    Never trusts the caller: a missing, non-numeric, zero, or negative
    value falls back to `default`; anything above `max_limit` is clamped
    down. This is the one place every LIST/SEARCH function below routes
    its limit through, so no adapter can accidentally dump an unbounded
    table (Phase 20)."""
    try:
        value = int(limit) if limit is not None else default
    except (TypeError, ValueError):
        value = default
    if value <= 0:
        value = default
    return max(1, min(value, max_limit))


def _iso(value: datetime | date | None) -> str | None:
    return value.isoformat() if value is not None else None


def _user_id(user: Any) -> int | None:
    raw = getattr(user, "id", None)
    try:
        return int(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# personnel_hr
# ---------------------------------------------------------------------------


def personnel_hr_read_personnel_record(user: Any, sicil_no: str) -> dict[str, Any] | None:
    """Single personnel record by sicil_no. Field selection mirrors the
    already-shipped app.services.personnel.list_query.build_personnel_list_row."""
    try:
        from app.models import User
        from app.services.personnel.list_query import build_personnel_list_row

        record = User.query.filter_by(sicil_no=sicil_no).first()
        if record is None:
            return None
        return build_personnel_list_row(record)
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.personnel_hr_read_personnel_record failed")
        return None


def personnel_hr_list_personnel(user: Any, *, limit: int = _DEFAULT_LIMIT, birim: str | None = None) -> list[dict[str, Any]]:
    """Active-scope personnel rows (admin role excluded), same base query as
    the live personnel list screen."""
    try:
        from app.models import User
        from app.services.personnel.list_query import (
            build_personnel_list_base_query,
            build_personnel_list_rows,
        )

        query = build_personnel_list_base_query(User)
        if birim:
            query = query.filter(User.birim == birim)
        rows = query.order_by(User.ad.asc(), User.soyad.asc()).limit(_clamp_limit(limit)).all()
        return build_personnel_list_rows(rows)
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.personnel_hr_list_personnel failed")
        return []


def personnel_hr_list_pending_leave_requests(user: Any, *, limit: int = _DEFAULT_LIMIT) -> list[dict[str, Any]]:
    """Leave requests with status='bekliyor' (confirmed real pending value
    against app/templates/hr_leave.html)."""
    try:
        from app.models.hr_models import PersonnelLeave

        rows = (
            PersonnelLeave.query.filter(PersonnelLeave.status == "bekliyor")
            .order_by(PersonnelLeave.start_date.desc())
            .limit(_clamp_limit(limit))
            .all()
        )
        return [
            {
                "id": r.id,
                "user_id": r.user_id,
                "leave_type": r.leave_type,
                "status": r.status,
                "start_date": _iso(r.start_date),
                "end_date": _iso(r.end_date),
                "approved_day_count": r.approved_day_count,
            }
            for r in rows
        ]
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.personnel_hr_list_pending_leave_requests failed")
        return []


# ---------------------------------------------------------------------------
# performance_mgmt
# ---------------------------------------------------------------------------


def performance_mgmt_list_active_periods(user: Any, *, limit: int = _DEFAULT_LIMIT) -> list[dict[str, Any]]:
    try:
        from app.models.performance_models import PerformancePeriod

        rows = (
            PerformancePeriod.query.filter(PerformancePeriod.is_active.is_(True))
            .order_by(PerformancePeriod.start_date.desc())
            .limit(_clamp_limit(limit))
            .all()
        )
        return [
            {
                "id": p.id,
                "title": p.title,
                "period_type": p.period_type,
                "start_date": _iso(p.start_date),
                "end_date": _iso(p.end_date),
                "results_published": bool(p.results_published),
            }
            for p in rows
        ]
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.performance_mgmt_list_active_periods failed")
        return []


def performance_mgmt_read_period_summary(user: Any, period_id: int) -> dict[str, Any] | None:
    try:
        from app.models.performance_models import PerformanceEvaluation, PerformancePeriod

        period = db.session.get(PerformancePeriod, period_id)
        if period is None:
            return None
        evaluation_count = PerformanceEvaluation.query.filter(PerformanceEvaluation.period_id == period_id).count()
        return {
            "id": period.id,
            "title": period.title,
            "period_type": period.period_type,
            "start_date": _iso(period.start_date),
            "end_date": _iso(period.end_date),
            "is_active": bool(period.is_active),
            "results_published": bool(period.results_published),
            "evaluation_count": evaluation_count,
        }
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.performance_mgmt_read_period_summary failed")
        return None


def performance_mgmt_list_incomplete_evaluations(user: Any, *, period_id: int, limit: int = _DEFAULT_LIMIT) -> list[dict[str, Any]]:
    """Per-person evaluation rows for one period where status != 'tamamlandi'
    (the real "completed" value used throughout this codebase, e.g.
    app/performance/publish_helpers.py:18). Returns employee_id (FK to
    users.id) plus status -- deliberately no score/comment fields, since
    this is meant for cross-module intersection (see
    cross_module_orchestrator.py), not for displaying evaluation content."""
    try:
        from app.models.performance_models import PerformanceEvaluation

        rows = (
            PerformanceEvaluation.query.filter(
                PerformanceEvaluation.period_id == period_id,
                PerformanceEvaluation.status != "tamamlandi",
            )
            .order_by(PerformanceEvaluation.employee_id.asc())
            .limit(_clamp_limit(limit))
            .all()
        )
        return [{"employee_id": e.employee_id, "status": e.status} for e in rows]
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.performance_mgmt_list_incomplete_evaluations failed")
        return []


def performance_mgmt_summarize_evaluation_completion(user: Any, period_id: int) -> dict[str, int]:
    try:
        from app.models.performance_models import PerformanceEvaluation

        rows = (
            db.session.query(PerformanceEvaluation.status, func.count(PerformanceEvaluation.id))
            .filter(PerformanceEvaluation.period_id == period_id)
            .group_by(PerformanceEvaluation.status)
            .all()
        )
        return {str(status): int(count) for status, count in rows}
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.performance_mgmt_summarize_evaluation_completion failed")
        return {}


# ---------------------------------------------------------------------------
# portal
# ---------------------------------------------------------------------------


def portal_read_post_detail(user: Any, post_id: int) -> dict[str, Any] | None:
    try:
        from app.models.portal_models import PortalPost
        from app.services.portal_service import can_user_view_post

        post = db.session.get(PortalPost, post_id)
        if post is None:
            return None
        if not can_user_view_post(user, post):
            return None
        return {
            "id": post.id,
            "title": post.title,
            "body": post.body,
            "post_type": post.post_type,
            "status": post.status,
            "published_at": _iso(post.published_at),
            "author_user_id": post.author_user_id,
        }
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.portal_read_post_detail failed")
        return None


def portal_list_flagged_posts_for_moderation(user: Any, *, limit: int = _DEFAULT_LIMIT) -> list[dict[str, Any]]:
    try:
        from app.models.portal_models import PortalPostReport

        rows = (
            PortalPostReport.query.filter(PortalPostReport.status == "open")
            .order_by(PortalPostReport.created_at.desc())
            .limit(_clamp_limit(limit))
            .all()
        )
        return [
            {
                "id": r.id,
                "post_id": r.post_id,
                "reporter_user_id": r.reporter_user_id,
                "reason": r.reason,
                "status": r.status,
                "created_at": _iso(r.created_at),
            }
            for r in rows
        ]
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.portal_list_flagged_posts_for_moderation failed")
        return []


# ---------------------------------------------------------------------------
# file_center (auth_override -- see capability_registry module docstring)
# ---------------------------------------------------------------------------


def file_center_read_quota_status(user: Any) -> dict[str, Any] | None:
    try:
        from app.models.file_center_models import FileQuotaPolicy, FileQuotaUsage

        policy = FileQuotaPolicy.query.filter_by(scope_type="global", is_active=True).first()
        total_bytes, total_files = (
            db.session.query(
                func.coalesce(func.sum(FileQuotaUsage.used_bytes), 0),
                func.coalesce(func.sum(FileQuotaUsage.file_count), 0),
            ).first()
            or (0, 0)
        )
        return {
            "policy_label": policy.label if policy else None,
            "max_storage_gb": policy.max_storage_gb if policy else None,
            "warning_threshold_percent": policy.warning_threshold_percent if policy else None,
            "total_used_bytes": int(total_bytes or 0),
            "total_file_count": int(total_files or 0),
        }
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.file_center_read_quota_status failed")
        return None


def file_center_list_recent_security_scans(user: Any, *, limit: int = _DEFAULT_LIMIT) -> list[dict[str, Any]]:
    try:
        from app.models.file_center_models import FileSecurityScan

        rows = (
            FileSecurityScan.query.order_by(FileSecurityScan.created_at.desc())
            .limit(_clamp_limit(limit))
            .all()
        )
        return [
            {
                "id": r.id,
                "file_id": r.file_id,
                "status": r.status,
                "scanner": r.scanner,
                "scanned_at": _iso(r.scanned_at),
            }
            for r in rows
        ]
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.file_center_list_recent_security_scans failed")
        return []


def file_center_explain_role_matrix(user: Any) -> list[dict[str, Any]]:
    try:
        from app.models.file_center_models import FileCenterRolePermission

        rows = (
            FileCenterRolePermission.query.filter_by(is_active=True)
            .order_by(FileCenterRolePermission.role_key.asc())
            .limit(_MAX_LIMIT)
            .all()
        )
        return [
            {
                "role_key": r.role_key,
                "role_label": r.role_label,
                "can_upload_files": bool(r.can_upload_files),
                "can_download_files": bool(r.can_download_files),
                "can_create_guest_links": bool(r.can_create_guest_links),
                "can_manage_settings": bool(r.can_manage_settings),
                "can_manage_security": bool(r.can_manage_security),
            }
            for r in rows
        ]
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.file_center_explain_role_matrix failed")
        return []


# ---------------------------------------------------------------------------
# communication
# ---------------------------------------------------------------------------


def communication_list_active_announcements(user: Any, *, limit: int = _DEFAULT_LIMIT) -> list[dict[str, Any]]:
    try:
        from app.models.announcement_popup_models import Announcement

        rows = (
            Announcement.query.filter(Announcement.is_active.is_(True))
            .order_by(Announcement.created_at.desc())
            .limit(_clamp_limit(limit))
            .all()
        )
        return [
            {
                "id": a.id,
                "title": a.title,
                "announcement_type": a.announcement_type,
                "publish_start_at": _iso(a.publish_start_at),
                "publish_end_at": _iso(a.publish_end_at),
            }
            for a in rows
        ]
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.communication_list_active_announcements failed")
        return []


def communication_summarize_my_unread_messages(user: Any) -> dict[str, int]:
    """Self-scoped: counts, for the GIVEN user only, message threads where
    the thread has a newer last_message_at than the participant's own
    last_read_at."""
    try:
        from app.models.communication_models import MessageThread, MessageThreadParticipant

        uid = _user_id(user)
        if uid is None:
            return {"unread_thread_count": 0}
        unread_count = (
            db.session.query(func.count(MessageThreadParticipant.id))
            .join(MessageThread, MessageThread.id == MessageThreadParticipant.thread_id)
            .filter(
                MessageThreadParticipant.user_id == uid,
                MessageThreadParticipant.left_at.is_(None),
                MessageThread.last_message_at.isnot(None),
                or_(
                    MessageThreadParticipant.last_read_at.is_(None),
                    MessageThreadParticipant.last_read_at < MessageThread.last_message_at,
                ),
            )
            .scalar()
        )
        return {"unread_thread_count": int(unread_count or 0)}
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.communication_summarize_my_unread_messages failed")
        return {"unread_thread_count": 0}


def communication_read_announcement_detail(user: Any, announcement_id: int) -> dict[str, Any] | None:
    try:
        from app.models.announcement_popup_models import Announcement

        a = db.session.get(Announcement, announcement_id)
        if a is None or not a.is_active:
            return None
        return {
            "id": a.id,
            "title": a.title,
            "body": a.body,
            "announcement_type": a.announcement_type,
            "publish_start_at": _iso(a.publish_start_at),
            "publish_end_at": _iso(a.publish_end_at),
        }
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.communication_read_announcement_detail failed")
        return None


# ---------------------------------------------------------------------------
# surveys
# ---------------------------------------------------------------------------


def surveys_list_active_surveys_for_management(user: Any, *, limit: int = _DEFAULT_LIMIT) -> list[dict[str, Any]]:
    try:
        from app.models.communication_models import Survey

        rows = (
            Survey.query.filter(Survey.status == "published")
            .order_by(Survey.created_at.desc())
            .limit(_clamp_limit(limit))
            .all()
        )
        return [
            {
                "id": s.id,
                "title": s.title,
                "survey_type": s.survey_type,
                "start_at": _iso(s.start_at),
                "end_at": _iso(s.end_at),
                "is_anonymous": bool(s.is_anonymous),
            }
            for s in rows
        ]
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.surveys_list_active_surveys_for_management failed")
        return []


# ---------------------------------------------------------------------------
# support_help
# ---------------------------------------------------------------------------


def support_help_list_my_tickets(user: Any, *, limit: int = _DEFAULT_LIMIT) -> list[dict[str, Any]]:
    """Self-scoped to the given user's own created tickets."""
    try:
        from app.models.support_models import SupportTicket

        uid = _user_id(user)
        if uid is None:
            return []
        rows = (
            SupportTicket.query.filter(SupportTicket.created_by_user_id == uid)
            .order_by(SupportTicket.created_at.desc())
            .limit(_clamp_limit(limit))
            .all()
        )
        return [
            {
                "id": t.id,
                "ticket_no": t.ticket_no,
                "title": t.title,
                "status": t.status,
                "priority": t.priority,
                "created_at": _iso(t.created_at),
            }
            for t in rows
        ]
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.support_help_list_my_tickets failed")
        return []


def support_help_read_ticket_detail(user: Any, ticket_id: int) -> dict[str, Any] | None:
    """Self-scoped: only returns the ticket if the given user is its
    creator or its assignee."""
    try:
        from app.models.support_models import SupportTicket

        uid = _user_id(user)
        t = db.session.get(SupportTicket, ticket_id)
        if t is None:
            return None
        if uid is None or (t.created_by_user_id != uid and t.assigned_to_user_id != uid):
            return None
        return {
            "id": t.id,
            "ticket_no": t.ticket_no,
            "title": t.title,
            "description": t.description,
            "status": t.status,
            "priority": t.priority,
            "created_at": _iso(t.created_at),
            "closed_at": _iso(t.closed_at),
        }
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.support_help_read_ticket_detail failed")
        return None


def support_help_search_help_center_articles(user: Any, query: str, *, limit: int = 20) -> list[dict[str, Any]]:
    try:
        from app.models.support_models import SupportHelpArticle

        text = (query or "").strip()
        base = SupportHelpArticle.query.filter(SupportHelpArticle.is_published.is_(True))
        if text:
            like = f"%{text}%"
            base = base.filter(or_(SupportHelpArticle.title.ilike(like), SupportHelpArticle.summary.ilike(like)))
        rows = base.order_by(SupportHelpArticle.sort_order.asc()).limit(_clamp_limit(limit, default=20, max_limit=50)).all()
        return [
            {
                "id": a.id,
                "slug": a.slug,
                "title": a.title,
                "summary": a.summary,
                "category_slug": a.category_slug,
            }
            for a in rows
        ]
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.support_help_search_help_center_articles failed")
        return []


# ---------------------------------------------------------------------------
# ai_decision_support
# ---------------------------------------------------------------------------


def ai_decision_support_list_open_recommendations(user: Any, *, limit: int = _DEFAULT_LIMIT) -> list[dict[str, Any]]:
    try:
        from app.models.ai_models import AIRecommendation

        rows = (
            AIRecommendation.query.filter(AIRecommendation.status == "open")
            .order_by(AIRecommendation.created_at.desc())
            .limit(_clamp_limit(limit))
            .all()
        )
        return [
            {
                "id": r.id,
                "module_type": r.module_type,
                "recommendation_type": r.recommendation_type,
                "title": r.title,
                "severity": r.severity,
                "created_at": _iso(r.created_at),
            }
            for r in rows
        ]
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.ai_decision_support_list_open_recommendations failed")
        return []


def ai_decision_support_summarize_usage(user: Any, *, sample_size: int = 200) -> dict[str, dict[str, int]]:
    """Groups the most recent `sample_size` AI request log rows by
    provider_name and status. The bound is on the sample window, not on
    the whole table."""
    try:
        from app.models.ai_models import AIRequestLog

        bounded = _clamp_limit(sample_size, default=200, max_limit=500)
        subq = AIRequestLog.query.order_by(AIRequestLog.created_at.desc()).limit(bounded).subquery()
        rows = db.session.query(subq.c.provider_name, subq.c.status, func.count()).group_by(subq.c.provider_name, subq.c.status).all()
        summary: dict[str, dict[str, int]] = {}
        for provider_name, status, count in rows:
            key = provider_name or "unknown"
            summary.setdefault(key, {})[str(status)] = int(count)
        return summary
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.ai_decision_support_summarize_usage failed")
        return {}


# ---------------------------------------------------------------------------
# virtual_assistant
# ---------------------------------------------------------------------------


def virtual_assistant_discover_available_modules(user: Any) -> list[dict[str, Any]]:
    """Self-describing: enumerates active modules from module_registry and
    whether THIS user can currently see each one's anchor_menu_key (when it
    has one). Does not itself grant access to anything."""
    try:
        from app.route_support import can_access_menu
        from app.services.settings.module_registry import list_active_modules

        result: list[dict[str, Any]] = []
        for m in list_active_modules():
            visible = True
            if m.anchor_menu_key:
                try:
                    visible = bool(can_access_menu(user, m.anchor_menu_key))
                except Exception:
                    current_app.logger.exception(
                        "assistant_v2 read_adapters.virtual_assistant_discover_available_modules: "
                        "can_access_menu failed for module_key=%s",
                        m.module_key,
                    )
                    visible = False
            result.append(
                {
                    "module_key": m.module_key,
                    "display_name": m.display_name,
                    "description": m.description,
                    "module_type": m.module_type,
                    "is_visible_to_user": visible,
                }
            )
        return result
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.virtual_assistant_discover_available_modules failed")
        return []


def virtual_assistant_discover_my_capabilities(user: Any) -> list[dict[str, Any]]:
    """Self-describing: enumerates this same capability registry and
    computes, per capability, whether THIS user could currently invoke it --
    using the exact same authorization mechanisms a real router would use
    (menu-key resolution for permission_key capabilities, the two documented
    auth_override checks, always-available for self-describing entries)."""
    try:
        from app.file_center.permissions import can_manage_file_center_settings
        from app.route_support import ADMIN_FAMILY_ROLES, can_access_menu, user_has_any_role
        from app.services.assistant_v2.capability_registry import list_active_capabilities

        out: list[dict[str, Any]] = []
        for cap in list_active_capabilities():
            available = False
            try:
                if cap.is_self_describing:
                    available = True
                elif cap.permission_key:
                    available = bool(can_access_menu(user, cap.permission_key))
                elif cap.extra.get("auth_override") == "app.file_center.permissions.can_manage_file_center_settings":
                    available = bool(can_manage_file_center_settings(user))
                elif cap.extra.get("auth_override") == "admin_required_role_family":
                    available = bool(user_has_any_role(user, ADMIN_FAMILY_ROLES))
            except Exception:
                current_app.logger.exception(
                    "assistant_v2 read_adapters.virtual_assistant_discover_my_capabilities: "
                    "authorization check failed for capability_key=%s",
                    cap.capability_key,
                )
                available = False
            out.append(
                {
                    "capability_key": cap.capability_key,
                    "module_key": cap.module_key,
                    "display_name": cap.display_name,
                    "operation_type": cap.operation_type,
                    "is_available": available,
                }
            )
        return out
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.virtual_assistant_discover_my_capabilities failed")
        return []


# ---------------------------------------------------------------------------
# dashboard
# ---------------------------------------------------------------------------


def dashboard_explain_module(user: Any) -> dict[str, Any] | None:
    try:
        from app.services.settings.module_registry import get_module

        m = get_module("dashboard")
        if m is None:
            return None
        return {
            "module_key": m.module_key,
            "display_name": m.display_name,
            "description": m.description,
            "widget_visibility_note": (
                "Dashboard widget görünürlüğü şu an kod içinde role göre sabittir; "
                "ayrı bir ayar sayfası henüz yok."
            ),
        }
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.dashboard_explain_module failed")
        return None


# ---------------------------------------------------------------------------
# settings_auth
# ---------------------------------------------------------------------------


def settings_auth_list_unit_menu_overrides(user: Any, unit_name: str, *, limit: int = 50) -> list[dict[str, Any]]:
    try:
        from app.models.settings_models import UnitMenuProfile

        rows = (
            UnitMenuProfile.query.filter(UnitMenuProfile.unit_name == unit_name)
            .order_by(UnitMenuProfile.menu_key.asc())
            .limit(_clamp_limit(limit, default=50, max_limit=100))
            .all()
        )
        return [
            {
                "unit_name": r.unit_name,
                "menu_key": r.menu_key,
                "is_visible": bool(r.is_visible),
                "source_type": r.source_type,
            }
            for r in rows
        ]
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.settings_auth_list_unit_menu_overrides failed")
        return []


def settings_auth_summarize_role_permission_coverage(user: Any) -> dict[str, int]:
    try:
        from app.models.settings_models import RoleMenuDefault

        rows = (
            db.session.query(RoleMenuDefault.role_name, func.count(RoleMenuDefault.id))
            .filter(RoleMenuDefault.is_visible.is_(True))
            .group_by(RoleMenuDefault.role_name)
            .all()
        )
        return {str(role): int(count) for role, count in rows}
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.settings_auth_summarize_role_permission_coverage failed")
        return {}


# ---------------------------------------------------------------------------
# notifications
# ---------------------------------------------------------------------------


def notifications_list_my_notifications(user: Any, *, limit: int = _DEFAULT_LIMIT) -> list[dict[str, Any]]:
    """Self-scoped to the given user's own notifications."""
    try:
        from app.models.communication_models import Notification

        uid = _user_id(user)
        if uid is None:
            return []
        rows = (
            Notification.query.filter(Notification.user_id == uid)
            .order_by(Notification.created_at.desc())
            .limit(_clamp_limit(limit))
            .all()
        )
        return [
            {
                "id": n.id,
                "title": n.title,
                "notification_type": n.notification_type,
                "priority": n.priority,
                "is_read": bool(n.is_read),
                "created_at": _iso(n.created_at),
            }
            for n in rows
        ]
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.notifications_list_my_notifications failed")
        return []


def notifications_summarize_my_unread_count(user: Any) -> dict[str, int]:
    """Self-scoped to the given user's own unread notifications."""
    try:
        from app.models.communication_models import Notification

        uid = _user_id(user)
        if uid is None:
            return {}
        rows = (
            db.session.query(Notification.priority, func.count(Notification.id))
            .filter(Notification.user_id == uid, Notification.is_read.is_(False))
            .group_by(Notification.priority)
            .all()
        )
        return {str(priority): int(count) for priority, count in rows}
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.notifications_summarize_my_unread_count failed")
        return {}


def notifications_read_notification_detail(user: Any, notification_id: int) -> dict[str, Any] | None:
    """Self-scoped: only returns the notification if it belongs to the
    given user."""
    try:
        from app.models.communication_models import Notification

        uid = _user_id(user)
        n = db.session.get(Notification, notification_id)
        if n is None or uid is None or n.user_id != uid:
            return None
        return {
            "id": n.id,
            "title": n.title,
            "body": n.body,
            "notification_type": n.notification_type,
            "priority": n.priority,
            "is_read": bool(n.is_read),
            "link_url": n.link_url,
            "created_at": _iso(n.created_at),
        }
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.notifications_read_notification_detail failed")
        return None


# ---------------------------------------------------------------------------
# email_automation
# ---------------------------------------------------------------------------


def email_automation_summarize_performance_reminder_health(user: Any, *, sample_size: int = 200) -> dict[str, dict[str, int]]:
    try:
        from app.models.communication_models import MailLog
        from app.services.mail_core import (
            PERFORMANCE_REMINDER_MAIL_TYPE,
            PERFORMANCE_RESULT_MAIL_TYPE,
        )

        bounded = _clamp_limit(sample_size, default=200, max_limit=500)
        subq = (
            MailLog.query.filter(MailLog.mail_type.in_([PERFORMANCE_REMINDER_MAIL_TYPE, PERFORMANCE_RESULT_MAIL_TYPE]))
            .order_by(MailLog.sent_at.desc())
            .limit(bounded)
            .subquery()
        )
        rows = db.session.query(subq.c.mail_type, subq.c.is_success, func.count()).group_by(subq.c.mail_type, subq.c.is_success).all()
        summary: dict[str, dict[str, int]] = {}
        for mail_type, is_success, count in rows:
            bucket = summary.setdefault(str(mail_type), {"success": 0, "failed": 0})
            bucket["success" if is_success else "failed"] += int(count)
        return summary
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.email_automation_summarize_performance_reminder_health failed")
        return {}


# ---------------------------------------------------------------------------
# scheduled_jobs
# ---------------------------------------------------------------------------


def scheduled_jobs_read_feedback_followup_status(user: Any) -> dict[str, Any] | None:
    try:
        raw = os.environ.get("BYS360_FEEDBACK_FOLLOWUP_SCHEDULER", "")
        enabled = raw.strip().lower() in {"1", "true", "yes", "on"}
        return {
            "scheduler_key": "feedback_followup",
            "env_var": "BYS360_FEEDBACK_FOLLOWUP_SCHEDULER",
            "raw_value": raw or None,
            "enabled": enabled,
        }
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.scheduled_jobs_read_feedback_followup_status failed")
        return None


def scheduled_jobs_list_recent_digest_jobs(user: Any, *, limit: int = _DEFAULT_LIMIT) -> list[dict[str, Any]]:
    try:
        from app.models.communication_phase5_models import CommunicationDigestJob

        rows = (
            CommunicationDigestJob.query.order_by(CommunicationDigestJob.created_at.desc())
            .limit(_clamp_limit(limit))
            .all()
        )
        return [
            {
                "id": j.id,
                "user_id": j.user_id,
                "digest_type": j.digest_type,
                "period_label": j.period_label,
                "status": j.status,
                "scheduled_for": _iso(j.scheduled_for),
                "executed_at": _iso(j.executed_at),
            }
            for j in rows
        ]
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.scheduled_jobs_list_recent_digest_jobs failed")
        return []


def scheduled_jobs_summarize_automation_health(user: Any, *, sample_size: int = 200) -> dict[str, int]:
    try:
        from app.models.communication_phase5_models import CommunicationAutomationLog

        bounded = _clamp_limit(sample_size, default=200, max_limit=500)
        subq = (
            CommunicationAutomationLog.query.order_by(CommunicationAutomationLog.executed_at.desc())
            .limit(bounded)
            .subquery()
        )
        rows = db.session.query(subq.c.status, func.count()).group_by(subq.c.status).all()
        return {str(status): int(count) for status, count in rows}
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.scheduled_jobs_summarize_automation_health failed")
        return {}


# ---------------------------------------------------------------------------
# security_session
# ---------------------------------------------------------------------------


def security_session_read_captcha_policy(user: Any) -> dict[str, Any] | None:
    try:
        enabled = bool(current_app.config.get("CAPTCHA_ENABLED", True))
        force_for_unknown = bool(current_app.config.get("LOGIN_FORCE_CAPTCHA_FOR_UNKNOWN_USER", True))
        return {
            "captcha_enabled": enabled,
            "login_force_captcha_for_unknown_user": force_for_unknown,
        }
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.security_session_read_captcha_policy failed")
        return None


# security_session deliberately has only one adapter (see
# capability_registry.py's module docstring / inline comment for why: the
# module is system_critical/critical with no route_endpoint, and even
# seemingly-safe lockout aggregation here is a reconnaissance risk).


# ---------------------------------------------------------------------------
# virtual_assistant: knowledge bank (mandate Phase A/B)
# ---------------------------------------------------------------------------


def virtual_assistant_search_knowledge_bank(user: Any, question: str) -> list[dict[str, Any]]:
    """Thin wrapper around the existing, already-shipped
    app.services.ai_agent.knowledge.search_knowledge_answer -- reused, not
    reimplemented, per this project's own "do not replace with hardcoded
    dictionaries" instruction. That function already: (a) only ever reads
    from list_knowledge_entries(include_inactive=False), i.e. an
    inactive/unapproved entry can never be returned (Phase B), and (b)
    treats question_patterns/answer/tags purely as data for substring/token
    scoring -- it never executes or interprets stored text as instructions.
    This wrapper adds only the bounded limit and the dict-shape this
    project's response_composer already knows how to render (a plain list
    of dicts with a label-priority field)."""
    try:
        from app.services.ai_agent.knowledge import search_knowledge_answer

        text = (question or "").strip()
        if not text:
            return []
        matches = search_knowledge_answer(text, audience="all", limit=3)
        return [
            {
                "title": m.get("title"),
                "answer": m.get("answer"),
                "match_score": m.get("match_score"),
            }
            for m in matches
        ]
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.virtual_assistant_search_knowledge_bank failed")
        return []


# ---------------------------------------------------------------------------
# audit
# ---------------------------------------------------------------------------


def audit_read_change_log_detail(user: Any, change_log_id: int) -> dict[str, Any] | None:
    try:
        from app.models.settings_models import SettingsChangeLog

        row = db.session.get(SettingsChangeLog, change_log_id)
        if row is None:
            return None
        return {
            "id": row.id,
            "change_scope": row.change_scope,
            "action_type": row.action_type,
            "summary": row.summary,
            "actor_user_id": row.actor_user_id,
            "target_user_id": row.target_user_id,
            "target_role_name": row.target_role_name,
            "is_rollback": bool(row.is_rollback),
            "created_at": _iso(row.created_at),
        }
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.audit_read_change_log_detail failed")
        return None


def audit_summarize_recent_change_activity(user: Any, *, sample_size: int = 200) -> dict[str, int]:
    try:
        from app.models.settings_models import SettingsChangeLog

        bounded = _clamp_limit(sample_size, default=200, max_limit=500)
        subq = (
            SettingsChangeLog.query.order_by(SettingsChangeLog.created_at.desc())
            .limit(bounded)
            .subquery()
        )
        rows = db.session.query(subq.c.change_scope, func.count()).group_by(subq.c.change_scope).all()
        return {str(scope): int(count) for scope, count in rows}
    except Exception:
        current_app.logger.exception("assistant_v2 read_adapters.audit_summarize_recent_change_activity failed")
        return {}


__all__ = [
    "personnel_hr_read_personnel_record",
    "personnel_hr_list_personnel",
    "personnel_hr_list_pending_leave_requests",
    "performance_mgmt_list_active_periods",
    "performance_mgmt_read_period_summary",
    "performance_mgmt_list_incomplete_evaluations",
    "performance_mgmt_summarize_evaluation_completion",
    "portal_read_post_detail",
    "portal_list_flagged_posts_for_moderation",
    "file_center_read_quota_status",
    "file_center_list_recent_security_scans",
    "file_center_explain_role_matrix",
    "communication_list_active_announcements",
    "communication_summarize_my_unread_messages",
    "communication_read_announcement_detail",
    "surveys_list_active_surveys_for_management",
    "support_help_list_my_tickets",
    "support_help_read_ticket_detail",
    "support_help_search_help_center_articles",
    "ai_decision_support_list_open_recommendations",
    "ai_decision_support_summarize_usage",
    "virtual_assistant_discover_available_modules",
    "virtual_assistant_discover_my_capabilities",
    "dashboard_explain_module",
    "settings_auth_list_unit_menu_overrides",
    "settings_auth_summarize_role_permission_coverage",
    "notifications_list_my_notifications",
    "notifications_summarize_my_unread_count",
    "notifications_read_notification_detail",
    "email_automation_summarize_performance_reminder_health",
    "scheduled_jobs_read_feedback_followup_status",
    "scheduled_jobs_list_recent_digest_jobs",
    "scheduled_jobs_summarize_automation_health",
    "security_session_read_captcha_policy",
    "audit_read_change_log_detail",
    "audit_summarize_recent_change_activity",
]
