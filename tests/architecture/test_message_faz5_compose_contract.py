from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTES = ROOT / "app" / "communication" / "messages_routes.py"
COMPOSE = ROOT / "app" / "services" / "messages" / "compose.py"
INIT = ROOT / "app" / "services" / "messages" / "__init__.py"


def test_compose_service_exports_expected_helpers():
    compose = COMPOSE.read_text(encoding="utf-8")
    init = INIT.read_text(encoding="utf-8")
    for name in [
        "load_active_compose_users",
        "load_all_active_compose_users",
        "build_recent_message_users_for_compose",
        "build_compose_user_cards",
        "resolve_active_recipient",
        "sort_compose_users",
    ]:
        assert f"def {name}" in compose
        assert name in init


def test_routes_use_compose_service_bridge():
    routes = ROUTES.read_text(encoding="utf-8")
    assert "_svc_load_active_compose_users" in routes
    assert "_svc_load_all_active_compose_users" in routes
    assert "_svc_build_recent_message_users_for_compose" in routes
    assert "_svc_build_compose_user_cards" in routes
    assert "def _build_recent_message_users_for_compose" not in routes
    assert "def _build_compose_user_cards" not in routes


def test_compose_service_does_not_take_over_send_writes():
    compose = COMPOSE.read_text(encoding="utf-8")
    for forbidden in [
        "db.session.add",
        "db.session.commit",
        "db.session.rollback",
        "db.session.flush",
        "save_message_attachment",
        "notify_user",
        "Message(",
    ]:
        assert forbidden not in compose


def test_live_send_routes_remain_present():
    routes = ROUTES.read_text(encoding="utf-8")
    assert "def messages_new_impl" in routes
    assert "def messages_send_impl" in routes
    assert "consume_form_token" in routes
