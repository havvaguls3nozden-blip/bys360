from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTE = ROOT / "app" / "communication" / "messages_routes.py"
SERVICE = ROOT / "app" / "services" / "messages" / "serialization.py"


def test_message_routes_use_service_bridge_for_low_risk_helpers():
    text = ROUTE.read_text(encoding="utf-8")
    assert "from app.services.messages import (" in text
    assert "return _svc_format_dt_label(value)" in text
    assert "return _svc_build_reaction_map(messages)" in text
    assert "return _svc_build_thread_presence(thread, participants, _utcnow())" in text
    assert "return _svc_serialize_message(message, reaction_map=reaction_map)" in text


def test_message_live_write_flows_remain_in_route_in_phase3():
    text = ROUTE.read_text(encoding="utf-8")
    for fn in [
        "def messages_send_impl",
        "def messages_edit_impl",
        "def messages_delete_impl",
        "def messages_react_impl",
        "def messages_thread_typing_impl",
    ]:
        assert fn in text


def test_message_serialization_payload_keeps_mobile_contract():
    text = SERVICE.read_text(encoding="utf-8")
    for key in [
        '"stored_filename"',
        '"download_url"',
        '"preview_url"',
        '"body_is_placeholder"',
        '"reaction_options"',
    ]:
        assert key in text
