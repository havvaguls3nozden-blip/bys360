"""CSP Dalga 5 - Portal post-card partial'ının döngü-güvenli event delegation'a
taşınması: kontrat testi.

BYS360 `app/security/headers.py` uygular:
    script-src: 'self' https:  (unsafe-inline YOK)

Bu dalga, Wave4'ün BİLİNÇLİ OLARAK kapsam dışı bıraktığı tek dosyayı kapsar
(bkz. `tests/security/test_csp_wave4_portal_survey_contract.py` içindeki
`test_post_card_partial_out_of_scope_is_completely_untouched` testinin
docstring'i): `app/templates/portal/_post_card.html`. Bu partial
`{% for item in portal_feed_posts %}{% include 'portal/_post_card.html' %}{% endfor %}`
deseniyle N kez (post başına bir kez) render edilir; bu yüzden partial'ın
İÇİNE hiçbir `<script>` bloğu KONULAMAZ -- aksi halde her render'da
`querySelectorAll` tekrar çalışır ve aynı form/img'e N kez listener bağlanır
(çift/üçlü confirm dialog'u, çift onerror tetiklenmesi gibi fonksiyonel
bug). Dalga 5'in çözümü budur: partial'daki inline `onerror=`/`onsubmit=
confirm(...)` iki tür handler `data-fallback-class`/`data-confirm`
attribute'larına çevrilir; gerçek JS delegasyonu partial'ın DIŞINDA,
`app/static/js/bys360_portal.js` içine SAYFA BAŞINA BİR KEZ yüklenen tek bir
merkezi bloğa eklenir:
    - `document.addEventListener('submit', ...)` (submit bubble eder --
      delegation güvenlidir), confirm iptalinde `event.preventDefault()`.
    - `document.addEventListener('error', ..., true)` (error BUBBLE ETMEZ,
      bu yüzden capture-phase / 3. parametre `true` zorunludur).
Her iki delegated listener da `.closest('[data-portal-post-card]')` ile
YALNIZCA post-card içindeki form/img'lerle sınırlıdır -- feed.html/
profile.html'in KENDİ (post-card dışı) avatar fallback'leri ve diğer
partiallerin (composer, profile-summary-card vb.) `data-fallback-class`
kullanan img'leri bu delegasyonla eşleşmez (onlar zaten kendi özel
`addEventListener('error', ...)` çağrılarına sahiptir, Wave4 kapsamında).

`document.documentElement` üzerindeki `data-bys360-postcard-delegation-bound`
attribute guard'ı, `bys360_portal.js` dosyasının (teorik olarak) birden çok
kez include edilmesi durumunda bile delegasyonun yalnızca BİR KEZ
bağlanmasını garanti eder (idempotent guard).

`<article id="post-{{ post.id }}" ... data-portal-post-card
data-portal-post-id="{{ post.id }}">` her post-card'ı sarmalar; bu,
delegasyonun dayandığı stabil kapsam sınırıdır.

Bu dosyanın sahiplik alanı SADECE testtir -- aşağıdaki üretim dosyalarına
DOKUNMAZ (onlar paralel çalışan başka ajanların işidir):
    - app/templates/portal/_post_card.html
    - app/static/js/bys360_portal.js
    - app/templates/portal/feed.html
    - app/templates/portal/profile.html
    - app/templates/portal/group_detail.html

Not (render testleri için önemli, bkz. Wave4 docstring'i ile aynı desendedir):
bu app `app/template_safety.py` içinde `app.jinja_env.undefined =
ChainableUndefined` ayarlar; context'te sağlanmayan değişkenlere zincirlenmiş
attribute erişimi (`post.wall_owner.full_name` vb.) veya `{% for x in
undefined_var %}` döngüsü hata fırlatmaz (boş döner). `post.attachments`
gibi `is defined` ile korunan alanlar için gerçekçilik adına
`types.SimpleNamespace(all=lambda: [])` stub'ı kullanılır (coordinator
notu): bu, `.all()` çağrısının SimpleNamespace üzerinde patlamasını önler
ve gerçek SQLAlchemy `lazy='dynamic'` ilişkisinin davranışını taklit eder.

Statik testler `tests/security/test_csp_wave1_inline_handlers_contract.py`,
`test_csp_wave2_performance_print_mail_contract.py` ve
`test_csp_wave4_portal_survey_contract.py` ile aynı desendedir
(Path.read_text() + regex, sonra gerçek Jinja motoruyla `render_template()`
çıktı testleri; `app` fixture'ı `tests/conftest.py`'den gelir).

ÖNEMLİ SINIRLAMA: Bu dosyadaki HİÇBİR test gerçek bir tarayıcıda çalışmaz.
`render_template()` yalnızca ÜRETİLEN HTML'i doğrular (inline handler yok,
data-* attribute'ları doğru, script tag'i sayfa başına bir kez). CSP enforce
edilmiş gerçek bir tarayıcıda `submit`/`error` event delegation'ının fiilen
çalıştığını (confirm dialog'unun açılıp iptal edilebildiğini, kırık
görselin fallback class'ını aldığını) KANITLAMAZ -- bu, ayrı bir manuel/E2E
doğrulama gerektirir ve bu dosyanın kapsamı dışındadır.
"""
from __future__ import annotations

import re
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

POST_CARD_TEMPLATE = "app/templates/portal/_post_card.html"
PORTAL_JS = "app/static/js/bys360_portal.js"
FEED_TEMPLATE = "app/templates/portal/feed.html"
PROFILE_TEMPLATE = "app/templates/portal/profile.html"
GROUP_DETAIL_TEMPLATE = "app/templates/portal/group_detail.html"

WAVE5_PARENT_TEMPLATES = [FEED_TEMPLATE, PROFILE_TEMPLATE, GROUP_DETAIL_TEMPLATE]

# HTML attribute syntax: bosluk + on<harfler> + '=' + tirnak. CSS/JS icindeki
# "javascript:" gibi metinsel string literal'leri yanlislikla yakalamaz.
_INLINE_EVENT_ATTR_RE = re.compile(r"""[\s]on[a-zA-Z]+\s*=\s*["']""")
# Kanonik "gercekten tehlikeli javascript: URL" deseni: href/src attribute
# DEGERI olarak kullanilan javascript:. base.html'in kendi savunma kodundaki
# (`.startsWith('javascript:')`) metinsel JS string literal'leri bu regex'e
# TAKILMAZ -- bu bilincli bir tercih (bkz. Wave2/Wave4 docstring'leri, ayni
# ayrimi yaparlar).
_JS_HREF_RE = re.compile(r"""(?:href|src)\s*=\s*["']\s*javascript:""", re.IGNORECASE)
_PORTAL_JS_SCRIPT_SRC_RE = re.compile(r"""<script[^>]*\ssrc="[^"]*bys360_portal\.js[^"]*"[^>]*>""")

DELETE_CONFIRM_MESSAGE_INSTAGRAM = "Bu Instagram kaydı portal akışından kaldırılacak. Devam etmek istiyor musunuz?"
DELETE_CONFIRM_MESSAGE_STANDARD = "Bu paylaşım yayından kaldırılacak. Devam etmek istiyor musunuz?"


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Sahte veri kurucular (types.SimpleNamespace). `_post_card.html` dikkatle
# okunarak hangi alanlara erisildigi tespit edildi (post.*, item.*).
# `post.attachments.all()` gibi cagrilar duz SimpleNamespace'te patlar; bu
# yuzden `attachments` alani `.all()` metoduna sahip bir stub olarak verilir.
# ---------------------------------------------------------------------------


def _fake_user(**overrides: object) -> types.SimpleNamespace:
    base: dict[str, object] = dict(
        id=1,
        profile_photo_url="https://example.invalid/avatar.jpg",
        full_name="Wave5 Proba Kullanici",
        ad="Wave5",
        soyad="Proba",
        email="wave5.proba@example.invalid",
        unvan="Test Unvani",
        birim="Test Birimi",
        is_authenticated=True,
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


def _fake_post(post_id: int, **overrides: object) -> types.SimpleNamespace:
    base: dict[str, object] = dict(
        id=post_id,
        post_type="post",
        attachments=types.SimpleNamespace(all=lambda: []),
        is_pinned=False,
        title=f"Wave5 Test Başlık {post_id}",
        body=f"Wave5 test gövde metni {post_id}",
        published_at=None,
        author=_fake_user(id=post_id + 1000, full_name=f"Yazar {post_id}"),
        author_user_id=post_id + 1000,
        wall_owner=None,
        wall_owner_user_id=None,
        comments_enabled=False,
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


def _fake_item(post_id: int, **overrides: object) -> types.SimpleNamespace:
    base: dict[str, object] = dict(
        post=_fake_post(post_id),
        visibility_label="Herkese Açık",
        post_type_label="Kurumsal Duyuru",
        wall_owner_label=None,
        total_reactions=0,
        comments_count=0,
        saved=False,
        user_reaction=None,
        reaction_counts={},
        can_delete=True,
        recent_comments=[],
        recent_replies={},
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


def _reaction_options() -> list[dict[str, str]]:
    from app.services.portal_service import REACTION_OPTIONS

    return REACTION_OPTIONS


def _feed_context(items: list[types.SimpleNamespace]) -> dict[str, object]:
    return {
        "current_user": _fake_user(),
        "portal_groups": [],
        "portal_feed_posts": items,
        "portal_reaction_options": _reaction_options(),
    }


def _profile_context(items: list[types.SimpleNamespace]) -> dict[str, object]:
    return {
        "portal_profile_user": _fake_user(),
        "current_user": _fake_user(),
        "portal_feed_posts": items,
        "portal_can_post_to_wall": False,
        "portal_reaction_options": _reaction_options(),
    }


def _group_detail_context(items: list[types.SimpleNamespace]) -> dict[str, object]:
    return {
        "portal_group": types.SimpleNamespace(id=1, name="Wave5 Test Grubu", description="Wave5 kontrat testi grubu"),
        "current_user": _fake_user(),
        "portal_feed_posts": items,
        "portal_reaction_options": _reaction_options(),
    }


_PARENT_TEMPLATE_NAME_AND_CONTEXT = {
    FEED_TEMPLATE: ("portal/feed.html", _feed_context),
    PROFILE_TEMPLATE: ("portal/profile.html", _profile_context),
    GROUP_DETAIL_TEMPLATE: ("portal/group_detail.html", _group_detail_context),
}


# ---------------------------------------------------------------------------
# 1) Statik kaynak-kod kontratı: `_post_card.html`
# ---------------------------------------------------------------------------


def test_post_card_partial_source_has_no_inline_event_attributes() -> None:
    """Madde 1: `_post_card.html` kaynağında hiçbir inline event-attribute
    (on*=) yok -- eski satır 46 onerror, satır 153/191 onsubmit=confirm
    tamamen kaldırılmış olmalı."""
    text = _read(POST_CARD_TEMPLATE)
    matches = _INLINE_EVENT_ATTR_RE.findall(text)
    assert not matches, (
        f"{POST_CARD_TEMPLATE} icinde inline event-attribute (on*=) bulundu: {matches!r}. "
        "CSP script-src 'self' https: (unsafe-inline yok) altinda bunlar calismaz."
    )


def test_post_card_partial_source_has_no_script_tag() -> None:
    """Madde 2: `_post_card.html` kaynağında `<script` etiketi YOK (0 adet).
    Bu partial post basina N kez include edildigi icin icine script koymak
    her render'da ayni listener'in tekrar baglanmasina yol acar."""
    text = _read(POST_CARD_TEMPLATE)
    assert text.count("<script") == 0, (
        f"{POST_CARD_TEMPLATE} icinde <script etiketi bulundu; bu partial N kez "
        "include edildigi icin script barindiramaz (coordinator kesin kurali)."
    )


def test_post_card_partial_source_has_fallback_class_and_confirm_attributes() -> None:
    """Madde 3: `_post_card.html` kaynağında `data-fallback-class="is-photo-missing"`
    VE iki `data-confirm="..."` (mesajları birebir) mevcut."""
    text = _read(POST_CARD_TEMPLATE)
    assert 'data-fallback-class="is-photo-missing"' in text
    assert f'data-confirm="{DELETE_CONFIRM_MESSAGE_INSTAGRAM}"' in text, (
        "Instagram silme formunun data-confirm mesaji birebir bulunamadi."
    )
    assert f'data-confirm="{DELETE_CONFIRM_MESSAGE_STANDARD}"' in text, (
        "Standart paylasim silme formunun data-confirm mesaji birebir bulunamadi."
    )
    # Tam olarak iki data-confirm attribute'u bekleniyor (fazla/eksik degil).
    assert text.count('data-confirm="') == 2


def test_post_card_partial_confirm_messages_preserved_verbatim_individually() -> None:
    """Madde 11 (parça a): İki data-confirm mesajı ayrı ayrı, harfiyen
    (Türkçe karakterler dahil) doğrulanır -- birinin yanlışlıkla diğerine
    veya kısaltılmış bir varyanta dönüştürülmediğinden emin olunur."""
    text = _read(POST_CARD_TEMPLATE)
    instagram_form_snippet = (
        "data-confirm=\"Bu Instagram kaydı portal akışından kaldırılacak. "
        "Devam etmek istiyor musunuz?\""
    )
    standard_form_snippet = (
        "data-confirm=\"Bu paylaşım yayından kaldırılacak. "
        "Devam etmek istiyor musunuz?\""
    )
    assert instagram_form_snippet in text
    assert standard_form_snippet in text


# ---------------------------------------------------------------------------
# 2) Statik kaynak-kod kontratı: `bys360_portal.js` delegasyon bloğu
# ---------------------------------------------------------------------------


def test_portal_js_delegation_listeners_registered_exactly_once() -> None:
    """Madde 7: yeni delegasyon bloğundaki `document.addEventListener('submit'`
    ve `document.addEventListener('error'` çağrıları dosyada TAM OLARAK
    birer kez geçer -- ikinci bir kopya çift-listener/çift-confirm bug'ına
    yol açar."""
    text = _read(PORTAL_JS)
    assert text.count("document.addEventListener('submit'") == 1, (
        "document.addEventListener('submit' TAM OLARAK 1 kez beklenir."
    )
    assert text.count("document.addEventListener('error'") == 1, (
        "document.addEventListener('error' TAM OLARAK 1 kez beklenir."
    )


def _extract_submit_delegation_block(text: str) -> str:
    idx = text.index("document.addEventListener('submit'")
    return text[idx : idx + 450]


def _extract_error_delegation_block(text: str) -> str:
    idx = text.index("document.addEventListener('error'")
    return text[idx : idx + 450]


def test_portal_js_delegation_scopes_both_handlers_to_post_card() -> None:
    """Madde 9: hem submit hem error delegasyon bloğu, sadece post-card
    içindeki elementlerle sınırlamak için `.closest('[data-portal-post-card]')`
    (veya eşdeğer güvenli hedef çözümleme) kontrolü içeriyor -- aksi halde
    feed.html/profile.html'in kendi (post-card dışı) avatar/form'larıyla
    yanlışlıkla eşleşip çift davranışa yol açar."""
    text = _read(PORTAL_JS)
    submit_block = _extract_submit_delegation_block(text)
    error_block = _extract_error_delegation_block(text)
    assert ".closest('[data-portal-post-card]')" in submit_block, (
        "submit delegasyon bloğunda [data-portal-post-card] kapsam sınırı bulunamadı."
    )
    assert ".closest('[data-portal-post-card]')" in error_block, (
        "error delegasyon bloğunda [data-portal-post-card] kapsam sınırı bulunamadı."
    )


def test_portal_js_error_delegation_uses_capture_phase() -> None:
    """Madde 10: `error` olayı BUBBLE ETMEZ; bu yüzden delegasyonun capture
    aşamasında (3. parametre `true`) kayıtlı olması ZORUNLUDUR, yoksa
    listener hiçbir zaman tetiklenmez."""
    text = _read(PORTAL_JS)
    error_block = _extract_error_delegation_block(text)
    assert re.search(r",\s*true\s*\)\s*;", error_block), (
        "document.addEventListener('error', ..., true) capture-phase "
        f"kaydı bulunamadı. Bloktan alınan metin: {error_block!r}"
    )


def test_portal_js_submit_delegation_calls_preventdefault_and_window_confirm_on_cancel() -> None:
    """Madde 11 (parça b): confirm iptal edildiğinde `event.preventDefault()`
    çağrıldığını ve `window.confirm(` kullanıldığını doğrular -- aksi halde
    'iptal' formun yine de gönderilmesine yol açar."""
    text = _read(PORTAL_JS)
    submit_block = _extract_submit_delegation_block(text)
    assert "window.confirm(" in submit_block
    assert "event.preventDefault();" in submit_block
    assert "!window.confirm(message)" in submit_block


def test_portal_js_introduces_no_dangerous_js_sinks() -> None:
    """Madde 17: `eval(`, `new Function(`, `document.write(` yasaklı
    sink'lerinden hiçbiri `bys360_portal.js` içine eklenmemiş."""
    text = _read(PORTAL_JS)
    for forbidden in ("eval(", "new Function(", "document.write("):
        assert forbidden not in text, f"{PORTAL_JS} icinde yasakli sink bulundu: {forbidden}"


@pytest.mark.parametrize("relative_path", [POST_CARD_TEMPLATE, PORTAL_JS])
def test_no_inline_handler_attribute_built_as_js_string_literal(relative_path: str) -> None:
    """Madde 16: `_post_card.html` ve `bys360_portal.js` kaynağında bir
    inline handler'ın HTML string'i olarak JS içinde üretilmediğini (yani
    `'onclick='` veya `"onerror="` gibi bir literal yokluğunu) doğrular --
    bu, delegasyonun DOM'a innerHTML/string ile geri sızdırılmadığının
    kanıtıdır."""
    text = _read(relative_path)
    for literal in ("'onclick='", '"onclick="', "'onerror='", '"onerror="'):
        assert literal not in text, f"{relative_path} icinde yasakli JS string literal bulundu: {literal}"


# ---------------------------------------------------------------------------
# 3) Repo-genelinde statik kontrat
# ---------------------------------------------------------------------------


def test_repo_wide_templates_have_zero_javascript_url_hrefs() -> None:
    """Madde 15: `app/templates/**/*.html` genelinde `javascript:` içeren
    href/src attribute değeri sayısı 0. (base.html'in kendi savunma
    kodundaki `.startsWith('javascript:')` gibi metinsel JS string
    literal'leri bu kontrolün kapsamı dışıdır -- bkz. Wave2/Wave4
    docstring'lerindeki aynı ayrım; `_JS_HREF_RE` yalnızca gerçek href/src
    attribute değerlerini yakalar.)"""
    offenders: list[str] = []
    for path in sorted((REPO_ROOT / "app" / "templates").rglob("*.html")):
        text = path.read_text(encoding="utf-8")
        if _JS_HREF_RE.search(text):
            offenders.append(str(path.relative_to(REPO_ROOT)))
    assert offenders == [], f"javascript: href/src bulunan dosyalar: {offenders!r}"


# ---------------------------------------------------------------------------
# 4) Çalışma-zamanı render kontrolü: gerçek Flask app + gerçek Jinja motoru
#    ile `render_template()` çağrısı (bkz. `app` fixture, tests/conftest.py).
# ---------------------------------------------------------------------------


def test_feed_render_with_multiple_posts_produces_matching_post_card_count(app) -> None:
    """Madde 4: feed.html gerçek `render_template()` ile en az 3 sahte post
    içeren context'te render edilebiliyor VE render çıktısında
    `data-portal-post-card` tam post sayısı kadar (3) geçiyor."""
    from flask import render_template

    items = [_fake_item(9001), _fake_item(9002), _fake_item(9003)]
    with app.test_request_context("/"):
        html = render_template("portal/feed.html", **_feed_context(items))

    assert html.count("data-portal-post-card") == 3
    assert not _INLINE_EVENT_ATTR_RE.findall(html)


def test_profile_render_with_multiple_posts_produces_matching_post_card_count(app) -> None:
    """Madde 5: profile.html için aynı çoklu-post render doğrulaması."""
    from flask import render_template

    items = [_fake_item(9101), _fake_item(9102), _fake_item(9103)]
    with app.test_request_context("/"):
        html = render_template("portal/profile.html", **_profile_context(items))

    assert html.count("data-portal-post-card") == 3
    assert not _INLINE_EVENT_ATTR_RE.findall(html)


def test_group_detail_render_with_multiple_posts_produces_matching_post_card_count(app) -> None:
    """Madde 6: group_detail.html için aynı çoklu-post render doğrulaması."""
    from flask import render_template

    items = [_fake_item(9201), _fake_item(9202), _fake_item(9203)]
    with app.test_request_context("/"):
        html = render_template("portal/group_detail.html", **_group_detail_context(items))

    assert html.count("data-portal-post-card") == 3
    assert not _INLINE_EVENT_ATTR_RE.findall(html)


def test_feed_render_with_five_posts_loads_portal_js_script_exactly_once(app) -> None:
    """Madde 8: Duplicate-listener negatif testi. feed.html'i 5 sahte post
    ile render et; render çıktısında `<script src=".../bys360_portal.js"`
    referansı TAM OLARAK 1 kez geçiyor (5 post'a rağmen script tag'i 5 kez
    değil 1 kez render ediliyor) -- bu, partial'ın script İÇERMEDİĞİNİN ve
    script'in yalnız parent'ta 1 kez yüklendiğinin dolaylı kanıtıdır."""
    from flask import render_template

    items = [_fake_item(pid) for pid in (9301, 9302, 9303, 9304, 9305)]
    with app.test_request_context("/"):
        html = render_template("portal/feed.html", **_feed_context(items))

    assert html.count("data-portal-post-card") == 5
    script_matches = _PORTAL_JS_SCRIPT_SRC_RE.findall(html)
    assert len(script_matches) == 1, (
        f"bys360_portal.js script tag'i tam olarak 1 kez beklenir, {len(script_matches)} bulundu: "
        f"{script_matches!r}"
    )


@pytest.mark.parametrize("relative_path", WAVE5_PARENT_TEMPLATES)
def test_parent_page_loads_portal_js_script_exactly_once(app, relative_path: str) -> None:
    """Madde 13: Her 3 parent sayfada (feed/profile/group_detail)
    `bys360_portal.js` script tag'inin render çıktısında TAM OLARAK 1 kez
    geçtiğini doğrular (parent başına en fazla 1 yükleme kontratı)."""
    from flask import render_template

    template_name, context_builder = _PARENT_TEMPLATE_NAME_AND_CONTEXT[relative_path]
    items = [_fake_item(9401), _fake_item(9402), _fake_item(9403)]
    with app.test_request_context("/"):
        html = render_template(template_name, **context_builder(items))

    script_matches = _PORTAL_JS_SCRIPT_SRC_RE.findall(html)
    assert len(script_matches) == 1, (
        f"{relative_path}: bys360_portal.js script tag'i tam olarak 1 kez beklenir, "
        f"{len(script_matches)} bulundu: {script_matches!r}"
    )


def test_feed_render_maps_each_post_id_to_its_own_delete_action(app) -> None:
    """Madde 12: feed.html'i 2 farklı post_id'li (501 ve 502) sahte post ile
    render et; render çıktısında HER İKİ post'un action URL'i
    (`/portal/posts/501/delete` ve `/portal/posts/502/delete`) AYRI AYRI ve
    DOĞRU geçiyor -- "doğru post ID doğru action'a yönlenir" kontratı.
    Her post'un kendi `<article id="post-N">` bloğu içinde YALNIZCA kendi
    action URL'ini içerdiği, komşu post'un URL'ini SIZDIRMADIĞI ayrıca
    doğrulanır (yanlış post-id eşleşmesine karşı katı kontrol)."""
    from flask import render_template

    items = [_fake_item(501), _fake_item(502)]
    with app.test_request_context("/"):
        html = render_template("portal/feed.html", **_feed_context(items))

    assert "/portal/posts/501/delete" in html
    assert "/portal/posts/502/delete" in html

    # Her article-bloğunu kendi post-id'sine gore ayristir ve capraz-sizinti olmadigini dogrula.
    segments = html.split('id="post-')
    segment_501 = next(seg for seg in segments if seg.startswith('501"'))
    segment_502 = next(seg for seg in segments if seg.startswith('502"'))

    assert "/portal/posts/501/delete" in segment_501
    assert "/portal/posts/502/delete" not in segment_501
    assert "/portal/posts/502/delete" in segment_502
    assert "/portal/posts/501/delete" not in segment_502


@pytest.mark.parametrize(
    ("relative_path", "context_builder"),
    [
        (FEED_TEMPLATE, _feed_context),
        (PROFILE_TEMPLATE, _profile_context),
    ],
)
def test_parent_page_still_has_own_avatar_fallback_regression_guard(app, relative_path, context_builder) -> None:
    """Madde 14: feed.html ve profile.html'in KENDİ (post-card dışı, Wave4'te
    eklenen) avatar `data-fallback-class="is-photo-missing"` yapısı ve
    KENDİ per-sayfa fallback script'i (`querySelectorAll('img[data-fallback-class]')`
    bloğu) hâlâ kaynak dosyada mevcut -- Wave5'in `_post_card.html`/
    `bys360_portal.js` değişikliği bu Wave4 deseniyle çakışıp onu
    silmemeli/bozmamalı (regresyon koruması). Hem statik kaynak hem de
    gerçek render çıktısı üzerinden doğrulanır."""
    text = _read(relative_path)
    assert 'data-fallback-class="is-photo-missing"' in text
    assert "querySelectorAll('img[data-fallback-class]')" in text
    assert "addEventListener('error'" in text
    assert "img.remove();" in text

    from flask import render_template

    template_name, _ = _PARENT_TEMPLATE_NAME_AND_CONTEXT[relative_path]
    items = [_fake_item(9501)]
    with app.test_request_context("/"):
        html = render_template(template_name, **context_builder(items))

    assert 'data-fallback-class="is-photo-missing"' in html
    assert "querySelectorAll('img[data-fallback-class]')" in html
