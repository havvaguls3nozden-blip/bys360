from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import inspect, text

logger = logging.getLogger(__name__)

"""BYS360 Performans V2.1.17 hatırlatma onaylı gönderim hazırlığı.

Bu servis Dönem Yönetim Merkezi içinde seçili performans dönemi için
amir hatırlatma hedef listesini, gönderim özeti ve e-posta önizleme metinlerini
hazırlar. Doğrudan e-posta gönderimi yapmaz; yalnızca onaya sunulacak güvenli
hazırlık verisini üretir.
"""

RULE_VERSION = "performance_v2_1_17_reminder_approval_prep"
PERIOD_TABLE = "performance_periods"
ASSIGNMENT_TABLE = "evaluation_assignments"
USER_TABLE = "users"


def _db():
    from app.extensions import db
    return db


def _rollback() -> None:
    try:
        _db().session.rollback()
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/v2_1_17_reminder_approval_prep.py | line=32")
        pass


def _inspector():
    return inspect(_db().engine)


def _has_table(table_name: str) -> bool:
    try:
        return bool(_inspector().has_table(table_name))
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/v2_1_17_reminder_approval_prep.py | line=43")
        return False


def _columns(table_name: str) -> set[str]:
    try:
        if not _has_table(table_name):
            return set()
        return {str(col.get("name")) for col in _inspector().get_columns(table_name)}
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/v2_1_17_reminder_approval_prep.py | line=52")
        return set()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or default)
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/v2_1_17_reminder_approval_prep.py | line=59")
        return default


def _as_text(value: Any, default: str = "") -> str:
    text_value = str(value or "").strip()
    return text_value if text_value else default


def _rows(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    try:
        return [dict(row) for row in _db().session.execute(text(sql), params or {}).mappings().all()]
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/v2_1_17_reminder_approval_prep.py | line=71")
        _rollback()
        return []


def _row(sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    try:
        item = _db().session.execute(text(sql), params or {}).mappings().first()
        return dict(item) if item else None
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/v2_1_17_reminder_approval_prep.py | line=80")
        _rollback()
        return None


def _name_expr(alias: str) -> str:
    cols = _columns(USER_TABLE)
    parts: list[str] = []
    if "full_name_cache" in cols:
        parts.append(f"NULLIF({alias}.full_name_cache,'')")
    if "full_name" in cols:
        parts.append(f"NULLIF({alias}.full_name,'')")
    if {"ad", "soyad"}.issubset(cols):
        parts.append(f"NULLIF(TRIM(COALESCE({alias}.ad,'') || ' ' || COALESCE({alias}.soyad,'')),'')")
    if "name" in cols:
        parts.append(f"NULLIF({alias}.name,'')")
    if "email" in cols:
        parts.append(f"NULLIF({alias}.email,'')")
    parts.append(f"'Kullanıcı #' || {alias}.id")
    return "COALESCE(" + ", ".join(parts) + ")"


def _email_expr(alias: str) -> str:
    return f"{alias}.email" if "email" in _columns(USER_TABLE) else "NULL"


def _title_expr(alias: str) -> str:
    cols = _columns(USER_TABLE)
    if "unvan" in cols:
        return f"{alias}.unvan"
    if "title" in cols:
        return f"{alias}.title"
    return "NULL"


def _period_title_expr() -> str:
    cols = _columns(PERIOD_TABLE)
    parts: list[str] = []
    if "title" in cols:
        parts.append("NULLIF(title,'')")
    if "name" in cols:
        parts.append("NULLIF(name,'')")
    parts.append("'Performans Dönemi #' || id")
    return "COALESCE(" + ", ".join(parts) + ")"


def _period_title(period_id: int | None, fallback: str = "") -> str:
    pid = _safe_int(period_id)
    if not pid or not _has_table(PERIOD_TABLE):
        return _as_text(fallback, "Performans Dönemi")
    row = _row(f"SELECT {_period_title_expr()} AS display_title FROM {PERIOD_TABLE} WHERE id=:pid", {"pid": pid})
    return _as_text((row or {}).get("display_title"), _as_text(fallback, f"Performans Dönemi #{pid}"))


def _completed_clause(alias: str = "a") -> str:
    cols = _columns(ASSIGNMENT_TABLE)
    status_clause = "false"
    if "status" in cols:
        status_clause = f"LOWER(COALESCE({alias}.status,'')) IN ('tamamlandi','tamamlandı','completed','done','bitti')"
    if "completed_at" in cols:
        return f"({alias}.completed_at IS NOT NULL OR {status_clause})"
    return f"({status_clause})"


def _readiness() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for table in [PERIOD_TABLE, ASSIGNMENT_TABLE, USER_TABLE]:
        checks.append({"name": f"table::{table}", "ok": _has_table(table)})
    assignment_cols = _columns(ASSIGNMENT_TABLE)
    for col in ["period_id", "evaluator_id", "employee_id"]:
        checks.append({"name": f"evaluation_assignments.{col}", "ok": col in assignment_cols})
    checks.append({"name": "approval_preview_only", "ok": True})
    return {"ok": all(item.get("ok") for item in checks), "checks": checks, "rule_version": RULE_VERSION}


def _preview_for(row: dict[str, Any], period_title: str) -> dict[str, str]:
    name = _as_text(row.get("evaluator_name"), "Sayın Amir")
    pending = _safe_int(row.get("pending"))
    overdue = _safe_int(row.get("overdue"))
    due_soon = _safe_int(row.get("due_soon"))
    if overdue > 0:
        subject = f"BYS360 Performans Değerlendirme Gecikme Hatırlatması - {period_title}"
        body = f"Sayın {name}, {period_title} kapsamında tarafınıza atanmış {pending} açık değerlendirme görevi bulunmaktadır. Bu görevlerden {overdue} tanesinde son tarih geçmiş görünmektedir. Değerlendirme sürecinin zamanında tamamlanabilmesi için BYS360 üzerinden ilgili görevlerinizi kontrol etmenizi rica ederiz."
    elif due_soon > 0:
        subject = f"BYS360 Performans Değerlendirme Son Tarih Hatırlatması - {period_title}"
        body = f"Sayın {name}, {period_title} kapsamında tarafınıza atanmış {pending} açık değerlendirme görevi bulunmaktadır. Bu görevlerden {due_soon} tanesinde son tarih yaklaşmaktadır. Değerlendirmelerinizi süresi içinde tamamlamanızı rica ederiz."
    else:
        subject = f"BYS360 Performans Değerlendirme Hatırlatması - {period_title}"
        body = f"Sayın {name}, {period_title} kapsamında tarafınıza atanmış {pending} açık değerlendirme görevi bulunmaktadır. Sürecin sağlıklı ilerleyebilmesi için BYS360 üzerinden değerlendirme görevlerinizi kontrol etmenizi rica ederiz."
    return {"subject": subject, "body": body}


def _target_rows(period_id: int, *, due_days: int = 2, limit: int = 60) -> list[dict[str, Any]]:
    if not (_has_table(ASSIGNMENT_TABLE) and _has_table(USER_TABLE)):
        return []
    assignment_cols = _columns(ASSIGNMENT_TABLE)
    if not {"period_id", "evaluator_id"}.issubset(assignment_cols):
        return []
    completed = _completed_clause("a")
    due_threshold = datetime.now() + timedelta(days=max(1, min(30, int(due_days or 2))))
    due_date_expr = "a.due_date" if "due_date" in assignment_cols else "NULL"
    overdue_expr = "0"
    due_soon_expr = "0"
    if "due_date" in assignment_cols:
        overdue_expr = f"SUM(CASE WHEN NOT {completed} AND a.due_date IS NOT NULL AND a.due_date < CURRENT_TIMESTAMP THEN 1 ELSE 0 END)"
        due_soon_expr = f"SUM(CASE WHEN NOT {completed} AND a.due_date IS NOT NULL AND a.due_date >= CURRENT_TIMESTAMP AND a.due_date <= :due_threshold THEN 1 ELSE 0 END)"
    completed_expr = f"SUM(CASE WHEN {completed} THEN 1 ELSE 0 END)"
    rows = _rows(
        f"""
        SELECT a.evaluator_id,
               {_name_expr('u')} AS evaluator_name,
               {_email_expr('u')} AS evaluator_email,
               {_title_expr('u')} AS evaluator_title,
               COUNT(*) AS total,
               {completed_expr} AS completed,
               {overdue_expr} AS overdue,
               {due_soon_expr} AS due_soon,
               MIN(CASE WHEN NOT {completed} THEN {due_date_expr} ELSE NULL END) AS nearest_due_date,
               COUNT(DISTINCT a.employee_id) AS employee_count
          FROM {ASSIGNMENT_TABLE} a
          LEFT JOIN {USER_TABLE} u ON u.id = a.evaluator_id
         WHERE a.period_id=:period_id
         GROUP BY a.evaluator_id, evaluator_name, evaluator_email, evaluator_title
         ORDER BY overdue DESC, due_soon DESC, (COUNT(*) - {completed_expr}) DESC, COUNT(*) DESC
         LIMIT :limit
        """,
        {"period_id": period_id, "due_threshold": due_threshold, "limit": max(10, min(200, int(limit or 60)))},
    )
    period_title = _period_title(period_id)
    targets: list[dict[str, Any]] = []
    for row in rows:
        total = _safe_int(row.get("total"))
        completed_count = _safe_int(row.get("completed"))
        pending = max(0, total - completed_count)
        row["pending"] = pending
        row["has_email"] = bool(_as_text(row.get("evaluator_email")))
        row["status_class"] = "danger" if _safe_int(row.get("overdue")) else ("warn" if _safe_int(row.get("due_soon")) else "info")
        row["reminder_label"] = "Gecikme" if _safe_int(row.get("overdue")) else ("Son Tarih" if _safe_int(row.get("due_soon")) else "Bekleyen Görev")
        if pending > 0:
            preview = _preview_for(row, period_title)
            row["preview_subject"] = preview["subject"]
            row["preview_body"] = preview["body"]
            targets.append(row)
    return targets


def _summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    valid = [item for item in rows if item.get("has_email")]
    return {
        "target_evaluators": len(rows),
        "ready_to_approve": len(valid),
        "missing_email": max(0, len(rows) - len(valid)),
        "pending_tasks": sum(_safe_int(item.get("pending")) for item in rows),
        "overdue_tasks": sum(_safe_int(item.get("overdue")) for item in rows),
        "due_soon_tasks": sum(_safe_int(item.get("due_soon")) for item in rows),
    }


def build_reminder_approval_prep_state(
    *,
    period_id: int | None = None,
    period_title: str = "",
    due_days: int = 2,
    limit: int = 60,
) -> dict[str, Any]:
    pid = _safe_int(period_id)
    title = _period_title(pid, period_title)
    base: dict[str, Any] = {
        "rule_version": RULE_VERSION,
        "period_id": pid,
        "period_title": title,
        "rows": [],
        "summary": {"target_evaluators": 0, "ready_to_approve": 0, "missing_email": 0, "pending_tasks": 0, "overdue_tasks": 0, "due_soon_tasks": 0},
        "status": "donem_secilmedi",
        "status_label": "Dönem Seçilmedi",
        "status_class": "muted",
        "message": "Hatırlatma hazırlığı için dönem seçin.",
        "can_prepare": False,
        "can_approve_next": False,
        "preview": None,
        "readiness": _readiness(),
    }
    if not pid:
        return base
    readiness = base["readiness"]
    if not readiness.get("ok"):
        base.update({
            "status": "altyapi_kontrol",
            "status_label": "Altyapı Kontrolü",
            "status_class": "warn",
            "message": "Hatırlatma hazırlığı için dönem, görev ve kullanıcı kayıtları kontrol edilmeli.",
        })
        return base
    rows = _target_rows(pid, due_days=due_days, limit=limit)
    summary = _summary(rows)
    base["rows"] = rows
    base["summary"] = summary
    base["can_prepare"] = summary.get("target_evaluators", 0) > 0
    base["can_approve_next"] = summary.get("ready_to_approve", 0) > 0
    base["preview"] = rows[0] if rows else None
    if not rows:
        base.update({
            "status": "hatirlatma_gerekmiyor",
            "status_label": "Hatırlatma Gerekmiyor",
            "status_class": "ok",
            "message": "Seçili dönem için açık değerlendirme görevi bulunan amir görünmüyor.",
        })
    elif summary.get("missing_email", 0) and not summary.get("ready_to_approve", 0):
        base.update({
            "status": "eposta_kontrol",
            "status_label": "E-posta Kontrolü",
            "status_class": "warn",
            "message": "Hedef amirlerin e-posta bilgisi tamamlanmadan gönderim onayına geçilmemeli.",
        })
    elif summary.get("overdue_tasks", 0) > 0:
        base.update({
            "status": "onay_hazir",
            "status_label": "Onaya Hazır",
            "status_class": "danger",
            "message": "Geciken değerlendirme görevleri için hatırlatma listesi onaya hazırlandı.",
        })
    elif summary.get("due_soon_tasks", 0) > 0:
        base.update({
            "status": "onay_hazir",
            "status_label": "Onaya Hazır",
            "status_class": "warn",
            "message": "Son tarihi yaklaşan değerlendirmeler için hatırlatma listesi onaya hazırlandı.",
        })
    else:
        base.update({
            "status": "onay_hazir",
            "status_label": "Onaya Hazır",
            "status_class": "info",
            "message": "Bekleyen değerlendirme görevleri için hatırlatma listesi hazırlandı.",
        })
    return base


def prepare_reminder_approval_preview(period_id: int | None, *, due_days: int = 2, limit: int = 60) -> dict[str, Any]:
    state = build_reminder_approval_prep_state(period_id=period_id, due_days=due_days, limit=limit)
    summary = state.get("summary") or {}
    ok = bool(state.get("can_prepare"))
    if ok:
        msg = f"Hatırlatma hazırlığı oluşturuldu. Hedef amir: {summary.get('target_evaluators', 0)}, onaya hazır: {summary.get('ready_to_approve', 0)}, bekleyen görev: {summary.get('pending_tasks', 0)}."
    else:
        msg = state.get("message") or "Hatırlatma hazırlığı oluşturulamadı."
    return {"ok": ok, "message": msg, "state": state, "rule_version": RULE_VERSION}


def run_v2_1_17_reminder_approval_prep_gate(period_id: int | None = None) -> dict[str, Any]:
    state = build_reminder_approval_prep_state(period_id=period_id, limit=5)
    checks = [
        {"name": "state_builds", "ok": isinstance(state, dict), "message": "Hatırlatma onay hazırlığı durumu hazırlanıyor."},
        {"name": "readiness_checked", "ok": isinstance(state.get("readiness"), dict), "message": "Dönem, görev ve kullanıcı altyapısı kontrol ediliyor."},
        {"name": "preview_only", "ok": True, "message": "Bu adım doğrudan e-posta gönderimi yapmaz; onay hazırlığı üretir."},
        {"name": "corporate_labels", "ok": bool(state.get("status_label")), "message": "Kullanıcıya kurumsal durum etiketi gösteriliyor."},
    ]
    return {"ok": all(item.get("ok") for item in checks), "checks": checks, "rule_version": RULE_VERSION, "status": state.get("status")}
