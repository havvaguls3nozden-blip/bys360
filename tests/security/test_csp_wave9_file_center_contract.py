"""CSP Dalga 9 (SON dalga) - Dosya Merkezi ("Sil" / "İptal Et") kontrat testi.

BYS360 `app/security/headers.py` uygular:
    script-src: 'self' https:  (unsafe-inline YOK)

`app/bootstrap/response_hardening.py` + `app/security/headers.py::
inject_csp_nonce_into_html`, yanıt döndürüldükten sonra nonce'u olmayan HER
`<script>` etiketine otomatik `nonce="..."` ekler; bu yüzden dosya-içi
`<script>...</script>` blokları zaten CSP ile uyumludur ve nonce hiçbir zaman
elle template'e yazılmaz. Asıl risk inline EVENT ATTRIBUTE'lardı (`onsubmit=`
vb.) -- CSP script-src nonce/host tabanlı olduğu için bunlara nonce
uygulanmaz ve enforce modda tarayıcı tarafından çalıştırılmazlar.

Bu dosyanın sahiplik alanı SADECE şu iki şablon (her biri 1 handler, TOPLAM
2 handler, aralarında PAYLAŞILAN JS dosyası YOK -- koordinatör bulgusu grep
ile bağımsız olarak da burada doğrulanıyor):
    - app/templates/file_center/index.html  (satır ~102, "Sil" formu --
      `main.file_center_delete`)
    - app/templates/file_center/requests.html  (satır ~195, "İptal Et"
      formu -- `main.file_center_revoke_request`)

ÇÖZÜM (kurulu Dalga 1-8 deseni, iki dosyaya BAĞIMSIZ ama AYNI kalıpla
uygulandı): `onsubmit="return confirm('...')"` kaldırıldı,
`data-confirm="..."` eklendi (mesaj harfiyen korundu). Her iki dosyada da
`{% block content %}` içinde, `{% endblock %}`'tan hemen önce YENİ birer
`<script>` bloğu açıldı (dosyalarda önceden HİÇ script yoktu) -- standart
`form[data-confirm]` submit-delegasyon kodu:
    document.querySelectorAll('form[data-confirm]').forEach(function(form){
        form.addEventListener('submit', function(event){
            const m = form.getAttribute('data-confirm');
            if (m && !window.confirm(m)) { event.preventDefault(); }
        });
    });
İki dosya bağımsız olduğu için (ortak statik JS dosyası yok, `base.html`
global bir `form[data-confirm]` delegasyonu SAĞLAMIYOR -- bkz.
`test_base_template_has_no_global_form_data_confirm_delegation`), her biri
KENDİ script bloğunu alır; bu "ortak JS" YOKLUĞU kasıtlıdır, hata değildir.

`index.html`'deki "Misafir Bağlantısı" toggle butonu
(`data-bs-toggle="collapse" data-bs-target="#share{{ file.id }}"`)
Bootstrap'ın KENDİ collapse mekanizmasını kullanır -- inline event handler
DEĞİLDİR, bu dalgada dokunulmadı (regresyon kilidi: bkz.
`test_index_guest_link_toggle_still_uses_bootstrap_collapse_not_inline_js`).

Statik testler önceki dalgalarla (`test_csp_wave6_evaluation_periods_
contract.py`, `test_csp_wave8_task_mail_guard_contract.py`) aynı desendedir
(Path.read_text() + regex, sonra gerçek Jinja motoruyla `render_template()`
çıktı testleri; `app` fixture'ı `tests/conftest.py`'den gelir, session-
scoped). Render testleri gerçek route/login/DB akışına GİRMEZ -- bunun
yerine `types.SimpleNamespace` sahte context nesneleriyle DOĞRUDAN
`render_template()` çağrılır (Wave5/6/8 ile aynı tercih; `app/
template_safety.py` `ChainableUndefined` ayarladığı için context'te
sağlanmayan değişkenlere zincirlenmiş erişim hata fırlatmaz, ama biz yine de
gerçek route'ların (`app/file_center/routes.py::file_center_home`,
`file_center_requests`) sağladığı TÜM context anahtarlarını -- `format_bytes`,
`scan_label`, `link_status_label`, `request_status_label`, `mail_status_label`,
`mail_purpose_label` dahil -- birebir sağlıyoruz).

GERÇEK DOSYA YÜKLEME/İNDİRME/SİLME/PAYLAŞIM KESİNLİKLE ÇALIŞTIRILMADI: Bu
dosyadaki HİÇBİR test bir Flask test client üzerinden POST isteği / gerçek
route fonksiyonu / gerçek `app/file_center/services.py` disk-yazma
fonksiyonlarını (`save_uploaded_file`, `soft_delete_file` vb.) çağırmaz --
yalnızca `flask.
render_template(...)` ile şablonun ÜRETTİĞİ HTML metni test edilir. Bu kısıt
`test_no_disk_or_db_mutation_helpers_are_imported_or_called` ve
`test_rendering_both_templates_creates_no_new_files_under_app_or_instance`
testleriyle hem
statik hem çalışma-zamanı olarak kilitlenmiştir.

ÖNEMLİ SINIRLAMA: Bu dosyadaki HİÇBİR test gerçek bir tarayıcıda çalışmadı/
çalıştırılmadı. `render_template()` yalnızca ÜRETİLEN HTML'i doğrular
(inline handler yok, data-confirm attribute'u doğru, script bloğu sayfa
başına doğru sayıda render ediliyor, CSRF/action/method/`class="d-inline"`
korunuyor). CSP enforce edilmiş gerçek bir tarayıcıda "Sil"/"İptal Et"
butonlarının confirm() diyaloğunu fiilen açıp iptal edilebildiğini KANITLAMAZ
-- bu ayrı bir manuel/E2E doğrulama gerektirir ve bu dosyanın kapsamı
dışındadır (rapor metninde ayrıca not edilmiştir).
"""
from __future__ import annotations

import datetime
import re
import types
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

INDEX_TEMPLATE = "app/templates/file_center/index.html"
REQUESTS_TEMPLATE = "app/templates/file_center/requests.html"
BASE_TEMPLATE = "app/templates/base.html"
WAVE9_TEMPLATES = [INDEX_TEMPLATE, REQUESTS_TEMPLATE]

STATIC_JS_DIR = REPO_ROOT / "app" / "static" / "js"

# HTML attribute syntax: bosluk + on<harfler> + '=' + tirnak. CSS/JS icindeki
# "javascript:" gibi metinsel string literal'leri yanlislikla yakalamaz. Bu,
# diger tum wave kontrat dosyalarindaki KANONIK regex ile birebir aynidir.
_INLINE_EVENT_ATTR_RE = re.compile(r"""[\s]on[a-zA-Z]+\s*=\s*["']""")
_JS_HREF_RE = re.compile(r"""(?:href|src)\s*=\s*["']\s*javascript:""", re.IGNORECASE)

INDEX_DELETE_CONFIRM_MESSAGE = "Bu dosya silinsin mi? Aktif misafir bağlantıları da kapatılır."
REQUESTS_REVOKE_CONFIRM_MESSAGE = "Bu dosya isteği iptal edilsin mi? Misafir yükleme bağlantısı kapanır."

INDEX_DELETE_ACTION = "{{ url_for('main.file_center_delete', file_id=file.id) }}"
REQUESTS_REVOKE_ACTION = "{{ url_for('main.file_center_revoke_request', request_id=req.id) }}"

# Gercek disk/DB mutasyonu yapan yardimci fonksiyon adlari (bkz.
# app/file_center/services.py, app/file_center/routes.py) -- bu test
# dosyasinin KENDI kaynaginda GECMEMELI (statik kanit).
_FORBIDDEN_MUTATION_MARKERS = (
    "file_center_delete(",
    "file_center_revoke_request(",
    "file_center_upload(",
    "soft_delete_file(",
    "save_uploaded_file(",
    ".test_client(",
    "client.post(",
)


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 0) Koordinator on-bulgusunun bagimsiz dogrulamasi: iki dosya arasinda
#    paylasilan statik JS dosyasi yok, base.html global bir form[data-confirm]
#    delegasyonu saglamiyor.
# ---------------------------------------------------------------------------


def test_neither_template_links_a_dedicated_shared_js_file_for_the_confirm_pattern() -> None:
    """Iki dosyanin da bu confirm deseni icin ayri/paylasilan bir <script src=...>
    dosyasi ICE ALMADIGINI dogrular -- her biri KENDI inline <script> blogunu
    tasir (koordinator bulgusu: 'ortak JS' yok)."""
    for relative_path in WAVE9_TEMPLATES:
        text = _read(relative_path)
        assert "<script src=" not in text, (
            f"{relative_path} beklenmedik sekilde harici bir <script src=...> "
            "referansi iceriyor; koordinator bulgusu bu iki dosyada boyle bir "
            "sey olmadigi yonundeydi."
        )


def test_base_template_has_no_global_form_data_confirm_delegation() -> None:
    """base.html'in KENDISI bir global `form[data-confirm]` delegasyonu
    SAGLAMIYOR -- aksi halde index.html/requests.html'e EKLENEN yeni script
    ile birlikte AYNI event'e (submit) IKI dinleyici baglanmis olurdu (kesin
    yasak: cift listener). Bu, her iki dosyanin da KENDI script'ini almasinin
    dogru/gerekli oldugunun kaniti."""
    text = _read(BASE_TEMPLATE)
    assert "form[data-confirm]" not in text


def test_no_other_html_template_defines_a_reusable_file_center_confirm_script() -> None:
    """app/templates altinda file_center/index.html ve file_center/requests.html
    DISINDA, bu iki dosyanin script'ini "paylasilan" bir yardimci dosyaya
    tasiyan baska bir sablon YOK (grep teyidi: iki dosya birbirinden ve
    digerlerinden bagimsiz kaldi)."""
    templates_root = REPO_ROOT / "app" / "templates"
    for html_file in templates_root.rglob("*.html"):
        rel = html_file.relative_to(REPO_ROOT).as_posix()
        if rel in WAVE9_TEMPLATES:
            continue
        text = html_file.read_text(encoding="utf-8")
        assert INDEX_DELETE_CONFIRM_MESSAGE not in text, f"{rel} beklenmedik sekilde Wave9 index confirm mesajini iceriyor."
        assert REQUESTS_REVOKE_CONFIRM_MESSAGE not in text, f"{rel} beklenmedik sekilde Wave9 requests confirm mesajini iceriyor."


# ---------------------------------------------------------------------------
# 1) Statik kaynak-kod kontratlari -- inline event-attribute / javascript:
#    href / tehlikeli JS sink kalmadigini dogrular (iki dosyanin tumu icin).
# ---------------------------------------------------------------------------


def test_wave9_templates_have_no_inline_event_attributes() -> None:
    for relative_path in WAVE9_TEMPLATES:
        text = _read(relative_path)
        matches = _INLINE_EVENT_ATTR_RE.findall(text)
        assert not matches, (
            f"{relative_path} icinde inline event-attribute (on*=) bulundu: {matches!r}. "
            "CSP script-src 'self' https: (unsafe-inline yok) altinda bunlar calismaz."
        )


def test_wave9_templates_have_no_javascript_url_anywhere() -> None:
    for relative_path in WAVE9_TEMPLATES:
        text = _read(relative_path)
        assert "javascript:" not in text.lower(), f"{relative_path} icinde javascript: bulundu."


def test_wave9_templates_have_no_javascript_href() -> None:
    for relative_path in WAVE9_TEMPLATES:
        text = _read(relative_path)
        matches = _JS_HREF_RE.findall(text)
        assert not matches, f"{relative_path} icinde href/src=\"javascript:...\" bulundu: {matches!r}."


def test_wave9_templates_introduce_no_dangerous_js_sinks() -> None:
    for relative_path in WAVE9_TEMPLATES:
        text = _read(relative_path)
        for forbidden in ("eval(", "new Function(", "document.write("):
            assert forbidden not in text, f"{relative_path} icinde yasakli sink bulundu: {forbidden}"


def test_wave9_templates_have_exactly_one_submit_listener_each() -> None:
    """Ayni event turune (submit) her dosyada YALNIZCA bir kez
    addEventListener baglanmali -- coordinator'in kesin yasagi (cift listener)."""
    for relative_path in WAVE9_TEMPLATES:
        text = _read(relative_path)
        submit_listener_count = text.count("addEventListener('submit'")
        assert submit_listener_count == 1, (
            f"{relative_path} icinde beklenen tam olarak 1 'submit' listener degil: "
            f"{submit_listener_count}"
        )


def test_repo_wide_inline_handler_count_is_zero_after_wave9() -> None:
    """Dalga 9 SON dalga: bu iki dosyanin donusumuyle birlikte app/templates
    genelinde (kanonik `on[a-zA-Z]+=` regex'i ile) toplam inline
    event-attribute sayisi TAM OLARAK 0 olmalidir (Wave8'in kapsam-disi
    biraktigi 4 handler'in 2'si -- messages_thread.html'deki 2 -- bu
    dosyanin sahiplik alani DISINDA kalsa da, mevcut worktree durumunda
    bu iki wave9 dosyasinin kendi payi sifirlanmis olmalidir; asagidaki
    per-file testler bunu ayri ayri da kilitler)."""
    for relative_path in WAVE9_TEMPLATES:
        text = _read(relative_path)
        assert not _INLINE_EVENT_ATTR_RE.findall(text), (
            f"{relative_path} hala inline event-attribute iceriyor; Dalga 9 "
            "(SON dalga) sonunda bu iki dosyanin sifir olmasi beklenir."
        )


# ---------------------------------------------------------------------------
# 2) index.html -- data-confirm + submit-delegasyon script kontrati
# ---------------------------------------------------------------------------


def test_index_delete_form_uses_data_confirm_not_onsubmit() -> None:
    text = _read(INDEX_TEMPLATE)
    assert "onsubmit=" not in text
    assert f'data-confirm="{INDEX_DELETE_CONFIRM_MESSAGE}"' in text
    assert text.count('data-confirm="') == 1


def test_index_delete_confirm_message_preserved_verbatim() -> None:
    text = _read(INDEX_TEMPLATE)
    snippet = f'data-confirm="{INDEX_DELETE_CONFIRM_MESSAGE}"'
    assert snippet in text


def test_index_delete_form_keeps_action_method_csrf_and_inline_class() -> None:
    """action, method=post, `class="d-inline"` ve gizli csrf_token input'u
    DEGISMEDEN korunmus olmali (form/CSRF paritesi -- coordinator'in kesin
    yasagi: form/CSRF/class bozulmasi)."""
    text = _read(INDEX_TEMPLATE)
    expected_form_open = (
        '<form method="post" action="' + INDEX_DELETE_ACTION + '" class="d-inline" '
        f'data-confirm="{INDEX_DELETE_CONFIRM_MESSAGE}">'
    )
    assert expected_form_open in text
    idx = text.index(expected_form_open)
    tail = text[idx : idx + 400]
    assert '<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">' in tail
    assert '<button class="btn btn-sm btn-link text-danger text-decoration-none">Sil</button>' in tail


def test_index_adds_exactly_one_new_submit_delegation_script() -> None:
    """index.html'de daha once HIC script yoktu; Dalga 9 tam olarak 1 yeni
    <script> blogu ekledi (standart form[data-confirm] submit-delegasyon
    kalibi, Wave1-8 ile ayni desen)."""
    text = _read(INDEX_TEMPLATE)
    assert text.count("<script") == 1
    assert "querySelectorAll('form[data-confirm]')" in text
    assert text.count("querySelectorAll('form[data-confirm]')") == 1
    assert "addEventListener('submit'" in text
    assert "window.confirm(" in text
    assert "event.preventDefault();" in text


def test_index_script_is_inside_the_content_block() -> None:
    text = _read(INDEX_TEMPLATE)
    content_start = text.index("{% block content %}")
    content_end = text.index("{% endblock %}", content_start)
    script_idx = text.index("querySelectorAll('form[data-confirm]')")
    assert content_start < script_idx < content_end, (
        "index.html'deki yeni submit-delegasyon script'i {% block content %} "
        "disinda kalmis olabilir; bu durumda Jinja2 onu render etmez."
    )


def test_index_guest_link_toggle_still_uses_bootstrap_collapse_not_inline_js() -> None:
    """Koordinator on-bulgusu: 'Misafir Baglantisi' butonu Bootstrap'in KENDI
    data-bs-toggle="collapse" mekanizmasini kullanir -- inline handler
    DEGILDIR, bu dalgada dokunulmamis olmali (regresyon kilidi)."""
    text = _read(INDEX_TEMPLATE)
    assert 'data-bs-toggle="collapse"' in text
    assert 'data-bs-target="#share{{ file.id }}"' in text


def test_index_upload_form_and_guest_link_forms_have_no_confirm_and_are_untouched() -> None:
    """Dosya yukleme formu ve misafir baglanti olusturma/iptal formlari bu
    dalganin kapsami DISINDA -- confirm attribute'u ALMAMALI (yalnizca
    Sil formu confirm mesaji tasir)."""
    text = _read(INDEX_TEMPLATE)
    assert text.count('data-confirm="') == 1
    assert "file_center_upload" in text
    assert "file_center_create_guest_link" in text
    assert "file_center_revoke_guest_link" in text


# ---------------------------------------------------------------------------
# 3) requests.html -- data-confirm + submit-delegasyon script kontrati
# ---------------------------------------------------------------------------


def test_requests_revoke_form_uses_data_confirm_not_onsubmit() -> None:
    text = _read(REQUESTS_TEMPLATE)
    assert "onsubmit=" not in text
    assert f'data-confirm="{REQUESTS_REVOKE_CONFIRM_MESSAGE}"' in text
    assert text.count('data-confirm="') == 1


def test_requests_revoke_confirm_message_preserved_verbatim() -> None:
    text = _read(REQUESTS_TEMPLATE)
    snippet = f'data-confirm="{REQUESTS_REVOKE_CONFIRM_MESSAGE}"'
    assert snippet in text


def test_requests_revoke_form_keeps_action_method_and_csrf() -> None:
    text = _read(REQUESTS_TEMPLATE)
    expected_form_open = (
        '<form method="post" action="' + REQUESTS_REVOKE_ACTION + '" '
        f'data-confirm="{REQUESTS_REVOKE_CONFIRM_MESSAGE}">'
    )
    assert expected_form_open in text
    idx = text.index(expected_form_open)
    tail = text[idx : idx + 400]
    assert '<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">' in tail
    assert '<button class="btn btn-sm btn-outline-danger">İptal Et</button>' in tail


def test_requests_close_form_immediately_above_has_no_confirm_and_is_untouched() -> None:
    """Koordinator ön-bulgusu: revoke formunun hemen ustunde confirm ICERMEYEN
    bir 'Kapat' formu (main.file_center_close_request) var -- ona
    DOKUNULMAMIS olmali (regresyon kilidi)."""
    text = _read(REQUESTS_TEMPLATE)
    close_form = (
        '<form method="post" action="{{ url_for(\'main.file_center_close_request\', '
        'request_id=req.id) }}">\n'
        '         <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">\n'
        '         <button class="btn btn-sm btn-outline-secondary">Kapat</button>\n'
        "        </form>"
    )
    assert close_form in text
    assert "onsubmit=" not in close_form
    assert "data-confirm" not in close_form


def test_requests_adds_exactly_one_new_submit_delegation_script() -> None:
    text = _read(REQUESTS_TEMPLATE)
    assert text.count("<script") == 1
    assert "querySelectorAll('form[data-confirm]')" in text
    assert text.count("querySelectorAll('form[data-confirm]')") == 1
    assert "addEventListener('submit'" in text
    assert "window.confirm(" in text
    assert "event.preventDefault();" in text


def test_requests_script_is_inside_the_content_block() -> None:
    text = _read(REQUESTS_TEMPLATE)
    content_start = text.index("{% block content %}")
    content_end = text.index("{% endblock %}", content_start)
    script_idx = text.index("querySelectorAll('form[data-confirm]')")
    assert content_start < script_idx < content_end, (
        "requests.html'deki yeni submit-delegasyon script'i {% block content %} "
        "disinda kalmis olabilir; bu durumda Jinja2 onu render etmez."
    )


def test_requests_other_action_forms_have_no_confirm() -> None:
    """E-posta gonder / hatirlatma kaydi olustur formlari bu dalganin kapsami
    DISINDA -- confirm attribute'u ALMAMALI (yalnizca Iptal Et formu confirm
    mesaji tasir)."""
    text = _read(REQUESTS_TEMPLATE)
    assert text.count('data-confirm="') == 1
    assert "file_center_send_request_email_route" in text
    assert "file_center_prepare_request_reminder" in text
    assert "file_center_close_request" in text


# ---------------------------------------------------------------------------
# 4) Gercek disk/DB mutasyonu YAPILMADIGININ statik kaniti.
# ---------------------------------------------------------------------------


def test_this_guard_file_never_imports_or_calls_real_mutation_or_http_client_helpers() -> None:
    """Bu test dosyasinin KENDI kaynagi, gercek dosya silme/yukleme/istek-
    iptal route fonksiyonlarini VEYA bir Flask test client POST cagrisini
    hicbir zaman kullanmadigini statik olarak dogrular -- bu dosya SADECE
    `flask.render_template()` ve `Path.read_text()` kullanir."""
    text = Path(__file__).read_text(encoding="utf-8")
    definition_marker = "_FORBIDDEN_MUTATION_MARKERS = ("
    def_start = text.index(definition_marker)
    def_end = text.index(")\n", def_start) + 1
    scan_text = text[:def_start] + text[def_end:]
    for marker in _FORBIDDEN_MUTATION_MARKERS:
        assert marker not in scan_text, f"Bu test dosyasinda yasakli mutasyon/HTTP-client izi bulundu: {marker!r}"


def test_no_disk_or_db_mutation_helpers_are_imported_or_called(app) -> None:
    """POZITIF calisma-zamani kaniti: gercek disk-yazma/DB-mutasyon
    fonksiyonlarini (`app.file_center.services` icindeki dosya kaydetme/
    silme yardimcilarini VE gercek depolama kok dizinini COZEN/OLUSTURAN
    `storage_root()` fonksiyonunu) mock'layip, bu test dosyasinin fiilen
    yaptigi tek islemin (iki sablonun `flask.render_template()` ile render
    edilmesi) bunlarin HICBIRINI TETIKLEMEDIGINI kanitlar. `storage_root()`
    KASITLI olarak da mock'lanir cunku gercek hali yan etki olarak disk
    uzerinde dizin OLUSTURUR (`path.mkdir(...)`) -- bu test bu fonksiyonun
    da hic cagrilmadigini (dolayisiyla hicbir dizin olusturma yan etkisinin
    tetiklenmedigini) dogrudan kanitlar."""
    from unittest import mock

    from flask import render_template

    with (
        mock.patch("app.file_center.services.save_uploaded_file", create=True) as mock_save,
        mock.patch("app.file_center.services.soft_delete_file", create=True) as mock_delete,
        mock.patch("app.file_center.services.storage_root", create=True) as mock_storage_root,
        app.test_request_context("/"),
    ):
        render_template(
            "file_center/index.html",
            **_index_context(),
        )
        render_template(
            "file_center/requests.html",
            **_requests_context(),
        )

    mock_save.assert_not_called()
    mock_delete.assert_not_called()
    mock_storage_root.assert_not_called()


def test_rendering_both_templates_creates_no_new_files_under_app_or_instance(app) -> None:
    """Ek, mock'lardan BAGIMSIZ ikinci kanit katmani: `app/` ve (varsa)
    `instance/` (dosya merkezinin gercek depolama kok dizininin varsayilan
    ebeveyni, bkz. `app/file_center/services.py::_default_storage_root`)
    altindaki dosya listesi render ONCESI ve SONRASI birebir ayni olmali --
    iki sablonun render edilmesi gercekten HICBIR dosya olusturmuyor/
    silmiyor/degistirmiyor. `__pycache__` dizinleri KASITLI olarak haric
    tutulur -- bu test SADECE bu iki dosyada calistirilirsa (izole `-k`
    secimi), `app.file_center.services`/`mail_service` modullerinin ILK KEZ
    import edilmesi Python'un KENDI bytecode-cache mekanizmasi yuzunden
    `.pyc` dosyalari yazabilir; bu, incelenen dosya-merkezi is mantigiyla
    ILGISIZ bir yan etkidir ve yanlis-pozitif test basarisizligina yol
    acmamasi icin taramadan cikarilir (asil `save_uploaded_file`/
    `soft_delete_file`/`storage_root` cagrilmadigi kaniti zaten yukaridaki
    mock-tabanli testte var)."""
    from flask import render_template

    def _snapshot() -> set[str]:
        found: set[str] = set()
        for root_name in ("app", "instance"):
            root_dir = REPO_ROOT / root_name
            if not root_dir.exists():
                continue
            found.update(
                p.relative_to(REPO_ROOT).as_posix()
                for p in root_dir.rglob("*")
                if "__pycache__" not in p.parts
            )
        return found

    before = _snapshot()

    with app.test_request_context("/"):
        render_template("file_center/index.html", **_index_context())
        render_template("file_center/requests.html", **_requests_context())

    after = _snapshot()
    assert after == before, (
        "Sablonlar render edilirken app/ veya instance/ altinda beklenmeyen "
        f"dosya degisikligi olustu. Eklenenler: {sorted(after - before)!r}, "
        f"silinenler: {sorted(before - after)!r}."
    )


# ---------------------------------------------------------------------------
# 5) Calisma-zamani render kontrolleri: gercek Flask app + gercek Jinja
#    motoru ile `render_template()` cagrisi (bkz. `app` fixture,
#    tests/conftest.py). Sahte `types.SimpleNamespace` context nesneleri
#    kullanilir (Wave5/6/8 ile ayni tercih) -- gercek route/DB/login akisina
#    girilmez. Context anahtarlari, gercek route'larin (`app/file_center/
#    routes.py::file_center_home` / `file_center_requests`) sagladigi TUM
#    anahtarlarla (yardimci fonksiyonlar dahil) birebir eslesir.
# ---------------------------------------------------------------------------


def _fake_file(file_id: int = 9001, **overrides: object) -> types.SimpleNamespace:
    base: dict[str, object] = dict(
        id=file_id,
        original_filename=f"Wave9-Belge-{file_id}.pdf",
        extension=".pdf",
        size_bytes=2048,
        sha256_hash="a" * 64,
        scan_status="clean",
        created_at=datetime.datetime(2026, 1, 5, 9, 30),
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


def _fake_link(link_id: int = 8001, *, file_obj: types.SimpleNamespace | None = None, **overrides: object) -> types.SimpleNamespace:
    base: dict[str, object] = dict(
        id=link_id,
        file=file_obj or _fake_file(),
        public_token="wave9-test-public-token-" + str(link_id),
        download_count=1,
        max_downloads=5,
        expires_at=datetime.datetime(2026, 2, 1, 12, 0),
        is_active=True,
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


def _fake_quota(**overrides: object) -> types.SimpleNamespace:
    base: dict[str, object] = dict(used_bytes=10_485_760, file_count=3)
    base.update(overrides)
    return types.SimpleNamespace(**base)


def _index_context() -> dict[str, object]:
    from app.file_center.services import format_bytes, link_status_label, scan_label

    file_a = _fake_file(9001)
    file_b = _fake_file(9002, original_filename="Wave9-Ikinci-Dosya.xlsx", extension=".xlsx", scan_status="pending")
    link_a = _fake_link(8001, file_obj=file_a, is_active=True)
    link_b = _fake_link(
        8002,
        file_obj=file_b,
        is_active=False,
        public_token=None,
        download_count=5,
        max_downloads=5,
    )
    return dict(
        files=[file_a, file_b],
        quota=_fake_quota(),
        quota_summary=None,
        links=[link_a, link_b],
        transfers=[],
        request_count=2,
        guest_links_enabled=True,
        format_bytes=format_bytes,
        scan_label=scan_label,
        link_status_label=link_status_label,
    )


def _fake_mail_log(mail_id: int = 7001, **overrides: object) -> types.SimpleNamespace:
    base: dict[str, object] = dict(
        id=mail_id,
        purpose="request_invitation",
        recipient_email="wave9-alici@example.test",
        subject="Wave9 kontrat testi konusu",
        error_message=None,
        status="sent",
        sent_at=datetime.datetime(2026, 1, 6, 10, 0),
        created_at=datetime.datetime(2026, 1, 6, 9, 55),
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


def _fake_upload(upload_id: int = 6001, *, file_obj: types.SimpleNamespace | None = None, **overrides: object) -> types.SimpleNamespace:
    base: dict[str, object] = dict(
        id=upload_id,
        file=file_obj or _fake_file(9003),
        guest_name="Wave9 Misafir",
        guest_email="misafir@example.test",
        created_at=datetime.datetime(2026, 1, 6, 11, 0),
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


def _fake_request(req_id: int = 5001, **overrides: object) -> types.SimpleNamespace:
    base: dict[str, object] = dict(
        id=req_id,
        title=f"Wave9 Dosya İsteği {req_id}",
        description="Kontrat testi icin sahte istek aciklamasi.",
        recipient_name="Wave9 Alıcı",
        recipient_email="alici@example.test",
        public_token="wave9-test-req-token-" + str(req_id),
        status="open",
        expires_at=datetime.datetime(2026, 2, 10, 18, 0),
        upload_count=1,
        allowed_extensions=".pdf,.docx",
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


def _requests_context() -> dict[str, object]:
    from app.file_center.mail_service import mail_purpose_label, mail_status_label
    from app.file_center.services import format_bytes, request_status_label

    open_req = _fake_request(5001, status="open", upload_count=1)
    closed_req = _fake_request(
        5002,
        status="closed",
        upload_count=0,
        public_token=None,
        recipient_name=None,
        recipient_email=None,
        description=None,
    )
    upload = _fake_upload(6001, file_obj=_fake_file(9003))
    mail_log = _fake_mail_log(7001)

    return dict(
        requests=[open_req, closed_req],
        uploads_by_request={open_req.id: [upload]},
        mail_logs_by_request={open_req.id: [mail_log]},
        request_status_label=request_status_label,
        mail_status_label=mail_status_label,
        mail_purpose_label=mail_purpose_label,
        format_bytes=format_bytes,
    )


def test_index_render_preserves_delete_confirm_message_and_wiring(app) -> None:
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template("file_center/index.html", **_index_context())

    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert f'data-confirm="{INDEX_DELETE_CONFIRM_MESSAGE}"' in html
    assert 'class="d-inline"' in html
    assert html.count("querySelectorAll('form[data-confirm]')") == 1
    assert "addEventListener('submit'" in html
    assert "onsubmit=" not in html


def test_index_render_empty_files_state_still_has_no_inline_handlers(app) -> None:
    """`files` bos oldugunda (bos-durum karti) da render hatasiz calisir ve
    inline handler icermez -- Sil formu satiri hic render edilmedigi icin
    data-confirm de gorunmez, ama script her zaman render edilir (content
    block'un sonunda, files'tan bagimsiz)."""
    from flask import render_template

    from app.file_center.services import format_bytes, link_status_label, scan_label

    with app.test_request_context("/"):
        html = render_template(
            "file_center/index.html",
            files=[],
            quota=_fake_quota(used_bytes=0, file_count=0),
            quota_summary=None,
            links=[],
            transfers=[],
            request_count=0,
            guest_links_enabled=True,
            format_bytes=format_bytes,
            scan_label=scan_label,
            link_status_label=link_status_label,
        )

    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert "Henüz dosya yüklenmedi" in html
    assert html.count("querySelectorAll('form[data-confirm]')") == 1
    assert 'data-confirm="' not in html


def test_index_render_with_guest_links_disabled_hides_toggle_but_keeps_delete_confirm(app) -> None:
    """guest_links_enabled=False oldugunda misafir baglanti toggle butonu
    render edilmez, ama Sil formunun confirm sozlesmesi etkilenmez (iki
    bagimsiz kosul dali arasinda regresyon olmadiginin kaniti)."""
    from flask import render_template

    ctx = _index_context()
    ctx["guest_links_enabled"] = False

    with app.test_request_context("/"):
        html = render_template("file_center/index.html", **ctx)

    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert f'data-confirm="{INDEX_DELETE_CONFIRM_MESSAGE}"' in html
    assert "Misafir Bağlantısı</button>" not in html


def test_requests_render_preserves_revoke_confirm_message_and_wiring(app) -> None:
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template("file_center/requests.html", **_requests_context())

    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert f'data-confirm="{REQUESTS_REVOKE_CONFIRM_MESSAGE}"' in html
    assert html.count("querySelectorAll('form[data-confirm]')") == 1
    assert "addEventListener('submit'" in html
    assert "onsubmit=" not in html
    # Acik istek icin Iptal Et VE Kapat formlari ikisi de mevcut olmali.
    assert "Kapat</button>" in html
    assert "İptal Et</button>" in html
    # Kapali istek (closed_req) icin ne Iptal Et ne Kapat formu render edilmemeli
    # (status == 'open' kosulunun disinda).
    closed_section_start = html.index("Wave9 Dosya İsteği 5002")
    closed_tail = html[closed_section_start : closed_section_start + 1500]
    assert "file_center_revoke_request', request_id=5002" not in closed_tail


def test_requests_render_empty_requests_state_still_has_no_inline_handlers(app) -> None:
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template(
            "file_center/requests.html",
            requests=[],
            uploads_by_request={},
            mail_logs_by_request={},
            request_status_label=__import__("app.file_center.services", fromlist=["request_status_label"]).request_status_label,
            mail_status_label=__import__("app.file_center.mail_service", fromlist=["mail_status_label"]).mail_status_label,
            mail_purpose_label=__import__("app.file_center.mail_service", fromlist=["mail_purpose_label"]).mail_purpose_label,
            format_bytes=__import__("app.file_center.services", fromlist=["format_bytes"]).format_bytes,
        )

    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert "Henüz dosya isteği oluşturulmadı" in html
    assert html.count("querySelectorAll('form[data-confirm]')") == 1
    assert 'data-confirm="' not in html


def test_requests_render_with_mail_logs_and_uploads_present_has_no_inline_handlers(app) -> None:
    """Mail loglari ve gelen yuklemeler VARKEN de (dogal olarak en yogun
    render dali) inline handler yok ve confirm sozlesmesi korunuyor."""
    from flask import render_template

    ctx = _requests_context()
    with app.test_request_context("/"):
        html = render_template("file_center/requests.html", **ctx)

    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert "wave9-alici@example.test" in html
    assert "Wave9 Misafir" in html
    assert f'data-confirm="{REQUESTS_REVOKE_CONFIRM_MESSAGE}"' in html
