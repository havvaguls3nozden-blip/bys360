"""CSP Dalga 4 - Portal ve Anket Yönetimi ekranları kontrat testi.

BYS360 `app/security/headers.py` uygular:
    script-src: 'self' https:  (unsafe-inline YOK)
`app/security/headers.py::inject_csp_nonce_into_html` response sonrası TÜM
`<script>` etiketlerine otomatik nonce ekler; template'lerde nonce elle
YAZILMAZ (bu dosya da yazmaz).

Bu dosyanın sahiplik alanı yalnızca şu yedi template:
    - app/templates/survey_manage.html               (4 x onsubmit=confirm)
    - app/templates/portal/feed.html                  (1 x onerror avatar)
    - app/templates/portal/people.html                (1 x onerror avatar)
    - app/templates/portal/profile.html               (1 x onerror avatar)
    - app/templates/portal/_experience_v2_hub.html    (1 x onerror avatar, 'is-empty')
    - app/templates/portal/_composer.html             (1 x onerror avatar)
    - app/templates/portal/_profile_summary_card_v2d.html (1 x onerror avatar)

KAPSAM DIŞI (koordinatör bilinçli olarak dışarıda bıraktı):
    - app/templates/portal/_post_card.html
Bu partial `{% for item in portal_feed_posts %}{% include 'portal/_post_card.html' %}{% endfor %}`
şeklinde N kez (post başına bir kez) include edilir. İçine bir `<script>`
bloğu eklemek o script'in N kez render edilmesine, dolayısıyla her
render'ında `querySelectorAll` çalışıp TÜM sayfadaki form/img'lere TEKRAR
TEKRAR listener bağlamasına (çift/üçlü confirm dialog'u veya çift onerror
tetiklenmesi gibi fonksiyonel bug) yol açar. Bu dosya bu riski hem
docstring'de belgeler hem de aşağıda `git diff` ile HEAD'e göre hiçbir
değişiklik yapılmadığını kilitleyen bir test içerir.

Kurulu desenler (bkz. `git diff HEAD -- app/templates/performance/v2_1_4_category_scope.html`
ve `git diff HEAD -- app/templates/performance_mail_reminders.html`):
    onsubmit="return confirm('...')"
        -> data-confirm="..." + querySelectorAll('form[data-confirm]') + submit
           listener + event.preventDefault() iptalde.
    onerror="this.remove(); this.parentElement.classList.add('...')"
        -> img'e data-fallback-class="..." + querySelectorAll('img[data-fallback-class]')
           + DOĞRUDAN addEventListener('error', ...) (delegation değil,
           'error' event bubble etmediği için).

Statik testler `tests/security/test_csp_wave1_inline_handlers_contract.py`
ve `tests/security/test_csp_wave2_performance_print_mail_contract.py` ile
aynı desendedir (Path.read_text() + regex, sonra gerçek Jinja motoruyla
`render_template()` çıktı testleri; `app` fixture'ı `tests/conftest.py`'den
gelir).

Not (render testleri için önemli): bu app `app/template_safety.py` içinde
`app.jinja_env.undefined = ChainableUndefined` ayarlar; bu nedenle
context'te sağlanmayan değişkenlere zincirlenmiş attribute/item erişimi
(`current_user.full_name`, `person.profile_photo_url` vb.) hata fırlatmaz,
sessizce boş/Undefined döner. `render_template()` kwargs'ları Flask'ın
`update_template_context()` davranışı gereği context processor'ların
(ör. flask-login'in enjekte ettiği anonim `current_user`) ÜZERİNE yazar; bu
sayede aşağıdaki testler gerçek login olmadan `current_user`/`portal_people`/
`portal_profile_user` gibi değişkenleri sahte (ama gerçekçi) nesnelerle
doğrudan besleyip üretilen HTML'de `data-fallback-class` değerinin fiilen
img etiketine yazıldığını doğrulayabilir. Render testleri tam sayfa
(base.html dahil) ürettiği için `javascript:` metnini HER YERDE arayan
statik testin aksine, render testleri yalnızca `href=/src="javascript:...`
ve inline `on*=` desenlerini arar -- base.html'in kendi (bu dalganın
kapsamı dışındaki) savunma kodu link href'lerini `.startsWith('javascript:')`
ile filtrelediği için ham "javascript:" metni sayfanın başka yerlerinde
zararsızca geçebilir (bkz. Wave2 dashboard render testi de aynı ayrımı
yapar: yalnızca `_JS_HREF_RE`, `_JS_URL_ANYWHERE_RE` DEĞİL).
"""
from __future__ import annotations

import re
import subprocess
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

SURVEY_MANAGE_TEMPLATE = "app/templates/survey_manage.html"
PORTAL_FEED_TEMPLATE = "app/templates/portal/feed.html"
PORTAL_PEOPLE_TEMPLATE = "app/templates/portal/people.html"
PORTAL_PROFILE_TEMPLATE = "app/templates/portal/profile.html"
PORTAL_EXPERIENCE_V2_HUB_TEMPLATE = "app/templates/portal/_experience_v2_hub.html"
PORTAL_COMPOSER_TEMPLATE = "app/templates/portal/_composer.html"
PORTAL_PROFILE_SUMMARY_CARD_TEMPLATE = "app/templates/portal/_profile_summary_card_v2d.html"

# KAPSAM DIŞI - dokunulmadı, yalnızca git-diff kilidi için referans edilir.
PORTAL_POST_CARD_TEMPLATE = "app/templates/portal/_post_card.html"

WAVE4_OWNED_FILES = [
    SURVEY_MANAGE_TEMPLATE,
    PORTAL_FEED_TEMPLATE,
    PORTAL_PEOPLE_TEMPLATE,
    PORTAL_PROFILE_TEMPLATE,
    PORTAL_EXPERIENCE_V2_HUB_TEMPLATE,
    PORTAL_COMPOSER_TEMPLATE,
    PORTAL_PROFILE_SUMMARY_CARD_TEMPLATE,
]

# onerror avatar-fallback desenini kullanan altı portal dosyası (survey_manage.html hariç).
WAVE4_PHOTO_FALLBACK_FILES = [
    PORTAL_FEED_TEMPLATE,
    PORTAL_PEOPLE_TEMPLATE,
    PORTAL_PROFILE_TEMPLATE,
    PORTAL_EXPERIENCE_V2_HUB_TEMPLATE,
    PORTAL_COMPOSER_TEMPLATE,
    PORTAL_PROFILE_SUMMARY_CARD_TEMPLATE,
]

# 'is-photo-missing' fallback class'ını kullanan beş dosya (_experience_v2_hub.html hariç,
# o 'is-empty' kullanır -- koordinatörün talimatındaki bilinçli isim farkı).
WAVE4_IS_PHOTO_MISSING_FILES = [
    PORTAL_FEED_TEMPLATE,
    PORTAL_PEOPLE_TEMPLATE,
    PORTAL_PROFILE_TEMPLATE,
    PORTAL_COMPOSER_TEMPLATE,
    PORTAL_PROFILE_SUMMARY_CARD_TEMPLATE,
]

SURVEY_MANAGE_CONFIRM_MESSAGES = [
    "Seçili anketler kalıcı olarak silinecek. Devam edilsin mi?",
    "Seçili anketler ve tüm yanıtları kalıcı olarak silinecek. Bu işlem geri alınamaz. Devam edilsin mi?",
    "Bu anket kalıcı olarak silinecek. Devam edilsin mi?",
    "Bu anket ve tüm yanıtları kalıcı olarak silinecek. Bu işlem geri alınamaz. Devam edilsin mi?",
]

# HTML attribute syntax: bosluk + on<harfler> + '=' + tirnak. CSS/JS icindeki
# "javascript:" gibi metinsel string literal'leri yanlislikla yakalamaz.
_INLINE_EVENT_ATTR_RE = re.compile(r"""[\s]on[a-zA-Z]+\s*=\s*["']""")
_JS_HREF_RE = re.compile(r"""(?:href|src)\s*=\s*["']\s*javascript:""", re.IGNORECASE)
_JS_URL_ANYWHERE_RE = re.compile(r"""javascript:""", re.IGNORECASE)


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1) Statik kaynak-kod kontratı (Path.read_text + regex, tarayıcı çalışma
#    zamanı davranışını kanıtlamaz). Jinja if-bloklarının arkasına gizlenmiş
#    kod da dahil kayıtsız şartsız taranır.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative_path", WAVE4_OWNED_FILES)
def test_wave4_file_has_no_inline_event_attributes(relative_path: str) -> None:
    text = _read(relative_path)
    matches = _INLINE_EVENT_ATTR_RE.findall(text)
    assert not matches, (
        f"{relative_path} icinde inline event-attribute (on*=) bulundu: {matches!r}. "
        "CSP script-src 'self' https: (unsafe-inline yok) altinda bunlar calismaz; "
        "data-* attribute + addEventListener kalibina cevrilmeli."
    )


@pytest.mark.parametrize("relative_path", WAVE4_OWNED_FILES)
def test_wave4_file_has_no_javascript_url(relative_path: str) -> None:
    text = _read(relative_path)
    assert not _JS_HREF_RE.search(text), (
        f"{relative_path} icinde href/src=\"javascript:...\" bulundu."
    )
    assert not _JS_URL_ANYWHERE_RE.search(text), (
        f"{relative_path} icinde beklenmedik bir javascript: metni bulundu."
    )


@pytest.mark.parametrize("relative_path", WAVE4_OWNED_FILES)
def test_wave4_file_introduces_no_dangerous_js_sinks(relative_path: str) -> None:
    """Duzeltme sirasinda eval/new Function/document.write eklenmedigini dogrular."""
    text = _read(relative_path)
    for forbidden in ("eval(", "new Function(", "document.write("):
        assert forbidden not in text, f"{relative_path} icinde yasakli sink bulundu: {forbidden}"


@pytest.mark.parametrize("relative_path", WAVE4_OWNED_FILES)
def test_wave4_file_does_not_duplicate_the_same_listener_twice(relative_path: str) -> None:
    """Her dosyada 'form[data-confirm]' veya 'img[data-fallback-class]'
    delegasyonunun EN FAZLA bir kez tanimlandigini dogrular -- ayni
    listener'in iki kez baglanmasi (KESIN YASAKLAR listesindeki madde)
    cift tetiklenmeye yol acar."""
    text = _read(relative_path)
    assert text.count("querySelectorAll('form[data-confirm]')") <= 1
    assert text.count("querySelectorAll('img[data-fallback-class]')") <= 1


def test_survey_manage_onsubmit_removed_and_four_confirm_messages_preserved_verbatim() -> None:
    """Koordinatorun envanteri: survey_manage.html'de 4 adet onsubmit=confirm
    formu vardi (2 toplu + 2 tekil, force-delete cifti KALICI/geri alinamaz
    islemler). Bu test hepsinin data-confirm karsiliginin, MESAJ METNI
    HARFIYEN korunarak, mevcut oldugunu tek tek dogrular."""
    text = _read(SURVEY_MANAGE_TEMPLATE)
    assert "onsubmit=" not in text
    assert 'id="surveyBulkDeleteForm"' in text
    assert 'id="surveyBulkForceDeleteForm"' in text

    for message in SURVEY_MANAGE_CONFIRM_MESSAGES:
        assert f'data-confirm="{message}"' in text, f"beklenen data-confirm bulunamadi: {message!r}"
    # Tam olarak 4 data-confirm attribute'u olmali (fazla/eksik degil).
    assert text.count('data-confirm="') == 4

    assert "querySelectorAll('form[data-confirm]')" in text
    assert "addEventListener('submit'" in text


def test_survey_manage_confirm_delegation_calls_preventdefault_on_cancel() -> None:
    """Confirm iptal edildiginde submit'in varsayilan davranisinin
    engellendigini (event.preventDefault) kaynak seviyesinde dogrular --
    aksi halde 'iptal' formun yine de gonderilmesine yol acar (KESIN
    YASAKLAR: form submit/confirm davranisini bozma)."""
    text = _read(SURVEY_MANAGE_TEMPLATE)
    assert "if (message && !window.confirm(message))" in text
    assert "event.preventDefault();" in text


def test_survey_manage_phase1_js_untouched_and_no_conflict() -> None:
    """survey_manage.html zaten static/js/survey_manage_phase1.js yukluyor;
    bu dosyaya DOKUNULMADI ve o dosya form[data-confirm] ile cakismiyor
    (yalniz #surveySmartFilterMount ozet panelini olusturuyor)."""
    js_path = REPO_ROOT / "app/static/js/survey_manage_phase1.js"
    text = js_path.read_text(encoding="utf-8")
    assert "data-confirm" not in text
    assert "confirm(" not in text
    result = subprocess.run(
        ["git", "diff", "--exit-code", "--", "app/static/js/survey_manage_phase1.js"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"app/static/js/survey_manage_phase1.js HEAD'e gore degismis (bu dosyaya "
        f"dokunulmamaliydi):\n{result.stdout}"
    )


@pytest.mark.parametrize("relative_path", WAVE4_PHOTO_FALLBACK_FILES)
def test_wave4_photo_fallback_file_has_data_fallback_class_and_error_listener(relative_path: str) -> None:
    text = _read(relative_path)
    assert "onerror=" not in text
    assert 'data-fallback-class="' in text
    assert "querySelectorAll('img[data-fallback-class]')" in text
    # 'error' olayi bubble ETMEZ; delegation yerine dogrudan addEventListener kullanilmali.
    assert "addEventListener('error'" in text
    assert "img.remove();" in text
    assert "img.getAttribute('data-fallback-class')" in text


@pytest.mark.parametrize("relative_path", WAVE4_IS_PHOTO_MISSING_FILES)
def test_wave4_five_files_use_is_photo_missing_fallback_class_verbatim(relative_path: str) -> None:
    text = _read(relative_path)
    assert 'data-fallback-class="is-photo-missing"' in text
    assert 'data-fallback-class="is-empty"' not in text


def test_wave4_experience_v2_hub_uses_is_empty_fallback_class_verbatim() -> None:
    """Koordinatorun talimatindaki bilincli istisna: bu dosyada class adi
    'is-empty' (digerlerinde 'is-photo-missing'); birebir korunmali."""
    text = _read(PORTAL_EXPERIENCE_V2_HUB_TEMPLATE)
    assert 'data-fallback-class="is-empty"' in text
    assert 'data-fallback-class="is-photo-missing"' not in text


def test_post_card_partial_has_no_inline_script_tag() -> None:
    """KRITIK KAPSAM SINIRI (Dalga 4 -> Dalga 5 guncellemesi):
    app/templates/portal/_post_card.html Dalga 4'te bilincli olarak KAPSAM
    DISI birakilmisti (bu test o zaman dosyanin HEAD'e gore hic degismedigini
    kilitliyordu) cunku post basina bir kez (N kez) include edilir; icine
    <script> eklemek her render'da querySelectorAll'in TUM sayfadaki
    form/img'lere TEKRAR listener baglamasina (cift/uclu confirm dialog'u,
    cift onerror tetiklenmesi gibi fonksiyonel bug) yol acardi.

    Dalga 5 bu partial'i DEGISTIRDI (kasitli, kapsam dahilinde): 3 inline
    event-attribute'u data-* sozlesmesine cevirdi ve listener'i partial
    DISINA, app/static/js/bys360_portal.js icindeki tek merkezi, dongu-guvenli
    delegasyona tasidi (bkz. tests/security/test_csp_wave5_portal_postcard_delegation_contract.py).
    Bu yuzden artik "hic degismedi" degil, "hala <script> icermiyor ve inline
    handler icermiyor" invaryanti dogru kontrattir -- partial'in kendisi asla
    script tasimamali, degismis olmasi sorun degil."""
    text = _read(PORTAL_POST_CARD_TEMPLATE)
    assert "<script" not in text, (
        f"{PORTAL_POST_CARD_TEMPLATE} icinde <script> etiketi bulundu -- "
        "bu partial N kez render edildigi icin script icermemeli."
    )
    assert not _INLINE_EVENT_ATTR_RE.findall(text), (
        f"{PORTAL_POST_CARD_TEMPLATE} icinde inline event-attribute bulundu."
    )


def test_post_card_partial_still_included_in_a_for_loop_as_expected() -> None:
    """Yukaridaki 'dokunulmadi' testinin anlamli olmasi icin, bu partial'in
    hala coordinatorun tarif ettigi N-kez-include deseninde kullanildigini
    (feed.html ve profile.html icinde) dogrular -- yoksa risk senaryosu
    artik gecerli olmayabilir ve test sessizce anlamsizlasabilir."""
    for owner_template in (PORTAL_FEED_TEMPLATE, PORTAL_PROFILE_TEMPLATE):
        text = _read(owner_template)
        assert "{% for item in portal_feed_posts %}{% include 'portal/_post_card.html' %}{% endfor %}" in text


# ---------------------------------------------------------------------------
# 2) Calisma-zamani render kontrolu: gercek Flask app + gercek Jinja motoru
#    ile `render_template()` cagrisi (bkz. `app` fixture, tests/conftest.py).
#    Bu yedi template login_required/menu_key_required arkasindaki route'lar
#    tarafindan doldurulur; route'un tam auth+menu-key+rol-matrisi+DB
#    zincirini burada yeniden kurmak bu kontratin kapsamini asar (ayrica
#    `app/route_support.py::menu_key_required` artik admin bypass'i
#    ICERMIYOR, canli rol matrisine bagli -- bkz. BYS360_SETTINGS_LIVE_AUTHORITY_V2).
#    Bunun yerine template'ler dogrudan `render_template()` ile, route'un
#    ureteceği context'e denk gelen GERCEKCI (ama sahte) degerlerle render
#    edilir. Bu app `ChainableUndefined` kullandigi icin saglanmayan
#    degiskenlere guvenli sekilde bos deger dondurur (yukaridaki modul
#    docstring'inde detaylandirilmistir); asagidaki context'ler yalnizca
#    onerror/onsubmit degisikliklerinin GERCEKTEN gorunur oldugunu (avatar
#    img'i data-fallback-class ile render edildigini, confirm formlarinin
#    data-confirm ile render edildigini) kanitlamak icin saglanir. Bu HALA
#    gercek bir tarayici testi DEGILDIR: CSP enforce edilmis bir tarayicida
#    script'lerin fiilen calistigini kanitlamaz.
# ---------------------------------------------------------------------------


def _fake_user(**overrides):
    base = dict(
        id=1,
        profile_photo_url="https://example.invalid/avatar.jpg",
        full_name="Wave4 Proba Kullanici",
        ad="Wave4",
        soyad="Proba",
        email="wave4.proba@example.invalid",
        unvan="Test Unvani",
        birim="Test Birimi",
        ust_birim=None,
        sicil_no="90001",
        role_label="Kullanici",
        role="personel",
        is_authenticated=True,
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


def _fake_survey_row(**overrides):
    survey_defaults = dict(
        id=101,
        title="Wave4 Test Anketi",
        description="Wave4 kontrat testi icin sahte anket.",
        survey_type="genel",
        status="draft",
        start_at=None,
        end_at=None,
        created_by=None,
    )
    survey_defaults.update(overrides.pop("survey", {}))
    row = {
        "survey": types.SimpleNamespace(**survey_defaults),
        "state_label": "Taslak",
        "question_count": 3,
        "assignment_count": 10,
        "response_count": 2,
        "response_rate": 20,
    }
    row.update(overrides)
    return row


def _assert_no_inline_handlers_or_js_href(html: str, label: str) -> None:
    assert not _INLINE_EVENT_ATTR_RE.findall(html), (
        f"{label} gercek render ciktisinda inline event-attribute bulundu."
    )
    assert not _JS_HREF_RE.search(html), (
        f"{label} gercek render ciktisinda javascript: href/src bulundu."
    )
    for forbidden in ("eval(", "new Function(", "document.write("):
        assert forbidden not in html, f"{label} render ciktisinda yasakli sink bulundu: {forbidden}"


def test_survey_manage_render_has_no_inline_handlers_and_confirm_messages_intact(app) -> None:
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template(
            "survey_manage.html",
            rows=[_fake_survey_row()],
            current_status="all",
        )

    _assert_no_inline_handlers_or_js_href(html, "survey_manage.html")

    for message in SURVEY_MANAGE_CONFIRM_MESSAGES:
        assert f'data-confirm="{message}"' in html, f"render ciktisinda data-confirm bulunamadi: {message!r}"
    assert 'id="surveyBulkDeleteForm"' in html
    assert 'id="surveyBulkForceDeleteForm"' in html


@pytest.mark.parametrize(
    ("template_name", "context_builder", "expected_fallback_class"),
    [
        (
            "portal/feed.html",
            lambda: {"current_user": _fake_user(), "portal_groups": []},
            "is-photo-missing",
        ),
        (
            "portal/people.html",
            lambda: {
                "portal_people": [_fake_user(id=2, profile_photo_url="https://example.invalid/person.jpg")],
                "portal_people_query": "",
            },
            "is-photo-missing",
        ),
        (
            "portal/profile.html",
            lambda: {
                "portal_profile_user": _fake_user(),
                "current_user": _fake_user(),
                "portal_feed_posts": [],
                "portal_can_post_to_wall": False,
            },
            "is-photo-missing",
        ),
        (
            "portal/_experience_v2_hub.html",
            lambda: {
                "current_user": _fake_user(),
                "portal_v2": {"profile": {"photo_url": "https://example.invalid/hub.jpg"}},
            },
            "is-empty",
        ),
        (
            "portal/_composer.html",
            lambda: {"current_user": _fake_user()},
            "is-photo-missing",
        ),
        (
            "portal/_profile_summary_card_v2d.html",
            lambda: {"portal_card_user": _fake_user(), "current_user": _fake_user()},
            "is-photo-missing",
        ),
    ],
)
def test_wave4_photo_fallback_render_shows_data_fallback_class_not_onerror(
    app, template_name: str, context_builder, expected_fallback_class: str
) -> None:
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template(template_name, **context_builder())

    _assert_no_inline_handlers_or_js_href(html, template_name)
    assert "onerror=" not in html
    assert f'data-fallback-class="{expected_fallback_class}"' in html
    assert "querySelectorAll('img[data-fallback-class]')" in html
