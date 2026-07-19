from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
def test_admin_path_guard_exists():
    text=(ROOT/'app/bootstrap/operational_guards.py').read_text(encoding='utf-8')
    assert 'def _enforce_admin_path_guard' in text
    assert '_is_admin_path(request.path)' in text
    assert '_has_admin_family_access(current_user)' in text
def test_setup_admin_only_first_install_contract():
    text=(ROOT/'app/main_handlers/auth_handlers.py').read_text(encoding='utf-8')
    assert 'def setup_admin' in text
    assert 'if User.query.count() > 0' in text
