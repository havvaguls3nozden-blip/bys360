from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTES = ROOT / "app" / "communication" / "surveys_routes.py"
RESULTS = ROOT / "app" / "services" / "surveys" / "results.py"
INIT = ROOT / "app" / "services" / "surveys" / "__init__.py"


def _function_block(source: str, name: str) -> str:
    tree = ast.parse(source)
    lines = source.splitlines()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return "\n".join(lines[node.lineno - 1 : node.end_lineno])
    raise AssertionError(f"Fonksiyon bulunamadı: {name}")


def test_results_service_functions_exist():
    text = RESULTS.read_text(encoding="utf-8")
    funcs = {node.name for node in ast.walk(ast.parse(text)) if isinstance(node, ast.FunctionDef)}
    expected = {
        "safe_question_answers",
        "latest_completed_label_for_survey",
        "simple_completion_trend",
        "build_question_summary_row",
        "summarize_question_for_csv",
        "build_survey_results_csv_text",
        "build_survey_results_context",
    }
    assert expected.issubset(funcs)


def test_results_service_is_exported():
    text = INIT.read_text(encoding="utf-8")
    assert "build_survey_results_context" in text
    assert "build_survey_results_csv_text" in text
    assert "safe_question_answers" in text


def test_routes_use_results_service_bridge():
    text = ROUTES.read_text(encoding="utf-8")
    assert "_service_build_survey_results_context" in text
    assert "_service_build_survey_results_csv_text" in text
    assert "_service_safe_question_answers" in text


def test_survey_results_route_is_thin():
    text = ROUTES.read_text(encoding="utf-8")
    block = _function_block(text, "survey_results")
    assert "_service_build_survey_results_context" in block
    assert "rating_averages" not in block
    assert "option_stats" not in block


def test_csv_export_route_is_thin():
    text = ROUTES.read_text(encoding="utf-8")
    block = _function_block(text, "survey_results_export_csv")
    assert "_service_build_survey_results_csv_text" in block
    assert "csv.writer" not in block
    assert "SurveyAnswer" not in block
