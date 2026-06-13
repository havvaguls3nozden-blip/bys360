from __future__ import annotations




def raw_score_to_100(raw_score: float | int | None) -> float:
    if raw_score is None:
        return 0.0
    try:
        value = float(raw_score)
    except (TypeError, ValueError):
        return 0.0
    value = max(1.0, min(5.0, value))
    return round(value * 20.0, 2)


def compute_final_score(level_scores: dict[int, float | int | None], weights: dict[int, float]) -> float:
    total = 0.0
    for level, weight in weights.items():
        score = level_scores.get(level)
        if score is None:
            continue
        total += float(score) * (float(weight) / 100.0)
    return round(total, 2)