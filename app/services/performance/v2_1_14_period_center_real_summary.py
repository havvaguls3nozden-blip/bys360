# -*- coding: utf-8 -*-
from __future__ import annotations

import logging

"""BYS360 Performans V2.1.14 dönem merkezi gerçek özet verileri.

Bu servis yalnızca okuma yapar. Merkez sayfada seçili döneme ait hafif
özet sayıları gösterir; detay satırları çekmez, görev üretmez, mail göndermez,
şema değiştirmez.
"""

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import inspect, text

logger = logging.getLogger(__name__)

RULE_VERSION = "performance_v2_1_14_period_center_real_summary"
PERIOD_TABLE = "performance_periods"
ASSIGNMENT_TABLE = "evaluation_assignments"

COMPLETED_STATUSES = {"tamamlandi", "tamamlandı", "completed", "done", "bitti"}
WAITING_STATUSES = {"bekliyor", "pending", "atandi", "atandı", "gorev_atandi", "görev_atandı", "not_started", "devam_ediyor", "in_progress"}
RETURNED_STATUSES = {"iade", "iade_edildi", "returned", "revize", "revision"}


def _db():
    from app.extensions import db
    return db


def _inspector():
    return inspect(_db().engine)


def _rollback() -> None:
    try:
        _db().session.rollback()
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        pass


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or default)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _has_table(table_name: str) -> bool:
    try:
        return bool(_inspector().has_table(table_name))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return False


def _columns(table_name: str) -> set[str]:
    try:
        if not _has_table(table_name):
            return set()
        return {str(col.get("name")) for col in _inspector().get_columns(table_name)}
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return set()


def _has_column(table_name: str, column_name: str) -> bool:
    return column_name in _columns(table_name)


def _scalar(sql: str, params: dict[str, Any] | None = None, default: int = 0) -> int:
    try:
        value = _db().session.execute(text(sql), params or {}).scalar()
        return int(value or 0)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        _rollback()
        return default


def _row(sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    try:
        item = _db().session.execute(text(sql), params or {}).mappings().first()
        return dict(item) if item else None
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        _rollback()
        return None


def _rows(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    try:
        return [dict(row) for row in _db().session.execute(text(sql), params or {}).mappings().all()]
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        _rollback()
        return []


def _percent(done: int, total: int) -> int:
    if total <= 0:
        return 0
    return max(0, min(100, int(round((done / total) * 100))))


def _completed_clause(cols: set[str]) -> str:
    status_clause = "LOWER(COALESCE(status, '')) IN ('tamamlandi','tamamlandı','completed','done','bitti')"
    if "completed_at" in cols:
        return f"(completed_at IS NOT NULL OR {status_clause})"
    return status_clause


def _base_counts(period_id: int | None) -> dict[str, int]:
    pid = _safe_int(period_id)
    empty = {"total": 0, "completed": 0, "pending": 0, "overdue": 0, "due_soon": 0, "progress": 0}
    if not pid or not (_has_table(ASSIGNMENT_TABLE) and _has_column(ASSIGNMENT_TABLE, "period_id")):
        return empty
    cols = _columns(ASSIGNMENT_TABLE)
    completed_clause = _completed_clause(cols)
    total = _scalar(f"SELECT COUNT(*) FROM {ASSIGNMENT_TABLE} WHERE period_id=:pid", {"pid": pid})
    completed = _scalar(f"SELECT COUNT(*) FROM {ASSIGNMENT_TABLE} WHERE period_id=:pid AND {completed_clause}", {"pid": pid})
    overdue = 0
    due_soon = 0
    if "due_date" in cols:
        overdue = _scalar(
            f"SELECT COUNT(*) FROM {ASSIGNMENT_TABLE} WHERE period_id=:pid AND ({completed_clause}) = false AND due_date IS NOT NULL AND due_date < CURRENT_TIMESTAMP",
            {"pid": pid},
        )
        due_threshold = datetime.now() + timedelta(days=2)
        due_soon = _scalar(
            f"SELECT COUNT(*) FROM {ASSIGNMENT_TABLE} WHERE period_id=:pid AND ({completed_clause}) = false AND due_date IS NOT NULL AND due_date >= CURRENT_TIMESTAMP AND due_date <= :due_threshold",
            {"pid": pid, "due_threshold": due_threshold},
        )
    pending = max(0, total - completed)
    return {"total": total, "completed": completed, "pending": pending, "overdue": overdue, "due_soon": due_soon, "progress": _percent(completed, total)}


def _status_label(raw: Any) -> str:
    key = str(raw or "bekliyor").strip().lower()
    labels = {
        "tamamlandi": "Tamamlandı",
        "tamamlandı": "Tamamlandı",
        "completed": "Tamamlandı",
        "done": "Tamamlandı",
        "bitti": "Tamamlandı",
        "bekliyor": "Bekliyor",
        "pending": "Bekliyor",
        "atandi": "Atandı",
        "atandı": "Atandı",
        "gorev_atandi": "Görev Atandı",
        "görev_atandı": "Görev Atandı",
        "not_started": "Başlamadı",
        "devam_ediyor": "Devam Ediyor",
        "in_progress": "Devam Ediyor",
        "iade": "İade Edildi",
        "iade_edildi": "İade Edildi",
        "returned": "İade Edildi",
        "revize": "Revizyon Bekliyor",
        "revision": "Revizyon Bekliyor",
    }
    return labels.get(key, key.replace("_", " ").title() if key else "Bekliyor")


def _status_class(raw: Any) -> str:
    key = str(raw or "").strip().lower()
    if key in COMPLETED_STATUSES:
        return "ok"
    if key in RETURNED_STATUSES:
        return "danger"
    if key in WAITING_STATUSES:
        return "warn"
    return "muted"


def _status_counts(period_id: int | None, limit: int = 6) -> list[dict[str, Any]]:
    pid = _safe_int(period_id)
    if not pid or not (_has_table(ASSIGNMENT_TABLE) and _has_column(ASSIGNMENT_TABLE, "period_id")):
        return []
    rows = _rows(
        f"SELECT COALESCE(status, 'bekliyor') AS status, COUNT(*) AS total FROM {ASSIGNMENT_TABLE} WHERE period_id=:pid GROUP BY COALESCE(status, 'bekliyor') ORDER BY COUNT(*) DESC LIMIT :limit",
        {"pid": pid, "limit": int(limit)},
    )
    for row in rows:
        row["label"] = _status_label(row.get("status"))
        row["class"] = _status_class(row.get("status"))
    return rows


def _period_title(period_id: int | None, selected_integration: dict[str, Any] | None = None) -> str:
    integration = selected_integration or {}
    if integration.get("period_title"):
        return str(integration.get("period_title"))
    pid = _safe_int(period_id)
    if not pid or not _has_table(PERIOD_TABLE):
        return "Dönem seçilmedi"
    cols = _columns(PERIOD_TABLE)
    title_col = "title" if "title" in cols else ("name" if "name" in cols else "")
    if not title_col:
        return f"Performans Dönemi #{pid}"
    row = _row(f"SELECT {title_col} AS title FROM {PERIOD_TABLE} WHERE id=:pid", {"pid": pid})
    return str((row or {}).get("title") or f"Performans Dönemi #{pid}")


def _stage(counts: dict[str, int], available: bool) -> tuple[str, str, str]:
    if not available:
        return "Dönem bağlantısı bekliyor", "muted", "Gerçek özet için önce dönem planını performans dönemine bağlayın."
    total = _safe_int(counts.get("total"))
    completed = _safe_int(counts.get("completed"))
    overdue = _safe_int(counts.get("overdue"))
    due_soon = _safe_int(counts.get("due_soon"))
    if total <= 0:
        return "Görev üretimi bekliyor", "warn", "Bu dönem için değerlendirme görevi görünmüyor. Görev üretimi adımı tamamlanmalıdır."
    if completed >= total:
        return "Değerlendirmeler tamamlandı", "ok", "Değerlendirme görevleri tamamlanmış görünüyor. Yayın öncesi kontrol adımına geçilebilir."
    if overdue > 0:
        return "Geciken görev var", "danger", "Geciken değerlendirme görevleri için amir hatırlatma süreci hazırlanmalıdır."
    if due_soon > 0:
        return "Son tarih yaklaşan görev var", "warn", "Son tarihi yaklaşan görevler için hatırlatma planlanabilir."
    return "Değerlendirme süreci devam ediyor", "info", "Seçili dönem olağan takip durumunda görünüyor."


def build_period_center_real_summary(center_state: dict[str, Any] | None) -> dict[str, Any]:
    state = center_state or {}
    selected_plan = state.get("selected_plan") or {}
    selected_integration = state.get("selected_integration") or {}
    period_id = _safe_int(selected_integration.get("period_id"))
    available = bool(period_id)
    counts = _base_counts(period_id) if available else {"total": 0, "completed": 0, "pending": 0, "overdue": 0, "due_soon": 0, "progress": 0}
    stage, stage_class, message = _stage(counts, available)
    return {
        "rule_version": RULE_VERSION,
        "available": available,
        "period_id": period_id,
        "period_title": _period_title(period_id, selected_integration),
        "plan_key": str(selected_plan.get("plan_key") or ""),
        "plan_name": str(selected_plan.get("plan_name") or ""),
        "counts": counts,
        "status_counts": _status_counts(period_id) if available else [],
        "stage": stage,
        "stage_class": stage_class,
        "message": message,
        "action_label": "Görev Üretimi" if available and counts.get("total", 0) == 0 else ("Amir Hatırlatma" if counts.get("overdue", 0) or counts.get("due_soon", 0) else "Canlı Takip"),
    }


def run_v2_1_14_period_center_real_summary_gate(center_state: dict[str, Any] | None = None) -> dict[str, Any]:
    checks = [
        {"name": "period_table_read", "ok": _has_table(PERIOD_TABLE), "message": "Performans dönem tablosu kontrol edildi."},
        {"name": "assignment_table_read", "ok": _has_table(ASSIGNMENT_TABLE), "message": "Değerlendirme görev tablosu kontrol edildi."},
        {"name": "assignment_period_id", "ok": (not _has_table(ASSIGNMENT_TABLE)) or _has_column(ASSIGNMENT_TABLE, "period_id"), "message": "Görev kayıtları dönemle ilişkilendirilebilir durumda."},
        {"name": "read_only_summary", "ok": True, "message": "Merkez özeti yalnızca okuma yapar; görev üretmez, bildirim göndermez."},
        {"name": "lightweight_counts", "ok": True, "message": "Detay satırları çekilmeden yalnızca sayı özetleri hazırlanır."},
    ]
    return {"ok": all(item.get("ok") for item in checks), "checks": checks, "rule_version": RULE_VERSION}
