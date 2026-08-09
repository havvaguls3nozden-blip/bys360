from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from flask import current_app
from sqlalchemy import inspect, text

from app.extensions import db
from app.services.performance.meeting_development import (
    DEFAULT_SETTINGS,
    build_meeting_development_summary,
    ensure_meeting_foundation_schema,
)
from app.services.performance.meeting_development_gate import (
    FORBIDDEN_UI_TERMS,
    STATUS_LABELS,
    TEST_SCENARIOS,
    build_gate_summary,
)

ops_logger = logging.getLogger(__name__)
logger = ops_logger

"""BYS360 Toplantı Geliştirme Faz 4 final canlı kontrol servisi."""

REQUIRED_TABLES = [
    "performance_employee_categories",
    "performance_employee_category_assignments",
    "performance_period_targets",
    "performance_period_observation_notes",
    "performance_legacy_scorecards",
]

REQUIRED_FILES = [
    "app/performance/meeting_development_routes.py",
    "app/performance/meeting_test_routes.py",
    "app/performance/meeting_development_faz3_routes.py",
    "app/performance/meeting_development_faz4_routes.py",
    "app/services/performance/meeting_development.py",
    "app/services/performance/meeting_development_gate.py",
    "app/services/performance/meeting_development_final_gate.py",
    "app/templates/performance/meeting_development.html",
    "app/templates/performance/meeting_development_scenarios.html",
    "app/templates/performance/meeting_development_faz3.html",
    "app/templates/performance/meeting_development_faz4.html",
]

REQUIRED_TOKENS = {
    "app/performance/__init__.py": [
        "meeting_development_routes",
        "meeting_test_routes",
        "meeting_development_faz3_routes",
        "meeting_development_faz4_routes",
    ],
    "app/templates/base.html": [
        "Toplantı Geliştirme",
        "Toplantı Testleri",
        "Toplantı Derinleştirme",
        "Final Kontrol",
        "meeting-development/final-gate",
    ],
}

# BYS360_NAV_CANONICAL_SOURCE_FIX: menu_registry.py bir bridge/re-export
# dosyasıdır; menü kayıtlarının kanonik kaynağı değildir (bkz. dosyanın
# kendi "P11-D2/P11-D3 ... veri bloğu data modülüne taşındı" yorumları).
# Bu dört menü kaydı artık menu_registry.py'nin ham metninde literal arama
# ile değil, gerçek kanonik registry verisine (MENU_SECTIONS) ve canlı
# url_map'e karşı davranışsal olarak doğrulanır.
REQUIRED_CANONICAL_MENU_ITEMS = [
    {"key": "performance_meeting_development", "endpoint": "main.performance_meeting_development"},
    {"key": "performance_meeting_test_scenarios", "endpoint": "main.performance_meeting_test_scenarios"},
    {"key": "performance_meeting_development_faz3", "endpoint": "main.performance_meeting_development_faz3"},
    {"key": "performance_meeting_final_gate", "endpoint": "main.performance_meeting_final_gate"},
]


def _canonical_menu_item(key: str) -> dict[str, Any] | None:
    try:
        from app.menu_registry_data_sections import MENU_SECTIONS
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return None
    for section in MENU_SECTIONS:
        for item in section.get("items", []):
            if item.get("key") == key:
                return item
    return None


def _menu_item_canonically_registered(key: str, endpoint: str) -> bool:
    item = _canonical_menu_item(key)
    if not item or item.get("endpoint") != endpoint:
        return False
    try:
        from app.route_support import MANAGER_FAMILY_ROLES
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return False
    if not (set(item.get("required_roles") or []) & MANAGER_FAMILY_ROLES):
        return False
    try:
        return endpoint in current_app.view_functions
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return False

VISIBLE_TEMPLATE_SCAN = [
    "app/templates/performance/meeting_development.html",
    "app/templates/performance/meeting_development_scenarios.html",
    "app/templates/performance/meeting_development_faz3.html",
    "app/templates/performance/meeting_development_faz4.html",
    "app/templates/performance/president_approval_scorecard.html",
    "app/templates/performance/president_approval_scorecard_v2.html",
]

FINAL_CHECKS = [
    {"code": "F1_SETTINGS", "title": "Toplantı ayarları yüklü", "expected": "1/5 açıklama ayarı, 3. amir opsiyonu, grup ortalaması ve geçmiş karne arşivi ayarları modül ayarlarında görünür.", "priority": "P0"},
    {"code": "F2_TEST_SCENARIOS", "title": "Pilot senaryoları tamamlanabilir", "expected": "10 senaryolu test ekranı erişilebilir; düşük performans, görünürlük, 3. amir ve arşiv senaryoları listelenir.", "priority": "P0"},
    {"code": "F3_FUNCTIONAL_FOUNDATION", "title": "Kategori, geçmiş karne ve ara not altyapısı hazır", "expected": "Personel kategori eşleştirme, geçmiş karne arşivi ve ara dönem notları için tablolar hazırdır.", "priority": "P0"},
    {"code": "LOW_SCORE_LOCK", "title": "70 altı yayın kilidi korunur", "expected": "70 altı sonuç İK/Admin ön kontrolü ve Başkan onayı tamamlanmadan personele kesin/yayınlanmış gösterilmez.", "priority": "P0"},
    {"code": "NO_TECHNICAL_LANGUAGE", "title": "Teknik ifadeler ekrana sızmaz", "expected": "Faz senkronu, workflow state ve scorecard_pending gibi teknik ifadeler kullanıcı ekranında görünmez.", "priority": "P0"},
    {"code": "MENU_AND_PERMISSION", "title": "Menü ve yetki kontrolü birlikte çalışır", "expected": "Toplantı geliştirme ekranları yalnızca yönetici/üst yetki kapsamındaki rollerde görünür; backend erişim kontrolü korunur.", "priority": "P0"},
]


def _project_root() -> Path:
    try:
        return Path(current_app.root_path).resolve().parent
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return Path.cwd().resolve()


def _read_text(rel: str) -> str:
    path = _project_root() / rel
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def _has_table(name: str) -> bool:
    try:
        return inspect(db.engine).has_table(name)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return False


def _scalar(sql: str, params: dict[str, Any] | None = None, default: Any = 0) -> Any:
    try:
        return db.session.execute(text(sql), params or {}).scalar() or default
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _setting_exists(key: str) -> bool:
    if not _has_table("module_settings"):
        return False
    return bool(_scalar("SELECT id FROM module_settings WHERE module_key='performance' AND setting_key=:key LIMIT 1", {"key": key}, default=0))


def build_final_gate_context() -> dict[str, Any]:
    ensure_meeting_foundation_schema(seed_categories=True)
    db_summary = build_gate_summary()
    meeting_summary = build_meeting_development_summary()
    errors: list[str] = []
    warnings: list[str] = []
    passed: list[str] = []
    root = _project_root()

    for rel in REQUIRED_FILES:
        if not (root / rel).exists():
            errors.append(f"Eksik dosya: {rel}")
        else:
            passed.append(f"Dosya hazır: {rel}")

    for rel, tokens in REQUIRED_TOKENS.items():
        content = _read_text(rel)
        if not content:
            errors.append(f"Okunamadı: {rel}")
            continue
        for token in tokens:
            if token not in content:
                errors.append(f"Eksik işaret: {rel} -> {token}")
            else:
                passed.append(f"İşaret hazır: {token}")

    for item in REQUIRED_CANONICAL_MENU_ITEMS:
        key = item["key"]
        endpoint = item["endpoint"]
        if _menu_item_canonically_registered(key, endpoint):
            passed.append(f"Menü kaydı doğrulandı: {key}")
        else:
            errors.append(f"Menü kaydı doğrulanamadı: {key} (endpoint={endpoint})")

    for table in REQUIRED_TABLES:
        if _has_table(table):
            passed.append(f"Tablo hazır: {table}")
        else:
            errors.append(f"Eksik tablo: {table}")

    for key in DEFAULT_SETTINGS:
        if _setting_exists(key):
            passed.append(f"Ayar hazır: {key}")
        else:
            warnings.append(f"Ayar veritabanında görünmedi: {key}")

    for rel in VISIBLE_TEMPLATE_SCAN:
        content = _read_text(rel)
        if not content:
            continue
        for term in FORBIDDEN_UI_TERMS:
            if term in content:
                if rel.endswith("meeting_development_faz4.html"):
                    continue
                warnings.append(f"Teknik ifade kontrol edilmeli: {rel} -> {term}")

    status = "GEÇTİ" if not errors else "KONTROL GEREKİYOR"
    return {
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "passed": passed[:80],
        "final_checks": FINAL_CHECKS,
        "db_summary": db_summary,
        "meeting_summary": meeting_summary,
        "test_scenarios": [scenario.__dict__ for scenario in TEST_SCENARIOS],
        "status_labels": STATUS_LABELS,
        "forbidden_terms": FORBIDDEN_UI_TERMS,
        "required_tables": REQUIRED_TABLES,
        "required_settings": list(DEFAULT_SETTINGS.keys()),
    }


def print_final_gate_report() -> int:
    context = build_final_gate_context()
    ops_logger.info("BYS360 Toplantı Geliştirme Faz 4 Final Gate")
    ops_logger.info(str(f"DURUM={context['status']}"))
    ops_logger.info(str(f"HATA={len(context['errors'])} UYARI={len(context['warnings'])}"))
    for item in context["errors"]:
        ops_logger.info(" ".join(str(x) for x in ("HATA |", item)))
    for item in context["warnings"]:
        ops_logger.info(" ".join(str(x) for x in ("UYARI |", item)))
    if context["errors"]:
        return 1
    ops_logger.info("BYS360_MEETING_DEVELOPMENT_FAZ4_FINAL_GATE_OK")
    return 0
