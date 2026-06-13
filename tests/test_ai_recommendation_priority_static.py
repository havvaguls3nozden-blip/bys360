from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_faz9_service_is_read_only():
    service = read("app/services/ai/recommendation_priority.py")
    assert "AI_FINAL_DECISION_ENABLED = False" in service
    assert "AI_AUTO_APPLY_ENABLED = False" in service
    assert "DB_WRITE_ENABLED = False" in service
    assert "db.session.commit" not in service
    assert "db.session.add" not in service


def test_faz9_routes_are_registered_on_main_bp():
    routes = read("app/admin/ai_phase9_routes.py")
    assert "/admin/analysis-center/recommendation-priority" in routes
    assert "/admin/ai-recommendation-priority" in routes
    assert "admin_ai_recommendation_priority_export" in routes


def test_faz9_template_mentions_contract():
    template = read("app/templates/admin_analysis_recommendation_priority.html")
    assert "Salt-okunur" in template
    assert "İnsan onayı" in template
    assert "KVKK" in template
