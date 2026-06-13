from __future__ import annotations

from types import SimpleNamespace

from app.services.performance.team_compare_service import (
    apply_filters,
    build_excel_workbook,
    build_rows,
    build_stats,
    build_unit_rankings,
)



def _evaluation(**kwargs):
    employee = kwargs.pop('employee', SimpleNamespace(full_name='Ada Lovelace', ad='Ada', soyad='Lovelace', sicil_no='001', birim='YAZILIM', ust_birim='BT'))
    level_1 = kwargs.pop('level_1_evaluator', SimpleNamespace(full_name='Birinci Amir'))
    level_2 = kwargs.pop('level_2_evaluator', SimpleNamespace(full_name='İkinci Amir'))
    base = dict(
        employee=employee,
        evaluation_exempted=False,
        status='tamamlandi',
        level_1_total_100=80,
        level_2_total_100=90,
        final_total_100=85,
        level_1_evaluator=level_1,
        level_2_evaluator=level_2,
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


def test_build_rows_creates_team_compare_shape():
    rows = build_rows([_evaluation()], visible_score_fn=lambda _: 88.5)
    assert rows[0]['employee_name'] == 'Ada Lovelace'
    assert rows[0]['final_total'] == 88.5
    assert rows[0]['status'] == 'done'


def test_apply_filters_supports_quick_and_search_filters():
    rows = [
        {'employee_name': 'Ada Lovelace', 'sicil_no': '001', 'birim': 'YAZILIM', 'ust_birim': 'BT', 'level_1_name': 'A', 'level_2_name': 'B', 'status_label': 'Tamamlandı', 'attention': 'Denge bandında', 'final_total': 95, 'status': 'done'},
        {'employee_name': 'Grace Hopper', 'sicil_no': '002', 'birim': 'İK', 'ust_birim': 'DESTEK', 'level_1_name': 'C', 'level_2_name': 'D', 'status_label': 'Bekliyor', 'attention': 'Süreç devam ediyor', 'final_total': 55, 'status': 'pending'},
    ]
    filtered = apply_filters(rows, selected_quick='high', q='ada')
    assert len(filtered) == 1
    assert filtered[0]['employee_name'] == 'Ada Lovelace'


def test_build_stats_and_unit_rankings_calculate_summary_fields():
    rows = [
        {'employee_name': 'Ada', 'birim': 'YAZILIM', 'final_total': 95, 'status': 'done'},
        {'employee_name': 'Grace', 'birim': 'YAZILIM', 'final_total': 65, 'status': 'partial'},
        {'employee_name': 'Linus', 'birim': 'İK', 'final_total': 75, 'status': 'pending'},
    ]
    stats = build_stats(rows)
    rankings = build_unit_rankings(rows)
    assert stats['row_count'] == 3
    assert stats['high_count'] == 1
    assert stats['low_count'] == 1
    assert rankings[0]['birim'] == 'YAZILIM'
    assert rankings[0]['count'] == 2


def test_build_excel_workbook_returns_binary_stream():
    rows = [
        {'employee_name': 'Ada', 'sicil_no': '001', 'birim': 'YAZILIM', 'ust_birim': 'BT', 'level_1_name': 'A', 'level_1_total': 80, 'level_2_name': 'B', 'level_2_total': 90, 'final_total': 85, 'status_label': 'Tamamlandı', 'attention': 'Denge bandında'}
    ]
    output = build_excel_workbook(rows)
    data = output.getvalue()
    assert data[:2] == b'PK'
    assert len(data) > 100
