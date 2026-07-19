
"""BYS360 performans zinciri için tek merkezli kural motoru.

Bu dosya zincir kararının kurumsal anayasasıdır. Ekranlar, görev üretimi,
otomatik hiyerarşi onarımı ve V2 performans akışı aynı slot mantığını buradan
okumalıdır. Slot sırası ile işlem sırası bilinçli olarak ayrıdır:

- Slot 1 kurumsal nihai amirdir.
- Slot 2 önce işlem yapan üst akış amiridir.
- Slot 3 varsa önce görüş/puan veren ek amirdir.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from app.services.hierarchy_rulebook_service import build_lookup, desired_manager_sicils
from app.services.explicit_manager_chain_service import current_manager_tuple, has_explicit_manager_fields

RULE_ENGINE_VERSION = "2026-04-18-chain-engine-lock-v1"

GROUP_STAFF_SLOTS: Mapping[int, str] = {
    1: "grup_baskani",
    2: "koordinator",
    3: "birim_amiri_optional",
}
COORDINATOR_SLOTS: Mapping[int, str] = {
    1: "baskan_yardimcisi",
    2: "grup_baskani",
}
GROUP_MANAGER_SLOTS: Mapping[int, str] = {
    1: "baskan",
    2: "baskan_yardimcisi",
}
SPECIAL_DIRECT_PRESIDENT_TITLES: tuple[str, ...] = (
    "baskan_danismani",
    "ozel_kalem",
    "ic_denetci",
)

DEFAULT_TWO_MANAGER_FLOW: tuple[int, int] = (2, 1)
DEFAULT_THREE_MANAGER_FLOW: tuple[int, int, int] = (3, 2, 1)
DEFAULT_SINGLE_MANAGER_FLOW: tuple[int, ...] = (1,)

SINGLE_MANAGER_WEIGHTS: Mapping[int, float] = {1: 100.0, 2: 0.0, 3: 0.0}
TWO_MANAGER_WEIGHTS: Mapping[int, float] = {1: 50.0, 2: 50.0, 3: 0.0}
THREE_MANAGER_COMMENT_WEIGHTS: Mapping[int, float] = {1: 50.0, 2: 50.0, 3: 0.0}
THREE_MANAGER_SCORING_WEIGHTS: Mapping[int, float] = {1: 40.0, 2: 40.0, 3: 20.0}


@dataclass(slots=True)
class AuthoritativeChain:
    employee_id: int | None
    rule_code: str
    manager_1_sicil: str | None = None
    manager_2_sicil: str | None = None
    manager_3_sicil: str | None = None
    expected_levels: tuple[int, ...] = field(default_factory=tuple)
    flow_order: tuple[int, ...] = field(default_factory=tuple)
    info_notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    explicit_level_3_requested: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "rule_code": self.rule_code,
            "manager_1_sicil": self.manager_1_sicil,
            "manager_2_sicil": self.manager_2_sicil,
            "manager_3_sicil": self.manager_3_sicil,
            "expected_levels": list(self.expected_levels),
            "flow_order": list(self.flow_order),
            "info_notes": list(self.info_notes),
            "warnings": list(self.warnings),
            "explicit_level_3_requested": self.explicit_level_3_requested,
        }


def _safe(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def compute_flow_order(*, manager_1_sicil: str | None, manager_2_sicil: str | None, manager_3_sicil: str | None) -> tuple[int, ...]:
    """Dolmuş slotlara göre işlem sırasını üretir.

    Tek amirli özel kurallarda yalnızca (1,) döner. İki amirli zincirde sıra
    her zaman 2 -> 1; üç amir varsa 3 -> 2 -> 1'dir.
    """
    if _safe(manager_3_sicil):
        return DEFAULT_THREE_MANAGER_FLOW
    if _safe(manager_2_sicil):
        return DEFAULT_TWO_MANAGER_FLOW
    if _safe(manager_1_sicil):
        return DEFAULT_SINGLE_MANAGER_FLOW
    return tuple()


def _to_authoritative_chain(raw: Any, user: Any) -> AuthoritativeChain:
    manager_1 = _safe(getattr(raw, "manager_1_sicil", None)) or None
    manager_2 = _safe(getattr(raw, "manager_2_sicil", None)) or None
    manager_3 = _safe(getattr(raw, "manager_3_sicil", None)) or None
    return AuthoritativeChain(
        employee_id=getattr(user, "id", None),
        rule_code=_safe(getattr(raw, "rule_code", "")) or "unknown",
        manager_1_sicil=manager_1,
        manager_2_sicil=manager_2,
        manager_3_sicil=manager_3,
        expected_levels=tuple(getattr(raw, "expected_levels", tuple()) or tuple()),
        flow_order=compute_flow_order(manager_1_sicil=manager_1, manager_2_sicil=manager_2, manager_3_sicil=manager_3),
        info_notes=list(getattr(raw, "info_notes", []) or []),
        warnings=list(getattr(raw, "warnings", []) or []),
        explicit_level_3_requested=bool(getattr(raw, "explicit_level_3_requested", False)),
    )


def _explicit_authoritative_chain(user: Any) -> AuthoritativeChain:
    # BYS360_EXPLICIT_MANAGER_CHAIN_V2
    # Excel/import veya personel kartında elle verilmiş amir sicilleri varsa
    # performans ekranları ve görev üretimi için bu alanlar kaynak kabul edilir.
    current = current_manager_tuple(user)
    manager_1 = _safe(current.manager_1_sicil) or None
    manager_2 = _safe(current.manager_2_sicil) or None
    manager_3 = _safe(current.manager_3_sicil) or None
    expected_levels = tuple(level for level, value in ((1, manager_1), (2, manager_2), (3, manager_3)) if _safe(value))
    return AuthoritativeChain(
        employee_id=getattr(user, "id", None),
        rule_code="explicit_personnel_manager_chain",
        manager_1_sicil=manager_1,
        manager_2_sicil=manager_2,
        manager_3_sicil=manager_3,
        expected_levels=expected_levels,
        flow_order=compute_flow_order(manager_1_sicil=manager_1, manager_2_sicil=manager_2, manager_3_sicil=manager_3),
        info_notes=["Personel kartındaki/Excel importtaki açık amir sicil zinciri esas alındı."],
        warnings=[],
        explicit_level_3_requested=bool(manager_3),
    )


def resolve_authoritative_chain(
    user: Any,
    users: Iterable[Any] | None = None,
    *,
    lookup: Any | None = None,
    preserve_explicit_level3: bool = True,
    prefer_explicit_chain: bool = True,
) -> AuthoritativeChain:
    """Kullanıcı için tek yetkili zincir sonucunu üretir.

    `lookup` verildiyse tekrar oluşturulmaz. Böylece toplu görev üretiminde
    performans kaybı olmaz. `users` verildiyse lookup burada kurulur.
    """
    if prefer_explicit_chain and has_explicit_manager_fields(user):
        return _explicit_authoritative_chain(user)
    if lookup is None:
        lookup = build_lookup(list(users or []))
    raw = desired_manager_sicils(user, lookup, preserve_explicit_level3=preserve_explicit_level3)
    return _to_authoritative_chain(raw, user)


def resolve_authoritative_desired_chain(
    user: Any,
    lookup: Any,
    *,
    preserve_explicit_level3: bool = True,
    prefer_explicit_chain: bool = True,
) -> AuthoritativeChain:
    """Eski servislerin kullandığı DesiredChain alanlarıyla uyumlu kısayol."""
    return resolve_authoritative_chain(
        user,
        lookup=lookup,
        preserve_explicit_level3=preserve_explicit_level3,
        prefer_explicit_chain=prefer_explicit_chain,
    )


def weights_for_chain(*, has_level_2: bool, has_level_3: bool, level_3_mode: str = "comment_only") -> dict[int, float]:
    if not has_level_2:
        return dict(SINGLE_MANAGER_WEIGHTS)
    if not has_level_3:
        return dict(TWO_MANAGER_WEIGHTS)
    if level_3_mode == "scoring":
        return dict(THREE_MANAGER_SCORING_WEIGHTS)
    return dict(THREE_MANAGER_COMMENT_WEIGHTS)


def get_chain_rule_matrix_snapshot() -> dict[str, Any]:
    return {
        "version": RULE_ENGINE_VERSION,
        "slots": {
            "group_staff": dict(GROUP_STAFF_SLOTS),
            "coordinator": dict(COORDINATOR_SLOTS),
            "group_manager": dict(GROUP_MANAGER_SLOTS),
            "special_direct_president": list(SPECIAL_DIRECT_PRESIDENT_TITLES),
        },
        "flow_orders": {
            "single": list(DEFAULT_SINGLE_MANAGER_FLOW),
            "two_manager": list(DEFAULT_TWO_MANAGER_FLOW),
            "three_manager": list(DEFAULT_THREE_MANAGER_FLOW),
        },
        "weights": {
            "single": dict(SINGLE_MANAGER_WEIGHTS),
            "two_manager": dict(TWO_MANAGER_WEIGHTS),
            "three_manager_comment_only": dict(THREE_MANAGER_COMMENT_WEIGHTS),
            "three_manager_scoring": dict(THREE_MANAGER_SCORING_WEIGHTS),
        },
        "visibility": {
            "blind_review_allowed": False,
            "employee_result_requires_publish": True,
            "next_manager_sees_previous_score_and_comment": True,
        },
    }


def assert_chain_constitution_alignment() -> None:
    snapshot = get_chain_rule_matrix_snapshot()
    assert snapshot["slots"]["group_staff"][1] == "grup_baskani"
    assert snapshot["slots"]["group_staff"][2] == "koordinator"
    assert snapshot["slots"]["coordinator"][1] == "baskan_yardimcisi"
    assert snapshot["slots"]["coordinator"][2] == "grup_baskani"
    assert snapshot["slots"]["group_manager"][1] == "baskan"
    assert snapshot["slots"]["group_manager"][2] == "baskan_yardimcisi"


__all__ = [
    "AuthoritativeChain",
    "COORDINATOR_SLOTS",
    "DEFAULT_SINGLE_MANAGER_FLOW",
    "DEFAULT_THREE_MANAGER_FLOW",
    "DEFAULT_TWO_MANAGER_FLOW",
    "GROUP_MANAGER_SLOTS",
    "GROUP_STAFF_SLOTS",
    "RULE_ENGINE_VERSION",
    "SPECIAL_DIRECT_PRESIDENT_TITLES",
    "assert_chain_constitution_alignment",
    "compute_flow_order",
    "get_chain_rule_matrix_snapshot",
    "resolve_authoritative_chain",
    "resolve_authoritative_desired_chain",
    "weights_for_chain",
]
