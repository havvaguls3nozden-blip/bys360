"""
BYS360 SP-4B Gerçek Eksik Kapatma Servisi

Kapsam:
- Sistem içi bildirim altyapısı
- Rapor/dışa aktarım olay kaydı
- Teslim hazırlık durum özeti
"""
from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy import inspect, text

try:
    from app import db
except Exception:  # pragma: no cover
    db = None


def _has_table(table_name: str) -> bool:
    if db is None:
        return False
    try:
        return table_name in inspect(db.engine).get_table_names()
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return False


def create_system_notification(
    user_id: int | None,
    title: str,
    body: str,
    category: str = "GENEL",
    related_url: str | None = None,
    channel: str = "system",
) -> dict[str, Any]:
    """Kullanıcıya sistem içi bildirim kaydı oluşturur."""
    if db is None or not _has_table("bys360_notifications"):
        return {"ok": False, "reason": "notification_table_missing"}

    sql = text("""
        INSERT INTO bys360_notifications
            (user_id, title, body, category, related_url, channel, status, created_at)
        VALUES
            (:user_id, :title, :body, :category, :related_url, :channel, 'unread', CURRENT_TIMESTAMP)
        RETURNING id
    """)
    result = db.session.execute(sql, {
        "user_id": user_id,
        "title": title,
        "body": body,
        "category": category,
        "related_url": related_url,
        "channel": channel,
    })
    notification_id = result.scalar()
    db.session.commit()
    return {"ok": True, "notification_id": notification_id}


def mark_notification_read(notification_id: int, user_id: int | None = None) -> dict[str, Any]:
    """Bildirim kaydını okundu işaretler."""
    if db is None or not _has_table("bys360_notifications"):
        return {"ok": False, "reason": "notification_table_missing"}

    if user_id is None:
        sql = text("""
            UPDATE bys360_notifications
            SET status='read', read_at=CURRENT_TIMESTAMP
            WHERE id=:notification_id
        """)
        params = {"notification_id": notification_id}
    else:
        sql = text("""
            UPDATE bys360_notifications
            SET status='read', read_at=CURRENT_TIMESTAMP
            WHERE id=:notification_id AND user_id=:user_id
        """)
        params = {"notification_id": notification_id, "user_id": user_id}

    result = db.session.execute(sql, params)
    db.session.commit()
    return {"ok": True, "updated": result.rowcount}


def list_user_notifications(user_id: int, limit: int = 20) -> list[dict[str, Any]]:
    """Kullanıcı bildirimlerini listeler."""
    if db is None or not _has_table("bys360_notifications"):
        return []

    rows = db.session.execute(text("""
        SELECT id, title, body, category, related_url, channel, status, created_at, read_at
        FROM bys360_notifications
        WHERE user_id=:user_id OR user_id IS NULL
        ORDER BY created_at DESC, id DESC
        LIMIT :limit
    """), {"user_id": user_id, "limit": limit}).mappings().all()
    return [dict(row) for row in rows]


def register_export_event(
    user_id: int | None,
    report_name: str,
    export_format: str,
    status: str = "created",
    file_path: str | None = None,
    row_count: int | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """PDF/Excel/CSV dışa aktarım olayını kayıt altına alır."""
    if db is None or not _has_table("bys360_export_events"):
        return {"ok": False, "reason": "export_event_table_missing"}

    result = db.session.execute(text("""
        INSERT INTO bys360_export_events
            (user_id, report_name, export_format, status, file_path, row_count, note, created_at)
        VALUES
            (:user_id, :report_name, :export_format, :status, :file_path, :row_count, :note, CURRENT_TIMESTAMP)
        RETURNING id
    """), {
        "user_id": user_id,
        "report_name": report_name,
        "export_format": export_format,
        "status": status,
        "file_path": file_path,
        "row_count": row_count,
        "note": note,
    })
    export_id = result.scalar()
    db.session.commit()
    return {"ok": True, "export_id": export_id}


def build_delivery_status_summary() -> dict[str, Any]:
    """SP-4 teslim hazırlık tabloları üzerinden özet üretir."""
    summary = {
        "notification_table": _has_table("bys360_notifications"),
        "export_event_table": _has_table("bys360_export_events"),
        "delivery_item_table": _has_table("bys360_delivery_items"),
        "open_items": 0,
        "completed_items": 0,
    }

    if db is None or not summary["delivery_item_table"]:
        return summary

    rows = db.session.execute(text("""
        SELECT status, COUNT(*) AS count
        FROM bys360_delivery_items
        GROUP BY status
    """)).mappings().all()

    for row in rows:
        if row["status"] == "completed":
            summary["completed_items"] = int(row["count"])
        else:
            summary["open_items"] += int(row["count"])

    return summary
