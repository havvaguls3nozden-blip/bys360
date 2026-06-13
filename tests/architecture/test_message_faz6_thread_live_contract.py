from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_message_faz6_thread_detail_service_exists():
    source = (ROOT / "app/services/messages/thread_detail.py").read_text(encoding="utf-8")
    assert "def load_thread_detail_payload" in source
    assert "def build_thread_activity_payload" in source
    assert "def build_thread_live_payload" in source


def test_message_faz6_routes_use_service_bridge():
    source = (ROOT / "app/communication/messages_routes.py").read_text(encoding="utf-8")
    assert "_svc_load_thread_detail_payload" in source
    assert "_svc_build_thread_activity_payload" in source
    assert "_svc_build_thread_live_payload" in source


def test_message_faz6_exports_are_public():
    source = (ROOT / "app/services/messages/__init__.py").read_text(encoding="utf-8")
    assert "build_thread_activity_payload" in source
    assert "build_thread_live_payload" in source
    assert "load_thread_detail_payload" in source
