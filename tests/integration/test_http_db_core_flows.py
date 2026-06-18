from __future__ import annotations

import importlib
from collections import Counter

import pytest
from sqlalchemy import text


def _make_app(monkeypatch):
    """BYS360 uygulamasını gerçek Flask test client ile açar.

    Bu testler canlı veriye dokunmaz. Varsayılan olarak SQLite memory DB ile
    yalnızca app factory, blueprint registration, security guard ve temel HTTP
    davranışını doğrular. Gerçek staging DB ile koşmak istenirse:

        BYS360_INTEGRATION_USE_REAL_DB=1
        TEST_DATABASE_URL=postgresql+psycopg2://...
    """
    monkeypatch.setenv("APP_ENV", "testing")
    monkeypatch.setenv("FLASK_ENV", "testing")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("DEFAULT_FIRST_LOGIN_PASSWORD", "test-password")
    monkeypatch.setenv("FLASK_SKIP_SCHEMA_VALIDATION", "1")
    monkeypatch.setenv("AUTO_REPAIR_SCHEMA", "false")
    monkeypatch.setenv("STRICT_SCHEMA_CHECK", "false")
    monkeypatch.setenv("REQUIRE_DOTENV_FILE", "false")
    monkeypatch.setenv("STRICT_ENV_VALIDATION", "false")
    monkeypatch.setenv("WTF_CSRF_ENABLED", "false")
    monkeypatch.setenv("CACHE_BACKEND", "memory")
    monkeypatch.setenv("SECURITY_RATE_LIMIT_BACKEND", "memory")
    monkeypatch.setenv("ASYNC_TASKS_ENABLED", "0")

    use_real_db = str(__import__("os").environ.get("BYS360_INTEGRATION_USE_REAL_DB", "")).lower() in {"1", "true", "yes", "on"}
    if not use_real_db:
        monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    elif __import__("os").environ.get("TEST_DATABASE_URL"):
        monkeypatch.setenv("DATABASE_URL", __import__("os").environ["TEST_DATABASE_URL"])

    app_module = importlib.import_module("app")
    app = app_module.create_app()
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        LOGIN_DISABLED=False,
    )
    return app


@pytest.fixture(scope="function")
def app(monkeypatch):
    return _make_app(monkeypatch)


@pytest.fixture(scope="function")
def client(app):
    return app.test_client()


def _assert_safe_response(response, *, path: str, allowed: set[int] | None = None) -> None:
    if allowed is not None:
        assert response.status_code in allowed, f"{path} beklenmeyen HTTP durum: {response.status_code}"
    assert response.status_code < 500, f"{path} 5xx verdi: {response.status_code}"
    assert response.status_code != 404, f"{path} route kayıp görünüyor"


def test_app_factory_registers_routes_without_duplicate_endpoints(app):
    """Intentional alias URLs are allowed; exact duplicate rule keys are not."""
    route_keys = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint == "static":
            continue

        methods = ",".join(
            sorted(method for method in rule.methods if method not in {"HEAD", "OPTIONS"})
        )
        route_keys.append((rule.endpoint, rule.rule, methods))

    route_counts = Counter(route_keys)
    duplicated = {
        f"{endpoint} {path}|{methods}": count
        for (endpoint, path, methods), count in route_counts.items()
        if count > 1
    }
    assert duplicated == {}, f"Duplicate endpoint/path/method found: {duplicated}"

def test_main_blueprint_namespace_is_modular_source_distributed(app):
    """Shared main blueprint is allowed, but it must stay source-module distributed."""
    module_counts = Counter()

    for rule in app.url_map.iter_rules():
        if not rule.endpoint.startswith("main."):
            continue

        view_func = app.view_functions.get(rule.endpoint)
        module_name = getattr(view_func, "__module__", "<unknown>")
        module_counts[module_name] += 1

    main_route_count = sum(module_counts.values())
    assert main_route_count > 0

    # If the legacy main namespace is still large, it must be distributed across modules.
    # If future work moves domains to their own blueprints and main shrinks, this test stays valid.
    if main_route_count >= 200:
        largest_module, largest_count = module_counts.most_common(1)[0]
        assert len(module_counts) >= 20, {
            "main_route_count": main_route_count,
            "source_module_count": len(module_counts),
        }
        assert largest_count <= 80, {
            "largest_module": largest_module,
            "largest_count": largest_count,
            "main_route_count": main_route_count,
        }


def test_database_session_is_available(app):
    from app.extensions import db

    with app.app_context():
        assert db.session.execute(text("SELECT 1")).scalar() == 1


def test_healthz_contract(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    payload = response.get_json(silent=True) or {}
    assert payload.get("service") == "bys360"


def test_root_get_is_safe(client):
    response = client.get("/")
    assert response.status_code in {200, 302, 401, 403}
    assert response.status_code < 500


def test_root_post_is_blocked_by_security_guard(client):
    response = client.post("/", data={"unexpected": "mutation"})
    assert response.status_code in {405, 429}
    assert response.status_code < 500


@pytest.mark.parametrize(
    "path",
    [
        "/performance/personel-analizi",
        "/performance/team-comparison",
        "/performance/core-health",
        "/hr-management",
        "/hr-management/leave",
        "/hr-management/attendance",
        "/hr-management/reports",
    ],
)
def test_live_core_protected_routes_exist_and_do_not_500(client, path):
    response = client.get(path)
    _assert_safe_response(response, path=path, allowed={200, 302, 401, 403})


@pytest.mark.parametrize("path", ["/portal", "/strategy", "/education", "/education-isg"])
def test_removed_scope_routes_are_not_publicly_open(client, path):
    response = client.get(path)
    assert response.status_code in {302, 401, 403, 404, 410}
    assert response.status_code < 500
    assert response.status_code != 200, f"{path} kapsam dışıyken açık 200 dönmemeli"

# BYS360_SPRINT2_LEGACY_INTEGRATION_CISAFE_HOTFIX_V8_1
# Bu dosya app factory / route kayıtları / DB bağlantı zinciri gibi geniş kapsamlı entegrasyon davranışlarını kontrol eder.
# Standart CI-safe seçiminden ayrılır; gerektiğinde özel integration/realdb koşusunda çalıştırılır.
pytestmark = [pytest.mark.legacy_integration, pytest.mark.realdb]
