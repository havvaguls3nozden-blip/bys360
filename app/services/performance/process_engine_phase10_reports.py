from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import text

from app.extensions import db

logger = logging.getLogger(__name__)

PHASE10_VERSION = "2026-04-30-process-reports-phase10"
REPORT_URL = "/performans/surec-raporlari"


@dataclass(frozen=True)
class ProcessReportRow:
    flow_id: int
    evaluation_id: int | None
    period_id: int | None
    employee_id: int | None
    final_score: float | None
    current_status: str
    current_stage: str
    current_owner_name: str
    president_status: str
    publish_lock_status: str
    publish_allowed: bool | None
    is_overdue: bool
    overdue_days: int
    tracking_bucket: str
    tracking_priority: int
    tracking_label: str
    last_visible_action: str
    tracking_updated_at: datetime | None


def _table_exists(table_name: str) -> bool:
    return bool(
        db.session.execute(
            text("SELECT to_regclass(:table_name) IS NOT NULL"),
            {"table_name": f"public.{table_name}"},
        ).scalar()
    )


def _columns(table_name: str) -> set[str]:
    rows = db.session.execute(
        text(
            """
            SELECT column_name
              FROM information_schema.columns
             WHERE table_schema = 'public'
               AND table_name = :table_name
            """
        ),
        {"table_name": table_name},
    ).fetchall()
    return {str(row[0]) for row in rows}


def _col(cols: set[str], name: str, fallback_sql: str = "NULL") -> str:
    return name if name in cols else fallback_sql


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return None


def ensure_phase10_report_schema() -> dict[str, Any]:
    statements = [
        """
        CREATE TABLE IF NOT EXISTS performance_process_report_snapshots (
            id SERIAL PRIMARY KEY,
            report_key VARCHAR(80) NOT NULL,
            period_id INTEGER NULL,
            total_count INTEGER NOT NULL DEFAULT 0,
            president_pending_count INTEGER NOT NULL DEFAULT 0,
            publish_locked_count INTEGER NOT NULL DEFAULT 0,
            overdue_count INTEGER NOT NULL DEFAULT 0,
            risk_count INTEGER NOT NULL DEFAULT 0,
            payload_json TEXT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_perf_report_snapshots_key_created ON performance_process_report_snapshots(report_key, created_at)",
        "CREATE INDEX IF NOT EXISTS ix_perf_report_snapshots_period ON performance_process_report_snapshots(period_id)",
    ]
    for statement in statements:
        db.session.execute(text(statement))
    db.session.commit()
    return {"ok": True, "version": PHASE10_VERSION}


def _fetch_rows(limit: int = 250, bucket: str = "all") -> list[ProcessReportRow]:
    if not _table_exists("performance_process_flows"):
        return []

    cols = _columns("performance_process_flows")
    select_sql = f"""
        SELECT
            id AS flow_id,
            {_col(cols, 'evaluation_id')} AS evaluation_id,
            {_col(cols, 'period_id')} AS period_id,
            {_col(cols, 'employee_id')} AS employee_id,
            {_col(cols, 'final_score', 'NULL')} AS final_score,
            COALESCE({_col(cols, 'current_status', 'NULL')}, 'takipte') AS current_status,
            COALESCE({_col(cols, 'current_stage', 'NULL')}, {_col(cols, 'tracking_label', 'NULL')}, 'Süreç takipte') AS current_stage,
            COALESCE({_col(cols, 'current_owner_name', 'NULL')}, 'Atanmamış') AS current_owner_name,
            COALESCE({_col(cols, 'president_status', 'NULL')}, {_col(cols, 'president_approval_status', 'NULL')}, 'gerekli_degil') AS president_status,
            COALESCE({_col(cols, 'publish_lock_status', 'NULL')}, 'kontrol_edilmedi') AS publish_lock_status,
            {_col(cols, 'publish_allowed', 'NULL')} AS publish_allowed,
            COALESCE({_col(cols, 'is_overdue', 'NULL')}, FALSE) AS is_overdue,
            COALESCE({_col(cols, 'overdue_days', 'NULL')}, 0) AS overdue_days,
            COALESCE({_col(cols, 'tracking_bucket', 'NULL')}, 'tum_surecler') AS tracking_bucket,
            COALESCE({_col(cols, 'tracking_priority', 'NULL')}, 0) AS tracking_priority,
            COALESCE({_col(cols, 'tracking_label', 'NULL')}, {_col(cols, 'current_stage', 'NULL')}, 'Süreç takipte') AS tracking_label,
            COALESCE({_col(cols, 'last_visible_action', 'NULL')}, {_col(cols, 'last_action_title', 'NULL')}, {_col(cols, 'current_stage', 'NULL')}, 'Son işlem yok') AS last_visible_action,
            COALESCE({_col(cols, 'tracking_updated_at', 'NULL')}, {_col(cols, 'updated_at', 'NULL')}, {_col(cols, 'created_at', 'NULL')}) AS tracking_updated_at
          FROM performance_process_flows
    """

    where_parts: list[str] = []
    params: dict[str, Any] = {"limit": max(1, min(int(limit or 250), 1000))}

    if bucket and bucket != "all":
        if bucket == "president_pending":
            where_parts.append("COALESCE(" + _col(cols, 'president_status', 'NULL') + ", " + _col(cols, 'president_approval_status', 'NULL') + ", '') IN ('pending', 'president_pending', 'onay_bekliyor')")
        elif bucket == "publish_locked":
            where_parts.append("COALESCE(" + _col(cols, 'publish_allowed', 'TRUE') + ", TRUE) = FALSE")
        elif bucket == "overdue":
            where_parts.append("COALESCE(" + _col(cols, 'is_overdue', 'FALSE') + ", FALSE) = TRUE")
        elif bucket == "completed":
            where_parts.append("COALESCE(" + _col(cols, 'current_status', "''") + ", '') IN ('completed', 'tamamlandi', 'tamamlandı', 'finalized', 'kesinlesti')")
        else:
            where_parts.append("COALESCE(" + _col(cols, 'tracking_bucket', "''") + ", '') = :bucket")
            params["bucket"] = bucket

    if where_parts:
        select_sql += " WHERE " + " AND ".join(where_parts)

    select_sql += " ORDER BY COALESCE(" + _col(cols, 'tracking_priority', '0') + ", 0) DESC, COALESCE(" + _col(cols, 'tracking_updated_at', 'NULL') + ", " + _col(cols, 'updated_at', 'NULL') + ", " + _col(cols, 'created_at', 'NULL') + ") DESC NULLS LAST LIMIT :limit"

    rows = db.session.execute(text(select_sql), params).mappings().all()
    result: list[ProcessReportRow] = []
    for row in rows:
        result.append(
            ProcessReportRow(
                flow_id=_safe_int(row.get("flow_id")),
                evaluation_id=row.get("evaluation_id"),
                period_id=row.get("period_id"),
                employee_id=row.get("employee_id"),
                final_score=_safe_float(row.get("final_score")),
                current_status=str(row.get("current_status") or "takipte"),
                current_stage=str(row.get("current_stage") or "Süreç takipte"),
                current_owner_name=str(row.get("current_owner_name") or "Atanmamış"),
                president_status=str(row.get("president_status") or "gerekli_degil"),
                publish_lock_status=str(row.get("publish_lock_status") or "kontrol_edilmedi"),
                publish_allowed=row.get("publish_allowed"),
                is_overdue=bool(row.get("is_overdue")),
                overdue_days=_safe_int(row.get("overdue_days")),
                tracking_bucket=str(row.get("tracking_bucket") or "tum_surecler"),
                tracking_priority=_safe_int(row.get("tracking_priority")),
                tracking_label=str(row.get("tracking_label") or "Süreç takipte"),
                last_visible_action=str(row.get("last_visible_action") or "Son işlem yok"),
                tracking_updated_at=row.get("tracking_updated_at"),
            )
        )
    return result


def _summary(rows: Iterable[ProcessReportRow]) -> dict[str, int]:
    materialized = list(rows)
    return {
        "total": len(materialized),
        "president_pending": sum(1 for row in materialized if row.president_status in {"pending", "president_pending", "onay_bekliyor"}),
        "publish_locked": sum(1 for row in materialized if row.publish_allowed is False or row.publish_lock_status in {"locked", "kilitli", "blocked"}),
        "overdue": sum(1 for row in materialized if row.is_overdue),
        "risk": sum(1 for row in materialized if row.final_score is not None and row.final_score < 70),
        "completed": sum(1 for row in materialized if row.current_status in {"completed", "tamamlandi", "tamamlandı", "finalized", "kesinlesti"}),
    }


def build_phase10_report_context(bucket: str = "all", limit: int = 250, viewer: Any | None = None, status_filter: str | None = None, **_: Any) -> dict[str, Any]:
    if status_filter and (not bucket or bucket == "all"):
        bucket = status_filter
    rows = _fetch_rows(limit=limit, bucket=bucket)
    summary = _summary(rows)
    report_rows = [row.__dict__ for row in rows]
    return {
        "version": PHASE10_VERSION,
        "active_bucket": status_filter or bucket or "all",
        "summary": summary,
        "rows": report_rows,
        "filters": [
            {"key": "all", "label": "Tüm Süreçler"},
            {"key": "president_pending", "label": "Başkan Onayı Bekleyenler"},
            {"key": "publish_locked", "label": "Yayın Kilitleri"},
            {"key": "overdue", "label": "Geciken Süreçler"},
            {"key": "completed", "label": "Tamamlananlar"},
        ],
        "generated_at": datetime.now(),
        "report_url": REPORT_URL,
    }


def synchronize_phase10_report_snapshots(limit: int = 1000) -> dict[str, Any]:
    ensure_phase10_report_schema()
    context = build_phase10_report_context(bucket="all", limit=limit)
    summary = context["summary"]
    db.session.execute(
        text(
            """
            INSERT INTO performance_process_report_snapshots
                (report_key, period_id, total_count, president_pending_count, publish_locked_count, overdue_count, risk_count, payload_json, created_at)
            VALUES
                (:report_key, NULL, :total_count, :president_pending_count, :publish_locked_count, :overdue_count, :risk_count, :payload_json, CURRENT_TIMESTAMP)
            """
        ),
        {
            "report_key": "phase10_process_summary",
            "total_count": summary.get("total", 0),
            "president_pending_count": summary.get("president_pending", 0),
            "publish_locked_count": summary.get("publish_locked", 0),
            "overdue_count": summary.get("overdue", 0),
            "risk_count": summary.get("risk", 0),
            "payload_json": str(summary),
        },
    )
    db.session.commit()
    return {"ok": True, "summary": summary, "version": PHASE10_VERSION}
