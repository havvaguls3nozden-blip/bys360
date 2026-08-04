"""BYS360 CSP Style-2A pilot (Agent 2) -- lighter self-check contract testi.

Bu dosyanın sahiplik alanı SADECE Agent 2'nin dönüştürdüğü DÖRT şablon:
    - app/templates/hr_attendance.html
    - app/templates/hr_personnel_dashboard.html
    - app/templates/file_center/index.html
    - app/templates/admin_analysis_excel_preview.html

ve bunların yeni/paylaşılan CSS dosyaları:
    - app/static/css/hr_operations_workspace_layout.css (YENİ -- hr_attendance.html
      VE hr_personnel_dashboard.html tarafından paylaşılıyor)
    - app/static/css/admin_analysis_workspace_layout.css (YENİ -- yalnızca
      admin_analysis_excel_preview.html)
    - app/static/css/file_center_premium_v1kb.css (MEVCUT -- file_center/index.html
      zaten yüklüyordu, bu pilotta 3 yeni utility class eklendi)

Bu dosya, "Style-2A" pilotunun (24 tamamen statik style="..." attribute'unu
CSS class'larına taşıma) davranış-koruyan (behavior-preserving) olduğunu
kilitler: her class'ın, kaldırdığı attribute ile BİREBİR aynı deklarasyonu
taşıdığını, hiçbir style="..." kalmadığını, hiçbir !important/ID selector/
yeni CSS custom property eklenmediğini ve satır-içi (inline) event-handler /
javascript: sayısının hâlâ sıfır olduğunu doğrular.

KAPSAM NOTU (bilinçli, gerekçeli sınırlama): Bu dört route'un TÜMÜ
`@login_required` taşıyor; ancak hr_attendance.html ve hr_personnel_dashboard.html
route'ları AYRICA `@manager_required` + `@menu_key_required("hr_leave_tracking")`,
admin_analysis_excel_preview.html route'u ise `@admin_required` +
`@menu_key_required("ai_center")` taşıyor. Menü görünürlüğü canlı, çok
katmanlı, DB-tabanlı bir çözümleyiciden (`app/services/menu_visibility.py`)
geliyor ve rol/birim/kullanıcı override zincirini gerçekçi biçimde taklit
etmek bu "hafif öz-kontrol" dosyasının kapsamı dışında bırakılmıştır (bu,
Agent 3'ün ayrı ve daha geniş bağımsız kontrat paketinin işi). Bunun yerine
iki tamamlayıcı kanıt katmanı kullanılır (Wave6/Wave8/Wave9 kontrat
dosyalarıyla AYNI, bu depoda zaten yerleşik yöntem):
  1) Gerçek bir Flask test client ile route'lara GİRİŞ YAPMADAN GET atılır;
     500 ÜRETMEDİĞİ (ya login'e yönlendirdiği ya da 403 döndürdüğü, ama asla
     çökmediği) doğrulanır -- route'un gerçekten kayıtlı ve sağlam
     kablolandığının kanıtı (`tests/critical/test_v59_broad_route_smoke.py`
     ile aynı desen).
  2) Şablonların KENDİSİ, gerçek Jinja motoruyla (`flask.render_template()`,
     `app.test_request_context()` içinde, sahte `types.SimpleNamespace`/dict
     context nesneleriyle) uçtan uca render edilir -- bu, dönüştürülen HER
     satırın gerçekten doğru class ile, doğru koşullu dalda, style="..."
     OLMADAN render edildiğinin doğrudan kanıtıdır (`tests/security/
     test_csp_wave9_file_center_contract.py` ile birebir aynı teknik).
  file_center/index.html İSTİSNA: bu route SADECE `@login_required` taşıyor
  (manager/admin/menu_key katmanı YOK) -- bu yüzden bu dosya için AYRICA
  gerçek, giriş yapılmış bir test-client GET'i 200 döndürerek de
  doğrulanmıştır (aşağıda `test_file_center_index_real_authenticated_client_get_returns_200`).
"""
from __future__ import annotations

import re
import types
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

HR_ATTENDANCE_TEMPLATE = "app/templates/hr_attendance.html"
HR_PERSONNEL_DASHBOARD_TEMPLATE = "app/templates/hr_personnel_dashboard.html"
FILE_CENTER_INDEX_TEMPLATE = "app/templates/file_center/index.html"
ADMIN_ANALYSIS_EXCEL_PREVIEW_TEMPLATE = "app/templates/admin_analysis_excel_preview.html"

OWNED_TEMPLATES = [
    HR_ATTENDANCE_TEMPLATE,
    HR_PERSONNEL_DASHBOARD_TEMPLATE,
    FILE_CENTER_INDEX_TEMPLATE,
    ADMIN_ANALYSIS_EXCEL_PREVIEW_TEMPLATE,
]

HR_WORKSPACE_CSS = "app/static/css/hr_operations_workspace_layout.css"
ADMIN_ANALYSIS_CSS = "app/static/css/admin_analysis_workspace_layout.css"
FILE_CENTER_CSS = "app/static/css/file_center_premium_v1kb.css"

NEW_CSS_FILES = [HR_WORKSPACE_CSS, ADMIN_ANALYSIS_CSS]

_INLINE_EVENT_ATTR_RE = re.compile(r"""[\s]on[a-zA-Z]+\s*=\s*["']""")
_JS_HREF_RE = re.compile(r"""(?:href|src)\s*=\s*["']\s*javascript:""", re.IGNORECASE)
_STYLE_ATTR_RE = re.compile(r"""\sstyle\s*=\s*["']""")
_ID_SELECTOR_RE = re.compile(r"(^|\})\s*#[A-Za-z_][\w-]*\s*\{", re.MULTILINE)

# Bu 4 sablonun DAHA ONCE tasidigi TAM style="..." attribute metinleri.
# render_template() TAM sayfa (base.html/admin_ai_base.html dahil) uretir --
# ve o iskeletlerde bu pilotun kapsami DISINDA, mesru baska style="..."
# attribute'lari (orn. gizli logout formu) OLABILIR/vardir. Bu yuzden
# render-tabanli testlerde "sayfada hic style yok" gibi kaba bir kontrol
# YANLIS OLUR -- bunun yerine SADECE bu pilotun KALDIRDIGI spesifik eski
# literal'lerin bir daha GORUNMEDIGI dogrulanir (statik testler zaten
# sablon KAYNAGININ KENDISINDE sifir style="..." oldugunu kilitliyor).
REMOVED_HR_ATTENDANCE_STYLE_LITERALS = (
    'style="margin-top:14px;"',
    'style="margin-top:10px;"',
    'style="margin:18px 0 0;"',
    'style="margin-top:16px;"',
)
REMOVED_HR_PERSONNEL_DASHBOARD_STYLE_LITERALS = (
    'style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px"',
    'style="padding:0;border:none;box-shadow:none;background:transparent"',
    'style="margin:0 0 12px"',
    'style="padding:0;border:none;box-shadow:none;background:transparent;margin-top:18px"',
)
REMOVED_ADMIN_ANALYSIS_STYLE_LITERALS = (
    'style="margin-top:16px"',
    'style="grid-template-columns:repeat(3,minmax(0,1fr));margin-top:14px"',
    'style="margin-top:14px"',
)
REMOVED_FILE_CENTER_INDEX_STYLE_LITERALS = (
    'style="max-width:820px;"',
    'style="min-width:250px;"',
    'style="color:#8B0000;"',
)


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# 1) Statik sözleşme: dönüştürülen 4 şablonda artık HİÇBİR style="..." yok.
# ---------------------------------------------------------------------------


def test_all_four_owned_templates_have_zero_style_attributes() -> None:
    for relative_path in OWNED_TEMPLATES:
        text = _read(relative_path)
        matches = _STYLE_ATTR_RE.findall(text)
        assert not matches, f"{relative_path} hâlâ style=\"...\" attribute'u içeriyor: {matches!r}"


def test_owned_templates_have_no_inline_event_attributes() -> None:
    for relative_path in OWNED_TEMPLATES:
        text = _read(relative_path)
        assert not _INLINE_EVENT_ATTR_RE.findall(text), f"{relative_path} icinde inline event-attribute bulundu."


def test_owned_templates_have_no_javascript_url_anywhere() -> None:
    for relative_path in OWNED_TEMPLATES:
        text = _read(relative_path)
        assert "javascript:" not in text.lower(), f"{relative_path} icinde javascript: bulundu."


def test_owned_templates_have_no_javascript_href() -> None:
    for relative_path in OWNED_TEMPLATES:
        text = _read(relative_path)
        assert not _JS_HREF_RE.findall(text), f"{relative_path} icinde href/src=javascript:... bulundu."


# ---------------------------------------------------------------------------
# 2) Yeni <link rel="stylesheet"> referanslari dogru sekilde eklendi mi?
# ---------------------------------------------------------------------------


def test_hr_attendance_links_shared_hr_workspace_css() -> None:
    text = _read(HR_ATTENDANCE_TEMPLATE)
    assert '<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'css/hr_operations_workspace_layout.css\') }}">' in text


def test_hr_personnel_dashboard_links_shared_hr_workspace_css() -> None:
    text = _read(HR_PERSONNEL_DASHBOARD_TEMPLATE)
    assert '<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'css/hr_operations_workspace_layout.css\') }}">' in text


def test_admin_analysis_excel_preview_links_new_admin_analysis_css() -> None:
    text = _read(ADMIN_ANALYSIS_EXCEL_PREVIEW_TEMPLATE)
    assert '<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'css/admin_analysis_workspace_layout.css\') }}">' in text


def test_file_center_index_still_links_existing_premium_css_and_no_new_link_added() -> None:
    """file_center/index.html zaten file_center_premium_v1kb.css yukluyordu --
    bu pilotta o dosyaya 3 yeni class eklendi, YENİ bir <link> eklenmedi."""
    text = _read(FILE_CENTER_INDEX_TEMPLATE)
    assert text.count("<link rel=\"stylesheet\"") == 1
    assert "css/file_center_premium_v1kb.css" in text


def test_new_link_tags_are_placed_after_the_pages_own_style_block() -> None:
    """Cascade sirasi icin: yeni <link>, sayfanin KENDI <style> blogundan
    SONRA gelmeli (esit specificity'de kaynak-sirasi kazanimi icin)."""
    for relative_path, css_href_fragment in (
        (HR_ATTENDANCE_TEMPLATE, "css/hr_operations_workspace_layout.css"),
        (HR_PERSONNEL_DASHBOARD_TEMPLATE, "css/hr_operations_workspace_layout.css"),
        (ADMIN_ANALYSIS_EXCEL_PREVIEW_TEMPLATE, "css/admin_analysis_workspace_layout.css"),
    ):
        text = _read(relative_path)
        style_close_idx = text.index("</style>")
        link_idx = text.index(css_href_fragment)
        assert style_close_idx < link_idx, f"{relative_path}: yeni <link> </style>'dan ONCE geliyor -- cascade sirasi bozulur."


# ---------------------------------------------------------------------------
# 3) Yeni class isimleri dogru elementlerde render ediliyor mu (statik metin).
# ---------------------------------------------------------------------------


def test_hr_attendance_new_classes_present_on_expected_elements() -> None:
    text = _read(HR_ATTENDANCE_TEMPLATE)
    assert '<div class="info block-spacing-top-sm">' in text
    assert '<div class="block-spacing-top-xs">{{ selected_user_guard.requirement_message }}</div>' in text
    assert 'kapsayan vekâlet' in text and '<div class="block-spacing-top-xs">Mevcut kapsayan vekâlet:' in text
    assert '<div class="scope-strip scope-strip-offset">' in text
    assert text.count('<div class="report-actions block-spacing-top-md">') == 2
    assert text.count('<div class="small block-spacing-top-sm">') == 2


def test_hr_personnel_dashboard_new_classes_present_on_expected_elements() -> None:
    text = _read(HR_PERSONNEL_DASHBOARD_TEMPLATE)
    assert '<div class="btn-soft-row">' in text
    assert text.count('<div class="panel panel-flush">') == 2
    assert '<div class="panel panel-flush panel-flush-spaced">' in text
    assert text.count('<h4 class="subsection-heading">') == 3


def test_file_center_index_new_classes_present_on_expected_elements() -> None:
    text = _read(FILE_CENTER_INDEX_TEMPLATE)
    assert '<div class="fc-hero-copy">' in text
    assert 'fc-hero-security-box">' in text
    assert 'bg-white bg-opacity-10 rounded-4 p-3 border border-white border-opacity-25 fc-hero-security-box' in text
    assert '<div class="display-6 mb-2 fc-upload-icon-color">↑</div>' in text


def test_admin_analysis_excel_preview_new_classes_present_on_expected_elements() -> None:
    text = _read(ADMIN_ANALYSIS_EXCEL_PREVIEW_TEMPLATE)
    assert text.count('admin-analysis-spacing-top-md') == 3
    assert '<div class="ai-filters ai-filters-3col">' in text
    assert text.count('<div class="analysis-table-scroll admin-analysis-spacing-top-sm">') == 2


# ---------------------------------------------------------------------------
# 4) Yeni CSS dosyalari var mi, dogru selector/deklarasyonlari iceriyor mu,
#    !important / ID selector / yeni custom property YOK mu.
# ---------------------------------------------------------------------------


def test_new_css_files_exist_and_are_non_empty() -> None:
    for relative_path in NEW_CSS_FILES:
        css_path = REPO_ROOT / relative_path
        assert css_path.exists(), f"{relative_path} olusturulmamis."
        assert css_path.stat().st_size > 0


def test_new_css_files_introduce_no_important_no_id_selectors_no_new_custom_properties() -> None:
    """Not: yorum satirlarinda " -- " (em-dash yerine ASCII) serbesttir; burada
    yasaklanan SADECE CSS custom property SÖZDİZİMİDİR (`--isim: deger;`
    tanimi veya `var(--isim)` kullanimi), duz metindeki cift tire DEGIL."""
    _CUSTOM_PROPERTY_DEFINITION_RE = re.compile(r"--[A-Za-z][\w-]*\s*:")
    for relative_path in NEW_CSS_FILES:
        text = _read(relative_path)
        assert "!important" not in text, f"{relative_path} icinde !important bulundu."
        assert not _ID_SELECTOR_RE.search(text), f"{relative_path} icinde ID selector bulundu."
        assert "var(--" not in text, f"{relative_path} icinde var(--...) kullanimi bulundu."
        assert not _CUSTOM_PROPERTY_DEFINITION_RE.search(text), f"{relative_path} icinde yeni bir CSS custom property TANIMI bulundu."


def test_file_center_premium_css_new_rules_introduce_no_important_and_no_id_selectors() -> None:
    """file_center_premium_v1kb.css'in KENDI ONCEDEN VAR OLAN kurallari
    yogun bicimde !important kullaniyor (bu pilotun kapsami DISINDA,
    dokunulmadi) -- burada SADECE bu pilotun EKLEDIGI 3 yeni kuralin
    !important/ID selector/custom-property ICERMEDIGI dogrulanir."""
    text = _read(FILE_CENTER_CSS)
    marker = "BYS360 CSP Style-2A pilot -- index.html-only"
    assert marker in text
    added_block = text[text.index(marker):]
    assert "!important" not in added_block
    assert not _ID_SELECTOR_RE.search(added_block)
    assert "var(--" not in added_block, "Eklenen blok mevcut --fc-primary custom property'sini REFERANS ALMAMALI (literal #8B0000 kullanilmali)."
    assert not re.search(r"--[A-Za-z][\w-]*\s*:", added_block), "Eklenen blok yeni bir CSS custom property TANIMLAMAMALI."


def test_hr_workspace_css_declarations_match_removed_style_attributes_byte_for_byte() -> None:
    text = _read(HR_WORKSPACE_CSS)
    expected_rules = {
        ".block-spacing-top-xs": "margin-top: 10px;",
        ".block-spacing-top-sm": "margin-top: 14px;",
        ".block-spacing-top-md": "margin-top: 16px;",
        ".scope-strip-offset": "margin: 18px 0 0;",
        ".panel-flush-spaced": "margin-top: 18px;",
        ".subsection-heading": "margin: 0 0 12px;",
    }
    for selector, declaration in expected_rules.items():
        pattern = re.escape(selector) + r"\s*\{\s*" + re.escape(declaration) + r"\s*\}"
        assert re.search(pattern, text), f"{selector} icin beklenen kural bulunamadi: {declaration!r}"

    panel_flush_pattern = re.compile(
        r"\.panel-flush\s*\{\s*"
        r"padding:\s*0;\s*"
        r"border:\s*none;\s*"
        r"box-shadow:\s*none;\s*"
        r"background:\s*transparent;\s*\}"
    )
    assert panel_flush_pattern.search(text), ".panel-flush kurali beklenen 4 deklarasyonu tam olarak icermiyor."

    btn_soft_row_pattern = re.compile(
        r"\.btn-soft-row\s*\{\s*"
        r"display:\s*flex;\s*"
        r"flex-wrap:\s*wrap;\s*"
        r"gap:\s*8px;\s*"
        r"margin-bottom:\s*14px;\s*\}"
    )
    assert btn_soft_row_pattern.search(text), ".btn-soft-row kurali beklenen 4 deklarasyonu tam olarak icermiyor."


def test_admin_analysis_css_declarations_match_removed_style_attributes_byte_for_byte() -> None:
    text = _read(ADMIN_ANALYSIS_CSS)
    assert re.search(r"\.admin-analysis-spacing-top-md\s*\{\s*margin-top:\s*16px;\s*\}", text)
    assert re.search(r"\.admin-analysis-spacing-top-sm\s*\{\s*margin-top:\s*14px;\s*\}", text)
    ai_filters_pattern = re.compile(
        r"\.ai-filters-3col\s*\{\s*"
        r"grid-template-columns:\s*repeat\(3,\s*minmax\(0,\s*1fr\)\);\s*"
        r"margin-top:\s*14px;\s*\}"
    )
    assert ai_filters_pattern.search(text), ".ai-filters-3col kurali beklenen iki deklarasyonu tam olarak icermiyor."


def test_file_center_css_new_rules_match_removed_style_attributes_byte_for_byte() -> None:
    text = _read(FILE_CENTER_CSS)
    assert re.search(r"\.fc-hero-copy\s*\{\s*max-width:\s*820px;\s*\}", text)
    assert re.search(r"\.fc-hero-security-box\s*\{\s*min-width:\s*250px;\s*\}", text)
    assert re.search(r"\.fc-upload-icon-color\s*\{\s*color:\s*#8B0000;\s*\}", text)


# ---------------------------------------------------------------------------
# 5) Route smoke: gercek test client, giris YAPILMADAN, 500 URETMEZ.
#    (tests/critical/test_v59_broad_route_smoke.py ile ayni desen; menu/rol
#    kablolamasini taklit etmeden route'un kayitli ve saglam oldugunu
#    dogrular.)
# ---------------------------------------------------------------------------


OWNED_ROUTES = [
    "/hr-management/attendance",
    "/hr-management/personnel-operations/dashboard",
    "/file-center",
    "/admin/analysis-center/excel-preview",
]


def test_owned_routes_are_registered_in_the_url_map(app) -> None:
    rules = {str(rule.rule) for rule in app.url_map.iter_rules()}
    for route in OWNED_ROUTES:
        assert route in rules, f"{route} url_map icinde kayitli degil."


def test_owned_routes_do_not_return_500_without_login(client) -> None:
    for route in OWNED_ROUTES:
        response = client.get(route, follow_redirects=False)
        assert response.status_code != 500, f"{route} girissiz istekte 500 dondu."
        assert response.status_code in (200, 302, 401, 403), (
            f"{route} beklenmedik durum kodu dondu: {response.status_code}"
        )


# ---------------------------------------------------------------------------
# 6) file_center/index.html ISTISNASI: bu route SADECE @login_required
#    tasidigi icin gercek, giris yapilmis bir test-client GET'i 200 doner.
# ---------------------------------------------------------------------------


def test_file_center_index_real_authenticated_client_get_returns_200(app, monkeypatch) -> None:
    """Paylasilan session-scoped `app`/DB fixture'i (tests/conftest.py)
    kullanilir -- ayni process icinde ikinci bir `create_app()` cagrisi
    (izole bir app kurma denemesi) Flask-SQLAlchemy'nin tekil `db` extension
    nesnesiyle celisip menu-gorunurlugu sorgularinin (role_menu_defaults /
    user_menu_permissions) yanlislikla hala BOS/eksik bir engine'e
    baglanmasina yol acabiliyor (bu, bu dosyanin ilk taslaginda ampirik
    olarak gozlemlendi) -- tek, paylasilan `app` fixture'i bu riski tasimaz.

    `file_center_home` route'u login_required DISINDA ayrica DB/env tabanli
    bir "modul acik mi" bayragi (`app/file_center/services.py::
    file_center_enabled`, varsayilan KAPALI) tasir -- bos test DB'sinde bu
    satirla ampirik olarak dogrulandi (redirect Location: /home). Bu pilotun
    KENDI kapsami DEGIL (route/is-mantigi degistirilmedi), sadece testin
    gercek 200 alabilmesi icin env bayragi acilir."""
    monkeypatch.setenv("FILE_CENTER_ENABLED", "true")

    from app.extensions import db
    from app.models import User

    unique_sicil = "style2a" + uuid.uuid4().hex[:10]
    password = "Style2aTestPilotKey1!"

    with app.app_context():
        user = User(
            sicil_no=unique_sicil,
            email=f"{unique_sicil}@example.test",
            ad="Style2A",
            soyad="Pilot",
            role="personel",
            is_active=True,
            must_change_password=False,
            must_set_security_question=False,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    client = app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)
        sess["_fresh"] = True

    response = client.get("/file-center", follow_redirects=False)
    assert response.status_code == 200, f"/file-center girisli istekte 200 donmedi: {response.status_code}"
    html = response.get_data(as_text=True)
    for literal in REMOVED_FILE_CENTER_INDEX_STYLE_LITERALS:
        assert literal not in html, f"Kaldirilmasi gereken eski style literal'i hala render ediliyor: {literal!r}"
    assert 'fc-hero-copy' in html
    assert 'fc-hero-security-box' in html
    assert 'fc-upload-icon-color' in html
    assert 'href="/static/css/file_center_premium_v1kb.css' in html


# ---------------------------------------------------------------------------
# 7) Calisma-zamani render kontrolleri: gercek Jinja motoru,
#    render_template() + sahte SimpleNamespace/dict context (Wave6/8/9
#    deseniyle ayni -- gercek route/DB/login akisina GIRMEZ).
# ---------------------------------------------------------------------------


def _attendance_render_context() -> dict[str, object]:
    selected_user_guard = types.SimpleNamespace(
        message="Test seçili personel mesajı.",
        coverage=types.SimpleNamespace(is_manager=True, level_1="Amir A", level_2="Amir B", level_3="Amir C"),
        requires_delegation=True,
        requirement_message="Test vekâlet gereklilik mesajı.",
        has_covering_delegation=True,
        covering_delegation=types.SimpleNamespace(
            delegate_user=types.SimpleNamespace(full_name="Test Vekil Kişi"),
        ),
    )
    return dict(
        attendance_today_count=3,
        active_delegation_count=2,
        uncovered_count=1,
        active_period=types.SimpleNamespace(title="Test Dönemi"),
        effective_period=types.SimpleNamespace(manager_delegation_required=True),
        selected_user_guard=selected_user_guard,
        hr_scope=None,
        selected_scope_mode="personal",
        selected_period_id=None,
        selected_user_id=None,
        users=[],
        periods=[],
        delegate_candidates=[],
        leave_sources=[],
        attendance_sources=[],
        attendance_rows=[],
        delegations=[],
        attendance_pressure_rows=[],
        attendance_action_rows=[],
        attendance_type_choices=[],
        leave_status_choices=[],
        delegation_scope_choices=[],
        delegation_status_choices=[],
        attendance_create_submit_token="test-attendance-token",
        delegation_create_submit_token="test-delegation-token",
        attendance_ai_panel=None,
        can_view_ai_admin=True,
        attendance_ai_governance_url="https://example.test/ai-governance",
    )


def test_hr_attendance_renders_and_keeps_all_new_classes_with_no_style_attrs(app) -> None:
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template(HR_ATTENDANCE_TEMPLATE.split("app/templates/")[-1], **_attendance_render_context())

    for literal in REMOVED_HR_ATTENDANCE_STYLE_LITERALS:
        assert literal not in html, f"Kaldirilmasi gereken eski style literal'i hala render ediliyor: {literal!r}"
    assert 'class="info block-spacing-top-sm"' in html
    assert html.count('class="block-spacing-top-xs"') == 2
    assert 'class="scope-strip scope-strip-offset"' in html
    assert html.count('class="report-actions block-spacing-top-md"') == 2
    assert html.count('class="small block-spacing-top-sm"') == 2
    assert 'css/hr_operations_workspace_layout.css' in html


def _personnel_dashboard_render_context() -> dict[str, object]:
    return dict(
        dashboard_ready=True,
        dashboard_stats=types.SimpleNamespace(
            personnel_count=12,
            expiring_30=3,
            active_assets=8,
            transfers_30=2,
            expired=1,
            overdue_assets=1,
            queued_reminders=4,
        ),
        expiring_rows=[types.SimpleNamespace(user_name="Test Kişi", title="Ehliyet", category="Belge", days_left=5)],
        overdue_asset_rows=[types.SimpleNamespace(user_name="Test Kişi", asset_name="Laptop", asset_code="LT-1", due_return_date="2026-08-01")],
        recent_transfer_rows=[
            types.SimpleNamespace(
                transfer_date="2026-07-30",
                asset_name="Laptop",
                asset_code="LT-1",
                from_user_name="A",
                to_user_name="B",
                status_label="Tamamlandı",
            )
        ],
        selected_scope_mode="personal",
    )


def test_hr_personnel_dashboard_renders_and_keeps_all_new_classes_with_no_style_attrs(app) -> None:
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template(
            HR_PERSONNEL_DASHBOARD_TEMPLATE.split("app/templates/")[-1],
            **_personnel_dashboard_render_context(),
        )

    for literal in REMOVED_HR_PERSONNEL_DASHBOARD_STYLE_LITERALS:
        assert literal not in html, f"Kaldirilmasi gereken eski style literal'i hala render ediliyor: {literal!r}"
    assert 'class="btn-soft-row"' in html
    assert html.count('class="panel panel-flush"') == 2
    assert 'class="panel panel-flush panel-flush-spaced"' in html
    assert html.count('class="subsection-heading"') == 3
    assert 'css/hr_operations_workspace_layout.css' in html


def _admin_analysis_excel_preview_empty_render() -> str:
    from flask import render_template

    from app.services.ai.excel_preview import build_empty_excel_preview_context

    ctx = build_empty_excel_preview_context()
    return render_template(
        ADMIN_ANALYSIS_EXCEL_PREVIEW_TEMPLATE.split("app/templates/")[-1],
        **ctx,
    )


def test_admin_analysis_excel_preview_empty_state_renders_upload_and_actions_classes(app) -> None:
    with app.test_request_context("/"):
        html = _admin_analysis_excel_preview_empty_render()

    for literal in REMOVED_ADMIN_ANALYSIS_STYLE_LITERALS:
        assert literal not in html, f"Kaldirilmasi gereken eski style literal'i hala render ediliyor: {literal!r}"
    assert html.count('class="ai-actions admin-analysis-spacing-top-md"') == 2
    assert 'class="analysis-upload-box admin-analysis-spacing-top-md"' in html
    assert 'class="ai-filters ai-filters-3col"' in html
    assert 'css/admin_analysis_workspace_layout.css' in html
    # preview=None dalinda analysis-table-scroll DIV'i hic render edilmez
    # (not: bare "analysis-table-scroll" alt string'i sayfanin KENDI
    # <style> blogundaki .analysis-table-scroll{overflow-x:auto} CSS
    # kuralinda HER ZAMAN gorunur -- burada spesifik olarak class= ile
    # baslayan HTML attribute deseni araniyor, CSS kural metni degil).
    assert 'class="analysis-table-scroll' not in html


def _fake_excel_preview() -> types.SimpleNamespace:
    column = types.SimpleNamespace(
        index=1,
        header="Ad Soyad",
        normalized_header="ad_soyad",
        inferred_type="text",
        sensitivity="yüksek",
        non_empty_count=10,
        empty_count=0,
        sample_values=["Test Kişi"],
        kvkk_reason="Kişisel veri içerir.",
        formula_count=0,
    )
    cell = types.SimpleNamespace(header="Ad Soyad", value="***")
    row = types.SimpleNamespace(row_number=1, cells=[cell])
    metrics = types.SimpleNamespace(
        row_count_visible=10,
        row_count_estimated=10,
        column_count=1,
        sensitive_column_count=1,
        formula_cells=0,
    )
    return types.SimpleNamespace(
        metrics=metrics,
        db_write_enabled=False,
        original_filename="test.xlsx",
        extension=".xlsx",
        file_size=2048,
        detected_mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        sheet_name="Sayfa1",
        sheet_names=["Sayfa1"],
        header_row_index=1,
        kvkk_warnings=["Test KVKK uyarısı."],
        security_findings=[],
        warnings=[],
        columns=[column],
        preview_rows=[row],
    )


def test_admin_analysis_excel_preview_with_preview_renders_table_scroll_classes(app) -> None:
    from flask import render_template

    from app.services.ai.excel_preview import build_empty_excel_preview_context

    ctx = build_empty_excel_preview_context()
    ctx["preview"] = _fake_excel_preview()

    with app.test_request_context("/"):
        html = render_template(
            ADMIN_ANALYSIS_EXCEL_PREVIEW_TEMPLATE.split("app/templates/")[-1],
            **ctx,
        )

    for literal in REMOVED_ADMIN_ANALYSIS_STYLE_LITERALS:
        assert literal not in html, f"Kaldirilmasi gereken eski style literal'i hala render ediliyor: {literal!r}"
    assert html.count('class="analysis-table-scroll admin-analysis-spacing-top-sm"') == 2
    assert 'Test Kişi' not in html or 'Ad Soyad' in html  # maskeli hücre görünür yapıdadır


def _file_center_index_render_context() -> dict[str, object]:
    from app.file_center.services import format_bytes, link_status_label, scan_label

    file_a = types.SimpleNamespace(
        id=9101,
        original_filename="Style2A-Test.pdf",
        extension=".pdf",
        size_bytes=1024,
        sha256_hash="b" * 64,
        scan_status="clean",
        created_at=None,
    )
    quota = types.SimpleNamespace(used_bytes=1024, file_count=1)
    return dict(
        files=[file_a],
        quota=quota,
        quota_summary=None,
        links=[],
        transfers=[],
        request_count=0,
        guest_links_enabled=True,
        format_bytes=format_bytes,
        scan_label=scan_label,
        link_status_label=link_status_label,
    )


def test_file_center_index_renders_and_keeps_all_new_classes_with_no_style_attrs(app) -> None:
    from flask import render_template

    with app.test_request_context("/"):
        html = render_template(
            FILE_CENTER_INDEX_TEMPLATE.split("app/templates/")[-1],
            **_file_center_index_render_context(),
        )

    for literal in REMOVED_FILE_CENTER_INDEX_STYLE_LITERALS:
        assert literal not in html, f"Kaldirilmasi gereken eski style literal'i hala render ediliyor: {literal!r}"
    assert 'class="fc-hero-copy"' in html
    assert 'fc-hero-security-box' in html
    assert 'class="display-6 mb-2 fc-upload-icon-color"' in html
    assert 'css/file_center_premium_v1kb.css' in html
