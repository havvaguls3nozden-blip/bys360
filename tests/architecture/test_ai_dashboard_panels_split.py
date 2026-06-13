from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AI_DIR = ROOT / "app" / "services" / "ai"


def test_dashboard_panels_facade_is_thin():
    facade = AI_DIR / "dashboard_panels.py"
    assert facade.exists()
    assert facade.read_text(encoding="utf-8").count("\n") < 140


def test_dashboard_panel_parts_are_not_monoliths():
    parts = sorted(AI_DIR.glob("dashboard_panel_*.py"))
    assert parts, "AI panel parçaları bulunamadı"
    oversized = []
    for path in parts:
        lines = path.read_text(encoding="utf-8").count("\n") + 1
        if lines > 1250:
            oversized.append((path.name, lines))
    assert not oversized, f"Büyük AI panel dosyaları kaldı: {oversized}"


def test_dashboard_panels_public_exports_exist():
    facade_text = (AI_DIR / "dashboard_panels.py").read_text(encoding="utf-8")
    for public_name in [
        "build_dashboard_ai_panel",
        "build_management_ai_panel",
        "build_message_inbox_ai_panel",
        "build_hr_leave_ai_panel",
        "build_repository_dashboard_ai_panel",
    ]:
        assert public_name in facade_text
