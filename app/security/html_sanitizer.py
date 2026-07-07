# -*- coding: utf-8 -*-
"""Small HTML safety filters for BYS360 templates."""
from __future__ import annotations

import html
import re
from typing import Any

from markupsafe import Markup, escape

try:
    import bleach  # type: ignore
except Exception:  # pragma: no cover
    bleach = None  # type: ignore

_ALLOWED_SOCIAL_TAGS = ["blockquote", "a", "br"]
_ALLOWED_SOCIAL_ATTRS = {
    "blockquote": ["class", "data-dnt", "data-instgrm-permalink", "data-instgrm-version", "align"],
    "a": ["href", "title", "target", "rel"],
}
_ALLOWED_PROTOCOLS = ["http", "https"]
_ALLOWED_NAV_ATTRS = {"title", "role", "aria-label", "aria-current"}
_ONCLICK_LOGOUT = "return submitLogoutForm(event);"
_ATTR_RE = re.compile(r"([A-Za-z0-9_:\-.]+)\s*=\s*([\"'])(.*?)\2", re.S)
_EVENT_ATTR_RE = re.compile(r"\s+on[a-zA-Z]+\s*=\s*([\"']).*?\1", re.S)
_SCRIPT_RE = re.compile(r"<\s*(script|style|iframe|object|embed)[^>]*>.*?<\s*/\s*\1\s*>", re.I | re.S)
_JS_URL_RE = re.compile(r"javascript\s*:", re.I)


def _strip_obvious_danger(value: str) -> str:
    value = _SCRIPT_RE.sub("", value)
    value = _EVENT_ATTR_RE.sub("", value)
    value = _JS_URL_RE.sub("", value)
    return value


def safe_social_embed(value: Any) -> Markup:
    raw = _strip_obvious_danger(str(value or ""))
    if not raw.strip():
        return Markup("")
    if bleach is None:
        return Markup(escape(raw))
    cleaned = bleach.clean(
        raw,
        tags=_ALLOWED_SOCIAL_TAGS,
        attributes=_ALLOWED_SOCIAL_ATTRS,
        protocols=_ALLOWED_PROTOCOLS,
        strip=True,
    )
    return Markup(_strip_obvious_danger(cleaned))


def safe_nav_attrs(value: Any) -> Markup:
    raw = str(value or "")
    attrs: list[str] = []
    for match in _ATTR_RE.finditer(raw):
        name = match.group(1).strip().lower()
        attr_value = match.group(3).strip()
        if name.startswith("data-") or name in _ALLOWED_NAV_ATTRS:
            attrs.append(f'{name}="{html.escape(attr_value, quote=True)}"')
        elif name == "onclick" and attr_value == _ONCLICK_LOGOUT:
            attrs.append('onclick="return submitLogoutForm(event);"')
    return Markup(" ".join(attrs))
