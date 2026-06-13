from __future__ import annotations




from app.core.datetime_utils import utc_now
import json
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any

from app.services.ai.governance import build_ai_governance_snapshot
from app.services.ai.governance_settings import get_governance_thresholds
from app.services.ai.quality import build_ai_quality_snapshot
from app.services.ai.weekly_summary import build_ai_weekly_summary
from app.services.ai.localization import ai_module_label


TEMPLATE_FILE_NAME = "ai_executive_report_template.json"
DEFAULT_TEMPLATE: dict[str, Any] = {
    "report_title": "BYS360 AI Yönetici Özeti",
    "report_subtitle": "Karar vericiler için kalite, risk ve aksiyon görünümü",
    "sections": [
        "executive_summary",
        "highlights",
        "risk_watch",
        "priority_actions",
        "module_focus",
        "prompt_focus",
    ],
    "share_pack": {
        "default_recipients": ["Üst Yönetim", "Personel/İdari İşler", "BT"],
        "recommended_formats": ["markdown", "json", "csv"],
    },
    "labels": {
        "high": "Yüksek",
        "medium": "Orta",
        "low": "Düşük",
        "critical": "Kritik",
        "warning": "Uyarı",
        "stable": "Dengeli",
    },
}


def _template_path() -> Path:
    return Path(__file__).resolve().parents[3] / 'config' / TEMPLATE_FILE_NAME


def _safe_int(value: Any, default: int, minimum: int = 1, maximum: int = 365) -> int:
    try:
        parsed = int(value or default)
    except (TypeError, ValueError):
        parsed = default
    return max(min(parsed, maximum), minimum)


def _merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dict(merged.get(key) or {}, value)
        else:
            merged[key] = value
    return merged


def get_ai_executive_template() -> dict[str, Any]:
    path = _template_path()
    if not path.exists():
        return deepcopy(DEFAULT_TEMPLATE)
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return deepcopy(DEFAULT_TEMPLATE)
    if not isinstance(payload, dict):
        return deepcopy(DEFAULT_TEMPLATE)
    return _merge_dict(DEFAULT_TEMPLATE, payload)


def _module_card(row: dict[str, Any]) -> dict[str, Any]:
    quality_score = int(row.get('quality_score') or 0)
    risk_level = 'low'
    if quality_score < 50 or int(row.get('negative_feedback') or 0) >= 3:
        risk_level = 'high'
    elif quality_score < 70 or int(row.get('backlog_total') or 0) >= 5:
        risk_level = 'medium'
    return {
        'module_type': row.get('module_type') or 'genel',
        'quality_score': quality_score,
        'module_label': ai_module_label(row.get('module_type') or 'genel'),
        'success_rate': int(row.get('success_rate') or 0),
        'backlog_total': int(row.get('backlog_total') or 0),
        'negative_feedback': int(row.get('negative_feedback') or 0),
        'request_total': int(row.get('request_total') or 0),
        'risk_level': risk_level,
    }


def _prompt_card(row: dict[str, Any]) -> dict[str, Any]:
    quality_score = int(row.get('quality_score') or 0)
    stability = 'stable'
    if quality_score < 50 or int(row.get('negative_feedback') or 0) >= 3:
        stability = 'critical'
    elif quality_score < 70:
        stability = 'warning'
    return {
        'prompt_version': row.get('prompt_version') or 'tanimsiz',
        'quality_score': quality_score,
        'success_rate': int(row.get('success_rate') or 0),
        'open_recommendations': int(row.get('open_recommendations') or 0),
        'negative_feedback': int(row.get('negative_feedback') or 0),
        'request_total': int(row.get('request_total') or 0),
        'stability': stability,
    }


def _priority_message(governance_score: int, critical_alert_total: int) -> str:
    if critical_alert_total > 0 or governance_score < 45:
        return 'AI tarafında acil yönetici takibi gerektiren risk alanları var.'
    if governance_score < 70:
        return 'Karar destek genel görünümü izlenebilir düzeyde; birkaç modül ve istem için iyileştirme gerekli.'
    return 'Karar destek genel görünümü dengeli; düzenli takip ve haftalık özet akışı yeterli görünüyor.'


def build_ai_executive_brief(*, lookback_days: int | None = None) -> dict[str, Any]:
    thresholds = get_governance_thresholds()
    lookback = _safe_int(lookback_days, int(thresholds.get('default_lookback_days') or 30), 1, 180)
    template = get_ai_executive_template()

    quality_snapshot = build_ai_quality_snapshot(lookback_days=lookback)
    governance_snapshot = build_ai_governance_snapshot(
        lookback_days=lookback,
        module_quality_floor=int(thresholds.get('module_quality_floor') or 65),
        prompt_quality_floor=int(thresholds.get('prompt_quality_floor') or 60),
        backlog_limit=int(thresholds.get('backlog_limit') or 8),
        negative_feedback_limit=int(thresholds.get('negative_feedback_limit') or 3),
    )
    weekly_summary = build_ai_weekly_summary(lookback_days=min(lookback, 30))

    summary = dict(governance_snapshot.get('summary') or {})
    module_rows = [ _module_card(row) for row in (quality_snapshot.get('module_rows') or [])[:6] ]
    prompt_rows = [ _prompt_card(row) for row in (quality_snapshot.get('prompt_rows') or [])[:6] ]
    alerts = list(governance_snapshot.get('all_alerts') or [])[:6]
    actions = list(governance_snapshot.get('actions') or [])[:6]
    highlights = list(weekly_summary.get('highlights') or [])[:4]

    executive_summary = {
        'title': template.get('report_title') or DEFAULT_TEMPLATE['report_title'],
        'subtitle': template.get('report_subtitle') or DEFAULT_TEMPLATE['report_subtitle'],
        'lookback_days': lookback,
        'generated_at': utc_now(),
        'governance_score': int(summary.get('governance_score') or 0),
        'quality_score': int(summary.get('quality_score') or 0),
        'request_total': int(summary.get('request_total') or 0),
        'open_recommendations': int(summary.get('open_recommendations') or 0),
        'critical_alert_total': int(summary.get('critical_alert_total') or 0),
        'warning_alert_total': int(summary.get('warning_alert_total') or 0),
        'negative_feedback': int(summary.get('negative_feedback') or 0),
        'priority_message': _priority_message(int(summary.get('governance_score') or 0), int(summary.get('critical_alert_total') or 0)),
    }

    narrative_lines = [
        f"Son {lookback} günde AI yönetişim skoru {executive_summary['governance_score']} ve kalite skoru {executive_summary['quality_score']} olarak ölçüldü.",
        f"Toplam {executive_summary['request_total']} Karar destek çağrısı üretildi; açık öneri sayısı {executive_summary['open_recommendations']}, negatif geri bildirim sayısı {executive_summary['negative_feedback']}.",
        f"Kritik alarm sayısı {executive_summary['critical_alert_total']}, uyarı düzeyindeki alarm sayısı {executive_summary['warning_alert_total']}.",
        executive_summary['priority_message'],
    ]

    share_pack = {
        'default_recipients': list((template.get('share_pack') or {}).get('default_recipients') or []),
        'recommended_formats': list((template.get('share_pack') or {}).get('recommended_formats') or []),
        'suggested_subject': f"BYS360 AI Yönetici Özeti · Son {lookback} Gün",
        'suggested_message': (
            f"BYS360 AI görünümü için son {lookback} günü kapsayan yönetici özeti hazırlandı. "
            f"Yönetişim skoru {executive_summary['governance_score']}, kalite skoru {executive_summary['quality_score']}. "
            f"Öne çıkan risk ve aksiyonlar rapor paketine işlendi."
        ),
    }

    return {
        'page_title': 'AI Yönetici Özeti',
        'page_kicker': 'Yönetici raporu',
        'page_subtitle': 'Kurumsal rapor düzeninde yönetici özeti ve paylaşım paketi',
        'template': template,
        'thresholds': thresholds,
        'summary': summary,
        'executive_summary': executive_summary,
        'narrative_lines': narrative_lines,
        'highlights': highlights,
        'alerts': alerts,
        'actions': actions,
        'module_rows': module_rows,
        'prompt_rows': prompt_rows,
        'weekly_summary': weekly_summary,
        'share_pack': share_pack,
        'lookback_days': lookback,
        'generated_at': executive_summary['generated_at'],
    }


def render_ai_executive_markdown(snapshot: dict[str, Any]) -> str:
    summary = snapshot.get('executive_summary') or {}
    lines: list[str] = []
    lines.append(f"# {summary.get('title') or 'BYS360 AI Yönetici Özeti'}")
    lines.append("")
    lines.append(f"_{summary.get('subtitle') or ''}_")
    lines.append("")
    lines.append(f"- Kapsam: Son {snapshot.get('lookback_days') or 0} gün")
    generated_at = snapshot.get('generated_at')
    if generated_at:
        lines.append(f"- Oluşturulma: {generated_at.strftime('%d.%m.%Y %H:%M')}")
    lines.append(f"- Yönetişim skoru: {summary.get('governance_score') or 0}")
    lines.append(f"- Kalite skoru: {summary.get('quality_score') or 0}")
    lines.append("")
    lines.append("## Yönetici Özeti")
    lines.append("")
    for item in snapshot.get('narrative_lines') or []:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Öne Çıkan Başlıklar")
    lines.append("")
    for item in snapshot.get('highlights') or []:
        lines.append(f"- **{item.get('title') or 'Başlık'}:** {item.get('body') or ''}")
    lines.append("")
    lines.append("## Öncelikli Riskler")
    lines.append("")
    for item in snapshot.get('alerts') or []:
        lines.append(f"- **{item.get('title') or 'Risk'}** ({item.get('severity') or 'bilgi'}): {item.get('body') or ''}")
    lines.append("")
    lines.append("## Önerilen Aksiyonlar")
    lines.append("")
    for item in snapshot.get('actions') or []:
        lines.append(f"- **{item.get('title') or 'Aksiyon'}:** {item.get('body') or ''}")
    lines.append("")
    lines.append("## Modül Odağı")
    lines.append("")
    for row in snapshot.get('module_rows') or []:
        lines.append(
            f"- **{row.get('module_type')}** · kalite {row.get('quality_score')} · başarı %{row.get('success_rate')} · açık iş yükü {row.get('backlog_total')} · negatif {row.get('negative_feedback')}"
        )
    lines.append("")
    lines.append("## İstem Odağı")
    lines.append("")
    for row in snapshot.get('prompt_rows') or []:
        lines.append(
            f"- **{row.get('prompt_version')}** · kalite {row.get('quality_score')} · başarı %{row.get('success_rate')} · açık öneri {row.get('open_recommendations')} · negatif {row.get('negative_feedback')}"
        )
    lines.append("")
    share_pack = snapshot.get('share_pack') or {}
    lines.append("## Paylaşım Notu")
    lines.append("")
    lines.append(f"- Önerilen konu: {share_pack.get('suggested_subject') or ''}")
    lines.append(f"- Önerilen alıcı grubu: {', '.join(share_pack.get('default_recipients') or [])}")
    return "\n".join(lines).strip() + "\n"