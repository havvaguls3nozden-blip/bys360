from __future__ import annotations



import logging
# Ortak yardımcılar: AI panel üreticileri küçük dosyalara bölündü; public import yolu korunur.
THIRD_MANAGER_STANDARD_KEY = "ucuncu_yonetici_sicil"
THIRD_MANAGER_HEADER_ALIASES = [
    "ucuncu_yonetici_sicil",
    "üçüncü yönetici sicil",
    "ucuncu yonetici sicil",
    "3. amir sicil",
    "3 amir sicil",
    "new_y3",
]

from typing import Any, Iterable

import unicodedata

from flask import current_app, url_for
from sqlalchemy import func
from werkzeug.routing import BuildError

from app.extensions import db
from app.models import AIFeedbackLog, AIRecommendation, AIRequestLog, AISummaryCache
from app.services.ai.schema_guard import get_ai_schema_status

def _get(source: Any, key: str, default: Any = None) -> Any:
    if source is None:
        return default
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _tone_from_counts(*, critical: int = 0, warning: int = 0) -> str:
    if critical > 0:
        return "critical"
    if warning > 0:
        return "watch"
    return "calm"


def _badge_from_tone(tone: str) -> str:
    return {
        "critical": "Kritik odak",
        "watch": "Yakın takip",
        "calm": "Dengeli görünüm",
    }.get(tone, "AI özeti")


def _top_reason_pairs(reason_rows: Iterable[Any] | None, limit: int = 3) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for reason, count in list(reason_rows or [])[: max(int(limit or 0), 0)]:
        result.append({"label": str(reason), "value": _to_int(count)})
    return result


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    folded = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in folded if not unicodedata.combining(ch))


def _is_informational_hierarchy_reason(message: Any) -> bool:
    lowered = _normalize_text(message).lower()
    hukuk_single_manager_info = (
        (('hukuk müşavirliği' in lowered or 'hukuk musavirligi' in lowered) and ('tek amir kuralı uygulandı' in lowered or 'tek amir kurali uygulandi' in lowered))
    )
    return hukuk_single_manager_info or any(token in lowered for token in [
        'başkan performans değerlendirme zincirine dahil edilmez',
        'baskan performans degerlendirme zincirine dahil edilmez',
        'amir zinciri kurala göre onarıldı',
        'amir zinciri kurala gore onarildi',
        'özel tek amir kuralı uygulandı',
        'ozel tek amir kurali uygulandi',
        'özel başkanlık birimi tek amir kuralı uygulandı',
        'ozel baskanlik birimi tek amir kurali uygulandi',
        'tek amir kuralı uygulandı',
        'tek amir kurali uygulandi',
        'hukuk personeli tek amir kuralı uygulandı',
        'hukuk personeli tek amir kurali uygulandi',
        '3. amir yorumcu modunda',
        '3 amir yorumcu modunda',
    ])


def _extract_hierarchy_issue_messages(row: Any) -> list[str]:
    messages: list[str] = []
    for bucket in (_get(row, 'issues', []) or [], _get(row, 'warnings', []) or [], _get(row, 'info_notes', []) or []):
        for item in list(bucket or []):
            msg = _get(item, 'message', item)
            msg = str(msg).strip() if msg is not None else ''
            if msg:
                messages.append(msg)
    return messages


def _has_real_hierarchy_warning(row: Any) -> bool:
    return any(not _is_informational_hierarchy_reason(msg) for msg in _extract_hierarchy_issue_messages(row))


def _is_hierarchy_missing_exempt(row: Any) -> bool:
    if bool(_get(row, 'exempt_from_missing')):
        return True
    role = str(_get(_get(row, 'user') or {}, 'role') or _get(row, 'role') or '').strip().lower()
    return role == 'baskan' or bool(_get(row, 'is_single_manager_case'))


def _has_first_manager_binding(row: Any) -> bool:
    user = _get(row, 'user') or {}
    chain = _get(row, 'chain') or {}
    first_manager = (
        _get(user, 'yonetici_sicil')
        or _get(user, 'manager_1')
        or _get(row, 'manager_1')
        or _get(row, 'manager_1_id')
        or _get(row, 'manager_1_name')
        or _get(chain, 'manager_1')
        or _get(chain, 'manager_1_id')
        or _get(chain, 'manager_1_name')
    )
    return bool(str(first_manager).strip()) if first_manager is not None else False


def _has_level_3_binding(row: Any) -> bool:
    chain = _get(row, 'chain') or {}
    level_3 = (
        _get(row, 'has_level_3_resolved')
        or _get(row, 'has_level_3')
        or _get(row, 'manager_3_id')
        or _get(chain, 'manager_3_id')
    )
    return bool(str(level_3).strip()) if level_3 is not None else False


def _safe_url_for(endpoint: str, **values: Any) -> str | None:
    try:
        return url_for(endpoint, **values)
    except BuildError:
        try:
            current_app.logger.warning("AI dashboard link uretilemedi: %s", endpoint)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360_CLAUDE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/ai/dashboard_panel_common.py")
        return None
    except Exception as exc:
        try:
            current_app.logger.warning(
                "AI dashboard link fallback verdi | endpoint=%s | values=%s | exc=%s",
                endpoint,
                values,
                exc,
            )
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360_CLAUDE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/ai/dashboard_panel_common.py")
        return None


def _safe_len(value: Any) -> int:
    try:
        return len(value or [])
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return 0


def _safe_bool(value: Any) -> bool:
    return bool(value)


def _safe_title_case(value: Any, default: str = "Genel") -> str:
    text = str(value or "").strip()
    return text.title() if text else default


def _compose_standard_panel(
    *,
    tone: str,
    headline: str,
    summary: str,
    bullets: list[str] | None = None,
    actions: list[dict[str, Any]] | None = None,
    spotlight: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "badge": _badge_from_tone(tone),
        "tone": tone,
        "headline": headline,
        "summary": summary,
        "bullets": list(bullets or [])[:4],
        "actions": list(actions or [])[:4],
        "spotlight": list(spotlight or [])[:4],
    }


# Yıldız import eski public yolu bozmadan yardımcıları da taşır.
__all__ = [name for name in globals() if not name.startswith("__")]
