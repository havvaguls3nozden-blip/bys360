# -*- coding: utf-8 -*-
from __future__ import annotations

from app.services.performance.phase2_category_center import (
    DEFAULT_CATEGORY_LABELS,
    assign_user_category,
    category_average_without_person_detail,
    normalize_category_label,
)


class FakeUser:
    def __init__(self):
        self.personnel_category = None
        self.performance_category_id = None


class FakeScore:
    def __init__(self, score, category):
        self.final_score = score
        self.personnel_category = category


def test_phase2_default_categories_are_institutional():
    assert "Güvenlik" in DEFAULT_CATEGORY_LABELS
    assert "Temizlik" in DEFAULT_CATEGORY_LABELS
    assert "İdari Personel" in DEFAULT_CATEGORY_LABELS
    assert "Teknik Personel" in DEFAULT_CATEGORY_LABELS
    assert "Deneme Süreli Personel" in DEFAULT_CATEGORY_LABELS
    assert "Diğer" in DEFAULT_CATEGORY_LABELS


def test_phase2_category_normalization_and_assignment():
    user = FakeUser()
    label = assign_user_category(user, "guvenlik")
    assert label == "Güvenlik"
    assert user.personnel_category == "Güvenlik"
    assert normalize_category_label("") == "Diğer"


def test_phase2_category_average_does_not_expose_person_detail():
    summary = category_average_without_person_detail(
        [FakeScore(80, "Güvenlik"), FakeScore(60, "Güvenlik"), FakeScore(100, "Temizlik")],
        "Güvenlik",
    )
    assert summary["average_score"] == 70.0
    assert summary["count"] == 2
    assert summary["detail_visible"] is False
    assert summary["person_detail_visible"] is False
    assert "kişi detayı" in summary["privacy_note"]
