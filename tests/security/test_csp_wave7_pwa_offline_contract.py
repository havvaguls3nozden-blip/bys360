"""CSP Dalga 7 (+ Dalga 9A guncellemesi) - PWA offline sayfasi kontrat testi.

BYS360 `app/security/headers.py` uygular:
    script-src: 'self' https:  (unsafe-inline YOK)

TARIHCE -- Dalga 7'de yalniz `app/templates/pwa/offline.html` donusturulmustu
(id="offlineRetryBtn" + nonce'lu <script>), `app/static/pwa/offline.html`
(service worker'in dogrudan cache'ten servis ettigi AYRI fiziksel dosya)
BILINCLI olarak dokunulmadan birakilmisti -- cunku o zamanki analiz statik
dosyanin nonce enjeksiyonundan GECMEDIGINI (Flask'in `direct_passthrough`
response'lari icin `inject_csp_nonce_into_html` erken cikar) gosteriyordu, bu
da nonce'lu bir <script>'in orada CALISAMAYACAGI anlamina geliyordu. Bu, iki
dosyanin GECICI olarak senkron olmamasina yol acmisti.

DALGA 9A GUNCELLEMESI: Bu senkron-olmama durumu KAPATILDI. Cozum: HER IKI
dosyada da `onclick="location.reload()"` / nonce'lu script+id yerine, hicbir
JavaScript GEREKTIRMEYEN semantik bir cozum kullanildi: bos `href=""` ile bir
`<a>` etiketi. Bos href, gecerli HTML/tarayici semantigiyle MEVCUT BELGE
URL'sine (service worker navigasyon fallback'inde bu, adres cubugundaki
GERCEK hedef URL'dir, offline.html'in kendi dosya yolu degil) yeniden GET
istegi yapar -- `location.reload()` ile ISLEVSEL OLARAK AYNI sonucu uretir,
ama JS'siz. Bu sayede:
    - Statik dosyanin nonce alamama sorunu tamamen ORTADAN KALKAR (script
      tag'i yok, nonce'a hic ihtiyac yok).
    - Iki dosya YENIDEN byte-birebir ayni hale getirilebilir (asagida
      `test_template_and_static_copy_are_now_out_of_sync` fonksiyonu
      Dalga 9A'da ANLAMINI TERSINE cevirerek -- artik "senkron DEGIL"
      degil, "senkron" durumu kilitler; fonksiyon adi tarihi/geriye donuk
      referans olarak korunuyor, git gecmisinde izlenebilirlik icin).
    - `app/static/pwa/service-worker.js`/`sw.js`'e HICBIR degisiklik
      GEREKMEDI (cache listesindeki URL/mantik degismedi, yalniz cache'e
      konan dosyanin ICERIGI degisti).

Guncel/ongoing PWA-offline-kapanis kapisi
`tests/security/test_csp_wave9a_pwa_offline_closure_contract.py`'dir -- bu
dosya onunla birlikte, ondan BAGIMSIZ ikinci bir kanit katmani olarak calisir.

Statik testler `tests/security/test_csp_wave1_inline_handlers_contract.py`,
`tests/security/test_csp_wave2_performance_print_mail_contract.py` ve
`tests/security/test_csp_wave6_pdf_print_contract.py` ile ayni desendedir
(Path.read_text() + regex, sonra gercek Jinja motoruyla `render_template()`
cikti testleri; `app` fixture'i `tests/conftest.py`'den gelir).

ONEMLI SINIRLAMA: Bu dosyadaki HICBIR test gercek bir tarayicida veya gercek
bir service worker kaydiyla calismaz. `render_template()` yalnizca ureTilen
HTML'i dogrular (inline handler yok, href="" retry linki dogru, script tag'i
YOK). CSP enforce edilmis gercek bir tarayicida "Sayfayi yenile" linkinin
fiilen tiklanip mevcut URL'yi yeniden istedigini KANITLAMAZ -- bu, ayri bir
manuel/E2E dogrulama gerektirir ve bu dosyanin kapsami disindadir; bu tur bir
gercek tarayici/service-worker testi bu gorev sirasinda YAPILMAMISTIR.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

OFFLINE_TEMPLATE = "app/templates/pwa/offline.html"
OFFLINE_STATIC_COPY = "app/static/pwa/offline.html"

# HTML attribute syntax: bosluk + on<harfler> + '=' + tirnak. CSS/JS icindeki
# "javascript:" gibi metinsel string literal'leri yanlislikla yakalamaz.
_INLINE_EVENT_ATTR_RE = re.compile(r"""[\s]on[a-zA-Z]+\s*=\s*["']""")
_JS_HREF_RE = re.compile(r"""(?:href|src)\s*=\s*["']\s*javascript:""", re.IGNORECASE)
_JS_URL_ANYWHERE_RE = re.compile(r"""javascript:""", re.IGNORECASE)

_FORBIDDEN_JS_SINKS = ("eval(", "new Function(", "document.write(")


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1) Statik kaynak-kod kontrati (Path.read_text + regex).
# ---------------------------------------------------------------------------


def test_offline_template_has_no_inline_event_attributes() -> None:
    """onclick="location.reload()" tamamen kaldirilmis olmali (0 adet on*=)."""
    text = _read(OFFLINE_TEMPLATE)
    matches = _INLINE_EVENT_ATTR_RE.findall(text)
    assert not matches, (
        f"{OFFLINE_TEMPLATE} icinde inline event-attribute (on*=) bulundu: {matches!r}. "
        "CSP script-src 'self' https: (unsafe-inline yok) altinda bunlar calismaz."
    )


def test_offline_template_has_no_javascript_href() -> None:
    text = _read(OFFLINE_TEMPLATE)
    assert not _JS_HREF_RE.search(text), f"{OFFLINE_TEMPLATE} icinde href/src=\"javascript:...\" bulundu."
    assert not _JS_URL_ANYWHERE_RE.search(text), f"{OFFLINE_TEMPLATE} icinde beklenmedik javascript: metni bulundu."


def test_offline_template_introduces_no_dangerous_js_sinks() -> None:
    text = _read(OFFLINE_TEMPLATE)
    for forbidden in _FORBIDDEN_JS_SINKS:
        assert forbidden not in text, f"{OFFLINE_TEMPLATE} icinde yasakli sink bulundu: {forbidden}"


def test_offline_template_retry_link_is_javascript_free() -> None:
    """DALGA 9A: `id="offlineRetryBtn"` + click-listener deseni yerine JS
    GEREKTIRMEYEN bos-href linki kullanilir -- statik kopyada nonce
    alamayacagi icin script tabanli cozum kalici olarak terk edildi."""
    text = _read(OFFLINE_TEMPLATE)
    assert "onclick=" not in text
    assert 'id="offlineRetryBtn"' not in text
    assert '<a class="btn secondary" href="">Sayfayı yenile</a>' in text


def test_offline_template_has_no_script_tag_at_all() -> None:
    """DALGA 9A: JS-free cozum sayesinde artik HICBIR <script> etiketi yok
    (ne nonce'lu ne nonce'suz) -- statik kopyayla tam markup paritesi."""
    text = _read(OFFLINE_TEMPLATE)
    assert "<script" not in text
    assert "location.reload()" not in text


def test_offline_template_retry_link_is_untouched() -> None:
    """<a class="btn primary" href="/">Tekrar dene</a> bir LINK'tir, event
    handler icermez -- bu dalganin kapsami disinda, dokunulmamis olmali."""
    text = _read(OFFLINE_TEMPLATE)
    assert '<a class="btn primary" href="/">Tekrar dene</a>' in text


def test_offline_template_has_zero_script_tags() -> None:
    """DALGA 9A: Duplicate-binding riski yapisal olarak IMKANSIZ -- hic
    <script> yok, hic addEventListener yok."""
    text = _read(OFFLINE_TEMPLATE)
    assert text.count("<script") == 0, (
        f"{OFFLINE_TEMPLATE} icinde 0 <script etiketi beklenir, "
        f"{text.count('<script')} bulundu."
    )
    assert text.count("</script>") == 0
    assert "addEventListener(" not in text


def test_offline_template_does_not_extend_base() -> None:
    """Dosya bagimsiz bir <!doctype html> belgesidir, {% extends %}
    KULLANMAZ -- bu yuzden global delegasyon/nonce-farkli varsayimlar
    gecerli degildir (kendi yerel script blogu gerekir)."""
    text = _read(OFFLINE_TEMPLATE)
    assert "{% extends" not in text
    assert "<!doctype html>" in text.lower()


# ---------------------------------------------------------------------------
# 2) Template/statik-kopya senkronizasyon durumu.
#    TARIHCE: Dalga 7'de "statige DOKUNULMADI, iki dosya senkron DEGIL"
#    kilitleniyordu. DALGA 9A bunu KAPATTI: JS-free cozum sayesinde iki
#    dosya YENIDEN byte-birebir ayni -- fonksiyon adlari tarihi referans
#    olarak korundu, govdeler guncel/dogru durumu dogrular.
# ---------------------------------------------------------------------------


def test_static_offline_copy_completely_untouched() -> None:
    """DALGA 9A: Bu isim tarihi bir referanstir (Dalga 7'de dogruydu).
    Guncel kural: statik kopya artik template ile SENKRON GUNCELLENDI (JS-free
    cozum, service worker/cache mimarisine dokunmadan). Service worker
    dosyalarina (`service-worker.js`/`sw.js`) bu dalgada HIC dokunulmadi --
    onu asagidaki test ayrica kilitler."""
    for sw_file in ("service-worker.js", "sw.js"):
        result = subprocess.run(
            ["git", "diff", "--exit-code", "--", f"app/static/pwa/{sw_file}"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, (
            f"app/static/pwa/{sw_file} HEAD'e gore degismis -- Dalga 9A service "
            f"worker dosyalarina dokunmamaliydi:\n{result.stdout}"
        )


def test_static_offline_copy_still_has_old_onclick_handler() -> None:
    """DALGA 9A: Bu isim tarihi bir referanstir. Guncel durum: statik kopyada
    ARTIK eski onclick yok -- JS-free href="" desenine gecirildi."""
    text = _read(OFFLINE_STATIC_COPY)
    assert 'onclick="location.reload()"' not in text
    assert "onclick=" not in text
    assert 'id="offlineRetryBtn"' not in text
    assert '<a class="btn secondary" href="">Sayfayı yenile</a>' in text


def test_template_and_static_copy_are_now_out_of_sync() -> None:
    """DALGA 9A: Bu isim tarihi bir referanstir (Dalga 7 sonrasi durumu
    tanimliyordu). Guncel/dogru kural TAM TERSI: iki dosya YENIDEN
    byte-birebir ayni olmalidir (JS-free cozum her iki dosyaya da ozdes
    sekilde uygulandi)."""
    template_text = _read(OFFLINE_TEMPLATE)
    static_text = _read(OFFLINE_STATIC_COPY)
    assert template_text == static_text, (
        "Template ve statik kopya artik ayni degil -- Dalga 9A'nin JS-free "
        "cozumu her iki dosyaya da ozdes sekilde uygulanmis olmaliydi."
    )


# ---------------------------------------------------------------------------
# 3) Calisma-zamani render kontrolu: gercek Flask app + gercek Jinja motoru
#    ile `render_template()` cagrisi (bkz. `app` fixture, tests/conftest.py).
# ---------------------------------------------------------------------------


def test_offline_template_renders_without_context(app) -> None:
    """Bu sablon hicbir Jinja degiskeni kullanmaz (bagimsiz statik icerik) --
    context'siz render edilebilir olmali."""
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template(OFFLINE_TEMPLATE.split("app/templates/")[1])

    assert 'id="offlineRetryBtn"' not in html
    assert "location.reload()" not in html
    assert '<a class="btn secondary" href="">Sayfayı yenile</a>' in html
    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert not _JS_HREF_RE.search(html)
    for forbidden in _FORBIDDEN_JS_SINKS:
        assert forbidden not in html


def test_offline_template_render_has_zero_script_tags(app) -> None:
    """DALGA 9A: Render ciktisinda (nonce enjeksiyonu ONCESI ham Jinja
    ciktisi) hic <script bulunmaz -- JS-free cozum."""
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template(OFFLINE_TEMPLATE.split("app/templates/")[1])

    assert html.count("<script") == 0
    assert "addEventListener(" not in html


def test_offline_route_uses_render_template_not_static_file() -> None:
    """`app/pwa/routes.py`'deki `/offline` route'u `render_template(\"pwa/
    offline.html\")` cagirir -- `send_from_directory`/`send_file` DEGIL. Bu,
    CSP nonce enjeksiyonunun bu route icin CALISTIGININ (statik dosya
    passthrough kontrolune takilmadiginin) kaynak-kod kaniti."""
    routes_text = (REPO_ROOT / "app" / "pwa" / "routes.py").read_text(encoding="utf-8")
    assert 'return render_template("pwa/offline.html")' in routes_text


def test_service_worker_files_point_offline_url_at_static_copy_not_route() -> None:
    """`service-worker.js` ve `sw.js` her ikisi de `BYS360_OFFLINE_URL` olarak
    `/static/pwa/offline.html` kullanir (route olan `/offline` DEGIL) ve bunu
    `cache.match(...)` ile dogrudan donerler -- bu, statik kopyanin Flask
    render/CSP-nonce pipeline'ini bypass ettiginin kaynak-kod kaniti."""
    for sw_file in ("service-worker.js", "sw.js"):
        sw_text = (REPO_ROOT / "app" / "static" / "pwa" / sw_file).read_text(encoding="utf-8")
        assert "BYS360_OFFLINE_URL = '/static/pwa/offline.html'" in sw_text
        assert "cache.match(BYS360_OFFLINE_URL)" in sw_text
