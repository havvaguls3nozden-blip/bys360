
"""AI redaction / maskeleme servis köprüsü.

Faz 1, AIRedactionRule tablo sözleşmesine uygun prompt öncesi kural payloadları ve runtime maskeleme
yardımcıları ekler. DB sorgusu veya commit yapmaz; aktif kural satırları route
ya da ilerideki servislerden bu katmana verilir.
"""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any
from collections.abc import Iterable, Mapping

from .security_contract import SENSITIVE_FIELD_NAMES, redact_mapping_for_ai, should_redact_field

DEFAULT_REDACTION_REPLACEMENT = "***"
DEFAULT_MODULE_TYPE = "general"


@dataclass(frozen=True)
class RedactionRuleSnapshot:
    module_type: str
    field_name: str
    redaction_type: str = "mask"
    replacement_text: str = DEFAULT_REDACTION_REPLACEMENT
    is_active: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _get_attr(row: Any, key: str, default: Any = None) -> Any:
    if isinstance(row, Mapping):
        return row.get(key, default)
    return getattr(row, key, default)


def _clean(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def normalize_redaction_field(field_name: Any) -> str:
    return _clean(field_name).lower()


def build_ai_redaction_rule_payload(
    *,
    module_type: str = DEFAULT_MODULE_TYPE,
    field_name: str,
    redaction_type: str = "mask",
    replacement_text: str | None = None,
    is_active: bool = True,
) -> dict[str, Any]:
    return RedactionRuleSnapshot(
        module_type=_clean(module_type, DEFAULT_MODULE_TYPE)[:50],
        field_name=normalize_redaction_field(field_name)[:100],
        redaction_type=_clean(redaction_type, "mask")[:50],
        replacement_text=_clean(replacement_text, DEFAULT_REDACTION_REPLACEMENT)[:100],
        is_active=bool(is_active),
    ).to_dict()


def build_default_redaction_rule_payloads(module_type: str = DEFAULT_MODULE_TYPE) -> list[dict[str, Any]]:
    return [
        build_ai_redaction_rule_payload(module_type=module_type, field_name=field_name)
        for field_name in sorted(SENSITIVE_FIELD_NAMES)
    ]


def extract_active_redaction_rules(rows: Iterable[Any], *, module_type: str | None = None) -> list[RedactionRuleSnapshot]:
    rules: list[RedactionRuleSnapshot] = []
    wanted_module = _clean(module_type).lower() if module_type else None
    for row in rows or []:
        active = bool(_get_attr(row, "is_active", True))
        if not active:
            continue
        row_module = _clean(_get_attr(row, "module_type", DEFAULT_MODULE_TYPE), DEFAULT_MODULE_TYPE).lower()
        if wanted_module and row_module not in {wanted_module, DEFAULT_MODULE_TYPE}:
            continue
        field_name = normalize_redaction_field(_get_attr(row, "field_name"))
        if not field_name:
            continue
        rules.append(
            RedactionRuleSnapshot(
                module_type=row_module,
                field_name=field_name,
                redaction_type=_clean(_get_attr(row, "redaction_type", "mask"), "mask"),
                replacement_text=_clean(
                    _get_attr(row, "replacement_text", DEFAULT_REDACTION_REPLACEMENT),
                    DEFAULT_REDACTION_REPLACEMENT,
                ),
                is_active=True,
            )
        )
    return rules


def _redact_by_rules(value: Any, rules_by_field: Mapping[str, RedactionRuleSnapshot], *, key: str | None = None) -> Any:
    normalized_key = normalize_redaction_field(key)
    rule = rules_by_field.get(normalized_key)
    if rule or should_redact_field(normalized_key):
        return (rule.replacement_text if rule else DEFAULT_REDACTION_REPLACEMENT) or DEFAULT_REDACTION_REPLACEMENT
    if isinstance(value, Mapping):
        return {item_key: _redact_by_rules(item_value, rules_by_field, key=str(item_key)) for item_key, item_value in value.items()}
    if isinstance(value, list):
        return [_redact_by_rules(item, rules_by_field) for item in value]
    if isinstance(value, tuple):
        return tuple(_redact_by_rules(item, rules_by_field) for item in value)
    return value


def apply_ai_redaction_rules(payload: Mapping[str, Any], rules: Iterable[RedactionRuleSnapshot | Mapping[str, Any]] = ()) -> dict[str, Any]:
    normalized_rules: dict[str, RedactionRuleSnapshot] = {}
    for rule in rules or []:
        if isinstance(rule, RedactionRuleSnapshot):
            snapshot = rule
        else:
            snapshot = RedactionRuleSnapshot(
                module_type=_clean(rule.get("module_type"), DEFAULT_MODULE_TYPE),
                field_name=normalize_redaction_field(rule.get("field_name")),
                redaction_type=_clean(rule.get("redaction_type"), "mask"),
                replacement_text=_clean(rule.get("replacement_text"), DEFAULT_REDACTION_REPLACEMENT),
                is_active=bool(rule.get("is_active", True)),
            )
        if snapshot.is_active and snapshot.field_name:
            normalized_rules[snapshot.field_name] = snapshot
    if not normalized_rules:
        return redact_mapping_for_ai(dict(payload))
    return _redact_by_rules(dict(payload), normalized_rules)


_EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?<!\d)(?:\+?90\s*)?(?:0?\d{3})[\s\-.]?\d{3}[\s\-.]?\d{2}[\s\-.]?\d{2}(?!\d)")
_TCKN_RE = re.compile(r"(?<!\d)\d{11}(?!\d)")


def redact_text_for_ai_log(text: Any, replacement: str = DEFAULT_REDACTION_REPLACEMENT) -> str:
    value = str(text or "")
    value = _EMAIL_RE.sub(replacement, value)
    value = _PHONE_RE.sub(replacement, value)
    value = _TCKN_RE.sub(replacement, value)
    return value


def build_ai_redaction_context(rows: Iterable[Any] = (), *, module_type: str | None = None) -> dict[str, Any]:
    rules = extract_active_redaction_rules(rows, module_type=module_type)
    return {
        "module_type": module_type or DEFAULT_MODULE_TYPE,
        "rule_count": len(rules),
        "active_fields": sorted({rule.field_name for rule in rules}),
        "default_sensitive_fields": sorted(SENSITIVE_FIELD_NAMES),
        "safe_default_enabled": True,
        "text_masking_enabled": True,
    }
