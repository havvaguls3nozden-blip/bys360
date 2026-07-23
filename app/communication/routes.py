from __future__ import annotations

import logging

"""Communication route family compatibility hub.

Bu dosya iletişim paketinin tek import yüzeyidir. Route registry halen
``app.communication.routes`` modülünü import ettiği için alt domain route
modülleri burada import edilerek ana blueprint'e kaydedilir.
"""

from flask_login import (  # noqa: E402 - deferred import (staged facade/route-registration architecture)
    current_user,  # noqa: E402 - deferred import (staged facade/route-registration architecture)
)

from app.route_registry import (  # noqa: E402 - deferred import (staged facade/route-registration architecture)
    main_bp,  # noqa: E402 - deferred import (staged facade/route-registration architecture)
)
from app.services.message_service import (  # noqa: E402 - deferred import (staged facade/route-registration architecture)
    get_unread_notification_count as _get_unread_notification_count,
)

LEGACY_SHIM = False
LEGACY_RUNTIME_STATUS = "active_modular_main_blueprint_routes"
LEGACY_ARCHIVE_MODULE = "app.legacy_routes_archive.routes_communication"
LEGACY_ROUTE_FAMILY = "communication_messages_notifications_surveys_announcements_popup"
LEGACY_NOTE = (
    "Communication route ailesi domain bazlı sahipliğe taşındı; "
    "app.communication.routes dosyası uyumluluk omurgası ve export yüzeyi olarak çalışır. "
    "Faz 5 ile okunma raporu, kişi bazlı izleme ve CSV dışa aktarım yüzeyi de eklendi."
)


@main_bp.app_context_processor
def bys360_notification_context():
    if current_user.is_authenticated:
        return {"unread_notification_count": _get_unread_notification_count(current_user.id)}
    return {"unread_notification_count": 0}


from . import (  # noqa: E402 - deferred import (staged facade/route-registration architecture)
    feedback_routes as _feedback_routes,  # noqa: E402,F401
    phase1_routes as _phase1_routes,  # noqa: E402,F401
    phase2_routes as _phase2_routes,  # noqa: E402,F401
    phase3_routes as _phase3_routes,  # noqa: E402,F401
    phase4_routes as _phase4_routes,  # noqa: E402,F401
    phase5_routes as _phase5_routes,  # noqa: E402,F401
)
from .announcement_popup_routes import (  # noqa: E402,F401
    announcement_popup_acknowledge,
    announcement_popup_dismiss,
    announcement_popup_edit,
    announcement_popup_manage,
    announcement_popup_media,
    announcement_popup_new,
    announcement_popup_report,
    announcement_popup_report_csv,
    announcement_popup_runtime_context,
    announcement_popup_runtime_pending,
    announcement_popup_target_count,
    announcement_popup_toggle,
)
from .announcements_routes import (  # noqa: E402,F401
    announcements_list,
    announcements_new,
)
from .messages_routes import (  # noqa: E402,F401
    message_attachment_download,
    messages_delete,
    messages_edit,
    messages_inbox,
    messages_mark_read,
    messages_new,
    messages_react,
    messages_send,
    messages_thread,
    messages_thread_activity,
    messages_thread_live,
    messages_thread_typing,
    messages_toggle_archive,
    messages_toggle_mute,
    messages_toggle_pin,
)
from .notifications_routes import (  # noqa: E402,F401
    notifications_bulk_delete,
    notifications_bulk_mark_read,
    notifications_bulk_mark_unread,
    notifications_list,
    notifications_mark_all_read,
    notifications_mark_read,
    notifications_mark_unread,
    notifications_unread_count,
)
from .surveys_routes import (  # noqa: E402,F401
    survey_archive,
    survey_bulk_action,
    survey_close,
    survey_create,
    survey_delete,
    survey_edit,
    survey_manage,
    survey_publish,
    survey_restore,
    survey_results,
    survey_results_export_csv,
    survey_submit,
    survey_take,
    survey_target_users,
    survey_unpublish,
    surveys_list,
)

messages_thread_send = messages_send
messages_thread_mark_read = messages_mark_read
messages_thread_mute_toggle = messages_toggle_mute
messages_thread_archive_toggle = messages_toggle_archive
messages_thread_pin_toggle = messages_toggle_pin

# BYS360 V2.15.10 - Günlük personel bilgilendirme maili route bağlantısı
# Bu import main_bp üzerinde /executive-summary/daily-weather-mail endpointini kayıt eder.
try:
    from . import daily_weather_mail_routes as _daily_weather_mail_routes  # noqa: E402,F401
except Exception:
    import logging
    logging.getLogger(__name__).exception("BYS360 günlük hava maili route modülü yüklenemedi.")

__all__ = [
    "LEGACY_SHIM",
    "LEGACY_RUNTIME_STATUS",
    "LEGACY_ARCHIVE_MODULE",
    "LEGACY_ROUTE_FAMILY",
    "LEGACY_NOTE",
    "messages_inbox",
    "messages_new",
    "messages_thread",
    "messages_thread_activity",
    "messages_thread_live",
    "messages_thread_typing",
    "messages_send",
    "messages_thread_send",
    "messages_mark_read",
    "messages_thread_mark_read",
    "messages_react",
    "messages_toggle_mute",
    "messages_thread_mute_toggle",
    "messages_toggle_archive",
    "messages_thread_archive_toggle",
    "messages_toggle_pin",
    "messages_thread_pin_toggle",
    "messages_edit",
    "messages_delete",
    "message_attachment_download",
    "notifications_list",
    "notifications_unread_count",
    "notifications_mark_read",
    "notifications_mark_unread",
    "notifications_mark_all_read",
    "notifications_bulk_mark_read",
    "notifications_bulk_mark_unread",
    "notifications_bulk_delete",
    "surveys_list",
    "survey_take",
    "survey_submit",
    "survey_target_users",
    "survey_manage",
    "survey_create",
    "survey_edit",
    "survey_publish",
    "survey_unpublish",
    "survey_close",
    "survey_archive",
    "survey_restore",
    "survey_bulk_action",
    "survey_delete",
    "survey_results",
    "survey_results_export_csv",
    "announcements_list",
    "announcements_new",
    "announcement_popup_manage",
    "announcement_popup_new",
    "announcement_popup_edit",
    "announcement_popup_toggle",
    "announcement_popup_target_count",
    "announcement_popup_runtime_pending",
    "announcement_popup_acknowledge",
    "announcement_popup_dismiss",
    "announcement_popup_media",
    "announcement_popup_report",
    "announcement_popup_report_csv",
]


# Canlı Omurga Faz 0:
# Bu registry, iletişim route ailesinin re-export yüzeyini statik/okunabilir hale getirir.
# Route davranışını değiştirmez; yalnızca import/check katmanının modüler yapıyı doğru
# görmesini sağlar.
from .export_registry import (  # noqa: E402
    build_communication_export_registry,
    validate_communication_export_surface,
)

COMMUNICATION_ROUTE_EXPORTS = tuple(__all__)
COMMUNICATION_EXPORT_REGISTRY = build_communication_export_registry(
    globals(),
    COMMUNICATION_ROUTE_EXPORTS,
)


def get_communication_export_registry():
    """Return a copy of the communication export registry for audits/diagnostics."""

    return dict(COMMUNICATION_EXPORT_REGISTRY)


def validate_communication_exports():
    """Validate that exported compatibility names are present and safe."""

    return validate_communication_export_surface(globals(), COMMUNICATION_ROUTE_EXPORTS)
