# -*- coding: utf-8 -*-
"""BYS360 geri bildirim süreç hattı durum makinesi.

Maintenance'un orta/uzun vadeli önerisindeki P0 -> P1 -> P2 -> P3 -> P4 -> Final
sıralamasını tek merkezde tutar. Bu servis idari karar üretmez; yalnızca
adım sırası, atlama kontrolü ve kurumsal durum etiketlerini sağlar.

Veritabanı tabloları varsa canlı kayıtları okur; tablolar henüz uygulanmadıysa
sözleşme/kontrat modunda güvenli varsayılan durum üretir. Böylece overlay
canlıyı bozmaz, ama schema scripti çalıştırıldığında süreç motoru kayıtlı hale gelir.
"""
from __future__ import annotations


from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable

from sqlalchemy import inspect, text

from app.extensions import db
import logging
logger = logging.getLogger(__name__)


RULE_VERSION = "claude_feedback_state_machine_v1"


@dataclass(frozen=True)
class FeedbackStateStep:
    key: str
    order: int
    title: str
    phase_label: str
    required_previous: tuple[str, ...]
    description: str


STATE_STEPS: tuple[FeedbackStateStep, ...] = (
    FeedbackStateStep(
        key="aftercare",
        order=1,
        title="Görüşme Sonrası Notlar",
        phase_label="P0",
        required_previous=(),
        description="Görüşme kaydı, hazırlık notu, görüşme özeti ve eylem planı başlangıcı.",
    ),
    FeedbackStateStep(
        key="guide",
        order=2,
        title="Görüşme Rehberi",
        phase_label="P1",
        required_previous=("aftercare",),
        description="Yöneticiye kurumsal ve yapıcı görüşme dili sağlayan rehber adımı.",
    ),
    FeedbackStateStep(
        key="integration",
        order=3,
        title="Karne Bağlantısı",
        phase_label="P2",
        required_previous=("aftercare", "guide"),
        description="Personel, dönem, karne ve görüşme hafızasının ilişkilendirilmesi.",
    ),
    FeedbackStateStep(
        key="followup",
        order=4,
        title="Eylem Planı Takibi",
        phase_label="P3",
        required_previous=("aftercare", "guide", "integration"),
        description="Açık aksiyonların takip tarihi, durum ve bildirim kayıtlarıyla izlenmesi.",
    ),
    FeedbackStateStep(
        key="ready",
        order=5,
        title="Yayına Hazırlık Kontrolü",
        phase_label="P4",
        required_previous=("aftercare", "guide", "integration", "followup"),
        description="Yayın öncesi eksik adım, teknik dil ve hazırlık kontrolleri.",
    ),
    FeedbackStateStep(
        key="live_control",
        order=6,
        title="Canlı Kullanım Kontrolü",
        phase_label="Final",
        required_previous=("aftercare", "guide", "integration", "followup", "ready"),
        description="Canlıya uygunluk, veri, bağlantı, yetki ve beyaz ekran riski kontrolü.",
    ),
)

VALID_STATUSES = {"not_started", "in_progress", "completed", "blocked", "skipped"}
COMPLETED_STATUSES = {"completed"}


STATUS_LABELS = {
    "not_started": "Başlamadı",
    "in_progress": "Devam Ediyor",
    "completed": "Tamamlandı",
    "blocked": "Sıra Bekliyor",
    "skipped": "Atlandı",
}

STATUS_CLASS = {
    "not_started": "muted",
    "in_progress": "warn",
    "completed": "ok",
    "blocked": "fail",
    "skipped": "fail",
}


def step_keys() -> list[str]:
    return [step.key for step in STATE_STEPS]


def step_by_key(key: str) -> FeedbackStateStep | None:
    key = str(key or "").strip()
    return next((step for step in STATE_STEPS if step.key == key), None)


def _tables_available() -> bool:
    try:
        inspector = inspect(db.engine)
        tables = set(inspector.get_table_names())
        return {"performance_feedback_pipeline_flows", "performance_feedback_pipeline_steps"}.issubset(tables)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        try:
            db.session.rollback()
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/feedback_process_state_machine.py")
        return False


def _default_statuses() -> dict[str, str]:
    statuses = {step.key: "not_started" for step in STATE_STEPS}
    if STATE_STEPS:
        statuses[STATE_STEPS[0].key] = "in_progress"
    return statuses


def _normalize_status(value: Any) -> str:
    status = str(value or "not_started").strip().lower()
    return status if status in VALID_STATUSES else "not_started"


def _read_statuses(flow_id: int | None = None) -> tuple[dict[str, str], int | None, bool]:
    if not _tables_available():
        return _default_statuses(), None, False

    try:
        selected_flow_id = flow_id
        if selected_flow_id is None:
            row = db.session.execute(
                text("""
                    SELECT id
                    FROM performance_feedback_pipeline_flows
                    WHERE is_active = TRUE
                    ORDER BY updated_at DESC NULLS LAST, id DESC
                    LIMIT 1
                """)
            ).mappings().first()
            selected_flow_id = int(row["id"]) if row else None

        if selected_flow_id is None:
            return _default_statuses(), None, True

        rows = db.session.execute(
            text("""
                SELECT step_key, step_status
                FROM performance_feedback_pipeline_steps
                WHERE flow_id = :flow_id
            """),
            {"flow_id": selected_flow_id},
        ).mappings().all()
        statuses = _default_statuses()
        for row in rows:
            key = str(row.get("step_key") or "")
            if key in statuses:
                statuses[key] = _normalize_status(row.get("step_status"))
        return statuses, selected_flow_id, True
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/feedback_process_state_machine.py | line=181")
        db.session.rollback()
        return _default_statuses(), None, False


def _blocked_by(statuses: dict[str, str], step: FeedbackStateStep) -> list[str]:
    return [key for key in step.required_previous if statuses.get(key) not in COMPLETED_STATUSES]


def can_mark_step(statuses: dict[str, str], step_key: str, target_status: str) -> tuple[bool, str]:
    """Adım atlamayı engelleyen merkezi karar fonksiyonu."""
    step = step_by_key(step_key)
    if step is None:
        return False, "Bilinmeyen süreç adımı."
    target_status = _normalize_status(target_status)
    if target_status == "completed":
        blocked = _blocked_by(statuses, step)
        if blocked:
            labels = [step_by_key(key).title for key in blocked if step_by_key(key)]
            return False, "Önce tamamlanması gereken adımlar: " + ", ".join(labels)
    return True, "Adım sırası uygundur."


def build_feedback_state_snapshot(flow_id: int | None = None) -> dict[str, Any]:
    statuses, selected_flow_id, storage_ready = _read_statuses(flow_id=flow_id)
    rows: list[dict[str, Any]] = []
    blocked_count = 0
    completed_count = 0

    for step in STATE_STEPS:
        stored_status = statuses.get(step.key, "not_started")
        blocked_by = _blocked_by(statuses, step)
        effective_status = "blocked" if blocked_by and stored_status == "not_started" else stored_status
        if effective_status == "completed":
            completed_count += 1
        if effective_status == "blocked":
            blocked_count += 1
        rows.append({
            "key": step.key,
            "order": step.order,
            "title": step.title,
            "phase_label": step.phase_label,
            "description": step.description,
            "status": effective_status,
            "status_label": STATUS_LABELS.get(effective_status, "Başlamadı"),
            "status_class": STATUS_CLASS.get(effective_status, "muted"),
            "blocked_by": blocked_by,
            "blocked_by_labels": [step_by_key(key).title for key in blocked_by if step_by_key(key)],
        })

    total = len(STATE_STEPS)
    percent = int(round((completed_count / total) * 100)) if total else 0
    return {
        "flow_id": selected_flow_id,
        "storage_ready": storage_ready,
        "rule_version": RULE_VERSION,
        "steps": rows,
        "summary": {
            "total": total,
            "completed": completed_count,
            "blocked": blocked_count,
            "percent": percent,
        },
        "note": "P0’dan Final adımına kadar süreç sırası tek merkezde kontrol edilir; önceki adımlar tamamlanmadan sonraki adım tamamlandı yapılamaz.",
    }


def ensure_feedback_pipeline_flow(*, actor_id: int | None = None, title: str = "Geri Bildirim Süreç Hattı") -> int | None:
    """Tablolar uygulanmışsa varsayılan canlı süreç kaydını oluşturur."""
    if not _tables_available():
        return None
    now = datetime.utcnow()
    try:
        row = db.session.execute(
            text("""
                SELECT id
                FROM performance_feedback_pipeline_flows
                WHERE is_active = TRUE
                ORDER BY updated_at DESC NULLS LAST, id DESC
                LIMIT 1
            """)
        ).mappings().first()
        if row:
            return int(row["id"])
        flow_id = db.session.execute(
            text("""
                INSERT INTO performance_feedback_pipeline_flows
                    (title, current_step_key, current_status, is_active, created_by_id, created_at, updated_at, rule_version)
                VALUES
                    (:title, 'aftercare', 'in_progress', TRUE, :actor_id, :now, :now, :rule_version)
                RETURNING id
            """),
            {"title": title, "actor_id": actor_id, "now": now, "rule_version": RULE_VERSION},
        ).scalar()
        for step in STATE_STEPS:
            status = "in_progress" if step.order == 1 else "not_started"
            db.session.execute(
                text("""
                    INSERT INTO performance_feedback_pipeline_steps
                        (flow_id, step_key, step_order, step_title, phase_label, step_status, created_at, updated_at, rule_version)
                    VALUES
                        (:flow_id, :step_key, :step_order, :step_title, :phase_label, :step_status, :now, :now, :rule_version)
                """),
                {
                    "flow_id": flow_id,
                    "step_key": step.key,
                    "step_order": step.order,
                    "step_title": step.title,
                    "phase_label": step.phase_label,
                    "step_status": status,
                    "now": now,
                    "rule_version": RULE_VERSION,
                },
            )
        db.session.commit()
        return int(flow_id)
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/feedback_process_state_machine.py | line=297")
        db.session.rollback()
        return None


def claude_feedback_state_machine_contract() -> dict[str, Any]:
    return {
        "rule_version": RULE_VERSION,
        "step_order": [step.key for step in STATE_STEPS],
        "phase_labels": {step.key: step.phase_label for step in STATE_STEPS},
        "statuses": sorted(VALID_STATUSES),
        "skip_prevention": True,
    }
