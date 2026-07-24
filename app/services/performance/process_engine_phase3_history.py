"""BYS360 Performans Süreç Akışı Motoru - Faz 3 Puanlama Geçmişi Servisi.

Bu servis mevcut puanlama ekranlarına doğrudan müdahale etmez. Faz 3 amacı,
puanlama geçmişi ve süreç adımı kayıtlarının güvenli biçimde üretilmesi için
tek merkezli yardımcı fonksiyonlar sağlamaktır.
"""
from __future__ import annotations

import hashlib
import logging
from collections.abc import Mapping
from datetime import datetime
from typing import Any

from sqlalchemy import inspect, text

from app.extensions import db
from app.security.sql_identifiers import (
    quote_sql_identifier,
    validate_sql_identifier,
)

logger = logging.getLogger(__name__)


SCORING_HISTORY_TABLE = "performance_scoring_history"
FLOW_STEPS_TABLE = "performance_process_flow_steps"
FLOWS_TABLE = "performance_process_flows"


def _now() -> datetime:
    return datetime.utcnow()


def _table_exists(table_name: str) -> bool:
    try:
        return inspect(db.engine).has_table(table_name)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return False


def _columns(table_name: str) -> set[str]:
    try:
        return {col["name"] for col in inspect(db.engine).get_columns(table_name)}
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return set()


def _first_value(source: Mapping[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if name in source and source[name] is not None:
            return source[name]
    return default


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip()


def _event_key(payload: Mapping[str, Any]) -> str:
    parts = [
        _safe_str(payload.get("evaluation_id")),
        _safe_str(payload.get("period_id")),
        _safe_str(payload.get("employee_id")),
        _safe_str(payload.get("scorer_user_id")),
        _safe_str(payload.get("manager_level")),
        _safe_str(payload.get("score_value")),
        _safe_str(payload.get("action_at") or payload.get("created_at")),
    ]
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:40]


def _insert_if_columns(
    table_name: str,
    payload: dict[str, Any],
    unique_key: str | None = None,
) -> bool:
    allowed_tables = {
        SCORING_HISTORY_TABLE,
        FLOW_STEPS_TABLE,
    }

    safe_table_name = validate_sql_identifier(
        table_name,
        allowed=allowed_tables,
    )
    quoted_table_name = quote_sql_identifier(
        safe_table_name,
        dialect=db.engine.dialect,
        allowed=allowed_tables,
    )

    if not _table_exists(safe_table_name):
        return False

    cols = _columns(safe_table_name)

    safe_unique_key = None
    quoted_unique_key = None
    if unique_key is not None:
        safe_unique_key = validate_sql_identifier(
            unique_key,
            allowed=cols,
        )
        quoted_unique_key = quote_sql_identifier(
            safe_unique_key,
            dialect=db.engine.dialect,
            allowed=cols,
        )

    clean_payload = {
        key: value
        for key, value in payload.items()
        if key in cols
    }
    if not clean_payload:
        return False

    if (
        safe_unique_key
        and quoted_unique_key
        and clean_payload.get(safe_unique_key)
    ):
        exists = db.session.execute(
            text(
                f"SELECT 1 FROM {quoted_table_name} "
                f"WHERE {quoted_unique_key} = :event_key LIMIT 1"
            ),
            {"event_key": clean_payload[safe_unique_key]},
        ).scalar()
        if exists:
            return False

    keys = list(clean_payload.keys())
    quoted_keys = [
        quote_sql_identifier(
            key,
            dialect=db.engine.dialect,
            allowed=cols,
        )
        for key in keys
    ]
    parameter_names = [
        f"value_{index}"
        for index in range(len(keys))
    ]
    parameters = {
        parameter_name: clean_payload[key]
        for key, parameter_name in zip(
            keys,
            parameter_names,
            strict=True,
        )
    }
    sql = (
        f"INSERT INTO {quoted_table_name} "
        f"({', '.join(quoted_keys)}) "
        f"VALUES ({', '.join(':' + name for name in parameter_names)})"
    )
    db.session.execute(text(sql), parameters)
    return True


def ensure_phase3_columns() -> None:
    """Faz 3 için gerekli kolonları mevcut tablolara güvenli şekilde ekler."""
    ddl_statements = [
        # Puanlama geçmişi
        "ALTER TABLE performance_scoring_history ADD COLUMN IF NOT EXISTS evaluation_id INTEGER",
        "ALTER TABLE performance_scoring_history ADD COLUMN IF NOT EXISTS period_id INTEGER",
        "ALTER TABLE performance_scoring_history ADD COLUMN IF NOT EXISTS employee_id INTEGER",
        "ALTER TABLE performance_scoring_history ADD COLUMN IF NOT EXISTS scorer_user_id INTEGER",
        "ALTER TABLE performance_scoring_history ADD COLUMN IF NOT EXISTS scorer_name VARCHAR(255)",
        "ALTER TABLE performance_scoring_history ADD COLUMN IF NOT EXISTS scorer_role VARCHAR(120)",
        "ALTER TABLE performance_scoring_history ADD COLUMN IF NOT EXISTS manager_level VARCHAR(50)",
        "ALTER TABLE performance_scoring_history ADD COLUMN IF NOT EXISTS score_value NUMERIC(6,2)",
        "ALTER TABLE performance_scoring_history ADD COLUMN IF NOT EXISTS score_source VARCHAR(120)",
        "ALTER TABLE performance_scoring_history ADD COLUMN IF NOT EXISTS general_comment TEXT",
        "ALTER TABLE performance_scoring_history ADD COLUMN IF NOT EXISTS action_status VARCHAR(80)",
        "ALTER TABLE performance_scoring_history ADD COLUMN IF NOT EXISTS next_owner_user_id INTEGER",
        "ALTER TABLE performance_scoring_history ADD COLUMN IF NOT EXISTS next_owner_name VARCHAR(255)",
        "ALTER TABLE performance_scoring_history ADD COLUMN IF NOT EXISTS next_stage VARCHAR(120)",
        "ALTER TABLE performance_scoring_history ADD COLUMN IF NOT EXISTS action_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "ALTER TABLE performance_scoring_history ADD COLUMN IF NOT EXISTS event_key VARCHAR(80)",
        # Süreç adımları
        "ALTER TABLE performance_process_flow_steps ADD COLUMN IF NOT EXISTS evaluation_id INTEGER",
        "ALTER TABLE performance_process_flow_steps ADD COLUMN IF NOT EXISTS period_id INTEGER",
        "ALTER TABLE performance_process_flow_steps ADD COLUMN IF NOT EXISTS employee_id INTEGER",
        "ALTER TABLE performance_process_flow_steps ADD COLUMN IF NOT EXISTS step_code VARCHAR(120)",
        "ALTER TABLE performance_process_flow_steps ADD COLUMN IF NOT EXISTS step_title VARCHAR(255)",
        "ALTER TABLE performance_process_flow_steps ADD COLUMN IF NOT EXISTS step_order INTEGER",
        "ALTER TABLE performance_process_flow_steps ADD COLUMN IF NOT EXISTS actor_user_id INTEGER",
        "ALTER TABLE performance_process_flow_steps ADD COLUMN IF NOT EXISTS actor_name VARCHAR(255)",
        "ALTER TABLE performance_process_flow_steps ADD COLUMN IF NOT EXISTS owner_user_id INTEGER",
        "ALTER TABLE performance_process_flow_steps ADD COLUMN IF NOT EXISTS owner_name VARCHAR(255)",
        "ALTER TABLE performance_process_flow_steps ADD COLUMN IF NOT EXISTS status VARCHAR(80)",
        "ALTER TABLE performance_process_flow_steps ADD COLUMN IF NOT EXISTS description TEXT",
        "ALTER TABLE performance_process_flow_steps ADD COLUMN IF NOT EXISTS action_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "ALTER TABLE performance_process_flow_steps ADD COLUMN IF NOT EXISTS event_key VARCHAR(80)",
    ]
    index_statements = [
        "CREATE INDEX IF NOT EXISTS ix_perf_scoring_event_key ON performance_scoring_history(event_key)",
        "CREATE INDEX IF NOT EXISTS ix_perf_scoring_eval_actor ON performance_scoring_history(evaluation_id, scorer_user_id)",
        "CREATE INDEX IF NOT EXISTS ix_perf_scoring_employee_period ON performance_scoring_history(employee_id, period_id)",
        "CREATE INDEX IF NOT EXISTS ix_perf_flow_step_event_key ON performance_process_flow_steps(event_key)",
        "CREATE INDEX IF NOT EXISTS ix_perf_flow_step_eval_status ON performance_process_flow_steps(evaluation_id, status)",
        "CREATE INDEX IF NOT EXISTS ix_perf_flow_step_owner_status ON performance_process_flow_steps(owner_user_id, status)",
    ]
    for sql in ddl_statements + index_statements:
        db.session.execute(text(sql))
    db.session.commit()


def record_scoring_history(
    *,
    evaluation_id: int | None = None,
    period_id: int | None = None,
    employee_id: int | None = None,
    scorer_user_id: int | None = None,
    scorer_name: str | None = None,
    scorer_role: str | None = None,
    manager_level: str | None = None,
    score_value: float | None = None,
    score_source: str = "performance_scoring",
    general_comment: str | None = None,
    action_status: str = "puanlandi",
    next_owner_user_id: int | None = None,
    next_owner_name: str | None = None,
    next_stage: str | None = None,
    action_at: datetime | None = None,
    commit: bool = True,
) -> bool:
    """Tek bir puanlama hareketini geçmişe ve süreç adımına yazar."""
    ensure_phase3_columns()
    action_at = action_at or _now()
    payload = {
        "evaluation_id": evaluation_id,
        "period_id": period_id,
        "employee_id": employee_id,
        "scorer_user_id": scorer_user_id,
        "scorer_name": scorer_name,
        "scorer_role": scorer_role,
        "manager_level": manager_level,
        "score_value": score_value,
        "score_source": score_source,
        "general_comment": general_comment,
        "action_status": action_status,
        "next_owner_user_id": next_owner_user_id,
        "next_owner_name": next_owner_name,
        "next_stage": next_stage,
        "action_at": action_at,
    }
    payload["event_key"] = _event_key(payload)

    inserted_history = _insert_if_columns(SCORING_HISTORY_TABLE, payload, unique_key="event_key")

    step_payload = {
        "evaluation_id": evaluation_id,
        "period_id": period_id,
        "employee_id": employee_id,
        "step_code": "scoring_recorded",
        "step_title": "Puanlama Kaydı Oluşturuldu",
        "step_order": 30,
        "actor_user_id": scorer_user_id,
        "actor_name": scorer_name,
        "owner_user_id": next_owner_user_id,
        "owner_name": next_owner_name,
        "status": action_status,
        "description": next_stage or "Puanlama geçmişi kayıt altına alındı.",
        "action_at": action_at,
        "event_key": payload["event_key"],
    }
    inserted_step = _insert_if_columns(FLOW_STEPS_TABLE, step_payload, unique_key="event_key")

    if commit:
        db.session.commit()
    return bool(inserted_history or inserted_step)


def record_from_mapping(row: Mapping[str, Any], *, commit: bool = True) -> bool:
    """Farklı tablo/kolon adlarından gelen satırı normalize ederek kaydeder."""
    return record_scoring_history(
        evaluation_id=_first_value(row, "evaluation_id", "evaluation_id_id", "id"),
        period_id=_first_value(row, "period_id", "performance_period_id"),
        employee_id=_first_value(row, "employee_id", "user_id", "personnel_id", "evaluated_user_id"),
        scorer_user_id=_first_value(row, "scorer_user_id", "manager_user_id", "evaluator_id", "created_by_id", "updated_by_id"),
        scorer_name=_safe_str(_first_value(row, "scorer_name", "manager_name", "evaluator_name", "created_by_name"), "Bilinmiyor"),
        scorer_role=_safe_str(_first_value(row, "scorer_role", "manager_role", "evaluator_role"), ""),
        manager_level=_safe_str(_first_value(row, "manager_level", "manager_slot", "level", "slot"), ""),
        score_value=_first_value(row, "score_value", "score", "final_score", "final_total_100", "total_score"),
        general_comment=_first_value(row, "general_comment", "comment", "notes", "opinion"),
        action_status=_safe_str(_first_value(row, "action_status", "status"), "puanlandi"),
        next_owner_user_id=_first_value(row, "next_owner_user_id", "next_manager_id", "current_owner_id"),
        next_owner_name=_first_value(row, "next_owner_name", "next_manager_name", "current_owner_name"),
        next_stage=_first_value(row, "next_stage", "flow_status", "current_stage"),
        action_at=_first_value(row, "action_at", "scored_at", "updated_at", "created_at") or _now(),
        commit=commit,
    )


def _backfill_phase3_from_evaluation_items(limit: int | None = None) -> dict[str, int]:
    """Mevcut performans kalemlerinden amir bazlı puanlama geçmişi üretir.

    Canlıda Başkan Onayları ve karne ekranında teknik bekleme metni görünmemesi için
    gerçek performans değerlendirme kalemleri amir seviyesine göre özetlenir.
    """
    if not _table_exists("performance_evaluation_items") or not _table_exists("performance_evaluations"):
        return {"scanned": 0, "inserted": 0}

    item_cols = _columns("performance_evaluation_items")
    eval_cols = _columns("performance_evaluations")
    if "evaluation_id" not in item_cols or "manager_level" not in item_cols:
        return {"scanned": 0, "inserted": 0}

    if "score_100" in item_cols:
        score_expr = "ROUND(AVG(NULLIF(i.score_100, 0))::numeric, 2)"
        score_filter = "i.score_100 IS NOT NULL AND i.score_100 > 0"
    elif "score" in item_cols:
        score_expr = "ROUND(AVG((((i.score::numeric - 1) / 4) * 100))::numeric, 2)"
        score_filter = "i.score IS NOT NULL"
    else:
        return {"scanned": 0, "inserted": 0}

    evaluator_case_parts = []
    if "level_1_evaluator_id" in eval_cols:
        evaluator_case_parts.append("WHEN 1 THEN e.level_1_evaluator_id")
    if "level_2_evaluator_id" in eval_cols:
        evaluator_case_parts.append("WHEN 2 THEN e.level_2_evaluator_id")
    if "level_3_evaluator_id" in eval_cols:
        evaluator_case_parts.append("WHEN 3 THEN e.level_3_evaluator_id")
    evaluator_expr = "CASE i.manager_level " + " ".join(evaluator_case_parts) + " ELSE NULL END" if evaluator_case_parts else "NULL"

    time_candidates = []
    for alias, cols in (("i", item_cols), ("e", eval_cols)):
        if "updated_at" in cols:
            time_candidates.append(f"{alias}.updated_at")
        if "created_at" in cols:
            time_candidates.append(f"{alias}.created_at")
    time_expr = "COALESCE(" + ", ".join(time_candidates + ["CURRENT_TIMESTAMP"]) + ")"

    limit_sql = "LIMIT :limit" if limit else ""
    params = {"limit": int(limit)} if limit else {}
    rows = db.session.execute(
        text(
            f"""
            WITH item_summary AS (
                SELECT
                    i.evaluation_id,
                    e.period_id,
                    e.employee_id,
                    i.manager_level,
                    {evaluator_expr} AS scorer_user_id,
                    {score_expr} AS score_value,
                    MAX({time_expr}) AS action_at
                FROM performance_evaluation_items i
                JOIN performance_evaluations e ON e.id = i.evaluation_id
                WHERE {score_filter}
                GROUP BY i.evaluation_id, e.period_id, e.employee_id, i.manager_level, scorer_user_id
                ORDER BY i.evaluation_id, i.manager_level
                {limit_sql}
            )
            SELECT
                s.*,
                NULLIF(TRIM(CONCAT_WS(' ', u.ad, u.soyad)), '') AS scorer_full_name,
                u.email AS scorer_email
            FROM item_summary s
            LEFT JOIN users u ON u.id = s.scorer_user_id
            """
        ),
        params,
    ).mappings().all()

    inserted = 0
    scanned = 0
    for row in rows:
        scanned += 1
        level = row.get("manager_level")
        scorer_name = row.get("scorer_full_name") or row.get("scorer_email") or (f"{level}. amir" if level else "Amir")
        try:
            ok = record_scoring_history(
                evaluation_id=row.get("evaluation_id"),
                period_id=row.get("period_id"),
                employee_id=row.get("employee_id"),
                scorer_user_id=row.get("scorer_user_id"),
                scorer_name=scorer_name,
                manager_level=str(level or ""),
                score_value=row.get("score_value"),
                score_source="performance_evaluation_items",
                action_status="puanlandi",
                next_stage="Değerlendirme zinciri izlendi",
                next_owner_name=None,
                action_at=row.get("action_at") or _now(),
                commit=False,
            )
            if ok:
                inserted += 1
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/performance/process_engine_phase3_history.py:323)")
            db.session.rollback()
            ensure_phase3_columns()
            continue
    db.session.commit()
    return {"scanned": scanned, "inserted": inserted}


def backfill_from_existing_evaluations(limit: int | None = None) -> dict[str, int]:
    """Mevcut değerlendirme tablolarından okunabilen puanlama özetlerini geçmişe işler.

    Öncelik, gerçek kriter puanlarının tutulduğu performance_evaluation_items tablosudur.
    Diğer eski/yardımcı tablolar destek amaçlı taranır. Fonksiyon canlı akışı bozmaz;
    uygun kaynak yoksa sıfır kayıtla döner.
    """
    ensure_phase3_columns()
    inserted = 0
    scanned = 0

    item_summary = _backfill_phase3_from_evaluation_items(limit=limit)
    inserted += int(item_summary.get("inserted", 0) or 0)
    scanned += int(item_summary.get("scanned", 0) or 0)

    source_tables = [
        "performance_evaluation_scores",
        "performance_evaluation_answers",
        "performance_evaluations",
        "performance_tasks",
        "performance_assignments",
        "evaluation_assignments",
    ]
    for table_name in source_tables:
        if not _table_exists(table_name):
            continue
        cols = _columns(table_name)
        select_cols = list(cols)
        if not select_cols:
            continue
        sql = f"SELECT {', '.join(select_cols)} FROM {table_name}"
        if limit:
            sql += " LIMIT :limit"
            rows = db.session.execute(text(sql), {"limit": int(limit)}).mappings().all()
        else:
            rows = db.session.execute(text(sql)).mappings().all()
        for row in rows:
            scanned += 1
            if not any(key in row for key in ("score", "score_value", "final_score", "final_total_100", "total_score", "status")):
                continue
            try:
                if record_from_mapping(dict(row), commit=False):
                    inserted += 1
            except Exception:
                logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
                __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/performance/process_engine_phase3_history.py:375)")
                db.session.rollback()
                ensure_phase3_columns()
                continue
    db.session.commit()
    return {"scanned": scanned, "inserted": inserted}
