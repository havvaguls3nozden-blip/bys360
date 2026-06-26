"""Independent effective-menu top-level policy blocks."""


def apply_daily_weather_policy_block(globals_dict, *, logging):
    """Apply daily-weather menu visibility policy mutations to the caller module globals."""
    try:
        _BYS360_DAILY_WEATHER_SYSTEM_ADMIN_ROLES = {'admin', 'super_admin', 'system_admin', 'sistem_yoneticisi'}
        _BYS360_DAILY_WEATHER_DISALLOWED_ROLES = {'baskan', 'baskan_yardimcisi', 'grup_baskani', 'mali_musavir', 'koordinator', 'birim_sorumlusu', 'performans_yetkilisi', 'personel', 'user', 'employee', 'ik', 'hr'}
        for _policy_name in [
            "PHASE3_PERFORMANCE_MENU_POLICY",
            "PHASE3_2_PERFORMANCE_MENU_POLICY",
            "PERFORMANCE_MENU_POLICY",
            "ROLE_MENU_POLICY",
            "ROLE_MATRIX_POLICY",
        ]:
            _policy = globals_dict.get(_policy_name)
            if isinstance(_policy, dict):
                _policy["daily_weather_mail"] = set(_BYS360_DAILY_WEATHER_SYSTEM_ADMIN_ROLES)
                _policy.setdefault("executive_summary", set())
                if isinstance(_policy.get("executive_summary"), set):
                    _policy["executive_summary"].update(_BYS360_DAILY_WEATHER_SYSTEM_ADMIN_ROLES)
                elif isinstance(_policy.get("executive_summary"), list):
                    for _r in _BYS360_DAILY_WEATHER_SYSTEM_ADMIN_ROLES:
                        if _r not in _policy["executive_summary"]:
                            _policy["executive_summary"].append(_r)
        for _set_name in [
            "PHASE3_2_MANAGER_VISIBLE_KEYS",
            "PHASE3_2_GENERAL_VISIBLE_KEYS",
            "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS",
            "PERFORMANCE_ROLE_MATRIX_KEYS",
        ]:
            _target = globals_dict.get(_set_name)
            if isinstance(_target, set):
                _target.add("daily_weather_mail")
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        pass


def apply_role_matrix_runtime_authority_keys_block(ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS):
    """Apply role-matrix runtime authority key mutations."""
    try:
        ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS.update({
            "ai_agent_panel",
            "performance_president_approvals",
            "performance_personnel_support_publish_approval",
            "performance_process_tracking",
            "performance_process_reports",
            "performance_interim_notes",
            "performance_development_guidance",
            "performance_meeting_p3_reminders",
            "performance_archive",
            "performance_kpi_dashboard",
            "performance_kpi_management",
            "performance_competency_library",
            "performance_self_assessment",
            "performance_kpi_analysis",
            "performance_team_compare",
            "performance_feedback_meetings",
            "team_performance_comparison_history",
        })
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/settings/effective_menu.py:822)")


def apply_performance_role_matrix_new_tab_policy_block(policy_globals, _BYS360_PERFORMANCE_ROLE_MATRIX_NEW_TAB_POLICY):
    """Apply performance role-matrix new-tab policy mutations."""
    for _policy_name in [
        "PHASE3_PERFORMANCE_MENU_POLICY",
        "PHASE3_2_PERFORMANCE_MENU_POLICY",
        "PERFORMANCE_MENU_POLICY",
        "ROLE_MENU_POLICY",
        "ROLE_MATRIX_POLICY",
    ]:
        _policy = policy_globals.get(_policy_name)
        if isinstance(_policy, dict):
            for _key, _roles in _BYS360_PERFORMANCE_ROLE_MATRIX_NEW_TAB_POLICY.items():
                _current = _policy.setdefault(_key, set())
                if isinstance(_current, set):
                    _current.update(_roles)
                elif isinstance(_current, list):
                    _current.extend([_r for _r in _roles if _r not in _current])


def apply_process_menu_policy_block(policy_globals, _BYS360_PROCESS_MENU_KEYS, _BYS360_PROCESS_MENU_ROLES):
    """Apply process menu policy mutations."""
    for _policy_name in [
        "PHASE3_PERFORMANCE_MENU_POLICY",
        "PHASE3_2_PERFORMANCE_MENU_POLICY",
        "PERFORMANCE_MENU_POLICY",
        "ROLE_MENU_POLICY",
    ]:
        _policy = policy_globals.get(_policy_name)
        if isinstance(_policy, dict):
            for _key in _BYS360_PROCESS_MENU_KEYS:
                _current = _policy.setdefault(_key, set())
                if isinstance(_current, set):
                    _current.update(_BYS360_PROCESS_MENU_ROLES)
                elif isinstance(_current, list):
                    _current.extend([_r for _r in _BYS360_PROCESS_MENU_ROLES if _r not in _current])


def apply_reminders_menu_policy_block(policy_globals, _BYS360_REMINDERS_MENU_KEY, _BYS360_REMINDERS_ALLOWED_ROLES):
    """Apply reminders menu policy mutations."""
    for _policy_name in [
        "PHASE3_PERFORMANCE_MENU_POLICY",
        "PHASE3_2_PERFORMANCE_MENU_POLICY",
        "PERFORMANCE_MENU_POLICY",
        "ROLE_MENU_POLICY",
    ]:
        _policy = policy_globals.get(_policy_name)
        if isinstance(_policy, dict):
            _current = _policy.setdefault(_BYS360_REMINDERS_MENU_KEY, set())
            if isinstance(_current, set):
                _current.update(_BYS360_REMINDERS_ALLOWED_ROLES)
            elif isinstance(_current, list):
                _current.extend([_r for _r in _BYS360_REMINDERS_ALLOWED_ROLES if _r not in _current])


def apply_period_center_key_roles_block(CORE_MENU_VISIBILITY_POLICY, ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS, _BYS360_V223_PERIOD_CENTER_KEY_ROLES, logging):
    """Apply V2.2.3 period center key-role policy mutations."""
    for _key, _roles in _BYS360_V223_PERIOD_CENTER_KEY_ROLES.items():
        try:
            ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS.add(_key)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
            pass
        try:
            CORE_MENU_VISIBILITY_POLICY.setdefault(_key, set()).update(set(_roles))
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
            pass


def apply_performance_role_matrix_new_tab_sets_block(policy_globals, _BYS360_PERFORMANCE_ROLE_MATRIX_NEW_TAB_POLICY):
    """Apply performance role matrix new-tab set mutations."""
    for _set_name in [
        "PHASE3_2_MANAGER_VISIBLE_KEYS",
        "PHASE3_2_GENERAL_VISIBLE_KEYS",
        "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS",
        "PERFORMANCE_ROLE_MATRIX_KEYS",
    ]:
        _target = policy_globals.get(_set_name)
        if isinstance(_target, set):
            _target.update(_BYS360_PERFORMANCE_ROLE_MATRIX_NEW_TAB_POLICY.keys())
        elif isinstance(_target, list):
            _target.extend([_k for _k in _BYS360_PERFORMANCE_ROLE_MATRIX_NEW_TAB_POLICY.keys() if _k not in _target])


__all__ = [
    "apply_daily_weather_policy_block",
    "apply_performance_role_matrix_new_tab_policy_block",
    "apply_performance_role_matrix_new_tab_sets_block",
    "apply_period_center_key_roles_block",
    "apply_process_menu_policy_block",
    "apply_reminders_menu_policy_block",
    "apply_role_matrix_runtime_authority_keys_block",
]
