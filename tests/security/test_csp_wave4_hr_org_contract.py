"""CSP Dalga 4 - HR/Organizasyon ekranlari kontrat testi.

BYS360 `app/security/headers.py` uygular:
    script-src: 'self' https:  (unsafe-inline YOK)

Bu dosyanin sahiplik alani yalnizca su bes template:
    - app/templates/hr_attendance.html
    - app/templates/hr_leave.html
    - app/templates/org_units.html
    - app/templates/org_units_list.html
    - app/templates/hierarchy_settings.html

Koordinatorun envanteri bu bes dosyada toplam 5 inline event-attribute
tespit etmisti:
    - hr_attendance.html: 2 (silme formu onsubmit=confirm, iki farkli mesaj)
    - hr_leave.html: 1 (silme formu onsubmit=confirm)
    - org_units.html: 1 (silme formu onsubmit=confirm)
    - org_units_list.html: 1 (silme formu onsubmit=confirm)
    - hierarchy_settings.html: 1 (ozel durum -- confirm degil, onchange ile
      dogrudan navigate; select degistiginde sayfa yeni period_id ile
      yeniden yukleniyordu)

Dort silme formu `data-confirm="<orijinal mesaj>"` + ortak
`form[data-confirm]` submit-listener kalibina cevrildi (performance/
process_engine_tracking.html referans deseniyle ayni). hierarchy_settings.html
ozel durumu `data-nav-base` + `data-nav-scope` + `change` listener ile
orijinal URL kurgusu (period_id=..&scope=..) birebir korunarak cozuldu.

Bu dosya o donusumu once bagimsiz statik regex taramasiyla (kaynak metin),
sonra da gercek Jinja/Flask motoruyla uretilen HTML uzerinde kilitler:
ileride biri bu bes dosyaya inline handler eklerse hem kaynak metin hem de
render edilen HTML testi kirilir.

Statik testler `tests/security/test_csp_wave2_performance_print_mail_contract.py`
ile ayni desendedir (Path.read_text() + regex + gercek app fixture'i ile
render, bkz. tests/conftest.py `app` fixture).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

HR_ATTENDANCE_TEMPLATE = "app/templates/hr_attendance.html"
HR_LEAVE_TEMPLATE = "app/templates/hr_leave.html"
ORG_UNITS_TEMPLATE = "app/templates/org_units.html"
ORG_UNITS_LIST_TEMPLATE = "app/templates/org_units_list.html"
HIERARCHY_SETTINGS_TEMPLATE = "app/templates/hierarchy_settings.html"

WAVE4_HR_ORG_FILES = [
    HR_ATTENDANCE_TEMPLATE,
    HR_LEAVE_TEMPLATE,
    ORG_UNITS_TEMPLATE,
    ORG_UNITS_LIST_TEMPLATE,
    HIERARCHY_SETTINGS_TEMPLATE,
]

# HTML attribute syntax: bosluk + on<harfler> + '=' + tirnak. CSS/JS icindeki
# "javascript:" gibi metinsel string literal'leri yanlislikla yakalamaz.
_INLINE_EVENT_ATTR_RE = re.compile(r"""[\s]on[a-zA-Z]+\s*=\s*["']""")
_JS_HREF_RE = re.compile(r"""(?:href|src)\s*=\s*["']\s*javascript:""", re.IGNORECASE)
_JS_URL_ANYWHERE_RE = re.compile(r"""javascript:""", re.IGNORECASE)


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1) Statik kaynak-kod kontrati (Path.read_text + regex). Jinja if-bloklari
#    arkasina gizli butonlari da yakalar -- runtime render testi (asagida)
#    veri baglamina bagli oldugu icin bu bloklarin tumunu her zaman
#    tetiklemeyebilir; statik tarama kosulsuzdur.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative_path", WAVE4_HR_ORG_FILES)
def test_hr_org_file_has_no_inline_event_attributes(relative_path: str) -> None:
    text = _read(relative_path)
    matches = _INLINE_EVENT_ATTR_RE.findall(text)
    assert not matches, (
        f"{relative_path} icinde inline event-attribute (on*=) bulundu: {matches!r}. "
        "CSP script-src 'self' https: (unsafe-inline yok) altinda bunlar calismaz; "
        "data-* attribute + addEventListener kalibina cevrilmeli."
    )


@pytest.mark.parametrize("relative_path", WAVE4_HR_ORG_FILES)
def test_hr_org_file_has_no_javascript_href(relative_path: str) -> None:
    text = _read(relative_path)
    assert not _JS_HREF_RE.search(text), (
        f"{relative_path} icinde href/src=\"javascript:...\" bulundu."
    )
    assert not _JS_URL_ANYWHERE_RE.search(text), (
        f"{relative_path} icinde beklenmedik bir javascript: metni bulundu."
    )


@pytest.mark.parametrize("relative_path", WAVE4_HR_ORG_FILES)
def test_hr_org_file_introduces_no_dangerous_js_sinks(relative_path: str) -> None:
    """Duzeltme sirasinda eval/new Function/document.write eklenmedigini dogrular."""
    text = _read(relative_path)
    for forbidden in ("eval(", "new Function(", "document.write("):
        assert forbidden not in text, f"{relative_path} icinde yasakli sink bulundu: {forbidden}"


def test_hr_attendance_both_delete_forms_use_data_confirm() -> None:
    """Koordinatorun envanteri: bu dosyada 2 ayri silme formu (devamsizlik
    kaydi + vekalet kaydi) farkli confirm mesajlariyla vardi. Ikisinin de
    data-confirm karsiliginin birebir metinle korundugunu dogrular."""
    text = _read(HR_ATTENDANCE_TEMPLATE)
    assert "onsubmit=" not in text

    assert 'data-confirm="Kayıt silinsin mi?"' in text
    assert 'data-confirm="Vekâlet kaydı silinsin mi?"' in text

    assert "querySelectorAll('form[data-confirm]')" in text
    assert "addEventListener('submit'" in text
    assert "if (message && !window.confirm(message))" in text
    assert "event.preventDefault();" in text


def test_hr_leave_delete_form_uses_data_confirm() -> None:
    text = _read(HR_LEAVE_TEMPLATE)
    assert "onsubmit=" not in text

    assert 'data-confirm="İzin kaydı silinsin mi?"' in text

    assert "querySelectorAll('form[data-confirm]')" in text
    assert "addEventListener('submit'" in text
    assert "if (message && !window.confirm(message))" in text
    assert "event.preventDefault();" in text


def test_org_units_delete_form_uses_data_confirm() -> None:
    text = _read(ORG_UNITS_TEMPLATE)
    assert "onsubmit=" not in text

    assert 'data-confirm="Bu birimi silmek istediğinize emin misiniz?"' in text

    assert "querySelectorAll('form[data-confirm]')" in text
    assert "addEventListener('submit'" in text
    assert "if (message && !window.confirm(message))" in text
    assert "event.preventDefault();" in text


def test_org_units_list_delete_form_uses_data_confirm_and_keeps_inline_style() -> None:
    text = _read(ORG_UNITS_LIST_TEMPLATE)
    assert "onsubmit=" not in text

    assert 'data-confirm="Bu kayıt silinsin mi?"' in text
    # style="display:inline;" attribute'u korunmali (davranis paritesi).
    assert 'style="display:inline;"' in text

    assert "querySelectorAll('form[data-confirm]')" in text
    assert "addEventListener('submit'" in text
    assert "if (message && !window.confirm(message))" in text
    assert "event.preventDefault();" in text


def test_hierarchy_settings_period_select_uses_data_nav_attributes() -> None:
    """Ozel durum: confirm degil, navigate. Orijinal onchange
    `window.location='...?period_id=' + this.value + '&scope=...'` kurgusu
    data-nav-base/data-nav-scope + change listener'a tasindi; URL parcalari
    (period_id=, &scope=) birebir korunmali."""
    text = _read(HIERARCHY_SETTINGS_TEMPLATE)
    assert "onchange=" not in text

    assert "data-nav-base=" in text
    assert "data-nav-scope=" in text

    assert "querySelector('select[data-nav-base]')" in text
    assert "addEventListener('change'" in text
    assert "getAttribute('data-nav-base')" in text
    assert "getAttribute('data-nav-scope')" in text
    assert "?period_id=" in text
    assert "&scope=" in text


def test_org_units_and_org_units_list_csrf_tokens_untouched() -> None:
    """org_units.html ve org_units_list.html'deki CSRF token input'lari
    handler donusumunden etkilenmemis olmali (hem toggle-active hem
    delete formlarinda)."""
    org_units_text = _read(ORG_UNITS_TEMPLATE)
    assert org_units_text.count('<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">') == 2

    org_units_list_text = _read(ORG_UNITS_LIST_TEMPLATE)
    assert '<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">' in org_units_list_text


# ---------------------------------------------------------------------------
# 2) Calisma-zamani render kontrolu: gercek Flask app + gercek Jinja motoru
#    ile `render_template` cagrisi (bkz. `app` fixture, tests/conftest.py).
#    Bu bes template login_required/menu_key_required arkasinda kompleks is
#    verisi bekleyen route'lar tarafindan doldurulur; route'un tam
#    auth+rol+menu-key+DB zincirini burada yeniden kurmak bu kontratin
#    kapsamini asar. Bunun yerine template'ler dogrudan `render_template()`
#    ile (bos/varsayilan baglamda) render edilir -- tum degiskenler Jinja
#    `ChainableUndefined` + `if X %}...{% endif %}` / `or` korumalariyla
#    yazildigi icin bu gercekten calisir (asagida dogrulanmistir) ve gercek
#    Jinja derleme+yurutmeyi kullanir. Bu HALA gercek bir tarayici testi
#    DEGILDIR: CSP enforce edilmis bir tarayicida script'lerin fiilen
#    calistigini kanitlamaz; yalnizca uretilen HTML'de inline
#    event-attribute/javascript: href kalmadigini ve script bloklarinin
#    gercekten render edildigini dogrular. Kayit-donen dallardaki
#    (attendance_rows, leaves, rows vb. dolu) data-confirm butonlari bu
#    bos-baglam render'inda tetiklenmez (Jinja `{% for row in ... %}`
#    bos listede hic calismaz); o dallar yukaridaki statik kaynak
#    testleriyle kosulsuz kilitlenir.
# ---------------------------------------------------------------------------

_TEMPLATE_NAME_BY_PATH = {
    HR_ATTENDANCE_TEMPLATE: "hr_attendance.html",
    HR_LEAVE_TEMPLATE: "hr_leave.html",
    ORG_UNITS_TEMPLATE: "org_units.html",
    ORG_UNITS_LIST_TEMPLATE: "org_units_list.html",
    HIERARCHY_SETTINGS_TEMPLATE: "hierarchy_settings.html",
}


@pytest.mark.parametrize("relative_path", WAVE4_HR_ORG_FILES)
def test_hr_org_template_render_has_no_inline_handlers(app, relative_path: str) -> None:
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
    for forbidden in ("eval(", "new Function(", "document.write("):
        assert forbidden not in html, f"{template_name} render ciktisinda yasakli sink bulundu: {forbidden}"


def test_hierarchy_settings_render_includes_data_nav_and_original_url_parts(app) -> None:
    """Bos baglamda bile (selected_period yok) dönem select'i ve script
    hook'u her zaman render edilir; bu, data-nav-base/data-nav-scope
    attribute'larinin ve orijinal URL kurgusunun (period_id=, &scope=)
    CSP nonce'u ile birlikte gercekten sayfaya cikacagini dogrular."""
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template("hierarchy_settings.html")

    assert "data-nav-base=" in html
    assert "data-nav-scope=" in html
    assert "querySelector('select[data-nav-base]')" in html
    assert "?period_id=" in html
    assert "&scope=" in html


def test_hr_attendance_render_includes_confirm_script_hook(app) -> None:
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template("hr_attendance.html")

    assert "querySelectorAll('form[data-confirm]')" in html
    assert "addEventListener('submit'" in html


def test_hr_leave_render_includes_confirm_script_hook(app) -> None:
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template("hr_leave.html")

    assert "querySelectorAll('form[data-confirm]')" in html
    assert "addEventListener('submit'" in html


def test_org_units_render_includes_confirm_script_hook(app) -> None:
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template("org_units.html")

    assert "querySelectorAll('form[data-confirm]')" in html
    assert "addEventListener('submit'" in html


def test_org_units_list_render_includes_confirm_script_hook(app) -> None:
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template("org_units_list.html")

    assert "querySelectorAll('form[data-confirm]')" in html
    assert "addEventListener('submit'" in html
