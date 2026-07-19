"""
BYS360 AI Karar Destek Faz 12 final gate entegrasyonu.

BYS360_AI_DECISION_FAZ12_INTEGRATION_OK
"""
from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from app.services.ai_decision.final_gate_policy import build_final_report


def get_ai_decision_final_gate_report(project_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(project_root) if project_root else Path.cwd()
    return build_final_report(root)


def write_ai_decision_final_gate_report(project_root: str | Path | None = None) -> dict[str, Any]:
    root = Path(project_root) if project_root else Path.cwd()
    report = build_final_report(root)
    report_dir = root / "reports" / "ai_decision_faz12"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / "ai_decision_faz12_final_gate.json"
    report_file.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report
