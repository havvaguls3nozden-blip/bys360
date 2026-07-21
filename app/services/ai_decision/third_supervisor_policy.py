
"""BYS360 AI Karar Destek Faz 4 üçüncü amir politika servisi.

Bu servis 3. amir alanını karar destek açısından değerlendirir. Amaç;
3. amir olmayan kayıtlar için boş sütun, gereksiz bekleme ve hatalı görev
sinyalini görünür kılmak; 3. amir olan kayıtlarda ise yorum modu / puan modu
ayrımını kurumsal Türkçe statülerle tek merkezden üretmektir.

BYS360_AI_DECISION_FAZ4_THIRD_SUPERVISOR_POLICY
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any

_VALID_MODES = {"disabled", "comment", "score"}
_TURKISH_TRANSLATION = str.maketrans(
    {
        "ı": "i",
        "İ": "i",
        "ğ": "g",
        "Ğ": "g",
        "ü": "u",
        "Ü": "u",
        "ş": "s",
        "Ş": "s",
        "ö": "o",
        "Ö": "o",
        "ç": "c",
        "Ç": "c",
    }
)


def normalize_key(value: Any) -> str:
    text = str(value or "").strip().lower().translate(_TURKISH_TRANSLATION)
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def coerce_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "evet", "yes", "on", "aktif", "active", "enabled"}:
        return True
    if text in {"0", "false", "hayir", "hayır", "no", "off", "pasif", "inactive", "disabled"}:
        return False
    return default


def coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(str(value).replace(",", "."))
    except Exception:
        return default


def get_first_attr(obj: Any, names: Iterable[str], default: Any = None) -> Any:
    for name in names:
        if isinstance(obj, Mapping) and name in obj:
            return obj.get(name)
        if hasattr(obj, name):
            return getattr(obj, name)
    return default


@dataclass(frozen=True)
class ThirdSupervisorPolicy:
    """3. amir için ayarlanabilir Faz 4 politika sözleşmesi."""

    enabled: bool = True
    mode: str = "comment"
    show_column: bool = True
    weight_enabled: bool = False
    synthetic_task_guard_enabled: bool = True
    empty_column_guard_enabled: bool = True
    default_first_weight: float = 60.0
    default_second_weight: float = 40.0
    default_third_weight: float = 0.0
    prompt_version: str = "ai_decision_faz4_third_supervisor_v1"

    def normalized_mode(self) -> str:
        mode = normalize_key(self.mode)
        if mode in {"yorum", "gorus", "goruş", "comment_only"}:
            return "comment"
        if mode in {"puan", "scoring", "score_mode"}:
            return "score"
        if mode in _VALID_MODES:
            return mode
        return "comment" if self.enabled else "disabled"

    @property
    def is_comment_mode(self) -> bool:
        return self.enabled and self.normalized_mode() == "comment"

    @property
    def is_score_mode(self) -> bool:
        return self.enabled and self.normalized_mode() == "score"

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "mode": self.normalized_mode(),
            "show_column": self.show_column,
            "weight_enabled": self.weight_enabled,
            "synthetic_task_guard_enabled": self.synthetic_task_guard_enabled,
            "empty_column_guard_enabled": self.empty_column_guard_enabled,
            "default_first_weight": self.default_first_weight,
            "default_second_weight": self.default_second_weight,
            "default_third_weight": self.default_third_weight,
            "prompt_version": self.prompt_version,
            "corporate_notice": "3. amir yalnızca kurum kuralı gerektiriyorsa gösterilir; yoksa boş bekleme alanı üretilmez.",
        }


@dataclass(frozen=True)
class ThirdSupervisorStatus:
    has_third_supervisor: bool
    show_column: bool
    expected_action: str
    status_label: str
    score_effect_label: str
    raw_status: str | None = None
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "has_third_supervisor": self.has_third_supervisor,
            "show_column": self.show_column,
            "expected_action": self.expected_action,
            "status_label": self.status_label,
            "score_effect_label": self.score_effect_label,
            "raw_status": self.raw_status,
            "warnings": list(self.warnings),
        }


def build_third_supervisor_policy(settings: Mapping[str, Any] | None = None) -> ThirdSupervisorPolicy:
    """Ayar sözlüğünden 3. amir karar destek politikasını üretir."""
    settings = settings or {}
    enabled = coerce_bool(
        settings.get("performance.third_supervisor_enabled", settings.get("third_supervisor_enabled")),
        True,
    )
    mode = str(settings.get("performance.third_supervisor_mode", settings.get("third_supervisor_mode", "comment")) or "comment")
    show_column = coerce_bool(
        settings.get("performance.third_supervisor_show_column", settings.get("third_supervisor_show_column")),
        True,
    )
    weight_enabled = coerce_bool(
        settings.get("performance.third_supervisor_weight_enabled", settings.get("third_supervisor_weight_enabled")),
        normalize_key(mode) in {"score", "puan", "scoring"},
    )
    return ThirdSupervisorPolicy(
        enabled=enabled,
        mode=mode,
        show_column=show_column,
        weight_enabled=weight_enabled,
        synthetic_task_guard_enabled=coerce_bool(settings.get("ai_decision.faz4_synthetic_task_guard_enabled"), True),
        empty_column_guard_enabled=coerce_bool(settings.get("ai_decision.faz4_empty_column_guard_enabled"), True),
        default_first_weight=coerce_float(settings.get("performance.default_first_supervisor_weight"), 60.0),
        default_second_weight=coerce_float(settings.get("performance.default_second_supervisor_weight"), 40.0),
        default_third_weight=coerce_float(settings.get("performance.default_third_supervisor_weight"), 0.0),
    )


def third_supervisor_id(evaluation: Any) -> Any:
    return get_first_attr(
        evaluation,
        (
            "level_3_evaluator_id",
            "third_supervisor_id",
            "third_evaluator_id",
            "evaluator_3_id",
            "ucuncu_amir_id",
        ),
    )


def third_supervisor_score(evaluation: Any) -> Any:
    return get_first_attr(
        evaluation,
        (
            "level_3_score",
            "third_supervisor_score",
            "third_score",
            "score_3",
            "ucuncu_amir_puani",
        ),
    )


def third_supervisor_comment(evaluation: Any) -> str:
    value = get_first_attr(
        evaluation,
        (
            "level_3_comment",
            "third_supervisor_comment",
            "third_comment",
            "comment_3",
            "ucuncu_amir_gorusu",
        ),
        "",
    )
    return str(value or "").strip()


def raw_third_status(evaluation: Any) -> str | None:
    value = get_first_attr(
        evaluation,
        (
            "level_3_status",
            "third_supervisor_status",
            "third_status",
            "status_3",
            "ucuncu_amir_durumu",
        ),
    )
    return None if value is None else str(value)


def has_third_supervisor(evaluation: Any) -> bool:
    value = third_supervisor_id(evaluation)
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return bool(value)


def should_show_third_supervisor_column(policy: ThirdSupervisorPolicy, evaluations: Iterable[Any]) -> bool:
    """Boş 3. amir sütunu üretmeyi engeller."""
    if not policy.enabled or not policy.show_column:
        return False
    return any(has_third_supervisor(item) for item in evaluations)


def expected_third_supervisor_action(policy: ThirdSupervisorPolicy, evaluation: Any) -> str:
    if not policy.enabled or not has_third_supervisor(evaluation):
        return "none"
    if policy.is_score_mode:
        return "score"
    if policy.is_comment_mode:
        return "comment"
    return "none"


def _raw_status_indicates_waiting(value: str | None) -> bool:
    key = normalize_key(value)
    return any(token in key for token in ("bekliyor", "waiting", "pending", "wait", "3", "third", "ucuncu"))


def build_third_supervisor_status(policy: ThirdSupervisorPolicy, evaluation: Any) -> ThirdSupervisorStatus:
    present = has_third_supervisor(evaluation)
    action = expected_third_supervisor_action(policy, evaluation)
    status = raw_third_status(evaluation)
    warnings: list[str] = []

    if not policy.enabled:
        return ThirdSupervisorStatus(False, False, "none", "3. Amir Kullanılmıyor", "Puan etkisi yok", status)

    if not present:
        if policy.synthetic_task_guard_enabled and _raw_status_indicates_waiting(status):
            warnings.append("3. amir olmayan kayıtta bekleme izi görünüyor.")
        return ThirdSupervisorStatus(False, False, "none", "3. Amir Bulunmuyor", "Puan etkisi yok", status, tuple(warnings))

    if action == "comment":
        if third_supervisor_score(evaluation) not in (None, ""):
            warnings.append("Yorum modundaki 3. amir kaydında puan izi bulunuyor.")
        label = "Yorum/Görüş Bekliyor"
        if third_supervisor_comment(evaluation):
            label = "Yorum/Görüş Tamamlandı"
        return ThirdSupervisorStatus(True, policy.show_column, action, label, "Puan etkisi yok", status, tuple(warnings))

    if action == "score":
        label = "Puanlama Bekliyor"
        if third_supervisor_score(evaluation) not in (None, ""):
            label = "Puanlama Tamamlandı"
        return ThirdSupervisorStatus(True, policy.show_column, action, label, "Puan katkısı var", status, tuple(warnings))

    return ThirdSupervisorStatus(present, policy.show_column, action, "3. Amir Kontrolü Gerekiyor", "Ayar kontrolü gerekli", status, tuple(warnings))


def evaluate_weight_contract(policy: ThirdSupervisorPolicy, weights: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """3. amir ağırlık kuralını güvenli biçimde değerlendirir."""
    weights = weights or {}
    first = coerce_float(weights.get("first", weights.get("level_1", policy.default_first_weight)), policy.default_first_weight)
    second = coerce_float(weights.get("second", weights.get("level_2", policy.default_second_weight)), policy.default_second_weight)
    third = coerce_float(weights.get("third", weights.get("level_3", policy.default_third_weight)), policy.default_third_weight)
    total = round(first + second + third, 4)
    warnings: list[str] = []

    if policy.is_comment_mode and abs(third) > 0.0001:
        warnings.append("Yorum modunda 3. amir ağırlığı 0 olmalıdır.")
    if policy.is_score_mode and abs(total - 100.0) > 0.0001:
        warnings.append("Puan modunda amir ağırlıkları toplamı 100 olmalıdır.")
    if policy.is_score_mode and third <= 0:
        warnings.append("Puan modunda 3. amir ağırlığı tanımlanmalıdır.")

    return {
        "first": first,
        "second": second,
        "third": third,
        "total": total,
        "ok": not warnings,
        "warnings": warnings,
        "label": "Ağırlık dengesi uygun" if not warnings else "Ağırlık dengesi kontrol edilmeli",
    }


def build_third_supervisor_flow_summary(
    evaluations: Iterable[Any],
    policy: ThirdSupervisorPolicy | None = None,
) -> dict[str, Any]:
    policy = policy or ThirdSupervisorPolicy()
    items = list(evaluations or [])
    statuses = [build_third_supervisor_status(policy, item) for item in items]
    with_third = sum(1 for item in statuses if item.has_third_supervisor)
    warnings = [warning for item in statuses for warning in item.warnings]
    return {
        "policy": policy.to_dict(),
        "total_evaluations": len(items),
        "with_third_supervisor": with_third,
        "without_third_supervisor": max(len(items) - with_third, 0),
        "show_column": should_show_third_supervisor_column(policy, items),
        "warning_count": len(warnings),
        "warnings": warnings[:25],
        "status_labels": [item.status_label for item in statuses[:100]],
        "marker": "BYS360_AI_DECISION_FAZ4_THIRD_SUPERVISOR_SUMMARY_OK",
    }
