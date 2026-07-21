from __future__ import annotations


def current_actionable_levels(resolved_chain, existing_assignments: list[object]) -> list[int]:
    submitted_levels = {
        getattr(item, 'manager_level', None)
        for item in existing_assignments
        if (getattr(item, 'status', '') or '').strip().lower() in {'tamamlandi', 'submitted'}
    }
    actionable: list[int] = []
    for level in resolved_chain.order:
        if level not in resolved_chain.levels:
            continue
        previous_required = [candidate for candidate in resolved_chain.order if candidate > level and candidate in resolved_chain.levels]
        if any(candidate not in submitted_levels for candidate in previous_required):
            continue
        actionable.append(level)
    return actionable