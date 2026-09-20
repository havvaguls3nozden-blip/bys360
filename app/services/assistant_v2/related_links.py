"""BYS360 Assistant V2 -- trusted related-link resolution (mandate Phase D).

A related link is never built from an arbitrary/client-supplied URL. It is
always derived from two already-trusted sources:

  1. `app.menu_registry_data_sections.MENU_SECTIONS` -- the SAME raw menu
     table the real sidebar is built from, which maps a real `menu_key` to a
     real, already-registered Flask endpoint name. This module reads it
     directly (not the Settings-Center-filtered `flatten_menu_definitions()`
     view), so related-link resolution never depends on an unrelated
     Settings Center visibility gate.
  2. `app.route_support.can_access_menu(user, menu_key)` -- the exact same
     authorization check every other part of this app uses, re-run for the
     CURRENT user on every call, never cached across users or requests.

If the endpoint cannot be resolved (unknown menu_key, endpoint needs URL
arguments this module doesn't have, or the user is not authorized for that
menu_key), no clickable link is produced -- callers may still show the label
alone if they choose to (Phase D: "Allow label-only informational source if
needed"), but this module never returns an unauthorized or broken URL.
"""
from __future__ import annotations

import logging
from typing import Any

from flask import url_for
from werkzeug.routing import BuildError

from app.route_support import can_access_menu

logger = logging.getLogger(__name__)


def _menu_key_to_endpoint(menu_key: str) -> str | None:
    from app.menu_registry_data_sections import MENU_SECTIONS

    for section in MENU_SECTIONS:
        for item in section.get("items", []) or []:
            if item.get("key") == menu_key and item.get("endpoint"):
                return str(item["endpoint"])
    return None


def resolve_related_link(user: Any, menu_key: str | None, label: str) -> dict[str, str] | None:
    """Returns {"label": ..., "url": ..., "module_key": ...}-shaped dict only
    when the target endpoint resolves AND the current user is authorized for
    it. Returns None (never a label-only stub) when the caller has no use
    for a label-only entry -- see `resolve_related_link_label_only` for that
    variant."""
    if not menu_key:
        return None
    endpoint = _menu_key_to_endpoint(menu_key)
    if not endpoint:
        return None
    try:
        if not can_access_menu(user, menu_key):
            return None
    except Exception:
        logger.exception("assistant_v2 related_links: authorization re-check failed for menu_key=%s", menu_key)
        return None
    try:
        href = url_for(endpoint)
    except BuildError:
        return None
    except Exception:
        logger.exception("assistant_v2 related_links: url_for failed for endpoint=%s", endpoint)
        return None
    return {"label": label, "url": href}


__all__ = ["resolve_related_link"]
