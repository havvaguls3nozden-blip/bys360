from app.services.performance.ops_center import _build_readiness_summary, _merge_signal_rows


def test_readiness_summary_forces_critical_when_blocker_exists():
    result = _build_readiness_summary(
        go_live_score=92,
        task_score=100,
        publish_score=96,
        blocker_count=1,
        warning_count=0,
    )
    assert result['readiness_tone'] == 'critical'
    assert result['readiness_label'] == 'Blokaj var'
    assert result['readiness_score'] <= 69


def test_readiness_summary_promotes_ok_when_clean():
    result = _build_readiness_summary(
        go_live_score=84,
        task_score=88,
        publish_score=92,
        blocker_count=0,
        warning_count=0,
    )
    assert result['readiness_tone'] == 'ok'
    assert result['readiness_label'] == 'Operasyon hazır'
    assert result['readiness_score'] >= 90


def test_merge_signal_rows_preserves_source_and_action():
    rows = _merge_signal_rows('Görev ön kontrolü', [
        {'title': 'Kriter toplamı 100 değil', 'detail': 'Aktif kriter toplamı 96.', 'action': 'Kriterleri düzelt.'}
    ], 'critical')
    assert rows[0]['source'] == 'Görev ön kontrolü'
    assert rows[0]['tone'] == 'critical'
    assert rows[0]['title'] == 'Kriter toplamı 100 değil'
    assert rows[0]['action'] == 'Kriterleri düzelt.'
