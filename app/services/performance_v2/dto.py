from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class LevelMode(StrEnum):
    DISABLED = 'off'
    COMMENT_ONLY = 'comment_only'
    SCORE_ENABLED = 'scoring'


class ChainType(StrEnum):
    PRESIDENCY = 'presidency'
    GROUP = 'group'


class SubjectType(StrEnum):
    PRESIDENCY = 'presidency_subject'
    GROUP_MANAGER = 'group_manager_subject'
    COORDINATOR = 'coordinator_subject'
    GROUP_STAFF = 'group_staff_subject'
    HUKUK_STAFF = 'hukuk_staff_subject'


@dataclass(slots=True)
class ChainIssue:
    code: str
    message: str
    severity: str = 'warning'
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ChainLevel:
    level: int
    label: str
    evaluator_id: int | None = None
    evaluator_sicil: str | None = None
    evaluator_name: str | None = None
    evaluator_role: str | None = None
    source_field: str | None = None
    score_enabled: bool = True
    visible_to_next: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ResolvedChain:
    chain_type: str
    subject_type: str
    order: list[int]
    level_mode: str
    levels: dict[int, ChainLevel] = field(default_factory=dict)
    issues: list[ChainIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'chain_type': self.chain_type,
            'subject_type': self.subject_type,
            'order': list(self.order),
            'level_mode': self.level_mode,
            'levels': {level: payload.to_dict() for level, payload in self.levels.items()},
            'issues': [issue.to_dict() for issue in self.issues],
        }


@dataclass(slots=True)
class WeightPlan:
    level_weights: dict[int, float]
    normalized_total: float
    level_mode: str
    source: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class AssignmentPreview:
    level: int
    label: str
    evaluator_id: int | None
    evaluator_name: str | None
    evaluator_role: str | None
    due_date_iso: str | None
    score_enabled: bool
    visible_previous_levels: list[int]
    existing_status: str | None = None
    existing_assignment_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)