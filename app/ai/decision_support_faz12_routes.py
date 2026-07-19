"""
BYS360 AI Karar Destek Faz 12 route'ları.

BYS360_AI_DECISION_FAZ12_ROUTES_OK
"""
from __future__ import annotations

from pathlib import Path
from flask import Blueprint, jsonify, render_template

from app.services.ai_decision.final_gate_integration import get_ai_decision_final_gate_report

ai_decision_faz12_bp = Blueprint(
    "ai_decision_faz12",
    __name__,
    url_prefix="/ai/decision-support/faz12",
)


@ai_decision_faz12_bp.get("/health")
def ai_decision_faz12_health():
    return jsonify({
        "ok": True,
        "phase": "Faz 12",
        "marker": "BYS360_AI_DECISION_FAZ12_HEALTH_OK",
        "message": "AI Karar Destek Faz 12 final gate hazır.",
    })


@ai_decision_faz12_bp.get("/final-gate")
def ai_decision_faz12_final_gate():
    report = get_ai_decision_final_gate_report(Path.cwd())
    return render_template("ai_decision/faz12_final_gate.html", report=report)


@ai_decision_faz12_bp.get("/final-gate.json")
def ai_decision_faz12_final_gate_json():
    return jsonify(get_ai_decision_final_gate_report(Path.cwd()))
