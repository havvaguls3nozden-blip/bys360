from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTE = ROOT / "app" / "communication" / "messages_routes.py"
STATE = ROOT / "app" / "services" / "messages" / "state.py"
INIT = ROOT / "app" / "services" / "messages" / "__init__.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_faz8_state_service_functions_exist():
    state = _read(STATE)
    for fn in [
        "mark_thread_read_for_user",
        "toggle_thread_mute_for_user",
        "toggle_thread_archive_for_user",
        "toggle_thread_pin_for_user",
    ]:
        assert f"def {fn}" in state


def test_faz8_state_functions_exported():
    init = _read(INIT)
    for fn in [
        "mark_thread_read_for_user",
        "toggle_thread_mute_for_user",
        "toggle_thread_archive_for_user",
        "toggle_thread_pin_for_user",
    ]:
        assert fn in init


def test_faz8_routes_use_state_services():
    route = _read(ROUTE)
    assert "_svc_mark_thread_read_for_user" in route
    assert "_svc_toggle_thread_mute_for_user" in route
    assert "_svc_toggle_thread_archive_for_user" in route
    assert "_svc_toggle_thread_pin_for_user" in route


def test_faz8_critical_write_routes_still_exist():
    route = _read(ROUTE)
    for marker in [
        "def messages_send_impl",
        "def messages_new_impl",
        "def messages_edit_impl",
        "def messages_delete_impl",
    ]:
        assert marker in route
