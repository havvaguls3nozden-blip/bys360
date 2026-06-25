# BYS360 Effective Menu BYS360 Context Preflight V34B
- Generated at: 2026-06-25T21:13:27
- Status: READY_FOR_FACADE_SPLIT
- Ready for split: True
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: 0d41c34
- Target: app/services/settings/effective_menu.py
- Suggested module: app/services/settings/effective_menu_parts/bys360_context.py
- Closure function count: 29 / 29
- Closure total lines: 355
- Projected target lines after split: 1777
- Needed assignments: ['PORTAL_ROLE_MATRIX_V2_12_DEFAULTS', 'PORTAL_ROLE_MATRIX_V2_12_KEYS', '_BYS360_EXEC_KNOWN_KEYS', '_BYS360_EXEC_URL_MARKERS', '_BYS360_GENERAL_CATEGORY_CHILD_KEYS_V1', '_BYS360_GENERAL_CATEGORY_SECTION_KEYS_V1', '_BYS360_PERFORMANCE_CHILD_KEYS', '_BYS360_PERFORMANCE_GENERAL_SHORTCUT_KEYS_V4', '_BYS360_PERFORMANCE_MAIN_KEYS', '_BYS360_PERFORMANCE_MAIN_KEYS_V4', '_BYS360_PERF_RM_V8_ALIAS_GROUPS', '_BYS360_PERF_RM_V8_CANONICAL_CHILD_KEYS', '_BYS360_PERF_RM_V8_CHILD_KEYS', '_BYS360_PERF_RM_V8_MAIN_KEYS']
- Missing functions: []
- Missing assignments: []
- Outside calls: []
- Used imports: ['Any', 'RoleMenuDefault', 'UserMenuPermission', 'is_removed_menu_key', 'logging']
- Used classes: []
- Unknown external names: ['UnitMenuProfile']

## Closure Functions
- normalize_role_name | line=39 | length=2 | inside=[] | outside=[]
- _rollback | line=43 | length=8 | inside=[] | outside=[]
- _safe_query_all | line=360 | length=6 | inside=['_rollback'] | outside=[]
- _get_unit_name_for_authority | line=375 | length=14 | inside=[] | outside=[]
- _row_map_by_key | line=391 | length=8 | inside=[] | outside=[]
- _load_role_matrix_state | line=401 | length=6 | inside=['_row_map_by_key', '_safe_query_all', 'normalize_role_name'] | outside=[]
- _load_unit_profile_state | line=409 | length=12 | inside=['_get_unit_name_for_authority', '_row_map_by_key', '_safe_query_all'] | outside=[]
- _load_user_override_state | line=423 | length=6 | inside=['_row_map_by_key', '_safe_query_all'] | outside=[]
- _bys360_press_news_role | line=456 | length=8 | inside=[] | outside=[]
- _bys360_performance_role_state | line=1200 | length=7 | inside=['_load_role_matrix_state', 'normalize_role_name'] | outside=[]
- _bys360_apply_performance_main_switch | line=1208 | length=15 | inside=['_bys360_performance_role_state'] | outside=[]
- _bys360_restore_general_section_v4 | line=1240 | length=9 | inside=[] | outside=[]
- _bys360_apply_performance_shortcut_gate_v4 | line=1250 | length=6 | inside=[] | outside=[]
- _bys360_perf_rm_v8_norm_role | line=1437 | length=2 | inside=[] | outside=[]
- _bys360_perf_rm_v8_state_for_keys | line=1441 | length=23 | inside=[] | outside=[]
- _bys360_perf_rm_v8_apply_aliases | line=1466 | length=14 | inside=['_bys360_perf_rm_v8_state_for_keys'] | outside=[]
- _bys360_perf_rm_v8_apply_main_gate | line=1482 | length=23 | inside=['_bys360_perf_rm_v8_state_for_keys'] | outside=[]
- _bys360_person_matrix_user_is_admin_v1 | line=1515 | length=7 | inside=['normalize_role_name'] | outside=[]
- _bys360_person_matrix_can_open_v1 | line=1524 | length=15 | inside=['_bys360_person_matrix_user_is_admin_v1'] | outside=[]
- _bys360_general_category_bool_v1 | line=1640 | length=2 | inside=[] | outside=[]
- _bys360_general_category_state_v1 | line=1644 | length=21 | inside=['_load_role_matrix_state', '_load_unit_profile_state', '_load_user_override_state'] | outside=[]
- _bys360_apply_general_category_visibility_fix_v1 | line=1667 | length=29 | inside=['_bys360_general_category_bool_v1', '_bys360_general_category_state_v1', 'normalize_role_name'] | outside=[]
- _bys360_force_home_menu_visible_v1 | line=1702 | length=9 | inside=[] | outside=[]
- _bys360_portal_role_matrix_v2_12_apply | line=1757 | length=38 | inside=['_load_role_matrix_state', '_load_unit_profile_state', '_load_user_override_state', 'normalize_role_name'] | outside=[]
- _bys360_exec_norm | line=1845 | length=8 | inside=['normalize_role_name'] | outside=[]
- _bys360_is_exec_summary_menu_key | line=1855 | length=13 | inside=[] | outside=[]
- _bys360_exec_item_matches | line=1870 | length=12 | inside=['_bys360_is_exec_summary_menu_key'] | outside=[]
- _bys360_admin_period_reminder_norm_v1 | line=2086 | length=7 | inside=[] | outside=[]
- _bys360_admin_period_reminder_is_admin_v1 | line=2094 | length=25 | inside=['_bys360_admin_period_reminder_norm_v1'] | outside=[]

## Assignment Sources

### line 1133 names=['_BYS360_PERFORMANCE_MAIN_KEYS']
```python
_BYS360_PERFORMANCE_MAIN_KEYS = {'performance_module', 'performance_management', 'performans_yonetimi'}
```

### line 1134 names=['_BYS360_PERFORMANCE_CHILD_KEYS']
```python
_BYS360_PERFORMANCE_CHILD_KEYS = {'performance_tasks', 'performance_scorecard', 'scorecards', 'my_performance_comparison', 'performance_dashboard', 'performance_reports', 'performance_criteria', 'criteria', 'performance_periods', 'periods', 'performance_evaluation_tasks', 'assignments', 'performance_task_management', 'performance_hierarchy_tree', 'performance_hierarchy_assignments', 'performance_team_compare', 'team_analysis', 'team_performance_comparison_history', 'performance_feedback_meetings', 'feedback_meetings', 'performance_publish', 'publish', 'performance_mail_settings', 'performance_mail', 'performance_process_tracking', 'performance_process_reports', 'performance_president_approvals', 'performance_personnel_support_publish_approval', 'performance_archive', 'performance_interim_notes', 'performance_development_guidance', 'performance_meeting_p3_reminders', 'performance_kpi_dashboard', 'performance_kpi_management', 'performance_competency_library', 'performance_self_assessment', 'performance_kpi_analysis'}
```

### line 1230 names=['_BYS360_PERFORMANCE_MAIN_KEYS_V4']
```python
_BYS360_PERFORMANCE_MAIN_KEYS_V4 = {'performance_module', 'performance_management', 'performans_yonetimi'}
```

### line 1231 names=['_BYS360_PERFORMANCE_GENERAL_SHORTCUT_KEYS_V4']
```python
_BYS360_PERFORMANCE_GENERAL_SHORTCUT_KEYS_V4 = {'performance_tasks', 'performance_scorecard', 'performance_archive', 'my_performance_comparison', 'performance_reports'}
```

### line 1315 names=['_BYS360_PERF_RM_V8_MAIN_KEYS']
```python
_BYS360_PERF_RM_V8_MAIN_KEYS = {"performance_module", "performance_management", "performans_yonetimi"}
```

### line 1316 names=['_BYS360_PERF_RM_V8_ALIAS_GROUPS']
```python
_BYS360_PERF_RM_V8_ALIAS_GROUPS = {
    "performance_tasks": ["performance_tasks"],
    "performance_scorecard": ["performance_scorecard", "scorecards"],
    "my_performance_comparison": ["my_performance_comparison"],
    "performance_reports": ["performance_reports"],
    "performance_archive": ["performance_archive"],
    "performance_dashboard": ["performance_dashboard"],
    "performance_criteria": ["performance_criteria", "criteria"],
    "performance_periods": ["performance_periods", "periods"],
    "performance_evaluation_tasks": ["performance_evaluation_tasks", "assignments"],
    "performance_task_management": ["performance_task_management"],
    "performance_hierarchy_tree": ["performance_hierarchy_tree"],
    "performance_hierarchy_assignments": ["performance_hierarchy_assignments"],
    "performance_team_compare": ["performance_team_compare", "team_analysis"],
    "team_performance_comparison_history": ["team_performance_comparison_history"],
    "performance_feedback_meetings": ["performance_feedback_meetings", "feedback_meetings"],
    "performance_publish": ["performance_publish", "publish"],
    "performance_mail_settings": ["performance_mail_settings", "performance_mail"],
    "performance_process_tracking": ["performance_process_tracking"],
    "performance_process_reports": ["performance_process_reports"],
    "performance_president_approvals": ["performance_president_approvals"],
    "performance_personnel_support_publish_approval": ["performance_personnel_support_publish_approval"],
    "performance_interim_notes": ["performance_interim_notes"],
    "performance_development_guidance": ["performance_development_guidance"],
    "performance_meeting_p3_reminders": ["performance_meeting_p3_reminders"],
    "performance_feedback_aftercare": ["performance_feedback_aftercare"],
    "performance_feedback_aftercare_new": ["performance_feedback_aftercare_new"],
    "performance_feedback_meeting_guide": ["performance_feedback_meeting_guide"],
    "performance_feedback_followup": ["performance_feedback_followup"],
    "performance_kpi_dashboard": ["performance_kpi_dashboard"],
    "performance_kpi_management": ["performance_kpi_management"],
    "performance_competency_library": ["performance_competency_library"],
    "performance_self_assessment": ["performance_self_assessment"],
    "performance_kpi_analysis": ["performance_kpi_analysis"],
    "performance_history_import": ["performance_history_import"],
}
```

### line 1352 names=['_BYS360_PERF_RM_V8_CHILD_KEYS']
```python
_BYS360_PERF_RM_V8_CHILD_KEYS = {key for values in _BYS360_PERF_RM_V8_ALIAS_GROUPS.values() for key in values}
```

### line 1353 names=['_BYS360_PERF_RM_V8_CANONICAL_CHILD_KEYS']
```python
_BYS360_PERF_RM_V8_CANONICAL_CHILD_KEYS = set(_BYS360_PERF_RM_V8_ALIAS_GROUPS.keys())
```

### line 1626 names=['_BYS360_GENERAL_CATEGORY_SECTION_KEYS_V1']
```python
_BYS360_GENERAL_CATEGORY_SECTION_KEYS_V1 = {"general_section", "genel", "general"}
```

### line 1627 names=['_BYS360_GENERAL_CATEGORY_CHILD_KEYS_V1']
```python
_BYS360_GENERAL_CATEGORY_CHILD_KEYS_V1 = {
    "home",
    "dashboard",
    "notifications",
    "support_index",
    "support_new",
    "support_my_tickets",
    "support_assigned",
    "support_all",
    "support_help_admin",
}
```

### line 1734 names=['PORTAL_ROLE_MATRIX_V2_12_KEYS']
```python
PORTAL_ROLE_MATRIX_V2_12_KEYS = {
    "portal_feed", "portal_people", "portal_profiles", "portal_post_create", "portal_wall_post",
    "portal_post_interact", "portal_post_report", "portal_post_delete", "portal_groups",
    "portal_group_create", "portal_moderation",
}
```

### line 1739 names=['PORTAL_ROLE_MATRIX_V2_12_DEFAULTS']
```python
PORTAL_ROLE_MATRIX_V2_12_DEFAULTS = {
    "admin": PORTAL_ROLE_MATRIX_V2_12_KEYS,
    "baskan": PORTAL_ROLE_MATRIX_V2_12_KEYS,
    "baskan_yardimcisi": PORTAL_ROLE_MATRIX_V2_12_KEYS,
    "grup_baskani": PORTAL_ROLE_MATRIX_V2_12_KEYS,
    "mali_musavir": PORTAL_ROLE_MATRIX_V2_12_KEYS,
    "koordinator": PORTAL_ROLE_MATRIX_V2_12_KEYS - {"portal_moderation"},
    "birim_sorumlusu": PORTAL_ROLE_MATRIX_V2_12_KEYS - {"portal_moderation"},
    "personel": PORTAL_ROLE_MATRIX_V2_12_KEYS - {"portal_group_create", "portal_moderation"},
}
```

### line 1841 names=['_BYS360_EXEC_KNOWN_KEYS']
```python
_BYS360_EXEC_KNOWN_KEYS = {'daily_weather_mail', 'executive_summary_tasks', 'executive_summary_automatic_emails', 'executive_summary_auto_emails', 'executive_summary_logs', 'executive_summary_mail_logs', 'executive_summary_panel', 'executive_summary_test_send', 'executive_daily_weather_mail', 'executive_summary_scheduled_jobs', 'executive_summary_test', 'executive_summary', 'executive_summary_admin_panel', 'executive_summary_dashboard'}
```

### line 1842 names=['_BYS360_EXEC_URL_MARKERS']
```python
_BYS360_EXEC_URL_MARKERS = ('/dashboard/yonetici-ozeti', '/executive-summary', '/yonetici-ozeti')
```

## Safety
- live_system_changed: False
- files_moved: False
- files_deleted: False
- database_touched: False
- source_files_modified: False
