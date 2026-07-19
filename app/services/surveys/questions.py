"""Anket soru taslağı oluşturma yardımcıları."""
from __future__ import annotations

from typing import Any
from collections.abc import Iterable

from .contracts import SurveyQuestionDraft
from .normalizers import (
    SURVEY_ALLOWED_LOGIC_MODES,
    SURVEY_ALLOWED_LOGIC_OPERATORS,
    SURVEY_ALLOWED_QUESTION_TYPES,
    dedup_preserve,
    normalize_choice,
    safe_text,
)


def _list(values: Iterable[Any] | None) -> list[Any]:
    return list(values or [])


def _at(values: list[Any], index: int, default: Any = "") -> Any:
    return values[index] if index < len(values) else default


def _checked(value: Any) -> bool:
    return str(value or "").strip() == "1"


def build_question_payload_dicts(
    *,
    question_texts: Iterable[Any] | None,
    question_types: Iterable[Any] | None = None,
    question_requireds: Iterable[Any] | None = None,
    option_blocks: Iterable[Any] | None = None,
    helper_texts: Iterable[Any] | None = None,
    logic_modes: Iterable[Any] | None = None,
    logic_sources: Iterable[Any] | None = None,
    logic_operators: Iterable[Any] | None = None,
    logic_values: Iterable[Any] | None = None,
) -> list[dict[str, Any]]:
    """Canlı route'taki eski `_survey_build_question_payloads` davranışının aynısı.

    Veritabanına yazmaz; sadece form dizilerini doğrular ve sözlük payload üretir.
    Bu fonksiyonun hata mesajları canlı kullanıcı deneyimi bozulmasın diye eski
    route fonksiyonuyla aynı tutulmuştur.
    """
    texts = _list(question_texts)
    types = _list(question_types)
    requireds = _list(question_requireds)
    options_blocks = _list(option_blocks)
    helpers = _list(helper_texts)
    modes = _list(logic_modes)
    sources = _list(logic_sources)
    operators = _list(logic_operators)
    values = _list(logic_values)

    payloads: list[dict[str, Any]] = []
    max_len = max(
        len(texts),
        len(types),
        len(requireds),
        len(options_blocks),
        len(helpers),
        len(modes),
        len(sources),
        len(operators),
        len(values),
        0,
    )

    for idx in range(max_len):
        qtext = safe_text(_at(texts, idx, ""))
        qtype = normalize_choice(safe_text(_at(types, idx, "text")), SURVEY_ALLOWED_QUESTION_TYPES, "text")
        qreq = safe_text(_at(requireds, idx, "1"))
        raw_options = safe_text(_at(options_blocks, idx, ""))
        helper_text = safe_text(_at(helpers, idx, ""))
        logic_mode = normalize_choice(safe_text(_at(modes, idx, "always")), SURVEY_ALLOWED_LOGIC_MODES, "always")
        logic_source_raw = safe_text(_at(sources, idx, ""))
        logic_operator = normalize_choice(safe_text(_at(operators, idx, "answered")), SURVEY_ALLOWED_LOGIC_OPERATORS, "answered")
        logic_value = safe_text(_at(values, idx, ""))

        is_blank_card = (
            not qtext
            and not raw_options
            and qtype == "text"
            and not helper_text
            and logic_mode == "always"
            and not logic_source_raw
            and not logic_value
        )
        if is_blank_card:
            continue

        row_no = len(payloads) + 1
        if not qtext:
            raise ValueError(f"{row_no}. sorunun metni boş bırakılamaz.")
        if len(qtext) > 5000:
            raise ValueError(f"{row_no}. soru metni çok uzun. Lütfen daha kısa yazın.")
        if helper_text and len(helper_text) > 500:
            helper_text = helper_text[:500]

        options: list[str] = []
        if qtype == "yes_no":
            options = ["Evet", "Hayır"]
        elif qtype in {"single_choice", "multiple_choice"}:
            options = dedup_preserve(raw_options.splitlines())
            if len(options) < 2:
                raise ValueError(f'"{qtext}" sorusu için en az iki seçenek girilmelidir.')
        for opt in options:
            if len(opt) > 255:
                raise ValueError(f'"{qtext}" sorusundaki seçeneklerden biri çok uzun.')

        logic_source_sort_order = None
        if logic_mode == "conditional":
            if not logic_source_raw.isdigit() or int(logic_source_raw) <= 0:
                raise ValueError(f'"{qtext}" sorusunda koşul kaynağı olarak geçerli bir önceki soru numarası girilmelidir.')
            logic_source_sort_order = int(logic_source_raw)
            if logic_operator != "answered" and not logic_value:
                raise ValueError(f'"{qtext}" sorusunda seçilen koşul operatörü için koşul değeri zorunludur.')
        else:
            logic_operator = "answered"
            logic_value = ""

        payloads.append(
            {
                "question_text": qtext,
                "question_type": qtype,
                "is_required": _checked(qreq),
                "sort_order": row_no,
                "options": options,
                "helper_text": helper_text,
                "logic_mode": logic_mode,
                "logic_source_sort_order": logic_source_sort_order,
                "logic_operator": logic_operator,
                "logic_value": logic_value,
            }
        )

    if not payloads:
        raise ValueError("En az bir soru girilmelidir.")

    total_questions = len(payloads)
    for item in payloads:
        source_order = item.get("logic_source_sort_order")
        if not source_order:
            continue
        if source_order >= int(item["sort_order"]):
            raise ValueError(f'"{item["question_text"]}" sorusunda koşul kaynağı yalnızca önceki sorulardan biri olabilir.')
        if source_order > total_questions:
            raise ValueError(f'"{item["question_text"]}" sorusunda belirtilen koşul kaynağı mevcut değil.')
    return payloads


def build_question_payloads(
    *,
    question_texts: Iterable[Any] | None,
    question_types: Iterable[Any] | None = None,
    question_requireds: Iterable[Any] | None = None,
    option_blocks: Iterable[Any] | None = None,
    helper_texts: Iterable[Any] | None = None,
    logic_modes: Iterable[Any] | None = None,
    logic_sources: Iterable[Any] | None = None,
    logic_operators: Iterable[Any] | None = None,
    logic_values: Iterable[Any] | None = None,
) -> list[SurveyQuestionDraft]:
    """Dataclass çıktısı isteyen yeni kodlar için ince uyumluluk katmanı."""
    rows = build_question_payload_dicts(
        question_texts=question_texts,
        question_types=question_types,
        question_requireds=question_requireds,
        option_blocks=option_blocks,
        helper_texts=helper_texts,
        logic_modes=logic_modes,
        logic_sources=logic_sources,
        logic_operators=logic_operators,
        logic_values=logic_values,
    )
    return [
        SurveyQuestionDraft(
            question_text=str(row["question_text"]),
            question_type=str(row["question_type"]),
            is_required=bool(row["is_required"]),
            sort_order=int(row["sort_order"]),
            options=list(row.get("options") or []),
            helper_text=str(row.get("helper_text") or ""),
            logic_mode=str(row.get("logic_mode") or "always"),
            logic_source_question_id=row.get("logic_source_sort_order"),
            logic_operator=str(row.get("logic_operator") or "answered"),
            logic_value=str(row.get("logic_value") or ""),
        )
        for row in rows
    ]
