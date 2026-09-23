"""CSP Dalga 3 - Toplanti Grubu B kontrat testi.

BYS360 `app/security/headers.py` uygular:
    script-src: 'self' https:  (unsafe-inline YOK)

Bu dosyanin sahiplik alani yalnizca su alti template ("Grup B"):
    - app/templates/performance/meeting_p0_completion.html
    - app/templates/performance/meeting_p1_scope.html
    - app/templates/performance/meeting_p2_archive_notes.html
    - app/templates/performance/meeting_p3_reminders.html
    - app/templates/performance/meeting_final_closure.html
    - app/templates/performance/meeting_rule_enforcement.html

Koordinatorun envanteri: bu alti dosyanin her birinde AYNI kalip vardi --
filtre toolbar'inin sonundaki "Yenile" butonu icin tek bir
`onclick="window.location.reload()"` (dosya basina 1 adet, toplam 6).
`javascript:` URL'i hicbir dosyada yoktu.

Not: statik metin karsilastirmasi sirasinda 5 dosyanin (meeting_p0_completion,
meeting_p1_scope, meeting_p2_archive_notes, meeting_final_closure,
meeting_rule_enforcement) BYTE-ICIN-BYTE ayni oldugu (md5) dogrulanmistir --
bu koordinatorun bilgisi disinda bir bulgu degil, sadece bu testin neden 5
dosyada ayni id ("bysMdReloadBtn") kullandigini aciklar. Altinci dosya
(meeting_p3_reminders.html) farkli bir CSS/JS ad alani kullanir
(bys-rem-*/bysRemSearch/bysRemStatus) ve butonu "bysRemReloadBtn" id'sini
alir.

Duzeltme deseni Wave 1/2 ile aynidir: `onclick=` kaldirilir, butona
benzersiz bir `id` eklenir, dosyanin altindaki mevcut arama/filtre IIFE'si
GENISLETILIR (yeni script blogu ACILMAZ) ve icine
`getElementById(...).addEventListener('click', ...)` eklenir.

Statik testler `tests/security/test_csp_wave1_inline_handlers_contract.py`
ve `tests/security/test_csp_wave2_performance_print_mail_contract.py` ile
ayni desendedir (Path.read_text() + regex + gercek app fixture'i ile render).
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

P0_COMPLETION_TEMPLATE = "app/templates/performance/meeting_p0_completion.html"
P1_SCOPE_TEMPLATE = "app/templates/performance/meeting_p1_scope.html"
P2_ARCHIVE_NOTES_TEMPLATE = "app/templates/performance/meeting_p2_archive_notes.html"
P3_REMINDERS_TEMPLATE = "app/templates/performance/meeting_p3_reminders.html"
FINAL_CLOSURE_TEMPLATE = "app/templates/performance/meeting_final_closure.html"
RULE_ENFORCEMENT_TEMPLATE = "app/templates/performance/meeting_rule_enforcement.html"

# KOORDINATOR DUZELTMESI: meeting_p0_completion.html originally belonged to
# this six-file "Group B" (same onclick->addEventListener reload-button
# pattern as its siblings). A later, legitimate wave ("BYS360 Meeting UI
# Context Adapter -- Dalga 1 / P0 Completion") rewrote that ONE template's
# entire body into a real, read-only P0 status screen with zero
# interactivity (no search/filter, no reload button, no <script> block at
# all) -- see test_meeting_p0_completion_ui_context_adapter_contract.py for
# that wave's own full evidence chain, including its own "no inline
# handler/no javascript:/no |safe" static checks that now cover this file
# instead. Removed from both lists below so this Wave-3 contract's OWN
# "exactly one reload-button click listener" / "bysMdReloadBtn id present"
# assertions no longer see that later, unrelated, in-scope redesign as a
# regression -- same class of drift already handled for
# test_csp_style3c_meeting_family_group_a_contract.py's own scope-guard test
# and test_meeting_p0_completion_settings_query_dialect_fix_contract.py's
# own MEETING_FAMILY_TEMPLATES list.
WAVE3_MEETING_GROUP_B_FILES = [
    P1_SCOPE_TEMPLATE,
    P2_ARCHIVE_NOTES_TEMPLATE,
    P3_REMINDERS_TEMPLATE,
    FINAL_CLOSURE_TEMPLATE,
    RULE_ENFORCEMENT_TEMPLATE,
]

# "bysMdReloadBtn" id'sini kullanan dosyalar (kalan 4 tanesi byte-ayni
# icerige sahip; meeting_p0_completion.html yukaridaki KOORDINATOR
# DUZELTMESI nedeniyle bu listeden cikarildi).
BYS_MD_RELOAD_BTN_FILES = [
    P1_SCOPE_TEMPLATE,
    P2_ARCHIVE_NOTES_TEMPLATE,
    FINAL_CLOSURE_TEMPLATE,
    RULE_ENFORCEMENT_TEMPLATE,
]

# HTML attribute syntax: bosluk + on<harfler> + '=' + tirnak. CSS/JS icindeki
# "javascript:" gibi metinsel string literal'leri yanlislikla yakalamaz.
_INLINE_EVENT_ATTR_RE = re.compile(r"""[\s]on[a-zA-Z]+\s*=\s*["']""")
_JS_HREF_RE = re.compile(r"""(?:href|src)\s*=\s*["']\s*javascript:""", re.IGNORECASE)
_JS_URL_ANYWHERE_RE = re.compile(r"""javascript:""", re.IGNORECASE)


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1) Statik kaynak-kod kontrati (Path.read_text + regex).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative_path", WAVE3_MEETING_GROUP_B_FILES)
def test_meeting_group_b_file_has_no_inline_event_attributes(relative_path: str) -> None:
    text = _read(relative_path)
    matches = _INLINE_EVENT_ATTR_RE.findall(text)
    assert not matches, (
        f"{relative_path} icinde inline event-attribute (on*=) bulundu: {matches!r}. "
        "CSP script-src 'self' https: (unsafe-inline yok) altinda bunlar calismaz; "
        "id + addEventListener kalibina cevrilmeli."
    )


@pytest.mark.parametrize("relative_path", WAVE3_MEETING_GROUP_B_FILES)
def test_meeting_group_b_file_has_no_javascript_href(relative_path: str) -> None:
    text = _read(relative_path)
    assert not _JS_HREF_RE.search(text), (
        f"{relative_path} icinde href/src=\"javascript:...\" bulundu."
    )
    assert not _JS_URL_ANYWHERE_RE.search(text), (
        f"{relative_path} icinde beklenmedik bir javascript: metni bulundu."
    )


@pytest.mark.parametrize("relative_path", WAVE3_MEETING_GROUP_B_FILES)
def test_meeting_group_b_file_introduces_no_dangerous_js_sinks(relative_path: str) -> None:
    """Duzeltme sirasinda eval/new Function/document.write eklenmedigini dogrular."""
    text = _read(relative_path)
    for forbidden in ("eval(", "new Function(", "document.write("):
        assert forbidden not in text, f"{relative_path} icinde yasakli sink bulundu: {forbidden}"


@pytest.mark.parametrize("relative_path", WAVE3_MEETING_GROUP_B_FILES)
def test_meeting_group_b_file_has_exactly_one_click_listener(relative_path: str) -> None:
    """Koordinatorun envanteri: her dosyada tam olarak 1 inline onclick vardi
    (Yenile butonu). Duzeltme sonrasi tam olarak 1 addEventListener('click', ...)
    eklenmis olmali -- ne eksik ne fazla (cift baglama yasak)."""
    text = _read(relative_path)
    assert text.count('addEventListener("click"') == 1, (
        f"{relative_path}: tam olarak 1 adet addEventListener(\"click\", ...) bekleniyordu."
    )


@pytest.mark.parametrize("relative_path", BYS_MD_RELOAD_BTN_FILES)
def test_bys_md_files_use_reload_btn_id_and_listener(relative_path: str) -> None:
    text = _read(relative_path)
    assert 'id="bysMdReloadBtn"' in text
    assert 'getElementById("bysMdReloadBtn")' in text
    assert "window.location.reload()" in text


def test_p3_reminders_uses_its_own_reload_btn_id_and_listener() -> None:
    """meeting_p3_reminders.html digerlerinden farkli ad alanina (bys-rem-*)
    sahiptir; reload butonu da kendi ad alanina uygun id alir."""
    text = _read(P3_REMINDERS_TEMPLATE)
    assert 'id="bysRemReloadBtn"' in text
    assert 'getElementById("bysRemReloadBtn")' in text
    assert "window.location.reload()" in text


@pytest.mark.parametrize("relative_path", WAVE3_MEETING_GROUP_B_FILES)
def test_meeting_group_b_reload_button_keeps_original_classes(relative_path: str) -> None:
    """Butonun class/attribute'lari korunmali; sadece onclick kaldirilip id eklenmeli."""
    text = _read(relative_path)
    assert 'class="btn btn-sm btn-outline-secondary"' in text
    assert '<i class="fa-solid fa-rotate-right me-1"></i> Yenile' in text


@pytest.mark.parametrize("relative_path", WAVE3_MEETING_GROUP_B_FILES)
def test_meeting_group_b_file_does_not_use_fake_data_onclick_attribute(relative_path: str) -> None:
    """Inline handler icerigini string olarak baska bir data-* attribute'a
    tasima yasaktir (orn. data-onclick="..."). Gercek addEventListener
    kullanilmali."""
    text = _read(relative_path)
    assert "data-onclick" not in text


# ---------------------------------------------------------------------------
# 2) Calisma-zamani render kontrolu: gercek Flask app + gercek Jinja motoru
#    ile `render_template` cagrisi (bkz. `app` fixture, tests/conftest.py).
#    Bu alti template login_required/menu_key_required arkasindaki route'lar
#    tarafindan is verisi (page_summary, reminder_items, overdue_items vb.)
#    ile doldurulur; route'un tam auth+rol+menu-key+DB zincirini burada
#    yeniden kurmak bu kontratin kapsamini asar. Template'ler tum
#    degiskenleri Jinja `{% set x = x if x is defined and x else ... %}` /
#    `|default(...)` korumalariyla yazdigi icin bos baglamda dogrudan
#    render_template() ile calisir (asagida dogrulanmistir). `safe_url_for`
#    (app/route_support.py) endpoint bulunamazsa BuildError'i yakalayip "#"
#    fallback dondugu icin bos baglamda url_for zinciri patlamaz.
#    Bu HALA gercek bir tarayici testi DEGILDIR: CSP enforce edilmis bir
#    tarayicida script'lerin fiilen calistigini kanitlamaz; yalnizca uretilen
#    HTML'de inline event-attribute/javascript: href kalmadigini ve script
#    bloklarinin gercekten render edildigini dogrular.
# ---------------------------------------------------------------------------

_TEMPLATE_NAME_BY_PATH = {
    P0_COMPLETION_TEMPLATE: "performance/meeting_p0_completion.html",
    P1_SCOPE_TEMPLATE: "performance/meeting_p1_scope.html",
    P2_ARCHIVE_NOTES_TEMPLATE: "performance/meeting_p2_archive_notes.html",
    P3_REMINDERS_TEMPLATE: "performance/meeting_p3_reminders.html",
    FINAL_CLOSURE_TEMPLATE: "performance/meeting_final_closure.html",
    RULE_ENFORCEMENT_TEMPLATE: "performance/meeting_rule_enforcement.html",
}


@pytest.mark.parametrize("relative_path", WAVE3_MEETING_GROUP_B_FILES)
def test_meeting_group_b_template_render_has_no_inline_handlers(app, relative_path: str) -> None:
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


@pytest.mark.parametrize("relative_path", BYS_MD_RELOAD_BTN_FILES)
def test_bys_md_template_render_includes_reload_hook(app, relative_path: str) -> None:
    """Bos baglamda bile sayfanin en altindaki ortak <script> blogu (arama/
    filtre + reload-btn listener) her zaman render edilir; bu hook'un CSP
    nonce'u ile birlikte gercekten sayfaya cikacagini dogrular."""
    from flask import render_template

    template_name = _TEMPLATE_NAME_BY_PATH[relative_path]
    with app.test_request_context("/"):
        html = render_template(template_name)

    assert 'id="bysMdReloadBtn"' in html
    assert 'getElementById("bysMdReloadBtn")' in html
    assert "addEventListener(\"click\"" in html
    assert "window.location.reload()" in html


def test_p3_reminders_template_render_includes_reload_hook(app) -> None:
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template("performance/meeting_p3_reminders.html")

    assert 'id="bysRemReloadBtn"' in html
    assert 'getElementById("bysRemReloadBtn")' in html
    assert "addEventListener(\"click\"" in html
    assert "window.location.reload()" in html
