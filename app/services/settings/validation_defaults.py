"""BYS360 ayar tanimi dogrulama ve varsayilan deger katmani.

Settings Service Tamamlama Faz 2:
- Ayar kataloglarinin zorunlu alanlarini merkezi olarak dogrular.
- Eksik ama guvenli tamamlanabilir alanlari normalize eder.
- Varsayilan deger snapshot'ini settings_service.py disinda uretir.
- Veritabani semasina ve canli davranisa dokunmaz.
"""
from __future__ import annotations


from collections import OrderedDict
from typing import Any, Iterable


ALLOWED_VALUE_TYPES: set[str] = {"string", "bool", "int"}
ALLOWED_INPUT_TYPES: set[str] = {"text", "textarea", "bool", "number", "select", "email", "url", "password"}


def _clean_text(value: Any, fallback: str = "") -> str:
    text = str(value if value is not None else fallback).strip()
    return text or fallback


def _input_type_for(value_type: str, current: Any = None) -> str:
    incoming = _clean_text(current)
    if incoming:
        return incoming
    if value_type == "bool":
        return "bool"
    if value_type == "int":
        return "number"
    return "text"


def normalize_system_setting_definition(item: dict[str, Any]) -> dict[str, Any]:
    """Tek sistem ayar tanimini eksik guvenli alanlarla tamamlar."""
    normalized = dict(item)
    setting_key = _clean_text(normalized.get("setting_key"))
    group_key = _clean_text(normalized.get("group_key"), "general")
    value_type = _clean_text(normalized.get("value_type"), "string")
    if value_type not in ALLOWED_VALUE_TYPES:
        value_type = "string"
    normalized["setting_key"] = setting_key
    normalized["group_key"] = group_key
    normalized["group_label"] = _clean_text(normalized.get("group_label"), group_key)
    normalized["group_description"] = _clean_text(normalized.get("group_description"))
    normalized["label"] = _clean_text(normalized.get("label"), setting_key)
    normalized["description"] = _clean_text(normalized.get("description"))
    normalized["value_type"] = value_type
    normalized["input_type"] = _input_type_for(value_type, normalized.get("input_type"))
    normalized.setdefault("default", "false" if value_type == "bool" else "0" if value_type == "int" else "")
    return normalized


def normalize_module_setting_definition(item: dict[str, Any]) -> dict[str, Any]:
    """Tek modul ayar tanimini eksik guvenli alanlarla tamamlar."""
    normalized = normalize_system_setting_definition(item)
    module_key = _clean_text(item.get("module_key"))
    normalized["module_key"] = module_key
    normalized["module_label"] = _clean_text(item.get("module_label"), module_key)
    normalized["module_description"] = _clean_text(item.get("module_description"))
    return normalized


def normalize_system_setting_definitions(definitions: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sistem ayar katalogunu sirasi korunarak normalize eder ve tekrar edenleri tekillestirir."""
    indexed: OrderedDict[str, dict[str, Any]] = OrderedDict()
    for item in definitions:
        normalized = normalize_system_setting_definition(item)
        key = normalized.get("setting_key") or ""
        if not key or key in indexed:
            continue
        indexed[key] = normalized
    return list(indexed.values())


def normalize_module_setting_definitions(definitions: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Modul ayar katalogunu sirasi korunarak normalize eder ve tekrar edenleri tekillestirir."""
    indexed: OrderedDict[tuple[str, str], dict[str, Any]] = OrderedDict()
    for item in definitions:
        normalized = normalize_module_setting_definition(item)
        module_key = normalized.get("module_key") or ""
        setting_key = normalized.get("setting_key") or ""
        pair = (module_key, setting_key)
        if not module_key or not setting_key or pair in indexed:
            continue
        indexed[pair] = normalized
    return list(indexed.values())


def _validate_system_item(item: dict[str, Any], seen: set[str], errors: list[str], warnings: list[str]) -> None:
    key = _clean_text(item.get("setting_key"))
    if not key:
        errors.append("system.setting_key bos")
        return
    if key in seen:
        errors.append(f"system.duplicate | {key}")
    seen.add(key)
    for field in ("group_key", "group_label", "label", "value_type", "input_type"):
        if _clean_text(item.get(field)) == "":
            errors.append(f"system.{key}.{field} bos")
    if item.get("value_type") not in ALLOWED_VALUE_TYPES:
        errors.append(f"system.{key}.value_type gecersiz: {item.get('value_type')}")
    if item.get("input_type") not in ALLOWED_INPUT_TYPES:
        warnings.append(f"system.{key}.input_type alisilmadik: {item.get('input_type')}")


def _validate_module_item(item: dict[str, Any], seen: set[tuple[str, str]], errors: list[str], warnings: list[str]) -> None:
    module_key = _clean_text(item.get("module_key"))
    setting_key = _clean_text(item.get("setting_key"))
    pair = (module_key, setting_key)
    if not module_key or not setting_key:
        errors.append("module.module_key/setting_key bos")
        return
    if pair in seen:
        errors.append(f"module.duplicate | {module_key}.{setting_key}")
    seen.add(pair)
    for field in ("module_label", "label", "value_type", "input_type"):
        if _clean_text(item.get(field)) == "":
            errors.append(f"module.{module_key}.{setting_key}.{field} bos")
    if item.get("value_type") not in ALLOWED_VALUE_TYPES:
        errors.append(f"module.{module_key}.{setting_key}.value_type gecersiz: {item.get('value_type')}")
    if item.get("input_type") not in ALLOWED_INPUT_TYPES:
        warnings.append(f"module.{module_key}.{setting_key}.input_type alisilmadik: {item.get('input_type')}")


def validate_settings_catalog_contract(
    system_definitions: Iterable[dict[str, Any]],
    module_definitions: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Ayar katalogu sozlesmesini yan etkisiz denetler."""
    system_items = list(system_definitions)
    module_items = list(module_definitions)
    errors: list[str] = []
    warnings: list[str] = []
    seen_system: set[str] = set()
    seen_module: set[tuple[str, str]] = set()
    for item in system_items:
        _validate_system_item(item, seen_system, errors, warnings)
    for item in module_items:
        _validate_module_item(item, seen_module, errors, warnings)
    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "system_total": len(system_items),
        "module_total": len(module_items),
        "system_default_total": len([item for item in system_items if "default" in item]),
        "module_default_total": len([item for item in module_items if "default" in item]),
    }


def build_settings_defaults_snapshot(
    system_definitions: Iterable[dict[str, Any]],
    module_definitions: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Sistem ve modul ayarlarinin varsayilan deger haritasini uretir."""
    system_defaults = OrderedDict()
    for item in system_definitions:
        key = _clean_text(item.get("setting_key"))
        if key:
            system_defaults[key] = item.get("default")
    module_defaults: OrderedDict[str, OrderedDict[str, Any]] = OrderedDict()
    for item in module_definitions:
        module_key = _clean_text(item.get("module_key"))
        setting_key = _clean_text(item.get("setting_key"))
        if not module_key or not setting_key:
            continue
        module_defaults.setdefault(module_key, OrderedDict())[setting_key] = item.get("default")
    return {
        "system_defaults": dict(system_defaults),
        "module_defaults": {key: dict(value) for key, value in module_defaults.items()},
        "stats": {
            "system_total": len(system_defaults),
            "module_total": sum(len(value) for value in module_defaults.values()),
            "module_group_total": len(module_defaults),
        },
    }


__all__ = [
    "ALLOWED_INPUT_TYPES",
    "ALLOWED_VALUE_TYPES",
    "build_settings_defaults_snapshot",
    "normalize_module_setting_definition",
    "normalize_module_setting_definitions",
    "normalize_system_setting_definition",
    "normalize_system_setting_definitions",
    "validate_settings_catalog_contract",
]
