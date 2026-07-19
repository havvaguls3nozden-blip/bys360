"""Faz H - giris, captcha ve guvenli oturum kontrol servisi."""
from __future__ import annotations

from pathlib import Path
from typing import Dict
import logging
logger = logging.getLogger(__name__)


def _scan_file(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8')
    except Exception:
        logger.exception("BYS360 V6B guarded exception | file=app/services/ui/auth_guardrails_service.py | line=13")
        return ''


def build_auth_guardrails_snapshot(project_root: str) -> dict[str, object]:
    root = Path(project_root)
    candidate_files = [
        root / 'app/__init__.py',
        root / 'app/routes.py',
        root / 'app/main_handlers/account_handlers.py',
        root / 'app/security.py',
    ]
    text = '\n'.join(_scan_file(p) for p in candidate_files if p.exists())
    lowered = text.lower()
    snapshot = {
        'captcha_reference': 'captcha' in lowered,
        'failed_login_threshold_reference': '3 failed' in lowered or '3 hatalı' in lowered or 'three failed' in lowered,
        'secret_question_reference': 'secret question' in lowered or 'gizli soru' in lowered,
        'password_change_reference': 'password change' in lowered or 'şifre değiş' in lowered,
        'session_cookie_reference': 'session_cookie' in lowered,
        'remember_cookie_reference': 'remember_cookie' in lowered,
    }
    snapshot['score'] = sum(
        1
        for key in [
            'captcha_reference',
            'failed_login_threshold_reference',
            'secret_question_reference',
            'password_change_reference',
        ]
        if snapshot.get(key)
    )
    return snapshot
