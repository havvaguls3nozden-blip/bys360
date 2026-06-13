from __future__ import annotations



from app.core.datetime_utils import utc_now
from collections import Counter
from datetime import datetime, timedelta
from typing import Any

from app.models import Notification


PRIORITY_ORDER = {
    'critical': 5,
    'urgent': 4,
    'high': 3,
    'normal': 2,
    'low': 1,
}


def _safe_int(value: Any, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value or default)
    except (TypeError, ValueError):
        parsed = default
    return max(min(parsed, maximum), minimum)


def _normalize(value: Any) -> str:
    return str(value or '').strip().lower()


def _priority_rank(value: str) -> int:
    return PRIORITY_ORDER.get(_normalize(value), 0)


def _tone(priority_total: int, unread_total: int) -> str:
    if priority_total >= 8 or unread_total >= 25:
        return 'critical'
    if priority_total >= 3 or unread_total >= 10:
        return 'watch'
    return 'calm'


def _headline(priority_total: int, unread_total: int) -> str:
    if priority_total >= 8:
        return 'Bildirim kutusunda acil öncelik birikimi var'
    if priority_total >= 3:
        return 'Bildirim kutusunda dikkat isteyen başlıklar öne çıkıyor'
    if unread_total >= 10:
        return 'Bildirim kutusunda okunmamış yük büyüyor'
    return 'Bildirim akışı dengeli görünüyor'


def _build_reason(row: Any) -> str:
    pieces: list[str] = []
    priority = _normalize(getattr(row, 'priority', None))
    if priority in {'critical', 'urgent', 'high'}:
        pieces.append(f"{priority} öncelik")
    if not bool(getattr(row, 'is_read', False)):
        pieces.append('okunmamış')
    if getattr(row, 'created_at', None):
        age_hours = int(max((utc_now() - row.created_at).total_seconds(), 0) // 3600)
        if age_hours <= 24:
            pieces.append('son 24 saat')
    ntype = _normalize(getattr(row, 'notification_type', None))
    if ntype:
        pieces.append(ntype)
    return ', '.join(pieces) if pieces else 'genel görünüm'


def build_ai_notification_priority_snapshot(*, lookback_days: int = 7, priority: str = '', notification_type: str = '', unread_only: bool = False, limit: int = 40) -> dict[str, Any]:
    lookback_days = _safe_int(lookback_days, 7, 1, 90)
    limit = _safe_int(limit, 40, 5, 500)
    selected_priority = _normalize(priority)
    selected_notification_type = _normalize(notification_type)
    selected_unread_only = bool(unread_only)

    since = utc_now() - timedelta(days=lookback_days)
    base_query = Notification.query.filter(Notification.created_at >= since)
    all_rows = base_query.order_by(Notification.created_at.desc(), Notification.id.desc()).all()

    total_count = len(all_rows)
    unread_count = sum(1 for row in all_rows if not bool(getattr(row, 'is_read', False)))
    priority_total = sum(1 for row in all_rows if _priority_rank(getattr(row, 'priority', None)) >= 3)
    today_count = sum(1 for row in all_rows if getattr(row, 'created_at', None) and row.created_at.date() == utc_now().date())

    filtered = list(all_rows)
    if selected_priority:
        filtered = [row for row in filtered if _normalize(getattr(row, 'priority', None)) == selected_priority]
    if selected_notification_type:
        filtered = [row for row in filtered if _normalize(getattr(row, 'notification_type', None)) == selected_notification_type]
    if selected_unread_only:
        filtered = [row for row in filtered if not bool(getattr(row, 'is_read', False))]

    filtered.sort(
        key=lambda row: (
            _priority_rank(getattr(row, 'priority', None)),
            0 if not bool(getattr(row, 'is_read', False)) else 1,
            getattr(row, 'created_at', datetime.min),
            getattr(row, 'id', 0),
        ),
        reverse=True,
    )
    visible_rows = filtered[:limit]

    type_counter = Counter(_normalize(getattr(row, 'notification_type', None)) or 'genel' for row in all_rows)
    priority_counter = Counter(_normalize(getattr(row, 'priority', None)) or 'normal' for row in all_rows)

    priority_rows = []
    for row in visible_rows:
        priority_rows.append({
            'id': getattr(row, 'id', None),
            'created_at': getattr(row, 'created_at', None),
            'title': getattr(row, 'title', '') or '-',
            'body': getattr(row, 'body', '') or '',
            'priority': _normalize(getattr(row, 'priority', None)) or 'normal',
            'notification_type': _normalize(getattr(row, 'notification_type', None)) or 'genel',
            'source_type': _normalize(getattr(row, 'source_type', None)) or '',
            'source_id': getattr(row, 'source_id', None),
            'is_read': bool(getattr(row, 'is_read', False)),
            'link_url': getattr(row, 'link_url', None),
            'reason': _build_reason(row),
        })

    highlights = [
        {
            'title': 'Öncelikli bildirim havuzu',
            'body': f'Son {lookback_days} günde {priority_total} yüksek öncelikli kayıt bulundu. Okunmamış toplam {unread_count}.',
        },
        {
            'title': 'Bugün gelen trafik',
            'body': f'Bugün kutuya {today_count} bildirim düştü. Filtre sonrası ekranda {len(visible_rows)} kayıt gösteriliyor.',
        },
        {
            'title': 'Filtre görünümü',
            'body': f"Öncelik filtresi: {selected_priority or 'tümü'} · Tür filtresi: {selected_notification_type or 'tümü'} · Sadece okunmamış: {'evet' if selected_unread_only else 'hayır'}.",
        },
    ]

    action_rows = [
        {'label': 'Toplam', 'value': total_count},
        {'label': 'Okunmamış', 'value': unread_count},
        {'label': 'Öncelikli', 'value': priority_total},
        {'label': 'Bugün', 'value': today_count},
    ]

    return {
        'page_title': 'AI Bildirim Önceliklendirme',
        'page_kicker': 'İletişim',
        'page_subtitle': 'Bildirim kutusunu öncelik, okunmamış yük ve tür kırılımı ile birlikte özetler.',
        'selected_lookback_days': lookback_days,
        'selected_priority': selected_priority,
        'selected_notification_type': selected_notification_type,
        'selected_unread_only': selected_unread_only,
        'summary': {
            'total_count': total_count,
            'unread_count': unread_count,
            'priority_total': priority_total,
            'today_count': today_count,
            'filtered_count': len(filtered),
            'visible_count': len(visible_rows),
        },
        'tone': _tone(priority_total, unread_count),
        'headline': _headline(priority_total, unread_count),
        'highlights': highlights,
        'actions': action_rows,
        'priority_rows': priority_rows,
        'type_breakdown': sorted(type_counter.items(), key=lambda item: (-item[1], item[0])),
        'priority_breakdown': sorted(priority_counter.items(), key=lambda item: (-_priority_rank(item[0]), -item[1], item[0])),
        'priority_options': ['critical', 'urgent', 'high', 'normal', 'low'],
        'notification_type_options': sorted(type_counter.keys()),
    }


def export_ai_notification_priority_rows(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in snapshot.get('priority_rows') or []:
        created_at = row.get('created_at')
        rows.append({
            'id': row.get('id'),
            'created_at': created_at.isoformat() if created_at else '',
            'priority': row.get('priority'),
            'notification_type': row.get('notification_type'),
            'title': row.get('title'),
            'is_read': 'evet' if row.get('is_read') else 'hayır',
            'reason': row.get('reason'),
        })
    return rows