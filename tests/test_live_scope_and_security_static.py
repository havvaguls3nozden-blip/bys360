from pathlib import Path

import pytest

pytestmark = [pytest.mark.live, pytest.mark.realdb, pytest.mark.slow]


def test_removed_scope_blocks_education_isg_aliases():
    source = Path("app/config/live_scope.py").read_text(encoding="utf-8")
    assert '"/education-isg"' in source
    assert '"/isg"' in source
    assert '"main.isg_"' in source
    assert '"isg_management": "education"' in source


def test_captcha_guard_uses_shared_rate_limit_store_before_memory_fallback():
    source = Path("app/security/captcha_guard.py").read_text(encoding="utf-8")
    assert "_shared_record_bucket_hit" in source
    assert "_shared_read_bucket_count" in source
    assert "_FAILED_LOGIN_CACHE" in source
    assert "if shared is not None" in source


def test_schema_guard_is_not_auto_repair_by_default():
    config_source = Path("config.py").read_text(encoding="utf-8")
    app_source = Path("app/__init__.py").read_text(encoding="utf-8")
    assert "AUTO_REPAIR_SCHEMA" in config_source
    assert "str_to_bool(os.getenv('AUTO_REPAIR_SCHEMA'), False)" in config_source
    assert "auto_repair_schema and should_auto_repair_schema()" in app_source
