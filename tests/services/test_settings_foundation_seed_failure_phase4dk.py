from __future__ import annotations

import app.services.settings.foundation_access as foundation


def test_seed_failure_result_keeps_ok_false():
    rollback_calls = []

    result = (
        foundation
        .ensure_settings_phase1_seeded_handler(
            updated_by_user_id=7,
            table_exists=lambda name: True,
            flatten_menu_definitions_func=(
                lambda: (
                    (_ for _ in ()).throw(
                        RuntimeError(
                            "seed failure"
                        )
                    )
                )
            ),
            filter_live_menu_keys=(
                lambda keys: list(keys)
            ),
            static_role_default_menu_keys_func=(
                lambda role_name: set()
            ),
            role_menu_defaults={},
            role_menu_default_model=object,
            system_setting_model=object,
            module_setting_model=object,
            db_session=object(),
            system_definitions=[],
            iter_live_module_setting_definitions_func=(
                lambda: []
            ),
            value_to_storage=(
                lambda value, value_type: (
                    str(value)
                )
            ),
            safe_rollback=(
                lambda: rollback_calls.append(
                    "rollback"
                )
            ),
        )
    )

    # BYS360 H1F: the raw exception text ("seed failure") must never reach
    # the caller -- app/main_handlers/account_settings_helpers.py flashes
    # this "error" value verbatim on the live Ayarlar (Settings) admin
    # screen. ensure_settings_phase1_seeded_handler now returns a fixed
    # safe Turkish message instead; operator diagnosis still happens via
    # logger.exception(...) inside the handler.
    assert result == {
        "ok": False,
        "seeded_role_defaults": 0,
        "seeded_system_settings": 0,
        "seeded_module_settings": 0,
        "error": "Ayarlar omurgası hazırlanırken beklenmeyen bir hata oluştu.",
    }
    assert "seed failure" not in result["error"]

    assert rollback_calls == [
        "rollback"
    ]
