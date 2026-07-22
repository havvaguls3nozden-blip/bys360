"""
BYS360 çekirdek arka plan görevleri.

Bu görevler RQ worker içinde de, kontrollü inline fallback içinde de çalışabilecek şekilde yazılmıştır.
Ağır işler HTTP isteğinin içinde büyümesin diye servis fonksiyonları buradan tetiklenir.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _ensure_app_context():
    """Aktif Flask context yoksa yeni app context açar."""
    try:
        from flask import has_app_context
        if has_app_context():
            return None
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/tasks/core_background_tasks.py)")
    from app import create_app
    app = create_app()
    ctx = app.app_context()
    ctx.push()
    return ctx


def _write_json_report(name: str, payload: dict[str, Any]) -> str:
    folder = Path(os.getenv("ASYNC_TASK_REPORT_FOLDER", ""))
    if not str(folder).strip():
        folder = _project_root() / "reports" / "async_tasks"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return str(path)


def run_core_health_snapshot() -> dict[str, Any]:
    ctx = _ensure_app_context()
    try:
        try:
            from app.services.performance.core_health_panel import build_core_health_payload
            payload = build_core_health_payload()
        except Exception as exc:
            payload = {"ok": False, "error": str(exc), "note": "core_health_panel okunamadı."}
        payload["generated_at"] = datetime.now(timezone.utc).isoformat()
        path = _write_json_report("core_health_snapshot.json", payload)
        return {"ok": True, "path": path, "payload_ok": bool(payload.get("ok", True))}
    finally:
        if ctx is not None:
            ctx.pop()


def run_module_maturity_snapshot() -> dict[str, Any]:
    ctx = _ensure_app_context()
    try:
        try:
            from app.services.module_maturity import build_module_maturity_report
            payload = build_module_maturity_report()
        except Exception as exc:
            payload = {"ok": False, "error": str(exc), "note": "module_maturity okunamadı."}
        payload["generated_at"] = datetime.now(timezone.utc).isoformat()
        path = _write_json_report("module_maturity_snapshot.json", payload)
        return {"ok": True, "path": path, "payload_ok": bool(payload.get("ok", True))}
    finally:
        if ctx is not None:
            ctx.pop()


def refresh_feedback_pulse_analytics(unit_id: int | None = None, days: int = 30) -> dict[str, Any]:
    """Nabız analitiği snapshot görevi.

    Eski sürüm build_pulse_analytics'i unit_id keyword'üyle çağırıyordu; servis
    user-benzeri bağlam beklediği için worker tarafında hata üretiyordu. Bu görev
    artık ortak feedback task fonksiyonunu kullanır.
    """
    if unit_id is None:
        return {"ok": False, "error": "unit_id zorunludur"}
    from app.tasks.feedback_tasks import refresh_pulse_analytics_for_unit
    payload = refresh_pulse_analytics_for_unit(unit_id=int(unit_id), days=days)
    report_name = f"feedback_pulse_analytics_u{unit_id}_{days}d.json"
    path = _write_json_report(report_name, payload if isinstance(payload, dict) else {"data": payload})
    return {"ok": True, "path": path, "payload": payload}


def run_nightly_maintenance_bundle() -> dict[str, Any]:
    """Gece çalıştırmaya uygun hafif bakım demeti.

    Şimdilik sadece snapshot üretir; ileride mail/rapor/export işleri buraya bağlanabilir.
    """
    results = {
        "core_health": run_core_health_snapshot(),
        "module_maturity": run_module_maturity_snapshot(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    path = _write_json_report("nightly_maintenance_bundle.json", results)
    return {"ok": True, "path": path, "results": results}
