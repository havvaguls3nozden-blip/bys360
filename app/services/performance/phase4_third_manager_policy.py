# -*- coding: utf-8 -*-
"""
BYS360 Performans Tamamlama Faz 4
3. Amir Opsiyonelliği ve Akış Temizliği Politika Merkezi

Bu dosya doğrudan canlı veri yazmaz. 3. amir görünürlüğü, görev üretimi,
statü dili ve ağırlık normalizasyonu için güvenli yardımcı sözleşme sunar.
"""
from __future__ import annotations

import logging

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional
logger = logging.getLogger(__name__)


PHASE4_POLICY_MARKER = "BYS360_PERFORMANCE_COMPLETION_PHASE4_THIRD_MANAGER_POLICY"


THIRD_MANAGER_MODE_COMMENT = "comment"
THIRD_MANAGER_MODE_SCORE = "score"
THIRD_MANAGER_MODE_DISABLED = "disabled"

THIRD_MANAGER_STATUS_LABELS = {
    "third_manager_missing": "3. Amir Tanımlı Değil",
    "third_manager_disabled": "3. Amir Devre Dışı",
    "third_manager_comment_pending": "3. Amir Görüş/Yorum Bekliyor",
    "third_manager_comment_done": "3. Amir Görüş/Yorum Tamamlandı",
    "third_manager_score_pending": "3. Amir Puanlama Bekliyor",
    "third_manager_score_done": "3. Amir Puanlama Tamamlandı",
}


@dataclass(frozen=True)
class ThirdManagerDecision:
    enabled: bool
    has_third_manager: bool
    mode: str
    show_column: bool
    create_task: bool
    score_required: bool
    comment_required: bool
    score_weight: float
    status_key: str
    status_label: str


def _bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "evet", "on", "aktif", "enabled"}


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _norm_mode(value: Any) -> str:
    raw = str(value or THIRD_MANAGER_MODE_COMMENT).strip().lower()
    if raw in {"puan", "score", "scoring", "puan_modu"}:
        return THIRD_MANAGER_MODE_SCORE
    if raw in {"kapali", "kapalı", "disabled", "off", "none", "yok"}:
        return THIRD_MANAGER_MODE_DISABLED
    return THIRD_MANAGER_MODE_COMMENT


def resolve_third_manager_policy(
    *,
    third_manager_id: Any = None,
    third_manager_name: Any = None,
    settings: Optional[Mapping[str, Any]] = None,
    completed: bool = False,
) -> ThirdManagerDecision:
    """
    3. amir için tek karar noktası.

    Kurallar:
    - 3. amir zorunlu değildir.
    - 3. amir yoksa kolon/görev/statü üretilmez.
    - Yorum modunda puan beklenmez, ağırlık 0 kabul edilir.
    - Puan modunda ağırlık hesabına dahil olabilir.
    """
    settings = settings or {}
    enabled = _bool(settings.get("performance.phase4.third_manager_enabled", True), True)
    mode = _norm_mode(settings.get("performance.phase4.third_manager_mode", THIRD_MANAGER_MODE_COMMENT))
    has_third = bool(third_manager_id or str(third_manager_name or "").strip())

    if not enabled or mode == THIRD_MANAGER_MODE_DISABLED:
        return ThirdManagerDecision(
            enabled=False,
            has_third_manager=has_third,
            mode=THIRD_MANAGER_MODE_DISABLED,
            show_column=False,
            create_task=False,
            score_required=False,
            comment_required=False,
            score_weight=0.0,
            status_key="third_manager_disabled",
            status_label=THIRD_MANAGER_STATUS_LABELS["third_manager_disabled"],
        )

    if not has_third:
        return ThirdManagerDecision(
            enabled=True,
            has_third_manager=False,
            mode=mode,
            show_column=False,
            create_task=False,
            score_required=False,
            comment_required=False,
            score_weight=0.0,
            status_key="third_manager_missing",
            status_label=THIRD_MANAGER_STATUS_LABELS["third_manager_missing"],
        )

    if mode == THIRD_MANAGER_MODE_SCORE:
        status_key = "third_manager_score_done" if completed else "third_manager_score_pending"
        return ThirdManagerDecision(
            enabled=True,
            has_third_manager=True,
            mode=THIRD_MANAGER_MODE_SCORE,
            show_column=True,
            create_task=True,
            score_required=True,
            comment_required=False,
            score_weight=_float(settings.get("performance.phase4.third_manager_score_weight", 20), 20.0),
            status_key=status_key,
            status_label=THIRD_MANAGER_STATUS_LABELS[status_key],
        )

    status_key = "third_manager_comment_done" if completed else "third_manager_comment_pending"
    return ThirdManagerDecision(
        enabled=True,
        has_third_manager=True,
        mode=THIRD_MANAGER_MODE_COMMENT,
        show_column=True,
        create_task=True,
        score_required=False,
        comment_required=True,
        score_weight=0.0,
        status_key=status_key,
        status_label=THIRD_MANAGER_STATUS_LABELS[status_key],
    )


def normalize_manager_weights(weights: Optional[Mapping[str, Any]] = None, third_manager_mode: str = THIRD_MANAGER_MODE_COMMENT) -> Dict[str, float]:
    """
    Amir ağırlıklarını her durumda %100'e normalize eder.
    Yorum modunda 3. amir ağırlığı 0'dır.
    """
    weights = dict(weights or {})
    w1 = max(_float(weights.get("manager_1", weights.get("first_manager", 60)), 60.0), 0.0)
    w2 = max(_float(weights.get("manager_2", weights.get("second_manager", 40)), 40.0), 0.0)

    mode = _norm_mode(third_manager_mode)
    w3 = 0.0
    if mode == THIRD_MANAGER_MODE_SCORE:
        w3 = max(_float(weights.get("manager_3", weights.get("third_manager", 20)), 20.0), 0.0)

    total = w1 + w2 + w3
    if total <= 0:
        return {"manager_1": 100.0, "manager_2": 0.0, "manager_3": 0.0}

    return {
        "manager_1": round((w1 / total) * 100, 4),
        "manager_2": round((w2 / total) * 100, 4),
        "manager_3": round((w3 / total) * 100, 4),
    }


def filter_fake_third_manager_tasks(tasks: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """
    3. amir olmayan kayıtlarda sahte 3. amir görevinin UI/akışa düşmesini engeller.
    """
    cleaned: List[Dict[str, Any]] = []
    for task in tasks or []:
        row = dict(task)
        level = str(row.get("manager_level") or row.get("level") or row.get("amir_seviyesi") or "").strip()
        if level in {"3", "third", "third_manager", "ucuncu", "üçüncü"}:
            if not (row.get("manager_id") or row.get("manager_name") or row.get("third_manager_id") or row.get("third_manager_name")):
                continue
            mode = _norm_mode(row.get("third_manager_mode") or row.get("mode") or THIRD_MANAGER_MODE_COMMENT)
            if mode == THIRD_MANAGER_MODE_DISABLED:
                continue
            if mode == THIRD_MANAGER_MODE_COMMENT:
                row["score_required"] = False
                row["task_label"] = row.get("task_label") or "3. Amir Görüş/Yorum Bekliyor"
            elif mode == THIRD_MANAGER_MODE_SCORE:
                row["score_required"] = True
                row["task_label"] = row.get("task_label") or "3. Amir Puanlama Bekliyor"
        cleaned.append(row)
    return cleaned


def should_show_third_manager_column(rows: Iterable[Mapping[str, Any]], settings: Optional[Mapping[str, Any]] = None) -> bool:
    """
    Tablo/formlarda 3. amir kolonu sadece gerçekten kullanılacaksa görünür.
    """
    for row in rows or []:
        decision = resolve_third_manager_policy(
            third_manager_id=row.get("third_manager_id") or row.get("manager_3_id"),
            third_manager_name=row.get("third_manager_name") or row.get("manager_3_name"),
            settings=settings,
        )
        if decision.show_column:
            return True
    return False


def third_manager_status_label(status_key: str) -> str:
    return THIRD_MANAGER_STATUS_LABELS.get(str(status_key or "").strip(), "3. Amir Durumu")

# BYS360_PERFORMANCE_COMPLETION_PHASE5_SCORECARD_UI_BOUND
# Karne/puanlama ekranları phase5_scorecard_ui_policy sözleşmesini kullanır.
