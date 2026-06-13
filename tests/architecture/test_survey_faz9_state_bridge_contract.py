from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_survey_state_service_exports_required_functions():
    text = (ROOT / "app/services/surveys/state.py").read_text(encoding="utf-8")
    for name in [
        "publish_survey",
        "unpublish_survey",
        "close_survey",
        "archive_survey",
        "restore_survey",
        "bulk_survey_action",
        "delete_survey_if_allowed",
    ]:
        assert f"def {name}" in text


def test_survey_routes_use_state_service_bridge():
    text = (ROOT / "app/communication/surveys_routes.py").read_text(encoding="utf-8")
    for marker in [
        "_service_publish_survey(",
        "_service_unpublish_survey(",
        "_service_close_survey(",
        "_service_archive_survey(",
        "_service_restore_survey(",
        "_service_bulk_survey_action(",
        "_service_delete_survey_if_allowed(",
    ]:
        assert marker in text


def test_survey_state_service_keeps_response_delete_guards():
    text = (ROOT / "app/services/surveys/state.py").read_text(encoding="utf-8")
    assert "safe_completed_response_count" in text
    assert "safe_any_response_count" in text
    assert "Yanıt almış anket kalıcı olarak silinemez" in text
