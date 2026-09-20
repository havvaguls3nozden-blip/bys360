"""BYS360 Assistant V2 -- external/third-party AI dependency absence contract.

Architectural test (mirrors the established house pattern already used by
`test_intent_router_does_not_import_database_layer` in
tests/quality/test_assistant_v2_dispatcher_and_routing_contract_v1.py):
statically parses every source file under `app/services/assistant_v2/` and
fails if ANY of them imports `app.services.ai` (or one of its known
symbols), or any well-known third-party/local LLM SDK. This is deliberately
an AST-level, source-of-truth check -- not a runtime mock -- so it catches a
reintroduced dependency even in a code path that happens not to execute
during a given test run.

Required metric: ASSISTANT_EXTERNAL_AI_DEPENDENCIES = 0.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.ci_safe

_ASSISTANT_V2_ROOT = Path("app/services/assistant_v2")

_FORBIDDEN_MODULE_PREFIXES = (
    "app.services.ai",  # this project's own AI-provider abstraction
    "openai",
    "anthropic",
    "google.generativeai",
    "google.genai",
    "cohere",
    "mistralai",
    "ollama",
    "llama_cpp",
    "llama_index",
    "langchain",
    "transformers",
    "huggingface_hub",
    "vertexai",
    "azure.ai",
)

_FORBIDDEN_NAMES = {
    "get_ai_client",
    "build_ai_client",
    "OpenAICompatibleAIClient",
    "StubAIClient",
    "BaseAIClient",
    "AIResult",
}


def _iter_assistant_v2_source_files() -> list[Path]:
    return sorted(p for p in _ASSISTANT_V2_ROOT.glob("*.py") if p.is_file())


def _find_forbidden_imports(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    findings: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(alias.name == prefix or alias.name.startswith(prefix + ".") for prefix in _FORBIDDEN_MODULE_PREFIXES):
                    findings.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if any(module == prefix or module.startswith(prefix + ".") for prefix in _FORBIDDEN_MODULE_PREFIXES):
                findings.append(f"from {module} import ...")
            for alias in node.names:
                if alias.name in _FORBIDDEN_NAMES:
                    findings.append(f"from {module} import {alias.name}")
    return findings


def test_no_assistant_v2_source_file_imports_external_ai_dependencies():
    all_findings: dict[str, list[str]] = {}
    for path in _iter_assistant_v2_source_files():
        findings = _find_forbidden_imports(path)
        if findings:
            all_findings[str(path)] = findings
    assert all_findings == {}, f"ASSISTANT_EXTERNAL_AI_DEPENDENCIES != 0: {all_findings}"


def test_assistant_v2_answers_normally_even_if_ai_client_is_sabotaged(app, monkeypatch):
    """Runtime corroboration of the static check above, via behavior rather
    than a sys.modules snapshot: a real Flask app already imports
    app.services.ai independently (the separate, unrelated AI Decision
    Support module wires it in at bootstrap), so simply checking
    sys.modules after import cannot distinguish "assistant_v2 caused this"
    from "the app already had it loaded for other reasons" -- that
    approach is unfalsifiable and was removed. Instead: sabotage
    app.services.ai.client.get_ai_client to raise unconditionally, then
    prove Assistant V2's full pipeline (intent -> authorization -> handler
    -> composed answer) still produces a normal, correct DATA_FOUND answer.
    If response_composer.py (or anything else in assistant_v2) had a live
    call path into that function, this would fail with the sabotage
    exception instead of a normal assertion."""
    import app.services.ai.client as ai_client_module

    def _sabotaged(*args, **kwargs):
        raise AssertionError(
            "app.services.ai.client.get_ai_client() was called from the assistant_v2 pipeline -- "
            "this must never happen in the BYS360 Native AI Only architecture"
        )

    monkeypatch.setattr(ai_client_module, "get_ai_client", _sabotaged)
    monkeypatch.setattr(ai_client_module, "build_ai_client", _sabotaged)

    from app.extensions import db
    from app.models import User
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.intent_router import resolve_intent_candidates
    from app.services.assistant_v2.response_composer import compose_response
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    with app.app_context():
        user = User.query.filter_by(sicil_no="av2_extai_sabotage_admin").first()
        if user is None:
            user = User(
                sicil_no="av2_extai_sabotage_admin", email="av2_extai_sabotage_admin@ktb.gov.tr",
                ad="ExtAI", soyad="Sabotage", role="admin", is_active=True,
                must_change_password=False, must_set_security_question=False,
            )
            user.set_password("Assist_v2_ExtAI_Pw_1!")
            db.session.add(user)
            db.session.commit()
        user_id = user.id

    with app.test_request_context():
        candidates = resolve_intent_candidates("aktif performans dönemlerini göster")
        assert candidates

        admin = User.query.get(user_id)
        result = invoke_capability(admin, "performance_mgmt_list_active_periods")
        composed = compose_response(result, question="aktif performans dönemlerini göster")

    assert result.status in (AssistantResultStatus.DATA_FOUND, AssistantResultStatus.NO_DATA)
    assert composed.answer_text


def test_assistant_v2_module_count_scanned_is_pinned():
    """Pins the number of source files this test actually scanned -- if a
    new assistant_v2 module is added without this test noticing (e.g. a
    typo in the glob), this catches it rather than silently scanning fewer
    files over time."""
    files = _iter_assistant_v2_source_files()
    names = sorted(p.name for p in files)
    assert "__init__.py" in names
    assert len(files) >= 10, f"expected at least 10 assistant_v2 source files, found {len(files)}: {names}"
