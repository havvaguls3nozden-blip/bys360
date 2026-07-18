from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

try:
    from flask_login import current_user
except Exception:  # pragma: no cover
    __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center_engine.py:12")
    current_user = None

from app.models import User
try:
    from app.services.settings.settings_service import get_setting_value, set_setting_value
except Exception:
    __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center_engine.py:19")
    get_setting_value = None
    set_setting_value = None

TASKS: dict[str, dict[str, Any]] = {
    "PERSONEL_MORNING": {"title": "Personel Sabah Bilgilendirmesi", "audience": "staff", "hour": 8, "minute": 0},
    "PERSONEL_NOON": {"title": "Personel Öğlen Bilgilendirmesi", "audience": "staff", "hour": 12, "minute": 30},
    "PERSONEL_EVENING": {"title": "Personel Akşam Bilgilendirmesi", "audience": "staff", "hour": 17, "minute": 30},
    "MANAGER_MORNING": {"title": "Yönetici Sabah Özeti", "audience": "manager", "hour": 7, "minute": 45},
    "MANAGER_EVENING": {"title": "Yönetici Akşam Özeti", "audience": "manager", "hour": 17, "minute": 45},
}

DEFAULT_LOCATION = {"city": "Çanakkale", "latitude": "40.1553", "longitude": "26.4142"}


def _setting(key: str, default: Any = None) -> Any:
    if get_setting_value is None:
        return default
    try:
        v = get_setting_value(key, default)
        return default if v is None else v
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center_engine.py:40")
        return default


def _set(key: str, value: Any, actor_user_id: int | None = None) -> None:
    if set_setting_value is None:
        return
    try:
        set_setting_value(key, value if isinstance(value, str) else json.dumps(value, ensure_ascii=False), actor_user_id=actor_user_id)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center_engine.py:49")
        pass


def _json_setting(key: str, default: Any) -> Any:
    raw = _setting(key, None)
    if raw in (None, ""):
        return default
    if isinstance(raw, (list, dict)):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center_engine.py:61")
        return default


def ensure_defaults(actor_user_id: int | None = None) -> dict[str, Any]:
    current_config()
    if not _setting("cic.v3.initialized", ""):
        for key, meta in TASKS.items():
            _set(f"cic.task.{key}.enabled", "1", actor_user_id)
            _set(f"cic.task.{key}.hour", str(meta["hour"]), actor_user_id)
            _set(f"cic.task.{key}.minute", str(meta["minute"]), actor_user_id)
        _set("cic.location", DEFAULT_LOCATION, actor_user_id)
        _set("cic.v3.initialized", "1", actor_user_id)
    return current_config()


def current_config() -> dict[str, Any]:
    tasks = {}
    for key, meta in TASKS.items():
        tasks[key] = {
            **meta,
            "enabled": str(_setting(f"cic.task.{key}.enabled", "1")).lower() in ("1", "true", "evet", "yes", "on"),
            "hour": int(_setting(f"cic.task.{key}.hour", meta["hour"]) or meta["hour"]),
            "minute": int(_setting(f"cic.task.{key}.minute", meta["minute"]) or meta["minute"]),
            "last_result": _json_setting(f"cic.task.{key}.last_result", {}),
        }
    return {
        "tasks": tasks,
        "location": _json_setting("cic.location", DEFAULT_LOCATION),
        "manager_ids": _json_setting("cic.recipients.manager_ids", []),
        "staff_ids": _json_setting("cic.recipients.staff_ids", []),
    }


def _safe_col(model: Any, names: tuple[str, ...]):
    for name in names:
        col = getattr(model, name, None)
        if col is not None and hasattr(col, "asc"):
            return col
    return None


def list_users(search: str | None = None, limit: int = 500):
    q = User.query
    if search:
        term = f"%{search.strip()}%"
        clauses = []
        for name in ("email", "username", "first_name", "last_name", "name", "sicil_no", "registry_no"):
            col = getattr(User, name, None)
            if col is not None and hasattr(col, "ilike"):
                clauses.append(col.ilike(term))
        # full_name bazı projelerde property olabilir, bu yüzden filtreye zorlamıyoruz.
        if clauses:
            from sqlalchemy import or_
            q = q.filter(or_(*clauses))
    col = _safe_col(User, ("email", "username", "id"))
    if col is not None:
        q = q.order_by(col.asc())
    return q.limit(limit).all()


def get_user_label(user: User) -> str:
    for attr in ("full_name", "name"):
        try:
            val = getattr(user, attr, None)
            if val:
                return str(val)
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center_engine.py:128")
            pass
    first = getattr(user, "first_name", "") or ""
    last = getattr(user, "last_name", "") or ""
    full = f"{first} {last}".strip()
    return full or getattr(user, "email", "") or getattr(user, "username", "") or f"Kullanıcı #{getattr(user, 'id', '')}"


def get_recipients(audience: str):
    cfg = current_config()
    ids = cfg["manager_ids"] if audience == "manager" else cfg["staff_ids"]
    if not ids:
        return []
    return User.query.filter(User.id.in_(ids)).all()


def update_recipients(audience: str, ids: list[int], actor_user_id: int | None = None) -> None:
    clean = []
    for v in ids:
        try:
            iv = int(v)
            if iv not in clean:
                clean.append(iv)
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center_engine.py:151")
            pass
    key = "cic.recipients.manager_ids" if audience == "manager" else "cic.recipients.staff_ids"
    _set(key, clean, actor_user_id)


def _weather_summary(kind: str) -> dict[str, str]:
    # Faz 2 güvenli fallback: dış servis yoksa mail yine gider.
    loc = current_config().get("location") or DEFAULT_LOCATION
    city = loc.get("city") or "Çanakkale"
    today = date.today().strftime("%d.%m.%Y")
    return {
        "city": city,
        "today": today,
        "weather": "Güncel hava durumu servisi Faz 2 yapılandırmasıyla çalışacaktır; servis erişilemezse bu güvenli bilgilendirme metni kullanılır.",
        "clothing": "Sabah ve akşam saatlerinde hava değişimine karşı hafif bir üstlük bulundurmanız önerilir.",
        "tomorrow": "Yarın için hava durumunu gün içinde tekrar kontrol etmeniz önerilir.",
    }


def build_subject(task_key: str) -> str:
    return {
        "PERSONEL_MORNING": "BYS360 Günaydın Bilgilendirmesi",
        "PERSONEL_NOON": "BYS360 Gün Ortası Bilgilendirme Notu",
        "PERSONEL_EVENING": "BYS360 Akşam Bilgilendirmesi ve Yarın İçin Hazırlık",
        "MANAGER_MORNING": "BYS360 Yönetici Sabah Özeti",
        "MANAGER_EVENING": "BYS360 Yönetici Akşam Özeti",
    }.get(task_key, "BYS360 Kurumsal Bilgilendirme")


def build_body(task_key: str, user: User | None = None) -> str:
    name = get_user_label(user) if user else "Değerli çalışma arkadaşımız"
    w = _weather_summary(task_key)
    if task_key == "PERSONEL_MORNING":
        return f"""Merhaba {name},\n\nGünaydın. Bugününüzün verimli, başarılı ve huzurlu geçmesini dileriz.\n\n{w['city']} için günlük bilgilendirme:\n{w['weather']}\n\nKıyafet önerisi:\n{w['clothing']}\n\nİyi çalışmalar dileriz.\n\nBYS360 Kurumsal Bilgilendirme Merkezi"""
    if task_key == "PERSONEL_NOON":
        return f"""Merhaba {name},\n\nMesainizin iyi ve verimli geçtiğini umarız. BYS360 kullanımınızda bir aksaklık, öneri veya geri bildirim ihtiyacınız varsa Geri Bildirim Merkezi üzerinden iletebilirsiniz.\n\nGünün kalan bölümünde kolaylıklar dileriz.\n\nBYS360 Kurumsal Bilgilendirme Merkezi"""
    if task_key == "PERSONEL_EVENING":
        return f"""Merhaba {name},\n\nİyi akşamlar. Bugünkü çalışmalarınız için teşekkür ederiz.\n\nYarın için kısa bilgilendirme:\n{w['tomorrow']}\n\nÖneri:\n{w['clothing']}\n\nSağlıklı ve huzurlu bir akşam dileriz.\n\nBYS360 Kurumsal Bilgilendirme Merkezi"""
    if task_key == "MANAGER_MORNING":
        return f"""Sayın {name},\n\nBYS360 Yönetici Sabah Özeti bilginize sunulur.\n\nBugün izlenmesi önerilen başlıklar:\n- Bekleyen görevler ve onaylar\n- Güncel geri bildirim ve destek talepleri\n- Gün içinde takip edilmesi gereken kurumsal bilgilendirme akışları\n\nİyi çalışmalar dileriz.\n\nBYS360 Kurumsal Bilgilendirme Merkezi"""
    if task_key == "MANAGER_EVENING":
        return f"""Sayın {name},\n\nBYS360 Yönetici Akşam Özeti bilginize sunulur.\n\nGün sonu takip başlıkları:\n- Gün içinde oluşan kayıtlar\n- Bekleyen işlem ve görevler\n- Ertesi gün için dikkat gerektiren alanlar\n\nİyi akşamlar dileriz.\n\nBYS360 Kurumsal Bilgilendirme Merkezi"""
    return "BYS360 Kurumsal Bilgilendirme Merkezi"


def _send_email(to: str, subject: str, body: str) -> bool:
    # Mevcut projedeki mail servislerini dinamik dene; yoksa güvenli dry-run gibi false dönme.
    candidates = [
        ("app.services.mail_service", "send_email"),
        ("app.services.email_service", "send_email"),
        ("app.services.notifications.email", "send_email"),
    ]
    for mod_name, fn_name in candidates:
        try:
            mod = __import__(mod_name, fromlist=[fn_name])
            fn = getattr(mod, fn_name, None)
            if fn:
                try:
                    fn(to=to, subject=subject, body=body)
                except TypeError:
                    fn(to, subject, body)
                return True
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center_engine.py:214")
            continue
    return False




# BYS360_PHASE4B_WEEKEND_MAIL_GUARD_V1_HELPER_START
def _bys360_phase4b_is_weekend(now=None) -> bool:
    """Cumartesi/Pazar otomatik personel gün ortası mailini durdurmak için servis katmanı kilidi."""
    from datetime import datetime as _bys360_weekend_guard_datetime

    current = now or _bys360_weekend_guard_datetime.now()
    try:
        return current.weekday() >= 5
    except Exception:
        return False
# BYS360_PHASE4B_WEEKEND_MAIL_GUARD_V1_HELPER_END

def run_task(task_key: str, *, dry_run: bool = False, force: bool = False, actor_user_id: int | None = None) -> dict[str, Any]:
    # BYS360_PHASE4B_WEEKEND_MAIL_GUARD_V1_START
    if str(task_key or "").strip().upper() == "PERSONEL_NOON" and _bys360_phase4b_is_weekend():
        return {
            "ok": True,
            "skipped": True,
            "reason": "weekend_guard",
            "task_key": "PERSONEL_NOON",
            "message": "Hafta sonu olduğu için Personel Öğlen Bilgilendirmesi gönderilmedi.",
        }
    # BYS360_PHASE4B_WEEKEND_MAIL_GUARD_V1_END
    ensure_defaults(actor_user_id=actor_user_id)
    cfg = current_config()
    task = cfg["tasks"].get(task_key)
    if not task:
        return {"ok": False, "task_key": task_key, "error": "Bilinmeyen görev"}
    if not task.get("enabled") and not force:
        return {"ok": True, "task_key": task_key, "skipped": True, "reason": "Görev pasif"}
    recipients = get_recipients(task["audience"])
    subject = build_subject(task_key)
    sent = 0
    failed = 0
    details = []
    for u in recipients:
        email = getattr(u, "email", None) or getattr(u, "mail", None)
        if not email:
            failed += 1
            details.append({"user_id": getattr(u, "id", None), "ok": False, "reason": "E-posta adresi yok"})
            continue
        body = build_body(task_key, u)
        ok = True if dry_run else _send_email(email, subject, body)
        if ok:
            sent += 1
        else:
            failed += 1
        details.append({"user_id": getattr(u, "id", None), "email": email, "ok": ok})
    result = {
        "ok": failed == 0,
        "dry_run": dry_run,
        "task_key": task_key,
        "task_title": task["title"],
        "recipient_count": len(recipients),
        "sent": sent,
        "failed": failed,
        "ran_at": datetime.now().isoformat(timespec="seconds"),
        "details": details[:50],
    }
    _set(f"cic.task.{task_key}.last_result", result, actor_user_id)
    return result


def dashboard_context(search: str | None = None) -> dict[str, Any]:
    ensure_defaults()
    cfg = current_config()
    return {
        "config": cfg,
        "tasks": cfg["tasks"],
        "manager_recipients": get_recipients("manager"),
        "staff_recipients": get_recipients("staff"),
        "users": list_users(search=search, limit=500),
        "search": search or "",
        "logs": [t.get("last_result", {}) for t in cfg["tasks"].values() if t.get("last_result")],
        "location": cfg.get("location") or DEFAULT_LOCATION,
        "get_user_label": get_user_label,
    }
