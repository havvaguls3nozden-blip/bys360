"""BYS360_PHASE5_3A_A2_HOST_HEADER_OPEN_REDIRECT_HARDENING

`app/security/redirect_guard.py` (framework'ten bağımsız saf mantık) ve
`app/route_support.py` (Flask/`current_app.config` köprüsü) için negatif ve
pozitif sözleşme testleri.

Bu dosya iki katmanı ayrı ayrı doğrular:
  1. Saf modül testleri: Flask app/request context KURMADAN, doğrudan
     `redirect_guard.is_safe_redirect_target(...)` üzerinde onlarca saldırı
     deseni + geçerli senaryo (parametrize).
  2. Entegrasyon testleri: gerçek Flask `app` fixture'ı ile, SAHTE bir
     `Host` başlığı altında `app.route_support.is_safe_redirect_target` ve
     `redirect_to_next_or`'un host-header poisoning'e karşı bağışık
     olduğunu, kararın yalnızca kanonik `APP_BASE_URL`'e dayandığını kanıtlar.
"""
from __future__ import annotations

import pytest

from app.route_support import (
    is_safe_redirect_target as route_is_safe_redirect_target,
    redirect_to_next_or,
)
from app.security import redirect_guard

# ---------------------------------------------------------------------------
# 1) Saf modül testleri (Flask context gerektirmez)
# ---------------------------------------------------------------------------

CANONICAL_BASE_URL = "https://trusted.example"
ALLOWLIST = [".portal.trusted.example"]


@pytest.mark.parametrize(
    "target",
    [
        # Sahte/dış domain (host header poisoning'in nihai hedefi budur:
        # saldırganın kendi domaini "izinli" görünmeye çalışır).
        "https://evil.example/",
        "HTTPS://EVIL.EXAMPLE/x",
        # Protocol-relative / scheme-relative.
        "//evil.example",
        "///evil.example",
        # Ters eğik çizgi (backslash) varyasyonları -- WHATWG URL ayrıştırıcısı
        # http/https gibi 'special' şemalarda '\\' karakterini de '/' gibi ele
        # alır; bu yüzden tarayıcıda '//evil.example' ile eşdeğerdir.
        "/\\evil.example",
        "\\/evil.example",
        "\\\\evil.example",
        "/\\/evil.example",
        # Percent-encode edilmiş ayraçlar (tek ve çift kodlama).
        "/%2Fevil.example",
        "/%2fevil.example",
        "/%5Cevil.example",
        "/%5cevil.example",
        "/%252Fevil.example",
        # userinfo içeren URL -- tarayıcı '@' öncesini yok sayıp gerçek host'a
        # (evil.example) gider; is_trusted_host bunu ASLA "trusted.example"
        # olarak yorumlamamalı.
        "https://trusted.example@evil.example/",
        "https://trusted.example:443@evil.example/",
        # "Güvenilir host'u prefix/alt dize olarak taşıyan ama aslında farklı
        # bir domain olan" klasik sonek tuzağı.
        "https://trusted.example.evil.example/",
        "https://eviltrusted.example/",
        # allowlist sonek sınırını (dot-boundary) yanlışlıkla atlatmaya çalışan
        # bir varyant: 'eviltrusted.example' ile biten ama '.trusted.example'
        # ile BİTMEYEN bir host.
        "https://portaltrusted.example/",
        # Doğru host, yanlış (kanonik olmayan) port.
        "https://trusted.example:9999/",
        # Tehlikeli şemalar.
        "javascript:alert(1)",
        "JavaScript:alert(1)",
        "data:text/html,<script>alert(1)</script>",
        "vbscript:msgbox(1)",
        "file:///etc/passwd",
        # Kontrol karakteriyle şema gizleme denemesi ('\t' temizlendikten
        # sonra hâlâ tehlikeli şema olarak tespit edilmeli).
        "java\tscript:alert(1)",
        # Boş / None.
        "",
        None,
        "   ",
    ],
)
def test_pure_guard_rejects_open_redirect_and_host_poisoning_patterns(target):
    assert redirect_guard.is_safe_redirect_target(
        target,
        app_base_url=CANONICAL_BASE_URL,
        allowed_hosts=ALLOWLIST,
        allow_local_dev=False,
    ) is False


@pytest.mark.parametrize(
    "target",
    [
        "/dashboard",
        "/dashboard?next=/x",
        "/nested/path/with-dash_and.dot",
        "https://trusted.example/",
        "https://trusted.example:443/anything",
        "HTTPS://TRUSTED.EXAMPLE/mixed-case-host-still-canonical",
        "https://portal.trusted.example/",  # allowlist sonek kuralı: tam eşleşme de kabul
        "https://sub.portal.trusted.example/",  # gerçek alt alan adı
    ],
)
def test_pure_guard_accepts_relative_and_canonical_absolute_targets(target):
    assert redirect_guard.is_safe_redirect_target(
        target,
        app_base_url=CANONICAL_BASE_URL,
        allowed_hosts=ALLOWLIST,
        allow_local_dev=False,
    ) is True


def test_pure_guard_local_dev_exception_is_opt_in_only():
    dev_target = "http://localhost:5000/"
    assert redirect_guard.is_safe_redirect_target(
        dev_target, app_base_url=CANONICAL_BASE_URL, allowed_hosts=[], allow_local_dev=True
    ) is True
    assert redirect_guard.is_safe_redirect_target(
        dev_target, app_base_url=CANONICAL_BASE_URL, allowed_hosts=[], allow_local_dev=False
    ) is False


def test_pure_guard_allowlist_suffix_has_dot_boundary():
    # 'eviltrusted.example', '.trusted.example' sonekiyle BİTMEZ (aradaki nokta
    # sınırı olmadan 'trusted.example' ile bitse bile eşleşmemeli).
    assert redirect_guard.is_trusted_host("eviltrusted.example", [".trusted.example"]) is False
    assert redirect_guard.is_trusted_host("trusted.example", [".trusted.example"]) is True
    assert redirect_guard.is_trusted_host("api.trusted.example", [".trusted.example"]) is True
    assert redirect_guard.is_trusted_host("trusted.example.evil.example", [".trusted.example"]) is False


# ---------------------------------------------------------------------------
# 2) Entegrasyon testleri: gerçek Flask app + sahte Host başlığı
# ---------------------------------------------------------------------------


@pytest.fixture
def canonical_app(app, monkeypatch):
    """Testler boyunca kanonik APP_BASE_URL'i deterministik bir değere sabitler."""
    monkeypatch.setitem(app.config, "APP_BASE_URL", CANONICAL_BASE_URL)
    monkeypatch.setitem(app.config, "REDIRECT_ALLOWED_HOSTS", [])
    monkeypatch.setitem(app.config, "TESTING", True)
    return app


def test_forged_host_header_does_not_grant_trust_for_matching_absolute_target(canonical_app):
    """Saldırgan 'Host: evil.attacker.example' gönderse bile, aynı hedefe
    mutlak yönlendirme kabul edilmemeli -- karar request.host'a değil,
    APP_BASE_URL'e dayanmalı.
    """
    with canonical_app.test_request_context("/some/path", base_url="http://evil.attacker.example"):
        from flask import request

        assert request.host == "evil.attacker.example"  # sahte Host gerçekten set edildi
        assert route_is_safe_redirect_target("https://evil.attacker.example/steal") is False
        assert route_is_safe_redirect_target("http://evil.attacker.example/steal") is False


def test_forged_host_header_does_not_block_canonical_or_relative_targets(canonical_app):
    """Sahte Host başlığı, göreli veya kanonik hedeflerin kabulünü de
    ETKİLEMEMELİ (yanlış negatif / kırılan yerel yönlendirme olmamalı).
    """
    with canonical_app.test_request_context("/some/path", base_url="http://evil.attacker.example"):
        assert route_is_safe_redirect_target("/dashboard") is True
        assert route_is_safe_redirect_target(f"{CANONICAL_BASE_URL}/dashboard") is True


def test_redirect_to_next_or_falls_back_when_next_is_malicious(canonical_app):
    with canonical_app.test_request_context(
        "/login?next=https://evil.example/steal", base_url="http://evil.attacker.example"
    ):
        response = redirect_to_next_or(default_endpoint="main.dashboard")
        assert response.status_code in {301, 302, 303, 307, 308}
        location = response.headers["Location"]
        assert "evil.example" not in location


def test_redirect_to_next_or_honors_safe_relative_next(canonical_app):
    with canonical_app.test_request_context(
        "/login?next=/dashboard", base_url="http://evil.attacker.example"
    ):
        response = redirect_to_next_or(default_endpoint="main.dashboard")
        assert response.headers["Location"] == "/dashboard"


def test_redirect_to_next_or_has_no_redirect_loop_on_unsafe_next(canonical_app):
    """Güvensiz bir 'next' verildiğinde ve default_endpoint/fallback_url
    verilmediğinde tek, sonlu bir yönlendirme üretilmeli (main.dashboard) --
    döngü ya da istisna olmamalı.
    """
    with canonical_app.test_request_context(
        "/login?next=javascript:alert(1)", base_url="http://evil.attacker.example"
    ):
        response = redirect_to_next_or()
        assert response.status_code in {301, 302, 303, 307, 308}
        assert response.headers["Location"]
