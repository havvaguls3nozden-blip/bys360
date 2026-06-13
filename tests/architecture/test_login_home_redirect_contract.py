from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8", errors="ignore")


def test_login_success_redirects_to_home_not_dashboard() -> None:
    text = read("app/main_handlers/auth_handlers.py")
    assert 'return redirect(url_for("main.home"))' in text
    assert 'return redirect(url_for("main.dashboard"))' not in text


def test_first_login_security_flows_are_preserved() -> None:
    text = read("app/main_handlers/auth_handlers.py")
    assert 'must_set_security_question' in text
    assert 'return redirect(url_for("main.account_security_setup"))' in text
    assert 'must_change_password' in text
    assert 'return redirect(url_for("main.account_change_password"))' in text


def test_home_route_and_template_exist() -> None:
    routes = read("app/routes.py")
    assert '@main_bp.route("/home")' in routes
    assert 'def home()' in routes
    assert 'return _home_handler()' in routes
    assert (ROOT / "app/templates/home.html").exists()


def test_root_index_keeps_authenticated_user_on_home() -> None:
    public_handlers = read("app/main_handlers/public_handlers.py")
    assert 'return redirect(url_for("main.home"))' in public_handlers
    assert 'return redirect(url_for("main.login"))' in public_handlers
