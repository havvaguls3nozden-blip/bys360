"""BYS360 H1E-N -- team_compare_service status_view() raw-value closure.

Found during Section 14's fresh, from-scratch repo-wide re-audit:
status_view()'s catch-all branch (anything other than the two explicitly
checked "tamamlandi"/"kismen_tamamlandi" values) did
`status_label_map.get(normalized, normalized or "Bekliyor")` -- since
`normalized or "Bekliyor"` evaluates to `normalized` itself whenever
`normalized` is a non-empty string, this is exactly the
`X_LABELS.get(raw, raw)` self-fallback shape this whole initiative
targets: a genuinely unmapped/unexpected PerformanceEvaluation.status
value (STATUS_OPTIONS only covers bekliyor/kismen_tamamlandi/
tamamlandi/yayinlandi) would leak raw into both the on-screen team
comparison table and its Excel export (build_excel_workbook() renders
this same status_label field into a workbook cell).

Fixed by dropping the `normalized or` fragment -- the catch-all branch
already treats every one of these values as status_class="pending", so
reusing "Bekliyor" (the correct Turkish word for "pending", and already
the function's own intended default) is consistent with that
classification, not a generic "Bilinmiyor" substitute.

Writes NOTHING to any production source file.
"""
from __future__ import annotations

from types import SimpleNamespace

from app.services.performance.team_compare_service import build_rows, status_view


def test_status_view_never_leaks_a_raw_unmapped_status() -> None:
    status_class, status_label = status_view("future_eval_status_v9")
    assert status_class == "pending"
    assert status_label == "Bekliyor"
    assert status_label != "future_eval_status_v9"


def test_status_view_known_values_still_correct() -> None:
    assert status_view("tamamlandi") == ("done", "Tamamlandı")
    assert status_view("kismen_tamamlandi") == ("partial", "Kısmen Tamamlandı")
    assert status_view("bekliyor") == ("pending", "Bekliyor")
    assert status_view("yayinlandi") == ("pending", "Yayımlandı")


def test_status_view_empty_value_still_falls_back_to_bekliyor() -> None:
    assert status_view("") == ("pending", "Bekliyor")
    assert status_view(None) == ("pending", "Bekliyor")


def test_build_rows_never_leaks_raw_unmapped_evaluation_status() -> None:
    employee = SimpleNamespace(full_name="Test Personel", ad="Test", soyad="Personel", sicil_no="999", birim="TEST", ust_birim="TEST")
    evaluation = SimpleNamespace(
        employee=employee,
        evaluation_exempted=False,
        status="future_eval_status_v9",
        level_1_total_100=70,
        level_2_total_100=70,
        final_total_100=70,
        level_1_evaluator=SimpleNamespace(full_name="Amir"),
        level_2_evaluator=SimpleNamespace(full_name="Amir 2"),
    )
    rows = build_rows([evaluation], visible_score_fn=lambda _: 70.0)

    assert rows[0]["status_label"] == "Bekliyor"
    assert rows[0]["status_label"] != "future_eval_status_v9"
    # The raw stored status value itself is never touched by this display fix.
    assert evaluation.status == "future_eval_status_v9"
