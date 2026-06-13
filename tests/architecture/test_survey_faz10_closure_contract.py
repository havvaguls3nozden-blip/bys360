from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _function_names(source: str) -> set[str]:
    tree = ast.parse(source)
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}


def test_survey_route_contract_is_still_present():
    names = _function_names(_source("app/communication/surveys_routes.py"))
    for required in {
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
    }:
        assert required in names


def test_survey_service_exports_faz10_helpers():
    source = _source("app/services/surveys/__init__.py")
    for required in {
        "persist_survey_questions",
        "survey_form_state_from_mapping",
        "survey_state_from_db",
        "get_assigned_surveys_for_user",
        "latest_response_for_user",
        "survey_question_phase2_ready",
        "survey_response_phase2_ready",
    }:
        assert required in source


def test_survey_route_is_below_closure_budget():
    line_count = len(_source("app/communication/surveys_routes.py").splitlines())
    assert line_count <= 1200
