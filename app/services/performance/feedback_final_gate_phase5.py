# -*- coding: utf-8 -*-
"""BYS360 Performans Geri Bildirim Süreci Final Kontrol servisi.

Bu servis görüşme sonrası notlar, görüşme rehberi, karne entegrasyonu ve
eylem planı takibi bileşenlerinin birlikte kurulu olup olmadığını denetler.
Uygulama ekranı için güvenli ve kısa kontrol özeti üretir; idari karar vermez.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import logging
logger = logging.getLogger(__name__)


PHASE_COMPONENTS: list[dict[str, Any]] = [
    {
        "key": "aftercare",
        "title": "Görüşme Sonrası Notlar",
        "description": "Hazırlık, görüşme özeti, personel son sözü, güçlü yönler, gelişim alanları ve eylem planı kayıtları.",
        "files": [
            "app/services/performance/feedback_aftercare.py",
            "app/performance/feedback_aftercare_routes.py",
            "app/templates/performance/feedback_aftercare.html",
        ],
        "markers": {
            "app/performance/__init__.py": "BYS360_FEEDBACK_AFTERCARE_PHASE1_ROUTES_IMPORT",
            "app/templates/base.html": "BYS360_FEEDBACK_AFTERCARE_PHASE1_MENU",
        },
        "needles": {
            "app/services/performance/feedback_aftercare.py": [
                "feedback_meeting_preparations",
                "feedback_meeting_after_notes",
                "feedback_meeting_action_plans",
                "ensure_feedback_aftercare_schema",
            ],
            "app/templates/performance/feedback_aftercare.html": [
                "Görüşme Sonrası Notlar",
                "Eylem Planı",
                "Personel son sözü",
            ],
        },
    },
    {
        "key": "guide",
        "title": "Geri Bildirim Rehberi",
        "description": "60 dakikalık akış, senaryo bazlı açılış cümleleri, içgörü soruları ve SBI örnek bankası.",
        "files": [
            "app/services/performance/feedback_meeting_guide.py",
            "app/performance/feedback_meeting_guide_routes.py",
            "app/templates/performance/feedback_meeting_guide.html",
        ],
        "markers": {
            "app/performance/__init__.py": "BYS360_FEEDBACK_GUIDE_PHASE2_ROUTES_IMPORT",
            "app/templates/base.html": "BYS360_FEEDBACK_GUIDE_PHASE2_MENU",
        },
        "needles": {
            "app/services/performance/feedback_meeting_guide.py": [
                "FLOW_STEPS",
                "SCENARIOS",
                "SBI_EXAMPLES",
                "opening_sentences",
            ],
            "app/templates/performance/feedback_meeting_guide.html": [
                "60 Dakikalık Görüşme Akış Rehberi",
                "Senaryo",
                "SBI",
            ],
        },
    },
    {
        "key": "integration",
        "title": "Karne ve Süreç Hafızası Entegrasyonu",
        "description": "Not karnesi, dönem içi not, görüşme sonrası not ve eylem planını tek süreç ekranında birleştirir.",
        "files": [
            "app/services/performance/feedback_integration.py",
            "app/performance/feedback_integration_routes.py",
            "app/templates/performance/feedback_integration_phase3.html",
        ],
        "markers": {
            "app/performance/__init__.py": "BYS360_FEEDBACK_INTEGRATION_PHASE3_ROUTES_IMPORT",
            "app/templates/base.html": "BYS360_FEEDBACK_INTEGRATION_PHASE3_MENU",
        },
        "needles": {
            "app/services/performance/feedback_integration.py": [
                "build_integration_context",
                "scorecards",
                "interim_notes",
                "aftercare_meetings",
                "action_plans",
            ],
            "app/templates/performance/feedback_integration_phase3.html": [
                "Karne",
                "Dönem İçi Notlar",
                "Görüşme Sonrası Takip",
                "Süreç Zaman Çizelgesi",
            ],
        },
    },
    {
        "key": "followup",
        "title": "Eylem Planı Takibi",
        "description": "30 günlük mini takip, yaklaşan/geciken aksiyon uyarısı, bildirim ve mail log kaydı.",
        "files": [
            "app/services/performance/feedback_followup_phase4.py",
            "app/performance/feedback_followup_phase4_routes.py",
            "app/templates/performance/feedback_followup_phase4.html",
        ],
        "markers": {
            "app/performance/__init__.py": "BYS360_FEEDBACK_FOLLOWUP_PHASE4_ROUTES_IMPORT",
            "app/templates/base.html": "BYS360_FEEDBACK_FOLLOWUP_PHASE4_MENU",
        },
        "needles": {
            "app/services/performance/feedback_followup_phase4.py": [
                "feedback_action_followup_notices",
                "normalize_30_day_followups",
                "generate_followup_notices",
                "mail_logs",
                "notifications",
            ],
            "app/templates/performance/feedback_followup_phase4.html": [
                "Eylem Planı Takibi",
                "30 günlük mini takip",
                "Bildirim ve Mail Log Kayıtları",
            ],
        },
    },
]

SCENARIOS: list[dict[str, Any]] = [
    {
        "key": "prep_screen",
        "title": "1. Görüşme hazırlığı kayda alınabiliyor",
        "intent": "Amir görüşmeye girmeden amaç, somut örnek, açılış cümlesi ve hassas konuları hazırlayabilmeli.",
        "requires": [
            ("app/services/performance/feedback_aftercare.py", "feedback_meeting_preparations"),
            ("app/services/performance/feedback_aftercare.py", "opening_sentence"),
            ("app/services/performance/feedback_aftercare.py", "sbi_examples"),
        ],
    },
    {
        "key": "after_notes",
        "title": "2. Görüşme sonrası not ve özet tutuluyor",
        "intent": "Görüşme özeti, personelin değerlendirmesi, amir gözlemi ve son söz kayıt altında olmalı.",
        "requires": [
            ("app/services/performance/feedback_aftercare.py", "feedback_meeting_after_notes"),
            ("app/services/performance/feedback_aftercare.py", "employee_self_assessment"),
            ("app/services/performance/feedback_aftercare.py", "employee_final_words"),
        ],
    },
    {
        "key": "action_plan",
        "title": "3. Eylem planı ve takip tarihi oluşuyor",
        "intent": "Görüşme somut aksiyon, sorumlu, hedef tarih ve takip notuyla kapanmalı.",
        "requires": [
            ("app/services/performance/feedback_aftercare.py", "feedback_meeting_action_plans"),
            ("app/services/performance/feedback_aftercare.py", "smart_description"),
            ("app/services/performance/feedback_followup_phase4.py", "follow_up_check_date"),
        ],
    },
    {
        "key": "flow_60",
        "title": "4. 60 dakikalık görüşme akışı görünür",
        "intent": "Açılış, öz değerlendirme, yönetici puanı, güçlü yön, gelişim alanı ve kapanış adımları rehberde bulunmalı.",
        "requires": [
            ("app/services/performance/feedback_meeting_guide.py", "FLOW_STEPS"),
            ("app/services/performance/feedback_meeting_guide.py", "Açılış"),
            ("app/services/performance/feedback_meeting_guide.py", "Öz değerlendirme"),
            ("app/services/performance/feedback_meeting_guide.py", "Eylem planı"),
        ],
    },
    {
        "key": "scenario_bank",
        "title": "5. Senaryo bazlı açılış cümleleri ve sorular var",
        "intent": "Düşük performans, yüksek performans, terfi, itiraz ve hassas durumlar için yöneticinin dili desteklenmeli.",
        "requires": [
            ("app/services/performance/feedback_meeting_guide.py", "SCENARIOS"),
            ("app/services/performance/feedback_meeting_guide.py", "openings"),
            ("app/services/performance/feedback_meeting_guide.py", "questions"),
        ],
    },
    {
        "key": "sbi_bank",
        "title": "6. SBI örnek bankası hazır",
        "intent": "Geri bildirim kişiye değil; durum, davranış ve etki üzerinden kurulmalı.",
        "requires": [
            ("app/services/performance/feedback_meeting_guide.py", "SBI_EXAMPLES"),
            ("app/templates/performance/feedback_meeting_guide.html", "SBI"),
        ],
    },
    {
        "key": "scorecard_memory",
        "title": "7. Karne süreç hafızasına bağlanıyor",
        "intent": "Karne, dönem içi notlar ve görüşme sonrası kayıtlar tek bakışta okunabilmeli.",
        "requires": [
            ("app/services/performance/feedback_integration.py", "scorecards"),
            ("app/services/performance/feedback_integration.py", "interim_notes"),
            ("app/services/performance/feedback_integration.py", "aftercare_meetings"),
            ("app/templates/performance/feedback_integration_phase3.html", "Süreç Zaman Çizelgesi"),
        ],
    },
    {
        "key": "followup_notice",
        "title": "8. Yaklaşan ve geciken aksiyonlar izleniyor",
        "intent": "30 günlük mini takip, gecikme uyarısı, bildirim ve mail log kaydı üretilebilmeli.",
        "requires": [
            ("app/services/performance/feedback_followup_phase4.py", "normalize_30_day_followups"),
            ("app/services/performance/feedback_followup_phase4.py", "generate_followup_notices"),
            ("app/services/performance/feedback_followup_phase4.py", "mail_logs"),
            ("app/services/performance/feedback_followup_phase4.py", "notifications"),
        ],
    },
    {
        "key": "visibility",
        "title": "9. Menü ve route görünürlüğü kontrollü",
        "intent": "Yönetici/performans yetkilisi erişimi menü ve backend tarafında birlikte korunmalı.",
        "requires": [
            ("app/templates/base.html", "BYS360_FEEDBACK_AFTERCARE_PHASE1_MENU"),
            ("app/templates/base.html", "BYS360_FEEDBACK_GUIDE_PHASE2_MENU"),
            ("app/templates/base.html", "BYS360_FEEDBACK_INTEGRATION_PHASE3_MENU"),
            ("app/templates/base.html", "BYS360_FEEDBACK_FOLLOWUP_PHASE4_MENU"),
        ],
    },
    {
        "key": "corporate_language",
        "title": "10. Kullanıcı ekranı kurumsal ve teknik dilden arındırılmış",
        "intent": "Kullanıcıya phase/sync/workflow gibi teknik ifadeler gösterilmemeli; Türkçe ve kurumsal dil korunmalı.",
        "requires": [
            ("app/templates/performance/feedback_aftercare.html", "Görüşme Sonrası"),
            ("app/templates/performance/feedback_meeting_guide.html", "Geri Bildirim"),
            ("app/templates/performance/feedback_integration_phase3.html", "Süreç Hafızası"),
            ("app/templates/performance/feedback_followup_phase4.html", "Eylem Planı"),
        ],
        "forbidden_templates": ["workflow state", "phase sync", "authorized_scope", "scorecard_pending", "president_pending"],
    },
]

FORBIDDEN_USER_VISIBLE = ["workflow state", "phase sync", "authorized_scope", "scorecard_pending", "president_pending", "blocked_president_pending"]


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _read(root: Path, rel: str) -> str:
    path = root / rel
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _exists(root: Path, rel: str) -> bool:
    return (root / rel).exists()


def _contains(root: Path, rel: str, needle: str) -> bool:
    return needle in _read(root, rel)


def _template_forbidden_hits(root: Path, forbidden: list[str] | None = None) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    terms = [t.lower() for t in (forbidden or FORBIDDEN_USER_VISIBLE)]
    template_files = [
        "app/templates/performance/feedback_aftercare.html",
        "app/templates/performance/feedback_meeting_guide.html",
        "app/templates/performance/feedback_integration_phase3.html",
        "app/templates/performance/feedback_followup_phase4.html",
        "app/templates/performance/feedback_final_gate_phase5.html",
    ]
    for rel in template_files:
        text = _read(root, rel).lower()
        if not text:
            continue
        for term in terms:
            if term in text:
                hits.append({"file": rel, "term": term})
    return hits


def _component_status(root: Path, component: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    checks: list[dict[str, Any]] = []
    for rel in component.get("files", []):
        ok = _exists(root, rel)
        checks.append({"type": "file", "target": rel, "ok": ok})
        if not ok:
            errors.append(f"Eksik dosya: {rel}")
    for rel, marker in component.get("markers", {}).items():
        ok = _contains(root, rel, marker)
        checks.append({"type": "marker", "target": f"{rel} -> {marker}", "ok": ok})
        if not ok:
            errors.append(f"Marker bulunamadı: {rel} -> {marker}")
    for rel, needles in component.get("needles", {}).items():
        for needle in needles:
            ok = _contains(root, rel, needle)
            checks.append({"type": "content", "target": f"{rel} -> {needle}", "ok": ok})
            if not ok:
                errors.append(f"Beklenen içerik yok: {rel} -> {needle}")
    total = len(checks) or 1
    passed = sum(1 for c in checks if c.get("ok"))
    return {
        "key": component["key"],
        "title": component["title"],
        "description": component["description"],
        "ok": not errors,
        "passed": passed,
        "total": total,
        "percent": round(passed * 100 / total),
        "checks": checks,
        "errors": errors,
    }


def _scenario_status(root: Path, scenario: dict[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    errors: list[str] = []
    for rel, needle in scenario.get("requires", []):
        ok = _contains(root, rel, needle)
        checks.append({"file": rel, "needle": needle, "ok": ok})
        if not ok:
            errors.append(f"{rel} içinde beklenen içerik yok: {needle}")
    forbidden_hits = _template_forbidden_hits(root, scenario.get("forbidden_templates")) if scenario.get("forbidden_templates") else []
    for hit in forbidden_hits:
        errors.append(f"Kullanıcı ekranında teknik ifade bulundu: {hit['file']} -> {hit['term']}")
    total = len(checks) + (1 if scenario.get("forbidden_templates") else 0)
    passed = sum(1 for c in checks if c.get("ok")) + (1 if scenario.get("forbidden_templates") and not forbidden_hits else 0)
    if total == 0:
        total = 1
    return {
        "key": scenario["key"],
        "title": scenario["title"],
        "intent": scenario["intent"],
        "ok": not errors,
        "passed": passed,
        "total": total,
        "checks": checks,
        "errors": errors,
    }


def _database_status() -> dict[str, Any]:
    """Canlı uygulama bağlamında tablo varlığını okumaya çalışır; başarısızsa engelleyici sayılmaz."""
    table_names = [
        "feedback_meetings",
        "feedback_meeting_preparations",
        "feedback_meeting_after_notes",
        "feedback_meeting_action_plans",
        "feedback_action_followup_notices",
        "mail_logs",
        "notifications",
    ]
    try:
        from sqlalchemy import inspect  # type: ignore
        from app.extensions import db  # type: ignore
        inspector = inspect(db.engine)
        rows = []
        for table in table_names:
            try:
                rows.append({"table": table, "exists": bool(inspector.has_table(table))})
            except Exception:
                logger.exception("BYS360 V6C guarded exception | file=app/services/performance/feedback_final_gate_phase5.py | line=361")
                rows.append({"table": table, "exists": False})
        return {"available": True, "tables": rows, "ok": all(r["exists"] for r in rows[:4])}
    except Exception as exc:  # pragma: no cover
        logger.exception("BYS360 V6C guarded exception | file=app/services/performance/feedback_final_gate_phase5.py | line=364")
        return {"available": False, "ok": None, "message": str(exc)}


def build_phase5_context(root_path: str | Path | None = None, include_database: bool = True) -> dict[str, Any]:
    root = Path(root_path) if root_path else _project_root()
    components = [_component_status(root, item) for item in PHASE_COMPONENTS]
    scenarios = [_scenario_status(root, item) for item in SCENARIOS]
    all_errors = [err for c in components for err in c.get("errors", [])] + [err for s in scenarios for err in s.get("errors", [])]
    forbidden_hits = _template_forbidden_hits(root)
    for hit in forbidden_hits:
        all_errors.append(f"Kullanıcı ekranında teknik ifade bulundu: {hit['file']} -> {hit['term']}")
    total_units = len(components) + len(scenarios) + 1
    passed_units = sum(1 for c in components if c.get("ok")) + sum(1 for s in scenarios if s.get("ok")) + (0 if forbidden_hits else 1)
    database = _database_status() if include_database else {"available": False, "ok": None, "message": "Komut satırı kontrolünde veritabanı kontrolü atlandı."}
    warnings: list[str] = []
    if not database.get("available"):
        warnings.append("Veritabanı bağlantısı uygulama bağlamında okunamadı; dosya ve kurulum kontrolü yapıldı.")
    elif database.get("ok") is False:
        warnings.append("Bazı görüşme takip tabloları veritabanında görünmüyor; önce önceki kurulum scriptlerini çalıştırın.")
    ready_percent = round(passed_units * 100 / total_units)
    return {
        "root": str(root),
        "ok": not all_errors,
        "ready_percent": ready_percent,
        "components": components,
        "scenarios": scenarios,
        "errors": all_errors,
        "warnings": warnings,
        "forbidden_hits": forbidden_hits,
        "database": database,
        "summary": {
            "component_total": len(components),
            "component_ok": sum(1 for c in components if c.get("ok")),
            "scenario_total": len(scenarios),
            "scenario_ok": sum(1 for s in scenarios if s.get("ok")),
            "error_count": len(all_errors),
            "warning_count": len(warnings),
        },
        "quick_links": [
            {"label": "Görüşme Sonrası Notlar", "endpoint": "main.performance_feedback_aftercare", "icon": "fa-solid fa-clipboard-check"},
            {"label": "Geri Bildirim Rehberi", "endpoint": "main.performance_feedback_meeting_guide", "icon": "fa-solid fa-comments"},
            {"label": "Geri Bildirim Entegrasyonu", "endpoint": "main.performance_feedback_integration", "icon": "fa-solid fa-link"},
            {"label": "Eylem Planı Takibi", "endpoint": "main.performance_feedback_followup", "icon": "fa-solid fa-calendar-check"},
        ],
    }
