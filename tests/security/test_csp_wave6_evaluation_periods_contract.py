"""CSP strict migration -- Wave 6 (evaluation_form.html / periods.html / period_edit.html)
contract test.

`app/security/headers.py` script-src varsayilani `'self' https:` -- unsafe-inline
YOK. `app/bootstrap/response_hardening.py` + `app/security/headers.py::
inject_csp_nonce_into_html`, nonce'u olmayan HER `<script>` etiketine otomatik
`nonce="..."` ekler; bu yuzden dosya-ici `<script>...</script>` bloklari zaten
korunuyor. Asil risk inline EVENT ATTRIBUTE'lardi (`onclick=`, `onsubmit=`,
`onerror=`) -- CSP script-src nonce/host tabanli oldugu icin bunlara nonce
uygulanmaz ve enforce modda tarayici tarafindan calistirilmazlar.

Bu dosya, Wave 6 kapsamindaki 3 dosyada bu deseni kaldirdigini dogrular:

  - `app/templates/period_edit.html`: 1 inline `onerror=` (ÇATAB logo
    fallback'i) -> `data-fallback-src="..."`. YENI SCRIPT EKLENMEDI: dosya
    `{% extends "base.html" %}` kullanir ve icerigi `{% block content %}`
    icinde render edilir; base.html'in ZATEN VAR OLAN
    `document.querySelectorAll('img[data-fallback-src]').forEach(...)`
    global delegasyonu (Wave 1/2/4'te kurulmus, `base.html` satir ~821)
    bunu otomatik kapsar (bkz. `test_csp_wave2_personnel_inline_handlers_
    contract.py`'deki ayni desen, personnel_edit.html icin).
  - `app/templates/periods.html`: 1 inline `onsubmit="return confirm(...)"`
    (dönem silme formu, cok uzun/kritik bir uyari mesaji) ->
    `data-confirm="..."` (mesaj harfiyen korunur) + kurulu Wave 1-5
    desenindeki standart `form[data-confirm]` submit-delegasyon script'i
    (dosyada onceden HİÇ script yoktu, bu yuzden `{% block content %}`
    icinde YENI bir `<script>` acildi -- tam olarak 1 adet).
  - `app/templates/evaluation_form.html`: 2 inline handler turu (5x
    `onclick="applyBulkScore(N)"` toplu puan butonlari + 1x
    `onclick="clearBulkScores()"` temizleme butonu) -> `data-bulk-value="N"`
    / `id="clearBulkScoresBtn"` + MEVCUT `<script>` IIFE'sinin ICINE
    eklenen `querySelectorAll('[data-bulk-value]')` / `getElementById(
    'clearBulkScoresBtn')` kablolamasi. `applyBulkScore`/`clearBulkScores`
    fonksiyon TANIMLARI (script'in ic kapsaminda, `(function () { ... })();`
    IIFE'si icinde) DEGISTIRILMEDI -- sadece cagrildiklari yer inline
    attribute'tan addEventListener'a tasindi. Yeni kablolama kodu AYNI
    IIFE kapsaminin ICINDE eklendigi icin (fonksiyon tanimlariyla ayni
    closure'da), bu ayrica onceden var olan bir kapsam sorununu da
    (IIFE-local fonksiyonlarin global onclick'ten hic erisilemez olmasi
    riskini) yan etki olarak ortadan kaldirir.

Bu dosyanin sahiplik alani SADECE testtir -- yukaridaki 3 sablon dosyasi
Wave 6 kapsaminda AYRICA elle duzenlendi (bu ajanin gorevinin bir parcasi
olarak, coordinator talimatiyla); `base.html`'e SADECE salt-okunur regresyon
kontrolu icin bakilir (degistirilmez, Wave 1/2/4'un sahiplik alaninda).

Statik testler `tests/security/test_csp_wave2_personnel_inline_handlers_
contract.py` ve `tests/security/test_csp_wave5_portal_postcard_delegation_
contract.py` ile ayni desendedir (Path.read_text() + regex, sonra gercek
Jinja motoruyla `render_template()` cikti testleri; `app` fixture'i
`tests/conftest.py`'den gelir, session-scoped, `db.create_all()` cagirir).

Render testleri gercek route/login akisina GIRMEZ (Wave5 ile ayni tercih):
`period_edit.html` / `periods.html` / `evaluation_form.html` route'lari
(bkz. `app/performance/admin_core_routes.py::performance_period_edit`,
`performance_periods`; `app/performance/evaluation_core_routes.py` zinciri)
agir DB/servis katmani gerektirir. Bunun yerine `types.SimpleNamespace`
sahte context nesneleriyle DOGRUDAN `render_template()` cagrilir -- bu app
`app/template_safety.py` icinde `app.jinja_env.undefined = ChainableUndefined`
ayarladigi icin (bkz. Wave4/Wave5 docstring'leri ile ayni not) context'te
saglanmayan degiskenlere zincirlenmis erisim hata firlatmaz.

ÖNEMLİ SINIRLAMA: Bu dosyadaki HİÇBİR test gerçek bir tarayıcıda çalışmaz.
`render_template()` yalnızca ÜRETİLEN HTML'i doğrular (inline handler yok,
data-* attribute'ları doğru, script tag'i beklenen sayida, delegasyon
kodu render ciktisinda mevcut). CSP enforce edilmiş gerçek bir tarayıcıda
confirm dialog'unun fiilen açılıp iptal edilebildiğini, toplu puan
butonlarının fiilen tıklanabildiğini veya img fallback'inin fiilen
tetiklendiğini KANITLAMAZ -- bu ayrı bir manuel/E2E doğrulama gerektirir
ve bu dosyanın kapsamı dışındadır (rapor metninde ayrıca not edilir).
"""
from __future__ import annotations

import datetime
import re
import types
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

PERIOD_EDIT_TEMPLATE = "app/templates/period_edit.html"
PERIODS_TEMPLATE = "app/templates/periods.html"
EVALUATION_FORM_TEMPLATE = "app/templates/evaluation_form.html"
BASE_TEMPLATE = "app/templates/base.html"

WAVE6_TEMPLATES = [PERIOD_EDIT_TEMPLATE, PERIODS_TEMPLATE, EVALUATION_FORM_TEMPLATE]

# HTML attribute syntax: bosluk + on<harfler> + '=' + tirnak. CSS/JS icindeki
# metinsel string literal'leri yanlislikla yakalamaz (Wave1/2/4/5 ile ayni desen).
_INLINE_EVENT_ATTR_RE = re.compile(r"""[\s]on[a-zA-Z]+\s*=\s*["']""")
_JS_HREF_RE = re.compile(r"""(?:href|src)\s*=\s*["']\s*javascript:""", re.IGNORECASE)

PERIOD_DELETE_CONFIRM_MESSAGE = (
    "Bu dönem; görevleri, puanları, karne/snapshot kayıtları, Başkan onayı "
    "ve diğer dönem bağlantılarıyla birlikte silinecek. Devam edilsin mi?"
)


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1) Statik kaynak-kod kontratlari -- inline event-attribute / javascript:
#    href / tehlikeli JS sink kalmadigini dogrular (3 dosyanin tumu icin).
# ---------------------------------------------------------------------------


def test_wave6_templates_have_no_inline_event_attributes() -> None:
    for relative_path in WAVE6_TEMPLATES:
        text = _read(relative_path)
        matches = _INLINE_EVENT_ATTR_RE.findall(text)
        assert not matches, (
            f"{relative_path} icinde inline event-attribute (on*=) bulundu: {matches!r}. "
            "CSP script-src 'self' https: (unsafe-inline yok) altinda bunlar calismaz."
        )


def test_wave6_templates_have_no_javascript_url_anywhere() -> None:
    for relative_path in WAVE6_TEMPLATES:
        text = _read(relative_path)
        assert "javascript:" not in text.lower(), f"{relative_path} icinde javascript: bulundu."


def test_wave6_templates_have_no_javascript_href() -> None:
    for relative_path in WAVE6_TEMPLATES:
        text = _read(relative_path)
        matches = _JS_HREF_RE.findall(text)
        assert not matches, f"{relative_path} icinde href/src=\"javascript:...\" bulundu: {matches!r}."


def test_wave6_templates_introduce_no_dangerous_js_sinks() -> None:
    for relative_path in WAVE6_TEMPLATES:
        text = _read(relative_path)
        for forbidden in ("eval(", "new Function(", "document.write("):
            assert forbidden not in text, f"{relative_path} icinde yasakli sink bulundu: {forbidden}"


def test_wave6_templates_have_no_duplicate_listener_on_same_event() -> None:
    """Ayni event turune (submit/click) her formda/butonda YALNIZCA bir kez
    addEventListener baglanmali -- coordinator'in kesin yasagi (cift listener)."""
    periods_text = _read(PERIODS_TEMPLATE)
    assert periods_text.count("addEventListener('submit'") == 1
    eval_text = _read(EVALUATION_FORM_TEMPLATE)
    # 1 adet click-delegasyonu (data-bulk-value butonlari) + 1 adet click-delegasyonu
    # (clearBulkScoresBtn) + mevcut (Wave6 oncesi) radio 'change' delegasyonu.
    assert eval_text.count("addEventListener('click'") == 2


# ---------------------------------------------------------------------------
# 2) period_edit.html -- base.html kisayolu (YENI SCRIPT YOK) kontrati
# ---------------------------------------------------------------------------


def test_period_edit_avatar_uses_data_fallback_src_not_onerror() -> None:
    text = _read(PERIOD_EDIT_TEMPLATE)
    assert "onerror=" not in text
    assert 'data-fallback-src="' in text
    assert text.count('data-fallback-src="') == 1


def test_period_edit_introduces_no_new_script_tag() -> None:
    """Koordinator talimati: base.html'in global delegasyonu kullanildigi
    icin period_edit.html'e YENI bir <script> blogu EKLENMEMELI (0 adet)."""
    text = _read(PERIOD_EDIT_TEMPLATE)
    assert text.count("<script") == 0, (
        f"{PERIOD_EDIT_TEMPLATE} icinde beklenmeyen <script> blogu bulundu; "
        "bu dosya base.html'in mevcut img[data-fallback-src] delegasyonuna "
        "guvenmeli, kendi script'ini tanimlamamali."
    )


def test_period_edit_does_not_redefine_the_fallback_src_mechanism() -> None:
    """Mekanizma period_edit.html'de YENIDEN tanimlanmiyor; base.html'deki
    mevcut `img[data-fallback-src]` global dinleyicisine guveniyor."""
    text = _read(PERIOD_EDIT_TEMPLATE)
    assert "img[data-fallback-src]" not in text


def test_base_html_still_provides_the_shared_fallback_src_listener_regression_guard() -> None:
    """period_edit.html'nin guvendigi paylasilan mekanizmanin base.html'de
    hala mevcut oldugunu dogrular (bu dosyanin sahiplik alani DISINDA, salt
    okunur bir on-kosul/regresyon kontrolu -- bkz. ayni desen Wave2 personel
    testinde)."""
    text = _read(BASE_TEMPLATE)
    assert "querySelectorAll('img[data-fallback-src]')" in text
    assert "addEventListener('error'" in text


# ---------------------------------------------------------------------------
# 3) periods.html -- data-confirm + submit-delegasyon script kontrati
# ---------------------------------------------------------------------------


def test_periods_delete_form_uses_data_confirm_not_onsubmit() -> None:
    text = _read(PERIODS_TEMPLATE)
    assert "onsubmit=" not in text
    assert f'data-confirm="{PERIOD_DELETE_CONFIRM_MESSAGE}"' in text
    assert text.count('data-confirm="') == 1


def test_periods_delete_confirm_message_preserved_verbatim() -> None:
    """Uzun/kritik uyari mesaji harfiyen (Turkce karakterler dahil, tek
    karakter bile degismeden) korunmus olmali."""
    text = _read(PERIODS_TEMPLATE)
    snippet = (
        'data-confirm="Bu dönem; görevleri, puanları, karne/snapshot '
        "kayıtları, Başkan onayı ve diğer dönem bağlantılarıyla birlikte "
        'silinecek. Devam edilsin mi?"'
    )
    assert snippet in text


def test_periods_delete_form_keeps_inline_form_class_and_csrf_and_action() -> None:
    """`class="inline-form"` attribute'u, method="POST", action url_for(...)
    ve gizli csrf_token input'u DEGISMEDEN korunmus olmali (form/CSRF
    paritesi -- coordinator'in kesin yasagi: form/CSRF bozulmasi)."""
    text = _read(PERIODS_TEMPLATE)
    expected_form_open = (
        "<form method=\"POST\" "
        "action=\"{{ url_for('main.performance_period_delete', period_id=period.id) }}\" "
        'class="inline-form" '
        f'data-confirm="{PERIOD_DELETE_CONFIRM_MESSAGE}">'
    )
    assert expected_form_open in text
    # Bu form icinde hemen ardindan gizli csrf_token input'u degismeden duruyor.
    idx = text.index(expected_form_open)
    tail = text[idx : idx + 400]
    assert '<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">' in tail


def test_periods_adds_exactly_one_new_submit_delegation_script() -> None:
    """periods.html'de daha once HİÇ script yoktu; Wave6 tam olarak 1 yeni
    `<script>` blogu ekledi (standart form[data-confirm] submit-delegasyon
    kalibi, Wave1-5 ile ayni desen)."""
    text = _read(PERIODS_TEMPLATE)
    assert text.count("<script") == 1
    assert "querySelectorAll('form[data-confirm]')" in text
    assert "addEventListener('submit'" in text
    assert "window.confirm(" in text
    assert "event.preventDefault();" in text


def test_periods_script_is_inside_the_content_block() -> None:
    """Regresyon kilidi (Wave2 personnel_list.html'deki bulgu ile ayni
    sinifta bir risk): script `{% block content %}...{% endblock %}`
    KAPANMADAN ONCE, yani named block'un ICINDE olmali -- aksi halde Jinja2
    onu render ciktisina hic yansitmaz."""
    text = _read(PERIODS_TEMPLATE)
    content_start = text.index("{% block content %}")
    content_end = text.index("{% endblock %}", content_start)
    script_idx = text.index("querySelectorAll('form[data-confirm]')")
    assert content_start < script_idx < content_end, (
        "periods.html'deki yeni submit-delegasyon script'i {% block content %} "
        "disinda kalmis olabilir; bu durumda Jinja2 onu render etmez."
    )


# ---------------------------------------------------------------------------
# 4) evaluation_form.html -- data-bulk-value / id kontrati, fonksiyon
#    tanimlarinin korunmasi, mevcut script IIFE'sine kablolama eklenmesi.
# ---------------------------------------------------------------------------


def test_evaluation_form_bulk_buttons_use_data_attributes_not_onclick() -> None:
    """Kaynak (render edilmemis) sablonda `data-bulk-value="{{ bulk_value }}"`
    TEK bir Jinja dongu satirinda gecer (1..5 icin ayri ayri DEGIL, cunku
    degerler render zamaninda dolduruluyor) -- render-zamani dogrulamasi
    (5 ayri deger, `count == 5`) asagida
    `test_evaluation_form_render_wires_five_bulk_buttons_and_clear_button`
    testinde yapiliyor."""
    text = _read(EVALUATION_FORM_TEMPLATE)
    assert "onclick=" not in text
    assert 'data-bulk-value="{{ bulk_value }}"' in text
    assert "{% for bulk_value in [1, 2, 3, 4, 5] %}" in text
    assert 'id="clearBulkScoresBtn"' in text


def test_evaluation_form_bulk_score_function_definitions_are_unchanged() -> None:
    """`applyBulkScore`/`clearBulkScores` fonksiyon TANIMLARI (govdeleri)
    Wave6'da DEGISTIRILMEMELI -- sadece cagrildiklari yer (inline onclick'ten
    addEventListener'a) tasindi. Fonksiyon imzalarinin (ve govde
    baslangicinin) hala kaynak kodda oldugunu dogrular."""
    text = _read(EVALUATION_FORM_TEMPLATE)
    assert "function applyBulkScore(score) {" in text
    assert "function clearBulkScores() {" in text
    # applyBulkScore govdesindeki dogrulama/kapsam mantigi (scope='empty'
    # vb.) da korunmus olmali -- rastgele kirpilmadiginin kaniti.
    assert "const scope = getBulkScope();" in text
    assert "targetRadio.checked = true;" in text


def test_evaluation_form_wiring_added_inside_existing_script_not_a_new_one() -> None:
    """Koordinator talimati: yeni bir <script> blogu ACILMADI; kablolama
    kodu MEVCUT tek script'in (IIFE'nin) icine eklendi. Dosyada TAM OLARAK
    1 <script> etiketi olmali (Wave6 oncesiyle ayni sayida)."""
    text = _read(EVALUATION_FORM_TEMPLATE)
    assert text.count("<script") == 1
    assert "querySelectorAll('[data-bulk-value]')" in text
    assert "getElementById('clearBulkScoresBtn')" in text


def test_evaluation_form_wiring_is_inside_the_same_iife_as_the_functions_it_calls() -> None:
    """Yeni kablolama kodu, `applyBulkScore`/`clearBulkScores` fonksiyon
    tanimlarinin ICINDE bulundugu `(function () { ... })();` IIFE'sinin
    KAPANISINDAN (`})();`) ONCE yer almali -- aksi halde bu fonksiyonlar
    IIFE-local oldugundan disardan cagrilamaz (ReferenceError)."""
    text = _read(EVALUATION_FORM_TEMPLATE)
    iife_start = text.index("(function () {")
    iife_end = text.index("})();", iife_start)
    wiring_idx = text.index("querySelectorAll('[data-bulk-value]')")
    define_apply_idx = text.index("function applyBulkScore(score) {")
    define_clear_idx = text.index("function clearBulkScores() {")
    assert iife_start < define_apply_idx < iife_end
    assert iife_start < define_clear_idx < iife_end
    assert iife_start < wiring_idx < iife_end, (
        "Yeni data-bulk-value kablolama kodu IIFE kapanisindan (})();) SONRA "
        "eklenmis gorunuyor; bu durumda applyBulkScore/clearBulkScores "
        "kapsam disinda kalir ve cagrilamaz."
    )
    # Kablolama, initializePreviews()/recalculate() cagrilarindan HEMEN
    # SONRA eklendi (coordinator'in belirttigi ekleme noktasi).
    anchor_idx = text.index("initializePreviews();\n    recalculate();")
    assert anchor_idx < wiring_idx


def test_evaluation_form_bulk_click_wiring_binds_each_button_exactly_once() -> None:
    """5 data-bulk-value butonu TEK bir `querySelectorAll(...).forEach(...)`
    ile (delegasyon degil, dogrudan baglama) kabloluyor -- sayfa basina 1
    kez calisan script icin bu yeterli ve her butona YALNIZ 1 dinleyici
    baglar (coordinator'in acikladigi gerekce)."""
    text = _read(EVALUATION_FORM_TEMPLATE)
    assert text.count("querySelectorAll('[data-bulk-value]')") == 1
    assert text.count("getElementById('clearBulkScoresBtn')") == 1


# ---------------------------------------------------------------------------
# 5) Calisma-zamani render kontrolleri: gercek Flask app + gercek Jinja
#    motoru ile `render_template()` cagrisi (bkz. `app` fixture,
#    tests/conftest.py). Sahte `types.SimpleNamespace` context nesneleri
#    kullanilir (Wave5 ile ayni tercih) -- gercek route/DB/login akisina
#    girilmez.
# ---------------------------------------------------------------------------


def _fake_period(period_id: int = 6001, **overrides: object) -> types.SimpleNamespace:
    base: dict[str, object] = dict(
        id=period_id,
        title="Wave6 Kontrat Test Dönemi",
        period_type="Aylık",
        start_date=datetime.date(2026, 1, 1),
        end_date=datetime.date(2026, 1, 31),
        description="Wave6 kontrat testi için oluşturulan sahte dönem.",
        is_active=True,
        is_locked=False,
        results_published=False,
        special_scenario_type=None,
        scope_type="all",
        scope_unit_label="",
        scope_category_label="",
        scope_personnel_filter="",
        evaluation_window_start=None,
        evaluation_window_end=None,
        evaluation_due_days=None,
        evaluation_due_days_effective=None,
        minimum_presence_days_for_evaluation=0,
        leave_skip_threshold_days=None,
        absence_skip_threshold_days=None,
        auto_skip_if_fully_absent=True,
        manager_delegation_required=True,
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


def test_period_edit_render_uses_data_fallback_src_and_base_delegation_is_included(app) -> None:
    """period_edit.html'in render ciktisinda `data-fallback-src` VE
    base.html'in kendi global delegasyon script'inin (`img[data-fallback-src]`)
    render ciktisina GERCEKTEN dahil oldugunu dogrular (base.html extend
    edildigi icin otomatik gelir -- bu, kisayolun GERCEKTEN calistigi
    varsayimini kaynak-kod okumasinin otesinde dogrulayan tek katmandir)."""
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template(
            "period_edit.html",
            period=_fake_period(),
            ai_period_form_panel=None,
        )

    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert 'data-fallback-src="' in html
    assert "onerror=" not in html
    # base.html'in global delegasyonu render ciktisinda GERCEKTEN mevcut.
    assert "querySelectorAll('img[data-fallback-src]')" in html
    assert "addEventListener('error'" in html


def test_periods_render_preserves_delete_confirm_message_and_wiring(app) -> None:
    """periods.html'in render ciktisinda uzun confirm mesajinin BIREBIR
    korundugunu VE submit-delegasyon script'inin gercekten render edildigini
    dogrular."""
    from flask import render_template

    period = _fake_period()
    row = {
        "period": period,
        "weight_summary": "1. Amir %40 • 2. Amir %30 • 3. Amir %30",
        "availability_summary": "Asgari fiili gün kuralı kapalı",
        "assignment_count": 3,
        "evaluation_count": 2,
        "completed_count": 1,
        "coverage_summary": {"exempted": 0, "uncovered": 0, "chain_issue": 0, "delegated": 0},
        "coverage_latest_created_at": None,
        "coverage_unit_rows": [],
    }

    with app.test_request_context("/"):
        html = render_template(
            "periods.html",
            period_rows=[row],
            periods=[period],
            total_count=1,
            active_count=1,
            published_count=0,
            locked_count=0,
            selected_status=None,
            q=None,
            ai_periods_panel=None,
        )

    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert f'data-confirm="{PERIOD_DELETE_CONFIRM_MESSAGE}"' in html
    assert 'class="inline-form"' in html
    assert "querySelectorAll('form[data-confirm]')" in html
    assert "addEventListener('submit'" in html


def test_periods_render_empty_state_still_has_no_inline_handlers(app) -> None:
    """`period_rows` bos oldugunda (bos-durum karti) da render hatasiz
    calisir ve inline handler icermez -- delete formu satiri hic
    render edilmedigi icin data-confirm de gorunmez (regresyon: sablon
    bos listede kirilmamali)."""
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template(
            "periods.html",
            period_rows=[],
            periods=[],
            total_count=0,
            active_count=0,
            published_count=0,
            locked_count=0,
            selected_status=None,
            q=None,
            ai_periods_panel=None,
        )

    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert "Filtreye uygun dönem bulunamadı." in html
    # Script her zaman render edilir (period_rows'tan bagimsiz, content
    # block'un sonunda); bos durumda bile mevcut olmali.
    assert "querySelectorAll('form[data-confirm]')" in html


def _fake_evaluation_form_context(*, manager_level: int = 2) -> dict[str, object]:
    assignment = types.SimpleNamespace(manager_level=manager_level)
    evaluation = types.SimpleNamespace(
        level_1_total_100=72.5,
        level_2_total_100=0,
        level_3_total_100=0,
        final_total_100=0,
        level_2_evaluator_id=None,
        level_3_evaluator_id=None,
        level_2_seen_level_1_at=None,
        level_3_general_comment=None,
        level_3_comment=None,
        level_2_general_comment=None,
        level_2_comment=None,
        level_3_evaluator=None,
    )
    period = types.SimpleNamespace(title="Wave6 Kontrat Test Dönemi")
    employee = types.SimpleNamespace(full_name="Wave6 Test Personel", birim="Test Birimi")
    workflow = types.SimpleNamespace(label="Test Akışı", can_level_1_edit=True, can_level_2_return=True)
    effective_weights = types.SimpleNamespace(
        evaluator_1_weight=40, evaluator_2_weight=30, evaluator_3_weight=30,
    )
    return dict(
        assignment=assignment,
        evaluation=evaluation,
        period=period,
        employee=employee,
        workflow=workflow,
        level_3_scoring_enabled=True,
        evaluation_window=None,
        criteria_list=[],
        current_items_map={},
        level_1_items_map={},
        level_2_items_map={},
        level_3_items_map={},
        current_general_comment="",
        current_saved_level_total=0,
        saved=False,
        can_return_to_level_1=False,
        can_withdraw_level_1=False,
        history_url="/performance/history/6001",
        previous_general_comments=[],
        effective_weights=effective_weights,
    )


def test_evaluation_form_render_has_five_bulk_buttons_and_wired_functions(app) -> None:
    """evaluation_form.html'in render ciktisinda 5 `data-bulk-value`
    butonunun (1,2,3,4,5) VE `applyBulkScore`/`clearBulkScores` fonksiyon
    tanimlarinin hala dosyada oldugunu, render EDILMIS HTML uzerinden
    dogrular (yalnizca kaynak kodda degil)."""
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template("evaluation_form.html", **_fake_evaluation_form_context(manager_level=2))

    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    for value in (1, 2, 3, 4, 5):
        assert f'data-bulk-value="{value}"' in html
    assert html.count('data-bulk-value="') == 5
    assert 'id="clearBulkScoresBtn"' in html

    assert "function applyBulkScore(score) {" in html
    assert "function clearBulkScores() {" in html
    assert "querySelectorAll('[data-bulk-value]')" in html
    assert "getElementById('clearBulkScoresBtn')" in html


def test_evaluation_form_render_level1_manager_view_still_has_no_inline_handlers(app) -> None:
    """1. amir gorunumunde (manager_level=1, can_level_1_edit=True) de toplu
    puan aracubu render edilir ve inline handler icermez -- iki farkli
    manager_level dalinin (2 ve 1) ikisinde de regresyon olmadigini dogrular."""
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template("evaluation_form.html", **_fake_evaluation_form_context(manager_level=1))

    assert not _INLINE_EVENT_ATTR_RE.findall(html)
    assert html.count('data-bulk-value="') == 5
    assert 'id="clearBulkScoresBtn"' in html
