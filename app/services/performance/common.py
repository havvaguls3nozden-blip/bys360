from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, overload

from app.extensions import db
from app.models import PerformancePeriod, PerformanceWeightConfig, User

from .rules import (
    DEFAULT_THREE_MANAGER_SCORING_WEIGHTS,
    DEFAULT_TWO_MANAGER_WEIGHTS,
    LEVEL_3_DEFAULT_MODE,
)

logger = logging.getLogger(__name__)

# --- BYS360 third-manager Excel import compatibility patch ---
THIRD_MANAGER_STANDARD_KEY = "ucuncu_yonetici_sicil"
THIRD_MANAGER_HEADER_ALIASES = [
    "ucuncu_yonetici_sicil",
    "üçüncü yönetici sicil",
    "ucuncu yonetici sicil",
    "3. amir sicil",
    "3 amir sicil",
    "new_y3",
]

TR_CHAR_MAP = str.maketrans({
    "ç": "c", "Ç": "c",
    "ğ": "g", "Ğ": "g",
    "ı": "i", "I": "i", "İ": "i",
    "ö": "o", "Ö": "o",
    "ş": "s", "Ş": "s",
    "ü": "u", "Ü": "u",
})

PRESIDENT_ROLE_KEYS = {"baskan"}
PRESIDENT_TITLE_KEYS = {"baskan"}
HUKUK_UNIT_KEYS = ("hukuk musavirligi", "sorumlu hukuk musavirligi")
HUKUK_TITLE_KEYS = ("hukuk musavir", "sorumlu hukuk musavir")


@dataclass
class ManagerChain:
    employee_id: int
    employee_name: str
    employee_sicil: str
    manager_1_id: int | None = None
    manager_2_id: int | None = None
    manager_3_id: int | None = None
    manager_1_name: str = "-"
    manager_2_name: str = "-"
    manager_3_name: str = "-"
    info_notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    is_single_manager_case: bool = False
    level_3_enabled: bool = False
    level_3_scoring_enabled: bool = False
    effective_weights: dict[str, float] = field(default_factory=dict)


def _safe_str(value: Any) -> str:
    return str(value).strip() if value is not None else ""


@overload
def _safe_float(value: Any, default: float = 0.0) -> float: ...
@overload
def _safe_float(value: Any, default: None) -> float | None: ...
def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    try:
        if value in (None, ""):
            return default
        if isinstance(value, str):
            value = value.strip().replace(",", ".")
            if not value:
                return default
        return float(value)
    except (TypeError, ValueError):
        return default


@overload
def _safe_int(value: Any, default: int = 0) -> int: ...
@overload
def _safe_int(value: Any, default: None) -> int | None: ...
def _safe_int(value: Any, default: int | None = 0) -> int | None:
    try:
        if value in (None, "") or isinstance(value, bool):
            return default
        if isinstance(value, str):
            value = value.strip().replace(",", ".")
            if not value:
                return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _normalize_text(value: Any) -> str:
    text = (value or "").strip()
    text = text.translate(TR_CHAR_MAP)
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _full_name(user: Any) -> str:
    if not user:
        return "-"
    full_name = _safe_str(getattr(user, "full_name", ""))
    if full_name:
        return full_name
    ad = _safe_str(getattr(user, "ad", ""))
    soyad = _safe_str(getattr(user, "soyad", ""))
    return f"{ad} {soyad}".strip() or "-"


def is_performance_scope_user(user: User | None) -> bool:
    if not user:
        return False
    try:
        from app.services.hierarchy_rulebook_service import is_system_user
        if is_system_user(user):
            return False
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        role_key = _normalize_text(getattr(user, "role", ""))
        role_label_key = _normalize_text(getattr(user, "role_label", ""))
        if role_key == "admin" or role_label_key in {"admin", "sistem yoneticisi", "system admin", "system administrator", "super admin", "superadmin"}:
            return False
    return bool(getattr(user, "is_active", True))


def is_president(user: User | None) -> bool:
    if not user:
        return False
    role_key = _normalize_text(getattr(user, "role", ""))
    title_key = _normalize_text(getattr(user, "unvan", ""))
    role_label_key = _normalize_text(getattr(user, "role_label", ""))
    return role_key in PRESIDENT_ROLE_KEYS or title_key in PRESIDENT_TITLE_KEYS or role_label_key in PRESIDENT_TITLE_KEYS


def is_hukuk_context(user: User | None) -> bool:
    if not user:
        return False
    birim_key = _normalize_text(getattr(user, "birim", ""))
    ust_birim_key = _normalize_text(getattr(user, "ust_birim", ""))
    title_key = _normalize_text(getattr(user, "unvan", ""))
    return any(token in title_key for token in HUKUK_TITLE_KEYS) or any(token in birim_key for token in HUKUK_UNIT_KEYS) or any(token in ust_birim_key for token in HUKUK_UNIT_KEYS)


def is_hukuk_single_manager_case(user: User | None) -> bool:
    if not user or not is_hukuk_context(user):
        return False

    # Kurumsal özel kural:
    # Hukuk Müşavirliği içinde bir hukuk müşaviri başka bir hukuk müşavirine
    # açık biçimde bağlıysa bu kayıt tek amirli çalışır. Amir yalnızca bağlı
    # olduğu hukuk müşaviridir; 2. amir zinciri açılmaz.
    role_key = _normalize_text(getattr(user, "role", ""))
    title_key = _normalize_text(getattr(user, "unvan", ""))
    is_hukuk_title = any(token in title_key for token in HUKUK_TITLE_KEYS)
    is_hukuk_like = role_key in {"mali_musavir", "grup_baskani", "personel"} or is_hukuk_title
    if not is_hukuk_like:
        return False

    for field_name in ("yonetici_sicil", "ikinci_yonetici_sicil", "ucuncu_yonetici_sicil"):
        manager_sicil = _safe_str(getattr(user, field_name, ""))
        if not manager_sicil:
            continue
        manager = User.query.filter_by(sicil_no=manager_sicil, is_active=True).first()
        if not manager or getattr(manager, "id", None) == getattr(user, "id", None):
            continue
        if is_hukuk_context(manager):
            return True
    return False


def is_single_manager_case(user: User | None) -> bool:
    if not user or is_president(user):
        return False
    if is_hukuk_single_manager_case(user):
        return True
    if is_hukuk_context(user):
        return False
    manager_1_sicil = _safe_str(getattr(user, "yonetici_sicil", ""))
    manager_2_sicil = _safe_str(getattr(user, "ikinci_yonetici_sicil", ""))
    manager_3_sicil = _safe_str(getattr(user, "ucuncu_yonetici_sicil", ""))
    if not manager_1_sicil or manager_2_sicil or manager_3_sicil:
        return False
    manager_1 = User.query.filter_by(sicil_no=manager_1_sicil, is_active=True).first()
    return bool(manager_1 and is_president(manager_1))


def get_period(period_id: int | None = None) -> PerformancePeriod | None:
    try:
        if period_id:
            return db.session.get(PerformancePeriod, int(period_id))
    except (TypeError, ValueError):
        return None
    return (
        PerformancePeriod.query.filter_by(is_active=True)
        .order_by(PerformancePeriod.id.desc())
        .first()
    )


def get_active_period() -> PerformancePeriod | None:
    return (
        PerformancePeriod.query.filter_by(is_active=True)
        .order_by(PerformancePeriod.start_date.desc(), PerformancePeriod.id.desc())
        .first()
    )


def get_active_weight_config(period_id: int | None = None) -> PerformanceWeightConfig | None:
    query = PerformanceWeightConfig.query.filter_by(is_active=True)
    if period_id is not None:
        # BYS360 DEFECT X: a period-scoped lookup must never fall back to
        # another period's config. Returning None here is the correct signal
        # for callers (e.g. get_base_weight_map) to apply their own existing
        # period-level/global default weighting.
        return query.filter_by(period_id=period_id).order_by(PerformanceWeightConfig.id.desc()).first()
    return query.order_by(PerformanceWeightConfig.id.desc()).first()


def get_base_weight_map(period_id: int | None = None) -> dict[str, float]:
    period = get_period(period_id)
    config = get_active_weight_config((period.id if period else None) or period_id)
    if config:
        return {
            "evaluator_1_weight": _safe_float(getattr(config, "evaluator_1_weight", 50), 50.0),
            "evaluator_2_weight": _safe_float(getattr(config, "evaluator_2_weight", 50), 50.0),
            "evaluator_3_weight": _safe_float(getattr(config, "evaluator_3_weight", 0), 0.0),
        }
    if period:
        return {
            "evaluator_1_weight": _safe_float(getattr(period, "level_1_weight", 50), 50.0),
            "evaluator_2_weight": _safe_float(getattr(period, "level_2_weight", 50), 50.0),
            "evaluator_3_weight": _safe_float(getattr(period, "level_3_weight", 0), 0.0),
        }
    return {"evaluator_1_weight": 50.0, "evaluator_2_weight": 50.0, "evaluator_3_weight": 0.0}


def fetch_active_non_admin_users(include_president: bool = True) -> list[User]:
    users = (
        User.query.filter(User.is_active.is_(True))
        .order_by(User.ust_birim.asc(), User.birim.asc(), User.ad.asc(), User.soyad.asc())
        .all()
    )
    users = [u for u in users if is_performance_scope_user(u)]
    if include_president:
        return users
    return [u for u in users if not is_president(u)]


def fetch_active_users() -> list[User]:
    return fetch_active_non_admin_users(include_president=False)


def _resolve_manager(sicil_no: str, users_by_sicil: dict[str, User]) -> User | None:
    if not sicil_no:
        return None
    sicil_no = _safe_str(sicil_no)
    return users_by_sicil.get(sicil_no) or User.query.filter_by(sicil_no=sicil_no, is_active=True).first()


__all__ = [
    "ManagerChain",
    "_full_name",
    "_normalize_text",
    "_resolve_manager",
    "_safe_float",
    "_safe_int",
    "_safe_str",
    "calculate_effective_weights",
    "fetch_active_non_admin_users",
    "fetch_active_users",
    "get_active_period",
    "get_active_weight_config",
    "get_base_weight_map",
    "get_period",
    "get_period_level_3_flags",
    "is_hukuk_context",
    "is_hukuk_single_manager_case",
    "is_president",
    "is_single_manager_case",
    "is_performance_scope_user",
    "normalize_weight_inputs",
]


def get_president_user(users_by_sicil=None):

    if users_by_sicil:
        try:
            for user in users_by_sicil.values():
                role = str(getattr(user, "role", "") or "").strip().lower()
                unvan = str(getattr(user, "unvan", "") or "").strip().lower()
                full_name = str(getattr(user, "full_name", "") or "").strip().lower()
                if role in {"baskan", "başkan", "president"}:
                    return user
                if "başkan" in unvan or "baskan" in unvan:
                    return user
                if "başkan" in full_name or "baskan" in full_name:
                    return user
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/common.py")
    """
    Geriye dönük uyumluluk hotfix'i.
    Bazı modüller app.services.performance.common içinden bu fonksiyonu bekliyor.
    Uygun kullanıcıyı rol/unvan/email/birim ipuçlarıyla bulmaya çalışır.
    """
    try:
        from app.models import User
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        try:
            from app.models.user import User  # type: ignore[no-redef]
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            return None

    def _first(query):
        try:
            return query.first()
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            return None

    # 1) Rol adı
    try:
        user = _first(User.query.filter(User.role.in_(["president", "baskan", "başkan"])))
        if user:
            return user
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        import logging
        logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/common.py")
    for attr in ("title", "unvan", "position", "job_title"):
        try:
            column = getattr(User, attr)
            user = _first(User.query.filter(column.ilike("%başkan%")))
            if user:
                return user
            user = _first(User.query.filter(column.ilike("%baskan%")))
            if user:
                return user
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/common.py")
    for rel_name in ("organization_unit", "unit", "department"):
        try:
            rel = getattr(User, rel_name)
            # ilişki üzerinden güvenli sorgu kurmak zor olabileceği için fallback bırakıyoruz
            if hasattr(rel, "has"):
                user = _first(User.query.filter(rel.has(name="Başkanlık Makamı")))
                if user:
                    return user
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/common.py")
    for attr in ("is_top_manager", "is_president", "is_baskan"):
        try:
            column = getattr(User, attr)
            user = _first(User.query.filter(column == True))  # noqa: E712
            if user:
                return user
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/common.py")
    try:
        user = _first(User.query.filter(User.email.ilike("%baskan%")))
        if user:
            return user
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        import logging
        logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/common.py")
    return None

def get_evaluation_window_start(period: PerformancePeriod | None) -> date | None:
    if not period:
        return None
    return getattr(period, "evaluation_start_date", None) or getattr(period, "start_date", None)

def get_evaluation_window_end(period: PerformancePeriod | None) -> date | None:
    if not period:
        return None
    return getattr(period, "evaluation_end_date", None) or getattr(period, "end_date", None)

def get_evaluation_due_days(period: PerformancePeriod | None) -> int | None:
    if not period:
        return None
    raw = getattr(period, "evaluation_due_days", None)
    try:
        value = int(raw)  # type: ignore[arg-type]  # defensive parse; falls through to except below
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None

def get_evaluation_window_state(period: PerformancePeriod | None, check_date: date | None = None) -> dict[str, Any]:
    target = check_date or date.today()
    start = get_evaluation_window_start(period)
    end = get_evaluation_window_end(period)
    due_days = get_evaluation_due_days(period)
    not_started = bool(start and target < start)
    expired = bool(end and target > end)
    is_open = not not_started and not expired
    return {
        "start": start,
        "end": end,
        "due_days": due_days,
        "check_date": target,
        "not_started": not_started,
        "expired": expired,
        "is_open": is_open,
        "can_submit": is_open,
    }

def build_assignment_due_date(period: PerformancePeriod | None, assigned_at: datetime | None = None):
    if not period:
        return None
    builder = getattr(period, "build_due_datetime", None)
    if callable(builder):
        return builder(assigned_at=assigned_at)
    end = get_evaluation_window_end(period)
    if end is None:
        return None
    return datetime.combine(end, datetime.max.time().replace(microsecond=0))

# BYS360_PHASE4_5_COMMON_WEIGHT_OVERRIDE
def get_period_level_3_flags(period=None, weight_config=None) -> dict[str, Any]:
    period = period or get_active_period()
    weight_config = weight_config or get_active_weight_config(getattr(period, "id", None) if period else None)

    enabled = False
    scoring_enabled = False
    mode = "off"

    if weight_config:
        enabled = bool(getattr(weight_config, "level_3_enabled", False))
        mode = _safe_str(getattr(weight_config, "level_3_mode", "")) or ("scoring" if _safe_float(getattr(weight_config, "evaluator_3_weight", 0), 0) > 0 else LEVEL_3_DEFAULT_MODE)
        scoring_enabled = mode == "scoring" or _safe_float(getattr(weight_config, "evaluator_3_weight", 0), 0) > 0

    if period:
        enabled = bool(enabled or getattr(period, "enable_level_3", False) or getattr(period, "enable_level_3_scoring", False))
        scoring_enabled = bool(scoring_enabled or getattr(period, "enable_level_3_scoring", False))
        if not enabled and getattr(period, "enable_level_3_scoring", False):
            enabled = True

    try:
        from app.services.performance.third_supervisor_policy import (
            third_supervisor_policy_snapshot,
        )
        snapshot = third_supervisor_policy_snapshot(period)
        # Merkezi ayarlar kurumsal nihai davranışı belirler. Dönem/weight config değerleri yalnızca
        # yardımcı veri olarak kalır; ağırlığa dahil olma için scoring_enabled ayarı şarttır.
        if snapshot:
            enabled = bool(snapshot.get("enabled"))
            scoring_enabled = bool(snapshot.get("scoring_enabled"))
            mode = "scoring" if scoring_enabled else ("comment_only" if enabled else "off")
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        if not enabled:
            mode = "off"
            scoring_enabled = False
        elif scoring_enabled:
            mode = "scoring"
        else:
            mode = LEVEL_3_DEFAULT_MODE

    if not enabled:
        mode = "off"
        scoring_enabled = False
    elif scoring_enabled:
        mode = "scoring"
    else:
        mode = LEVEL_3_DEFAULT_MODE

    return {"enabled": enabled, "scoring_enabled": scoring_enabled, "mode": mode}


def normalize_weight_inputs(
    evaluator_1_weight: float,
    evaluator_2_weight: float,
    evaluator_3_weight: float,
    level_3_enabled: bool,
    level_3_scoring_enabled: bool,
) -> dict[str, Any]:
    mode = "scoring" if bool(level_3_enabled and level_3_scoring_enabled) else (LEVEL_3_DEFAULT_MODE if level_3_enabled else "off")
    try:
        from app.services.performance.third_supervisor_policy import (
            normalize_third_supervisor_weights,
        )
        normalized = normalize_third_supervisor_weights(
            {
                "evaluator_1_weight": evaluator_1_weight,
                "evaluator_2_weight": evaluator_2_weight,
                "evaluator_3_weight": evaluator_3_weight,
            },
            enabled_levels={1, 2, 3 if level_3_enabled else 0},
            include_third=bool(level_3_enabled and level_3_scoring_enabled),
        )
        return {
            "evaluator_1_weight": normalized[1],
            "evaluator_2_weight": normalized[2],
            "evaluator_3_weight": normalized[3],
            "level_3_enabled": bool(level_3_enabled),
            "level_3_scoring_enabled": bool(level_3_enabled and level_3_scoring_enabled),
            "level_3_mode": mode,
        }
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        w1 = max(0.0, _safe_float(evaluator_1_weight, 0.0))
        w2 = max(0.0, _safe_float(evaluator_2_weight, 0.0))
        w3 = max(0.0, _safe_float(evaluator_3_weight, 0.0)) if mode == "scoring" else 0.0
        total = w1 + w2 + w3
        if total <= 0:
            w1, w2, w3 = DEFAULT_THREE_MANAGER_SCORING_WEIGHTS if mode == "scoring" else DEFAULT_TWO_MANAGER_WEIGHTS
            total = 100.0
        result: dict[str, Any] = {
            "evaluator_1_weight": round((w1 / total) * 100.0, 2),
            "evaluator_2_weight": round((w2 / total) * 100.0, 2),
            "evaluator_3_weight": round((w3 / total) * 100.0, 2),
            "level_3_enabled": bool(level_3_enabled),
            "level_3_scoring_enabled": bool(level_3_enabled and level_3_scoring_enabled),
            "level_3_mode": mode,
        }
        drift = round(100.0 - (result["evaluator_1_weight"] + result["evaluator_2_weight"] + result["evaluator_3_weight"]), 2)
        if drift:
            result["evaluator_1_weight"] = round(result["evaluator_1_weight"] + drift, 2)
        return result


def calculate_effective_weights(
    period,
    employee,
    manager_1_id,
    manager_2_id,
    manager_3_id,
) -> dict[str, float]:
    base = get_base_weight_map(getattr(period, "id", None) if period else None)
    single_manager = is_single_manager_case(employee)
    try:
        from app.services.performance.third_supervisor_policy import (
            normalize_third_supervisor_effective_weights,
        )
        return normalize_third_supervisor_effective_weights(
            base,
            period=period,
            manager_1_id=manager_1_id,
            manager_2_id=manager_2_id,
            manager_3_id=manager_3_id,
            single_manager=single_manager,
        )
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        active_levels: dict[int, float] = {}
        if manager_1_id:
            active_levels[1] = base["evaluator_1_weight"]
        if not single_manager and manager_2_id:
            active_levels[2] = base["evaluator_2_weight"]
        flags = get_period_level_3_flags(period)
        if manager_3_id and flags["enabled"] and flags["scoring_enabled"]:
            active_levels[3] = base["evaluator_3_weight"] or 20.0
        if single_manager:
            active_levels = {1: 100.0} if manager_1_id else {}
        if not active_levels:
            return {"evaluator_1_weight": 0.0, "evaluator_2_weight": 0.0, "evaluator_3_weight": 0.0}
        total = sum(active_levels.values())
        if total <= 0:
            total = 100.0
            active_levels = {level: 100.0 / len(active_levels) for level in active_levels}
        effective = {
            "evaluator_1_weight": round((active_levels.get(1, 0.0) / total) * 100.0, 2),
            "evaluator_2_weight": round((active_levels.get(2, 0.0) / total) * 100.0, 2),
            "evaluator_3_weight": round((active_levels.get(3, 0.0) / total) * 100.0, 2),
        }
        drift = round(100.0 - sum(effective.values()), 2)
        if drift and any(effective.values()):
            for key in ("evaluator_3_weight", "evaluator_2_weight", "evaluator_1_weight"):
                if effective.get(key, 0.0) > 0:
                    effective[key] = round(effective[key] + drift, 2)
                    break
        return effective

