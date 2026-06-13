from __future__ import annotations

import pytest

pytestmark = [pytest.mark.live, pytest.mark.realdb, pytest.mark.slow]

from pathlib import Path

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
    "SurveyAnswer",
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
