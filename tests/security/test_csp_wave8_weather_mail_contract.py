"""CSP Dalga 8 - Mail/görev ayar ekranları ("Günlük Hava Durumu Maili")
kontrat testi.

BYS360 `app/security/headers.py` uygular:
    script-src: 'self' https:  (unsafe-inline YOK)

`app/security/headers.py::inject_csp_nonce_into_html` yanıt döndürdükten
sonra TÜM `<script>` etiketlerine (nonce'u olmayanlara) otomatik
`nonce="..."` ekler; bu merkezi mekanizma sayesinde template içindeki
`<script>...</script>` blokları zaten CSP ile uyumludur ve nonce hiçbir
zaman elle template'e yazılmaz. Asıl risk inline EVENT ATTRIBUTE'lardı
(`onclick=`, `onsubmit=` vb.) -- bunlara nonce uygulanmaz ve enforce modda
tarayıcı tarafından çalıştırılmazlar.

Bu dosyanın sahiplik alanı yalnızca şu iki template (toplam 2 handler, AYNI
handler İKİ dosyada tekrarlanıyor):
    - app/templates/executive_summary/daily_weather_mail_tasks.html
      (CANLI -- route: app/dashboard/executive_summary_routes.py:144-148,
      `executive_summary_daily_weather_mail_tasks_v1_3_1()`,
      `return render_template("executive_summary/daily_weather_mail_tasks.html")`
      -- context KWARGS YOK, tüm template değişkenleri `|default(...)` ile
      korunuyor.)
    - app/templates/communication/daily_weather_mail_settings.html
      (ORPHAN -- bkz. aşağıdaki "ORPHAN-ROUTE TEYİDİ" bölümü.)

ORPHAN-ROUTE TEYİDİ (koordinatör bulgusunun bağımsız doğrulaması):
    `grep -rn "communication/daily_weather_mail_settings" app --include=*.py`
    SIFIR sonuç döndürür (bu dosyada da doğrulanmıştır, bkz.
    `test_orphan_settings_template_is_never_referenced_by_any_python_route`).
    Gerçek `/communication/daily-weather-mail` (ve `/executive-summary/
    daily-weather-mail`) GET route'u
    (`app/communication/daily_weather_mail_routes.py:126-157`,
    `daily_weather_mail_settings()`) FARKLI bir template render eder:
    `render_template("executive_summary/mail_center/overview.html", ...)`
    (TemplateNotFound durumunda bile `_fallback_html(...)` bir Python
    f-string'i döndürür, `communication/daily_weather_mail_settings.html`
    HİÇ render edilmez). `app/menu_registry_data_sections.py` içindeki tek
    eşleşme `"main.daily_weather_mail_settings"` bir Flask ENDPOINT adıdır
    (fonksiyon adı), template dosya yolu değildir -- karıştırılmamalıdır.
    Bu iki isim tesadüfen benzer ama farklı şeylerdir. Dolayısıyla
    `communication/daily_weather_mail_settings.html` dosyasının içeriğini
    HİÇBİR route render ETMEZ; bu dosya kod tabanında yalnızca statik bir
    kalıntıdır (muhtemelen önceki bir refactor'ın artığı).

Koordinatör, iki template'in (ve kapsam dışındaki iki kardeş dosyanın) BYTE-
BİREBİR AYNI (31 satır, aynı tek handler) olduğunu tespit etti; bu da bu
dosyada bağımsız olarak doğrulanmıştır (bkz.
`test_both_wave8_templates_remain_byte_identical_to_each_other`).

Her iki dosyada da AYNI TEK handler (satır 12, "Sabah Mailini Gönder" formu):
    `<form method="post" action="/executive-summary/daily-weather-mail/send-now"
     onsubmit="return confirm('Seçili alıcılara sabah hava durumu maili şimdi
     gönderilsin mi?');">...`
Hemen önündeki "Kuru Çalıştır" formu (`action=".../dry-run"`) `onsubmit`
İÇERMİYORDU -- ona DOKUNULMADI (regresyon kilidi: bkz.
`test_dry_run_form_has_no_confirm_attribute_regression`).

ÇÖZÜM (her iki dosyaya da BİREBİR AYNI şekilde uygulandı): `onsubmit`
kaldırıldı, `data-confirm="Seçili alıcılara sabah hava durumu maili şimdi
gönderilsin mi?"` eklendi. Dosyanın SONUNDA (satır ~30) ZATEN var olan tek
`<script>(function(){...})();</script>` bloğu (arama/filtre/checkbox-sayma
JS'i) YENİDEN AÇILMADI -- standart submit-delegasyon kodu, bu MEVCUT IIFE'nin
`count();` çağrısından SONRA, `})();` kapanışından ÖNCE eklendi:
    `document.querySelectorAll('form[data-confirm]').forEach(function(form){
     form.addEventListener('submit', function(event){ const
     m=form.getAttribute('data-confirm'); if(m && !window.confirm(m)){
     event.preventDefault(); } }); });`
Bu, kurulu Dalga 1-7 desenidir (bkz. `test_csp_wave6_criteria_weights_
contract.py`, `test_csp_wave7_support_help_contract.py`). Sonuç: her iki
dosyada da hâlâ TAM OLARAK 1 `<script>` etiketi var (yeni blok YOK), ve
`querySelectorAll('form[data-confirm]')` sayfa başına TAM OLARAK 1 kez
geçiyor.

Statik testler `tests/security/test_csp_wave6_criteria_weights_contract.py`
ve `tests/security/test_csp_wave7_support_help_contract.py` ile aynı
desendedir (Path.read_text() + regex, sonra gerçek Jinja motoruyla
`render_template()` çıktı testleri; `app` fixture'ı `tests/conftest.py`'den
gelir).

GERÇEK MAIL/WEATHER API/GÖREV ÇALIŞTIRILMADIĞININ KANITI: Bu dosyadaki HİÇBİR
test `client.post(...)` (veya `requests.post/get`, `urlopen`) ÇAĞIRMAZ --
yalnızca `flask.render_template(...)` ile şablonun ÜRETTİĞİ HTML metni test
edilir (route fonksiyonları hiç tetiklenmez, dolayısıyla gerçek mail
gönderimi / weather API çağrısı / Windows Görev Zamanlayıcı işlemi /
PowerShell çalıştırma KESİNLİKLE gerçekleşmez). Bu kısıt
`test_this_contract_file_never_posts_to_dangerous_endpoints` testiyle
dosyanın kendi kaynağı üzerinden PROGRAMATİK olarak da kilitlenmiştir.
`scripts/windows/register_bys360_executive_summary_tasks_v2_14_1.ps1`,
`..._v2_14_3.ps1`, `scripts/communication/run_daily_weather_personnel_mail.ps1`
gibi HİÇBİR PowerShell dosyasına bu değişiklikte dokunulmadı (bu dosyalar bu
kontrat testinde hiç import/read edilmez).

ÖNEMLİ SINIRLAMA: Bu dosyadaki HİÇBİR test gerçek bir tarayıcıda
çalışmadı/çalıştırılmadı. `render_template()` yalnızca ÜRETİLEN HTML'i
doğrular (inline handler yok, data-confirm attribute'u doğru, script
bloğu sayfa başına doğru sayıda render ediliyor). CSP enforce edilmiş
gerçek bir tarayıcıda "Sabah Mailini Gönder" butonunun confirm()
diyaloğunu fiilen açıp iptal edilebildiğini KANITLAMAZ -- bu, ayrı bir
manuel/E2E doğrulama gerektirir ve bu dosyanın kapsamı dışındadır.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

TASKS_TEMPLATE = "app/templates/executive_summary/daily_weather_mail_tasks.html"
SETTINGS_TEMPLATE = "app/templates/communication/daily_weather_mail_settings.html"

WAVE8_FILES = [TASKS_TEMPLATE, SETTINGS_TEMPLATE]

SEND_NOW_CONFIRM_MESSAGE = "Seçili alıcılara sabah hava durumu maili şimdi gönderilsin mi?"

# HTML attribute syntax: bosluk + on<harfler> + '=' + tirnak. CSS/JS icindeki
# "javascript:" gibi metinsel string literal'leri yanlislikla yakalamaz.
_INLINE_EVENT_ATTR_RE = re.compile(r"""[\s]on[a-zA-Z]+\s*=\s*["']""")
_JS_HREF_RE = re.compile(r"""(?:href|src)\s*=\s*["']\s*javascript:""", re.IGNORECASE)
_JS_URL_ANYWHERE_RE = re.compile(r"""javascript:""", re.IGNORECASE)

_FORBIDDEN_JS_SINKS = ("eval(", "new Function(", "document.write(")

# Bu kontrat dosyasi SADECE render_template() cagirir; asagidaki isim/attribute
# kumeleri bu dosyanin KENDI KAYNAK KODUNDA (AST Call dugumu olarak, docstring/
# yorum METNI olarak DEGIL) hic gecmemelidir -- gecerse gercek bir POST/network/
# subprocess cagrisi riski var demektir (mail gonderme / weather API / Windows
# Task Scheduler / launcher calistirma KESINLIKLE YASAK -- bkz. modul docstring'i).
_FORBIDDEN_CALL_ATTR_NAMES = {"post", "urlopen", "system", "Popen", "check_output", "check_call"}
_FORBIDDEN_CALL_FUNC_NAMES = {"eval", "urlopen"}
_FORBIDDEN_IMPORT_MODULE_NAMES = {"requests", "subprocess", "urllib.request"}


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _fake_recipient(user_id: int, **overrides: object) -> dict[str, object]:
    base: dict[str, object] = dict(
        id=user_id,
        full_name=f"Wave8 Test Kullanıcı {user_id}",
        username=f"wave8user{user_id}",
        email=f"wave8user{user_id}@example.com",
        sicil_no=f"SC{user_id}",
        birim="Bilgi İşlem",
        unvan="Uzman",
    )
    base.update(overrides)
    return base


def _fake_log(entry_id: int, **overrides: object) -> dict[str, object]:
    base: dict[str, object] = dict(
        sent_at=None,
        created_at="2026-08-01 08:15",
        recipient_email=f"log{entry_id}@example.com",
        to_email=None,
        subject="Sabah Hava Durumu",
        is_success=True,
        status="success",
        error_message=None,
    )
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# 0) Bu kontrat dosyasinin kendisi gercek bir POST/network cagrisi icermez.
# ---------------------------------------------------------------------------


def test_this_contract_file_never_calls_dangerous_network_or_process_functions() -> None:
    """Regresyon kilidi: bu kontrat dosyası SADECE `flask.render_template()`
    çağırır; hiçbir zaman gerçek bir HTTP POST/GET isteği, subprocess/
    PowerShell/launcher çalıştırma veya `eval()` çağrısı içermez -- yani
    /send-now, /dry-run, /settings gibi POST endpoint'lerine hiçbir istemci
    isteği atılmaz, gerçek mail/weather/task-scheduler kodu tetiklenmez.

    Bu, dosyanın kendi kaynağını `ast` ile PARSE EDEREK (metin/regex ile
    DEĞİL) doğrulanır -- böylece bu kısıtı açıklayan DOCSTRING/yorum
    METNİ (örn. "client.post(...) çağırmaz" cümlesi) yanlış-pozitif
    üretmez; yalnızca GERÇEK Python `Call` düğümleri (fiilen çalışacak
    kod) kontrol edilir. İleride biri yanlışlıkla böyle bir çağrı
    eklerse CI derhal yakalar."""
    import ast

    source = Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(Path(__file__)))

    offending_calls: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in _FORBIDDEN_IMPORT_MODULE_NAMES:
                    offending_calls.append(f"import {alias.name}")
        elif isinstance(node, ast.ImportFrom) and node.module in _FORBIDDEN_IMPORT_MODULE_NAMES:
            offending_calls.append(f"from {node.module} import ...")
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr in _FORBIDDEN_CALL_ATTR_NAMES:
                offending_calls.append(f".{func.attr}(...)")
            elif isinstance(func, ast.Name) and func.id in _FORBIDDEN_CALL_FUNC_NAMES:
                offending_calls.append(f"{func.id}(...)")

    assert not offending_calls, (
        f"Bu kontrat dosyası SADECE render_template() ile çalışmalı; "
        f"YASAKLI çağrı/import bulundu: {offending_calls!r} -- "
        "gerçek mail/weather/task POST'u veya subprocess riski."
    )


# ---------------------------------------------------------------------------
# 1) Statik kaynak-kod kontratı (Path.read_text + regex). Kosulsuz calisir,
#    Jinja if-bloklarinin arkasinda kalan durumlari da yakalar.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_wave8_file_has_no_inline_event_attributes(relative_path: str) -> None:
    text = _read(relative_path)
    matches = _INLINE_EVENT_ATTR_RE.findall(text)
    assert not matches, (
        f"{relative_path} icinde inline event-attribute (on*=) bulundu: {matches!r}. "
        "CSP script-src 'self' https: (unsafe-inline yok) altinda bunlar calismaz."
    )


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_wave8_file_has_no_javascript_href_or_url(relative_path: str) -> None:
    text = _read(relative_path)
    assert not _JS_HREF_RE.search(text), f"{relative_path} icinde href/src=\"javascript:...\" bulundu."
    assert not _JS_URL_ANYWHERE_RE.search(text), f"{relative_path} icinde beklenmedik bir javascript: metni bulundu."


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_wave8_file_introduces_no_dangerous_js_sinks(relative_path: str) -> None:
    """Duzeltme sirasinda eval/new Function/document.write eklenmedigini dogrular."""
    text = _read(relative_path)
    for forbidden in _FORBIDDEN_JS_SINKS:
        assert forbidden not in text, f"{relative_path} icinde yasakli sink bulundu: {forbidden}"


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_wave8_file_has_no_forbidden_inline_handler_string_literal(relative_path: str) -> None:
    """Inline handler'in HTML string'i olarak JS icinde uretilmedigini
    (yani `'onsubmit='` gibi bir literal yoklugunu) dogrular -- bu,
    delegasyonun DOM'a innerHTML/string ile geri sizdirilmadiginin kanitidir."""
    text = _read(relative_path)
    for literal in ("'onclick='", '"onclick="', "'onsubmit='", '"onsubmit="'):
        assert literal not in text, f"{relative_path} icinde yasakli JS string literal bulundu: {literal}"


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_wave8_file_send_now_form_has_data_confirm_message_verbatim(relative_path: str) -> None:
    text = _read(relative_path)
    assert "onsubmit=" not in text
    assert f'data-confirm="{SEND_NOW_CONFIRM_MESSAGE}"' in text
    # Tam olarak 1 form attribute'u (JS tarafindaki 'form[data-confirm]'
    # secici stringi ayri, o asagida test_wave8_file_has_exactly_one_script_
    # tag_with_form_confirm_delegation icinde dogrulaniyor).
    assert text.count(f'data-confirm="{SEND_NOW_CONFIRM_MESSAGE}"') == 1


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_wave8_file_send_now_form_action_method_and_csrf_untouched(relative_path: str) -> None:
    text = _read(relative_path)
    assert (
        '<form method="post" action="/executive-summary/daily-weather-mail/send-now" '
        f'data-confirm="{SEND_NOW_CONFIRM_MESSAGE}">'
        '<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">'
        '<button class="bys-btn dark" type="submit">'
        '<i class="fa-solid fa-paper-plane"></i> Sabah Mailini Gönder</button></form>'
    ) in text


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_dry_run_form_has_no_confirm_attribute_regression(relative_path: str) -> None:
    """Regresyon kilidi: 'Kuru Çalıştır' formu (send-now formunun HEMEN
    ÖNÜNDE) hiçbir zaman onsubmit/confirm icermiyordu -- koordinator
    talimati geregi bu forma DOKUNULMADI, hala confirm'siz."""
    text = _read(relative_path)
    assert (
        '<form method="post" action="/executive-summary/daily-weather-mail/dry-run">'
        '<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">'
        '<button class="bys-btn soft" type="submit">'
        '<i class="fa-solid fa-vial-circle-check"></i> Kuru Çalıştır</button></form>'
    ) in text


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_wave8_file_csrf_hidden_input_count_untouched(relative_path: str) -> None:
    """3 CSRF hidden input bekleniyor: dry-run formu, send-now formu,
    mainSettingsForm -- hicbiri kaldirilmadi/bozulmadi."""
    text = _read(relative_path)
    assert text.count('<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">') == 3


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_wave8_file_has_exactly_one_script_tag_with_form_confirm_delegation(relative_path: str) -> None:
    """Koordinator talimati: YENI bir <script> blogu ACILMADI -- standart
    submit-delegasyon kodu, dosyanin SONUNDA zaten var olan (arama/filtre/
    checkbox-sayma) tek IIFE'nin ICINE eklendi."""
    text = _read(relative_path)
    assert text.count("<script") == 1
    assert text.count("querySelectorAll('form[data-confirm]')") == 1
    assert "if(m && !window.confirm(m)){ event.preventDefault(); }" in text


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_wave8_file_existing_search_filter_js_still_present_regression(relative_path: str) -> None:
    """Regresyon kilidi: mevcut arama/filtre/checkbox-sayma IIFE'si (bu
    dalganin kapsami disi) hala mevcut ve fonksiyonel -- yeni delegasyon
    kodu bu IIFE'nin sonuna (count(); cagrisindan SONRA, kapanistan ONCE)
    eklendi, IIFE'nin govdesi ikiye BOLUNMEDI."""
    text = _read(relative_path)
    assert "getElementById('recipientSearch')" in text
    assert "getElementById('selectVisible')" in text
    assert "getElementById('clearVisible')" in text
    assert (
        "count();document.querySelectorAll('form[data-confirm]').forEach(function(form){"
        " form.addEventListener('submit', function(event){ const m=form.getAttribute('data-confirm');"
        " if(m && !window.confirm(m)){ event.preventDefault(); } }); });})();</script>"
    ) in text


def test_both_wave8_templates_remain_byte_identical_to_each_other() -> None:
    """Koordinator bulgusu: bu iki template (Dalga 8 oncesi) BYTE-BIREBIR
    AYNI'ydi. Duzeltme her iki dosyaya da BIREBIR AYNI sekilde uygulandigi
    icin hala byte-birebir ayni olmalilar -- bu, 'iki dosyada da ayni
    degisiklik yapildi' iddiasinin bagimsiz kaniti."""
    assert _read(TASKS_TEMPLATE) == _read(SETTINGS_TEMPLATE)


def test_wave8_templates_are_31_lines_each_regression() -> None:
    for relative_path in WAVE8_FILES:
        line_count = len(_read(relative_path).splitlines())
        assert line_count == 31, f"{relative_path} beklenmedik satir sayisina sahip: {line_count}"


# ---------------------------------------------------------------------------
# 2) Orphan-route teyidi: communication/daily_weather_mail_settings.html
#    HICBIR Python route tarafindan render EDILMEZ.
# ---------------------------------------------------------------------------


def test_orphan_settings_template_is_never_referenced_by_any_python_route() -> None:
    """Koordinator bulgusunun bagimsiz teyidi:
    `communication/daily_weather_mail_settings.html` (tam sablon yolu)
    hicbir *.py dosyasinda gecmiyor -- yani hicbir route bu dosyayi
    render_template() ile cagirmiyor. Gercek `/communication/daily-weather-
    mail` GET route'u (`app/communication/daily_weather_mail_routes.py`,
    `daily_weather_mail_settings()` fonksiyonu) baska bir template
    (`executive_summary/mail_center/overview.html`) render eder;
    fonksiyon adiyla (`daily_weather_mail_settings`) template dosya yolu
    (`communication/daily_weather_mail_settings.html`) TESADUFEN benzer
    ama farkli seylerdir."""
    app_dir = REPO_ROOT / "app"
    full_template_path_needle = "communication/daily_weather_mail_settings.html"
    offending_files: list[str] = []
    for py_file in app_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        if full_template_path_needle in content:
            offending_files.append(str(py_file.relative_to(REPO_ROOT)))
    assert not offending_files, (
        f"communication/daily_weather_mail_settings.html artik bir route tarafindan "
        f"render ediliyor gibi gorunuyor: {offending_files!r}. Bu, orphan-route "
        "varsayimini ve dolayisiyla bu kontrat dosyasinin kapsam gerekcesini gecersiz kilar."
    )


def test_real_communication_route_renders_a_different_template_not_the_orphan_one() -> None:
    """`app/communication/daily_weather_mail_routes.py` icindeki gercek
    `daily_weather_mail_settings()` fonksiyonu render_template() cagrisinda
    `executive_summary/mail_center/overview.html` kullanir --
    `communication/daily_weather_mail_settings.html` DEGIL."""
    routes_source = (REPO_ROOT / "app/communication/daily_weather_mail_routes.py").read_text(encoding="utf-8")
    assert "def daily_weather_mail_settings():" in routes_source
    assert 'render_template("executive_summary/mail_center/overview.html"' in routes_source
    assert 'render_template("communication/daily_weather_mail_settings.html")' not in routes_source
    assert "communication/daily_weather_mail_settings.html" not in routes_source


def test_live_tasks_template_route_source_still_calls_render_template_with_no_kwargs() -> None:
    """Canli route'un (executive_summary_daily_weather_mail_tasks_v1_3_1)
    hala context KWARGS OLMADAN render_template cagirdigini kaynak
    seviyesinde dogrular -- asagidaki render testinin 'gercek route
    davranisini taklit ediyor' iddiasinin kaniti."""
    routes_source = (REPO_ROOT / "app/dashboard/executive_summary_routes.py").read_text(encoding="utf-8")
    assert 'def executive_summary_daily_weather_mail_tasks_v1_3_1():' in routes_source
    assert 'return render_template("executive_summary/daily_weather_mail_tasks.html")' in routes_source


# ---------------------------------------------------------------------------
# 3) Calisma-zamani render kontrolu: gercek Flask app + gercek Jinja motoru
#    ile `render_template()` cagrisi (bkz. `app` fixture, tests/conftest.py).
#    Hicbir test client.post(...) COAGIRMAZ (bkz. bolum 0).
# ---------------------------------------------------------------------------


def test_tasks_template_renders_with_zero_context_kwargs_like_real_route(app) -> None:
    """EN ONEMLI TEST: gercek CANLI route (`executive_summary_daily_weather_
    mail_tasks_v1_3_1`) render_template()'i HICBIR context kwarg'i
    OLMADAN cagiriyor. Bu test TAM OLARAK ayni cagriyi tekrarlar --
    template icindeki tum degiskenler `|default(...)` ile korunuyor
    oldugu icin bu, hicbir exception firlatmadan basariyla render
    edilmelidir. Bu, canli route'un Dalga 8 degisikligiyle BOZULMADIGININ
    dogrudan kanitidir."""
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template("executive_summary/daily_weather_mail_tasks.html")

    assert "onsubmit=" not in html
    assert f'data-confirm="{SEND_NOW_CONFIRM_MESSAGE}"' in html
    # base.html birden fazla <script> etiketi icerdigi icin (harici JS'ler,
    # font-awesome/bootstrap CDN linkleri vb.) TAM sayfa render'inda toplam
    # <script> sayisini degil, bu dalganin birlestirdigi ozel delegasyon
    # bloğunun sayfa basina TAM OLARAK 1 kez gectigini dogruluyoruz.
    assert html.count("count();document.querySelectorAll('form[data-confirm]').forEach(function(form){") == 1
    assert html.count("querySelectorAll('form[data-confirm]')") == 1
    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert not _JS_HREF_RE.search(html)
    # Bos context'te for donguleri (selected_people/all_people/logs) 'empty'
    # dallarina duser, sayfa yine de hatasiz tamamlanir.
    assert "Henüz seçili alıcı yok." in html
    assert "Aktif personel listesi alınamadı." in html
    assert "Mail log kaydı bulunamadı." in html


def test_orphan_settings_template_also_renders_with_zero_context_kwargs_regression(app) -> None:
    """Byte-birebir ayni oldugu icin bu orphan sablon da bos context'te
    ayni sekilde hatasiz render edilir -- ek regresyon guvencesi (canli
    route tarafindan boyle cagirilmiyor olsa da, template'in kendisi
    bagimsiz olarak gecerli)."""
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template("communication/daily_weather_mail_settings.html")

    assert "onsubmit=" not in html
    assert f'data-confirm="{SEND_NOW_CONFIRM_MESSAGE}"' in html
    # base.html birden fazla <script> etiketi icerdigi icin (harici JS'ler,
    # font-awesome/bootstrap CDN linkleri vb.) TAM sayfa render'inda toplam
    # <script> sayisini degil, bu dalganin birlestirdigi ozel delegasyon
    # bloğunun sayfa basina TAM OLARAK 1 kez gectigini dogruluyoruz.
    assert html.count("count();document.querySelectorAll('form[data-confirm]').forEach(function(form){") == 1
    assert html.count("querySelectorAll('form[data-confirm]')") == 1
    assert not _INLINE_EVENT_ATTR_RE.findall(html)


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_render_with_multiple_recipients_and_logs_preserves_confirm_and_csrf(relative_path: str, app) -> None:
    """N (3) alici + N (2) log kaydiyla render edilse bile send-now formunun
    data-confirm mesaji AYNEN korunur, CSRF/action/method bozulmaz, ve
    delegasyon script'i sayfa basina hala tam olarak 1 kez gecer (dongu
    tekrarindan etkilenmez -- form dongunun DISINDA)."""
    from flask import render_template

    recipients = [_fake_recipient(901), _fake_recipient(902), _fake_recipient(903)]
    logs = [_fake_log(1), _fake_log(2, is_success=False, status="failed", error_message="SMTP timeout")]
    template_name = relative_path.split("app/templates/", 1)[1]

    with app.test_request_context("/"):
        html = render_template(
            template_name,
            selected_users=recipients,
            users=recipients,
            selected_ids={901, 902},
            config={"run_hour": 8, "run_minute": 15, "enabled": True, "last_sent_date": "2026-08-02"},
            logs=logs,
        )

    assert "onsubmit=" not in html
    assert html.count(f'data-confirm="{SEND_NOW_CONFIRM_MESSAGE}"') == 1
    # base.html birden fazla <script> etiketi icerdigi icin (harici JS'ler,
    # font-awesome/bootstrap CDN linkleri vb.) TAM sayfa render'inda toplam
    # <script> sayisini degil, bu dalganin birlestirdigi ozel delegasyon
    # bloğunun sayfa basina TAM OLARAK 1 kez gectigini dogruluyoruz.
    assert html.count("count();document.querySelectorAll('form[data-confirm]').forEach(function(form){") == 1
    assert html.count("querySelectorAll('form[data-confirm]')") == 1
    # Render edilmis ciktida Jinja ifadesi ({{ csrf_token() }}) cozulmus
    # olmali; form etiketiyle data-confirm ve CSRF input'unun onek kismi
    # (gercek token degeri conftest ayarina gore degisebilir, o yuzden tam
    # deger degil yalnizca sabit onek kontrol edilir) hala AYNEN mevcut.
    assert (
        '<form method="post" action="/executive-summary/daily-weather-mail/send-now" '
        f'data-confirm="{SEND_NOW_CONFIRM_MESSAGE}">'
        '<input type="hidden" name="csrf_token" value="'
    ) in html
    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert "Wave8 Test Kullanıcı 901" in html
    assert "wave8user901@example.com" in html
    # class="selected-person" (kart div'i) tam olarak 3 kez -- CSS kuralindaki
    # ".selected-person{...}" tanimi (1 ek "selected-person" alt-string'i)
    # yanlislikla sayilmasin diye class attribute'unun tamami araniyor.
    assert html.count('<div class="selected-person">') == 3


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_render_with_empty_recipients_and_logs_still_has_single_script(relative_path: str, app) -> None:
    """Bos `selected_users`/`users`/`logs` listeleriyle ({% else %} dallari)
    render edilse bile delegasyon script'i tam olarak 1 kez render edilir
    ve confirm mesaji hala mevcuttur."""
    from flask import render_template

    template_name = relative_path.split("app/templates/", 1)[1]
    with app.test_request_context("/"):
        html = render_template(
            template_name,
            selected_users=[],
            users=[],
            selected_ids=set(),
            config={},
            logs=[],
        )

    assert "Henüz seçili alıcı yok." in html
    assert "Aktif personel listesi alınamadı." in html
    assert "Mail log kaydı bulunamadı." in html
    # base.html birden fazla <script> etiketi icerdigi icin (harici JS'ler,
    # font-awesome/bootstrap CDN linkleri vb.) TAM sayfa render'inda toplam
    # <script> sayisini degil, bu dalganin birlestirdigi ozel delegasyon
    # bloğunun sayfa basina TAM OLARAK 1 kez gectigini dogruluyoruz.
    assert html.count("count();document.querySelectorAll('form[data-confirm]').forEach(function(form){") == 1
    assert html.count("querySelectorAll('form[data-confirm]')") == 1
    assert f'data-confirm="{SEND_NOW_CONFIRM_MESSAGE}"' in html
    assert not _INLINE_EVENT_ATTR_RE.findall(html)


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_render_does_not_invoke_any_real_mail_or_weather_or_scheduler_code(relative_path: str, app) -> None:
    """Bu test render_template()'in SADECE Jinja motorunu calistirdigini,
    hicbir gercek mail-gonderme / weather-API / Windows Task Scheduler /
    PowerShell fonksiyonunu IMPORT ETMEDIGINI/CAGIRMADIGINI dolayli olarak
    dogrular: route modulleri (app.communication.daily_weather_mail_routes,
    app.dashboard.executive_summary_routes) bu testte HIC import edilmez --
    yalnizca `flask.render_template` ve `app` fixture'i (Flask app nesnesi,
    zaten conftest tarafindan olusturulmus) kullanilir. Render sirasinda
    olusan HTML metninde de gercek bir gonderim/API sonucuna dair hicbir
    iz (ornegin bir HTTP durum kodu, bir SMTP yaniti) yoktur -- yalnizca
    statik komut metinleri (`.command` bloklari) gorunur, bunlar hicbir
    zaman calistirilmaz."""
    from flask import render_template

    template_name = relative_path.split("app/templates/", 1)[1]
    with app.test_request_context("/"):
        html = render_template(template_name)

    # Komut bloklari yalnizca METIN olarak gorunur (kopyala-yapistir icin);
    # bu render cagrisi sirasinda gercekten calistirilmadiklarinin kaniti,
    # test surecinin sifir subprocess/network cagrisi yapmasidir (bkz.
    # bolum 0 -- bu dosyada hicbir subprocess/requests/urlopen cagrisi yok).
    assert "send_daily_weather_personnel_mail.py --force" in html
    assert "install_bys360_daily_mail_tasks_v1_4.ps1" in html
