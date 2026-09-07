from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import bindparam, inspect, text

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

    BYS360 DEFECT AL: the prior implementation hand-rolled a dialect branch
    (raw ``sqlite_master`` vs. raw PostgreSQL-only ``information_schema``),
    duplicating logic that SQLAlchemy's ``inspect()`` already provides
    dialect-neutrally by construction -- the same proven pattern already
    used elsewhere in this module family (process_engine_phase4_flow.py,
    phase6_president_approvals.py, phase7_president_rule.py).
    """
    try:
        bind = db.session.get_bind()
        return bool(inspect(bind).has_table(table_name))
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
    """Return table column names for SQLite and PostgreSQL safely.

    BYS360 DEFECT AL: dialect-neutral via SQLAlchemy ``inspect()``,
    replacing the prior hand-rolled sqlite_master/information_schema branch.
    """
    try:
        bind = db.session.get_bind()
        inspector = inspect(bind)
        if not inspector.has_table(table_name):
            return set()
        return {str(column["name"]) for column in inspector.get_columns(table_name)}
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


# BYS360 DEFECT AN: these three functions referenced a wide set of
# performance_process_flows columns (current_owner_user_id, tracking_bucket,
# president_status, is_overdue, current_stage, tracking_label,
# last_action_title) that no migration and no reachable runtime schema path
# ever creates -- confirmed against a real, migration-built database. Every
# request to the live Süreç Takibi page raised OperationalError. Fixed with
# this module's own _table_columns() gating (already the established
# pattern elsewhere in this file); current_owner_user_id/president_status
# are replaced by their real, canonical equivalents
# (current_owner_id/president_approval_status) where a real column exists,
# and the remaining fields -- which have no real column under any name
# today -- degrade to their neutral SQL value (never true/never matched)
# rather than raising. Restoring real tracking data for these fields is a
# separate, larger item (a genuine schema migration would be required) and
# is intentionally not attempted here.
def _status_clause(status_filter: str, flow_cols: set[str] | None = None) -> tuple[str, dict[str, Any]]:
    """BYS360 DEFECT AN: takes flow_cols as an optional parameter (falling
    back to its own _table_columns() lookup only when the caller doesn't
    already have one) so this stays a pure, deterministic clause-builder --
    _flow_base_rows() passes its own already-computed set instead of every
    caller of this function issuing its own redundant schema-introspection
    query."""
    normalized = str(status_filter or "all").strip().lower()
    if normalized in {"all", "tum", "tumu"}:
        return "", {}
    if flow_cols is None:
        flow_cols = _table_columns("performance_process_flows")
    owner_expr = "f.current_owner_id" if "current_owner_id" in flow_cols else "NULL"
    bucket_expr = "f.tracking_bucket" if "tracking_bucket" in flow_cols else "NULL"
    president_status_expr = "f.president_status" if "president_status" in flow_cols else "NULL"
    overdue_expr = "f.is_overdue" if "is_overdue" in flow_cols else "NULL"
    if normalized in {"waiting", "bekleyen"}:
        return f"AND COALESCE({owner_expr}, 0) <> 0 AND LOWER(COALESCE({bucket_expr}, f.current_status, '')) NOT IN ('completed', 'finalized', 'kesinlesti', 'kesinleşti')", {}
    if normalized in {"president", "baskan", "baskan_onayi"}:
        return f"AND LOWER(COALESCE({president_status_expr}, f.president_approval_status, {bucket_expr}, '')) IN ('pending', 'bekliyor', 'president_pending', 'baskan_onayi_bekliyor', 'başkan_onayı_bekliyor')", {}
    if normalized in {"overdue", "geciken"}:
        return f"AND COALESCE({overdue_expr}, FALSE) = TRUE", {}
    if normalized in {"completed", "tamamlanan"}:
        return "AND (COALESCE(f.is_finalized, FALSE) = TRUE OR LOWER(COALESCE(f.current_status, '')) IN ('completed', 'finalized', 'kesinlesti', 'kesinleşti', 'tamamlandi', 'tamamlandı'))", {}
    if normalized in {"returned", "iade"}:
        return f"AND LOWER(COALESCE({president_status_expr}, f.president_approval_status, f.current_status, '')) IN ('returned', 'iade', 'iade_edildi')", {}
    return "", {}


def _scope_clause(viewer: Any, flow_cols: set[str] | None = None) -> tuple[str, dict[str, Any]]:
    """BYS360 DEFECT AN: see _status_clause() -- flow_cols is an optional
    parameter for the same reason (pure, deterministic, no redundant
    schema-introspection query when the caller already has one)."""
    if is_admin_user(viewer):
        return "", {}
    viewer_id = int(getattr(viewer, "id", 0) or 0)
    role = normalize_role(getattr(viewer, "role", None))
    title = normalize_role(getattr(viewer, "unvan", None))
    if "baskan" in f"{role} {title}":
        return "", {}
    if flow_cols is None:
        flow_cols = _table_columns("performance_process_flows")
    owner_expr = "f.current_owner_id" if "current_owner_id" in flow_cols else "NULL"
    return f"AND ({owner_expr} = :viewer_id OR f.employee_id = :viewer_id)", {"viewer_id": viewer_id}


def _build_search_clause(search: str) -> tuple[str, dict[str, Any]]:
    cleaned = str(search or "").strip()
    if not cleaned:
        return "", {}

    user_cols = _table_columns("users") if table_exists("users") else set()
    flow_cols = _table_columns("performance_process_flows")
    search_parts: list[str] = []
    for alias in ("emp", "owner"):
        for column in (
            "full_name_cache", "full_name", "display_name", "ad_soyad",
            "adi_soyadi", "name", "username", "email", "ad", "soyad",
            "adi", "soyadi", "sicil_no"
        ):
            if column in user_cols:
                search_parts.append(f"LOWER(COALESCE({alias}.{_qident(column)}, '')) LIKE :search")
    if "current_stage" in flow_cols:
        search_parts.append("LOWER(COALESCE(f.current_stage, '')) LIKE :search")
    search_parts.append("LOWER(COALESCE(f.current_status, '')) LIKE :search")
    for column in ("tracking_label", "last_action_title"):
        if column in flow_cols:
            search_parts.append(f"LOWER(COALESCE(f.{column}, '')) LIKE :search")
    return "AND (" + " OR ".join(search_parts) + ")", {"search": f"%{cleaned.lower()}%"}


def _flow_base_rows(*, viewer: Any, status_filter: str, search: str, limit: int = 300) -> list[Any]:
    # BYS360 DEFECT AN: computed once and passed into _status_clause()/
    # _scope_clause() so they stay pure, deterministic clause-builders
    # instead of each issuing its own redundant schema-introspection query.
    flow_cols = _table_columns("performance_process_flows")
    status_sql, status_params = _status_clause(status_filter, flow_cols)
    scope_sql, scope_params = _scope_clause(viewer, flow_cols)
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

    # BYS360 DEFECT AN: most of these tracking-specific columns have no real
    # backing under any name; each is read with column-presence gating
    # (flow_cols, computed once above) so the query executes, with
    # current_owner_user_id/president_status mapped to their real,
    # canonical equivalents.
    def _flow_expr(name: str, real_name: str | None = None) -> str:
        candidate = real_name or name
        return f"f.{candidate}" if candidate in flow_cols else "NULL"

    current_owner_id_expr = _flow_expr("current_owner_id")
    current_stage_expr = _flow_expr("current_stage")
    current_owner_name_expr = _flow_expr("current_owner_name")
    last_action_title_expr = _flow_expr("last_action_title")
    waiting_since_expr = _flow_expr("waiting_since")
    waiting_days_expr = _flow_expr("waiting_days")
    is_overdue_expr = _flow_expr("is_overdue")
    overdue_days_expr = _flow_expr("overdue_days")
    tracking_status_expr = _flow_expr("tracking_status")
    tracking_bucket_expr = _flow_expr("tracking_bucket")
    tracking_priority_expr = _flow_expr("tracking_priority")
    tracking_label_expr = _flow_expr("tracking_label")
    last_visible_action_expr = _flow_expr("last_visible_action")
    president_required_expr = _flow_expr("president_required", "president_approval_required")
    president_status_expr = _flow_expr("president_status")
    president_requested_at_expr = _flow_expr("president_requested_at")
    updated_by_engine_at_expr = _flow_expr("updated_by_engine_at")
    owner_join = f"LEFT JOIN users owner ON owner.id = {current_owner_id_expr}" if current_owner_id_expr != "NULL" else ""

    return _rows(
        f"""
        SELECT
            f.id AS flow_id,
            f.evaluation_id,
            f.period_id,
            {period_select}
            f.employee_id,
            f.current_status,
            {current_stage_expr} AS current_stage,
            {current_owner_id_expr} AS current_owner_id,
            {current_owner_name_expr} AS current_owner_name,
            {last_action_title_expr} AS last_action_title,
            f.last_action_at,
            {waiting_since_expr} AS waiting_since,
            {waiting_days_expr} AS waiting_days,
            {is_overdue_expr} AS is_overdue,
            {overdue_days_expr} AS overdue_days,
            {tracking_status_expr} AS tracking_status,
            {tracking_bucket_expr} AS tracking_bucket,
            {tracking_priority_expr} AS tracking_priority,
            {tracking_label_expr} AS tracking_label,
            {last_visible_action_expr} AS last_visible_action,
            f.final_score,
            {president_required_expr} AS president_required,
            {president_status_expr} AS president_status,
            f.president_approval_status,
            {president_requested_at_expr} AS president_requested_at,
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
        {owner_join}
        {period_join}
        WHERE 1=1
        {status_sql}
        {scope_sql}
        {search_sql}
        ORDER BY COALESCE({is_overdue_expr}, FALSE) DESC,
                 COALESCE({waiting_days_expr}, 0) DESC,
                 COALESCE(f.last_action_at, {updated_by_engine_at_expr}, f.created_at, CURRENT_TIMESTAMP) DESC
        LIMIT :limit
        """,
        params,
    )


def _steps_for_flows(flow_ids: list[int]) -> dict[int, list[dict[str, Any]]]:
    """BYS360 DEFECT AN: action_at/tracking_visible are not real columns on
    performance_process_flow_steps under any migration or reachable
    runtime schema path -- confirmed against a real, migration-built
    database. Referencing them by name in WHERE/ORDER BY (not just the
    SELECT list) raised OperationalError even though the SELECT itself is
    a plain ``SELECT *``; row.get(...) below already tolerates their
    absence, so only the two raw references need gating."""
    if not flow_ids:
        return {}
    step_cols = _table_columns("performance_process_flow_steps")
    action_at_expr = "action_at" if "action_at" in step_cols else "NULL"
    tracking_visible_filter = (
        " AND COALESCE(tracking_visible, TRUE) = TRUE" if "tracking_visible" in step_cols else ""
    )
    order_expr = f"COALESCE(step_order, 0), COALESCE({action_at_expr}, created_at, CURRENT_TIMESTAMP), id"
    rows = _rows(
        f"""
        SELECT *
        FROM performance_process_flow_steps
        WHERE flow_id IN :flow_ids
        {tracking_visible_filter}
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
    """BYS360 DEFECT AN: action_at is not a real column on
    performance_scoring_history (no migration touches this table; the ORM
    model only has created_at) -- confirmed against a real,
    migration-built database. row.get("action_at") below already falls
    back to created_at, so only the raw ORDER BY reference needs gating."""
    if not flow_ids:
        return {}
    if not column_exists("performance_scoring_history", "evaluation_id"):
        return {}
    history_cols = _table_columns("performance_scoring_history")
    action_at_expr = "h.action_at" if "action_at" in history_cols else "NULL"
    rows = _rows(
        f"""
        SELECT
            h.*,
            f.id AS flow_id
        FROM performance_scoring_history h
        JOIN performance_process_flows f
          ON f.evaluation_id = h.evaluation_id
        WHERE f.id IN :flow_ids
        ORDER BY COALESCE({action_at_expr}, h.created_at, CURRENT_TIMESTAMP), h.id
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
    if row.get("current_owner_id"):
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
            "owner_user_id": row.get("current_owner_id"),
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
    """BYS360 DEFECT AN: both the SELECT and the UPDATE below referenced the
    same wide set of ungated tracking columns as _flow_base_rows() (see the
    note above _status_clause()) -- gated the same way, for the same
    reason: none of the tracking_*/waiting_*/is_overdue/last_visible_action
    columns exist under any name today, so the UPDATE now only writes the
    columns that are actually present, and current_owner_user_id is read as
    the real current_owner_id.
    """
    if not table_exists("performance_process_flows"):
        return Phase8SyncResult()
    sql_limit = "LIMIT :limit" if limit else ""
    params = {"limit": int(limit)} if limit else {}
    flow_cols = _table_columns("performance_process_flows")

    def _flow_expr(name: str, real_name: str | None = None) -> str:
        candidate = real_name or name
        return candidate if candidate in flow_cols else "NULL"

    rows = _rows(
        f"""
        SELECT id, current_status,
               {_flow_expr("current_stage")} AS current_stage,
               {_flow_expr("current_owner_id")} AS current_owner_id,
               {_flow_expr("current_owner_name")} AS current_owner_name,
               {_flow_expr("waiting_since")} AS waiting_since,
               {_flow_expr("waiting_days")} AS waiting_days,
               is_finalized,
               {_flow_expr("president_status")} AS president_status,
               president_approval_status,
               {_flow_expr("president_required", "president_approval_required")} AS president_required,
               {_flow_expr("last_action_title")} AS last_action_title,
               last_action_at
        FROM performance_process_flows
        ORDER BY id DESC
        {sql_limit}
        """,
        params,
    )
    optional_set_columns = {
        "tracking_status",
        "tracking_bucket",
        "tracking_priority",
        "tracking_label",
        "tracking_url",
        "is_overdue",
        "overdue_days",
        "last_visible_action",
        "tracking_updated_at",
        "process_version",
    }
    available_set_columns = optional_set_columns & flow_cols
    updated = 0
    for row in rows:
        flow_id = int(row["id"])
        bucket = _row_bucket(row)
        waiting_days = int(row.get("waiting_days") or 0)
        is_overdue = bool(row.get("is_overdue") or waiting_days >= 7)
        priority = 80 if bucket == "president_pending" or is_overdue else "normal"
        last_visible_action_sources = ", ".join(
            column for column in ("last_action_title", "last_visible_action", "current_stage") if column in flow_cols
        )
        set_expressions = {
            "tracking_status": "COALESCE(current_status, tracking_status, 'takipte')",
            "tracking_bucket": ":bucket",
            "tracking_priority": ":priority",
            "tracking_label": "COALESCE(current_stage, tracking_label, 'Süreç takipte')" if "current_stage" in flow_cols else "COALESCE(tracking_label, 'Süreç takipte')",
            "tracking_url": "COALESCE(tracking_url, '/performans/surec-takibi')",
            "is_overdue": ":is_overdue",
            "overdue_days": (
                "CASE WHEN :is_overdue THEN COALESCE(waiting_days, 0) ELSE COALESCE(overdue_days, 0) END"
                if "waiting_days" in flow_cols
                else "CASE WHEN :is_overdue THEN :waiting_days ELSE COALESCE(overdue_days, 0) END"
            ),
            "last_visible_action": f"COALESCE({last_visible_action_sources})" if last_visible_action_sources else "last_visible_action",
            "tracking_updated_at": "CURRENT_TIMESTAMP",
            "process_version": ":version",
        }
        assignments = ", ".join(f"{column} = {set_expressions[column]}" for column in available_set_columns)
        if not assignments:
            updated += 1
            continue
        db.session.execute(
            text(f"UPDATE performance_process_flows SET {assignments} WHERE id = :flow_id"),
            {
                "bucket": bucket,
                "priority": _normalize_tracking_priority(priority),
                "is_overdue": is_overdue,
                "waiting_days": waiting_days,
                "version": PHASE8_VERSION,
                "flow_id": flow_id,
            },
        )
        updated += 1
    db.session.commit()
    return Phase8SyncResult(flows_checked=len(rows), flows_updated=updated)
