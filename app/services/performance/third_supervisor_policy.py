from __future__ import annotations

import logging
from typing import Any

"""BYS360 Faz 4.1 - 3. amir merkezi ayar/politika servisi.

Bu servis yalnızca ayarları okur ve normalize eder. Görev üretimi, tablo sütunu,
statü dili ve ağırlık uygulaması Faz 4.2-4.5 adımlarında bu servise bağlanacaktır.
"""

logger = logging.getLogger(__name__)

# BYS360_PHASE4_1_THIRD_SUPERVISOR_SETTINGS
DEFAULTS = {
    "performance.third_supervisor_enabled": True,
    "performance.third_supervisor_mode": "comment_only",
    "performance.third_supervisor_show_column": False,
    "performance.third_supervisor_weight_enabled": False,
}

VALID_COMMENT_MODES = {"comment_only", "yorumcu", "yorum", "comment"}
VALID_SCORE_MODES = {"scoring", "score", "puan", "puanlama"}
VALID_DISABLED_MODES = {"off", "disabled", "kapali", "kapalı", "false", "0"}


def _coerce_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return bool(default)
    text = str(value).strip().lower()
    if text in {"1", "true", "on", "yes", "evet", "aktif", "açık", "acik"}:
        return True
    if text in {"0", "false", "off", "no", "hayır", "hayir", "pasif", "kapalı", "kapali"}:
        return False
    return bool(default)


def _normalize_mode(value: Any, default: str = "comment_only") -> str:
    text = str(value or "").strip().lower()
    if text in VALID_SCORE_MODES:
        return "scoring"
    if text in VALID_DISABLED_MODES:
        return "off"
    if text in VALID_COMMENT_MODES:
        return "comment_only"
    return default


def _read_module_setting(module_key: str, setting_key: str, default: Any) -> Any:
    try:
        try:
            from app.models.settings_models import ModuleSetting
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            from app.models import ModuleSetting
        row = ModuleSetting.query.filter_by(module_key=module_key, setting_key=setting_key).first()
        if row is None or getattr(row, "is_active", True) is False:
            return default
        value = getattr(row, "value_text", None)
        return default if value in (None, "") else value
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def get_third_supervisor_setting(setting_key: str, default: Any | None = None) -> Any:
    full_key = f"performance.{setting_key}"
    if default is None:
        default = DEFAULTS.get(full_key)
    return _read_module_setting("performance", setting_key, default)


def third_supervisor_policy_snapshot(period: Any | None = None) -> dict[str, Any]:
    enabled = _coerce_bool(
        get_third_supervisor_setting("third_supervisor_enabled"),
        DEFAULTS["performance.third_supervisor_enabled"],
    )
    raw_mode = get_third_supervisor_setting(
        "third_supervisor_mode",
        DEFAULTS["performance.third_supervisor_mode"],
    )
    mode = _normalize_mode(raw_mode, "comment_only")
    show_column = _coerce_bool(
        get_third_supervisor_setting("third_supervisor_show_column"),
        DEFAULTS["performance.third_supervisor_show_column"],
    )
    weight_enabled = _coerce_bool(
        get_third_supervisor_setting("third_supervisor_weight_enabled"),
        DEFAULTS["performance.third_supervisor_weight_enabled"],
    )

    if period is not None:
        show_column = bool(show_column or getattr(period, "level_3_column_visible", False))

    if not enabled or mode == "off":
        return {
            "enabled": False,
            "mode": "off",
            "show_column": False,
            "weight_enabled": False,
            "scoring_enabled": False,
        }

    scoring_enabled = bool(mode == "scoring" and weight_enabled)
    return {
        "enabled": True,
        "mode": "scoring" if scoring_enabled else "comment_only",
        "show_column": bool(show_column),
        "weight_enabled": bool(weight_enabled),
        "scoring_enabled": bool(scoring_enabled),
    }


def third_supervisor_enabled(period: Any | None = None) -> bool:
    return bool(third_supervisor_policy_snapshot(period).get("enabled"))


def third_supervisor_mode(period: Any | None = None) -> str:
    return str(third_supervisor_policy_snapshot(period).get("mode") or "off")


def third_supervisor_show_column(period: Any | None = None, *, has_third_supervisor: bool = False) -> bool:
    snapshot = third_supervisor_policy_snapshot(period)
    return bool(snapshot.get("enabled") and (snapshot.get("show_column") or has_third_supervisor))


def third_supervisor_weight_enabled(period: Any | None = None) -> bool:
    snapshot = third_supervisor_policy_snapshot(period)
    return bool(snapshot.get("enabled") and snapshot.get("scoring_enabled") and snapshot.get("weight_enabled"))


__all__ = [
    "DEFAULTS",
    "get_third_supervisor_setting",
    "third_supervisor_enabled",
    "third_supervisor_mode",
    "third_supervisor_policy_snapshot",
    "third_supervisor_show_column",
    "third_supervisor_weight_enabled",
]

# BYS360_PHASE4_2_THIRD_SUPERVISOR_TASK_POLICY
def _phase4_2_payload_evaluator_id(payload: Any) -> Any:
    if payload is None:
        return None
    if isinstance(payload, dict):
        return payload.get("evaluator_id") or payload.get("manager_3_id") or payload.get("level_3_evaluator_id")
    return getattr(payload, "evaluator_id", None) or getattr(payload, "manager_3_id", None) or getattr(payload, "level_3_evaluator_id", None)


def should_create_third_supervisor_task(*, period: Any | None = None, payload: Any | None = None, evaluator_id: Any | None = None) -> bool:
    """3. amir görevinin gerçekten üretilip üretilmeyeceğini belirler."""
    try:
        if not third_supervisor_enabled(period):
            return False
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        import logging
        logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/third_supervisor_policy.py")
    resolved = evaluator_id if evaluator_id is not None else _phase4_2_payload_evaluator_id(payload)
    try:
        return bool(int(resolved or 0) > 0)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return bool(str(resolved or "").strip())


def should_keep_third_supervisor_assignment(*, period: Any | None = None, assignment: Any | None = None) -> bool:
    evaluator_id = getattr(assignment, "evaluator_id", None) if assignment is not None else None
    return should_create_third_supervisor_task(period=period, evaluator_id=evaluator_id)

# BYS360_PHASE4_5_THIRD_SUPERVISOR_WEIGHT_POLICY
def _phase4_5_safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        if isinstance(value, str):
            value = value.strip().replace(",", ".")
            if not value:
                return default
        return float(value)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _phase4_5_has_value(value: Any) -> bool:
    try:
        return int(value or 0) > 0
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return bool(str(value or "").strip())


def resolve_third_supervisor_weight_mode(period: Any | None = None, *, manager_3_id: Any | None = None) -> dict[str, Any]:
    """3. amirin ağırlığa katılıp katılmayacağını tek merkezden döndürür."""
    snapshot = third_supervisor_policy_snapshot(period)
    enabled = bool(snapshot.get("enabled"))
    scoring_enabled = bool(snapshot.get("scoring_enabled") and _phase4_5_has_value(manager_3_id))
    if not enabled:
        mode = "off"
    elif scoring_enabled:
        mode = "scoring"
    else:
        mode = "comment_only"
    return {
        "enabled": enabled,
        "mode": mode,
        "scoring_enabled": scoring_enabled,
        "include_weight": bool(enabled and scoring_enabled),
    }


def normalize_third_supervisor_weights(
    raw_weights: dict[Any, Any] | None,
    *,
    enabled_levels: set[int] | list[int] | tuple[int, ...] | None = None,
    include_third: bool = False,
) -> dict[int, float]:
    """Aktif 1/2/3 amir ağırlıklarını her durumda toplam 100 olacak şekilde normalize eder.

    include_third=False ise 3. amir yorum modundadır ve ağırlığı 0 kalır.
    include_third=True ise 3. amir puan modundadır; 3. amir seviyesi varsa ağırlık hesabına dahil edilir.
    """
    raw_weights = raw_weights or {}
    raw = {
        1: max(0.0, _phase4_5_safe_float(raw_weights.get(1, raw_weights.get("evaluator_1_weight", 0.0)), 0.0)),
        2: max(0.0, _phase4_5_safe_float(raw_weights.get(2, raw_weights.get("evaluator_2_weight", 0.0)), 0.0)),
        3: max(0.0, _phase4_5_safe_float(raw_weights.get(3, raw_weights.get("evaluator_3_weight", 0.0)), 0.0)),
    }
    levels = {int(level) for level in (enabled_levels or {1, 2}) if int(level) in {1, 2, 3}}
    if not levels:
        levels = {1, 2}

    if not include_third:
        levels.discard(3)
        raw[3] = 0.0
    elif 3 in levels and raw[3] <= 0:
        # Puan modunda 3. amir gerçekten varsa ama ağırlık girilmemişse kurumsal varsayılan uygulanır.
        # Böylece 3. amir puan moduna alınmışken fiilen %0'da kalmaz.
        raw[3] = 20.0
        if 1 in levels and raw[1] <= 0:
            raw[1] = 40.0
        if 2 in levels and raw[2] <= 0:
            raw[2] = 40.0

    active = [level for level in (1, 2, 3) if level in levels and (level != 3 or include_third)]
    if not active:
        return {1: 0.0, 2: 0.0, 3: 0.0}

    total = sum(raw.get(level, 0.0) for level in active)
    if total <= 0:
        share = round(100.0 / len(active), 2)
        result = {1: 0.0, 2: 0.0, 3: 0.0}
        for level in active:
            result[level] = share
        drift = round(100.0 - sum(result.values()), 2)
        result[active[-1]] = round(result[active[-1]] + drift, 2)
        return result

    result = {1: 0.0, 2: 0.0, 3: 0.0}
    for level in active:
        result[level] = round((raw.get(level, 0.0) / total) * 100.0, 2)
    drift = round(100.0 - sum(result.values()), 2)
    if drift:
        result[active[-1]] = round(result[active[-1]] + drift, 2)
    if not include_third:
        result[3] = 0.0
    return result


def normalize_third_supervisor_effective_weights(
    raw_weights: dict[Any, Any] | None,
    *,
    period: Any | None = None,
    manager_1_id: Any | None = None,
    manager_2_id: Any | None = None,
    manager_3_id: Any | None = None,
    single_manager: bool = False,
) -> dict[str, float]:
    if single_manager:
        if _phase4_5_has_value(manager_1_id):
            return {"evaluator_1_weight": 100.0, "evaluator_2_weight": 0.0, "evaluator_3_weight": 0.0}
        return {"evaluator_1_weight": 0.0, "evaluator_2_weight": 0.0, "evaluator_3_weight": 0.0}

    active_levels: set[int] = set()
    if _phase4_5_has_value(manager_1_id):
        active_levels.add(1)
    if _phase4_5_has_value(manager_2_id):
        active_levels.add(2)
    if _phase4_5_has_value(manager_3_id):
        active_levels.add(3)

    weight_mode = resolve_third_supervisor_weight_mode(period, manager_3_id=manager_3_id)
    normalized = normalize_third_supervisor_weights(
        raw_weights,
        enabled_levels=active_levels or {1, 2},
        include_third=bool(weight_mode.get("include_weight")),
    )
    return {
        "evaluator_1_weight": float(normalized.get(1, 0.0)),
        "evaluator_2_weight": float(normalized.get(2, 0.0)),
        "evaluator_3_weight": float(normalized.get(3, 0.0)),
    }

# BYS360_PHASE4_6_POLICY_ALIGNMENT
# BYS360_PHASE4_3_THIRD_SUPERVISOR_STATUS_LANGUAGE
# Final gate uyum notu: Yorum/Görüş Bekliyor | Puanlama Bekliyor
def _phase4_6_resolve_third_supervisor_mode(period: Any | None = None) -> str:
    """3. amir modunu final gate ve UI statü dili için güvenli biçimde çözer."""
    try:
        raw_mode = get_third_supervisor_setting(
            "third_supervisor_mode",
            DEFAULTS.get("performance.third_supervisor_mode", "comment_only"),
        )
        try:
            return _normalize_mode(raw_mode, "comment_only")
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            value = str(raw_mode or "comment_only").strip().lower()
            if value in {"scoring", "score", "puan", "puan_modu", "puanlama"}:
                return "scoring"
            return "comment_only"
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        try:
            value = str(third_supervisor_mode(period) or "comment_only").strip().lower()
            if value in {"scoring", "score", "puan", "puan_modu", "puanlama"}:
                return "scoring"
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/third_supervisor_policy.py")
    return "comment_only"


def third_supervisor_pending_status_label(period: Any | None = None) -> str:
    """3. amir bekleme statüsünün kullanıcıya görünen Türkçe etiketi."""
    if _phase4_6_resolve_third_supervisor_mode(period) == "scoring":
        return "Puanlama Bekliyor"
    return "Yorum/Görüş Bekliyor"


def third_supervisor_assignment_waiting_label(period: Any | None = None) -> str:
    """Final gate ile uyumlu bekleme etiketi alias'ı."""
    return third_supervisor_pending_status_label(period)


def humanize_third_supervisor_assignment_status(
    assignment: Any | None = None,
    period: Any | None = None,
    status: Any | None = None,
) -> str:
    """3. amir görev statüsünü teknik kod göstermeden kurumsal dile çevirir."""
    raw_status = status if status is not None else getattr(assignment, "status", None)
    normalized = str(raw_status or "").strip().lower()
    if bool(getattr(assignment, "completed_at", None)) or normalized in {"completed", "submitted", "tamamlandi", "tamamlandı"}:
        return "Tamamlandı"
    if normalized in {"partial", "kismen_tamamlandi", "kısmen_tamamlandı"}:
        return "Kısmen Tamamlandı"
    try:
        level = int(getattr(assignment, "manager_level", 0) or 0)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        level = 0
    if level == 3 and normalized in {"", "-", "none", "pending", "bekliyor", "draft"}:
        return third_supervisor_assignment_waiting_label(period)
    if normalized in {"", "-", "none", "pending", "bekliyor", "draft"}:
        return "Bekliyor"
    return str(raw_status or "-")

