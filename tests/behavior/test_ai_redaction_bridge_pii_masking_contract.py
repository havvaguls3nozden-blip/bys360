"""BYS360_PHASE5_AGENT3_REDACTION_CONTRACT

Behavioral contract tests for the PII redaction layer that sits directly in
front of the AI Decision Support Center's prompt/summary construction:

- ``app/services/ai_decision/redaction_bridge.py``
  (``apply_ai_redaction_rules``, ``extract_active_redaction_rules``,
  ``redact_text_for_ai_log``, ``build_ai_redaction_context``)
- ``app/services/ai_decision/security_contract.py``
  (``should_redact_field``, ``redact_mapping_for_ai``)

Everything exercised here is pure Python (regex matching over plain strings,
dict/list/tuple walking over plain dicts and ``SimpleNamespace``/``dict``
"row" stand-ins). None of the target functions perform a DB query or need a
Flask application context -- ``extract_active_redaction_rules`` only ever
iterates whatever ``rows`` iterable its caller hands it, it never queries the
database itself -- so no app/DB fixture is used anywhere in this file, and no
``app.*`` module is imported beyond the two modules under test.

CONFIRMED PRODUCTION DEFECT (not fixed here, not asserted as correct -- see
the STOP-rule note next to ``test_build_ai_redaction_context_metadata_fields_are_correct``
below and the agent's final report): ``build_ai_redaction_context`` computes
``rules = extract_active_redaction_rules(...)`` and correctly summarizes them
as ``rule_count``/``active_fields``, but never puts the actual rule objects
into its returned dict under any key. The one real caller of this pattern,
``app/services/ai_decision/summary_cache.py::build_ai_safe_summary_text``,
does ``apply_ai_redaction_rules(payload, redaction_context.get("rules", []))``
-- which is always ``[]`` because the key does not exist -- so any
custom/DB-configured redaction rule for a field outside the static
``SENSITIVE_FIELD_NAMES`` set is silently never applied when routed through
``build_ai_redaction_context``, even though ``rule_count``/``active_fields``
report it as active. This file proves the underlying rule-application
machinery (``apply_ai_redaction_rules`` + ``extract_active_redaction_rules``
wired directly) works correctly; it deliberately does not assert that the
``build_ai_redaction_context`` -> ``.get("rules", [])`` pathway applies custom
rules, since that would encode the defect as the expected contract.

SECOND CONFIRMED PRODUCTION DEFECT: ``apply_ai_redaction_rules`` accepts
``rules: Iterable[RedactionRuleSnapshot | Mapping[str, Any]]`` -- both input
shapes are explicitly supported by its own type signature -- but only
normalizes ``field_name`` to lowercase for the ``Mapping`` shape
(``normalize_redaction_field(rule.get("field_name"))``). When a rule is
already a ``RedactionRuleSnapshot`` instance, its ``field_name`` is used
completely as-is (``snapshot = rule``) as the dict key in
``normalized_rules``, with no normalization call. ``_redact_by_rules``
always lowercases the *payload* key it looks up
(``normalize_redaction_field(key)``), so any ``RedactionRuleSnapshot`` built
directly with a non-lowercase ``field_name`` (e.g. ``"Employee_No"``) can
never match -- not even against a payload key of the exact same casing,
because the payload-side lookup key is forced to lowercase while the stored
rule key is not. Reproduced directly:
``apply_ai_redaction_rules({"Employee_No": "999"}, [RedactionRuleSnapshot(module_type="general", field_name="Employee_No", is_active=True)])``
returns ``{"Employee_No": "999"}`` -- completely unmasked, despite an exact
field-name match. This does not currently bite the one real production
caller (``extract_active_redaction_rules`` always lowercases ``field_name``
before constructing its ``RedactionRuleSnapshot`` instances), but it is a
real, reproducible break of the "field-name matching is case-insensitive"
contract for any ``RedactionRuleSnapshot`` built directly with mixed/upper
case -- a fully valid input per the function's own type signature. Not
fixed here (out of the STOP-rule boundary); see the agent's final report.
Tests below only exercise the two casing combinations that are actually
correct (payload-key casing against an already-lowercase
``RedactionRuleSnapshot``, and mixed-case ``field_name`` supplied via the
``Mapping`` shape, which IS normalized).
"""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from app.services.ai_decision.redaction_bridge import (
    DEFAULT_REDACTION_REPLACEMENT,
    RedactionRuleSnapshot,
    apply_ai_redaction_rules,
    build_ai_redaction_context,
    extract_active_redaction_rules,
    redact_text_for_ai_log,
)
from app.services.ai_decision.security_contract import (
    SENSITIVE_FIELD_NAMES,
    redact_mapping_for_ai,
    should_redact_field,
)

# ---------------------------------------------------------------------------
# should_redact_field -- case-insensitive default-field membership
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field_name",
    ["tckn", "TCKN", " Tckn ", "phone", "PHONE", "email", "E_Posta", "iban", "password", "token", "secret"],
)
def test_should_redact_field_true_for_default_sensitive_fields_case_insensitive(field_name: str) -> None:
    assert should_redact_field(field_name) is True


@pytest.mark.parametrize(
    "field_name",
    ["full_name", "department", "note", "status", "created_at", "", None, "   "],
)
def test_should_redact_field_false_for_non_sensitive_or_blank_input(field_name: Any) -> None:
    assert should_redact_field(field_name) is False


def test_should_redact_field_covers_every_default_sensitive_field_name() -> None:
    for name in SENSITIVE_FIELD_NAMES:
        assert should_redact_field(name) is True
        assert should_redact_field(name.upper()) is True


# ---------------------------------------------------------------------------
# redact_mapping_for_ai -- pure key-based recursive masking
# ---------------------------------------------------------------------------


def test_redact_mapping_for_ai_masks_default_field_and_keeps_siblings() -> None:
    payload = {"tckn": "12345678901", "full_name": "Ayse Yilmaz"}
    result = redact_mapping_for_ai(payload)
    assert result["tckn"] == "***"
    assert result["full_name"] == "Ayse Yilmaz"


def test_redact_mapping_for_ai_is_case_insensitive_on_key_name() -> None:
    result = redact_mapping_for_ai({"TCKN": "12345678901", "Email": "a@b.com"})
    assert result["TCKN"] == "***"
    assert result["Email"] == "***"


def test_redact_mapping_for_ai_recurses_through_nested_dict_list_and_tuple() -> None:
    payload = {
        "level1": {
            "level2": [
                {"tckn": "12345678901", "note": "keep-1"},
                {"nested": ("plain-text", {"password": "supersecret", "ok": "keep-2"})},
            ],
            "sibling": "keep-3",
        },
        "top_sibling": "keep-4",
    }
    result = redact_mapping_for_ai(payload)

    assert result["level1"]["level2"][0]["tckn"] == "***"
    assert result["level1"]["level2"][0]["note"] == "keep-1"
    nested = result["level1"]["level2"][1]["nested"]
    assert isinstance(nested, tuple)  # tuple identity must survive the recursion
    assert nested[0] == "plain-text"  # not key-matched -> untouched by key-based masking
    assert nested[1]["password"] == "***"
    assert nested[1]["ok"] == "keep-2"
    assert result["level1"]["sibling"] == "keep-3"
    assert result["top_sibling"] == "keep-4"


def test_redact_mapping_for_ai_preserves_list_type_at_every_level() -> None:
    result = redact_mapping_for_ai({"items": [{"tckn": "1"}, {"tckn": "2"}]})
    assert isinstance(result["items"], list)
    assert [item["tckn"] for item in result["items"]] == ["***", "***"]


def test_redact_mapping_for_ai_non_dict_top_level_returns_empty_dict() -> None:
    # Deliberately wrong-typed inputs (None / list / str) to prove the
    # function fails closed at runtime rather than raising -- ignore the
    # static type errors these intentionally violate.
    assert redact_mapping_for_ai(None) == {}  # type: ignore[arg-type]
    assert redact_mapping_for_ai([{"tckn": "1"}]) == {}  # type: ignore[arg-type]
    assert redact_mapping_for_ai("tckn") == {}  # type: ignore[arg-type]


def test_redact_mapping_for_ai_plain_text_payload_passes_through_unchanged() -> None:
    payload = {"department": "IT", "title": "Uzman", "count": 3, "active": True}
    assert redact_mapping_for_ai(payload) == payload


# ---------------------------------------------------------------------------
# redact_text_for_ai_log -- free-text regex masking (TCKN / email / phone)
# ---------------------------------------------------------------------------


def test_redact_text_for_ai_log_masks_turkish_national_id() -> None:
    text = "Musteri kimlik no 12345678901 olarak kayitlidir."
    result = redact_text_for_ai_log(text)
    assert "12345678901" not in result
    assert "***" in result


def test_redact_text_for_ai_log_masks_email_address() -> None:
    text = "Iletisim: user.name+test@Example.CO.UK lutfen."
    result = redact_text_for_ai_log(text)
    assert "@" not in result
    assert "***" in result


@pytest.mark.parametrize(
    "phone_text",
    [
        "0532 123 45 67",
        "05321234567",
        "+90 532 123 45 67",
        "532 123 45 67",
        "0532-123-45-67",
    ],
)
def test_redact_text_for_ai_log_masks_phone_number_in_common_formats(phone_text: str) -> None:
    result = redact_text_for_ai_log(f"Telefon: {phone_text} numarasindan ulasilabilir.")
    assert "***" in result
    assert phone_text not in result


def test_redact_text_for_ai_log_masks_multiple_pii_types_in_one_string() -> None:
    text = "TCKN: 12345678901, email: user@test.com, tel: 0532 111 22 33 bilgileri."
    result = redact_text_for_ai_log(text)
    assert "12345678901" not in result
    assert "user@test.com" not in result
    assert "0532 111 22 33" not in result
    assert result.count("***") == 3


def test_redact_text_for_ai_log_plain_non_pii_text_passes_through_unchanged() -> None:
    text = "Bu tamamen normal bir metindir."
    assert redact_text_for_ai_log(text) == text


@pytest.mark.parametrize(
    "safe_text",
    [
        "Fatura no: 2026083012345 kayitlidir.",  # 13 consecutive digits, not phone/TCKN shaped
        "Siparis kodu 123456789 dir.",  # 9 digits, below TCKN/phone minimum
    ],
)
def test_redact_text_for_ai_log_does_not_false_positive_on_non_pii_digit_runs(safe_text: str) -> None:
    assert redact_text_for_ai_log(safe_text) == safe_text


def test_redact_text_for_ai_log_twelve_digit_run_is_outside_tckn_and_phone_width_and_is_not_masked() -> None:
    # TCKN is exactly 11 digits and phone is exactly 10 (with optional
    # separators/leading 0), both anchored with (?<!\d)/(?!\d) boundaries;
    # a bare 12-digit run fits neither shape and must pass through untouched.
    twelve_digits = "Kod: 123456789012 son."
    assert redact_text_for_ai_log(twelve_digits) == twelve_digits


def test_redact_text_for_ai_log_bare_ten_digit_run_is_masked_via_phone_shape() -> None:
    # A 10-digit run with no separators still structurally matches the phone
    # pattern (leading-0 group is optional), so it is masked even though it
    # is not a TCKN. Documents this real, non-obvious overlap explicitly.
    result = redact_text_for_ai_log("Kod: 1234567890 son.")
    assert result == "Kod: *** son."


def test_redact_text_for_ai_log_handles_none_and_non_string_input_without_raising() -> None:
    assert redact_text_for_ai_log(None) == ""
    assert redact_text_for_ai_log(12345678901) == "***"


def test_redact_text_for_ai_log_honors_custom_replacement_token() -> None:
    result = redact_text_for_ai_log("mail: a@b.com", replacement="[GIZLI]")
    assert result == "mail: [GIZLI]"


# ---------------------------------------------------------------------------
# extract_active_redaction_rules -- DB-row-shaped filtering (pure function,
# rows are supplied by the caller; no DB access happens inside it)
# ---------------------------------------------------------------------------


def test_extract_active_redaction_rules_includes_active_row_for_matching_module() -> None:
    rows = [SimpleNamespace(module_type="hr", field_name="employee_no", redaction_type="mask", replacement_text="***", is_active=True)]
    rules = extract_active_redaction_rules(rows, module_type="hr")
    assert len(rules) == 1
    assert rules[0].field_name == "employee_no"
    assert rules[0].module_type == "hr"
    assert rules[0].is_active is True


def test_extract_active_redaction_rules_excludes_inactive_row() -> None:
    rows = [SimpleNamespace(module_type="hr", field_name="employee_no", is_active=False)]
    rules = extract_active_redaction_rules(rows, module_type="hr")
    assert rules == []


def test_extract_active_redaction_rules_excludes_row_scoped_to_a_different_module_type() -> None:
    rows = [SimpleNamespace(module_type="finance", field_name="vergi_no", is_active=True)]
    rules = extract_active_redaction_rules(rows, module_type="hr")
    assert rules == []


def test_extract_active_redaction_rules_general_module_row_always_matches() -> None:
    rows = [SimpleNamespace(module_type="general", field_name="shared_field", is_active=True)]
    for wanted in ("hr", "finance", "anything_else"):
        rules = extract_active_redaction_rules(rows, module_type=wanted)
        assert [r.field_name for r in rules] == ["shared_field"]


def test_extract_active_redaction_rules_no_module_filter_returns_every_active_row() -> None:
    rows = [
        SimpleNamespace(module_type="general", field_name="general_field", is_active=True),
        SimpleNamespace(module_type="hr", field_name="hr_field", is_active=True),
        SimpleNamespace(module_type="finance", field_name="finance_field", is_active=True),
        SimpleNamespace(module_type="hr", field_name="inactive_field", is_active=False),
    ]
    rules = extract_active_redaction_rules(rows, module_type=None)
    assert sorted(r.field_name for r in rules) == ["finance_field", "general_field", "hr_field"]


def test_extract_active_redaction_rules_supports_mapping_shaped_rows_and_normalizes_case() -> None:
    rows = [{"module_type": "HR", "field_name": "Employee_No", "is_active": True}]
    rules = extract_active_redaction_rules(rows, module_type="hr")
    assert len(rules) == 1
    assert rules[0].module_type == "hr"
    assert rules[0].field_name == "employee_no"


def test_extract_active_redaction_rules_skips_row_with_blank_field_name() -> None:
    rows = [SimpleNamespace(module_type="general", field_name="   ", is_active=True)]
    assert extract_active_redaction_rules(rows) == []


def test_extract_active_redaction_rules_defaults_missing_is_active_to_true() -> None:
    rows = [SimpleNamespace(module_type="general", field_name="new_field")]  # no is_active attr at all
    rules = extract_active_redaction_rules(rows)
    assert len(rules) == 1
    assert rules[0].field_name == "new_field"


def test_extract_active_redaction_rules_handles_none_and_empty_rows() -> None:
    # None is a deliberately wrong-typed input (fail-closed check).
    assert extract_active_redaction_rules(None) == []  # type: ignore[arg-type]
    assert extract_active_redaction_rules([]) == []


# ---------------------------------------------------------------------------
# apply_ai_redaction_rules -- the combined transformation entry point
# ---------------------------------------------------------------------------


def test_apply_ai_redaction_rules_masks_default_sensitive_field_with_no_custom_rules() -> None:
    payload = {"tckn": "12345678901", "full_name": "keep-me"}
    result = apply_ai_redaction_rules(payload)
    assert result["tckn"] == "***"
    assert result["full_name"] == "keep-me"


def test_apply_ai_redaction_rules_default_fallback_survives_when_custom_rules_present() -> None:
    # This is the core "default fallback must never be silently disabled just
    # because the caller passed custom rules" invariant: a default-set field
    # (tckn) not covered by any custom rule must still be masked alongside
    # the custom-ruled field.
    custom_rule = RedactionRuleSnapshot(module_type="general", field_name="custom_field", is_active=True)
    payload = {"tckn": "12345678901", "custom_field": "x", "other": "keep"}
    result = apply_ai_redaction_rules(payload, [custom_rule])
    assert result["tckn"] == "***"
    assert result["custom_field"] == "***"
    assert result["other"] == "keep"


def test_apply_ai_redaction_rules_honors_active_custom_rule_for_non_default_field() -> None:
    rows = [SimpleNamespace(module_type="hr", field_name="sgk_no", is_active=True)]
    active_rules = extract_active_redaction_rules(rows, module_type="hr")
    payload = {"sgk_no": "55555", "keep": "x"}
    result = apply_ai_redaction_rules(payload, active_rules)
    assert result["sgk_no"] == "***"
    assert result["keep"] == "x"


def test_apply_ai_redaction_rules_honors_custom_rule_several_levels_deep() -> None:
    rows = [SimpleNamespace(module_type="hr", field_name="sgk_no", replacement_text="###", is_active=True)]
    active_rules = extract_active_redaction_rules(rows, module_type="hr")
    payload = {"outer": {"inner": [{"sgk_no": "55555", "keep": "x"}]}}
    result = apply_ai_redaction_rules(payload, active_rules)
    assert result["outer"]["inner"][0]["sgk_no"] == "###"
    assert result["outer"]["inner"][0]["keep"] == "x"


def test_apply_ai_redaction_rules_ignores_wrongly_scoped_module_rule_but_keeps_default_masking() -> None:
    rows = [SimpleNamespace(module_type="finance", field_name="vergi_no", is_active=True)]
    active_rules = extract_active_redaction_rules(rows, module_type="hr")  # scoping excludes it upstream
    payload = {"vergi_no": "77777", "tckn": "12345678901"}
    result = apply_ai_redaction_rules(payload, active_rules)
    assert result["vergi_no"] == "77777"  # not masked: rule never made it into the active set
    assert result["tckn"] == "***"  # default fallback still applies


def test_apply_ai_redaction_rules_uses_custom_replacement_text() -> None:
    rule = RedactionRuleSnapshot(module_type="general", field_name="employee_no", replacement_text="[REDACTED]", is_active=True)
    result = apply_ai_redaction_rules({"employee_no": "999"}, [rule])
    assert result["employee_no"] == "[REDACTED]"


def test_apply_ai_redaction_rules_accepts_plain_mapping_shaped_rule_objects() -> None:
    dict_rule = {"module_type": "general", "field_name": "custom_dict_field", "replacement_text": "HIDDEN", "is_active": True}
    result = apply_ai_redaction_rules({"custom_dict_field": "abc", "plain": "keep"}, [dict_rule])
    assert result["custom_dict_field"] == "HIDDEN"
    assert result["plain"] == "keep"


def test_apply_ai_redaction_rules_excludes_inactive_rule_passed_directly() -> None:
    active_rule = RedactionRuleSnapshot(module_type="general", field_name="employee_no", replacement_text="[REDACTED]", is_active=True)
    inactive_rule = RedactionRuleSnapshot(module_type="general", field_name="ignored_field", replacement_text="[NOPE]", is_active=False)
    payload = {"employee_no": "999", "ignored_field": "sensitive-ish", "tckn": "12345678901", "plain": "keep"}
    result = apply_ai_redaction_rules(payload, [active_rule, inactive_rule])
    assert result["employee_no"] == "[REDACTED]"
    assert result["ignored_field"] == "sensitive-ish"  # inactive rule must not apply
    assert result["tckn"] == "***"  # default fallback still applies alongside custom rules
    assert result["plain"] == "keep"


def test_apply_ai_redaction_rules_payload_key_case_insensitive_against_normalized_rule() -> None:
    # extract_active_redaction_rules always normalizes field_name to lowercase
    # before constructing RedactionRuleSnapshot (this is what the real
    # DB-row -> extract_active_redaction_rules -> apply_ai_redaction_rules
    # pipeline always produces); the payload's own key casing must still be
    # matched case-insensitively against that normalized rule.
    rule = RedactionRuleSnapshot(module_type="general", field_name="employee_no", is_active=True)
    result = apply_ai_redaction_rules({"EMPLOYEE_NO": "999", "TCKN": "12345678901"}, [rule])
    assert result["EMPLOYEE_NO"] == "***"
    assert result["TCKN"] == "***"


def test_apply_ai_redaction_rules_mapping_shaped_rule_normalizes_mixed_case_field_name() -> None:
    # A Mapping/dict-shaped rule (e.g. {"field_name": "Employee_No", ...}) is
    # explicitly supported by apply_ai_redaction_rules's own type signature
    # (RedactionRuleSnapshot | Mapping[str, Any]) and is passed through
    # normalize_redaction_field() before use, so mixed-case field names in
    # that shape are correctly lowercased and still match an upper-case
    # payload key.
    dict_rule = {"module_type": "general", "field_name": "Employee_No", "is_active": True}
    result = apply_ai_redaction_rules({"EMPLOYEE_NO": "999"}, [dict_rule])
    assert result["EMPLOYEE_NO"] == "***"


def test_apply_ai_redaction_rules_plain_payload_passes_through_unchanged() -> None:
    payload = {"department": "IT", "title": "Uzman", "count": 3}
    assert apply_ai_redaction_rules(payload) == payload
    # also unchanged when (irrelevant) custom rules for unrelated fields are present
    rule = RedactionRuleSnapshot(module_type="general", field_name="unrelated_field", is_active=True)
    assert apply_ai_redaction_rules(payload, [rule]) == payload


def test_apply_ai_redaction_rules_default_only_and_custom_rule_paths_both_preserve_tuple_type() -> None:
    rule = RedactionRuleSnapshot(module_type="general", field_name="password", is_active=True)
    payload = {"items": (1, {"password": "p"}, 3)}

    no_custom = apply_ai_redaction_rules(payload)
    assert isinstance(no_custom["items"], tuple)
    assert no_custom["items"][1]["password"] == "***"

    with_custom = apply_ai_redaction_rules(payload, [rule])
    assert isinstance(with_custom["items"], tuple)
    assert with_custom["items"][1]["password"] == "***"


# ---------------------------------------------------------------------------
# build_ai_redaction_context -- metadata contract that IS correct.
#
# STOP-RULE NOTE: this function also computes the active RedactionRuleSnapshot
# list internally but does not expose it under any key of the returned dict
# (confirmed: `"rules" in build_ai_redaction_context(...)` is False). A real
# caller (`summary_cache.build_ai_safe_summary_text`) reads
# `redaction_context.get("rules", [])`, which is therefore always `[]`, so
# custom DB-configured rules never actually reach `apply_ai_redaction_rules`
# through this function. That specific gap is intentionally NOT tested here
# (see module docstring and the agent's final report) to avoid asserting the
# defect as the expected contract. Only the metadata fields that ARE correct
# are covered below.
# ---------------------------------------------------------------------------


def test_build_ai_redaction_context_metadata_fields_are_correct() -> None:
    # Deliberately does NOT assert anything about whether a "rules" key is
    # present/absent in the returned dict -- see the STOP-RULE NOTE above.
    # Pinning that key's current absence would turn this test into exactly
    # the kind of known-bug characterization this wave's rules forbid: fixing
    # the defect (adding the rule objects under some key) would then break
    # this test for no behavioral reason. Only the metadata fields that are
    # independently correct today, and would remain correct after a fix, are
    # asserted here.
    rows = [
        SimpleNamespace(module_type="hr", field_name="employee_no", is_active=True),
        SimpleNamespace(module_type="finance", field_name="vergi_no", is_active=True),
        SimpleNamespace(module_type="hr", field_name="inactive_field", is_active=False),
    ]
    context = build_ai_redaction_context(rows, module_type="hr")

    assert context["module_type"] == "hr"
    assert context["rule_count"] == 1
    assert context["active_fields"] == ["employee_no"]
    assert context["default_sensitive_fields"] == sorted(SENSITIVE_FIELD_NAMES)
    assert context["safe_default_enabled"] is True
    assert context["text_masking_enabled"] is True


def test_build_ai_redaction_context_defaults_module_type_when_none_given() -> None:
    context = build_ai_redaction_context([], module_type=None)
    assert context["module_type"] == "general"
    assert context["rule_count"] == 0
    assert context["active_fields"] == []


def test_build_ai_redaction_context_default_sensitive_fields_always_reflects_static_set() -> None:
    context = build_ai_redaction_context([])
    assert context["default_sensitive_fields"] == sorted(SENSITIVE_FIELD_NAMES)
    assert "tckn" in context["default_sensitive_fields"]


# ---------------------------------------------------------------------------
# DEFAULT_REDACTION_REPLACEMENT sanity (used implicitly throughout above)
# ---------------------------------------------------------------------------


def test_default_redaction_replacement_constant_is_the_mask_token_used_by_defaults() -> None:
    assert DEFAULT_REDACTION_REPLACEMENT == "***"
    result = apply_ai_redaction_rules({"tckn": "12345678901"})
    assert result["tckn"] == DEFAULT_REDACTION_REPLACEMENT
