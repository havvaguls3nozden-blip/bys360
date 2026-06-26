# BYS360 Effective Menu Status After Final Wrapper Split V44A
- Generated at: 2026-06-26T11:50:44
- Status: WRAPPER_TRY_BLOCKS_CLEARED_READY_FOR_BLOCK_REVIEW
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: b283413
- Target: app/services/settings/effective_menu.py
- Lines: 929
- Lines to go under 800: 130
- Top-level functions: 5
- All functions: 5
- Top-level blocks: 81
- Large top-level blocks >=15: 5
- Build wrapper blocks: 1
- Duplicate function names: []
- Runtime returncode: 0
- Runtime import OK: True
- Build NameError seen: False
- Force failed message seen: False
- Traceback seen: False

## Parts Modules
- app/services/settings/effective_menu_parts/__init__.py | lines=1 | top_funcs=0 | all_funcs=0 | assignments=0
- app/services/settings/effective_menu_parts/apply_context.py | lines=415 | top_funcs=15 | all_funcs=15 | assignments=5
- app/services/settings/effective_menu_parts/build_context.py | lines=305 | top_funcs=1 | all_funcs=1 | assignments=1
- app/services/settings/effective_menu_parts/build_wrapper_context.py | lines=206 | top_funcs=4 | all_funcs=8 | assignments=1
- app/services/settings/effective_menu_parts/bys360_constants.py | lines=457 | top_funcs=0 | all_funcs=0 | assignments=47
- app/services/settings/effective_menu_parts/bys360_context.py | lines=517 | top_funcs=29 | all_funcs=29 | assignments=15
- app/services/settings/effective_menu_parts/phase3_constants.py | lines=190 | top_funcs=0 | all_funcs=0 | assignments=7
- app/services/settings/effective_menu_parts/role_constants.py | lines=149 | top_funcs=0 | all_funcs=0 | assignments=2

## Build Wrapper Blocks
- kind=FunctionDef | line=917 | length=12 | nested_functions=['build_menu_visibility_map'] | preview=def build_menu_visibility_map(user, *args, **kwargs):  # type: ignore[no-redef]

## Large Top-Level Blocks Top 20
- kind=Try | line=769 | length=33 | nested_funcs=0 | contains_build=False | preview=try:
- kind=FunctionDef | line=124 | length=30 | nested_funcs=1 | contains_build=False | preview=def _user_has_any_assigned_survey(user: Any, *, rollback: RollbackHook | None = None) -> bool:
- kind=Try | line=415 | length=22 | nested_funcs=0 | contains_build=False | preview=try:
- kind=AnnAssign | line=21 | length=16 | nested_funcs=0 | contains_build=False | preview=CORE_MENU_VISIBILITY_POLICY: dict[str, set[str]] = {
- kind=For | line=366 | length=15 | nested_funcs=0 | contains_build=False | preview=for _policy_name in [

## Recommended Function Candidates Top 20

## Safety
- live_system_changed: False
- database_touched: False
- nginx_or_backup_created: False
- source_files_modified: False
- new_files_created: False
