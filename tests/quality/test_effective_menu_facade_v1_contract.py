from pathlib import Path

import pytest

pytestmark = pytest.mark.ci_safe


def test_effective_menu_is_facade_v1():
    path = Path("app/services/settings/effective_menu.py")
    text = path.read_text(encoding="utf-8")
    assert len(text.splitlines()) < 400
    assert "apply_runtime_policy_blocks" in text
    assert "build_menu_visibility_map" in text


def test_runtime_policy_context_contract_v1():
    path = Path("app/services/settings/effective_menu_parts/runtime_policy_context.py")
    text = path.read_text(encoding="utf-8")
    assert path.exists()
    assert len(text.splitlines()) < 800
    assert "def apply_runtime_policy_blocks" in text
    assert "exec(" not in text
    assert "eval(" not in text
    assert "_name.startswith(\"_BYS360_\")" in text
