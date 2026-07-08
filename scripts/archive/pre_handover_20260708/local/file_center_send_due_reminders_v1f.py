from __future__ import annotations

from datetime import timedelta
from pathlib import Path
import os
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flask import url_for

from app import create_app
from app.core.datetime_utils import utc_now
from app.extensions import db
from app.file_center.mail_service import send_file_request_email
from app.models.file_center_models import FileCenterMailLog, FileRequest


def _base_url() -> str:
    return (os.getenv("FILE_CENTER_PUBLIC_BASE_URL") or "http://127.0.0.1:8000").rstrip("/")


app = create_app()
with app.app_context():
    now = utc_now()
    days = int(os.getenv("FILE_CENTER_AUTO_REMINDER_DAYS", "2"))
    resend_hours = int(os.getenv("FILE_CENTER_AUTO_REMINDER_RESEND_HOURS", "20"))
    until = now + timedelta(days=days)
    since = now - timedelta(hours=resend_hours)

    rows = (
        FileRequest.query.filter(
            FileRequest.status == "open",
            FileRequest.expires_at >= now,
            FileRequest.expires_at <= until,
            FileRequest.upload_count == 0,
            FileRequest.recipient_email.isnot(None),
        )
        .order_by(FileRequest.expires_at.asc())
        .all()
    )

    sent = 0
    skipped = 0
    failed = 0
    for row in rows:
        recent_sent = FileCenterMailLog.query.filter(
            FileCenterMailLog.request_id == row.id,
            FileCenterMailLog.purpose == "auto_reminder",
            FileCenterMailLog.status == "sent",
            FileCenterMailLog.created_at >= since,
        ).first()
        if recent_sent:
            skipped += 1
            continue
        upload_url = _base_url() + url_for("main.file_center_guest_upload", token=row.public_token)
        mail_log = send_file_request_email(row, upload_url=upload_url, purpose="auto_reminder", actor_user_id=None)
        db.session.commit()
        if mail_log.status == "sent":
            sent += 1
        elif mail_log.status == "failed":
            failed += 1
        else:
            skipped += 1

    print("OK: V1F otomatik hatırlatma kontrolü tamamlandı.")
    print("Uygun talep:", len(rows))
    print("Gönderildi:", sent)
    print("Başarısız:", failed)
    print("Atlandı:", skipped)
