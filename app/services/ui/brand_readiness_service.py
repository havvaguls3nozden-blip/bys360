"""Faz H - kurumsal tasarim ve marka tutarliligi kontrol servisi."""
from __future__ import annotations

from pathlib import Path


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8')
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return ''


def _file_exists(root: Path, relative: str) -> bool:
    return (root / relative).exists()


def build_brand_readiness_snapshot(project_root: str) -> dict[str, object]:
    root = Path(project_root)
    base_candidates: list[str] = [
        'app/templates/base.html',
        'templates/base.html',
    ]
    base_path = next((root / p for p in base_candidates if (root / p).exists()), None)
    base_text = _read_text(base_path) if base_path else ''

    findings = {
        'base_template_found': bool(base_path),
        'sidebar_color_reference': '#8B0000' in base_text,
        'watermark_reference': 'ay_yildiz' in base_text or 'ay-yildiz' in base_text,
        'footer_copyright_reference': '© 2026 Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı' in base_text,
        'captcha_reference': 'captcha' in base_text.lower(),
        'logo_candidates': {
            'static/ay_yildiz.png': _file_exists(root, 'app/static/ay_yildiz.png') or _file_exists(root, 'static/ay_yildiz.png'),
            'static/ay_yildiz.svg': _file_exists(root, 'app/static/ay_yildiz.svg') or _file_exists(root, 'static/ay_yildiz.svg'),
            'static/img/logo.png': _file_exists(root, 'app/static/img/logo.png') or _file_exists(root, 'static/img/logo.png'),
        },
    }
    findings['score'] = sum(
        1 for key in ['base_template_found', 'sidebar_color_reference', 'watermark_reference', 'footer_copyright_reference']
        if findings.get(key)
    )
    return findings