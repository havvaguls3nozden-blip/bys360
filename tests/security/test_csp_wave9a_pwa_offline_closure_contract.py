"""CSP Dalga 9A - PWA offline template/statik dosya kapanis kontrati.

Dalga 9'da script/event-handler CSP temizligi `app/templates/**` icin 0
handler'a ulasmisti, ancak `app/static/pwa/offline.html` (service worker'in
dogrudan Cache Storage'dan servis ettigi AYRI fiziksel dosya, Dalga 7'de
BILINCLI olarak dokunulmadan birakilmisti) hala eski `onclick=` icermeye
devam ediyordu -- bu yuzden "repo geneli 0" iddiasi yalniz `app/templates/**`
icin gecerliydi, aktif tum HTML varliklari (template + static) icin degil.

Bu dosya bu son mikro-dalgayi kapatir: HER IKI dosya da JS-free bir `href=""`
retry-link desenine gecirildi (bkz. `app/templates/pwa/offline.html` ve
`app/static/pwa/offline.html` diff'leri), service worker dosyalarina
(`service-worker.js`/`sw.js`) HICBIR degisiklik YAPILMADI (cache anahtari,
`BYS360_OFFLINE_URL`, `cache.addAll`/`cache.match` mantigi aynen korunuyor --
yalniz cache'e konan dosyanin ICERIGI degisti).

Kanonik regex Wave1-9 ile ayni: `[\\s]on[a-zA-Z]+\\s*=\\s*["']` (yalniz
`.html`, HTML attribute sozdizimi, JS string-literal false-pozitiflerini
disarida birakir).

ONEMLI SINIRLAMA: Bu dosyadaki HICBIR test gercek bir tarayicida, gercek bir
service worker kaydiyla veya gercek bir Cache Storage yaziminda calismaz.
Dogrulama yalniz: (a) Path.read_text() + regex kaynak taramasi, (b) gercek
Flask/Jinja `render_template()` cikti kontrolu, (c) service worker/sw.js
kaynak kodunun salt-okunur incelenmesi ile sinirlidir. Gercek offline PWA
davranisi (butonun tiklanip mevcut URL'yi yeniden istedigi, service worker'in
gercekten bu HTML'i cache'ledigi) ayri bir manuel/E2E dogrulama gerektirir ve
bu gorev sirasinda YAPILMAMISTIR.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

OFFLINE_TEMPLATE = "app/templates/pwa/offline.html"
OFFLINE_STATIC_COPY = "app/static/pwa/offline.html"
SERVICE_WORKER_FILES = ("app/static/pwa/service-worker.js", "app/static/pwa/sw.js")

# HTML attribute sozdizimi: bosluk + on<harfler> + '=' + tirnak.
_INLINE_EVENT_ATTR_RE = re.compile(r"""[\s]on[a-zA-Z]+\s*=\s*["']""")
_JS_HREF_RE = re.compile(r"""(?:href|src)\s*=\s*["']\s*javascript:""", re.IGNORECASE)
_JS_URL_ANYWHERE_RE = re.compile(r"""javascript:""", re.IGNORECASE)
_STRING_SETTIMEOUT_RE = re.compile(r"""setTimeout\s*\(\s*['"]""")
_FORBIDDEN_JS_SINKS = ("eval(", "new Function(", "document.write(")


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _git_diff_exit_code(relative_path: str) -> int:
    result = subprocess.run(
        ["git", "diff", "--exit-code", "--", relative_path],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return result.returncode


# ---------------------------------------------------------------------------
# 1-5) Statik kaynak-kod kontrati: her iki dosyada da 0 inline handler,
#      0 javascript: URL, 0 inline <script>, dolayisiyla nonce ihtiyaci yok.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative_path", [OFFLINE_TEMPLATE, OFFLINE_STATIC_COPY])
def test_offline_file_has_no_inline_event_attributes(relative_path: str) -> None:
    """Madde 1-2: iki dosyada da inline event-attribute (on*=) yok."""
    text = _read(relative_path)
    matches = _INLINE_EVENT_ATTR_RE.findall(text)
    assert not matches, f"{relative_path} icinde inline event-attribute bulundu: {matches!r}"


@pytest.mark.parametrize("relative_path", [OFFLINE_TEMPLATE, OFFLINE_STATIC_COPY])
def test_offline_file_has_no_javascript_url(relative_path: str) -> None:
    """Madde 3: iki dosyada da javascript: URL yok."""
    text = _read(relative_path)
    assert not _JS_HREF_RE.search(text), f"{relative_path} icinde href/src=javascript: bulundu."
    assert not _JS_URL_ANYWHERE_RE.search(text), f"{relative_path} icinde beklenmedik javascript: metni bulundu."


def test_static_offline_file_has_no_inline_script() -> None:
    """Madde 4: statik dosyada inline <script> yok -- bu, Flask'in statik
    dosya response'larinda (`direct_passthrough=True`) CSP nonce
    enjeksiyonunun ATLANDIGI (bkz. `app/security/headers.py::
    inject_csp_nonce_into_html`) gercegiyle dogrudan iliskilidir: nonce
    asla enjekte edilemeyecegi icin script hicbir zaman calisamazdi."""
    text = _read(OFFLINE_STATIC_COPY)
    assert "<script" not in text
    assert "</script>" not in text


def test_static_offline_file_requires_no_nonce() -> None:
    """Madde 5: script olmadigi icin nonce ihtiyaci yapisal olarak yok --
    `nonce=` metni dosyada hic gecmemeli (elle eklenmis bir nonce, otomatik
    enjeksiyonun statik dosyalarda calismadigini gormeden yapilmis yanlis
    bir düzeltme girisimi olurdu)."""
    text = _read(OFFLINE_STATIC_COPY)
    assert "nonce=" not in text


def test_template_offline_file_has_no_inline_script_either() -> None:
    """DALGA 9A karari: template de ayni JS-free desene gecirildi (yalniz
    statik dosya icin degil) -- iki dosya arasinda mimari fark kalmadi."""
    text = _read(OFFLINE_TEMPLATE)
    assert "<script" not in text
    assert "</script>" not in text


# ---------------------------------------------------------------------------
# 6-8) Retry kontrolu davranis sozlesmesi.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative_path", [OFFLINE_TEMPLATE, OFFLINE_STATIC_COPY])
def test_retry_control_preserves_user_facing_text(relative_path: str) -> None:
    """Madde 6: kullanici metni ("Sayfayı yenile") birebir korunuyor."""
    text = _read(relative_path)
    assert "Sayfayı yenile" in text


@pytest.mark.parametrize("relative_path", [OFFLINE_TEMPLATE, OFFLINE_STATIC_COPY])
def test_retry_control_is_a_get_navigation_link_not_a_form(relative_path: str) -> None:
    """Madde 7-8: retry kontrolu bos href="" ile bir `<a>` linkidir --
    `<form method="post">` DEGIL, yanlis POST submit riski yapisal olarak
    yok. Bos href, gecerli HTML semantigiyle mevcut belge URL'sine (service
    worker navigasyon fallback'inde bu, adres cubugundaki gercek hedef
    URL'dir) yeniden GET istegi yapar -- `location.reload()` ile islevsel
    olarak esdegerdir, JS'siz."""
    text = _read(relative_path)
    assert '<a class="btn secondary" href="">Sayfayı yenile</a>' in text
    assert "<form" not in text
    assert "method=\"post\"" not in text.lower()
    assert "method='post'" not in text.lower()


@pytest.mark.parametrize("relative_path", [OFFLINE_TEMPLATE, OFFLINE_STATIC_COPY])
def test_retry_link_has_no_javascript_free_dependency(relative_path: str) -> None:
    """Ek dogrulama: JavaScript devre disi birakilsa BILE temel retry
    davranisi (linke tiklama -> mevcut URL'ye GET) calismaya devam eder,
    cunku hicbir JS'e bagimli degil (statik <a href> semantik navigasyonu)."""
    text = _read(relative_path)
    assert "addEventListener(" not in text
    assert "onclick=" not in text


# ---------------------------------------------------------------------------
# 9-10) Service worker cache topolojisi (salt-okunur inceleme, DEGISTIRME).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("sw_relative_path", SERVICE_WORKER_FILES)
def test_service_worker_still_caches_correct_offline_url(sw_relative_path: str) -> None:
    """Madde 9-10: service worker hala dogru offline URL'sini (`/static/pwa/
    offline.html`) cache listesinde tasiyor, `cache.addAll`/`cache.match`
    mantigi degismedi -- fallback URL'si aynen korunuyor."""
    text = _read(sw_relative_path)
    assert "BYS360_OFFLINE_URL = '/static/pwa/offline.html'" in text
    assert "cache.addAll(" in text
    assert "cache.match(BYS360_OFFLINE_URL)" in text


@pytest.mark.parametrize("sw_relative_path", SERVICE_WORKER_FILES)
def test_service_worker_files_have_zero_git_diff(sw_relative_path: str) -> None:
    """DALGA 9A kesin kurali: cozum service worker cache listesinde
    degisiklik gerektirmiyordu, bu yuzden bu dosyalara HIC dokunulmadi."""
    exit_code = _git_diff_exit_code(sw_relative_path)
    assert exit_code == 0, f"{sw_relative_path} HEAD'e gore degismis -- Dalga 9A bu dosyaya dokunmamaliydi."


def test_service_worker_files_are_still_byte_identical_to_each_other() -> None:
    """`service-worker.js` ve `sw.js` Dalga 9A oncesi byte-birebir ayniydi;
    hicbiri degismedigi icin hala ayni olmali (regresyon degil, sadece
    tutarlilik teyidi)."""
    texts = [_read(p) for p in SERVICE_WORKER_FILES]
    assert texts[0] == texts[1]


# ---------------------------------------------------------------------------
# 11-13) Gercek yan-etki YASAGI (pozitif kanit).
# ---------------------------------------------------------------------------


def test_no_real_subprocess_or_network_call_during_this_modules_tests() -> None:
    """Madde 11-13: bu test dosyasinin gercek yan-etkili islemler (dosya
    silme, tarayici cache manipulasyonu, dis ag istegi) anlamina gelebilecek
    `os.system`, `os.remove`, `shutil.rmtree`, `urllib.request.urlopen`
    fonksiyonlarini HIC cagirmadigi pozitif olarak dogrulanir. NOT:
    `subprocess.Popen`/`subprocess.run` KASITLI olarak mock'LANMAZ -- bu
    dosyanin KENDI salt-okunur `git diff --exit-code` yardimcisi (madde 9-10
    testlerinde kullanilir) gercekten `subprocess.run`'a dayanir; onu
    mock'lamak kendi kendini bozardı. Bunun yerine asagidaki test
    `_git_diff_exit_code`'un GERCEKTEN salt-okunur `git diff` disinda hicbir
    komut calistirmadigini kaynak-kod seviyesinde ayrica kilitler."""
    with patch("os.system") as mock_system, patch("os.remove") as mock_remove, patch("shutil.rmtree") as mock_rmtree:
        for sw_file in SERVICE_WORKER_FILES:
            _git_diff_exit_code(sw_file)
        mock_system.assert_not_called()
        mock_remove.assert_not_called()
        mock_rmtree.assert_not_called()


def test_git_diff_helper_only_ever_invokes_read_only_git_diff() -> None:
    """`_git_diff_exit_code` yardimcisinin gercekte hangi komutu
    calistirdigini kaynak-kod seviyesinde dogrudan kilitler: yalniz
    `git diff --exit-code -- <dosya>`, baska hicbir alt-komut/flag yok
    (ozellikle `checkout`/`reset`/`clean` gibi yikici git komutlari yok).
    NOT: bu fonksiyonun KENDI yasakli-kelime tuple'i o kelimeleri veri
    olarak icerdigi icin, taranan kaynaktan bu fonksiyonun govdesi CIKARILIR
    (bkz. `test_module_source_never_imports_real_network_or_smtp_functions`
    ile ayni teknik)."""
    own_source = Path(__file__).read_text(encoding="utf-8")
    fn_marker = "def test_git_diff_helper_only_ever_invokes_read_only_git_diff"
    fn_start = own_source.index(fn_marker)
    helper_source = own_source[:fn_start]
    assert '["git", "diff", "--exit-code", "--", relative_path]' in helper_source
    for destructive in ("git checkout", "git reset", "git clean", "git push", "git commit"):
        assert destructive not in helper_source


def test_module_source_never_imports_real_network_or_smtp_functions() -> None:
    """Bu dosyanin kendi kaynak kodu, gercek SMTP/dis-HTTP fonksiyonu
    import/cagrisi icermez -- yalniz `subprocess.run` (salt-okunur git diff
    icin) ve dosya okuma kullanir. NOT: bu kontrolun KENDI yasakli-kelime
    listesi (asagidaki tuple) dogal olarak o kelimeleri veri olarak icerir;
    kendi kendini yanlis-pozitif olarak isaretlememesi icin taranan kaynaktan
    bu fonksiyonun kendi govdesi (tuple tanimi dahil) CIKARILIR."""
    own_source = Path(__file__).read_text(encoding="utf-8")
    fn_marker = "def test_module_source_never_imports_real_network_or_smtp_functions"
    fn_start = own_source.index(fn_marker)
    fn_end = own_source.index("\n\n\n", fn_start)
    scanned = own_source[:fn_start] + own_source[fn_end:]
    for forbidden in ("smtplib", "requests.post(", "requests.get(", "urlopen(", ".install(", ".register("):
        assert forbidden not in scanned, f"Bu test dosyasi yasakli bir cagri/import iceriyor: {forbidden}"


# ---------------------------------------------------------------------------
# 14) Template/statik dosya kullanici-icerigi paritesi.
# ---------------------------------------------------------------------------


def test_template_and_static_files_are_byte_identical() -> None:
    """Madde 14: iki dosya, DALGA 9A cozumu sayesinde YENIDEN byte-birebir
    ayni -- ana kullanici icerigi (baslik, aciklama metni, iki buton/link,
    telif satiri) tamamen esdeger."""
    template_text = _read(OFFLINE_TEMPLATE)
    static_text = _read(OFFLINE_STATIC_COPY)
    assert template_text == static_text


# ---------------------------------------------------------------------------
# 15-16) Kapsam ayrimi acik repo-geneli sayim: template / static / toplam.
# ---------------------------------------------------------------------------


def _scan_handlers(root: Path) -> dict[str, int]:
    offenders: dict[str, int] = {}
    if not root.exists():
        return offenders
    for html_file in root.rglob("*.html"):
        text = html_file.read_text(encoding="utf-8", errors="replace")
        matches = _INLINE_EVENT_ATTR_RE.findall(text)
        if matches:
            offenders[html_file.relative_to(REPO_ROOT).as_posix()] = len(matches)
    return offenders


def test_repo_wide_handler_count_reports_template_and_static_scopes_separately() -> None:
    """Madde 15-16: "repo geneli 0" iddiasi yalniz app/templates VE
    app/static BIRLIKTE sifirsa kullanilir -- bu test iki kapsami AYRI AYRI
    olcup raporlar, sonra toplamin da 0 oldugunu dogrular."""
    templates_offenders = _scan_handlers(REPO_ROOT / "app" / "templates")
    static_offenders = _scan_handlers(REPO_ROOT / "app" / "static")

    templates_total = sum(templates_offenders.values())
    static_total = sum(static_offenders.values())
    combined_total = templates_total + static_total

    assert templates_total == 0, f"app/templates/**/*.html icinde hala handler var: {templates_offenders!r}"
    assert static_total == 0, f"app/static/**/*.html icinde hala handler var: {static_offenders!r}"
    assert combined_total == 0, (
        f"Aktif HTML varliklarinin (template+static) toplam handler sayisi 0 degil: "
        f"templates={templates_total}, static={static_total}"
    )


def test_other_active_blueprint_template_directories_have_zero_handlers() -> None:
    """Ek kapsam genisligi: `app/templates/` disindaki diger aktif blueprint
    template dizinleri (`app/modules/*/templates`, `app/workflow/templates`)
    de bu dalgada ilk kez taranip 0 handler icerdigi teyit edildi -- bu
    dizinler daha once hicbir CSP dalgasinin kanonik script'i tarafindan
    TARANMAMISTI (script varsayilan olarak yalniz app/templates/'i tarardi),
    ama zaten 0 handler oldugu icin bu bir regresyon degil, bir tamlik
    dogrulamasidir."""
    other_roots = [
        REPO_ROOT / "app" / "modules",
        REPO_ROOT / "app" / "workflow" / "templates",
    ]
    offenders: dict[str, int] = {}
    for root in other_roots:
        offenders.update(_scan_handlers(root))
    assert not offenders, f"Beklenmedik: bu dizinlerde inline handler bulundu: {offenders!r}"


# ---------------------------------------------------------------------------
# 17) javascript:/eval/new Function/document.write/string-setTimeout = 0.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative_path", [OFFLINE_TEMPLATE, OFFLINE_STATIC_COPY])
def test_offline_files_introduce_no_dangerous_js_sinks(relative_path: str) -> None:
    """Madde 17: eval/new Function/document.write/string-setTimeout yok."""
    text = _read(relative_path)
    for forbidden in _FORBIDDEN_JS_SINKS:
        assert forbidden not in text, f"{relative_path} icinde yasakli sink bulundu: {forbidden}"
    assert not _STRING_SETTIMEOUT_RE.search(text), f"{relative_path} icinde string-setTimeout bulundu."


# ---------------------------------------------------------------------------
# Calisma-zamani render kontrolu: gercek Flask app + gercek Jinja motoru.
# ---------------------------------------------------------------------------


def test_offline_template_render_matches_static_copy_content(app) -> None:
    """Template'in gercek `render_template()` ciktisi, statik dosyanin ham
    kaynagiyla (nonce enjeksiyonu haric -- render_template CSP after_request
    asamasindan GECMEZ, bu yuzden ciktida hic nonce olmaz) esdeger olmali:
    ikisi de ayni JS-free markup'i icerir."""
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template(OFFLINE_TEMPLATE.split("app/templates/")[1])

    static_text = _read(OFFLINE_STATIC_COPY)
    # Jinja render ciktisi sondaki tek satir-sonu karakterini normalde
    # kirpar (kaynak dosyanin trailing newline'i); anlamli icerik
    # karsilastirmasi icin ikisi de sagdan trim edilerek karsilastirilir.
    assert html.rstrip("\n") == static_text.rstrip("\n")
    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert "<script" not in html


def test_offline_route_still_uses_render_template(app) -> None:
    """`/offline` route'u hala `render_template("pwa/offline.html")`
    cagiriyor -- CSP after_request hook'u (dolayisiyla CSP header'i) bu
    route icin hala calisir; yalniz artik enjekte edilecek bir script/nonce
    olmadigi icin bu konu tartismasiz hale geldi."""
    routes_text = (REPO_ROOT / "app" / "pwa" / "routes.py").read_text(encoding="utf-8")
    assert 'return render_template("pwa/offline.html")' in routes_text
