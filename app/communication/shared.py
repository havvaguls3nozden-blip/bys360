from __future__ import annotations

import datetime as _dt
import logging
from typing import Any
from urllib.parse import urlsplit

from flask import current_app, redirect, request, url_for
from flask_login import current_user
from werkzeug.routing import BuildError

from app.core.datetime_utils import utc_now
from app.models import SurveyQuestionOption
from app.route_support import issue_form_token, safe_render
from app.services.ai import build_message_compose_ai_panel, build_notification_priority_ai_panel
from app.services.message_service import (
    MESSAGE_THREAD_BADGE_OPTIONS as _MESSAGE_THREAD_BADGE_OPTIONS,
    MESSAGE_THREAD_COLOR_OPTIONS as _MESSAGE_THREAD_COLOR_OPTIONS,
    MESSAGE_THREAD_ICON_OPTIONS as _MESSAGE_THREAD_ICON_OPTIONS,
)

logger = logging.getLogger(__name__)


def _utcnow():
    try:
        return utc_now()
    except Exception:  # pragma: no cover
        logger.exception("BYS360 V6C guarded exception | file=app/communication/shared.py | line=27")
        return utc_now()


def _utcdate():
    return _utcnow().date()


def _parse_datetime_input(raw_value: str | None):
    value = (raw_value or "").strip()
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = _dt.datetime.fromisoformat(normalized)
        if parsed.tzinfo is not None:
            return parsed.astimezone(_dt.UTC).replace(tzinfo=None)
        return parsed
    except ValueError as exc:
        raise ValueError("Tarih-saat alanı okunamadı. Lütfen takvim alanını yeniden seçin.") from exc


def _log_communication_exception(context: str, exc: BaseException, **extra):
    try:
        current_app.logger.exception(
            "Communication route failure [%s] | extra=%s | error=%s",
            context,
            extra,
            exc,
        )
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/communication/shared.py)")


def _normalize_text_search(raw_value: str | None, *, limit: int = 120) -> str:
    value = " ".join((raw_value or "").strip().split())
    return value[:limit]


def _current_message_view_state(thread_id: int | None = None) -> dict[str, Any]:
    current_filter = (request.form.get("current_filter") or request.args.get("filter") or "active").strip().lower()
    if current_filter not in {"active", "unread", "pinned", "muted", "archived", "all"}:
        current_filter = "active"
    current_scope = (request.form.get("current_scope") or request.args.get("scope") or "all").strip().lower()
    if current_scope not in {"all", "self"}:
        current_scope = "all"
    search_query = _normalize_text_search(request.form.get("q") or request.args.get("q"))
    state: dict[str, str | int] = {"filter": current_filter}
    if current_scope != "all":
        state["scope"] = current_scope
    if search_query:
        state["q"] = search_query
    if thread_id:
        state["thread_id"] = thread_id
    return state


def _redirect_messages_view(thread_id: int | None = None):
    return redirect(url_for("main.messages_inbox", **_current_message_view_state(thread_id)))


def _current_notifications_view_state() -> dict[str, str]:
    current_view = (request.form.get("current_view") or request.args.get("view") or "all").strip().lower()
    if current_view not in {"all", "unread", "read", "priority", "support", "performance", "surveys", "system"}:
        current_view = "all"
    search_query = _normalize_text_search(request.form.get("q") or request.args.get("q"))
    state = {"view": current_view}
    if search_query:
        state["q"] = search_query
    return state


def _legacy_notification_view_to_portal_filter(view_name: str | None) -> str:
    mapping = {
        "all": "all",
        "unread": "unread",
        "read": "all",
        "priority": "portal",
        "support": "all",
        "performance": "all",
        "surveys": "all",
        "system": "all",
    }
    normalized = (view_name or "all").strip().lower()
    return mapping.get(normalized, "all")


def _notification_redirect_endpoint() -> str:
    for endpoint in ("main.notifications_list", "main.notifications_list"):
        try:
            url_for(endpoint)
            return endpoint
        except BuildError:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/communication/shared.py:118)")
            continue
    return "main.notifications_list"


def _redirect_notifications_view():
    state = _current_notifications_view_state()
    query_kwargs = {"view": state.get("view") or "all"}
    if state.get("q"):
        query_kwargs["q"] = state.get("q")
    return redirect(url_for("main.notifications_list", **query_kwargs))


def _safe_internal_redirect(link_url: str | None):
    target = (link_url or "").strip()
    if not target:
        return _redirect_notifications_view()

    if target.startswith("/") and not target.startswith("//"):
        return redirect(target)

    try:
        parsed = urlsplit(target)
        request_root = urlsplit(request.host_url)
        if parsed.scheme in {"http", "https"} and parsed.netloc and parsed.netloc == request_root.netloc:
            safe_path = parsed.path or "/"
            if parsed.query:
                safe_path = f"{safe_path}?{parsed.query}"
            if parsed.fragment:
                safe_path = f"{safe_path}#{parsed.fragment}"
            return redirect(safe_path)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/communication/shared.py)")

    return _redirect_notifications_view()


def _clean_message_body(raw_value: str | None, *, limit: int = 6000) -> str:
    value = (raw_value or "").replace("\r\n", "\n").replace("\r", "\n")
    return value.strip()[:limit]


def _question_option_id_set(question) -> set[int]:
    option_query = getattr(question, "options", None)
    if option_query is None:
        return set()
    ordered_options = (
        option_query.order_by(SurveyQuestionOption.sort_order.asc(), SurveyQuestionOption.id.asc()).all()
        if hasattr(option_query, "order_by")
        else list(option_query)
    )
    return {
        int(option.id)
        for option in ordered_options
        if getattr(option, "id", None) is not None
    }


def _render_message_new(*, users, recent_users=None, recipient_user_id: int | None = None, body: str = "", badge_label: str = "", icon_name: str = "", accent_color: str = ""):
    submit_token = issue_form_token("messages_new", scope=str(current_user.id))
    selected_recipient = str(recipient_user_id) if recipient_user_id else ""
    return safe_render(
        "messages_new.html",
        "<h3>Yeni Mesaj</h3>",
        users=users,
        recent_users=recent_users or [],
        selected_recipient_user_id=selected_recipient,
        selected_body=body,
        selected_badge_label=badge_label,
        selected_icon_name=icon_name,
        selected_accent_color=accent_color,
        message_badge_options=_MESSAGE_THREAD_BADGE_OPTIONS,
        message_icon_options=_MESSAGE_THREAD_ICON_OPTIONS,
        message_color_options=_MESSAGE_THREAD_COLOR_OPTIONS,
        submit_token=submit_token,
        ai_message_compose_panel=build_message_compose_ai_panel(
            users=users,
            selected_recipient_user_id=selected_recipient,
            body=body,
            badge_label=badge_label,
            icon_name=icon_name,
            accent_color=accent_color,
        ),
    )


def _render_notifications_page(*, notifications, unread_count, read_count, priority_count, today_count, current_view, search_query, filter_counts):
    ai_notifications_panel = build_notification_priority_ai_panel(
        notifications=notifications,
        unread_count=unread_count,
        read_count=read_count,
        priority_count=priority_count,
        today_count=today_count,
        current_view=current_view,
        filter_counts=filter_counts,
    )
    return safe_render(
        "notifications_list.html",
        "<h3>Bildirimler</h3>",
        notifications=notifications,
        unread_count=unread_count,
        read_count=read_count,
        priority_count=priority_count,
        today_count=today_count,
        current_view=current_view,
        search_query=search_query,
        filter_counts=filter_counts,
        visible_notification_count=len(notifications),
        ai_notifications_panel=ai_notifications_panel,
    )


def _empty_notification_counts() -> dict[str, int]:
    return {"all": 0, "unread": 0, "read": 0, "priority": 0, "support": 0, "performance": 0, "surveys": 0, "system": 0}
