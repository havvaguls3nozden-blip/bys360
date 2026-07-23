"""Canonical CIC scheduler configuration and due-task orchestration."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from app.extensions import db
from app.services.cic.cic_context import (
    _cic_auto_last_run_key,
    _cic_is_weekend,
    _cic_weekday_name_tr,
)
from app.services.cic.config_context import (
    _now,
    ensure_defaults,
    get_config,
    get_setting,
    set_setting,
)
from app.services.cic.mail_service import send_task
from app.services.cic.task_contract import BASE_KEY, TASK_DEFINITIONS

logger = logging.getLogger(__name__)

__all__ = [
    "_run_due_tasks_base",
    "get_auto_scheduler_config",
    "run_due_tasks",
    "set_auto_scheduler_config",
]


def _cic_auto_bool(value: object, default: bool = False) -> bool:
    if value is None:
        return default
    text = str(value).strip().lower()
    if not text:
        return default
    return text in {"1", "true", "on", "yes", "evet", "aktif", "checked"}


def get_auto_scheduler_config() -> dict[str, object]:
    enabled_raw = get_setting(f"{BASE_KEY}.auto_scheduler_enabled", "false") or "false"
    weekdays_raw = get_setting(f"{BASE_KEY}.auto_scheduler_weekdays_only", "true") or "true"
    try:
        late_window = int(get_setting(f"{BASE_KEY}.auto_scheduler_late_window_minutes", "20") or "20")
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:1769")
        late_window = 20
    late_window = max(1, min(120, late_window))
    return {
        "enabled": _cic_auto_bool(enabled_raw, default=False),
        "weekdays_only": _cic_auto_bool(weekdays_raw, default=True),
        "late_window_minutes": late_window,
        "windows_task_name": "BYS360 CIC Auto Mail Scheduler",
        "poll_interval_minutes": 5,
        "description": "Windows görevi yalnızca yoklama yapar; hangi mailin aktif/pasif olduğu, saati ve hafta içi kuralı BYS360 ekranlarından yönetilir.",
        "weekend_policy": "Cumartesi ve pazar günleri otomatik mail gönderilmez.",
    }


def set_auto_scheduler_config(payload: dict[str, object], actor_user_id: int | None = None) -> None:
    enabled = "true" if _cic_auto_bool(payload.get("auto_scheduler_enabled"), default=False) else "false"
    if "auto_scheduler_weekdays_only" in payload:
        weekdays_only = "true" if _cic_auto_bool(payload.get("auto_scheduler_weekdays_only"), default=True) else "false"
    else:
        weekdays_only = str(get_setting(f"{BASE_KEY}.auto_scheduler_weekdays_only", "true") or "true").lower()
        if weekdays_only not in {"true", "false"}:
            weekdays_only = "true"
    try:
        late_window = int(payload.get("auto_scheduler_late_window_minutes") or 20)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:1793")
        late_window = 20
    late_window = max(1, min(120, late_window))

    set_setting(f"{BASE_KEY}.auto_scheduler_enabled", enabled, label="Otomatik mail zamanlayıcı", value_type="boolean", actor_user_id=actor_user_id)
    set_setting(f"{BASE_KEY}.auto_scheduler_weekdays_only", weekdays_only, label="Otomatik mail yalnızca hafta içi", value_type="boolean", actor_user_id=actor_user_id)
    set_setting(f"{BASE_KEY}.auto_scheduler_late_window_minutes", str(late_window), label="Otomatik mail gecikme toleransı", value_type="integer", actor_user_id=actor_user_id)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()


def _run_due_tasks_base(*, now: datetime | None = None, dry_run: bool = False, actor_user_id: int | None = None, force: bool = False) -> dict[str, Any]:
    """Zamanı gelen aktif mail görevlerini çalıştırır; hafta sonu otomatik gönderimi engeller."""
    ensure_defaults(actor_user_id=actor_user_id)
    scheduler = get_auto_scheduler_config()
    current = now or _now()
    today = current.strftime("%Y-%m-%d")
    weekday_name = _cic_weekday_name_tr(current)

    if not scheduler.get("enabled") and not force:
        return {
            "ok": True,
            "scheduler_enabled": False,
            "message": "Otomatik mail zamanlayıcısı BYS360 Sistem ekranında pasif.",
            "now": current.strftime("%Y-%m-%d %H:%M:%S"),
            "weekday": weekday_name,
            "ran": [],
            "skipped": [],
        }

    if bool(scheduler.get("weekdays_only", True)) and _cic_is_weekend(current) and not force:
        return {
            "ok": True,
            "scheduler_enabled": True,
            "weekdays_only": True,
            "weekend_blocked": True,
            "dry_run": dry_run,
            "force": force,
            "now": current.strftime("%Y-%m-%d %H:%M:%S"),
            "weekday": weekday_name,
            "message": "Bugün hafta sonu olduğu için otomatik mail gönderimi yapılmadı.",
            "results": [],
            "ran": [],
            "skipped": [{"action": "skipped", "reason": "Hafta sonu otomatik gönderim kapalı", "weekday": weekday_name}],
            "ran_any": False,
        }

    cfg = get_config()
    tasks_cfg = cfg.get("tasks", {}) if isinstance(cfg, dict) else {}
    late_window = int(scheduler.get("late_window_minutes") or 20)
    results: list[dict[str, Any]] = []
    ran_any = False

    for task_key, meta in TASK_DEFINITIONS.items():
        task_cfg = tasks_cfg.get(task_key, {}) if isinstance(tasks_cfg, dict) else {}
        enabled = bool(task_cfg.get("enabled", False))
        try:
            hour = int(task_cfg.get("hour", meta.get("default_hour", 12)))
            minute = int(task_cfg.get("minute", meta.get("default_minute", 0)))
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:1884")
            hour = int(meta.get("default_hour", 12))
            minute = int(meta.get("default_minute", 0))
        scheduled = current.replace(hour=max(0, min(23, hour)), minute=max(0, min(59, minute)), second=0, microsecond=0)
        diff_minutes = (current - scheduled).total_seconds() / 60.0
        last_run = get_setting(_cic_auto_last_run_key(task_key), "") or ""
        already_today = last_run.startswith(today)

        row: dict[str, Any] = {
            "task_key": task_key,
            "task_label": meta.get("label", task_key),
            "enabled": enabled,
            "scheduled_time": f"{hour:02d}:{minute:02d}",
            "last_auto_run": last_run,
            "weekday": weekday_name,
        }

        if not enabled:
            row.update({"action": "skipped", "reason": "Görev pasif"})
            results.append(row)
            continue
        if already_today and not force:
            row.update({"action": "skipped", "reason": "Bugün zaten otomatik çalıştı"})
            results.append(row)
            continue
        if not force and not (0 <= diff_minutes <= late_window):
            row.update({"action": "waiting", "reason": f"Zamanı gelmedi veya {late_window} dk tolerans dışında"})
            results.append(row)
            continue

        result = send_task(task_key, dry_run=dry_run, actor_user_id=actor_user_id)
        set_setting(_cic_auto_last_run_key(task_key), current.strftime("%Y-%m-%d %H:%M:%S"), label=f"{meta.get('label', task_key)} son otomatik çalışma", actor_user_id=actor_user_id)
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
        row.update({"action": "ran", "result": result})
        results.append(row)
        ran_any = True

    return {
        "ok": True,
        "scheduler_enabled": True,
        "weekdays_only": bool(scheduler.get("weekdays_only", True)),
        "weekend_blocked": False,
        "dry_run": dry_run,
        "force": force,
        "now": current.strftime("%Y-%m-%d %H:%M:%S"),
        "weekday": weekday_name,
        "late_window_minutes": late_window,
        "ran_any": ran_any,
        "results": results,
        "ran": [r for r in results if r.get("action") == "ran"],
        "skipped": [r for r in results if r.get("action") != "ran"],
    }


def run_due_tasks(*, now: datetime | None = None, dry_run: bool = False, actor_user_id: int | None = None, force: bool = False) -> dict[str, Any]:
    """Run due CIC mail tasks through one explicit public layer.

    Flattened legacy wrapper chain:
    - Base scheduler execution is handled by _run_due_tasks_base.
    - Weekend celebration exception tasks are applied explicitly after the base result.
    """
    from app.services.cic.celebration_service import _cic_v40_run_weekend_celebrations

    result = _run_due_tasks_base(now=now, dry_run=dry_run, actor_user_id=actor_user_id, force=force)

    current = now or _now()
    if result.get("weekend_blocked") and not force:
        extra = _cic_v40_run_weekend_celebrations(current, dry_run=dry_run, actor_user_id=actor_user_id)
        if extra:
            result["weekend_blocked"] = False
            result["message"] = "Hafta sonu genel gonderimler engellendi; kutlama gorevleri ayar geregi calistirildi."
            result.setdefault("results", []).extend(extra)
            result["ran"] = list(result.get("ran") or []) + extra
            result["ran_any"] = True

    return result
