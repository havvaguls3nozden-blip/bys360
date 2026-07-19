from __future__ import annotations


import json
import subprocess
from typing import Any

from flask import current_app
import logging
logger = logging.getLogger(__name__)

try:
    from app import db
except Exception:
    logger.exception("BYS360 V6C guarded exception | file=app/services/executive_mail_center.py | line=14")
    db = None

try:
    from sqlalchemy import inspect, text
except Exception:
    logger.exception("BYS360 V6C guarded exception | file=app/services/executive_mail_center.py | line=19")
    text = None

MAIL_CENTER_VERSION = "BYS360_EXECUTIVE_MAIL_CENTER_V1_6_FULL_PAGES"

DEFAULT_TASKS = [
    {
        "key": "morning_weather",
        "title": "Sabah Hava Durumu ve Kıyafet Önerisi",
        "description": "Bugünün hava durumu, ertesi gün tahmini, kıyafet önerisi ve iyi dilek mesajı.",
        "script": "scripts/communication/send_daily_weather_personnel_mail.py",
        "task_name": "BYS360 Daily Weather Personnel Mail",
        "default_time": "08:15",
        "status": "Aktif",
    },
    {
        "key": "midday_pulse",
        "title": "Gün Ortası Kontrol Maili",
        "description": "Günün nasıl geçtiği, sistem kullanımı ve geri bildirim bağlantısı için kısa kontrol maili.",
        "script": "scripts/communication/send_daily_pulse_check_mail.py",
        "task_name": "BYS360 Daily Pulse Check Mail",
        "default_time": "13:00",
        "status": "Pilot",
    },
    {
        "key": "evening_tomorrow",
        "title": "Akşam Ertesi Gün Bilgilendirmesi",
        "description": "Ertesi gün beklenen hava durumu, hazırlık notu ve iyi akşamlar mesajı.",
        "script": "scripts/communication/send_daily_evening_tomorrow_mail.py",
        "task_name": "BYS360 Daily Evening Tomorrow Mail",
        "default_time": "17:00",
        "status": "Pilot",
    },
]

def _db_ready() -> bool:
    return db is not None and text is not None

def _system_settings_columns() -> set[str]:
    if not _db_ready():
        return set()
    try:
        return {str(col.get("name")) for col in inspect(db.engine).get_columns("system_settings") if col.get("name")}
    except Exception:
        logger.exception("BYS360 settings hardening: system_settings kolonları okunamadı")
        return set()


def _setting_get(key: str, default: str = "") -> str:
    if not _db_ready():
        return default
    try:
        cols = _system_settings_columns()
        if {"setting_key", "value_text"} <= cols:
            row = db.session.execute(text("SELECT value_text FROM system_settings WHERE setting_key=:k LIMIT 1"), {"k": key}).fetchone()
        elif {"key", "value"} <= cols:
            row = db.session.execute(text("SELECT value FROM system_settings WHERE key=:k LIMIT 1"), {"k": key}).fetchone()
        else:
            return default
        return str(row[0]) if row and row[0] is not None else default
    except Exception:
        logger.exception("BYS360 settings hardening: system setting read failed | key=%s", key)
        return default


def _setting_set(key: str, value: str) -> None:
    if not _db_ready():
        return
    try:
        cols = _system_settings_columns()
        if {"setting_key", "value_text"} <= cols:
            exists = db.session.execute(text("SELECT id FROM system_settings WHERE setting_key=:k LIMIT 1"), {"k": key}).fetchone()
            if exists:
                db.session.execute(text("UPDATE system_settings SET value_text=:v, updated_at=CURRENT_TIMESTAMP WHERE setting_key=:k"), {"k": key, "v": value})
            else:
                db.session.execute(text("INSERT INTO system_settings (setting_key, group_key, label, value_text, value_type, description, is_active) VALUES (:k, 'mail', :label, :v, 'json', :desc, 1)"), {"k": key, "v": value, "label": key, "desc": "Yönetici mail merkezi ayarı"})
        elif {"key", "value"} <= cols:
            exists = db.session.execute(text("SELECT id FROM system_settings WHERE key=:k LIMIT 1"), {"k": key}).fetchone()
            if exists:
                db.session.execute(text("UPDATE system_settings SET value=:v WHERE key=:k"), {"k": key, "v": value})
            else:
                db.session.execute(text("INSERT INTO system_settings (key, value) VALUES (:k, :v)"), {"k": key, "v": value})
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

def get_mail_tasks() -> list[dict[str, Any]]:
    raw = _setting_get("executive_mail_center.tasks_json", "")
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, list) and data:
                return data
        except Exception:
            logger.exception("BYS360 V6C guarded exception | file=app/services/executive_mail_center.py | line=87")
            pass
    return DEFAULT_TASKS

def save_mail_tasks(tasks: list[dict[str, Any]]) -> None:
    _setting_set("executive_mail_center.tasks_json", json.dumps(tasks, ensure_ascii=False))

def get_selected_recipients() -> list[dict[str, Any]]:
    ids = []
    raw = _setting_get("daily_weather_mail.recipient_user_ids", "[]")
    try:
        ids = [int(x) for x in json.loads(raw or "[]")]
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/executive_mail_center.py | line=99")
        ids = []
    if not ids or not _db_ready():
        return []
    rows = db.session.execute(text("""
        SELECT id, full_name, email, username, title, unit_name
        FROM users
        WHERE id = ANY(:ids)
        ORDER BY full_name
    """), {"ids": ids}).mappings().all()
    return [dict(r) for r in rows]

def list_users(q: str = "") -> list[dict[str, Any]]:
    if not _db_ready():
        return []
    like = f"%{q.lower()}%"
    rows = db.session.execute(text("""
        SELECT id, full_name, email, username, title, unit_name
        FROM users
        WHERE COALESCE(is_active, true)=true
          AND (:q='' OR lower(COALESCE(full_name,'')) LIKE :like OR lower(COALESCE(email,'')) LIKE :like OR lower(COALESCE(username,'')) LIKE :like)
        ORDER BY full_name
        LIMIT 300
    """), {"q": q.lower(), "like": like}).mappings().all()
    return [dict(r) for r in rows]

def save_recipients(user_ids: list[int]) -> None:
    clean = []
    for x in user_ids:
        try:
            clean.append(int(x))
        except Exception:
            logger.exception("BYS360 V6C guarded exception | file=app/services/executive_mail_center.py | line=130")
            continue
    clean = sorted(set(clean))
    _setting_set("daily_weather_mail.recipient_user_ids", json.dumps(clean, ensure_ascii=False))
    _setting_set("executive_mail_center.pilot_mode", "1")

def get_recent_mail_logs(limit: int = 50) -> list[dict[str, Any]]:
    if not _db_ready():
        return []
    candidates = [
        "mail_logs", "email_logs", "notification_mail_logs"
    ]
    for table in candidates:
        try:
            rows = db.session.execute(text(f"""
                SELECT *
                FROM {table}
                ORDER BY COALESCE(created_at, sent_at, updated_at, now()) DESC
                LIMIT :limit
            """), {"limit": limit}).mappings().all()
            return [dict(r) for r in rows]
        except Exception:
            logger.exception("BYS360 V6C guarded exception | file=app/services/executive_mail_center.py | line=151")
            continue
    return []

def get_scheduled_task_statuses() -> list[dict[str, Any]]:
    result = []
    if not hasattr(subprocess, "run"):
        return result
    for t in DEFAULT_TASKS:
        try:
            p = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", f"Get-ScheduledTask -TaskName '{t['task_name']}' | Select-Object TaskName,State | ConvertTo-Json -Compress"],
                capture_output=True, text=True, timeout=8
            )
            status = p.stdout.strip() or p.stderr.strip()
            result.append({"task_name": t["task_name"], "status": status, "ok": p.returncode == 0})
        except Exception as exc:
            logger.exception("BYS360 V6C guarded exception | file=app/services/executive_mail_center.py | line=167")
            result.append({"task_name": t["task_name"], "status": str(exc), "ok": False})
    return result

def run_task_script(script: str, dry_run: bool = False) -> dict[str, Any]:
    import sys
    from pathlib import Path
    project_root = Path(current_app.root_path).parent
    py = project_root / ".venv" / "Scripts" / "python.exe"
    if not py.exists():
        py = Path(sys.executable)
    cmd = [str(py), str(project_root / script)]
    if dry_run:
        cmd.append("--dry-run")
    else:
        cmd.append("--force")
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=str(project_root))
        return {
            "ok": p.returncode == 0,
            "returncode": p.returncode,
            "stdout": p.stdout[-4000:],
            "stderr": p.stderr[-4000:],
            "command": " ".join(cmd),
        }
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/services/executive_mail_center.py | line=192")
        return {"ok": False, "error": str(exc), "command": " ".join(cmd)}
