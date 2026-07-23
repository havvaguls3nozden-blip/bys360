"""BYS360 anket servis iskeleti.

Faz 2 canlı koruma kuralı:
- Bu paket eklenir ama `surveys_routes.py` henüz değiştirilmez.
- Fonksiyonlar route içindeki mevcut yardımcıların güvenli taşıma hedefidir.
- Veritabanı ve Flask context gerektiren işler fonksiyon içinde lazy import yapar.
"""
from __future__ import annotations

from .authoring import (
    persist_survey_questions,
    survey_form_state_from_mapping,
    survey_question_attr,
    survey_state_from_db,
)
from .contracts import (
    SurveyAccessResult,
    SurveyMetricSummary,
    SurveyQuestionDraft,
    SurveyTargetDraft,
    as_plain_dict,
)
from .listing import (
    build_survey_state_row,
    get_assigned_surveys_for_user,
    latest_response_for_user,
)
from .metrics import answer_value_to_text, completion_percent, empty_survey_counts, status_counts
from .normalizers import (
    clean_target_values,
    dedup_preserve,
    normalize_choice,
    safe_text,
    split_option_block,
)
from .questions import build_question_payload_dicts, build_question_payloads
from .repository import (
    safe_any_response_count,
    safe_assignment_count,
    safe_completed_response_count,
    safe_question_count,
    safe_question_options,
    safe_survey_questions,
    survey_question_compat_defaults,
)
from .results import (
    build_question_summary_row,
    build_survey_results_context,
    build_survey_results_csv_text,
    latest_completed_label_for_survey,
    safe_question_answers,
    simple_completion_trend,
    summarize_question_for_csv,
)
from .schema import (
    clear_schema_cache,
    has_table_columns,
    survey_question_phase2_ready,
    survey_response_phase2_ready,
    table_columns,
)
from .state import (
    SurveyBulkActionResult,
    SurveyStateResult,
    archive_survey,
    bulk_survey_action,
    close_survey,
    delete_survey_if_allowed,
    publish_survey,
    restore_survey,
    unpublish_survey,
)
from .submission import submit_survey_response
from .submission_contract import (
    SubmissionContractCheck,
    ensure_order,
    evaluate_submission_contract,
    submission_contract_checks,
)
from .targets import (
    active_user_count,
    assigned_survey_assignment_rows_for_user,
    assignment_matches_user_filter,
    build_target_draft,
    distinct_user_values,
    estimate_survey_target_user_ids,
    matching_assignment_for_user,
    resolve_target_user_ids,
    selected_user_items,
    selected_user_items_by_ids,
    target_user_search_items,
    user_item,
)
from .time_utils import format_survey_dt, survey_access_state, survey_local_now

__all__ = [
    "SurveyBulkActionResult",
    "SurveyStateResult",
    "archive_survey",
    "bulk_survey_action",
    "close_survey",
    "delete_survey_if_allowed",
    "publish_survey",
    "restore_survey",
    "unpublish_survey",
    "submission_contract_checks",
    "evaluate_submission_contract",
    "ensure_order",
    "SubmissionContractCheck",
    "submit_survey_response",
    "persist_survey_questions",
    "survey_form_state_from_mapping",
    "survey_question_attr",
    "survey_state_from_db",
    "build_survey_state_row",
    "get_assigned_surveys_for_user",
    "latest_response_for_user",
    "table_columns",
    "has_table_columns",
    "survey_response_phase2_ready",
    "survey_question_phase2_ready",
    "clear_schema_cache",
    "SurveyAccessResult",
    "SurveyMetricSummary",
    "SurveyQuestionDraft",
    "SurveyTargetDraft",
    "active_user_count",
    "assigned_survey_assignment_rows_for_user",
    "assignment_matches_user_filter",
    "matching_assignment_for_user",
    "distinct_user_values",
    "estimate_survey_target_user_ids",
    "resolve_target_user_ids",
    "selected_user_items_by_ids",
    "target_user_search_items",
    "answer_value_to_text",
    "as_plain_dict",
    "build_question_payload_dicts",
    "build_question_payloads",
    "build_target_draft",
    "clean_target_values",
    "completion_percent",
    "dedup_preserve",
    "empty_survey_counts",
    "format_survey_dt",
    "normalize_choice",
    "build_question_summary_row",
    "build_survey_results_context",
    "build_survey_results_csv_text",
    "latest_completed_label_for_survey",
    "safe_question_answers",
    "simple_completion_trend",
    "summarize_question_for_csv",
    "safe_any_response_count",
    "safe_assignment_count",
    "safe_completed_response_count",
    "safe_question_count",
    "safe_question_options",
    "safe_survey_questions",
    "survey_question_compat_defaults",
    "safe_text",
    "selected_user_items",
    "split_option_block",
    "status_counts",
    "survey_access_state",
    "survey_local_now",
    "user_item",
]
