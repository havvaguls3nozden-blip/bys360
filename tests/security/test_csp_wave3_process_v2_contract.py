"""CSP Dalga 3 - Surec Motoru + V2 Donem/Kategori kontrat testi.

BYS360 `app/security/headers.py` uygular:
    script-src: 'self' https:  (unsafe-inline YOK)

Bu dosyanin sahiplik alani yalnizca su bes template:
    - app/templates/performance/process_engine_tracking.html
    - app/templates/performance/process_reports_advanced.html
    - app/templates/performance/process_engine_president_approvals.html
    - app/templates/performance/v2_1_7_period_management_center.html
    - app/templates/performance/v2_1_4_category_scope.html

Koordinatorun envanteri bu bes dosyada toplam 7 inline event-attribute
(2 onchange + 5 onsubmit) tespit etmisti; `javascript:` URL yoktu. Bu dosya
o tespiti once bagimsiz statik regex taramasiyla (kaynak metin), sonra da
gercek Jinja/Flask motoruyla uretilen HTML uzerinde kilitler: ileride biri
bu bes dosyaya inline handler eklerse hem kaynak metin hem de render edilen
HTML testi kirilir.

`performance/` alt dizininin geri kalani (mail_reminders, hierarchy_assignments,
publish, reports_print, v2_phase6_print vb.) bu dalganin KAPSAMI DISINDADIR --
onlar Dalga 1/2'de kilitlendi (bkz. test_csp_wave1_inline_handlers_contract.py,
test_csp_wave2_performance_print_mail_contract.py). Bu dosya o alanlara
dokunmaz/test etmez.

Statik testler onceki dalga kontrat dosyalariyla ayni desendedir
(Path.read_text() + regex + gercek app fixture'i ile render).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

TRACKING_TEMPLATE = "app/templates/performance/process_engine_tracking.html"
REPORTS_ADVANCED_TEMPLATE = "app/templates/performance/process_reports_advanced.html"
PRESIDENT_APPROVALS_TEMPLATE = "app/templates/performance/process_engine_president_approvals.html"
PERIOD_MANAGEMENT_TEMPLATE = "app/templates/performance/v2_1_7_period_management_center.html"
CATEGORY_SCOPE_TEMPLATE = "app/templates/performance/v2_1_4_category_scope.html"

WAVE3_PROCESS_V2_FILES = [
    TRACKING_TEMPLATE,
    REPORTS_ADVANCED_TEMPLATE,
    PRESIDENT_APPROVALS_TEMPLATE,
    PERIOD_MANAGEMENT_TEMPLATE,
    CATEGORY_SCOPE_TEMPLATE,
]

# HTML attribute syntax: bosluk + on<harfler> + '=' + tirnak. CSS/JS icindeki
# "javascript:" gibi metinsel string literal'leri yanlislikla yakalamaz.
_INLINE_EVENT_ATTR_RE = re.compile(r"""[\s]on[a-zA-Z]+\s*=\s*["']""")
_JS_HREF_RE = re.compile(r"""(?:href|src)\s*=\s*["']\s*javascript:""", re.IGNORECASE)
_JS_URL_ANYWHERE_RE = re.compile(r"""javascript:""", re.IGNORECASE)


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1) Statik kaynak-kod kontrati (Path.read_text + regex). Jinja if/for
#    bloklari (orn. {% if can_manage_process_tracking %}, {% for row in rows %})
#    arkasina gizli form/select'leri de yakalar -- runtime render testi
#    (asagida) bos baglamda calistigi icin bu bloklarin tumunu tetiklemez;
#    statik tarama kosulsuzdur.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative_path", WAVE3_PROCESS_V2_FILES)
def test_process_v2_file_has_no_inline_event_attributes(relative_path: str) -> None:
    text = _read(relative_path)
    matches = _INLINE_EVENT_ATTR_RE.findall(text)
    assert not matches, (
        f"{relative_path} icinde inline event-attribute (on*=) bulundu: {matches!r}. "
        "CSP script-src 'self' https: (unsafe-inline yok) altinda bunlar calismaz; "
        "data-* attribute + addEventListener kalibina cevrilmeli."
    )


@pytest.mark.parametrize("relative_path", WAVE3_PROCESS_V2_FILES)
def test_process_v2_file_has_no_javascript_href(relative_path: str) -> None:
    text = _read(relative_path)
    assert not _JS_HREF_RE.search(text), (
        f"{relative_path} icinde href/src=\"javascript:...\" bulundu."
    )
    assert not _JS_URL_ANYWHERE_RE.search(text), (
        f"{relative_path} icinde beklenmedik bir javascript: metni bulundu."
    )


@pytest.mark.parametrize("relative_path", WAVE3_PROCESS_V2_FILES)
def test_process_v2_file_introduces_no_dangerous_js_sinks(relative_path: str) -> None:
    """Duzeltme sirasinda eval/new Function/document.write eklenmedigini dogrular."""
    text = _read(relative_path)
    for forbidden in ("eval(", "new Function(", "document.write("):
        assert forbidden not in text, f"{relative_path} icinde yasakli sink bulundu: {forbidden}"


def test_process_v2_file_has_no_javascript_url_scheme_construction() -> None:
    """Yasak listesindeki 'javascript: URL uretme' kuralini ayrica dogrudan
    dogrular: hicbir dosyada 'javascript:' alt string'i (herhangi bir
    baglamda) bulunmamali."""
    for relative_path in WAVE3_PROCESS_V2_FILES:
        text = _read(relative_path)
        assert "javascript:" not in text.lower()


# ---------------------------------------------------------------------------
# 2) Dosya bazinda data-confirm / data-autosubmit + tekil listener kurulumu
#    dogrulamasi. Confirm mesajlari AYNEN (Turkce karakterler dahil)
#    korunmus olmali.
# ---------------------------------------------------------------------------


def test_process_engine_tracking_all_three_handlers_replaced() -> None:
    """Koordinatorun envanteri: bu dosyada 3 inline event-attribute vardi
    (1 onchange select + 2 onsubmit form). Bu test onlarin data-*
    karsiliklarinin hepsinin mevcut oldugunu ve TEK bir delegasyon
    kurulumunun (autosubmit icin, confirm icin) her ikisini de kapsadigini
    dogrular."""
    text = _read(TRACKING_TEMPLATE)
    assert "onchange=" not in text
    assert "onsubmit=" not in text

    assert 'data-autosubmit="1"' in text

    expected_confirm_messages = [
        "Görünen süreç takip kayıtları listeden kaldırılacak. Karne ve değerlendirme kayıtları silinmez. Devam edilsin mi?",
        "Bu kayıt yalnızca süreç takip listesinden kaldırılacak. Devam edilsin mi?",
    ]
    for message in expected_confirm_messages:
        assert f'data-confirm="{message}"' in text, f"beklenen data-confirm bulunamadi: {message!r}"

    # Tek delegasyon kurulumu: querySelectorAll cagrisi her turden yalnizca bir kez.
    assert text.count("querySelectorAll('[data-autosubmit]')") == 1
    assert text.count("querySelectorAll('form[data-confirm]')") == 1
    assert "addEventListener('change'" in text
    assert "addEventListener('submit'" in text


def test_process_engine_tracking_confirm_delegation_calls_preventdefault_on_cancel() -> None:
    """Confirm iptal edildiginde form submit edilmemeli (event.preventDefault)."""
    text = _read(TRACKING_TEMPLATE)
    assert "if (message && !window.confirm(message))" in text
    assert "event.preventDefault();" in text


def test_process_reports_advanced_autosubmit_handler_replaced() -> None:
    text = _read(REPORTS_ADVANCED_TEMPLATE)
    assert "onchange=" not in text
    assert "onsubmit=" not in text

    assert 'data-autosubmit="1"' in text
    assert text.count("querySelectorAll('[data-autosubmit]')") == 1
    assert "addEventListener('change'" in text


def test_president_approvals_delete_form_uses_data_confirm() -> None:
    text = _read(PRESIDENT_APPROVALS_TEMPLATE)
    assert "onsubmit=" not in text

    expected_message = (
        "Bu kayıt Başkan Onayları listesinden kaldırılacak. "
        "Personel, karne ve puan verisi silinmez. Devam edilsin mi?"
    )
    assert f'data-confirm="{expected_message}"' in text

    assert text.count("querySelectorAll('form[data-confirm]')") == 1
    assert "addEventListener('submit'" in text
    assert "if (message && !window.confirm(message))" in text
    assert "event.preventDefault();" in text


def test_period_management_center_launch_assignments_form_uses_data_confirm() -> None:
    text = _read(PERIOD_MANAGEMENT_TEMPLATE)
    assert "onsubmit=" not in text

    expected_message = "Bu dönem için değerlendirme görevleri üretilecek. Devam edilsin mi?"
    assert f'data-confirm="{expected_message}"' in text

    assert text.count("querySelectorAll('form[data-confirm]')") == 1
    assert "addEventListener('submit'" in text
    assert "if (message && !window.confirm(message))" in text
    assert "event.preventDefault();" in text

    # Bu dosyada onceden hic <script> blogu yoktu; yeni blok {% block content %}
    # icinde, {% endblock %}'tan hemen once eklendi.
    assert "{% block content %}" in text
    content_start = text.index("{% block content %}")
    script_pos = text.index("<script>")
    endblock_positions = [m.start() for m in re.finditer(r"\{%\s*endblock\s*%\}", text)]
    assert endblock_positions, "endblock bulunamadi"
    first_endblock_after_script = next(pos for pos in endblock_positions if pos > script_pos)
    assert content_start < script_pos < first_endblock_after_script


def test_category_scope_delete_category_form_uses_data_confirm_and_preserves_hidden_inputs() -> None:
    text = _read(CATEGORY_SCOPE_TEMPLATE)
    assert "onsubmit=" not in text

    expected_message = "Bu kategori silinsin mi? Bağlı kayıt varsa kategori pasife alınır ve geçmiş korunur."
    assert f'data-confirm="{expected_message}"' in text

    assert text.count("querySelectorAll('form[data-confirm]')") == 1
    assert "addEventListener('submit'" in text
    assert "if (message && !window.confirm(message))" in text
    assert "event.preventDefault();" in text

    # CSRF token ve diger hidden input'lar (action, category_key) tek satirlik
    # yogun form icinde BOZULMAMIS olmali -- tam blok birebir korunmus olmali.
    preserved_hidden_inputs_block = (
        '{% if csrf_token is defined %}<input type="hidden" name="csrf_token" '
        'value="{{ csrf_token() }}">{% endif %}<input type="hidden" name="action" '
        'value="delete_category"><input type="hidden" name="category_key" '
        'value="{{ cat.category_key }}">'
    )
    assert preserved_hidden_inputs_block in text

    # Bu dosyada onceden hic <script> blogu yoktu; yeni blok {% block content %}
    # icinde, {% endblock %}'tan hemen once eklendi.
    assert "{% block content %}" in text
    content_start = text.index("{% block content %}")
    script_pos = text.index("<script>")
    endblock_positions = [m.start() for m in re.finditer(r"\{%\s*endblock\s*%\}", text)]
    assert endblock_positions, "endblock bulunamadi"
    first_endblock_after_script = next(pos for pos in endblock_positions if pos > script_pos)
    assert content_start < script_pos < first_endblock_after_script


# ---------------------------------------------------------------------------
# 3) Calisma-zamani render kontrolu: gercek Flask app + gercek Jinja motoru
#    ile `render_template` cagrisi (bkz. `app` fixture, tests/conftest.py).
#    Bu bes template'in tamami, view fonksiyonu context'i olmadan (bos/
#    varsayilan baglamda) dogrudan render edildiginde bile basariyla
#    calisir -- degiskenler ya Jinja `|default(...)`/`is defined` korumalariyla
#    ya da varsayilan (sessiz) Undefined davranisiyla (bos string / falsy)
#    yazilmistir. Bu HALA gercek bir tarayici testi DEGILDIR: CSP enforce
#    edilmis bir tarayicida script'lerin fiilen calistigini kanitlamaz;
#    yalnizca uretilen HTML'de inline event-attribute/javascript: href
#    kalmadigini ve yeni <script> bloklarinin gercekten Jinja content
#    block'u icinde render edildigini (bos baglamda bile ortaya ciktigini)
#    dogrular. Kosullu dallardaki (orn. {% if can_manage_process_tracking %},
#    {% for row in rows %}) data-confirm butonlari bu bos-baglam render'inda
#    tetiklenmeyebilir -- o dallar yukaridaki statik kaynak testleriyle
#    kosulsuz kilitlenir.
# ---------------------------------------------------------------------------

_TEMPLATE_NAME_BY_PATH = {
    TRACKING_TEMPLATE: "performance/process_engine_tracking.html",
    REPORTS_ADVANCED_TEMPLATE: "performance/process_reports_advanced.html",
    PRESIDENT_APPROVALS_TEMPLATE: "performance/process_engine_president_approvals.html",
    PERIOD_MANAGEMENT_TEMPLATE: "performance/v2_1_7_period_management_center.html",
    CATEGORY_SCOPE_TEMPLATE: "performance/v2_1_4_category_scope.html",
}


@pytest.mark.parametrize("relative_path", WAVE3_PROCESS_V2_FILES)
def test_process_v2_template_render_has_no_inline_handlers(app, relative_path: str) -> None:
    from flask import render_template

    template_name = _TEMPLATE_NAME_BY_PATH[relative_path]
    with app.test_request_context("/"):
        html = render_template(template_name)

    assert not _INLINE_EVENT_ATTR_RE.findall(html), (
        f"{template_name} gercek render ciktisinda inline event-attribute bulundu."
    )
    assert not _JS_HREF_RE.search(html), (
        f"{template_name} gercek render ciktisinda javascript: href bulundu."
    )
    # NOT: html burada base.html'i de icerir (extends zinciri); base.html bu
    # dalganin KAPSAMI DISINDADIR ve orada savunma amacli bir string literal
    # olarak ("...startsWith('javascript:')") mesru sekilde "javascript:" gecer.
    # Bu yuzden "javascript: hicbir yerde gecmez" kontrolu yalnizca statik
    # kaynak testinde (yukarida, YALNIZCA bu 5 dosyanin kendi metni uzerinde)
    # kosulsuz uygulanir; burada href/src regex'i yeterlidir.
    for forbidden in ("eval(", "new Function(", "document.write("):
        assert forbidden not in html, f"{template_name} render ciktisinda yasakli sink bulundu: {forbidden}"


def test_process_engine_tracking_render_includes_autosubmit_and_confirm_script_hooks(app) -> None:
    """Bos baglamda bile (tracking_items yok) sayfanin en altindaki mevcut
    <script> blogu icine eklenen autosubmit + data-confirm delegasyon
    kancalari her zaman render edilir -- bu script blogu kosula bagli
    degildir."""
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template("performance/process_engine_tracking.html")

    assert 'data-autosubmit="1"' in html
    assert "querySelectorAll('[data-autosubmit]')" in html
    assert "querySelectorAll('form[data-confirm]')" in html
    assert "addEventListener('change'" in html
    assert "addEventListener('submit'" in html


def test_process_reports_advanced_render_includes_autosubmit_script_hook(app) -> None:
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template("performance/process_reports_advanced.html")

    assert 'data-autosubmit="1"' in html
    assert "querySelectorAll('[data-autosubmit]')" in html
    assert "addEventListener('change'" in html


def test_president_approvals_render_includes_confirm_script_hook(app) -> None:
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template("performance/process_engine_president_approvals.html")

    assert "querySelectorAll('form[data-confirm]')" in html
    assert "addEventListener('submit'" in html


def test_period_management_center_render_includes_new_script_block_in_content(app) -> None:
    """Bu dosyada onceden <script> blogu yoktu; testin amaci yeni eklenen
    blogun gercekten {% block content %} icinde (dead/orphan Jinja bloguna
    degil) render edildigini kanitlamaktir."""
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template("performance/v2_1_7_period_management_center.html")

    assert "querySelectorAll('form[data-confirm]')" in html
    assert "addEventListener('submit'" in html
    assert "if (message && !window.confirm(message))" in html
    assert "event.preventDefault();" in html


def test_category_scope_render_includes_new_script_block_in_content(app) -> None:
    """Bu dosyada onceden <script> blogu yoktu; testin amaci yeni eklenen
    blogun gercekten {% block content %} icinde render edildigini
    kanitlamaktir (CSRF token/hidden input'lar bozulmadan)."""
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template("performance/v2_1_4_category_scope.html")

    assert "querySelectorAll('form[data-confirm]')" in html
    assert "addEventListener('submit'" in html
    assert "if (message && !window.confirm(message))" in html
    assert "event.preventDefault();" in html
