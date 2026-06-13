# -*- coding: utf-8 -*-
"""BYS360 test ortamı güvenli başlangıç ve CI-safe kapsam disiplini.

Bu dosya yalnızca pytest çalışırken devreye girer. Canlı uygulama ayarlarını
ve üretim SECRET_KEY politikasını gevşetmez; test sürecinde terminalde kalmış
APP_ENV=production gibi değerlerin unit testleri gereksiz yere durdurmasını engeller.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

# Testler uygulama paketini import etmeden önce güvenli test bağlamı kurulmalıdır.
os.environ["APP_ENV"] = "testing"
os.environ["FLASK_ENV"] = "testing"
os.environ["TESTING"] = "true"
os.environ["BYS360_TESTING"] = "true"

# Bu değer canlı anahtar değildir; yalnızca pytest import zincirinde Config'in
# güçlü anahtar kontrolünü test ortamı için güvenli biçimde geçmek içindir.
os.environ["SECRET_KEY"] = "bys360-pytest-only-secret-key-2026-minimum-strong"

# Test sırasında canlı davranışı etkileyebilecek yan etkiler kapalı tutulur.
os.environ.setdefault("MAINTENANCE_MODE", "false")
os.environ.setdefault("CSP_REPORT_ONLY", "true")
os.environ.setdefault("WTF_CSRF_ENABLED", "false")
os.environ.setdefault("MAIL_SUPPRESS_SEND", "true")
os.environ.setdefault("SCHEDULER_ENABLED", "false")

# BYS360_QUALITY9_CI_SAFE_SCOPE_DISCIPLINE_START
# CI-safe artık tüm eski testleri otomatik işaretlemez. Eski sprint/refactor,
# uzman inceleme, gerçek DB, canlı HTTP ve fixture isteyen testler ayrı kapıdır.
# CI-safe kapısı yalnızca tests/quality altındaki deterministik kalite sözleşmesi
# testlerini çalıştırır. Bu sayede kalite kapısı gerçek sinyal üretir ve legacy
# borçlar ayrı fazlarda ele alınır.
_BYS360_CI_SAFE_ALLOWED_PATH_PARTS = {
    str(Path("tests") / "quality"),
}


def _bys360_item_path(item: pytest.Item) -> str:
    path = getattr(item, "path", None) or getattr(item, "fspath", "")
    return str(path).replace("\\", "/")


def _bys360_is_ci_safe_scope_active(config: pytest.Config) -> bool:
    markexpr = getattr(config.option, "markexpr", "") or ""
    args = " ".join(str(arg) for arg in getattr(config, "args", []) or [])
    return "ci_safe" in markexpr or "ci_safe" in args


def _bys360_is_allowed_ci_safe_item(item: pytest.Item) -> bool:
    item_path = _bys360_item_path(item)
    return "/tests/quality/" in item_path or item_path.endswith("/tests/quality")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if not _bys360_is_ci_safe_scope_active(config):
        return

    kept: list[pytest.Item] = []
    deselected: list[pytest.Item] = []
    for item in items:
        if _bys360_is_allowed_ci_safe_item(item):
            kept.append(item)
        else:
            deselected.append(item)

    if deselected:
        config.hook.pytest_deselected(items=deselected)
        items[:] = kept
# BYS360_QUALITY9_CI_SAFE_SCOPE_DISCIPLINE_END

# BYS360_A5_P2C_TEST_DB_FIX_START
# Test-only app/client fixtures. Runtime uygulama koduna dokunmaz.
# Ama?: route smoke testlerinde g?venli, yerel ve bo? SQLite test DB yolu sa?lamak.

import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def app():
    test_runtime = Path("reports/quality/a5_p2c_test_runtime").resolve()
    test_runtime.mkdir(parents=True, exist_ok=True)

    db_path = test_runtime / "bys360_a5_test.sqlite3"
    db_uri = "sqlite:///" + db_path.as_posix()

    os.environ["BYS360_TESTING"] = "1"
    os.environ["FLASK_ENV"] = "testing"
    os.environ["APP_ENV"] = "testing"
    os.environ["DATABASE_URL"] = db_uri
    os.environ["SQLALCHEMY_DATABASE_URI"] = db_uri

    from app import create_app

    app_obj = create_app()
    app_obj.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI=db_uri,
        DATABASE_URL=db_uri,
    )

    try:
        from app.extensions import db
    except Exception:
        db = None

    if db is not None:
        with app_obj.app_context():
            try:
                db.create_all()
            except Exception:
                # Baz? statik/contract testlerinde schema gerekmeyebilir.
                # Runtime hatas?n? gizlememek i?in route testleri yine sonucu g?sterecek.
                pass

    yield app_obj


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def runner(app):
    return app.test_cli_runner()
# BYS360_A5_P2C_TEST_DB_FIX_END
