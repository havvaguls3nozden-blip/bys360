from __future__ import annotations

from app.services.module_maturity import build_module_maturity_report


def test_module_maturity_report_has_live_core_modules():
    report = build_module_maturity_report()
    labels = {module["key"] for module in report["modules"]}
    assert {"security", "performance", "hr", "communication", "operations"}.issubset(labels)
    assert report["overall_score"] >= 8.0


def test_module_maturity_uses_redis_and_http_quality_signals():
    report = build_module_maturity_report()
    flat = [check for module in report["modules"] for check in module["checks"]]
    assert any(check["label"] == "Paylaşımlı rate-limit" and check["ok"] for check in flat)
    assert any(check["label"] == "HTTP entegrasyon testi" and check["ok"] for check in flat)
