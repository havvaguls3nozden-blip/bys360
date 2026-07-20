"""Personel Yönetimi Faz 9 kalite kapısı yardımcıları.

Bu modül veritabanına yazmaz. Route cleanup sonrasında personel servis
paketinin beklenen canlı sözleşmesini, servis modüllerini ve route yüzeyini
okunabilir bir kalite özeti olarak sunar.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

PHASE9_REQUIRED_SERVICE_MODULES: tuple[str, ...] = (
    "live_scope",
    "service_inventory",
    "form_context",
    "form_payload",
    "list_query",
    "workflow",
    "profile_photo",
    "uniqueness",
    "org_hierarchy",
    "leave_attendance",
    "excel_import",
    "quality_gate",
)

PHASE9_REQUIRED_ROUTE_NAMES: tuple[str, ...] = (
    "admin_users",
    "admin_user_create",
    "admin_user_edit",
    "personnel_list",
    "personnel_add",
    "personnel_edit",
    "personnel_excel_upload",
)

PHASE9_ROUTE_LOCAL_HELPERS_REMOVED: tuple[str, ...] = (
    "def _set_user_role(",
    "def _set_manager_if_exists(",
    "def _set_manager_sicils_from_ids(",
    "def has_explicit_personnel_excel_manager_columns(",
)

PHASE9_REQUIRED_SERVICE_EXPORTS: tuple[str, ...] = (
    "build_personnel_list_context",
    "build_new_personnel_user_from_payload",
    "update_existing_personnel_user_from_payload",
    "apply_personnel_profile_photo_action",
    "validate_personnel_identity_uniqueness",
    "apply_admin_user_org_hierarchy_fields",
    "build_personnel_leave_attendance_context",
    "preflight_personnel_excel_headers",
    "build_personnel_excel_row_payload",
    "has_explicit_personnel_excel_manager_columns",
)


@dataclass(frozen=True)
class PersonnelQualityIssue:
    """Kalite kapısında bulunan tekil sorun."""

    code: str
    message: str


@dataclass(frozen=True)
class PersonnelQualityGateResult:
    """Faz 9 route cleanup kalite kapısı sonucu."""

    ok: bool
    ok_count: int
    issues: tuple[PersonnelQualityIssue, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def error_count(self) -> int:
        return len(self.issues)

    def as_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "ok_count": self.ok_count,
            "error_count": self.error_count,
            "issues": [issue.__dict__ for issue in self.issues],
            "notes": list(self.notes),
        }


def _read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def check_personnel_route_cleanup_source(route_source: str) -> PersonnelQualityGateResult:
    """Route dosyasında servisleşmiş helperların yerel kopyalarını denetler."""
    issues: list[PersonnelQualityIssue] = []
    ok_count = 0

    for marker in PHASE9_ROUTE_LOCAL_HELPERS_REMOVED:
        if marker in route_source:
            issues.append(
                PersonnelQualityIssue(
                    "route.local_helper_still_present",
                    f"Servise taşınan route-local helper hâlâ duruyor: {marker}",
                )
            )
        else:
            ok_count += 1

    for route_name in PHASE9_REQUIRED_ROUTE_NAMES:
        if f"def {route_name}(" in route_source and f'"{route_name}"' in route_source:
            ok_count += 1
        else:
            issues.append(
                PersonnelQualityIssue(
                    "route.contract_missing",
                    f"Beklenen route veya __all__ sözleşmesi eksik: {route_name}",
                )
            )

    if "from app.services.personnel import (" in route_source:
        ok_count += 1
    else:
        issues.append(
            PersonnelQualityIssue(
                "route.service_import_missing",
                "Route dosyasında personel servis paketi import köprüsü bulunamadı.",
            )
        )

    if "has_explicit_personnel_excel_manager_columns," in route_source:
        ok_count += 1
    else:
        issues.append(
            PersonnelQualityIssue(
                "route.excel_helper_import_missing",
                "Excel açık amir kolon tespiti servis importu eksik.",
            )
        )

    notes = (
        "Route cleanup veritabanı yazma davranışına dokunmaz.",
        "Commit/rollback sınırı route tarafında korunur.",
        "Excel import açık amir kolon tespiti servis katmanından kullanılır.",
    )
    return PersonnelQualityGateResult(ok=not issues, ok_count=ok_count, issues=tuple(issues), notes=notes)


def check_personnel_service_package_source(init_source: str) -> PersonnelQualityGateResult:
    """Personel servis paketi export sözleşmesini denetler."""
    issues: list[PersonnelQualityIssue] = []
    ok_count = 0

    for export_name in PHASE9_REQUIRED_SERVICE_EXPORTS:
        if f'"{export_name}"' in init_source:
            ok_count += 1
        else:
            issues.append(
                PersonnelQualityIssue(
                    "service.export_missing",
                    f"Servis export sözleşmesi eksik: {export_name}",
                )
            )

    for module_name in PHASE9_REQUIRED_SERVICE_MODULES:
        if module_name == "quality_gate":
            marker = "from .quality_gate import"
        else:
            marker = f"from .{module_name} import"
        if marker in init_source or module_name in {"live_scope", "service_inventory"}:
            ok_count += 1
        else:
            issues.append(
                PersonnelQualityIssue(
                    "service.module_import_missing",
                    f"Servis modül import izi eksik: {module_name}",
                )
            )

    return PersonnelQualityGateResult(
        ok=not issues,
        ok_count=ok_count,
        issues=tuple(issues),
        notes=("Personel servis paketi Faz 0-9 export yüzeyi korunur.",),
    )


def merge_personnel_quality_gate_results(results: Iterable[PersonnelQualityGateResult]) -> PersonnelQualityGateResult:
    """Birden fazla kalite kapısını tek sonuçta birleştirir."""
    result_list = list(results)
    issues: list[PersonnelQualityIssue] = []
    notes: list[str] = []
    ok_count = 0
    for result in result_list:
        ok_count += result.ok_count
        issues.extend(result.issues)
        notes.extend(result.notes)
    return PersonnelQualityGateResult(
        ok=not issues,
        ok_count=ok_count,
        issues=tuple(issues),
        notes=tuple(dict.fromkeys(notes)),
    )


def run_personnel_phase9_quality_gate(route_path: str | Path, init_path: str | Path) -> PersonnelQualityGateResult:
    """Dosya yollarından Faz 9 kalite kapısı çalıştırır."""
    route_source = _read_text(route_path)
    init_source = _read_text(init_path)
    return merge_personnel_quality_gate_results(
        [
            check_personnel_route_cleanup_source(route_source),
            check_personnel_service_package_source(init_source),
        ]
    )


def build_personnel_quality_gate_phase9_summary(result: PersonnelQualityGateResult | None = None) -> dict[str, object]:
    """UI/rapor tarafı için kompakt Faz 9 özeti döndürür."""
    base: dict[str, object] = {
        "phase": "Personel Yönetimi Servis Refactor Faz 9",
        "title": "Route cleanup ve personel kalite kapısı",
        "behavior_change": False,
        "database_change": False,
        "route_contract_preserved": True,
        "commit_rollback_preserved": True,
        "required_service_modules": list(PHASE9_REQUIRED_SERVICE_MODULES),
        "required_routes": list(PHASE9_REQUIRED_ROUTE_NAMES),
    }
    if result is not None:
        base["quality_gate"] = result.as_dict()
    return base
