"""CSP Dalga 6 - Performans "Sorular / Kriterler" ve "Puan Ağırlıkları"
ekranları kontrat testi.

BYS360 `app/security/headers.py` uygular:
    script-src: 'self' https:  (unsafe-inline YOK)

`app/security/headers.py::inject_csp_nonce_into_html` yanıt döndürdükten
sonra TÜM `<script>` etiketlerine (nonce'u olmayanlara) otomatik
`nonce="..."` ekler; bu merkezi mekanizma sayesinde template içindeki
`<script>...</script>` blokları zaten CSP ile uyumludur ve nonce hiçbir
zaman elle template'e yazılmaz. Asıl risk inline EVENT ATTRIBUTE'lardı
(`onclick=`, `onsubmit=` vb.) -- bunlara nonce uygulanmaz ve enforce modda
tarayıcı tarafından çalıştırılmazlar.

Bu dosyanın sahiplik alanı şu template:
    - app/templates/criteria.html  (3 handler: 2x onclick -> toggleEditBox,
      1x onsubmit -> confirm())

Not (weights.html kaldırıldı): bu dosya başlangıçta app/templates/weights.html
(1 handler: 1x onsubmit -> confirm()) için de aynı CSP-safety kontratını
taşıyordu -- aşağıdaki "ÇÖZÜM (weights.html)" paragrafı o dönemin tarihsel
kaydı olarak bırakıldı. weights.html, sonraki "BYS360 Orphan Template + Dead
Helper Micro-Cleanup" dalgasında ORPHAN_CONFIRMED bulunup dosya olarak
tamamen silindi (bkz.
tests/security/test_weights_orphan_template_and_dead_safe_url_for_cleanup_contract.py);
artık var olmayan bir dosyanın CSP-safety özelliklerini test etmenin anlamı
kalmadığı için o dalgada weights.html'e özgü tüm testler (WAVE6_FILES
parametrizasyonundan çıkarma dahil) buradan kaldırıldı. criteria.html'e ait
hiçbir test bundan etkilenmedi.

ÇÖZÜM (criteria.html): Bu template `{% for item in criteria_list %}...
{% endfor %}` döngüsüyle N kriter kartı render eder; her kartta İKİ buton
(Düzenle + kutu-içi Kapat) AYNI `edit-box-{{ item.id }}` hedefini açıp
kapatıyordu (`onclick="toggleEditBox('edit-box-{{ item.id }}')"`). Döngü
içinde tekrarlı içerik olduğu için EVENT DELEGATION tercih edildi: her iki
butona `data-toggle-edit-box="edit-box-{{ item.id }}"` eklendi, `onclick`
kaldırıldı. Var olan tek `<script>` bloğuna (yeni blok açılmadan, mevcut
`toggleEditBox` fonksiyonunun YANINA) TEK bir
`document.addEventListener('click', ...)` delegasyonu eklendi --
`event.target.closest('[data-toggle-edit-box]')` ile bulunan butonun
attribute değeri doğrudan `toggleEditBox(...)`'a geçirilir. Bu delegasyon
sayfa başına (döngü tekrarından bağımsız) YALNIZCA BİR KEZ kurulur, N kart
için de çalışır. `toggleEditBox` fonksiyonunun kendisi HİÇ değiştirilmedi.

Silme formundaki `onsubmit="return confirm('Bu kriter silinsin mi?');"`
kurulu Dalga 1-5 desenine göre `data-confirm="Bu kriter silinsin mi?"` +
standart `form[data-confirm]` submit-delegasyonuna çevrildi; bu delegasyon
da AYNI mevcut `<script>` bloğuna eklendi (ikinci bir `<script>` bloğu
açılmadı). Böylece criteria.html'de TEK script bloğu içinde hem
toggle-delegasyonu hem form-confirm-delegasyonu kurulu -- ikisi de tek
seferlik.

ÇÖZÜM (weights.html): Bu template'te `<script>` bloğu hiç yoktu. Silme
formundaki `onsubmit="return confirm('Bu ağırlık kaydını silmek
istediğinize emin misiniz?');"` aynı standart desenle
`data-confirm="Bu ağırlık kaydını silmek istediğinize emin misiniz?"` +
`{% block content %}` içinde `{% endblock %}`'tan hemen önce eklenen YENİ
tek bir `<script>` bloğundaki `form[data-confirm]` submit-delegasyonuna
çevrildi. Bu form `{% for item in weights %}...{% endfor %}` döngüsü
içinde olsa da delegasyon script'i döngü DIŞINDA, sayfa başına bir kez
render edilir; bu yüzden N satır için de tek delegasyon yeterlidir.

Not: `weights.html` / `weight_create.html` / `weight_edit.html` ve
`main.performance_weight_*` endpoint'leri bu ajanın incelemesi sırasında
Python tarafında (route katmanında) HİÇBİR YERDE bağlı bulunamadı --
şablon `safe_url_for()` kullanır (bkz. `app/route_support.py::safe_url_for`),
bu da `BuildError` durumunda sessizce `"#"` fallback'ine döner ve loglar;
bu yüzden endpoint'lerin gerçekte kayıtlı olup olmaması bu kontrat
testlerinin render başarısını ETKİLEMEZ (aynı güvenli davranış zaten
Dalga 1-5'te de kullanılmıştı, bkz. `v2_1_4_category_scope.html` referans
diff'i).

Statik testler `tests/security/test_csp_wave4_admin_contract.py` ve
`test_csp_wave5_portal_postcard_delegation_contract.py` ile aynı desendedir
(Path.read_text() + regex, sonra gerçek Jinja motoruyla `render_template()`
çıktı testleri; `app` fixture'ı `tests/conftest.py`'den gelir).

ÖNEMLİ SINIRLAMA: Bu dosyadaki HİÇBİR test gerçek bir tarayıcıda
çalışmadı/çalıştırılmadı. `render_template()` yalnızca ÜRETİLEN HTML'i
doğrular (inline handler yok, data-* attribute'ları doğru, script tag'i
sayfa başına bir kez render ediliyor, delegasyon çağrıları kaynak kodda
bir kez geçiyor). CSP enforce edilmiş gerçek bir tarayıcıda "Düzenle"/
"Kapat" butonlarının kutuyu fiilen açıp kapattığını veya silme
formlarındaki `confirm()` diyaloğunun açılıp iptal edilebildiğini
KANITLAMAZ -- bu, ayrı bir manuel/E2E doğrulama gerektirir ve bu dosyanın
kapsamı dışındadır.
"""
from __future__ import annotations

import re
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

CRITERIA_TEMPLATE = "app/templates/criteria.html"

WAVE6_FILES = [CRITERIA_TEMPLATE]

DELETE_CONFIRM_MESSAGE_CRITERIA = "Bu kriter silinsin mi?"

# HTML attribute syntax: bosluk + on<harfler> + '=' + tirnak. CSS/JS icindeki
# "javascript:" gibi metinsel string literal'leri yanlislikla yakalamaz.
_INLINE_EVENT_ATTR_RE = re.compile(r"""[\s]on[a-zA-Z]+\s*=\s*["']""")
_JS_HREF_RE = re.compile(r"""(?:href|src)\s*=\s*["']\s*javascript:""", re.IGNORECASE)
_JS_URL_ANYWHERE_RE = re.compile(r"""javascript:""", re.IGNORECASE)


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _fake_criterion(item_id: int, **overrides: object) -> types.SimpleNamespace:
    base: dict[str, object] = dict(
        id=item_id,
        name=f"Wave6 Test Kriteri {item_id}",
        description=f"Wave6 kontrat test açıklaması {item_id}",
        weight=20.0,
        sort_order=item_id,
        is_active=True,
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


# ---------------------------------------------------------------------------
# 1) Statik kaynak-kod kontratı (Path.read_text + regex). Kosulsuz calisir,
#    Jinja if-bloklarinin arkasinda kalan durumlari da yakalar.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative_path", WAVE6_FILES)
def test_wave6_file_has_no_inline_event_attributes(relative_path: str) -> None:
    text = _read(relative_path)
    matches = _INLINE_EVENT_ATTR_RE.findall(text)
    assert not matches, (
        f"{relative_path} icinde inline event-attribute (on*=) bulundu: {matches!r}. "
        "CSP script-src 'self' https: (unsafe-inline yok) altinda bunlar calismaz."
    )


@pytest.mark.parametrize("relative_path", WAVE6_FILES)
def test_wave6_file_has_no_javascript_href_or_url(relative_path: str) -> None:
    text = _read(relative_path)
    assert not _JS_HREF_RE.search(text), f"{relative_path} icinde href/src=\"javascript:...\" bulundu."
    assert not _JS_URL_ANYWHERE_RE.search(text), f"{relative_path} icinde beklenmedik bir javascript: metni bulundu."


@pytest.mark.parametrize("relative_path", WAVE6_FILES)
def test_wave6_file_introduces_no_dangerous_js_sinks(relative_path: str) -> None:
    """Duzeltme sirasinda eval/new Function/document.write eklenmedigini dogrular."""
    text = _read(relative_path)
    for forbidden in ("eval(", "new Function(", "document.write("):
        assert forbidden not in text, f"{relative_path} icinde yasakli sink bulundu: {forbidden}"


@pytest.mark.parametrize("relative_path", WAVE6_FILES)
def test_wave6_file_has_no_forbidden_inline_handler_string_literal(relative_path: str) -> None:
    """Bir inline handler'in HTML string'i olarak JS icinde uretilmedigini
    (yani `'onclick='`/`"onsubmit="` gibi bir literal yoklugunu) dogrular --
    bu, delegasyonun DOM'a innerHTML/string ile geri sizdirilmadiginin
    kanitidir."""
    text = _read(relative_path)
    for literal in ("'onclick='", '"onclick="', "'onsubmit='", '"onsubmit="'):
        assert literal not in text, f"{relative_path} icinde yasakli JS string literal bulundu: {literal}"


def test_criteria_source_has_data_toggle_edit_box_attributes_on_both_buttons() -> None:
    """criteria.html kaynağında hem "Düzenle" hem kutu-içi "Kapat" butonu
    `data-toggle-edit-box="edit-box-{{ item.id }}"` taşıyor, `onclick` yok."""
    text = _read(CRITERIA_TEMPLATE)
    assert "onclick=" not in text
    assert 'data-toggle-edit-box="edit-box-{{ item.id }}"' in text
    assert text.count('data-toggle-edit-box="edit-box-{{ item.id }}"') == 2


def test_criteria_source_toggle_edit_box_function_definition_preserved() -> None:
    """`toggleEditBox` fonksiyon TANIMI (gövdesiyle birlikte) dokunulmadan
    korunmuş olmalı -- yalnızca ona bağlı çağırıcı inline attribute'lar
    kaldırıldı."""
    text = _read(CRITERIA_TEMPLATE)
    assert "function toggleEditBox(id) {" in text
    assert 'const box = document.getElementById(id);' in text
    assert 'box.classList.toggle("show");' in text


def test_criteria_source_click_delegation_calls_toggle_edit_box_exactly_once() -> None:
    """Delegasyon (`document.addEventListener('click', ...)` içinde
    `[data-toggle-edit-box]` arayan blok) kaynak kodda TAM OLARAK bir kez
    geçer -- N kart için tekrar tekrar kurulmaz."""
    text = _read(CRITERIA_TEMPLATE)
    assert text.count("document.addEventListener('click'") == 1
    assert "event.target.closest('[data-toggle-edit-box]')" in text
    assert "toggleEditBox(btn.getAttribute('data-toggle-edit-box'));" in text


def test_criteria_source_delete_form_has_data_confirm_message_verbatim() -> None:
    text = _read(CRITERIA_TEMPLATE)
    assert f'data-confirm="{DELETE_CONFIRM_MESSAGE_CRITERIA}"' in text
    assert text.count('data-confirm="') == 1


def test_criteria_source_form_confirm_delegation_present_exactly_once() -> None:
    text = _read(CRITERIA_TEMPLATE)
    assert text.count("querySelectorAll('form[data-confirm]')") == 1
    assert "if (message && !window.confirm(message))" in text
    assert "event.preventDefault();" in text


def test_criteria_source_has_exactly_one_script_block() -> None:
    """criteria.html'de yeni bir `<script>` bloğu AÇILMADI -- toggle-
    delegasyonu ve form-confirm-delegasyonu var olan TEK script bloğuna
    eklendi."""
    text = _read(CRITERIA_TEMPLATE)
    assert text.count("<script") == 1


def test_criteria_source_csrf_hidden_input_untouched() -> None:
    text = _read(CRITERIA_TEMPLATE)
    assert '<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">' in text


def test_base_template_has_no_global_form_data_confirm_delegation() -> None:
    """Regresyon kilidi: `base.html` şu an KENDİ `form[data-confirm]`
    submit-delegasyonuna SAHİP DEĞİL. criteria.html render testlerinin
    "tam sayfa çıktısında `querySelectorAll('form[data-confirm]')` tam olarak
    1 kez geçer" varsayımı buna dayanır -- biri ileride base.html'e global bir
    form[data-confirm] delegasyonu eklerse bu, criteria.html'in kendi yerel
    delegasyonuyla ÇİFT LİSTENER (çift confirm dialog'u) oluşturacağından bu
    test o riski erken yakalar."""
    text = _read("app/templates/base.html")
    assert "querySelectorAll('form[data-confirm]')" not in text
    assert "data-confirm" not in text


# ---------------------------------------------------------------------------
# 2) Calisma-zamani render kontrolu: gercek Flask app + gercek Jinja motoru
#    ile `render_template()` cagrisi (bkz. `app` fixture, tests/conftest.py).
# ---------------------------------------------------------------------------


def test_criteria_render_with_multiple_items_has_no_inline_handlers(app) -> None:
    """En az 2 sahte `item` içeren context ile criteria.html render edilir;
    çıktıda hiçbir inline event-attribute (on*=) kalmamalı."""
    from flask import render_template

    items = [_fake_criterion(101), _fake_criterion(102), _fake_criterion(103)]
    with app.test_request_context("/"):
        html = render_template(
            "criteria.html",
            criteria_list=items,
            total_count=len(items),
            active_count=len(items),
            passive_count=0,
        )

    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert not _JS_HREF_RE.search(html)


def test_criteria_render_toggle_delegation_script_rendered_exactly_once_for_n_cards(app) -> None:
    """N (3) kriter kartı render edilse bile, delegasyon script'inin
    (script bloğunun kendisi) render çıktısında YALNIZ 1 kez geçtiğini
    doğrular -- döngü içindeki tekrarlı içerik script'i N kez
    çoğaltmamalı."""
    from flask import render_template

    items = [_fake_criterion(201), _fake_criterion(202), _fake_criterion(203)]
    with app.test_request_context("/"):
        html = render_template(
            "criteria.html",
            criteria_list=items,
            total_count=len(items),
            active_count=len(items),
            passive_count=0,
        )

    # Not: `html.count("<script")` burada kasıtlı olarak KULLANILMAZ --
    # criteria.html `base.html`'i extends eder ve base.html'in kendisi zaten
    # onlarca `<script>` içerir (layout/menü/JS include'ları); tam sayfa
    # render çıktısında ham "<script" sayımı bu şablona özgü bir sinyal
    # değildir. Bunun yerine YALNIZ criteria.html'e özgü, base.html'de
    # bulunmayan benzersiz alt-dizeler sayılır (base.html'in KENDİ,
    # farklı-amaçlı `document.addEventListener('click', ...)` menü-dropdown
    # dinleyicisiyle (satır ~922) yanlışlıkla karıştırılmaması için).
    assert html.count("event.target.closest('[data-toggle-edit-box]')") == 1
    assert html.count("querySelectorAll('form[data-confirm]')") == 1

    # Her N kart için IKI data-toggle-edit-box butonu (Duzenle + Kapat) render edilir.
    assert html.count('data-toggle-edit-box="edit-box-201"') == 2
    assert html.count('data-toggle-edit-box="edit-box-202"') == 2
    assert html.count('data-toggle-edit-box="edit-box-203"') == 2

    # Her N kart icin bir silme formu, dolayisiyla N adet ayni data-confirm mesaji.
    assert html.count(f'data-confirm="{DELETE_CONFIRM_MESSAGE_CRITERIA}"') == 3


def test_criteria_render_preserves_toggle_edit_box_function_definition(app) -> None:
    """`toggleEditBox` fonksiyonunun render çıktısında hâlâ tanımlı
    olduğunu doğrular (delegasyon fonksiyonu ÇAĞIRIR, TANIMINI silmez)."""
    from flask import render_template

    items = [_fake_criterion(301), _fake_criterion(302)]
    with app.test_request_context("/"):
        html = render_template(
            "criteria.html",
            criteria_list=items,
            total_count=len(items),
            active_count=len(items),
            passive_count=0,
        )

    assert "function toggleEditBox(id) {" in html
    assert "toggleEditBox(btn.getAttribute('data-toggle-edit-box'));" in html


def test_criteria_render_with_empty_list_still_has_single_script_and_no_handlers(app) -> None:
    """Boş `criteria_list` (empty-box dalı) ile render edilse bile script
    bloğu hâlâ tam olarak 1 kez render edilir ve inline handler yoktur --
    delegasyon listener'ları DOM'da kart olmasa da güvenle kurulabilir."""
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template(
            "criteria.html",
            criteria_list=[],
            total_count=0,
            active_count=0,
            passive_count=0,
        )

    # Bkz. yukarıdaki not: tam sayfa "<script" sayımı base.html'in kendi
    # script'leri yüzünden bu şablona özgü bir sinyal değildir; bunun yerine
    # criteria.html'e özgü benzersiz delegasyon alt-dizesi sayılır.
    assert html.count("event.target.closest('[data-toggle-edit-box]')") == 1
    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert "function toggleEditBox(id) {" in html
