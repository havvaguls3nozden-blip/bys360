# BYS360 Effective Menu Status After Independent Block Split V45A
- Generated at: 2026-06-26T12:23:23
- Status: READY_FOR_FUNCTION_OR_BLOCK_REVIEW
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: 21d129c
- Target: app/services/settings/effective_menu.py
- Lines: 901
- Lines to go under 800: 102
- Top-level functions: 5
- All functions: 5
- Top-level assignments: 11
- Top-level blocks: 82
- Large top-level blocks >=10: 14
- Duplicate function names: []
- Runtime returncode: 0
- Runtime import OK: True
- Build NameError seen: False
- Force failed message seen: False
- Traceback seen: False

## Parts Modules
- app/services/settings/effective_menu_parts/__init__.py | lines=1 | top_funcs=0 | all_funcs=0 | assignments=0
- app/services/settings/effective_menu_parts/apply_context.py | lines=415 | top_funcs=15 | all_funcs=15 | assignments=5
- app/services/settings/effective_menu_parts/block_context.py | lines=43 | top_funcs=1 | all_funcs=1 | assignments=1
- app/services/settings/effective_menu_parts/build_context.py | lines=305 | top_funcs=1 | all_funcs=1 | assignments=1
- app/services/settings/effective_menu_parts/build_wrapper_context.py | lines=206 | top_funcs=4 | all_funcs=8 | assignments=1
- app/services/settings/effective_menu_parts/bys360_constants.py | lines=457 | top_funcs=0 | all_funcs=0 | assignments=47
- app/services/settings/effective_menu_parts/bys360_context.py | lines=517 | top_funcs=29 | all_funcs=29 | assignments=15
- app/services/settings/effective_menu_parts/phase3_constants.py | lines=190 | top_funcs=0 | all_funcs=0 | assignments=7
- app/services/settings/effective_menu_parts/role_constants.py | lines=149 | top_funcs=0 | all_funcs=0 | assignments=2

## Best Next Block Target
- kind: FunctionDef
- line: 124
- length: 30
- nested functions: ['_user_has_any_assigned_survey']
- preview: def _user_has_any_assigned_survey(user: Any, *, rollback: RollbackHook | None = None) -> bool:

## Best Next Function Target
- prefix: _user
- functions: 1
- lines: 30
- projected: 871
- suggested: app/services/settings/effective_menu_parts/user_context.py

## Large Top-Level Blocks Top 20
- kind=FunctionDef | line=124 | length=30 | nested_funcs=1 | preview=def _user_has_any_assigned_survey(user: Any, *, rollback: RollbackHook | None = None) -> bool:
- kind=Try | line=415 | length=22 | nested_funcs=0 | preview=try:
- kind=AnnAssign | line=21 | length=16 | nested_funcs=0 | preview=CORE_MENU_VISIBILITY_POLICY: dict[str, set[str]] = {
- kind=For | line=366 | length=15 | nested_funcs=0 | preview=for _policy_name in [
- kind=For | line=337 | length=14 | nested_funcs=0 | preview=for _policy_name in [
- kind=For | line=309 | length=13 | nested_funcs=0 | preview=for _policy_name in [
- kind=For | line=860 | length=13 | nested_funcs=0 | preview=for _key, _roles in _BYS360_V223_PERIOD_CENTER_KEY_ROLES.items():
- kind=FunctionDef | line=889 | length=12 | nested_funcs=1 | preview=def build_menu_visibility_map(user, *args, **kwargs):  # type: ignore[no-redef]
- kind=For | line=382 | length=11 | nested_funcs=0 | preview=for _set_name in [
- kind=For | line=477 | length=11 | nested_funcs=0 | preview=for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
- kind=For | line=624 | length=11 | nested_funcs=0 | preview=for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
- kind=For | line=323 | length=10 | nested_funcs=0 | preview=for _set_name in [
- kind=For | line=352 | length=10 | nested_funcs=0 | preview=for _set_name in [
- kind=Assign | line=745 | length=10 | nested_funcs=0 | preview=PORTAL_ROLE_MATRIX_V2_12_DEFAULTS = {

## Top-Level Functions
- name=_user_has_any_assigned_survey | line=124 | length=30 | preview=def _user_has_any_assigned_survey(user: Any, *, rollback: RollbackHook | None = None) -> bool:
- name=build_menu_visibility_map | line=889 | length=12 | preview=def build_menu_visibility_map(user, *args, **kwargs):  # type: ignore[no-redef]
- name=_log_warning | line=74 | length=8 | preview=def _log_warning(logger: Any, message: str, *args: Any) -> None:
- name=_truthy_bool | line=193 | length=5 | preview=def _truthy_bool(value: Any) -> bool:
- name=_active_menu_items | line=115 | length=2 | preview=def _active_menu_items() -> list[dict[str, Any]]:

## Safety
- live_system_changed: False
- database_touched: False
- nginx_or_backup_created: False
- source_files_modified: False
- new_files_created: False
