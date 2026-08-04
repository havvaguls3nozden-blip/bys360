"""CSP Dalga 7 - Destek "Yardım Merkezi" rehber ekranları kontrat testi.

BYS360 `app/security/headers.py` uygular:
    script-src: 'self' https:  (unsafe-inline YOK)

`app/security/headers.py::inject_csp_nonce_into_html` yanıt döndürdükten
sonra TÜM `<script>` etiketlerine (nonce'u olmayanlara) otomatik
`nonce="..."` ekler; bu merkezi mekanizma sayesinde template içindeki
`<script>...</script>` blokları (ve harici `<script src=...>` etiketleri)
zaten CSP ile uyumludur ve nonce hiçbir zaman elle template'e yazılmaz.
Asıl risk inline EVENT ATTRIBUTE'lardı (`onclick=`, `onsubmit=` vb.) --
bunlara nonce uygulanmaz ve enforce modda tarayıcı tarafından
çalıştırılmazlar.

Bu dosyanın sahiplik alanı yalnızca şu iki template (toplam 2 handler):
    - app/templates/support/help_admin_list.html  (1 handler: onsubmit ->
      confirm())
    - app/templates/support/help_article.html      (1 handler: onclick ->
      window.print())

ÇÖZÜM (help_admin_list.html): Bu template `base.html`'i extend eder, kendi
`<script>` bloğuna sahip değildi (yalnızca harici
`js/faz4_support_account_mobile.js` referansı vardı). O statik JS dosyası
(`app/static/js/faz4_support_account_mobile.js`) okunup incelendi -- içinde
`form[data-confirm]` veya benzer bir submit-delegasyon deseni YOK (yalnızca
mobil tablo-kart dönüşümü ve anket "eksik soruya atla" mantığı içeriyor,
konusu tamamen farklı). Bu yüzden o dosyaya DOKUNULMADI. Silme formundaki
`onsubmit="return confirm('Bu makaleyi silmek istediğinize emin
misiniz?');"` kurulu Dalga 1-6 desenine göre
`data-confirm="Bu makaleyi silmek istediğinize emin misiniz?"` +
`{% block content %}` içinde `{% endblock %}`'tan hemen önce (mevcut
`<script src=".../faz4_support_account_mobile.js">` etiketinden SONRA)
eklenen YENİ tek bir `<script>` bloğundaki standart `form[data-confirm]`
submit-delegasyonuna çevrildi. `class="inline"` attribute'una ve CSRF
hidden input'a DOKUNULMADI. Form `{% for article in articles %}...
{% endfor %}` döngüsü içinde olsa da delegasyon script'i döngü DIŞINDA,
sayfa başına bir kez render edilir; bu yüzden N satır için de tek
delegasyon yeterlidir (aynı mimari `weights.html` / Dalga 6, bkz.
`test_csp_wave6_criteria_weights_contract.py`).

ÇÖZÜM (help_article.html): Bu template de `base.html`'i extend eder, kendi
`<script>` bloğuna sahip değildi (yalnızca harici
`js/bys360_support_learning.js` referansı vardı). O statik JS dosyası
incelendi: zaten `data-copy-support-link` attribute'lu butonu
`document.querySelector('[data-copy-support-link]')` ile bulup
`addEventListener('click', ...)` bağlayan, `DOMContentLoaded` içinde
çağrılan küçük fonksiyonlardan oluşan bir "her özellik kendi fonksiyonu"
konvansiyonuna sahip (bkz. `copyArticleLink()`, `smoothAnchors()`, ikisi de
`document.addEventListener('DOMContentLoaded', function(){...})` içinde
çağrılıyor). "Yazdır" butonu bu MEVCUT dosyanın konvansiyonuna tam uyuyor
(aynı dosyada zaten id/attribute tabanlı, `DOMContentLoaded`'da bağlanan bir
buton kalıbı var) -- bu yüzden yeni bir template-içi `<script>` bloğu AÇMAK
yerine AYNI `bys360_support_learning.js` dosyasına üçüncü bir fonksiyon
(`bindArticlePrint()`) eklenip mevcut `DOMContentLoaded` çağrısına dahil
edildi. Template tarafında yalnızca
`onclick="window.print()"` kaldırılıp `id="helpArticlePrintBtn"` eklendi;
`type="button"` ve `data-copy-support-link` butonuna hiç dokunulmadı.

ÖNEMLİ: `app/static/js/bys360_support_learning.js` bu dalgada DEĞİŞTİRİLDİ
(statik JS dosyasına dokunuldu) -- gerekçe yukarıda açıklanmıştır: bu
dosyanın kendi yerleşik konvansiyonu (id/attribute + DOMContentLoaded'da
bağlanan küçük fonksiyonlar) yeni "Yazdır" davranışı için şablon-içi bir
script bloğu açmaktan daha tutarlı bir ev. `app/static/js/
faz4_support_account_mobile.js` dosyasına ise DOKUNULMADI (help_admin_list.
html için yeni delegasyon şablon içinde yerel bir `<script>` bloğuna
eklendi, çünkü o JS dosyasının konusu -- mobil tablo/kart dönüşümü --
form-confirm delegasyonuyla ilgisizdir).

Statik testler `tests/security/test_csp_wave6_criteria_weights_contract.py`
ve `tests/security/test_csp_wave6_pdf_print_contract.py` ile aynı desendedir
(Path.read_text() + regex, sonra gerçek Jinja motoruyla `render_template()`
çıktı testleri; `app` fixture'ı `tests/conftest.py`'den gelir).

ÖNEMLİ SINIRLAMA: Bu dosyadaki HİÇBİR test gerçek bir tarayıcıda
çalışmadı/çalıştırılmadı. `render_template()` yalnızca ÜRETİLEN HTML'i
doğrular (inline handler yok, data-*/id attribute'ları doğru, script
bloğu/harici script referansı sayfa başına doğru sayıda render ediliyor).
CSP enforce edilmiş gerçek bir tarayıcıda "Sil" butonunun confirm()
diyaloğunu fiilen açıp iptal edilebildiğini veya "Yazdır" butonunun
`window.print()`'i fiilen tetiklediğini KANITLAMAZ -- bu, ayrı bir
manuel/E2E doğrulama gerektirir ve bu dosyanın kapsamı dışındadır.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

HELP_ADMIN_LIST_TEMPLATE = "app/templates/support/help_admin_list.html"
HELP_ARTICLE_TEMPLATE = "app/templates/support/help_article.html"
FAZ4_SUPPORT_ACCOUNT_MOBILE_JS = "app/static/js/faz4_support_account_mobile.js"
SUPPORT_LEARNING_JS = "app/static/js/bys360_support_learning.js"
BASE_TEMPLATE = "app/templates/base.html"

WAVE7_FILES = [HELP_ADMIN_LIST_TEMPLATE, HELP_ARTICLE_TEMPLATE]

DELETE_CONFIRM_MESSAGE = "Bu makaleyi silmek istediğinize emin misiniz?"

# HTML attribute syntax: bosluk + on<harfler> + '=' + tirnak. CSS/JS icindeki
# "javascript:" gibi metinsel string literal'leri yanlislikla yakalamaz.
_INLINE_EVENT_ATTR_RE = re.compile(r"""[\s]on[a-zA-Z]+\s*=\s*["']""")
_JS_HREF_RE = re.compile(r"""(?:href|src)\s*=\s*["']\s*javascript:""", re.IGNORECASE)
_JS_URL_ANYWHERE_RE = re.compile(r"""javascript:""", re.IGNORECASE)

_FORBIDDEN_JS_SINKS = ("eval(", "new Function(", "document.write(")


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _fake_article_row(item_id: int, **overrides: object) -> dict[str, object]:
    base: dict[str, object] = dict(
        id=item_id,
        title=f"Wave7 Test Rehberi {item_id}",
        slug=f"wave7-test-rehberi-{item_id}",
        summary=f"Wave7 kontrat test özeti {item_id}",
        category_slug="genel",
        is_published=True,
        source_type="manual",
    )
    base.update(overrides)
    return base


def _fake_article_detail(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = dict(
        title="Wave7 Test Rehber Detayı",
        summary="Wave7 kontrat test rehber özeti.",
        category={"icon": "fa-solid fa-book-open", "title": "Genel"},
        roles=[{"icon": "fa-solid fa-user", "title": "Personel"}],
        tags=["wave7", "kontrat"],
        sections=[
            {"title": "Giriş", "body": "Bu bölüm giriş metnidir.", "bullet_items": ["Madde 1", "Madde 2"]},
        ],
        related_articles=[{"slug": "ilgili-rehber", "title": "İlgili Rehber"}],
    )
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# 1) Statik kaynak-kod kontratı (Path.read_text + regex). Kosulsuz calisir,
#    Jinja if-bloklarinin arkasinda kalan durumlari da yakalar.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative_path", WAVE7_FILES)
def test_wave7_file_has_no_inline_event_attributes(relative_path: str) -> None:
    text = _read(relative_path)
    matches = _INLINE_EVENT_ATTR_RE.findall(text)
    assert not matches, (
        f"{relative_path} icinde inline event-attribute (on*=) bulundu: {matches!r}. "
        "CSP script-src 'self' https: (unsafe-inline yok) altinda bunlar calismaz."
    )


@pytest.mark.parametrize("relative_path", WAVE7_FILES)
def test_wave7_file_has_no_javascript_href_or_url(relative_path: str) -> None:
    text = _read(relative_path)
    assert not _JS_HREF_RE.search(text), f"{relative_path} icinde href/src=\"javascript:...\" bulundu."
    assert not _JS_URL_ANYWHERE_RE.search(text), f"{relative_path} icinde beklenmedik bir javascript: metni bulundu."


@pytest.mark.parametrize("relative_path", WAVE7_FILES)
def test_wave7_file_introduces_no_dangerous_js_sinks(relative_path: str) -> None:
    """Duzeltme sirasinda eval/new Function/document.write eklenmedigini dogrular."""
    text = _read(relative_path)
    for forbidden in _FORBIDDEN_JS_SINKS:
        assert forbidden not in text, f"{relative_path} icinde yasakli sink bulundu: {forbidden}"


@pytest.mark.parametrize("relative_path", WAVE7_FILES)
def test_wave7_file_has_no_forbidden_inline_handler_string_literal(relative_path: str) -> None:
    """Bir inline handler'in HTML string'i olarak JS icinde uretilmedigini
    (yani `'onclick='`/`"onsubmit="` gibi bir literal yoklugunu) dogrular --
    bu, delegasyonun DOM'a innerHTML/string ile geri sizdirilmadiginin
    kanitidir."""
    text = _read(relative_path)
    for literal in ("'onclick='", '"onclick="', "'onsubmit='", '"onsubmit="'):
        assert literal not in text, f"{relative_path} icinde yasakli JS string literal bulundu: {literal}"


def test_help_admin_list_delete_form_has_data_confirm_message_verbatim() -> None:
    text = _read(HELP_ADMIN_LIST_TEMPLATE)
    assert "onsubmit=" not in text
    assert f'data-confirm="{DELETE_CONFIRM_MESSAGE}"' in text
    assert text.count('data-confirm="') == 1


def test_help_admin_list_delete_form_class_inline_preserved() -> None:
    """class="inline" attribute'unun silme formunda hala oldugunu dogrular
    (koordinator talimati: bu attribute'a dokunma)."""
    text = _read(HELP_ADMIN_LIST_TEMPLATE)
    assert (
        "action=\"{{ url_for('main.support_help_admin_delete', article_id=article.id) }}\" "
        'class="inline" data-confirm="' + DELETE_CONFIRM_MESSAGE + '"'
    ) in text


def test_help_admin_list_csrf_hidden_input_untouched() -> None:
    """4 CSRF hidden input bekleniyor: ilk-yükleme formu, hazır-rehberleri-
    güncelle formu, döngü içindeki yayınla/taslağa-al formu ve döngü
    içindeki silme formu -- hiçbiri kaldırılmadı/bozulmadı."""
    text = _read(HELP_ADMIN_LIST_TEMPLATE)
    assert text.count('<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">') == 4


def test_help_admin_list_has_exactly_one_new_script_block_with_form_confirm_delegation() -> None:
    text = _read(HELP_ADMIN_LIST_TEMPLATE)
    assert text.count("<script") == 2  # 1 harici src="...faz4_support_account_mobile.js" + 1 yeni yerel blok
    assert text.count("querySelectorAll('form[data-confirm]')") == 1
    assert "if (message && !window.confirm(message))" in text
    assert "event.preventDefault();" in text


def test_help_admin_list_external_script_reference_untouched() -> None:
    text = _read(HELP_ADMIN_LIST_TEMPLATE)
    assert (
        '<script src="{{ url_for(\'static\', filename=\'js/faz4_support_account_mobile.js\') }}"></script>'
        in text
    )


def test_help_article_print_button_uses_id_not_onclick() -> None:
    text = _read(HELP_ARTICLE_TEMPLATE)
    assert "onclick=" not in text
    assert 'id="helpArticlePrintBtn"' in text
    assert text.count('id="helpArticlePrintBtn"') == 1


def test_help_article_print_button_keeps_type_button() -> None:
    text = _read(HELP_ARTICLE_TEMPLATE)
    assert '<button class="support-btn-soft" type="button" id="helpArticlePrintBtn">' in text


def test_help_article_copy_link_button_untouched_regression() -> None:
    """`data-copy-support-link` butonu (mevcut, bu dalganin kapsami disi)
    hic degismedi -- ne attribute'u ne de konumu."""
    text = _read(HELP_ARTICLE_TEMPLATE)
    assert (
        '<button class="support-btn-soft" type="button" data-copy-support-link>'
        '<i class="fa-solid fa-link"></i> Bağlantıyı Kopyala</button>'
        in text
    )


def test_help_article_introduces_no_local_script_block() -> None:
    """Koordinator talimati geregi help_article.html icin yerel bir
    <script> bloğu ACILMADI (harici bys360_support_learning.js dosyasina
    entegre edildi) -- template'in kendi kaynaginda hala hicbir <script>...
    </script> bloğu yok, yalnizca harici <script src="..."> referansi var."""
    text = _read(HELP_ARTICLE_TEMPLATE)
    assert "<script>" not in text
    assert text.count("<script") == 1
    assert (
        '<script src="{{ url_for(\'static\', filename=\'js/bys360_support_learning.js\') }}"></script>'
        in text
    )
    # window.print() cagrisi artik template kaynaginda degil, harici JS'te.
    assert "window.print()" not in text


# ---------------------------------------------------------------------------
# 2) Statik JS dosyalari uzerindeki kontrat. faz4_support_account_mobile.js
#    DOKUNULMADI (regresyon kilidi); bys360_support_learning.js'e YENI bir
#    fonksiyon eklendi (mevcut convention: id + DOMContentLoaded).
# ---------------------------------------------------------------------------


def test_faz4_support_account_mobile_js_has_no_form_data_confirm_pattern() -> None:
    """Regresyon kilidi: bu JS dosyasinin form[data-confirm] delegasyonuna
    SAHIP OLMADIGINI (ve bu dalgada byle bir seyin eklenmedigini) dogrular
    -- help_admin_list.html'in kendi yerel script blogu bu dosyaya
    guvenerek atlanmadi, cift-delegasyon riski yok."""
    text = _read(FAZ4_SUPPORT_ACCOUNT_MOBILE_JS)
    assert "data-confirm" not in text
    assert "querySelectorAll('form[data-confirm]')" not in text


def test_support_learning_js_has_print_handler_bound_via_id() -> None:
    text = _read(SUPPORT_LEARNING_JS)
    assert "getElementById('helpArticlePrintBtn')" in text
    assert "window.print()" in text
    assert text.count("getElementById('helpArticlePrintBtn')") == 1
    assert text.count("window.print()") == 1


def test_support_learning_js_print_handler_registered_exactly_once_in_boot() -> None:
    """Yeni `bindArticlePrint()` fonksiyonunun TEK bir DOMContentLoaded
    cagrisi icinde, mevcut copyArticleLink()/smoothAnchors() cagrilarinin
    YANINA eklendigini (cift dinleyici/cift DOMContentLoaded olusturmadan)
    dogrular."""
    text = _read(SUPPORT_LEARNING_JS)
    assert text.count("document.addEventListener('DOMContentLoaded'") == 1
    assert "bindArticlePrint();" in text
    assert "copyArticleLink(); smoothAnchors(); bindArticlePrint();" in text
    # 3 = copyArticleLink (buton click) + smoothAnchors (link click, virgülden
    # sonra boşluksuz "'click',function") + bindArticlePrint (yeni, buton click).
    assert text.count("addEventListener('click'") == 3


def test_support_learning_js_preserves_existing_copy_link_and_smooth_anchor_functions() -> None:
    """Regresyon kilidi: mevcut `copyArticleLink` ve `smoothAnchors`
    fonksiyon tanimlari (govdeleriyle birlikte) dokunulmadan korunmus
    olmali."""
    text = _read(SUPPORT_LEARNING_JS)
    assert "function copyArticleLink(){" in text
    assert "var btn=document.querySelector('[data-copy-support-link]');" in text
    assert "function smoothAnchors(){" in text
    assert "document.querySelectorAll('[data-support-anchor]')" in text


def test_support_learning_js_introduces_no_dangerous_js_sinks() -> None:
    text = _read(SUPPORT_LEARNING_JS)
    for forbidden in _FORBIDDEN_JS_SINKS:
        assert forbidden not in text


def test_base_template_has_no_global_form_data_confirm_delegation() -> None:
    """Regresyon kilidi: `base.html` şu an KENDİ `form[data-confirm]`
    submit-delegasyonuna SAHİP DEĞİL. help_admin_list.html render
    testlerinin "tam sayfa çıktısında `querySelectorAll('form[data-confirm]')`
    tam olarak 1 kez geçer" varsayımı buna dayanır -- biri ileride base.html'e
    global bir form[data-confirm] delegasyonu eklerse bu, help_admin_list.
    html'in kendi yerel delegasyonuyla ÇİFT LİSTENER (çift confirm dialog'u)
    oluşturacağından bu test o riski erken yakalar."""
    text = _read(BASE_TEMPLATE)
    assert "querySelectorAll('form[data-confirm]')" not in text
    assert "data-confirm" not in text


def test_base_template_has_no_help_article_print_button_id_collision() -> None:
    """Regresyon kilidi: `base.html` (veya baska bir global include) zaten
    `id="helpArticlePrintBtn"` uretmiyor -- ID cakismasi olsaydi
    `getElementById` yanlis butona baglanabilirdi."""
    text = _read(BASE_TEMPLATE)
    assert 'id="helpArticlePrintBtn"' not in text


# ---------------------------------------------------------------------------
# 3) Calisma-zamani render kontrolu: gercek Flask app + gercek Jinja motoru
#    ile `render_template()` cagrisi (bkz. `app` fixture, tests/conftest.py).
# ---------------------------------------------------------------------------


def test_help_admin_list_render_with_multiple_articles_has_no_inline_handlers(app) -> None:
    """En az 2 sahte `article` iceren context ile help_admin_list.html
    render edilir; ciktida hicbir inline event-attribute (on*=) kalmamali."""
    from flask import render_template

    articles = [_fake_article_row(701), _fake_article_row(702), _fake_article_row(703, is_published=False)]
    with app.test_request_context("/"):
        html = render_template(
            "support/help_admin_list.html",
            articles=articles,
            search_query=None,
            status_filter="all",
            editable_help_ready=True,
        )

    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert not _JS_HREF_RE.search(html)


def test_help_admin_list_render_confirm_message_and_inline_class_preserved_for_each_row(app) -> None:
    """N (3) makale satiri render edilse bile her satirin kendi silme
    formunda AYNI data-confirm mesaji birebir korunur ve class="inline"
    attribute'u hala mevcuttur."""
    from flask import render_template

    articles = [_fake_article_row(801), _fake_article_row(802), _fake_article_row(803)]
    with app.test_request_context("/"):
        html = render_template(
            "support/help_admin_list.html",
            articles=articles,
            search_query=None,
            status_filter="all",
            editable_help_ready=True,
        )

    assert html.count(f'data-confirm="{DELETE_CONFIRM_MESSAGE}"') == 3
    for article_id in (801, 802, 803):
        assert (
            f"action=\"/support/help-admin/{article_id}/delete\" class=\"inline\" "
            f'data-confirm="{DELETE_CONFIRM_MESSAGE}"' in html
        )
    # Delegasyon script'i sayfa basina bir kez render edilir (base.html'in
    # KENDI form[data-confirm] deseni olmadigi ayrica dogrulanmistir, bkz.
    # test_base_template_has_no_global_form_data_confirm_delegation).
    assert html.count("querySelectorAll('form[data-confirm]')") == 1
    assert not _INLINE_EVENT_ATTR_RE.findall(html)


def test_help_admin_list_render_with_empty_articles_still_has_single_script(app) -> None:
    """Bos `articles` listesiyle (Jinja `{% else %}` dali, 'uygun makale
    bulunamadi') render edilse bile delegasyon script'i tam olarak 1 kez
    render edilir."""
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template(
            "support/help_admin_list.html",
            articles=[],
            search_query=None,
            status_filter="all",
            editable_help_ready=True,
        )

    assert "Filtreye uygun makale bulunamadı." in html
    assert html.count("querySelectorAll('form[data-confirm]')") == 1
    assert not _INLINE_EVENT_ATTR_RE.findall(html)


def test_help_article_render_has_print_button_id_and_no_inline_handlers(app) -> None:
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template("support/help_article.html", article=_fake_article_detail())

    assert 'id="helpArticlePrintBtn"' in html
    assert "onclick=" not in html
    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert not _JS_HREF_RE.search(html)


def test_help_article_render_preserves_copy_link_button_regression(app) -> None:
    """Regresyon korumasi: `data-copy-support-link` butonu (bu dalganin
    kapsami disi, onceden var olan islevsellik) render ciktisinda hala
    mevcut ve dokunulmamis."""
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template("support/help_article.html", article=_fake_article_detail())

    assert "data-copy-support-link" in html
    assert (
        '<button class="support-btn-soft" type="button" data-copy-support-link>'
        '<i class="fa-solid fa-link"></i> Bağlantıyı Kopyala</button>'
        in html
    )


def test_help_article_render_external_script_reference_present_exactly_once(app) -> None:
    """`bys360_support_learning.js` referansi (yazdirma mantiginin tasindigi
    dosya) render ciktisinda tam olarak bir kez gecer; template kaynaginda
    yeni bir yerel <script> bloğu YOK."""
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template("support/help_article.html", article=_fake_article_detail())

    assert html.count("js/bys360_support_learning.js") == 1


def test_help_article_render_with_multiple_sections_and_related_articles(app) -> None:
    """Birden fazla bolum + ilgili rehber ile render edilse bile yazdirma
    butonu/id'si degismeden mevcut olmali (dongu tekrarindan etkilenmez --
    buton dongu disinda, sayfa basina bir kez render edilir)."""
    from flask import render_template

    article = _fake_article_detail(
        sections=[
            {"title": "Bölüm 1", "body": "Metin 1", "bullet_items": ["A", "B"]},
            {"title": "Bölüm 2", "body": "Metin 2", "bullet_items": []},
        ],
        related_articles=[
            {"slug": "rehber-a", "title": "Rehber A"},
            {"slug": "rehber-b", "title": "Rehber B"},
        ],
    )
    with app.test_request_context("/"):
        html = render_template("support/help_article.html", article=article)

    assert html.count('id="helpArticlePrintBtn"') == 1
    assert "Rehber A" in html
    assert "Rehber B" in html
    assert not _INLINE_EVENT_ATTR_RE.findall(html)


def test_help_article_render_with_missing_optional_fields_still_safe(app) -> None:
    """`sections`/`related_articles`/`roles`/`tags` gibi opsiyonel alanlar
    context'te hic verilmese bile (ChainableUndefined, bkz.
    `app/template_safety.py`) render hatasiz tamamlanir ve yazdirma butonu
    hala mevcuttur."""
    from flask import render_template

    minimal_article = {"title": "Minimal Rehber", "summary": "Özet."}
    with app.test_request_context("/"):
        html = render_template("support/help_article.html", article=minimal_article)

    assert 'id="helpArticlePrintBtn"' in html
    assert not _INLINE_EVENT_ATTR_RE.findall(html)
