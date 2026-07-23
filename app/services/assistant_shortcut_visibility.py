"""BYS360 Sanal Asistan kısa yol görünürlüğü.

Bu dosya yalnızca asistan kısa yollarının rol matrisine göre görünürlüğünü sağlar.
Login, parola, CAPTCHA, auth, config ve DB bağlantı ayarlarına dokunmaz.
"""
from __future__ import annotations

import json
import re
import unicodedata
from typing import Any

from sqlalchemy import bindparam, text

try:
    from flask_login import current_user
except Exception:  # pragma: no cover
    __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/assistant_shortcut_visibility.py:16")
    current_user = None

ASSISTANT_SHORTCUTS: dict[str, dict[str, Any]] = {
    "assistant_center": {"title": "Sanal Asistan Merkezi", "labels": ["Sanal Asistan Merkezi", "Asistan Merkezi", "Sanal Asistan"]},
    "assistant_my_reminders": {"title": "Bana Ait Hatırlatmalar", "labels": ["Bana Ait Hatırlatmalar", "Hatırlatmalarım", "Hatırlatmalar"]},
    "assistant_scheduled_jobs": {"title": "Zamanlanmış İş Planlama", "labels": ["Zamanlanmış İş Planlama", "Zamanlanmış İşler", "Zamanlanmis Isler"]},
    "assistant_report_create": {"title": "Rapor Oluşturma", "labels": ["Rapor Oluşturma", "Rapor Oluştur", "Rapor Olustur"]},
    "assistant_report_share": {"title": "Rapor Paylaşımı", "labels": ["Rapor Paylaşımı", "Rapor Paylaş", "Rapor Paylas"]},
    "assistant_ai_summary": {"title": "AI Özet ve Karar Notu", "labels": ["AI Özet ve Karar Notu", "AI Özet", "AI Ozet", "Karar Notu"]},
    "assistant_process_alerts": {"title": "Süreç Hatırlatma ve Uyarılar", "labels": ["Süreç Hatırlatma ve Uyarılar", "Süreç Uyarıları", "Surec Uyarilari"]},
    "assistant_logs": {"title": "Asistan İşlem Logları", "labels": ["Asistan İşlem Logları", "Asistan Logları", "Asistan Loglari"]},
    "assistant_settings": {"title": "Asistan Ayarları", "labels": ["Asistan Ayarları", "Sanal Asistan Ayarları", "Asistan Ayarlari"]},
}

_DEFAULT_TRUE = {key: True for key in ASSISTANT_SHORTCUTS}
_DEFAULT_FALSE = {key: False for key in ASSISTANT_SHORTCUTS}
DEFAULT_ROLE_POLICY: dict[str, dict[str, bool]] = {
    "admin": _DEFAULT_TRUE,
    "sistem_yoneticisi": _DEFAULT_TRUE,
    "baskan": _DEFAULT_TRUE,
    "baskan_yardimcisi": _DEFAULT_TRUE,
    "grup_baskani": _DEFAULT_TRUE,
    "mali_musavir": _DEFAULT_TRUE,
    "koordinator": _DEFAULT_TRUE,
    "birim_sorumlusu": _DEFAULT_TRUE,
    "personel": {
        "assistant_center": True,
        "assistant_my_reminders": True,
        "assistant_scheduled_jobs": False,
        "assistant_report_create": False,
        "assistant_report_share": False,
        "assistant_ai_summary": False,
        "assistant_process_alerts": True,
        "assistant_logs": False,
        "assistant_settings": False,
    },
    "kullanici": {
        "assistant_center": True,
        "assistant_my_reminders": True,
        "assistant_scheduled_jobs": False,
        "assistant_report_create": False,
        "assistant_report_share": False,
        "assistant_ai_summary": False,
        "assistant_process_alerts": True,
        "assistant_logs": False,
        "assistant_settings": False,
    },
    "": _DEFAULT_FALSE,
    "none": _DEFAULT_FALSE,
}

def _normalize(value: Any) -> str:
    raw = "" if value is None else str(value)
    raw = raw.strip().lower().replace("ı", "i").replace("İ", "i")
    raw = unicodedata.normalize("NFKD", raw)
    raw = "".join(ch for ch in raw if not unicodedata.combining(ch))
    raw = raw.replace(" ", "_").replace("-", "_").replace("/", "_")
    return re.sub(r"_+", "_", raw).strip("_")

def _current_role() -> str:
    user = current_user
    if not user or not getattr(user, "is_authenticated", False):
        return ""
    for attr in ("role", "role_label", "unvan"):
        val = getattr(user, attr, None)
        if val:
            return _normalize(val)
    return ""

def _truthy(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "evet", "yes", "on", "açık", "acik", "enabled"}:
        return True
    if text in {"0", "false", "hayır", "hayir", "no", "off", "kapalı", "kapali", "disabled"}:
        return False
    return None

def _db_session():
    try:
        from app.extensions import db
        return db.session
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/assistant_shortcut_visibility.py:104")
        return None

def _candidate_keys(key: str) -> set[str]:
    k = _normalize(key)
    candidates = {k, f"assistant.{k}", f"assistant_{k}", f"asistan.{k}", f"asistan_{k}", f"sanal_asistan.{k}", f"sanal_asistan_{k}", k.replace("assistant_", ""), k.replace("assistant_", "asistan_"), k.replace("assistant_", "sanal_asistan_")}
    return {_normalize(x) for x in candidates if x}

def _table_columns(session, table_name: str) -> set[str]:
    """Return table columns with SQLAlchemy inspector.

    This avoids SQLAlchemy 2.x raw SQL errors and avoids PostgreSQL-only
    information_schema lookups during local SQLite smoke tests.
    """
    if session is None or not table_name:
        return set()
    try:
        bind = None
        try:
            bind = session.get_bind()
        except Exception:
            bind = getattr(session, "bind", None)
        if bind is None:
            return set()

        from sqlalchemy import inspect as _sa_inspect

        inspector = _sa_inspect(bind)
        try:
            if not inspector.has_table(table_name):
                return set()
        except Exception:
            # Some dialects/permissions may not support has_table reliably.
            pass
        return {str(col.get("name")) for col in inspector.get_columns(table_name) if col.get("name")}
    except Exception:
        # Column lookup is optional for shortcut visibility. Do not log noisy
        # tracebacks on login; absence of a table simply disables DB override.
        return set()

def _query_user_menu_permission(session, key: str) -> bool | None:
    user = current_user
    user_id = getattr(user, "id", None)
    if not user_id:
        return None
    cols = _table_columns(session, "user_menu_permissions")
    if not cols:
        return None
    user_cols = [c for c in ("user_id", "personnel_id", "account_id") if c in cols]
    key_cols = [c for c in ("menu_key", "feature_key", "permission_key", "module_key", "key") if c in cols]
    value_cols = [c for c in ("is_visible", "visible", "enabled", "is_enabled", "allowed", "value") if c in cols]
    if not user_cols or not key_cols or not value_cols:
        return None
    try:
        stmt = text(
            f"select {value_cols[0]} from user_menu_permissions "
            f"where {user_cols[0]} = :uid and lower(cast({key_cols[0]} as text)) in :keys "
            "order by id desc limit 1"
        ).bindparams(bindparam("keys", expanding=True))
        row = session.execute(stmt, {"uid": user_id, "keys": list(_candidate_keys(key))}).fetchone()
        return _truthy(row[0]) if row else None
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/assistant_shortcut_visibility.py:138")
        return None

def _query_role_menu_default(session, role: str, key: str) -> bool | None:
    cols = _table_columns(session, "role_menu_defaults")
    if not cols:
        return None
    role_cols = [c for c in ("role", "role_key", "role_name", "role_label") if c in cols]
    key_cols = [c for c in ("menu_key", "feature_key", "permission_key", "module_key", "key") if c in cols]
    value_cols = [c for c in ("is_visible", "visible", "enabled", "is_enabled", "allowed", "value") if c in cols]
    if not role_cols or not key_cols or not value_cols:
        return None
    try:
        stmt = text(
            f"select {value_cols[0]} from role_menu_defaults "
            f"where lower(cast({role_cols[0]} as text)) in :roles "
            f"and lower(cast({key_cols[0]} as text)) in :keys order by id desc limit 1"
        ).bindparams(bindparam("roles", expanding=True), bindparam("keys", expanding=True))
        row = session.execute(
            stmt,
            {"roles": list({role, role.replace("_", " ")}), "keys": list(_candidate_keys(key))},
        ).fetchone()
        return _truthy(row[0]) if row else None
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/assistant_shortcut_visibility.py:156")
        return None

def _parse_json(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    if value is None:
        return None
    try:
        return json.loads(str(value).strip())
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/assistant_shortcut_visibility.py:166")
        return None

def _lookup_nested_policy(data: Any, role: str, key: str) -> bool | None:
    if data is None:
        return None
    keys = _candidate_keys(key)
    roles = {role, role.replace("_", " ")}
    if isinstance(data, dict):
        for fkey in keys:
            val = data.get(fkey)
            if isinstance(val, dict):
                for r in roles:
                    t = _truthy(val.get(r))
                    if t is not None:
                        return t
            else:
                t = _truthy(val)
                if t is not None:
                    return t
        for r in roles:
            val = data.get(r)
            if isinstance(val, dict):
                for fkey in keys:
                    t = _truthy(val.get(fkey))
                    if t is not None:
                        return t
        for val in data.values():
            found = _lookup_nested_policy(val, role, key)
            if found is not None:
                return found
    if isinstance(data, list):
        for item in data:
            found = _lookup_nested_policy(item, role, key)
            if found is not None:
                return found
    return None

def _query_json_settings(session, role: str, key: str) -> bool | None:
    for table in ("module_settings", "system_settings"):
        cols = _table_columns(session, table)
        if not cols:
            continue
        key_cols = [c for c in ("key", "setting_key", "name", "code") if c in cols]
        value_cols = [c for c in ("value", "setting_value", "json_value", "data", "payload") if c in cols]
        if not key_cols or not value_cols:
            continue
        try:
            rows = session.execute(
                text(
                    f"select {key_cols[0]}, {value_cols[0]} from {table} "
                    f"where lower(cast({key_cols[0]} as text)) like '%assistant%' "
                    f"or lower(cast({key_cols[0]} as text)) like '%asistan%' "
                    f"or lower(cast({key_cols[0]} as text)) like '%role_matrix%' "
                    f"or lower(cast({key_cols[0]} as text)) like '%rol_matrisi%'"
                )
            ).fetchall()
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/assistant_shortcut_visibility.py:217)")
            continue
        for _, raw in rows:
            found = _lookup_nested_policy(_parse_json(raw), role, key)
            if found is not None:
                return found
    return None

def assistant_shortcut_visible(feature_key: str) -> bool:
    role = _current_role()
    key = _normalize(feature_key)
    if key != "assistant_center" and assistant_shortcut_visible("assistant_center") is False:
        return False
    session = _db_session()
    if session is not None:
        user_value = _query_user_menu_permission(session, key)
        if user_value is not None:
            return bool(user_value)
        json_value = _query_json_settings(session, role, key)
        if json_value is not None:
            return bool(json_value)
        role_value = _query_role_menu_default(session, role, key)
        if role_value is not None:
            return bool(role_value)
    policy = DEFAULT_ROLE_POLICY.get(role)
    if policy and key in policy:
        return bool(policy[key])
    return any(x in role for x in ("admin", "yonetici", "yönetici", "baskan", "başkan", "koordinator", "koordinat", "grup"))

def assistant_shortcut_visibility_map() -> dict[str, bool]:
    return {key: assistant_shortcut_visible(key) for key in ASSISTANT_SHORTCUTS}

def assistant_shortcut_label_map() -> dict[str, list[str]]:
    return {key: list(value.get("labels", [])) for key, value in ASSISTANT_SHORTCUTS.items()}

def register_assistant_shortcut_visibility_context(app):
    """Asistan kısayol görünürlük helper'larını idempotent ve güvenli bağlar."""
    if getattr(app, "_bys360_assistant_shortcut_visibility_context_registered", False):
        return app

    @app.context_processor
    def _assistant_shortcut_visibility_context():
        # BYS360_V59_4_ASSISTANT_SHORTCUT_CONTEXT_KEYS_SAFE
        # Bu context processor şablona her zaman aynı anahtarları verir.
        # Servis/DB tarafı hata verse bile base.html UndefinedError üretmez.
        try:
            visibility = assistant_shortcut_visibility_map()
            if not isinstance(visibility, dict):
                visibility = {}
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/assistant_shortcut_visibility.py:269")
            visibility = {}  # BYS360_V59_4_ASSISTANT_SHORTCUT_EXCEPTION_FALLBACK_SAFE

        try:
            labels = assistant_shortcut_label_map()
            if not isinstance(labels, dict):
                labels = {}
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/assistant_shortcut_visibility.py:276")
            labels = {}

        def _safe_assistant_shortcut_visible(key):
            try:
                return bool(assistant_shortcut_visible(key))
            except Exception:
                __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/assistant_shortcut_visibility.py:282")
                return False

        def _safe_assistant_shortcut_visibility_map():
            try:
                value = assistant_shortcut_visibility_map()
                return value if isinstance(value, dict) else {}
            except Exception:
                __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/assistant_shortcut_visibility.py:289")
                return {}

        def _safe_assistant_shortcut_label_map():
            try:
                value = assistant_shortcut_label_map()
                return value if isinstance(value, dict) else {}
            except Exception:
                __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/assistant_shortcut_visibility.py:296")
                return {}

        return {
            "assistant_shortcut_visible": _safe_assistant_shortcut_visible,
            "assistant_shortcut_visibility_map": _safe_assistant_shortcut_visibility_map,
            "assistant_shortcut_label_map": _safe_assistant_shortcut_label_map,
            "assistant_shortcut_visibility_json": visibility,
            "assistant_shortcut_label_json": labels,
        }
    app._bys360_assistant_shortcut_visibility_context_registered = True
    return app
