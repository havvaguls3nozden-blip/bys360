"""CSP Dalga 2 - Ajan 3 (Performans) kontrat testi.

BYS360 `app/security/headers.py` uygular:
    script-src: 'self' https:  (unsafe-inline YOK)

Bu dosyanin sahiplik alani yalnizca su bes template:
    - app/templates/performance_hierarchy_assignments.html
    - app/templates/performance_mail_reminders.html
    - app/templates/performance_publish.html
    - app/templates/performance_reports_print.html
    - app/templates/performance_v2_phase6_print.html

Koordinatorun grep taramasi bu bes dosyada toplam 12 inline event-attribute
(onclick=/onchange=/onsubmit=) tespit etmisti; `javascript:` URL yoktu. Bu
dosya o tespiti once bagimsiz statik regex taramasiyla (kaynak metin),
sonra da gercek Jinja/Flask motoruyla uretilen HTML uzerinde kilitler:
ileride biri bu bes dosyaya inline handler eklerse hem kaynak metin hem de
render edilen HTML testi kirilir.

`performance/` alt dizini (meeting_*, process_engine_* vb.) bu dalganin
KAPSAMI DISINDADIR -- koordinator bilincli olarak sonraki bir dalgaya
birakti; bu dosya o alt dizine dokunmaz/test etmez.

Statik testler `tests/security/test_csp_wave1_inline_handlers_contract.py`
ve `tests/security/test_csp_wave2_dashboard_contract.py` ile ayni desendedir
(Path.read_text() + regex + gercek app fixture'i ile render).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

HIERARCHY_TEMPLATE = "app/templates/performance_hierarchy_assignments.html"
MAIL_REMINDERS_TEMPLATE = "app/templates/performance_mail_reminders.html"
PUBLISH_TEMPLATE = "app/templates/performance_publish.html"
REPORTS_PRINT_TEMPLATE = "app/templates/performance_reports_print.html"
V2_PHASE6_PRINT_TEMPLATE = "app/templates/performance_v2_phase6_print.html"

WAVE2_PERFORMANCE_FILES = [
    HIERARCHY_TEMPLATE,
    MAIL_REMINDERS_TEMPLATE,
    PUBLISH_TEMPLATE,
    REPORTS_PRINT_TEMPLATE,
    V2_PHASE6_PRINT_TEMPLATE,
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
#    (orn. {% if selected_period %}) arkasina gizli butonlari da yakalar --
#    runtime render testi (asagida) veri baglamina bagli oldugu icin bu
#    bloklarin tumunu her zaman tetiklemeyebilir; statik tarama kosulsuzdur.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative_path", WAVE2_PERFORMANCE_FILES)
def test_performance_file_has_no_inline_event_attributes(relative_path: str) -> None:
    text = _read(relative_path)
    matches = _INLINE_EVENT_ATTR_RE.findall(text)
    assert not matches, (
        f"{relative_path} icinde inline event-attribute (on*=) bulundu: {matches!r}. "
        "CSP script-src 'self' https: (unsafe-inline yok) altinda bunlar calismaz; "
        "data-* attribute + addEventListener kalibina cevrilmeli."
    )


@pytest.mark.parametrize("relative_path", WAVE2_PERFORMANCE_FILES)
def test_performance_file_has_no_javascript_href(relative_path: str) -> None:
    text = _read(relative_path)
    assert not _JS_HREF_RE.search(text), (
        f"{relative_path} icinde href/src=\"javascript:...\" bulundu."
    )
    assert not _JS_URL_ANYWHERE_RE.search(text), (
        f"{relative_path} icinde beklenmedik bir javascript: metni bulundu."
    )


@pytest.mark.parametrize("relative_path", WAVE2_PERFORMANCE_FILES)
def test_performance_file_introduces_no_dangerous_js_sinks(relative_path: str) -> None:
    """Duzeltme sirasinda eval/new Function/document.write eklenmedigini dogrular."""
    text = _read(relative_path)
    for forbidden in ("eval(", "new Function(", "document.write("):
        assert forbidden not in text, f"{relative_path} icinde yasakli sink bulundu: {forbidden}"


def test_hierarchy_assignments_auto_assign_form_uses_data_confirm() -> None:
    text = _read(HIERARCHY_TEMPLATE)
    assert 'onsubmit=' not in text
    assert 'id="autoAssignFilteredForm"' in text
    assert 'data-confirm="Filtrelenen kay' in text
    assert "getElementById('autoAssignFilteredForm')" in text
    assert "addEventListener('submit'" in text


def test_publish_unpublish_period_form_uses_data_confirm() -> None:
    text = _read(PUBLISH_TEMPLATE)
    assert 'onsubmit=' not in text
    assert 'id="unpublishPeriodForm"' in text
    assert 'data-confirm="Bu d' in text
    assert 'getElementById("unpublishPeriodForm")' in text
    assert 'addEventListener("submit"' in text


def test_reports_print_button_uses_id_and_click_listener() -> None:
    text = _read(REPORTS_PRINT_TEMPLATE)
    assert 'onclick=' not in text
    assert 'id="printReportBtn"' in text
    assert "getElementById('printReportBtn')" in text
    assert "addEventListener('click'" in text
    assert "window.print()" in text


def test_v2_phase6_print_buttons_use_ids_and_click_listeners() -> None:
    text = _read(V2_PHASE6_PRINT_TEMPLATE)
    assert 'onclick=' not in text
    assert 'id="phase6CloseBtn"' in text
    assert 'id="phase6PrintBtn"' in text
    assert "getElementById('phase6CloseBtn')" in text
    assert "getElementById('phase6PrintBtn')" in text
    assert text.count("addEventListener('click'") == 2
    assert "window.close()" in text
    assert "window.print()" in text


def test_mail_reminders_all_seven_inline_handlers_replaced() -> None:
    """Koordinatorun envanteri: bu dosyada 7 inline event-attribute vardi
    (1 onchange + 6 onclick). Bu test onlarin data-* karsiliklarinin
    hepsinin mevcut oldugunu tek tek dogrular."""
    text = _read(MAIL_REMINDERS_TEMPLATE)
    assert 'onchange=' not in text
    assert 'onclick=' not in text

    assert 'data-autosubmit="1"' in text
    assert "getElementById('period_id')" in text

    expected_confirm_messages = [
        "Seçili dönem için tüm uygun amirlere hatırlatma maili gönderilsin mi?",
        "Mail otomasyonu seçili kurallarla çalıştırılsın mı?",
        "Seçili yöneticilere hatırlatma gönderilsin mi?",
        "Bekleme süresi aktif. Buna rağmen zorla tekrar gönderilsin mi?",
        "Bu dönem için başarısız tüm mailler yeniden denensin mi?",
    ]
    for message in expected_confirm_messages:
        assert f'data-confirm="{message}"' in text, f"beklenen data-confirm bulunamadi: {message!r}"

    # item.manager.ad / item.manager.soyad ile dinamik uretilen mesaj (dongude,
    # per-satir farkli metin uretir; sabit metin degil, kalip aranir).
    assert 'data-confirm="{{ item.manager.ad }} {{ item.manager.soyad }}' in text

    assert "querySelectorAll('[data-confirm]')" in text
    assert "addEventListener('click'" in text


def test_mail_reminders_confirm_delegation_calls_preventdefault_on_cancel() -> None:
    """Confirm iptal edildiginde submit/click varsayilan davranisinin
    engellendigini (event.preventDefault) kaynak seviyesinde dogrular --
    aksi halde 'iptal' butonun/formun yine de tetiklenmesine yol acar."""
    text = _read(MAIL_REMINDERS_TEMPLATE)
    assert "if (message && !window.confirm(message))" in text
    assert "event.preventDefault();" in text


# ---------------------------------------------------------------------------
# 2) Calisma-zamani render kontrolu: gercek Flask app + gercek Jinja motoru
#    ile `render_template` cagrisi (bkz. `app` fixture, tests/conftest.py).
#    Bu bes template login_required/admin_required/menu_key_required arkasinda
#    kompleks is verisi (donem, yonetici listesi, mail_health vb.) bekleyen
#    route'lar tarafindan doldurulur; route'un tam auth+rol+menu-key+DB
#    zincirini burada yeniden kurmak bu kontratin kapsamini asar. Bunun
#    yerine template'ler dogrudan `render_template()` ile (bos/varsayilan
#    baglamda) render edilir -- tum degiskenler Jinja `|default(...)` /
#    `if X %}...{% endif %}` korumalariyla yazildigi icin bu gercekten
#    calisir (asagida dogrulanmistir) ve gercek Jinja derleme+yurutmeyi
#    kullanir. Bu HALA gercek bir tarayici testi DEGILDIR: CSP enforce
#    edilmis bir tarayicida script'lerin fiilen calistigini kanitlamaz;
#    yalnizca uretilen HTML'de inline event-attribute/javascript: href
#    kalmadigini ve script bloklarinin gercekten render edildigini dogrular.
#    Donem-secili (selected_period dolu) dallardaki data-confirm butonlari
#    bu bos-baglam render'inda tetiklenmez (Jinja {% if selected_period %}
#    ile korunur); o dallar yukaridaki statik kaynak testleriyle kosulsuz
#    kilitlenir.
# ---------------------------------------------------------------------------

_TEMPLATE_NAME_BY_PATH = {
    HIERARCHY_TEMPLATE: "performance_hierarchy_assignments.html",
    MAIL_REMINDERS_TEMPLATE: "performance_mail_reminders.html",
    PUBLISH_TEMPLATE: "performance_publish.html",
    REPORTS_PRINT_TEMPLATE: "performance_reports_print.html",
    V2_PHASE6_PRINT_TEMPLATE: "performance_v2_phase6_print.html",
}


@pytest.mark.parametrize("relative_path", WAVE2_PERFORMANCE_FILES)
def test_performance_template_render_has_no_inline_handlers(app, relative_path: str) -> None:
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


def test_mail_reminders_render_includes_script_hooks_for_toggle_and_autosubmit(app) -> None:
    """Bos baglamda bile (selected_period yok) sayfanin en altindaki ortak
    <script> blogu (toggle-all + autosubmit + data-confirm delegation) her
    zaman render edilir; bu, bu hook'larin CSP nonce'u ile birlikte gercekten
    sayfaya cikacagini dogrular."""
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template("performance_mail_reminders.html")

    assert "toggle-all-managers" in html
    assert "querySelectorAll('[data-confirm]')" in html
    assert "getElementById('period_id')" in html


def test_v2_phase6_print_render_includes_close_and_print_hooks(app) -> None:
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template("performance_v2_phase6_print.html")

    assert 'id="phase6CloseBtn"' in html
    assert 'id="phase6PrintBtn"' in html
    assert "window.close()" in html
    assert "window.print()" in html
