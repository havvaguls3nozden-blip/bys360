from __future__ import annotations

import logging
from functools import wraps

from flask import abort
from flask_login import current_user

logger = logging.getLogger(__name__)


def role_required(*allowed_roles: str):
    allowed = {str(r).strip().lower() for r in allowed_roles}

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            role = str(getattr(current_user, "role", "") or "").strip().lower()
            if role not in allowed:
                abort(403)
            return view_func(*args, **kwargs)

        return wrapper

    return decorator


def menu_visible_required(menu_key: str):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)

            perms = getattr(current_user, "menu_permissions", None)
            if perms is None:
                return view_func(*args, **kwargs)

            try:
                iterable = perms.all() if hasattr(perms, "all") else perms
            except Exception as exc:
                logger.exception("BYS360 critical exception captured in app/security/decorators.py", exc_info=exc)
                iterable = []

            visible = {getattr(p, "menu_key", None): bool(getattr(p, "is_visible", False)) for p in iterable}
            if menu_key in visible and not visible[menu_key]:
                abort(403)

            return view_func(*args, **kwargs)

        return wrapper

    return decorator