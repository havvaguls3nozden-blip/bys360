from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any

from flask import current_app

from app.core.datetime_utils import utc_now
from app.services.ai.client import get_provider_snapshot
from app.services.ai.schema_guard import get_ai_schema_status


@dataclass(frozen=True)
class PreflightTarget:
    key: str
    label: str
    detail: str = ""

CRITICAL_ENDPOINTS: tuple[PreflightTarget, ...] = (
    PreflightTarget("main.dashboard", "Ana dashboard", "Üst yönetim görünümü"),
    PreflightTarget("main.admin_ai_center", "AI kontrol merkezi", "Yönetim ve denetim merkezi"),
    PreflightTarget("main.admin_ai_module_health", "AI modül sağlığı", "Modül bazlı risk tablosu"),
    PreflightTarget("main.admin_ai_operations_report", "AI operasyon raporu", "Modüller arası ortak karar masası"),
    PreflightTarget("main.performance_task_management_recommendations", "Performans AI öneri merkezi", "Görev yönetimi AI önerileri"),
    PreflightTarget("main.performance_task_management_recommendations_export", "Performans AI dışa aktarımı", "Performans AI öneri dışa aktarımı"),
    PreflightTarget("main.hr_leave_management", "İzin yönetimi", "İzin AI özeti"),
    PreflightTarget("main.hr_leave_ai_report_export", "İzin AI raporu dışa aktarımı", "İzin yönetici raporu"),
    PreflightTarget("main.hr_attendance_management", "Devamsızlık & vekâlet", "Vekâlet AI özeti"),
    PreflightTarget("main.hr_attendance_ai_report_export", "Vekâlet AI raporu dışa aktarımı", "Devamsızlık/vekâlet yönetici raporu"),
)


CRITICAL_TEMPLATES: tuple[PreflightTarget, ...] = (
    PreflightTarget("admin_ai_center.html", "AI kontrol merkezi şablonu"),
    PreflightTarget("admin_ai_module_health.html", "AI modül sağlığı şablonu"),
    PreflightTarget("admin_ai_operations_report.html", "AI operasyon raporu şablonu"),
    PreflightTarget("admin_ai_schema_not_ready.html", "AI korumalı mod şablonu"),
    PreflightTarget("assignment_recommendations.html", "Performans AI öneri şablonu"),
    PreflightTarget("hr_leave.html", "İzin yönetimi şablonu"),
    PreflightTarget("hr_attendance.html", "Devamsızlık & vekâlet şablonu"),
    PreflightTarget("dashboard.html", "Ana dashboard şablonu"),
)

IMPORT_CHECKS: tuple[PreflightTarget, ...] = (
    PreflightTarget("app.models:AIRequestLog", "AI istek günlüğü dışa aktarımı"),
    PreflightTarget("app.models:AIRecommendation", "AI öneri kaydı dışa aktarımı"),
    PreflightTarget("app.models:AIFeedbackLog", "AI geri bildirim günlüğü dışa aktarımı"),
    PreflightTarget("app.models:AIRedactionRule", "AI maskeleme kuralı dışa aktarımı"),
    PreflightTarget("app.models:AISummaryCache", "AI özet önbelleği dışa aktarımı"),
    PreflightTarget("app.services.ai.audit:log_ai_request", "AI audit request log yardımcıları"),
    PreflightTarget("app.services.ai.audit:upsert_ai_summary_cache", "AI summary cache yardımcıları"),
    PreflightTarget("app.services.ai.dashboard_panels:build_dashboard_ai_operations_bridge", "Dashboard AI operasyon köprüsü"),
    PreflightTarget("app.services.ai.schema_guard:get_ai_schema_status", "AI şema guard yardımcıları"),
)


def _ok_result(category: str, key: str, label: str, detail: str = "") -> dict[str, Any]:
    return {
        "category": category,
        "key": key,
        "label": label,
        "status": "ok",
        "tone": "success",
        "detail": detail or "Hazır görünüyor.",
    }


def _warning_result(category: str, key: str, label: str, detail: str, *, advice: str = "") -> dict[str, Any]:
    return {
        "category": category,
        "key": key,
        "label": label,
        "status": "warning",
        "tone": "warning",
        "detail": detail,
        "advice": advice,
    }


def _template_exists(template_name: str) -> bool:
    loader = current_app.jinja_env.loader
    if loader is None:  # pragma: no cover
        return False
    try:
        loader.get_source(current_app.jinja_env, template_name)
        return True
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return False


def _import_symbol(path: str) -> tuple[bool, str]:
    module_name, _, symbol_name = path.partition(":")
    try:
        module = importlib.import_module(module_name)
        if symbol_name:
            getattr(module, symbol_name)
        return True, "Import zinciri hazır."
    except Exception as exc:  # pragma: no cover - depends on runtime env
        return False, str(exc)


def build_ai_preflight_snapshot() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    schema_status = get_ai_schema_status()
    if schema_status.get("ready"):
        checks.append(
            _ok_result(
                "schema",
                "ai_schema",
                "AI şema hazırlığı",
                f"{len(schema_status.get('errors') or [])} hata ile temiz görünüyor.",
            )
        )
    else:
        checks.append(
            _warning_result(
                "schema",
                "ai_schema",
                "AI şema hazırlığı",
                str(schema_status.get("message") or "AI şeması eksik."),
                advice="Migration / şema onarımı tamamlanmadan AI ekranları korumalı modda çalışır.",
            )
        )

    provider_snapshot = get_provider_snapshot()
    if provider_snapshot.get("ready_for_live_provider"):
        checks.append(
            _ok_result(
                "provider",
                "ai_provider",
                "AI sağlayıcı hazırlığı",
                "Gerçek sağlayıcı bağlantısı canlı kullanım için hazır görünüyor.",
            )
        )
    else:
        provider_detail = "AI sağlayıcısı şu anda canlı hazır değil."
        if provider_snapshot.get("using_stub_mode"):
            provider_detail = "AI katmanı yerel taslak modda çalışıyor."
        checks.append(
            _warning_result(
                "provider",
                "ai_provider",
                "AI sağlayıcı hazırlığı",
                provider_detail,
                advice="Canlı kullanıcı görünürlüğü açılacaksa gerçek sağlayıcı bağlantısı ve fallback politikası birlikte doğrulanmalı.",
            )
        )

    for item in IMPORT_CHECKS:
        ok, message = _import_symbol(item.key)
        if ok:
            checks.append(_ok_result("import", item.key, item.label, item.detail or message))
        else:
            checks.append(
                _warning_result(
                    "import",
                    item.key,
                    item.label,
                    f"Import hatası: {message}",
                    advice="İlgili dışa aktarma/içe aktarma zinciri güncellenmeli.",
                )
            )

    view_functions = current_app.view_functions
    for item in CRITICAL_ENDPOINTS:
        if item.key in view_functions:
            checks.append(_ok_result("endpoint", item.key, item.label, item.detail or "Endpoint kayıtlı."))
        else:
            checks.append(
                _warning_result(
                    "endpoint",
                    item.key,
                    item.label,
                    "Endpoint bulunamadı.",
                    advice="Route adı ve base.html / ilgili şablon bağlantıları birlikte kontrol edilmeli.",
                )
            )

    for item in CRITICAL_TEMPLATES:
        if _template_exists(item.key):
            checks.append(_ok_result("template", item.key, item.label, item.detail or "Şablon dosyası mevcut."))
        else:
            checks.append(
                _warning_result(
                    "template",
                    item.key,
                    item.label,
                    "Şablon dosyası bulunamadı.",
                    advice="Şablon yolu veya dosya adı kırılmış olabilir.",
                )
            )

    ok_count = sum(1 for row in checks if row.get("status") == "ok")
    warning_count = sum(1 for row in checks if row.get("status") != "ok")
    readiness_score = int(round((ok_count / len(checks)) * 100)) if checks else 0

    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in checks:
        grouped.setdefault(str(row.get("category") or "genel"), []).append(row)

    top_actions: list[dict[str, str]] = []
    if not schema_status.get("ready"):
        top_actions.append(
            {
                "title": "AI şema hazırlığını tamamlayın",
                "body": str(schema_status.get("message") or "AI tabloları eksik görünüyor."),
                "tone": "warning",
            }
        )
    missing_endpoints = [row for row in checks if row.get("category") == "endpoint" and row.get("status") != "ok"]
    if missing_endpoints:
        top_actions.append(
            {
                "title": "Eksik endpoint bağlantılarını düzeltin",
                "body": f"{len(missing_endpoints)} kritik endpoint görünmüyor. Menü ve şablon bağlantıları tekrar doğrulanmalı.",
                "tone": "warning",
            }
        )
    missing_templates = [row for row in checks if row.get("category") == "template" and row.get("status") != "ok"]
    if missing_templates:
        top_actions.append(
            {
                "title": "Şablon kırıklarını temizleyin",
                "body": f"{len(missing_templates)} kritik şablon dosyası bulunamadı. Dağıtımdan önce dosya yolları netleştirilmeli.",
                "tone": "warning",
            }
        )
    import_issues = [row for row in checks if row.get("category") == "import" and row.get("status") != "ok"]
    if import_issues:
        top_actions.append(
            {
                "title": "Import zincirini sertleştirin",
                "body": f"{len(import_issues)} içe/dışa aktarma sorunu var. Uygulama açılışı veya yönetim AI ekranları bunlardan etkilenebilir.",
                "tone": "warning",
            }
        )
    if not provider_snapshot.get("ready_for_live_provider"):
        top_actions.append(
            {
                "title": "Sağlayıcı canlı hazır değil",
                "body": "Gerçek model bağlantısı kapalıysa kullanıcı görünür AI senaryolarını pilot sınırında tutun veya gerçek sağlayıcıya geçin.",
                "tone": "warning",
            }
        )
    if not top_actions:
        top_actions.append(
            {
                "title": "Toplu AI regresyon görünümü dengeli",
                "body": "Kritik schema, endpoint, import ve şablon kontrolleri temiz görünüyor. Son adım gerçek veri smoke testi.",
                "tone": "success",
            }
        )

    smoke_paths = [
        {"label": "AI kontrol merkezi", "endpoint": "main.admin_ai_center", "path": "/admin/ai-center"},
        {"label": "AI operasyon raporu", "endpoint": "main.admin_ai_operations_report", "path": "/admin/ai-operations-report"},
        {"label": "Performans AI öneri merkezi", "endpoint": "main.performance_task_management_recommendations", "path": "/performance/task-management/recommendations"},
        {"label": "İzin yönetimi", "endpoint": "main.hr_leave_management", "path": "/hr-management/leave"},
        {"label": "Devamsızlık & vekâlet", "endpoint": "main.hr_attendance_management", "path": "/hr-management/attendance"},
        {"label": "Ana dashboard", "endpoint": "main.dashboard", "path": "/dashboard"},
    ]

    return {
        "generated_at": utc_now(),
        "schema_status": schema_status,
        "summary": {
            "check_total": len(checks),
            "ok_count": ok_count,
            "warning_count": warning_count,
            "readiness_score": readiness_score,
        },
        "checks": checks,
        "grouped_checks": grouped,
        "top_actions": top_actions[:4],
        "smoke_paths": smoke_paths,
    }