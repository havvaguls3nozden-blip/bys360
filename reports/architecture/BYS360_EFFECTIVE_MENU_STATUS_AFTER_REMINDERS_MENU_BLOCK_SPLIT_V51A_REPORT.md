# BYS360 Effective Menu Status After Reminders Menu Block Split V51A
- Generated at: 2026-06-26T15:11:08
- Status: READY_FOR_FUNCTION_OR_BLOCK_REVIEW
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: 9b03b62
- Target: app/services/settings/effective_menu.py
- Lines: 830
- Lines to go under 800: 31
- Top-level functions: 4
- All functions: 4
- Top-level assignments: 10
- Top-level blocks: 86
- Large top-level blocks >=6: 39
- Duplicate function names: []
- Runtime returncode: 0
- Runtime import OK: True
- Build NameError seen: False
- Force failed message seen: False
- Traceback seen: False

## Best Next Block Target
- kind: For
- line: 789
- length: 13
- nested functions: []
- preview: for _key, _roles in _BYS360_V223_PERIOD_CENTER_KEY_ROLES.items():

## Best Next Function Target
- prefix: build
- functions: 1
- lines: 12
- projected: 818
- suggested: app/services/settings/effective_menu_parts/build_context.py

## Large Top-Level Blocks Top 30
- kind=For | line=789 | length=13 | nested_funcs=0 | preview=for _key, _roles in _BYS360_V223_PERIOD_CENTER_KEY_ROLES.items():
- kind=FunctionDef | line=818 | length=12 | nested_funcs=1 | preview=def build_menu_visibility_map(user, *args, **kwargs):  # type: ignore[no-redef]
- kind=For | line=328 | length=11 | nested_funcs=0 | preview=for _set_name in [
- kind=For | line=406 | length=11 | nested_funcs=0 | preview=for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
- kind=For | line=553 | length=11 | nested_funcs=0 | preview=for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
- kind=For | line=281 | length=10 | nested_funcs=0 | preview=for _set_name in [
- kind=For | line=305 | length=10 | nested_funcs=0 | preview=for _set_name in [
- kind=Assign | line=674 | length=10 | nested_funcs=0 | preview=PORTAL_ROLE_MATRIX_V2_12_DEFAULTS = {
- kind=For | line=251 | length=9 | nested_funcs=0 | preview=for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY"]:
- kind=For | line=349 | length=9 | nested_funcs=0 | preview=for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY"]:
- kind=For | line=452 | length=9 | nested_funcs=0 | preview=for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
- kind=For | line=483 | length=9 | nested_funcs=0 | preview=for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
- kind=For | line=502 | length=9 | nested_funcs=0 | preview=for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
- kind=For | line=588 | length=9 | nested_funcs=0 | preview=for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
- kind=FunctionDef | line=62 | length=8 | nested_funcs=1 | preview=def _log_warning(logger: Any, message: str, *args: Any) -> None:
- kind=Try | line=367 | length=8 | nested_funcs=0 | preview=try:
- kind=For | line=386 | length=8 | nested_funcs=0 | preview=for _policy_name in ["PHASE3_PERFORMANCE_MENU_POLICY", "PHASE3_2_PERFORMANCE_MENU_POLICY", "PERFORMANCE_MENU_POLICY", "ROLE_MENU_POLICY", "ROLE_MATRIX_POLICY"]:
- kind=For | line=417 | length=8 | nested_funcs=0 | preview=for _set_name in ["ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS", "PHASE3_2_MANAGER_VISIBLE_KEYS", "PHASE3_2_GENERAL_VISIBLE_KEYS", "PERFORMANCE_ROLE_MATRIX_KEYS"]:
- kind=Try | line=539 | length=7 | nested_funcs=0 | preview=try:
- kind=Try | line=546 | length=7 | nested_funcs=0 | preview=try:
- kind=Expr | line=4 | length=6 | nested_funcs=0 | preview="""Ayarlar servis menü görünürlük çözümleyicisi.
- kind=For | line=261 | length=6 | nested_funcs=0 | preview=for _set_name in ["PHASE3_2_MANAGER_VISIBLE_KEYS", "PHASE3_2_GENERAL_VISIBLE_KEYS", "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS"]:
- kind=For | line=394 | length=6 | nested_funcs=0 | preview=for _set_name in ["PHASE3_2_MANAGER_VISIBLE_KEYS", "PHASE3_2_GENERAL_VISIBLE_KEYS", "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS", "PERFORMANCE_ROLE_MATRIX_KEYS"]:
- kind=Try | line=429 | length=6 | nested_funcs=0 | preview=try:
- kind=Try | line=445 | length=6 | nested_funcs=0 | preview=try:
- kind=For | line=462 | length=6 | nested_funcs=0 | preview=for _set_name in ["PHASE3_2_MANAGER_VISIBLE_KEYS", "PHASE3_2_GENERAL_VISIBLE_KEYS", "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS", "PERFORMANCE_ROLE_MATRIX_KEYS"]:
- kind=Try | line=472 | length=6 | nested_funcs=0 | preview=try:
- kind=Try | line=496 | length=6 | nested_funcs=0 | preview=try:
- kind=For | line=511 | length=6 | nested_funcs=0 | preview=for _set_name in ["PHASE3_2_MANAGER_VISIBLE_KEYS", "PHASE3_2_GENERAL_VISIBLE_KEYS", "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS", "PERFORMANCE_ROLE_MATRIX_KEYS"]:
- kind=Try | line=525 | length=6 | nested_funcs=0 | preview=try:
