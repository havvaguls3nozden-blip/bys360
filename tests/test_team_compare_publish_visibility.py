from app.services.performance.team_compare_service import build_rows, build_stats


class DummyEmployee:
    full_name = "Ayşe Yılmaz"
    sicil_no = "1001"
    birim = "Strateji"
    ust_birim = "Kurumsal"


class DummyEvaluation:
    employee = DummyEmployee()
    level_1_evaluator = type("U", (), {"full_name": "Birinci Amir"})()
    level_2_evaluator = type("U", (), {"full_name": "Ikinci Amir"})()
    level_1_total_100 = 82
    level_2_total_100 = 88
    status = "tamamlandi"


def test_team_compare_rows_include_publish_visibility():
    rows = build_rows(
        [DummyEvaluation()],
        visible_score_fn=lambda _: 90,
        visibility_resolver=lambda _: {"publish_label": "Personele Açık", "publish_badge_class": "published", "employee_visible": True, "can_view_unpublished": False},
    )
    assert rows[0]["publish_label"] == "Personele Açık"
    stats = build_stats(rows)
    assert stats["employee_visible_count"] == 1
