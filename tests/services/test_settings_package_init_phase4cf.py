from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import cast

from app.services import settings
from app.services.settings.contracts import SettingChange


def test_build_change_payload_masks_sensitive_values_and_serializes_time() -> None:
    changed_at = datetime(
        2026,
        7,
        14,
        19,
        50,
        tzinfo=UTC,
    )

    meta = {
        "source": "unit-test",
    }

    change = SimpleNamespace(
        key="api_token",
        old_value="old-token",
        new_value="new-token",
        actor_id=42,
        operation="update",
        reason="rotation",
        changed_at=changed_at,
        meta=meta,
    )

    payload = settings.build_change_payload(
        cast(SettingChange, change)
    )

    assert payload == {
        "key": "api_token",
        "old_value": "********",
        "new_value": "********",
        "actor_id": 42,
        "operation": "update",
        "reason": "rotation",
        "changed_at": changed_at.isoformat(),
        "meta": {
            "source": "unit-test",
        },
    }

    assert payload["meta"] is not meta


def test_build_change_payload_preserves_public_values_and_empty_optional_fields() -> None:
    change = SimpleNamespace(
        key="site_name",
        old_value="Old Name",
        new_value="BYS360",
        actor_id=None,
        operation="create",
        reason=None,
        changed_at=None,
        meta=None,
    )

    assert settings.build_change_payload(
        cast(SettingChange, change)
    ) == {
        "key": "site_name",
        "old_value": "Old Name",
        "new_value": "BYS360",
        "actor_id": None,
        "operation": "create",
        "reason": None,
        "changed_at": None,
        "meta": {},
    }
