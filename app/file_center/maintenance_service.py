"""BYS360 Dosya Merkezi bakım ve yönetici raporlama servisi.

V1G kapsamı:
- Yönetici özet metrikleri
- Kota kullanımını yeniden hesaplama
- Süresi dolan misafir indirme bağlantılarını pasifleştirme
- Süresi dolan dosya isteklerini kapatma
- Silinmiş dosya kayıtlarını raporlama

Bu servis local geliştirme içindir; canlıya geçişte zamanlanmış görev ve yetki kontrolleri ayrıca sıkılaştırılır.
"""
from __future__ import annotations

import os
import shutil
from datetime import timedelta
from pathlib import Path
from typing import Any

from app.core.datetime_utils import utc_now
from app.extensions import db
from app.models.file_center_models import (
    FileAuditLog,
    FileCenterMailLog,
    FileDownloadLog,
    FileQuotaUsage,
    FileRequest,
    FileRequestUpload,
    FileShareLink,
    FileStorageItem,
)


def _storage_root() -> Path:
    from app.file_center.services import storage_root

    return storage_root()


def storage_health_summary() -> dict[str, int | str | bool]:
    root = _storage_root()
    usage = shutil.disk_usage(root)
    used_percent = int(round((usage.used / usage.total) * 100)) if usage.total else 0
    threshold = int(os.getenv("FILE_CENTER_DISK_ALERT_PERCENT", "85") or 85)
    return {
        "storage_root": str(root),
        "total_bytes": int(usage.total),
        "used_bytes": int(usage.used),
        "free_bytes": int(usage.free),
        "used_percent": used_percent,
        "alert_percent": threshold,
        "is_alert": used_percent >= threshold,
    }


def run_file_center_maintenance_tick(actor_user_id: int | None = None, *, scan_limit: int = 250) -> dict[str, object]:
    from app.file_center.services import scan_pending_files

    expired = expire_due_links_and_requests(actor_user_id=actor_user_id)
    quota = recalculate_quotas(actor_user_id=actor_user_id)
    scan = scan_pending_files(limit=scan_limit, actor_user_id=actor_user_id)
    disk = storage_health_summary()
    if disk.get("is_alert"):
        db.session.add(FileAuditLog(
            actor_user_id=actor_user_id,
            action="file_center_disk_alert",
            message=f"Dosya Merkezi depolama alanı uyarısı: %{disk['used_percent']} dolu. Kök: {disk['storage_root']}",
        ))
    return {"expired": expired, "quota": quota, "scan": scan, "disk": disk}


def _safe_sum(values) -> int:
    return int(sum(int(x or 0) for x in values))


def build_admin_summary() -> dict[str, Any]:
    files = FileStorageItem.query.all()
    active_files = [x for x in files if not x.is_deleted]
    deleted_files = [x for x in files if x.is_deleted]
    links = FileShareLink.query.all()
    requests = FileRequest.query.all()
    uploads = FileRequestUpload.query.count()
    downloads = FileDownloadLog.query.count()
    mail_logs = FileCenterMailLog.query.all()

    now = utc_now()
    expiring_links = [x for x in links if x.is_active and x.expires_at and x.expires_at >= now and x.expires_at <= now + timedelta(days=2)]
    expired_active_links = [x for x in links if x.is_active and x.expires_at and x.expires_at < now]
    expired_open_requests = [x for x in requests if x.status == "open" and x.expires_at and x.expires_at < now]
    open_requests = [x for x in requests if x.status == "open"]
    failed_mails = [x for x in mail_logs if x.status == "failed"]
    skipped_mails = [x for x in mail_logs if x.status == "skipped"]

    total_bytes = _safe_sum(x.size_bytes for x in active_files)
    deleted_bytes = _safe_sum(x.size_bytes for x in deleted_files)

    top_files = sorted(active_files, key=lambda x: int(x.size_bytes or 0), reverse=True)[:10]
    recent_audits = FileAuditLog.query.order_by(FileAuditLog.created_at.desc()).limit(30).all()
    recent_downloads = FileDownloadLog.query.order_by(FileDownloadLog.created_at.desc()).limit(30).all()

    return {
        "total_files": len(active_files),
        "deleted_files": len(deleted_files),
        "total_bytes": total_bytes,
        "deleted_bytes": deleted_bytes,
        "active_links": len([x for x in links if x.is_active]),
        "expired_active_links": len(expired_active_links),
        "expiring_links": len(expiring_links),
        "open_requests": len(open_requests),
        "expired_open_requests": len(expired_open_requests),
        "uploads": uploads,
        "downloads": downloads,
        "mail_sent": len([x for x in mail_logs if x.status == "sent"]),
        "mail_failed": len(failed_mails),
        "mail_skipped": len(skipped_mails),
        "top_files": top_files,
        "recent_audits": recent_audits,
        "recent_downloads": recent_downloads,
        "storage_root": str(_storage_root()),
        "storage_health": storage_health_summary(),
    }


def recalculate_quotas(actor_user_id: int | None = None) -> dict[str, int]:
    active_files = FileStorageItem.query.filter_by(is_deleted=False).all()
    usage: dict[int, dict[str, int]] = {}
    for item in active_files:
        row = usage.setdefault(int(item.owner_user_id), {"bytes": 0, "count": 0})
        row["bytes"] += int(item.size_bytes or 0)
        row["count"] += 1

    for user_id, data in usage.items():
        quota = FileQuotaUsage.query.filter_by(user_id=user_id).one_or_none()
        if quota is None:
            quota = FileQuotaUsage(user_id=user_id)
            db.session.add(quota)
        quota.used_bytes = data["bytes"]
        quota.file_count = data["count"]

    # Dosyası kalmayan kullanıcıların kotasını sıfırla.
    for quota in FileQuotaUsage.query.all():
        if int(quota.user_id) not in usage:
            quota.used_bytes = 0
            quota.file_count = 0

    db.session.add(FileAuditLog(
        actor_user_id=actor_user_id,
        action="quota_recalculated",
        message=f"Dosya Merkezi kota bilgileri yeniden hesaplandı. Kullanıcı sayısı: {len(usage)}",
    ))
    return {"users": len(usage), "files": len(active_files)}


def expire_due_links_and_requests(actor_user_id: int | None = None) -> dict[str, int]:
    now = utc_now()
    expired_links = FileShareLink.query.filter(FileShareLink.is_active.is_(True), FileShareLink.expires_at < now).all()
    for link in expired_links:
        link.is_active = False
        link.revoked_at = now
        link.revoked_by_user_id = actor_user_id

    expired_requests = FileRequest.query.filter(FileRequest.status == "open", FileRequest.expires_at < now).all()
    for row in expired_requests:
        row.status = "expired"
        row.closed_at = now

    db.session.add(FileAuditLog(
        actor_user_id=actor_user_id,
        action="expired_items_closed",
        message=f"Süresi dolan bağlantı/istek bakımı yapıldı. Link: {len(expired_links)}, İstek: {len(expired_requests)}",
    ))
    return {"links": len(expired_links), "requests": len(expired_requests)}


def maintenance_checklist() -> list[dict[str, str]]:
    summary = build_admin_summary()
    items: list[dict[str, str]] = []
    if summary["expired_active_links"]:
        items.append({"level": "warning", "title": "Süresi dolmuş aktif link var", "detail": f"{summary['expired_active_links']} bağlantı bakım işlemi bekliyor."})
    if summary["expired_open_requests"]:
        items.append({"level": "warning", "title": "Süresi dolmuş açık dosya isteği var", "detail": f"{summary['expired_open_requests']} istek kapatılmalı veya yenilenmeli."})
    if summary["mail_failed"]:
        items.append({"level": "danger", "title": "Başarısız e-posta gönderimi var", "detail": f"{summary['mail_failed']} mail gönderimi başarısız olmuş."})
    if summary["expiring_links"]:
        items.append({"level": "info", "title": "Yakında süresi dolacak linkler var", "detail": f"{summary['expiring_links']} bağlantı iki gün içinde kapanacak."})
    if not items:
        items.append({"level": "success", "title": "Bakım uyarısı yok", "detail": "Dosya Merkezi için acil bakım gerektiren kayıt görünmüyor."})
    return items
