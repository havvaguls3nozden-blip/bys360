from __future__ import annotations



from .rules import visible_previous_levels


def build_previous_level_comment_snapshot(evaluation, current_level: int, policy, level_mode) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for level in visible_previous_levels(current_level=current_level, policy=policy, level_mode=level_mode):
        result.append(
            {
                'level': level,
                'general_comment': getattr(evaluation, f'level_{level}_general_comment', None) if evaluation else None,
                'score_100': getattr(evaluation, f'level_{level}_total_100', None) if evaluation else None,
                'completed': bool(getattr(evaluation, f'level_{level}_completed', False)) if evaluation else False,
            }
        )
    return result