from __future__ import annotations



from app.core.datetime_utils import utc_now
import json
import time
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

from flask import current_app


_CACHE: dict[str, object] = {
    "key": None,
    "value": None,
    "expires_at": 0.0,
}

_TURKISH_MONTHS = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]

_TURKISH_WEEKDAYS = [
    "Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar",
]

_WEATHER_CODE_MAP = {
    0: ("Açık", "fa-sun"),
    1: ("Çoğunlukla açık", "fa-sun"),
    2: ("Parçalı bulutlu", "fa-cloud-sun"),
    3: ("Bulutlu", "fa-cloud"),
    45: ("Sisli", "fa-smog"),
    48: ("Yoğun sis", "fa-smog"),
    51: ("Hafif çisenti", "fa-cloud-rain"),
    53: ("Çisenti", "fa-cloud-rain"),
    55: ("Yoğun çisenti", "fa-cloud-rain"),
    56: ("Donan çisenti", "fa-cloud-rain"),
    57: ("Kuvvetli donan çisenti", "fa-cloud-rain"),
    61: ("Hafif yağmurlu", "fa-cloud-rain"),
    63: ("Yağmurlu", "fa-cloud-rain"),
    65: ("Kuvvetli yağmurlu", "fa-cloud-showers-heavy"),
    66: ("Donan yağmur", "fa-cloud-meatball"),
    67: ("Kuvvetli donan yağmur", "fa-cloud-meatball"),
    71: ("Hafif karlı", "fa-snowflake"),
    73: ("Karlı", "fa-snowflake"),
    75: ("Yoğun karlı", "fa-snowflake"),
    77: ("Kar taneli", "fa-snowflake"),
    80: ("Sağanak yağış", "fa-cloud-showers-heavy"),
    81: ("Kuvvetli sağanak", "fa-cloud-showers-heavy"),
    82: ("Şiddetli sağanak", "fa-cloud-showers-heavy"),
    85: ("Kar sağanağı", "fa-snowflake"),
    86: ("Yoğun kar sağanağı", "fa-snowflake"),
    95: ("Gök gürültülü fırtına", "fa-bolt"),
    96: ("Dolu ihtimalli fırtına", "fa-cloud-bolt"),
    99: ("Şiddetli dolulu fırtına", "fa-cloud-bolt"),
}


def _safe_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _safe_int(value, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _now_in_timezone(timezone_name: str) -> datetime:
    try:
        return datetime.now(ZoneInfo(timezone_name or "Europe/Istanbul"))
    except Exception:
        return utc_now()


def _format_turkish_date(value: datetime) -> str:
    month_name = _TURKISH_MONTHS[max(0, min(value.month - 1, 11))]
    weekday_name = _TURKISH_WEEKDAYS[value.weekday()]
    return f"{value.day} {month_name} {value.year} {weekday_name}"


def _weather_label_and_icon(code: int) -> tuple[str, str]:
    return _WEATHER_CODE_MAP.get(code, ("Hava bilgisi güncelleniyor", "fa-cloud"))


def _build_tip(code: int, *, temperature_c: float, wind_kmh: float, precipitation_probability: int) -> tuple[str, str, str]:
    rainy_codes = {51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82}
    snowy_codes = {71, 73, 75, 77, 85, 86}
    storm_codes = {95, 96, 99}
    foggy_codes = {45, 48}

    if code in storm_codes:
        return (
            "fa-cloud-bolt",
            "Tedbir önerisi",
            "Açık alan planlarınızı gözden geçirin; ani yağış ve kuvvetli rüzgâra karşı hazırlıklı olun.",
        )
    if code in snowy_codes:
        return (
            "fa-snowflake",
            "Dikkat önerisi",
            "Kaygan zemin riskine karşı ulaşım ve saha planlamasında tedbirli olun.",
        )
    if code in rainy_codes or precipitation_probability >= 45:
        return (
            "fa-umbrella",
            "Günlük öneri",
            "Şemsiyenizi unutmayın; dış saha hareketlerinde su geçirmez ekipman tercih edin.",
        )
    if code in foggy_codes:
        return (
            "fa-eye-low-vision",
            "Görüş önerisi",
            "Sis nedeniyle görüş azalabilir; saha ve ulaşım planlarını daha kontrollü yürütün.",
        )
    if wind_kmh >= 30:
        return (
            "fa-wind",
            "Rüzgâr önerisi",
            "Rüzgâr etkili görünüyor; açık alan ve afiş/stand benzeri kurulumlarda dikkatli olun.",
        )
    if temperature_c >= 30:
        return (
            "fa-bottle-water",
            "Sıcak hava önerisi",
            "Su tüketimini artırın ve uzun süreli açık alan planlarında gölgelik molaları ihmal etmeyin.",
        )
    if temperature_c <= 5:
        return (
            "fa-mitten",
            "Soğuk hava önerisi",
            "Kalın giyinmeniz ve açık alan görevlerinde soğuğa karşı hazırlıklı olmanız önerilir.",
        )
    return (
        "fa-seedling",
        "Günlük öneri",
        "Hava koşulları dengeli görünüyor; açık alan planları için uygun bir gün olabilir.",
    )


def _fetch_open_meteo(*, latitude: float, longitude: float, timezone_name: str) -> dict:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "timezone": timezone_name,
        "current": "temperature_2m,weather_code,wind_speed_10m,is_day",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weather_code",
        "forecast_days": 1,
    }
    endpoint = "https://api.open-meteo.com/v1/forecast?" + urlencode(params)
    request = Request(endpoint, headers={"User-Agent": "BYS360-Portal/1.0"})
    with urlopen(request, timeout=4) as response:
        return json.loads(response.read().decode("utf-8"))


def build_portal_weather_widget() -> dict:
    config = current_app.config
    enabled = bool(config.get("PORTAL_WEATHER_ENABLED", True))
    timezone_name = str(config.get("PORTAL_WEATHER_TIMEZONE", "Europe/Istanbul") or "Europe/Istanbul")
    now_value = _now_in_timezone(timezone_name)

    base_payload = {
        "enabled": enabled,
        "available": False,
        "location_label": str(config.get("PORTAL_WEATHER_LOCATION_LABEL", "Tarihi Alan") or "Tarihi Alan"),
        "date_label": _format_turkish_date(now_value),
        "time_label": now_value.strftime("%H:%M"),
        "condition_label": "Hava durumu bilgisi alınamadı",
        "icon": "fa-cloud",
        "temperature_c": None,
        "temperature_display": "--°C",
        "min_max_display": "-- / --",
        "wind_display": "-- km/sa",
        "tip_icon": "fa-circle-info",
        "tip_title": "Bilgi",
        "tip_text": "Hava durumu servisi şu anda yanıt vermiyor. Lütfen daha sonra tekrar kontrol edin.",
        "updated_label": now_value.strftime("%H:%M"),
    }
    if not enabled:
        return base_payload

    latitude = _safe_float(config.get("PORTAL_WEATHER_LAT", 40.1846), 40.1846)
    longitude = _safe_float(config.get("PORTAL_WEATHER_LON", 26.3577), 26.3577)
    cache_minutes = max(_safe_int(config.get("PORTAL_WEATHER_CACHE_MINUTES", 45), 45), 5)
    cache_key = (round(latitude, 4), round(longitude, 4), timezone_name)

    current_ts = time.time()
    if _CACHE.get("key") == cache_key and current_ts < float(_CACHE.get("expires_at", 0) or 0):
        cached_value = _CACHE.get("value")
        if isinstance(cached_value, dict):
            return cached_value

    try:
        payload = _fetch_open_meteo(latitude=latitude, longitude=longitude, timezone_name=timezone_name)
        current_data = payload.get("current") or {}
        daily_data = payload.get("daily") or {}

        weather_code = _safe_int(current_data.get("weather_code"), 0)
        temperature_c = round(_safe_float(current_data.get("temperature_2m"), 0.0))
        wind_kmh = round(_safe_float(current_data.get("wind_speed_10m"), 0.0))
        temp_max = round(_safe_float((daily_data.get("temperature_2m_max") or [None])[0], temperature_c))
        temp_min = round(_safe_float((daily_data.get("temperature_2m_min") or [None])[0], temperature_c))
        precipitation_probability = _safe_int((daily_data.get("precipitation_probability_max") or [0])[0], 0)

        condition_label, icon = _weather_label_and_icon(weather_code)
        tip_icon, tip_title, tip_text = _build_tip(
            weather_code,
            temperature_c=float(temperature_c),
            wind_kmh=float(wind_kmh),
            precipitation_probability=precipitation_probability,
        )

        result = {
            **base_payload,
            "available": True,
            "condition_label": condition_label,
            "icon": icon,
            "temperature_c": temperature_c,
            "temperature_display": f"{temperature_c}°C",
            "min_max_display": f"{temp_min}° / {temp_max}°",
            "wind_display": f"{wind_kmh} km/sa",
            "tip_icon": tip_icon,
            "tip_title": tip_title,
            "tip_text": tip_text,
            "updated_label": now_value.strftime("%H:%M"),
        }
        _CACHE.update({
            "key": cache_key,
            "value": result,
            "expires_at": current_ts + (cache_minutes * 60),
        })
        return result
    except Exception as exc:  # pragma: no cover
        current_app.logger.warning("Portal hava durumu alınamadı: %s", exc)
        return base_payload