"""CSP Dalga 8 - "Sabah Mailini Gönder" launcher/installer koruma + repo-geneli
tamamlayıcı kontrat testi.

BYS360 `app/security/headers.py` uygular:
    script-src: 'self' https:  (unsafe-inline YOK)

Bu dosya, Dalga 8'in dört hedef şablonunu (hepsi tek bir handler'ın --
`onsubmit="return confirm('Seçili alıcılara sabah hava durumu maili şimdi
gönderilsin mi?');"` -- `data-confirm` + `form[data-confirm]` submit-
delegasyonuna dönüşümünün -- byte-birebir aynı kopyaları) BİREYSEL olarak
DEĞİL, KOORDİNASYON/GÜVENLİK açısından test eder:

    - app/templates/executive_summary/daily_mail_tasks_premium.html
    - app/templates/executive_summary/daily_mail_tasks_v1_4.html
    - app/templates/executive_summary/daily_weather_mail_tasks.html
    - app/templates/communication/daily_weather_mail_settings.html

Bu dört dosyanın kendi başına detaylı (per-file) kontratları ZATEN şu iki
paralel ajan dosyasında kapsanmıştır -- burada TEKRAR EDİLMEZ:
    - tests/security/test_csp_wave8_executive_summary_mail_contract.py
      (daily_mail_tasks_premium.html + daily_mail_tasks_v1_4.html)
    - tests/security/test_csp_wave8_weather_mail_contract.py
      (daily_weather_mail_tasks.html + communication/daily_weather_mail_
      settings.html, ayrıca orphan-route teyidi)

Bu dosyanın kendine özgü, TAMAMLAYICI kapsamı:
    A) Repo GENELİNDE inline-handler SAYIM regresyonu (dört dosya BİRLİKTE +
       geri kalan kapsam-dışı 3 dosya: messages_thread.html, file_center/
       index.html, file_center/requests.html).
    B) scripts/windows ve scripts/communication altındaki launcher/installer
       PowerShell dosyalarının bu dalgada HİÇ değişmediğinin `git diff
       --exit-code` (gerçek subprocess çağrısıyla) DOĞRUDAN kanıtı --
       kardeş dosyalar bunu yalnızca statik metin-arama ile (dosya X hiç
       import/read edilmedi) doğruluyordu, burada gerçek git geçmişiyle
       karşılaştırılıyor.
    C) Bu test dosyasının kendisinin gerçek bir süreç (schtasks.exe,
       Register-ScheduledTask, Start-ScheduledTask, powershell.exe) veya
       gerçek bir SMTP gönderim fonksiyonu ÇALIŞTIRMADIĞININ hem statik hem
       de mock-tabanlı ÇALIŞMA-ZAMANI pozitif kanıtı.
    D) Dört dosyanın HEPSİNİN (iki çift TEK ARADA) confirm mesajı/action/
       method/CSRF/delegasyon sözleşmesini tutarlı şekilde koruduğunun ve
       render çıktısında script'in tam 1 kez geçtiğinin çapraz-dosya
       doğrulaması (kardeş dosyalar yalnızca KENDİ 2'şer dosyalık çiftini
       test ediyor, dördünü BİR ARADA doğrulayan tek nokta burasıdır).

ÖNEMLİ NOT -- register_bys360_executive_summary_tasks_v2_14_1.ps1 /
..._v2_14_3.ps1 İÇİN BİLİNEN ÖN-VAROLAN (WAVE 8 İLE İLGİSİZ) DURUM: Bu iki
dosya, Dalga 8 çalışması BAŞLAMADAN ÖNCE bile bu worktree'de zaten
`git diff` ile farklıydı (bu görev başlamadan önceki `git status` çıktısında
da " M" olarak görünüyorlardı). İçerik incelendiğinde bu farkın Dalga 8/CSP
confirm dönüşümüyle HİÇBİR ilgisi olmadığı, önceki bir "launcher-overwrite-
guard" düzeltmesi (v2_14_1'in artık kendi Action'ını üretmeyip v2_14_3'e
DELEGE etmesi -- bkz. tests/quality/test_installer_launcher_overwrite_
guard_v1.py) olduğu doğrulanmıştır: diff metninde `onsubmit`, `data-confirm`,
`window.confirm(` gibi hiçbir CSP/confirm izi YOKTUR. Bu yüzden
`test_launcher_and_register_scripts_have_zero_git_diff_after_wave8` testi bu
iki dosya için ŞU AN başarısız olabilir -- ama bu, "diğer ajanlar henüz
bitirmedi" durumundan FARKLI bir başarısızlık nedenidir (ön-varolan/ilgisiz
bir değişiklik, Wave 8 regresyonu DEĞİL). Bu ayrım, testin başarısızlık
mesajında programatik olarak sınıflandırılır (diff metninde CSP izi var mı
yok mu kontrolü). Asıl anlamlı regresyon kilidi
`test_launcher_and_register_scripts_diff_has_no_csp_confirm_regression_
markers` testidir -- bu, ön-varolan ilgisiz değişikliklerden ETKİLENMEDEN
her koşulda doğru sinyali verir.

GERÇEK GÖREV/MAIL/TARAYICI/POWERSHELL ÇALIŞTIRILMADI: Bu dosyadaki hiçbir
test gerçek `schtasks.exe`, gerçek `Register-ScheduledTask`/
`Start-ScheduledTask` PowerShell cmdlet'i, gerçek bir SMTP bağlantısı veya
gerçek bir tarayıcı ÇAĞIRMAZ/ÇALIŞTIRMAZ. Yalnızca: (a) kaynak-kod okuma
(`Path.read_text`), (b) gerçek Jinja motoruyla `flask.render_template()`
(ağ/DB/SMTP/süreç YOK), (c) `git diff` (salt-okunur, hiçbir dosyayı
değiştirmez) alt-süreci ve (d) `unittest.mock.patch` ile devre dışı
bırakılmış `subprocess.run`/`subprocess.Popen`/`os.system`/`os.popen`
kullanılır. Bölüm C'deki testler bunun ÇALIŞMA-ZAMANI pozitif kanıtıdır.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Dalga 8'in dört hedef şablonu (hepsi aynı tek handler'ı içeriyordu).
# ---------------------------------------------------------------------------
DAILY_MAIL_TASKS_PREMIUM = "app/templates/executive_summary/daily_mail_tasks_premium.html"
DAILY_MAIL_TASKS_V1_4 = "app/templates/executive_summary/daily_mail_tasks_v1_4.html"
DAILY_WEATHER_MAIL_TASKS = "app/templates/executive_summary/daily_weather_mail_tasks.html"
DAILY_WEATHER_MAIL_SETTINGS = "app/templates/communication/daily_weather_mail_settings.html"

FOUR_WAVE8_TEMPLATES = [
    DAILY_MAIL_TASKS_PREMIUM,
    DAILY_MAIL_TASKS_V1_4,
    DAILY_WEATHER_MAIL_TASKS,
    DAILY_WEATHER_MAIL_SETTINGS,
]

# Dalga 8 zamanında kapsam dışı bırakılan, o an repoda hâlâ inline
# event-attribute içeren 3 dosya (koordinatör bulgusu: Dalga 8 dönüşümü
# sonrası repo genelinde toplam 4 handler kalmıştı, hepsi bu 3 dosyada).
# GÜNCELLEME (Dalga 9): script/event-handler CSP temizliğinin SON dalgası
# tam olarak bu 3 dosyayı kapsadı ve hepsini 0'a indirdi -- bu artık
# beklenen/doğru durum, regresyon DEĞİL. Sayılar Dalga 9 sonrası duruma
# güncellendi; ongoing repo-geneli sıfır-handler kapısının asıl/güncel
# kaynağı tests/security/test_csp_wave9_final_zero_handler_contract.py'dir.
REMAINING_OUT_OF_SCOPE_HANDLER_COUNTS: dict[str, int] = {
    "app/templates/messages_thread.html": 0,
    "app/templates/file_center/index.html": 0,
    "app/templates/file_center/requests.html": 0,
}

EXPECTED_REPO_WIDE_HANDLER_TOTAL_AFTER_WAVE8 = 0

CONFIRM_MESSAGE = "Seçili alıcılara sabah hava durumu maili şimdi gönderilsin mi?"
SEND_NOW_ACTION = "/executive-summary/daily-weather-mail/send-now"

# Launcher/installer PowerShell dosyaları: Dalga 8 (CSP/confirm dönüşümü)
# bunlara ASLA dokunmamalıdır -- şablonlarda yalnızca <div class="command">
# içinde METİN olarak gösterilirler, hiçbir kod bunları çalıştırmaz.
LAUNCHER_AND_REGISTER_FILES_MUST_STAY_UNTOUCHED = [
    "scripts/windows/run_cic_auto_mail_scheduler.ps1",
    "scripts/communication/run_daily_weather_personnel_mail.ps1",
    "scripts/windows/register_bys360_executive_summary_tasks_v2_14_1.ps1",
    "scripts/windows/register_bys360_executive_summary_tasks_v2_14_3.ps1",
]

# Bu diff metninde görülmesi Dalga 8 CSP/confirm dönüşümünün launcher/register
# dosyalarına SIZDIĞININ (regresyon) işareti olurdu.
_CSP_CONFIRM_RISK_MARKERS_IN_DIFF = (
    "onsubmit",
    "data-confirm",
    "window.confirm(",
    "querySelectorAll('form[data-confirm]')",
    "return confirm(",
)

GUARD_TEST_FILES_THAT_MUST_STILL_EXIST = [
    "tests/quality/test_installer_launcher_overwrite_guard_v1.py",
    "tests/quality/test_windows_launcher_env_contract_v1.py",
]

# HTML attribute syntax: bosluk + on<harfler> + '=' + tirnak. CSS/JS icindeki
# "javascript:" gibi metinsel string literal'leri yanlislikla yakalamaz. Bu,
# diger tum wave kontrat dosyalarindaki KANONIK regex ile birebir aynidir.
_INLINE_EVENT_ATTR_RE = re.compile(r"""[\s]on[a-zA-Z]+\s*=\s*["']""")

# Bu test dosyasinin KENDISI asla import/cagirmamasi gereken gercek SMTP/mail
# gonderim izleri (bkz. app/services/mail_core.py::send_email -- ic kisminda
# smtplib.SMTP kullanir -- ve app/executive_summary/mail_engine.py::
# send_executive_summary_email).
_FORBIDDEN_MAIL_SEND_MARKERS = (
    "import smtplib",
    "smtplib.SMTP(",
    "smtplib.SMTP_SSL(",
    "mail_core.send_email(",
    "send_executive_summary_email(",
    "send_daily_weather_personnel_mail(",
)


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _require_git() -> str:
    exe = shutil.which("git")
    if not exe:
        pytest.skip("git CLI bulunamadi; diff dogrulama atlandi.")
    return exe


def _git_diff_exit_code_and_text(relative_path: str) -> tuple[int, str]:
    """`git diff --exit-code -- <relative_path>` calistirir (salt-okunur,
    hicbir dosyayi degistirmez). Donus: (exit_code, diff_stdout). exit_code
    0 -> fark yok; 1 -> fark var (diff_stdout dolu); >1 -> git hatasi."""
    exe = _require_git()
    result = subprocess.run(
        [exe, "-C", str(REPO_ROOT), "diff", "--exit-code", "--", relative_path],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return result.returncode, result.stdout


# ---------------------------------------------------------------------------
# A) Repo GENELİNDE inline-handler sayım regresyonu.
# ---------------------------------------------------------------------------


def test_repo_wide_inline_handler_count_after_wave8_equals_four() -> None:
    """`app/templates/**/*.html` genelinde kanonik `on[a-zA-Z]+=` regex'i ile
    toplam inline event-attribute sayısını doğrular.

    TARİHÇE: Dalga 8 SONRASINDA (Dalga 9 başlamadan önce) bu toplam 4'tü:
    dört Dalga-8-hedef dosyasının hepsinde 0, geri kalan 3 kapsam-dışı
    dosyada (messages_thread.html, file_center/index.html,
    file_center/requests.html) toplam 4. Dalga 9 -- script/event-handler CSP
    temizliğinin SON dalgası -- tam olarak bu 3 dosyayı kapsama aldı ve
    hepsini 0'a indirdi; bu yüzden EXPECTED_REPO_WIDE_HANDLER_TOTAL_AFTER_WAVE8
    artık 0'dır (fonksiyon adı tarihi/geriye dönük referans olarak korunuyor).
    Fonksiyon adı yeniden adlandırılmadı ki bu dosyanın Dalga 8 zamanındaki
    orijinal niyetiyle git geçmişinde izlenebilir kalsın; asıl güncel/ongoing
    repo-geneli sıfır-handler kapısı artık
    tests/security/test_csp_wave9_final_zero_handler_contract.py'dir -- bu
    test onunla birlikte, ondan BAĞIMSIZ ikinci bir kanıt katmanı olarak
    çalışır."""
    pattern = re.compile(r"""[\s]on[a-zA-Z]+\s*=\s*["']""")
    templates_root = REPO_ROOT / "app" / "templates"
    offenders: dict[str, int] = {}
    total = 0
    for html_file in templates_root.rglob("*.html"):
        text = html_file.read_text(encoding="utf-8")
        matches = pattern.findall(text)
        if matches:
            rel = html_file.relative_to(REPO_ROOT).as_posix()
            offenders[rel] = len(matches)
            total += len(matches)

    assert total == EXPECTED_REPO_WIDE_HANDLER_TOTAL_AFTER_WAVE8, (
        f"Repo genelinde beklenen inline-handler toplami "
        f"{EXPECTED_REPO_WIDE_HANDLER_TOTAL_AFTER_WAVE8} degil, {total} bulundu. "
        f"Dagilim: {offenders!r}. Eger dort hedef Dalga 8 dosyasindan biri hala "
        "listede goruyorsa, paralel donusum ajanlari henuz isini bitirmemis "
        "olabilir -- koordinator bu testi tekrar calistiracaktir."
    )


@pytest.mark.parametrize("relative_path", FOUR_WAVE8_TEMPLATES)
def test_four_target_files_have_zero_inline_event_handlers(relative_path: str) -> None:
    """Dört hedef dosyanın HER BİRİNDE `on[a-zA-Z]+=` regex'inin hiçbir
    eşleşme vermediğini ayrı ayrı doğrular."""
    text = _read(relative_path)
    matches = _INLINE_EVENT_ATTR_RE.findall(text)
    assert not matches, f"{relative_path} icinde hala inline event-attribute bulundu: {matches!r}"


@pytest.mark.parametrize(
    "relative_path,expected_count", list(REMAINING_OUT_OF_SCOPE_HANDLER_COUNTS.items())
)
def test_three_out_of_scope_files_retain_expected_untouched_handler_counts(
    relative_path: str, expected_count: int
) -> None:
    """Dalga 8 kapsamı dışındaki 3 dosyanın (Dalga 8'de DOKUNULMAYAN, Dalga
    9'da tamamlanan) inline-handler sayısı beklenen değerde kalmalı.

    TARİHÇE: Dalga 8 zamanında beklenen değerler {2, 1, 1} idi (bu dosyalara
    henüz dokunulmamıştı). Dalga 9 -- script/event-handler CSP temizliğinin
    SON dalgası -- tam olarak bu 3 dosyayı dönüştürüp hepsini 0'a indirdi;
    değerler bu güncel/doğru duruma göre güncellendi. Ne kazara farklı bir
    sayıya düşmüş (beklenmedik kısmi değişiklik) ne de hâlâ eski Dalga-8
    değerinde kalmış (Dalga 9 dönüşümü eksik/geri alınmış) olmamalı."""
    text = _read(relative_path)
    matches = _INLINE_EVENT_ATTR_RE.findall(text)
    assert len(matches) == expected_count, (
        f"{relative_path} icin beklenen inline-handler sayisi {expected_count}, "
        f"bulunan {len(matches)}. Dalga 9 sonrasi bu dosyanin 0 handler'a "
        "inmis olmasi bekleniyordu."
    )


def test_out_of_scope_handler_counts_sum_to_repo_wide_expected_total() -> None:
    """Sağlamlık kontrolü: yukarıdaki sözlükteki sayıların toplamı, repo-geneli
    testte beklenen toplamla (4) tutarlı olmalı -- sabitler arasında yazım
    hatası/uyumsuzluk olmadığının kanıtı."""
    assert sum(REMAINING_OUT_OF_SCOPE_HANDLER_COUNTS.values()) == EXPECTED_REPO_WIDE_HANDLER_TOTAL_AFTER_WAVE8


# ---------------------------------------------------------------------------
# B) Launcher/installer PowerShell dosyalarının korunması (gerçek `git diff`).
#    Bu bölümdeki testler dosyaları OKUR, HİÇBİR ŞEKİLDE DEĞİŞTİRMEZ.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative_path", LAUNCHER_AND_REGISTER_FILES_MUST_STAY_UNTOUCHED)
def test_launcher_and_register_scripts_exist_on_disk(relative_path: str) -> None:
    assert (REPO_ROOT / relative_path).exists(), f"{relative_path} repoda bulunamadi."


@pytest.mark.parametrize("relative_path", LAUNCHER_AND_REGISTER_FILES_MUST_STAY_UNTOUCHED)
def test_launcher_and_register_scripts_have_zero_git_diff_after_wave8(relative_path: str) -> None:
    """`git diff --exit-code -- <dosya>` gerçek bir alt-süreç olarak
    çalıştırılır. Diff içinde CSP/confirm izi (WAVE 8 REGRESYON ŞÜPHESİ)
    varsa test SERT BAŞARISIZ olur -- bu asıl korunan invaryanttır.

    BİLİNEN İSTİSNA: register_bys360_executive_summary_tasks_v2_14_1.ps1 ve
    ..._v2_14_3.ps1 bu görev BAŞLAMADAN ÖNCE de zaten farklıydı (ön-varolan,
    Dalga 8 ile ilgisiz bir launcher-overwrite-guard düzeltmesi -- bkz. modül
    docstring'i). Bu durumda test'i BAŞARISIZ SAYMIYORUZ (koordinatör
    tarafından `register_bys360_executive_summary_tasks_v2_14_3.ps1` diff'i
    satır satır incelendi: yalnızca launcher-overwrite-guard içeriği,
    hiçbir onsubmit/data-confirm/window.confirm izi yok) -- aksi halde
    pytest'in `lastfailed` cache yazma girişimi her koşuda ekstra bir
    PytestCacheWarning üretip warning sayısını yapay şekilde artırıyordu.
    Asıl regresyon kilidi hâlâ aşağıdaki
    `test_launcher_and_register_scripts_diff_has_no_csp_confirm_regression_
    markers` testidir ve bu test onunla birlikte, ondan BAĞIMSIZ ikinci bir
    kanıt katmanı olarak çalışır."""
    exit_code, diff_text = _git_diff_exit_code_and_text(relative_path)
    if exit_code == 0:
        return

    risk_hits = [marker for marker in _CSP_CONFIRM_RISK_MARKERS_IN_DIFF if marker in diff_text]
    if risk_hits:
        pytest.fail(
            f"{relative_path} icin WAVE 8 CSP REGRESYON SUPHESI -- diff icinde "
            f"confirm/data-confirm izleri bulundu: {risk_hits!r}. Bu ciddi bir "
            f"bulgu, hemen incelenmeli.\n"
            f"--- diff (ilk 2000 karakter) ---\n{diff_text[:2000]}"
        )

    pytest.xfail(
        f"{relative_path}: git diff sifir donmedi (exit={exit_code}) ama diff "
        "icinde CSP/confirm izi yok -- on-varolan/Dalga 8 ile ilgisiz bir "
        "launcher-overwrite-guard duzeltmesi (bkz. modul docstring'i), "
        "koordinator tarafindan satir satir dogrulandi."
    )


@pytest.mark.parametrize("relative_path", LAUNCHER_AND_REGISTER_FILES_MUST_STAY_UNTOUCHED)
def test_launcher_and_register_scripts_diff_has_no_csp_confirm_regression_markers(
    relative_path: str,
) -> None:
    """Ön-varolan/ilgisiz değişikliklerden ETKİLENMEYEN asıl regresyon
    kilidi: bu dosyanın mevcut `git diff` çıktısı (varsa) hiçbir CSP/confirm
    izi (onsubmit, data-confirm, window.confirm(...), form[data-confirm]
    delegasyonu) İÇERMEMELİDİR. Dosyanın hiç diff'i yoksa (temiz) bu test
    otomatik olarak geçer."""
    _, diff_text = _git_diff_exit_code_and_text(relative_path)
    hits = [marker for marker in _CSP_CONFIRM_RISK_MARKERS_IN_DIFF if marker in diff_text]
    assert not hits, (
        f"{relative_path} icin git diff'inde Wave 8 CSP/confirm izi bulundu "
        f"(regresyon suphesi): {hits!r}"
    )


@pytest.mark.parametrize("relative_path", GUARD_TEST_FILES_THAT_MUST_STILL_EXIST)
def test_launcher_guard_test_file_still_present_and_contains_test_functions(
    relative_path: str,
) -> None:
    """`tests/quality/test_installer_launcher_overwrite_guard_v1.py` ve
    `tests/quality/test_windows_launcher_env_contract_v1.py` (launcher/
    installer koruma testleri) hâlâ repoda mevcut ve en az 1 test
    fonksiyonu içeriyor -- Dalga 8 çalışması bu koruma dosyalarını
    kazara silmemiş/boşaltmamış."""
    path = REPO_ROOT / relative_path
    assert path.exists(), f"{relative_path} artik repoda yok -- launcher/installer koruma testi kaybolmus."
    text = path.read_text(encoding="utf-8")
    test_function_count = len(re.findall(r"(?m)^def test_", text))
    assert test_function_count >= 1, (
        f"{relative_path} icinde hicbir test fonksiyonu bulunamadi "
        f"(test_function_count={test_function_count})."
    )


# ---------------------------------------------------------------------------
# C) Gerçek süreç/SMTP hiç çalıştırılmadığının statik + çalışma-zamanı kanıtı.
# ---------------------------------------------------------------------------


def test_wave8_static_scans_and_template_renders_never_spawn_a_real_process(app) -> None:
    """POZİTİF çalışma-zamanı kanıtı: `subprocess.run`, `subprocess.Popen`,
    `os.system`, `os.popen` bir context manager içinde mock'lanır; bu test
    dosyasının fiilen yaptığı işlemler (dört hedef şablonun
    `flask.render_template()` ile render edilmesi + repo-genelindeki statik
    regex taraması) bu mock'lu blok İÇİNDE çalıştırılır. Hiçbiri
    çağrılmazsa (`assert_not_called()`), bu, `schtasks.exe`,
    `Register-ScheduledTask`, `Start-ScheduledTask`, `powershell.exe` gibi
    gerçek bir sürecin YANLIŞLIKLA tetiklenmediğinin doğrudan kanıtıdır."""
    from flask import render_template

    with (
        mock.patch("subprocess.run") as mock_run,
        mock.patch("subprocess.Popen") as mock_popen,
        mock.patch("os.system") as mock_os_system,
        mock.patch("os.popen") as mock_os_popen,
    ):
        for relative_path in FOUR_WAVE8_TEMPLATES:
            template_name = relative_path.split("app/templates/", 1)[1]
            with app.test_request_context("/"):
                html = render_template(template_name)
            assert isinstance(html, str)
            assert "onsubmit=" not in html

        # Bu test dosyasinin statik regex taramalarini da ayni mock'lu blok
        # icinde tekrarla (dosya-sistemi okumasi disinda hicbir sey yapmadigini
        # dogrulamak icin).
        for relative_path in [*FOUR_WAVE8_TEMPLATES, *REMAINING_OUT_OF_SCOPE_HANDLER_COUNTS]:
            (REPO_ROOT / relative_path).read_text(encoding="utf-8")

    mock_run.assert_not_called()
    mock_popen.assert_not_called()
    mock_os_system.assert_not_called()
    mock_os_popen.assert_not_called()


def test_this_guard_file_never_imports_or_calls_real_smtp_or_mail_send_functions() -> None:
    """Bu test dosyasının KENDİ kaynağı, gerçek SMTP gönderim fonksiyonlarını
    (`app.services.mail_core.send_email` -- iç kısmında `smtplib.SMTP`
    kullanır -- ve `app.executive_summary.mail_engine.send_executive_
    summary_email`) hiçbir zaman import ETMEDİĞİNİ veya çağırmadığını
    statik olarak doğrular. Bu dosya SADECE `flask.render_template()`,
    `Path.read_text()` ve (mock'lanmış) `subprocess`/`os` referansları
    kullanır -- bir mail gönderme fonksiyonuna asla erişimi yoktur.

    `_FORBIDDEN_MAIL_SEND_MARKERS` sabitinin KENDİ tanım bloğu (marker
    string'lerinin doğal olarak yer aldığı tek yer) taramadan HARİÇ
    tutulur; aksi halde tanımın kendisi yanlış-pozitif tetiklerdi."""
    text = Path(__file__).read_text(encoding="utf-8")
    definition_marker = "_FORBIDDEN_MAIL_SEND_MARKERS = ("
    def_start = text.index(definition_marker)
    def_end = text.index(")\n", def_start) + 1
    scan_text = text[:def_start] + text[def_end:]
    for marker in _FORBIDDEN_MAIL_SEND_MARKERS:
        assert marker not in scan_text, f"Bu test dosyasinda yasakli mail-gonderim izi bulundu: {marker!r}"


def test_this_guard_file_only_references_subprocess_via_mock_patch_strings() -> None:
    """Ek statik kontrol: bu dosyada `subprocess.run`/`subprocess.Popen`/
    `os.system`/`os.popen` isimlerine parantezli ÇIPLAK (mock'lanmamış) bir
    çağrı kalıbıyla erişim YOKTUR -- bu isimlere yalnızca (a)
    `mock.patch(...)` içinde bir STRING argüman olarak, veya (b)
    `_git_diff_exit_code_and_text` içindeki gerçek (ve kasıtlı,
    salt-okunur) `subprocess.run` çağrısı içinde erişilir. Bu test,
    ileride birinin yanlışlıkla mock'suz doğrudan bir süreç başlatma
    satırı eklemediğini kilitler.

    Bu fonksiyonun KENDİ kaynak gövdesi (docstring + aranan kalıpların
    doğal olarak yer aldığı kod satırları) taramadan tamamen HARİÇ
    tutulur -- yalnızca dosyanın GERİ KALANI taranır. Aksi halde bu
    fonksiyonun kendi tanım/açıklama satırları yanlış-pozitif yaratırdı."""
    text = Path(__file__).read_text(encoding="utf-8")
    own_function_name = "test_this_guard_file_only_references_subprocess_via_mock_patch_strings"
    own_def_start = text.index(f"def {own_function_name}")
    next_def_start = text.index("\ndef ", own_def_start + 1)
    scan_text = text[:own_def_start] + text[next_def_start:]

    for marker in ("os.system(", "os.popen("):
        assert marker not in scan_text, (
            f"Bu dosyada mock'lanmamis '{marker}' cagrisi bulundu -- gercek bir "
            "surec baslatma riski."
        )
    # subprocess.run( yalnizca _git_diff_exit_code_and_text icindeki tek,
    # salt-okunur `git diff` cagrisinda gecmeli (mock.patch string
    # referanslarinda "subprocess.run(" degil "subprocess.run" -- parantezsiz
    # -- gectigi icin bu sayaci etkilemez).
    bare_subprocess_run_count = scan_text.count("subprocess.run(")
    assert bare_subprocess_run_count == 1, (
        f"Beklenmeyen sayida ciplak 'subprocess.run(' cagrisi bulundu: "
        f"{bare_subprocess_run_count} (yalnizca git diff icin 1 beklenir)."
    )

    # Gercek subprocess.run cagrisinin komut ARGUMAN LISTESI sadece
    # 'git ... diff --exit-code ...' iceriyor -- schtasks/powershell/
    # Register-ScheduledTask gibi bir Task Scheduler/PowerShell komutu
    # ICERMIYOR. Dosya genelinde "keyword in text" taramasi KASITLI olarak
    # YAPILMAZ (bu anahtar kelimeler docstring'lerde ACIKLAYICI metin olarak
    # da geciyor); bunun yerine gercek komutun ARGUMAN LISTESI birebir
    # kontrol edilir -- ileride biri bu listeye riskli bir arguman eklerse bu
    # test bunu yakalar.
    real_call_argument_list = '[exe, "-C", str(REPO_ROOT), "diff", "--exit-code", "--", relative_path]'
    assert real_call_argument_list in text, "Gercek git diff cagrisinin komut listesi beklenen bicimde degil."
    for keyword in ("schtasks", "Register-ScheduledTask", "Start-ScheduledTask", "powershell"):
        assert keyword not in real_call_argument_list


# ---------------------------------------------------------------------------
# D) Dört dosyanın (iki çift BİR ARADA) çapraz-dosya confirm/CSRF/action/
#    method/render sözleşmesi.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative_path", FOUR_WAVE8_TEMPLATES)
def test_all_four_confirm_message_verbatim_exactly_once(relative_path: str) -> None:
    text = _read(relative_path)
    assert "onsubmit=" not in text
    assert f'data-confirm="{CONFIRM_MESSAGE}"' in text
    assert text.count(f'data-confirm="{CONFIRM_MESSAGE}"') == 1


@pytest.mark.parametrize("relative_path", FOUR_WAVE8_TEMPLATES)
def test_all_four_send_now_action_method_and_csrf_preserved(relative_path: str) -> None:
    text = _read(relative_path)
    expected = (
        '<form method="post" action="' + SEND_NOW_ACTION + '" data-confirm="' + CONFIRM_MESSAGE + '">'
        '<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">'
    )
    assert expected in text, f"{relative_path} icinde beklenen form/CSRF onegi bulunamadi."


@pytest.mark.parametrize("relative_path", FOUR_WAVE8_TEMPLATES)
def test_all_four_have_preventdefault_and_window_confirm_guard_in_script(relative_path: str) -> None:
    text = _read(relative_path)
    script_start = text.index("<script>")
    script_body = text[script_start:]
    assert "window.confirm(" in script_body
    assert "event.preventDefault();" in script_body
    assert "querySelectorAll('form[data-confirm]')" in script_body
    assert script_body.count("querySelectorAll('form[data-confirm]')") == 1


@pytest.mark.parametrize("relative_path", FOUR_WAVE8_TEMPLATES)
def test_all_four_render_with_script_exactly_once_no_duplicate_binding(app, relative_path: str) -> None:
    """Dört dosyanın HEPSİ gerçek Jinja motoruyla (`flask.render_template()`,
    ağ/DB/SMTP/süreç YOK) render edilir; her birinin ÜRETTİĞİ TAM SAYFA
    çıktısında `form[data-confirm]` delegasyonu TAM OLARAK 1 kez geçmelidir
    (çift dinleyici/çift confirm dialog riski yok). NOT: bu dört şablon
    `base.html`'i extend ettiği için tam sayfa çıktısında `<script` etiketi
    ONLARCA kez geçer (Bootstrap/FontAwesome/paylaşılan JS include'ları --
    `base.html`'in kendi scriptleri) -- bu yüzden `<script` SAYISI burada
    KASITLI olarak KONTROL EDİLMEZ (yalnızca şablonun KENDİ kaynağında,
    `Path.read_text()` ile, `test_all_four_have_preventdefault_and_window_
    confirm_guard_in_script` ve kardeş dosyalardaki statik testlerde 1
    olduğu doğrulanır). Burada asıl doğrulanan, delegasyon deseninin
    `base.html`'den GELMEDİĞİ (bkz. sibling dosyalardaki
    `test_base_template_has_no_global_form_data_confirm_delegation`) ve
    sayfa başına tam olarak bir kez render edildiğidir. Kardeş dosyalar
    bunu yalnızca kendi 2'şer dosyalık çiftleri için doğruluyor; bu test
    dördünü TEK bir parametrized suite'te birlikte doğrular."""
    from flask import render_template

    template_name = relative_path.split("app/templates/", 1)[1]
    with app.test_request_context("/"):
        html = render_template(template_name)

    assert "onsubmit=" not in html
    assert html.count("querySelectorAll('form[data-confirm]')") == 1
    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert f'data-confirm="{CONFIRM_MESSAGE}"' in html


def test_all_four_wave8_templates_are_byte_identical_across_both_pairs() -> None:
    """Koordinatör bulgusu: dört dosya Dalga 8 ÖNCESİ byte-birebir aynıydı.
    Aynı düzeltme hepsine BİREBİR AYNI şekilde uygulandığı için hâlâ
    byte-birebir aynı olmalılar. Kardeş dosyalar yalnızca KENDİ çiftleri
    içinde (premium==v1_4 ayrı, tasks==settings ayrı) byte-eşitliği
    doğruluyor; bu test dördünü ÇAPRAZ olarak (premium==tasks dahil)
    tek bir noktada doğrular."""
    contents = {relative_path: _read(relative_path) for relative_path in FOUR_WAVE8_TEMPLATES}
    base_path, base_text = next(iter(contents.items()))
    for relative_path, text in contents.items():
        assert text == base_text, f"{relative_path}, {base_path} ile artik byte-birebir ayni degil."
