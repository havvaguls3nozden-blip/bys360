"""BYS360 eylem planı takip bildirimleri zamanlayıcısı.

APScheduler kuruluysa uygulama içinde güvenli şekilde tetiklenebilir. Kurulu değilse
bu modül uygulama açılışını bozmaz; Windows Görev Zamanlayıcı veya ayrı script ile
çalıştırma seçeneği korunur.
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def _truthy(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on", "aktif", "evet"}


def _run_job(app: Any, days_ahead: int) -> None:
    with app.app_context():
        try:
            from app.services.performance.feedback_followup_phase4 import generate_followup_notices
            result = generate_followup_notices(
                current_user_id=None,
                current_user_role=None,
                is_superuser=True,
                days_ahead=days_ahead,
            )
            logger.info(
                "BYS360 eylem planı takip bildirimi çalıştı | created=%s skipped=%s",
                result.get("created"),
                result.get("skipped"),
            )
        except Exception as exc:  # pragma: no cover - canlı log güvenliği
            logger.exception("BYS360 eylem planı takip bildirimi çalıştırılamadı: %s", exc)


def init_feedback_followup_scheduler(app: Any) -> bool:
    """İsteğe bağlı arka plan zamanlayıcıyı başlatır.

    Varsayılan olarak kapalıdır. Canlıda etkinleştirmek için:
    BYS360_FEEDBACK_FOLLOWUP_SCHEDULER=1

    Ortam değişkenleri:
    - BYS360_FEEDBACK_FOLLOWUP_SCHEDULER_INTERVAL_MINUTES: varsayılan 1440
    - BYS360_FEEDBACK_FOLLOWUP_DAYS_AHEAD: varsayılan 7
    """
    if getattr(app, "_bys360_feedback_followup_scheduler_ready", False):
        return True

    if not _truthy(os.getenv("BYS360_FEEDBACK_FOLLOWUP_SCHEDULER", "0")):
        app._bys360_feedback_followup_scheduler_ready = False
        logger.info("BYS360 eylem planı takip zamanlayıcısı kapalı. Harici script/Görev Zamanlayıcı kullanılabilir.")
        return False

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        app._bys360_feedback_followup_scheduler_ready = False
        logger.warning("APScheduler bulunamadı; takip bildirimi için scripts/run_feedback_followup_scheduler.py veya Windows Görev Zamanlayıcı kullanın: %s", exc)
        return False

    interval_minutes = int(os.getenv("BYS360_FEEDBACK_FOLLOWUP_SCHEDULER_INTERVAL_MINUTES", "1440") or 1440)
    days_ahead = int(os.getenv("BYS360_FEEDBACK_FOLLOWUP_DAYS_AHEAD", "7") or 7)
    scheduler = BackgroundScheduler(daemon=True, timezone=os.getenv("TZ", "Europe/Istanbul"))
    scheduler.add_job(
        lambda: _run_job(app, days_ahead),
        trigger="interval",
        minutes=max(5, interval_minutes),
        id="bys360_feedback_followup_notices",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    app._bys360_feedback_followup_scheduler = scheduler
    app._bys360_feedback_followup_scheduler_ready = True
    logger.info("BYS360 eylem planı takip zamanlayıcısı aktif | interval=%s dk | days_ahead=%s", interval_minutes, days_ahead)
    return True

# BYS360_PERFORMANCE_COMPLETION_PHASE9_REMINDER_BOUND
# Otomatik hatırlatma ve aksatan amir bildirimi phase9_reminder_policy sözleşmesini kullanır.
