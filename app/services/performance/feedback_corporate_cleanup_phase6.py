# -*- coding: utf-8 -*-
"""BYS360 Performans Geri Bildirim Hattı Kurumsal Son Kontrol servisi.

Bu servis canlıya yakın kullanım için görüşme ekranlarında teknik dil, güvenli
bağlantı, mobil uyum, boş veri mesajı, yetki ve beyaz ekran riskini denetler.
İdari karar üretmez; yalnızca kurulum/kalite kontrol özeti verir.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import re
import py_compile

import logging

logger = logging.getLogger(__name__)
ops_logger = logging.getLogger(__name__)

CHECK_FILES = [
    "app/templates/performance/feedback_aftercare.html",
    "app/templates/performance/feedback_meeting_guide.html",
    "app/templates/performance/feedback_integration_phase3.html",
    "app/templates/performance/feedback_followup_phase4.html",
    "app/templates/performance/feedback_final_gate_phase5.html",
    "app/templates/performance/feedback_corporate_cleanup_phase6.html",
]

ROUTE_FILES = [
    "app/performance/feedback_aftercare_routes.py",
    "app/performance/feedback_meeting_guide_routes.py",
    "app/performance/feedback_integration_routes.py",
    "app/performance/feedback_followup_phase4_routes.py",
    "app/performance/feedback_final_gate_phase5_routes.py",
    "app/performance/feedback_corporate_cleanup_phase6_routes.py",
]

SERVICE_FILES = [
    "app/services/performance/feedback_aftercare.py",
    "app/services/performance/feedback_meeting_guide.py",
    "app/services/performance/feedback_integration.py",
    "app/services/performance/feedback_followup_phase4.py",
    "app/services/performance/feedback_final_gate_phase5.py",
    "app/services/performance/feedback_corporate_cleanup_phase6.py",
]

MENU_MARKERS = [
    "BYS360_FEEDBACK_AFTERCARE_PHASE1_MENU",
    "BYS360_FEEDBACK_GUIDE_PHASE2_MENU",
    "BYS360_FEEDBACK_INTEGRATION_PHASE3_MENU",
    "BYS360_FEEDBACK_FOLLOWUP_PHASE4_MENU",
    "BYS360_FEEDBACK_FINAL_GATE_PHASE5_MENU",
    "BYS360_FEEDBACK_CORPORATE_CLEANUP_PHASE6_MENU",
]

ROUTE_MARKERS = [
    "BYS360_FEEDBACK_AFTERCARE_PHASE1_ROUTES_IMPORT",
    "BYS360_FEEDBACK_GUIDE_PHASE2_ROUTES_IMPORT",
    "BYS360_FEEDBACK_INTEGRATION_PHASE3_ROUTES_IMPORT",
    "BYS360_FEEDBACK_FOLLOWUP_PHASE4_ROUTES_IMPORT",
    "BYS360_FEEDBACK_FINAL_GATE_PHASE5_ROUTES_IMPORT",
    "BYS360_FEEDBACK_CORPORATE_CLEANUP_PHASE6_ROUTES_IMPORT",
]

# Sadece kullanıcıya görünen metinde aranır. CSS, Jinja yorumları ve HTML etiketleri temizlenir.
FORBIDDEN_VISIBLE_PATTERNS = [
    ("faz_label", re.compile(r"\bFaz\s*[1-9]\b", re.IGNORECASE)),
    ("phase_label", re.compile(r"\bphase\s*[1-9]?\b", re.IGNORECASE)),
    ("sync_label", re.compile(r"\bsync\b|senkronu", re.IGNORECASE)),
    ("workflow_label", re.compile(r"workflow\s*state", re.IGNORECASE)),
    ("debug_label", re.compile(r"\bdebug\b|traceback|stack trace", re.IGNORECASE)),
    ("dummy_label", re.compile(r"\bdummy\b|TODO|FIXME", re.IGNORECASE)),
    ("broken_html", re.compile(r"<\s*/\s*html\s*>|<\s+/html\s*>", re.IGNORECASE)),
    ("overlay_label", re.compile(r"\boverlay\b", re.IGNORECASE)),
]

QUICK_LINKS = [
    {"label": "Görüşme Sonrası Notlar", "endpoint": "main.performance_feedback_aftercare", "icon": "fa-solid fa-clipboard-check"},
    {"label": "Geri Bildirim Rehberi", "endpoint": "main.performance_feedback_meeting_guide", "icon": "fa-solid fa-comments"},
    {"label": "Karne Bağlantısı", "endpoint": "main.performance_feedback_integration", "icon": "fa-solid fa-link"},
    {"label": "Eylem Planı Takibi", "endpoint": "main.performance_feedback_followup", "icon": "fa-solid fa-calendar-check"},
    {"label": "Genel Kontrol", "endpoint": "main.performance_feedback_final_gate", "icon": "fa-solid fa-circle-check"},
]


def _project_root(root: str | Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    return Path(__file__).resolve().parents[3]


def read_text(root: Path, rel: str) -> str:
    path = root / rel
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def visible_text(text: str) -> str:
    text = re.sub(r"{#.*?#}", " ", text, flags=re.DOTALL)
    text = re.sub(r"{%.*?%}", " ", text, flags=re.DOTALL)
    text = re.sub(r"{{.*?}}", " ", text, flags=re.DOTALL)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<pre.*?</pre>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def check_files(root: Path) -> dict[str, Any]:
    items = []
    errors = []
    for rel in CHECK_FILES + ROUTE_FILES + SERVICE_FILES:
        ok = (root / rel).exists()
        items.append({"file": rel, "ok": ok})
        if not ok:
            errors.append(f"Eksik dosya: {rel}")
    return {"key": "files", "title": "Ekran Bileşenleri", "ok": not errors, "items": items, "errors": errors}


def check_python(root: Path) -> dict[str, Any]:
    items = []
    errors = []
    py_files = ROUTE_FILES + SERVICE_FILES + [
        "scripts/repair_performance_feedback_corporate_cleanup_phase6.py",
        "scripts/check_performance_feedback_corporate_cleanup_phase6.py",
    ]
    for rel in py_files:
        path = root / rel
        if not path.exists():
            continue
        try:
            py_compile.compile(str(path), doraise=True)
            items.append({"file": rel, "ok": True})
        except Exception as exc:
            logger.exception("BYS360 V6C guarded exception | file=app/services/performance/feedback_corporate_cleanup_phase6.py | line=136")
            items.append({"file": rel, "ok": False, "error": str(exc)})
            errors.append(f"Python sözdizimi hatası: {rel}: {exc}")
    return {"key": "python", "title": "Uygulama Sağlığı", "ok": not errors, "items": items, "errors": errors}


def check_corporate_language(root: Path) -> dict[str, Any]:
    items = []
    errors = []
    for rel in CHECK_FILES:
        text = read_text(root, rel)
        if not text:
            continue
        plain = visible_text(text)
        file_hits = []
        for key, pattern in FORBIDDEN_VISIBLE_PATTERNS:
            match = pattern.search(plain)
            if match:
                file_hits.append({"key": key, "value": match.group(0)})
        ok = not file_hits
        items.append({"file": rel, "ok": ok, "hits": file_hits})
        for hit in file_hits:
            errors.append(f"Kullanıcıya görünen teknik ifade: {rel} -> {hit['value']}")
    return {"key": "language", "title": "Kurumsal Dil Temizliği", "ok": not errors, "items": items, "errors": errors}


def check_safe_links(root: Path) -> dict[str, Any]:
    items = []
    errors = []
    raw_url_for = re.compile(r"(?<!safe_)url_for\s*\(")
    for rel in CHECK_FILES:
        text = read_text(root, rel)
        if not text:
            continue
        count = len(raw_url_for.findall(text))
        ok = count == 0
        items.append({"file": rel, "ok": ok, "raw_url_for_count": count})
        if not ok:
            errors.append(f"Güvenli bağlantı kullanımı eksik: {rel} içinde {count} raw url_for var")
    return {"key": "links", "title": "Sayfa Bağlantıları", "ok": not errors, "items": items, "errors": errors}


def check_mobile(root: Path) -> dict[str, Any]:
    items = []
    errors = []
    for rel in CHECK_FILES:
        text = read_text(root, rel)
        if not text:
            continue
        ok = "@media" in text and ("max-width" in text or "max_width" in text)
        items.append({"file": rel, "ok": ok})
        if not ok:
            errors.append(f"Mobil kırılım kontrolü eksik görünüyor: {rel}")
    return {"key": "mobile", "title": "Mobil Görünüm", "ok": not errors, "items": items, "errors": errors}


def check_empty_states(root: Path) -> dict[str, Any]:
    items = []
    warnings = []
    needles = ["bulunamadı", "kayıt", "henüz", "empty", "boş"]
    for rel in CHECK_FILES:
        text = visible_text(read_text(root, rel)).lower()
        if not text:
            continue
        ok = any(n in text for n in needles)
        items.append({"file": rel, "ok": ok})
        if not ok:
            warnings.append(f"Boş veri mesajı ayrıca gözden geçirilebilir: {rel}")
    return {"key": "empty", "title": "Boş Veri Mesajları", "ok": True, "items": items, "warnings": warnings}


def check_access(root: Path) -> dict[str, Any]:
    items = []
    errors = []
    for rel in ROUTE_FILES:
        text = read_text(root, rel)
        if not text:
            continue
        has_login = "@login_required" in text
        has_guard = any(token in text for token in ["access_denied", "_allowed", "is_manager_user", "allowed", "_is_admin", "_can_view_guide", "can_view_guide"])
        ok = has_login and has_guard
        items.append({"file": rel, "ok": ok, "login_required": has_login, "guard": has_guard})
        if not ok:
            errors.append(f"Yetki kontrolü zayıf görünüyor: {rel}")
    return {"key": "access", "title": "Yetki ve Erişim", "ok": not errors, "items": items, "errors": errors}


def check_menu_and_routes(root: Path) -> dict[str, Any]:
    base = read_text(root, "app/templates/base.html")
    init = read_text(root, "app/performance/__init__.py")
    items = []
    errors = []
    for marker in MENU_MARKERS:
        ok = marker in base
        items.append({"type": "menu", "marker": marker, "ok": ok})
        if not ok:
            errors.append(f"Menü markerı eksik: {marker}")
    for marker in ROUTE_MARKERS:
        ok = marker in init
        items.append({"type": "route_import", "marker": marker, "ok": ok})
        if not ok:
            errors.append(f"Route import markerı eksik: {marker}")
    return {"key": "menu", "title": "Menü ve Sayfa Bağlantıları", "ok": not errors, "items": items, "errors": errors}


def check_white_screen(root: Path) -> dict[str, Any]:
    items = []
    errors = []
    for rel in CHECK_FILES:
        text = read_text(root, rel)
        if not text:
            continue
        has_extends = "extends \"base.html\"" in text or "extends 'base.html'" in text
        has_content = "block content" in text
        broken_html = bool(re.search(r"<\s+/\s*html|<\s*/\s*html", text, flags=re.IGNORECASE))
        ok = has_extends and has_content and not broken_html
        items.append({"file": rel, "ok": ok, "extends_base": has_extends, "block_content": has_content, "broken_html": broken_html})
        if not ok:
            errors.append(f"Beyaz ekran riski kontrol edilmeli: {rel}")
    return {"key": "white_screen", "title": "Sayfa Açılış Sağlığı", "ok": not errors, "items": items, "errors": errors}


def check_database(root: Path) -> dict[str, Any]:
    """Canlı kontrolünde temel geri bildirim veritabanı yapılarını doğrular."""
    required_tables = {
        "users": "Kullanıcı omurgası",
        "performance_periods": "Performans dönemleri",
        "performance_evaluations": "Performans değerlendirmeleri",
        "feedback_meetings": "Geri bildirim görüşmeleri",
        "feedback_meeting_action_plans": "Eylem planları",
        "performance_interim_notes": "Dönem içi notlar",
        "performance_archived_results": "Geçmiş karne arşivi",
    }
    try:
        from sqlalchemy import inspect
        from app.extensions import db

        inspector = inspect(db.engine)
        existing = set(inspector.get_table_names())
        items = []
        errors = []
        for table, label in required_tables.items():
            ok = table in existing
            items.append({"table": table, "label": label, "ok": ok})
            if not ok:
                errors.append(f"Veritabanı tablosu eksik: {table} ({label})")
        return {"key": "database", "title": "Veritabanı Kontrolü", "ok": not errors, "items": items, "errors": errors}
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        try:
            from app.extensions import db
            db.session.rollback()
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            import logging
            logging.getLogger(__name__).exception("BYS360_CLAUDE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/feedback_corporate_cleanup_phase6.py")
        return {
            "key": "database",
            "title": "Veritabanı Kontrolü",
            "ok": False,
            "items": [],
            "errors": [f"Veritabanı kontrolü çalıştırılamadı: {exc}"],
        }


def build_phase6_context(root: str | Path | None = None, include_database: bool = False) -> dict[str, Any]:
    project_root = _project_root(root)
    checks = [
        check_files(project_root),
        check_python(project_root),
        check_corporate_language(project_root),
        check_safe_links(project_root),
        check_mobile(project_root),
        check_empty_states(project_root),
        check_access(project_root),
        check_menu_and_routes(project_root),
        check_white_screen(project_root),
    ]
    if include_database:
        checks.append(check_database(project_root))
    errors: list[str] = []
    warnings: list[str] = []
    for check in checks:
        errors.extend(check.get("errors", []) or [])
        warnings.extend(check.get("warnings", []) or [])
    total = len(checks)
    ok_count = sum(1 for c in checks if c.get("ok"))
    ready_percent = int(round((ok_count / total) * 100)) if total else 0
    return {
        "ok": not errors,
        "ready_percent": ready_percent,
        "checks": checks,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "ok_count": ok_count,
            "total": total,
            "error_count": len(errors),
            "warning_count": len(warnings),
        },
        "quick_links": QUICK_LINKS,
        "database": {"available": bool(include_database) and not any(c.get("key") == "database" and not c.get("ok") for c in checks), "checked": bool(include_database)},
    }


if __name__ == "__main__":
    import json
    ops_logger.info(str(json.dumps(build_phase6_context(), ensure_ascii=False, indent=2)))
