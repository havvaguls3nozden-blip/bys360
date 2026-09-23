"""CSP Dalga 6 - PDF/Print sablonlari kontrat testi.

BYS360 `app/security/headers.py` uygular:
    script-src: 'self' https:  (unsafe-inline YOK)

`app/security/headers.py::inject_csp_nonce_into_html` response sonrasi TUM
`<script>` etiketlerine otomatik nonce ekler; sablonlarda nonce elle
YAZILMAZ (bu dosyanin testleri de nonce aramaz).

Bu dosyanin sahiplik alani yalnizca iki sablon:
    - app/templates/reports_pdf.html      (1 handler: onclick=window.print())
    - app/templates/scorecard_pdf.html    (3 handler: onclick=window.close(),
      onclick=window.print(), onerror=... img fallback)

PDF render motoru analizi (koordinatorun on arastirmasi, bu dosyada bagimsiz
olarak dogrulanmistir):
    - Repo genelinde weasyprint/wkhtmltopdf/playwright/pdfkit/xhtml2pdf/
      reportlab icin grep 0 sonuc dondurur (bkz. requirements.txt).
    - `app/performance/reporting_routes.py` (reports_pdf.html'i render eden
      `performance_reports_pdf` route'u) ve `app/performance/
      evaluation_core_routes.py` (scorecard_pdf.html'i render eden
      `performance_scorecard_pdf` route'u) ikisi de duz
      `flask_render_template(...)` cagirir ve normal bir Flask HTML
      response'u dondurur -- ozel bir PDF mimetype/response-header veya
      headless bir render motoru cagrisi YOKTUR.
    - Kullanici bu sayfayi tarayicida acar; "PDF Kaydet / Yazdir" /
      "PDF Olarak Kaydet / Yazdir" butonu `window.print()` cagirir ve
      tarayicinin kendi yazdirma/"PDF olarak kaydet" akisini tetikler.
      `reports_pdf.html`'in `page_subtitle` bloğu bunu acikca soyler
      ("Bu gorunum tarayicidan PDF olarak kaydedilebilir"); `scorecard_pdf
      .html`'deki `.screen-toolbar{display:none}` kurali `@media print`
      icindedir (toolbar yalnizca EKRANDA gorunur, yazdirma/PDF ciktisinda
      gizlenir).
    - SONUC: buradaki JavaScript normal calisan, canli kullanici-etkilesimli
      koddur ("olu kod" degildir); standart CSP donusumu (id + addEventListener)
      uygulanmistir.

Statik testler `tests/security/test_csp_wave1_inline_handlers_contract.py`
ve `tests/security/test_csp_wave2_performance_print_mail_contract.py` ile
ayni desendedir (Path.read_text() + regex + gercek app fixture'i ile render).

Onemli mimari not -- scorecard_pdf.html'deki pre-existing 4. dinleyici:
    `scorecard_pdf.html` zaten Wave 6 ONCESINDE su script'e sahipti:
        window.addEventListener("load", function () {
            setTimeout(function () { window.print(); }, 400);
        });
    Bu, sayfa yuklendiginde yazdirma iletisim kutusunu OTOMATIK tetikleyen,
    bu dalganin KAPSAMI DISINDA (ve inline event-attribute icermeyen, zaten
    CSP-uyumlu) bir davranistir. Koordinatorun talimati yalnizca 4 YENI
    listener'i (reports_pdf: 1 click; scorecard_pdf: close-click +
    print-click + img-error fallback = 3) kapsar; bu pre-existing "load"
    dinleyicisi BİLİNCLİ olarak DOKUNULMADAN birakilmis ve TEK script
    blogu icine (yeni ikinci bir <script> etiketi ACMADAN) tasinmistir.
    Asagidaki "gereksiz JS eklenmedi" testleri bu nedenle script icindeki
    toplam `addEventListener` cagrisini 4 (1 load + 2 click + 1 error)
    olarak kilitler -- 5. bir cagri eklenirse test kirilir.
"""
from __future__ import annotations

import re
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

REPORTS_PDF_TEMPLATE = "app/templates/reports_pdf.html"
SCORECARD_PDF_TEMPLATE = "app/templates/scorecard_pdf.html"

WAVE6_PDF_PRINT_FILES = [
    REPORTS_PDF_TEMPLATE,
    SCORECARD_PDF_TEMPLATE,
]

# HTML attribute syntax: bosluk + on<harfler> + '=' + tirnak. CSS/JS icindeki
# "javascript:" gibi metinsel string literal'leri yanlislikla yakalamaz.
_INLINE_EVENT_ATTR_RE = re.compile(r"""[\s]on[a-zA-Z]+\s*=\s*["']""")
_JS_HREF_RE = re.compile(r"""(?:href|src)\s*=\s*["']\s*javascript:""", re.IGNORECASE)
_JS_URL_ANYWHERE_RE = re.compile(r"""javascript:""", re.IGNORECASE)

_FORBIDDEN_JS_SINKS = ("eval(", "new Function(", "document.write(")

# Bu dalganin PDF/print sayfalari minimal kalmalidir: yalnizca close/print/
# fallback disinda yeni bir JS "ozellik" (analytics, network cagrisi,
# depolama, global durum) eklenmedigini dogrulamak icin taranan kaliplar.
_FORBIDDEN_EXTRA_JS_PATTERNS = (
    "fetch(",
    "XMLHttpRequest",
    "console.",
    "localStorage",
    "sessionStorage",
    "WebSocket",
    "gtag(",
    "dataLayer",
    "analytics",
    "setInterval(",
    "innerHTML =",
    "innerHTML=",
    "import(",
    "require(",
    "addEventListener('submit'",
    'addEventListener("submit"',
)


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1) Statik kaynak-kod kontrati (Path.read_text + regex).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative_path", WAVE6_PDF_PRINT_FILES)
def test_pdf_print_file_has_no_inline_event_attributes(relative_path: str) -> None:
    text = _read(relative_path)
    matches = _INLINE_EVENT_ATTR_RE.findall(text)
    assert not matches, (
        f"{relative_path} icinde inline event-attribute (on*=) bulundu: {matches!r}. "
        "CSP script-src 'self' https: (unsafe-inline yok) altinda bunlar calismaz; "
        "id + addEventListener kalibina cevrilmeli."
    )


@pytest.mark.parametrize("relative_path", WAVE6_PDF_PRINT_FILES)
def test_pdf_print_file_has_no_javascript_href(relative_path: str) -> None:
    text = _read(relative_path)
    assert not _JS_HREF_RE.search(text), (
        f"{relative_path} icinde href/src=\"javascript:...\" bulundu."
    )
    assert not _JS_URL_ANYWHERE_RE.search(text), (
        f"{relative_path} icinde beklenmedik bir javascript: metni bulundu."
    )


@pytest.mark.parametrize("relative_path", WAVE6_PDF_PRINT_FILES)
def test_pdf_print_file_introduces_no_dangerous_js_sinks(relative_path: str) -> None:
    """Duzeltme sirasinda eval/new Function/document.write eklenmedigini dogrular."""
    text = _read(relative_path)
    for forbidden in _FORBIDDEN_JS_SINKS:
        assert forbidden not in text, f"{relative_path} icinde yasakli sink bulundu: {forbidden}"


def test_reports_pdf_print_button_uses_id_and_click_listener() -> None:
    text = _read(REPORTS_PDF_TEMPLATE)
    assert 'onclick=' not in text
    assert 'id="reportsPdfPrintBtn"' in text
    assert "getElementById('reportsPdfPrintBtn')" in text
    assert "addEventListener('click'" in text
    assert "window.print()" in text
    # Sadece 1 <script> blogu (base.html'in kendi scriptleri haric, bu
    # dosyanin KENDI kaynaginda yalnizca bu yeni blok var).
    assert text.count("<script>") == 1


def test_scorecard_pdf_close_and_print_buttons_use_ids_and_click_listeners() -> None:
    text = _read(SCORECARD_PDF_TEMPLATE)
    assert 'onclick=' not in text
    assert 'onerror=' not in text
    assert 'id="scorecardCloseBtn"' in text
    assert 'id="scorecardPrintBtn"' in text
    assert "getElementById('scorecardCloseBtn')" in text
    assert "getElementById('scorecardPrintBtn')" in text
    assert text.count("addEventListener('click'") == 2
    assert "window.close()" in text
    assert "window.print()" in text


def test_scorecard_pdf_logo_uses_data_fallback_src_pattern() -> None:
    """base.html'deki ile ayni desen/isimlendirme (onImgError, once:true) --
    bu dosya base.html'i extend etmedigi icin (bagimsiz <!doctype html>
    belgesi) kendi yerel kopyasina ihtiyac duyar, global delegasyonu
    KULLANAMAZ."""
    text = _read(SCORECARD_PDF_TEMPLATE)
    assert 'data-fallback-src="{{ url_for(\'static\', filename=\'img/logo.png\') }}"' in text
    assert "querySelectorAll('img[data-fallback-src]')" in text
    assert "addEventListener('error', function onImgError()" in text
    assert "removeEventListener('error', onImgError)" in text
    assert "img.src = img.getAttribute('data-fallback-src')" in text
    assert "{ once: true }" in text


def test_scorecard_pdf_has_single_script_block() -> None:
    """Koordinator talimati: 'TEK bir script blogu ac'. Pre-existing
    otomatik-yazdirma (window 'load' listener'i) korunarak yeni 3 dinleyici
    AYNI script etiketine eklendi -- ikinci bir <script> etiketi acilmadi."""
    text = _read(SCORECARD_PDF_TEMPLATE)
    assert text.count("<script>") == 1
    assert text.count("</script>") == 1


# ---------------------------------------------------------------------------
# 2) "Gereksiz JS eklenmedi" kontrati: PDF/print sablonlari minimal kalmali.
#    scorecard_pdf.html'in script blogunda pre-existing "load" otomatik-
#    yazdirma haric YALNIZCA 3 yeni mantiksal islem (close-click, print-
#    click, img-error fallback) bulunur -- baska hicbir yeni fonksiyon/
#    global/analytics/tracking kodu YOKTUR.
# ---------------------------------------------------------------------------


def _extract_script_block(text: str, template_name: str) -> str:
    match = re.search(r"<script>(.*?)</script>", text, re.DOTALL)
    assert match, f"{template_name} icinde <script>...</script> blogu bulunamadi."
    return match.group(1)


def test_scorecard_pdf_script_contains_no_extraneous_js() -> None:
    text = _read(SCORECARD_PDF_TEMPLATE)
    script = _extract_script_block(text, SCORECARD_PDF_TEMPLATE)
    for forbidden in _FORBIDDEN_EXTRA_JS_PATTERNS:
        assert forbidden not in script, (
            f"{SCORECARD_PDF_TEMPLATE} script blogunda beklenmeyen/gereksiz JS kalibi "
            f"bulundu: {forbidden!r}. Bu sayfa minimal kalmali (close/print/fallback disinda "
            "hicbir yeni ozellik eklenmemeli)."
        )
    for forbidden in _FORBIDDEN_JS_SINKS:
        assert forbidden not in script


def test_scorecard_pdf_script_listener_count_is_exactly_four() -> None:
    """1 pre-existing 'load' (otomatik yazdirma, Wave 6 kapsami disi, dokunulmadi)
    + 2 yeni 'click' (kapat, yazdir) + 1 yeni 'error' (logo fallback) = 4.
    Bu sayi artarsa (5+), script blogu icine yetkisiz/gereksiz bir 5. dinleyici
    eklenmis demektir ve bu test kasitli olarak kirilir."""
    text = _read(SCORECARD_PDF_TEMPLATE)
    script = _extract_script_block(text, SCORECARD_PDF_TEMPLATE)
    assert script.count("addEventListener(") == 4
    assert script.count('addEventListener("load"') == 1
    assert script.count("addEventListener('click'") == 2
    assert script.count("addEventListener('error'") == 1


def test_scorecard_pdf_script_dom_query_count_is_minimal() -> None:
    """Yalnizca 2 getElementById (close, print) + 1 querySelectorAll
    (img[data-fallback-src]) beklenir -- fazlasi gereksiz DOM sorgusu
    eklendigi anlamina gelir."""
    text = _read(SCORECARD_PDF_TEMPLATE)
    script = _extract_script_block(text, SCORECARD_PDF_TEMPLATE)
    assert script.count("getElementById(") == 2
    assert script.count("querySelectorAll(") == 1


def test_reports_pdf_script_contains_no_extraneous_js() -> None:
    text = _read(REPORTS_PDF_TEMPLATE)
    script = _extract_script_block(text, REPORTS_PDF_TEMPLATE)
    for forbidden in _FORBIDDEN_EXTRA_JS_PATTERNS:
        assert forbidden not in script
    for forbidden in _FORBIDDEN_JS_SINKS:
        assert forbidden not in script
    # 2 = 1 disari 'DOMContentLoaded' sarmalayicisi + 1 ic 'click' handler'i.
    assert script.count("addEventListener(") == 2
    assert script.count("addEventListener('DOMContentLoaded'") == 1
    assert script.count("addEventListener('click'") == 1
    assert script.count("getElementById(") == 1


# ---------------------------------------------------------------------------
# 3) Calisma-zamani render kontrolu: gercek Flask app + gercek Jinja motoru
#    ile `render_template` cagrisi (bkz. `app` fixture, tests/conftest.py).
#    Bu app `ChainableUndefined` kullanir (app/template_safety.py) -- eksik
#    context degiskenleri hataya degil bos/Falsy degerlere cozulur. Asagidaki
#    stub'lar yine de GERCEKCI degerlerle saglanir (types.SimpleNamespace)
#    ki hem gosterge/tablo dallari hem de close/print/fallback hook'lari
#    ayni anda tetiklensin. Bu HALA gercek bir tarayici veya PDF motoru
#    testi DEGILDIR: yalnizca uretilen HTML'de inline event-attribute
#    kalmadigini ve script/hook'larin gercekten render edildigini dogrular.
# ---------------------------------------------------------------------------


def _fake_filter_summary(**overrides: object) -> types.SimpleNamespace:
    base: dict[str, object] = dict(
        scope_label="Kurum geneli",
        period_title="2026 Donem 1",
        query_text="-",
        status="Tumu",
        row_count=0,
        scope_description="Yalnizca yetkili gorunum kapsamindaki personel listelenir.",
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


def _fake_evaluation(**overrides: object) -> types.SimpleNamespace:
    base: dict[str, object] = dict(
        published_at=None,
        level_1_total_100=80.0,
        level_2_total_100=85.0,
        level_3_total_100=0.0,
        final_total_100=82.5,
        report_final_score=82.5,
        status="Yayinlandi",
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


def _fake_row(**overrides: object) -> types.SimpleNamespace:
    base: dict[str, object] = dict(
        level_1_items=[],
        level_1_comment=None,
        level_2_items=[],
        level_2_comment=None,
        level_3_items=[],
        level_3_comment=None,
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


def _fake_employee(**overrides: object) -> types.SimpleNamespace:
    base: dict[str, object] = dict(
        id=1,
        full_name="Wave6 Test Personel",
        ad="Wave6",
        soyad="Personel",
        birim="Test Birimi",
        sicil_no="90006",
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


def test_reports_pdf_render_includes_print_hook_and_no_inline_handlers(app) -> None:
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template(
            "reports_pdf.html",
            evaluations=[],
            filter_summary=_fake_filter_summary(),
        )

    assert 'id="reportsPdfPrintBtn"' in html
    assert "getElementById('reportsPdfPrintBtn')" in html
    assert "window.print()" in html
    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert not _JS_HREF_RE.search(html)
    for forbidden in _FORBIDDEN_JS_SINKS:
        assert forbidden not in html


def test_reports_pdf_render_with_evaluation_rows_still_has_print_hook(app) -> None:
    """Bos olmayan evaluations listesiyle de (tablo dali render edilir)
    print butonu/hook'u degismeden mevcut olmali."""
    from flask import render_template

    item = types.SimpleNamespace(
        period=types.SimpleNamespace(title="2026 Donem 1"),
        employee=_fake_employee(),
        level_1_total_100=80.0,
        level_2_total_100=85.0,
        level_3_total_100=0.0,
        final_total_100=82.5,
        report_final_score=82.5,
        status="Yayinlandi",
    )

    with app.test_request_context("/"):
        html = render_template(
            "reports_pdf.html",
            evaluations=[item],
            filter_summary=_fake_filter_summary(row_count=1),
        )

    assert 'id="reportsPdfPrintBtn"' in html
    assert "Wave6 Test Personel" in html
    assert not _INLINE_EVENT_ATTR_RE.findall(html)


def test_scorecard_pdf_render_includes_close_print_and_fallback_hooks(app) -> None:
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template(
            "scorecard_pdf.html",
            evaluation=_fake_evaluation(),
            row=_fake_row(),
            employee=_fake_employee(),
            period=types.SimpleNamespace(title="2026 Donem 1"),
        )

    assert 'id="scorecardCloseBtn"' in html
    assert 'id="scorecardPrintBtn"' in html
    assert "window.close()" in html
    assert "window.print()" in html
    assert 'data-fallback-src="' in html
    assert "img.src = img.getAttribute('data-fallback-src')" in html
    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert not _JS_HREF_RE.search(html)
    for forbidden in _FORBIDDEN_JS_SINKS:
        assert forbidden not in html
    # Bagimsiz standalone belge (base.html extend edilmiyor): render
    # ciktisinda tam olarak 1 <script> etiketi beklenir.
    assert html.count("<script>") == 1


def test_scorecard_pdf_render_with_populated_supervisor_items(app) -> None:
    """1./2./3. amir panellerinin dolu veriyle de (item.criteria.name/weight/
    score/score_100/comment erisimleri) hatasiz render edildigini ve
    close/print/fallback hook'larinin degismeden kaldigini dogrular."""
    from flask import render_template

    criteria = types.SimpleNamespace(name="Zamanlilik", weight=25)
    item = types.SimpleNamespace(criteria=criteria, score=4, score_100=90.0, comment="Iyi.")
    row = _fake_row(
        level_1_items=[item],
        level_1_comment="Genel olarak basarili.",
        level_2_items=[item],
        level_2_comment="Gelistirilebilir.",
    )

    with app.test_request_context("/"):
        html = render_template(
            "scorecard_pdf.html",
            evaluation=_fake_evaluation(),
            row=row,
            employee=_fake_employee(),
            period=types.SimpleNamespace(title="2026 Donem 1"),
        )

    assert "Zamanlilik" in html
    assert 'id="scorecardCloseBtn"' in html
    assert 'id="scorecardPrintBtn"' in html
    assert not _INLINE_EVENT_ATTR_RE.findall(html)
