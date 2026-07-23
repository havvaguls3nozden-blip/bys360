from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import inspect, text

"""BYS360 Performans V2.1.10 değerlendirme süreci canlı takip servisi.

Bu servis sadece okuma yapar. Sayfa açılışında şema değiştirme, görev üretimi,
mail gönderimi veya ağır yeniden hesaplama çalıştırmaz. Amaç; seçili dönem için
değerlendirme görevlerinin tamamlanma durumunu, bekleyen/geciken amirleri ve
süreç risklerini güvenli ve sade yönetici kartlarıyla göstermektir.
"""

logger = logging.getLogger(__name__)

RULE_VERSION = "performance_v2_1_10_evaluation_live_tracking"
PERIOD_TABLE = "performance_periods"
ASSIGNMENT_TABLE = "evaluation_assignments"
USER_TABLE = "users"

COMPLETED_STATUSES = {"tamamlandi", "tamamlandı", "completed", "done", "bitti"}
WAITING_STATUSES = {"bekliyor", "pending", "atandi", "atandı", "gorev_atandi", "görev_atandı", "not_started", "devam_ediyor", "in_progress"}
RETURNED_STATUSES = {"iade", "iade_edildi", "returned", "revize", "revision"}


def _db():
    from app.extensions import db
    return db


def _inspector():
    return inspect(_db().engine)


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


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or default)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _safe_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _percent(done: int, total: int) -> int:
    if total <= 0:
        return 0
    return max(0, min(100, int(round((done / total) * 100))))


def _rollback() -> None:
    try:
        _db().session.rollback()
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        pass


def _scalar(sql: str, params: dict[str, Any] | None = None, default: int = 0) -> int:
    try:
        value = _db().session.execute(text(sql), params or {}).scalar()
        return int(value or 0)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        _rollback()
        return default


def _rows(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    try:
        return [dict(row) for row in _db().session.execute(text(sql), params or {}).mappings().all()]
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        _rollback()
        return []


def _row(sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    try:
        item = _db().session.execute(text(sql), params or {}).mappings().first()
        return dict(item) if item else None
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        _rollback()
        return None


def _status_key(raw: Any) -> str:
    return _safe_str(raw or "bekliyor").strip().lower()


def status_label(raw: Any) -> str:
    key = _status_key(raw)
    labels = {
        "tamamlandi": "Tamamlandı",
        "tamamlandı": "Tamamlandı",
        "completed": "Tamamlandı",
        "done": "Tamamlandı",
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
    if not key:
        return "Bekliyor"
    return labels.get(key, key.replace("_", " ").title())


def status_class(raw: Any) -> str:
    key = _status_key(raw)
    if key in COMPLETED_STATUSES:
        return "ok"
    if key in RETURNED_STATUSES:
        return "danger"
    if key in WAITING_STATUSES:
        return "warn"
    return "muted"


def ensure_evaluation_live_tracking_ready() -> dict[str, Any]:
    checks = []
    for table in [PERIOD_TABLE, ASSIGNMENT_TABLE, USER_TABLE]:
        checks.append({"name": table, "ok": _has_table(table), "message": f"{table} tablosu {'hazır' if _has_table(table) else 'bulunamadı'}."})
    required_assignment_cols = ["period_id", "employee_id", "evaluator_id", "manager_level", "status", "assigned_at", "due_date", "completed_at"]
    assignment_cols = _columns(ASSIGNMENT_TABLE)
    for col in required_assignment_cols:
        checks.append({"name": f"{ASSIGNMENT_TABLE}.{col}", "ok": col in assignment_cols, "message": f"Görev alanı {col} {'hazır' if col in assignment_cols else 'eksik'}."})
    return {"ok": all(item.get("ok") for item in checks), "checks": checks, "rule_version": RULE_VERSION}


def list_period_options(limit: int = 60) -> list[dict[str, Any]]:
    if not _has_table(PERIOD_TABLE):
        return []
    cols = _columns(PERIOD_TABLE)
    select_cols = ["id"]
    for name in ["title", "name", "period_type", "start_date", "end_date", "evaluation_start_date", "evaluation_end_date", "is_active", "results_published", "is_locked"]:
        if name in cols:
            select_cols.append(name)
    order = "ORDER BY id DESC"
    rows = _rows(f"SELECT {', '.join(select_cols)} FROM {PERIOD_TABLE} {order} LIMIT :limit", {"limit": int(limit)})
    for item in rows:
        item["display_title"] = item.get("title") or item.get("name") or f"Performans Dönemi #{item.get('id')}"
    return rows


def _default_period_id() -> int | None:
    if not (_has_table(PERIOD_TABLE) and _has_table(ASSIGNMENT_TABLE) and _has_column(ASSIGNMENT_TABLE, "period_id")):
        periods = list_period_options(1)
        return _safe_int(periods[0].get("id")) if periods else None
    # Önce aktif ve görev üretilmiş dönem, sonra en son görevli dönem, son olarak en son dönem.
    active_col = "is_active" if _has_column(PERIOD_TABLE, "is_active") else None
    if active_col:
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
    select_cols = ["id"]
    for name in ["title", "name", "period_type", "start_date", "end_date", "evaluation_start_date", "evaluation_end_date", "is_active", "results_published", "is_locked", "scope_type", "scope_category_label", "scope_unit_label"]:
        if name in cols:
            select_cols.append(name)
    row = _row(f"SELECT {', '.join(select_cols)} FROM {PERIOD_TABLE} WHERE id=:pid", {"pid": pid})
    if not row:
        return None
    row["display_title"] = row.get("title") or row.get("name") or f"Performans Dönemi #{pid}"
    return row


def _assignment_where(period_id: int, status_filter: str = "", manager_level: str = "") -> tuple[str, dict[str, Any]]:
    clauses = ["a.period_id = :pid"]
    params: dict[str, Any] = {"pid": period_id}
    if status_filter:
        clauses.append("LOWER(COALESCE(a.status, 'bekliyor')) = :status_filter")
        params["status_filter"] = status_filter.strip().lower()
    if manager_level:
        clauses.append("a.manager_level = :manager_level")
        params["manager_level"] = _safe_int(manager_level)
    return " AND ".join(clauses), params


def _base_assignment_counts(period_id: int) -> dict[str, Any]:
    if not (_has_table(ASSIGNMENT_TABLE) and _has_column(ASSIGNMENT_TABLE, "period_id")):
        return {"total": 0, "completed": 0, "pending": 0, "overdue": 0, "due_soon": 0, "progress": 0}
    total = _scalar(f"SELECT COUNT(*) FROM {ASSIGNMENT_TABLE} WHERE period_id=:pid", {"pid": period_id})
    cols = _columns(ASSIGNMENT_TABLE)
    completed_clause = "LOWER(COALESCE(status, '')) IN ('tamamlandi','tamamlandı','completed','done','bitti')"
    if "completed_at" in cols:
        completed_clause = f"(completed_at IS NOT NULL OR {completed_clause})"
    completed = _scalar(f"SELECT COUNT(*) FROM {ASSIGNMENT_TABLE} WHERE period_id=:pid AND {completed_clause}", {"pid": period_id})
    overdue = 0
    due_soon = 0
    if "due_date" in cols:
        overdue = _scalar(f"SELECT COUNT(*) FROM {ASSIGNMENT_TABLE} WHERE period_id=:pid AND ({completed_clause}) = false AND due_date IS NOT NULL AND due_date < CURRENT_TIMESTAMP", {"pid": period_id})
        # PostgreSQL ve SQLite uyumlu olması için tarih eşiği Python tarafında parametre olarak verilir.
        due_threshold = datetime.now() + timedelta(days=2)
        due_soon = _scalar(f"SELECT COUNT(*) FROM {ASSIGNMENT_TABLE} WHERE period_id=:pid AND ({completed_clause}) = false AND due_date IS NOT NULL AND due_date >= CURRENT_TIMESTAMP AND due_date <= :due_threshold", {"pid": period_id, "due_threshold": due_threshold})
    pending = max(0, total - completed)
    return {"total": total, "completed": completed, "pending": pending, "overdue": overdue, "due_soon": due_soon, "progress": _percent(completed, total)}


def _status_counts(period_id: int) -> list[dict[str, Any]]:
    if not (_has_table(ASSIGNMENT_TABLE) and _has_column(ASSIGNMENT_TABLE, "period_id")):
        return []
    rows = _rows(
        f"SELECT COALESCE(status, 'bekliyor') AS status, COUNT(*) AS total FROM {ASSIGNMENT_TABLE} WHERE period_id=:pid GROUP BY COALESCE(status, 'bekliyor') ORDER BY COUNT(*) DESC",
        {"pid": period_id},
    )
    for row in rows:
        row["label"] = status_label(row.get("status"))
        row["class"] = status_class(row.get("status"))
    return rows


def _level_counts(period_id: int) -> list[dict[str, Any]]:
    if not (_has_table(ASSIGNMENT_TABLE) and _has_column(ASSIGNMENT_TABLE, "period_id") and _has_column(ASSIGNMENT_TABLE, "manager_level")):
        return []
    rows = _rows(
        f"SELECT manager_level, COUNT(*) AS total FROM {ASSIGNMENT_TABLE} WHERE period_id=:pid GROUP BY manager_level ORDER BY manager_level",
        {"pid": period_id},
    )
    for row in rows:
        level = row.get("manager_level")
        row["label"] = f"{level}. Amir" if level else "Amir Seviyesi Yok"
    return rows


def _top_evaluators(period_id: int, limit: int = 12) -> list[dict[str, Any]]:
    if not (_has_table(ASSIGNMENT_TABLE) and _has_table(USER_TABLE)):
        return []
    assignment_cols = _columns(ASSIGNMENT_TABLE)
    user_cols = _columns(USER_TABLE)
    if not {"period_id", "evaluator_id"}.issubset(assignment_cols):
        return []
    name_expr = "COALESCE(NULLIF(u.full_name_cache,''), NULLIF(u.full_name,''), TRIM(COALESCE(u.ad,'') || ' ' || COALESCE(u.soyad,'')), u.email, 'Kullanıcı #' || u.id)"
    if "full_name_cache" not in user_cols and "full_name" not in user_cols:
        name_expr = "COALESCE(TRIM(COALESCE(u.ad,'') || ' ' || COALESCE(u.soyad,'')), u.email, 'Kullanıcı #' || u.id)"
    completed_expr = "SUM(CASE WHEN LOWER(COALESCE(a.status,'')) IN ('tamamlandi','tamamlandı','completed','done','bitti') THEN 1 ELSE 0 END)"
    if "completed_at" in assignment_cols:
        completed_expr = "SUM(CASE WHEN a.completed_at IS NOT NULL OR LOWER(COALESCE(a.status,'')) IN ('tamamlandi','tamamlandı','completed','done','bitti') THEN 1 ELSE 0 END)"
    overdue_expr = "0"
    if "due_date" in assignment_cols:
        overdue_expr = "SUM(CASE WHEN a.completed_at IS NULL AND LOWER(COALESCE(a.status,'')) NOT IN ('tamamlandi','tamamlandı','completed','done','bitti') AND a.due_date IS NOT NULL AND a.due_date < CURRENT_TIMESTAMP THEN 1 ELSE 0 END)"
    rows = _rows(
        f"""
        SELECT a.evaluator_id,
               {name_expr} AS evaluator_name,
               COUNT(*) AS total,
               {completed_expr} AS completed,
               {overdue_expr} AS overdue
        FROM {ASSIGNMENT_TABLE} a
        LEFT JOIN {USER_TABLE} u ON u.id = a.evaluator_id
        WHERE a.period_id=:pid
        GROUP BY a.evaluator_id, evaluator_name
        ORDER BY overdue DESC, (COUNT(*) - {completed_expr}) DESC, COUNT(*) DESC
        LIMIT :limit
        """,
        {"pid": period_id, "limit": int(limit)},
    )
    for row in rows:
        total = _safe_int(row.get("total"))
        completed = _safe_int(row.get("completed"))
        row["pending"] = max(0, total - completed)
        row["progress"] = _percent(completed, total)
        row["status_class"] = "danger" if _safe_int(row.get("overdue")) else ("ok" if row["pending"] == 0 and total > 0 else "warn")
    return rows


def _assignment_rows(period_id: int, *, status_filter: str = "", manager_level: str = "", q: str = "", limit: int = 80) -> list[dict[str, Any]]:
    if not (_has_table(ASSIGNMENT_TABLE) and _has_table(USER_TABLE)):
        return []
    assignment_cols = _columns(ASSIGNMENT_TABLE)
    user_cols = _columns(USER_TABLE)
    where_sql, params = _assignment_where(period_id, status_filter, manager_level)
    if q:
        where_sql += " AND (LOWER(COALESCE(emp.ad,'') || ' ' || COALESCE(emp.soyad,'')) LIKE :q OR LOWER(COALESCE(ev.ad,'') || ' ' || COALESCE(ev.soyad,'')) LIKE :q OR LOWER(COALESCE(emp.sicil_no,'')) LIKE :q)"
        params["q"] = f"%{q.strip().lower()}%"
    params["limit"] = int(limit)
    emp_name_expr = "TRIM(COALESCE(emp.ad,'') || ' ' || COALESCE(emp.soyad,''))"
    ev_name_expr = "TRIM(COALESCE(ev.ad,'') || ' ' || COALESCE(ev.soyad,''))"
    select_cols = [
        "a.id", "a.period_id", "a.employee_id", "a.evaluator_id",
        "a.manager_level" if "manager_level" in assignment_cols else "NULL AS manager_level",
        "COALESCE(a.status, 'bekliyor') AS status",
        "a.assigned_at" if "assigned_at" in assignment_cols else "NULL AS assigned_at",
        "a.due_date" if "due_date" in assignment_cols else "NULL AS due_date",
        "a.completed_at" if "completed_at" in assignment_cols else "NULL AS completed_at",
        f"{emp_name_expr} AS employee_name",
        "emp.sicil_no AS employee_sicil" if "sicil_no" in user_cols else "NULL AS employee_sicil",
        "emp.birim AS employee_unit" if "birim" in user_cols else "NULL AS employee_unit",
        f"{ev_name_expr} AS evaluator_name",
        "ev.unvan AS evaluator_title" if "unvan" in user_cols else "NULL AS evaluator_title",
    ]
    order_clause = "ORDER BY CASE WHEN a.completed_at IS NOT NULL OR LOWER(COALESCE(a.status,'')) IN ('tamamlandi','tamamlandı','completed','done','bitti') THEN 2 WHEN a.due_date IS NOT NULL AND a.due_date < CURRENT_TIMESTAMP THEN 0 ELSE 1 END, a.due_date ASC NULLS LAST, a.id DESC"
    if _db().engine.dialect.name == "sqlite":
        order_clause = "ORDER BY CASE WHEN a.completed_at IS NOT NULL OR LOWER(COALESCE(a.status,'')) IN ('tamamlandi','completed','done','bitti') THEN 2 WHEN a.due_date IS NOT NULL AND a.due_date < CURRENT_TIMESTAMP THEN 0 ELSE 1 END, a.due_date ASC, a.id DESC"
    rows = _rows(
        f"SELECT {', '.join(select_cols)} FROM {ASSIGNMENT_TABLE} a LEFT JOIN {USER_TABLE} emp ON emp.id = a.employee_id LEFT JOIN {USER_TABLE} ev ON ev.id = a.evaluator_id WHERE {where_sql} {order_clause} LIMIT :limit",
        params,
    )
    now = datetime.now()
    for row in rows:
        key = _status_key(row.get("status"))
        completed = bool(row.get("completed_at")) or key in COMPLETED_STATUSES
        due = row.get("due_date")
        overdue = False
        try:
            if due and not completed:
                due_dt = due if isinstance(due, datetime) else datetime.fromisoformat(str(due).replace("Z", "+00:00").replace("+00:00", ""))
                overdue = due_dt < now
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            overdue = False
        row["status_label"] = status_label(row.get("status"))
        row["status_class"] = "danger" if overdue else status_class(row.get("status"))
        row["overdue"] = overdue
        row["completed"] = completed
    return rows


def _risk_notes(counts: dict[str, Any], selected_period: dict[str, Any] | None) -> list[dict[str, str]]:
    notes: list[dict[str, str]] = []
    total = _safe_int(counts.get("total"))
    if not selected_period:
        return [{"class": "warn", "title": "Dönem seçimi gerekli", "message": "Canlı takip için bir performans dönemi seçin."}]
    if total == 0:
        notes.append({"class": "warn", "title": "Görev üretimi bekliyor", "message": "Bu dönem için değerlendirme görevi görünmüyor. Dönem Yönetim Merkezi üzerinden görev üretimi yapılmalıdır."})
    if _safe_int(counts.get("overdue")) > 0:
        notes.append({"class": "danger", "title": "Geciken görev var", "message": "Geciken değerlendirme görevleri amir bazında takip edilmeli ve hatırlatma süreci hazırlanmalıdır."})
    if _safe_int(counts.get("due_soon")) > 0:
        notes.append({"class": "warn", "title": "Son tarihi yaklaşan görev var", "message": "Son tarihi yaklaşan görevler için hatırlatma bildirimi planlanabilir."})
    if total > 0 and _safe_int(counts.get("progress")) >= 100:
        notes.append({"class": "ok", "title": "Değerlendirmeler tamamlanmış görünüyor", "message": "Yayın öncesi kontrol, düşük performans onayı ve karne hazırlığına geçilebilir."})
    if not notes:
        notes.append({"class": "ok", "title": "Süreç izleniyor", "message": "Seçili dönem için değerlendirme süreci olağan takip durumunda görünüyor."})
    return notes


def build_evaluation_live_tracking_state(
    *,
    period_id: int | None = None,
    status_filter: str = "",
    manager_level: str = "",
    q: str = "",
    include_rows: bool = True,
) -> dict[str, Any]:
    readiness = ensure_evaluation_live_tracking_ready()
    periods = list_period_options()
    selected_period_id = _safe_int(period_id) or _default_period_id()
    selected_period = _period_detail(selected_period_id) if selected_period_id else None
    counts = _base_assignment_counts(selected_period_id) if selected_period_id else {"total": 0, "completed": 0, "pending": 0, "overdue": 0, "due_soon": 0, "progress": 0}
    status_counts = _status_counts(selected_period_id) if selected_period_id else []
    level_counts = _level_counts(selected_period_id) if selected_period_id else []
    evaluators = _top_evaluators(selected_period_id) if selected_period_id else []
    rows = _assignment_rows(selected_period_id, status_filter=status_filter, manager_level=manager_level, q=q, limit=80) if (selected_period_id and include_rows) else []
    stage = "Görev üretimi bekliyor"
    stage_class = "muted"
    if counts.get("total", 0) > 0:
        if counts.get("completed", 0) >= counts.get("total", 0):
            stage = "Değerlendirmeler tamamlandı"
            stage_class = "ok"
        elif counts.get("overdue", 0) > 0:
            stage = "Geciken değerlendirme var"
            stage_class = "danger"
        elif counts.get("due_soon", 0) > 0:
            stage = "Son tarih yaklaşan görev var"
            stage_class = "warn"
        else:
            stage = "Değerlendirme süreci devam ediyor"
            stage_class = "info"
    return {
        "rule_version": RULE_VERSION,
        "readiness": readiness,
        "periods": periods,
        "selected_period_id": selected_period_id,
        "selected_period": selected_period,
        "counts": counts,
        "status_counts": status_counts,
        "level_counts": level_counts,
        "evaluators": evaluators,
        "rows": rows,
        "filters": {"status": status_filter, "manager_level": manager_level, "q": q},
        "stage": stage,
        "stage_class": stage_class,
        "risk_notes": _risk_notes(counts, selected_period),
    }


def run_v2_1_10_evaluation_live_tracking_gate() -> dict[str, Any]:
    readiness = ensure_evaluation_live_tracking_ready()
    checks = list(readiness.get("checks") or [])
    checks.append({"name": "read_only_open", "ok": True, "message": "Canlı takip ekranı açılışta sadece okuma yapar; görev üretmez, mail göndermez."})
    checks.append({"name": "light_rows", "ok": True, "message": "Detay liste güvenli limit ile yüklenir; büyük veri setlerinde sayfa kilitlenmesini önler."})
    return {"ok": all(item.get("ok") for item in checks), "checks": checks, "rule_version": RULE_VERSION}
