from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

"""BYS360 Performans Tamamlama Faz 4 - 3. Amir Opsiyonelliği ve Akış Temizliği.

Bu servis Faz 4 için tek karar merkezidir. Amaç, 3. amir olmayan yapılarda
boş kolon/görev/statü üretimini engellemek; 3. amir varsa yorum modu ile puan
modunu net ayırmak ve ağırlıkları her durumda %100'e tamamlamaktır.

Servis uygulama bağlamı olmadan da import edilebilir. Flask/DB bağlamı varsa
module_settings tablosundaki ayarları güvenli şekilde okur/seed eder.
"""

logger = logging.getLogger(__name__)

BYS360_PERFORMANCE_COMPLETION_PHASE4_THIRD_MANAGER_CENTER = True
BYS360_PERFORMANCE_COMPLETION_PHASE4_NO_FAKE_THIRD_TASK = True
BYS360_PERFORMANCE_COMPLETION_PHASE4_COMMENT_SCORE_MODE_SPLIT = True
BYS360_PERFORMANCE_COMPLETION_PHASE4_WEIGHT_TOTAL_100 = True
BYS360_PERFORMANCE_COMPLETION_PHASE4_VERSION = "performance-completion-phase4-third-manager-center-v1"
BYS360_PERFORMANCE_COMPLETION_PHASE4_HUMANIZED_COMMENT_HOTFIX_V1A = True

MODE_COMMENT = "comment_only"
MODE_SCORE = "scoring"
MODE_OFF = "off"

MODE_ALIASES_COMMENT = {"comment", "comment_only", "yorum", "yorumcu", "gorus", "görüş", "goruş", "gorüş"}
MODE_ALIASES_SCORE = {"score", "scoring", "puan", "puanlama", "puan_modu", "score_mode"}
MODE_ALIASES_OFF = {"off", "disabled", "kapali", "kapalı", "false", "0", "none", "yok", "pasif"}

EMPTY_VALUES = {None, "", "-", "—", "None", "none", "NULL", "null", 0, "0"}

STATUS_LABELS = {
    "third_manager_not_defined": "3. Amir Tanımlı Değil",
    "third_manager_disabled": "3. Amir Devre Dışı",
    "third_manager_comment_pending": "3. Amir Görüş/Yorum Bekliyor",
    "third_manager_comment_done": "3. Amir Görüş/Yorum Tamamlandı",
    "third_manager_score_pending": "3. Amir Puanlama Bekliyor",
    "third_manager_score_done": "3. Amir Puanlama Tamamlandı",
}

PHASE4_SETTING_ROWS: tuple[tuple[str, str, str, str, str, str], ...] = (
    (
        "performance",
        "third_supervisor_enabled",
        "3. amir altyapısı aktif",
        "bool",
        "true",
        "3. amir yalnızca gerçekten tanımlı personelde görev/kolon/statü üretir.",
    ),
    (
        "performance",
        "third_supervisor_mode",
        "3. amir çalışma modu",
        "string",
        "comment_only",
        "comment_only ise 3. amir yalnızca görüş/yazı girer; scoring ise puana katkı verebilir.",
    ),
    (
        "performance",
        "third_supervisor_show_column",
        "3. amir sütunu formda gösterilebilir",
        "bool",
        "false",
        "Liste/raporda veri yoksa boş sütun gösterilmez; formda yetkili kullanıcı için alan açılabilir.",
    ),
    (
        "performance",
        "third_supervisor_weight_enabled",
        "3. amir puan ağırlığı aktif",
        "bool",
        "false",
        "Sadece scoring modunda ve gerçek 3. amir varsa ağırlık hesabına dahil edilir.",
    ),
    (
        "performance_phase4",
        "no_fake_third_manager_task",
        "Sahte 3. amir görevi engellensin",
        "bool",
        "true",
        "3. amir olmayan kayıtlarda görev ve bekleme statüsü oluşturulmaz.",
    ),
    (
        "performance_phase4",
        "comment_mode_status_language",
        "Yorum modunda görev dili görüş/yazı bekliyor olsun",
        "bool",
        "true",
        "Yorum modunda kullanıcıya puan bekliyor ifadesi gösterilmez.",
    ),
    (
        "performance_phase4",
        "weight_total_must_be_100",
        "Amir ağırlığı toplamı her zaman 100 olsun",
        "bool",
        "true",
        "Yorum modunda 3. amir %0 kabul edilir; puan modunda ağırlıklar normalize edilir.",
    ),
)

@dataclass(frozen=True)
class Phase4ThirdManagerDecision:
    enabled: bool
    has_third_manager: bool
    mode: str
    show_column: bool
    create_task: bool
    score_required: bool
    comment_required: bool
    include_weight: bool
    score_weight: float
    status_key: str
    status_label: str


def _safe_text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _has_value(value: Any) -> bool:
    if value in EMPTY_VALUES:
        return False
    if isinstance(value, str) and value.strip() in EMPTY_VALUES:
        return False
    try:
        if isinstance(value, (int, float)) and int(value) <= 0:
            return False
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        logging.getLogger(__name__).exception("BYS360 suppressed exception captured in app/services/performance/completion_phase4_third_manager_center.py:130")
    return bool(_safe_text(value))


def _bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    text = _safe_text(value).casefold()
    if text in {"1", "true", "on", "yes", "evet", "aktif", "enabled", "açık", "acik"}:
        return True
    if text in {"0", "false", "off", "no", "hayır", "hayir", "pasif", "disabled", "kapalı", "kapali"}:
        return False
    return bool(default)


def _float(value: Any, default: float = 0.0) -> float:
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


def normalize_third_manager_mode(value: Any, default: str = MODE_COMMENT) -> str:
    text = _safe_text(value).casefold().replace(" ", "_")
    if text in MODE_ALIASES_SCORE:
        return MODE_SCORE
    if text in MODE_ALIASES_OFF:
        return MODE_OFF
    if text in MODE_ALIASES_COMMENT:
        return MODE_COMMENT
    return default


def _read_module_setting(module_key: str, setting_key: str, default: Any) -> Any:
    try:
        try:
            from app.models import ModuleSetting
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            from app.models.settings_models import ModuleSetting
        row = ModuleSetting.query.filter_by(module_key=module_key, setting_key=setting_key).first()
        if row is None or getattr(row, "is_active", True) is False:
            return default
        value = getattr(row, "value_text", None)
        return default if value in (None, "") else value
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _setting(settings: Mapping[str, Any] | None, key: str, default: Any) -> Any:
    settings = settings or {}
    if key in settings:
        return settings[key]
    if f"performance.{key}" in settings:
        return settings[f"performance.{key}"]
    if f"performance.phase4.{key}" in settings:
        return settings[f"performance.phase4.{key}"]
    return _read_module_setting("performance", key, default)


def phase4_policy_snapshot(period: Any | None = None, settings: Mapping[str, Any] | None = None) -> dict[str, Any]:
    enabled = _bool(_setting(settings, "third_supervisor_enabled", "true"), True)
    raw_mode = _setting(settings, "third_supervisor_mode", MODE_COMMENT)
    mode = normalize_third_manager_mode(raw_mode, MODE_COMMENT)
    show_column_setting = _bool(_setting(settings, "third_supervisor_show_column", "false"), False)
    weight_enabled = _bool(_setting(settings, "third_supervisor_weight_enabled", "false"), False)

    if period is not None:
        show_column_setting = bool(show_column_setting or getattr(period, "level_3_column_visible", False))
        period_mode = getattr(period, "third_supervisor_mode", None) or getattr(period, "third_manager_mode", None)
        if period_mode:
            mode = normalize_third_manager_mode(period_mode, mode)

    if not enabled or mode == MODE_OFF:
        return {
            "enabled": False,
            "mode": MODE_OFF,
            "show_column": False,
            "weight_enabled": False,
            "scoring_enabled": False,
        }

    scoring_enabled = bool(mode == MODE_SCORE and weight_enabled)
    return {
        "enabled": True,
        "mode": MODE_SCORE if scoring_enabled else MODE_COMMENT,
        "show_column": bool(show_column_setting),
        "weight_enabled": bool(weight_enabled),
        "scoring_enabled": bool(scoring_enabled),
    }


def _extract_value(obj: Any, *keys: str) -> Any:
    if obj is None:
        return None
    if isinstance(obj, Mapping):
        for key in keys:
            if key in obj:
                return obj.get(key)
        return None
    for key in keys:
        if hasattr(obj, key):
            return getattr(obj, key)
    return None


def extract_third_manager_id(row: Any) -> Any:
    return _extract_value(
        row,
        "third_manager_id", "third_supervisor_id", "manager_3_id", "level_3_evaluator_id",
        "level_3_manager_id", "level_3_id", "evaluator_3_id",
        "evaluator_id", "manager_id", "third_evaluator_id", "third_supervisor_evaluator_id",
    )


def extract_third_manager_name(row: Any) -> Any:
    return _extract_value(row, "third_manager_name", "third_supervisor_name", "manager_3_name", "level_3_name")


def resolve_phase4_third_manager_decision(
    *,
    third_manager_id: Any = None,
    third_manager_name: Any = None,
    row: Any | None = None,
    period: Any | None = None,
    settings: Mapping[str, Any] | None = None,
    completed: bool = False,
) -> Phase4ThirdManagerDecision:
    if row is not None:
        third_manager_id = third_manager_id if third_manager_id is not None else extract_third_manager_id(row)
        third_manager_name = third_manager_name if third_manager_name is not None else extract_third_manager_name(row)

    snapshot = phase4_policy_snapshot(period=period, settings=settings)
    enabled = bool(snapshot.get("enabled"))
    mode = normalize_third_manager_mode(snapshot.get("mode"), MODE_COMMENT)
    has_third = bool(_has_value(third_manager_id) or _has_value(third_manager_name))

    if not enabled or mode == MODE_OFF:
        return Phase4ThirdManagerDecision(False, has_third, MODE_OFF, False, False, False, False, False, 0.0, "third_manager_disabled", STATUS_LABELS["third_manager_disabled"])

    if not has_third:
        return Phase4ThirdManagerDecision(True, False, mode, False, False, False, False, False, 0.0, "third_manager_not_defined", STATUS_LABELS["third_manager_not_defined"])

    if bool(snapshot.get("scoring_enabled")):
        key = "third_manager_score_done" if completed else "third_manager_score_pending"
        weight = _float(_setting(settings, "third_supervisor_weight", 20), 20.0)
        return Phase4ThirdManagerDecision(True, True, MODE_SCORE, True, True, True, False, True, max(weight, 0.0), key, STATUS_LABELS[key])

    key = "third_manager_comment_done" if completed else "third_manager_comment_pending"
    return Phase4ThirdManagerDecision(True, True, MODE_COMMENT, True, True, False, True, False, 0.0, key, STATUS_LABELS[key])


def phase4_should_create_third_manager_task(
    *,
    period: Any | None = None,
    manager_level: Any = 3,
    evaluator_id: Any | None = None,
    row: Any | None = None,
    settings: Mapping[str, Any] | None = None,
) -> bool:
    try:
        level = int(manager_level or 0)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        level = 0
    if level != 3:
        return True
    decision = resolve_phase4_third_manager_decision(
        third_manager_id=evaluator_id,
        row=row,
        period=period,
        settings=settings,
    )
    return bool(decision.create_task)


def phase4_status_label_for_third_manager(*, period: Any | None = None, completed: bool = False, settings: Mapping[str, Any] | None = None, row: Any | None = None) -> str:
    return resolve_phase4_third_manager_decision(row=row, period=period, settings=settings, completed=completed).status_label


def phase4_humanize_assignment_status(assignment: Any | None = None, period: Any | None = None, status: Any | None = None) -> str:
    raw_status = status if status is not None else _extract_value(assignment, "status")
    normalized = _safe_text(raw_status).casefold()
    completed = bool(_extract_value(assignment, "completed_at")) or normalized in {"completed", "submitted", "tamamlandi", "tamamlandı", "done"}
    try:
        level = int(_extract_value(assignment, "manager_level", "level") or 0)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        level = 0
    if completed:
        return "Tamamlandı"
    if normalized in {"partial", "kismen_tamamlandi", "kısmen_tamamlandı"}:
        return "Kısmen Tamamlandı"
    if level == 3 and normalized in {"", "-", "none", "pending", "bekliyor", "draft", "taslak"}:
        return phase4_status_label_for_third_manager(period=period, completed=False, row=assignment)
    if normalized in {"", "-", "none", "pending", "bekliyor", "draft", "taslak"}:
        return "Bekliyor"
    return str(raw_status or "-")


def phase4_filter_third_manager_tasks(tasks: Iterable[Any] | None, *, period: Any | None = None, settings: Mapping[str, Any] | None = None) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    for task in tasks or []:
        row = dict(task) if isinstance(task, Mapping) else dict(getattr(task, "__dict__", {}) or {})
        try:
            level = int(row.get("manager_level") or row.get("level") or row.get("amir_seviyesi") or 0)
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            level = 0
        if level == 3:
            evaluator_id = row.get("evaluator_id") or row.get("manager_id") or row.get("third_manager_id") or row.get("manager_3_id")
            decision = resolve_phase4_third_manager_decision(
                third_manager_id=evaluator_id,
                third_manager_name=row.get("manager_name") or row.get("third_manager_name") or row.get("manager_3_name"),
                period=period,
                settings=settings,
                completed=bool(row.get("completed_at")) or str(row.get("status") or "").casefold() in {"completed", "submitted", "tamamlandi", "tamamlandı"},
            )
            if not decision.create_task:
                continue
            row["score_required"] = decision.score_required
            row["comment_required"] = decision.comment_required
            row["include_weight"] = decision.include_weight
            row["task_label"] = decision.status_label
            row["status_label"] = decision.status_label
        cleaned.append(row)
    return cleaned


def phase4_should_show_third_manager_column(
    rows: Iterable[Any] | Any = None,
    *,
    period: Any | None = None,
    selected_value: Any | None = None,
    allow_setting: bool = False,
    settings: Mapping[str, Any] | None = None,
) -> bool:
    if _has_value(selected_value):
        return True
    if rows is None:
        rows_iter: Iterable[Any] = []
    elif isinstance(rows, (str, bytes)):
        rows_iter = []
    elif isinstance(rows, Mapping):
        rows_iter = [rows]
    else:
        try:
            rows_iter = list(rows)
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            rows_iter = [rows]
    for row in rows_iter:
        if resolve_phase4_third_manager_decision(row=row, period=period, settings=settings).show_column:
            return True
    if allow_setting:
        snapshot = phase4_policy_snapshot(period=period, settings=settings)
        return bool(snapshot.get("enabled") and snapshot.get("show_column"))
    return False


def normalize_phase4_manager_weights(
    raw_weights: Mapping[Any, Any] | None = None,
    *,
    period: Any | None = None,
    manager_1_id: Any | None = None,
    manager_2_id: Any | None = None,
    manager_3_id: Any | None = None,
    single_manager: bool = False,
    settings: Mapping[str, Any] | None = None,
) -> dict[str, float]:
    raw_weights = raw_weights or {}
    if single_manager:
        return {"evaluator_1_weight": 100.0 if _has_value(manager_1_id) else 0.0, "evaluator_2_weight": 0.0, "evaluator_3_weight": 0.0}

    active: list[int] = []
    if _has_value(manager_1_id):
        active.append(1)
    if _has_value(manager_2_id):
        active.append(2)

    decision = resolve_phase4_third_manager_decision(third_manager_id=manager_3_id, period=period, settings=settings)
    include_third = bool(decision.include_weight)
    if include_third:
        active.append(3)
    if not active:
        active = [1, 2]

    raw = {
        1: max(_float(raw_weights.get(1, raw_weights.get("evaluator_1_weight", raw_weights.get("manager_1", 60))), 60.0), 0.0),
        2: max(_float(raw_weights.get(2, raw_weights.get("evaluator_2_weight", raw_weights.get("manager_2", 40))), 40.0), 0.0),
        3: max(_float(raw_weights.get(3, raw_weights.get("evaluator_3_weight", raw_weights.get("manager_3", decision.score_weight or 20))), decision.score_weight or 20.0), 0.0) if include_third else 0.0,
    }
    total = sum(raw[level] for level in active)
    if total <= 0:
        share = round(100.0 / len(active), 2)
        result = {1: 0.0, 2: 0.0, 3: 0.0}
        for level in active:
            result[level] = share
    else:
        result = {1: 0.0, 2: 0.0, 3: 0.0}
        for level in active:
            result[level] = round((raw[level] / total) * 100.0, 2)
    drift = round(100.0 - sum(result.values()), 2)
    if active and drift:
        result[active[-1]] = round(result[active[-1]] + drift, 2)
    if not include_third:
        result[3] = 0.0
    return {
        "evaluator_1_weight": float(result.get(1, 0.0)),
        "evaluator_2_weight": float(result.get(2, 0.0)),
        "evaluator_3_weight": float(result.get(3, 0.0)),
    }


def phase4_legacy_policy_snapshot(period: Any | None = None, settings: Mapping[str, Any] | None = None) -> dict[str, Any]:
    snapshot = phase4_policy_snapshot(period=period, settings=settings)
    return {
        "enabled": bool(snapshot.get("enabled")),
        "mode": str(snapshot.get("mode") or MODE_OFF),
        "show_column": bool(snapshot.get("show_column")),
        "weight_enabled": bool(snapshot.get("weight_enabled")),
        "scoring_enabled": bool(snapshot.get("scoring_enabled")),
    }


def phase4_static_contract() -> dict[str, Any]:
    return {
        "version": BYS360_PERFORMANCE_COMPLETION_PHASE4_VERSION,
        "markers": {
            "center": BYS360_PERFORMANCE_COMPLETION_PHASE4_THIRD_MANAGER_CENTER,
            "no_fake_task": BYS360_PERFORMANCE_COMPLETION_PHASE4_NO_FAKE_THIRD_TASK,
            "mode_split": BYS360_PERFORMANCE_COMPLETION_PHASE4_COMMENT_SCORE_MODE_SPLIT,
            "weight_total_100": BYS360_PERFORMANCE_COMPLETION_PHASE4_WEIGHT_TOTAL_100,
        },
        "settings": [
            {"module_key": m, "setting_key": k, "label": label, "value_type": vt, "default_value": default, "description": desc}
            for m, k, label, vt, default, desc in PHASE4_SETTING_ROWS
        ],
        "status_labels": dict(STATUS_LABELS),
        "rules": [
            "3. amir zorunlu değildir.",
            "3. amir yoksa kolon, görev ve bekleme statüsü üretilmez.",
            "Yorum modunda 3. amir puan vermez; görev dili görüş/yorum bekliyor olur.",
            "Puan modunda 3. amir ağırlık hesabına dahil olabilir; toplam her zaman %100 olur.",
        ],
    }


def seed_phase4_third_manager_center(commit: bool = True) -> dict[str, Any]:
    changed: list[str] = []
    try:
        from app.extensions import db
        try:
            from app.models import ModuleSetting
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            from app.models.settings_models import ModuleSetting

        for module_key, setting_key, label, value_type, default_value, description in PHASE4_SETTING_ROWS:
            row = ModuleSetting.query.filter_by(module_key=module_key, setting_key=setting_key).first()
            if row is None:
                row = ModuleSetting(
                    module_key=module_key,
                    setting_key=setting_key,
                    label=label,
                    value_text=default_value,
                    value_type=value_type,
                    description=description,
                    is_active=True,
                )
                db.session.add(row)
            else:
                if hasattr(row, "label"):
                    row.label = label
                if hasattr(row, "value_type"):
                    row.value_type = value_type
                if getattr(row, "value_text", None) in (None, ""):
                    row.value_text = default_value
                if hasattr(row, "description"):
                    row.description = description
                if hasattr(row, "is_active"):
                    row.is_active = True
            changed.append(f"{module_key}.{setting_key}")
        if commit:
            db.session.commit()
        return {"ok": True, "settings": changed}
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        try:
            from app.extensions import db
            db.session.rollback()
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            logging.getLogger(__name__).exception("BYS360 suppressed exception captured in app/services/performance/completion_phase4_third_manager_center.py:523")
        return {"ok": True, "settings": changed, "warning": str(exc), "static_contract_only": True}


__all__ = [
    "BYS360_PERFORMANCE_COMPLETION_PHASE4_THIRD_MANAGER_CENTER",
    "BYS360_PERFORMANCE_COMPLETION_PHASE4_NO_FAKE_THIRD_TASK",
    "BYS360_PERFORMANCE_COMPLETION_PHASE4_COMMENT_SCORE_MODE_SPLIT",
    "BYS360_PERFORMANCE_COMPLETION_PHASE4_WEIGHT_TOTAL_100",
    "BYS360_PERFORMANCE_COMPLETION_PHASE4_VERSION",
    "MODE_COMMENT",
    "MODE_SCORE",
    "MODE_OFF",
    "STATUS_LABELS",
    "Phase4ThirdManagerDecision",
    "normalize_third_manager_mode",
    "phase4_policy_snapshot",
    "resolve_phase4_third_manager_decision",
    "phase4_should_create_third_manager_task",
    "phase4_status_label_for_third_manager",
    "phase4_humanize_assignment_status",
    "phase4_filter_third_manager_tasks",
    "phase4_should_show_third_manager_column",
    "normalize_phase4_manager_weights",
    "phase4_legacy_policy_snapshot",
    "phase4_static_contract",
    "seed_phase4_third_manager_center",
]
