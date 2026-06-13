from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ROUTE_FILE = PROJECT_ROOT / "app" / "communication" / "messages_routes.py"
SERVICE_FILE = PROJECT_ROOT / "app" / "services" / "message_service.py"

EXPECTED_ENDPOINTS = {
    "messages_inbox": "/messages",
    "messages_new": "/messages/new",
    "messages_thread": "/messages/thread/<int:thread_id>",
    "messages_thread_activity": "/messages/thread/<int:thread_id>/activity",
    "messages_thread_live": "/messages/thread/<int:thread_id>/live",
    "messages_thread_typing": "/messages/thread/<int:thread_id>/typing",
    "messages_react": "/messages/<int:message_id>/react",
    "messages_send": "/messages/thread/<int:thread_id>/send",
    "messages_mark_read": "/messages/thread/<int:thread_id>/mark-read",
    "messages_toggle_mute": "/messages/thread/<int:thread_id>/mute-toggle",
    "messages_toggle_archive": "/messages/thread/<int:thread_id>/archive-toggle",
    "messages_toggle_pin": "/messages/thread/<int:thread_id>/pin-toggle",
    "messages_edit": "/messages/<int:message_id>/edit",
    "messages_delete": "/messages/<int:message_id>/delete",
    "message_attachment_download": "/messages/attachments/<filename>",
}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _decorated_block(text: str, function_name: str) -> str:
    pattern = re.compile(rf"((?:^@[^\n]+\n)+def\s+{re.escape(function_name)}\s*\([^\n]*\):.*?)(?=^@main_bp\.route|\Z)", re.M | re.S)
    match = pattern.search(text)
    return match.group(1) if match else ""


def _function_block(text: str, function_name: str) -> str:
    pattern = re.compile(rf"(^def\s+{re.escape(function_name)}\s*\([^\n]*\):.*?)(?=^def\s+|^@main_bp\.route|\Z)", re.M | re.S)
    match = pattern.search(text)
    return match.group(1) if match else ""


def test_message_route_file_exists():
    assert ROUTE_FILE.exists(), "messages_routes.py bulunmalı"


def test_message_live_endpoints_keep_guards():
    text = _read(ROUTE_FILE)
    for function_name, url in EXPECTED_ENDPOINTS.items():
        block = _decorated_block(text, function_name)
        assert block, f"{function_name} endpoint wrapper eksik"
        assert url in block, f"{function_name} URL sözleşmesi bozuldu"
        assert "@login_required" in block, f"{function_name} login_required içermeli"
        assert '@menu_key_required("messages")' in block, f"{function_name} messages menü yetkisi içermeli"
        assert f"return {function_name}_impl" in block, f"{function_name} impl fonksiyonuna delegasyon yapmalı"


def test_message_write_impls_are_present_for_future_refactor():
    text = _read(ROUTE_FILE)
    for function_name in [
        "messages_send_impl",
        "messages_react_impl",
        "messages_thread_typing_impl",
        "messages_mark_read_impl",
        "messages_toggle_mute_impl",
        "messages_toggle_archive_impl",
        "messages_toggle_pin_impl",
        "messages_edit_impl",
        "messages_delete_impl",
    ]:
        block = _function_block(text, function_name)
        assert block, f"{function_name} eksik"
        assert "return" in block, f"{function_name} route davranışı dönmeli"


def test_message_db_writes_do_not_skip_basic_safety_keywords():
    text = _read(ROUTE_FILE)
    for function_name in ["messages_send_impl", "messages_edit_impl", "messages_delete_impl"]:
        block = _function_block(text, function_name)
        assert "db.session.commit" in block, f"{function_name} commit sözleşmesi korunmalı"
        assert "db.session.rollback" in block, f"{function_name} rollback sözleşmesi korunmalı"


def test_message_send_attachment_and_notification_contract():
    text = _read(ROUTE_FILE)
    block = _function_block(text, "messages_send_impl")
    assert "_normalize_incoming_message_files" in block
    assert "_save_message_attachment" in block
    assert "_notify_user" in block


def test_message_service_file_security_symbols_exist():
    text = _read(SERVICE_FILE)
    for symbol in [
        "ALLOWED_MESSAGE_FILE_EXTENSIONS",
        "MAX_MESSAGE_FILE_SIZE",
        "MAX_MESSAGE_TOTAL_SIZE",
        "MAX_MESSAGE_ATTACHMENTS",
        "normalize_incoming_message_files",
        "save_message_attachment",
        "get_message_attachment_for_user",
        "resolve_message_attachment_download",
    ]:
        assert symbol in text, f"message_service dosya güvenliği sözleşmesi eksik: {symbol}"
