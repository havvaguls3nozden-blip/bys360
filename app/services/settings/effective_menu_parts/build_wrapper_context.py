"""V2.1.3C build_menu_visibility_map wrapper extracted from effective_menu."""

from __future__ import annotations


def apply_v213c_category_menu_wrapper(
    current_build_menu_visibility_map,
    *,
    logging,
    normalize_role_name,
    is_removed_menu_key,
):
    """Apply the V2.1.3C category menu wrapper while preserving legacy behavior."""
    try:
        _BYS360_V213C_CATEGORY_MENU_KEY = "performance_personnel_category_card"
        _BYS360_V213C_CATEGORY_ROLES = {
                "admin", "administrator", "super_admin", "system_admin", "sistem_yoneticisi"
            }
        for _policy_name in [
                "CORE_MENU_VISIBILITY_POLICY",
                "PHASE3_PERFORMANCE_MENU_POLICY",
                "PHASE3_2_PERFORMANCE_MENU_POLICY",
                "PERFORMANCE_MENU_POLICY",
                "ROLE_MENU_POLICY",
                "ROLE_MATRIX_POLICY",
            ]:
                _policy = globals().get(_policy_name)
                if isinstance(_policy, dict):
                    _current = _policy.setdefault(_BYS360_V213C_CATEGORY_MENU_KEY, set())
                    if isinstance(_current, set):
                        _current.update(_BYS360_V213C_CATEGORY_ROLES)
                    elif isinstance(_current, list):
                        for _role in _BYS360_V213C_CATEGORY_ROLES:
                            if _role not in _current:
                                _current.append(_role)
        for _set_name in [
                "PHASE3_2_GENERAL_VISIBLE_KEYS",
                "PERFORMANCE_ROLE_MATRIX_KEYS",
                "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS",
            ]:
                _target = globals().get(_set_name)
                if isinstance(_target, set):
                    _target.add(_BYS360_V213C_CATEGORY_MENU_KEY)
                elif isinstance(_target, list) and _BYS360_V213C_CATEGORY_MENU_KEY not in _target:
                    _target.append(_BYS360_V213C_CATEGORY_MENU_KEY)
        _BYS360_V213C_PREVIOUS_BUILD_MENU_VISIBILITY_MAP = current_build_menu_visibility_map
        def _bys360_v213c_build_menu_visibility_map_wrapper(user, *args, **kwargs):  # type: ignore[no-redef]
                visibility = dict(_BYS360_V213C_PREVIOUS_BUILD_MENU_VISIBILITY_MAP(user, *args, **kwargs) or {})
                try:
                    _role = normalize_role_name(getattr(user, "role", ""))
                except Exception:
                    logger = __import__("logging").getLogger(__name__)
                    logger.exception("BYS360 effective menu isleminde hata yakalandi")
                    _role = str(getattr(user, "role", "") or "").strip().lower()
                _is_admin_like = bool(
                    _role in _BYS360_V213C_CATEGORY_ROLES
                    or getattr(user, "is_admin", False)
                    or getattr(user, "is_superuser", False)
                )
                if _is_admin_like and not is_removed_menu_key(_BYS360_V213C_CATEGORY_MENU_KEY):
                    visibility[_BYS360_V213C_CATEGORY_MENU_KEY] = True
                    visibility["performance_module"] = True
                    visibility["performance_management"] = True
                    visibility["performans_yonetimi"] = True
                return visibility

        return _bys360_v213c_build_menu_visibility_map_wrapper
    except Exception:
        try:
            logging.exception("BYS360 V2.1.3C kategori menü effective_menu force uygulanamadı")
        except Exception:
            pass
        return current_build_menu_visibility_map


__all__ = [
    "apply_v213c_category_menu_wrapper",
]
