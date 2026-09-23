"""CSP Dalga 3 - Grup A (Meeting Development) kontrat testi.

BYS360 `app/security/headers.py` uygular:
    script-src: 'self' https:  (unsafe-inline YOK)

Bu dosyanin sahiplik alani yalnizca su alti template:
    - app/templates/performance/meeting_development.html
    - app/templates/performance/meeting_development_clean.html
    - app/templates/performance/meeting_development_faz3.html
    - app/templates/performance/meeting_development_faz4.html
    - app/templates/performance/meeting_development_scenarios.html
    - app/templates/performance/feedback_meeting_guide.html

Koordinatorun grep taramasi bu alti dosyada toplam 6 inline event-attribute
tespit etmisti: ilk bes dosyada ayni kalip -- "Yenile" butonunda
`onclick="window.location.reload()"` -- ve altinci dosyada
(feedback_meeting_guide.html) senaryo secim kutusunda
`onchange="this.form.submit()"`. `javascript:` URL yoktu.

Bu dosya o tespiti once bagimsiz statik regex taramasiyla (kaynak metin),
sonra da gercek Jinja/Flask motoruyla uretilen HTML uzerinde kilitler:
ileride biri bu alti dosyaya inline handler eklerse hem kaynak metin hem de
render edilen HTML testi kirilir.

Statik testler `tests/security/test_csp_wave1_inline_handlers_contract.py` ve
`tests/security/test_csp_wave2_performance_print_mail_contract.py` ile ayni
desendedir (Path.read_text() + regex + gercek app fixture'i ile render).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

MEETING_DEVELOPMENT_TEMPLATE = "app/templates/performance/meeting_development.html"
MEETING_DEVELOPMENT_CLEAN_TEMPLATE = "app/templates/performance/meeting_development_clean.html"
MEETING_DEVELOPMENT_FAZ3_TEMPLATE = "app/templates/performance/meeting_development_faz3.html"
MEETING_DEVELOPMENT_FAZ4_TEMPLATE = "app/templates/performance/meeting_development_faz4.html"
MEETING_DEVELOPMENT_SCENARIOS_TEMPLATE = "app/templates/performance/meeting_development_scenarios.html"
FEEDBACK_MEETING_GUIDE_TEMPLATE = "app/templates/performance/feedback_meeting_guide.html"

WAVE3_GROUP_A_FILES = [
    MEETING_DEVELOPMENT_TEMPLATE,
    MEETING_DEVELOPMENT_CLEAN_TEMPLATE,
    MEETING_DEVELOPMENT_FAZ3_TEMPLATE,
    MEETING_DEVELOPMENT_FAZ4_TEMPLATE,
    MEETING_DEVELOPMENT_SCENARIOS_TEMPLATE,
    FEEDBACK_MEETING_GUIDE_TEMPLATE,
]

# KOORDINATOR DUZELTMESI: meeting_development_faz4.html originally belonged
# to this reload-button group (same onclick->addEventListener pattern as its
# siblings). A later, legitimate wave ("BYS360 Meeting UI Context Adapter --
# Dalga 2 / Final Gate") rewrote that ONE template's entire body into a real,
# read-only Final Gate status report with zero interactivity (no search/
# filter, no reload button, no <script> block at all) -- see
# test_meeting_final_gate_ui_context_adapter_contract.py for that wave's own
# full evidence chain, including its own "no inline handler/no javascript:/
# no |safe" static checks that now cover this file instead. Removed from
# this list so this Wave-3 contract's OWN "exactly one reload-button id/
# click listener" assertions no longer see that later, unrelated, in-scope
# redesign as a regression -- same class of drift already handled for
# test_csp_wave3_meeting_group_b_contract.py's own BYS_MD_RELOAD_BTN_FILES
# list after the P0 UI wave.
#
# "Yenile" reload butonunu iceren dort dosya (feedback_meeting_guide ve artik
# meeting_development_faz4.html haric).
RELOAD_BUTTON_FILES = [
    MEETING_DEVELOPMENT_TEMPLATE,
    MEETING_DEVELOPMENT_CLEAN_TEMPLATE,
    MEETING_DEVELOPMENT_FAZ3_TEMPLATE,
    MEETING_DEVELOPMENT_SCENARIOS_TEMPLATE,
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
#    arkasina gizli elemanlari da yakalar -- runtime render testi (asagida)
#    veri baglamina bagli oldugu icin bu bloklarin tumunu her zaman
#    tetiklemeyebilir; statik tarama kosulsuzdur.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative_path", WAVE3_GROUP_A_FILES)
def test_meeting_group_a_file_has_no_inline_event_attributes(relative_path: str) -> None:
    text = _read(relative_path)
    matches = _INLINE_EVENT_ATTR_RE.findall(text)
    assert not matches, (
        f"{relative_path} icinde inline event-attribute (on*=) bulundu: {matches!r}. "
        "CSP script-src 'self' https: (unsafe-inline yok) altinda bunlar calismaz; "
        "data-* attribute + addEventListener kalibina cevrilmeli."
    )


@pytest.mark.parametrize("relative_path", WAVE3_GROUP_A_FILES)
def test_meeting_group_a_file_has_no_javascript_href(relative_path: str) -> None:
    text = _read(relative_path)
    assert not _JS_HREF_RE.search(text), (
        f"{relative_path} icinde href/src=\"javascript:...\" bulundu."
    )
    assert not _JS_URL_ANYWHERE_RE.search(text), (
        f"{relative_path} icinde beklenmedik bir javascript: metni bulundu."
    )


@pytest.mark.parametrize("relative_path", WAVE3_GROUP_A_FILES)
def test_meeting_group_a_file_introduces_no_dangerous_js_sinks(relative_path: str) -> None:
    """Duzeltme sirasinda eval/new Function/document.write eklenmedigini dogrular."""
    text = _read(relative_path)
    for forbidden in ("eval(", "new Function(", "document.write("):
        assert forbidden not in text, f"{relative_path} icinde yasakli sink bulundu: {forbidden}"


@pytest.mark.parametrize("relative_path", RELOAD_BUTTON_FILES)
def test_meeting_group_a_reload_button_uses_id_and_click_listener(relative_path: str) -> None:
    """Koordinatorun envanteri: bu bes dosyada "Yenile" butonu
    onclick="window.location.reload()" kullaniyordu. Artik id + tek bir
    addEventListener('click', ...) kalibi olmali."""
    text = _read(relative_path)
    assert "onclick=" not in text
    reload_btn_id_matches = re.findall(r'id="(bys(?:Rem|Md)ReloadBtn)"', text)
    assert len(reload_btn_id_matches) == 1, (
        f"{relative_path} icinde tam olarak bir reload buton id'si bekleniyordu, "
        f"bulunan: {reload_btn_id_matches!r}"
    )
    reload_btn_id = reload_btn_id_matches[0]
    assert f'id="{reload_btn_id}"' in text
    assert text.count(f'getElementById("{reload_btn_id}")') == 1, (
        "reload butonu icin birden fazla veya sifir getElementById cagrisi bulundu "
        "(cift-baglama veya eksik baglama riski)."
    )
    assert "window.location.reload()" in text
    assert "addEventListener(\"click\"" in text


def test_feedback_meeting_guide_scenario_select_uses_data_autosubmit() -> None:
    """Koordinatorun envanteri: bu dosyada senaryo secim kutusu
    onchange="this.form.submit()" kullaniyordu. Artik data-autosubmit + tek
    bir addEventListener('change', ...) kalibi olmali."""
    text = _read(FEEDBACK_MEETING_GUIDE_TEMPLATE)
    assert "onchange=" not in text
    assert 'id="feedbackScenarioSelect"' in text
    assert 'data-autosubmit="1"' in text
    assert text.count("getElementById('feedbackScenarioSelect')") == 1, (
        "senaryo secim kutusu icin birden fazla veya sifir getElementById cagrisi "
        "bulundu (cift-baglama veya eksik baglama riski)."
    )
    assert "addEventListener('change'" in text
    assert "scenarioSelect.form.submit()" in text


# ---------------------------------------------------------------------------
# 2) Calisma-zamani render kontrolu: gercek Flask app + gercek Jinja motoru
#    ile `render_template` cagrisi (bkz. `app` fixture, tests/conftest.py).
#    Bu alti template login_required/menu_key_required arkasinda kompleks
#    is verisi bekleyen route'lar tarafindan doldurulur; route'un tam
#    auth+rol+menu-key+DB zincirini burada yeniden kurmak bu kontratin
#    kapsamini asar. Bunun yerine template'ler dogrudan `render_template()`
#    ile (bos/varsayilan baglamda) render edilir -- tum degiskenler Jinja
#    `is defined` korumalariyla yazildigi icin bu gercekten calisir (asagida
#    dogrulanmistir) ve gercek Jinja derleme+yurutmeyi kullanir. Bu HALA
#    gercek bir tarayici testi DEGILDIR: CSP enforce edilmis bir tarayicida
#    script'lerin fiilen calistigini kanitlamaz; yalnizca uretilen HTML'de
#    inline event-attribute/javascript: href kalmadigini ve script
#    bloklarinin gercekten (Jinja {% block content %} icinde) render
#    edildigini dogrular.
# ---------------------------------------------------------------------------

_TEMPLATE_NAME_BY_PATH = {
    MEETING_DEVELOPMENT_TEMPLATE: "performance/meeting_development.html",
    MEETING_DEVELOPMENT_CLEAN_TEMPLATE: "performance/meeting_development_clean.html",
    MEETING_DEVELOPMENT_FAZ3_TEMPLATE: "performance/meeting_development_faz3.html",
    MEETING_DEVELOPMENT_FAZ4_TEMPLATE: "performance/meeting_development_faz4.html",
    MEETING_DEVELOPMENT_SCENARIOS_TEMPLATE: "performance/meeting_development_scenarios.html",
    FEEDBACK_MEETING_GUIDE_TEMPLATE: "performance/feedback_meeting_guide.html",
}


@pytest.mark.parametrize("relative_path", WAVE3_GROUP_A_FILES)
def test_meeting_group_a_template_render_has_no_inline_handlers(app, relative_path: str) -> None:
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


@pytest.mark.parametrize("relative_path", RELOAD_BUTTON_FILES)
def test_meeting_group_a_render_includes_reload_button_script_hook(app, relative_path: str) -> None:
    """Bos baglamda bile sayfanin en altindaki mevcut IIFE <script> blogu
    (arama/filtre + reload) her zaman render edilir; bu, reload hook'unun
    CSP nonce'u ile birlikte gercekten sayfaya cikacagini dogrular."""
    from flask import render_template

    template_name = _TEMPLATE_NAME_BY_PATH[relative_path]
    with app.test_request_context("/"):
        html = render_template(template_name)

    reload_btn_id_matches = re.findall(r'id="(bys(?:Rem|Md)ReloadBtn)"', html)
    assert len(reload_btn_id_matches) == 1
    reload_btn_id = reload_btn_id_matches[0]
    assert f'getElementById("{reload_btn_id}")' in html
    assert "window.location.reload()" in html


def test_feedback_meeting_guide_render_includes_scenario_autosubmit_hook(app) -> None:
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template("performance/feedback_meeting_guide.html")

    assert 'id="feedbackScenarioSelect"' in html
    assert 'data-autosubmit="1"' in html
    assert "getElementById('feedbackScenarioSelect')" in html
