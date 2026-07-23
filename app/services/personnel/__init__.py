"""BYS360 Personel Yönetimi servis paketi.

Faz 0 amacı:
- Canlı personel omurgasını tek yerde tanımlamak.
- Mevcut route/kayıt davranışına dokunmadan servis refactor için güvenli
  envanter yüzeyi oluşturmak.
- Personel, organizasyon, izin, devamsızlık ve vekâlet hattını sonraki
  fazlarda parça parça servisleştirmeye hazırlamak.

Faz 1 amacı:
- Personel ekleme/düzenleme form context hazırlığını servisleştirmek.
- Form payload okuma/temizleme davranışını tek yerde toplamak.
- Commit/rollback, fotoğraf yükleme ve model yazma sırasını değiştirmemek.

Faz 2 amacı:
- Personel listeleme, arama ve filtreleme bağlamını servisleştirmek.
- Liste ekranındaki stats/user_rows/role_values/birimler sözleşmesini korumak.
- Veritabanı yazma davranışına dokunmamak.

Faz 3 amacı:
- Personel ekleme/güncelleme model iş akışını servisleştirmek.
- Commit/rollback, fotoğraf dosyası ve flash/redirect davranışını route tarafında korumak.
- Organizasyon birimi, amir sicil ve şifre güncelleme adımlarını tek yerde toplamak.

Faz 4 amacı:
- Profil fotoğrafı yükleme/silme kararını servisleştirmek.
- Eski fotoğraf silme işleminde static kökü dışına taşan şüpheli yolları silmemek.
- Commit/rollback ve flash/redirect davranışını route tarafında korumak.

Faz 5 amacı:
- Sicil no ve e-posta tekillik kontrollerini servisleştirmek.
- Amir seçim çakışması ve şifre güncelleme doğrulamasını tek yerde toplamak.
- Veritabanı yazma davranışına ve route sözleşmesine dokunmamak.

Faz 6 amacı:
- Organizasyon birimi oluşturma/bağlama kararını servisleştirmek.
- Sicil ve id bazlı 1/2/3. amir atama köprüsünü tek yerde toplamak.
- Commit/rollback ve route sözleşmesini korumak.

Faz 7 amacı:
- İzin, devamsızlık ve vekâlet kayıtlarını okuma/context servisi olarak toplamak.
- Kayıt/onay davranışına dokunmadan performans etkili sinyalleri görünür kılmak.

Faz 8 amacı:
- Excel personel aktarımı başlık preflight ve satır payload okuma davranışını servisleştirmek.
- Import commit/rollback sırasına dokunmadan doğrulama yüzeyini merkezi hale getirmek.

Faz 9 amacı:
- Route içindeki servisleşmiş eski helper kopyalarını temizlemek.
- Personel route sözleşmesi ve servis export yüzeyi için kalite kapısı eklemek.
"""
from __future__ import annotations

from .categories import (
    PERSONNEL_CATEGORY_DEFAULTS,
    PERSONNEL_CATEGORY_OPTIONS,
    assign_user_performance_category,
    ensure_personnel_category,
    get_personnel_category_options,
    get_user_personnel_category_label,
    normalize_personnel_category_label,
    seed_default_personnel_categories,
    slugify_personnel_category,
    user_matches_personnel_category,
)
from .excel_import import (
    PERSONNEL_EXCEL_MANAGER_1_ALIASES,
    PERSONNEL_EXCEL_MANAGER_2_ALIASES,
    PERSONNEL_EXCEL_MANAGER_3_ALIASES,
    PERSONNEL_EXCEL_MANAGER_ALIASES,
    PERSONNEL_EXCEL_REQUIRED_HEADERS,
    PERSONNEL_EXCEL_ROLE_ALIASES,
    PersonnelExcelPreflightResult,
    PersonnelExcelRowPayload,
    build_personnel_excel_column_index,
    build_personnel_excel_import_phase8_summary,
    build_personnel_excel_row_payload,
    excel_scalar,
    has_explicit_personnel_excel_manager_columns,
    normalize_personnel_excel_headers,
    preflight_personnel_excel_headers,
    row_has_required_personnel_excel_fields,
)
from .final_hardening import (
    PHASE10_EXPECTED_FILES,
    PHASE10_REQUIRED_ROUTE_NAMES,
    PHASE10_REQUIRED_SERVICE_EXPORTS,
    PHASE10_REQUIRED_SERVICE_MODULES,
    PHASE10_SERVICE_SOURCE_FORBIDDEN_MARKERS,
    PersonnelFinalHardeningIssue,
    PersonnelFinalHardeningResult,
    build_personnel_final_hardening_phase10_summary,
    check_personnel_final_required_files,
    check_personnel_final_route_contract,
    check_personnel_final_service_exports,
    check_personnel_final_service_write_boundary,
    merge_personnel_final_hardening_results,
    render_personnel_final_hardening_report,
    run_personnel_final_hardening_gate,
)
from .form_context import (
    build_personnel_create_form_context,
    build_personnel_edit_form_context,
    build_personnel_form_phase1_summary,
)
from .form_payload import (
    PERSONNEL_MANAGER_FIELDS,
    PERSONNEL_REQUIRED_FIELDS,
    PersonnelFormPayload,
    PersonnelFormValidationResult,
    missing_required_personnel_fields,
    read_personnel_form_payload,
    validate_edit_password_fields,
    validate_manager_selection,
    validate_required_personnel_payload,
)
from .leave_attendance import (
    ACTIVE_LEAVE_ATTENDANCE_STATUSES,
    LEAVE_ATTENDANCE_REQUIRED_TABLES,
    PENDING_LEAVE_ATTENDANCE_STATUSES,
    PersonnelLeaveAttendanceContext,
    PersonnelLeaveAttendanceFilters,
    PersonnelLeaveAttendanceReadiness,
    build_personnel_leave_attendance_cards,
    build_personnel_leave_attendance_context,
    build_personnel_leave_attendance_notes,
    build_personnel_leave_attendance_phase7_summary,
    check_leave_attendance_readiness,
    list_personnel_attendance_rows,
    list_personnel_delegation_rows,
    list_personnel_leave_balances,
    list_personnel_leave_rows,
    read_leave_attendance_filters,
)
from .list_query import (
    PersonnelListFilters,
    PersonnelListRow,
    PersonnelListStats,
    apply_personnel_list_filters,
    build_personnel_list_base_query,
    build_personnel_list_context,
    build_personnel_list_phase2_summary,
    build_personnel_list_row,
    build_personnel_list_rows,
    build_personnel_list_stats,
    build_personnel_role_values,
    build_personnel_unit_options,
    read_personnel_list_filters,
)
from .live_scope import (
    PERSONNEL_CORE_TABLES,
    PERSONNEL_OPTIONAL_EXTENSION_TABLES,
    PERSONNEL_ROUTE_SHIMS,
    PERSONNEL_SERVICE_MODULES,
    PERSONNEL_TEMPLATE_SURFACE,
    build_personnel_live_scope,
    check_personnel_phase0_surface,
)
from .org_hierarchy import (
    PersonnelOrgHierarchyResult,
    apply_admin_user_org_hierarchy_fields,
    apply_manager_id_hierarchy,
    apply_manager_sicil_hierarchy,
    attach_organization_unit_to_user,
    attach_personnel_payload_org_hierarchy,
    build_personnel_org_hierarchy_phase6_summary,
    ensure_personnel_organization_unit,
    resolve_manager_by_id,
)
from .profile_photo import (
    PersonnelProfilePhotoResult,
    apply_personnel_profile_photo_action,
    build_personnel_profile_photo_phase4_summary,
    delete_personnel_profile_photo,
    upload_personnel_profile_photo,
)
from .quality_gate import (
    PHASE9_REQUIRED_ROUTE_NAMES,
    PHASE9_REQUIRED_SERVICE_EXPORTS,
    PHASE9_REQUIRED_SERVICE_MODULES,
    PHASE9_ROUTE_LOCAL_HELPERS_REMOVED,
    PersonnelQualityGateResult,
    PersonnelQualityIssue,
    build_personnel_quality_gate_phase9_summary,
    check_personnel_route_cleanup_source,
    check_personnel_service_package_source,
    merge_personnel_quality_gate_results,
    run_personnel_phase9_quality_gate,
)
from .service_inventory import (
    PersonnelServiceFunction,
    build_personnel_service_inventory,
    render_personnel_service_inventory_markdown,
)
from .uniqueness import (
    PersonnelConflictValidationResult,
    build_personnel_uniqueness_phase5_summary,
    validate_admin_manager_sicil_conflicts,
    validate_personnel_identity_uniqueness,
    validate_personnel_manager_id_conflicts,
    validate_personnel_password_change_conflicts,
)
from .workflow import (
    PersonnelMutationSummary,
    apply_personnel_edit_flags,
    apply_personnel_first_login_defaults,
    apply_personnel_identity_payload,
    apply_personnel_initial_password,
    apply_personnel_manager_payload,
    apply_personnel_password_update,
    attach_personnel_org_unit,
    build_new_personnel_user_from_payload,
    build_personnel_workflow_phase3_summary,
    set_personnel_manager_if_exists,
    set_personnel_manager_sicils_from_ids,
    set_personnel_role,
    update_existing_personnel_user_from_payload,
)

__all__ = [
    "PERSONNEL_CORE_TABLES",
    "PERSONNEL_MANAGER_FIELDS",
    "PERSONNEL_OPTIONAL_EXTENSION_TABLES",
    "PERSONNEL_REQUIRED_FIELDS",
    "PERSONNEL_CATEGORY_OPTIONS",
    "user_matches_personnel_category",
    "slugify_personnel_category",
    "seed_default_personnel_categories",
    "normalize_personnel_category_label",
    "get_user_personnel_category_label",
    "get_personnel_category_options",
    "ensure_personnel_category",
    "assign_user_performance_category",
    "PERSONNEL_CATEGORY_DEFAULTS",
    "PERSONNEL_ROUTE_SHIMS",
    "PERSONNEL_SERVICE_MODULES",
    "PERSONNEL_TEMPLATE_SURFACE",
    "PersonnelFormPayload",
    "PersonnelFormValidationResult",
    "PersonnelListFilters",
    "PersonnelListRow",
    "PersonnelListStats",
    "apply_personnel_list_filters",
    "build_personnel_list_base_query",
    "build_personnel_list_context",
    "build_personnel_list_phase2_summary",
    "build_personnel_list_row",
    "build_personnel_list_rows",
    "build_personnel_list_stats",
    "build_personnel_role_values",
    "build_personnel_unit_options",
    "read_personnel_list_filters",
    "PersonnelMutationSummary",
    "upload_personnel_profile_photo",
    "delete_personnel_profile_photo",
    "build_personnel_profile_photo_phase4_summary",
    "apply_personnel_profile_photo_action",
    "PersonnelProfilePhotoResult",
    "PersonnelConflictValidationResult",
    "build_personnel_uniqueness_phase5_summary",
    "validate_admin_manager_sicil_conflicts",
    "validate_personnel_identity_uniqueness",
    "validate_personnel_manager_id_conflicts",
    "validate_personnel_password_change_conflicts",
    "apply_personnel_edit_flags",
    "apply_personnel_first_login_defaults",
    "apply_personnel_identity_payload",
    "apply_personnel_initial_password",
    "apply_personnel_manager_payload",
    "apply_personnel_password_update",
    "attach_personnel_org_unit",
    "build_new_personnel_user_from_payload",
    "build_personnel_workflow_phase3_summary",
    "set_personnel_manager_if_exists",
    "set_personnel_manager_sicils_from_ids",
    "set_personnel_role",
    "update_existing_personnel_user_from_payload",
    "PersonnelOrgHierarchyResult",
    "apply_admin_user_org_hierarchy_fields",
    "apply_manager_id_hierarchy",
    "apply_manager_sicil_hierarchy",
    "attach_organization_unit_to_user",
    "attach_personnel_payload_org_hierarchy",
    "build_personnel_org_hierarchy_phase6_summary",
    "ensure_personnel_organization_unit",
    "resolve_manager_by_id",
    "ACTIVE_LEAVE_ATTENDANCE_STATUSES",
    "LEAVE_ATTENDANCE_REQUIRED_TABLES",
    "PENDING_LEAVE_ATTENDANCE_STATUSES",
    "PersonnelLeaveAttendanceContext",
    "PersonnelLeaveAttendanceFilters",
    "PersonnelLeaveAttendanceReadiness",
    "build_personnel_leave_attendance_cards",
    "build_personnel_leave_attendance_context",
    "build_personnel_leave_attendance_notes",
    "build_personnel_leave_attendance_phase7_summary",
    "check_leave_attendance_readiness",
    "list_personnel_attendance_rows",
    "list_personnel_delegation_rows",
    "list_personnel_leave_balances",
    "list_personnel_leave_rows",
    "read_leave_attendance_filters",
    "PERSONNEL_EXCEL_MANAGER_ALIASES",
    "PERSONNEL_EXCEL_MANAGER_1_ALIASES",
    "PERSONNEL_EXCEL_MANAGER_2_ALIASES",
    "PERSONNEL_EXCEL_MANAGER_3_ALIASES",
    "PERSONNEL_EXCEL_REQUIRED_HEADERS",
    "PERSONNEL_EXCEL_ROLE_ALIASES",
    "PersonnelExcelPreflightResult",
    "PersonnelExcelRowPayload",
    "build_personnel_excel_column_index",
    "build_personnel_excel_import_phase8_summary",
    "build_personnel_excel_row_payload",
    "excel_scalar",
    "has_explicit_personnel_excel_manager_columns",
    "normalize_personnel_excel_headers",
    "preflight_personnel_excel_headers",
    "row_has_required_personnel_excel_fields",
    "PersonnelServiceFunction",
    "build_personnel_create_form_context",
    "build_personnel_edit_form_context",
    "build_personnel_form_phase1_summary",
    "build_personnel_live_scope",
    "build_personnel_service_inventory",
    "check_personnel_phase0_surface",
    "missing_required_personnel_fields",
    "read_personnel_form_payload",
    "render_personnel_service_inventory_markdown",
    "validate_edit_password_fields",
    "validate_manager_selection",
    "validate_required_personnel_payload",
    "PHASE9_REQUIRED_ROUTE_NAMES",
    "PHASE9_REQUIRED_SERVICE_EXPORTS",
    "PHASE9_REQUIRED_SERVICE_MODULES",
    "PHASE9_ROUTE_LOCAL_HELPERS_REMOVED",
    "PersonnelQualityGateResult",
    "PersonnelQualityIssue",
    "build_personnel_quality_gate_phase9_summary",
    "check_personnel_route_cleanup_source",
    "check_personnel_service_package_source",
    "merge_personnel_quality_gate_results",
    "run_personnel_phase9_quality_gate",
    "PHASE10_EXPECTED_FILES",
    "PHASE10_REQUIRED_ROUTE_NAMES",
    "PHASE10_REQUIRED_SERVICE_EXPORTS",
    "PHASE10_REQUIRED_SERVICE_MODULES",
    "PHASE10_SERVICE_SOURCE_FORBIDDEN_MARKERS",
    "PersonnelFinalHardeningIssue",
    "PersonnelFinalHardeningResult",
    "build_personnel_final_hardening_phase10_summary",
    "check_personnel_final_required_files",
    "check_personnel_final_route_contract",
    "check_personnel_final_service_exports",
    "check_personnel_final_service_write_boundary",
    "merge_personnel_final_hardening_results",
    "render_personnel_final_hardening_report",
    "run_personnel_final_hardening_gate",
]


# BYS360_PHASE2_PERSONNEL_CATEGORY_EXPORTS
try:
    from .categories import (
        assign_user_performance_category,
        get_personnel_category_options,
        normalize_personnel_category_label,
        user_matches_personnel_category,
    )
except Exception:  # pragma: no cover
    __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/personnel/__init__.py:368)")
