"""BYS360 geri bildirim/nabız arka plan görevleri."""
from __future__ import annotations

from datetime import datetime, timezone, UTC
from types import SimpleNamespace
from typing import Any


def _ensure_app_context():
    try:
        from flask import has_app_context
        if has_app_context():
            return None
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/tasks/feedback_tasks.py)")
    from app import create_app
    app = create_app()
    ctx = app.app_context()
    ctx.push()
    return ctx


def refresh_pulse_analytics_for_unit(unit_id: int, days: int = 30, minimum_group_size: int = 5) -> dict[str, Any]:
    """Bir birimin nabız analitiği cache'ini worker içinde yeniler.

    build_pulse_analytics mevcut imzayı korur: user benzeri bir nesne bekler.
    Worker, sadece organization_unit_id taşıyan güvenli bir bağlam nesnesiyle
    analitiği yeniden üretir; anonim kayıtlar yine isimli risk listesine girmez.
    """
    ctx = _ensure_app_context()
    try:
        from app.services.feedback_service import build_pulse_analytics
        actor_context = SimpleNamespace(organization_unit_id=int(unit_id))
        payload = build_pulse_analytics(actor_context, days=max(7, min(int(days or 30), 120)), minimum_group_size=minimum_group_size)
        return {
            "ok": True,
            "unit_id": int(unit_id),
            "days": int(days or 30),
            "generated_at": datetime.now(UTC).isoformat(),
            "participant_count": payload.get("participant_count") if isinstance(payload, dict) else None,
            "eligible": payload.get("eligible") if isinstance(payload, dict) else None,
        }
    finally:
        if ctx is not None:
            ctx.pop()
