from __future__ import annotations

REQUIRED_ITEM_COMMENT_SCORES = {1, 5}
GENERAL_COMMENT_THRESHOLD_LOW = 70.0
GENERAL_COMMENT_THRESHOLD_HIGH = 90.0


def normalize_score(value) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def requires_item_comment(score) -> bool:
    normalized = normalize_score(score)
    return normalized in REQUIRED_ITEM_COMMENT_SCORES


def requires_general_comment(final_total_100: float | int | None) -> bool:
    if final_total_100 is None:
        return False
    try:
        total = float(final_total_100)
    except (TypeError, ValueError):
        return False
    return total < GENERAL_COMMENT_THRESHOLD_LOW or total > GENERAL_COMMENT_THRESHOLD_HIGH
