from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTES = ROOT / "app" / "communication" / "surveys_routes.py"
SERVICE = ROOT / "app" / "services" / "surveys" / "submission.py"
INIT = ROOT / "app" / "services" / "surveys" / "__init__.py"


def test_survey_submit_uses_submission_service_bridge():
    text = ROUTES.read_text(encoding="utf-8")
    assert "submit_survey_response as _service_submit_survey_response" in text
    assert "_service_submit_survey_response(" in text


def test_route_keeps_token_before_service_write():
    text = ROUTES.read_text(encoding="utf-8")
    submit = text[text.find("def survey_submit(survey_id):"):]
    assert submit.find('consume_form_token("survey_submit"') < submit.find("_service_submit_survey_response(")


def test_inline_answer_write_removed_from_route_submit():
    text = ROUTES.read_text(encoding="utf-8")
    submit = text[text.find("def survey_submit(survey_id):"):]
    assert "db.session.add(SurveyAnswer" not in submit
    assert "SurveyAnswer(" not in submit


def test_submission_service_owns_response_and_answer_write():
    text = SERVICE.read_text(encoding="utf-8")
    assert "def submit_survey_response(" in text
    assert "SurveyResponse(" in text
    assert "SurveyAnswer" in text
    assert "session.flush()" in text
    assert "session.commit()" in text


def test_package_exports_submission_bridge():
    text = INIT.read_text(encoding="utf-8")
    assert "from .submission import submit_survey_response" in text
    assert '"submit_survey_response"' in text
