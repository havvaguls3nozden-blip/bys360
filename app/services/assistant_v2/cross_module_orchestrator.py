"""BYS360 Assistant V2 -- cross-module orchestration (mandate Phase 10 / G).

A cross-module answer is built EXCLUSIVELY by calling
`capability_dispatcher.invoke_capability()` once per constituent capability
-- each call goes through the exact same authorization gate as a standalone
capability invocation -- and then intersecting the already-authorized,
already-bounded results in plain Python. There is no raw multi-table SQL
join anywhere in this module, and no capability here can see a module's data
that its own independent authorization check did not already allow.

Fail-closed rule (explicit, not implicit): if ANY constituent capability
required to compute the combined answer is denied/unavailable/erroring, the
WHOLE cross-module result fails closed -- it does NOT silently degrade into
answering a narrower question with only the data that happened to be
authorized. For "kimin değerlendirmesi eksik" (whose evaluation is
incomplete), returning just the personnel list when performance access was
denied would answer a different question in a way that could be mistaken for
an actual answer -- exactly the kind of misleading partial result this
project's anti-hallucination stance (mandate Phase 9) exists to prevent.

This file implements ONE worked example end-to-end
(`personnel_pending_evaluation_in_unit`, matching the mandate's own example:
"Birimimde performans değerlendirmesi tamamlanmamış personeli göster") as a
template other cross-module orchestrations can follow -- it is not meant to
be the only one ever built.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.services.assistant_v2.capability_dispatcher import invoke_capability
from app.services.assistant_v2.result_contract import AssistantResultStatus

_TERMINAL_NON_DATA_STATUSES = frozenset(
    {
        AssistantResultStatus.ACCESS_DENIED,
        AssistantResultStatus.CAPABILITY_UNAVAILABLE,
        AssistantResultStatus.SYSTEM_ERROR,
    }
)


@dataclass(frozen=True)
class CrossModuleResult:
    status: AssistantResultStatus
    message: str
    data: list[dict] | None = None
    contributing_capability_keys: tuple[str, ...] = ()
    contributing_module_keys: tuple[str, ...] = ()
    source_labels: tuple[str, ...] = ()


def personnel_pending_evaluation_in_unit(user, *, birim: str, period_id: int) -> CrossModuleResult:
    """Personnel (personnel_hr) intersected with incomplete performance
    evaluations (performance_mgmt) for one unit and one period. Both
    constituent capabilities are independently authorized; the intersection
    itself happens only after both calls have already returned."""
    personnel_result = invoke_capability(user, "personnel_hr_list_personnel", birim=birim)
    if personnel_result.status in _TERMINAL_NON_DATA_STATUSES:
        return CrossModuleResult(
            status=personnel_result.status,
            message=personnel_result.message,
            contributing_capability_keys=("personnel_hr_list_personnel",),
            contributing_module_keys=("personnel_hr",),
        )

    evaluations_result = invoke_capability(
        user, "performance_mgmt_list_incomplete_evaluations", period_id=period_id
    )
    if evaluations_result.status in _TERMINAL_NON_DATA_STATUSES:
        # Fail closed for the WHOLE query, even though personnel_result may
        # have succeeded -- see module docstring: never silently answer a
        # narrower question with only the authorized half.
        return CrossModuleResult(
            status=evaluations_result.status,
            message=evaluations_result.message,
            contributing_capability_keys=(
                "personnel_hr_list_personnel",
                "performance_mgmt_list_incomplete_evaluations",
            ),
            contributing_module_keys=("personnel_hr", "performance_mgmt"),
        )

    personnel_rows: list[dict] = personnel_result.data or []
    incomplete_rows: list[dict] = evaluations_result.data or []
    incomplete_employee_ids = {row.get("employee_id") for row in incomplete_rows if row.get("employee_id") is not None}

    matched = [row for row in personnel_rows if row.get("id") in incomplete_employee_ids]

    source_labels = tuple(
        label
        for label in (personnel_result.source_label, evaluations_result.source_label)
        if label
    )
    contributing_capability_keys = (
        "personnel_hr_list_personnel",
        "performance_mgmt_list_incomplete_evaluations",
    )
    contributing_module_keys = ("personnel_hr", "performance_mgmt")

    if not matched:
        return CrossModuleResult(
            status=AssistantResultStatus.NO_DATA,
            message="Bu birimde performans değerlendirmesi tamamlanmamış personel bulunamadı.",
            contributing_capability_keys=contributing_capability_keys,
            contributing_module_keys=contributing_module_keys,
        )

    return CrossModuleResult(
        status=AssistantResultStatus.DATA_FOUND,
        message="İstenen bilgi bulundu.",
        data=matched,
        contributing_capability_keys=contributing_capability_keys,
        contributing_module_keys=contributing_module_keys,
        source_labels=source_labels,
    )


__all__ = ["CrossModuleResult", "personnel_pending_evaluation_in_unit"]
