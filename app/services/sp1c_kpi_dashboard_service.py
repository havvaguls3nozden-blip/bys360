from __future__ import annotations

# BYS360 SP-1C KPI Dashboard Veri Servisi

from dataclasses import dataclass
from typing import Any, Dict, List

try:
    from app import db
except Exception:  # pragma: no cover
    db = None


@dataclass
class DashboardSummary:
    total_targets: int = 0
    completed_targets: int = 0
    risk_targets: int = 0
    critical_targets: int = 0
    average_completion: float = 0.0


def _safe_query_targets() -> List[Dict[str, Any]]:
    if db is None:
        return []
    try:
        rows = db.session.execute(
            """
            SELECT
                target_code,
                target_name,
                target_type,
                category,
                COALESCE(completion_rate, 0) AS completion_rate,
                COALESCE(status, 'ongoing') AS status,
                COALESCE(risk_level, 'low') AS risk_level
            FROM performance_targets
            ORDER BY id DESC
            LIMIT 20
            """
        ).mappings().all()
        return [dict(row) for row in rows]
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return []


def _calculate_summary(targets: List[Dict[str, Any]]) -> DashboardSummary:
    total = len(targets)
    if total == 0:
        return DashboardSummary()
    completed = sum(1 for t in targets if str(t.get("status", "")).lower() in ["completed", "tamamlandı", "tamamlandi"])
    risk = sum(1 for t in targets if str(t.get("risk_level", "")).lower() in ["medium", "risk", "riskli"])
    critical = sum(1 for t in targets if str(t.get("risk_level", "")).lower() in ["high", "critical", "kritik"])
    avg = sum(float(t.get("completion_rate") or 0) for t in targets) / total
    return DashboardSummary(total, completed, risk, critical, round(avg, 2))


def build_sp1c_kpi_dashboard_context(current_user: Any) -> Dict[str, Any]:
    targets = _safe_query_targets()
    summary = _calculate_summary(targets)
    ai_notes = []
    if summary.critical_targets:
        ai_notes.append("Kritik seviyede hedefler bulunuyor. Öncelikli takip önerilir.")
    if summary.risk_targets:
        ai_notes.append("Riskli hedefler için sorumlu birimlerden güncel durum alınması önerilir.")
    if not ai_notes:
        ai_notes.append("KPI görünümü düzenli ilerliyor. Yeni hedef girişleriyle analiz gücü artacaktır.")

    return {
        "page_title": "KPI ve Hedef Yönetimi",
        "summary": summary.__dict__,
        "targets": targets,
        "ai_notes": ai_notes,
    }
