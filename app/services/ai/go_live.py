from __future__ import annotations

from app.core.datetime_utils import utc_now
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from app.services.ai.client import get_provider_snapshot
from app.services.ai.executive_reporting import build_ai_executive_brief
from app.services.ai.governance import build_ai_governance_snapshot
from app.services.ai.governance_settings import get_governance_thresholds
from app.services.ai.quality import build_ai_quality_snapshot
from app.services.ai.schema_guard import get_ai_schema_status

CHECKLIST_FILE_NAME = 'ai_release_checklist.json'
DEFAULT_CHECKLIST: dict[str, Any] = {
    'release_title': 'BYS360 AI Canlıya Alma Kontrol Listesi',
    'release_subtitle': 'AI yönetişim, kalite ve kabul kontrollerinin son görünümü',
    'gates': [
        {'key': 'schema_ready', 'label': 'Şema hazır', 'owner': 'BT', 'severity': 'critical'},
        {'key': 'provider_ready', 'label': 'Gerçek sağlayıcı hazır', 'owner': 'BT', 'severity': 'critical'},
        {'key': 'quality_floor', 'label': 'Kalite eşiği', 'owner': 'BT / Ürün', 'severity': 'high'},
        {'key': 'governance_floor', 'label': 'Yönetişim eşiği', 'owner': 'BT / Yönetim', 'severity': 'high'},
        {'key': 'backlog_limit', 'label': 'Açık öneri/backlog limiti', 'owner': 'Admin', 'severity': 'medium'},
        {'key': 'negative_feedback_limit', 'label': 'Negatif geri bildirim limiti', 'owner': 'Admin', 'severity': 'medium'},
        {'key': 'critical_alerts', 'label': 'Kritik alarm kontrolü', 'owner': 'BT', 'severity': 'critical'},
        {'key': 'export_pack_ready', 'label': 'Yönetici özeti ve export paketi hazır', 'owner': 'Yönetim', 'severity': 'medium'},
    ],
    'acceptance_sections': [],
    'signoff_roles': ['Üst Yönetim', 'BT', 'Personel/İdari İşler', 'Sistem Yöneticisi'],
    'artifact_targets': ['AI Kontrol Merkezi', 'Kalite Panosu', 'Yönetişim Merkezi'],
}


def _checklist_path() -> Path:
    return Path(__file__).resolve().parents[3] / 'config' / CHECKLIST_FILE_NAME


def _merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dict(merged.get(key) or {}, value)
        else:
            merged[key] = value
    return merged


def get_ai_release_checklist() -> dict[str, Any]:
    path = _checklist_path()
    if not path.exists():
        return deepcopy(DEFAULT_CHECKLIST)
    try:
        payload = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return deepcopy(DEFAULT_CHECKLIST)
    if not isinstance(payload, dict):
        return deepcopy(DEFAULT_CHECKLIST)
    return _merge_dict(DEFAULT_CHECKLIST, payload)


def _gate_result(ok: bool, label: str, detail: str, owner: str, severity: str = 'medium') -> dict[str, Any]:
    return {
        'label': label,
        'ok': bool(ok),
        'status': 'pass' if ok else ('fail' if severity in {'critical', 'high'} else 'warn'),
        'detail': detail,
        'owner': owner,
        'severity': severity,
    }


def _status_counts(gates: list[dict[str, Any]]) -> dict[str, int]:
    result = {'pass': 0, 'warn': 0, 'fail': 0}
    for gate in gates:
        key = gate.get('status') or 'warn'
        result[key] = result.get(key, 0) + 1
    return result


def build_ai_go_live_snapshot(lookback_days: int = 14) -> dict[str, Any]:
    schema_status = get_ai_schema_status()
    provider_snapshot = get_provider_snapshot()
    thresholds = get_governance_thresholds()
    quality = build_ai_quality_snapshot(lookback_days=lookback_days)
    governance = build_ai_governance_snapshot(lookback_days=lookback_days)
    executive = build_ai_executive_brief(lookback_days=lookback_days)
    checklist = get_ai_release_checklist()

    quality_score = int((quality or {}).get('summary', {}).get('quality_score') or 0)
    governance_score = int((governance or {}).get('governance_summary', {}).get('governance_score') or 0)
    open_recommendations = int((governance or {}).get('governance_summary', {}).get('open_recommendations') or 0)
    negative_feedback = int((governance or {}).get('governance_summary', {}).get('negative_feedback') or 0)
    critical_alert_total = int((governance or {}).get('governance_summary', {}).get('critical_alert_total') or 0)

    gates: list[dict[str, Any]] = []
    for item in checklist.get('gates') or []:
        key = item.get('key')
        label = item.get('label') or key or 'Kontrol'
        owner = item.get('owner') or 'BT'
        severity = item.get('severity') or 'medium'
        if key == 'schema_ready':
            gates.append(_gate_result(bool(schema_status.get('ready')), label, schema_status.get('message') or 'Şema durumu kontrol edildi.', owner, severity))
        elif key == 'provider_ready':
            gates.append(
                _gate_result(
                    bool(provider_snapshot.get('ready_for_live_provider')) or not bool(provider_snapshot.get('require_real_provider_for_user_visible')),
                    label,
                    'Gerçek sağlayıcı hazır.' if provider_snapshot.get('ready_for_live_provider') else 'Sağlayıcı yerel taslak / eksik yapılandırma modunda.',
                    owner,
                    severity,
                )
            )
        elif key == 'quality_floor':
            floor = int(thresholds.get('module_quality_floor') or 0)
            gates.append(_gate_result(quality_score >= floor, label, f'Genel kalite skoru {quality_score}; eşik {floor}.', owner, severity))
        elif key == 'governance_floor':
            floor = int(thresholds.get('module_quality_floor') or 0)
            gates.append(_gate_result(governance_score >= floor, label, f'Yönetişim skoru {governance_score}; eşik {floor}.', owner, severity))
        elif key == 'backlog_limit':
            limit = int(thresholds.get('backlog_limit') or 0)
            gates.append(_gate_result(open_recommendations <= limit, label, f'Açık öneri/backlog {open_recommendations}; limit {limit}.', owner, severity))
        elif key == 'negative_feedback_limit':
            limit = int(thresholds.get('negative_feedback_limit') or 0)
            gates.append(_gate_result(negative_feedback <= limit, label, f'Negatif geri bildirim {negative_feedback}; limit {limit}.', owner, severity))
        elif key == 'critical_alerts':
            gates.append(_gate_result(critical_alert_total == 0, label, f'Kritik alarm sayısı {critical_alert_total}.', owner, severity))
        elif key == 'export_pack_ready':
            export_ready = bool((executive or {}).get('share_pack', {}).get('recommended_formats'))
            gates.append(_gate_result(export_ready, label, 'Yönetici özeti ve dışa aktarma paketleri oluşturulabiliyor.', owner, severity))
        else:
            gates.append(_gate_result(True, label, 'Kontrol maddesi yapılandırılmış fakat özel kural tanımlanmamış.', owner, severity))

    counts = _status_counts(gates)
    blockers = [gate for gate in gates if gate.get('status') == 'fail']
    warnings = [gate for gate in gates if gate.get('status') == 'warn']
    highlights = [
        {
            'title': 'Canlıya alma kararı',
            'body': 'Kritik blokaj yoksa pilot için açılabilir; blokaj varsa önce kırmızı maddeler kapatılmalıdır.',
        },
        {
            'title': 'Yönetici görünürlüğü',
            'body': 'Haftalık özet, yönetici özeti ve paylaşım merkezi birlikte karar desteği üretir.',
        },
        {
            'title': 'Kontrollü kullanım',
            'body': 'Otomatik gönderim yoktur; yönetici ve admin onayıyla kontrollü ilerlenir.',
        },
    ]

    if counts['fail'] == 0 and counts['warn'] <= 1:
        rollout_decision = 'Pilot canlı kullanım için uygun'
        rollout_tone = 'success'
    elif counts['fail'] == 0:
        rollout_decision = 'Kontrollü pilot önerilir'
        rollout_tone = 'warning'
    else:
        rollout_decision = 'Canlıya alma ertelenmeli'
        rollout_tone = 'danger'

    signoff_rows = [
        {'role': role, 'status': 'Bekliyor', 'note': 'Nihai kabul sonrası güncellenir.'}
        for role in (checklist.get('signoff_roles') or [])
    ]

    artifact_rows = [
        {'name': name, 'status': 'Hazır', 'note': 'İlgili AI yönetim ekranında görüntülenebilir.'}
        for name in (checklist.get('artifact_targets') or [])
    ]

    return {
        'page_title': 'AI Canlıya Alma Hazır Oluşu',
        'generated_at': utc_now(),
        'lookback_days': lookback_days,
        'schema_status': schema_status,
        'provider_snapshot': provider_snapshot,
        'thresholds': thresholds,
        'quality': quality,
        'governance': governance,
        'executive': executive,
        'checklist': checklist,
        'gates': gates,
        'counts': counts,
        'blockers': blockers,
        'warnings': warnings,
        'highlights': highlights,
        'rollout_decision': rollout_decision,
        'rollout_tone': rollout_tone,
        'signoff_rows': signoff_rows,
        'artifact_rows': artifact_rows,
    }


def render_ai_go_live_markdown(snapshot: dict[str, Any]) -> str:
    lines = [
        '# BYS360 AI Canlıya Alma Hazır Oluşu',
        '',
        f"Karar: {snapshot.get('rollout_decision')}",
        f"Pencere: Son {snapshot.get('lookback_days')} gün",
        '',
        '## Kontrol Özeti',
        f"- Geçen: {snapshot.get('counts', {}).get('pass', 0)}",
        f"- Uyarı: {snapshot.get('counts', {}).get('warn', 0)}",
        f"- Blokaj: {snapshot.get('counts', {}).get('fail', 0)}",
        '',
        '## Kontrol Maddeleri',
    ]
    for gate in snapshot.get('gates') or []:
        icon = '✅' if gate.get('status') == 'pass' else ('⚠️' if gate.get('status') == 'warn' else '⛔')
        lines.append(f"- {icon} {gate.get('label')}: {gate.get('detail')} (Sorumlu: {gate.get('owner')})")

    lines.extend(['', '## İmza / Teslim Rolleri'])
    for row in snapshot.get('signoff_rows') or []:
        lines.append(f"- {row.get('role')}: {row.get('status')}")

    lines.extend(['', '## Teslim Artefaktları'])
    for row in snapshot.get('artifact_rows') or []:
        lines.append(f"- {row.get('name')}: {row.get('status')}")
    return '\n'.join(lines)