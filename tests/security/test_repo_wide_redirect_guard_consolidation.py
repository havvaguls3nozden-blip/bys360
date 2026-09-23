"""BYS360_PHASE5_3C_A2_REPO_WIDE_REDIRECT_CONSOLIDATION

Bölüm 3B'de tespit edilip düzeltilmeden bırakılan 4 bağımsız "next"/yönlendirme
hedefi güven kararı bu turda `app.route_support.is_safe_redirect_target`
(-> `app.security.redirect_guard.is_safe_redirect_target`) üzerine
konsolide edildi:

  1. `app/error_handlers.py::_safe_csrf_referer_target`
     (eskiden `request.host_url` tabanlıydı: `referer.startswith(host_url)`).
  2. `app/__init__.py::_bys360_b77_safe_csrf_referrer_target`
     (`_register_csrf_refresh_handler` içindeki CSRF hata işleyicisinin
     kullandığı yardımcı; eskiden `referrer.startswith(host_url) or
     referrer.startswith("/")` idi).
  3. `app/communication/shared.py::_safe_internal_redirect`
     (eskiden `target.startswith("/") and not target.startswith("//")`
     + `request.host_url` tabanlı mutlak-URL karşılaştırması idi).
  4. `app/services/announcement_popup_service.py::_safe_url`
     (admin duyuru CTA linki; eskiden göreli hedefler için aynı zayıf
     `startswith("/")/startswith("//")` kontrolü kullanıyordu).

`tests/security/test_redirect_guard_open_redirect_hardening.py` zaten saf
guard'ı (redirect_guard + route_support) onlarca saldırı deseniyle kapsamlı
biçimde test ediyor; bu dosya onu TEKRARLAMAZ. Amaç, yukarıdaki 4 akışın
GERÇEKTEN o merkezi guard'ı çağırdığını -- kendi başına yeniden
uygulanmış bir kopyasını değil -- kanıtlamaktır.

ÖNEMLİ MİMARİ BULGU (bu turda tespit edildi, davranış bu testler tarafından
üretilmedi): `app/__init__.py`'nin CSRF hata işleyicisi
(`_register_csrf_refresh_handler` içindeki `bys360_b77_handle_csrf_error`),
`create_app()` içinde `app/error_handlers.py::register_error_handlers`'dan
SONRA kaydedilir. Flask'ın `error_handler_spec` sözlüğünde `CSRFError` için
aynı anahtar ikinci kez yazıldığından `app/error_handlers.py::handle_csrf_error`
canlı istekte ARTIK HİÇ ÇAĞRILMAZ (gölgede kalır) -- bu doğrudan
`app.error_handler_spec` sözlüğü incelenerek doğrulanmıştır. Bu; bu turun
ürettiği bir yan etki değil, kod tabanının önceden var olan bir gerçeğidir.
İki dosya da görev kapsamında olduğu için ikisi de düzeltildi ve ayrı ayrı
test edilir: `app/__init__.py`'ninki gerçek bir HTTP round-trip (CSRFError
gerçekten tetiklenerek) ile, `app/error_handlers.py`'ninki ise -- şu an
gölgede olduğu için -- doğrudan fonksiyon çağrısıyla.
"""
from __future__ import annotations

import pytest

CANONICAL_HOST = "trusted.example"
CANONICAL_BASE_URL = f"https://{CANONICAL_HOST}"

# ---------------------------------------------------------------------------
# Ortak saldırı deseni sabitleri (redirect_guard'ın kendi 43 testinin
# TEKRARI değil -- burada amaç "bu akış guard'ı gerçekten çağırıyor mu")
# ---------------------------------------------------------------------------

MALICIOUS_RELATIVE_TARGETS = [
    pytest.param("//evil.example", id="protocol-relative"),
    pytest.param("/\\evil.example", id="slash-backslash-scheme-relative"),
    pytest.param("\\evil.example", id="bare-backslash"),
    pytest.param("%2f%2fevil.example", id="percent-encoded-double-slash"),
    pytest.param("%5cevil.example", id="percent-encoded-backslash"),
    pytest.param("%252f%252fevil.example", id="double-percent-encoded-double-slash"),
]

MALICIOUS_ABSOLUTE_HOST_TARGETS = [
    pytest.param(f"https://{CANONICAL_HOST}.evil.example/", id="subdomain-suffix-trick"),
    pytest.param(f"https://{CANONICAL_HOST}@evil.example/steal", id="userinfo-prefix-trick"),
    pytest.param("https://evil.example/", id="different-host"),
]

MALICIOUS_SCHEME_TARGETS = [
    pytest.param("javascript:alert(1)", id="javascript-scheme"),
    pytest.param("JaVaScript:alert(1)", id="mixed-case-dangerous-scheme"),
    pytest.param("data:text/html,<script>alert(1)</script>", id="data-scheme"),
]

CRLF_TARGETS = [
    pytest.param("/\r\n/evil.example", id="crlf-control-char-obfuscated-protocol-relative"),
]

FAKE_HOST_REDIRECT_TARGETS = MALICIOUS_ABSOLUTE_HOST_TARGETS

# CRLF hedefleri yalnizca hedef DEGERIN dogrudan bir Python string olarak akista
# (DB alani / form alani) tasindigi durumlarda anlamlidir. `Referer` gibi bir
# HTTP basligindan geliyorsa, Werkzeug'un (ve gercek HTTP istemcilerinin)
# kendisi ham CRLF iceren bir baslik degeri KURULMASINA izin vermez (bkz.
# `werkzeug.datastructures.headers._str_header_value`); bu yuzden
# header-tasinan akislar (error_handlers/_safe_csrf_referer_target,
# app/__init__.py'nin CSRF isleyicisi) icin CRLF senaryosu test-araci
# seviyesinde insa edilemez ve listeye DAHIL EDILMEZ. Guard'in kendisi
# (`redirect_guard.py`) CRLF/kontrol karakteri temizlemesini zaten saf
# fonksiyon seviyesinde kapsamli test ediyor
# (`tests/security/test_redirect_guard_open_redirect_hardening.py`).
ALL_MALICIOUS_TARGETS_HEADER_CARRIED = (
    MALICIOUS_RELATIVE_TARGETS + MALICIOUS_ABSOLUTE_HOST_TARGETS + MALICIOUS_SCHEME_TARGETS
)

EMPTY_TARGETS = [
    pytest.param("", id="empty"),
    pytest.param("   ", id="whitespace-only"),
    pytest.param(None, id="none"),
]

POSITIVE_RELATIVE_TARGETS = [
    pytest.param("/", id="root"),
    pytest.param("/dashboard", id="dashboard"),
    pytest.param("/path?x=1", id="path-with-query"),
    pytest.param("/path#section", id="path-with-fragment"),
]

ALL_MALICIOUS_TARGETS = (
    MALICIOUS_RELATIVE_TARGETS
    + MALICIOUS_ABSOLUTE_HOST_TARGETS
    + MALICIOUS_SCHEME_TARGETS
    + CRLF_TARGETS
)


@pytest.fixture
def canonical_app(app, monkeypatch):
    """Testler boyunca kanonik APP_BASE_URL'i deterministik bir değere sabitler.

    `tests/security/test_redirect_guard_open_redirect_hardening.py` içindeki
    `canonical_app` fixture'ı ile aynı desen (paylaşılan session-scope `app`
    fixture'ı, `monkeypatch` ile test başına izole edilmiş config).
    """
    monkeypatch.setitem(app.config, "APP_BASE_URL", CANONICAL_BASE_URL)
    monkeypatch.setitem(app.config, "REDIRECT_ALLOWED_HOSTS", [])
    monkeypatch.setitem(app.config, "TESTING", True)
    return app


# ===========================================================================
# 1) app/error_handlers.py::_safe_csrf_referer_target
# ===========================================================================


def _call_safe_csrf_referer_target(flask_app, referer):
    from app import error_handlers

    headers = {}
    if referer is not None:
        headers["Referer"] = referer
    with flask_app.test_request_context("/some/path", headers=headers):
        return error_handlers._safe_csrf_referer_target()


@pytest.mark.parametrize("target", ALL_MALICIOUS_TARGETS_HEADER_CARRIED)
def test_error_handlers_csrf_referer_target_rejects_malicious_referer(canonical_app, target):
    result = _call_safe_csrf_referer_target(canonical_app, target)
    assert "evil.example" not in result
    assert not result.lower().startswith("javascript:")
    assert not result.lower().startswith("data:")


@pytest.mark.parametrize("target", EMPTY_TARGETS)
def test_error_handlers_csrf_referer_target_falls_back_when_referer_absent(canonical_app, target):
    result = _call_safe_csrf_referer_target(canonical_app, target)
    # Bos/None Referer -> guvenli fallback (main.dashboard/main.login/"/").
    assert result
    assert "evil" not in result


@pytest.mark.parametrize("target", POSITIVE_RELATIVE_TARGETS)
def test_error_handlers_csrf_referer_target_honors_safe_relative_referer(canonical_app, target):
    assert _call_safe_csrf_referer_target(canonical_app, target) == target


def test_error_handlers_csrf_referer_target_honors_canonical_absolute_referer(canonical_app):
    target = f"{CANONICAL_BASE_URL}/settings?tab=security"
    assert _call_safe_csrf_referer_target(canonical_app, target) == target


def test_error_handlers_csrf_referer_target_ignores_forged_host_header(canonical_app):
    """Sahte Host başlığı taşıyan istekte bile karar `request.host_url`'e
    değil kanonik `APP_BASE_URL`'e dayanmalı."""
    from flask import request

    from app import error_handlers

    with canonical_app.test_request_context(
        "/some/path",
        base_url="http://evil.attacker.example",
        headers={"Referer": "http://evil.attacker.example/steal"},
    ):
        assert request.host == "evil.attacker.example"  # sahte Host gercekten set edildi
        result = error_handlers._safe_csrf_referer_target()
        assert "evil.attacker.example" not in result


# ===========================================================================
# 2) app/__init__.py::_bys360_b77_safe_csrf_referrer_target (+ canlı CSRF akışı)
# ===========================================================================


@pytest.mark.parametrize("target", ALL_MALICIOUS_TARGETS)
def test_init_csrf_safe_referrer_target_rejects_malicious(canonical_app, target):
    # Bu test dogrudan fonksiyon cagrisi kullanir (HTTP Referer basligi
    # DEGIL), bu yuzden CRLF varyanti da (ALL_MALICIOUS_TARGETS icindeki)
    # dahil edilebilir -- header-tasima kisiti burada yok.
    import app as app_package

    with canonical_app.app_context():
        assert app_package._bys360_b77_safe_csrf_referrer_target(target) is None


@pytest.mark.parametrize("target", EMPTY_TARGETS)
def test_init_csrf_safe_referrer_target_rejects_empty(canonical_app, target):
    import app as app_package

    with canonical_app.app_context():
        assert app_package._bys360_b77_safe_csrf_referrer_target(target) is None


@pytest.mark.parametrize("target", POSITIVE_RELATIVE_TARGETS)
def test_init_csrf_safe_referrer_target_honors_safe_relative(canonical_app, target):
    import app as app_package

    with canonical_app.app_context():
        assert app_package._bys360_b77_safe_csrf_referrer_target(target) == target


def test_init_csrf_safe_referrer_target_honors_canonical_absolute(canonical_app):
    import app as app_package

    target = f"{CANONICAL_BASE_URL}/settings?tab=security"
    with canonical_app.app_context():
        assert app_package._bys360_b77_safe_csrf_referrer_target(target) == target


def test_init_csrf_handler_live_http_round_trip_rejects_malicious_referrer(canonical_app, monkeypatch):
    """`app/__init__.py`'nin CSRF hata işleyicisi -- gerçekte tetiklenen tek
    işleyici (bkz. modül docstring'i) -- gerçek bir CSRFError üzerinden,
    kötü niyetli bir `Referer` ile açık yönlendirme üretmemeli."""
    monkeypatch.setitem(canonical_app.config, "WTF_CSRF_ENABLED", True)
    client = canonical_app.test_client()
    try:
        response = client.post(
            "/login",
            data={"sicil_or_email": "does-not-matter", "password": "does-not-matter"},
            headers={"Referer": "https://evil.example/steal"},
        )
        assert response.status_code in {301, 302, 303, 307, 308}
        location = response.headers.get("Location", "")
        assert "evil.example" not in location
    finally:
        canonical_app.config["WTF_CSRF_ENABLED"] = False


def test_init_csrf_handler_live_http_round_trip_honors_safe_canonical_referrer(canonical_app, monkeypatch):
    """Pozitif eşlenik: kanonik host'a ait güvenli bir `Referer`, gerçek bir
    CSRFError akışında olduğu gibi onurlandırılmalı."""
    monkeypatch.setitem(canonical_app.config, "WTF_CSRF_ENABLED", True)
    client = canonical_app.test_client()
    target = f"{CANONICAL_BASE_URL}/settings?tab=security"
    try:
        response = client.post(
            "/login",
            data={"sicil_or_email": "does-not-matter", "password": "does-not-matter"},
            headers={"Referer": target},
        )
        assert response.status_code in {301, 302, 303, 307, 308}
        assert response.headers.get("Location") == target
    finally:
        canonical_app.config["WTF_CSRF_ENABLED"] = False


# ===========================================================================
# 3) app/communication/shared.py::_safe_internal_redirect
# ===========================================================================


def _call_safe_internal_redirect(flask_app, target):
    from app.communication import shared as communication_shared

    with flask_app.test_request_context("/notifications"):
        response = communication_shared._safe_internal_redirect(target)
        return response.headers.get("Location", "")


@pytest.mark.parametrize("target", ALL_MALICIOUS_TARGETS)
def test_communication_shared_safe_internal_redirect_rejects_malicious(canonical_app, target):
    location = _call_safe_internal_redirect(canonical_app, target)
    assert "evil.example" not in location
    assert not location.lower().startswith("javascript:")
    assert not location.lower().startswith("data:")


@pytest.mark.parametrize("target", EMPTY_TARGETS)
def test_communication_shared_safe_internal_redirect_falls_back_when_absent(canonical_app, target):
    location = _call_safe_internal_redirect(canonical_app, target)
    assert location  # notifications listesine dusen bir fallback URL'i olmali
    assert "evil" not in location


@pytest.mark.parametrize("target", POSITIVE_RELATIVE_TARGETS)
def test_communication_shared_safe_internal_redirect_honors_safe_relative(canonical_app, target):
    assert _call_safe_internal_redirect(canonical_app, target) == target


def test_communication_shared_safe_internal_redirect_honors_canonical_absolute(canonical_app):
    target = f"{CANONICAL_BASE_URL}/messages/42"
    assert _call_safe_internal_redirect(canonical_app, target) == target


def test_communication_shared_safe_internal_redirect_ignores_forged_host_header(canonical_app):
    """Eski kod `request.host_url` ile karsilastiriyordu; sahte Host
    basligiyla gelen bir istekte bile karti kanonik APP_BASE_URL'e
    dayanmali (istegin kendi host'una degil)."""
    from app.communication import shared as communication_shared

    with canonical_app.test_request_context(
        "/notifications", base_url="http://evil.attacker.example"
    ):
        response = communication_shared._safe_internal_redirect(
            "http://evil.attacker.example/steal"
        )
        location = response.headers.get("Location", "")
        assert "evil.attacker.example" not in location


# ===========================================================================
# 4) app/services/announcement_popup_service.py::_safe_url (admin CTA linki)
# ===========================================================================


def _call_safe_url(flask_app, value, **kwargs):
    from app.services import announcement_popup_service

    with flask_app.app_context():
        return announcement_popup_service._safe_url(value, **kwargs)


@pytest.mark.parametrize(
    "target",
    MALICIOUS_RELATIVE_TARGETS + MALICIOUS_SCHEME_TARGETS + CRLF_TARGETS,
)
def test_announcement_cta_safe_url_rejects_relative_bypass_and_dangerous_schemes(canonical_app, target):
    # allow_relative=True (CTA/cover_image_path varsayilani): backslash/encoded
    # ayrac varyantlari ve tehlikeli semalar reddedilmeli (bos string doner).
    assert _call_safe_url(canonical_app, target, allow_relative=True) == ""


@pytest.mark.parametrize("target", EMPTY_TARGETS)
def test_announcement_cta_safe_url_rejects_empty(canonical_app, target):
    assert _call_safe_url(canonical_app, target, allow_relative=True) == ""


@pytest.mark.parametrize("target", POSITIVE_RELATIVE_TARGETS)
def test_announcement_cta_safe_url_honors_safe_relative(canonical_app, target):
    assert _call_safe_url(canonical_app, target, allow_relative=True) == target


def test_announcement_cta_safe_url_honors_canonical_absolute(canonical_app):
    target = f"{CANONICAL_BASE_URL}/promo"
    assert _call_safe_url(canonical_app, target, allow_relative=True) == target


def test_announcement_cta_safe_url_still_allows_legitimate_external_absolute_link(canonical_app):
    """Regresyon koruması: CTA/medya linki tasarım gereği admin'in KEYFİ bir
    dış https sitesine bağlantı vermesine izin verir (kanonik host'a
    kısıtlanmamıştır) -- bu davranış BİLİNÇLİ olarak değiştirilmedi, yalnızca
    göreli hedef bypass'ı kapatıldı. Bu test, düzeltmenin meşru dış
    bağlantıları kırmadığını kanıtlar."""
    target = "https://egitim-portali.example.org/kurumsal-video"
    assert _call_safe_url(canonical_app, target, allow_relative=True) == target


def test_announcement_cta_safe_url_media_url_absolute_only_branch_unaffected(canonical_app):
    """`allow_relative=False` (media_url dalı) guard'ı hiç çağırmaz; davranış
    değişmedi -- yalnızca şema+netloc denetlenir."""
    target = "https://player.vimeo.com/video/123456789"
    assert _call_safe_url(canonical_app, target, allow_relative=False) == target
    assert _call_safe_url(canonical_app, "/relative/path", allow_relative=False) == ""


def test_announcement_normalize_form_rejects_malicious_cta_relative_bypass(canonical_app):
    from app.services import announcement_popup_service

    with canonical_app.app_context():
        form = {"cta_url": "/\\evil.example", "title": "Duyuru", "body": "Metin"}
        result = announcement_popup_service.normalize_announcement_form(form)
        assert result["cta_url"] is None


def test_announcement_normalize_form_honors_safe_relative_cta(canonical_app):
    """Pozitif: duyuru popup'inin ic yonlendirmesi (CTA) guvenli goreli bir
    hedefi oldugu gibi korumali."""
    from app.services import announcement_popup_service

    with canonical_app.app_context():
        form = {"cta_url": "/dashboard?tab=announcements", "title": "Duyuru", "body": "Metin"}
        result = announcement_popup_service.normalize_announcement_form(form)
        assert result["cta_url"] == "/dashboard?tab=announcements"


# ===========================================================================
# 5) Repo geneli sözleşme: bağımsız (guard'a delege etmeyen) redirect güven
#    kararı kalmadığını statik olarak da doğrular.
# ===========================================================================


def test_no_independent_host_url_redirect_trust_decisions_remain_in_fixed_files():
    """Bu görevin 4 hedef dosyasında artık `request.host_url`/`request.host`
    TABANLI BAĞIMSIZ BİR KOD YOLU (fiili çağrı/karşılaştırma deseni) kalmamalı.

    NOT: Bazı dosyalarda eski (kaldırılan) davranışı açıklayan yorum satırları
    KASITLI olarak `request.host_url` metnini içerir (bkz. değişiklik
    gerekçesi yorumları) -- bu test yalnızca gerçek KOD desenlerini arar,
    yorum/docstring içindeki tarihsel referansları değil.
    """
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]

    forbidden_code_patterns_by_file = {
        repo_root / "app" / "communication" / "shared.py": [
            "urlsplit(request.host_url)",
            'target.startswith("/") and not target.startswith("//")',
        ],
        repo_root / "app" / "services" / "announcement_popup_service.py": [
            'raw.startswith("/") and not raw.startswith("//")',
        ],
        repo_root / "app" / "error_handlers.py": [
            "referer.startswith(host_url)",
            'referer.startswith("/") and not referer.startswith("//")',
        ],
        repo_root / "app" / "__init__.py": [
            'referrer.startswith(host_url) or referrer.startswith("/")',
        ],
    }
    for path, forbidden_patterns in forbidden_code_patterns_by_file.items():
        lines = path.read_text(encoding="utf-8").splitlines()
        code_lines = "\n".join(
            line for line in lines if not line.strip().startswith("#")
        )
        for pattern in forbidden_patterns:
            assert pattern not in code_lines, (
                f"{path} hala bagimsiz bir kod deseni iceriyor: {pattern}"
            )
