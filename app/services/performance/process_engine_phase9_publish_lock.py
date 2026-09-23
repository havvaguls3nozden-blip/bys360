from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy import inspect, text

from app.extensions import db

logger = logging.getLogger(__name__)

PHASE9_VERSION = "2026-04-30-performance-process-engine-phase9-publish-lock"
PHASE9_PUBLISH_LOCK_SERVICE = True
LOW_SCORE_THRESHOLD = Decimal("70")

APPROVED_STATUSES = {
    "approved",
    "president_approved",
    "onaylandi",
    "onaylandı",
    "baskan_onayladi",
    "baskan_onayladı",
    "completed",
    "finalized",
    "kesinlesti",
    "kesinleşti",
}

RETURNED_STATUSES = {
    "returned",
    "rejected",
    "iade",
    "iade_edildi",
    "president_returned",
    "baskan_iade",
}

PENDING_STATUSES = {
    "pending",
    "president_pending",
    "baskan_onayi_bekliyor",
    "başkan_onayı_bekliyor",
    "onay_bekliyor",
}


def _table_exists(table_name: str) -> bool:
    """BYS360 DEFECT AL: raw PostgreSQL-only ``information_schema.tables``
    query (filtered by the PostgreSQL-only ``current_schema()`` SQL
    function) replaced with SQLAlchemy's ``inspect()``, which is
    dialect-neutral by construction."""
    return bool(inspect(db.engine).has_table(table_name))


def _column_exists(table_name: str, column_name: str) -> bool:
    if not _table_exists(table_name):
        return False
    return any(
        column["name"] == column_name
        for column in inspect(db.engine).get_columns(table_name)
    )


def _as_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return None


def _normalize_status(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


@dataclass(frozen=True)
class PublishLockResult:
    evaluation_id: int | None
    flow_id: int | None
    period_id: int | None
    employee_id: int | None
    final_score: Decimal | None
    publish_allowed: bool
    lock_status: str
    lock_reason: str
    required_action: str
    blocked_by: str
    president_approval_id: int | None
    president_status: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "evaluation_id": self.evaluation_id,
            "flow_id": self.flow_id,
            "period_id": self.period_id,
            "employee_id": self.employee_id,
            "final_score": str(self.final_score) if self.final_score is not None else None,
            "publish_allowed": self.publish_allowed,
            "lock_status": self.lock_status,
            "lock_reason": self.lock_reason,
            "required_action": self.required_action,
            "blocked_by": self.blocked_by,
            "president_approval_id": self.president_approval_id,
            "president_status": self.president_status,
        }


def _latest_approval(evaluation_id: int | None, flow_id: int | None) -> dict[str, Any] | None:
    if not _table_exists("performance_president_approvals"):
        return None
    conditions: list[str] = []
    params: dict[str, Any] = {}
    if evaluation_id is not None:
        conditions.append("evaluation_id = :evaluation_id")
        params["evaluation_id"] = evaluation_id
    if flow_id is not None and _column_exists("performance_president_approvals", "flow_id"):
        conditions.append("flow_id = :flow_id")
        params["flow_id"] = flow_id
    if not conditions:
        return None
    # BYS360 DEFECT AM: the status expression referenced decision_status/
    # visible_status, neither of which is a real column on
    # performance_president_approvals (confirmed by the model and by every
    # migration that owns this table) -- status (already first in the
    # COALESCE) is the real, correct source.
    row = db.session.execute(
        text(
            f"""
            SELECT id,
                   COALESCE(status, '') AS status,
                   COALESCE(final_score, score) AS final_score,
                   president_user_id,
                   requested_at
              FROM performance_president_approvals
             WHERE {' OR '.join(conditions)}
             ORDER BY id DESC
             LIMIT 1
            """
        ),
        params,
    ).mappings().first()
    return dict(row) if row else None


def _latest_flow(evaluation_id: int) -> dict[str, Any] | None:
    """BYS360 DEFECT AM: query referenced ``president_required``, which does
    not exist on performance_process_flows -- the real column is
    ``president_approval_required`` (confirmed by the model and by every
    migration that owns this table). The output key stays ``president_required``
    (via the AS alias) since evaluate_publish_lock() reads that exact key.
    ``current_stage`` was dropped: it is not a real column on this table and
    is never read by any caller in this module."""
    if not _table_exists("performance_process_flows"):
        return None
    row = db.session.execute(
        text(
            """
            SELECT id,
                   evaluation_id,
                   period_id,
                   employee_id,
                   final_score,
                   COALESCE(president_approval_required, false) AS president_required,
                   COALESCE(president_approval_status, '') AS president_status,
                   COALESCE(current_status, '') AS current_status
              FROM performance_process_flows
             WHERE evaluation_id = :evaluation_id
             ORDER BY id DESC
             LIMIT 1
            """
        ),
        {"evaluation_id": evaluation_id},
    ).mappings().first()
    return dict(row) if row else None


def evaluate_publish_lock(evaluation_id: int) -> PublishLockResult:
    """Return the publication decision for a single evaluation.

    This function is intentionally read-only. It does not publish, finalize, or
    change an evaluation. It only tells the caller whether publication is allowed.
    """
    flow = _latest_flow(evaluation_id)
    if not flow:
        return PublishLockResult(
            evaluation_id=evaluation_id,
            flow_id=None,
            period_id=None,
            employee_id=None,
            final_score=None,
            publish_allowed=True,
            lock_status="allowed_no_flow",
            lock_reason="Süreç kaydı bulunmadığı için Faz 9 kilidi uygulanmadı.",
            required_action="Süreç senkronu gerekiyorsa Faz 7 ve Faz 8 senkronları çalıştırılmalıdır.",
            blocked_by="",
            president_approval_id=None,
            president_status="",
        )

    final_score = _as_decimal(flow.get("final_score"))
    flow_id = int(flow["id"]) if flow.get("id") is not None else None
    approval = _latest_approval(evaluation_id=evaluation_id, flow_id=flow_id)
    president_status = _normalize_status(approval.get("status") if approval else flow.get("president_status"))
    president_approval_id = int(approval["id"]) if approval and approval.get("id") is not None else None

    requires_president = bool(flow.get("president_required")) or (
        final_score is not None and final_score < LOW_SCORE_THRESHOLD
    )

    if not requires_president:
        return PublishLockResult(
            evaluation_id=evaluation_id,
            flow_id=flow_id,
            period_id=flow.get("period_id"),
            employee_id=flow.get("employee_id"),
            final_score=final_score,
            publish_allowed=True,
            lock_status="allowed",
            lock_reason="Başkan onayı gerektiren nihai 70 altı durum bulunmadı.",
            required_action="Yayın öncesi diğer standart kontroller uygulanabilir.",
            blocked_by="",
            president_approval_id=president_approval_id,
            president_status=president_status,
        )

    if president_status in APPROVED_STATUSES:
        return PublishLockResult(
            evaluation_id=evaluation_id,
            flow_id=flow_id,
            period_id=flow.get("period_id"),
            employee_id=flow.get("employee_id"),
            final_score=final_score,
            publish_allowed=True,
            lock_status="allowed_president_approved",
            lock_reason="70 altı nihai sonuç için Başkan onayı tamamlandı.",
            required_action="Sonuç yayın/kesinleşme sürecine alınabilir.",
            blocked_by="",
            president_approval_id=president_approval_id,
            president_status=president_status,
        )

    if president_status in RETURNED_STATUSES:
        return PublishLockResult(
            evaluation_id=evaluation_id,
            flow_id=flow_id,
            period_id=flow.get("period_id"),
            employee_id=flow.get("employee_id"),
            final_score=final_score,
            publish_allowed=False,
            lock_status="blocked_president_returned",
            lock_reason="Başkan tarafından iade edilen 70 altı nihai sonuç yayınlanamaz.",
            required_action="İade gerekçesine göre süreç yeniden değerlendirilmelidir.",
            blocked_by="president_approval",
            president_approval_id=president_approval_id,
            president_status=president_status,
        )

    return PublishLockResult(
        evaluation_id=evaluation_id,
        flow_id=flow_id,
        period_id=flow.get("period_id"),
        employee_id=flow.get("employee_id"),
        final_score=final_score,
        publish_allowed=False,
        lock_status="blocked_president_pending",
        lock_reason="Bu değerlendirme 70 altı nihai sonuç içerdiği için Başkan onayı tamamlanmadan yayınlanamaz.",
        required_action="Başkan Onayları ekranında onay süreci tamamlanmalıdır.",
        blocked_by="president_approval",
        president_approval_id=president_approval_id,
        president_status=president_status or "pending",
    )


def _upsert_publish_lock(result: PublishLockResult) -> None:
    if result.evaluation_id is None:
        return
    db.session.execute(
        text(
            """
            INSERT INTO performance_publish_locks
                (flow_id, evaluation_id, period_id, employee_id, final_score,
                 lock_status, lock_reason, required_action, blocked_by,
                 president_approval_id, president_status, publish_allowed,
                 process_version, created_at, updated_at)
            VALUES
                (:flow_id, :evaluation_id, :period_id, :employee_id, :final_score,
                 :lock_status, :lock_reason, :required_action, :blocked_by,
                 :president_approval_id, :president_status, :publish_allowed,
                 :process_version, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (evaluation_id)
            DO UPDATE SET
                 flow_id = EXCLUDED.flow_id,
                 period_id = EXCLUDED.period_id,
                 employee_id = EXCLUDED.employee_id,
                 final_score = EXCLUDED.final_score,
                 lock_status = EXCLUDED.lock_status,
                 lock_reason = EXCLUDED.lock_reason,
                 required_action = EXCLUDED.required_action,
                 blocked_by = EXCLUDED.blocked_by,
                 president_approval_id = EXCLUDED.president_approval_id,
                 president_status = EXCLUDED.president_status,
                 publish_allowed = EXCLUDED.publish_allowed,
                 process_version = EXCLUDED.process_version,
                 updated_at = CURRENT_TIMESTAMP
            """
        ),
        {
            "flow_id": result.flow_id,
            "evaluation_id": result.evaluation_id,
            "period_id": result.period_id,
            "employee_id": result.employee_id,
            "final_score": result.final_score,
            "lock_status": result.lock_status,
            "lock_reason": result.lock_reason,
            "required_action": result.required_action,
            "blocked_by": result.blocked_by,
            "president_approval_id": result.president_approval_id,
            "president_status": result.president_status,
            "publish_allowed": result.publish_allowed,
            "process_version": PHASE9_VERSION,
        },
    )
    if result.flow_id is not None and _column_exists("performance_process_flows", "publish_lock_status"):
        db.session.execute(
            text(
                """
                UPDATE performance_process_flows
                   SET publish_lock_status = :lock_status,
                       publish_lock_reason = :lock_reason,
                       publish_lock_required_action = :required_action,
                       publish_allowed = :publish_allowed,
                       publish_checked_at = CURRENT_TIMESTAMP,
                       process_version = :process_version
                 WHERE id = :flow_id
                """
            ),
            {
                "flow_id": result.flow_id,
                "lock_status": result.lock_status,
                "lock_reason": result.lock_reason,
                "required_action": result.required_action,
                "publish_allowed": result.publish_allowed,
                "process_version": PHASE9_VERSION,
            },
        )


def synchronize_publish_locks(limit: int | None = None) -> dict[str, Any]:
    if not _table_exists("performance_process_flows"):
        return {"checked": 0, "blocked": 0, "allowed": 0, "message": "performance_process_flows yok"}

    sql_limit = " LIMIT :limit" if limit else ""
    params = {"limit": limit} if limit else {}
    rows = db.session.execute(
        text(
            f"""
            SELECT DISTINCT evaluation_id
              FROM performance_process_flows
             WHERE evaluation_id IS NOT NULL
               AND (
                    COALESCE(president_required, false) = true
                    OR COALESCE(final_score, 100) < 70
                    OR COALESCE(president_status, president_approval_status, '') <> ''
               )
             ORDER BY evaluation_id DESC
             {sql_limit}
            """
        ),
        params,
    ).scalars().all()

    checked = 0
    blocked = 0
    allowed = 0
    for evaluation_id in rows:
        result = evaluate_publish_lock(int(evaluation_id))
        _upsert_publish_lock(result)
        checked += 1
        if result.publish_allowed:
            allowed += 1
        else:
            blocked += 1
    db.session.commit()
    return {
        "checked": checked,
        "blocked": blocked,
        "allowed": allowed,
        "version": PHASE9_VERSION,
    }
