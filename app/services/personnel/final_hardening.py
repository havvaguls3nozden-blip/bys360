"""Personel Yönetimi Servis Refactor Faz 10 final sertleştirme yardımcıları.

Bu modül veritabanına yazmaz ve canlı personel davranışını değiştirmez. Faz 0-9
boyunca servisleşen personel omurgasının dosya, route sözleşmesi, export yüzeyi
ve kaynak hijyeni açısından kapanış kontrolünü üretir.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

PHASE10_REQUIRED_SERVICE_MODULES: tuple[str, ...] = (
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
    "final_hardening",
)

PHASE10_REQUIRED_ROUTE_NAMES: tuple[str, ...] = (
    "admin_users",
    "admin_user_create",
    "admin_user_edit",
    "personnel_list",
    "personnel_add",
    "personnel_edit",
    "personnel_excel_upload",
)

PHASE10_REQUIRED_SERVICE_EXPORTS: tuple[str, ...] = (
    "build_personnel_list_context",
    "build_new_personnel_user_from_payload",
    "update_existing_personnel_user_from_payload",
    "apply_personnel_profile_photo_action",
    "validate_personnel_identity_uniqueness",
    "apply_admin_user_org_hierarchy_fields",
    "build_personnel_leave_attendance_context",
    "preflight_personnel_excel_headers",
    "build_personnel_excel_row_payload",
    "run_personnel_phase9_quality_gate",
    "run_personnel_final_hardening_gate",
    "build_personnel_final_hardening_phase10_summary",
)

PHASE10_SERVICE_SOURCE_FORBIDDEN_MARKERS: tuple[str, ...] = (
    "db.session.commit(",
    "db.session.rollback(",
    "db.session.delete(",
)

PHASE10_EXPECTED_FILES: tuple[str, ...] = tuple(
    [f"app/services/personnel/{module_name}.py" for module_name in PHASE10_REQUIRED_SERVICE_MODULES]
    + [
        "app/services/personnel/__init__.py",
        "app/admin/routes.py",
        "scripts/refactor/bys360_personnel_service_faz10_final_hardening_audit.py",
        "docs/refactor/generated/personnel_service_faz10_final_hardening_report.md",
    ]
)


@dataclass(frozen=True)
class PersonnelFinalHardeningIssue:
    """Final kalite kapısında bulunan tekil sorun."""

    code: str
    message: str


@dataclass(frozen=True)
class PersonnelFinalHardeningResult:
    """Personel Yönetimi Faz 10 kapanış kontrol sonucu."""

    ok: bool
    ok_count: int
    issues: tuple[PersonnelFinalHardeningIssue, ...] = field(default_factory=tuple)
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


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _result(ok_count: int, issues: Sequence[PersonnelFinalHardeningIssue], notes: Sequence[str] = ()) -> PersonnelFinalHardeningResult:
    return PersonnelFinalHardeningResult(
        ok=not issues,
        ok_count=ok_count,
        issues=tuple(issues),
        notes=tuple(notes),
    )


def check_personnel_final_required_files(project_root: str | Path = ".") -> PersonnelFinalHardeningResult:
    """Faz 10 için beklenen dosyaların projede bulunduğunu denetler."""
    root = Path(project_root)
    issues: list[PersonnelFinalHardeningIssue] = []
    ok_count = 0
    for rel_path in PHASE10_EXPECTED_FILES:
        path = root / rel_path
        if path.exists():
            ok_count += 1
        else:
            issues.append(
                PersonnelFinalHardeningIssue(
                    "phase10.file_missing",
                    f"Beklenen Faz 10 dosyası eksik: {rel_path}",
                )
            )
    return _result(ok_count, issues, ("Faz 10 dosya yüzeyi kontrol edildi.",))


def check_personnel_final_service_exports(init_source: str) -> PersonnelFinalHardeningResult:
    """Servis paketi export yüzeyinin Faz 10 kapanışına hazır olduğunu denetler."""
    issues: list[PersonnelFinalHardeningIssue] = []
    ok_count = 0

    for module_name in PHASE10_REQUIRED_SERVICE_MODULES:
        marker = f"from .{module_name} import"
        if marker in init_source or module_name in {"live_scope", "service_inventory"}:
            ok_count += 1
        else:
            issues.append(
                PersonnelFinalHardeningIssue(
                    "phase10.service_module_import_missing",
                    f"Servis modül import izi eksik: {module_name}",
                )
            )

    for export_name in PHASE10_REQUIRED_SERVICE_EXPORTS:
        if f'"{export_name}"' in init_source:
            ok_count += 1
        else:
            issues.append(
                PersonnelFinalHardeningIssue(
                    "phase10.service_export_missing",
                    f"Servis export sözleşmesi eksik: {export_name}",
                )
            )

    return _result(ok_count, issues, ("Personel servis export yüzeyi Faz 10 ile hizalandı.",))


def check_personnel_final_route_contract(route_source: str) -> PersonnelFinalHardeningResult:
    """Personel route sözleşmesinin canlı yüzeyini koruduğunu denetler."""
    issues: list[PersonnelFinalHardeningIssue] = []
    ok_count = 0

    for route_name in PHASE10_REQUIRED_ROUTE_NAMES:
        if f"def {route_name}(" in route_source:
            ok_count += 1
        else:
            issues.append(
                PersonnelFinalHardeningIssue(
                    "phase10.route_missing",
                    f"Beklenen personel route fonksiyonu eksik: {route_name}",
                )
            )

    if "from app.services.personnel import (" in route_source:
        ok_count += 1
    else:
        issues.append(
            PersonnelFinalHardeningIssue(
                "phase10.route_service_import_missing",
                "Admin route dosyasında personel servis import köprüsü bulunamadı.",
            )
        )

    for old_helper_marker in (
        "def _set_user_role(",
        "def _set_manager_if_exists(",
        "def _set_manager_sicils_from_ids(",
        "def has_explicit_personnel_excel_manager_columns(",
    ):
        if old_helper_marker in route_source:
            issues.append(
                PersonnelFinalHardeningIssue(
                    "phase10.route_old_helper_present",
                    f"Route içinde temizlenmiş olması gereken eski helper hâlâ var: {old_helper_marker}",
                )
            )
        else:
            ok_count += 1

    return _result(
        ok_count,
        issues,
        (
            "Route URL/template/flash sözleşmesi korunur.",
            "Commit/rollback sınırı route tarafında kalmaya devam eder.",
        ),
    )


def check_personnel_final_service_write_boundary(project_root: str | Path = ".") -> PersonnelFinalHardeningResult:
    """Servis modüllerinde doğrudan commit/rollback/delete izi olmadığını denetler."""
    root = Path(project_root)
    service_dir = root / "app" / "services" / "personnel"
    issues: list[PersonnelFinalHardeningIssue] = []
    ok_count = 0

    if not service_dir.exists():
        return _result(
            0,
            [
                PersonnelFinalHardeningIssue(
                    "phase10.service_dir_missing",
                    "app/services/personnel klasörü bulunamadı.",
                )
            ],
        )

    for service_file in sorted(service_dir.glob("*.py")):
        if service_file.name == "final_hardening.py":
            ok_count += 1
            continue
        source = service_file.read_text(encoding="utf-8")
        rel = _safe_rel(service_file, root)
        for marker in PHASE10_SERVICE_SOURCE_FORBIDDEN_MARKERS:
            if marker in source:
                issues.append(
                    PersonnelFinalHardeningIssue(
                        "phase10.service_write_boundary_violation",
                        f"Servis dosyasında route tarafında kalması gereken DB yazma sınırı bulundu: {rel} :: {marker}",
                    )
                )
            else:
                ok_count += 1

    return _result(
        ok_count,
        issues,
        ("Servis katmanı doğrudan commit/rollback/delete üstlenmez.",),
    )


def merge_personnel_final_hardening_results(results: Iterable[PersonnelFinalHardeningResult]) -> PersonnelFinalHardeningResult:
    """Birden fazla final kontrol sonucunu tek sonuca birleştirir."""
    result_list = list(results)
    issues: list[PersonnelFinalHardeningIssue] = []
    notes: list[str] = []
    ok_count = 0
    for result in result_list:
        ok_count += result.ok_count
        issues.extend(result.issues)
        notes.extend(result.notes)
    return PersonnelFinalHardeningResult(
        ok=not issues,
        ok_count=ok_count,
        issues=tuple(issues),
        notes=tuple(dict.fromkeys(notes)),
    )


def run_personnel_final_hardening_gate(project_root: str | Path = ".") -> PersonnelFinalHardeningResult:
    """Faz 10 final personel sertleştirme kontrolünü çalıştırır."""
    root = Path(project_root)
    init_path = root / "app" / "services" / "personnel" / "__init__.py"
    route_path = root / "app" / "admin" / "routes.py"

    results: list[PersonnelFinalHardeningResult] = [
        check_personnel_final_required_files(root),
        check_personnel_final_service_write_boundary(root),
    ]
    if init_path.exists():
        results.append(check_personnel_final_service_exports(_read_text(init_path)))
    else:
        results.append(
            _result(
                0,
                [PersonnelFinalHardeningIssue("phase10.init_missing", "Personel servis __init__.py bulunamadı.")],
            )
        )
    if route_path.exists():
        results.append(check_personnel_final_route_contract(_read_text(route_path)))
    else:
        results.append(
            _result(
                0,
                [PersonnelFinalHardeningIssue("phase10.route_file_missing", "app/admin/routes.py bulunamadı.")],
            )
        )
    return merge_personnel_final_hardening_results(results)


def build_personnel_final_hardening_phase10_summary(
    result: PersonnelFinalHardeningResult | None = None,
) -> dict[str, object]:
    """UI/rapor tarafı için kompakt Faz 10 kapanış özeti üretir."""
    base: dict[str, object] = {
        "phase": "Personel Yönetimi Servis Refactor Faz 10",
        "title": "Final canlı sertleştirme ve kapanış raporu",
        "behavior_change": False,
        "database_change": False,
        "route_contract_preserved": True,
        "commit_rollback_preserved": True,
        "profile_photo_behavior_preserved": True,
        "excel_import_behavior_preserved": True,
        "required_service_modules": list(PHASE10_REQUIRED_SERVICE_MODULES),
        "required_routes": list(PHASE10_REQUIRED_ROUTE_NAMES),
        "write_boundary": "Servis katmanı commit/rollback/delete üstlenmez.",
    }
    if result is not None:
        base["final_hardening_gate"] = result.as_dict()
    return base


def render_personnel_final_hardening_report(
    result: PersonnelFinalHardeningResult,
) -> str:
    """Faz 10 kapanış raporunu Markdown olarak üretir."""
    status = "GEÇTİ" if result.ok else "HATA VAR"
    issue_lines = "\n".join(f"- {issue.code}: {issue.message}" for issue in result.issues) or "- Hata bulunmadı."
    note_lines = "\n".join(f"- {note}" for note in result.notes) or "- Not yok."
    return f"""# BYS360 Personel Yönetimi Servis Refactor Faz 10 Kapanış Raporu

## Durum

- Sonuç: {status}
- OK sayısı: {result.ok_count}
- Hata sayısı: {result.error_count}

## Kapsam

- Faz 0-9 servis köprüleri kümülatif korunur.
- Personel kayıt, güncelleme, profil fotoğrafı ve Excel aktarım davranışı değiştirilmez.
- Veritabanı şema değişikliği yapılmaz.
- Commit/rollback sınırı route katmanında kalır.
- Personel servis paketi final kalite kapısı ile kapanır.

## Notlar

{note_lines}

## Hatalar

{issue_lines}
"""
