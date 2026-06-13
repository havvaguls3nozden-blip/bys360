"""Faz H - sidebar / menu tutarlilik kontrol servisi."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8')
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return ''


def build_navigation_consistency_snapshot(project_root: str) -> Dict[str, object]:
    root = Path(project_root)
    base_candidates = [
        root / 'app/templates/base.html',
        root / 'templates/base.html',
    ]
    base_path = next((p for p in base_candidates if p.exists()), None)
    content = _read_text(base_path) if base_path else ''

    sections: List[str] = [
        'Genel',
        'Personel Yönetimi',
        'Performans Yönetimi',
        'İletişim ve Anket Yönetimi',
        'İç Portal',
        'Eğitim Yönetimi',
    ]
    section_hits = {name: (name in content) for name in sections}
    accordion_keywords = ['accordion', 'collapse', 'data-bs-toggle', 'submenu']
    active_keywords = ['active', 'is-active', 'nav-active', 'selected']

    return {
        'base_template_found': bool(base_path),
        'section_hits': section_hits,
        'accordion_behavior_references': {k: (k in content) for k in accordion_keywords},
        'active_state_references': {k: (k in content) for k in active_keywords},
        'score': int(bool(base_path)) + sum(1 for v in section_hits.values() if v),
    }