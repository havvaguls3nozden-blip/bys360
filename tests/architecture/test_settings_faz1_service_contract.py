from app.services.settings import (
    SettingDefinition,
    build_change_payload,
    build_definition,
    mask_sensitive_value,
    normalize_menu_key,
    to_bool,
)


def test_boolean_normalization_contract():
    assert to_bool("evet") is True
    assert to_bool("off") is False
    assert to_bool(None, default=True) is True


def test_sensitive_value_is_masked():
    assert mask_sensitive_value("SECRET_KEY", "abc") == "********"
    assert mask_sensitive_value("APP_TITLE", "BYS360") == "BYS360"


def test_menu_key_normalization_contract():
    assert normalize_menu_key("Performans Yönetimi") == "performans_yönetimi"


def test_definition_contract():
    definition = build_definition({"key": "site_title", "label": "Site Başlığı", "type": "string"})
    assert isinstance(definition, SettingDefinition)
    assert definition.key == "site_title"


def test_change_payload_masks_sensitive_value():
    from app.services.settings import SettingChange

    payload = build_change_payload(SettingChange(key="MAIL_PASSWORD", old_value="old", new_value="new"))
    assert payload["old_value"] == "********"
    assert payload["new_value"] == "********"
