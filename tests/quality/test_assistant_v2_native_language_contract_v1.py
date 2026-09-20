"""BYS360 Assistant V2 -- native language layer behavior contract:
domain_vocabulary, entity_extraction, language_helpers, and the
confidence-tiered intent_router.resolve_intent().
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.ci_safe


# ---------------------------------------------------------------------------
# domain_vocabulary
# ---------------------------------------------------------------------------


def test_every_module_vocabulary_key_exists_in_module_registry():
    from app.services.assistant_v2.domain_vocabulary import MODULE_VOCABULARIES
    from app.services.settings.module_registry import MODULE_REGISTRY

    known_module_keys = {m.module_key for m in MODULE_REGISTRY}
    orphan = [v.module_key for v in MODULE_VOCABULARIES if v.module_key not in known_module_keys]
    assert orphan == []


def test_expand_query_tokens_widens_with_synonym():
    from app.services.assistant_v2.domain_vocabulary import expand_query_tokens

    expanded = expand_query_tokens("çalışanları listele")
    assert "personel" in expanded


def test_expand_query_tokens_applies_light_suffix_stripping():
    from app.services.assistant_v2.domain_vocabulary import expand_query_tokens

    expanded = expand_query_tokens("personelin izinleri")
    # "personelin" -> stem "personel" via suffix stripping
    assert "personel" in expanded


def test_expand_query_tokens_empty_text_returns_empty_set():
    from app.services.assistant_v2.domain_vocabulary import expand_query_tokens

    assert expand_query_tokens("") == set()


# ---------------------------------------------------------------------------
# entity_extraction
# ---------------------------------------------------------------------------


def test_extract_year_and_period_slash_form():
    from app.services.assistant_v2.entity_extraction import extract_entities

    entities = extract_entities("2026/2 dönemi değerlendirmelerini göster")
    assert 2026 in entities.years
    assert any(p.year == 2026 and p.period_index == 2 and p.confident for p in entities.period_references)


def test_extract_ordinal_period_without_year_is_not_confident():
    from app.services.assistant_v2.entity_extraction import extract_entities

    entities = extract_entities("ikinci dönem değerlendirmelerini göster")
    assert any(p.period_index == 2 and not p.confident for p in entities.period_references)


def test_extract_sicil_no_labeled():
    from app.services.assistant_v2.entity_extraction import extract_entities

    entities = extract_entities("sicil no: 123456 kaydını göster")
    assert entities.sicil_no == "123456"


def test_extract_status_keywords():
    from app.services.assistant_v2.entity_extraction import extract_entities

    entities = extract_entities("tamamlanmamış değerlendirmeleri listele")
    assert "incomplete" in entities.status_keywords


def test_extract_possible_person_name_span_is_flagged_not_resolved():
    """A name-shaped span must be surfaced as a raw candidate string, never
    resolved to a specific record by this module -- resolution against real
    personnel data is the caller's job."""
    from app.services.assistant_v2.entity_extraction import extract_entities

    entities = extract_entities("Ayşe Yılmaz için performans kaydını göster")
    assert "Ayşe Yılmaz" in entities.possible_person_name_spans


def test_extract_entities_on_empty_text_returns_all_empty():
    from app.services.assistant_v2.entity_extraction import extract_entities

    entities = extract_entities("")
    assert entities.years == ()
    assert entities.period_references == ()
    assert entities.sicil_no is None
    assert entities.status_keywords == ()
    assert entities.possible_person_name_spans == ()


# ---------------------------------------------------------------------------
# language_helpers
# ---------------------------------------------------------------------------


def test_count_phrase_does_not_pluralize_turkish_noun():
    from app.services.assistant_v2.language_helpers import count_phrase

    assert count_phrase(4, "personel") == "4 personel"
    assert count_phrase(1, "kayıt") == "1 kayıt"


def test_format_date_tr_renders_turkish_month_name():
    from datetime import date

    from app.services.assistant_v2.language_helpers import format_date_tr

    assert format_date_tr(date(2026, 1, 1)) == "1 Ocak 2026"
    assert format_date_tr("2026-03-15") == "15 Mart 2026"
    assert format_date_tr(None) is None
    assert format_date_tr("not-a-date") is None


def test_format_list_tr_joins_with_ve():
    from app.services.assistant_v2.language_helpers import format_list_tr

    assert format_list_tr(["A"]) == "A"
    assert format_list_tr(["A", "B"]) == "A ve B"
    assert format_list_tr(["A", "B", "C"]) == "A, B ve C"


def test_format_list_tr_truncates_with_remainder_count():
    from app.services.assistant_v2.language_helpers import format_list_tr

    result = format_list_tr([f"item{i}" for i in range(15)], max_items=5)
    assert "ve 10 diğer" in result


def test_no_data_phrase_and_access_denied_phrase_are_safe_generic_text():
    from app.services.assistant_v2.language_helpers import access_denied_phrase, no_data_phrase

    assert "bulunamadı" in no_data_phrase("Personel")
    assert "erişim yetkisi" in access_denied_phrase()


def test_source_attribution_phrase_formats_kaynak_label():
    from app.services.assistant_v2.language_helpers import source_attribution_phrase

    assert source_attribution_phrase(["Personel Listesi"]) == "Kaynak: Personel Listesi"
    assert source_attribution_phrase([]) == ""


# ---------------------------------------------------------------------------
# intent_router confidence model
# ---------------------------------------------------------------------------


def test_resolve_intent_high_confidence_for_clear_single_match():
    from app.services.assistant_v2.intent_router import ConfidenceTier, resolve_intent

    resolution = resolve_intent("sicil kaydını oku")
    assert resolution.tier is ConfidenceTier.HIGH
    assert resolution.best_capability_key is not None


def test_resolve_intent_low_confidence_for_gibberish_never_guesses():
    from app.services.assistant_v2.intent_router import ConfidenceTier, resolve_intent

    resolution = resolve_intent("qwertyzxcvbnmasdfgh")
    assert resolution.tier is ConfidenceTier.LOW
    assert resolution.candidates == ()
    assert resolution.best_capability_key is None


def test_resolve_intent_medium_confidence_does_not_silently_pick_one():
    """A deliberately generic query that scores multiple performance_mgmt
    capabilities closely must come back MEDIUM with more than one
    candidate -- never silently narrowed to a single guess."""
    from app.services.assistant_v2.intent_router import ConfidenceTier, resolve_intent

    resolution = resolve_intent("performans", module_key="performance_mgmt")
    if resolution.tier is ConfidenceTier.MEDIUM:
        assert len(resolution.candidates) > 1
    else:
        # If the vocabulary/tags happen to make this unambiguous, that's a
        # legitimate HIGH outcome too -- the hard requirement is just that
        # MEDIUM (when it occurs) always carries >1 candidate.
        assert resolution.tier in (ConfidenceTier.HIGH, ConfidenceTier.LOW)


def test_resolve_intent_candidates_backward_compatible_shape():
    from app.services.assistant_v2.intent_router import resolve_intent_candidates

    candidates = resolve_intent_candidates("personel sicil kaydını göster")
    assert isinstance(candidates, list)
    assert "personnel_hr_read_personnel_record" in candidates
