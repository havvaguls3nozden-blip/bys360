from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.extensions import db

PHASE4_VERSION = "2026-04-29-process-flow-phase4"

_FINALIZED_STATUS_TOKENS = {"tamamlandi", "tamamlandı", "completed", "published"}


def ensure_process_flow_for_evaluation(evaluation: Any, *, flush: bool = True) -> Any:
    """Değerlendirmenin genel süreç takip kaydını oluşturur veya günceller.

    BYS360 DEFECT AP: performance_process_flows tablosunun production'da
    erişilebilir hiçbir writer'ı yoktu -- sync_phase4_flows()/_ensure_flow()
    (bu dosyanın kendi eski Faz 4 yardımcıları) ve Phase7'nin eşdeğer akış
    oluşturma yolu hiçbir yerden çağrılmıyordu, bu yüzden Süreç Takibi ekranı
    doğru okuma mantığına sahip olsa da gösterecek veri bulamıyordu.

    Bu fonksiyon, aynı süreç içinde zaten canlı ve çağrılan
    low_score_process_service.ensure_low_score_process_for_evaluation ile
    birebir aynı çağrı noktasından (değerlendirme tamamlandığında) tetiklenir
    ve aynı ORM tabanlı "varsa güncelle, yoksa oluştur" desenini izler.

    Bilinçli olarak ayrık tutulur: başkan onayı gerekip gerekmediği veya
    düşük puan durumu gibi iş kararları burada tekrarlanmaz. Bu kayıt
    yalnızca değerlendirmenin genel süreç durumunu (aşama, son işlem
    zamanı, final puan) izler; düşük puan/başkan onayı iş akışının kendi
    kaydı (PerformanceLowScoreProcess) tamamen ayrı ve o konuda tek
    yetkili kaynak olmaya devam eder.
    """
    if evaluation is None or getattr(evaluation, "id", None) is None:
        return None

    from app.models.performance_process_engine_models import PerformanceProcessFlow

    status = (getattr(evaluation, "status", "") or "").strip().lower()
    step_key = status or "created"
    is_finalized = status in _FINALIZED_STATUS_TOKENS
    now = datetime.utcnow()

    flow = PerformanceProcessFlow.query.filter_by(evaluation_id=evaluation.id).first()
    if flow is not None:
        flow.period_id = getattr(evaluation, "period_id", flow.period_id)
        flow.employee_id = getattr(evaluation, "employee_id", flow.employee_id)
        flow.current_step_key = step_key
        flow.current_status = step_key
        flow.final_score = getattr(evaluation, "final_total_100", flow.final_score)
        flow.is_finalized = is_finalized
        flow.last_action_at = now
        if flush:
            db.session.flush()
        return flow

    new_flow = PerformanceProcessFlow(
        evaluation_id=evaluation.id,
        period_id=getattr(evaluation, "period_id", None),
        employee_id=getattr(evaluation, "employee_id", None),
        current_step_key=step_key,
        current_status=step_key,
        final_score=getattr(evaluation, "final_total_100", None),
        is_finalized=is_finalized,
        started_at=now,
        last_action_at=now,
        rule_version=PHASE4_VERSION,
    )
    try:
        with db.session.begin_nested():
            db.session.add(new_flow)
            db.session.flush()
    except IntegrityError:
        # Eşzamanlı iki çağrı aynı değerlendirme için yarışırsa (evaluation_id
        # tekil alan): kaybeden tarafın eklemesi geri alınır (yalnızca bu
        # savepoint kapsamında -- çağıranın kendi bekleyen değişiklikleri
        # etkilenmez) ve kazanan tarafın kaydı okunup döndürülür.
        existing = PerformanceProcessFlow.query.filter_by(evaluation_id=evaluation.id).first()
        if existing is None:
            raise
        return existing
    return new_flow


@dataclass(frozen=True)
class Phase4SyncResult:
    flows_created: int = 0
    flows_updated: int = 0
    steps_created: int = 0


def _scalar(sql: str, params: dict[str, Any] | None = None) -> Any:
    return db.session.execute(text(sql), params or {}).scalar()


def _rows(sql: str, params: dict[str, Any] | None = None) -> list[Any]:
    return list(db.session.execute(text(sql), params or {}).mappings())


def table_exists(table_name: str) -> bool:
    """BYS360 DEFECT AJ: raw PostgreSQL-only ``information_schema.tables``
    query replaced with SQLAlchemy's ``inspect()``, which is dialect-neutral
    by construction (works identically against SQLite/PostgreSQL) -- the
    same proven pattern already used by process_engine_phase3_history.py's
    ``_table_exists`` and process_engine_phase8_tracking.py's own fixed
    helpers."""
    return bool(inspect(db.engine).has_table(table_name))


def column_exists(table_name: str, column_name: str) -> bool:
    return column_name in _table_columns(table_name)


def _add_column(table_name: str, column_name: str, ddl_type: str) -> None:
    """BYS360 DEFECT AJ: ``ADD COLUMN IF NOT EXISTS`` is PostgreSQL-only --
    SQLite raises ``sqlite3.OperationalError: near "EXISTS": syntax error``
    on it unconditionally (confirmed empirically, identical to Defect AI's
    finding in process_engine_phase8_tracking.py). Existence is checked
    first via ``column_exists`` (now dialect-neutral), then a plain
    ``ADD COLUMN`` (portable to both dialects) runs only when the column is
    actually missing."""
    if column_exists(table_name, column_name):
        return
    db.session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl_type}"))


def _create_index(index_name: str, ddl: str) -> None:
    db.session.execute(text(f"CREATE INDEX IF NOT EXISTS {index_name} {ddl}"))


def apply_phase4_schema() -> None:
    required_tables = [
        "performance_process_flows",
        "performance_process_flow_steps",
        "performance_scoring_history",
    ]
    missing = [name for name in required_tables if not table_exists(name)]
    if missing:
        raise RuntimeError("Faz 4 icin Faz 2 ve Faz 3 tablolari gerekli: " + ", ".join(missing))

    flow_columns = {
        "current_stage": "VARCHAR(120)",
        "current_status": "VARCHAR(80)",
        "current_owner_user_id": "INTEGER",
        "current_owner_name": "VARCHAR(255)",
        "last_action_title": "VARCHAR(255)",
        "last_action_at": "TIMESTAMP",
        "waiting_since": "TIMESTAMP",
        "waiting_days": "INTEGER DEFAULT 0",
        "flow_summary": "TEXT",
        "flow_locked": "BOOLEAN DEFAULT FALSE",
        "is_finalized": "BOOLEAN DEFAULT FALSE",
        "process_version": "VARCHAR(120)",
        "updated_by_engine_at": "TIMESTAMP",
    }
    for column_name, ddl_type in flow_columns.items():
        _add_column("performance_process_flows", column_name, ddl_type)

    step_columns = {
        "step_order": "INTEGER",
        "visible_title": "VARCHAR(255)",
        "visible_status": "VARCHAR(120)",
        "waiting_owner_name": "VARCHAR(255)",
        "duration_days": "INTEGER DEFAULT 0",
        "source_table": "VARCHAR(120)",
        "source_id": "INTEGER",
        "process_version": "VARCHAR(120)",
    }
    for column_name, ddl_type in step_columns.items():
        _add_column("performance_process_flow_steps", column_name, ddl_type)

    db.session.execute(
        text(
            """
            UPDATE performance_process_flows
               SET current_status = COALESCE(current_status, 'takipte'),
                   current_stage = COALESCE(current_stage, 'Süreç oluşturuldu'),
                   waiting_days = COALESCE(waiting_days, 0),
                   flow_locked = COALESCE(flow_locked, FALSE),
                   is_finalized = COALESCE(is_finalized, FALSE),
                   process_version = COALESCE(process_version, :version),
                   updated_by_engine_at = COALESCE(updated_by_engine_at, CURRENT_TIMESTAMP)
            """
        ),
        {"version": PHASE4_VERSION},
    )

    _create_index(
        "ix_perf_flow_current_owner_status",
        "ON performance_process_flows(current_owner_user_id, current_status)",
    )
    _create_index(
        "ix_perf_flow_waiting_since",
        "ON performance_process_flows(waiting_since)",
    )
    _create_index(
        "ix_perf_steps_eval_order_phase4",
        "ON performance_process_flow_steps(evaluation_id, step_order)",
    )
    _create_index(
        "ix_perf_steps_owner_status_phase4",
        "ON performance_process_flow_steps(owner_user_id, status)",
    )

    db.session.commit()


def _table_columns(table_name: str) -> set[str]:
    """BYS360 DEFECT AJ: dialect-neutral via SQLAlchemy ``inspect()``,
    replacing the prior raw PostgreSQL-only ``information_schema.columns``
    query (same fix rationale as ``table_exists`` above)."""
    if not table_exists(table_name):
        return set()
    return {col["name"] for col in inspect(db.engine).get_columns(table_name)}


def _insert_if_columns(table_name: str, payload: dict[str, Any]) -> int:
    available = _table_columns(table_name)
    filtered = {key: value for key, value in payload.items() if key in available}
    if not filtered:
        return 0
    columns = ", ".join(filtered.keys())
    values = ", ".join(f":{key}" for key in filtered)
    db.session.execute(text(f"INSERT INTO {table_name} ({columns}) VALUES ({values})"), filtered)
    return 1


def _update_flow(flow_id: int, payload: dict[str, Any]) -> None:
    available = _table_columns("performance_process_flows")
    filtered = {key: value for key, value in payload.items() if key in available}
    if not filtered:
        return
    assignments = ", ".join(f"{key} = :{key}" for key in filtered)
    filtered["flow_id"] = flow_id
    db.session.execute(text(f"UPDATE performance_process_flows SET {assignments} WHERE id = :flow_id"), filtered)


def _find_flow_id(evaluation_id: int | None, period_id: int | None, employee_id: int | None) -> int | None:
    if evaluation_id is not None and column_exists("performance_process_flows", "evaluation_id"):
        found = _scalar(
            "SELECT id FROM performance_process_flows WHERE evaluation_id = :evaluation_id ORDER BY id DESC LIMIT 1",
            {"evaluation_id": evaluation_id},
        )
        if found:
            return int(found)
    if period_id is not None and employee_id is not None:
        found = _scalar(
            """
            SELECT id
            FROM performance_process_flows
            WHERE period_id = :period_id
              AND employee_id = :employee_id
            ORDER BY id DESC
            LIMIT 1
            """,
            {"period_id": period_id, "employee_id": employee_id},
        )
        if found:
            return int(found)
    return None


def _ensure_flow(evaluation_id: int | None, period_id: int | None, employee_id: int | None) -> tuple[int | None, bool]:
    existing = _find_flow_id(evaluation_id, period_id, employee_id)
    if existing:
        return existing, False

    payload = {
        "evaluation_id": evaluation_id,
        "period_id": period_id,
        "employee_id": employee_id,
        "current_stage": "Süreç oluşturuldu",
        "current_status": "takipte",
        "last_action_title": "Süreç kaydı oluşturuldu",
        "last_action_at": datetime.utcnow(),
        "waiting_since": datetime.utcnow(),
        "waiting_days": 0,
        "flow_summary": "Performans değerlendirme süreci izlemeye alındı.",
        "flow_locked": False,
        "is_finalized": False,
        "process_version": PHASE4_VERSION,
        "updated_by_engine_at": datetime.utcnow(),
    }
    _insert_if_columns("performance_process_flows", payload)
    flow_id = _find_flow_id(evaluation_id, period_id, employee_id)
    return flow_id, bool(flow_id)


def _step_exists(evaluation_id: int | None, event_key: str, action_at: Any, actor_user_id: Any) -> bool:
    return bool(
        _scalar(
            """
            SELECT EXISTS (
                SELECT 1
                FROM performance_process_flow_steps
                WHERE COALESCE(evaluation_id, -1) = COALESCE(:evaluation_id, -1)
                  AND COALESCE(event_key, '') = COALESCE(:event_key, '')
                  AND COALESCE(actor_user_id, -1) = COALESCE(:actor_user_id, -1)
                  AND COALESCE(action_at, TIMESTAMP '1970-01-01') = COALESCE(:action_at, TIMESTAMP '1970-01-01')
            )
            """,
            {
                "evaluation_id": evaluation_id,
                "event_key": event_key,
                "actor_user_id": actor_user_id,
                "action_at": action_at,
            },
        )
    )


def _safe_title(value: Any, fallback: str) -> str:
    text_value = str(value or "").strip()
    return text_value if text_value else fallback


def _flow_source_rows() -> list[Any]:
    if table_exists("performance_scoring_history"):
        return _rows(
            """
            SELECT
                id,
                evaluation_id,
                period_id,
                employee_id,
                scorer_user_id,
                scorer_name,
                manager_level,
                score_value,
                action_status,
                event_key,
                next_stage,
                next_owner_user_id,
                next_owner_name,
                action_at
            FROM performance_scoring_history
            ORDER BY COALESCE(action_at, CURRENT_TIMESTAMP), id
            """
        )
    return []


def sync_phase4_flows() -> Phase4SyncResult:
    rows = _flow_source_rows()
    flows_created = 0
    flows_updated = 0
    steps_created = 0

    latest_by_flow: dict[int, Any] = {}
    order_by_flow: dict[int, int] = {}

    for row in rows:
        evaluation_id = row.get("evaluation_id")
        period_id = row.get("period_id")
        employee_id = row.get("employee_id")
        flow_id, created = _ensure_flow(evaluation_id, period_id, employee_id)
        if not flow_id:
            continue
        flows_created += 1 if created else 0
        order_by_flow[flow_id] = order_by_flow.get(flow_id, 0) + 1

        event_key = _safe_title(row.get("event_key"), "puanlama_islemi")
        action_at = row.get("action_at")
        actor_user_id = row.get("scorer_user_id")
        if not _step_exists(evaluation_id, event_key, action_at, actor_user_id):
            step_title = f"{_safe_title(row.get('manager_level'), 'Amir')} puanlama işlemi"
            next_stage = _safe_title(row.get("next_stage"), "Sıradaki aşama belirlenecek")
            waiting_owner = _safe_title(row.get("next_owner_name"), "")
            status = "bekliyor" if waiting_owner or row.get("next_owner_user_id") else "tamamlandı"
            _insert_if_columns(
                "performance_process_flow_steps",
                {
                    "flow_id": flow_id,
                    "evaluation_id": evaluation_id,
                    "period_id": period_id,
                    "employee_id": employee_id,
                    "step_code": event_key,
                    "step_title": step_title,
                    "visible_title": step_title,
                    "visible_status": status,
                    "status": status,
                    "description": f"{_safe_title(row.get('scorer_name'), 'Kullanıcı')} tarafından puanlama kaydı işlendi.",
                    "actor_user_id": actor_user_id,
                    "owner_user_id": row.get("next_owner_user_id"),
                    "waiting_owner_name": waiting_owner,
                    "action_at": action_at,
                    "step_order": order_by_flow[flow_id],
                    "source_table": "performance_scoring_history",
                    "source_id": row.get("id"),
                    "process_version": PHASE4_VERSION,
                    "event_key": event_key,
                },
            )
            steps_created += 1
        latest_by_flow[flow_id] = row

    for flow_id, row in latest_by_flow.items():
        next_owner_user_id = row.get("next_owner_user_id")
        next_owner_name = _safe_title(row.get("next_owner_name"), "")
        next_stage = _safe_title(row.get("next_stage"), "Süreç izleniyor")
        status = "bekliyor" if next_owner_user_id or next_owner_name else "tamamlandı"
        summary = "Süreç sıradaki sorumluya geçti." if status == "bekliyor" else "Puanlama adımı tamamlandı."
        _update_flow(
            flow_id,
            {
                "current_stage": next_stage,
                "current_status": status,
                "current_owner_user_id": next_owner_user_id,
                "current_owner_name": next_owner_name or None,
                "last_action_title": "Puanlama işlemi işlendi",
                "last_action_at": row.get("action_at") or datetime.utcnow(),
                "waiting_since": row.get("action_at") or datetime.utcnow(),
                "waiting_days": 0,
                "flow_summary": summary,
                "is_finalized": status == "tamamlandı",
                "process_version": PHASE4_VERSION,
                "updated_by_engine_at": datetime.utcnow(),
            },
        )
        flows_updated += 1

    db.session.commit()
    return Phase4SyncResult(
        flows_created=flows_created,
        flows_updated=flows_updated,
        steps_created=steps_created,
    )


def phase4_required_columns() -> dict[str, list[str]]:
    return {
        "performance_process_flows": [
            "current_stage",
            "current_status",
            "current_owner_user_id",
            "current_owner_name",
            "last_action_title",
            "last_action_at",
            "waiting_since",
            "waiting_days",
            "flow_summary",
            "process_version",
        ],
        "performance_process_flow_steps": [
            "step_order",
            "visible_title",
            "visible_status",
            "waiting_owner_name",
            "duration_days",
            "source_table",
            "source_id",
            "process_version",
        ],
    }
