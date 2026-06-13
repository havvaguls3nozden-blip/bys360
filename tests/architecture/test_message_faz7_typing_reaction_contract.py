from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTE = ROOT / "app" / "communication" / "messages_routes.py"
SERVICE_INIT = ROOT / "app" / "services" / "messages" / "__init__.py"
TYPING = ROOT / "app" / "services" / "messages" / "typing.py"
REACTIONS = ROOT / "app" / "services" / "messages" / "reactions.py"


def test_message_faz7_service_files_exist():
    assert TYPING.exists()
    assert REACTIONS.exists()


def test_message_faz7_route_uses_service_bridge():
    text = ROUTE.read_text(encoding="utf-8")
    assert "_svc_update_thread_typing_state(" in text
    assert "_svc_toggle_message_reaction(" in text
    assert "MessageTypingState.query.filter_by(thread_id=thread_id" not in text
    assert "MessageReaction.query.filter_by(message_id=message.id" not in text


def test_message_faz7_exports_service_functions():
    text = SERVICE_INIT.read_text(encoding="utf-8")
    assert "update_thread_typing_state" in text
    assert "toggle_message_reaction" in text


def test_message_faz7_typing_contract_guards():
    text = TYPING.read_text(encoding="utf-8")
    assert "normalize_typing_flag" in text
    assert "participant_for_thread" in text
    assert "thread_type" in text
    assert "db.session.rollback()" in text


def test_message_faz7_reaction_contract_guards():
    text = REACTIONS.read_text(encoding="utf-8")
    assert "REACTION_OPTIONS" in text
    assert "participant_for_thread" in text
    assert "build_reaction_map([message])" in text
    assert "db.session.rollback()" in text
