from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import inspect, text

from app.extensions import db
from app.services.performance.process_engine_phase6_president_approvals import (
    can_view_president_approvals,
)

logger = logging.getLogger(__name__)

PRESIDENT_CARD_REVIEW_REPAIR_MARKER = "BYS360_PRESIDENT_CARD_REVIEW_FINAL_V1"

_STATUS_LABELS = {
    "draft": "Taslak",
    "authorized_scope": "Yetkili kapsam",
    "scorecard_pending": "Karne yayın bekliyor",
    "president_pending": "Başkan onayı bekliyor",
    "baskan_onayi_bekliyor": "Başkan onayı bekliyor",
    "başkan_onayı_bekliyor": "Başkan onayı bekliyor",
    "pending": "Başkan onayı bekliyor",
    "bekliyor": "Başkan onayı bekliyor",
    "blocked_president_pending": "Başkan onayı beklediği için yayın kilitli",
    "publish_blocked_president_pending": "Başkan onayı beklediği için yayın kilitli",
    "approved": "Başkan onayladı",
    "onaylandi": "Başkan onayladı",
    "onaylandı": "Başkan onayladı",
    "returned": "Başkan iade etti",
    "iade": "Başkan iade etti",
    "iade_edildi": "Başkan iade etti",
    "completed": "Tamamlandı",
    "tamamlandi": "Tamamlandı",
    "tamamlandı": "Tamamlandı",
    "blocked": "Yayın kilitli",
    "publish_blocked": "Yayın kilitli",
    "allowed": "Yayınlanabilir",
    "published": "Yayınlandı",
}


def _norm(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def status_label(value: Any, fallback: str = "Süreç takipte") -> str:
    raw = str(value or "").strip()
    if not raw:
        return fallback
    normalized = _norm(raw)
    if normalized in _STATUS_LABELS:
        return _STATUS_LABELS[normalized]
    if normalized.startswith("blocked_president"):
        return "Başkan onayı beklediği için yayın kilitli"
    if "president" in normalized and "pending" in normalized:
        return "Başkan onayı bekliyor"
    if "baskan" in normalized and "bek" in normalized:
        return "Başkan onayı bekliyor"
    return fallback


def table_exists(table_name: str) -> bool:
    """BYS360 DEFECT AL: raw PostgreSQL-only ``information_schema.tables``
    query replaced with SQLAlchemy's ``inspect()``, which is dialect-neutral
    by construction."""
    return bool(inspect(db.engine).has_table(table_name))


def table_columns(table_name: str) -> set[str]:
    if not table_exists(table_name):
        return set()
    return {str(row["name"]) for row in inspect(db.engine).get_columns(table_name)}


def _rows(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return [dict(row) for row in db.session.execute(text(sql), params or {}).mappings()]


def _one(sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    row = db.session.execute(text(sql), params or {}).mappings().first()
    return dict(row) if row else None


def _date(value: Any) -> str:
    if not value:
        return "-"
    if hasattr(value, "strftime"):
        return value.strftime("%d.%m.%Y %H:%M")
    return str(value)


def _score(value: Any) -> str:
    if value is None or value == "":
        return "-"
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return str(value)


def _name(row: dict[str, Any], prefix: str) -> str:
    full = str(row.get(f"{prefix}_full_name") or "").strip()
    if full:
        return full
    ad = str(row.get(f"{prefix}_ad") or "").strip()
    soyad = str(row.get(f"{prefix}_soyad") or "").strip()
    name = f"{ad} {soyad}".strip()
    return name or str(row.get(f"{prefix}_email") or "").strip() or "-"


def _user_name(user_id: Any) -> str:
    # BYS360_PRESIDENT_SCORECARD_DETAIL_V6: full_name kolonu olmayan canlı şemada güvenli ad üretir.
    if not user_id or not table_exists("users"):
        return "-"
    cols = table_columns("users")
    if "id" not in cols:
        return "-"

    wanted = [
        "full_name", "display_name", "name", "ad_soyad", "adi_soyadi",
        "ad", "soyad", "adi", "soyadi", "first_name", "last_name",
        "username", "email",
    ]
    selected = [c for c in wanted if c in cols]
    if not selected:
        return "-"

    def qident(name: str) -> str:
        return '"' + name.replace('"', '""') + '"'

    select_sql = ", ".join(qident(c) for c in selected)
    try:
        row = _one(
            f"""
            SELECT {select_sql}
            FROM users
            WHERE id = :user_id
            """,
            {"user_id": user_id},
        )
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        try:
            db.session.rollback()
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/president_card_review_service.py")
        return "-"

    if not row:
        return "-"

    for key in ("full_name", "display_name", "name", "ad_soyad", "adi_soyadi"):
        value = str(row.get(key) or "").strip()
        if value:
            return value

    first = str(row.get("ad") or row.get("adi") or row.get("first_name") or "").strip()
    last = str(row.get("soyad") or row.get("soyadi") or row.get("last_name") or "").strip()
    combined = f"{first} {last}".strip()
    if combined:
        return combined

    for key in ("email", "username"):
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return "-"

def _approval(approval_id: int) -> dict[str, Any] | None:
    """BYS360 DEFECT AM: the query referenced eight columns
    (pa.visible_status, f.current_stage, f.current_owner_name,
    f.last_action_title, f.publish_lock_status, f.publish_lock_reason,
    f.publish_lock_required_action, f.publish_allowed) that no migration and
    no reachable runtime schema-repair path ever creates -- confirmed
    against a real, migration-built database, not just the ORM model. Read
    with the same column-presence gating this file already uses in
    _history_from_scoring_table()/_flow_steps(); every caller of these
    fields in build_president_card_review_context() already has its own
    fallback for a missing value (visible_status falls back to
    approval_status, current_stage to current_status, publish_lock_* to
    fixed default text, publish_allowed to False). current_owner_name was
    dropped entirely: it is not read anywhere in this file.

    pa.score is left untouched -- it is a real, actively-synced legacy
    column (see process_engine_phase7_president_rule.py's _ensure_approval(),
    which writes the same value to both score and final_score), confirmed
    present on a real migration-built schema; an earlier, unrelated
    introspection-wave test that reported it missing used a database built
    from the ORM model only (db.create_all()), which does not reflect this
    migration-owned column.
    """
    if not table_exists("performance_president_approvals"):
        return None
    flow_cols = table_columns("performance_process_flows") if table_exists("performance_process_flows") else set()
    pa_cols = table_columns("performance_president_approvals")
    visible_status_expr = "pa.visible_status" if "visible_status" in pa_cols else "NULL"
    current_stage_expr = "f.current_stage" if "current_stage" in flow_cols else "NULL"
    last_action_title_expr = "f.last_action_title" if "last_action_title" in flow_cols else "NULL"
    publish_lock_status_expr = "f.publish_lock_status" if "publish_lock_status" in flow_cols else "NULL"
    publish_lock_reason_expr = "f.publish_lock_reason" if "publish_lock_reason" in flow_cols else "NULL"
    publish_lock_required_action_expr = "f.publish_lock_required_action" if "publish_lock_required_action" in flow_cols else "NULL"
    publish_allowed_expr = "f.publish_allowed" if "publish_allowed" in flow_cols else "NULL"
    return _one(
        f"""
        SELECT
            pa.id AS approval_id,
            pa.flow_id,
            pa.evaluation_id,
            pa.period_id,
            pa.employee_id,
            COALESCE(pa.final_score, pa.score, e.final_total_100, f.final_score) AS final_score,
            pa.status AS approval_status,
            {visible_status_expr} AS visible_status,
            pa.requested_at,
            pa.decided_at,
            pa.decision_note,
            pa.president_user_id,
            pa.president_name,
            f.current_status,
            {current_stage_expr} AS current_stage,
            {last_action_title_expr} AS last_action_title,
            f.last_action_at,
            {publish_lock_status_expr} AS publish_lock_status,
            {publish_lock_reason_expr} AS publish_lock_reason,
            {publish_lock_required_action_expr} AS publish_lock_required_action,
            {publish_allowed_expr} AS publish_allowed,
            e.status AS evaluation_status,
            e.workflow_status,
            e.level_1_evaluator_id,
            e.level_2_evaluator_id,
            e.level_3_evaluator_id,
            e.level_1_total_100,
            e.level_2_total_100,
            e.level_3_total_100,
            e.level_1_completed,
            e.level_2_completed,
            e.level_3_completed,
            e.level_1_general_comment,
            e.level_2_general_comment,
            e.level_3_general_comment,
            p.title AS period_title,
            u.ad AS employee_ad,
            u.soyad AS employee_soyad,
            u.email AS employee_email,
            u.sicil_no AS employee_sicil_no,
            u.birim AS employee_birim,
            u.ust_birim AS employee_ust_birim
        FROM performance_president_approvals pa
        LEFT JOIN performance_process_flows f ON f.id = pa.flow_id
        LEFT JOIN performance_evaluations e ON e.id = pa.evaluation_id
        LEFT JOIN performance_periods p ON p.id = COALESCE(pa.period_id, e.period_id, f.period_id)
        LEFT JOIN users u ON u.id = COALESCE(pa.employee_id, e.employee_id, f.employee_id)
        WHERE pa.id = :approval_id
        """,
        {"approval_id": approval_id},
    )


def _history_from_scoring_table(evaluation_id: int | None) -> list[dict[str, Any]]:
    if not evaluation_id or not table_exists("performance_scoring_history"):
        return []
    cols = table_columns("performance_scoring_history")
    score_expr = "NULL"
    for candidate in ("score_value", "score_100", "raw_score", "score"):
        if candidate in cols:
            score_expr = candidate
            break
    manager_expr = "manager_level" if "manager_level" in cols else ("scorer_level" if "scorer_level" in cols else "NULL")
    scorer_expr = "scorer_name" if "scorer_name" in cols else ("scorer_label" if "scorer_label" in cols else "NULL")
    action_expr = "action_at" if "action_at" in cols else ("created_at" if "created_at" in cols else "NULL")
    status_expr = "action_status" if "action_status" in cols else "NULL"
    next_stage_expr = "next_stage" if "next_stage" in cols else "NULL"
    next_owner_expr = "next_owner_name" if "next_owner_name" in cols else "NULL"
    rows = _rows(
        f"""
        SELECT id,
               {scorer_expr} AS scorer_name,
               {manager_expr} AS manager_level,
               {score_expr} AS score_value,
               {status_expr} AS action_status,
               {next_stage_expr} AS next_stage,
               {next_owner_expr} AS next_owner_name,
               {action_expr} AS action_at
        FROM performance_scoring_history
        WHERE evaluation_id = :evaluation_id
        ORDER BY COALESCE({action_expr}, CURRENT_TIMESTAMP), id
        """,
        {"evaluation_id": evaluation_id},
    )
    result: list[dict[str, Any]] = []
    for row in rows:
        result.append(
            {
                "source": "history",
                "scorer_name": row.get("scorer_name") or "-",
                "manager_level": row.get("manager_level") or "-",
                "score": _score(row.get("score_value")),
                "status": status_label(row.get("action_status"), "Kaydedildi"),
                "next_stage": status_label(row.get("next_stage"), "-"),
                "next_owner_name": row.get("next_owner_name") or "-",
                "action_at": _date(row.get("action_at")),
            }
        )
    return result


def _items_summary(evaluation_id: int | None) -> dict[int, dict[str, Any]]:
    if not evaluation_id or not table_exists("performance_evaluation_items"):
        return {}
    cols = table_columns("performance_evaluation_items")
    action_expr = "updated_at" if "updated_at" in cols else ("created_at" if "created_at" in cols else "NULL")
    rows = _rows(
        f"""
        SELECT manager_level,
               COUNT(*) AS item_count,
               AVG(NULLIF(score_100, 0)) AS avg_score_100,
               AVG(score) AS avg_raw_score,
               MAX({action_expr}) AS action_at
        FROM performance_evaluation_items
        WHERE evaluation_id = :evaluation_id
        GROUP BY manager_level
        ORDER BY manager_level
        """,
        {"evaluation_id": evaluation_id},
    )
    return {int(row["manager_level"]): row for row in rows if row.get("manager_level") is not None}


def _history_from_evaluation(row: dict[str, Any]) -> list[dict[str, Any]]:
    evaluation_id = row.get("evaluation_id")
    summaries = _items_summary(evaluation_id)
    history: list[dict[str, Any]] = []
    for level in (3, 2, 1):
        evaluator_id = row.get(f"level_{level}_evaluator_id")
        total = row.get(f"level_{level}_total_100")
        completed = bool(row.get(f"level_{level}_completed"))
        comment = row.get(f"level_{level}_general_comment") or ""
        item_summary = summaries.get(level, {})
        has_items = bool(item_summary)
        if not evaluator_id and not has_items and not completed:
            continue
        score_value = total if total not in (None, 0, 0.0) else item_summary.get("avg_score_100")
        next_stage = "Süreç tamamlandı"
        if level == 3:
            next_stage = "2. amir değerlendirmesi"
        elif level == 2:
            next_stage = "1. amir değerlendirmesi"
        elif level == 1:
            next_stage = "Başkan onayı bekliyor" if float(row.get("final_score") or 0) < 70 else "Süreç tamamlandı"
        history.append(
            {
                "source": "evaluation_items",
                "scorer_name": _user_name(evaluator_id) if evaluator_id else f"{level}. amir",
                "manager_level": level,
                "score": _score(score_value),
                "status": "Tamamlandı" if completed or score_value not in (None, "-") else "Bekliyor",
                "next_stage": next_stage,
                "next_owner_name": "-",
                "action_at": _date(item_summary.get("action_at")),
                "comment": comment,
                "item_count": item_summary.get("item_count") or 0,
            }
        )
    return history


def _flow_steps(flow_id: int | None, evaluation_id: int | None) -> list[dict[str, Any]]:
    if not table_exists("performance_process_flow_steps"):
        return []
    params: dict[str, Any]
    if flow_id:
        where_sql = "flow_id = :flow_id"
        params = {"flow_id": flow_id}
    elif evaluation_id:
        where_sql = "evaluation_id = :evaluation_id"
        params = {"evaluation_id": evaluation_id}
    else:
        return []
    cols = table_columns("performance_process_flow_steps")
    title_expr = "COALESCE(visible_title, step_title)" if "visible_title" in cols else "step_title"
    status_expr = "COALESCE(visible_status, step_status, status)" if "visible_status" in cols and "step_status" in cols else ("status" if "status" in cols else "NULL")
    actor_expr = "actor_label" if "actor_label" in cols else ("owner_label" if "owner_label" in cols else "NULL")
    summary_expr = "action_summary" if "action_summary" in cols else ("description" if "description" in cols else "NULL")
    date_expr = "action_at" if "action_at" in cols else ("created_at" if "created_at" in cols else "NULL")
    order_expr = "step_order" if "step_order" in cols else ("tracking_order" if "tracking_order" in cols else "0")
    rows = _rows(
        f"""
        SELECT id,
               {title_expr} AS step_title,
               {status_expr} AS step_status,
               {actor_expr} AS actor_label,
               {summary_expr} AS action_summary,
               {date_expr} AS action_at
        FROM performance_process_flow_steps
        WHERE {where_sql}
        ORDER BY COALESCE({order_expr}, 0), COALESCE({date_expr}, CURRENT_TIMESTAMP), id
        """,
        params,
    )
    return [
        {
            "title": row.get("step_title") or "Süreç adımı",
            "status": status_label(row.get("step_status"), "Süreç takipte"),
            "actor": row.get("actor_label") or "-",
            "summary": row.get("action_summary") or "",
            "date": _date(row.get("action_at")),
        }
        for row in rows
    ]


# BYS360_PRESIDENT_SCORECARD_DETAIL_V6_FUNCTIONS_INSTALLED
def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _level_label(level: Any) -> str:
    try:
        level_int = int(level)
    except (TypeError, ValueError):
        return "Amir"
    if level_int == 1:
        return "1. amir"
    if level_int == 2:
        return "2. amir"
    if level_int == 3:
        return "3. amir"
    return f"{level_int}. amir"


def _criteria_scorecard(evaluation_id: int | None) -> list[dict[str, Any]]:
    # BYS360_PRESIDENT_SCORECARD_DETAIL_V6: kriter bazlı detaylı not karnesi üretir.
    if not evaluation_id or not table_exists("performance_evaluation_items"):
        return []

    item_cols = table_columns("performance_evaluation_items")
    criteria_exists = table_exists("performance_criteria")
    criteria_cols = table_columns("performance_criteria") if criteria_exists else set()

    if "evaluation_id" not in item_cols:
        return []

    select_parts = ["i.id AS item_id"]
    select_parts.append("i.criteria_id AS criteria_id" if "criteria_id" in item_cols else "NULL AS criteria_id")
    select_parts.append("i.manager_level AS manager_level" if "manager_level" in item_cols else "NULL AS manager_level")
    select_parts.append("i.score AS raw_score" if "score" in item_cols else "NULL AS raw_score")
    select_parts.append("i.score_100 AS score_100" if "score_100" in item_cols else "NULL AS score_100")
    select_parts.append("i.comment AS comment" if "comment" in item_cols else "NULL AS comment")
    select_parts.append("i.strength_note AS strength_note" if "strength_note" in item_cols else "NULL AS strength_note")
    select_parts.append("i.justification AS justification" if "justification" in item_cols else "NULL AS justification")
    select_parts.append("i.updated_at AS updated_at" if "updated_at" in item_cols else ("i.created_at AS updated_at" if "created_at" in item_cols else "NULL AS updated_at"))

    join_sql = ""
    order_sql = "i.id"
    if criteria_exists and "criteria_id" in item_cols and "id" in criteria_cols:
        join_sql = "LEFT JOIN performance_criteria c ON c.id = i.criteria_id"
        select_parts.append("c.name AS criteria_name" if "name" in criteria_cols else "NULL AS criteria_name")
        select_parts.append("c.description AS criteria_description" if "description" in criteria_cols else "NULL AS criteria_description")
        select_parts.append("c.weight AS criteria_weight" if "weight" in criteria_cols else "NULL AS criteria_weight")
        if "sort_order" in criteria_cols:
            order_sql = "COALESCE(c.sort_order, 999999), COALESCE(c.name, ''), COALESCE(i.manager_level, 99), i.id"
        elif "name" in criteria_cols:
            order_sql = "COALESCE(c.name, ''), COALESCE(i.manager_level, 99), i.id"
        else:
            order_sql = "COALESCE(i.criteria_id, 0), COALESCE(i.manager_level, 99), i.id"
    else:
        select_parts.append("NULL AS criteria_name")
        select_parts.append("NULL AS criteria_description")
        select_parts.append("NULL AS criteria_weight")
        order_sql = "COALESCE(i.criteria_id, 0), COALESCE(i.manager_level, 99), i.id"

    try:
        rows = _rows(
            f"""
            SELECT {", ".join(select_parts)}
            FROM performance_evaluation_items i
            {join_sql}
            WHERE i.evaluation_id = :evaluation_id
            ORDER BY {order_sql}
            """,
            {"evaluation_id": evaluation_id},
        )
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        try:
            db.session.rollback()
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/president_card_review_service.py")
        return []

    grouped: dict[str, dict[str, Any]] = {}
    ordered_keys: list[str] = []
    for row in rows:
        key = str(row.get("criteria_id") or row.get("criteria_name") or row.get("item_id") or "-")
        if key not in grouped:
            ordered_keys.append(key)
            grouped[key] = {
                "criteria_id": row.get("criteria_id"),
                "criteria_name": row.get("criteria_name") or "Değerlendirme kriteri",
                "criteria_description": row.get("criteria_description") or "",
                "criteria_weight": _score(row.get("criteria_weight")) if row.get("criteria_weight") is not None else "-",
                "levels": {},
                "average_score_100": "-",
                "average_raw_score": "-",
                "low_flag": False,
            }

        level = row.get("manager_level")
        try:
            level_int = int(level)  # type: ignore[arg-type]  # defensive parse; falls through to except below
        except (TypeError, ValueError):
            level_int = 0
        score100 = _safe_float(row.get("score_100"))
        raw = _safe_float(row.get("raw_score"))
        note_parts = [
            str(row.get("comment") or "").strip(),
            str(row.get("strength_note") or "").strip(),
            str(row.get("justification") or "").strip(),
        ]
        note = " | ".join(part for part in note_parts if part)
        grouped[key]["levels"][level_int] = {
            "level": level_int,
            "label": _level_label(level_int),
            "raw_score": _score(raw),
            "score_100": _score(score100),
            "note": note,
            "updated_at": _date(row.get("updated_at")),
        }

    result: list[dict[str, Any]] = []
    for key in ordered_keys:
        item = grouped[key]
        scores100 = [v for v in (_safe_float(lv.get("score_100")) for lv in item["levels"].values()) if v is not None]
        raw_scores = [v for v in (_safe_float(lv.get("raw_score")) for lv in item["levels"].values()) if v is not None]
        if scores100:
            avg100 = sum(scores100) / len(scores100)
            item["average_score_100"] = _score(avg100)
            item["low_flag"] = avg100 < 70
        if raw_scores:
            item["average_raw_score"] = _score(sum(raw_scores) / len(raw_scores))
        for level in (1, 2, 3):
            item[f"level_{level}"] = item["levels"].get(
                level,
                {"label": _level_label(level), "raw_score": "-", "score_100": "-", "note": "", "updated_at": "-"},
            )
        result.append(item)
    return result


def _manager_totals(row: dict[str, Any], scorecard_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    totals: list[dict[str, Any]] = []
    counts_by_level: dict[int, int] = {}
    for item in scorecard_items:
        levels = item.get("levels") or {}
        for level in levels:
            if isinstance(level, int):
                counts_by_level[level] = counts_by_level.get(level, 0) + 1

    for level in (3, 2, 1):
        evaluator_id = row.get(f"level_{level}_evaluator_id")
        total = row.get(f"level_{level}_total_100")
        completed = bool(row.get(f"level_{level}_completed"))
        comment = str(row.get(f"level_{level}_general_comment") or "").strip()
        item_count = counts_by_level.get(level, 0)
        if not evaluator_id and total in (None, 0, 0.0, "") and not completed and not comment and not item_count:
            continue
        totals.append(
            {
                "level": level,
                "label": _level_label(level),
                "evaluator_name": _user_name(evaluator_id) if evaluator_id else _level_label(level),
                "total_score": _score(total),
                "completed": completed,
                "status": "Tamamlandı" if completed or total not in (None, 0, 0.0, "") else "Bekliyor",
                "general_comment": comment,
                "item_count": item_count,
            }
        )
    return totals


def _scorecard_interpretation(final_score: Any) -> dict[str, str]:
    value = _safe_float(final_score)
    if value is None:
        return {"label": "Puan bekleniyor", "tone": "neutral", "text": "Nihai performans puanı henüz kesinleşmemiştir."}
    if value < 70:
        return {
            "label": "70 altı düşük performans",
            "tone": "danger",
            "text": "Bu sonuç Başkan onayı tamamlanmadan personele kesin/yayınlanmış sonuç olarak gösterilmez.",
        }
    if value >= 90:
        return {"label": "90 üstü yüksek performans", "tone": "success", "text": "Sonuç yüksek performans bandındadır."}
    return {"label": "Standart performans bandı", "tone": "neutral", "text": "Sonuç standart performans bandındadır."}

def build_president_card_review_context(approval_id: int, viewer: Any) -> dict[str, Any]:
    if not can_view_president_approvals(viewer):
        return {"authorized": False, "approval": None, "scoring_history": [], "flow_steps": [], "scorecard_items": [], "manager_totals": [], "scorecard_interpretation": {}}
    row = _approval(approval_id)
    if not row:
        return {"authorized": True, "approval": None, "scoring_history": [], "flow_steps": [], "scorecard_items": [], "manager_totals": [], "scorecard_interpretation": {}}
    evaluation_id = row.get("evaluation_id")
    history = _history_from_scoring_table(evaluation_id)
    if not history:
        history = _history_from_evaluation(row)
    flow_steps = _flow_steps(row.get("flow_id"), evaluation_id)
    final_score = row.get("final_score")
    # BYS360_PHASE5_FINAL_GATE_LOW_SCORE_REVIEW_GUARD
    # 70 ve üzeri kayıt Başkan Onayı Karne İncelemesi ekranında gerçek düşük performans kaydı sayılmaz.
    try:
        if final_score is None or float(final_score) >= 70:
            return {"authorized": True, "approval": None, "scoring_history": [], "flow_steps": [], "scorecard_items": [], "manager_totals": [], "scorecard_interpretation": {}}
    except (TypeError, ValueError):
        return {"authorized": True, "approval": None, "scoring_history": [], "flow_steps": [], "scorecard_items": [], "manager_totals": [], "scorecard_interpretation": {}}
    scorecard_items = _criteria_scorecard(evaluation_id)
    manager_totals = _manager_totals(row, scorecard_items)
    scorecard_interpretation = _scorecard_interpretation(final_score)
    approval = {
        "approval_id": row.get("approval_id"),
        "flow_id": row.get("flow_id"),
        "evaluation_id": evaluation_id,
        "employee_name": _name(row, "employee"),
        "sicil_no": row.get("employee_sicil_no") or "-",
        "birim": row.get("employee_birim") or row.get("employee_ust_birim") or "-",
        "period_title": row.get("period_title") or "-",
        "final_score": _score(final_score),
        "approval_status": status_label(row.get("visible_status") or row.get("approval_status"), "Başkan onayı bekliyor"),
        "process_stage": status_label(row.get("current_stage") or row.get("current_status"), "Başkan onayı bekliyor"),
        "publish_lock_status": status_label(row.get("publish_lock_status"), "Yayın kontrolü bekliyor"),
        "publish_lock_reason": status_label(row.get("publish_lock_reason"), "Başkan onayı beklediği için yayın kilitli") if row.get("publish_lock_reason") else "Başkan onayı tamamlanmadan yayınlanamaz.",
        "publish_allowed": bool(row.get("publish_allowed")),
        "requested_at": _date(row.get("requested_at")),
        "decided_at": _date(row.get("decided_at")),
        "decision_note": row.get("decision_note") or "",
        "last_action_title": status_label(row.get("last_action_title"), "Başkan onayı bekliyor"),
        "last_action_at": _date(row.get("last_action_at")),
        "president_name": row.get("president_name") or _user_name(row.get("president_user_id")),
    }
    return {
        "authorized": True,
        "approval": approval,
        "scoring_history": history,
        "flow_steps": flow_steps,
        "scorecard_items": scorecard_items,
        "manager_totals": manager_totals,
        "scorecard_interpretation": scorecard_interpretation,
        "has_scorecard_items": bool(scorecard_items),
        "has_manager_totals": bool(manager_totals),
        "has_scoring_history": bool(history),
        "has_flow_steps": bool(flow_steps),
    }

# BYS360_PRESIDENT_SCORECARD_DETAIL_V6_FUNCTIONS_INSTALLED

# BYS360_PHASE5_1_PRESIDENT_SCORECARD_REVIEW_CONTEXT

# BYS360_PERFORMANCE_COMPLETION_PHASE6_LOW_SCORE_APPROVAL_BOUND
# 70 altı düşük performans üst onay/yayın kilidi phase6_low_score_approval_policy ile izlenir.
