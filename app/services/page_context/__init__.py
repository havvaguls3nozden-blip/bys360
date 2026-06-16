from __future__ import annotations

from app.config import is_removed


def _disabled_page_context(*args, **kwargs):
    return {
        "module_disabled": True,
        "module_disabled_title": "Modül devre dışı",
        "module_disabled_message": "Bu sayfa canlı öncesi temizlik kapsamında pasife alındı.",
    }


if not is_removed("portal"):
    from .portal import (
        build_portal_admin_dashboard_context,
        build_portal_calendar_page_context,
        build_portal_chat_inbox_page_context,
        build_portal_chat_thread_page_context,
        build_portal_event_detail_page_context,
        build_portal_feed_context,
        build_portal_feed_page_context,
        build_portal_hashtag_page_context,
        build_portal_notifications_context,
        build_portal_notifications_page_context,
        build_portal_profile_page_context,
        build_portal_stories_page_context,
    )
else:
    build_portal_admin_dashboard_context = _disabled_page_context
    build_portal_calendar_page_context = _disabled_page_context
    build_portal_chat_inbox_page_context = _disabled_page_context
    build_portal_chat_thread_page_context = _disabled_page_context
    build_portal_event_detail_page_context = _disabled_page_context
    build_portal_feed_context = _disabled_page_context
    build_portal_feed_page_context = _disabled_page_context
    build_portal_hashtag_page_context = _disabled_page_context
    build_portal_notifications_context = _disabled_page_context
    build_portal_notifications_page_context = _disabled_page_context
    build_portal_profile_page_context = _disabled_page_context
    build_portal_stories_page_context = _disabled_page_context

if not is_removed("repository") and not is_removed("education") and not is_removed("strategy"):
    from .repository import (
        build_education_record_page_context,
        build_repository_activity_page_context,
        build_repository_album_page_context,
        build_repository_dashboard_page_context,
        build_repository_document_page_context,
        build_repository_edit_history_page_context,
        build_repository_retention_page_context,
        build_repository_search_page_context,
        build_repository_showcase_approvals_page_context,
        build_repository_showcase_page_context,
        build_repository_tag_reports_page_context,
        build_repository_zip_reports_page_context,
        build_strategy_action_page_context,
        build_strategy_goal_page_context,
        build_strategy_plan_page_context,
    )
else:
    build_education_record_page_context = _disabled_page_context
    build_repository_activity_page_context = _disabled_page_context
    build_repository_album_page_context = _disabled_page_context
    build_repository_dashboard_page_context = _disabled_page_context
    build_repository_document_page_context = _disabled_page_context
    build_repository_edit_history_page_context = _disabled_page_context
    build_repository_retention_page_context = _disabled_page_context
    build_repository_search_page_context = _disabled_page_context
    build_repository_showcase_approvals_page_context = _disabled_page_context
    build_repository_showcase_page_context = _disabled_page_context
    build_repository_tag_reports_page_context = _disabled_page_context
    build_repository_zip_reports_page_context = _disabled_page_context
    build_strategy_action_page_context = _disabled_page_context
    build_strategy_goal_page_context = _disabled_page_context
    build_strategy_plan_page_context = _disabled_page_context
