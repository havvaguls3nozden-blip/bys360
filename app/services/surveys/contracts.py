"""Anket canlı modülü için küçük, yan etkisiz veri sözleşmeleri.

Bu dosya canlı route davranışını değiştirmez. Faz 2'nin amacı, ileride
`surveys_routes.py` içindeki iş mantığını güvenli parçalara taşımadan önce
ortak sözleşmeleri sabitlemektir.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SurveyAccessResult:
    """Bir kullanıcının ankete erişim durumunu temsil eder."""

    allowed: bool
    message: str = ""
    starts_at: datetime | None = None
    ends_at: datetime | None = None


@dataclass(slots=True)
class SurveyQuestionDraft:
    """Formdan gelen soru taslağı için taşınabilir yapı."""

    question_text: str
    question_type: str = "text"
    is_required: bool = False
    sort_order: int = 0
    options: list[str] = field(default_factory=list)
    helper_text: str = ""
    logic_mode: str = "always"
    logic_source_question_id: int | None = None
    logic_operator: str = "answered"
    logic_value: str = ""


@dataclass(slots=True)
class SurveyTargetDraft:
    """Anket hedef kitlesi için normalize edilmiş temsil."""

    target_type: str = "all"
    target_values: list[str] = field(default_factory=list)
    user_ids: list[int] = field(default_factory=list)


@dataclass(slots=True)
class SurveyMetricSummary:
    """Liste ve yönetici ekranlarında kullanılan temel sayılar."""

    total_surveys: int = 0
    draft: int = 0
    published: int = 0
    closed: int = 0
    archived: int = 0
    assignments: int = 0
    completed_responses: int = 0
    any_responses: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "total": int(self.total_surveys or 0),
            "draft": int(self.draft or 0),
            "published": int(self.published or 0),
            "closed": int(self.closed or 0),
            "archived": int(self.archived or 0),
            "assignments": int(self.assignments or 0),
            "completed_responses": int(self.completed_responses or 0),
            "any_responses": int(self.any_responses or 0),
        }


def as_plain_dict(value: Any) -> dict[str, Any]:
    """Dataclass veya model benzeri objeyi güvenli sözlük haline getirir."""
    if value is None:
        return {}
    if hasattr(value, "as_dict"):
        try:
            return dict(value.as_dict())
        except Exception:
            logger.exception("BYS360 V6C guarded exception | file=app/services/surveys/contracts.py | line=84")
            return {}
    if hasattr(value, "__dict__"):
        return {k: v for k, v in vars(value).items() if not k.startswith("_")}
    return {}
