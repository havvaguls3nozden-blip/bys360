from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTES = ROOT / "app" / "communication" / "messages_routes.py"
SERVICE_INIT = ROOT / "app" / "services" / "messages" / "__init__.py"
LIFECYCLE = ROOT / "app" / "services" / "messages" / "lifecycle.py"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_message_lifecycle_service_exists_and_exports_contract():
    lifecycle = read(LIFECYCLE)
    init_text = read(SERVICE_INIT)
    for token in [
        "def edit_message_for_user",
        "def delete_message_for_user",
        "def resolve_message_attachment_download_for_user",
        "MessageMutationResult",
        "MessageAttachmentDownloadResult",
    ]:
        assert token in lifecycle or token in init_text


def test_message_routes_use_lifecycle_service_bridge():
    text = read(ROUTES)
    assert "edit_message_for_user as _svc_edit_message_for_user" in text
    assert "delete_message_for_user as _svc_delete_message_for_user" in text
    assert "resolve_message_attachment_download_for_user as _svc_resolve_message_attachment_download_for_user" in text


def test_message_routes_no_longer_hold_direct_edit_delete_db_mutation():
    text = read(ROUTES)
    for forbidden in [
        "message.body = new_body",
        "message.is_deleted = True",
        "message.body = \"[silindi]\"",
    ]:
        assert forbidden not in text


def test_message_live_endpoints_are_preserved():
    text = read(ROUTES)
    for endpoint in [
        '@main_bp.route("/messages/<int:message_id>/edit", methods=["POST"])',
        '@main_bp.route("/messages/<int:message_id>/delete", methods=["POST"])',
        '@main_bp.route("/messages/attachments/<filename>")',
    ]:
        assert endpoint in text


def test_message_route_is_below_refactor_line_budget():
    assert len(read(ROUTES).splitlines()) <= 750
