"""CSP Dalga 4 - Admin ekranlari kontrat testi.

BYS360 `app/security/headers.py` uygular:
    script-src: 'self' https:  (unsafe-inline YOK)

`app/security/headers.py::inject_csp_nonce_into_html` yaniti donduren HER
`<script>` etiketine (nonce'u olmayanlara) otomatik `nonce="..."` ekler; bu
merkezi mekanizma sayesinde template icindeki `<script>...</script>` bloklari
zaten CSP ile uyumludur ve nonce hicbir zaman elle template'e yazilmaz. Asil
risk inline EVENT ATTRIBUTE'lardi (`onclick=`, `onchange=`, `onerror=`,
`onsubmit=` vb.) -- bunlara nonce uygulanmaz ve enforce modda tarayici
tarafindan calistirilmazlar.

Bu dosyanin sahiplik alani yalnizca su alti admin template'i:
    - app/templates/admin/role_matrix_center.html   (1x onclick -> window.print())
    - app/templates/admin_users.html                 (1x onerror -> avatar fallback)
    - app/templates/admin_ai_settings.html            (3x onclick -> confirm())
    - app/templates/admin_ai_review_queue.html        (1x onclick -> "tumunu sec")
    - app/templates/admin_user_edit.html              (2x onerror -> avatar fallback)
    - app/templates/excel_import.html                 (2x onclick -> hidden input set)

Koordinatorun envanteri toplam 10 inline event-attribute tespit etmisti;
`javascript:` URL yoktu. Bu dosya o tespiti once bagimsiz statik regex
taramasiyla (kaynak metin), sonra da mumkun oldugunca gercek Jinja/Flask
motoruyla uretilen HTML uzerinde kilitler.

AVATAR FALLBACK KARARI (onemli sapma notu):
`admin_users.html` ve `admin_user_edit.html` icin koordinator talimati
her img icin YENI, dosyaya ozel bir `querySelectorAll('img[data-fallback-src]')`
scripti eklenmesini oneriyordu. Inceleme sirasinda `app/templates/base.html`
icinde (satir ~821-826) ZATEN KURULU, global bir `img[data-fallback-src]`
'error' dinleyicisi bulundu -- bu tam olarak ayni deseni Wave 2'de
`personnel_edit.html` ve `personnel_profile.html` icin cozmus olan, once
merge edilmis mekanizmadir (bkz. `tests/security/test_csp_wave2_personnel_inline_handlers_contract.py`
docstring'i). Bu iki dosya da SADECE `data-fallback-src` attribute'u ekler,
KENDI script'lerini YAZMAZ. Bu iki admin template'i de `base.html`'i
extends eder ve img'leri `{% block content %}` icinde (global script'ten
ONCE, DOM sirasina gore) render edilir; bu yuzden aradaki kod tekrarini
onlemek ve "ayni islevi goren ikinci bir listener baglama" riskinden
kacinmak icin BU IKI DOSYADA YENI SCRIPT EKLENMEDI, sadece
`onerror="..."` -> `data-fallback-src="..."` donusumu yapildi ve mevcut
global dinleyiciye guvenildi. Asagidaki testler bu kararin dogru
calistigini hem statik (data-fallback-src var, onerror yok, yeni bir
`img[data-fallback-src]` sorgusu bu iki dosyada YOK) hem de gercek render
(base.html'in global scriptinin render ciktisina gercekten dahil oldugu)
seviyesinde kilitler.

Diger 4 dosyada (`role_matrix_center.html`, `admin_ai_settings.html`,
`admin_ai_review_queue.html`, `excel_import.html`) boyle bir global kanca
olmadigi icin koordinatorun talimatina birebir uyulmustur: dosyaya ozel
id + addEventListener + (varsa) data-confirm deseni.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

ROLE_MATRIX_TEMPLATE = "app/templates/admin/role_matrix_center.html"
ADMIN_USERS_TEMPLATE = "app/templates/admin_users.html"
AI_SETTINGS_TEMPLATE = "app/templates/admin_ai_settings.html"
AI_REVIEW_QUEUE_TEMPLATE = "app/templates/admin_ai_review_queue.html"
ADMIN_USER_EDIT_TEMPLATE = "app/templates/admin_user_edit.html"
EXCEL_IMPORT_TEMPLATE = "app/templates/excel_import.html"

WAVE4_ADMIN_FILES = [
    ROLE_MATRIX_TEMPLATE,
    ADMIN_USERS_TEMPLATE,
    AI_SETTINGS_TEMPLATE,
    AI_REVIEW_QUEUE_TEMPLATE,
    ADMIN_USER_EDIT_TEMPLATE,
    EXCEL_IMPORT_TEMPLATE,
]

# HTML attribute syntax: bosluk + on<harfler> + '=' + tirnak. CSS/JS icindeki
# "javascript:" gibi metinsel string literal'leri yanlislikla yakalamaz.
_INLINE_EVENT_ATTR_RE = re.compile(r"""[\s]on[a-zA-Z]+\s*=\s*["']""")
_JS_HREF_RE = re.compile(r"""(?:href|src)\s*=\s*["']\s*javascript:""", re.IGNORECASE)
_JS_URL_ANYWHERE_RE = re.compile(r"""javascript:""", re.IGNORECASE)


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1) Statik kaynak-kod kontrati (Path.read_text + regex). Kosulsuz calisir,
#    Jinja if-bloklarinin arkasinda kalan durumlari da yakalar.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("relative_path", WAVE4_ADMIN_FILES)
def test_admin_file_has_no_inline_event_attributes(relative_path: str) -> None:
    text = _read(relative_path)
    matches = _INLINE_EVENT_ATTR_RE.findall(text)
    assert not matches, (
        f"{relative_path} icinde inline event-attribute (on*=) bulundu: {matches!r}. "
        "CSP script-src 'self' https: (unsafe-inline yok) altinda bunlar calismaz; "
        "data-* attribute + addEventListener kalibina cevrilmeli."
    )


@pytest.mark.parametrize("relative_path", WAVE4_ADMIN_FILES)
def test_admin_file_has_no_javascript_href_or_url(relative_path: str) -> None:
    text = _read(relative_path)
    assert not _JS_HREF_RE.search(text), (
        f"{relative_path} icinde href/src=\"javascript:...\" bulundu."
    )
    assert not _JS_URL_ANYWHERE_RE.search(text), (
        f"{relative_path} icinde beklenmedik bir javascript: metni bulundu."
    )


@pytest.mark.parametrize("relative_path", WAVE4_ADMIN_FILES)
def test_admin_file_introduces_no_dangerous_js_sinks(relative_path: str) -> None:
    """Duzeltme sirasinda eval/new Function/document.write eklenmedigini dogrular."""
    text = _read(relative_path)
    for forbidden in ("eval(", "new Function(", "document.write("):
        assert forbidden not in text, f"{relative_path} icinde yasakli sink bulundu: {forbidden}"


def test_role_matrix_center_print_button_uses_id_and_click_listener() -> None:
    text = _read(ROLE_MATRIX_TEMPLATE)
    assert "onclick=" not in text
    assert 'id="rmPrintButton"' in text
    assert "getElementById('rmPrintButton')" in text
    assert "addEventListener('click'" in text
    assert "window.print()" in text


def test_admin_users_avatar_uses_data_fallback_src_and_no_local_script() -> None:
    text = _read(ADMIN_USERS_TEMPLATE)
    assert "onerror=" not in text
    assert 'data-fallback-src="{{ url_for(\'static\', filename=\'img/default-avatar.svg\') }}"' in text
    # Kasitli tasarim karari: bu dosya base.html'in global img[data-fallback-src]
    # dinleyicisine guvenir, kendi ikinci bir kopyasini eklemez (bkz. dosya
    # basligindaki "AVATAR FALLBACK KARARI" notu).
    assert "querySelectorAll('img[data-fallback-src]')" not in text
    assert "<script>" not in text


def test_admin_ai_settings_three_confirm_messages_preserved_exactly() -> None:
    text = _read(AI_SETTINGS_TEMPLATE)
    assert "onclick=" not in text
    assert text.count('data-confirm="Bu kayıt dosyası kaydı silinsin mi?"') == 2
    assert 'data-confirm="Bu kayıt dosyası kaydı silinsin mi? Yerleşik kayıt varsa ekran varsayılana döner."' in text
    assert text.count("data-confirm=") == 3
    assert "querySelectorAll('button[data-confirm]')" in text
    assert "addEventListener('click'" in text
    assert "if (message && !window.confirm(message))" in text
    assert "event.preventDefault();" in text


def test_admin_ai_review_queue_select_all_uses_id_and_change_listener() -> None:
    text = _read(AI_REVIEW_QUEUE_TEMPLATE)
    assert "onclick=" not in text
    assert 'id="recCheckAll"' in text
    assert "getElementById('recCheckAll')" in text
    assert "addEventListener('change'" in text
    assert "querySelectorAll('.rec-check')" in text


def test_admin_user_edit_avatars_use_data_fallback_src_and_no_new_fallback_script() -> None:
    text = _read(ADMIN_USER_EDIT_TEMPLATE)
    assert "onerror=" not in text
    assert text.count("data-fallback-src=") == 2
    assert 'id="profileMainPreview"' in text
    assert 'id="avatarPreview"' in text
    # Ayni sapma karari: yeni bir img[data-fallback-src] scripti EKLENMEDI,
    # base.html'in global dinleyicisine guvenilir. Dosyanin ZATEN VAR OLAN
    # `extra_scripts` blogundaki foto onizleme (FileReader) mantigi korunur.
    assert "querySelectorAll('img[data-fallback-src]')" not in text
    assert 'getElementById("profile_photo")' in text
    assert "{% block extra_scripts %}" in text


def test_excel_import_buttons_use_ids_and_click_listeners_no_preventdefault() -> None:
    text = _read(EXCEL_IMPORT_TEMPLATE)
    assert "onclick=" not in text
    assert 'id="excelQuickApplyBtn"' in text
    assert 'id="excelStandardApplyBtn"' in text
    assert "getElementById('excelQuickApplyBtn')" in text
    assert "getElementById('excelStandardApplyBtn')" in text
    assert text.count("addEventListener('click'") == 2
    assert "field.value = '1'" in text
    assert "field.value = '0'" in text
    # Bu iki buton normal form submit akisini KESMEMELI (preventDefault yok).
    assert "preventDefault" not in text


# ---------------------------------------------------------------------------
# 2) Calisma-zamani render kontrolu: gercek Flask app + gercek Jinja motoru
#    ile `render_template()` cagrisi (bkz. `app` fixture, tests/conftest.py).
#    Mumkun olan her yerde route'un GERCEK context-uretici servis
#    fonksiyonlari dogrudan cagrilir (route'un kendisi degil -- login_required/
#    admin_required/menu_key_required zincirini bu kontrat dosyasinda yeniden
#    kurmak kapsam disidir, tipki Wave 2/3 emsalinde oldugu gibi). Bu servis
#    fonksiyonlari DB'ye ihtiyac duysa da (orn. AIRecommendation sorgusu) `app`
#    fixture'i zaten bos bir sqlite semasi kurar (`db.create_all()`), bu yuzden
#    gercek sorgular guvenle 0 satir donerek calisir -- context TAMAMEN
#    elle uydurulmus degildir.
#
#    `admin_users.html` ve `admin_user_edit.html` icin route'un kendisi
#    (`app/admin/routes.py`) User.query / OrganizationUnit.query gibi ek
#    modeller ve `apply_admin_user_org_hierarchy_fields` gibi is mantigini
#    bir araya getiriyor; bunu burada yeniden kurmak bu kontratin kapsamini
#    asar, bu yuzden bu iki dosya icin route'un gecirdigi ayni anahtar
#    isimleriyle KUCUK/GUVENLI (bos liste / None) bir context elle
#    kurulmustur -- bu hala gercek Jinja derleme+yurutmedir, sadece veri
#    kaynagi DB yerine testin kendisidir.
# ---------------------------------------------------------------------------


def test_role_matrix_center_render_uses_real_service_context(app) -> None:
    """role_matrix_ui_service.build_role_matrix_ui_context DB/auth kullanmayan
    saf bir fonksiyon oldugu icin route'un GERCEK context'i burada birebir
    uretilebilir (bkz. app/admin/role_matrix_routes.py)."""
    from flask import render_template

    from app.services.role_matrix_ui_service import build_role_matrix_ui_context

    with app.test_request_context("/"):
        context = build_role_matrix_ui_context("tum")
        html = render_template("admin/role_matrix_center.html", **context)

    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert not _JS_HREF_RE.search(html)
    assert 'id="rmPrintButton"' in html
    assert "getElementById('rmPrintButton')" in html
    assert "window.print()" in html


def test_admin_ai_settings_render_uses_real_service_context(app) -> None:
    """build_ai_settings_snapshot / get_prompt_registry_editor_snapshot dosya
    tabanli kayit registry'sini okur, DB gerektirmez (bkz.
    app/admin/ai_phase2_routes.py::admin_ai_settings icin ayni cagrilar)."""
    from flask import render_template

    from app.services.ai.prompts import get_prompt_registry_editor_snapshot
    from app.services.ai.settings import build_ai_settings_snapshot

    with app.test_request_context("/"):
        snapshot = build_ai_settings_snapshot()
        editor = get_prompt_registry_editor_snapshot("", "")
        html = render_template(
            "admin_ai_settings.html",
            snapshot=snapshot,
            provider=snapshot.get("provider") or {},
            prompt_rows=snapshot.get("prompt_rows") or [],
            prompt_meta=snapshot.get("prompt_meta") or {},
            allowed_roles=snapshot.get("allowed_roles") or [],
            env_rows=snapshot.get("env_rows") or [],
            actions=snapshot.get("actions") or [],
            editor=editor,
            selected_label="Yeni kayıt",
            module_options=[],
            feature_options=[],
        )

    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert not _JS_HREF_RE.search(html)
    # Not: gercek registry dosyasindaki kayit sayisi ortama gore degisebilir,
    # bu yuzden burada TAM sayim degil VARLIK dogrulanir (tam sayim -- 3
    # data-confirm, ikisi ayni metin -- statik kaynak testinde yukarida
    # kosulsuz olarak zaten kilitlidir).
    assert 'data-confirm="Bu kayıt dosyası kaydı silinsin mi?"' in html
    assert 'data-confirm="Bu kayıt dosyası kaydı silinsin mi? Yerleşik kayıt varsa ekran varsayılana döner."' in html
    assert "querySelectorAll('button[data-confirm]')" in html


def test_admin_ai_review_queue_render_uses_real_db_backed_snapshot(app) -> None:
    """build_review_queue_snapshot AIRecommendation.query kullanir; `app`
    fixture'i bos bir sqlite semasi kurdugu icin bu gercek bir DB sorgusudur
    (0 satir doner), route'un login/menu-key zincirinden bagimsiz olarak."""
    from flask import render_template

    from app.services.ai.admin_queue import build_review_queue_snapshot

    with app.test_request_context("/"):
        snapshot = build_review_queue_snapshot(
            module_type="",
            target_table="",
            status="open",
            severity="",
            page=1,
            per_page=20,
        )
        html = render_template("admin_ai_review_queue.html", **snapshot)

    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert not _JS_HREF_RE.search(html)
    assert 'id="recCheckAll"' in html
    assert "getElementById('recCheckAll')" in html


def test_admin_users_render_with_minimal_safe_context(app) -> None:
    """admin_users.html'in for-donguleri (role_options, birim_options,
    ust_birim_options) Jinja `|default`/`is defined` korumasi ICERMIYOR --
    bu yuzden bos context'le render `UndefinedError` firlatir (route'un
    gecirdigi anahtarlar zorunludur). Route'un kendisi User.query +
    OrganizationUnit.query + is mantigi kurar; bunu burada yeniden kurmak
    kapsam disi oldugu icin ayni anahtar isimleriyle KUCUK/GUVENLI (bos
    liste) bir context elle kurulur -- yine de gercek Jinja derleme+yurutme
    kullanilir."""
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template(
            "admin_users.html",
            users=[],
            role_options=[],
            birim_options=[],
            ust_birim_options=[],
            manager_candidates=[],
            grouped_by_unit={},
            grouped_by_manager={},
            total_count=0,
            active_count=0,
            passive_count=0,
            ai_admin_users_panel=None,
        )

    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert not _JS_HREF_RE.search(html)
    # base.html'in KENDI global dinleyicisi (tek sayim) render ciktisinda
    # bulunur -- ama admin_users.html BUNUN UZERINE ikinci bir kopya
    # EKLEMEMELI (aksi halde ayni img icin cift baglama olur).
    assert html.count("querySelectorAll('img[data-fallback-src]')") == 1


def test_admin_user_edit_render_with_minimal_safe_context(app) -> None:
    """admin_user_edit.html icin de ayni gerekce: role_choices,
    manager_candidates gibi for-dongusu degiskenleri bos context'te
    UndefinedError firlatir; route'un ROLE_CHOICES / User.query /
    get_personnel_category_options cagrilarini burada yeniden kurmak yerine
    ayni anahtar isimleriyle guvenli bos degerler verilir."""
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template(
            "admin_user_edit.html",
            user_obj=None,
            unit_name_options=[],
            parent_unit_options=[],
            manager_candidates=[],
            role_choices=[],
            personnel_category_options=[],
            current_personnel_category="Diğer",
            ai_user_form_panel=None,
        )

    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert not _JS_HREF_RE.search(html)
    assert 'id="profileMainPreview"' in html
    assert 'id="avatarPreview"' in html
    # Ayni gerekce: base.html'in tek global dinleyicisi disinda ikinci bir
    # kopya EKLENMEMIS olmali.
    assert html.count("querySelectorAll('img[data-fallback-src]')") == 1


def test_excel_import_render_with_truly_empty_context(app) -> None:
    """excel_import.html'deki tum for-donguleri/degiskenler (errors,
    ai_excel_fix_panel, apply_ai_fixes) Jinja `{% if %}` korumasi ile
    yazilmis -- bu template GERCEKTEN bos context'le (route'a hic
    dokunmadan) render edilebilen tek Wave 4 dosyasidir."""
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template("excel_import.html")

    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert not _JS_HREF_RE.search(html)
    assert 'id="excelQuickApplyBtn"' in html
    assert 'id="excelStandardApplyBtn"' in html
    assert "getElementById('excelQuickApplyBtn')" in html
    assert "getElementById('excelStandardApplyBtn')" in html


def test_base_template_still_owns_global_avatar_fallback_listener() -> None:
    """Regresyon kilidi: admin_users.html / admin_user_edit.html kararlari
    base.html'in bu global dinleyiciyi KORUDUGUNA bagimlidir. Biri bunu
    base.html'den kaldirirsa bu iki admin ekranindaki avatar fallback'i
    sessizce kirilir -- bu test o baglantiyi acikca kilitler."""
    text = _read("app/templates/base.html")
    assert "querySelectorAll('img[data-fallback-src]')" in text
    assert "addEventListener('error'" in text
