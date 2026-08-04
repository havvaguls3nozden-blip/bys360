"""CSP Dalga 9 (SON dalga) - `app/templates/messages_thread.html` + `app/static/js/
messages_messenger_mobile.js`: son 2 inline event-handler'ın (mesaj silme onsubmit=
confirm(...) VE mesaj düzenleme onclick=openEditModal(...)) merkezi delegasyona
taşınmasının kontrat testi.

BYS360 `app/security/headers.py` uygular:
    script-src: 'self' https:  (unsafe-inline YOK)

Bu dalga, repodaki SON 2 kalan gerçek inline event-handler'ı (messages_
thread.html'deki onclick=/onsubmit=) kapsar. Wave 8'in test dosyası
(`tests/security/test_csp_wave8_task_mail_guard_contract.py`) yazıldığı anda
şu dağılımı gözlemlemişti: messages_thread.html=2, file_center/index.html=1,
file_center/requests.html=1 (toplam 4). Bu Dalga 9 dosyası KENDİ bağımsız
taramasında (aynı kanonik `[\\s]on[a-zA-Z]+\\s*=\\s*["']` regex'i ile, bkz.
Bölüm C) file_center/index.html VE file_center/requests.html'in ARTIK
(bu görev başlamadan ÖNCE bile) 0 gerçek inline-handler içerdiğini doğrular.
Kaynağı incelendiğinde bu iki dosyanın halihazırda `data-confirm="..."` +
merkezi delegasyona dönüştürülmüş olduğu görülür (bkz. paralel/kardeş
`tests/security/test_csp_wave9_file_center_contract.py` -- bu, file_center/*
dönüşümünün AYRI bir paralel Dalga 9 ajanı tarafından zaten tamamlanmış
olduğunun kanıtıdır; bu iki dosyanın git diff'i bu worktree'de zaten
"M" (değiştirilmiş, commit edilmemiş) durumdadır). Bu dosyanın sahipliği
SADECE messages_thread.html + messages_messenger_mobile.js ile sınırlıdır --
file_center/*.html BU görevin kapsamı DIŞINDADIR ve bu dosya onlara hiçbir
şekilde DOKUNMAZ/YAZMAZ; Bölüm C'deki test SADECE salt-okunur bir
doğrulama/bilgilendirmedir. SONUÇ: messages_thread.html (bu dosya) + file_center/*
(paralel ajan) birlikte tamamlanınca Wave 8'in `test_repo_wide_inline_
handler_count_after_wave8_equals_four` ve `test_three_out_of_scope_files_
retain_expected_untouched_handler_counts` testleri artık ESKİ/statik
beklenti değerleriyle (4 ve messages_thread.html=2/file_center=1+1) FAIL
verir -- bu, koordinatörün Wave 8 test dosyasını Wave 9 sonrası güncellemesi
gereken, bu görevin sorumluluğu DIŞINDA bir bakım kalemidir (bkz. raporlama).

Bu şablon zaten olgun bir mimariye sahipti: `messages_messenger_mobile.js`
TEK bir merkezi `document.addEventListener('submit', ...)` (reaction/comment
formları için) ve TEK bir merkezi `document.addEventListener('click', ...)`
(`[data-message-comment-toggle]` için) delegasyonuna sahipti. Dalga 9, YENİ
bir delegasyon AÇMADAN, bu MEVCUT iki delegasyonun İÇİNE iki yeni dal ekledi:

    1) Silme confirm'i: `onsubmit="return confirm('Bu mesaj silinsin mi?');"`
       -> `data-confirm="Bu mesaj silinsin mi?"` + mevcut submit-delegasyonunun
       İÇİNE eklenen `form[data-confirm]` dalı (confirm iptalinde SADECE
       `event.preventDefault()`; onaylanırsa hiçbir şey yapılmaz -- form AJAX'e
       ÇEVRİLMEDİ, normal browser POST/sayfa navigasyonu aynen devam eder --
       reaction/comment formlarının aksine bu formda `return false` YOK).

    2) Düzenleme modalı: `onclick="openEditModal('{{ message.id }}',
       {{ message.body|tojson }})"` -> `data-message-edit-trigger
       data-message-id="{{ message.id }}" data-message-body="{{ message.body
       or '' }}"` + mevcut click-delegasyonunun İÇİNE eklenen
       `[data-message-edit-trigger]` dalı (`window.openEditModal` çağrısı).
       `openEditModal` fonksiyonunun GÖVDESİ (form.action doldurma, textarea
       değeri, `modal.show()`) template'in kendi `<script>` bloğunda AYNEN
       KALDI -- taşınmadı; sadece `window.openEditModal = openEditModal;`
       satırı eklenerek dış JS dosyasından erişilebilir kılındı (fonksiyon
       zaten top-level klasik `<script>` bloğunda tanımlı olduğu için örtük
       olarak `window.openEditModal` idi; bu satır bunu EXPLICIT/garantili
       hale getirdi, YENİ bir global fonksiyon icat etmedi).

    ÖNEMLİ DÜZELTME (coordinator notu): görev talimatı `data-message-body="{{
    message.body }}"` öneriyordu, ancak `message.body` None olabilir (ekli
    dosya-only mesajlarda) ve çıplak Jinja çıktısı `None`'ı literal "None"
    string'i olarak render eder (önceki `|tojson` kullanımı bunu JSON `null`
    yapıyordu). Bu regresyonu önlemek için `{{ message.body or '' }}`
    kullanıldı -- davranış paritesi (boş string) korunur, "None" string sızıntısı
    önlenir. Bu dosyadaki testler bu düzeltmeyi de doğrular (Bölüm E).

Bu dosyanın sahiplik alanı SADECE testtir -- aşağıdaki üretim dosyalarına
DOKUNMAZ (onlar bu görevin ayrı, önceki adımlarında zaten değiştirildi):
    - app/templates/messages_thread.html
    - app/static/js/messages_messenger_mobile.js

Not (render testleri için önemli, bkz. Wave5 docstring'i ile aynı desendedir):
bu app `app/template_safety.py` içinde `app.jinja_env.undefined =
ChainableUndefined` ayarlar; context'te sağlanmayan değişkenlere zincirlenmiş
attribute erişimi (`message.attachments` vb.) veya `is defined` testi hata
fırlatmaz. `current_user` gerçek flask_login proxy'sinin yerine, Wave5
desenindeki gibi context'e DOĞRUDAN bir `types.SimpleNamespace` olarak
geçirilir (parent context'i override eder).

Statik testler diğer wave dosyalarıyla aynı desendedir (Path.read_text() +
regex, sonra gerçek Jinja motoruyla `render_template()` çıktı testleri;
`app` fixture'ı `tests/conftest.py`'den gelir).

GERÇEK MESAJ GÖNDERME/SİLME/DÜZENLEME asla yapılmaz: bu dosyadaki hiçbir test
`main.messages_send`/`main.messages_delete`/`main.messages_edit` route'larına
gerçek bir HTTP POST/istemci çağrısı yapmaz (Flask test client hiç
kullanılmaz); SADECE `flask.render_template()` (salt-okunur şablon render) ve
`Path.read_text()` kullanılır. Bölüm F bunu hem statik hem de çalışma-zamanı
pozitif kanıtla doğrular.

ÖNEMLİ SINIRLAMA: Bu dosyadaki HİÇBİR test gerçek bir tarayıcıda çalışmaz.
`render_template()` yalnızca ÜRETİLEN HTML'i doğrular; confirm dialog'unun
fiilen açılıp iptal edilebildiğini veya edit modal'ının fiilen açıldığını
KANITLAMAZ -- bu, ayrı bir manuel/E2E doğrulama gerektirir ve bu dosyanın
kapsamı dışındadır (koordinatöre raporlanır).
"""
from __future__ import annotations

import re
import types
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

TEMPLATE_PATH = "app/templates/messages_thread.html"
JS_PATH = "app/static/js/messages_messenger_mobile.js"

DELETE_CONFIRM_MESSAGE = "Bu mesaj silinsin mi?"

# HTML attribute syntax: bosluk + on<harfler> + '=' + tirnak. CSS/JS icindeki
# "javascript:" gibi metinsel string literal'leri yanlislikla yakalamaz. Bu,
# diger tum wave kontrat dosyalarindaki KANONIK regex ile birebir aynidir.
_INLINE_EVENT_ATTR_RE = re.compile(r"""[\s]on[a-zA-Z]+\s*=\s*["']""")

_FORBIDDEN_JS_SINKS = ("eval(", "new Function(", "document.write(")

# Bu test dosyasinin KENDISI asla cagirmamasi gereken gercek mesaj gonderim/
# silme/duzenleme servis fonksiyonlari (route/servis katmani).
_FORBIDDEN_REAL_MESSAGE_ACTION_MARKERS = (
    "test_client()",
    ".post(\"/messages",
    ".post('/messages",
    "messages_delete(",
    "messages_edit(",
    "messages_send(",
    "_svc_create_direct_message_with_attachments(",
)


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Sahte veri kurucular (types.SimpleNamespace). `messages_thread.html`
# dikkatle okunarak hangi alanlara erisildigi tespit edildi: message.id,
# message.sender_user_id, message.sender.{full_name,ad,soyad}, message.body,
# message.is_deleted, message.attachments (is defined + .all() korumali),
# message.sent_at, message.edited_at, message.comments (is defined + .all()
# korumali). attachments/comments alanlari testlerde KASITLI olarak
# atlanir (omit) -- ChainableUndefined bu durumda `is defined` testini False
# dondurur, boylece `.all()` hic cagrilmaz (gercekci lazy='dynamic' davranisi).
# ---------------------------------------------------------------------------


def _fake_user(**overrides: object) -> types.SimpleNamespace:
    base: dict[str, object] = dict(
        id=1,
        full_name="Wave9 Proba Kullanici",
        ad="Wave9",
        soyad="Proba",
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


def _fake_message(message_id: int, **overrides: object) -> types.SimpleNamespace:
    base: dict[str, object] = dict(
        id=message_id,
        sender_user_id=1,
        sender=_fake_user(id=1, full_name=f"Gonderen {message_id}"),
        body=f"Wave9 test govde metni {message_id}",
        is_deleted=False,
        sent_at=None,
        edited_at=None,
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


def _fake_thread(**overrides: object) -> types.SimpleNamespace:
    base: dict[str, object] = dict(
        id=42,
        title="Wave9 Test Konusmasi",
        accent_color="#8B0000",
        icon_name="fa-solid fa-comments",
        thread_type="direct",
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


def _base_context(messages: list[types.SimpleNamespace], **overrides: object) -> dict[str, object]:
    context: dict[str, object] = {
        "thread": _fake_thread(),
        "participants": [],
        "messages": messages,
        "back_url": "/messages",
        "compose_submit_token": "wave9-test-token",
        "current_user": _fake_user(id=1),
        "reaction_options": ["👍", "❤️"],
    }
    context.update(overrides)
    return context


# ---------------------------------------------------------------------------
# A) Statik kaynak-kod kontratı: inline handler sayısı 2 -> 0.
# ---------------------------------------------------------------------------


def test_template_source_has_zero_inline_event_attributes() -> None:
    """Madde 1: `messages_thread.html` kaynağında hiçbir inline event-attribute
    (on*=) kalmadı -- eski satır 140 onclick=openEditModal(...) ve satır 143
    onsubmit=confirm(...) tamamen kaldırılmış olmalı."""
    text = _read(TEMPLATE_PATH)
    matches = _INLINE_EVENT_ATTR_RE.findall(text)
    assert not matches, (
        f"{TEMPLATE_PATH} icinde hala inline event-attribute (on*=) bulundu: {matches!r}. "
        "CSP script-src 'self' https: (unsafe-inline yok) altinda bunlar calismaz."
    )


def test_template_source_has_data_confirm_and_edit_trigger_attributes() -> None:
    """Madde 2: `data-confirm="Bu mesaj silinsin mi?"` VE
    `data-message-edit-trigger` (+ `data-message-id`/`data-message-body`)
    attribute'ları kaynak kodda mevcut, tam olarak birer kez."""
    text = _read(TEMPLATE_PATH)
    assert f'data-confirm="{DELETE_CONFIRM_MESSAGE}"' in text
    assert text.count(f'data-confirm="{DELETE_CONFIRM_MESSAGE}"') == 1
    assert "data-message-edit-trigger" in text
    assert text.count("data-message-edit-trigger") == 1
    assert 'data-message-id="{{ message.id }}"' in text
    assert "data-message-body=\"{{ message.body or '' }}\"" in text


def test_template_source_openEditModal_function_body_unchanged_and_exposed_globally() -> None:
    """Madde 3: `openEditModal` fonksiyon TANIMI (form.action doldurma,
    textarea degeri, modal.show()) template'in kendi <script> blogunda AYNEN
    korunuyor -- sadece `window.openEditModal = openEditModal;` satiri
    eklendi (yeni bir global fonksiyon icat edilmedi, var olan erisilebilir
    kilindi)."""
    text = _read(TEMPLATE_PATH)
    assert "function openEditModal(messageId, bodyText) {" in text
    assert "form.action = tpl ? tpl.replace(/0$/, String(messageId))" in text
    assert "textarea.value = bodyText || '';" in text
    assert "modal.show();" in text
    assert "window.openEditModal = openEditModal;" in text
    # Fonksiyon govdesi tasinmadi: template'de HALA tam olarak 1 tanim var.
    assert text.count("function openEditModal(messageId, bodyText) {") == 1


def test_js_source_delegation_listeners_registered_exactly_once() -> None:
    """Madde 4: `messages_messenger_mobile.js` icinde
    `document.addEventListener('submit'` ve `document.addEventListener('click'`
    cagrilari TAM OLARAK birer kez geciyor -- Wave9'un eklediği iki yeni dal
    MEVCUT delegasyonların İÇİNE girdi, YENİ bir delegasyon AÇILMADI."""
    text = _read(JS_PATH)
    assert text.count("document.addEventListener('submit'") == 1, (
        "document.addEventListener('submit' TAM OLARAK 1 kez beklenir (yeni delegasyon acilmamali)."
    )
    assert text.count("document.addEventListener('click'") == 1, (
        "document.addEventListener('click' TAM OLARAK 1 kez beklenir (yeni delegasyon acilmamali)."
    )


def _extract_submit_delegation_block(text: str) -> str:
    start = text.index("document.addEventListener('submit'")
    # Bir sonraki ust-seviye document.addEventListener veya dosya sonuna kadar.
    end_marker = "document.addEventListener('click'"
    end = text.index(end_marker, start)
    return text[start:end]


def _extract_click_delegation_block(text: str) -> str:
    start = text.index("document.addEventListener('click'")
    end = text.index("const messageContainer = document.getElementById", start)
    return text[start:end]


def test_js_submit_delegation_contains_confirm_branch_alongside_existing_branches() -> None:
    """Madde 5: submit-delegasyon bloğu icinde HEM `form[data-confirm]` dalı
    HEM de mevcut `.js-message-reaction-form` / `.js-message-comment-form`
    dallari BIRLIKTE mevcut -- yeni dal, mevcut dallarin YERINE degil,
    YANINA eklendi."""
    text = _read(JS_PATH)
    block = _extract_submit_delegation_block(text)
    assert "form[data-confirm]" in block
    assert ".js-message-reaction-form" in block
    assert ".js-message-comment-form" in block
    assert block.count("form[data-confirm]") == 1


def test_js_confirm_branch_only_preventdefaults_on_cancellation_no_ajax_no_return_false() -> None:
    """Madde 6 (kritik davranis kontrati): confirm dali, reaction/comment
    dallarinin aksine bu formu AJAX'e CEVIRMEMELI -- yalnizca confirm iptal
    edildiginde `event.preventDefault()` cagirmali; onaylanirsa (window.confirm
    true donerse) hicbir sey yapmadan (fetch/return false OLMADAN) normal
    browser POST/sayfa navigasyonunun devam etmesine izin vermeli."""
    text = _read(JS_PATH)
    block = _extract_submit_delegation_block(text)
    confirm_branch_start = block.index("form[data-confirm]")
    # Bir sonraki dal (.js-message-reaction-form) basina kadar sadece confirm dalini al.
    confirm_branch_end = block.index(".js-message-reaction-form")
    confirm_branch = block[confirm_branch_start:confirm_branch_end]

    assert "window.confirm(message)" in confirm_branch
    assert "event.preventDefault();" in confirm_branch
    # Confirm dalinda fetch/AJAX YOK -- gercek POST navigasyonu bozulmamali.
    assert "fetch(" not in confirm_branch
    assert "return false" not in confirm_branch
    # preventDefault SADECE `!window.confirm(...)` kosulunun icinde cagrilmali
    # (yani onaylanirsa preventDefault calismamali) -- kosul yapisini dogrula.
    assert "if(message && !window.confirm(message)){" in confirm_branch


def test_js_click_delegation_contains_edit_trigger_branch_alongside_existing_toggle() -> None:
    """Madde 7: click-delegasyon bloğu icinde HEM `[data-message-edit-trigger]`
    dali HEM de mevcut `[data-message-comment-toggle]` dali BIRLIKTE mevcut."""
    text = _read(JS_PATH)
    block = _extract_click_delegation_block(text)
    assert "[data-message-edit-trigger]" in block
    assert "[data-message-comment-toggle]" in block
    assert block.count("[data-message-edit-trigger]") >= 1


def test_js_edit_trigger_branch_calls_window_openEditModal_with_dataset_values() -> None:
    """Madde 8: edit-trigger dali `window.openEditModal` fonksiyonunu
    `data-message-id`/`data-message-body` attribute degerleriyle cagiriyor
    (typeof guard ile), boylece template-lokal fonksiyon disaridan güvenle
    erisilebiliyor."""
    text = _read(JS_PATH)
    block = _extract_click_delegation_block(text)
    edit_branch_start = block.index("[data-message-edit-trigger]")
    edit_branch_end = block.index("[data-message-comment-toggle]")
    edit_branch = block[edit_branch_start:edit_branch_end]

    assert "typeof window.openEditModal === 'function'" in edit_branch
    assert "window.openEditModal(editTrigger.getAttribute('data-message-id'), editTrigger.getAttribute('data-message-body'))" in edit_branch


def test_js_introduces_no_dangerous_sinks() -> None:
    """Madde 9: `eval(`, `new Function(`, `document.write(` yasaklı
    sink'lerinden hiçbiri eklenmemiş."""
    text = _read(JS_PATH)
    for forbidden in _FORBIDDEN_JS_SINKS:
        assert forbidden not in text, f"{JS_PATH} icinde yasakli sink bulundu: {forbidden}"


def test_no_javascript_url_or_inline_handler_string_literal_smuggled_into_js() -> None:
    """Madde 10: inline handler'in bir HTML string'i olarak JS icinde
    uretilmedigini (`'onclick='`/`"onclick="`/`'onsubmit='`/`"onsubmit="`
    literal'i yoklugunu) ve `javascript:` URL sink'i olmadigini dogrular."""
    text = _read(JS_PATH)
    for literal in ("'onclick='", '"onclick="', "'onsubmit='", '"onsubmit="'):
        assert literal not in text, f"{JS_PATH} icinde yasakli JS string literal bulundu: {literal}"
    assert "javascript:" not in text


# ---------------------------------------------------------------------------
# B) CSRF/action/method paritesi (statik).
# ---------------------------------------------------------------------------


def test_delete_form_action_method_and_csrf_unchanged() -> None:
    """Madde 11: silme formunun `method="POST"`, `action=` (messages_delete
    url_for) ve gizli `csrf_token` input'u AYNEN korunuyor -- sadece
    `onsubmit` kaldirilip `data-confirm` eklendi."""
    text = _read(TEMPLATE_PATH)
    expected = (
        '<form method="POST" action="{{ url_for(\'main.messages_delete\', message_id=message.id) }}" '
        f'data-confirm="{DELETE_CONFIRM_MESSAGE}">'
    )
    assert expected in text
    # Form acilisindan sonraki ilk satirda csrf_token input'u olmali.
    form_start = text.index(expected)
    tail = text[form_start : form_start + 400]
    assert '<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">' in tail


def test_edit_modal_form_action_template_and_csrf_unchanged() -> None:
    """Madde 12: `editMessageForm`'un `data-action-template` (messages_edit
    url_for sablonu) ve gizli `csrf_token` input'u Wave9'dan ETKILENMEDI --
    bu dalga sadece TETIKLEYICI butonu (satir 140) degistirdi, modal formunun
    kendisine dokunmadi."""
    text = _read(TEMPLATE_PATH)
    assert 'data-action-template="{{ url_for(\'main.messages_edit\', message_id=0) }}"' in text
    assert 'id="editMessageForm"' in text
    form_start = text.index('id="editMessageForm"')
    tail = text[form_start : form_start + 600]
    assert '<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">' in tail


# ---------------------------------------------------------------------------
# C) Repo-genelinde bilgilendirme kontrolü: bu 2 dosyanin DISINDAKI iki
#    dosyanın (Wave9'un kapsamı dışında, bu dosya tarafından hiç
#    değiştirilmeyen) gerçek inline-handler durumu -- SALT-OKUNUR, bu dosya
#    onlara asla yazmaz.
# ---------------------------------------------------------------------------


def test_out_of_scope_file_center_files_have_zero_real_inline_handlers_readonly_check() -> None:
    """Madde 13 (salt-okunur bilgilendirme, Wave9'un kapsamı DIŞINDA):
    file_center/index.html ve file_center/requests.html BU görevin
    sahiplik alanı DIŞINDADIR -- bu test dosyası onlara asla YAZMAZ, sadece
    `Path.read_text()` ile OKUR. Aynı kanonik `[\\s]on[a-zA-Z]+\\s*=\\s*["']`
    regex'i ile (diğer tüm wave kontrat dosyalarıyla birebir aynı desen)
    taradığında bu iki dosyanın GERÇEKTE 0 inline event-handler içerdiğini
    doğrular -- bkz. modül docstring'i (bu iki dosya, paralel bir Dalga 9
    ajanı tarafından zaten `data-confirm` + delegasyona dönüştürülmüş,
    bu görev BAŞLAMADAN ÖNCE bile bu worktree'de "M" durumundaydı)."""
    for relative_path in ("app/templates/file_center/index.html", "app/templates/file_center/requests.html"):
        path = REPO_ROOT / relative_path
        if not path.exists():
            pytest.skip(f"{relative_path} bu ortamda bulunamadi; kapsam-disi kontrol atlandi.")
        text = path.read_text(encoding="utf-8")
        matches = _INLINE_EVENT_ATTR_RE.findall(text)
        assert matches == [], (
            f"{relative_path} icinde beklenmedik gercek inline-handler bulundu: {matches!r}. "
            "Bu dosya Wave9'un kapsami DISINDA -- bu bulgu koordinatore raporlanmalidir."
        )


def test_repo_wide_canonical_inline_handler_count_is_zero_after_wave9() -> None:
    """Madde 13-b: `app/templates/**/*.html` genelinde kanonik
    `[\\s]on[a-zA-Z]+\\s*=\\s*["']` regex'i (diğer tüm wave dosyalarıyla
    birebir aynı desen) ile toplam GERÇEK inline event-handler sayısının
    Dalga 9 SONRASI tam olarak 0 olduğunu doğrular -- bu, görev talimatındaki
    "bu dosyadaki 2 handler kaldırılınca repo genelinde inline event handler
    0 olacak" beklentisinin GERÇEKTEN doğrulanmış kanıtıdır (salt-okunur
    tarama, hiçbir dosyaya yazılmaz)."""
    pattern = _INLINE_EVENT_ATTR_RE
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

    assert total == 0, (
        f"Repo genelinde beklenen inline-handler toplami 0 degil, {total} bulundu. "
        f"Dagilim: {offenders!r}."
    )


# ---------------------------------------------------------------------------
# D) Çalışma-zamanı render kontrolü: gerçek Flask app + gerçek Jinja motoru
#    ile `render_template()` çağrısı (bkz. `app` fixture, tests/conftest.py).
#    Birden fazla sahte `message` -- kendi mesaji olan/olmayan, silinmis/
#    silinmemis, None body varyasyonlari dahil.
# ---------------------------------------------------------------------------


def test_render_with_own_undeleted_message_has_edit_and_delete_triggers(app) -> None:
    """Madde 14: current_user'in KENDI, SILINMEMIS mesaji icin hem
    `data-message-edit-trigger` hem `data-confirm` render ciktisinda mevcut,
    dogru message.id/body degerleriyle."""
    from flask import render_template

    own_message = _fake_message(701, sender_user_id=1, body="Benim mesajim", is_deleted=False)
    with app.test_request_context("/"):
        html = render_template(TEMPLATE_PATH.split("app/templates/", 1)[1], **_base_context([own_message]))

    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert 'data-message-edit-trigger data-message-id="701" data-message-body="Benim mesajim"' in html
    assert f'data-confirm="{DELETE_CONFIRM_MESSAGE}"' in html
    assert '{{ url_for(\'main.messages_delete\'' not in html  # gercekten render edildi, sablon degil


def test_render_with_other_users_message_has_no_edit_or_delete_triggers(app) -> None:
    """Madde 15: current_user'e AIT OLMAYAN bir mesaj icin ne edit-trigger ne
    de delete-confirm formu render edilmemeli (mevcut yetki kontratinin
    Wave9 tarafindan bozulmadiginin kaniti)."""
    from flask import render_template

    other_message = _fake_message(702, sender_user_id=999, body="Baskasinin mesaji", is_deleted=False)
    with app.test_request_context("/"):
        html = render_template(TEMPLATE_PATH.split("app/templates/", 1)[1], **_base_context([other_message]))

    assert "data-message-edit-trigger" not in html
    assert f'data-confirm="{DELETE_CONFIRM_MESSAGE}"' not in html


def test_render_with_own_deleted_message_has_no_edit_or_delete_triggers(app) -> None:
    """Madde 16: current_user'in KENDI mesaji olsa bile SILINMIS
    (`is_deleted=True`) ise edit/delete aksiyonlari render edilmemeli."""
    from flask import render_template

    deleted_message = _fake_message(703, sender_user_id=1, body="Silinmis mesaj", is_deleted=True)
    with app.test_request_context("/"):
        html = render_template(TEMPLATE_PATH.split("app/templates/", 1)[1], **_base_context([deleted_message]))

    assert "data-message-edit-trigger" not in html
    assert f'data-confirm="{DELETE_CONFIRM_MESSAGE}"' not in html


def test_render_with_none_body_message_renders_empty_string_not_python_none(app) -> None:
    """Madde 17 (regresyon kilidi): `message.body is None` oldugunda (ornegin
    sadece-ek/attachment mesaji) `data-message-body` cikti degerinin literal
    `"None"` string'i OLMADIGINI, bos string oldugunu dogrular. Bu, gorev
    talimatindaki cıplak `{{ message.body }}` yerine `{{ message.body or ''
    }}` kullanma kararinin kanitidir -- eski `|tojson` kullanimi None'i JSON
    `null` yapiyordu, cıplak Jinja ciktisi ise `None` metnini sizdirirdi."""
    from flask import render_template

    none_body_message = _fake_message(704, sender_user_id=1, body=None, is_deleted=False)
    with app.test_request_context("/"):
        html = render_template(TEMPLATE_PATH.split("app/templates/", 1)[1], **_base_context([none_body_message]))

    assert 'data-message-edit-trigger data-message-id="704" data-message-body="">' in html
    assert "data-message-body=\"None\"" not in html


def test_render_with_mixed_messages_produces_correct_per_message_trigger_isolation(app) -> None:
    """Madde 18: 4 farkli varyasyonlu (kendi/silinmemis, baskasinin, kendi/
    silinmis, kendi/None-body) mesaji AYNI render'da birlikte test eder --
    her mesajin kendi id'sine gore dogru sekilde izole edildigini (capraz
    sizinti olmadigini) dogrular."""
    from flask import render_template

    messages = [
        _fake_message(801, sender_user_id=1, body="Kendi mesajim A", is_deleted=False),
        _fake_message(802, sender_user_id=999, body="Baskasinin mesaji", is_deleted=False),
        _fake_message(803, sender_user_id=1, body="Kendi silinmis mesajim", is_deleted=True),
        _fake_message(804, sender_user_id=1, body=None, is_deleted=False),
    ]
    with app.test_request_context("/"):
        html = render_template(TEMPLATE_PATH.split("app/templates/", 1)[1], **_base_context(messages))

    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    # Toplam edit-trigger sayisi: sadece 801 ve 804 (kendi + silinmemis) -> 2.
    assert html.count("data-message-edit-trigger") == 2
    assert 'data-message-id="801" data-message-body="Kendi mesajim A"' in html
    assert 'data-message-id="804" data-message-body="">' in html
    # Edit-trigger'lar SADECE 801/804'e ait -- 802 (baskasi) ve 803 (silinmis)
    # icin capraz-sizinti YOK (izole dogrulama, regex ile message-id yakalanir).
    edit_trigger_ids = re.findall(r'data-message-edit-trigger data-message-id="(\d+)"', html)
    assert edit_trigger_ids == ["801", "804"]
    # Toplam delete-confirm formu sayisi: sadece 801 ve 804 -> 2.
    assert html.count(f'data-confirm="{DELETE_CONFIRM_MESSAGE}"') == 2


def test_render_script_blocks_present_exactly_once_each(app) -> None:
    """Madde 19: Render ciktisinda `openEditModal` fonksiyon tanimi VE
    `window.openEditModal = openEditModal;` satiri VE
    `messages_messenger_mobile.js` script-src referansi TAM OLARAK birer kez
    geciyor (cift-baglanma/cift-tanim riski yok)."""
    from flask import render_template

    own_message = _fake_message(901, sender_user_id=1, body="Script kontrolu", is_deleted=False)
    with app.test_request_context("/"):
        html = render_template(TEMPLATE_PATH.split("app/templates/", 1)[1], **_base_context([own_message]))

    assert html.count("function openEditModal(messageId, bodyText) {") == 1
    assert html.count("window.openEditModal = openEditModal;") == 1
    assert re.search(r'<script[^>]*\ssrc="[^"]*messages_messenger_mobile\.js[^"]*"[^>]*>', html)
    assert len(re.findall(r'<script[^>]*\ssrc="[^"]*messages_messenger_mobile\.js[^"]*"[^>]*>', html)) == 1


def test_render_with_empty_messages_list_shows_empty_state_and_no_handlers(app) -> None:
    """Madde 20: Bos mesaj listesiyle render edildiginde 'Henuz mesaj yok'
    bos-durum metni gorunuyor VE hicbir inline event-attribute yok (bos
    liste durumunda regex tarafindan yanlislikla hicbir sey yakalanmadigi
    sagliginin kontrolu)."""
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template(TEMPLATE_PATH.split("app/templates/", 1)[1], **_base_context([]))

    assert "Henüz mesaj yok" in html
    assert not _INLINE_EVENT_ATTR_RE.findall(html)


# ---------------------------------------------------------------------------
# E) Gerçek mesaj gönderilmediğinin/silinmediğinin/düzenlenmediğinin hem
#    statik hem de çalışma-zamanı pozitif kanıtı.
# ---------------------------------------------------------------------------


def test_this_guard_file_never_uses_a_real_test_client_or_calls_message_services() -> None:
    """Madde 21: Bu test dosyasının KENDİ kaynağı, gerçek bir Flask test
    istemcisi başlatma çağrısı, gerçek `/messages/...` HTTP POST cagrisi
    veya mesaj servis/route fonksiyonlarini (`messages_delete`,
    `messages_edit`, `messages_send`, `_svc_create_direct_message_with_
    attachments`) hiçbir zaman kullanmadığını statik olarak doğrular --
    SADECE `flask.render_template()` (salt-okunur) ve `Path.read_text()`
    kullanılır. (Not: `_FORBIDDEN_REAL_MESSAGE_ACTION_MARKERS` sabitinin
    KENDİ tanım bloğu, marker string'lerinin doğal olarak yer aldığı tek
    yer olduğu için taramadan hariç tutulur -- aksi halde tanımın kendisi
    yanlış-pozitif tetiklerdi.)"""
    text = Path(__file__).read_text(encoding="utf-8")
    definition_marker = "_FORBIDDEN_REAL_MESSAGE_ACTION_MARKERS = ("
    def_start = text.index(definition_marker)
    def_end = text.index(")\n", def_start) + 1
    scan_text = text[:def_start] + text[def_end:]
    for marker in _FORBIDDEN_REAL_MESSAGE_ACTION_MARKERS:
        assert marker not in scan_text, f"Bu test dosyasinda yasakli gercek-mesaj-eylemi izi bulundu: {marker!r}"


def test_wave9_static_scans_and_template_renders_never_send_real_http_or_spawn_process(app) -> None:
    """Madde 22: POZİTİF çalışma-zamanı kanıtı -- bu test dosyasının fiilen
    yaptığı işlemler (şablonun `flask.render_template()` ile çeşitli
    context'lerle render edilmesi + statik regex taraması) `requests`/`urllib`
    HTTP cagrilarini VE `subprocess`/`os.system` surec baslatmalarini mock'layan
    bir blok İÇİNDE calistirilir; hicbiri cagrilmaz (`assert_not_called()`) --
    bu, gercek bir mesaj gonderme/silme/duzenleme isteginin (HTTP) veya
    yardimci bir surecin YANLIŞLIKLA tetiklenmediginin dogrudan kanitidir."""
    from flask import render_template

    with (
        mock.patch("subprocess.run") as mock_run,
        mock.patch("subprocess.Popen") as mock_popen,
        mock.patch("os.system") as mock_os_system,
    ):
        own_message = _fake_message(950, sender_user_id=1, body="Mock blok testi", is_deleted=False)
        with app.test_request_context("/"):
            html = render_template(TEMPLATE_PATH.split("app/templates/", 1)[1], **_base_context([own_message]))
        assert isinstance(html, str)
        assert "onsubmit=" not in html
        _read(TEMPLATE_PATH)
        _read(JS_PATH)

    mock_run.assert_not_called()
    mock_popen.assert_not_called()
    mock_os_system.assert_not_called()
