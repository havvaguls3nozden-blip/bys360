from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTE = ROOT / "app" / "communication" / "messages_routes.py"
SERVICE = ROOT / "app" / "services" / "messages" / "sending.py"
INIT = ROOT / "app" / "services" / "messages" / "__init__.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_message_send_service_exists():
    content = _read(SERVICE)
    assert "MessageSendResult" in content
    assert "create_direct_message_with_attachments" in content
    assert "append_thread_message_with_attachments" in content
    assert "resolve_thread_for_sending" in content


def test_send_service_handles_commit_rollback_and_attachment_cleanup():
    content = _read(SERVICE)
    assert "db.session.commit()" in content
    assert "db.session.rollback()" in content
    assert "remove_message_attachment_file" in content
    assert "save_message_attachment" in content


def test_route_uses_send_service_bridge_without_losing_tokens():
    content = _read(ROUTE)
    assert "_svc_create_direct_message_with_attachments" in content
    assert "_svc_append_thread_message_with_attachments" in content
    assert 'consume_form_token("messages_new"' in content
    assert 'consume_form_token("messages_send"' in content
    assert "next_form_token" in content


def test_service_exports_are_public():
    content = _read(INIT)
    assert "create_direct_message_with_attachments" in content
    assert "append_thread_message_with_attachments" in content
    assert "resolve_thread_for_sending" in content
