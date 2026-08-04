"""CSP Dalga 9 - FINAL kapanış: repo genelinde inline event-handler sayısının
SIFIRA indiği kapı testi (script/event-handler CSP temizliğinin son dalgası).

BYS360 `app/security/headers.py` uygular:
    script-src: 'self' https:  (unsafe-inline YOK)

Bu dalga, Dalga 8'in bilinçli olarak kapsam dışı bıraktığı SON 3 dosyayı
kapsar (bkz. `tests/security/test_csp_wave8_task_mail_guard_contract.py`
içindeki `REMAINING_OUT_OF_SCOPE_HANDLER_COUNTS` sözlüğü):

    - app/templates/messages_thread.html                (2 inline handler)
    - app/templates/file_center/index.html               (1 inline handler)
    - app/templates/file_center/requests.html             (1 inline handler)

Paralel çalışan 2 ajan bu 3 dosyayı (+ `app/static/js/messages_messenger_
mobile.js` içindeki mevcut delegasyonun genişletilmesini) dönüştürüyor. Bu
test dosyasının sahiplik alanı SADECE TESTTİR -- yukarıdaki üretim
dosyalarına DOKUNMAZ.

ÖNEMLİ -- BU DOSYA YAZILIRKEN ÖLÇÜLEN GERÇEK DURUM: Bu görev başladığı anda
`app/templates/file_center/index.html` ve `app/templates/file_center/
requests.html` ZATEN dönüştürülmüştü (0 handler, `data-confirm` +
`querySelectorAll('form[data-confirm]')` deseni), yalnızca
`app/templates/messages_thread.html` HENÜZ dönüştürülmemişti (hâlâ 2 inline
handler: `onclick="openEditModal(...)"` ve `onsubmit="return confirm(...)"`).
Bu yüzden aşağıdaki "repo genelinde SIFIR" testleri, bu dosya ilk
yazıldığında koordinatörün belirttiği gibi FAIL verebilir/veriyordu (toplam
2, dağılım yalnızca messages_thread.html) -- bu, `messages_thread.html`
dönüşümünü yapan paralel ajan işini bitirince otomatik olarak PASS'e döner.
Test kasıtlı olarak KOŞULSUZ yazılmıştır (hedefe göre "bekleniyor" diye
gevşetilmemiştir) -- amaç, dönüşüm tamamlandığında GERÇEK bir kapı olması.

GERÇEK YAN ETKİ YASAĞI: Bu dosyadaki hiçbir test gerçek bir mesaj göndermez,
gerçek bir dosya yüklemez/indirmez/silmez, gerçeğe disk yazmaz, gerçek bir
depolama servisi (S3/yerel depolama vb.) çağırmaz. Yalnızca: (a) kaynak-kod
okuma (`Path.read_text`), (b) gerçek Jinja motoruyla `flask.render_template()`
(ağ/disk-yazma/DB-yazma YOK -- sadece SELECT tabanlı, sqlite bellek-benzeri
test DB'si üzerinde, `tests/conftest.py`'deki `app` fixture'ı ile), ve (c)
`unittest.mock.patch` ile devre dışı bırakılmış `subprocess`/`os`/`shutil`
yıkıcı fonksiyonları kullanılır. Bölüm C bunun çalışma-zamanı pozitif
kanıtıdır. Gerçek tarayıcı, gerçek upload/download, gerçek mesajlaşma akışı
BU DOSYADA test EDİLMEMİŞTİR (bu, ayrı bir manuel/E2E doğrulama gerektirir).
"""
from __future__ import annotations

import re
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Dalga 9'un 3 hedef dosyası (Dalga 8'in bilinçli kapsam dışı bıraktığı son 3
# dosya -- bkz. modül docstring'i).
# ---------------------------------------------------------------------------
MESSAGES_THREAD = "app/templates/messages_thread.html"
FILE_CENTER_INDEX = "app/templates/file_center/index.html"
FILE_CENTER_REQUESTS = "app/templates/file_center/requests.html"

THREE_WAVE9_TEMPLATES = [MESSAGES_THREAD, FILE_CENTER_INDEX, FILE_CENTER_REQUESTS]

MESSENGER_JS = "app/static/js/messages_messenger_mobile.js"

WAVE8_XFAIL_FILE = "tests/security/test_csp_wave8_task_mail_guard_contract.py"

# HTML attribute syntax: bosluk + on<harfler> + '=' + tirnak. CSS/JS icindeki
# "javascript:" gibi metinsel string literal'leri yanlislikla yakalamaz. Bu,
# Wave1-8 kontrat dosyalarindaki KANONIK regex ile birebir aynidir.
_INLINE_EVENT_ATTR_RE = re.compile(r"""[\s]on[a-zA-Z]+\s*=\s*["']""")

# href/src baglaminda javascript: URL -- Wave1/2/5/8 ile ayni kanonik desen.
# Genel metinsel "javascript:" (orn. base.html'deki `.startsWith('javascript:')`
# savunma kodu) bu deseni KASITLI olarak tetiklemez.
_JS_HREF_SRC_RE = re.compile(r"""(?:href|src)\s*=\s*["']\s*javascript:""", re.IGNORECASE)

# Static JS icinde bir inline handler attribute'unun STRING olarak
# uretilmedigini dogrulamak icin: 'onclick=' / "onclick=" vb. Wave5'teki
# `test_no_inline_handler_attribute_built_as_js_string_literal` ile ayni
# ailede, ama repo genelinde (tum app/static/**/*.js) ve daha genis bir
# handler-adi kumesiyle.
_HANDLER_STRING_LITERAL_RE = re.compile(r"""['"]on[a-zA-Z]+\s*=['"]""")

# eval(/new Function(/document.write( -- Wave1/Wave5 ile ayni yasakli sink
# ailesi. `eval(` icin negatif lookbehind, `ast.literal_eval(` gibi meşru
# Python kullanimlarini (repo genelinde app/**/*.py taranirken) yanlis-pozitif
# olarak yakalamamak icindir (bu isim, sonu "eval(" ile biten baska bir
# tanimlayicinin -- literal_eval, safe_eval vb. -- PARCASI olmamalidir).
_EVAL_RE = re.compile(r"""(?<![A-Za-z0-9_])eval\(""")
_NEW_FUNCTION_RE = re.compile(r"""new\s+Function\(""")
_DOCUMENT_WRITE_RE = re.compile(r"""document\.write\(""")
# setTimeout'un ILK argumaninin STRING olmasi (string-eval'li zamanlayici)
# tehlikelidir; fonksiyon referansiyla cagrilan setTimeout(function(){...}, n)
# (bu repoda -- orn. messages_messenger_mobile.js -- yaygin ve GUVENLI kullanim)
# bu desenle KASITLI olarak eslesmez.
_SETTIMEOUT_STRING_ARG_RE = re.compile(r"""setTimeout\s*\(\s*["']""")

_XFAIL_CALL_RE = re.compile(r"""pytest\.xfail\(""")
_XFAIL_MARK_RE = re.compile(r"""@pytest\.mark\.xfail""")


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _scan_repo_wide_inline_handlers() -> dict[str, list[int]]:
    """`app/templates/**/*.html` genelinde kanonik inline event-attribute
    regex'iyle tarama yapar; dosya -> (1-indeksli) eşleşen satır numaraları
    sözlüğü döner (debug kolaylığı için -- yalnızca dosya adı değil, TAM
    OLARAK hangi satırlarda kaldığı da görülebilsin diye)."""
    offenders: dict[str, list[int]] = {}
    templates_root = REPO_ROOT / "app" / "templates"
    for html_file in sorted(templates_root.rglob("*.html")):
        text = html_file.read_text(encoding="utf-8")
        line_hits = [
            idx
            for idx, line in enumerate(text.splitlines(), start=1)
            if _INLINE_EVENT_ATTR_RE.search(line)
        ]
        if line_hits:
            offenders[html_file.relative_to(REPO_ROOT).as_posix()] = line_hits
    return offenders


# ---------------------------------------------------------------------------
# A) Repo geneli sıfır-handler kapısı (kritik, FİNAL).
# ---------------------------------------------------------------------------


def test_repo_wide_inline_handler_count_is_exactly_zero() -> None:
    """Dalga 9'un asıl kapanış kapısı: `app/templates/**/*.html` genelinde
    kanonik `on[a-zA-Z]+=` regex'iyle bulunan TOPLAM inline event-attribute
    sayısı TAM OLARAK 0 olmalı.

    NOT: Bu dosya yazıldığı anda `messages_thread.html` dönüşümü henüz
    tamamlanmamış olabilir -- bu durumda bu test FAIL verir (toplam > 0,
    dağılım mesajında HANGİ dosya/satırlarda kaldığı açıkça listelenir).
    Bu BEKLENEN bir ara-durum başarısızlığıdır (bkz. modül docstring'i);
    paralel dönüşüm ajanı işini bitirdiğinde koordinatör bu testi tekrar
    çalıştırdığında PASS eder. Test koşullu/gevşetilmiş DEĞİLDİR."""
    offenders = _scan_repo_wide_inline_handlers()
    total = sum(len(lines) for lines in offenders.values())
    assert total == 0, (
        "Repo genelinde inline event-handler sayisi SIFIR olmali (CSP Dalga 9 "
        f"FINAL kapanisi). Bulunan toplam: {total}. Dosya -> satir dagilimi: "
        f"{offenders!r}. Eger burada messages_thread.html / file_center/index.html "
        "/ file_center/requests.html goruyorsan, ilgili donusum ajani henuz isini "
        "bitirmemis olabilir -- bu beklenen bir ara-durumdur, koordinator testi "
        "tekrar calistiracaktir."
    )


def test_repo_wide_handler_bearing_file_count_is_exactly_zero() -> None:
    """Madde E13: kanonik script ile 'handler bulunan dosya sayısı' 0 olmalı
    (dosya listesi boş) -- yukarıdaki toplam-sayım testinden BAĞIMSIZ ikinci
    bir açı: bir dosyada birden fazla handler kalmış olsa bile bu, aynı
    şekilde en az 1 offending dosya anlamına gelir; burada dosya listesinin
    KENDİSİNİN boş olduğu ayrıca doğrulanır."""
    offenders = _scan_repo_wide_inline_handlers()
    assert list(offenders.keys()) == [], (
        f"Inline handler bulunan dosya listesi bos degil: {sorted(offenders.keys())!r}"
    )


def test_repo_wide_javascript_url_href_or_src_is_exactly_zero() -> None:
    """href/src bağlamında `javascript:` URL sayısı repo genelinde 0 olmalı.
    `_JS_HREF_SRC_RE` yalnızca gerçek href/src attribute değerlerini yakalar;
    `base.html` içindeki `.startsWith('javascript:')` gibi metinsel JS string
    literal'leri (savunma kodu) bu desenle KASITLI olarak eşleşmez -- bu,
    Wave1/2/5/8 kontrat dosyalarındaki aynı ayrımdır."""
    offenders: dict[str, int] = {}
    total = 0
    templates_root = REPO_ROOT / "app" / "templates"
    for html_file in sorted(templates_root.rglob("*.html")):
        text = html_file.read_text(encoding="utf-8")
        matches = _JS_HREF_SRC_RE.findall(text)
        if matches:
            rel = html_file.relative_to(REPO_ROOT).as_posix()
            offenders[rel] = len(matches)
            total += len(matches)
    assert total == 0, f"javascript: href/src bulunan dosyalar: {offenders!r}"


def test_repo_wide_static_js_never_builds_inline_handler_attribute_as_string() -> None:
    """`app/static/**/*.js` genelinde bir inline handler attribute'unun
    (`'onclick='`, `"onchange="` vb.) HTML string'i olarak JS içinde
    üretilmediğini doğrular -- yani delegasyonun DOM'a innerHTML/string
    birleştirmesiyle geri sızdırılmadığının kanıtı.

    Bu dosya yazıldığı anda repo genelinde böyle bir string literal
    BULUNAMAMIŞTIR (offenders boş) -- yani Wave5'teki gibi hariç tutulması
    gereken zararsız bir yorum-satırı false-pozitifi bu tarihte YOKTUR. Test
    yine de offenders sözlüğünü hata mesajında raporlar; ileride biri gerçek
    bir handler-string üretimi eklerse bu test bunu YAKALAR (ileride zararsız
    bir yorum-satırı false-pozitifi ortaya çıkarsa, bu test o TEK satırı
    açıkça isim vererek hariç tutacak şekilde güncellenmelidir -- bugün
    itibarıyla böyle bir istisnaya gerek yoktur)."""
    offenders: dict[str, list[str]] = {}
    static_root = REPO_ROOT / "app" / "static"
    for js_file in sorted(static_root.rglob("*.js")):
        text = js_file.read_text(encoding="utf-8")
        matches = _HANDLER_STRING_LITERAL_RE.findall(text)
        if matches:
            offenders[js_file.relative_to(REPO_ROOT).as_posix()] = matches
    assert offenders == {}, (
        f"Static JS icinde inline-handler string literal(leri) bulundu: {offenders!r}"
    )


def test_repo_wide_no_dangerous_js_sinks_or_string_based_settimeout() -> None:
    """`app/**/*.{py,js,html}` genelinde `eval(`, `new Function(`,
    `document.write(` (koşulsuz yasaklı sink'ler) ve `setTimeout(` çağrısının
    İLK ARGÜMANI string olan (string-eval'li zamanlayıcı) desenlerin hiçbiri
    bulunmamalı. `eval(` için kullanılan negatif-lookbehind, `ast.literal_eval(`
    gibi meşru Python isimlerini (bu isim `eval(` ile BİTER ama tehlikeli bir
    sink DEĞİLDİR) yanlış-pozitif olarak yakalamaz."""
    offenders: dict[str, list[str]] = {}
    app_root = REPO_ROOT / "app"
    allowed_exts = {".py", ".js", ".html"}
    for path in sorted(app_root.rglob("*")):
        if path.is_dir() or path.suffix not in allowed_exts:
            continue
        text = path.read_text(encoding="utf-8", errors="strict")
        hits: list[str] = []
        if _EVAL_RE.search(text):
            hits.append("eval(")
        if _NEW_FUNCTION_RE.search(text):
            hits.append("new Function(")
        if _DOCUMENT_WRITE_RE.search(text):
            hits.append("document.write(")
        if _SETTIMEOUT_STRING_ARG_RE.search(text):
            hits.append("setTimeout(<string>)")
        if hits:
            offenders[path.relative_to(REPO_ROOT).as_posix()] = hits
    assert offenders == {}, f"Yasakli JS sink/string-setTimeout deseni bulundu: {offenders!r}"


# ---------------------------------------------------------------------------
# B) messages_thread.html / file_center/index.html / file_center/requests.html
#    dönüşümünün BAĞIMSIZ doğrulaması (paralel ajanların işine körü körüne
#    güvenilmez -- kaynak burada da ayrıca okunur).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative_path", THREE_WAVE9_TEMPLATES)
def test_three_target_files_have_zero_inline_event_handlers(relative_path: str) -> None:
    text = _read(relative_path)
    matches = _INLINE_EVENT_ATTR_RE.findall(text)
    assert not matches, f"{relative_path} icinde hala inline event-attribute bulundu: {matches!r}"


@pytest.mark.parametrize("relative_path", THREE_WAVE9_TEMPLATES)
def test_three_target_files_script_block_lives_inside_content_block_not_dead_code(
    relative_path: str,
) -> None:
    """Madde 6: `<script` etiket(ler)inin gerçek render edilen
    `{% block content %}` sınırları İÇİNDE kaldığını, yani dosyadaki SON
    `{% endblock %}`'tan (content block'un kapanışı -- title/page_kicker/
    page_title/page_subtitle gibi tek satırlık bloklar content'ten ÖNCE
    kendi satırında açılıp kapanır, content her zaman en geniş/son bloktur)
    ÖNCE geçtiğini kaynak-pozisyon (karakter offset) analiziyle doğrular."""
    text = _read(relative_path)
    content_open_marker = "{% block content %}"
    assert content_open_marker in text, f"{relative_path} icinde '{content_open_marker}' yok."
    content_open_idx = text.index(content_open_marker)

    last_endblock_idx = text.rindex("{% endblock %}")
    assert last_endblock_idx > content_open_idx, (
        f"{relative_path}: dosyadaki son '{{% endblock %}}' content block acilisindan ONCE "
        "geliyor gibi gorunuyor -- block sinirlari beklenmedik."
    )

    script_offsets = [m.start() for m in re.finditer(r"<script", text)]
    assert script_offsets, f"{relative_path} icinde hic <script etiketi bulunamadi."
    for offset in script_offsets:
        assert content_open_idx < offset < last_endblock_idx, (
            f"{relative_path}: offset {offset}'deki <script, 'content' block sinirlari "
            f"disinda (content_open={content_open_idx}, son_endblock={last_endblock_idx}) "
            "-- endblock disinda olu kod riski."
        )


def test_messenger_js_document_level_submit_and_click_delegation_each_exactly_once() -> None:
    """Madde 7: `messages_messenger_mobile.js` içinde
    `document.addEventListener('submit', ...)` ve
    `document.addEventListener('click', ...)` çağrılarının HER BİRİNİN TAM
    OLARAK 1 kez geçtiğini doğrular -- yeni bir donusum agent'inin YENİ bir
    document-seviyesi delegasyon AÇMADIĞININ, mevcut TEK delegasyonu
    genişlettiğinin kanıtı (çift-listener/çift-tetikleme riski yok).
    (Not: `form.addEventListener('submit', ...)` gibi tek bir form elemanına
    bağlı, document-seviyesi OLMAYAN listener'lar bu sayıma dahil değildir --
    yalnızca `document.addEventListener(...)` biçimindekiler sayılır.)"""
    text = _read(MESSENGER_JS)
    submit_count = text.count("document.addEventListener('submit'")
    click_count = text.count("document.addEventListener('click'")
    assert submit_count == 1, (
        f"{MESSENGER_JS}: document.addEventListener('submit', ...) tam olarak 1 kez "
        f"beklenirdi, {submit_count} bulundu."
    )
    assert click_count == 1, (
        f"{MESSENGER_JS}: document.addEventListener('click', ...) tam olarak 1 kez "
        f"beklenirdi, {click_count} bulundu."
    )


def test_messenger_js_submit_and_click_delegation_use_closest_not_direct_equality() -> None:
    """Madde 8: document-seviyesi `submit`/`click` delegasyon bloklarının
    hedef eşlemesi için `event.target.closest(...)` kullandığını (doğrudan
    `event.target === ...` katı eşitlik karşılaştırması DEĞİL) doğrular --
    ikon/span gibi bir butonun İÇİNDEKİ bir alt elemana tıklanınca da
    (nested/child click) doğru hedefe (butonun/formun kendisine) ulaşma
    garantisi. `closest()` bunu otomatik sağlar; katı `===` eşitliği tıklanan
    alt eleman butonun/formun kendisi DEĞİLSE delegasyonu SESSİZCE
    KAÇIRIR -- bu regresyonu yakalamak bu testin amacıdır."""
    text = _read(MESSENGER_JS)
    submit_start = text.index("document.addEventListener('submit'")
    click_start = text.index("document.addEventListener('click'", submit_start)
    submit_block = text[submit_start:click_start]

    click_end_marker = "const messageContainer = document.getElementById"
    click_end = text.index(click_end_marker, click_start) if click_end_marker in text[click_start:] else len(text)
    click_block = text[click_start:click_end]

    for label, block in (("submit", submit_block), ("click", click_block)):
        assert ".closest(" in block, (
            f"{MESSENGER_JS}: document-seviyesi '{label}' delegasyon blogunda .closest( "
            "kullanimi bulunamadi -- nested/child tiklama garanti edilmiyor olabilir."
        )
        assert "event.target ===" not in block, (
            f"{MESSENGER_JS}: document-seviyesi '{label}' delegasyon blogunda dogrudan "
            "'event.target === ...' katı esitlik karsilastirmasi bulundu -- closest() "
            "yerine kirilgan, nested/child tiklamayi KACIRAN bir kontrol kullanilmis olabilir."
        )


# ---------------------------------------------------------------------------
# C) Gerçek yan-etki YASAĞI: pozitif çalışma-zamanı kanıtı + statik kanıt.
# ---------------------------------------------------------------------------


def test_wave9_template_renders_and_static_scans_never_trigger_destructive_calls(app) -> None:
    """Madde 9: `subprocess.run`, `subprocess.Popen`, `os.system`,
    `os.remove`, `os.unlink`, `shutil.rmtree` bir context manager içinde
    mock'lanır; bu test dosyasının FİİLEN yaptığı işlemler -- 3 hedef
    şablonun gerçek Jinja motoruyla `flask.render_template()` ile render
    edilmesi (ağ/disk-yazma/DB-yazma YOK, yalnızca `tests/conftest.py`'deki
    `app` fixture'ının sağladığı test-yerel sqlite bağlantısı üzerinden) VE
    repo genelindeki statik dosya taramaları (yalnızca `Path.read_text`) --
    bu mock'lu blok İÇİNDE çalıştırılır. Hiçbiri çağrılmazsa
    (`assert_not_called()`), bu, gerçek bir mesaj gönderiminin, gerçek bir
    dosya silme/yükleme/indirme işleminin veya gerçek bir disk/süreç yan
    etkisinin YANLIŞLIKLA tetiklenmediğinin doğrudan kanıtıdır."""
    import types

    from flask import render_template

    from app.file_center.services import format_bytes

    with (
        mock.patch("subprocess.run") as mock_run,
        mock.patch("subprocess.Popen") as mock_popen,
        mock.patch("os.system") as mock_os_system,
        mock.patch("os.remove") as mock_os_remove,
        mock.patch("os.unlink") as mock_os_unlink,
        mock.patch("shutil.rmtree") as mock_rmtree,
    ):
        thread = types.SimpleNamespace(
            id=1,
            title="BYS360 Test Konusmasi",
            accent_color=None,
            icon_name=None,
            thread_type="group",
        )
        with app.test_request_context("/"):
            html_thread = render_template(
                "messages_thread.html",
                thread=thread,
                participants=[],
                messages=[],
                back_url="/messages",
                compose_submit_token="wave9-test-token",
            )
        with app.test_request_context("/"):
            html_index = render_template(
                "file_center/index.html",
                quota=None,
                files=[],
                links=[],
                guest_links_enabled=False,
                format_bytes=format_bytes,
            )
        with app.test_request_context("/"):
            html_requests = render_template("file_center/requests.html")

        assert isinstance(html_thread, str)
        assert isinstance(html_index, str)
        assert isinstance(html_requests, str)

        # Repo genelindeki statik taramalari da ayni mock'lu blok icinde
        # tekrarla (dosya-sistemi okumasi disinda hicbir sey yapmadigini
        # dogrulamak icin).
        for html_file in (REPO_ROOT / "app" / "templates").rglob("*.html"):
            html_file.read_text(encoding="utf-8")
        for js_file in (REPO_ROOT / "app" / "static").rglob("*.js"):
            js_file.read_text(encoding="utf-8")

    mock_run.assert_not_called()
    mock_popen.assert_not_called()
    mock_os_system.assert_not_called()
    mock_os_remove.assert_not_called()
    mock_os_unlink.assert_not_called()
    mock_rmtree.assert_not_called()


def test_this_wave9_contract_file_never_imports_or_calls_forbidden_network_process_functions() -> None:
    """Madde 10: bu test dosyasının KENDİ kaynağı `ast.parse` ile taranır
    (regex/string-match İLE DEĞİL -- böylece bu davranışı AÇIKLAYAN
    docstring/yorum metinleri yanlış-pozitif üretmez; yalnızca GERÇEKTEN
    çalışacak Python `Import`/`ImportFrom`/`Call` düğümleri kontrol edilir).
    Bu dosyanın gerçek bir istemci HTTP isteği (`.post(...)`), gerçek bir
    URL açma (`urlopen(...)`), gerçek bir `subprocess`/`requests` import'u
    HİÇBİR ZAMAN içermediğini doğrular -- Wave8 Ajan2'nin
    (`test_csp_wave8_weather_mail_contract.py`) aynı AST-tabanlı deseni."""
    import ast

    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(Path(__file__)))

    forbidden_import_modules = {"requests", "subprocess", "urllib.request", "urllib3", "httpx"}
    forbidden_call_attrs = {"post", "urlopen", "system", "Popen", "check_output", "check_call"}
    forbidden_call_funcs = {"eval", "urlopen"}

    offending: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in forbidden_import_modules:
                    offending.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module in forbidden_import_modules:
            offending.append(f"from {node.module} import ...")
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr in forbidden_call_attrs:
                offending.append(f".{func.attr}(...)")
            elif isinstance(func, ast.Name) and func.id in forbidden_call_funcs:
                offending.append(f"{func.id}(...)")

    assert not offending, (
        f"Bu kontrat dosyasi SADECE render_template()/Path.read_text()/mock.patch ile "
        f"calismali; YASAKLI cagri/import bulundu: {offending!r}."
    )


# ---------------------------------------------------------------------------
# D) Xfail bütünlüğü -- Dalga 9 hiçbir YENİ xfail eklememeli.
#
# ÖNEMLİ BULGU (bu ajanın yaptığı gerçek statik ölçüm): görev tanımı bu iki
# testin "pytest.xfail(...) cagrisi TAM OLARAK 2" olmasını beklediğini
# belirtiyordu. Bu dosya yazılırken yapılan gerçek regex sayımı (hem
# `test_csp_wave8_task_mail_guard_contract.py` dosyasının kendisinde hem de
# tüm `tests/security/**/*.py` ağacında -- bu dosyanın kendisi HARİÇ, bkz.
# `this_file` dışlaması aşağıda) TAM OLARAK 1 sonucu vermiştir (0 tane
# `pytest.mark.xfail` dekoratörü). Bu fark koordinatöre ayrıca raporlanmıştır.
# Aşağıdaki sabitler GERÇEK/ÖLÇÜLEN değeri (1) kilitler -- sabit olarak 2
# yazılsaydı bu test yazıldığı andan itibaren SÜREKLİ FAIL verir ve gerçek
# bir regresyonu sinyallemeyen gürültülü bir test olurdu. Korunan asıl
# invaryant: Dalga 9 (bu ajan dahil, SADECE test ekleyen ajan) bu sayıyı
# DEĞİŞTİRMEMELİDİR -- ne yeni bir xfail eklenmeli ne de mevcut olan
# kaldırılmalı.
# ---------------------------------------------------------------------------

EXPECTED_XFAIL_CALL_COUNT_IN_WAVE8_TASK_MAIL_GUARD_FILE = 1
EXPECTED_TOTAL_XFAIL_USAGE_COUNT_IN_TESTS_SECURITY_EXCLUDING_THIS_FILE = 1


def test_wave8_task_mail_guard_file_xfail_call_count_is_unchanged_by_wave9() -> None:
    """Madde 11: `test_csp_wave8_task_mail_guard_contract.py` OKUNUR
    (değiştirilmez). İçindeki xfail kullanım sayısının (xfail çağrısı +
    xfail dekoratörü toplamı) Dalga 9 öncesiyle AYNI (ölçülen: 1) kaldığını
    statik regex ile doğrular -- ne fazla ne eksik."""
    text = _read(WAVE8_XFAIL_FILE)
    call_count = len(_XFAIL_CALL_RE.findall(text))
    mark_count = len(_XFAIL_MARK_RE.findall(text))
    total = call_count + mark_count
    assert total == EXPECTED_XFAIL_CALL_COUNT_IN_WAVE8_TASK_MAIL_GUARD_FILE, (
        f"{WAVE8_XFAIL_FILE} icinde beklenen xfail kullanim sayisi "
        f"{EXPECTED_XFAIL_CALL_COUNT_IN_WAVE8_TASK_MAIL_GUARD_FILE} degil, {total} bulundu "
        f"(call={call_count}, mark-decorator={mark_count}). Dalga 9 bu dosyaya YENI bir "
        "xfail eklememeli/mevcut olani kaldirmamali."
    )


def test_repo_wide_tests_security_xfail_usage_total_is_unchanged_by_wave9() -> None:
    """Madde 12: repo genelinde `tests/security/**/*.py` içinde xfail
    kullanım TOPLAMININ (bu dosyanın KENDİSİ hariç -- kendi kaynağı, xfail
    regex'lerini backslash-escaped bir raw-string TANIMI olarak içerir; bu,
    gerçek bir `pytest.xfail(...)` çağrısı OLMADIĞI için zaten regex'le
    eşleşmez, ama netlik için yine de açıkça dışlanır) ölçülen değerle (1)
    aynı kaldığını doğrular -- Dalga 9'da YENİ bir xfail eklenmediğinin
    kanıtı."""
    this_file = Path(__file__).resolve()
    total = 0
    per_file: dict[str, int] = {}
    security_root = REPO_ROOT / "tests" / "security"
    for py_file in sorted(security_root.rglob("*.py")):
        if py_file.resolve() == this_file:
            continue
        text = py_file.read_text(encoding="utf-8")
        count = len(_XFAIL_CALL_RE.findall(text)) + len(_XFAIL_MARK_RE.findall(text))
        if count:
            per_file[py_file.relative_to(REPO_ROOT).as_posix()] = count
            total += count
    assert total == EXPECTED_TOTAL_XFAIL_USAGE_COUNT_IN_TESTS_SECURITY_EXCLUDING_THIS_FILE, (
        "tests/security/**/*.py genelinde (bu dosya haric) beklenen toplam xfail kullanimi "
        f"{EXPECTED_TOTAL_XFAIL_USAGE_COUNT_IN_TESTS_SECURITY_EXCLUDING_THIS_FILE} degil, "
        f"{total} bulundu. Dagilim: {per_file!r}."
    )
