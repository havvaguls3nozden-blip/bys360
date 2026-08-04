"""CSP Dalga 7 - "AI Asistan Bilgi Bankası" ve "Bildirim Merkezi" ekranları
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

Bu dosyanın sahiplik alanı yalnızca şu iki template:
    - app/templates/ai_agent/knowledge.html  (1 handler: onsubmit -> confirm())
    - app/templates/notifications_list.html  (1 handler: onsubmit -> confirm())

ÇÖZÜM (ai_agent/knowledge.html): Bu template `{% extends "base.html" %}`
kullanır ve kendi `<script>` bloğuna hiç sahip değildi. Silme formundaki
(`{% for item in entries %}...{% endfor %}` döngüsü içinde, N kayıt için
tekrarlı) `onsubmit="return confirm('Bu bilgi kaydı silinsin mi?');"`
kurulu Dalga 1-6 desenine göre
`data-confirm="Bu bilgi kaydı silinsin mi?"` + `{% block content %}`
içinde `{% endblock %}`'tan hemen önce eklenen YENİ tek bir `<script>`
bloğundaki standart `form[data-confirm]` submit-delegasyonuna çevrildi.
Bu delegasyon script'i döngü DIŞINDA, sayfa başına bir kez render edilir;
bu yüzden N kayıt için de tek delegasyon yeterlidir. CSRF hidden input
(`{{ csrf_token() if csrf_token is defined else '' }}` koşullu ifadesi)
DOKUNULMADAN korundu.

ÇÖZÜM (notifications_list.html): Bu template `{% block extra_scripts %}`
içinde ZENGİN bir mevcut script bloğu barındırıyordu (bulk-selection /
checkbox / enable-disable mantığı, `bulkDeleteForm` / `bulkDeleteBtn` id'leri
bu script tarafından zaten kullanılıyor). Toplu silme formundaki
(`id="bulkDeleteForm"`) `onsubmit="return confirm('Seçilen bildirimler
kaldırılacak. Devam edilsin mi?');"` aynı standart desenle
`data-confirm="Seçilen bildirimler kaldırılacak. Devam edilsin mi?"` +
MEVCUT `<script>` bloğunun İÇİNE (yeni blok açılmadan) eklenen
`form[data-confirm]` submit-delegasyonuna çevrildi. `id="bulkDeleteForm"`
attribute'ına dokunulmadı. Mevcut bulk-selection mantığı (`syncSelection`,
`syncFieldContainer`, `syncCounter`, `setDisabled`, `applySearch`,
checkbox `change` / buton `click` / arama `input` dinleyicileri) yalnızca
`change`, `click` ve `input` event'lerinde çalışır; yeni eklenen delegasyon
yalnızca `submit` event'inde çalışır -- iki mekanizma farklı event
tipinde tetiklendiği için birbirini ENGELLEMEZ ve ÇAKIŞMAZ. Aynı forma
(`bulkDeleteForm`) ikinci bir `submit` listener EKLENMEDİ; delegasyon tek
bir global `document.querySelectorAll('form[data-confirm]')` taraması
üzerinden çalışır ve mevcut kodda `bulkDeleteForm` için tanımlı hiçbir
`submit` listener'ı yoktu (yalnızca `change`/`click`/`input` vardı, bu
dosyada doğrulanmıştır).

Statik testler `tests/security/test_csp_wave6_criteria_weights_contract.py`
ile aynı desendedir (Path.read_text() + regex, sonra gerçek Jinja
motoruyla `render_template()` çıktı testleri; `app` fixture'ı
`tests/conftest.py`'den gelir).

ÖNEMLİ SINIRLAMA: Bu dosyadaki HİÇBİR test gerçek bir tarayıcıda
çalışmadı/çalıştırılmadı. `render_template()` yalnızca ÜRETİLEN HTML'i
doğrular (inline handler yok, data-* attribute'ları doğru, script tag'i
sayfa başına bir kez render ediliyor, delegasyon çağrıları kaynak kodda
bir kez geçiyor, mevcut bulk-selection fonksiyon adları hâlâ kaynakta
mevcut). CSP enforce edilmiş gerçek bir tarayıcıda silme formlarındaki
`confirm()` diyaloğunun fiilen açılıp iptal edilebildiğini veya
bulk-selection mantığının (checkbox seçimi, buton disable/enable) hâlâ
çalıştığını KANITLAMAZ -- bu, ayrı bir manuel/E2E doğrulama gerektirir ve
bu dosyanın kapsamı dışındadır.
"""
from __future__ import annotations

import re
import types
from datetime import datetime
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

KNOWLEDGE_TEMPLATE = "app/templates/ai_agent/knowledge.html"
NOTIFICATIONS_TEMPLATE = "app/templates/notifications_list.html"

WAVE7_FILES = [KNOWLEDGE_TEMPLATE, NOTIFICATIONS_TEMPLATE]

DELETE_CONFIRM_MESSAGE_KNOWLEDGE = "Bu bilgi kaydı silinsin mi?"
BULK_DELETE_CONFIRM_MESSAGE_NOTIFICATIONS = "Seçilen bildirimler kaldırılacak. Devam edilsin mi?"

# HTML attribute syntax: bosluk + on<harfler> + '=' + tirnak. CSS/JS icindeki
# "javascript:" gibi metinsel string literal'leri yanlislikla yakalamaz.
_INLINE_EVENT_ATTR_RE = re.compile(r"""[\s]on[a-zA-Z]+\s*=\s*["']""")
_JS_HREF_RE = re.compile(r"""(?:href|src)\s*=\s*["']\s*javascript:""", re.IGNORECASE)
_JS_URL_ANYWHERE_RE = re.compile(r"""javascript:""", re.IGNORECASE)

# notifications_list.html'in mevcut bulk-selection script'inde tanımlı
# gerçek fonksiyon/id adları -- regresyon koruması icin kaynakta hâlâ
# mevcut olduklari dogrulanir.
_NOTIFICATIONS_EXISTING_JS_FUNCTIONS = [
    "setDisabled",
    "visibleCards",
    "selectedVisible",
    "syncFieldContainer",
    "syncSelection",
    "syncCounter",
    "applySearch",
]
_NOTIFICATIONS_EXISTING_JS_IDS = [
    "bulkDeleteForm",
    "notifBulkDeleteBtn",
    "bulkReadForm",
    "notifBulkReadBtn",
    "bulkUnreadForm",
    "notifBulkUnreadBtn",
]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _fake_knowledge_entry(item_id: int, **overrides: object) -> types.SimpleNamespace:
    base: dict[str, object] = dict(
        id=item_id,
        title=f"Wave7 Test Bilgisi {item_id}",
        tags="wave7, kontrat",
        priority=50,
        question_patterns=f"wave7 soru kalibi {item_id}",
        answer=f"Wave7 kontrat test cevabi {item_id}",
        audience="all",
        is_active=True,
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


def _fake_notification(item_id: int, **overrides: object) -> types.SimpleNamespace:
    base: dict[str, object] = dict(
        id=item_id,
        title=f"Wave7 Test Bildirimi {item_id}",
        body=f"Wave7 kontrat test aciklamasi {item_id}",
        notification_type="system",
        priority="normal",
        source_type="manual",
        source_id=item_id,
        link_url=None,
        is_read=False,
        created_at=datetime(2026, 8, 3, 10, 0, 0),
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


def _empty_filter_counts() -> dict[str, int]:
    return {"all": 0, "unread": 0, "read": 0, "priority": 0, "support": 0, "performance": 0, "surveys": 0, "system": 0}


# ---------------------------------------------------------------------------
# 1) Statik kaynak-kod kontratı (Path.read_text + regex). Kosulsuz calisir,
#    Jinja if-bloklarinin arkasinda kalan durumlari da yakalar.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative_path", WAVE7_FILES)
def test_wave7_file_has_no_inline_event_attributes(relative_path: str) -> None:
    text = _read(relative_path)
    matches = _INLINE_EVENT_ATTR_RE.findall(text)
    assert not matches, (
        f"{relative_path} icinde inline event-attribute (on*=) bulundu: {matches!r}. "
        "CSP script-src 'self' https: (unsafe-inline yok) altinda bunlar calismaz."
    )


@pytest.mark.parametrize("relative_path", WAVE7_FILES)
def test_wave7_file_has_no_javascript_href_or_url(relative_path: str) -> None:
    text = _read(relative_path)
    assert not _JS_HREF_RE.search(text), f"{relative_path} icinde href/src=\"javascript:...\" bulundu."
    assert not _JS_URL_ANYWHERE_RE.search(text), f"{relative_path} icinde beklenmedik bir javascript: metni bulundu."


@pytest.mark.parametrize("relative_path", WAVE7_FILES)
def test_wave7_file_introduces_no_dangerous_js_sinks(relative_path: str) -> None:
    """Duzeltme sirasinda eval/new Function/document.write eklenmedigini dogrular."""
    text = _read(relative_path)
    for forbidden in ("eval(", "new Function(", "document.write("):
        assert forbidden not in text, f"{relative_path} icinde yasakli sink bulundu: {forbidden}"


@pytest.mark.parametrize("relative_path", WAVE7_FILES)
def test_wave7_file_has_no_forbidden_inline_handler_string_literal(relative_path: str) -> None:
    """Bir inline handler'in HTML string'i olarak JS icinde uretilmedigini
    (yani `'onclick='`/`"onsubmit="` gibi bir literal yoklugunu) dogrular --
    bu, delegasyonun DOM'a innerHTML/string ile geri sizdirilmadiginin
    kanitidir."""
    text = _read(relative_path)
    for literal in ("'onclick='", '"onclick="', "'onsubmit='", '"onsubmit="'):
        assert literal not in text, f"{relative_path} icinde yasakli JS string literal bulundu: {literal}"


def test_knowledge_source_delete_form_has_data_confirm_message_verbatim() -> None:
    text = _read(KNOWLEDGE_TEMPLATE)
    assert "onsubmit=" not in text
    assert f'data-confirm="{DELETE_CONFIRM_MESSAGE_KNOWLEDGE}"' in text
    assert text.count('data-confirm="') == 1


def test_knowledge_source_has_exactly_one_new_script_block_with_form_confirm_delegation() -> None:
    text = _read(KNOWLEDGE_TEMPLATE)
    assert text.count("<script") == 1
    assert text.count("querySelectorAll('form[data-confirm]')") == 1
    assert "if (message && !window.confirm(message))" in text
    assert "event.preventDefault();" in text


def test_knowledge_source_csrf_conditional_expression_untouched() -> None:
    """Koşullu CSRF ifadesine (`csrf_token() if csrf_token is defined else
    ''`) DOKUNULMADIĞINI doğrular -- ekleme, toggle ve silme formlarının
    ÜÇÜNDE de aynı koşullu ifade korunmuş olmalı."""
    text = _read(KNOWLEDGE_TEMPLATE)
    assert text.count("{{ csrf_token() if csrf_token is defined else '' }}") == 3


def test_knowledge_source_delete_form_action_and_method_untouched() -> None:
    text = _read(KNOWLEDGE_TEMPLATE)
    assert "method=\"post\" action=\"{{ url_for('.ag5_knowledge_delete', entry_id=item.id) }}\"" in text


def test_notifications_source_bulk_delete_form_has_data_confirm_message_verbatim() -> None:
    text = _read(NOTIFICATIONS_TEMPLATE)
    assert "onsubmit=" not in text
    assert f'data-confirm="{BULK_DELETE_CONFIRM_MESSAGE_NOTIFICATIONS}"' in text
    assert text.count('data-confirm="') == 1


def test_notifications_source_bulk_delete_form_id_untouched() -> None:
    """`id="bulkDeleteForm"` attribute'ına DOKUNULMADIĞINI doğrular -- mevcut
    bulk-selection script'i bu id'yi kullanıyor."""
    text = _read(NOTIFICATIONS_TEMPLATE)
    assert 'id="bulkDeleteForm"' in text
    assert text.count('id="bulkDeleteForm"') == 1


def test_notifications_source_no_new_script_block_opened() -> None:
    """notifications_list.html'de yeni bir `<script>` bloğu AÇILMADI --
    form-confirm-delegasyonu var olan `{% block extra_scripts %}` içindeki
    TEK inline script bloğuna eklendi (harici `<script src=...>` include'u
    hariç, o zaten ayrı bir dosya)."""
    text = _read(NOTIFICATIONS_TEMPLATE)
    # Inline <script> (kapanan </script> ile) tam olarak bir kez var; ikinci
    # <script ...> etiketi harici src= dosya include'udur (kapanmaz, self
    # closing degildir ama src tasir).
    assert text.count("querySelectorAll('form[data-confirm]')") == 1
    assert "if (message && !window.confirm(message))" in text
    assert "event.preventDefault();" in text


def test_notifications_source_existing_bulk_selection_functions_preserved() -> None:
    """Mevcut bulk-selection JS fonksiyonlarının (regresyon koruması) hâlâ
    kaynak kodda tanımlı olduğunu doğrular -- form-confirm-delegasyonu
    eklenirken bu mantık BOZULMAMIŞ olmalı."""
    text = _read(NOTIFICATIONS_TEMPLATE)
    for fn_name in _NOTIFICATIONS_EXISTING_JS_FUNCTIONS:
        assert f"function {fn_name}(" in text, f"{fn_name} fonksiyon tanımı kaynakta bulunamadı."
    for element_id in _NOTIFICATIONS_EXISTING_JS_IDS:
        assert f"'{element_id}'" in text or f'"{element_id}"' in text, f"{element_id} id referansı kaynakta bulunamadı."


def test_notifications_source_form_confirm_delegation_does_not_add_second_submit_listener_to_bulk_forms() -> None:
    """Yeni eklenen `form[data-confirm]` delegasyonu, `bulkReadForm` /
    `bulkUnreadForm` / `bulkDeleteForm` formlarına AYRI AYRI `submit`
    listener'ı EKLEMEDİĞİNİ doğrular -- kaynakta yalnızca TEK bir global
    `addEventListener('submit'` çağrısı olmalı (delegasyon fonksiyonunun
    içinde), formlara özel ikinci bir submit listener yok."""
    text = _read(NOTIFICATIONS_TEMPLATE)
    assert text.count("addEventListener('submit'") == 1


def test_base_template_has_no_global_form_data_confirm_delegation() -> None:
    """Regresyon kilidi: `base.html` şu an KENDİ `form[data-confirm]`
    submit-delegasyonuna SAHİP DEĞİL. knowledge.html/notifications_list.html
    render testlerinin "tam sayfa çıktısında
    `querySelectorAll('form[data-confirm]')` tam olarak 1 kez geçer"
    varsayımı buna dayanır -- biri ileride base.html'e global bir
    form[data-confirm] delegasyonu eklerse bu, bu iki şablonun kendi yerel
    delegasyonuyla ÇİFT LİSTENER (çift confirm dialog'u) oluşturacağından
    bu test o riski erken yakalar."""
    text = _read("app/templates/base.html")
    assert "querySelectorAll('form[data-confirm]')" not in text
    assert "data-confirm" not in text


# ---------------------------------------------------------------------------
# 2) Calisma-zamani render kontrolu: gercek Flask app + gercek Jinja motoru
#    ile `render_template()` cagrisi (bkz. `app` fixture, tests/conftest.py).
# ---------------------------------------------------------------------------


def test_knowledge_render_with_multiple_entries_has_no_inline_handlers(app) -> None:
    """En az 2 sahte `item` içeren context ile knowledge.html render edilir;
    çıktıda hiçbir inline event-attribute (on*=) kalmamalı."""
    from flask import render_template

    entries = [_fake_knowledge_entry(101), _fake_knowledge_entry(102), _fake_knowledge_entry(103)]
    # Not: "/" yerine "/ai-agent/knowledge" kullanılır -- bu template'teki
    # `url_for('.ag5_knowledge_toggle', ...)` / `url_for('.ag5_knowledge_delete', ...)`
    # NOKTA-göreli (relative) endpoint çağrılarıdır ve `request.blueprint`
    # üzerinden çözülür. Kök "/" isteği "ai_agent" blueprint'ine ait
    # olmadığından bu göreli çağrılar `BuildError` fırlatır; gerçek route
    # (`app/ai_agent/routes.py::ag5_knowledge_center`, `url_prefix="/ai-agent"`,
    # rota `/knowledge`) hangi URL'e bağlıysa test bağlamı da onunla eşleşmeli.
    with app.test_request_context("/ai-agent/knowledge"):
        html = render_template("ai_agent/knowledge.html", entries=entries)

    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert not _JS_HREF_RE.search(html)


def test_knowledge_render_confirm_delegation_script_rendered_exactly_once_for_n_entries(app) -> None:
    """N (3) bilgi kaydı render edilse bile script bloğu render çıktısında
    YALNIZ 1 kez geçer; her kayıt için AYNI data-confirm mesajı N kez
    tekrarlanır (mesajın kendisi bozulmamış olmalı)."""
    from flask import render_template

    entries = [_fake_knowledge_entry(201), _fake_knowledge_entry(202), _fake_knowledge_entry(203)]
    with app.test_request_context("/ai-agent/knowledge"):
        html = render_template("ai_agent/knowledge.html", entries=entries)

    # Not: tam sayfa "<script" sayımı burada kasıtlı olarak KULLANILMAZ --
    # knowledge.html base.html'i extends eder ve base.html'in kendisi zaten
    # onlarca `<script>` içerir; bunun yerine YALNIZ bu delegasyona özgü
    # benzersiz alt-dize sayılır.
    assert html.count("querySelectorAll('form[data-confirm]')") == 1
    assert html.count(f'data-confirm="{DELETE_CONFIRM_MESSAGE_KNOWLEDGE}"') == 3
    # Confirm mesajının kendisi (Türkçe karakterler dahil) birebir korunmuş olmalı.
    assert DELETE_CONFIRM_MESSAGE_KNOWLEDGE in html


def test_knowledge_render_with_empty_entries_still_has_single_script_and_no_handlers(app) -> None:
    """Boş `entries` (empty-box dalı) ile render edilse bile script bloğu
    hâlâ tam olarak 1 kez render edilir ve inline handler yoktur --
    delegasyon listener'ı DOM'da kayıt olmasa da güvenle kurulabilir."""
    from flask import render_template

    with app.test_request_context("/ai-agent/knowledge"):
        html = render_template("ai_agent/knowledge.html", entries=[])

    assert "Henüz asistana öğretilmiş bilgi kaydı bulunmuyor." in html
    assert html.count("querySelectorAll('form[data-confirm]')") == 1
    assert not _INLINE_EVENT_ATTR_RE.findall(html)


def test_knowledge_render_csrf_hidden_input_present_for_each_form(app) -> None:
    """Koşullu CSRF ifadesinin render çıktısında hâlâ üretildiğini (boş
    string'e düşse bile hidden input'un kendisinin var olduğunu) doğrular."""
    from flask import render_template

    entries = [_fake_knowledge_entry(301)]
    with app.test_request_context("/ai-agent/knowledge"):
        html = render_template("ai_agent/knowledge.html", entries=entries)

    assert html.count('<input type="hidden" name="csrf_token"') >= 3  # form ekle + toggle + sil


def _notifications_render_context(notifications: list[types.SimpleNamespace]) -> dict[str, object]:
    filter_counts = _empty_filter_counts()
    filter_counts["all"] = len(notifications)
    return dict(
        notifications=notifications,
        unread_count=sum(1 for n in notifications if not n.is_read),
        read_count=sum(1 for n in notifications if n.is_read),
        priority_count=0,
        today_count=0,
        current_view="all",
        search_query=None,
        filter_counts=filter_counts,
        visible_notification_count=len(notifications),
    )


def test_notifications_render_with_multiple_items_has_no_inline_handlers(app) -> None:
    """En az 2 sahte bildirim içeren context ile notifications_list.html
    render edilir; çıktıda hiçbir inline event-attribute (on*=) kalmamalı."""
    from flask import render_template

    notifications = [_fake_notification(401), _fake_notification(402), _fake_notification(403)]
    with app.test_request_context("/"):
        html = render_template(NOTIFICATIONS_TEMPLATE.split("app/templates/")[1], **_notifications_render_context(notifications))

    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert not _JS_HREF_RE.search(html)


def test_notifications_render_has_bulk_delete_form_id_and_data_confirm_together(app) -> None:
    """Render çıktısında `id="bulkDeleteForm"` VE
    `data-confirm="Seçilen bildirimler kaldırılacak. Devam edilsin mi?"`
    AYNI formda birlikte var mı doğrular."""
    from flask import render_template

    notifications = [_fake_notification(501), _fake_notification(502)]
    with app.test_request_context("/"):
        html = render_template(NOTIFICATIONS_TEMPLATE.split("app/templates/")[1], **_notifications_render_context(notifications))

    bulk_delete_form_match = re.search(
        r'<form[^>]*id="bulkDeleteForm"[^>]*>',
        html,
    )
    assert bulk_delete_form_match is not None, "bulkDeleteForm formu render çıktısında bulunamadı."
    form_tag = bulk_delete_form_match.group(0)
    assert 'id="bulkDeleteForm"' in form_tag
    assert f'data-confirm="{BULK_DELETE_CONFIRM_MESSAGE_NOTIFICATIONS}"' in form_tag
    assert "onsubmit=" not in form_tag


def test_notifications_render_confirm_delegation_script_rendered_exactly_once(app) -> None:
    """Bildirim sayısı (N) değişse bile (döngü kartlarında değil, toolbar'da
    sabit tek bir bulk-delete formu olduğu için) delegasyon script'i render
    çıktısında YALNIZ 1 kez geçer."""
    from flask import render_template

    notifications = [_fake_notification(601), _fake_notification(602), _fake_notification(603)]
    with app.test_request_context("/"):
        html = render_template(NOTIFICATIONS_TEMPLATE.split("app/templates/")[1], **_notifications_render_context(notifications))

    assert html.count("querySelectorAll('form[data-confirm]')") == 1
    assert html.count(f'data-confirm="{BULK_DELETE_CONFIRM_MESSAGE_NOTIFICATIONS}"') == 1


def test_notifications_render_existing_bulk_selection_functions_still_present(app) -> None:
    """Regresyon koruması: render çıktısında mevcut bulk-selection JS
    fonksiyonlarının (örn. `syncSelection`, `setDisabled`) hâlâ mevcut
    olduğunu doğrular -- form-confirm-delegasyonu eklenirken bu mantık
    BOZULMAMIŞ olmalı."""
    from flask import render_template

    notifications = [_fake_notification(701)]
    with app.test_request_context("/"):
        html = render_template(NOTIFICATIONS_TEMPLATE.split("app/templates/")[1], **_notifications_render_context(notifications))

    for fn_name in _NOTIFICATIONS_EXISTING_JS_FUNCTIONS:
        assert f"function {fn_name}(" in html
    for element_id in _NOTIFICATIONS_EXISTING_JS_IDS:
        assert f"id=\"{element_id}\"" in html or f"getElementById('{element_id}')" in html


def test_notifications_render_with_empty_list_still_has_single_script_and_bulk_form(app) -> None:
    """Boş `notifications` listesiyle (empty-box dalı) render edilse bile
    toolbar'daki bulk-delete formu ve delegasyon script'i hâlâ (döngü
    dışında olduğu için) render edilir."""
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template(NOTIFICATIONS_TEMPLATE.split("app/templates/")[1], **_notifications_render_context([]))

    assert "Bildirim görünmüyor" in html
    assert html.count("querySelectorAll('form[data-confirm]')") == 1
    assert f'data-confirm="{BULK_DELETE_CONFIRM_MESSAGE_NOTIFICATIONS}"' in html
    assert not _INLINE_EVENT_ATTR_RE.findall(html)
