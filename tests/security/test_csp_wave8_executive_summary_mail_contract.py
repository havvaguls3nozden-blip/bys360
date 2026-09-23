"""CSP Dalga 8 - Yönetici Özeti "Günlük Mail Görevleri" ayar ekranları kontrat testi.

BYS360 `app/security/headers.py` uygular:
    script-src: 'self' https:  (unsafe-inline YOK)

`app/security/headers.py::inject_csp_nonce_into_html` yanıt döndürdükten
sonra TÜM `<script>` etiketlerine (nonce'u olmayanlara) otomatik
`nonce="..."` ekler; bu merkezi mekanizma sayesinde template içindeki
`<script>...</script>` blokları zaten CSP ile uyumludur ve nonce hiçbir
zaman elle template'e yazılmaz. Asıl risk inline EVENT ATTRIBUTE'lardı
(`onclick=`, `onsubmit=` vb.) -- bunlara nonce uygulanmaz ve enforce modda
tarayıcı tarafından çalıştırılmazlar.

Bu dosyanın sahiplik alanı yalnızca şu iki template (toplam 1 benzersiz
handler, iki dosyada BİREBİR AYNI):
    - app/templates/executive_summary/daily_mail_tasks_premium.html
    - app/templates/executive_summary/daily_mail_tasks_v1_4.html

ORPHAN TEYİDİ (Wave 8'in kendi zamanında zaten doğru tespit edilmişti):
Bu iki dosya, dalga başlamadan önce de başladıktan sonra da
`grep -rn "daily_mail_tasks_premium\\|daily_mail_tasks_v1_4" app --include=*.py`
ile 0 (sıfır) eşleşme verir -- repo genelinde hiçbir `render_template()`
çağrısı bu iki dosya adını kullanmıyor. Yani bu ekranlar hiçbir route'a
bağlı değildi (muhtemelen eski/yedek ekran kopyaları).

SİLME (BYS360 Daily Weather/Mail Orphan Template Temizliği görevi): bu
doğru orphan tespitinin ardından her iki template de dosya sisteminden
SİLİNDİ. Bu dosyadaki TÜM eski statik/render testleri artık canlı
dosyaları DEĞİL, silme öncesi sabit bir git ref'ini (`PRE_DELETION_REF`)
okuyor -- böylece Wave 8'in orijinal CSP/confirm dönüşüm kanıtı SİLİNMEDEN
kalıcı olarak korunuyor (bkz. `_read()`/`_render_from_pre_deletion_ref()`).
Yeni `test_deleted_template_no_longer_exists_on_disk` testi silme sonrası
dosya-yokluğu sözleşmesini kilitler. Bu durum dönüşümün "gereksiz" olduğu
anlamına gelmiyordu -- kapsam kullanıcı tarafından açıkça bu iki dosya
olarak verilmişti; sonradan (ayrı bir görevde) her iki dosyanın da
gerçekten hiçbir route'a bağlanmadığı kesinleşince silindiler.

ÇÖZÜM (her iki dosyaya da BİREBİR AYNI şekilde uygulandı, Wave 8'in kendi
kapanışında): İki dosyada da tek risk aynı satırdaydı (döngü dışında,
sayfa başına bir kez render edilen "Sabah Mailini Gönder" formu):
    onsubmit="return confirm('Seçili alıcılara sabah hava durumu maili
    şimdi gönderilsin mi?');"
kaldırıldı,
    data-confirm="Seçili alıcılara sabah hava durumu maili şimdi
    gönderilsin mi?"
eklendi (mesaj birebir korunmuştur). Hemen yanındaki "Kuru Çalıştır"
formuna (action=".../dry-run") HİÇ dokunulmadı -- zaten onsubmit/confirm
içermiyordu ve koordinatör talimatı gereği ellenmedi.

Dosyanın sonunda (satır ~30) ZATEN var olan tek `<script>(function(){...});
</script>` bloğu (arama/filtre/checkbox-sayma JS'i) YENİ bir blok AÇILMADAN
kullanıldı: kurulu Dalga 1-7 `form[data-confirm]` submit-delegasyon deseni bu
MEVCUT IIFE'nin gövdesinin sonuna, son `count();` çağrısından hemen sonra ve
IIFE'yi kapatan `})();`'den hemen önce eklendi. Böylece dosya başına hâlâ tam
olarak 1 `<script` etiketi vardır (yeni harici veya yerel ikinci bir blok
YOK) ve tek delegasyon page-load başına bir kez kayıt olur.

GERÇEK MAIL/GÖREV ÇALIŞTIRILMADI: Bu dosyadaki hiçbir test (a) şablonların
bağlı olabileceği `/executive-summary/daily-weather-mail/*` route'larına
HTTP isteği atmaz -- yalnızca Jinja motoruyla `render_template_string()`
ile şablon PRE_DELETION_REF içeriğinden DOĞRUDAN render edilir, route
katmanına hiç girilmez; (b) gerçek SMTP/mail gönderme kodunu
(`app.executive_summary.mail_engine.send_executive_summary_email`,
`smtplib.SMTP`/`SMTP_SSL` kullanan fonksiyon) tetiklemez. Ayrıca
`test_render_never_calls_real_mail_send_function` testi bu gerçek gönderim
fonksiyonunu monkeypatch ile "çağrılırsa AssertionError fırlat" şeklinde
değiştirip tüm render senaryolarını çalıştırır ve fonksiyonun hiç
çağrılmadığını kanıtlar. `tests/conftest.py` ayrıca süreç genelinde
`MAIL_SUPPRESS_SEND=true` ve `WTF_CSRF_ENABLED=false` ortam bayraklarını
zaten ayarlar. Bu şablonlardaki
`scripts/windows/install_bys360_daily_mail_tasks_v1_4.ps1` ve benzeri
launcher komutları yalnızca `<div class="command">...</div>` içinde
METİN olarak GÖSTERİLİR -- bu dosyanın hiçbir testi o PowerShell
dosyalarını okumaz, çalıştırmaz veya değiştirmez.

ÖNEMLİ SINIRLAMA: Bu dosyadaki HİÇBİR test gerçek bir tarayıcıda
çalışmadı/çalıştırılmadı. Render testleri yalnızca ÜRETİLEN HTML'i
doğrular (inline handler yok, data-confirm attribute'u doğru, script bloğu
sayfa başına doğru sayıda render ediliyor). CSP enforce edilmiş gerçek bir
tarayıcıda "Sabah Mailini Gönder" butonunun confirm() diyaloğunu fiilen
açıp iptal edilebildiğini KANITLAMAZ -- bu, ayrı bir manuel/E2E doğrulama
gerektirir ve bu dosyanın kapsamı dışındadır.

Statik testler `tests/security/test_csp_wave7_support_help_contract.py` ile
aynı desendedir (git show + regex, sonra gerçek Jinja motoruyla
`render_template_string()` çıktı testleri; `app` fixture'ı
`tests/conftest.py`'den gelir).
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

PREMIUM_TEMPLATE = "app/templates/executive_summary/daily_mail_tasks_premium.html"
V1_4_TEMPLATE = "app/templates/executive_summary/daily_mail_tasks_v1_4.html"
BASE_TEMPLATE = "app/templates/base.html"

WAVE8_FILES = [PREMIUM_TEMPLATE, V1_4_TEMPLATE]

# Fixed commit immediately BEFORE the orphan-cleanup deletion commit -- the
# repo state where both templates still existed on disk.
PRE_DELETION_REF = "1d20cdeffdd1f20fe24c3f5414fa5d7ba498df47"

SEND_NOW_CONFIRM_MESSAGE = "Seçili alıcılara sabah hava durumu maili şimdi gönderilsin mi?"

# HTML attribute syntax: bosluk + on<harfler> + '=' + tirnak. CSS/JS icindeki
# "javascript:" gibi metinsel string literal'leri yanlislikla yakalamaz.
_INLINE_EVENT_ATTR_RE = re.compile(r"""[\s]on[a-zA-Z]+\s*=\s*["']""")
_JS_HREF_RE = re.compile(r"""(?:href|src)\s*=\s*["']\s*javascript:""", re.IGNORECASE)
_JS_URL_ANYWHERE_RE = re.compile(r"""javascript:""", re.IGNORECASE)

_FORBIDDEN_JS_SINKS = ("eval(", "new Function(", "document.write(")


def _git_show(ref: str, relative_path: str) -> str:
    result = subprocess.run(
        ["git", "show", f"{ref}:{relative_path}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        encoding="utf-8",
        errors="replace",
    )
    assert result.returncode == 0, f"'git show {ref}:{relative_path}' failed: {result.stderr!r}"
    return result.stdout


def _read(relative_path: str) -> str:
    """Reads the template's content at PRE_DELETION_REF -- both WAVE8_FILES
    were deleted after being confirmed orphan (see module docstring)."""
    return _git_show(PRE_DELETION_REF, relative_path)


def _render_from_pre_deletion_ref(app, relative_path: str, **context: object) -> str:
    from flask import render_template_string

    text = _git_show(PRE_DELETION_REF, relative_path)
    with app.test_request_context("/"):
        return render_template_string(text, **context)


def _fake_user(user_id: int, **overrides: object) -> dict[str, object]:
    base: dict[str, object] = dict(
        id=user_id,
        full_name=f"Wave8 Test Kullanıcı {user_id}",
        username=f"wave8user{user_id}",
        email=f"wave8user{user_id}@example.com",
        sicil_no=f"SC{user_id:04d}",
        birim="Bilgi İşlem",
        unvan="Uzman",
    )
    base.update(overrides)
    return base


def _fake_log(log_id: int, **overrides: object) -> dict[str, object]:
    base: dict[str, object] = dict(
        sent_at=None,
        created_at=f"2026-08-0{log_id % 9 + 1} 08:15",
        recipient_email=f"wave8log{log_id}@example.com",
        to_email=None,
        subject="Sabah Hava Durumu Bilgilendirmesi",
        is_success=True,
        status="success",
        error_message=None,
    )
    base.update(overrides)
    return base


def _render_context(**overrides: object) -> dict[str, object]:
    selected = [_fake_user(1), _fake_user(2)]
    all_people = [_fake_user(1), _fake_user(2), _fake_user(3)]
    base: dict[str, object] = dict(
        selected_users=selected,
        recipients=selected,
        users=all_people,
        selected_ids={1, 2},
        config={
            "enabled": True,
            "run_hour": 8,
            "run_minute": 15,
            "last_sent_date": "2026-08-02",
            "city": "Çanakkale",
            "latitude": "40.1553",
            "longitude": "26.4142",
            "last_result_json": {},
        },
        logs=[_fake_log(1), _fake_log(2, is_success=False, status="failed", error_message="SMTP zaman aşımı")],
        preview_error=None,
        preview=None,
    )
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# 1) Statik kaynak-kod kontratı (PRE_DELETION_REF'den git show + regex).
#    Kosulsuz calisir, Jinja if-bloklarinin arkasinda kalan durumlari da
#    yakalar.
# ---------------------------------------------------------------------------


def test_wave8_files_are_byte_identical() -> None:
    """Koordinator bulgusu: iki dosya donusum ONCESI byte-birebir aynıydı.
    Aynı düzeltme her iki dosyaya da BİREBİR AYNI şekilde uygulandığı için
    donusum SONRASI da (PRE_DELETION_REF'te) byte-birebir aynı kalmalidir."""
    premium = _read(PREMIUM_TEMPLATE)
    v1_4 = _read(V1_4_TEMPLATE)
    assert premium == v1_4


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
    """Bir inline handler'in HTML string'i olarak JS icinde uretilmedigini
    dogrular -- bu, delegasyonun DOM'a innerHTML/string ile geri
    sizdirilmadiginin kanitidir."""
    text = _read(relative_path)
    for literal in ("'onclick='", '"onclick="', "'onsubmit='", '"onsubmit="'):
        assert literal not in text, f"{relative_path} icinde yasakli JS string literal bulundu: {literal}"


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_wave8_file_send_now_form_has_data_confirm_message_verbatim(relative_path: str) -> None:
    text = _read(relative_path)
    assert "onsubmit=" not in text
    assert f'data-confirm="{SEND_NOW_CONFIRM_MESSAGE}"' in text
    assert text.count('data-confirm="') == 1


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_wave8_file_send_now_form_action_method_and_csrf_untouched(relative_path: str) -> None:
    """Form action/method ve CSRF hidden input'u degismedi -- yalnizca
    onsubmit -> data-confirm donusumu yapildi."""
    text = _read(relative_path)
    assert (
        '<form method="post" action="/executive-summary/daily-weather-mail/send-now" '
        f'data-confirm="{SEND_NOW_CONFIRM_MESSAGE}">'
        '<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">'
        in text
    )


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_wave8_file_dry_run_form_untouched_regression(relative_path: str) -> None:
    """Kapsam disi 'Kuru Calistir' formuna (confirm/onsubmit icermeyen,
    handler'i olmayan) hic dokunulmadi -- action/method/CSRF ve buton
    aynen korunmus olmali."""
    text = _read(relative_path)
    assert (
        '<form method="post" action="/executive-summary/daily-weather-mail/dry-run">'
        '<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">'
        '<button class="bys-btn soft" type="submit">'
        '<i class="fa-solid fa-vial-circle-check"></i> Kuru Çalıştır</button></form>'
        in text
    )
    assert 'data-confirm' not in text.split('dry-run">')[1].split('</form>')[0]


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_wave8_file_csrf_hidden_inputs_count_untouched(relative_path: str) -> None:
    """3 CSRF hidden input bekleniyor: dry-run formu, send-now formu ve
    mainSettingsForm -- hicbiri kaldirilmadi/bozulmadi."""
    text = _read(relative_path)
    assert text.count('<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">') == 3


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_wave8_file_has_exactly_one_script_block_with_no_new_block_opened(relative_path: str) -> None:
    """Yeni bir <script> bloğu ACILMADI -- mevcut tek IIFE'nin icine
    entegre edildi. Dosya basina hala tam olarak 1 <script etiketi var."""
    text = _read(relative_path)
    assert text.count("<script") == 1
    assert text.count("</script>") == 1


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_wave8_file_form_confirm_delegation_present_exactly_once(relative_path: str) -> None:
    text = _read(relative_path)
    assert text.count("querySelectorAll('form[data-confirm]')") == 1
    assert "if(m && !window.confirm(m))" in text
    assert "event.preventDefault();" in text


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_wave8_file_delegation_appended_inside_existing_iife_not_new_iife(relative_path: str) -> None:
    """Delegasyon kodunun mevcut IIFE'nin govdesinin SONUNA (son count()
    cagrisindan sonra, kapanan })(); parantezinden once) eklendigini, yeni
    bagimsiz bir (function(){...})(); olusturmadigini dogrular."""
    text = _read(relative_path)
    script_start = text.index("<script>(function(){")
    script_end = text.index("</script>", script_start)
    script_body = text[script_start:script_end]
    # Tek IIFE: yalnizca bir "(function(){" acilisi olmali.
    assert script_body.count("(function(){") == 1
    assert script_body.rstrip().endswith("})();")
    # Delegasyon, mevcut count() cagrilarindan SONRA (govdenin kuyruguna
    # eklendigi icin) gorunmeli.
    delegation_idx = script_body.index("querySelectorAll('form[data-confirm]')")
    last_count_idx = script_body.rindex("count();")
    assert delegation_idx > last_count_idx


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_wave8_file_preserves_existing_search_filter_and_count_logic_regression(relative_path: str) -> None:
    """Regresyon kilidi: arama/filtre ve secili-sayac mantigi (bu dalganin
    kapsami disi, onceden var olan islevsellik) hic degismedi."""
    text = _read(relative_path)
    assert "getElementById('recipientSearch')" in text
    assert "getElementById('selectedCountTop')" in text
    assert "getElementById('selectVisible')" in text
    assert "getElementById('clearVisible')" in text
    assert "recipient-cb" in text


def test_base_template_has_no_global_form_data_confirm_delegation() -> None:
    """Regresyon kilidi: `base.html` şu an KENDİ `form[data-confirm]`
    submit-delegasyonuna SAHİP DEĞİL. Wave8 şablonlarının kendi yerel
    delegasyonu bu varsayıma dayanır -- biri ileride base.html'e global bir
    form[data-confirm] delegasyonu eklerse bu, bu şablonların kendi yerel
    delegasyonuyla ÇİFT LİSTENER (çift confirm dialog'u) oluşturacağından
    bu test o riski erken yakalar."""
    text = (REPO_ROOT / BASE_TEMPLATE).read_text(encoding="utf-8")
    assert "querySelectorAll('form[data-confirm]')" not in text
    assert "data-confirm" not in text


def test_windows_powershell_launcher_scripts_untouched_by_this_wave() -> None:
    """Koordinator talimati: bu dalga scripts/windows altindaki hicbir
    PowerShell dosyasina dokunmamalidir (bu sablonlarda bu script'lerin
    yalnizca KOMUT METNI <div class="command"> icinde gosterilir, hicbir
    test/kod bunlari calistirmaz). Bu test, sablonlarin (PRE_DELETION_REF
    icindeki) o komut metinlerini hala degismeden referans verdigini
    dogrular (metin gosterimi -- calistirma degil)."""
    text = _read(V1_4_TEMPLATE)
    assert (
        "powershell -ExecutionPolicy Bypass -File "
        r".\scripts\windows\install_bys360_daily_mail_tasks_v1_4.ps1 -ProjectRoot "
        '"C:\\bys360\\project"'
        in text
    )
    # Bu sadece metin -- bu test dosyasi bu komutu asla subprocess/os.system
    # ile calistirmaz.


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_deleted_template_no_longer_exists_on_disk(relative_path: str) -> None:
    """Orphan-absence sözleşmesi: her iki template de artık dosya
    sisteminde YOK -- ORPHAN_CONFIRMED sınıflandırmasının silme kararının
    gerçekten uygulandığının kanıtı."""
    assert not (REPO_ROOT / relative_path).exists(), (
        f"{relative_path} hala diskte mevcut ama orphan-cleanup tarafindan silinmis "
        "olmasi bekleniyordu."
    )


# ---------------------------------------------------------------------------
# 2) Calisma-zamani render kontrolu: gercek Flask app + gercek Jinja motoru
#    ile PRE_DELETION_REF icerigini `render_template_string()` ile render
#    eder (bkz. `app` fixture, tests/conftest.py). ONEMLI: bu bolumdeki
#    HICBIR test route'a HTTP istegi atmaz.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_wave8_render_with_fake_recipients_has_no_inline_handlers(app, relative_path: str) -> None:
    html = _render_from_pre_deletion_ref(app, relative_path, **_render_context())

    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert not _JS_HREF_RE.search(html)
    assert "onsubmit=" not in html


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_wave8_render_confirm_message_and_form_action_preserved(app, relative_path: str) -> None:
    html = _render_from_pre_deletion_ref(app, relative_path, **_render_context())

    assert html.count(f'data-confirm="{SEND_NOW_CONFIRM_MESSAGE}"') == 1
    assert (
        '<form method="post" action="/executive-summary/daily-weather-mail/send-now" '
        f'data-confirm="{SEND_NOW_CONFIRM_MESSAGE}">'
        in html
    )
    assert html.count("querySelectorAll('form[data-confirm]')") == 1
    assert not _INLINE_EVENT_ATTR_RE.findall(html)


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_wave8_render_with_empty_recipients_and_logs_still_has_single_script(app, relative_path: str) -> None:
    """Bos alici/log listeleriyle ({% else %} dallari) render edilse bile
    delegasyon script'i tam olarak 1 kez render edilir ve inline handler
    kalmaz."""
    html = _render_from_pre_deletion_ref(
        app,
        relative_path,
        selected_users=[], recipients=[], users=[], selected_ids=set(), logs=[],
    )

    assert "Henüz seçili alıcı yok" in html
    assert "Aktif personel listesi alınamadı." in html
    assert "Mail log kaydı bulunamadı." in html
    assert html.count("querySelectorAll('form[data-confirm]')") == 1
    assert not _INLINE_EVENT_ATTR_RE.findall(html)


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_wave8_render_with_missing_optional_context_still_safe(app, relative_path: str) -> None:
    """Context'te hicbir opsiyonel deger verilmese bile (ChainableUndefined,
    bkz. `app/template_safety.py`) render hatasiz tamamlanir ve gonder
    formu hala data-confirm'e sahiptir. `selected_ids` ozellikle bos bir
    kumeyle verilir cunku sablon onu `|default` filtresi olmadan dogrudan
    `user.id in selected_ids` icinde kullanir."""
    html = _render_from_pre_deletion_ref(app, relative_path, selected_ids=set())

    assert f'data-confirm="{SEND_NOW_CONFIRM_MESSAGE}"' in html
    assert not _INLINE_EVENT_ATTR_RE.findall(html)


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_wave8_render_with_multiple_logs_success_and_failure_rows(app, relative_path: str) -> None:
    html = _render_from_pre_deletion_ref(
        app,
        relative_path,
        **_render_context(
            logs=[
                _fake_log(10, is_success=True, status="success"),
                _fake_log(11, is_success=False, status="failed", error_message="Bağlantı zaman aşımı"),
                _fake_log(12, is_success=False, status="pending", error_message=None),
            ]
        ),
    )

    assert "Başarılı" in html
    assert "Bağlantı zaman aşımı" in html
    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert html.count("querySelectorAll('form[data-confirm]')") == 1


@pytest.mark.parametrize("relative_path", WAVE8_FILES)
def test_wave8_render_does_not_perform_http_request_to_route(app, relative_path: str) -> None:
    """Bu testin dogasi geregi zaten bir route'a HTTP POST atmiyor -- yalnizca
    Jinja render cagrilir, `app.test_client()` hic kullanilmaz. Bu, sablonun
    bagli olabilecegi (mevcutta bagli OLMAYAN, bkz. orphan teyidi)
    `/executive-summary/daily-weather-mail/send-now` route handler'inin bu
    testte asla calismadiginin acik kanitidir."""
    html = _render_from_pre_deletion_ref(app, relative_path, **_render_context())

    assert isinstance(html, str)
    assert "/executive-summary/daily-weather-mail/send-now" in html
    # Bilincli olarak app.test_client().post(...) COGRULMADI -- bu test
    # dosyasinin hicbir yerinde bir HTTP istemcisi olusturulmaz veya route'a
    # istek gonderilmez.


def test_render_never_calls_real_mail_send_function(app, monkeypatch: pytest.MonkeyPatch) -> None:
    """Gercek mail gonderme fonksiyonunu (app.executive_summary.mail_engine.
    send_executive_summary_email, ic kisminda smtplib.SMTP/SMTP_SSL
    kullanir) monkeypatch ile "cagrilirsa AssertionError firlat" seklinde
    degistirip TUM Wave8 render senaryolarini calistirir. Fonksiyon hic
    cagrilmazsa (beklenen sonuc), bu satirlarin hicbiri patlamaz ve bu test
    PASS eder -- bu, render-only testlerin gercekten hicbir gercek mail
    gondermedigini calisma-zamaninda kanitlayan negatif kontroldur."""
    from app.executive_summary import mail_engine

    def _forbidden_send(*args: Any, **kwargs: Any) -> dict[str, Any]:
        raise AssertionError(
            "test_render_never_calls_real_mail_send_function: "
            "send_executive_summary_email GERCEKTEN cagrildi -- bu Wave8 "
            "sablon-render testlerinde KESINLIKLE olmamasi gereken bir yan "
            "etkidir."
        )

    monkeypatch.setattr(mail_engine, "send_executive_summary_email", _forbidden_send)

    for relative_path in WAVE8_FILES:
        html = _render_from_pre_deletion_ref(app, relative_path, **_render_context())
        assert isinstance(html, str)
        assert f'data-confirm="{SEND_NOW_CONFIRM_MESSAGE}"' in html

    # Buraya sorunsuz ulasilmasi (AssertionError firlamadan) fonksiyonun
    # hic cagrilmadiginin dogrudan kanitidir.
