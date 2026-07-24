from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class PersonnelSurfaceItem:
    key: str
    label: str
    path: str
    status: str
    note: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


# Canlı çekirdeğin personel tarafında korunacak ana veri alanları.
# Bu liste Faz 0'da sadece envanterdir; tablo oluşturmaz, migration çalıştırmaz.
PERSONNEL_CORE_TABLES: tuple[str, ...] = (
    "users",
    "organization_units",
    "organization_unit_versions",
    "employee_org_assignment_history",
    "attendance_events",
    "attendance_exceptions",
    "leave_policies",
    "leave_balances",
    "leave_records",
    "leave_requests",
    "personnel_leaves",
    "delegation_assignments",
)

# Projede mevcut olan, fakat ilk canlı çekirdek refactor'un ana hedefi olmayan
# personel genişleme tabloları. Faz 0 bunları silmez, devre dışı bırakmaz.
PERSONNEL_OPTIONAL_EXTENSION_TABLES: tuple[str, ...] = (
    "personnel_document_categories",
    "personnel_documents",
    "personnel_document_upload_batches",
    "personnel_process_notes",
    "personnel_status_history",
    "personnel_self_service_request_templates",
    "personnel_self_service_requests",
    "personnel_self_service_request_attachments",
    "personnel_self_service_request_logs",
    "personnel_self_service_request_tasks",
    "personnel_position_histories",
    "personnel_asset_assignments",
    "personnel_checklist_template_items",
    "personnel_checklist_reviews",
    "personnel_document_reminder_logs",
    "personnel_asset_transfer_logs",
    "personnel_lifecycle_cases",
    "personnel_lifecycle_tasks",
    "personnel_exit_interviews",
    "personnel_handover_records",
    "personnel_handover_items",
    "personnel_approval_stations",
    "personnel_digital_handover_documents",
    "personnel_exit_risk_assessments",
)

PERSONNEL_SERVICE_MODULES: tuple[PersonnelSurfaceItem, ...] = (
    PersonnelSurfaceItem(
        key="personnel_sync_service",
        label="Personel formu ve Excel senkronizasyon servisi",
        path="app/services/personnel_sync_service.py",
        status="existing_live_service",
        note="Personel ekleme/düzenleme, Excel alan eşleme ve 1/2/3. amir sicil çözümleme davranışı burada korunur.",
    ),
    PersonnelSurfaceItem(
        key="hr_operations_service",
        label="Personel operasyon ekranları servis gövdesi",
        path="app/services/hr_operations_service.py",
        status="existing_live_service",
        note="Profil, doküman, not, statü, zaman çizelgesi ve operasyon bağlamı üretir.",
    ),
    PersonnelSurfaceItem(
        key="leave_delegation_service",
        label="İzin, devamsızlık ve vekâlet servis gövdesi",
        path="app/services/leave_delegation_service.py",
        status="existing_live_service",
        note="İzin modu, vekâlet merkezi ve performans entegrasyonu için sağlık özetleri üretir.",
    ),
    PersonnelSurfaceItem(
        key="admin_user_service",
        label="Admin kullanıcı/personel form servis köprüsü",
        path="app/services/admin_user_service.py",
        status="existing_live_service",
        note="Zorunlu personel alanları, kurumsal e-posta ve amir tekrar kontrolleri korunur.",
    ),
    PersonnelSurfaceItem(
        key="personnel_org_hierarchy",
        label="Personel organizasyon ve hiyerarşi servis köprüsü",
        path="app/services/personnel/org_hierarchy.py",
        status="refactor_phase6_service",
        note="Organizasyon birimi bağlama ve sicil/id bazlı 1/2/3. amir atama köprüsünü sağlar.",
    ),
    PersonnelSurfaceItem(
        key="personnel_leave_attendance",
        label="Personel izin, devamsızlık ve vekâlet okuma köprüsü",
        path="app/services/personnel/leave_attendance.py",
        status="refactor_phase7_service",
        note="İzin, devamsızlık, izinli amir ve aktif vekâlet sinyallerini salt-okunur context olarak üretir.",
    ),
)

PERSONNEL_ROUTE_SHIMS: tuple[PersonnelSurfaceItem, ...] = (
    PersonnelSurfaceItem(
        key="routes_admin_personnel",
        label="Eski admin/personel route shim",
        path="app/routes_admin_personnel.py",
        status="archived_reference_only",
        note="Canlı route kaynağı değildir; geriye dönük referans için tutulur.",
    ),
    PersonnelSurfaceItem(
        key="routes_hr",
        label="Eski HR route shim",
        path="app/routes_hr.py",
        status="archived_reference_only",
        note="Canlı route kaynağı değildir; geriye dönük referans için tutulur.",
    ),
)

PERSONNEL_TEMPLATE_SURFACE: tuple[PersonnelSurfaceItem, ...] = (
    PersonnelSurfaceItem("personnel_list", "Personel listesi", "app/templates/personnel_list.html", "live_template"),
    PersonnelSurfaceItem("personnel_add", "Personel ekleme", "app/templates/personnel_add.html", "live_template"),
    PersonnelSurfaceItem("personnel_edit", "Personel düzenleme", "app/templates/personnel_edit.html", "live_template"),
    PersonnelSurfaceItem("personnel_profile", "Personel profili", "app/templates/personnel_profile.html", "live_template"),
    PersonnelSurfaceItem("personnel_excel_upload", "Personel Excel aktarımı", "app/templates/personnel_excel_upload.html", "live_template"),
    PersonnelSurfaceItem("hr_management", "Personel yönetimi ana ekranı", "app/templates/hr_management.html", "live_template"),
    PersonnelSurfaceItem("hr_attendance", "Devamsızlık ekranı", "app/templates/hr_attendance.html", "live_template"),
    PersonnelSurfaceItem("hr_leave", "İzin ekranı", "app/templates/hr_leave.html", "live_template"),
    PersonnelSurfaceItem("hr_reports", "Personel raporları", "app/templates/hr_reports.html", "live_template"),
)

PHASE0_NO_MUTATION_TOKENS: tuple[str, ...] = (
    "db.session." + "commit(",
    "db.session." + "rollback(",
    "db.session." + "delete(",
    "db." + "drop_all(",
    "db." + "create_all(",
    "ALTER" + " TABLE",
    "DROP" + " TABLE",
    "TRUN" + "CATE",
)


def _exists(project_root: Path, rel_path: str) -> bool:
    return (project_root / rel_path).exists()


def build_personnel_live_scope() -> dict[str, Any]:
    """Return a serialisable live-scope inventory for personnel refactor phases.

    This function intentionally has no Flask/SQLAlchemy dependency. It is safe to
    call from audit scripts, CI checks and documentation generators.
    """
    return {
        "phase": "personnel_service_faz0",
        "purpose": "inventory_and_service_refactor_foundation",
        "core_tables": list(PERSONNEL_CORE_TABLES),
        "optional_extension_tables": list(PERSONNEL_OPTIONAL_EXTENSION_TABLES),
        "service_modules": [item.to_dict() for item in PERSONNEL_SERVICE_MODULES],
        "route_shims": [item.to_dict() for item in PERSONNEL_ROUTE_SHIMS],
        "template_surface": [item.to_dict() for item in PERSONNEL_TEMPLATE_SURFACE],
        "runtime_mutation": False,
    }


def check_personnel_phase0_surface(project_root: str | Path = ".") -> list[dict[str, Any]]:
    """Check only file-surface readiness; do not import Flask app or touch DB."""
    root = Path(project_root)
    checks: list[dict[str, Any]] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    for item in PERSONNEL_SERVICE_MODULES:
        add(f"service.{item.key}", _exists(root, item.path), item.path)
    for item in PERSONNEL_ROUTE_SHIMS:
        add(f"route_shim.{item.key}", _exists(root, item.path), item.path)
    for item in PERSONNEL_TEMPLATE_SURFACE:
        add(f"template.{item.key}", _exists(root, item.path), item.path)

    add("core_tables.users", "users" in PERSONNEL_CORE_TABLES, "users canlı personel çekirdeğinde korunmalı")
    add("core_tables.org_units", "organization_units" in PERSONNEL_CORE_TABLES, "organizasyon birimleri korunmalı")
    add("core_tables.delegation", "delegation_assignments" in PERSONNEL_CORE_TABLES, "izin/vekâlet entegrasyonu korunmalı")
    add("phase0.no_runtime_mutation", True, "Faz 0 sadece envanter/servis iskeletidir")
    return checks


def render_personnel_live_scope_markdown(project_root: str | Path = ".") -> str:
    checks = check_personnel_phase0_surface(project_root)
    ok_count = sum(1 for item in checks if item["ok"])
    fail_count = len(checks) - ok_count
    lines = [
        "# BYS360 Personel Yönetimi Servis Refactor Faz 0",
        "",
        "Bu rapor personel yönetimi refactor zincirinin başlangıç envanteridir.",
        "Faz 0 uygulama davranışını, kayıt akışını, veritabanını veya route yönlendirmelerini değiştirmez.",
        "",
        f"- Kontrol: OK={ok_count} HATA={fail_count}",
        f"- Canlı çekirdek tablo sayısı: {len(PERSONNEL_CORE_TABLES)}",
        f"- Mevcut servis modülü sayısı: {len(PERSONNEL_SERVICE_MODULES)}",
        f"- Canlı template yüzeyi sayısı: {len(PERSONNEL_TEMPLATE_SURFACE)}",
        "",
        "## Canlı çekirdek tablolar",
    ]
    lines.extend(f"- `{name}`" for name in PERSONNEL_CORE_TABLES)
    lines.extend(["", "## Mevcut servis girişleri"])
    for item in PERSONNEL_SERVICE_MODULES:
        lines.append(f"- `{item.path}` — {item.label}")
    lines.extend(["", "## Kontroller"])
    for check in checks:
        mark = "OK" if check["ok"] else "HATA"
        lines.append(f"- {mark} `{check['name']}` — {check['detail']}")
    lines.append("")
    return "\n".join(lines)
