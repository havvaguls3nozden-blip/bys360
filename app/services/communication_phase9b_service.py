from __future__ import annotations



from app.core.datetime_utils import utc_now
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from flask import current_app

from app.extensions import db
import app.models as models
from app.models.communication_phase5_models import CommunicationAutomationLog
from app.services.communication_phase5_service import log_action, safe_str
from app.services.config_hardening_service import build_safe_env_patch
from app.services.go_live_readiness_service import build_go_live_readiness_context
from app.services.security_hardening_service import run_security_and_access_audit
import logging
logger = logging.getLogger(__name__)

try:
    from sqlalchemy import func
except Exception:  # pragma: no cover
    logger.exception("BYS360 V6C guarded exception | file=app/services/communication_phase9b_service.py | line=23")
    func = None


User = getattr(models, 'User', None)
MenuPermission = getattr(models, 'MenuPermission', None) or getattr(models, 'UserMenuPermission', None)
AuditLog = (
    getattr(models, 'AuditLog', None)
    or getattr(models, 'ModuleAuditLog', None)
    or getattr(models, 'SettingsChangeLog', None)
)
ImportLog = getattr(models, 'ImportLog', None) or getattr(models, 'PerformanceImportBatch', None)


class CommunicationPhase9BError(RuntimeError):
    pass


def _now() -> datetime:
    return utc_now()


def _project_root() -> Path:
    try:
        return Path(current_app.root_path).parent
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/communication_phase9b_service.py | line=48")
        return Path('.')


def _gate(key: str, label: str, status: str, detail: str, owner: str, action: str = '') -> dict[str, Any]:
    return {
        'key': key,
        'label': label,
        'status': status,
        'detail': detail,
        'owner': owner,
        'action': action,
    }


def _counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts = {'pass': 0, 'warn': 0, 'fail': 0}
    for row in rows:
        state = safe_str(row.get('status')).lower()
        if state in counts:
            counts[state] += 1
    return counts


def _tone_from_counts(counts: dict[str, int]) -> tuple[str, str]:
    if counts.get('fail', 0) > 0:
        return 'danger', 'Veri ve güvenlik geçişi bloke'
    if counts.get('warn', 0) > 0:
        return 'warning', 'Kontrollü veri ve güvenlik geçişi'
    return 'success', 'Veri ve güvenlik geçişi hazır'


def _recent_phase9b_logs(limit: int = 40) -> list[CommunicationAutomationLog]:
    return (
        CommunicationAutomationLog.query
        .filter(CommunicationAutomationLog.action_type.in_(['phase9b_gate', 'phase9b_decision']))
        .order_by(CommunicationAutomationLog.executed_at.desc())
        .limit(limit)
        .all()
    )


def _migration_summary() -> dict[str, Any]:
    project_root = _project_root()
    versions_dir = project_root / 'migrations' / 'versions'
    sql_dir = project_root / 'migrations' / 'sql'
    version_files = sorted(versions_dir.glob('*.py')) if versions_dir.exists() else []
    sql_files = sorted(sql_dir.glob('*.sql')) if sql_dir.exists() else []
    latest = None
    if version_files:
        latest_path = max(version_files, key=lambda p: p.stat().st_mtime)
        latest = {
            'name': latest_path.name,
            'modified_at': datetime.fromtimestamp(latest_path.stat().st_mtime),
        }
    return {
        'versions_dir': str(versions_dir),
        'sql_dir': str(sql_dir),
        'version_count': len(version_files),
        'sql_count': len(sql_files),
        'latest_version': latest,
        'exists': versions_dir.exists(),
    }


def _data_quality_summary() -> dict[str, Any]:
    summary = {
        'user_total': 0,
        'missing_sicil': 0,
        'duplicate_sicil': 0,
        'inactive_total': 0,
        'custom_permission_total': 0,
        'audit_log_total': 0,
        'import_log_total': 0,
    }
    if User is None:
        return summary

    try:
        query = User.query
        summary['user_total'] = query.count()
        if hasattr(User, 'sicil_no'):
            summary['missing_sicil'] = query.filter((User.sicil_no.is_(None)) | (User.sicil_no == '')).count()
            if func is not None:
                dup_rows = (
                    db.session.query(User.sicil_no, func.count(User.id).label('total'))
                    .filter(User.sicil_no.isnot(None))
                    .filter(User.sicil_no != '')
                    .group_by(User.sicil_no)
                    .having(func.count(User.id) > 1)
                    .all()
                )
                summary['duplicate_sicil'] = len(dup_rows)
        if hasattr(User, 'is_active'):
            summary['inactive_total'] = query.filter_by(is_active=False).count()
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360_CLAUDE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/communication_phase9b_service.py")
    try:
        if MenuPermission is not None:
            summary['custom_permission_total'] = MenuPermission.query.count()
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360_CLAUDE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/communication_phase9b_service.py")
    try:
        if AuditLog is not None:
            summary['audit_log_total'] = AuditLog.query.count()
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360_CLAUDE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/communication_phase9b_service.py")
    try:
        if ImportLog is not None:
            summary['import_log_total'] = ImportLog.query.count()
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360_CLAUDE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/communication_phase9b_service.py")
    return summary


def _env_snapshot() -> dict[str, Any]:
    project_root = _project_root()
    env_path = project_root / '.env'
    findings, suggestions = build_safe_env_patch(env_path, apply_safe_env=False)
    masked: dict[str, str] = {}
    for key, value in (suggestions or {}).items():
        if key == 'SECRET_KEY':
            masked[key] = 'Yeni güçlü secret üretin'
        else:
            masked[key] = value
    return {
        'env_path': str(env_path),
        'finding_count': len(findings),
        'findings': [
            {
                'code': item.code,
                'severity': item.severity,
                'title': item.title,
                'detail': item.detail,
            }
            for item in findings
        ],
        'suggestions': masked,
    }


def phase9b_transition_center_snapshot() -> dict[str, Any]:
    go_live = build_go_live_readiness_context()
    security_report = run_security_and_access_audit()
    migration = _migration_summary()
    data_quality = _data_quality_summary()
    env_snapshot = _env_snapshot()
    recent_logs = _recent_phase9b_logs(30)

    backup_files = len((go_live.get('backup_summary') or {}).get('recent_files') or [])
    log_files = len((go_live.get('log_summary') or {}).get('recent_files') or [])

    gates = [
        _gate(
            'sicil_identity',
            'Sicil / kurum ID veri omurgası',
            'pass' if data_quality['missing_sicil'] == 0 and data_quality['duplicate_sicil'] == 0 else 'fail',
            f"Toplam kullanıcı: {data_quality['user_total']} | Eksik sicil: {data_quality['missing_sicil']} | Çift sicil: {data_quality['duplicate_sicil']}",
            'BT / İK',
            'TC yerine sicil bazlı kimlik omurgası korunmalı.',
        ),
        _gate(
            'migration_inventory',
            'Migration envanteri ve görünürlüğü',
            'pass' if migration['exists'] and migration['version_count'] >= 1 else 'fail',
            f"Versiyon dosyası: {migration['version_count']} | SQL hotfix dosyası: {migration['sql_count']}",
            'BT',
            'Canlı öncesi hedef head ve uygulanacak SQL scriptleri sabitlenmeli.',
        ),
        _gate(
            'backup_rollback',
            'Yedek ve rollback kanıtı',
            'pass' if backup_files >= 1 and log_files >= 1 else 'fail',
            f"Son 14 gün yedek: {backup_files} | Son 7 gün log: {log_files}",
            'BT',
            'Rollback dokümanı ve geri dönüş sırası yazılı olmalı.',
        ),
        _gate(
            'security_audit',
            'Güvenlik ve erişim denetimi',
            'pass' if security_report.critical_count == 0 and security_report.warning_count == 0 else 'warn' if security_report.critical_count == 0 else 'fail',
            f"Kritik: {security_report.critical_count} | Uyarı: {security_report.warning_count} | Bilgi: {security_report.info_count}",
            'BT / İdare',
            'CAPTCHA, cookie, CSRF ve dosya erişim bulguları tek tek kapanmalı.',
        ),
        _gate(
            'env_hardening',
            'Üretim env sertleştirmesi',
            'pass' if env_snapshot['finding_count'] == 0 else 'warn',
            f"Env bulgusu: {env_snapshot['finding_count']}",
            'BT',
            'SECRET_KEY hariç önerilen env satırlarını canlı öncesi uygulayın.',
        ),
        _gate(
            'visibility_matrix',
            'Rol ve kişi bazlı görünürlük',
            'pass' if data_quality['custom_permission_total'] >= 1 else 'warn',
            f"Özel görünürlük kaydı: {data_quality['custom_permission_total']} | Audit kaydı: {data_quality['audit_log_total']}",
            'BT / İdari Birim',
            'Kritik sekmeler için kişi bazlı görünürlük son kez doğrulanmalı.',
        ),
    ]

    counts = _counts(gates)
    tone, decision = _tone_from_counts(counts)

    summary_cards = [
        {'label': 'Kritik bulgu', 'value': security_report.critical_count, 'suffix': ''},
        {'label': 'Env bulgusu', 'value': env_snapshot['finding_count'], 'suffix': ''},
        {'label': 'Migration dosyası', 'value': migration['version_count'], 'suffix': ''},
        {'label': 'Özel görünürlük', 'value': data_quality['custom_permission_total'], 'suffix': ''},
    ]

    focus_blocks = [
        {
            'title': 'Veri geçişi kontrolü',
            'status': gates[0]['status'],
            'items': [
                'Eksik veya tekrar eden sicil numaraları kapatılmalı.',
                'Pilot kullanıcı havuzu ile canlı kullanıcı havuzu ayrımı net olmalı.',
                'Aktarımdan gelen sorunlu satırlar son kez gözden geçirilmeli.',
            ],
        },
        {
            'title': 'Migration ve SQL hotfix sırası',
            'status': gates[1]['status'],
            'items': [
                'Alembic head ve SQL klasörü kontrol edilmeli.',
                'Elle çalıştırılacak script varsa runbook içine yazılmalı.',
                'Canlı öncesi dry-run notu oluşturulmalı.',
            ],
        },
        {
            'title': 'Güvenlik ve görünürlük',
            'status': gates[3]['status'],
            'items': [
                'CAPTCHA, gizli soru, cookie ve CSRF ayarları tekrar test edilmeli.',
                'Sicil temelli görünürlük ve export erişimi role göre doğrulanmalı.',
                'Dosya ve medya erişimleri loglanıyor olmalı.',
            ],
        },
    ]

    recommendations = [row for row in gates if row['status'] in {'warn', 'fail'}]

    return {
        'generated_at': _now(),
        'decision': decision,
        'tone': tone,
        'counts': counts,
        'gates': gates,
        'summary_cards': summary_cards,
        'focus_blocks': focus_blocks,
        'recommendations': recommendations,
        'migration': migration,
        'data_quality': data_quality,
        'env': env_snapshot,
        'go_live': go_live,
        'security': security_report.to_dict(),
        'recent_logs': recent_logs,
    }


def phase9b_payload() -> dict[str, Any]:
    return phase9b_transition_center_snapshot()


def build_phase9b_markdown() -> str:
    payload = phase9b_transition_center_snapshot()
    lines = [
        '# Faz 9B | Veri ve Güvenlik Geçişi',
        '',
        f"- Üretim zamanı: {payload['generated_at']}",
        f"- Karar: {payload['decision']}",
        '',
        '## Kapılar',
        '',
    ]
    for row in payload['gates']:
        lines.append(f"- [{row['status']}] {row['label']} — {row['detail']}")
    lines.extend([
        '',
        '## Veri kalitesi',
        '',
        f"- Toplam kullanıcı: {payload['data_quality']['user_total']}",
        f"- Eksik sicil: {payload['data_quality']['missing_sicil']}",
        f"- Çift sicil: {payload['data_quality']['duplicate_sicil']}",
        '',
        '## Güvenlik',
        '',
        f"- Kritik bulgu: {payload['security']['critical_count']}",
        f"- Uyarı: {payload['security']['warning_count']}",
    ])
    return '\n'.join(lines) + '\n'


def record_phase9b_gate(actor: Any, gate_key: str, status: str, note: str = '') -> CommunicationAutomationLog:
    gate_key = safe_str(gate_key) or 'phase9b_gate'
    status = safe_str(status).lower() or 'pending'
    row = log_action(
        'phase9b_gate',
        actor,
        'communication_phase9b',
        None,
        f'Faz 9B kapısı | {gate_key}',
        payload={'gate_key': gate_key, 'status': status, 'note': note},
        status='success' if status in {'pass', 'warn'} else 'failed' if status == 'fail' else 'pending',
    )
    db.session.commit()
    return row


def record_phase9b_decision(actor: Any, decision: str, note: str = '') -> CommunicationAutomationLog:
    decision = safe_str(decision) or 'controlled_transition'
    row = log_action(
        'phase9b_decision',
        actor,
        'communication_phase9b',
        None,
        f'Faz 9B karar | {decision}',
        payload={'decision': decision, 'note': note},
        status='success',
    )
    db.session.commit()
    return row
