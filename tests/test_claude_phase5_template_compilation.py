# -*- coding: utf-8 -*-
"""
BYS360 Claude Faz 5 - Tüm Jinja2 şablon derleme testi.

Bu test Faz 1'de yaşanan endb/endblock, unexpected '*', eksik blok kapanışı
ve benzeri üretim hatalarının tekrar canlıya çıkmasını engellemek için vardır.

Marker: BYS360_CLAUDE_ROADMAP_PHASE5_TEMPLATE_COMPILATION_TEST
"""
from __future__ import annotations

from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_ROOT = PROJECT_ROOT / "app" / "templates"


def _build_parse_environment() -> Environment:
    return Environment(
        loader=FileSystemLoader(str(TEMPLATE_ROOT)),
        autoescape=True,
        extensions=["jinja2.ext.do", "jinja2.ext.loopcontrols", "jinja2.ext.i18n"],
        keep_trailing_newline=True,
    )


def _template_files():
    if not TEMPLATE_ROOT.exists():
        return []
    ignored_parts = {"__pycache__", ".pytest_cache"}
    return [
        p for p in sorted(TEMPLATE_ROOT.rglob("*.html"))
        if not any(part in ignored_parts for part in p.parts)
    ]


@pytest.mark.parametrize(
    "template_path",
    _template_files(),
    ids=lambda p: str(p.relative_to(TEMPLATE_ROOT)).replace("\\", "/"),
)
def test_all_templates_parse_without_syntax_error(template_path: Path):
    env = _build_parse_environment()
    source = template_path.read_text(encoding="utf-8", errors="replace")
    env.parse(source)
