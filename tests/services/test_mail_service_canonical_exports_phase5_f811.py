from __future__ import annotations

from app.services import mail_core
from app.services import mail_performance_sender
from app.services import mail_service


def test_mail_service_exports_canonical_implementations():
    assert (
        mail_service.get_smtp_settings
        is mail_core.get_smtp_settings
    )
    assert mail_service.send_email is mail_core.send_email
    assert (
        mail_service.build_mail_system_health_snapshot
        is mail_performance_sender.build_mail_system_health_snapshot
    )
    assert (
        mail_service.send_bulk_assignment_reminders
        is mail_performance_sender.send_bulk_assignment_reminders
    )
