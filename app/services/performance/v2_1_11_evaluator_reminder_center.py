from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import inspect, text

logger = logging.getLogger(__name__)

"""BYS360 Performans V2.1.11 amir hatırlatma hazırlık merkezi servisi.

Bu servis yalnızca okuma ve önizleme üretir. Sayfa açılışında görev üretmez,
mail göndermez, şema değiştirmez ve kritik süreç statüsü yazmaz. Amaç;
V2.1.10 canlı takip ekranında görülen bekleyen/geciken değerlendirmeleri amir
bazında sadeleştirmek ve güvenli hatırlatma hazırlığı oluşturmaktır.
"""

RULE_VERSION = "performance_v2_1_11_evaluator_reminder_center"
PERIOD_TABLE = "performance_periods"
ASSIGNMENT_TABLE = "evaluation_assignments"
USER_TABLE = "users"

COMPLETED_STATUSES = {"tamamlandi", "tamamlandı", "completed", "done", "bitti"}
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
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/v2_1_11_evaluator_reminder_center.py | line=39")
        pass


def _has_table(table_name: str) -> bool:
    try:
        return bool(_inspector().has_table(table_name))
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/v2_1_11_evaluator_reminder_center.py | line=46")
        return False


def _columns(table_name: str) -> set[str]:
    try:
        if not _has_table(table_name):
            return set()
        return {str(col.get("name")) for col in _inspector().get_columns(table_name)}
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/v2_1_11_evaluator_reminder_center.py | line=55")
        return set()


def _has_column(table_name: str, column_name: str) -> bool:
    return column_name in _columns(table_name)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or default)
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/v2_1_11_evaluator_reminder_center.py | line=66")
        return default


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _percent(done: int, total: int) -> int:
    if total <= 0:
        return 0
    return max(0, min(100, int(round((done / total) * 100))))


def _scalar(sql: str, params: dict[str, Any] | None = None, default: int = 0) -> int:
    try:
        value = _db().session.execute(text(sql), params or {}).scalar()
        return int(value or 0)
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/v2_1_11_evaluator_reminder_center.py | line=86")
        _rollback()
        return default


def _rows(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    try:
        return [dict(row) for row in _db().session.execute(text(sql), params or {}).mappings().all()]
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/v2_1_11_evaluator_reminder_center.py | line=94")
        _rollback()
        return []


def _row(sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    try:
        item = _db().session.execute(text(sql), params or {}).mappings().first()
        return dict(item) if item else None
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/v2_1_11_evaluator_reminder_center.py | line=103")
        _rollback()
        return None


def _status_key(raw: Any) -> str:
    return _safe_str(raw or "bekliyor").strip().lower()


def _completion_clause(alias: str = "a") -> str:
    cols = _columns(ASSIGNMENT_TABLE)
    status_expr = f"LOWER(COALESCE({alias}.status, '')) IN ('tamamlandi','tamamlandı','completed','done','bitti')" if "status" in cols else "false"
    if "completed_at" in cols:
        return f"({alias}.completed_at IS NOT NULL OR {status_expr})"
    return f"({status_expr})"


def _name_expr(alias: str) -> str:
    cols = _columns(USER_TABLE)
    parts: list[str] = []
    if "full_name_cache" in cols:
        parts.append(f"NULLIF({alias}.full_name_cache,'')")
    if "full_name" in cols:
        parts.append(f"NULLIF({alias}.full_name,'')")
    if {"ad", "soyad"}.issubset(cols):
        parts.append(f"NULLIF(TRIM(COALESCE({alias}.ad,'') || ' ' || COALESCE({alias}.soyad,'')),'')")
    if "email" in cols:
        parts.append(f"NULLIF({alias}.email,'')")
    parts.append(f"'Kullanıcı #' || {alias}.id")
    return "COALESCE(" + ", ".join(parts) + ")"


def _email_expr(alias: str) -> str:
    return f"{alias}.email" if "email" in _columns(USER_TABLE) else "NULL"


def _title_expr(alias: str) -> str:
    return f"{alias}.unvan" if "unvan" in _columns(USER_TABLE) else "NULL"


def _period_title_expr() -> str:
    cols = _columns(PERIOD_TABLE)
    parts = []
    if "title" in cols:
        parts.append("NULLIF(title,'')")
    if "name" in cols:
        parts.append("NULLIF(name,'')")
    parts.append("'Performans Dönemi #' || id")
    return "COALESCE(" + ", ".join(parts) + ")"


def list_period_options(limit: int = 60) -> list[dict[str, Any]]:
    if not _has_table(PERIOD_TABLE):
        return []
    cols = _columns(PERIOD_TABLE)
    select_cols = ["id", f"{_period_title_expr()} AS display_title"]
    for name in ["title", "name", "period_type", "start_date", "end_date", "evaluation_start_date", "evaluation_end_date", "is_active", "results_published", "is_locked"]:
        if name in cols:
            select_cols.append(name)
    return _rows(f"SELECT {', '.join(select_cols)} FROM {PERIOD_TABLE} ORDER BY id DESC LIMIT :limit", {"limit": int(limit)})


def _default_period_id() -> int | None:
    if not (_has_table(PERIOD_TABLE) and _has_table(ASSIGNMENT_TABLE) and _has_column(ASSIGNMENT_TABLE, "period_id")):
        periods = list_period_options(1)
        return _safe_int(periods[0].get("id")) if periods else None
    if _has_column(PERIOD_TABLE, "is_active"):
        row = _row(
            f"SELECT p.id FROM {PERIOD_TABLE} p WHERE p.is_active = true AND EXISTS (SELECT 1 FROM {ASSIGNMENT_TABLE} a WHERE a.period_id = p.id) ORDER BY p.id DESC LIMIT 1"
        )
        if row:
            return _safe_int(row.get("id"))
    row = _row(f"SELECT period_id AS id FROM {ASSIGNMENT_TABLE} GROUP BY period_id ORDER BY MAX(id) DESC LIMIT 1")
    if row:
        return _safe_int(row.get("id"))
    periods = list_period_options(1)
    return _safe_int(periods[0].get("id")) if periods else None


def _period_detail(period_id: int | None) -> dict[str, Any] | None:
    pid = _safe_int(period_id)
    if not pid or not _has_table(PERIOD_TABLE):
        return None
    cols = _columns(PERIOD_TABLE)
    select_cols = ["id", f"{_period_title_expr()} AS display_title"]
    for name in ["title", "name", "period_type", "start_date", "end_date", "evaluation_start_date", "evaluation_end_date", "is_active", "results_published", "is_locked", "scope_type", "scope_category_label", "scope_unit_label"]:
        if name in cols:
            select_cols.append(name)
    return _row(f"SELECT {', '.join(select_cols)} FROM {PERIOD_TABLE} WHERE id=:pid", {"pid": pid})


def ensure_reminder_center_ready() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    for table in [PERIOD_TABLE, ASSIGNMENT_TABLE, USER_TABLE]:
        ok = _has_table(table)
        checks.append({"name": table, "ok": ok, "message": f"{table} tablosu {'hazır' if ok else 'bulunamadı'}."})
    assignment_cols = _columns(ASSIGNMENT_TABLE)
    for col in ["period_id", "employee_id", "evaluator_id", "status"]:
        checks.append({"name": f"{ASSIGNMENT_TABLE}.{col}", "ok": col in assignment_cols, "message": f"Hatırlatma hazırlığı için {col} alanı {'hazır' if col in assignment_cols else 'eksik'}."})
    checks.append({"name": "read_only_preview", "ok": True, "message": "Bu merkez mail göndermez; sadece amir bazlı hatırlatma ön hazırlığı üretir."})
    return {"ok": all(item.get("ok") for item in checks), "checks": checks, "rule_version": RULE_VERSION}


def _risk_filter_match(row: dict[str, Any], risk_filter: str) -> bool:
    risk = (risk_filter or "all").strip().lower()
    pending = _safe_int(row.get("pending"))
    overdue = _safe_int(row.get("overdue"))
    due_soon = _safe_int(row.get("due_soon"))
    progress = _safe_int(row.get("progress"))
    if risk in {"", "all"}:
        return True
    if risk == "overdue":
        return overdue > 0
    if risk == "due_soon":
        return due_soon > 0
    if risk == "pending":
        return pending > 0
    if risk == "low_progress":
        return pending > 0 and progress < 50
    if risk == "ready":
        return pending == 0 and _safe_int(row.get("total")) > 0
    return True


def _reminder_type(row: dict[str, Any]) -> tuple[str, str]:
    if _safe_int(row.get("overdue")) > 0:
        return "Gecikme Hatırlatması", "danger"
    if _safe_int(row.get("due_soon")) > 0:
        return "Son Tarih Hatırlatması", "warn"
    if _safe_int(row.get("pending")) > 0:
        return "Bekleyen Değerlendirme Hatırlatması", "info"
    return "Hatırlatma Gerekmiyor", "ok"


def _preview_message(row: dict[str, Any], period_title: str) -> dict[str, str]:
    name = row.get("evaluator_name") or "Sayın Amir"
    pending = _safe_int(row.get("pending"))
    overdue = _safe_int(row.get("overdue"))
    due_soon = _safe_int(row.get("due_soon"))
    if overdue > 0:
        subject = f"BYS360 Performans Değerlendirme Gecikme Hatırlatması - {period_title}"
        body = f"Sayın {name}, {period_title} kapsamında tarafınıza atanmış {pending} açık değerlendirme görevi bulunmaktadır. Bu görevlerden {overdue} tanesinde son tarih geçmiş görünmektedir. Lütfen BYS360 üzerinden değerlendirme görevlerinizi kontrol ediniz. Bu metin sistem tarafından hazırlanmış önizlemedir; henüz gönderilmemiştir."
    elif due_soon > 0:
        subject = f"BYS360 Performans Değerlendirme Son Tarih Hatırlatması - {period_title}"
        body = f"Sayın {name}, {period_title} kapsamında tarafınıza atanmış {pending} açık değerlendirme görevi bulunmaktadır. Bu görevlerden {due_soon} tanesinde son tarih yaklaşmaktadır. Lütfen ilgili değerlendirmeleri süresi içinde tamamlayınız. Bu metin sistem tarafından hazırlanmış önizlemedir; henüz gönderilmemiştir."
    elif pending > 0:
        subject = f"BYS360 Performans Değerlendirme Hatırlatması - {period_title}"
        body = f"Sayın {name}, {period_title} kapsamında tarafınıza atanmış {pending} açık değerlendirme görevi bulunmaktadır. Değerlendirme sürecinin zamanında tamamlanabilmesi için BYS360 Canlı Değerlendirme Takibi ekranını kontrol ediniz. Bu metin sistem tarafından hazırlanmış önizlemedir; henüz gönderilmemiştir."
    else:
        subject = f"BYS360 Performans Değerlendirme Durumu - {period_title}"
        body = f"Sayın {name}, {period_title} kapsamında açık değerlendirme göreviniz görünmemektedir. Bu kayıt için hatırlatma gönderimi önerilmez."
    return {"subject": subject, "body": body}


def _evaluator_rows(period_id: int, *, risk_filter: str = "all", manager_level: str = "", q: str = "", due_days: int = 2, limit: int = 80) -> list[dict[str, Any]]:
    if not (_has_table(ASSIGNMENT_TABLE) and _has_table(USER_TABLE)):
        return []
    assignment_cols = _columns(ASSIGNMENT_TABLE)
    if not {"period_id", "evaluator_id"}.issubset(assignment_cols):
        return []
    completed = _completion_clause("a")
    due_threshold = datetime.now() + timedelta(days=max(1, min(30, int(due_days or 2))))
    params: dict[str, Any] = {"pid": period_id, "due_threshold": due_threshold, "limit": max(10, min(300, int(limit or 80)))}
    where = ["a.period_id = :pid"]
    if manager_level and "manager_level" in assignment_cols:
        where.append("a.manager_level = :manager_level")
        params["manager_level"] = _safe_int(manager_level)
    if q:
        params["q"] = f"%{q.strip().lower()}%"
        search_parts = [f"LOWER({_name_expr('u')}) LIKE :q"]
        if "email" in _columns(USER_TABLE):
            search_parts.append("LOWER(COALESCE(u.email,'')) LIKE :q")
        where.append("(" + " OR ".join(search_parts) + ")")
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
        WHERE {' AND '.join(where)}
        GROUP BY a.evaluator_id, evaluator_name, evaluator_email, evaluator_title
        ORDER BY overdue DESC, due_soon DESC, (COUNT(*) - {completed_expr}) DESC, COUNT(*) DESC
        LIMIT :limit
        """,
        params,
    )
    period = _period_detail(period_id) or {}
    period_title = period.get("display_title") or f"Performans Dönemi #{period_id}"
    enriched: list[dict[str, Any]] = []
    for row in rows:
        total = _safe_int(row.get("total"))
        completed_count = _safe_int(row.get("completed"))
        pending = max(0, total - completed_count)
        row["pending"] = pending
        row["progress"] = _percent(completed_count, total)
        reminder_type, reminder_class = _reminder_type(row)
        row["reminder_type"] = reminder_type
        row["reminder_class"] = reminder_class
        preview = _preview_message(row, period_title)
        row["preview_subject"] = preview["subject"]
        row["preview_body"] = preview["body"]
        row["needs_reminder"] = pending > 0
        row["status_class"] = "danger" if _safe_int(row.get("overdue")) else ("warn" if _safe_int(row.get("due_soon")) else ("info" if pending else "ok"))
        if _risk_filter_match(row, risk_filter):
            enriched.append(row)
    return enriched


def _summary(evaluators: list[dict[str, Any]]) -> dict[str, Any]:
    total_evaluators = len(evaluators)
    need = sum(1 for item in evaluators if item.get("needs_reminder"))
    total_tasks = sum(_safe_int(item.get("total")) for item in evaluators)
    total_completed = sum(_safe_int(item.get("completed")) for item in evaluators)
    total_pending = sum(_safe_int(item.get("pending")) for item in evaluators)
    total_overdue = sum(_safe_int(item.get("overdue")) for item in evaluators)
    total_due_soon = sum(_safe_int(item.get("due_soon")) for item in evaluators)
    return {
        "total_evaluators": total_evaluators,
        "needs_reminder": need,
        "total_tasks": total_tasks,
        "total_completed": total_completed,
        "total_pending": total_pending,
        "total_overdue": total_overdue,
        "total_due_soon": total_due_soon,
        "progress": _percent(total_completed, total_tasks),
    }


def _notes(summary: dict[str, Any], selected_period: dict[str, Any] | None) -> list[dict[str, str]]:
    if not selected_period:
        return [{"class": "warn", "title": "Dönem seçimi gerekli", "message": "Amir hatırlatma hazırlığı için bir performans dönemi seçin."}]
    notes: list[dict[str, str]] = []
    if _safe_int(summary.get("total_tasks")) == 0:
        notes.append({"class": "warn", "title": "Görev görünmüyor", "message": "Seçili dönem için amir bazlı değerlendirme görevi bulunamadı. Önce dönem merkezi üzerinden görev üretimini kontrol edin."})
    if _safe_int(summary.get("total_overdue")) > 0:
        notes.append({"class": "danger", "title": "Geciken görevler var", "message": "Geciken değerlendirme görevleri için hatırlatma metni hazırlanmalı ve gönderim bir sonraki güvenli onay adımına bırakılmalıdır."})
    if _safe_int(summary.get("total_due_soon")) > 0:
        notes.append({"class": "warn", "title": "Son tarih yaklaşımı", "message": "Son tarihi yaklaşan görevler için nazik hatırlatma hazırlığı yapılabilir."})
    if _safe_int(summary.get("total_pending")) == 0 and _safe_int(summary.get("total_tasks")) > 0:
        notes.append({"class": "ok", "title": "Hatırlatma gerekmiyor", "message": "Seçili filtrede açık değerlendirme görevi görünmüyor."})
    if not notes:
        notes.append({"class": "ok", "title": "Süreç normal", "message": "Açık görevler takip edilebilir durumda. Gerekirse bekleyen amirler için önizleme metinleri kullanılabilir."})
    return notes


def build_evaluator_reminder_center_state(
    *,
    period_id: int | None = None,
    risk_filter: str = "all",
    manager_level: str = "",
    q: str = "",
    due_days: int = 2,
    include_rows: bool = True,
) -> dict[str, Any]:
    readiness = ensure_reminder_center_ready()
    periods = list_period_options()
    selected_period_id = _safe_int(period_id) or _default_period_id()
    selected_period = _period_detail(selected_period_id) if selected_period_id else None
    evaluators = _evaluator_rows(
        selected_period_id,
        risk_filter=risk_filter,
        manager_level=manager_level,
        q=q,
        due_days=due_days,
        limit=120,
    ) if selected_period_id and include_rows else []
    summary = _summary(evaluators)
    stage = "Hatırlatma hazırlığı"
    stage_class = "info"
    if summary.get("total_overdue", 0) > 0:
        stage = "Geciken amir takibi gerekli"
        stage_class = "danger"
    elif summary.get("total_due_soon", 0) > 0:
        stage = "Son tarih hatırlatması önerilir"
        stage_class = "warn"
    elif summary.get("total_pending", 0) == 0 and summary.get("total_tasks", 0) > 0:
        stage = "Hatırlatma gerekmiyor"
        stage_class = "ok"
    elif summary.get("total_tasks", 0) == 0:
        stage = "Görev üretimi bekliyor"
        stage_class = "muted"
    return {
        "rule_version": RULE_VERSION,
        "readiness": readiness,
        "periods": periods,
        "selected_period_id": selected_period_id,
        "selected_period": selected_period,
        "filters": {"risk_filter": risk_filter or "all", "manager_level": manager_level or "", "q": q or "", "due_days": _safe_int(due_days, 2)},
        "evaluators": evaluators,
        "summary": summary,
        "notes": _notes(summary, selected_period),
        "stage": stage,
        "stage_class": stage_class,
    }


def run_v2_1_11_evaluator_reminder_center_gate() -> dict[str, Any]:
    readiness = ensure_reminder_center_ready()
    checks = list(readiness.get("checks") or [])
    checks.append({"name": "no_mail_send", "ok": True, "message": "V2.1.11 gerçek mail göndermez; gönderim için ayrıca onaylı faz gerekir."})
    checks.append({"name": "safe_open", "ok": True, "message": "Sayfa açılışı sadece okuma ve sınırlı listeleme yapar."})
    checks.append({"name": "corporate_language", "ok": True, "message": "Kullanıcıya teknik durum kodları yerine kurumsal Türkçe açıklamalar gösterilir."})
    return {"ok": all(item.get("ok") for item in checks), "checks": checks, "rule_version": RULE_VERSION}
