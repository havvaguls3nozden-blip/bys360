from __future__ import annotations

from datetime import datetime, timezone
from statistics import mean
from typing import Any

from flask import current_app
from sqlalchemy.exc import IntegrityError

# BYS360 V1E: emergency runtime recovery for the Phase2Y wildcard-import regression.
# This deliberately restores the shared mobile contract first; explicit imports can be
# reintroduced later only after a per-file F821 gate and smoke test.
from app.api.mobile.shared import *  # noqa: F401,F403

@mobile_api_bp.post("/auth/login")
def mobile_login():
    from app.api.mobile.services.auth_service import delegate_mobile_login
    return delegate_mobile_login(_bys360_legacy_mobile_login)

def _bys360_legacy_mobile_login():
    return mobile_login_response(_issue_token, _issue_refresh_token, _full_name)


@mobile_api_bp.post("/auth/refresh")
def mobile_refresh():
    from app.api.mobile.services.auth_service import delegate_mobile_refresh
    return delegate_mobile_refresh(_bys360_legacy_mobile_refresh)

def _bys360_legacy_mobile_refresh():
    data = request.get_json(silent=True) or {}
    refresh_token = data.get("refresh_token") or data.get("refreshToken")
    return mobile_refresh_response(refresh_token, _load_refresh_token_user, _issue_token, _issue_refresh_token, _full_name)


@mobile_api_bp.get("/me")
@require_mobile_user
def mobile_me(user: User):
    from app.api.mobile.services.auth_service import delegate_mobile_me
    return delegate_mobile_me(_bys360_legacy_mobile_me, user)

def _bys360_legacy_mobile_me(user: User):
    return mobile_me_response(user, _module_payload, _metric, _item, _full_name)

