# BYS360 Effective Menu Apply Context Preflight V35B
- Generated at: 2026-06-26T08:45:00
- Status: READY_FOR_FACADE_SPLIT
- Ready for split: True
- Branch: phase4j-script-reduction-godobject-v1
- HEAD: 61fc9d9
- Target: app/services/settings/effective_menu.py
- Suggested module: app/services/settings/effective_menu_parts/apply_context.py
- Closure function count: 15 / 15
- Closure total lines: 236
- Projected target lines after split: 1574
- Needed assignments: ['CORE_MENU_VISIBILITY_POLICY', 'PHASE3_2_PERFORMANCE_MENU_POLICY', 'PHASE3_PERFORMANCE_MENU_POLICY', 'ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS']
- Missing functions: []
- Missing assignments: []
- Outside calls: []
- Used imports: ['Any', 'RoleMenuDefault', '_bys360_person_matrix_can_open_v1', '_bys360_press_news_role', '_load_role_matrix_state', '_load_unit_profile_state', '_load_user_override_state', '_rollback', 'is_removed_menu_key', 'normalize_role_name']
- Used classes: []
- Unknown external names: []

## Closure Functions
- _get_role_matrix_closed_keys_for_role | line=111 | length=21 | inside=[] | outside=[]
- _apply_role_matrix_closed_guard | line=134 | length=19 | inside=['_get_role_matrix_closed_keys_for_role'] | outside=[]
- _role_matrix_runtime_closed | line=155 | length=2 | inside=[] | outside=[]
- _role_allowed_for_menu | line=162 | length=9 | inside=[] | outside=[]
- _apply_core_menu_visibility_policy | line=175 | length=40 | inside=['_role_matrix_runtime_closed'] | outside=[]
- _apply_role_gate | line=248 | length=7 | inside=['_role_allowed_for_menu'] | outside=[]
- _apply_phase3_performance_menu_policy | line=278 | length=7 | inside=[] | outside=[]
- _phase3_2_ascii_tr | line=340 | length=10 | inside=[] | outside=[]
- _phase3_2_normalize_role_name | line=352 | length=9 | inside=['_phase3_2_ascii_tr'] | outside=[]
- _apply_phase3_2_performance_menu_visibility | line=363 | length=13 | inside=['_phase3_2_normalize_role_name'] | outside=[]
- _menu_item_by_key | line=402 | length=2 | inside=[] | outside=[]
- _allowed_by_static_gate | line=406 | length=5 | inside=['_role_allowed_for_menu'] | outside=[]
- _settings_explicitly_controls_key | line=413 | length=8 | inside=[] | outside=[]
- _apply_bys360_press_news_admin_only_policy | line=429 | length=8 | inside=[] | outside=[]
- _apply_bys360_settings_live_authority_v1 | line=1383 | length=76 | inside=['_allowed_by_static_gate', '_menu_item_by_key', '_settings_explicitly_controls_key'] | outside=[]

## Assignment Sources

### line 21 names=['CORE_MENU_VISIBILITY_POLICY']
```python
CORE_MENU_VISIBILITY_POLICY: dict[str, set[str]] = {
    "messages": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"},
    "notifications": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"},
    "surveys": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"},
    "survey_manage": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"},
    "survey_results": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"},
    "feedback_dashboard": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"},
    "feedback_pulse": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"},
    "feedback_campaigns": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"},
    "feedback_results": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"},
    "feedback_actions": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"},
    "feedback_manager": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"},
    "feedback_admin": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir"},
    "performance_reports": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"},
    "analysis_center": {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"},
}
```

### line 84 names=['ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS']
```python
ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS: set[str] = {
    "messages",
    "notifications",
    "surveys",
    "survey_manage",
    "survey_results",
    "feedback_dashboard",
    "feedback_pulse",
    "feedback_campaigns",
    "feedback_results",
    "feedback_actions",
    "feedback_manager",
    "feedback_admin",
    "portal_press_news",
    "announcements",
    "assistant_center",
    "assistant_my_reminders",
    "assistant_scheduled_tasks",
    "assistant_report_generate",
    "assistant_report_share",
    "assistant_ai_summary",
    "assistant_process_alerts",
    "assistant_logs",
    "assistant_settings",
}
```

### line 257 names=['PHASE3_PERFORMANCE_MENU_POLICY']
```python
PHASE3_PERFORMANCE_MENU_POLICY: dict[str, set[str]] = {
    # Personel: kendi karnesi ve kendi kıyas/ortalama görünümü.
    "performance_scorecard": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"},
    "my_performance_comparison": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu", "personel"},

    # Koordinatör/Grup Başkanı: kendi kapsamındaki personel ve ortalamalar.
    "performance_reports": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"},
    "performance_team_compare": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"},
    "team_performance_comparison_history": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"},

    # Yönetim ekranları: genel/teknik yönetim ailesi.
    "performance_criteria": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "baskan", "baskan_yardimcisi"},
    "performance_periods": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "baskan", "baskan_yardimcisi"},
    "performance_task_management": {"admin", "sistem_yoneticisi", "system_admin", "super_admin"},
    "performance_hierarchy_tree": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"},
    "performance_hierarchy_assignments": {"admin", "sistem_yoneticisi", "system_admin", "super_admin"},
    "performance_publish": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "baskan"},
    "performance_history_import": {"admin", "sistem_yoneticisi", "system_admin", "super_admin"},
}
```

### line 293 names=['PHASE3_2_PERFORMANCE_MENU_POLICY']
```python
PHASE3_2_PERFORMANCE_MENU_POLICY: dict[str, set[str]] = {
    # Personel: yalnızca kendi karnesi ve kendi grup/kategori ortalaması tarafı.
    "performance_scorecard": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu", "personel", "user", "standart_personel"},
    "my_performance_comparison": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu", "personel", "user", "standart_personel"},

    # Koordinatör ve Grup Başkanı: yalnızca kendi kapsamındaki personel/ortalama ekranları.
    "performance_reports": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu"},
    "performance_team_compare": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu"},
    "team_performance_comparison_history": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu"},
    "performance_evaluation_tasks": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu"},
    "performance_tasks": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu"},
    "performance_interim_notes": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu"},
    "performance_development_guidance": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu"},
    "performance_feedback_meetings": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu"},

    # Başkan/Admin: genel yönetim görünümü.
    "performance_criteria": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı"},
    "performance_periods": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı"},
    "performance_hierarchy_tree": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu"},
    "performance_publish": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president"},
    "performance_president_approvals": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president"},
    "performance_personnel_support_publish_approval": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "grup_baskani", "grup_başkanı"},

    # Teknik yönetim: yalnızca Admin/Sistem Yöneticisi.
    "performance_task_management": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator"},
    "performance_hierarchy_assignments": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator"},
    "performance_history_import": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator"},
    "performance_mail_settings": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator"},

    # Stratejik Performans — KPI, Hedef, Yetkinlik, Öz Değerlendirme
    "performance_kpi_dashboard": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör"},
    "performance_kpi_management": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör"},
    "performance_competency_library": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu"},
    "performance_self_assessment": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör", "birim_sorumlusu"},
    "performance_kpi_analysis": {"admin", "sistem_yoneticisi", "system_admin", "super_admin", "administrator", "baskan", "başkan", "president", "baskan_yardimcisi", "başkan_yardımcısı", "grup_baskani", "grup_başkanı", "mali_musavir", "mali_müşavir", "koordinator", "koordinatör"},
}
```

## Safety
- live_system_changed: False
- files_moved: False
- files_deleted: False
- database_touched: False
- source_files_modified: False
