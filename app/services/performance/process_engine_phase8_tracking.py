from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import bindparam, text

from app.extensions import db

logger = logging.getLogger(__name__)

# PHASE8_TRACKING_PRIORITY_NUMERIC_COMPAT
def _normalize_tracking_priority(value):
    """Return numeric tracking priority for DB compatibility.

    The tracking service may classify priorities with Turkish labels such as
    'yuksek'. The existing production column is numeric, so we normalize labels
    before persistence instead of changing the table type.
    """
    if value is None:
        return 50
    if isinstance(value, bool):
        return 100 if value else 50
    try:
        return int(value)
    except (TypeError, ValueError):
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/performance/process_engine_phase8_tracking.py)")
    normalized = str(value).strip().lower()
    mapping = {
        "kritik": 100,
        "acil": 100,
        "yüksek": 80,
        "yuksek": 80,
        "orta": 50,
        "normal": 50,
        "düşük": 20,
        "dusuk": 20,
        "low": 20,
        "medium": 50,
        "high": 80,
        "critical": 100,
    }
    return mapping.get(normalized, 50)
PHASE8_VERSION = "2026-04-30-process-tracking-phase8"


@dataclass(frozen=True)
class Phase8SyncResult:
    flows_checked: int = 0
    flows_updated: int = 0


def _prepare_clause(sql: str, expanding: tuple[str, ...]):
    """BYS360 DEFECT AB: builds a dialect-neutral TextClause. `expanding`
    names bind parameters whose value is a Python list that must become a
    real SQL IN-list (`IN (:p_1, :p_2, ...)`) at execute time, working
    identically on PostgreSQL and SQLite -- unlike PostgreSQL's `= ANY(:x)`
    array-bind syntax, which SQLite has no equivalent for at all."""
    clause = text(sql)
    if expanding:
        clause = clause.bindparams(*(bindparam(name, expanding=True) for name in expanding))
    return clause


def _scalar(sql: str, params: dict[str, Any] | None = None, *, expanding: tuple[str, ...] = ()) -> Any:
    return db.session.execute(_prepare_clause(sql, expanding), params or {}).scalar()


def _rows(sql: str, params: dict[str, Any] | None = None, *, expanding: tuple[str, ...] = ()) -> list[Any]:
    return list(db.session.execute(_prepare_clause(sql, expanding), params or {}).mappings())


def _execute(sql: str, params: dict[str, Any] | None = None, *, expanding: tuple[str, ...] = ()) -> Any:
    return db.session.execute(_prepare_clause(sql, expanding), params or {})


def table_exists(table_name: str) -> bool:
    """Return whether a table exists for the active SQLAlchemy database.

    Local development may run on SQLite, while live commonly runs on PostgreSQL.
    The old implementation used PostgreSQL information_schema directly and caused
    500 errors on SQLite pages such as /performance/process-tracking.
    """
    try:
        bind = db.session.get_bind()
        dialect_name = getattr(getattr(bind, "dialect", None), "name", "") or ""

        if dialect_name == "sqlite":
            return bool(
                _scalar(
                    """
                    SELECT 1
                    FROM sqlite_master
                    WHERE type = 'table'
                      AND name = :table_name
                    LIMIT 1
                    """,
                    {"table_name": table_name},
                )
            )

        return bool(
            _scalar(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                      AND table_name = :table_name
                )
                """,
                {"table_name": table_name},
            )
        )
    except Exception:
        logging.getLogger(__name__).exception(
            "BYS360 process tracking table_exists guvenli fallback | table=%s",
            table_name,
        )
        return False


def column_exists(table_name: str, column_name: str) -> bool:
    """Return whether a column exists on the active database backend."""
    try:
        return column_name in _table_columns(table_name)
    except Exception:
        logger.exception(
            "BYS360 process tracking column_exists guvenli fallback | table=%s column=%s",
            table_name,
            column_name,
        )
        return False


def _table_columns(table_name: str) -> set[str]:
    """Return table column names for SQLite and PostgreSQL safely."""
    try:
        bind = db.session.get_bind()
        dialect_name = getattr(getattr(bind, "dialect", None), "name", "") or ""

        if dialect_name == "sqlite":
            safe_table = "\"" + str(table_name).replace("\"", "\"\"") + "\""
            columns: set[str] = set()
            for row in _rows(f"PRAGMA table_info({safe_table})"):
                row_data = dict(row)
                name = row_data.get("name")
                if name:
                    columns.add(str(name))
            return columns

        return {
            row["column_name"]
            for row in _rows(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = :table_name
                """,
                {"table_name": table_name},
            )
        }
    except Exception:
        logger.exception(
            "BYS360 process tracking _table_columns guvenli fallback | table=%s",
            table_name,
        )
        return set()


def _qident(name: str) -> str:
    return '"' + str(name).replace('\"', '\"\"') + '"'


def _col_expr(alias: str, cols: set[str], column: str, fallback: str = 'NULL') -> str:
    return f"{alias}.{_qident(column)}" if column in cols else fallback


def _name_select_expr(alias: str, cols: set[str], out_alias: str) -> str:
    """Return a schema-safe SQL expression for a user display name.

    Some live databases have ``full_name_cache`` while older repair scripts
    expected ``full_name``. This helper never references a missing column,
    so process tracking does not fail with UndefinedColumn errors.
    """
    parts: list[str] = []
    for column in (
        'full_name_cache', 'full_name', 'display_name', 'ad_soyad',
        'adi_soyadi', 'name', 'username', 'email'
    ):
        if column in cols:
            parts.append(f"NULLIF({alias}.{_qident(column)}, '')")
    first_candidates = ['ad', 'adi', 'first_name']
    last_candidates = ['soyad', 'soyadi', 'last_name']
    first = next((c for c in first_candidates if c in cols), None)
    last = next((c for c in last_candidates if c in cols), None)
    if first or last:
        first_expr = f"COALESCE({alias}.{_qident(first)}, '')" if first else "''"
        last_expr = f"COALESCE({alias}.{_qident(last)}, '')" if last else "''"
        parts.insert(0, f"NULLIF(TRIM({first_expr} || ' ' || {last_expr}), '')")
    if not parts:
        return f"NULL AS {out_alias}"
    return f"COALESCE({', '.join(parts)}) AS {out_alias}"


def _period_name_select_expr(alias: str, cols: set[str]) -> str:
    """Return a schema-safe period title expression.

    Prevents old code paths from using a single hard-coded period title column.
    """
    parts: list[str] = []
    for column in ('title', 'name', 'period_name', 'label'):
        if column in cols:
            parts.append(f"NULLIF({alias}.{_qident(column)}, '')")
    if parts:
        return f"COALESCE({', '.join(parts)}, CAST(f.period_id AS TEXT)) AS period_name,"
    return "CAST(f.period_id AS TEXT) AS period_name,"

def _add_column(table_name: str, column_name: str, ddl_type: str) -> None:
    """BYS360 DEFECT AI: ``ADD COLUMN IF NOT EXISTS`` is PostgreSQL-only --
    SQLite raises ``sqlite3.OperationalError: near "EXISTS": syntax error``
    on it unconditionally (confirmed empirically), so every call to
    ``apply_phase8_schema()`` was completely broken under SQLite. Existence
    is now checked with this module's own dialect-neutral ``column_exists``
    (already used elsewhere in this file), then a plain ``ADD COLUMN``
    (portable to both dialects) runs only when the column is actually
    missing -- preserving idempotency without depending on PostgreSQL-only
    syntax."""
    if column_exists(table_name, column_name):
        return
    db.session.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl_type}"))


def _create_index(index_name: str, ddl: str) -> None:
    db.session.execute(text(f"CREATE INDEX IF NOT EXISTS {index_name} {ddl}"))


def apply_phase8_schema() -> None:
    required_tables = [
        "performance_process_flows",
        "performance_process_flow_steps",
        "performance_scoring_history",
        "performance_president_approvals",
        "performance_process_notifications",
    ]
    missing = [name for name in required_tables if not table_exists(name)]
    if missing:
        raise RuntimeError("Faz 8 icin Faz 2-7 altyapisi gerekli: " + ", ".join(missing))

    flow_columns = {
        "tracking_status": "VARCHAR(80)",
        "tracking_bucket": "VARCHAR(80)",
        "tracking_priority": "VARCHAR(40) DEFAULT 'normal'",
        "tracking_label": "VARCHAR(255)",
        "tracking_url": "VARCHAR(500)",
        "is_overdue": "BOOLEAN DEFAULT FALSE",
        "overdue_days": "INTEGER DEFAULT 0",
        "last_visible_action": "VARCHAR(255)",
        "tracking_updated_at": "TIMESTAMP",
    }
    for column_name, ddl_type in flow_columns.items():
        _add_column("performance_process_flows", column_name, ddl_type)

    step_columns = {
        "tracking_visible": "BOOLEAN DEFAULT TRUE",
        "tracking_group": "VARCHAR(80)",
    }
    for column_name, ddl_type in step_columns.items():
        _add_column("performance_process_flow_steps", column_name, ddl_type)

    db.session.execute(
        text(
            """
            UPDATE performance_process_flows
               SET tracking_status = COALESCE(tracking_status, current_status, 'takipte'),
                   tracking_bucket = COALESCE(
                        tracking_bucket,
                        CASE
                            WHEN LOWER(COALESCE(president_status, president_approval_status, '')) IN ('pending', 'bekliyor', 'baskan_onayi_bekliyor', 'başkan_onayı_bekliyor') THEN 'president_pending'
                            WHEN COALESCE(is_finalized, FALSE) = TRUE OR LOWER(COALESCE(current_status, '')) IN ('finalized', 'kesinlesti', 'kesinleşti', 'completed', 'tamamlandi', 'tamamlandı') THEN 'completed'
                            WHEN current_owner_user_id IS NOT NULL THEN 'waiting'
                            ELSE 'monitoring'
                        END
                   ),
                   tracking_label = COALESCE(tracking_label, current_stage, last_action_title, 'Süreç takipte'),
                   tracking_url = COALESCE(tracking_url, '/performans/surec-takibi'),
                   overdue_days = COALESCE(overdue_days, 0),
                   is_overdue = COALESCE(is_overdue, FALSE),
                   last_visible_action = COALESCE(last_visible_action, last_action_title, current_stage),
                   tracking_updated_at = COALESCE(tracking_updated_at, CURRENT_TIMESTAMP),
                   process_version = COALESCE(process_version, :version)
            """
        ),
        {"version": PHASE8_VERSION},
    )
    db.session.execute(
        text(
            """
            UPDATE performance_process_flow_steps
               SET tracking_visible = COALESCE(tracking_visible, TRUE),
                   tracking_group = COALESCE(tracking_group, status, step_code, 'surec')
            """
        )
    )
    _create_index("ix_perf_flow_tracking_bucket_phase8", "ON performance_process_flows(tracking_bucket)")
    _create_index("ix_perf_flow_tracking_owner_phase8", "ON performance_process_flows(current_owner_user_id, tracking_bucket)")
    _create_index("ix_perf_flow_tracking_overdue_phase8", "ON performance_process_flows(is_overdue, overdue_days)")
    _create_index("ix_perf_steps_tracking_visible_phase8", "ON performance_process_flow_steps(flow_id, tracking_visible)")
    db.session.commit()


def normalize_role(value: Any) -> str:
    raw = str(value or "").strip().lower()
    tr_map = str.maketrans("çğıöşüâîûİ", "cgiosuaiui")
    return raw.translate(tr_map).replace(" ", "_").replace("-", "_")


def user_display_name(user: Any) -> str:
    if user is None:
        return ""
    full = str(getattr(user, "full_name", "") or "").strip()
    if full:
        return full
    ad = str(getattr(user, "ad", "") or "").strip()
    soyad = str(getattr(user, "soyad", "") or "").strip()
    name = f"{ad} {soyad}".strip()
    return name or str(getattr(user, "email", "") or "").strip() or "Kullanıcı"


def is_admin_user(user: Any) -> bool:
    role = normalize_role(getattr(user, "role", None))
    return role in {"admin", "super_admin", "sistem_yoneticisi"}


def is_process_tracking_user(user: Any) -> bool:
    role = normalize_role(getattr(user, "role", None))
    title = normalize_role(getattr(user, "unvan", None))
    combined = f"{role} {title}"
    allowed_tokens = {
        "admin",
        "super_admin",
        "sistem_yoneticisi",
        "baskan",
        "baskan_yardimcisi",
        "grup_baskani",
        "koordinator",
        "mali_musavir",
        "birim_sorumlusu",
    }
    return bool(allowed_tokens.intersection(set(combined.split()))) or any(token in combined for token in allowed_tokens)


def can_view_process_tracking(user: Any) -> bool:
    return is_process_tracking_user(user)


def can_manage_process_tracking(user: Any) -> bool:
    """Süreç takip listesini temizleme yetkisi.

    Bu işlem değerlendirme/karne verisini değil, yalnızca süreç takip listesi
    kayıtlarını kaldırır. Canlı kullanımda yetkiyi sınırlı tutmak için admin,
    üst yönetim ve performans/personel destek yetkilileriyle sınırlandırılır.
    """
    role = normalize_role(getattr(user, "role", None))
    title = normalize_role(getattr(user, "unvan", None))
    combined = f"{role} {title}"
    if role in {"admin", "super_admin", "sistem_yoneticisi"}:
        return True
    allowed_tokens = (
        "baskan",
        "baskan_yardimcisi",
        "performans_yetkilisi",
        "personel_destek",
        "personel_ve_destek",
        "personel_destek_hizmetleri_grup_baskani",
    )
    return any(token in combined for token in allowed_tokens)


def _safe_text(value: Any, fallback: str = "-") -> str:
    text_value = str(value or "").strip()
    return text_value if text_value else fallback


def _safe_score(value: Any) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return str(value)


def _safe_date(value: Any) -> str:
    if value is None:
        return "-"
    if hasattr(value, "strftime"):
        return value.strftime("%d.%m.%Y %H:%M")
    return str(value)


def _normalize_status_key(value: Any) -> str:
    raw = str(value or "").strip().lower()
    tr_map = str.maketrans("çğıöşüâîûİ", "cgiosuaiui")
    return raw.translate(tr_map).replace(" ", "_").replace("-", "_")


def _clean_process_label(value: Any, fallback: str = "Süreçte") -> str:
    key = _normalize_status_key(value)
    labels = {
        "pending": "Bekliyor",
        "waiting": "Bekliyor",
        "bekliyor": "Bekliyor",
        "in_progress": "Süreçte",
        "takipte": "Süreçte",
        "monitoring": "Süreçte",
        "process": "Süreçte",
        "completed": "Tamamlandı",
        "finalized": "Tamamlandı",
        "tamamlandi": "Tamamlandı",
        "kesinlesti": "Tamamlandı",
        "approved": "Onaylandı",
        "approved_by_president": "Başkan Tarafından Onaylandı",
        "president_pending": "Başkan/Üst Onay Bekliyor",
        "baskan_onayi_bekliyor": "Başkan/Üst Onay Bekliyor",
        "blocked_president_pending": "Başkan/Üst Onay Kilidi",
        "hr_precheck": "Kontrol Aşamasında",
        "first_low_warning": "Düşük Performans Uyarısı Oluşturuldu",
        "second_low_repeat": "Tekrarlayan Düşük Performans Süreci",
        "returned": "İade Edildi",
        "rejected": "İade Edildi",
        "iade": "İade Edildi",
        "iade_edildi": "İade Edildi",
        "overdue": "Gecikti",
        "late": "Gecikti",
    }
    if key in labels:
        return labels[key]
    text_value = str(value or "").strip()
    if not text_value:
        return fallback
    # Kullanıcı ekranına geliştirici durum kodu düşmesin.
    if "_" in text_value or text_value.isupper() or key in {"draft", "debug", "sync", "workflow_state", "phase"}:
        return fallback
    return text_value


def _bucket_tone(bucket: str) -> str:
    key = _normalize_status_key(bucket)
    if key in {"overdue", "president_pending"}:
        return "danger"
    if key in {"waiting", "monitoring"}:
        return "warning"
    if key in {"completed", "approved"}:
        return "success"
    if key in {"returned", "rejected"}:
        return "neutral"
    return "info"


def _full_name_from_row(row: Any, prefix: str) -> str:
    full = _safe_text(row.get(prefix + "_full_name"), "")
    if full:
        return full
    ad = _safe_text(row.get(prefix + "_ad"), "")
    soyad = _safe_text(row.get(prefix + "_soyad"), "")
    name = f"{ad} {soyad}".strip()
    return name or _safe_text(row.get(prefix + "_email"))


def _status_clause(status_filter: str) -> tuple[str, dict[str, Any]]:
    normalized = str(status_filter or "all").strip().lower()
    if normalized in {"all", "tum", "tumu"}:
        return "", {}
    if normalized in {"waiting", "bekleyen"}:
        return "AND COALESCE(f.current_owner_user_id, 0) <> 0 AND LOWER(COALESCE(f.tracking_bucket, f.current_status, '')) NOT IN ('completed', 'finalized', 'kesinlesti', 'kesinleşti')", {}
    if normalized in {"president", "baskan", "baskan_onayi"}:
        return "AND LOWER(COALESCE(f.president_status, f.president_approval_status, f.tracking_bucket, '')) IN ('pending', 'bekliyor', 'president_pending', 'baskan_onayi_bekliyor', 'başkan_onayı_bekliyor')", {}
    if normalized in {"overdue", "geciken"}:
        return "AND COALESCE(f.is_overdue, FALSE) = TRUE", {}
    if normalized in {"completed", "tamamlanan"}:
        return "AND (COALESCE(f.is_finalized, FALSE) = TRUE OR LOWER(COALESCE(f.current_status, '')) IN ('completed', 'finalized', 'kesinlesti', 'kesinleşti', 'tamamlandi', 'tamamlandı'))", {}
    if normalized in {"returned", "iade"}:
        return "AND LOWER(COALESCE(f.president_status, f.president_approval_status, f.current_status, '')) IN ('returned', 'iade', 'iade_edildi')", {}
    return "", {}


def _scope_clause(viewer: Any) -> tuple[str, dict[str, Any]]:
    if is_admin_user(viewer):
        return "", {}
    viewer_id = int(getattr(viewer, "id", 0) or 0)
    role = normalize_role(getattr(viewer, "role", None))
    title = normalize_role(getattr(viewer, "unvan", None))
    if "baskan" in f"{role} {title}":
        return "", {}
    return "AND (f.current_owner_user_id = :viewer_id OR f.employee_id = :viewer_id)", {"viewer_id": viewer_id}


def _build_search_clause(search: str) -> tuple[str, dict[str, Any]]:
    cleaned = str(search or "").strip()
    if not cleaned:
        return "", {}

    user_cols = _table_columns("users") if table_exists("users") else set()
    search_parts: list[str] = []
    for alias in ("emp", "owner"):
        for column in (
            "full_name_cache", "full_name", "display_name", "ad_soyad",
            "adi_soyadi", "name", "username", "email", "ad", "soyad",
            "adi", "soyadi", "sicil_no"
        ):
            if column in user_cols:
                search_parts.append(f"LOWER(COALESCE({alias}.{_qident(column)}, '')) LIKE :search")
    search_parts.extend([
        "LOWER(COALESCE(f.current_stage, '')) LIKE :search",
        "LOWER(COALESCE(f.current_status, '')) LIKE :search",
        "LOWER(COALESCE(f.tracking_label, '')) LIKE :search",
        "LOWER(COALESCE(f.last_action_title, '')) LIKE :search",
    ])
    return "AND (" + " OR ".join(search_parts) + ")", {"search": f"%{cleaned.lower()}%"}


def _flow_base_rows(*, viewer: Any, status_filter: str, search: str, limit: int = 300) -> list[Any]:
    status_sql, status_params = _status_clause(status_filter)
    scope_sql, scope_params = _scope_clause(viewer)
    search_sql, search_params = _build_search_clause(search)
    params = {"limit": int(limit), **status_params, **scope_params, **search_params}

    period_join = ""
    period_select = "CAST(f.period_id AS TEXT) AS period_name,"
    if table_exists("performance_periods"):
        period_cols = _table_columns("performance_periods")
        period_join = "LEFT JOIN performance_periods pp ON pp.id = f.period_id"
        period_select = _period_name_select_expr("pp", period_cols)

    user_cols = _table_columns("users") if table_exists("users") else set()
    emp_full_name = _name_select_expr("emp", user_cols, "emp_full_name")
    owner_full_name = _name_select_expr("owner", user_cols, "owner_full_name")
    emp_ad = f"emp.{_qident('ad')} AS emp_ad" if "ad" in user_cols else "NULL AS emp_ad"
    emp_soyad = f"emp.{_qident('soyad')} AS emp_soyad" if "soyad" in user_cols else "NULL AS emp_soyad"
    emp_email = f"emp.{_qident('email')} AS emp_email" if "email" in user_cols else "NULL AS emp_email"
    owner_ad = f"owner.{_qident('ad')} AS owner_ad" if "ad" in user_cols else "NULL AS owner_ad"
    owner_soyad = f"owner.{_qident('soyad')} AS owner_soyad" if "soyad" in user_cols else "NULL AS owner_soyad"
    owner_email = f"owner.{_qident('email')} AS owner_email" if "email" in user_cols else "NULL AS owner_email"

    return _rows(
        f"""
        SELECT
            f.id AS flow_id,
            f.evaluation_id,
            f.period_id,
            {period_select}
            f.employee_id,
            f.current_status,
            f.current_stage,
            f.current_owner_user_id,
            f.current_owner_name,
            f.last_action_title,
            f.last_action_at,
            f.waiting_since,
            f.waiting_days,
            f.is_overdue,
            f.overdue_days,
            f.tracking_status,
            f.tracking_bucket,
            f.tracking_priority,
            f.tracking_label,
            f.last_visible_action,
            f.final_score,
            f.president_required,
            f.president_status,
            f.president_approval_status,
            f.president_requested_at,
            f.is_finalized,
            {emp_full_name},
            {emp_ad},
            {emp_soyad},
            {emp_email},
            {owner_full_name},
            {owner_ad},
            {owner_soyad},
            {owner_email}
        FROM performance_process_flows f
        LEFT JOIN users emp ON emp.id = f.employee_id
        LEFT JOIN users owner ON owner.id = f.current_owner_user_id
        {period_join}
        WHERE 1=1
        {status_sql}
        {scope_sql}
        {search_sql}
        ORDER BY COALESCE(f.is_overdue, FALSE) DESC,
                 COALESCE(f.waiting_days, 0) DESC,
                 COALESCE(f.last_action_at, f.updated_by_engine_at, f.created_at, CURRENT_TIMESTAMP) DESC
        LIMIT :limit
        """,
        params,
    )


def _steps_for_flows(flow_ids: list[int]) -> dict[int, list[dict[str, Any]]]:
    if not flow_ids:
        return {}
    _table_columns("performance_process_flow_steps")
    order_expr = "COALESCE(step_order, 0), COALESCE(action_at, created_at, CURRENT_TIMESTAMP), id"
    rows = _rows(
        f"""
        SELECT *
        FROM performance_process_flow_steps
        WHERE flow_id IN :flow_ids
          AND COALESCE(tracking_visible, TRUE) = TRUE
        ORDER BY {order_expr}
        """,
        {"flow_ids": flow_ids},
        expanding=("flow_ids",),
    )
    grouped: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        flow_id = int(row.get("flow_id") or 0)
        title = _safe_text(row.get("visible_title") or row.get("step_title") or row.get("step_code"), "Süreç adımı")
        status = _clean_process_label(row.get("visible_status") or row.get("status"), "Süreç adımı")
        description = _safe_text(row.get("description"), "")
        item = {
            "title": title,
            "status": status,
            "description": description,
            "owner_name": _safe_text(row.get("waiting_owner_name"), ""),
            "action_at": _safe_date(row.get("action_at") or row.get("created_at")),
            "code": _safe_text(row.get("step_code"), ""),
        }
        grouped.setdefault(flow_id, []).append(item)
    return grouped


def _history_for_flows(flow_ids: list[int]) -> dict[int, list[dict[str, Any]]]:
    if not flow_ids:
        return {}
    if not column_exists("performance_scoring_history", "evaluation_id"):
        return {}
    rows = _rows(
        """
        SELECT
            h.*,
            f.id AS flow_id
        FROM performance_scoring_history h
        JOIN performance_process_flows f
          ON f.evaluation_id = h.evaluation_id
        WHERE f.id IN :flow_ids
        ORDER BY COALESCE(h.action_at, h.created_at, CURRENT_TIMESTAMP), h.id
        """,
        {"flow_ids": flow_ids},
        expanding=("flow_ids",),
    )
    grouped: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        flow_id = int(row.get("flow_id") or 0)
        grouped.setdefault(flow_id, []).append(
            {
                "scorer_name": _safe_text(row.get("scorer_name"), "-"),
                "manager_level": _clean_process_label(row.get("manager_level"), "Amir"),
                "score_value": _safe_score(row.get("score_value")),
                "action_status": _clean_process_label(row.get("action_status"), "Süreçte"),
                "action_at": _safe_date(row.get("action_at") or row.get("created_at")),
                "next_stage": _safe_text(row.get("next_stage"), ""),
                "next_owner_name": _safe_text(row.get("next_owner_name"), ""),
            }
        )
    return grouped


def _row_bucket(row: Any) -> str:
    raw = str(row.get("tracking_bucket") or row.get("current_status") or "monitoring").strip().lower()
    if str(row.get("president_status") or row.get("president_approval_status") or "").lower() in {"pending", "bekliyor", "president_pending", "baskan_onayi_bekliyor", "başkan_onayı_bekliyor"}:
        return "president_pending"
    if row.get("is_overdue"):
        return "overdue"
    if row.get("is_finalized") or raw in {"completed", "finalized", "kesinlesti", "kesinleşti", "tamamlandi", "tamamlandı"}:
        return "completed"
    if row.get("current_owner_user_id"):
        return "waiting"
    return raw or "monitoring"


def _visible_bucket(bucket: str) -> str:
    labels = {
        "president_pending": "Başkan/Üst Onay Bekliyor",
        "overdue": "Gecikmiş Süreç",
        "waiting": "İşlem Bekliyor",
        "completed": "Tamamlandı",
        "returned": "İade Edildi",
        "monitoring": "Süreçte",
    }
    return labels.get(_normalize_status_key(bucket), "Süreçte")


def build_process_tracking_workspace(
    viewer: Any,
    *,
    status_filter: str = "all",
    search: str = "",
    limit: int = 300,
) -> dict[str, Any]:
    rows = _flow_base_rows(viewer=viewer, status_filter=status_filter, search=search, limit=limit)
    flow_ids = [int(row["flow_id"]) for row in rows if row.get("flow_id")]
    steps = _steps_for_flows(flow_ids)
    histories = _history_for_flows(flow_ids)
    items: list[dict[str, Any]] = []
    counts = {
        "total": 0,
        "waiting": 0,
        "overdue": 0,
        "president_pending": 0,
        "completed": 0,
        "returned": 0,
        "monitoring": 0,
    }
    for row in rows:
        bucket = _row_bucket(row)
        counts["total"] += 1
        counts[bucket if bucket in counts else "monitoring"] += 1
        flow_id = int(row.get("flow_id") or 0)
        owner_name = _safe_text(row.get("current_owner_name"), "") or _full_name_from_row(row, "owner")
        if owner_name == "-":
            owner_name = "Süreçte bekleyen kişi yok"
        item = {
            "flow_id": flow_id,
            "evaluation_id": row.get("evaluation_id"),
            "period_id": row.get("period_id"),
            "period_name": _safe_text(row.get("period_name"), "-"),
            "employee_id": row.get("employee_id"),
            "employee_name": _full_name_from_row(row, "emp"),
            "current_stage": _clean_process_label(row.get("current_stage") or row.get("tracking_label"), "Süreç takipte"),
            "current_status": _clean_process_label(row.get("current_status") or row.get("tracking_status"), "Süreçte"),
            "bucket": bucket,
            "bucket_label": _visible_bucket(bucket),
            "status_label": _visible_bucket(bucket),
            "status_tone": _bucket_tone(bucket),
            "owner_name": owner_name,
            "owner_user_id": row.get("current_owner_user_id"),
            "last_action": _clean_process_label(row.get("last_visible_action") or row.get("last_action_title"), "Süreç takipte"),
            "last_action_at": _safe_date(row.get("last_action_at")),
            "waiting_since": _safe_date(row.get("waiting_since")),
            "waiting_days": int(row.get("waiting_days") or 0),
            "is_overdue": bool(row.get("is_overdue")),
            "overdue_days": int(row.get("overdue_days") or 0),
            "final_score": _safe_score(row.get("final_score")),
            "president_required": bool(row.get("president_required")),
            "president_status": _clean_process_label(row.get("president_status") or row.get("president_approval_status"), "-"),
            "president_requested_at": _safe_date(row.get("president_requested_at")),
            "steps": steps.get(flow_id, []),
            "history": histories.get(flow_id, []),
        }
        items.append(item)
    return {
        "page_title": "Performans Süreç Takibi",
        "page_subtitle": "Değerlendirme süreçleri, gecikmeler, üst onaylar ve tamamlanan kayıtlar yetki kapsamına göre izlenir.",
        "status_filter": status_filter,
        "search": search,
        "items": items,
        "counts": counts,
        "viewer_name": user_display_name(viewer),
        "last_refreshed_at": _safe_date(datetime.now()),
    }

def _delete_tracking_flow_ids(flow_ids: list[int]) -> int:
    """Delete tracking-list records and their visible tracking children.

    This intentionally does not delete performance evaluations, scorecards,
    scoring history, president approval records or personnel records.
    """
    clean_ids = [int(value) for value in flow_ids if value]
    if not clean_ids or not table_exists("performance_process_flows"):
        return 0

    try:
        if table_exists("performance_process_flow_steps") and column_exists("performance_process_flow_steps", "flow_id"):
            _execute(
                "DELETE FROM performance_process_flow_steps WHERE flow_id IN :flow_ids",
                {"flow_ids": clean_ids},
                expanding=("flow_ids",),
            )

        if table_exists("performance_process_notifications") and column_exists("performance_process_notifications", "flow_id"):
            _execute(
                "DELETE FROM performance_process_notifications WHERE flow_id IN :flow_ids",
                {"flow_ids": clean_ids},
                expanding=("flow_ids",),
            )

        result = _execute(
            "DELETE FROM performance_process_flows WHERE id IN :flow_ids",
            {"flow_ids": clean_ids},
            expanding=("flow_ids",),
        )
        db.session.commit()
        try:
            return int(result.rowcount or 0)
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            return len(clean_ids)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        db.session.rollback()
        raise


def delete_process_tracking_flow(flow_id: int, viewer: Any) -> int:
    if not can_manage_process_tracking(viewer):
        raise PermissionError("Bu işlem için yetkiniz bulunmamaktadır.")
    return _delete_tracking_flow_ids([int(flow_id)])


def delete_visible_process_tracking_flows(
    viewer: Any,
    *,
    status_filter: str = "all",
    search: str = "",
    limit: int = 300,
) -> int:
    if not can_manage_process_tracking(viewer):
        raise PermissionError("Bu işlem için yetkiniz bulunmamaktadır.")
    rows = _flow_base_rows(viewer=viewer, status_filter=status_filter, search=search, limit=limit)
    flow_ids = [int(row["flow_id"]) for row in rows if row.get("flow_id")]
    return _delete_tracking_flow_ids(flow_ids)

def synchronize_phase8_tracking(limit: int | None = None) -> Phase8SyncResult:
    if not table_exists("performance_process_flows"):
        return Phase8SyncResult()
    sql_limit = "LIMIT :limit" if limit else ""
    params = {"limit": int(limit)} if limit else {}
    rows = _rows(
        f"""
        SELECT id, current_status, current_stage, current_owner_user_id, current_owner_name,
               waiting_since, waiting_days, is_finalized, president_status, president_approval_status,
               president_required, last_action_title, last_action_at
        FROM performance_process_flows
        ORDER BY id DESC
        {sql_limit}
        """,
        params,
    )
    updated = 0
    for row in rows:
        flow_id = int(row["id"])
        bucket = _row_bucket(row)
        waiting_days = int(row.get("waiting_days") or 0)
        is_overdue = bool(row.get("is_overdue") or waiting_days >= 7)
        priority = 80 if bucket == "president_pending" or is_overdue else "normal"
        db.session.execute(
            text(
                """
                UPDATE performance_process_flows
                   SET tracking_status = COALESCE(current_status, tracking_status, 'takipte'),
                       tracking_bucket = :bucket,
                       tracking_priority = :priority,
                       tracking_label = COALESCE(current_stage, tracking_label, 'Süreç takipte'),
                       tracking_url = COALESCE(tracking_url, '/performans/surec-takibi'),
                       is_overdue = :is_overdue,
                       overdue_days = CASE WHEN :is_overdue THEN COALESCE(waiting_days, 0) ELSE COALESCE(overdue_days, 0) END,
                       last_visible_action = COALESCE(last_action_title, last_visible_action, current_stage),
                       tracking_updated_at = CURRENT_TIMESTAMP,
                       process_version = :version
                 WHERE id = :flow_id
                """
            ),
            {
                "bucket": bucket,
                "priority": _normalize_tracking_priority(priority),
                "is_overdue": is_overdue,
                "version": PHASE8_VERSION,
                "flow_id": flow_id,
            },
        )
        updated += 1
    db.session.commit()
    return Phase8SyncResult(flows_checked=len(rows), flows_updated=updated)
