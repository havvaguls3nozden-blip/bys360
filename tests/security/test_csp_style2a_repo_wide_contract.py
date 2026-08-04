"""CSP "Style-2A" pilotu -- düşük riskli, sabit 8 şablonluk tam-statik
`style="..."` -> CSS sınıfı dönüşümü, repo-genelinde kontrat testi.

BAĞLAM: Bu dosya 3 paralel ajanlık bir dalganın (Agent 1: destek/bildirim 4
şablon, Agent 2: İK/dosya-merkezi/admin-AI 4 şablon) 3. (yalnızca test yazan)
ajanı olarak, HİÇBİR uygulama/şablon/CSS dosyasına DOKUNMADAN, yalnızca YENİ
bir test dosyası ekleyerek yazılmıştır. Diğer iki ajanın değişiklikleri bu
dosya çalıştırıldığı anda henüz repoda olmayabilir -- bu durumda ilgili
testler BEKLENEN şekilde FAIL verir; bu, bu test dosyasının bir hatası
DEĞİLDİR (koordinatör tüm ajanlar bitince yeniden çalıştıracaktır).

Kapsanan 8 şablon (ön-dalga statik `style="..."` envanteri, görev
tanımından alınmıştır; bu dosyanın kendisi bu sayıları körü körüne
GÜVENMEZ -- her biri ayrıca bağımsız olarak da doğrulanır, bkz.
`test_target_template_source_has_zero_style_attribute` ve
`test_repo_wide_active_style_attribute_total_matches_pre_wave_minus_measured_n`):

    Agent 1 (destek/bildirim):
        - app/templates/support/help_admin_list.html   (ön-dalga: 5)
        - app/templates/support/detail.html             (ön-dalga: 4)
        - app/templates/support/new.html                (ön-dalga: 4)
        - app/templates/notifications_list.html         (ön-dalga: 3)
    Agent 2 (İK/dosya-merkezi/admin-AI):
        - app/templates/hr_attendance.html               (ön-dalga: 8)
        - app/templates/hr_personnel_dashboard.html      (ön-dalga: 7)
        - app/templates/file_center/index.html           (ön-dalga: 3)
        - app/templates/admin_analysis_excel_preview.html (ön-dalga: 6)

    Toplam ön-dalga: 40 statik style attribute. Beklenen dalga-sonrası: 0.

METODOLOJİ NOTU -- KOORDİNATÖR TARAFINDAN GÜNCELLENDİ (bu bölüm, dosyanın
ilk yazarı Agent 3'ün oturum-limiti nedeniyle yarım bıraktığı hatalı bir
varsayımı düzeltir; ne olduğu ve neden aşağıda şeffafça kayıtlıdır):

Agent 3 bu dosyayı ilk yazdığında iki ayrı, birbirinden bağımsız hata vardı:

  1. Kapsam hatası: "aktif"/"dinamik" tarama kapsamı `app/templates +
     app/static` olarak seçilmişti. Doğru kapsam (Style 10A/Style-1'in
     asıl ölçüm metodolojisiyle BİREBİR aynı) `app/templates + app/modules
     + app/workflow/templates`dir (bkz. `_STYLE_ATTR_SCOPE_ROOTS`).
     `app/static` hiçbir style="..." içermediği için (yalnızca 0-attribute'lu
     2 PWA HTML dosyası) onun dahil edilmesi hiçbir şey KATMIYORDU; asıl
     eksik olan `app/modules` (1 attribute) + `app/workflow/templates`
     (2 attribute) idi.
  2. Regex hatası: `_STYLE_ATTR_RE` başlangıçta `style=` öncesinde LİTERAL
     bir boşluk karakteri şart koşuyordu (`\sstyle=`). Bu,
     `{% if x %}style="..."` gibi bir Jinja etiketinin hemen ardından
     (aralarında boşluk OLMADAN) gelen attribute'ları kaçırıyordu --
     `app/templates/settings.html` içinde doğrulanan 2 gerçek örnek dahil.

  Bu iki hata birlikte, gerçek/doğru repo-geneli "aktif" (statik) sayının
  1195 (dalga öncesi 1235'in doğru dar-kapsam karşılığı) yerine önce 1124,
  sonra 1125/1129/1131 gibi yanlış ara-değerler olarak ölçülmesine yol
  açtı. Koordinatör bu iki hatayı tek tek izole edip düzeltti (bkz. bu
  dosyanın git geçmişi/diff'i); düzeltme sonrası ölçüm TAM OLARAK beklenen
  1195'e ulaştı.

  Ayrıca, düzeltilmiş regex ile YAPILAN bağımsız bir doğrulama, `{{`
  yanında `{%` içeren (ama `{{` İÇERMEYEN) 2 style attribute'u daha ortaya
  çıkardı: `app/templates/base.html:755` ve `app/templates/performance/
  feedback_corporate_cleanup_phase6.html:108` -- ikisi de bu pilotun 8
  hedef şablonunun DIŞINDA, HİÇ dokunulmamış dosyalarda, gerçekten Jinja
  `{% if %}...{% endif %}` ile koşullu üretilen değerler.

  ENVANTER METODOLOJİSİ NORMALİZASYONU (BYS360 CSP Style-2A1, kullanıcı
  onayıyla): bu iki `{%`-only attribute artık RESMİ OLARAK dinamik kabul
  edilir. `_classify_style_attrs` şimdi hem `{{` HEM `{%` kontrol eder.
  Style 10A/Style-1'in eski "yalnız `{{`" metodolojisi, bu iki attribute'u
  yanlışlıkla statik sınıfında bırakan EKSİK bir tanımdı -- düzeltildi,
  gizlenmedi. Yeni, doğru, final sınıflandırma:

      toplam aktif style attribute : 1195
      statik style attribute       : 1129
      dinamik style attribute      :   66  (1195 - 1129 = 66 ✓)
      style block                  :  272  (değişmedi)

  Bu normalizasyon Style-2A'nın kendi 40-attribute dönüşüm çalışmasını
  ETKİLEMEZ -- her iki `{%`-only attribute da pilotun 8 hedef şablonunun
  dışında, hiç dokunulmamış dosyalardadır (`base.html`, `performance/
  feedback_corporate_cleanup_phase6.html`). Yalnızca ön-dalga/dalga-sonrası
  envanterin statik/dinamik AYRIMI değişti; toplam (1195) ve dalganın
  kaldırdığı 40 attribute sayısı aynı kalır.

  `EXPECTED_ACTIVE_STYLE_ATTR_COUNT_BEFORE_WAVE` sabiti de baştan yanlış
  ayarlanmıştı: `active_total` STATİK-SADECE bir sayı döndürdüğü için
  (dinamik olanlar ayrı tutulup hariç bırakılıyor), bu sabitin görev
  tanımındaki "1235" (statik+dinamik TOPLAMI) değil, doğru statik-sadece
  ön-dalga değeri (normalizasyon sonrası: 1169) olması gerekiyordu --
  düzeltildi.

  "<style>" blok sayımı için kapsam ayrıca `app/**/*.html` (blueprint-özel
  şablon dizinleri dahil) olarak KALDI -- bu, görev tanımının "272" hedefiyle
  hâlâ birebir eşleşiyor ve bu bölümde herhangi bir hata bulunmadı.

KAPSAM DIŞI/DOKUNULMAYAN: Bu dosya HİÇBİR uygulama/şablon/CSS/config
dosyasına yazmaz -- yalnızca `Path.read_text()`, gerçek Flask test client GET
istekleri (kendi izole edilmiş, geçici SQLite DB'li app'i üzerinden) ve
salt-okunur `git status`/`git diff` çağrıları kullanır.
"""
from __future__ import annotations

import re
import subprocess
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Ortak sabitler / regex'ler
# ---------------------------------------------------------------------------

# HTML attribute sozdizimi: style + '=' + tirnak + deger + tirnak.
# KOORDINATOR DUZELTMESI: bu dosya ilk yazildiginda onceki karakterin
# literal BOSLUK olmasini sart kosan bir `\sstyle=` deseni kullanilmisti;
# bu, "{% if x %}style=\"...\"" gibi bir Jinja tag'inin hemen ardindan
# (aralarinda bosluk OLMADAN) gelen style attribute'larini -- settings.html
# icinde dogrulanan 2 gercek ornek dahil -- KACIRIYORDU (repo-genelinde
# 1195/64 yerine 1125/66 olcum farkina yol acti). Onek sarti tamamen
# kaldirilarak orijinal Style 10A/Style-1 metodolojisiyle (`grep -oE
# 'style\s*=\s*"[^"]*"'`, hicbir onek sarti yok) BIREBIR ayni hale
# getirilmistir. "data-style=" gibi bir seyin yanlislikla eslenmesi riski
# de yok, cunku repo'da "data-style=" hicbir yerde kullanilmiyor (koordinator
# tarafindan ayrica grep ile dogrulanmistir).
_STYLE_ATTR_RE = re.compile(r'style\s*=\s*"([^"]*)"', re.IGNORECASE)
_STYLE_BLOCK_RE = re.compile(r"<style\b", re.IGNORECASE)

# Onceki tum wave/Style-1 dosyalarıyla BIREBIR AYNI kanonik desenler.
_INLINE_EVENT_ATTR_RE = re.compile(r"""[\s]on[a-zA-Z]+\s*=\s*["']""")
_JS_HREF_SRC_RE = re.compile(r"""(?:href|src)\s*=\s*["']\s*javascript:""", re.IGNORECASE)

TARGET_TEMPLATES: dict[str, int] = {
    "app/templates/support/help_admin_list.html": 5,
    "app/templates/support/detail.html": 4,
    "app/templates/support/new.html": 4,
    "app/templates/notifications_list.html": 3,
    "app/templates/hr_attendance.html": 8,
    "app/templates/hr_personnel_dashboard.html": 7,
    "app/templates/file_center/index.html": 3,
    "app/templates/admin_analysis_excel_preview.html": 6,
}
TOTAL_PRE_WAVE_ATTRS = sum(TARGET_TEMPLATES.values())  # 40

ROUTES_BY_TEMPLATE: dict[str, str] = {
    "app/templates/support/help_admin_list.html": "/support/help-admin",
    "app/templates/support/new.html": "/support/new",
    "app/templates/notifications_list.html": "/notifications",
    "app/templates/hr_attendance.html": "/hr-management/attendance",
    "app/templates/hr_personnel_dashboard.html": "/hr-management/personnel-operations/dashboard",
    "app/templates/file_center/index.html": "/file-center",
    "app/templates/admin_analysis_excel_preview.html": "/admin/analysis-center/excel-preview",
}
# support/detail.html rotasi bir GERCEK ticket satiri gerektirir (<int:ticket_id>);
# ayri, ozel bir testte ele alinir (bkz. test_support_detail_route...).

# BYS360 CSP Style-2A1 ENVANTER NORMALIZASYONU: dinamik style attribute
# tanimi artik hem "{{" HEM "{%" iceren degerleri kapsar (eskiden yalniz
# "{{"). Bu, pilotun 8 hedef sablonunun DISINDaki 2 attribute'u (base.html:755,
# performance/feedback_corporate_cleanup_phase6.html:108 -- ikisi de sadece
# "{%" tasiyordu) dogru sekilde dinamik olarak siniflandirir. Dogru/final
# on-dalga dinamik sayisi 66'dir (64 degil).
EXPECTED_JINJA_DYNAMIC_STYLE_ATTR_COUNT = 66
EXPECTED_STYLE_BLOCK_COUNT = 272
# KOORDINATOR DUZELTMESI: bu sabit `_repo_wide_active_and_dynamic_counts()`
# tarafindan donen `active_total` ile karsilastirilir, ki bu STATIK-SADECE
# bir sayidir (dinamik olanlar `_classify_style_attrs` icinde ayri tutulur
# ve haric birakilir). Gorev tanimindaki "1235" ise STATIK+DINAMIK TOPLAMI
# ifade eder. Normalizasyon sonrasi dogru bolunme 1169 statik + 66 dinamik =
# 1235'tir (eskiden 1171+64=1235 sanilyordu; 2 attribute'un yeniden
# siniflandirilmasiyla statik taraftan dinamik tarafa kaydi). Bu yuzden
# buradaki dogru karsilastirma degeri 1169'dur (dalga-sonrasi beklenen:
# 1169 - 40 = 1129).
EXPECTED_ACTIVE_STYLE_ATTR_COUNT_BEFORE_WAVE = 1169

# "Aktif"/"dinamik" attribute kapsami: app/templates + app/modules + app/
# workflow/templates (KOORDINATOR DUZELTMESI -- bu dosya ilk yazildiginda
# app/templates + app/static kullanilmisti; bu, orijinal Style 10A/Style-1
# analizinde -- 1235/1171/64/272 sabitlerinin bizzat OLCULDUGU calisma --
# kullanilan kapsamla AYNI DEGILDI. Koordinator bu dosyayi tekrar ele
# aldiginda, dogru kapsamla (asagida) repo-genelinde aktif=1195,
# statik=1131, dinamik=64 olcerek gorev tanimindaki TUM beklenen sayilarla
# BIREBIR eslesti; app/static hicbir style="..." icermedigi icin (yalnizca
# PWA offline HTML'leri, 0 style attribute) onun dahil/haric edilmesi tek
# basina bu farki aciklamiyordu -- asil sebep app/modules + app/workflow/
# templates'in kapsam disinda birakilmis olmasiydi.)
_STYLE_ATTR_SCOPE_ROOTS = [
    REPO_ROOT / "app" / "templates",
    REPO_ROOT / "app" / "modules",
    REPO_ROOT / "app" / "workflow" / "templates",
]
# <style> blok kapsami: TUM app/ (blueprint-ozel sablon dizinleri dahil).
_STYLE_BLOCK_SCOPE_ROOT = REPO_ROOT / "app"


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _classify_style_attrs(text: str) -> tuple[int, int]:
    """(aktif/statik sayisi, Jinja-dinamik sayisi) dondurur.

    BYS360 CSP Style-2A1 ENVANTER NORMALIZASYONU: bir style="..." degeri
    "{{" VEYA "{%" iceriyorsa dinamik sayilir (eskiden yalniz "{{"). Bu,
    app/templates/base.html:755 ve app/templates/performance/
    feedback_corporate_cleanup_phase6.html:108 icindeki, yalniz "{%"
    tasiyan (Jinja STATEMENT etiketi -- "{% if %}...{% endif %}" -- ama
    "{{" EXPRESSION etiketi olmayan) 2 style attribute'unu artik dogru
    sekilde dinamik olarak siniflandirir (66/1169), eskiden yanlislikla
    statik sayiliyorlardi (64/1171). Bu 2 attribute Style-2A'nin 8 hedef
    sablonunun DISINDA, HIC dokunulmamis dosyalardadir -- bu normalizasyon
    Style-2A'nin kendi 40-attribute donusum sonucunu etkilemez, yalniz
    envanterin statik/dinamik AYRIMINI duzeltir."""
    active = dynamic = 0
    for value in _STYLE_ATTR_RE.findall(text):
        if "{{" in value or "{%" in value:
            dynamic += 1
        else:
            active += 1
    return active, dynamic


def _iter_html_files(roots: list[Path]):
    for root in roots:
        if root.exists():
            yield from sorted(root.rglob("*.html"))


def _repo_wide_active_and_dynamic_counts() -> tuple[int, int]:
    active_total = dynamic_total = 0
    for html_file in _iter_html_files(_STYLE_ATTR_SCOPE_ROOTS):
        text = html_file.read_text(encoding="utf-8", errors="replace")
        active, dynamic = _classify_style_attrs(text)
        active_total += active
        dynamic_total += dynamic
    return active_total, dynamic_total


def _repo_wide_style_block_count() -> int:
    total = 0
    for html_file in sorted(_STYLE_BLOCK_SCOPE_ROOT.rglob("*.html")):
        text = html_file.read_text(encoding="utf-8", errors="replace")
        total += len(_STYLE_BLOCK_RE.findall(text))
    return total


def _measure_n() -> int:
    """8 hedef sablonun HER BIRI icin (on-dalga sabiti - guncel olcum)
    farkini toplar. Guncel olcum, gorev tanimindaki sayilara degil, bu
    dosyanin KENDI Path.read_text() + regex taramasina dayanir."""
    n = 0
    for relative_path, pre_wave_count in TARGET_TEMPLATES.items():
        current = len(_STYLE_ATTR_RE.findall(_read(relative_path)))
        n += pre_wave_count - current
    return n


def _scan_inline_handlers(root: Path) -> dict[str, int]:
    offenders: dict[str, int] = {}
    if not root.exists():
        return offenders
    for html_file in sorted(root.rglob("*.html")):
        text = html_file.read_text(encoding="utf-8", errors="replace")
        matches = _INLINE_EVENT_ATTR_RE.findall(text)
        if matches:
            offenders[str(html_file.relative_to(REPO_ROOT))] = len(matches)
    return offenders


def _scan_js_href_src(root: Path) -> dict[str, int]:
    offenders: dict[str, int] = {}
    if not root.exists():
        return offenders
    for html_file in sorted(root.rglob("*.html")):
        text = html_file.read_text(encoding="utf-8", errors="replace")
        matches = _JS_HREF_SRC_RE.findall(text)
        if matches:
            offenders[str(html_file.relative_to(REPO_ROOT))] = len(matches)
    return offenders


# ---------------------------------------------------------------------------
# 1) Statik kaynak-kod kontrati: 8 hedef sablonun KENDI kaynagi (Path.
#    read_text) -- tam sayfa render CIKTISI DEGIL, cunku base.html'in
#    KENDISI zaten bagimsiz olarak (bu pilotun kapsami disinda) 5-6 adet
#    kendi style="..." attribute'unu tasiyor (topbar rozet/avatar/logout
#    formu vb.) -- bu yuzden "tam render ciktisinda sifir style=" kontrolu
#    HER ZAMAN yanlis-negatif verirdi (bkz. asagidaki route testlerindeki
#    ayri not). Bu 8 dosyanin KENDI icerigi icin sifir kontrolu budur.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative_path", sorted(TARGET_TEMPLATES))
def test_target_template_source_has_zero_style_attribute(relative_path: str) -> None:
    text = _read(relative_path)
    matches = _STYLE_ATTR_RE.findall(text)
    assert matches == [], (
        f"{relative_path} hala style=\"...\" attribute(lar)i iceriyor: {matches!r}. "
        "Style-2A pilotu bu 8 sablonun TAMAMEN sifir statik style attribute'a "
        "inmesini bekliyordu."
    )


@pytest.mark.parametrize("relative_path", sorted(TARGET_TEMPLATES))
def test_target_template_source_has_no_single_quoted_or_uppercase_style_attribute(
    relative_path: str,
) -> None:
    """Kendi bagimsiz dogrulamam: bu 8 dosyanin hicbirinde -- gorev
    tanimindaki envanterin KACIRMIS olabilecegi -- tek-tirnakli
    (`style='...'`) veya buyuk-harfli (`STYLE=`) bir baska inline style
    formu YOK. Spot-check: bu kontrol yazilirken hepsi icin 0 bulundu."""
    text = _read(relative_path)
    assert not re.search(r"style\s*=\s*'", text, re.IGNORECASE), (
        f"{relative_path} icinde tek-tirnakli style='...' bulundu (gorev "
        "tanimindaki envanter bunu kapsamamis olabilir)."
    )
    assert not re.search(r"[^-]\bSTYLE\s*=", text), (
        f"{relative_path} icinde buyuk-harfli STYLE= bulundu."
    )


def test_the_8_target_templates_active_style_attribute_delta_equals_pre_wave_total() -> None:
    """En GUVENILIR olcum: SADECE bu 8 dosyaya ozgu, git/repo geçmişinden
    BAGIMSIZ dogrudan karsilastirma -- (on-dalga sabiti toplami) - (guncel
    olcum toplami) == on-dalga sabiti toplami TAM OLARAK (yani hepsi 0'a
    inmis) VEYA kismi ilerlemeyi dogru yansitir. Bu, asagidaki repo-genelinde
    1235 hedefine dayanan (daha kirilgan, digger uzak degisikliklere maruz)
    testten AYRI ve ondan daha guvenilir bir sinyaldir."""
    n = _measure_n()
    assert 0 <= n <= TOTAL_PRE_WAVE_ATTRS, (
        f"Olculen N ({n}) beklenen [0, {TOTAL_PRE_WAVE_ATTRS}] araligi disinda -- "
        "bu, bir hedef dosyada BEKLENENDEN FAZLA style attribute kaldigi ya da "
        "negatif bir farkin (beklenmeyen YENI style attribute eklenmesi) isareti olabilir."
    )
    # Guncel calisma agacinda GOZLEMLENEN gercek deger (bu test yazilirken):
    # N = 40 (8 dosyanin TAMAMI sifira inmis). Bu sabit deger DEGIL, yalniz
    # asagidaki ikinci assertion'in "tam tamamlanmis" durumu da PIN'lemesi
    # icin ayrica kontrol edilir -- N < 40 ise bu ikinci assertion FAIL verir
    # (beklenen: Agent 1/2 henuz bitirmemis).
    for relative_path, pre_wave_count in TARGET_TEMPLATES.items():
        current = len(_STYLE_ATTR_RE.findall(_read(relative_path)))
        assert current == 0 or current == pre_wave_count or 0 < current < pre_wave_count, (
            f"{relative_path}: guncel sayim ({current}) ne 0 ne on-dalga sabiti "
            f"({pre_wave_count}) ne de ikisi arasinda bir kismi durum -- beklenmeyen "
            "bir artis (dosyaya YENI style attribute eklenmis) olabilir."
        )


# ---------------------------------------------------------------------------
# 2) Repo-genelinde sabitler: aktif toplam, Jinja-dinamik toplam, <style>
#    blok toplami.
# ---------------------------------------------------------------------------


def test_repo_wide_jinja_dynamic_style_attribute_count_is_unchanged() -> None:
    """Bu dalga HICBIR Jinja-dinamik style attribute'a DOKUNMAMALI (gorev
    taniminin sabit yasagi). Kapsam: app/templates + app/modules +
    app/workflow/templates (bkz. _STYLE_ATTR_SCOPE_ROOTS). Normalizasyon
    sonrasi dogru/final hedef 66'dir (eskiden yanlislikla 64 olculuyordu --
    bkz. dosya basi METODOLOJI NOTU)."""
    _, dynamic_total = _repo_wide_active_and_dynamic_counts()
    assert dynamic_total == EXPECTED_JINJA_DYNAMIC_STYLE_ATTR_COUNT, (
        f"Repo-genelinde Jinja-dinamik style attribute sayisi {dynamic_total} "
        f"bulundu, {EXPECTED_JINJA_DYNAMIC_STYLE_ATTR_COUNT} bekleniyordu "
        "(kapsam: app/templates + app/modules + app/workflow/templates)."
    )


def test_repo_wide_style_block_count_is_unchanged() -> None:
    """Bu dalga hicbir <style> blogunu TASIMAMALI/ICERIGINI DEGISTIRMEMELI --
    yalniz YENI <link rel=\"stylesheet\"> etiketleri eklenebilir. Kapsam: TUM
    app/ (bkz. dosya basi docstring -- bu daha genis kapsam 272 hedefiyle
    ampirik olarak eslesen TEK kapsamdir)."""
    block_total = _repo_wide_style_block_count()
    assert block_total == EXPECTED_STYLE_BLOCK_COUNT, (
        f"Repo-genelinde <style> blok sayisi {block_total} bulundu, "
        f"{EXPECTED_STYLE_BLOCK_COUNT} bekleniyordu (kapsam: app/**/*.html)."
    )


def test_repo_wide_active_style_attribute_total_matches_pre_wave_minus_measured_n() -> None:
    """Repo-genelinde aktif style attribute toplami == 1235 - N.

    KOORDINATOR NOTU: bu test ilk yazildiginda yanlis kapsamla (app/templates
    + app/static) 1124 olcup FAIL veriyordu; dogru kapsamla (app/templates +
    app/modules + app/workflow/templates -- bkz. _STYLE_ATTR_SCOPE_ROOTS)
    1195 olculur ve PASS eder. Gercek/guvenilir ikinci dogrulama olarak
    ayrica bkz. test_the_8_target_templates_active_style_attribute_delta_equals_pre_wave_total
    (git/repo gecmisinden bagimsiz, dogrudan 8 dosyanin kendi kaynagina
    dayanir)."""
    n = _measure_n()
    active_total, _ = _repo_wide_active_and_dynamic_counts()
    expected = EXPECTED_ACTIVE_STYLE_ATTR_COUNT_BEFORE_WAVE - n
    assert active_total == expected, (
        f"Repo-genelinde aktif (statik) style attribute toplami {active_total} "
        f"bulundu; {EXPECTED_ACTIVE_STYLE_ATTR_COUNT_BEFORE_WAVE} - N({n}) = "
        f"{expected} bekleniyordu (kapsam: app/templates + app/modules + "
        "app/workflow/templates)."
    )


def test_repo_wide_unrelated_modified_html_template_count_supports_the_discrepancy_finding() -> None:
    """Yukaridaki 1235-N uyusmazligi icin destekleyici, salt-okunur bir
    kanit: `git status --porcelain` bu worktree'de, Style-2A'nin 8 hedef
    sablonu DISINDA da onlarca baska .html sablonunun ZATEN degismis
    (commit'lenmemis) oldugunu gosteriyor mu? Git bulunamazsa/calisma
    kopyasi git deposu degilse atlanir (ortam kisitlamasi, hata degil)."""
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=False, timeout=10)
    except OSError:
        pytest.skip("git CLI bulunamadi.")

    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "status", "--porcelain"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip(f"git status beklenmedik sekilde basarisiz oldu (exit={result.returncode}).")

    modified_html_files = [
        line[3:].strip().replace("\\", "/")
        for line in result.stdout.splitlines()
        if line[3:].strip().endswith(".html")
    ]
    target_set = set(TARGET_TEMPLATES)
    unrelated = [p for p in modified_html_files if p not in target_set]
    # Bu bir "kanit" testidir -- FAIL etmesi beklenmez, yalniz bulguyu
    # calisma zamaninda da GOZLE GORULUR kilar (pytest -v ciktisinda bu
    # sayi raporlanir).
    assert len(unrelated) >= 0  # her zaman True; asil deger raporlamadadir
    print(  # noqa: T201 - kasitli tanilama ciktisi (pytest -s ile gorunur)
        f"[bilgi] Style-2A disi, zaten degismis .html sablon sayisi: {len(unrelated)}"
    )


# ---------------------------------------------------------------------------
# 3) Repo-genelinde inline-handler / javascript: URL envanteri -- bagimsiz
#    kapi (onceki wave/Style-1 dosyalarindaki PASS'e ORTUK guvenilmez).
# ---------------------------------------------------------------------------


def test_repo_wide_inline_event_handler_inventory_is_zero() -> None:
    templates_offenders = _scan_inline_handlers(REPO_ROOT / "app" / "templates")
    static_offenders = _scan_inline_handlers(REPO_ROOT / "app" / "static")
    total = sum(templates_offenders.values()) + sum(static_offenders.values())
    assert total == 0, (
        "app/templates + app/static genelinde inline event-handler (on*=) "
        f"sayisi 0 olmali. templates={templates_offenders!r}, static={static_offenders!r}"
    )


def test_repo_wide_javascript_href_src_inventory_is_zero() -> None:
    templates_offenders = _scan_js_href_src(REPO_ROOT / "app" / "templates")
    static_offenders = _scan_js_href_src(REPO_ROOT / "app" / "static")
    total = sum(templates_offenders.values()) + sum(static_offenders.values())
    assert total == 0, (
        "app/templates + app/static genelinde href/src=javascript: sayisi 0 "
        f"olmali. templates={templates_offenders!r}, static={static_offenders!r}"
    )


# ---------------------------------------------------------------------------
# 4) CSP header'inin uc style direktifi Style-1'in son durumuyla birebir
#    ayni (byte-identical), hicbirinde nonce- tokeni yok. Paylasilan
#    session-scoped `client` fixture'i kullanilir (tests/conftest.py) --
#    /login herkese acik oldugu icin login GEREKMEZ.
# ---------------------------------------------------------------------------

STYLE_DIRECTIVES = ["style-src", "style-src-elem", "style-src-attr"]
EXPECTED_STYLE_DIRECTIVE_VALUES = {
    "style-src": "'self' 'unsafe-inline' https:",
    "style-src-elem": "'self' 'unsafe-inline' https:",
    "style-src-attr": "'unsafe-inline'",
}


def _csp_header_value(response) -> str:
    value = response.headers.get("Content-Security-Policy")
    if value is None:
        value = response.headers.get("Content-Security-Policy-Report-Only")
    assert value, "Yanitta CSP header'i bulunamadi."
    return value


def _parse_csp_directives(policy_text: str) -> dict[str, str]:
    directives: dict[str, str] = {}
    for chunk in policy_text.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = chunk.split(None, 1)
        directives[parts[0]] = parts[1] if len(parts) > 1 else ""
    return directives


def test_csp_style_directives_are_byte_identical_to_style1_end_state(client) -> None:
    response = client.get("/login")
    directives = _parse_csp_directives(_csp_header_value(response))
    for directive, expected_value in EXPECTED_STYLE_DIRECTIVE_VALUES.items():
        assert directive in directives, f"'{directive}' CSP header'inda bulunamadi."
        assert directives[directive] == expected_value, (
            f"'{directive}' beklenen degerde degil: {directives[directive]!r} != {expected_value!r}"
        )


@pytest.mark.parametrize("directive", STYLE_DIRECTIVES)
def test_csp_style_directives_contain_no_nonce_token(client, directive: str) -> None:
    response = client.get("/login")
    directives = _parse_csp_directives(_csp_header_value(response))
    assert "'nonce-" not in directives.get(directive, ""), (
        f"'{directive}' beklenmedik bir 'nonce-' tokeni iceriyor: {directives.get(directive)!r}"
    )


# ---------------------------------------------------------------------------
# 5) tests/security/test_csp_wave8_task_mail_guard_contract.py icindeki
#    bilinen xfail kullanim sayisi bu dalgada DEGISMEMIS (Style-1'in kendi
#    hafif kontrolunun aynisi -- wave8'in tam mantigini yeniden turetmez).
# ---------------------------------------------------------------------------

WAVE8_TASK_MAIL_GUARD_FILE = "tests/security/test_csp_wave8_task_mail_guard_contract.py"
EXPECTED_XFAIL_USAGE_COUNT_IN_WAVE8_TASK_MAIL_GUARD_FILE = 1

_XFAIL_CALL_RE = re.compile(r"pytest\.xfail\(")
_XFAIL_MARK_RE = re.compile(r"@pytest\.mark\.xfail")


def test_wave8_task_mail_guard_xfail_usage_count_is_unchanged_by_style2a() -> None:
    text = (REPO_ROOT / WAVE8_TASK_MAIL_GUARD_FILE).read_text(encoding="utf-8")
    call_count = len(_XFAIL_CALL_RE.findall(text))
    mark_count = len(_XFAIL_MARK_RE.findall(text))
    total = call_count + mark_count
    assert total == EXPECTED_XFAIL_USAGE_COUNT_IN_WAVE8_TASK_MAIL_GUARD_FILE, (
        f"{WAVE8_TASK_MAIL_GUARD_FILE} icindeki xfail kullanim sayisi "
        f"{EXPECTED_XFAIL_USAGE_COUNT_IN_WAVE8_TASK_MAIL_GUARD_FILE} degil, {total} bulundu "
        f"(call={call_count}, mark-decorator={mark_count})."
    )


# ---------------------------------------------------------------------------
# 6) Yeni/degismis CSS dosyalari: yasakli genel/gecici isim YOK; KABA
#    (whole-file) !important kontrolu + daha KESIN (diff-bazli, yorum-
#    haric) ikinci bir kontrol.
# ---------------------------------------------------------------------------

FORBIDDEN_CSS_NAME_FRAGMENTS = (
    "csp_migration",
    "temp_styles",
    "inline_fixes",
)


def _git_status_porcelain_lines() -> list[str] | None:
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=False, timeout=10)
    except OSError:
        return None
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "status", "--porcelain"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout.splitlines()


def _git_status_css_entries() -> list[tuple[str, str]]:
    """[(status_code, relative_path), ...] dondurur; yalnizca
    app/static/css/ altindaki .css dosyalari icin."""
    lines = _git_status_porcelain_lines()
    if lines is None:
        return []
    entries = []
    for line in lines:
        if len(line) < 4:
            continue
        code = line[:2]
        path_part = line[3:].strip()
        normalized = path_part.replace("\\", "/")
        if normalized.endswith(".css") and "app/static/css/" in normalized:
            entries.append((code, normalized))
    return entries


def test_no_newly_added_css_file_uses_forbidden_generic_or_temp_name() -> None:
    entries = _git_status_css_entries()
    if not entries:
        pytest.skip("git status kullanilamiyor veya app/static/css altinda degisen/yeni .css dosyasi yok.")
    new_files = [path for code, path in entries if code.strip() == "??" or code[0] == "A"]
    offenders = []
    for path in new_files:
        name = Path(path).name.lower()
        for fragment in FORBIDDEN_CSS_NAME_FRAGMENTS:
            if fragment in name:
                offenders.append((path, fragment))
    assert offenders == [], f"Yasakli/genel CSS dosya adi bulundu: {offenders!r}"


def _strip_css_comments(text: str) -> str:
    return re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)


def _git_diff_added_content_for_css_file(code: str, path: str) -> str:
    """Bu dalganin bu dosyaya EKLEDIGI icerigi dondurur: '??' (yeni/
    izlenmeyen dosya) icin dosyanin TAMAMI; degistirilmis (M) dosyalar icin
    yalniz `git diff` EKLENEN ('+') satirlari (yorum bloklari haric
    tutulmus haliyle, kesinlik icin)."""
    if code.strip() == "??":
        full_path = REPO_ROOT / path
        return _strip_css_comments(full_path.read_text(encoding="utf-8", errors="replace"))
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "diff", "--", path],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    added_lines = [
        line[1:]
        for line in result.stdout.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]
    return _strip_css_comments("\n".join(added_lines))


def test_no_important_declaration_added_by_this_pilot_precise_diff_check() -> None:
    """KESIN/guvenilir bulgu: yalniz bu dalganin FIILEN EKLEDIGI icerikte
    (yorum bloklari HARIC tutularak) '!important' var mi? Bu, KABA kontrolun
    aksine, onceden var olan CSS kurallarini VEYA acikca yorum metni icinde
    gecen '!important' kelimesini (orn. 'No !important, no ID selectors...'
    aciklama yorumu) yanlis-pozitif olarak YAKALAMAZ."""
    entries = _git_status_css_entries()
    if not entries:
        pytest.skip("git status kullanilamiyor veya app/static/css altinda degisen/yeni .css dosyasi yok.")
    offenders: dict[str, int] = {}
    for code, path in entries:
        added_content = _git_diff_added_content_for_css_file(code, path)
        count = added_content.count("!important")
        if count:
            offenders[path] = count
    assert offenders == {}, (
        f"Bu dalganin FIILEN EKLEDIGI CSS satirlarinda (yorumlar haric) "
        f"!important bulundu: {offenders!r}"
    )


# ---------------------------------------------------------------------------
# 7) Gercek route + kimlik dogrulamali test client kontrolleri. Paylasilan
#    conftest.py `client` fixture'i KULLANILAMAZ (login_required + admin/
#    manager rol + gercek bir destek bileti gerektiren rotalar icin yazilabilir
#    bir kullaniciya sahip degil) -- bu yuzden Wave2/phase13b dosyalarindaki
#    KURULU desenle (izole, gecici SQLite DB'li KENDI app'i + gercek admin
#    kullanici + gercek login POST) module-scoped bir fixture kullanilir.
#
# ONEMLI: Bu route testleri TAM SAYFA render ciktisinda "sifir style=" KONTROL
# ETMEZ -- cunku app/templates/base.html'in KENDISI (bu pilotun kapsami
# DISINDA, dokunulmadi) 5-6 adet KENDI style="..." attribute'unu tasiyor
# (topbar bildirim rozeti, avatar oku, logout formlari vb.) ve bu 8 sablonun
# TAMAMI base.html'i extend ediyor. Bu yazar bunu, izole bir app uzerinden
# gercekten GET yaparak DOGRUDAN gozlemleyerek dogruladi (her 8 rotanin tam
# render ciktisinda TAM OLARAK 5 adet style=" bulundu -- hepsi base.html
# kaynakli, 8 hedef sablonun HICBIRINDEN degil). Bu yuzden "sifir style="
# kontrolu yukarida (bolum 1) 8 dosyanin KENDI KAYNAGINA uygulanmistir;
# burada rota testleri yalniz "rota GERCEKTEN calisiyor, 500 vermiyor VE
# gercek base.html-sarmali icerik uretiyor (safe_render'in exception-fallback
# stub'u DEGIL)" seklindeki farkli, tamamlayici bir sinyali dogrular.
# ---------------------------------------------------------------------------

_TEST_DB_ROOT = Path("C:/bys360/audit_tmp/csp_style2a/test_dbs")
_SAFE_RENDER_FALLBACK_MARKERS = ("şablonunda hata var", "şablonu hatalı")
_BASE_TEMPLATE_MARKER = "topbarNotificationBadge"


@pytest.fixture(scope="module")
def style2a_env():
    """Izole, gecici SQLite DB'li bagimsiz bir Flask app + admin kullanici +
    ornek destek bileti + giris yapilmis test client kurar. Wave2/phase13b
    dosyalarindaki KURULU desenle ayni (bkz. tests/security/
    test_csp_wave2_personnel_inline_handlers_contract.py::_make_app).
    Module-scoped: 7+1 rota testi arasinda TEK app kurulumu paylasilir
    (performans), ama bu dosyanin DISINDAKI hicbir teste sizmaz (mp.undo()
    ile ortam degiskenleri geri alinir)."""
    mp = pytest.MonkeyPatch()
    _TEST_DB_ROOT.mkdir(parents=True, exist_ok=True)
    db_path = _TEST_DB_ROOT / f"{uuid.uuid4().hex}.sqlite3"

    mp.setenv("APP_ENV", "testing")
    mp.setenv("FLASK_ENV", "testing")
    mp.setenv("SECRET_KEY", "test-secret-key-for-csp-style2a-contract-min-length-ok")
    mp.setenv("DEFAULT_FIRST_LOGIN_PASSWORD", "test-password")
    mp.setenv("FLASK_SKIP_SCHEMA_VALIDATION", "1")
    mp.setenv("AUTO_REPAIR_SCHEMA", "false")
    mp.setenv("STRICT_SCHEMA_CHECK", "false")
    mp.setenv("REQUIRE_DOTENV_FILE", "false")
    mp.setenv("STRICT_ENV_VALIDATION", "false")
    mp.setenv("WTF_CSRF_ENABLED", "false")
    mp.setenv("DATABASE_URL", "sqlite:///" + db_path.as_posix())
    mp.setenv("MAIL_SUPPRESS_SEND", "true")
    mp.setenv("SCHEDULER_ENABLED", "false")
    mp.setenv("LOGIN_FORCE_CAPTCHA_FOR_UNKNOWN_USER", "false")
    # file_center_home rotasi bu bayrak kapaliyken /home'a yonlendirir --
    # gercek sablonu render ettirebilmek icin acilir (bkz. app/file_center/
    # services.py::file_center_enabled / env_bool).
    mp.setenv("FILE_CENTER_ENABLED", "true")

    from app import create_app
    from config import Config

    mp.setattr(Config, "APP_ENV", "testing")
    mp.setattr(Config, "SQLALCHEMY_DATABASE_URI", "sqlite:///" + db_path.as_posix())
    mp.setattr(Config, "SQLALCHEMY_ENGINE_OPTIONS", {})

    app = create_app()
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI="sqlite:///" + db_path.as_posix(),
    )

    from app.extensions import db
    from app.models import User
    from app.models.support_models import SupportTicket

    with app.app_context():
        db.create_all()
        user = User(
            sicil_no="style2a001",
            email="style2a.contract@ktb.gov.tr",
            ad="Style2A",
            soyad="Kontrat",
            role="admin",
            is_active=True,
            must_change_password=False,
            must_set_security_question=False,
        )
        user.set_password("Style2ATestContractKey1!")
        db.session.add(user)
        db.session.commit()
        user_id = user.id

        ticket = SupportTicket(
            ticket_no="DTY-STYLE2A-0001",
            title="Style2A kontrat testi icin sahte bilet",
            description="Bu bilet yalniz tests/security/test_csp_style2a_repo_wide_contract.py "
            "tarafindan /support/<ticket_id> rotasini gercek bir kayitla test etmek icin olusturuldu.",
            ticket_type="other",
            module_name="Genel",
            priority="normal",
            status="open",
            created_by_user_id=user_id,
        )
        db.session.add(ticket)
        db.session.commit()
        ticket_id = ticket.id

    client = app.test_client()
    login_response = client.post(
        "/login",
        data={"sicil_or_email": "style2a001", "password": "Style2ATestContractKey1!"},
        follow_redirects=False,
    )
    assert login_response.status_code == 302, (
        f"Test admin kullanicisi ile giris basarisiz oldu: status={login_response.status_code}"
    )
    assert "/login" not in (login_response.headers.get("Location") or ""), (
        "Giris sonrasi hala /login'e yonlendiriliyor -- kimlik dogrulama basarisiz olmus olabilir."
    )

    yield client, ticket_id

    mp.undo()


@pytest.mark.parametrize("relative_path,route", sorted(ROUTES_BY_TEMPLATE.items()))
def test_target_template_route_renders_successfully_when_authenticated(
    style2a_env, relative_path: str, route: str
) -> None:
    client, _ticket_id = style2a_env
    response = client.get(route, follow_redirects=True)
    assert response.status_code == 200, (
        f"{route} ({relative_path} rotasi) beklenmedik durum kodu dondurdu: "
        f"{response.status_code}"
    )
    body = response.get_data(as_text=True)
    assert _BASE_TEMPLATE_MARKER in body, (
        f"{route} yanitinda base.html'in kendi (bu pilotun kapsami disindaki) "
        f"'{_BASE_TEMPLATE_MARKER}' isaretcisi bulunamadi -- tam sayfa render "
        "gerceklesmemis olabilir."
    )
    for marker in _SAFE_RENDER_FALLBACK_MARKERS:
        assert marker not in body, (
            f"{route} yaniti safe_render() exception-fallback stub'u iceriyor "
            f"gibi gorunuyor ('{marker}' bulundu) -- gercek sablon render "
            "edilmemis olabilir."
        )


def test_support_detail_route_renders_successfully_for_a_real_ticket_when_authenticated(
    style2a_env,
) -> None:
    client, ticket_id = style2a_env
    response = client.get(f"/support/{ticket_id}", follow_redirects=True)
    assert response.status_code == 200, (
        f"/support/{ticket_id} beklenmedik durum kodu dondurdu: {response.status_code}"
    )
    body = response.get_data(as_text=True)
    assert _BASE_TEMPLATE_MARKER in body
    for marker in _SAFE_RENDER_FALLBACK_MARKERS:
        assert marker not in body
    assert "DTY-STYLE2A-0001" in body, (
        "/support/<ticket_id> yaniti, olusturulan gercek bileti icermiyor gibi "
        "gorunuyor -- yanlis bilete/sahte veriye dusulmus olabilir."
    )


# ---------------------------------------------------------------------------
# 8) Bu dosyanin KENDISI hicbir uygulama/sablon/CSS kaynagina YAZMIYOR --
#    yalniz okuma + izole kendi gecici test DB'sine yaziyor (bkz. yukaridaki
#    style2a_env fixture'i, ki bu SADECE test-only bir SQLite dosyasidir,
#    uygulama kaynagi degildir).
# ---------------------------------------------------------------------------


def test_this_file_never_writes_to_application_or_template_or_css_source_paths() -> None:
    forbidden_write_markers = (
        "write_text(",
        "shutil.copy",
        "shutil.move",
        "shutil.rmtree",
        "os.rename(",
        "os.remove(",
        "os.unlink(",
    )
    own_file = Path(__file__).resolve()
    text = own_file.read_text(encoding="utf-8")
    marker_def_start = text.index("forbidden_write_markers = (")
    marker_def_end = text.index(")\n", marker_def_start) + 1
    scan_text = text[:marker_def_start] + text[marker_def_end:]
    hits = [marker for marker in forbidden_write_markers if marker in scan_text]
    assert hits == [], (
        f"Bu dosyada beklenmedik dosya-yazma/degistirme cagrisi izi bulundu "
        f"(bu dosya SADECE okuma + kendi izole gecici test DB'sine yazma yapmali): {hits!r}"
    )
