from __future__ import annotations

import json
import ssl
import time
from datetime import datetime
from typing import Any
from urllib.request import urlopen

from flask import current_app
from sqlalchemy import or_

from app.extensions import db
from app.models import SystemSetting, User

try:
    from app.services.mail_core import send_email, create_mail_log
except Exception:  # pragma: no cover
    __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/corporate_information_center.py:20")
    send_email = None
    create_mail_log = None

VERSION = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE1"
GROUP_KEY = "corporate_information_center"
BASE_KEY = "corporate_information_center"
ADMIN_ROLES = {"admin", "administrator", "super_admin", "system_admin", "sistem_yoneticisi"}

TASK_DEFINITIONS: dict[str, dict[str, Any]] = {
    "staff_morning": {
        "category": "personel",
        "label": "Personel Sabah Bilgilendirmesi",
        "short_label": "Sabah Personel",
        "default_hour": 8,
        "default_minute": 0,
        "icon": "fa-sun",
        "description": "Günaydın mesajı, bugünkü hava durumu, kıyafet önerisi ve iyi dilek.",
        "recipient_group": "staff",
        "subject": "Günaydın | BYS360 Günlük Bilgilendirme",
        "body": """Sayın {ad_soyad},

Günaydın.

Bugün {konum} için hava durumu özeti:
{bugun_hava}

Kıyafet önerisi:
{kiyafet_onerisi}

Başarılı, verimli ve güzel bir gün geçirmenizi dileriz.

BYS360
Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı""",
    },
    # BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE6_1_STAFF_NOON_MESSAGE
    "staff_noon": {
        "category": "personel",
        "label": "Personel Öğlen Bilgilendirmesi",
        "short_label": "Öğlen Personel",
        "default_hour": 12,
        "default_minute": 30,
        "icon": "fa-mug-hot",
        "description": "Gün ortası iyi dilek, mesai kontrolü ve geri bildirim hatırlatması.",
        "recipient_group": "staff",
        "subject": "BYS360 Gün Ortası Destek Hatırlatması",
        "body": """Sayın {ad_soyad},

Gününüz nasıl geçiyor?

Sistemde destek ihtiyacı duyduğunuz bir konu var mı?

BYS360 kullanımı sırasında destek, öneri, hata bildirimi veya geliştirme ihtiyacı oluşursa Geri Bildirim Merkezi üzerinden bize iletebilirsiniz.

Geri bildirim bağlantısı:
{geri_bildirim_baglantisi}

İyi çalışmalar dileriz.

BYS360
Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı""",
    },
    "staff_evening": {
        "category": "personel",
        "label": "Personel Akşam Bilgilendirmesi",
        "short_label": "Akşam Personel",
        "default_hour": 17,
        "default_minute": 30,
        "icon": "fa-cloud-moon",
        "description": "İyi akşamlar mesajı, yarın hava durumu ve ertesi gün hazırlık notu.",
        "recipient_group": "staff",
        "subject": "İyi Akşamlar | BYS360 Yarın İçin Bilgilendirme",
        "body": """Sayın {ad_soyad},

İyi akşamlar.

Yarın {konum} için beklenen hava durumu:
{yarin_hava}

Yarın için öneri:
{yarin_oneri}

Bugünkü emekleriniz için teşekkür eder, güzel bir akşam dileriz.

BYS360""",
    },
    "manager_morning": {
        "category": "yonetici",
        "label": "Yönetici Sabah Özeti",
        "short_label": "Sabah Yönetici",
        "default_hour": 7,
        "default_minute": 45,
        "icon": "fa-chart-line",
        "description": "Yöneticiler için gün başlangıcı kısa kurum içi durum özeti.",
        "recipient_group": "managers",
        "subject": "BYS360 Yönetici Sabah Özeti",
        "body": """Sayın {ad_soyad},

BYS360 gün başlangıcı yönetici özeti aşağıdadır.

Tarih: {tarih}
Aktif personel sayısı: {aktif_personel_sayisi}
Son bilgilendirme durumu: {son_gonderim_durumu}
Bugün takip edilecek ana başlık: {gunun_notu}

Sistem bağlantısı:
{bys360_baglanti}

İyi çalışmalar dileriz.

BYS360""",
    },
    "manager_evening": {
        "category": "yonetici",
        "label": "Yönetici Akşam Özeti",
        "short_label": "Akşam Yönetici",
        "default_hour": 17,
        "default_minute": 45,
        "icon": "fa-clipboard-check",
        "description": "Yöneticiler için gün sonu kısa durum ve ertesi gün dikkat notu.",
        "recipient_group": "managers",
        "subject": "BYS360 Yönetici Akşam Özeti",
        "body": """Sayın {ad_soyad},

BYS360 gün sonu yönetici özeti aşağıdadır.

Tarih: {tarih}
Son gönderim durumu: {son_gonderim_durumu}
Yarın için dikkat notu: {yarin_yonetici_notu}

Sistem bağlantısı:
{bys360_baglanti}

İyi akşamlar dileriz.

BYS360""",
    },
}


def _now() -> datetime:
    return datetime.now()


def _has_settings_table() -> bool:
    try:
        from sqlalchemy import inspect as sa_inspect
        return bool(sa_inspect(db.engine).has_table("system_settings"))
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/corporate_information_center.py:168")
        return False


def get_setting(key: str, default: str = "") -> str:
    if not _has_settings_table():
        return default
    row = SystemSetting.query.filter_by(setting_key=key).first()
    if not row:
        return default
    return row.value_text if row.value_text is not None else default


def set_setting(key: str, value: str, *, label: str | None = None, description: str | None = None, value_type: str = "string", actor_user_id: int | None = None) -> None:
    if not _has_settings_table():
        return
    row = SystemSetting.query.filter_by(setting_key=key).first()
    if not row:
        row = SystemSetting(setting_key=key, group_key=GROUP_KEY, label=label or key, value_type=value_type, description=description or "")
        db.session.add(row)
    row.value_text = value
    row.group_key = GROUP_KEY
    row.label = label or row.label or key
    row.value_type = value_type or row.value_type or "string"
    if description is not None:
        row.description = description
    if actor_user_id is not None:
        row.updated_by_user_id = actor_user_id


def _loads_json(key: str, default: Any) -> Any:
    raw = get_setting(key, "")
    if not raw:
        return default
    try:
        return json.loads(raw)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/corporate_information_center.py:204")
        return default


def _dumps_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def can_manage(user: Any) -> bool:
    if not getattr(user, "is_authenticated", False):
        return False
    role = str(getattr(user, "role", "") or "").lower()
    return role in ADMIN_ROLES


def _ensure_defaults_base(actor_user_id: int | None = None) -> None:
    tasks = _loads_json(f"{BASE_KEY}.tasks", None)
    if not isinstance(tasks, dict):
        tasks = {}
    changed = False
    for key, meta in TASK_DEFINITIONS.items():
        if key not in tasks or not isinstance(tasks.get(key), dict):
            tasks[key] = {
                "enabled": True,
                "hour": meta["default_hour"],
                "minute": meta["default_minute"],
                "recipient_group": meta["recipient_group"],
                "last_status": "Henüz çalışmadı",
                "last_run_at": "",
            }
            changed = True
        else:
            for f, default in (("enabled", True), ("hour", meta["default_hour"]), ("minute", meta["default_minute"]), ("recipient_group", meta["recipient_group"])):
                if f not in tasks[key]:
                    tasks[key][f] = default
                    changed = True
    if changed:
        set_setting(f"{BASE_KEY}.tasks", _dumps_json(tasks), label="Kurumsal bilgilendirme görevleri", value_type="json", actor_user_id=actor_user_id)

    if get_setting(f"{BASE_KEY}.staff_recipient_mode", "") == "":
        set_setting(f"{BASE_KEY}.staff_recipient_mode", "manual", label="Personel alıcı modu", value_type="string", actor_user_id=actor_user_id)
    if get_setting(f"{BASE_KEY}.manager_recipient_ids", "") == "":
        set_setting(f"{BASE_KEY}.manager_recipient_ids", "[]", label="Yönetici alıcıları", value_type="json", actor_user_id=actor_user_id)
    if get_setting(f"{BASE_KEY}.staff_recipient_ids", "") == "":
        set_setting(f"{BASE_KEY}.staff_recipient_ids", "[]", label="Personel alıcıları", value_type="json", actor_user_id=actor_user_id)
    if get_setting(f"{BASE_KEY}.location_name", "") == "":
        set_setting(f"{BASE_KEY}.location_name", "Çanakkale", label="Hava durumu konumu", actor_user_id=actor_user_id)
    if get_setting(f"{BASE_KEY}.latitude", "") == "":
        set_setting(f"{BASE_KEY}.latitude", "40.1553", label="Enlem", actor_user_id=actor_user_id)
    if get_setting(f"{BASE_KEY}.longitude", "") == "":
        set_setting(f"{BASE_KEY}.longitude", "26.4142", label="Boylam", actor_user_id=actor_user_id)
    for key, meta in TASK_DEFINITIONS.items():
        s_key = f"{BASE_KEY}.template.{key}.subject"
        b_key = f"{BASE_KEY}.template.{key}.body"
        if get_setting(s_key, "") == "":
            set_setting(s_key, meta["subject"], label=f"{meta['label']} konusu", actor_user_id=actor_user_id)
        if get_setting(b_key, "") == "":
            set_setting(b_key, meta["body"], label=f"{meta['label']} metni", value_type="text", actor_user_id=actor_user_id)
    db.session.commit()


def get_config() -> dict[str, Any]:
    ensure_defaults()
    return {
        "tasks": _loads_json(f"{BASE_KEY}.tasks", {}),
        "staff_recipient_mode": get_setting(f"{BASE_KEY}.staff_recipient_mode", "manual") or "manual",
        "manager_recipient_ids": _clean_ids(_loads_json(f"{BASE_KEY}.manager_recipient_ids", [])),
        "staff_recipient_ids": _clean_ids(_loads_json(f"{BASE_KEY}.staff_recipient_ids", [])),
        "location_name": get_setting(f"{BASE_KEY}.location_name", "Çanakkale") or "Çanakkale",
        "latitude": get_setting(f"{BASE_KEY}.latitude", "40.1553") or "40.1553",
        "longitude": get_setting(f"{BASE_KEY}.longitude", "26.4142") or "26.4142",
    }


def _clean_ids(values: Any) -> list[int]:
    out: list[int] = []
    for v in values or []:
        try:
            iv = int(v)
            if iv not in out:
                out.append(iv)
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:288")
            pass
    return out


def save_tasks(payload: dict[str, Any], actor_user_id: int | None = None) -> None:
    cfg = get_config()
    tasks = cfg["tasks"]
    for key, meta in TASK_DEFINITIONS.items():
        t = tasks.setdefault(key, {})
        t["enabled"] = str(payload.get(f"enabled_{key}", "")).lower() in {"1", "true", "on", "yes"}
        try:
            t["hour"] = max(0, min(23, int(payload.get(f"hour_{key}", meta["default_hour"]))))
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:301")
            t["hour"] = meta["default_hour"]
        try:
            t["minute"] = max(0, min(59, int(payload.get(f"minute_{key}", meta["default_minute"]))))
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:305")
            t["minute"] = meta["default_minute"]
        t["recipient_group"] = meta["recipient_group"]
    set_setting(f"{BASE_KEY}.tasks", _dumps_json(tasks), label="Kurumsal bilgilendirme görevleri", value_type="json", actor_user_id=actor_user_id)
    db.session.commit()

def save_templates(payload: dict[str, Any], actor_user_id: int | None = None) -> None:
    for key, meta in TASK_DEFINITIONS.items():
        subject = (payload.get(f"subject_{key}") or meta["subject"]).strip()
        body = (payload.get(f"body_{key}") or meta["body"]).strip()
        set_setting(f"{BASE_KEY}.template.{key}.subject", subject, label=f"{meta['label']} konusu", actor_user_id=actor_user_id)
        set_setting(f"{BASE_KEY}.template.{key}.body", body, label=f"{meta['label']} metni", value_type="text", actor_user_id=actor_user_id)
    db.session.commit()


def _save_system_base(payload: dict[str, Any], actor_user_id: int | None = None) -> None:
    set_setting(f"{BASE_KEY}.location_name", (payload.get("location_name") or "Çanakkale").strip(), label="Hava durumu konumu", actor_user_id=actor_user_id)
    set_setting(f"{BASE_KEY}.latitude", (payload.get("latitude") or "40.1553").strip(), label="Enlem", actor_user_id=actor_user_id)
    set_setting(f"{BASE_KEY}.longitude", (payload.get("longitude") or "26.4142").strip(), label="Boylam", actor_user_id=actor_user_id)
    db.session.commit()


def _user_name(user: User | None) -> str:
    if not user:
        return "-"
    return (f"{getattr(user, 'ad', '') or ''} {getattr(user, 'soyad', '') or ''}".strip()
            or getattr(user, "full_name_cache", None)
            or getattr(user, "email", None)
            or f"Kullanıcı #{getattr(user, 'id', '-')}")


def list_users(search: str | None = None, limit: int = 800) -> list[User]:
    q = User.query
    if hasattr(User, "is_active"):
        try:
            q = q.filter(User.is_active.is_(True))
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:354")
            pass
    if search:
        s = f"%{search.strip()}%"
        clauses = []
        for attr in ("ad", "soyad", "email", "sicil_no", "birim", "ust_birim", "unvan", "role_label", "username"):
            col = getattr(User, attr, None)
            if col is not None and hasattr(col, "ilike"):
                clauses.append(col.ilike(s))
        if clauses:
            q = q.filter(or_(*clauses))
    # Güvenli sıralama: full_name/ad gibi property olabilecek alanlar order_by içinde kullanılmaz.
    try:
        return q.order_by(User.id.asc()).limit(limit).all()
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/corporate_information_center.py:365")
        return q.limit(limit).all()


def _users_by_ids(ids: list[int]) -> list[User]:
    if not ids:
        return []
    rows = User.query.filter(User.id.in_(ids)).all()
    order = {uid: idx for idx, uid in enumerate(ids)}
    return sorted(rows, key=lambda u: order.get(getattr(u, "id", 0), 999999))


def _active_staff_users() -> list[User]:
    q = User.query
    if hasattr(User, "is_active"):
        try:
            q = q.filter(User.is_active.is_(True))
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:386")
            pass
    if hasattr(User, "email"):
        q = q.filter(User.email.isnot(None), User.email != "")
    try:
        return q.order_by(User.id.asc()).all()
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/corporate_information_center.py:388")
        return q.all()


def get_recipients() -> dict[str, Any]:
    cfg = get_config()
    managers = _users_by_ids(cfg["manager_recipient_ids"])
    if cfg["staff_recipient_mode"] == "all_active":
        staff = _active_staff_users()
    else:
        staff = _users_by_ids(cfg["staff_recipient_ids"])
    return {"managers": managers, "staff": staff, "staff_mode": cfg["staff_recipient_mode"]}


def _weather() -> dict[str, str]:
    cfg = get_config()
    lat = cfg["latitude"]
    lon = cfg["longitude"]
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode&timezone=auto&forecast_days=2"
    try:
        with urlopen(url, timeout=8, context=ssl.create_default_context()) as r:
            data = json.loads(r.read().decode("utf-8"))
        cur = data.get("current_weather", {}) or {}
        daily = data.get("daily", {}) or {}
        today = _format_weather(cur.get("temperature"), daily, 0)
        tomorrow = _format_weather(None, daily, 1)
        temp = cur.get("temperature")
        return {
            "bugun_hava": today,
            "yarin_hava": tomorrow,
            "kiyafet_onerisi": _clothing(temp),
            "yarin_oneri": _tomorrow_note(tomorrow),
        }
    except Exception as exc:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:426")
        msg = f"Güncel hava durumu verisi şu anda alınamadı. Kontrol notu: {exc}"
        return {"bugun_hava": msg, "yarin_hava": msg, "kiyafet_onerisi": "Hava değişimlerine karşı hazırlıklı olunması önerilir.", "yarin_oneri": "Sabah çıkmadan güncel hava durumunu kontrol ediniz."}


def _format_weather(current_temp: Any, daily: dict[str, Any], idx: int) -> str:
    mins = daily.get("temperature_2m_min") or []
    maxs = daily.get("temperature_2m_max") or []
    probs = daily.get("precipitation_probability_max") or []
    parts = []
    if current_temp is not None:
        parts.append(f"Anlık sıcaklık: {current_temp}°C")
    if idx < len(mins) and idx < len(maxs):
        parts.append(f"Beklenen aralık: {mins[idx]}°C / {maxs[idx]}°C")
    if idx < len(probs):
        parts.append(f"Yağış olasılığı: %{probs[idx]}")
    return "\n".join(parts) if parts else "Hava durumu verisi sınırlı olarak alınabildi."


def _clothing(temp: Any) -> str:
    try:
        t = float(temp)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:448")
        return "Katmanlı ve mevsime uygun kıyafet tercih edilmesi önerilir."
    if t < 8:
        return "Kalın mont, kapalı ayakkabı ve soğuğa karşı koruyucu kıyafet önerilir."
    if t < 16:
        return "Sabah saatleri için ceket veya hırka önerilir."
    if t < 25:
        return "Hafif bir üstlük bulundurmak yeterli olabilir."
    return "Hafif, rahat ve hava alan kıyafet tercih edilebilir; su tüketimine dikkat edilmelidir."


def _tomorrow_note(weather_text: str) -> str:
    if "Yağış olasılığı" in weather_text:
        return "Yarın için ulaşım ve dış görev planlarında hava durumunu dikkate alınız."
    return "Yarınki mesai için planlamalarınızı güncel hava durumuna göre yapabilirsiniz."


def _dashboard_counts() -> dict[str, str]:
    try:
        active_count = User.query.filter(User.is_active.is_(True)).count() if hasattr(User, "is_active") else User.query.count()
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:468")
        active_count = "-"
    return {
        "aktif_personel_sayisi": active_count,
        "son_gonderim_durumu": get_setting(f"{BASE_KEY}.last_status", "Henüz gönderim yapılmadı") or "Henüz gönderim yapılmadı",
        "gunun_notu": "BYS360 süreçlerinin gün içinde düzenli izlenmesi önerilir.",
        "yarin_yonetici_notu": "Ertesi gün için bekleyen görev ve geri bildirimlerin kontrol edilmesi önerilir.",
    }


def _render_template_text_base(text: str, user: User | None, task_key: str) -> str:
    cfg = get_config()
    w = _weather() if task_key.startswith("staff_") else {"bugun_hava": "-", "yarin_hava": "-", "kiyafet_onerisi": "-", "yarin_oneri": "-"}
    counts = _dashboard_counts()
    context = {
        "ad_soyad": _user_name(user),
        "email": getattr(user, "email", "") if user else "",
        "tarih": _now().strftime("%d.%m.%Y"),
        "saat": _now().strftime("%H:%M"),
        "konum": cfg["location_name"],
        "bys360_baglanti": "https://bys360.canakkaletarihialan.gov.tr/",
        "geri_bildirim_baglantisi": "https://bys360.canakkaletarihialan.gov.tr/feedback",
        **w,
        **counts,
    }
    rendered = text or ""
    for k, v in context.items():
        rendered = rendered.replace("{" + k + "}", str(v))
    return rendered


def get_template(task_key: str) -> dict[str, str]:
    meta = TASK_DEFINITIONS[task_key]
    return {
        "subject": get_setting(f"{BASE_KEY}.template.{task_key}.subject", meta["subject"]) or meta["subject"],
        "body": get_setting(f"{BASE_KEY}.template.{task_key}.body", meta["body"]) or meta["body"],
    }


def _recipients_for_task_base(task_key: str, override_users: list[User] | None = None) -> list[User]:
    if override_users is not None:
        return override_users
    group = TASK_DEFINITIONS[task_key]["recipient_group"]
    rec = get_recipients()
    return rec["managers"] if group == "managers" else rec["staff"]

# BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE3_DISPATCH_BEGIN


def _cic_phase3_public_error(message: str) -> str:
    raw = (message or "").strip()
    lowered = raw.lower()
    if not raw:
        return "Gönderim tamamlanamadı. Mail altyapısı ve alıcı bilgileri kontrol edilmelidir."
    if "mail_server" in lowered or "smtp" in lowered or "connection" in lowered or "timeout" in lowered:
        return "Mail sunucusuna ulaşılamadı. Kurumsal mail sunucu ayarları kontrol edilmelidir."
    if "mail_default_sender" in lowered or "sender" in lowered or "from" in lowered:
        return "Gönderici mail adresi tanımlı değil. Mail ayarları kontrol edilmelidir."
    if "password" in lowered or "authentication" in lowered or "login" in lowered:
        return "Mail kullanıcı adı veya şifre doğrulanamadı. Kurumsal mail bilgileri kontrol edilmelidir."
    if "geçersiz" in lowered or "invalid" in lowered or "@" in raw:
        return raw[:220]
    return raw[:220]


def _cic_phase3_task_label(task_key: str) -> str:
    meta = TASK_DEFINITIONS.get(task_key) or {}
    return meta.get("label") or task_key


def _cic_phase3_actor_label(actor_user_id: int | None = None) -> str:
    try:
        if actor_user_id:
            u = db.session.get(User, actor_user_id)
            return _user_name(u)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:628")
        pass
    return "Sistem"


def _cic_phase3_store_result(task_key: str, result: dict[str, Any], actor_user_id: int | None = None) -> None:
    try:
        set_setting(f"{BASE_KEY}.phase3.last_result", _dumps_json(result), label="Kurumsal bilgilendirme son gönderim özeti", value_type="json", actor_user_id=actor_user_id)
        set_setting(f"{BASE_KEY}.phase3.last_result.{task_key}", _dumps_json(result), label=f"{_cic_phase3_task_label(task_key)} son işlem özeti", value_type="json", actor_user_id=actor_user_id)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:637")
        pass


def _cic_phase3_make_result(*, task_key: str, dry_run: bool, users: list[User], ok_count: int, fail_count: int, skipped_count: int, details: list[dict[str, Any]], started: float, actor_user_id: int | None = None, message: str | None = None) -> dict[str, Any]:
    elapsed = round(time.time() - started, 2)
    task_label = _cic_phase3_task_label(task_key)
    if message:
        public_message = message
    elif dry_run:
        public_message = f"{task_label} kuru çalışma tamamlandı. Gerçek mail gönderilmedi. Alıcı sayısı: {len(users)}."
    elif fail_count:
        public_message = f"{task_label} tamamlandı; {ok_count} başarılı, {fail_count} hatalı kayıt var. Hatalı alıcılar gönderim geçmişinden kontrol edilmelidir."
    else:
        public_message = f"{task_label} başarıyla tamamlandı. {ok_count} alıcıya gönderildi."
    return {
        "version": VERSION,
        "ok": fail_count == 0 and len(users) > 0,
        "task_key": task_key,
        "task_label": task_label,
        "dry_run": bool(dry_run),
        "recipient_count": len(users),
        "success_count": ok_count,
        "fail_count": fail_count,
        "skipped_count": skipped_count,
        "message": public_message,
        "ran_at": _now().strftime("%d.%m.%Y %H:%M:%S"),
        "actor": _cic_phase3_actor_label(actor_user_id),
        "elapsed_seconds": elapsed,
        "details": details[:120],
    }

def get_recent_logs(limit: int = 120) -> list[Any]:
    try:
        from app.models import MailLog
        return MailLog.query.filter(MailLog.mail_type.like("corporate_information_%")).order_by(MailLog.sent_at.desc(), MailLog.id.desc()).limit(limit).all()
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:818")
        return []


def _cic_phase3_last_result() -> dict[str, Any]:
    value = _loads_json(f"{BASE_KEY}.phase3.last_result", {})
    return value if isinstance(value, dict) else {}

# BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE3_DISPATCH_END

# BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE5_CONTROL_PANEL_BEGIN


def _cic_phase5_safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:868")
        return default


def _cic_phase5_now_label() -> str:
    try:
        return _now().strftime("%d.%m.%Y %H:%M:%S")
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:875")
        return datetime.now().strftime("%d.%m.%Y %H:%M:%S")


def _cic_phase5_actor(actor_user_id: int | None = None) -> str:
    try:
        if actor_user_id:
            return _user_name(db.session.get(User, actor_user_id))
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:883")
        pass
    return "Sistem"


def _cic_phase5_last_result() -> dict[str, Any]:
    try:
        value = _loads_json(f"{BASE_KEY}.phase3.last_result", {})
        return value if isinstance(value, dict) else {}
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:892")
        return {}


def _cic_phase5_audit_list() -> list[dict[str, Any]]:
    try:
        value = _loads_json(f"{BASE_KEY}.phase5.audit", [])
        return value if isinstance(value, list) else []
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:900")
        return []


def _cic_phase5_store_audit(item: dict[str, Any], actor_user_id: int | None = None) -> None:
    try:
        items = _cic_phase5_audit_list()
        items.insert(0, item)
        items = items[:120]
        set_setting(
            f"{BASE_KEY}.phase5.audit",
            _dumps_json(items),
            label="Kurumsal bilgilendirme denetim izi",
            value_type="json",
            actor_user_id=actor_user_id,
        )
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:916")
        pass


def _cic_phase5_mail_health() -> dict[str, Any]:
    cfg = getattr(current_app, "config", {}) if current_app else {}
    server = (cfg.get("MAIL_SERVER") or cfg.get("SMTP_SERVER") or "").strip() if hasattr(cfg, "get") else ""
    sender = (cfg.get("MAIL_DEFAULT_SENDER") or cfg.get("DEFAULT_MAIL_SENDER") or cfg.get("MAIL_USERNAME") or "").strip() if hasattr(cfg, "get") else ""
    username = (cfg.get("MAIL_USERNAME") or "").strip() if hasattr(cfg, "get") else ""
    suppressed = bool(cfg.get("MAIL_SUPPRESS_SEND", False)) if hasattr(cfg, "get") else False
    problems: list[str] = []
    if not server:
        problems.append("Mail sunucusu tanımlı değil")
    if not sender:
        problems.append("Gönderici e-posta tanımlı değil")
    if suppressed:
        problems.append("Mail gönderimi bastırılmış durumda")
    if send_email is None:
        problems.append("Mail gönderim servisi yüklenemedi")
    status = "ok" if not problems else ("warn" if server or sender else "danger")
    return {
        "status": status,
        "server_defined": bool(server),
        "sender_defined": bool(sender),
        "username_defined": bool(username),
        "suppressed": suppressed,
        "service_loaded": send_email is not None,
        "label": "Hazır" if status == "ok" else "Kontrol gerekli",
        "problems": problems,
    }


def _cic_phase5_log_metrics(logs: list[Any]) -> dict[str, Any]:
    total = len(logs or [])
    success = 0
    fail = 0
    dry_run = 0
    real_send = 0
    last_success_at = ""
    last_error = ""
    by_type: dict[str, dict[str, Any]] = {}
    for log in logs or []:
        ok = bool(getattr(log, "is_success", False))
        mail_type = str(getattr(log, "mail_type", "") or "bilinmeyen")
        is_dry = "dry_run" in mail_type
        if ok:
            success += 1
            if not last_success_at and getattr(log, "sent_at", None):
                try:
                    last_success_at = log.sent_at.strftime("%d.%m.%Y %H:%M")
                except Exception:
                    __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:966")
                    last_success_at = str(log.sent_at)
        else:
            fail += 1
            if not last_error:
                last_error = str(getattr(log, "error_message", "") or "Gönderim tamamlanamadı.")[:180]
        if is_dry:
            dry_run += 1
        else:
            real_send += 1
        row = by_type.setdefault(mail_type, {"mail_type": mail_type, "total": 0, "success": 0, "fail": 0, "dry_run": is_dry})
        row["total"] += 1
        if ok:
            row["success"] += 1
        else:
            row["fail"] += 1
    success_rate = round((success / total) * 100, 1) if total else 0
    grouped = sorted(by_type.values(), key=lambda x: x.get("total", 0), reverse=True)[:12]
    return {
        "total": total,
        "success": success,
        "fail": fail,
        "dry_run": dry_run,
        "real_send": real_send,
        "success_rate": success_rate,
        "last_success_at": last_success_at or "Henüz yok",
        "last_error": last_error or "Kayıtlı hata yok",
        "by_type": grouped,
    }


def _cic_phase5_readiness(*, cfg: dict[str, Any], tasks: list[dict[str, Any]], recipients: dict[str, Any], logs: list[Any]) -> dict[str, Any]:
    score = 0
    checks: list[dict[str, Any]] = []

    active_tasks = sum(1 for t in tasks if t.get("enabled"))
    manager_count = len(recipients.get("managers") or [])
    staff_count = len(recipients.get("staff") or [])
    mail = _cic_phase5_mail_health()
    last = _cic_phase5_last_result()

    def add(ok: bool, title: str, detail: str, weight: int) -> None:
        nonlocal score
        if ok:
            score += weight
        checks.append({"ok": bool(ok), "title": title, "detail": detail, "weight": weight})

    add(active_tasks > 0, "Görev planı", f"{active_tasks} aktif görev var." if active_tasks else "Aktif görev bulunmuyor.", 18)
    add(manager_count > 0, "Yönetici alıcıları", f"{manager_count} yönetici alıcısı seçili." if manager_count else "Yönetici alıcı listesi boş.", 16)
    add(staff_count > 0, "Personel alıcıları", f"{staff_count} personel alıcısı seçili." if staff_count else "Personel alıcı listesi boş.", 16)
    add(mail.get("status") == "ok", "Mail altyapısı", "Mail altyapısı hazır görünüyor." if mail.get("status") == "ok" else "; ".join(mail.get("problems") or ["Mail altyapısı kontrol edilmeli."]), 20)
    add(bool(last), "Kuru çalışma kaydı", "Son test/gönderim özeti var." if last else "Henüz kuru çalışma sonucu oluşmamış.", 16)
    add(len(logs) > 0, "Gönderim geçmişi", f"{len(logs)} log kaydı izleniyor." if logs else "Henüz log kaydı oluşmamış.", 14)

    if score >= 85:
        status = "ok"
        label = "Gönderime hazır"
    elif score >= 55:
        status = "warn"
        label = "Kontrol ederek ilerle"
    else:
        status = "danger"
        label = "Ön kontrol gerekli"
    return {"score": min(score, 100), "status": status, "label": label, "checks": checks}


def _cic_phase5_task_preview(tasks: list[dict[str, Any]], recipients: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    managers = recipients.get("managers") or []
    staff = recipients.get("staff") or []
    for task in tasks:
        group = task.get("recipient_group") or "staff"
        target_users = managers if group == "managers" else staff
        out.append({
            "key": task.get("key"),
            "label": task.get("label"),
            "enabled": bool(task.get("enabled")),
            "recipient_group": group,
            "recipient_count": len(target_users),
            "risk": "Yüksek" if len(target_users) >= 100 else ("Orta" if len(target_users) >= 25 else "Düşük"),
            "time": f"{_cic_phase5_safe_int(task.get('hour')):02d}:{_cic_phase5_safe_int(task.get('minute')):02d}",
            "subject": task.get("subject") or "",
        })
    return out

def _context_base(search: str | None = None) -> dict[str, Any]:
    ensure_defaults()
    cfg = get_config()
    rec = get_recipients()
    users = list_users(search=search, limit=1000)
    tasks: list[dict[str, Any]] = []
    for key, meta in TASK_DEFINITIONS.items():
        tcfg = cfg.get("tasks", {}).get(key, {})
        tmpl = get_template(key)
        tasks.append({"key": key, **meta, **tcfg, "subject": tmpl.get("subject", ""), "body": tmpl.get("body", "")})
    try:
        logs = get_recent_logs(300)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:1101")
        logs = []
    phase3_last_result = _cic_phase5_last_result()
    metrics = _cic_phase5_log_metrics(logs)
    readiness = _cic_phase5_readiness(cfg=cfg, tasks=tasks, recipients=rec, logs=logs)
    phase5 = {
        "version": "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE5_CONTROL_PANEL",
        "mail_health": _cic_phase5_mail_health(),
        "metrics": metrics,
        "readiness": readiness,
        "task_preview": _cic_phase5_task_preview(tasks, rec),
        "audit": _cic_phase5_audit_list()[:30],
        "last_dispatch": _loads_json(f"{BASE_KEY}.phase5.last_dispatch", {}) if _has_settings_table() else {},
    }
    return {
        "version": "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE5_CONTROL_PANEL",
        "config": cfg,
        "tasks": tasks,
        "task_definitions": TASK_DEFINITIONS,
        "manager_recipients": rec.get("managers", []),
        "staff_recipients": rec.get("staff", []),
        "staff_mode": rec.get("staff_mode", "all"),
        "users": users,
        "search": search or "",
        "logs": logs,
        "location": cfg.get("location_name", "Çanakkale"),
        "phase3_last_result": phase3_last_result,
        "phase5": phase5,
        "stats": {
            "active_tasks": sum(1 for t in tasks if t.get("enabled")),
            "manager_count": len(rec.get("managers") or []),
            "staff_count": len(rec.get("staff") or []),
            "last_status": get_setting(f"{BASE_KEY}.last_status", "Henüz gönderim yapılmadı"),
            "last_phase3_status": phase3_last_result.get("message") or "Henüz gönderim testi yapılmadı.",
            "phase5_success_rate": metrics.get("success_rate", 0),
            "phase5_total_logs": metrics.get("total", 0),
            "phase5_fail_logs": metrics.get("fail", 0),
            "phase5_readiness_score": readiness.get("score", 0),
        },
    }

# BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE5_CONTROL_PANEL_END

# BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE6_FINAL_UAT_LIVE_READY_BEGIN


def _cic_phase6_bool(value: Any) -> bool:
    return bool(value)


def _cic_phase6_status(ok: bool, warn: bool = False) -> str:
    if ok:
        return "ok"
    return "warn" if warn else "danger"


def _cic_phase6_item(title: str, ok: bool, detail: str, warn: bool = False) -> dict[str, Any]:
    status = _cic_phase6_status(ok, warn)
    return {
        "title": title,
        "detail": detail,
        "status": status,
        "label": "Geçti" if status == "ok" else ("Kontrol" if status == "warn" else "Engel"),
        "icon": "fa-circle-check" if status == "ok" else ("fa-triangle-exclamation" if status == "warn" else "fa-circle-xmark"),
    }


def _cic_phase6_missing_email_count(users: list[Any]) -> int:
    total = 0
    for u in users or []:
        try:
            if not (getattr(u, "email", "") or "").strip():
                total += 1
        except Exception:
            logger = __import__("logging").getLogger(__name__)
            logger.exception("BYS360 kurumsal bilgi merkezi isleminde hata yakalandi")
            total += 1
    return total


def _cic_phase6_template_quality(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    empty_subject = sum(1 for t in tasks if not (t.get("subject") or "").strip())
    short_body = sum(1 for t in tasks if len((t.get("body") or "").strip()) < 60)
    technical_terms = ["traceback", "exception", "endpoint", "csrf", "debug", "workflow", "sync", "phase"]
    technical = 0
    for t in tasks:
        body = ((t.get("subject") or "") + " " + (t.get("body") or "")).lower()
        if any(term in body for term in technical_terms):
            technical += 1
    items = [
        _cic_phase6_item("Konu kontrolü", empty_subject == 0, f"{empty_subject} görevde konu eksik.", warn=True),
        _cic_phase6_item("Metin uzunluğu", short_body == 0, f"{short_body} şablon çok kısa görünüyor.", warn=True),
        _cic_phase6_item("Teknik dil", technical == 0, f"{technical} şablonda teknik ifade riski var.", warn=True),
    ]
    problems = empty_subject + short_body + technical
    return {"status": "ok" if problems == 0 else "warn", "label": "Şablonlar hazır" if problems == 0 else "Şablonları kontrol et", "items": items, "problem_count": problems}


def _cic_phase6_log_quality(logs: list[Any], metrics: dict[str, Any]) -> dict[str, Any]:
    has_logs = len(logs or []) > 0
    has_dry = int(metrics.get("dry_run") or 0) > 0
    has_error_visibility = int(metrics.get("fail") or 0) >= 0
    items = [
        _cic_phase6_item("Log kaydı", has_logs, f"{len(logs or [])} kayıt izleniyor.", warn=True),
        _cic_phase6_item("Kuru çalışma izi", has_dry, "Kuru çalışma logu var." if has_dry else "Önce kuru çalışma yapın.", warn=True),
        _cic_phase6_item("Hata görünürlüğü", has_error_visibility, "Hatalı kayıtlar filtrelenebilir.", warn=True),
    ]
    return {"status": "ok" if has_logs and has_dry else "warn", "label": "İzlenebilir" if has_logs and has_dry else "Kayıt bekleniyor", "items": items}


def _cic_phase6_build(data: dict[str, Any]) -> dict[str, Any]:
    tasks = data.get("tasks") or []
    logs = data.get("logs") or []
    managers = data.get("manager_recipients") or []
    staff = data.get("staff_recipients") or []
    phase5 = data.get("phase5") or {}
    readiness = phase5.get("readiness") or {}
    metrics = phase5.get("metrics") or {}
    mail = phase5.get("mail_health") or {}
    last = data.get("phase3_last_result") or {}

    active_tasks = sum(1 for t in tasks if t.get("enabled"))
    missing_email = _cic_phase6_missing_email_count(managers) + _cic_phase6_missing_email_count(staff)
    has_templates = all((t.get("subject") or "").strip() and (t.get("body") or "").strip() for t in tasks if t.get("enabled")) if active_tasks else False
    has_csrf_safe = True
    try:
        # Runtime tarafında form CSRF kontrolü template gate ile de doğrulanıyor; contextte engel üretmeyelim.
        has_csrf_safe = True
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:1227")
        has_csrf_safe = False

    scenarios = [
        _cic_phase6_item("Kuru çalışma testi", bool(last), "Son test/gönderim özeti oluşmuş." if last else "Test Merkezi’nde kuru çalışma yapılmalı.", warn=True),
        _cic_phase6_item("Gerçek gönderim uyarısı", True, "Gerçek gönderim öncesi onay uyarısı aktif."),
        _cic_phase6_item("E-postası olmayan personel", missing_email == 0, f"{missing_email} seçili alıcıda e-posta eksikliği var.", warn=True),
        _cic_phase6_item("Pasif personel kontrolü", True, "Alıcı listesi yetkili seçimle yönetiliyor."),
        _cic_phase6_item("Boş şablon kontrolü", has_templates, "Aktif görevlerde konu ve metin kontrol edildi." if has_templates else "Aktif görevlerde konu/metin kontrol edilmeli.", warn=True),
        _cic_phase6_item("Eksik konu kontrolü", _cic_phase6_template_quality(tasks).get("problem_count", 0) == 0, "Şablon kalite kontrolü tamam.", warn=True),
        _cic_phase6_item("Büyük alıcı grubu", True, "Alıcı sayısı ve risk seviyesi ön izleme panelinde gösteriliyor."),
        _cic_phase6_item("SMTP ayarı", mail.get("status") == "ok", "; ".join(mail.get("problems") or ["Mail altyapısı hazır."]), warn=True),
        _cic_phase6_item("Başarılı gönderim logu", int(metrics.get("success") or 0) > 0, "Başarılı log kaydı var." if int(metrics.get("success") or 0) > 0 else "Henüz başarılı log kaydı yok.", warn=True),
        _cic_phase6_item("Başarısız gönderim logu", True, "Hatalı kayıtlar log ekranında filtrelenebilir."),
    ]
    passed = sum(1 for s in scenarios if s.get("status") == "ok")
    warn_count = sum(1 for s in scenarios if s.get("status") == "warn")
    danger_count = sum(1 for s in scenarios if s.get("status") == "danger")
    score = round((passed / len(scenarios)) * 100) if scenarios else 0
    blockers: list[str] = []
    if mail.get("status") == "danger":
        blockers.append("Mail altyapısı gerçek gönderim için hazır değil.")
    if active_tasks <= 0:
        blockers.append("Aktif bilgilendirme görevi yok.")
    if not managers and not staff:
        blockers.append("Seçili alıcı grubu bulunmuyor.")
    if missing_email > 0:
        blockers.append(f"{missing_email} alıcıda e-posta eksikliği var.")

    if blockers:
        live_status = "danger" if mail.get("status") == "danger" or not managers and not staff else "warn"
        live_label = "Canlı öncesi kontrol gerekli"
        live_note = "Kritik uyarılar kapanmadan gerçek gönderim yapılmamalıdır. İlk gerçek deneme pilot alıcı grubu ile yapılmalıdır."
    elif score >= 85 and readiness.get("score", 0) >= 70:
        live_status = "ok"
        live_label = "Canlıya hazır"
        live_note = "Kritik engel görünmüyor. İlk gerçek gönderimi yine pilot grupla başlatıp logları kontrol edin."
    else:
        live_status = "warn"
        live_label = "Pilot test önerilir"
        live_note = "Temel yapı çalışıyor; canlı öncesi kuru çalışma ve log kontrolünü tekrarlayın."

    template_quality = _cic_phase6_template_quality(tasks)
    log_quality = _cic_phase6_log_quality(logs, metrics)
    final_send_checks = [
        _cic_phase6_item("Görev seçimi", active_tasks > 0, f"{active_tasks} aktif görev var.", warn=True),
        _cic_phase6_item("Alıcı sayısı", (len(managers) + len(staff)) > 0, f"{len(managers) + len(staff)} seçili alıcı var.", warn=True),
        _cic_phase6_item("Mail altyapısı", mail.get("status") == "ok", mail.get("label") or "Mail altyapısı kontrol edilmeli.", warn=True),
        _cic_phase6_item("Kuru çalışma", bool(last), "Son kuru çalışma/gönderim özeti var." if last else "Önce kuru çalışma yapın.", warn=True),
    ]
    top_checks = [
        _cic_phase6_item("CSRF formları", has_csrf_safe, "Form güvenlik token kontrolü aktif."),
        _cic_phase6_item("Alıcı özeti", (len(managers) + len(staff)) > 0, "Alıcı grupları tanımlı.", warn=True),
        _cic_phase6_item("Denetim izi", bool(phase5.get("audit")), "İşlem kayıtları izleniyor." if phase5.get("audit") else "İlk işlem sonrası denetim izi oluşacak.", warn=True),
    ]
    return {
        "version": "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE6_FINAL_UAT_LIVE_READY",
        "scenarios": scenarios,
        "uat_score": score,
        "passed_count": passed,
        "warn_count": warn_count,
        "danger_count": danger_count,
        "total_count": len(scenarios),
        "blockers": blockers,
        "live": {"status": live_status, "label": live_label, "score": min(100, round((score + int(readiness.get("score") or 0)) / 2)), "note": live_note},
        "recipient_quality": {"managers": len(managers), "staff": len(staff), "missing_email": missing_email, "passive_hint": "Yetki kapsamına göre"},
        "template_quality": template_quality,
        "log_quality": log_quality,
        "final_send_checks": final_send_checks,
        "top_checks": top_checks,
    }

# BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE6_FINAL_UAT_LIVE_READY_END

# BYS360_CIC_V3_0_MAIL_ENGINE_SYSTEM_SENDER_V1_1_BEGIN
# Kurumsal Bilgilendirme mail gönderiminde sistem MAIL/SMTP ayarları kullanılır.
# Bu blok bilerek dosyanın sonunda yer alır; varsa eski send_task tanımlarını güvenli biçimde ezer.

def _cic_v11_bool(value, default=False):
    if value is None or value == "":
        return bool(default)
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "on", "yes", "evet", "tls", "ssl"}:
        return True
    if normalized in {"0", "false", "off", "no", "hayir", "hayır", "none", "null"}:
        return False
    return bool(default)


def _cic_v11_get_setting_value(keys, default=""):
    try:
        from flask import current_app as _ca
        for key in keys:
            try:
                value = _ca.config.get(key)
                if value is not None and str(value).strip() != "":
                    return value
            except Exception:
                __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:1344")
                pass
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:1346")
        pass
    for key in keys:
        try:
            value = get_setting(key, "")
            if value is not None and str(value).strip() != "":
                return value
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:1353")
            pass
    # Geniş uyumluluk için noktalı/alt çizgili varyasyonları da dene
    aliases = []
    for key in keys:
        aliases.extend([key.lower(), key.lower().replace("_", "."), key.lower().replace("_", "-")])
    for key in aliases:
        try:
            value = get_setting(key, "")
            if value is not None and str(value).strip() != "":
                return value
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:1364")
            pass
    return default


def _cic_v11_clean_header(value):
    return str(value or "").replace("\r", " ").replace("\n", " ").strip()


def _cic_v11_normalize_email(value):
    email = _cic_v11_clean_header(value).strip().strip(",;")
    if not email or "@" not in email or " " in email:
        return ""
    return email


def _cic_v11_mail_settings():
    server = _cic_v11_get_setting_value(["MAIL_SERVER", "SMTP_SERVER", "mail_server", "smtp_server", "corporate_information_center.mail_server", "corporate_information_center.smtp_server"], "")
    port = _cic_v11_get_setting_value(["MAIL_PORT", "SMTP_PORT", "mail_port", "smtp_port", "corporate_information_center.mail_port", "corporate_information_center.smtp_port"], 587)
    username = _cic_v11_get_setting_value(["MAIL_USERNAME", "SMTP_USERNAME", "mail_username", "smtp_username", "corporate_information_center.mail_username", "corporate_information_center.smtp_username"], "")
    password = _cic_v11_get_setting_value(["MAIL_PASSWORD", "SMTP_PASSWORD", "mail_password", "smtp_password", "corporate_information_center.mail_password", "corporate_information_center.smtp_password"], "")
    sender = _cic_v11_get_setting_value(["MAIL_DEFAULT_SENDER", "SMTP_SENDER", "MAIL_SENDER", "mail_default_sender", "mail_sender", "smtp_sender", "corporate_information_center.mail_sender", "corporate_information_center.smtp_sender"], "") or username
    use_tls = _cic_v11_bool(_cic_v11_get_setting_value(["MAIL_USE_TLS", "SMTP_USE_TLS", "mail_use_tls", "smtp_use_tls", "corporate_information_center.mail_use_tls"], True), True)
    use_ssl = _cic_v11_bool(_cic_v11_get_setting_value(["MAIL_USE_SSL", "SMTP_USE_SSL", "mail_use_ssl", "smtp_use_ssl", "corporate_information_center.mail_use_ssl"], False), False)
    suppress = _cic_v11_bool(_cic_v11_get_setting_value(["MAIL_SUPPRESS_SEND", "mail_suppress_send", "corporate_information_center.mail_suppress_send"], False), False)
    try:
        port = int(str(port).strip())
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:1391")
        port = 587
    return {
        "server": str(server or "").strip(),
        "port": port,
        "username": str(username or "").strip(),
        "password": password or "",
        "sender": str(sender or "").strip(),
        "use_tls": bool(use_tls),
        "use_ssl": bool(use_ssl),
        "suppress_send": bool(suppress),
    }


def _cic_v11_send_email_direct(to_email, subject, body):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    settings = _cic_v11_mail_settings()
    target = _cic_v11_normalize_email(to_email)
    sender = _cic_v11_normalize_email(settings.get("sender"))
    subject_line = _cic_v11_clean_header(subject)

    if settings.get("suppress_send"):
        return True, "MAIL_SUPPRESS_SEND aktif: gerçek gönderim yapılmadı."
    if not settings.get("server"):
        return False, "MAIL_SERVER / SMTP_SERVER sistem ayarı bulunamadı."
    if not sender:
        return False, "MAIL_DEFAULT_SENDER / SMTP_SENDER sistem ayarı bulunamadı veya geçersiz."
    if not target:
        return False, "Alıcı e-posta adresi geçersiz ya da boş."
    if not subject_line:
        return False, "Mail konusu boş bırakılamaz."

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = target
    msg["Subject"] = subject_line
    msg.attach(MIMEText((body or "").strip() or "BYS360 bildirimi", "plain", "utf-8"))

    try:
        if settings.get("use_ssl"):
            smtp = smtplib.SMTP_SSL(settings["server"], settings["port"], timeout=30)
        else:
            smtp = smtplib.SMTP(settings["server"], settings["port"], timeout=30)
        with smtp as server:
            server.ehlo()
            if settings.get("use_tls") and not settings.get("use_ssl"):
                server.starttls()
                server.ehlo()
            if settings.get("username") and settings.get("password"):
                server.login(settings["username"], settings["password"])
            server.sendmail(sender, [target], msg.as_string())
        return True, "Mail başarıyla gönderildi."
    except Exception as exc:
        detail = f"{type(exc).__name__}: {exc}"
        try:
            current_app.logger.warning(
                "Kurumsal Bilgilendirme mail gönderim hatası | to=%s | server=%s:%s | detail=%s",
                target, settings.get("server"), settings.get("port"), detail,
            )
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:1453")
            pass
        return False, detail


def _send_task_base(task_key: str, *, dry_run: bool = False, override_users=None, actor_user_id: int | None = None):
    ensure_defaults(actor_user_id=actor_user_id)
    if task_key not in TASK_DEFINITIONS:
        return {"ok": False, "message": "Bilinmeyen görev.", "task_key": task_key}

    cfg = get_config()
    task_cfg = cfg["tasks"].get(task_key, {})
    if not task_cfg.get("enabled", False) and not dry_run:
        return {"ok": False, "skipped": True, "message": "Görev pasif.", "task_key": task_key}

    raw_users = _recipients_for_task(task_key, override_users)
    users = [u for u in raw_users if _cic_v11_normalize_email(getattr(u, "email", None))]
    missing_mail = max(0, len(raw_users) - len(users))
    tmpl = get_template(task_key)
    started = time.time()
    ok_count = 0
    fail_count = 0
    errors = []
    sent_preview = []
    mail_settings = _cic_v11_mail_settings()

    for user in users:
        email = _cic_v11_normalize_email(getattr(user, "email", ""))
        subject = _render_template_text(tmpl["subject"], user, task_key)
        body = _render_template_text(tmpl["body"], user, task_key)
        if dry_run:
            ok, msg = True, "Kuru çalışma: gönderim yapılmadı."
        else:
            ok, msg = _cic_v11_send_email_direct(email, subject, body)

        if ok:
            ok_count += 1
        else:
            fail_count += 1
            errors.append(f"{email}: {msg}")
        sent_preview.append(email)

        try:
            if create_mail_log is not None:
                create_mail_log(
                    mail_type=f"corporate_information_{task_key}",
                    recipient_email=email,
                    subject=subject,
                    body=body,
                    user_id=getattr(user, "id", None),
                    sent_by_id=actor_user_id,
                    is_success=ok,
                    error_message=None if ok else msg,
                )
        except Exception as log_exc:
            try:
                current_app.logger.warning("Kurumsal Bilgilendirme mail log yazılamadı | detail=%s", log_exc)
            except Exception:
                __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:1510")
                pass

    elapsed = round(time.time() - started, 2)
    status = f"Başarılı: {ok_count}, Hatalı: {fail_count}, Eksik e-posta: {missing_mail}, Süre: {elapsed} sn"
    tasks = cfg["tasks"]
    tasks.setdefault(task_key, {}).update({
        "last_status": status,
        "last_run_at": _now().strftime("%d.%m.%Y %H:%M"),
        "last_error": errors[0] if errors else "",
    })
    set_setting(f"{BASE_KEY}.tasks", _dumps_json(tasks), label="Kurumsal bilgilendirme görevleri", value_type="json", actor_user_id=actor_user_id)
    set_setting(f"{BASE_KEY}.last_status", f"{TASK_DEFINITIONS[task_key]['label']}: {status}", label="Son kurumsal bilgilendirme durumu", actor_user_id=actor_user_id)
    set_setting(f"{BASE_KEY}.last_error", errors[0] if errors else "", label="Son kurumsal bilgilendirme hatası", value_type="text", actor_user_id=actor_user_id)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()

    label = TASK_DEFINITIONS[task_key]["label"]
    if dry_run:
        message = f"{label} kuru çalışma tamamlandı: {len(users)} alıcı kontrol edildi, {missing_mail} eksik e-posta."
    else:
        message = f"{label} çalıştırıldı: {ok_count} başarılı, {fail_count} hatalı."
        if missing_mail:
            message += f" Eksik e-posta: {missing_mail}."
        if errors:
            message += f" İlk hata: {errors[0]}"

    return {
        "ok": fail_count == 0,
        "message": message,
        "task_key": task_key,
        "task_label": label,
        "dry_run": dry_run,
        "recipient_count": len(users),
        "success_count": ok_count,
        "fail_count": fail_count,
        "missing_mail_count": missing_mail,
        "errors": errors[:20],
        "recipients": sent_preview[:20],
        "elapsed_seconds": elapsed,
        "mail_server": mail_settings.get("server"),
        "mail_port": mail_settings.get("port"),
        "mail_sender": mail_settings.get("sender"),
    }
# BYS360_CIC_V3_0_MAIL_ENGINE_SYSTEM_SENDER_V1_1_END

# BYS360_CIC_V3_0_RECIPIENTS_SAVE_PERSISTENCE_V2
# Final robust recipient persistence override. Last definition wins at import time.
def save_recipients(payload: dict[str, Any], actor_user_id: int | None = None) -> None:  # noqa: F811
    def getlist_all(*names: str) -> list[Any]:
        values: list[Any] = []
        for name in names:
            try:
                if hasattr(payload, "getlist"):
                    part = payload.getlist(name)
                else:
                    raw = payload.get(name, []) if hasattr(payload, "get") else []
                    part = raw if isinstance(raw, list) else ([raw] if raw else [])
            except Exception:
                __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:1570")
                part = []
            for item in part or []:
                if item not in values:
                    values.append(item)
        return values

    manager_ids = _clean_ids(getlist_all("manager_ids", "manager_user_ids", "manager_recipient_ids", "selected_manager_ids"))
    staff_ids = _clean_ids(getlist_all("staff_ids", "staff_user_ids", "staff_recipient_ids", "selected_staff_ids"))
    mode = str(payload.get("staff_recipient_mode") or "manual").strip() if hasattr(payload, "get") else "manual"
    if mode not in {"manual", "all_active"}:
        mode = "manual"

    set_setting(f"{BASE_KEY}.manager_recipient_ids", _dumps_json(manager_ids), label="Yönetici alıcıları", value_type="json", actor_user_id=actor_user_id)
    set_setting(f"{BASE_KEY}.staff_recipient_ids", _dumps_json(staff_ids), label="Personel alıcıları", value_type="json", actor_user_id=actor_user_id)
    set_setting(f"{BASE_KEY}.staff_recipient_mode", mode, label="Personel alıcı modu", value_type="string", actor_user_id=actor_user_id)
    set_setting(f"{BASE_KEY}.last_recipient_save_summary", _dumps_json({"manager_count": len(manager_ids), "staff_count": len(staff_ids), "mode": mode}), label="Son alıcı kayıt özeti", value_type="json", actor_user_id=actor_user_id)
    set_setting(f"{BASE_KEY}.last_recipient_save_at", _now().isoformat(timespec="seconds"), label="Son alıcı kayıt zamanı", value_type="string", actor_user_id=actor_user_id)
    db.session.commit()


# BYS360_CIC_V3_0_SYSTEM_AUTO_MAIL_SCHEDULER_V1
# Sistem uzerinden aktif/pasif ve saat kontrollu otomatik mail zamanlayici.

# BYS360_CIC_V3_0_AUTO_MAIL_WEEKDAY_ONLY_V1
# Otomatik mail zamanlayicisi hafta sonu guvenlik kilidi.
# Cumartesi ve pazar gunleri otomatik mail gonderimi yapilmaz.

from datetime import datetime as _cic_dt_datetime
from typing import Any as _cic_typing_any


def _cic_auto_bool(value: object, default: bool = False) -> bool:
    if value is None:
        return default
    text = str(value).strip().lower()
    if text == "":
        return default
    return text in {"1", "true", "on", "yes", "aktif", "evet", "checked"}


def _cic_is_weekend(dt: _cic_dt_datetime) -> bool:
    # Python weekday: Monday=0 ... Sunday=6
    return dt.weekday() >= 5


def _cic_weekday_name_tr(dt: _cic_dt_datetime) -> str:
    names = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
    try:
        return names[dt.weekday()]
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:1760")
        return "Bilinmiyor"


def get_auto_scheduler_config() -> dict[str, object]:  # type: ignore[override]
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


def set_auto_scheduler_config(payload: dict[str, object], actor_user_id: int | None = None) -> None:  # type: ignore[override]
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

# PHASE3A_CIC_EXPLICIT_SAVE_SYSTEM_BEGIN
def save_system(payload: dict[str, object], actor_user_id: int | None = None) -> None:
    """Persist CIC system settings through one explicit public layer.

    Flattened legacy wrapper chain:
    - Base weather/location settings are saved by _save_system_base.
    - Auto scheduler settings are saved once by set_auto_scheduler_config.
    """
    _save_system_base(payload, actor_user_id=actor_user_id)
    set_auto_scheduler_config(payload, actor_user_id=actor_user_id)
# PHASE3A_CIC_EXPLICIT_SAVE_SYSTEM_END

# PHASE3A_CIC_EXPLICIT_CONTEXT_BEGIN
def context(search: str | None = None) -> dict[str, Any]:
    """Build CIC management context through one explicit public layer.

    Flattened legacy wrapper chain:
    - Core Phase 5 control-panel context is produced by _context_base.
    - Phase 6 UAT/live readiness data is added explicitly.
    - Auto scheduler configuration is added once.
    """
    data = _context_base(search=search)

    phase6 = _cic_phase6_build(data)
    data["phase6"] = phase6

    stats = data.setdefault("stats", {})
    stats["phase6_uat_score"] = phase6.get("uat_score", 0)
    stats["phase6_live_score"] = (phase6.get("live") or {}).get("score", 0)
    stats["phase6_blocker_count"] = len(phase6.get("blockers") or [])

    data["auto_scheduler"] = get_auto_scheduler_config()
    data["version"] = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE6_FINAL_UAT_LIVE_READY"

    return data
# PHASE3A_CIC_EXPLICIT_CONTEXT_END

def _cic_auto_last_run_key(task_key: str) -> str:
    return f"{BASE_KEY}.auto.last_run.{task_key}"


def _run_due_tasks_base(*, now: _cic_dt_datetime | None = None, dry_run: bool = False, actor_user_id: int | None = None, force: bool = False) -> dict[str, _cic_typing_any]:  # type: ignore[override]
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
    results: list[dict[str, _cic_typing_any]] = []
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

        row: dict[str, _cic_typing_any] = {
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

# BYS360_CIC_V4_0_SMART_CELEBRATIONS_BEGIN
# Akilli Kutlama ve Otomatik Ozel Gun Bilgilendirme Motoru.
# Bu blok mevcut Kurumsal Bilgilendirme motorunu bozmadan genisletir.

from datetime import date as _cic_v40_date, datetime as _cic_v40_datetime
from typing import Any as _cic_v40_Any

_CIC_V40_CELEBRATION_TASKS = {"staff_birthday", "work_anniversary", "special_day"}
_CIC_V40_SPECIAL_DAY_DEFAULTS = [
    {"date": "03-18", "name": "18 Mart Çanakkale Zaferi ve Şehitleri Anma Günü", "enabled": True, "target": "all_staff"},
    {"date": "04-23", "name": "23 Nisan Ulusal Egemenlik ve Çocuk Bayramı", "enabled": True, "target": "all_staff"},
    {"date": "05-19", "name": "19 Mayıs Atatürk'ü Anma, Gençlik ve Spor Bayramı", "enabled": True, "target": "all_staff"},
    {"date": "08-30", "name": "30 Ağustos Zafer Bayramı", "enabled": True, "target": "all_staff"},
    {"date": "10-29", "name": "29 Ekim Cumhuriyet Bayramı", "enabled": True, "target": "all_staff"},
    {"date": "12-01", "name": "Seyit Onbaşı Anma Günü", "enabled": True, "target": "all_staff"},
]

TASK_DEFINITIONS.update({
    "staff_birthday": {
        "category": "kutlama",
        "label": "Doğum Günü Kutlaması",
        "short_label": "Doğum Günü",
        "default_hour": 9,
        "default_minute": 0,
        "icon": "fa-cake-candles",
        "description": "Doğum günü olan aktif personele yaş bilgisi göstermeden kurumsal kutlama gönderir.",
        "recipient_group": "celebration_birthday",
        "subject": "Doğum Gününüz Kutlu Olsun",
        "body": """Sayın {ad_soyad},

Doğum gününüzü kutlar; sağlıklı, mutlu ve başarılı bir yaş dileriz.

Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı""",
    },
    "work_anniversary": {
        "category": "kutlama",
        "label": "Göreve Başlama Yıl Dönümü",
        "short_label": "Hizmet Yılı",
        "default_hour": 9,
        "default_minute": 15,
        "icon": "fa-award",
        "description": "Göreve başlama yıl dönümü olan personele kurumsal teşekkür ve kutlama gönderir.",
        "recipient_group": "celebration_anniversary",
        "subject": "Kurum Hizmet Yıl Dönümünüz Kutlu Olsun",
        "body": """Sayın {ad_soyad},

Kurumumuzdaki {hizmet_yili}. hizmet yılınızı kutlar; emekleriniz ve katkılarınız için teşekkür ederiz.

Nice başarılı yıllar dileriz.

Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı""",
    },
    "special_day": {
        "category": "kutlama",
        "label": "Özel Gün Kutlaması",
        "short_label": "Özel Gün",
        "default_hour": 10,
        "default_minute": 0,
        "icon": "fa-flag",
        "description": "Tanımlı resmi/kurumsal özel günlerde hedef kitleye kutlama veya anma mesajı gönderir.",
        "recipient_group": "celebration_special_day",
        "subject": "{ozel_gun_adi}",
        "body": """Sayın {ad_soyad},

{ozel_gun_adi} vesilesiyle iyi dileklerimizi sunarız.

Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı""",
    },
})


def _cic_v40_bool(value: object, default: bool = False) -> bool:
    if value is None:
        return default
    text = str(value).strip().lower()
    if text == "":
        return default
    return text in {"1", "true", "on", "yes", "evet", "aktif", "checked"}


def _cic_v40_parse_date(value: object) -> _cic_v40_date | None:
    if value is None:
        return None
    if isinstance(value, _cic_v40_datetime):
        return value.date()
    if isinstance(value, _cic_v40_date):
        return value
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return _cic_v40_datetime.strptime(text, fmt).date()
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:2033")
            pass
    return None


def _cic_v40_user_date(user: object, *names: str) -> _cic_v40_date | None:
    for name in names:
        try:
            value = getattr(user, name, None)
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:2042")
            value = None
        parsed = _cic_v40_parse_date(value)
        if parsed:
            return parsed
    return None


def _cic_v40_today(now: object = None) -> _cic_v40_date:
    if isinstance(now, _cic_v40_datetime):
        return now.date()
    if isinstance(now, _cic_v40_date):
        return now
    try:
        return _now().date()
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:2057")
        return _cic_v40_date.today()


def _cic_v40_mmdd(d: _cic_v40_date | None) -> str:
    return d.strftime("%m-%d") if d else ""


def _cic_v40_days_until(month_day: str, today: _cic_v40_date | None = None) -> int | None:
    today = today or _cic_v40_today()
    try:
        month, day = [int(x) for x in month_day.split("-", 1)]
        target = _cic_v40_date(today.year, month, day)
        if target < today:
            target = _cic_v40_date(today.year + 1, month, day)
        return (target - today).days
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:2073")
        return None


def _cic_v40_setting_bool(name: str, default: bool = True) -> bool:
    return _cic_v40_bool(get_setting(f"{BASE_KEY}.{name}", "true" if default else "false"), default)


def ensure_celebration_schema() -> dict[str, object]:
    """Kullanici tablosunda kutlama motoru icin gerekli tarih alanlarini guvenli sekilde olusturur."""
    result: dict[str, object] = {"ok": True, "added": [], "warnings": []}
    try:
        from sqlalchemy import inspect as _sa_inspect, text as _sa_text
        inspector = _sa_inspect(db.engine)
        if not inspector.has_table("users"):
            result["ok"] = False
            result["warnings"] = ["users tablosu bulunamadı."]
            return result
        cols = {c.get("name") for c in inspector.get_columns("users")}
        dialect = getattr(db.engine.dialect, "name", "")
        needed = {
            "birth_date": "DATE",
            "hire_date": "DATE",
            "celebration_opt_out": "BOOLEAN DEFAULT FALSE",
        }
        with db.engine.begin() as conn:
            for col, sql_type in needed.items():
                if col in cols:
                    continue
                if dialect == "postgresql":
                    conn.execute(_sa_text(f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col} {sql_type}"))
                else:
                    conn.execute(_sa_text(f"ALTER TABLE users ADD COLUMN {col} {sql_type}"))
                result.setdefault("added", []).append(col)
    except Exception as exc:
        result["ok"] = False
        result.setdefault("warnings", []).append(str(exc))
    return result

# PHASE3A_CIC_EXPLICIT_ENSURE_DEFAULTS_BEGIN
def ensure_defaults(actor_user_id: int | None = None) -> None:
    """Ensure CIC default settings through one explicit public layer."""
    _ensure_defaults_base(actor_user_id=actor_user_id)

    defaults = {
        "celebrations_enabled": ("true", "Ak\u0131ll\u0131 kutlama motoru", "boolean"),
        "birthday_enabled": ("true", "Do\u011fum g\u00fcn\u00fc kutlamalar\u0131", "boolean"),
        "work_anniversary_enabled": ("true", "G\u00f6reve ba\u015flama y\u0131l d\u00f6n\u00fcm\u00fc kutlamalar\u0131", "boolean"),
        "special_day_enabled": ("true", "\u00d6zel g\u00fcn bilgilendirmeleri", "boolean"),
        "celebration_system_notifications_enabled": ("true", "Kutlamalar\u0131 sistem i\u00e7i bildirim olarak da olu\u015ftur", "boolean"),
        "celebrations_include_weekend": ("false", "Hafta sonu kutlamalar\u0131 otomatik \u00e7al\u0131\u015fs\u0131n", "boolean"),
        "special_day_recipient_mode": ("all_active", "\u00d6zel g\u00fcn hedef kitlesi", "string"),
        "special_days": (_dumps_json(_CIC_V40_SPECIAL_DAY_DEFAULTS), "\u00d6zel g\u00fcn takvimi", "json"),
    }

    changed = False
    for key, (value, label, value_type) in defaults.items():
        full_key = f"{BASE_KEY}.{key}"
        if get_setting(full_key, "") == "":
            set_setting(full_key, value, label=label, value_type=value_type, actor_user_id=actor_user_id)
            changed = True

    if changed:
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
# PHASE3A_CIC_EXPLICIT_ENSURE_DEFAULTS_END

def _cic_v40_special_days() -> list[dict[str, object]]:
    data = _loads_json(f"{BASE_KEY}.special_days", _CIC_V40_SPECIAL_DAY_DEFAULTS)
    if not isinstance(data, list):
        return list(_CIC_V40_SPECIAL_DAY_DEFAULTS)
    out: list[dict[str, object]] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        date_value = str(item.get("date") or "").strip()
        name = str(item.get("name") or "").strip()
        if not date_value or not name:
            continue
        out.append({
            "date": date_value,
            "name": name,
            "enabled": _cic_v40_bool(item.get("enabled"), True),
            "target": str(item.get("target") or "all_staff"),
        })
    return out or list(_CIC_V40_SPECIAL_DAY_DEFAULTS)


def _cic_v40_special_days_today(now: object = None) -> list[dict[str, object]]:
    today_key = _cic_v40_mmdd(_cic_v40_today(now))
    return [d for d in _cic_v40_special_days() if d.get("enabled") and str(d.get("date")) == today_key]


def _cic_v40_active_staff_candidates() -> list[User]:
    try:
        users = _active_staff_users()
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:2175")
        users = []
    clean: list[User] = []
    for user in users or []:
        if bool(getattr(user, "celebration_opt_out", False)):
            continue
        clean.append(user)
    return clean


def _cic_v40_birthday_users(now: object = None) -> list[User]:
    if not _cic_v40_setting_bool("celebrations_enabled", True) or not _cic_v40_setting_bool("birthday_enabled", True):
        return []
    today_key = _cic_v40_mmdd(_cic_v40_today(now))
    users: list[User] = []
    for user in _cic_v40_active_staff_candidates():
        birth = _cic_v40_user_date(user, "birth_date", "dogum_tarihi", "date_of_birth")
        if birth and _cic_v40_mmdd(birth) == today_key:
            users.append(user)
    return users


def _cic_v40_service_year(user: object, now: object = None) -> int:
    today = _cic_v40_today(now)
    hire = _cic_v40_user_date(user, "hire_date", "goreve_baslama_tarihi", "ise_baslama_tarihi", "start_date")
    if not hire:
        return 0
    years = today.year - hire.year
    if (today.month, today.day) < (hire.month, hire.day):
        years -= 1
    return max(0, years)


def _cic_v40_anniversary_users(now: object = None) -> list[User]:
    if not _cic_v40_setting_bool("celebrations_enabled", True) or not _cic_v40_setting_bool("work_anniversary_enabled", True):
        return []
    today_key = _cic_v40_mmdd(_cic_v40_today(now))
    users: list[User] = []
    for user in _cic_v40_active_staff_candidates():
        hire = _cic_v40_user_date(user, "hire_date", "goreve_baslama_tarihi", "ise_baslama_tarihi", "start_date")
        if hire and _cic_v40_mmdd(hire) == today_key and _cic_v40_service_year(user, now) > 0:
            users.append(user)
    return users


def _cic_v40_special_day_users(now: object = None) -> list[User]:
    if not _cic_v40_setting_bool("celebrations_enabled", True) or not _cic_v40_setting_bool("special_day_enabled", True):
        return []
    if not _cic_v40_special_days_today(now):
        return []
    mode = get_setting(f"{BASE_KEY}.special_day_recipient_mode", "all_active") or "all_active"
    if mode == "manual":
        try:
            return list(get_recipients().get("staff") or [])
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:2229")
            return []
    return _cic_v40_active_staff_candidates()

# PHASE3A_CIC_EXPLICIT_RECIPIENT_RENDER_BEGIN
def _recipients_for_task(task_key: str, override_users: list[User] | None = None) -> list[User]:
    """Resolve CIC task recipients through one explicit public layer."""
    if override_users is not None:
        return override_users
    if task_key == "staff_birthday":
        return _cic_v40_birthday_users()
    if task_key == "work_anniversary":
        return _cic_v40_anniversary_users()
    if task_key == "special_day":
        return _cic_v40_special_day_users()
    return _recipients_for_task_base(task_key, override_users)


def _render_template_text(text: str, user: User | None, task_key: str) -> str:
    """Render CIC mail template text through one explicit public layer."""
    rendered = _render_template_text_base(text, user, task_key)
    special_names = ", ".join(str(d.get("name")) for d in _cic_v40_special_days_today()) or "\u00d6zel G\u00fcn"
    service_year = _cic_v40_service_year(user) if user is not None else 0
    extra = {
        "ozel_gun_adi": special_names,
        "hizmet_yili": service_year or "de\u011ferli",
        "kutlama_notu": "Ya\u015f bilgisi g\u00f6sterilmeden, KVKK uyumlu kutlama metni olu\u015fturulmu\u015ftur.",
    }
    for key, value in extra.items():
        rendered = rendered.replace("{" + key + "}", str(value))
    return rendered
# PHASE3A_CIC_EXPLICIT_RECIPIENT_RENDER_END


def _cic_v40_create_system_notifications(task_key: str, users: list[User], actor_user_id: int | None = None) -> int:
    if not _cic_v40_setting_bool("celebration_system_notifications_enabled", True):
        return 0
    if task_key not in _CIC_V40_CELEBRATION_TASKS:
        return 0
    try:
        from app.models import Notification
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:2286")
        return 0
    today_id = int(_cic_v40_today().strftime("%Y%m%d"))
    tmpl = get_template(task_key)
    created = 0
    for user in users or []:
        try:
            exists = Notification.query.filter_by(
                user_id=getattr(user, "id", None),
                notification_type="corporate_celebration",
                source_type=task_key,
                source_id=today_id,
            ).first()
            if exists:
                continue
            title = _render_template_text(tmpl.get("subject", "Kurumsal Kutlama"), user, task_key).strip()[:255] or "Kurumsal Kutlama"
            body = _render_template_text(tmpl.get("body", ""), user, task_key).strip()
            db.session.add(Notification(
                user_id=getattr(user, "id"),
                title=title,
                body=body,
                notification_type="corporate_celebration",
                source_type=task_key,
                source_id=today_id,
                link_url="/dashboard/kurumsal-bilgilendirme/kutlamalar",
                priority="normal",
                is_read=False,
            ))
            created += 1
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:2315")
            pass
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
    return created

# PHASE3A_CIC_EXPLICIT_SEND_TASK_BEGIN
def send_task(task_key: str, *, dry_run: bool = False, override_users: list[User] | None = None, actor_user_id: int | None = None) -> dict[str, _cic_v40_Any]:
    """Send CIC mail task through one explicit public layer.

    Preserves current runtime behavior:
    - V11 direct mail implementation is handled by _send_task_base.
    - V40 celebration system notifications are applied after successful base execution path.
    """
    users_for_notification: list[User] = []
    if task_key in _CIC_V40_CELEBRATION_TASKS and override_users is None:
        users_for_notification = list(_recipients_for_task(task_key) or [])
    elif task_key in _CIC_V40_CELEBRATION_TASKS and override_users is not None:
        users_for_notification = list(override_users or [])

    result = _send_task_base(
        task_key,
        dry_run=dry_run,
        override_users=override_users,
        actor_user_id=actor_user_id,
    )

    if task_key in _CIC_V40_CELEBRATION_TASKS and not dry_run:
        result["system_notification_count"] = _cic_v40_create_system_notifications(
            task_key,
            users_for_notification,
            actor_user_id=actor_user_id,
        )

    return result
# PHASE3A_CIC_EXPLICIT_SEND_TASK_END

def _cic_v40_date_input(value: object) -> str:
    d = _cic_v40_parse_date(value)
    return d.isoformat() if d else ""


def _cic_v40_upcoming_users(kind: str, days: int = 30) -> list[dict[str, object]]:
    today = _cic_v40_today()
    rows: list[dict[str, object]] = []
    for user in _cic_v40_active_staff_candidates():
        if kind == "birthday":
            d = _cic_v40_user_date(user, "birth_date", "dogum_tarihi", "date_of_birth")
        else:
            d = _cic_v40_user_date(user, "hire_date", "goreve_baslama_tarihi", "ise_baslama_tarihi", "start_date")
        if not d:
            continue
        left = _cic_v40_days_until(_cic_v40_mmdd(d), today)
        if left is None or left > days:
            continue
        row = {"user": user, "date": d, "days_left": left}
        if kind == "anniversary":
            row["service_year"] = _cic_v40_service_year(user, today)
            if int(row["service_year"] or 0) <= 0:
                continue
        rows.append(row)
    return sorted(rows, key=lambda x: int(x.get("days_left") or 0))


def _cic_v40_upcoming_special_days(days: int = 45) -> list[dict[str, object]]:
    today = _cic_v40_today()
    rows: list[dict[str, object]] = []
    for item in _cic_v40_special_days():
        left = _cic_v40_days_until(str(item.get("date") or ""), today)
        if left is None or left > days:
            continue
        rows.append({**item, "days_left": left})
    return sorted(rows, key=lambda x: int(x.get("days_left") or 0))


def celebration_context(search: str | None = None) -> dict[str, _cic_v40_Any]:
    ensure_defaults()
    schema = ensure_celebration_schema()
    data = context(search)
    users = list_users(search=search, limit=1000)
    today_birthdays = _cic_v40_birthday_users()
    today_anniversaries = _cic_v40_anniversary_users()
    today_specials = _cic_v40_special_days_today()
    data.update({
        "active_tab": "celebrations",
        "celebration": {
            "schema": schema,
            "settings": {
                "celebrations_enabled": _cic_v40_setting_bool("celebrations_enabled", True),
                "birthday_enabled": _cic_v40_setting_bool("birthday_enabled", True),
                "work_anniversary_enabled": _cic_v40_setting_bool("work_anniversary_enabled", True),
                "special_day_enabled": _cic_v40_setting_bool("special_day_enabled", True),
                "system_notifications_enabled": _cic_v40_setting_bool("celebration_system_notifications_enabled", True),
                "include_weekend": _cic_v40_setting_bool("celebrations_include_weekend", False),
                "special_day_recipient_mode": get_setting(f"{BASE_KEY}.special_day_recipient_mode", "all_active") or "all_active",
            },
            "special_days": _cic_v40_special_days(),
            "special_days_json": _dumps_json(_cic_v40_special_days()),
            "today_birthdays": today_birthdays,
            "today_anniversaries": today_anniversaries,
            "today_specials": today_specials,
            "upcoming_birthdays": _cic_v40_upcoming_users("birthday", 30),
            "upcoming_anniversaries": _cic_v40_upcoming_users("anniversary", 30),
            "upcoming_special_days": _cic_v40_upcoming_special_days(45),
            "users": users,
            "stats": {
                "today_total": len(today_birthdays) + len(today_anniversaries) + len(today_specials),
                "birthday_count": len(today_birthdays),
                "anniversary_count": len(today_anniversaries),
                "special_day_count": len(today_specials),
                "upcoming_total": len(_cic_v40_upcoming_users("birthday", 30)) + len(_cic_v40_upcoming_users("anniversary", 30)) + len(_cic_v40_upcoming_special_days(45)),
            },
        },
    })
    return data


def save_celebration_settings(payload: dict[str, object], actor_user_id: int | None = None) -> None:
    ensure_celebration_schema()
    bool_fields = [
        "celebrations_enabled",
        "birthday_enabled",
        "work_anniversary_enabled",
        "special_day_enabled",
        "celebration_system_notifications_enabled",
        "celebrations_include_weekend",
    ]
    for field in bool_fields:
        set_setting(f"{BASE_KEY}.{field}", "true" if _cic_v40_bool(payload.get(field), False) else "false", label=field, value_type="boolean", actor_user_id=actor_user_id)
    mode = str(payload.get("special_day_recipient_mode") or "all_active").strip()
    if mode not in {"all_active", "manual"}:
        mode = "all_active"
    set_setting(f"{BASE_KEY}.special_day_recipient_mode", mode, label="Özel gün hedef kitlesi", value_type="string", actor_user_id=actor_user_id)

    raw_days = str(payload.get("special_days_json") or "").strip()
    if raw_days:
        try:
            parsed = json.loads(raw_days)
            if isinstance(parsed, list):
                set_setting(f"{BASE_KEY}.special_days", _dumps_json(parsed), label="Özel gün takvimi", value_type="json", actor_user_id=actor_user_id)
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 CIC kontrollü geri dönüş bloğu çalıştı")
            set_setting(f"{BASE_KEY}.special_days.last_error", "Özel gün JSON formatı geçerli değil; eski takvim korundu.", label="Özel gün son hata", value_type="text", actor_user_id=actor_user_id)

    ids = []
    try:
        ids = payload.getlist("user_ids") if hasattr(payload, "getlist") else payload.get("user_ids", [])
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:2452")
        ids = []
    for raw_id in ids or []:
        try:
            uid = int(raw_id)
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:2457")
            continue
        user = db.session.get(User, uid)
        if not user:
            continue
        birth_value = str(payload.get(f"birth_date_{uid}") or "").strip()
        hire_value = str(payload.get(f"hire_date_{uid}") or "").strip()
        opt_out = _cic_v40_bool(payload.get(f"celebration_opt_out_{uid}"), False)
        if hasattr(user, "birth_date"):
            setattr(user, "birth_date", _cic_v40_parse_date(birth_value))
        if hasattr(user, "hire_date"):
            setattr(user, "hire_date", _cic_v40_parse_date(hire_value))
        if hasattr(user, "celebration_opt_out"):
            setattr(user, "celebration_opt_out", opt_out)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

def _cic_v40_run_weekend_celebrations(current: _cic_v40_datetime, dry_run: bool = False, actor_user_id: int | None = None) -> list[dict[str, object]]:
    if not _cic_v40_setting_bool("celebrations_include_weekend", False):
        return []
    cfg = get_config()
    tasks_cfg = cfg.get("tasks", {}) if isinstance(cfg, dict) else {}
    results: list[dict[str, object]] = []
    today = current.strftime("%Y-%m-%d")
    late_window = int(get_auto_scheduler_config().get("late_window_minutes") or 20)
    for task_key in _CIC_V40_CELEBRATION_TASKS:
        task_cfg = tasks_cfg.get(task_key, {}) if isinstance(tasks_cfg, dict) else {}
        if not task_cfg.get("enabled", False):
            continue
        hour = int(task_cfg.get("hour", TASK_DEFINITIONS[task_key].get("default_hour", 9)))
        minute = int(task_cfg.get("minute", TASK_DEFINITIONS[task_key].get("default_minute", 0)))
        scheduled = current.replace(hour=max(0, min(23, hour)), minute=max(0, min(59, minute)), second=0, microsecond=0)
        diff_minutes = (current - scheduled).total_seconds() / 60.0
        last_run = get_setting(_cic_auto_last_run_key(task_key), "") or ""
        if last_run.startswith(today):
            continue
        if not (0 <= diff_minutes <= late_window):
            continue
        result = send_task(task_key, dry_run=dry_run, actor_user_id=actor_user_id)
        set_setting(_cic_auto_last_run_key(task_key), current.strftime("%Y-%m-%d %H:%M:%S"), label=f"{TASK_DEFINITIONS[task_key].get('label', task_key)} son otomatik çalışma", actor_user_id=actor_user_id)
        results.append({"task_key": task_key, "action": "ran", "result": result})
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
    return results

# PHASE3A_CIC_EXPLICIT_RUN_DUE_TASKS_BEGIN
def run_due_tasks(*, now: _cic_v40_datetime | None = None, dry_run: bool = False, actor_user_id: int | None = None, force: bool = False) -> dict[str, _cic_v40_Any]:
    """Run due CIC mail tasks through one explicit public layer.

    Flattened legacy wrapper chain:
    - Base scheduler execution is handled by _run_due_tasks_base.
    - Weekend celebration exception tasks are applied explicitly after the base result.
    """
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
# PHASE3A_CIC_EXPLICIT_RUN_DUE_TASKS_END


# BYS360_CIC_V4_0_SMART_CELEBRATIONS_END

# BYS360_CIC_V4_5_CELEBRATION_EXCEL_IMPORT_BEGIN
# Kutlama tarihleri için güvenli Excel ön kontrol ve uygulama motoru.
from datetime import date as _cic_v45_date, datetime as _cic_v45_datetime, timedelta as _cic_v45_timedelta
import re as _cic_v45_re
import unicodedata as _cic_v45_unicodedata


def _cic_v45_text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _cic_v45_norm(value: object) -> str:
    text = _cic_v45_text(value).lower()
    repl = str.maketrans({"ı":"i","İ":"i","ğ":"g","Ğ":"g","ü":"u","Ü":"u","ş":"s","Ş":"s","ö":"o","Ö":"o","ç":"c","Ç":"c"})
    text = text.translate(repl)
    text = _cic_v45_unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not _cic_v45_unicodedata.combining(ch))
    return _cic_v45_re.sub(r"[^a-z0-9]+", "", text)


def _cic_v45_norm_name(value: object) -> str:
    text = _cic_v45_text(value).lower()
    repl = str.maketrans({"ı":"i","İ":"i","ğ":"g","Ğ":"g","ü":"u","Ü":"u","ş":"s","Ş":"s","ö":"o","Ö":"o","ç":"c","Ç":"c"})
    text = text.translate(repl)
    return _cic_v45_re.sub(r"\s+", " ", _cic_v45_re.sub(r"[^a-z0-9 ]+", " ", text)).strip()


def _cic_v45_bool(value: object) -> bool | None:
    raw = _cic_v45_text(value)
    if not raw:
        return None
    text = _cic_v45_norm(raw)
    if text in {"1","true","evet","e","yes","y","aktif","pasifdegil","kutlamadisi","harictut"}:
        return True
    if text in {"0","false","hayir","h","no","n","pasif","yok"}:
        return False
    return None


def _cic_v45_parse_date(value: object) -> _cic_v45_date | None:
    if value is None:
        return None
    if isinstance(value, _cic_v45_datetime):
        return value.date()
    if isinstance(value, _cic_v45_date):
        return value
    if isinstance(value, (int, float)):
        try:
            if value > 20000:
                return (_cic_v45_datetime(1899, 12, 30) + _cic_v45_timedelta(days=float(value))).date()
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:2583")
            pass
    text = _cic_v45_text(value)
    if not text:
        return None
    text = text.replace("-", ".").replace("/", ".")
    for fmt in ("%d.%m.%Y", "%Y.%m.%d", "%d.%m.%y"):
        try:
            return _cic_v45_datetime.strptime(text, fmt).date()
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:2592")
            pass
    return None


def _cic_v45_header_key(value: object) -> str | None:
    h = _cic_v45_norm(value)
    mapping = {
        "sicilno":"sicil_no", "sicil":"sicil_no", "personelsicilno":"sicil_no", "kurumsicilno":"sicil_no",
        "adsoyad":"ad_soyad", "adisoyadi":"ad_soyad", "adsoyadi":"ad_soyad", "personel":"ad_soyad", "ad":"ad", "soyad":"soyad",
        "eposta":"email", "email":"email", "mail":"email", "kurummail":"email", "kurumeposta":"email",
        "dogumtarihi":"birth_date", "dogumgunu":"birth_date", "birthdate":"birth_date", "birthday":"birth_date",
        "isebaslamatarihi":"hire_date", "gorevebaslamatarihi":"hire_date", "baslamatarihi":"hire_date", "hizmetbaslangic":"hire_date", "hiredate":"hire_date",
        "kutlamadisi":"celebration_opt_out", "kutlamaharic":"celebration_opt_out", "kutlamaistemiyor":"celebration_opt_out", "optout":"celebration_opt_out",
        "not":"note", "aciklama":"note",
    }
    return mapping.get(h)


def _cic_v45_ensure_schema() -> None:
    try:
        from sqlalchemy import inspect as _sa_inspect, text as _sa_text
        inspector = _sa_inspect(db.engine)
        if not inspector.has_table("users"):
            return
        cols = {c.get("name") for c in inspector.get_columns("users")}
        with db.engine.begin() as conn:
            if "birth_date" not in cols:
                conn.execute(_sa_text("ALTER TABLE users ADD COLUMN IF NOT EXISTS birth_date DATE"))
            if "hire_date" not in cols:
                conn.execute(_sa_text("ALTER TABLE users ADD COLUMN IF NOT EXISTS hire_date DATE"))
            if "celebration_opt_out" not in cols:
                conn.execute(_sa_text("ALTER TABLE users ADD COLUMN IF NOT EXISTS celebration_opt_out BOOLEAN NOT NULL DEFAULT FALSE"))
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:2625")
        pass


def _cic_v45_existing_user_rows() -> list[dict[str, object]]:
    from sqlalchemy import inspect as _sa_inspect, text as _sa_text
    inspector = _sa_inspect(db.engine)
    cols = {c.get("name") for c in inspector.get_columns("users")}
    select_cols = ["id"]
    for col in ("sicil_no", "email", "ad", "soyad", "name", "full_name_cache"):
        if col in cols:
            select_cols.append(col)
    sql = "SELECT " + ", ".join(select_cols) + " FROM users"
    rows = db.session.execute(_sa_text(sql)).mappings().all()
    return [dict(r) for r in rows]


def _cic_v45_build_user_indexes(rows: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    by_sicil: dict[str, dict[str, object]] = {}
    by_email: dict[str, dict[str, object]] = {}
    by_name: dict[str, dict[str, object]] = {}
    for r in rows:
        sicil = _cic_v45_text(r.get("sicil_no"))
        email = _cic_v45_text(r.get("email")).lower()
        adsoyad = _cic_v45_text(((_cic_v45_text(r.get("ad")) + " " + _cic_v45_text(r.get("soyad"))).strip()) or r.get("full_name_cache") or r.get("name"))
        if sicil and sicil not in by_sicil:
            by_sicil[sicil] = r
        if email and email not in by_email:
            by_email[email] = r
        n = _cic_v45_norm_name(adsoyad)
        if n and n not in by_name:
            by_name[n] = r
    return {"sicil": by_sicil, "email": by_email, "name": by_name}


def import_celebration_dates_from_excel(file_storage: object, *, apply: bool = False, actor_user_id: int | None = None) -> dict[str, object]:
    _cic_v45_ensure_schema()
    result: dict[str, object] = {"ok": True, "mode": "apply" if apply else "preview", "total_rows": 0, "matched": 0, "updated": 0, "unmatched": 0, "skipped": 0, "errors": [], "warnings": [], "preview_rows": []}
    if file_storage is None or not getattr(file_storage, "filename", ""):
        result["ok"] = False
        result["errors"].append("Excel dosyası seçilmedi.")
        return result
    filename = str(getattr(file_storage, "filename", ""))
    if not filename.lower().endswith((".xlsx", ".xlsm")):
        result["ok"] = False
        result["errors"].append("Sadece .xlsx veya .xlsm dosyası yüklenebilir.")
        return result
    try:
        from openpyxl import load_workbook as _cic_v45_load_workbook
    except Exception:
        result["ok"] = False
        result["errors"].append("Excel okuma kütüphanesi bulunamadı. openpyxl kurulumu gerekiyor.")
        return result
    try:
        stream = getattr(file_storage, "stream", file_storage)
        try:
            stream.seek(0)
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/corporate_information_center.py:2682")
            pass
        wb = _cic_v45_load_workbook(stream, data_only=True, read_only=True)
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        headers = next(rows_iter, None)
    except Exception as exc:
        result["ok"] = False
        result["errors"].append("Excel dosyası okunamadı: " + str(exc))
        return result
    if not headers:
        result["ok"] = False
        result["errors"].append("Excel dosyasında başlık satırı bulunamadı.")
        return result
    header_map: dict[int, str] = {}
    for idx, h in enumerate(headers):
        key = _cic_v45_header_key(h)
        if key and key not in header_map.values():
            header_map[idx] = key
    if "sicil_no" not in header_map.values() and "email" not in header_map.values() and "ad_soyad" not in header_map.values():
        result["ok"] = False
        result["errors"].append("Eşleştirme için Sicil No, E-posta veya Ad Soyad başlığı bulunmalı.")
        return result
    if "birth_date" not in header_map.values() and "hire_date" not in header_map.values() and "celebration_opt_out" not in header_map.values():
        result["ok"] = False
        result["errors"].append("Güncellenecek alan bulunamadı. Doğum Tarihi, İşe Başlama Tarihi veya Kutlama Dışı başlığı gerekli.")
        return result
    indexes = _cic_v45_build_user_indexes(_cic_v45_existing_user_rows())
    updates: list[dict[str, object]] = []
    from sqlalchemy import text as _sa_text
    for excel_row_no, row in enumerate(rows_iter, start=2):
        values = {key: row[idx] if idx < len(row) else None for idx, key in header_map.items()}
        if not any(_cic_v45_text(v) for v in values.values()):
            continue
        result["total_rows"] = int(result["total_rows"]) + 1
        sicil = _cic_v45_text(values.get("sicil_no"))
        email = _cic_v45_text(values.get("email")).lower()
        name = _cic_v45_text(values.get("ad_soyad")) or (_cic_v45_text(values.get("ad")) + " " + _cic_v45_text(values.get("soyad"))).strip()
        user = None
        match_by = ""
        if sicil and sicil in indexes["sicil"]:
            user = indexes["sicil"][sicil]; match_by = "Sicil No"
        elif email and email in indexes["email"]:
            user = indexes["email"][email]; match_by = "E-posta"
        else:
            n = _cic_v45_norm_name(name)
            if n and n in indexes["name"]:
                user = indexes["name"][n]; match_by = "Ad Soyad"
        if not user:
            result["unmatched"] = int(result["unmatched"]) + 1
            if len(result["warnings"]) < 25:
                result["warnings"].append(f"Satır {excel_row_no}: Personel eşleşmedi ({sicil or email or name or 'tanımsız'}).")
            continue
        birth_date = _cic_v45_parse_date(values.get("birth_date")) if "birth_date" in values else None
        hire_date = _cic_v45_parse_date(values.get("hire_date")) if "hire_date" in values else None
        opt_raw = values.get("celebration_opt_out") if "celebration_opt_out" in values else None
        opt_out = _cic_v45_bool(opt_raw)
        fields: dict[str, object] = {}
        if "birth_date" in values and values.get("birth_date") not in (None, ""):
            if birth_date:
                fields["birth_date"] = birth_date
            else:
                result["warnings"].append(f"Satır {excel_row_no}: Doğum tarihi okunamadı.")
        if "hire_date" in values and values.get("hire_date") not in (None, ""):
            if hire_date:
                fields["hire_date"] = hire_date
            else:
                result["warnings"].append(f"Satır {excel_row_no}: İşe başlama tarihi okunamadı.")
        if opt_raw not in (None, "") and opt_out is not None:
            fields["celebration_opt_out"] = bool(opt_out)
        if not fields:
            result["skipped"] = int(result["skipped"]) + 1
            continue
        result["matched"] = int(result["matched"]) + 1
        preview = {"row": excel_row_no, "user_id": user.get("id"), "match_by": match_by, "sicil_no": sicil or _cic_v45_text(user.get("sicil_no")), "ad_soyad": name or ((_cic_v45_text(user.get("ad")) + " " + _cic_v45_text(user.get("soyad"))).strip()), "birth_date": str(fields.get("birth_date") or ""), "hire_date": str(fields.get("hire_date") or ""), "celebration_opt_out": fields.get("celebration_opt_out") if "celebration_opt_out" in fields else ""}
        if len(result["preview_rows"]) < 30:
            result["preview_rows"].append(preview)
        if apply:
            updates.append({"id": int(user["id"]), "fields": fields})
    if apply and updates:
        with db.engine.begin() as conn:
            for item in updates:
                fields = item["fields"]
                set_sql = []
                params: dict[str, object] = {"id": item["id"]}
                for col, val in fields.items():
                    set_sql.append(f"{col} = :{col}")
                    params[col] = val
                if set_sql:
                    conn.execute(_sa_text("UPDATE users SET " + ", ".join(set_sql) + " WHERE id = :id"), params)
                    result["updated"] = int(result["updated"]) + 1
    if not apply:
        result["warnings"].insert(0, "Ön kontrol yapıldı; veritabanına kayıt yazılmadı.")
    else:
        result["warnings"].insert(0, f"Uygulama tamamlandı; {result['updated']} personel kaydı güncellendi.")
    return result
# BYS360_CIC_V4_5_CELEBRATION_EXCEL_IMPORT_END
