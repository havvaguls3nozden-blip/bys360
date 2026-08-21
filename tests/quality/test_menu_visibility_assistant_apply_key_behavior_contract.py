"""Behavior-lock for app/services/menu_visibility.py::_bys360_assistant_apply_key
and _bys360_assistant_collect_from_db, written as part of TD-CAND-003 Wave 1.

This module previously carried TWO definitions of each function: an earlier,
narrower one (silently shadowed, unreachable -- overwritten before any
runtime consumer could observe it, no capture-and-delegate mechanism kept it
alive) and a later, richer one that is the sole implementation ever actually
called. This file locks the CURRENT (surviving) behavior before/after the
dead first definitions were deleted -- it does not test internal structure,
only observable input/output behavior.

pytestmark = ci_safe: pure-function tests, no DB/network/subprocess.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.ci_safe


def _apply_key(menu_map, raw_key, raw_value=True):
    from app.services.menu_visibility import _bys360_assistant_apply_key
    _bys360_assistant_apply_key(menu_map, raw_key, raw_value)
    return menu_map


def test_assistant_module_key_enables_module_and_defaults_panel_on():
    menu_map: dict[str, bool] = {}
    result = _apply_key(menu_map, "assistant_module", True)
    assert result["assistant_module"] is True
    assert result["ai_agent_panel"] is True  # setdefault: only filled in if absent


def test_assistant_module_key_disabled_forces_all_child_keys_false():
    menu_map = {"ai_agent_panel": True, "ai_agent_knowledge": True}
    result = _apply_key(menu_map, "assistant_module", False)
    assert result["assistant_module"] is False
    assert result["ai_agent_panel"] is False
    assert result["ai_agent_knowledge"] is False
    assert result["ai_agent_teaching_center"] is False
    assert result["ai_teaching_center"] is False


def test_assistant_module_key_enabled_does_not_override_existing_panel_value():
    """setdefault semantics: an explicitly-set ai_agent_panel is preserved,
    not clobbered, when assistant_module is separately enabled."""
    menu_map = {"ai_agent_panel": False}
    result = _apply_key(menu_map, "assistant_module", True)
    assert result["assistant_module"] is True
    assert result["ai_agent_panel"] is False  # setdefault: unchanged, already present


@pytest.mark.parametrize("alias", ["ai_agent", "AI_AGENT_MODULE", "virtual_assistant", "sanal_asistan"])
def test_assistant_module_aliases_all_map_to_assistant_module(alias):
    result = _apply_key({}, alias, True)
    assert result["assistant_module"] is True


@pytest.mark.parametrize("alias", ["ai_agent_panel", "assistant_panel", "asistan_paneli", "assistant_center"])
def test_panel_aliases_set_only_ai_agent_panel(alias):
    result = _apply_key({}, alias, True)
    assert result == {"ai_agent_panel": True}


@pytest.mark.parametrize("alias", ["ai_agent_knowledge", "ai_teaching_center", "asistan_bilgi_bankasi"])
def test_knowledge_aliases_set_both_knowledge_and_teaching_center(alias):
    result = _apply_key({}, alias, True)
    assert result["ai_agent_knowledge"] is True
    assert result["ai_teaching_center"] is True
    assert "assistant_module" not in result


def test_teaching_center_alias_sets_only_its_own_key():
    result = _apply_key({}, "ai_agent_teaching_center", True)
    assert result == {"ai_agent_teaching_center": True}


def test_generic_tab_key_is_set_verbatim_when_in_allowed_set():
    result = _apply_key({}, "assistant_my_reminders", True)
    assert result == {"assistant_my_reminders": True}


def test_unknown_key_is_silently_ignored():
    result = _apply_key({}, "totally_unrecognized_key", True)
    assert result == {}


def test_key_normalization_handles_case_and_turkish_characters():
    """Locks _bys360_assistant_norm's transform as observed through apply_key:
    uppercase + Turkish İ/ş/ğ/ü/ö/ç all fold to the same normalized key."""
    result = _apply_key({}, "ASISTAN_ÖĞRETIM_MERKEZI", True)
    assert result == {"ai_agent_teaching_center": True}


def test_falsey_string_values_are_treated_as_not_allowed():
    result = _apply_key({}, "ai_agent_panel", "false")
    assert result == {"ai_agent_panel": False}


def test_collect_from_db_returns_without_error_when_no_db_available(monkeypatch):
    """Locks the fully-degraded path: _bys360_assistant_get_db() returning
    None must be a safe, silent no-op -- no exception, no menu_map mutation."""
    import app.services.menu_visibility as menu_visibility_module

    monkeypatch.setattr(menu_visibility_module, "_bys360_assistant_get_db", lambda: None)
    menu_map = {"preexisting": True}
    menu_visibility_module._bys360_assistant_collect_from_db(object(), menu_map)
    assert menu_map == {"preexisting": True}
