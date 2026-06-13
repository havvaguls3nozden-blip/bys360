# -*- coding: utf-8 -*-
from __future__ import annotations


import logging
logger = logging.getLogger(__name__)

"""BYS360 geri bildirim görüşme hattı süreç görünümü.

Bu servis, görüşme sonrası not, görüşme rehberi, karne bağlantısı,
eylem planı takibi, yayına hazırlık ve canlı kontrol alanlarını tek
kurumsal ilerleme yüzeyinde toplar. İdari karar üretmez; yalnızca
hazırlık, yönlendirme ve süreç bütünlüğü gösterir.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from flask import current_app

from app.services.performance.feedback_process_state_machine import build_feedback_state_snapshot


MANAGER_ROLES = {
    "admin", "super_admin", "system_admin", "sistem_yoneticisi",
    "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir",
    "koordinator", "birim_sorumlusu", "yonetici", "manager", "performans_yetkilisi",
}


@dataclass(frozen=True)
class FeedbackPipelineStep:
    key: str
    title: str
    endpoint: str
    path: str
    template: str
    required_tables: tuple[str, ...]
    description: str
    icon: str


PIPELINE_STEPS: tuple[FeedbackPipelineStep, ...] = (
    FeedbackPipelineStep(
        key="aftercare",
        title="Görüşme Sonrası Notlar",
        endpoint="main.performance_feedback_aftercare",
        path="/performance/feedback-aftercare",
        template="app/templates/performance/feedback_aftercare.html",
        required_tables=("feedback_meetings", "feedback_meeting_action_plans"),
        description="Görüşme hazırlığı, görüşme özeti ve eylem planı kayıtlarını tek dosyada toplar.",
        icon="fa-solid fa-clipboard-check",
    ),
    FeedbackPipelineStep(
        key="guide",
        title="Görüşme Rehberi",
        endpoint="main.performance_feedback_meeting_guide",
        path="/performance/feedback-meeting-guide",
        template="app/templates/performance/feedback_meeting_guide.html",
        required_tables=("users",),
        description="Yöneticinin görüşmeyi yapıcı, somut ve kurumsal bir dille yürütmesine yardım eder.",
        icon="fa-solid fa-comments",
    ),
    FeedbackPipelineStep(
        key="integration",
        title="Karne ve Süreç Hafızası",
        endpoint="main.performance_feedback_integration",
        path="/performance/feedback-integration",
        template="app/templates/performance/feedback_integration_phase3.html",
        required_tables=("performance_evaluations", "performance_periods", "feedback_meetings"),
        description="Karne, dönem, personel ve görüşme kayıtlarının birlikte okunmasını sağlar.",
        icon="fa-solid fa-link",
    ),
    FeedbackPipelineStep(
        key="followup",
        title="Eylem Planı Takibi",
        endpoint="main.performance_feedback_followup",
        path="/performance/feedback-followup",
        template="app/templates/performance/feedback_followup_phase4.html",
        required_tables=("feedback_meeting_action_plans", "feedback_action_followup_notices"),
        description="Kararlaştırılan aksiyonların takip tarihi, durumu ve bildirim kaydını görünür kılar.",
        icon="fa-solid fa-calendar-check",
    ),
    FeedbackPipelineStep(
        key="ready",
        title="Yayına Hazırlık Kontrolü",
        endpoint="main.performance_feedback_final_gate",
        path="/performance/feedback-final-gate",
        template="app/templates/performance/feedback_final_gate_phase5.html",
        required_tables=("users", "performance_evaluations"),
        description="Görüşme hattının canlı kullanım öncesi ana hazırlık başlıklarını özetler.",
        icon="fa-solid fa-circle-check",
    ),
    FeedbackPipelineStep(
        key="live_control",
        title="Canlı Kullanım Kontrolü",
        endpoint="main.performance_feedback_corporate_cleanup",
        path="/performance/feedback-corporate-cleanup",
        template="app/templates/performance/feedback_corporate_cleanup_phase6.html",
        required_tables=("users", "feedback_meetings", "performance_interim_notes"),
        description="Teknik dil, bağlantı, görünürlük, mobil kullanım ve veritabanı hazırlığını kontrol eder.",
        icon="fa-solid fa-shield-heart",
    ),
)


def _role(user: Any) -> str:
    return str(getattr(user, "role", "") or "").strip().lower()


def can_view_feedback_pipeline(user: Any) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return bool(
        getattr(user, "is_admin", False)
        or getattr(user, "is_superuser", False)
        or _role(user) in MANAGER_ROLES
    )


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _endpoint_exists(endpoint: str) -> bool:
    try:
        return endpoint in {rule.endpoint for rule in current_app.url_map.iter_rules()}
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/feedback_pipeline.py | line=127")
        return False


def _table_status(required_tables: tuple[str, ...]) -> tuple[list[dict[str, Any]], list[str]]:
    if not required_tables:
        return [], []
    try:
        from sqlalchemy import inspect
        from app.extensions import db

        inspector = inspect(db.engine)
        existing = set(inspector.get_table_names())
        items = [{"name": table, "ok": table in existing} for table in required_tables]
        missing = [table for table in required_tables if table not in existing]
        return items, missing
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        try:
            from app.extensions import db
            db.session.rollback()
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            import logging
            logging.getLogger(__name__).exception("BYS360_CLAUDE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/feedback_pipeline.py")
        return [], [f"Veritabanı kontrolü çalıştırılamadı: {exc}"]


def build_feedback_pipeline_context(user: Any) -> dict[str, Any]:
    root = _project_root()
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    state_snapshot = build_feedback_state_snapshot()
    state_by_key = {item["key"]: item for item in state_snapshot.get("steps", [])}

    for index, step in enumerate(PIPELINE_STEPS, start=1):
        endpoint_ok = _endpoint_exists(step.endpoint)
        template_ok = (root / step.template).exists()
        table_items, missing_tables = _table_status(step.required_tables)
        if missing_tables:
            for item in missing_tables:
                warnings.append(f"{step.title}: {item}")

        checks = [endpoint_ok, template_ok, not missing_tables]
        percent = int(round((sum(1 for item in checks if item) / len(checks)) * 100))
        status = "ready" if percent == 100 else ("attention" if percent >= 67 else "missing")
        state_item = state_by_key.get(step.key, {})
        rows.append({
            "order": index,
            "key": step.key,
            "title": step.title,
            "endpoint": step.endpoint,
            "path": step.path,
            "description": step.description,
            "icon": step.icon,
            "endpoint_ok": endpoint_ok,
            "template_ok": template_ok,
            "tables": table_items,
            "missing_tables": missing_tables,
            "percent": percent,
            "status": status,
            "phase_label": state_item.get("phase_label"),
            "flow_status": state_item.get("status"),
            "flow_status_label": state_item.get("status_label"),
            "flow_status_class": state_item.get("status_class"),
            "blocked_by_labels": state_item.get("blocked_by_labels", []),
        })

    total = len(rows)
    ready = len([row for row in rows if row["status"] == "ready"])
    attention = len([row for row in rows if row["status"] == "attention"])
    missing = len([row for row in rows if row["status"] == "missing"])
    overall = int(round((sum(row["percent"] for row in rows) / (total * 100)) * 100)) if total else 0

    return {
        "access_denied": not can_view_feedback_pipeline(user),
        "steps": rows,
        "summary": {
            "total": total,
            "ready": ready,
            "attention": attention,
            "missing": missing,
            "overall_percent": overall,
            "warning_count": len(warnings),
        },
        "warnings": warnings[:50],
        "pipeline_note": "Görüşme hattı; not, rehber, karne bağlantısı, eylem takibi, yayına hazırlık ve canlı kontrol adımlarını birlikte izler.",
        "state_machine": state_snapshot,
    }
