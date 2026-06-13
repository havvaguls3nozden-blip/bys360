from __future__ import annotations

from datetime import datetime, timezone
from statistics import mean
from typing import Any

from flask import current_app
from sqlalchemy.exc import IntegrityError

# BYS360 V1E: emergency runtime recovery for the Phase2Y wildcard-import regression.
# This deliberately restores the shared mobile contract first; explicit imports can be
# reintroduced later only after a per-file F821 gate and smoke test.
from app.api.mobile.shared import *  # noqa: F401,F403

@mobile_api_bp.post('/notifications/<int:notification_id>/read')
@require_mobile_user
def mobile_notification_mark_read_v2864(user: User, notification_id: int):
    notification = Notification.query.filter_by(id=notification_id, user_id=user.id).first()
    if notification is None:
        return jsonify({'message': 'Bildirim bulunamadı veya bu bildirim için yetkiniz bulunmamaktadır.'}), 404
    try:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'message': 'Bildirim durumu güncellenemedi. Lütfen tekrar deneyin.'}), 500
    return jsonify({'source': 'real_api', 'ok': True, 'message': 'Bildirim okundu olarak işaretlendi.'})


@mobile_api_bp.post('/notifications/read-all')
@require_mobile_user
def mobile_notifications_mark_all_read_v2864(user: User):
    try:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        rows = Notification.query.filter_by(user_id=user.id, is_read=False).all()
        updated = 0
        for row in rows:
            row.is_read = True
            row.read_at = now
            updated += 1
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'message': 'Bildirimler güncellenemedi. Lütfen tekrar deneyin.'}), 500
    return jsonify({'source': 'real_api', 'ok': True, 'updated': updated, 'message': 'Okunmamış bildirimler okundu olarak işaretlendi.'})

