# BYS360 Effective Menu Status After Core Policy Split V48A
- Generated at: 2026-06-26T14:50:48
- Status: READY_FOR_FUNCTION_OR_BLOCK_REVIEW
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: ca19c82
- Target: app/services/settings/effective_menu.py
- Lines: 846
- Lines to go under 800: 47
- Top-level functions: 4
- All functions: 4
- Top-level assignments: 10
- Top-level blocks: 83
- Large top-level blocks >=6: 42
- Duplicate function names: []
- Runtime returncode: 0
- Runtime import OK: True
- Build NameError seen: False
- Force failed message seen: False
- Traceback seen: False

## Parts Modules
- app/services/settings/effective_menu_parts/__init__.py | lines=1 | top_funcs=0 | all_funcs=0 | assignments=0
- app/services/settings/effective_menu_parts/apply_context.py | lines=415 | top_funcs=15 | all_funcs=15 | assignments=5
- app/services/settings/effective_menu_parts/block_context.py | lines=70 | top_funcs=2 | all_funcs=2 | assignments=1
- app/services/settings/effective_menu_parts/build_context.py | lines=305 | top_funcs=1 | all_funcs=1 | assignments=1
- app/services/settings/effective_menu_parts/build_wrapper_context.py | lines=206 | top_funcs=4 | all_funcs=8 | assignments=1
- app/services/settings/effective_menu_parts/bys360_constants.py | lines=457 | top_funcs=0 | all_funcs=0 | assignments=47
- app/services/settings/effective_menu_parts/bys360_context.py | lines=517 | top_funcs=29 | all_funcs=29 | assignments=15
- app/services/settings/effective_menu_parts/core_policy_constants.py | lines=24 | top_funcs=0 | all_funcs=0 | assignments=2
- app/services/settings/effective_menu_parts/phase3_constants.py | lines=190 | top_funcs=0 | all_funcs=0 | assignments=7
- app/services/settings/effective_menu_parts/role_constants.py | lines=149 | top_funcs=0 | all_funcs=0 | assignments=2
- app/services/settings/effective_menu_parts/user_context.py | lines=74 | top_funcs=1 | all_funcs=1 | assignments=1

## Best Next Block Target
- kind: For
- line: 328
- length: 15
- nested functions: []
- preview: for _policy_name in [

## Best Next Function Target
- prefix: build
- functions: 1
- lines: 12
- projected: 834
- suggested: app/services/settings/effective_menu_parts/build_context.py

## Large Top-Level Blocks Top 30
- kind=For | line=328 | length=15 | nested_funcs=0 | preview=for _policy_name in [
- kind=For | line=299 | length=14 | nested_funcs=0 | preview=for _policy_name in [
- kind=For | line=271 | length=13 | nested_funcs=0 | preview=for _policy_name in [
- kind=For | line=805 | length=13 | nested_funcs=0 | preview=for _key, _roles in _BYS360_V223_PERIOD_CENTER_KEY_ROLES.items():
- kind=FunctionDef | line=834 | length=12 | nested_funcs=1 | preview=def build_menu_visibility_map(user, *args, **kwargs):  # type: ignore[no-redef]
- kind=For | line=344 | length=11 | nested_funcs=0 | preview=for _set_name in [
- kind=For | line=422 | length=11 | nested_funcs=0 | preview=for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
- kind=For | line=569 | length=11 | nested_funcs=0 | preview=for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
- kind=For | line=285 | length=10 | nested_funcs=0 | preview=for _set_name in [
- kind=For | line=314 | length=10 | nested_funcs=0 | preview=for _set_name in [
- kind=Assign | line=690 | length=10 | nested_funcs=0 | preview=PORTAL_ROLE_MATRIX_V2_12_DEFAULTS = {
- kind=For | line=251 | length=9 | nested_funcs=0 | preview=for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY"]:
- kind=For | line=365 | length=9 | nested_funcs=0 | preview=for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY"]:
- kind=For | line=468 | length=9 | nested_funcs=0 | preview=for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
- kind=For | line=499 | length=9 | nested_funcs=0 | preview=for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
- kind=For | line=518 | length=9 | nested_funcs=0 | preview=for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
- kind=For | line=604 | length=9 | nested_funcs=0 | preview=for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
- kind=FunctionDef | line=62 | length=8 | nested_funcs=1 | preview=def _log_warning(logger: Any, message: str, *args: Any) -> None:
- kind=Try | line=383 | length=8 | nested_funcs=0 | preview=try:
- kind=For | line=402 | length=8 | nested_funcs=0 | preview=for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
- kind=For | line=433 | length=8 | nested_funcs=0 | preview=for _set_name in ["ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS", "PHASE3_2_MANAGER_VISIBLE_KEYS", "PHASE3_2_GENERAL_VISIBLE_KEYS", "PERFORMANCE_ROLE_MATRIX_KEYS"]:
- kind=Try | line=555 | length=7 | nested_funcs=0 | preview=try:
- kind=Try | line=562 | length=7 | nested_funcs=0 | preview=try:
- kind=Expr | line=4 | length=6 | nested_funcs=0 | preview="""Ayarlar servis menü görünürlük çözümleyicisi.
- kind=For | line=261 | length=6 | nested_funcs=0 | preview=for _set_name in ["PHASE3_2_MANAGER_VISIBLE_KEYS", "PHASE3_2_GENERAL_VISIBLE_KEYS", "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS"]:
- kind=For | line=410 | length=6 | nested_funcs=0 | preview=for _set_name in ["PHASE3_2_MANAGER_VISIBLE_KEYS", "PHASE3_2_GENERAL_VISIBLE_KEYS", "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS", "PERFORMANCE_ROLE_MATRIX_KEYS"]:
- kind=Try | line=445 | length=6 | nested_funcs=0 | preview=try:
- kind=Try | line=461 | length=6 | nested_funcs=0 | preview=try:
- kind=For | line=478 | length=6 | nested_funcs=0 | preview=for _set_name in ["PHASE3_2_MANAGER_VISIBLE_KEYS", "PHASE3_2_GENERAL_VISIBLE_KEYS", "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS", "PERFORMANCE_ROLE_MATRIX_KEYS"]:
- kind=Try | line=488 | length=6 | nested_funcs=0 | preview=try:

## Top-Level Functions
- name=build_menu_visibility_map | line=834 | length=12 | preview=def build_menu_visibility_map(user, *args, **kwargs):  # type: ignore[no-redef]
- name=_log_warning | line=62 | length=8 | preview=def _log_warning(logger: Any, message: str, *args: Any) -> None:
- name=_truthy_bool | line=155 | length=5 | preview=def _truthy_bool(value: Any) -> bool:
- name=_active_menu_items | line=103 | length=2 | preview=def _active_menu_items() -> list[dict[str, Any]]:

## Top-Level Assignments Top 30
- line=690 | length=10 | targets=['PORTAL_ROLE_MATRIX_V2_12_DEFAULTS'] | preview=PORTAL_ROLE_MATRIX_V2_12_DEFAULTS = {
- line=666 | length=6 | targets=['PORTAL_MENU_VISIBILITY_POLICY'] | preview=PORTAL_MENU_VISIBILITY_POLICY = {
- line=742 | length=6 | targets=['build_menu_visibility_map'] | preview=build_menu_visibility_map = apply_v213c_category_menu_wrapper(
- line=755 | length=6 | targets=['build_menu_visibility_map'] | preview=build_menu_visibility_map = apply_v214_category_scope_wrapper(
- line=768 | length=6 | targets=['build_menu_visibility_map'] | preview=build_menu_visibility_map = apply_v215_category_period_scope_wrapper(
- line=781 | length=6 | targets=['build_menu_visibility_map'] | preview=build_menu_visibility_map = apply_v216_category_period_integration_wrapper(
- line=685 | length=5 | targets=['PORTAL_ROLE_MATRIX_V2_12_KEYS'] | preview=PORTAL_ROLE_MATRIX_V2_12_KEYS = {
- line=19 | length=1 | targets=['RollbackHook'] | preview=RollbackHook = Callable[[], None]
- line=192 | length=1 | targets=['build_menu_visibility_map'] | preview=build_menu_visibility_map = _BYS360_BUILD_MENU_VISIBILITY_MAP_CORE_V39C2
- line=830 | length=1 | targets=['_BYS360_PREV_BUILD_MENU_VISIBILITY_MAP_ADMIN_PERIOD_REMINDER_V1'] | preview=_BYS360_PREV_BUILD_MENU_VISIBILITY_MAP_ADMIN_PERIOD_REMINDER_V1 = build_menu_visibility_map

## Safety
- live_system_changed: False
- database_touched: False
- nginx_or_backup_created: False
- source_files_modified: False
- new_files_created: False
