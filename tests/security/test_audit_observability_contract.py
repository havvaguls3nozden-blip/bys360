from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]

def test_admin_guard_is_actually_called_before_request():
    text=(ROOT/'app/bootstrap/operational_guards.py').read_text(encoding='utf-8')
    assert 'admin_guard_response = _enforce_admin_path_guard()' in text
    assert 'if admin_guard_response is not None:' in text


def test_denied_admin_access_is_audited():
    text=(ROOT/'app/bootstrap/operational_guards.py').read_text(encoding='utf-8')
    assert 'admin_access_denied_unauthenticated' in text
    assert 'admin_access_denied_role' in text
    assert 'record_security_event(' in text


def test_audit_event_service_is_best_effort():
    text=(ROOT/'app/services/audit_event_service.py').read_text(encoding='utf-8')
    assert 'def record_security_event' in text
    assert 'write_audit_log(' in text
    assert 'db.session.commit()' in text
    assert 'db.session.rollback()' in text
    assert 'return None' in text
