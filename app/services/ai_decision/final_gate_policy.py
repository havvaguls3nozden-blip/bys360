# -*- coding: utf-8 -*-
"""
BYS360 AI Karar Destek Faz 12 final gate ve canlı hazırlık politikası.

Bu servis karar vermez; Faz 1-11 uygulama izlerini, gate sonuçlarını,
route/panel kayıtlarını ve canlı hazırlık sinyallerini insan denetimli final
kontrol notuna dönüştürür.

BYS360_AI_DECISION_FAZ12_POLICY_OK
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
from typing import Any

PHASES = tuple(range(1, 12))
FINAL_OK_MARKER = "BYS360_AI_DECISION_FAZ12_FINAL_GATE_READY"

FORBIDDEN_VISIBLE_TERMS = [
    "dummy",
    "authorized_scope",
    "workflow state",
    "workflow_state",
    "phase sync",
    "debug",
    "test only",
    "todo",
    "faz senkronu",
    "aşama 10",
]

ALLOWED_INTERNAL_TERMS = [
    "scripts/",
    "reports/",
    "migrations/",
]

@dataclass
class PhaseGateStatus:
    phase: int
    gate_script: str
    gate_report: str | None
    status: str
    detail: str

@dataclass
class FinalGateSignal:
    code: str
    level: str
    title: str
    detail: str


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return ""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return {}


def _find_gate_report(project_root: Path, phase: int) -> Path | None:
    candidates = [
        project_root / "reports" / f"ai_decision_faz{phase}" / f"ai_decision_faz{phase}_gate.json",
        project_root / "reports" / "overlay_manifests" / f"ai_decision_faz{phase}_manifest.json",
    ]
    for item in candidates:
        if item.exists():
            return item
    report_dir = project_root / "reports"
    if report_dir.exists():
        matches = list(report_dir.rglob(f"*faz{phase}*gate*.json"))
        if matches:
            return matches[0]
        matches = list(report_dir.rglob(f"*faz{phase}*manifest*.json"))
        if matches:
            return matches[0]
    return None


def collect_phase_gate_status(project_root: Path) -> list[PhaseGateStatus]:
    statuses: list[PhaseGateStatus] = []
    for phase in PHASES:
        gate_script = project_root / "scripts" / f"check_ai_decision_faz{phase}_gate.py"
        gate_report = _find_gate_report(project_root, phase)
        report_data = _read_json(gate_report) if gate_report else {}
        ok_marker = f"BYS360_AI_DECISION_FAZ{phase}_GATE_OK"
        status = "eksik"
        detail = "Gate script veya gate raporu bulunamadı."
        if gate_script.exists():
            status = "script_var"
            detail = "Gate script mevcut; son rapor henüz bulunamadı."
        if gate_report:
            text = _read_text(gate_report)
            errors = report_data.get("errors") or report_data.get("hatalar") or []
            hata = report_data.get("hata")
            ok_text = ok_marker in text or report_data.get("ok_marker") == ok_marker or report_data.get("gate") == ok_marker
            if errors or (isinstance(hata, int) and hata > 0):
                status = "hata"
                detail = "Gate raporunda hata kaydı var."
            elif ok_text or (gate_script.exists() and not errors):
                status = "ok"
                detail = "Gate izi temiz görünüyor."
            else:
                status = "kontrol_gerekli"
                detail = "Gate raporu var; OK marker açık doğrulanamadı."
        statuses.append(PhaseGateStatus(phase, str(gate_script.relative_to(project_root)), str(gate_report.relative_to(project_root)) if gate_report else None, status, detail))
    return statuses


def collect_live_readiness(project_root: Path) -> list[FinalGateSignal]:
    signals: list[FinalGateSignal] = []

    faz11_repair = project_root / "reports" / "ai_decision_faz11" / "ai_decision_faz11_live_repair_gate.json"
    if faz11_repair.exists():
        data = _read_json(faz11_repair)
        if int(data.get("hata", 0) or 0) == 0:
            signals.append(FinalGateSignal("faz11_live_repair", "ok", "Faz 11 canlı uyum temiz", "Route girintisi ve SQL bağlantı uyumu kontrol edilmiş görünüyor."))
        else:
            signals.append(FinalGateSignal("faz11_live_repair", "error", "Faz 11 canlı uyum hatası", "Faz 11 canlı onarım gate raporunda hata var."))
    else:
        signals.append(FinalGateSignal("faz11_live_repair", "warning", "Faz 11 canlı uyum raporu yok", "Faz 11 onarım overlay'i uygulanmadıysa önce çalıştırılması önerilir."))

    routes_file = project_root / "app" / "ai" / "routes.py"
    if routes_file.exists():
        content = _read_text(routes_file)
        if "try:\nfrom app.ai.decision_support_faz11_routes" in content or "except Exception:\npass" in content:
            signals.append(FinalGateSignal("route_indent", "error", "Route girinti izi bulundu", "app/ai/routes.py içinde hatalı try/except girinti izi var."))
        else:
            signals.append(FinalGateSignal("route_indent", "ok", "Route girinti kontrolü temiz", "AI route kayıtlarında bilinen girinti hatası izi görünmüyor."))
    else:
        signals.append(FinalGateSignal("route_file", "warning", "AI route dosyası yok", "app/ai/routes.py bulunamadı; proje yapısına göre manuel kontrol gerekebilir."))

    env_risks = [".env", ".venv", "__pycache__", ".pytest_cache"]
    found_risks = []
    for name in env_risks:
        if (project_root / name).exists():
            found_risks.append(name)
    if found_risks:
        signals.append(FinalGateSignal("release_hygiene", "warning", "Canlı paket hijyen uyarısı", "Proje kökünde canlı release dışı tutulması gereken izler var: " + ", ".join(found_risks)))
    else:
        signals.append(FinalGateSignal("release_hygiene", "ok", "Canlı paket hijyeni temiz", "Kök dizinde temel geliştirme kalıntısı görünmüyor."))

    return signals


def scan_visible_technical_terms(project_root: Path) -> list[FinalGateSignal]:
    signals: list[FinalGateSignal] = []
    template_roots = [project_root / "app" / "templates", project_root / "app" / "static" / "css"]
    hits: list[str] = []
    for base in template_roots:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.suffix.lower() not in {".html", ".css", ".js"}:
                continue
            rel = str(path.relative_to(project_root)).replace("\\", "/")
            text = _read_text(path).casefold()
            for term in FORBIDDEN_VISIBLE_TERMS:
                if term.casefold() in text:
                    # Karar destek içindeki marker/yorumlar değil, görünür yüzeyler için uyarı veriyoruz.
                    hits.append(f"{term} | {rel}")
                    break
    if hits:
        signals.append(FinalGateSignal("technical_terms", "warning", "Görünür teknik ifade izi", "; ".join(hits[:20])))
    else:
        signals.append(FinalGateSignal("technical_terms", "ok", "Görünür teknik ifade temiz", "Kontrol edilen şablon/CSS yüzeylerinde yasaklı teknik ifade izi bulunmadı."))
    return signals


def build_final_report(project_root: Path) -> dict[str, Any]:
    phases = collect_phase_gate_status(project_root)
    live = collect_live_readiness(project_root)
    visible = scan_visible_technical_terms(project_root)
    all_signals = live + visible
    errors = [s for s in all_signals if s.level == "error"] + [FinalGateSignal(f"faz{p.phase}", "error", f"Faz {p.phase} gate hatası", p.detail) for p in phases if p.status == "hata"]
    warnings = [s for s in all_signals if s.level == "warning"] + [FinalGateSignal(f"faz{p.phase}", "warning", f"Faz {p.phase} kontrol gerekli", p.detail) for p in phases if p.status in {"eksik", "kontrol_gerekli", "script_var"}]
    ok = not errors
    return {
        "phase": "BYS360 AI Karar Destek Faz 12 Final Gate",
        "ok": ok,
        "ok_marker": "BYS360_AI_DECISION_FAZ12_GATE_OK" if ok else "BYS360_AI_DECISION_FAZ12_GATE_FAILED",
        "final_marker": FINAL_OK_MARKER if ok else "BYS360_AI_DECISION_FAZ12_FINAL_GATE_BLOCKED",
        "hata": len(errors),
        "uyari": len(warnings),
        "phases": [asdict(p) for p in phases],
        "signals": [asdict(s) for s in all_signals],
        "errors": [asdict(s) for s in errors],
        "warnings": [asdict(s) for s in warnings],
    }
