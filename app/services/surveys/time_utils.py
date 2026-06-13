"""Anket modülü tarih/süre yardımcıları."""
from __future__ import annotations

from app.core.datetime_utils import utc_now
import datetime as _dt
from typing import Any

from .contracts import SurveyAccessResult
import logging
logger = logging.getLogger(__name__)

try:  # Python 3.9+
    from zoneinfo import ZoneInfo as _ZoneInfo
except Exception:  # pragma: no cover
    logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/time_utils.py | line=14")
    _ZoneInfo = None


def survey_local_now() -> _dt.datetime:
    """Europe/Istanbul yerel zamanını naive datetime olarak döndürür."""
    try:
        if _ZoneInfo is not None:
            return _dt.datetime.now(_ZoneInfo("Europe/Istanbul")).replace(tzinfo=None)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360_CLAUDE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/surveys/time_utils.py")
    return utc_now() + _dt.timedelta(hours=3)


def format_survey_dt(value: Any) -> str:
    """Kullanıcıya gösterilecek kısa tarih/saat formatı."""
    try:
        return value.strftime("%d.%m.%Y %H:%M")
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/time_utils.py | line=33")
        return ""


def survey_access_state(survey: Any, *, now: _dt.datetime | None = None) -> SurveyAccessResult:
    """Yayın, başlangıç ve bitiş tarihine göre erişim sözleşmesi.

    Route dosyası bu fonksiyonu henüz kullanmaz. Faz 3'te kontrollü şekilde
    bağlanacak ilk aday fonksiyondur.
    """
    if not survey:
        return SurveyAccessResult(False, "Anket bulunamadı.")

    status = str(getattr(survey, "status", "") or "").strip()
    if status != "published":
        return SurveyAccessResult(False, "Anket bulunamadı veya yayımlanmamış.")

    current = now or survey_local_now()
    starts_at = getattr(survey, "start_at", None)
    ends_at = getattr(survey, "end_at", None)

    if starts_at and starts_at > current:
        return SurveyAccessResult(False, f"Bu anket {format_survey_dt(starts_at)} tarihinde başlayacak.", starts_at, ends_at)
    if ends_at and ends_at < current:
        return SurveyAccessResult(False, f"Bu anketin yanıt süresi {format_survey_dt(ends_at)} tarihinde doldu.", starts_at, ends_at)
    return SurveyAccessResult(True, "", starts_at, ends_at)
