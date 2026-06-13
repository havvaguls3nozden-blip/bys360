
"""Performans anayasasi sabit politika bayraklari.

Bu dosya canli sistemde tartismali kural dallanmalarinin tek kaynaktan
yonetilmesi icin vardir. Aynı kural farkli validator, form ve publish
katmanlarinda yeniden yazilmaz.
"""
from __future__ import annotations

POLICY_VERSION = "2026-04-15-no-comment-for-score-three"

# Nihai kurum karari:
# 3 puan verilmesi tek basina ek yorum zorunlulugu dogurmaz.
REQUIRE_LEVEL_2_GENERAL_COMMENT_WHEN_LEVEL_1_SCORE_IS_THREE = False


def is_level_2_comment_required_when_level_1_score_is_three() -> bool:
    return REQUIRE_LEVEL_2_GENERAL_COMMENT_WHEN_LEVEL_1_SCORE_IS_THREE


__all__ = [
    "POLICY_VERSION",
    "REQUIRE_LEVEL_2_GENERAL_COMMENT_WHEN_LEVEL_1_SCORE_IS_THREE",
    "is_level_2_comment_required_when_level_1_score_is_three",
]
