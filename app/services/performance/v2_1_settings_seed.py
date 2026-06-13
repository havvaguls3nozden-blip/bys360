# -*- coding: utf-8 -*-
from __future__ import annotations


import logging

"""BYS360 Performans V2.1.1 varsayılan ayar seed servisi."""

from typing import Any

from app.extensions import db
from app.models import ModuleSetting, SettingsChangeLog
from app.services.performance.v2_1_rule_engine import DEFAULT_SETTINGS, MODULE_KEY, RULE_VERSION
logger = logging.getLogger(__name__)


def seed_performance_v2_1_1_settings(actor_user_id: int | None = None, *, overwrite: bool = False) -> dict[str, Any]:
    created = 0
    updated = 0
    unchanged = 0
    details: list[dict[str, Any]] = []

    for setting_key, meta in DEFAULT_SETTINGS.items():
        row = ModuleSetting.query.filter_by(module_key=MODULE_KEY, setting_key=setting_key).first()
        if row is None:
            row = ModuleSetting(
                module_key=MODULE_KEY,
                setting_key=setting_key,
                label=str(meta.get("label") or setting_key),
                value_text=str(meta.get("value_text") or ""),
                value_type=str(meta.get("value_type") or "string"),
                description=str(meta.get("description") or ""),
                is_active=True,
                updated_by_user_id=actor_user_id,
            )
            db.session.add(row)
            created += 1
            action = "created"
        else:
            changed = False
            for attr, source_key in (("label", "label"), ("value_type", "value_type"), ("description", "description")):
                new_value = str(meta.get(source_key) or "")
                if getattr(row, attr) != new_value:
                    setattr(row, attr, new_value)
                    changed = True
            if overwrite and row.value_text != str(meta.get("value_text") or ""):
                row.value_text = str(meta.get("value_text") or "")
                changed = True
            if not row.is_active:
                row.is_active = True
                changed = True
            if changed:
                row.updated_by_user_id = actor_user_id
                updated += 1
                action = "updated"
            else:
                unchanged += 1
                action = "unchanged"
        details.append({"setting_key": setting_key, "action": action})

    try:
        db.session.add(SettingsChangeLog(
            actor_user_id=actor_user_id,
            change_scope="performance_v2_1_1_settings_seed",
            action_type="seed_defaults",
            summary="BYS360 Performans V2.1.1 kural motoru varsayılan ayarları işlendi.",
            previous_state_json=None,
            new_state_json=RULE_VERSION,
        ))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        # SettingsChangeLog modeli bazı eski ortamlarda farklı kolonlarla gelebilir;
        # seed işlemi log yüzünden kırılmamalı.
        pass

    db.session.commit()
    return {"created": created, "updated": updated, "unchanged": unchanged, "details": details, "rule_version": RULE_VERSION}


def update_performance_v2_1_1_settings(payload: dict[str, Any], actor_user_id: int | None = None) -> dict[str, Any]:
    changed = 0
    rejected: list[str] = []
    for setting_key, meta in DEFAULT_SETTINGS.items():
        if setting_key not in payload:
            continue
        raw = payload.get(setting_key)
        row = ModuleSetting.query.filter_by(module_key=MODULE_KEY, setting_key=setting_key).first()
        if row is None:
            row = ModuleSetting(
                module_key=MODULE_KEY,
                setting_key=setting_key,
                label=str(meta.get("label") or setting_key),
                value_type=str(meta.get("value_type") or "string"),
                description=str(meta.get("description") or ""),
                is_active=True,
            )
            db.session.add(row)
        value_type = str(meta.get("value_type") or "string")
        value_text = _normalize_value(raw, value_type)
        if value_text is None:
            rejected.append(setting_key)
            continue
        if row.value_text != value_text:
            row.value_text = value_text
            row.updated_by_user_id = actor_user_id
            changed += 1
    try:
        db.session.add(SettingsChangeLog(
            actor_user_id=actor_user_id,
            change_scope="performance_v2_1_1_settings",
            action_type="update",
            summary=f"BYS360 Performans V2.1.1 ayarları güncellendi. Değişen: {changed}",
            previous_state_json=None,
            new_state_json=str(payload),
        ))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        pass
    db.session.commit()
    return {"changed": changed, "rejected": rejected}


def _normalize_value(raw: Any, value_type: str) -> str | None:
    if value_type == "bool":
        text = str(raw or "").strip().lower()
        if text in {"1", "true", "on", "yes", "evet", "aktif", "active", "açık", "acik"}:
            return "true"
        if text in {"0", "false", "off", "no", "hayir", "hayır", "pasif", "inactive", "kapalı", "kapali"}:
            return "false"
        return None
    if value_type == "float":
        try:
            return str(float(str(raw).replace(",", ".")))
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            return None
    return str(raw or "").strip()
