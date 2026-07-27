from __future__ import annotations

from pathlib import Path

# BYS360 Phase 9: pytest.mark.live/realdb/slow removed (2026-07-27) -- all
# three tests below are a static source-contract check (Path.read_text() +
# string-presence assertions against app/communication/surveys_routes.py),
# not a live-service or real-DB integration test; "live" here refers to the
# production/"canlı" route naming being verified, not a runtime dependency.
# No app.* import, DB, network, or subprocess use. The markers predate this
# repo's earliest visible commit with no recorded rationale, and an
# identical mistagging pattern was found on tests/test_live_scope_and_
# security_static.py (fixed in Phase 8) -- both trace to the same baseline
# commit, consistent with a naming-convention-driven mistagging rather than
# an actual runtime requirement.

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SURVEY_ROUTE = PROJECT_ROOT / "app" / "communication" / "surveys_routes.py"

EXPECTED_LIVE_FUNCTIONS = {
    "surveys_list",
    "survey_take",
    "survey_submit",
    "survey_manage",
    "survey_create",
    "survey_edit",
    "survey_publish",
    "survey_unpublish",
    "survey_close",
    "survey_archive",
    "survey_restore",
    "survey_bulk_action",
    "survey_delete",
    "survey_results",
}

EXPECTED_LIVE_KEYWORDS = {
    "Survey",
    "SurveyQuestion",
    "SurveyAssignment",
    "SurveyResponse",
    "_user_matches_assignment",
    "_get_assigned_surveys_for_user",
}


def test_survey_routes_file_exists() -> None:
    assert SURVEY_ROUTE.exists(), "Canlı anket route dosyası bulunamadı."


def test_survey_live_contract_function_names_are_present() -> None:
    source = SURVEY_ROUTE.read_text(encoding="utf-8", errors="replace")
    missing = sorted(name for name in EXPECTED_LIVE_FUNCTIONS if f"def {name}" not in source)
    assert not missing, f"Canlı anket sözleşme fonksiyonları eksik: {missing}"


def test_survey_live_contract_model_keywords_are_present() -> None:
    source = SURVEY_ROUTE.read_text(encoding="utf-8", errors="replace")
    missing = sorted(keyword for keyword in EXPECTED_LIVE_KEYWORDS if keyword not in source)
    assert not missing, f"Canlı anket model/yardımcı anahtarları eksik: {missing}"
