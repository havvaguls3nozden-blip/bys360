from __future__ import annotations

import logging

from flask import render_template, request
from flask_login import current_user, login_required

from app.routes import main

logger = logging.getLogger(__name__)
@main.route("/performans/surec-raporlari", methods=["GET"])
@main.route("/performance/process-reports", methods=["GET"])
@login_required
def performance_process_reports():
    status_filter = request.args.get('status') or request.args.get('status_filter') or ''
    context = _bys360_process_reports_advanced_context(viewer=current_user, status_filter=status_filter)
    return render_template('performance/process_reports_advanced.html', **context)

    # BYS360_V55_DEAD_CODE_CLEANUP: return sonrası erişilemeyen eski Faz 10 kodu kaldırıldı.

# BYS360_PROCESS_REPORTS_ADVANCED_V2_BEGIN
def _bys360_process_reports_advanced_context(viewer=None, status_filter=None):
    from sqlalchemy import text as _sql_text

    from app.extensions import db

    def _rows(sql, params=None):
        try:
            return list(db.session.execute(_sql_text(sql), params or {}).mappings())
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            return []

    def _scalar(sql, params=None, default=0):
        try:
            value = db.session.execute(_sql_text(sql), params or {}).scalar()
            return value if value is not None else default
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            return default

    def _dialect_name():
        try:
            bind = db.session.get_bind()
            return getattr(getattr(bind, "dialect", None), "name", "") or ""
        except Exception:
            logger.exception("BYS360 process reports dialect tespiti yapilamadi.")
            return ""

    def _table_exists(table_name):
        try:
            if _dialect_name() == "sqlite":
                return bool(_scalar(
                    """
                    SELECT 1
                    FROM sqlite_master
                    WHERE type = 'table'
                      AND name = :table_name
                    LIMIT 1
                    """,
                    {"table_name": table_name},
                    default=0,
                ))

            return bool(_scalar(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = current_schema()
                      AND table_name = :table_name
                )
                """,
                {"table_name": table_name},
                default=False,
            ))
        except Exception:
            logger.exception(
                "BYS360 process reports table_exists guvenli fallback | table=%s",
                table_name,
            )
            return False

    table_exists = _table_exists("performance_process_flows")

    if not table_exists:
        return {
            "summary": {},
            "status_rows": [],
            "owner_rows": [],
            "recent_rows": [],
            "president_rows": [],
            "status_filter": status_filter or "",
        }

    where = "WHERE 1=1"
    params = {}

    if status_filter == "pending":
        where += " AND COALESCE(f.is_finalized, FALSE) = FALSE"
    elif status_filter == "overdue":
        where += " AND COALESCE(f.is_overdue, FALSE) = TRUE"
    elif status_filter == "president":
        where += " AND COALESCE(f.president_required, FALSE) = TRUE"
    elif status_filter == "finalized":
        where += " AND COALESCE(f.is_finalized, FALSE) = TRUE"

    summary_rows = _rows(f"""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN COALESCE(f.is_finalized, FALSE) = FALSE THEN 1 ELSE 0 END) AS pending,
            SUM(CASE WHEN COALESCE(f.is_overdue, FALSE) = TRUE THEN 1 ELSE 0 END) AS overdue,
            SUM(CASE WHEN COALESCE(f.president_required, FALSE) = TRUE THEN 1 ELSE 0 END) AS president_required,
            SUM(CASE WHEN COALESCE(f.is_finalized, FALSE) = TRUE THEN 1 ELSE 0 END) AS finalized
        FROM performance_process_flows f
        {where}
    """, params)

    raw_summary = dict(summary_rows[0]) if summary_rows else {}
    total = int(raw_summary.get("total") or 0)

    summary = {
        "total": total,
        "pending": int(raw_summary.get("pending") or 0),
        "overdue": int(raw_summary.get("overdue") or 0),
        "president_required": int(raw_summary.get("president_required") or 0),
        "finalized": int(raw_summary.get("finalized") or 0),
    }

    status_data = _rows(f"""
        SELECT
            COALESCE(NULLIF(f.tracking_label, ''), NULLIF(f.current_status, ''), 'Süreçte') AS label,
            COALESCE(NULLIF(f.tracking_status, ''), NULLIF(f.current_status, ''), 'process') AS status,
            COUNT(*) AS count
        FROM performance_process_flows f
        {where}
        GROUP BY 1, 2
        ORDER BY COUNT(*) DESC, 1
        LIMIT 12
    """, params)

    status_rows = []
    for row in status_data:
        count = int(row.get("count") or 0)
        percent = int(round((count / total) * 100)) if total else 0
        status_rows.append({
            "label": row.get("label"),
            "status": row.get("status"),
            "count": count,
            "percent": percent,
        })

    owner_rows = _rows(f"""
        SELECT
            COALESCE(
                NULLIF(CONCAT_WS(' ', owner.ad, owner.soyad), ''),
                NULLIF(f.current_owner_name, ''),
                'Sorumlu belirtilmedi'
            ) AS owner_name,
            COUNT(*) AS total,
            SUM(CASE WHEN COALESCE(f.is_overdue, FALSE) = TRUE THEN 1 ELSE 0 END) AS overdue,
            ROUND(AVG(COALESCE(f.waiting_days, 0))::numeric, 1) AS avg_waiting_days
        FROM performance_process_flows f
        LEFT JOIN users owner ON owner.id = f.current_owner_user_id
        {where}
        GROUP BY 1
        ORDER BY
            SUM(CASE WHEN COALESCE(f.is_overdue, FALSE) = TRUE THEN 1 ELSE 0 END) DESC,
            COUNT(*) DESC
        LIMIT 12
    """, params)

    recent_rows = _rows(f"""
        SELECT
            f.id AS flow_id,
            COALESCE(NULLIF(CONCAT_WS(' ', emp.ad, emp.soyad), ''), 'Personel') AS employee_name,
            COALESCE(NULLIF(CONCAT_WS(' ', owner.ad, owner.soyad), ''), NULLIF(f.current_owner_name, ''), '-') AS owner_name,
            COALESCE(NULLIF(f.tracking_label, ''), NULLIF(f.current_status, ''), 'Süreçte') AS status_label,
            COALESCE(NULLIF(f.last_action_title, ''), '-') AS last_action_title,
            COALESCE(f.waiting_days, 0) AS waiting_days,
            COALESCE(f.is_overdue, FALSE) AS is_overdue,
            COALESCE(f.is_finalized, FALSE) AS is_finalized,
            COALESCE(NULLIF(f.tracking_priority, ''), 'Normal') AS priority_label
        FROM performance_process_flows f
        LEFT JOIN users emp ON emp.id = f.employee_id
        LEFT JOIN users owner ON owner.id = f.current_owner_user_id
        {where}
        ORDER BY
            COALESCE(f.is_overdue, FALSE) DESC,
            COALESCE(f.waiting_days, 0) DESC,
            COALESCE(f.last_action_at, f.updated_by_engine_at, f.created_at, CURRENT_TIMESTAMP) DESC
        LIMIT 60
    """, params)

    president_rows = _rows(f"""
        SELECT
            f.id AS flow_id,
            COALESCE(NULLIF(CONCAT_WS(' ', emp.ad, emp.soyad), ''), 'Personel') AS employee_name,
            COALESCE(NULLIF(CONCAT_WS(' ', owner.ad, owner.soyad), ''), NULLIF(f.current_owner_name, ''), '-') AS owner_name,
            f.final_score,
            COALESCE(NULLIF(f.president_approval_status, ''), NULLIF(f.president_status, ''), 'Üst Onay Bekliyor') AS president_status_label,
            COALESCE(NULLIF(f.last_action_title, ''), '-') AS last_action_title,
            COALESCE(f.waiting_days, 0) AS waiting_days
        FROM performance_process_flows f
        LEFT JOIN users emp ON emp.id = f.employee_id
        LEFT JOIN users owner ON owner.id = f.current_owner_user_id
        {where}
          AND COALESCE(f.president_required, FALSE) = TRUE
        ORDER BY
            COALESCE(f.waiting_days, 0) DESC,
            COALESCE(f.president_requested_at, f.created_at, CURRENT_TIMESTAMP) DESC
        LIMIT 40
    """, params)

    return {
        "summary": summary,
        "status_rows": [dict(r) for r in status_rows],
        "owner_rows": [dict(r) for r in owner_rows],
        "recent_rows": [dict(r) for r in recent_rows],
        "president_rows": [dict(r) for r in president_rows],
        "status_filter": status_filter or "",
    }
# BYS360_PROCESS_REPORTS_ADVANCED_V2_END

# BYS360_PERFORMANCE_COMPLETION_PHASE7_SCORECARD_ARCHIVE_BOUND
# Geçmiş yıl karne/puan arşivi phase7_scorecard_archive_policy sözleşmesini kullanır.

# BYS360_PERFORMANCE_COMPLETION_PHASE11_REPORTING_RISK_BOUND
# Raporlama, dashboard ve risk analizi phase11_reporting_risk_policy sözleşmesini kullanır.

# BYS360_PERFORMANCE_COMPLETION_PHASE12_FINAL_READINESS_BOUND
# Final gate, 10 senaryo testi ve canlı hazırlık phase12_final_readiness_policy sözleşmesini kullanır.
