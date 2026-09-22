from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from flask import current_app
from sqlalchemy import inspect as sa_inspect

from app.extensions import db
from app.models import MailLog, RoleMenuDefault, SystemSetting, User
from app.services.mail_core import create_mail_log, send_email

logger = logging.getLogger(__name__)

DAILY_WEATHER_MAIL_TYPE = "daily_weather_personnel_info"
DAILY_WEATHER_GROUP_KEY = "daily_weather_mail"
DAILY_WEATHER_MENU_KEY = "daily_weather_mail"
DEFAULT_CITY = "Çanakkale"
DEFAULT_LATITUDE = "40.1553"
DEFAULT_LONGITUDE = "26.4142"
DEFAULT_RUN_HOUR = "8"
DEFAULT_RUN_MINUTE = "15"
LOCAL_TZ = ZoneInfo("Europe/Istanbul")

DAILY_WEATHER_SETTING_DEFINITIONS: dict[str, dict[str, Any]] = {
    "daily_weather_mail.enabled": {
        "label": "Günlük personel bilgilendirme maili aktif",
        "default": "0",
        "value_type": "bool",
        "description": "1 olduğunda zamanlanmış iş seçili personele günlük hava durumu bilgilendirme maili gönderir.",
    },
    "daily_weather_mail.run_hour": {
        "label": "Günlük bilgilendirme maili gönderim saati",
        "default": DEFAULT_RUN_HOUR,
        "value_type": "int",
        "description": "Windows Görev Zamanlayıcı veya cron için önerilen saat bilgisidir.",
    },
    "daily_weather_mail.run_minute": {
        "label": "Günlük bilgilendirme maili gönderim dakikası",
        "default": DEFAULT_RUN_MINUTE,
        "value_type": "int",
        "description": "Gönderim dakikasıdır.",
    },
    "daily_weather_mail.city": {
        "label": "Hava durumu şehri",
        "default": DEFAULT_CITY,
        "value_type": "string",
        "description": "Mailde kullanılacak şehir adı.",
    },
    "daily_weather_mail.latitude": {
        "label": "Hava durumu enlem",
        "default": DEFAULT_LATITUDE,
        "value_type": "string",
        "description": "Hava durumu servisinde kullanılacak enlem.",
    },
    "daily_weather_mail.longitude": {
        "label": "Hava durumu boylam",
        "default": DEFAULT_LONGITUDE,
        "value_type": "string",
        "description": "Hava durumu servisinde kullanılacak boylam.",
    },
    "daily_weather_mail.include_tomorrow": {
        "label": "Ertesi gün tahmini eklensin",
        "default": "1",
        "value_type": "bool",
        "description": "Mailde yarın beklenen hava durumu bilgisini gösterir.",
    },
    "daily_weather_mail.include_clothing": {
        "label": "Kıyafet önerisi eklensin",
        "default": "1",
        "value_type": "bool",
        "description": "Hava durumuna göre genel kıyafet önerisi üretir.",
    },
    "daily_weather_mail.include_motivation": {
        "label": "İyi dilek mesajı eklensin",
        "default": "1",
        "value_type": "bool",
        "description": "Mail sonuna başarılı ve mutlu gün dileği ekler.",
    },
    "daily_weather_mail.recipient_user_ids": {
        "label": "Günlük bilgilendirme maili alıcı personel listesi",
        "default": "[]",
        "value_type": "json",
        "description": "Ekrandan seçilen personel kullanıcı ID listesi.",
    },
    "daily_weather_mail.last_sent_date": {
        "label": "Son günlük bilgilendirme gönderim tarihi",
        "default": "",
        "value_type": "string",
        "description": "Aynı gün yanlışlıkla tekrar otomatik gönderimi engeller.",
    },
    "daily_weather_mail.last_result_json": {
        "label": "Son günlük bilgilendirme sonucu",
        "default": "{}",
        "value_type": "json",
        "description": "Son otomatik/personel bilgilendirme çalışmasının özet sonucudur.",
    },
}

_ALLOWED_ADMIN_ROLES = {
    "admin",
    "super_admin",
    "system_admin",
    "sistem_yoneticisi",
    "baskan",
    "baskan_yardimcisi",
    "grup_baskani",
    "mali_musavir",
    "koordinator",
    "birim_sorumlusu",
    "performans_yetkilisi",
}

_WEATHER_CODE_LABELS = {
    0: "Açık",
    1: "Az bulutlu",
    2: "Parçalı bulutlu",
    3: "Kapalı",
    45: "Sisli",
    48: "Kırağılı sis",
    51: "Hafif çisenti",
    53: "Çisenti",
    55: "Yoğun çisenti",
    61: "Hafif yağmur",
    63: "Yağmurlu",
    65: "Kuvvetli yağmur",
    71: "Hafif kar",
    73: "Karlı",
    75: "Yoğun kar",
    80: "Hafif sağanak",
    81: "Sağanak yağış",
    82: "Kuvvetli sağanak",
    95: "Gök gürültülü sağanak",
    96: "Gök gürültülü dolu ihtimali",
    99: "Kuvvetli gök gürültülü dolu ihtimali",
}


@dataclass(frozen=True)
class WeatherDay:
    label: str
    condition: str
    min_temp: float | None
    max_temp: float | None
    rain_probability: int | None
    wind_speed: float | None


def _setting_table_ready() -> bool:
    try:
        return bool(sa_inspect(db.engine).has_table("system_settings"))
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/daily_weather_mail.py | line=157")
        return False


def _coerce_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return bool(default)
    text = str(value).strip().lower()
    if text in {"1", "true", "on", "yes", "evet", "aktif", "açık", "acik"}:
        return True
    if text in {"0", "false", "off", "no", "hayir", "hayır", "pasif", "kapalı", "kapali"}:
        return False
    return bool(default)


def _coerce_int(value: Any, default: int, minimum: int | None = None, maximum: int | None = None) -> int:
    try:
        parsed = int(str(value).strip())
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/daily_weather_mail.py | line=175")
        parsed = int(default)
    if minimum is not None:
        parsed = max(parsed, minimum)
    if maximum is not None:
        parsed = min(parsed, maximum)
    return parsed


def _coerce_float_text(value: Any, default: str) -> str:
    try:
        return str(float(str(value).strip())).rstrip("0").rstrip(".")
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/daily_weather_mail.py | line=187")
        return str(default)


def _today_local_date() -> str:
    return datetime.now(LOCAL_TZ).date().isoformat()


def get_setting_value(key: str, default: Any = None) -> str:
    definition = DAILY_WEATHER_SETTING_DEFINITIONS.get(key) or {}
    fallback = definition.get("default", default if default is not None else "")
    if not _setting_table_ready():
        return str(fallback or "")
    try:
        row = SystemSetting.query.filter_by(setting_key=key).first()
        value = (row.value_text or "").strip() if row else ""
        return value if value != "" else str(fallback or "")
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/daily_weather_mail.py | line=204")
        return str(fallback or "")


def set_setting_value(key: str, value: Any, *, actor_user_id: int | None = None) -> None:
    if not _setting_table_ready():
        raise RuntimeError("system_settings tablosu bulunamadı. Önce veritabanı güncellemesini tamamlayın.")
    definition = DAILY_WEATHER_SETTING_DEFINITIONS.get(key) or {
        "label": key,
        "default": "",
        "value_type": "string",
        "description": "BYS360 günlük personel bilgilendirme ayarı.",
    }
    row = SystemSetting.query.filter_by(setting_key=key).first()
    if row is None:
        row = SystemSetting(
            setting_key=key,
            group_key=DAILY_WEATHER_GROUP_KEY,
            label=definition.get("label", key),
            value_text=str(value if value is not None else ""),
            value_type=definition.get("value_type", "string"),
            description=definition.get("description", ""),
            is_active=True,
            updated_by_user_id=actor_user_id,
        )
        db.session.add(row)
        return
    row.group_key = DAILY_WEATHER_GROUP_KEY
    row.label = definition.get("label", row.label or key)
    row.value_text = str(value if value is not None else "")
    row.value_type = definition.get("value_type", row.value_type or "string")
    row.description = definition.get("description", row.description or "")
    row.is_active = True
    row.updated_by_user_id = actor_user_id


def ensure_daily_weather_defaults(actor_user_id: int | None = None) -> None:
    if not _setting_table_ready():
        return
    for key, definition in DAILY_WEATHER_SETTING_DEFINITIONS.items():
        row = SystemSetting.query.filter_by(setting_key=key).first()
        if row is None:
            db.session.add(
                SystemSetting(
                    setting_key=key,
                    group_key=DAILY_WEATHER_GROUP_KEY,
                    label=definition["label"],
                    value_text=str(definition.get("default", "")),
                    value_type=definition.get("value_type", "string"),
                    description=definition.get("description", ""),
                    is_active=True,
                    updated_by_user_id=actor_user_id,
                )
            )
        else:
            row.group_key = DAILY_WEATHER_GROUP_KEY
            row.label = definition["label"]
            row.value_type = definition.get("value_type", row.value_type or "string")
            row.description = definition.get("description", row.description or "")
            row.is_active = True
    _ensure_role_menu_defaults(actor_user_id=actor_user_id)
    db.session.commit()


def _ensure_role_menu_defaults(actor_user_id: int | None = None) -> None:
    try:
        for role in sorted(_ALLOWED_ADMIN_ROLES):
            row = RoleMenuDefault.query.filter_by(role_name=role, menu_key=DAILY_WEATHER_MENU_KEY).first()
            if row is None:
                db.session.add(
                    RoleMenuDefault(
                        role_name=role,
                        menu_key=DAILY_WEATHER_MENU_KEY,
                        is_visible=True,
                        source_type="seed",
                        updated_by_user_id=actor_user_id,
                        note="Günlük personel bilgilendirme maili yönetimi",
                    )
                )
            else:
                row.is_visible = True
                row.source_type = row.source_type or "seed"
                row.updated_by_user_id = actor_user_id
                row.note = row.note or "Günlük personel bilgilendirme maili yönetimi"
    except Exception:
        current_app.logger.exception("Günlük hava durumu maili rol menü varsayılanları kurulamadı.")


def current_config() -> dict[str, Any]:
    """Pure read of the current daily-weather-mail configuration.

    Deliberately does NOT call `ensure_daily_weather_defaults()` -- that
    call writes `RoleMenuDefault` rows for this feature's own menu key,
    and (mandate: daily-weather-mail menu visibility side-effect defect)
    `get_role_default_menu_keys_handler`
    (app/services/settings/menu_profile_access.py) treats the mere
    EXISTENCE of any explicit `RoleMenuDefault` row for a role as that
    role having fully opted out of the static/policy default menu set --
    so a role with no prior override rows silently loses default
    visibility into every OTHER, unrelated menu key the moment this
    read-only function's caller triggers that write. Every value below
    already falls back to its coded-in default via `get_setting_value`
    when no row exists yet, so this function was never dependent on the
    write to behave correctly. The two callers that legitimately need
    the bootstrap-on-first-use behavior already trigger it themselves,
    independently of this function: `save_config()` (below) and the
    management UI route
    (app/communication/daily_weather_mail_routes.py's
    `daily_weather_mail_settings()`, which already calls
    `ensure_daily_weather_defaults()` explicitly, immediately before
    calling this function) -- so removing the call here is a pure
    side-effect removal with no behavior change for either of them.
    """
    return {
        "enabled": _coerce_bool(get_setting_value("daily_weather_mail.enabled"), False),
        "run_hour": _coerce_int(get_setting_value("daily_weather_mail.run_hour"), 8, 0, 23),
        "run_minute": _coerce_int(get_setting_value("daily_weather_mail.run_minute"), 15, 0, 59),
        "city": get_setting_value("daily_weather_mail.city", DEFAULT_CITY) or DEFAULT_CITY,
        "latitude": _coerce_float_text(get_setting_value("daily_weather_mail.latitude", DEFAULT_LATITUDE), DEFAULT_LATITUDE),
        "longitude": _coerce_float_text(get_setting_value("daily_weather_mail.longitude", DEFAULT_LONGITUDE), DEFAULT_LONGITUDE),
        "include_tomorrow": _coerce_bool(get_setting_value("daily_weather_mail.include_tomorrow"), True),
        "include_clothing": _coerce_bool(get_setting_value("daily_weather_mail.include_clothing"), True),
        "include_motivation": _coerce_bool(get_setting_value("daily_weather_mail.include_motivation"), True),
        "recipient_user_ids": get_recipient_user_ids(),
        "last_sent_date": get_setting_value("daily_weather_mail.last_sent_date", ""),
        "last_result": get_last_result(),
    }


def save_config(payload: dict[str, Any], *, actor_user_id: int | None = None) -> dict[str, Any]:
    ensure_daily_weather_defaults(actor_user_id=actor_user_id)
    set_setting_value("daily_weather_mail.enabled", "1" if _coerce_bool(payload.get("enabled")) else "0", actor_user_id=actor_user_id)
    set_setting_value("daily_weather_mail.run_hour", str(_coerce_int(payload.get("run_hour"), 8, 0, 23)), actor_user_id=actor_user_id)
    set_setting_value("daily_weather_mail.run_minute", str(_coerce_int(payload.get("run_minute"), 15, 0, 59)), actor_user_id=actor_user_id)
    set_setting_value("daily_weather_mail.city", (payload.get("city") or DEFAULT_CITY).strip() or DEFAULT_CITY, actor_user_id=actor_user_id)
    set_setting_value("daily_weather_mail.latitude", _coerce_float_text(payload.get("latitude"), DEFAULT_LATITUDE), actor_user_id=actor_user_id)
    set_setting_value("daily_weather_mail.longitude", _coerce_float_text(payload.get("longitude"), DEFAULT_LONGITUDE), actor_user_id=actor_user_id)
    set_setting_value("daily_weather_mail.include_tomorrow", "1" if _coerce_bool(payload.get("include_tomorrow"), False) else "0", actor_user_id=actor_user_id)
    set_setting_value("daily_weather_mail.include_clothing", "1" if _coerce_bool(payload.get("include_clothing"), False) else "0", actor_user_id=actor_user_id)
    set_setting_value("daily_weather_mail.include_motivation", "1" if _coerce_bool(payload.get("include_motivation"), False) else "0", actor_user_id=actor_user_id)
    recipient_ids = normalize_recipient_ids(payload.get("recipient_user_ids") or [])
    set_setting_value("daily_weather_mail.recipient_user_ids", json.dumps(recipient_ids, ensure_ascii=False), actor_user_id=actor_user_id)
    db.session.commit()
    return current_config()


def normalize_recipient_ids(values: Any) -> list[int]:
    if values is None:
        return []
    if isinstance(values, str):
        values = [item for item in values.replace(";", ",").split(",") if item.strip()]
    result: list[int] = []
    seen: set[int] = set()
    for item in values or []:
        try:
            user_id = int(str(item).strip())
        except Exception:
            logger.exception("BYS360 V6C guarded exception | file=app/services/daily_weather_mail.py | line=337")
            continue
        if user_id > 0 and user_id not in seen:
            seen.add(user_id)
            result.append(user_id)
    return result


def get_recipient_user_ids() -> list[int]:
    raw = get_setting_value("daily_weather_mail.recipient_user_ids", "[]") or "[]"
    try:
        parsed = json.loads(raw)
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/daily_weather_mail.py | line=349")
        parsed = []
    return normalize_recipient_ids(parsed)


def get_recipient_users() -> list[User]:
    ids = get_recipient_user_ids()
    if not ids:
        return []
    users = User.query.filter(User.id.in_(ids), User.is_active.is_(True)).order_by(User.ad.asc(), User.soyad.asc()).all()
    order = {user_id: idx for idx, user_id in enumerate(ids)}
    users.sort(key=lambda u: order.get(getattr(u, "id", 0), 10_000))
    return users


def list_active_users_for_selection() -> list[User]:
    return User.query.filter(User.is_active.is_(True)).order_by(User.birim.asc().nullslast(), User.ad.asc(), User.soyad.asc()).all()


def get_last_result() -> dict[str, Any]:
    raw = get_setting_value("daily_weather_mail.last_result_json", "{}") or "{}"
    try:
        parsed = json.loads(raw)
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/daily_weather_mail.py | line=372")
        parsed = {}
    return parsed if isinstance(parsed, dict) else {}


def _weather_url(config: dict[str, Any]) -> str:
    params = {
        "latitude": config.get("latitude") or DEFAULT_LATITUDE,
        "longitude": config.get("longitude") or DEFAULT_LONGITUDE,
        "current": "temperature_2m,apparent_temperature,precipitation,rain,weather_code,wind_speed_10m",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max",
        "timezone": "Europe/Istanbul",
        "forecast_days": "2",
    }
    return "https://api.open-meteo.com/v1/forecast?" + urllib.parse.urlencode(params)


def fetch_weather(config: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = config or current_config()
    url = _weather_url(cfg)
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "BYS360-DailyWeatherMail/1.0"})
        with urllib.request.urlopen(request, timeout=18) as response:  # noqa: S310 - Kurumsal hava durumu API çağrısıdır.
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise RuntimeError(f"Hava durumu bilgisi alınamadı: {exc}") from exc
    return _normalize_weather_payload(payload, city=str(cfg.get("city") or DEFAULT_CITY))


def _normalize_weather_payload(payload: dict[str, Any], *, city: str) -> dict[str, Any]:
    daily = payload.get("daily") or {}
    current = payload.get("current") or {}
    dates = daily.get("time") or []
    codes = daily.get("weather_code") or []
    maxs = daily.get("temperature_2m_max") or []
    mins = daily.get("temperature_2m_min") or []
    rain_prob = daily.get("precipitation_probability_max") or []
    winds = daily.get("wind_speed_10m_max") or []

    def day_at(index: int, label: str) -> WeatherDay:
        code = _list_get(codes, index)
        return WeatherDay(
            label=label,
            condition=_WEATHER_CODE_LABELS.get(int(code), "Belirsiz") if code is not None else "Belirsiz",
            min_temp=_to_float(_list_get(mins, index)),
            max_temp=_to_float(_list_get(maxs, index)),
            rain_probability=_to_int(_list_get(rain_prob, index)),
            wind_speed=_to_float(_list_get(winds, index)),
        )

    today = day_at(0, "Bugün")
    tomorrow = day_at(1, "Yarın") if len(dates) > 1 else None
    current_code = current.get("weather_code")
    return {
        "city": city,
        "fetched_at": datetime.now(LOCAL_TZ).strftime("%d.%m.%Y %H:%M"),
        "current": {
            "temperature": _to_float(current.get("temperature_2m")),
            "apparent_temperature": _to_float(current.get("apparent_temperature")),
            "condition": _WEATHER_CODE_LABELS.get(int(current_code), today.condition) if current_code is not None else today.condition,
            "wind_speed": _to_float(current.get("wind_speed_10m")),
            "rain": _to_float(current.get("rain")),
            "precipitation": _to_float(current.get("precipitation")),
        },
        "today": today,
        "tomorrow": tomorrow,
    }


def _list_get(values: list[Any], index: int) -> Any:
    try:
        return values[index]
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/daily_weather_mail.py | line=444")
        return None


def _to_float(value: Any) -> float | None:
    try:
        return round(float(value), 1)
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/daily_weather_mail.py | line=451")
        return None


def _to_int(value: Any) -> int | None:
    try:
        return int(round(float(value)))
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/daily_weather_mail.py | line=458")
        return None


def _fmt_temp(value: float | None) -> str:
    return "-" if value is None else f"{value:g}°C"


def _fmt_percent(value: int | None) -> str:
    return "-" if value is None else f"%{value}"


def _fmt_wind(value: float | None) -> str:
    return "-" if value is None else f"{value:g} km/sa"


def build_clothing_suggestion(weather: dict[str, Any]) -> str:
    today: WeatherDay = weather["today"]
    max_temp = today.max_temp if today.max_temp is not None else weather.get("current", {}).get("temperature")
    rain_probability = today.rain_probability or 0
    wind_speed = today.wind_speed or weather.get("current", {}).get("wind_speed") or 0
    condition = (today.condition or "").lower()

    pieces: list[str] = []
    if max_temp is not None:
        if max_temp <= 8:
            pieces.append("Soğuk hava bekleniyor; kalın ve katmanlı kıyafet tercih edilmesi uygun olur.")
        elif max_temp <= 15:
            pieces.append("Serin hava bekleniyor; ince mont veya hırka bulundurulması faydalı olur.")
        elif max_temp >= 28:
            pieces.append("Sıcak hava bekleniyor; hafif, rahat ve nefes alan kıyafetler tercih edilebilir.")
        else:
            pieces.append("Günlük çalışma düzeni için mevsime uygun, rahat kıyafetler tercih edilebilir.")
    else:
        pieces.append("Günlük çalışma düzeni için mevsime uygun, rahat kıyafetler tercih edilebilir.")

    if rain_probability >= 45 or "yağ" in condition or "sağanak" in condition:
        pieces.append("Yağış ihtimaline karşı şemsiye veya yağmurluk bulundurulması önerilir.")
    if wind_speed >= 30:
        pieces.append("Rüzgâr etkili olabilir; rüzgâra karşı koruyucu bir dış katman faydalı olur.")
    return " ".join(pieces)


def _recipient_name(user: User) -> str:
    return (getattr(user, "full_name", "") or f"{getattr(user, 'ad', '')} {getattr(user, 'soyad', '')}").strip() or "Değerli çalışma arkadaşımız"


def compose_mail_body(user: User | None, config: dict[str, Any], weather: dict[str, Any]) -> tuple[str, str]:
    now = datetime.now(LOCAL_TZ)
    today: WeatherDay = weather["today"]
    tomorrow: WeatherDay | None = weather.get("tomorrow")
    current = weather.get("current") or {}
    city = weather.get("city") or config.get("city") or DEFAULT_CITY
    subject = f"BYS360 Günlük Bilgilendirme | {now.strftime('%d.%m.%Y')}"
    name = _recipient_name(user) if user else "Değerli çalışma arkadaşımız"

    lines: list[str] = [
        f"Sayın {name},",
        "",
        f"Bugün {city} için hava durumu bilgisi aşağıdadır.",
        "",
        "Bugünkü hava durumu:",
        f"- Anlık durum: {current.get('condition') or today.condition}",
        f"- Anlık sıcaklık: {_fmt_temp(current.get('temperature'))}",
        f"- Hissedilen sıcaklık: {_fmt_temp(current.get('apparent_temperature'))}",
        f"- Gün içi sıcaklık aralığı: {_fmt_temp(today.min_temp)} / {_fmt_temp(today.max_temp)}",
        f"- Yağış ihtimali: {_fmt_percent(today.rain_probability)}",
        f"- Rüzgâr: {_fmt_wind(today.wind_speed)}",
    ]
    if config.get("include_tomorrow") and tomorrow:
        lines.extend([
            "",
            "Yarın beklenen hava durumu:",
            f"- Beklenen durum: {tomorrow.condition}",
            f"- Sıcaklık aralığı: {_fmt_temp(tomorrow.min_temp)} / {_fmt_temp(tomorrow.max_temp)}",
            f"- Yağış ihtimali: {_fmt_percent(tomorrow.rain_probability)}",
            f"- Rüzgâr: {_fmt_wind(tomorrow.wind_speed)}",
        ])
    if config.get("include_clothing"):
        lines.extend([
            "",
            "Kıyafet önerisi:",
            build_clothing_suggestion(weather),
        ])
    if config.get("include_motivation"):
        lines.extend([
            "",
            "Tüm çalışma arkadaşlarımıza başarılı, sağlıklı ve mutlu bir gün dileriz.",
        ])
    institution_name = current_app.config.get("MAIL_INSTITUTION_NAME", "Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı")
    lines.extend([
        "",
        "Bu e-posta BYS360 günlük personel bilgilendirme sistemi tarafından otomatik olarak gönderilmiştir.",
        "",
        str(institution_name),
        "BYS360",
    ])
    return subject, "\n".join(lines)


def get_recent_logs(limit: int = 20) -> list[MailLog]:
    return (
        MailLog.query.filter_by(mail_type=DAILY_WEATHER_MAIL_TYPE)
        .order_by(MailLog.sent_at.desc())
        .limit(max(1, min(int(limit or 20), 100)))
        .all()
    )


def preview_daily_weather_mail(user: User | None = None) -> dict[str, Any]:
    config = current_config()
    weather = fetch_weather(config)
    subject, body = compose_mail_body(user, config, weather)
    return {"subject": subject, "body": body, "weather": weather, "config": config}


def run_daily_weather_mail(*, actor_user_id: int | None = None, force: bool = False, dry_run: bool = False) -> dict[str, Any]:
    ensure_daily_weather_defaults(actor_user_id=actor_user_id)
    config = current_config()
    today = _today_local_date()

    if not force and not config.get("enabled"):
        result = {"ok": False, "skipped": True, "reason": "Günlük personel bilgilendirme maili pasif.", "sent": 0, "failed": 0}
        _store_last_result(result, actor_user_id=actor_user_id)
        return result
    if not force and config.get("last_sent_date") == today:
        result = {"ok": True, "skipped": True, "reason": "Bugün için otomatik gönderim zaten yapılmış.", "sent": 0, "failed": 0}
        _store_last_result(result, actor_user_id=actor_user_id)
        return result

    recipients = get_recipient_users()
    if not recipients:
        result = {"ok": False, "skipped": True, "reason": "Seçili aktif alıcı personel bulunamadı.", "sent": 0, "failed": 0}
        _store_last_result(result, actor_user_id=actor_user_id)
        return result

    weather = fetch_weather(config)
    sent = 0
    failed = 0
    rows: list[dict[str, Any]] = []

    for user in recipients:
        subject, body = compose_mail_body(user, config, weather)
        email = (getattr(user, "email", "") or "").strip()
        if dry_run:
            ok, message = True, "Kuru çalışma: mail gönderilmedi."
        else:
            ok, message = send_email(email, subject, body)
        if ok:
            sent += 1
        else:
            failed += 1
        create_mail_log(
            mail_type=DAILY_WEATHER_MAIL_TYPE,
            recipient_email=email,
            subject=subject,
            body=body,
            user_id=getattr(user, "id", None),
            sent_by_id=actor_user_id,
            is_success=ok,
            error_message="" if ok else message,
        )
        rows.append({"user_id": getattr(user, "id", None), "name": _recipient_name(user), "email": email, "ok": ok, "message": message})

    result = {
        "ok": failed == 0,
        "skipped": False,
        "dry_run": dry_run,
        "sent": sent,
        "failed": failed,
        "recipient_count": len(recipients),
        "city": config.get("city"),
        "ran_at": datetime.now(LOCAL_TZ).isoformat(timespec="seconds"),
        "rows": rows[:50],
    }
    if not dry_run and (sent > 0 or failed > 0):
        set_setting_value("daily_weather_mail.last_sent_date", today, actor_user_id=actor_user_id)
    _store_last_result(result, actor_user_id=actor_user_id)
    db.session.commit()
    return result


def _store_last_result(result: dict[str, Any], *, actor_user_id: int | None = None) -> None:
    safe_result = dict(result)
    rows = safe_result.get("rows")
    if isinstance(rows, list) and len(rows) > 20:
        safe_result["rows"] = rows[:20]
        safe_result["rows_truncated"] = True
    set_setting_value("daily_weather_mail.last_result_json", json.dumps(safe_result, ensure_ascii=False), actor_user_id=actor_user_id)
    db.session.commit()


__all__ = [name for name in globals() if not name.startswith("__")]
