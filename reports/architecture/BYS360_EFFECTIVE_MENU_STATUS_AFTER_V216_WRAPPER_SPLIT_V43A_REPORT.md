# BYS360 Effective Menu Status After V216 Wrapper Split V43A
- Generated at: 2026-06-26T11:34:49
- Status: READY_FOR_NEXT_WRAPPER_PREFLIGHT
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: 791058f
- Target: app/services/settings/effective_menu.py
- Lines: 941
- Lines to go under 800: 142
- Top-level functions: 5
- All functions: 6
- Top-level blocks: 80
- Large top-level blocks >=20: 4
- Build wrapper blocks: 2
- Duplicate function names: ['build_menu_visibility_map']
- Runtime returncode: 0
- Runtime import OK: True
- Build NameError seen: False
- Force failed message seen: False
- Traceback seen: False

## Parts Modules
- app/services/settings/effective_menu_parts/__init__.py | lines=1 | top_funcs=0 | all_funcs=0 | assignments=0
- app/services/settings/effective_menu_parts/apply_context.py | lines=415 | top_funcs=15 | all_funcs=15 | assignments=5
- app/services/settings/effective_menu_parts/build_context.py | lines=305 | top_funcs=1 | all_funcs=1 | assignments=1
- app/services/settings/effective_menu_parts/build_wrapper_context.py | lines=168 | top_funcs=3 | all_funcs=6 | assignments=1
- app/services/settings/effective_menu_parts/bys360_constants.py | lines=457 | top_funcs=0 | all_funcs=0 | assignments=47
- app/services/settings/effective_menu_parts/bys360_context.py | lines=517 | top_funcs=29 | all_funcs=29 | assignments=15
- app/services/settings/effective_menu_parts/phase3_constants.py | lines=190 | top_funcs=0 | all_funcs=0 | assignments=7
- app/services/settings/effective_menu_parts/role_constants.py | lines=149 | top_funcs=0 | all_funcs=0 | assignments=2

## Best Next Wrapper Block Target
- kind: Try
- line: 834
- length: 22
- nested functions: ['build_menu_visibility_map']
- preview: try:

## Build Wrapper Blocks
- kind=Try | line=834 | length=22 | nested_functions=['build_menu_visibility_map'] | preview=try:
- kind=FunctionDef | line=929 | length=12 | nested_functions=['build_menu_visibility_map'] | preview=def build_menu_visibility_map(user, *args, **kwargs):  # type: ignore[no-redef]

## Large Top-Level Blocks Top 20
- kind=Try | line=769 | length=33 | nested_funcs=0 | contains_build=False | preview=try:
- kind=FunctionDef | line=124 | length=30 | nested_funcs=1 | contains_build=False | preview=def _user_has_any_assigned_survey(user: Any, *, rollback: RollbackHook | None = None) -> bool:
- kind=Try | line=415 | length=22 | nested_funcs=0 | contains_build=False | preview=try:
- kind=Try | line=834 | length=22 | nested_funcs=1 | contains_build=True | preview=try:

## Recommended Function Candidates Top 20

## Safety
- live_system_changed: False
- database_touched: False
- nginx_or_backup_created: False
- source_files_modified: False
- new_files_created: False
