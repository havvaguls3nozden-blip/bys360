from __future__ import annotations

import json
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any
import logging
logger = logging.getLogger(__name__)

try:
    from app import db
except Exception:
    logger.exception("BYS360 V6C guarded exception | file=app/services/executive_mail_center_v2.py | line=13")
    db = None
try:
    from app.models.user import User
except Exception:
    logger.exception("BYS360 V6C guarded exception | file=app/services/executive_mail_center_v2.py | line=17")
    try:
        from app.models import User
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/executive_mail_center_v2.py | line=20")
        User = None
try:
    from app.models.communication_models import MailLog
except Exception:
    logger.exception("BYS360 V6C guarded exception | file=app/services/executive_mail_center_v2.py | line=24")
    MailLog = None
try:
    from app.services.mail_core import send_email, create_mail_log
except Exception:
    logger.exception("BYS360 V6C guarded exception | file=app/services/executive_mail_center_v2.py | line=28")
    send_email = None
    create_mail_log = None
try:
    from app.services.settings.system_settings_service import get_setting_value, set_setting_value
except Exception:
    logger.exception("BYS360 V6C guarded exception | file=app/services/executive_mail_center_v2.py | line=33")
    def get_setting_value(key, default=None): return default
    def set_setting_value(key, value, actor_user_id=None): return None

SETTING_PREFIX = "executive_mail_center.v2"
DEFAULT_LOCATION = {"city": "Çanakkale", "latitude": "40.1467", "longitude": "26.4086"}
TASK_DEFINITIONS = [
    {"key":"manager_morning","audience":"managers","period":"morning","hour":8,"minute":0,"title":"Amir/Yönetici Sabah Özeti","description":"Amirlere sabah kurum içi durum, bekleyen işler ve kısa yönetici notu gönderir.","subject":"BYS360 Sabah Yönetici Özeti | {date}","enabled":True},
    {"key":"manager_evening","audience":"managers","period":"evening","hour":17,"minute":30,"title":"Amir/Yönetici Akşam Özeti","description":"Amirlere gün sonu durum, tamamlanan/bekleyen işler ve ertesi gün dikkat notu gönderir.","subject":"BYS360 Akşam Yönetici Özeti | {date}","enabled":True},
    {"key":"staff_morning","audience":"staff","period":"morning","hour":8,"minute":15,"title":"Personel Sabah Günaydın ve Hava Durumu","description":"Personele günaydın mesajı, güncel hava durumu ve kıyafet önerisi gönderir.","subject":"Günaydın | BYS360 Günlük Bilgilendirme | {date}","enabled":True},
    {"key":"staff_midday","audience":"staff","period":"midday","hour":13,"minute":0,"title":"Personel Gün Ortası Mesai Kontrolü","description":"Personele gün ortası iyi dilek ve geri bildirim bağlantısı gönderir.","subject":"BYS360 Gün Ortası Bilgilendirme | {date}","enabled":True},
    {"key":"staff_evening","audience":"staff","period":"evening","hour":17,"minute":15,"title":"Personel Akşam ve Yarın Hava Durumu","description":"Personele iyi akşamlar mesajı, yarın hava durumu ve hazırlık önerisi gönderir.","subject":"İyi Akşamlar | BYS360 Yarın Bilgilendirmesi | {date}","enabled":True},
]

def _key(name: str) -> str: return f"{SETTING_PREFIX}.{name}"
def _loads(raw: Any, default: Any):
    if raw in (None, ""): return default
    if isinstance(raw, (list, dict, bool, int, float)): return raw
    try: return json.loads(str(raw))
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/executive_mail_center_v2.py:60")
        return default
def _dumps(value: Any) -> str: return json.dumps(value, ensure_ascii=False, indent=2)
def _get(name: str, default: Any=None): return get_setting_value(_key(name), default)
def _set(name: str, value: Any, actor_user_id: int|None=None): return set_setting_value(_key(name), value if isinstance(value, str) else _dumps(value), actor_user_id=actor_user_id)

def ensure_defaults(actor_user_id: int|None=None) -> None:
    if not _get("tasks"): _set("tasks", TASK_DEFINITIONS, actor_user_id)
    if not _get("manager_recipient_ids"): _set("manager_recipient_ids", [], actor_user_id)
    if not _get("staff_recipient_ids"): _set("staff_recipient_ids", [], actor_user_id)
    if not _get("pilot_mode"): _set("pilot_mode", True, actor_user_id)
    if not _get("location"): _set("location", DEFAULT_LOCATION, actor_user_id)

def normalize_tasks(tasks: list[dict[str, Any]]|None=None) -> list[dict[str, Any]]:
    incoming = {str(t.get("key")): dict(t) for t in (tasks or []) if t.get("key")}
    out=[]
    for base in TASK_DEFINITIONS:
        item=dict(base); item.update(incoming.get(base["key"], {}))
        try: item["hour"] = max(0, min(23, int(item.get("hour", base["hour"]))))
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/executive_mail_center_v2.py:78")
            item["hour"] = base["hour"]
        try: item["minute"] = max(0, min(59, int(item.get("minute", base["minute"]))))
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/executive_mail_center_v2.py:80")
            item["minute"] = base["minute"]
        item["enabled"] = str(item.get("enabled", True)).lower() in {"1","true","on","yes","evet"}
        item["time_label"] = f"{item['hour']:02d}:{item['minute']:02d}"
        out.append(item)
    return out

def current_config() -> dict[str, Any]:
    ensure_defaults()
    return {
        "tasks": normalize_tasks(_loads(_get("tasks"), TASK_DEFINITIONS)),
        "manager_recipient_ids": [int(x) for x in _loads(_get("manager_recipient_ids"), []) if str(x).isdigit()],
        "staff_recipient_ids": [int(x) for x in _loads(_get("staff_recipient_ids"), []) if str(x).isdigit()],
        "pilot_mode": str(_get("pilot_mode", "true")).lower() in {"1","true","on","yes","evet"},
        "location": _loads(_get("location"), DEFAULT_LOCATION),
    }

def _parse_ids(values: Any) -> list[int]:
    if values is None: return []
    if isinstance(values, str): values = values.replace(";", ",").split(",")
    ids=[]
    for v in values:
        try:
            i=int(v)
            if i not in ids: ids.append(i)
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/executive_mail_center_v2.py:104")
            pass
    return ids

def save_tasks_from_form(form: Any, actor_user_id: int|None=None) -> list[dict[str, Any]]:
    tasks=[]
    for base in TASK_DEFINITIONS:
        key=base["key"]; item=dict(base)
        item["enabled"] = str(form.get(f"{key}_enabled") or "").lower() in {"1","on","true","yes","evet"}
        item["hour"] = form.get(f"{key}_hour") or base["hour"]
        item["minute"] = form.get(f"{key}_minute") or base["minute"]
        tasks.append(item)
    tasks=normalize_tasks(tasks); _set("tasks", tasks, actor_user_id); return tasks

def save_recipients_from_form(form: Any, actor_user_id: int|None=None) -> dict[str, Any]:
    getlist = form.getlist if hasattr(form, "getlist") else lambda k: form.get(k, [])
    _set("manager_recipient_ids", _parse_ids(getlist("manager_recipient_ids")), actor_user_id)
    _set("staff_recipient_ids", _parse_ids(getlist("staff_recipient_ids")), actor_user_id)
    _set("pilot_mode", str(form.get("pilot_mode") or "").lower() in {"1","on","true","yes","evet"}, actor_user_id)
    return current_config()

def save_location_from_form(form: Any, actor_user_id: int|None=None) -> dict[str, str]:
    loc={"city":(form.get("city") or DEFAULT_LOCATION["city"]).strip() or DEFAULT_LOCATION["city"], "latitude":(form.get("latitude") or DEFAULT_LOCATION["latitude"]).strip() or DEFAULT_LOCATION["latitude"], "longitude":(form.get("longitude") or DEFAULT_LOCATION["longitude"]).strip() or DEFAULT_LOCATION["longitude"]}
    _set("location", loc, actor_user_id); return loc

def list_users(search: str|None=None, limit: int=500) -> list[Any]:
    if User is None: return []
    q=User.query
    if hasattr(User, "is_active"):
        try: q=q.filter(User.is_active.is_(True))
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/executive_mail_center_v2.py:133")
            pass
    if search:
        from sqlalchemy import or_
        s=f"%{search.strip()}%"; filters=[]
        for attr in ("full_name","name","email","username","sicil_no","registry_no"):
            col=getattr(User, attr, None)
            if col is not None: filters.append(col.ilike(s))
        if filters: q=q.filter(or_(*filters))
    order=getattr(User,"full_name",None) or getattr(User,"name",None) or getattr(User,"id")
    return q.order_by(User.id.asc()).limit(limit).all()

def user_display_name(u: Any) -> str: return (getattr(u,"full_name",None) or getattr(u,"name",None) or getattr(u,"username",None) or f"Kullanıcı #{getattr(u,'id','-')}")
def user_email(u: Any) -> str: return (getattr(u,"email",None) or "").strip().lower()
def users_by_ids(ids: list[int]) -> list[Any]:
    if not ids or User is None: return []
    rows=User.query.filter(User.id.in_(ids)).all(); by={int(u.id):u for u in rows}
    return [by[i] for i in ids if i in by]
def selected_people() -> dict[str, list[Any]]:
    cfg=current_config(); return {"managers": users_by_ids(cfg["manager_recipient_ids"]), "staff": users_by_ids(cfg["staff_recipient_ids"])}
def get_recent_logs(limit: int=80) -> list[Any]:
    if MailLog is None: return []
    try: return MailLog.query.filter(MailLog.mail_type.like("exec_center_%")).order_by(MailLog.sent_at.desc(), MailLog.id.desc()).limit(limit).all()
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/executive_mail_center_v2.py:155")
        return []

def _weather_code_text(code: int|None) -> str:
    mapping={0:"Açık",1:"Az bulutlu",2:"Parçalı bulutlu",3:"Bulutlu",45:"Sisli",48:"Kırağılı sis",51:"Hafif çiseleme",53:"Çiseleme",55:"Yoğun çiseleme",61:"Hafif yağmur",63:"Yağmur",65:"Kuvvetli yağmur",71:"Hafif kar",73:"Kar",75:"Yoğun kar",80:"Kısa süreli yağmur",81:"Sağanak yağmur",82:"Kuvvetli sağanak",95:"Gök gürültülü"}
    return mapping.get(code, "Hava durumu bilgisi")

def fetch_weather(location: dict[str,str]|None=None) -> dict[str, Any]:
    loc=location or current_config().get("location") or DEFAULT_LOCATION
    params=urllib.parse.urlencode({"latitude":loc.get("latitude",DEFAULT_LOCATION["latitude"]),"longitude":loc.get("longitude",DEFAULT_LOCATION["longitude"]),"current":"temperature_2m,weather_code,wind_speed_10m","daily":"weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max","timezone":"Europe/Istanbul","forecast_days":2})
    try:
        with urllib.request.urlopen(f"https://api.open-meteo.com/v1/forecast?{params}", timeout=15) as r: data=json.loads(r.read().decode("utf-8"))
        cur=data.get("current") or {}; daily=data.get("daily") or {}
        def arr(name, idx):
            vals=daily.get(name) or []
            return vals[idx] if len(vals)>idx else None
        return {"ok":True,"city":loc.get("city") or "Çanakkale","today":{"condition":_weather_code_text(cur.get("weather_code")),"temp":cur.get("temperature_2m"),"wind":cur.get("wind_speed_10m"),"max":arr("temperature_2m_max",0),"min":arr("temperature_2m_min",0),"rain":arr("precipitation_probability_max",0)},"tomorrow":{"condition":_weather_code_text(arr("weather_code",1)),"max":arr("temperature_2m_max",1),"min":arr("temperature_2m_min",1),"rain":arr("precipitation_probability_max",1)},"source":"Open-Meteo"}
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/services/executive_mail_center_v2.py | line=163")
        return {"ok":False,"city":loc.get("city") or "Çanakkale","today":{},"tomorrow":{},"source":"fallback","error":str(exc)}

def clothing_advice(weather: dict[str, Any], tomorrow: bool=False) -> str:
    day=weather.get("tomorrow" if tomorrow else "today") or {}; text=(day.get("condition") or "").lower(); rain=day.get("rain"); temp=day.get("max") or day.get("temp")
    try:
        if rain is not None and int(rain)>=50: return "Yağış ihtimaline karşı şemsiye veya yağmurluk bulundurmanız önerilir."
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/executive_mail_center_v2.py:179")
        pass
    if "yağmur" in text or "sağanak" in text: return "Yağış ihtimaline karşı şemsiye veya yağmurluk bulundurmanız önerilir."
    try:
        t=float(temp)
        if t>=28: return "Hafif ve rahat kıyafetler tercih edilebilir; dış görevlerde güneşten korunmak faydalı olur."
        if t<=12: return "Serin hava nedeniyle katmanlı ve koruyucu kıyafet tercih edilmesi önerilir."
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/executive_mail_center_v2.py:185")
        pass
    return "Gün içinde rahat ve mevsime uygun kıyafet tercih edilmesi yeterli olacaktır."

def build_body(task: dict[str, Any], recipient: Any|None=None) -> str:
    d=datetime.now().strftime("%d.%m.%Y"); name=user_display_name(recipient) if recipient else "Çalışma arkadaşımız"; w=fetch_weather(); city=w.get("city","Çanakkale")
    if task["audience"]=="managers":
        intro="Günaydın. BYS360 yönetici özeti kapsamında güne başlarken dikkat edilmesi gereken başlıklar aşağıda sunulmuştur." if task["period"]=="morning" else "İyi akşamlar. BYS360 gün sonu yönetici özeti kapsamında günün genel durumu ve ertesi gün için dikkat notu aşağıda sunulmuştur."
        return f"""Sayın Yönetici,\n\n{intro}\n\nTarih: {d}\n\nÖzet Başlıkları:\n- BYS360 otomatik bildirim ve mail altyapısı çalışır durumdadır.\n- Bekleyen süreçler, destek talepleri, geri bildirimler ve performans görünürlüğü Yönetici Özeti ekranından takip edilmelidir.\n- Mail gönderim kayıtları Mail Logları alanında izlenebilir.\n\nHava Durumu ({city}):\n- Bugün: {w.get('today',{}).get('condition','Bilgi alınamadı')} | {w.get('today',{}).get('min','-')}°C / {w.get('today',{}).get('max','-')}°C\n- Yarın: {w.get('tomorrow',{}).get('condition','Bilgi alınamadı')} | {w.get('tomorrow',{}).get('min','-')}°C / {w.get('tomorrow',{}).get('max','-')}°C\n\nNot: Bu e-posta BYS360 tarafından otomatik üretilmiştir. Nihai idari değerlendirme ve karar yetkili yöneticilere aittir.\n\nÇanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı\nBYS360 Yönetici Özeti"""
    if task["period"]=="morning":
        return f"""Merhaba {name},\n\nGünaydın. Başarılı, sağlıklı ve verimli bir gün geçirmenizi dileriz.\n\nBugünkü hava durumu ({city}):\n- Durum: {w.get('today',{}).get('condition','Bilgi alınamadı')}\n- Sıcaklık: {w.get('today',{}).get('min','-')}°C / {w.get('today',{}).get('max','-')}°C\n- Yağış ihtimali: %{w.get('today',{}).get('rain','-')}\n\nKıyafet önerisi:\n{clothing_advice(w)}\n\nİyi çalışmalar dileriz.\n\nBYS360"""
    if task["period"]=="midday":
        return f"""Merhaba {name},\n\nMesainizin iyi ve verimli geçtiğini umarız.\n\nBYS360 kullanımı sırasında bir sorun, öneri, teşekkür veya geri bildirim iletmek isterseniz Geri Bildirim Merkezi üzerinden paylaşabilirsiniz.\n\nGeri Bildirim Merkezi: /feedback\n\nBaşarılı ve mutlu bir günün devamını dileriz.\n\nBYS360"""
    return f"""Merhaba {name},\n\nİyi akşamlar. Bugünkü çalışmalarınız için teşekkür ederiz.\n\nYarın için beklenen hava durumu ({city}):\n- Durum: {w.get('tomorrow',{}).get('condition','Bilgi alınamadı')}\n- Sıcaklık: {w.get('tomorrow',{}).get('min','-')}°C / {w.get('tomorrow',{}).get('max','-')}°C\n- Yağış ihtimali: %{w.get('tomorrow',{}).get('rain','-')}\n\nYarın için öneri:\n{clothing_advice(w, tomorrow=True)}\n\nİyi akşamlar dileriz.\n\nBYS360"""

def recipients_for_task(task: dict[str, Any]) -> list[Any]:
    cfg=current_config(); ids=cfg["manager_recipient_ids"] if task["audience"]=="managers" else cfg["staff_recipient_ids"]
    return [u for u in users_by_ids(ids) if user_email(u)]



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

def run_task(task_key: str, dry_run: bool=False, actor_user_id: int|None=None, only_user_id: int|None=None) -> dict[str, Any]:
    # BYS360_PHASE4B_WEEKEND_MAIL_GUARD_V1_START
    _bys360_phase4b_task_key = str(task_key or "").strip().lower()
    if _bys360_phase4b_task_key == "staff_midday" and _bys360_phase4b_is_weekend():
        return {
            "ok": True,
            "skipped": True,
            "reason": "weekend_guard",
            "task_key": "staff_midday",
            "sent_count": 0,
            "failed_count": 0,
            "message": "Hafta sonu olduğu için personel gün ortası maili gönderilmedi.",
        }
    # BYS360_PHASE4B_WEEKEND_MAIL_GUARD_V1_END
    ensure_defaults(actor_user_id); tasks={t["key"]:t for t in current_config()["tasks"]}; task=tasks.get(task_key)
    if not task: return {"ok":False,"task_key":task_key,"error":"Görev bulunamadı.","sent":0,"failed":0}
    if not task.get("enabled") and not dry_run: return {"ok":True,"task_key":task_key,"skipped":True,"reason":"Görev pasif.","sent":0,"failed":0}
    recipients=users_by_ids([only_user_id]) if only_user_id else recipients_for_task(task)
    result={"ok":True,"task_key":task_key,"task_title":task["title"],"dry_run":dry_run,"sent":0,"failed":0,"items":[]}
    subject=task.get("subject","BYS360 Bilgilendirme | {date}").format(date=datetime.now().strftime("%d.%m.%Y"))
    for user in recipients:
        email=user_email(user); body=build_body(task,user)
        if dry_run: ok,msg=True,"Kuru çalışma: mail gönderilmedi."
        elif send_email is None: ok,msg=False,"send_email servisi bulunamadı."
        else: ok,msg=send_email(email, subject, body)
        if create_mail_log is not None and db is not None:
            try:
                create_mail_log(mail_type=f"exec_center_{task_key}", recipient_email=email, subject=subject, body=body, user_id=getattr(user,"id",None), sent_by_id=actor_user_id, is_success=bool(ok), error_message=None if ok else msg); db.session.commit()
            except Exception:
                logger.exception("BYS360 V6C guarded exception | file=app/services/executive_mail_center_v2.py | line=209")
                try: db.session.rollback()
                except Exception:
                    __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/executive_mail_center_v2.py:221")
                    pass
        result["items"].append({"email":email,"name":user_display_name(user),"ok":ok,"message":msg})
        if ok: result["sent"]+=1
        else: result["failed"]+=1
    result["ok"]=result["failed"]==0
    return result

def run_due_tasks(actor_user_id: int|None=None, dry_run: bool=False) -> dict[str, Any]:
    now=datetime.now(); results=[]
    for task in current_config()["tasks"]:
        if task.get("enabled") and int(task.get("hour"))==now.hour and int(task.get("minute"))==now.minute:
            results.append(run_task(task["key"], dry_run=dry_run, actor_user_id=actor_user_id))
    return {"ok":True,"checked_at":now.isoformat(timespec="seconds"),"matched":len(results),"results":results}

def dashboard_context(search: str|None=None) -> dict[str, Any]:
    cfg=current_config(); people=selected_people()
    return {"config":cfg,"tasks":cfg["tasks"],"manager_recipients":people["managers"],"staff_recipients":people["staff"],"users":list_users(search=search, limit=500),"search":search or "","logs":get_recent_logs(80),"location":cfg["location"]}

