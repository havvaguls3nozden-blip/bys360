from __future__ import annotations

import ast
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from app.services import corporate_information_center
from app.services.cic import (
    facade,
    mail_service,
    query_service,
    scheduler_service,
)

ROOT = Path(__file__).resolve().parents[2]
MAIL_FUNCTIONS = {
    "_cic_phase5_mail_health",
    "_cic_phase6_missing_email_count",
    "_cic_v11_bool",
    "_cic_v11_clean_header",
    "_cic_v11_get_setting_value",
    "_cic_v11_mail_settings",
    "_cic_v11_normalize_email",
    "_cic_v11_send_email_direct",
    "_recipients_for_task",
    "_recipients_for_task_base",
    "_send_task_base",
    "get_recipients",
    "send_task",
}
SCHEDULER_FUNCTIONS = {
    "_run_due_tasks_base",
    "get_auto_scheduler_config",
    "run_due_tasks",
    "set_auto_scheduler_config",
}


def _definitions(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_mail_scheduler_bridges_are_deleted_and_ownership_is_canonical() -> None:
    assert not (ROOT / "app/services/cic/mail_scheduler_service.py").exists()
    assert not (ROOT / "app/services/cic/send_context.py").exists()
    assert not (ROOT / "app/services/cic/run_context.py").exists()
    assert _definitions(ROOT / "app/services/cic/mail_service.py") >= MAIL_FUNCTIONS
    assert _definitions(ROOT / "app/services/cic/scheduler_service.py") >= SCHEDULER_FUNCTIONS

    for path in (
        ROOT / "app/services/cic/mail_service.py",
        ROOT / "app/services/cic/scheduler_service.py",
    ):
        source = path.read_text(encoding="utf-8")
        assert "corporate_information_center as _legacy" not in source
        assert "_legacy." not in source
        assert "mail_scheduler_service" not in source
        assert "send_context" not in source
        assert "run_context" not in source


def test_public_and_compatibility_entry_points_use_canonical_services() -> None:
    assert facade.send_task is mail_service.send_task
    assert facade.get_recipients is mail_service.get_recipients
    assert facade.run_due_tasks is scheduler_service.run_due_tasks
    assert (
        facade.get_auto_scheduler_config
        is scheduler_service.get_auto_scheduler_config
    )
    assert (
        facade.set_auto_scheduler_config
        is scheduler_service.set_auto_scheduler_config
    )
    assert corporate_information_center.send_task is mail_service.send_task
    assert (
        corporate_information_center.run_due_tasks
        is scheduler_service.run_due_tasks
    )


def test_mail_header_email_and_boolean_contract() -> None:
    assert mail_service._cic_v11_clean_header(" A\r\nB ") == "A  B"
    assert mail_service._cic_v11_normalize_email(" a@example.test; ") == "a@example.test"
    assert mail_service._cic_v11_normalize_email("bad address") == ""
    assert mail_service._cic_v11_bool("tls") is True
    assert mail_service._cic_v11_bool("off", True) is False
    assert mail_service._cic_v11_bool("", True) is True


def test_mail_settings_preserve_config_setting_and_alias_precedence(monkeypatch) -> None:
    monkeypatch.setattr(
        mail_service,
        "_app_config",
        lambda: {"MAIL_SERVER": "smtp.config.test", "MAIL_PORT": "2525"},
    )
    values = {
        "MAIL_DEFAULT_SENDER": "sender@example.test",
        "MAIL_USE_TLS": "true",
        "MAIL_SUPPRESS_SEND": "false",
    }
    monkeypatch.setattr(
        mail_service,
        "get_setting",
        lambda key, default="": values.get(key, default),
    )

    settings = mail_service._cic_v11_mail_settings()

    assert settings["server"] == "smtp.config.test"
    assert settings["port"] == 2525
    assert settings["sender"] == "sender@example.test"
    assert settings["use_tls"] is True
    assert settings["suppress_send"] is False


def test_direct_mail_respects_suppression_and_validation(monkeypatch) -> None:
    monkeypatch.setattr(
        mail_service,
        "_cic_v11_mail_settings",
        lambda: {
            "server": "smtp.test",
            "port": 587,
            "username": "",
            "password": "",
            "sender": "sender@example.test",
            "use_tls": True,
            "use_ssl": False,
            "suppress_send": True,
        },
    )
    assert mail_service._cic_v11_send_email_direct(
        "user@example.test", "Subject", "Body"
    )[0] is True

    monkeypatch.setattr(
        mail_service,
        "_cic_v11_mail_settings",
        lambda: {
            "server": "",
            "port": 587,
            "username": "",
            "password": "",
            "sender": "sender@example.test",
            "use_tls": True,
            "use_ssl": False,
            "suppress_send": False,
        },
    )
    ok, message = mail_service._cic_v11_send_email_direct(
        "user@example.test", "Subject", "Body"
    )
    assert ok is False
    assert "MAIL_SERVER" in message


def test_recipient_resolution_preserves_manual_and_all_active_modes(
    monkeypatch,
) -> None:
    monkeypatch.setattr(query_service, "_users_by_ids", lambda ids: list(ids))
    monkeypatch.setattr(query_service, "_active_staff_users", lambda: [7, 8])
    monkeypatch.setattr(
        mail_service,
        "get_config",
        lambda: {
            "manager_recipient_ids": [1, 2],
            "staff_recipient_ids": [3],
            "staff_recipient_mode": "manual",
        },
    )
    manual = mail_service.get_recipients()
    assert manual == {"managers": [1, 2], "staff": [3], "staff_mode": "manual"}

    monkeypatch.setattr(
        mail_service,
        "get_config",
        lambda: {
            "manager_recipient_ids": [1],
            "staff_recipient_ids": [3],
            "staff_recipient_mode": "all_active",
        },
    )
    all_active = mail_service.get_recipients()
    assert all_active["staff"] == [7, 8]


def test_send_task_dry_run_preserves_result_and_persistence_contract(
    monkeypatch,
) -> None:
    user = SimpleNamespace(id=5, email="user@example.test")
    settings: list[tuple[str, str, dict[str, Any]]] = []
    logs: list[dict[str, Any]] = []
    commits: list[str] = []

    monkeypatch.setattr(mail_service, "ensure_defaults", lambda **_kwargs: None)
    monkeypatch.setattr(
        mail_service,
        "get_config",
        lambda: {
            "tasks": {
                "staff_morning": {
                    "enabled": True,
                    "last_status": "",
                    "last_run_at": "",
                }
            }
        },
    )
    monkeypatch.setattr(
        mail_service,
        "_recipients_for_task",
        lambda _task_key, _override=None: [user],
    )
    monkeypatch.setattr(
        mail_service._template_service,
        "get_template",
        lambda _task_key: {"subject": "Hello", "body": "Body"},
    )
    monkeypatch.setattr(
        mail_service._template_service,
        "_render_template_text",
        lambda text, _user, _task_key: text,
    )
    monkeypatch.setattr(
        mail_service,
        "_cic_v11_mail_settings",
        lambda: {"server": "smtp.test", "port": 587, "sender": "sender@test"},
    )
    monkeypatch.setattr(
        mail_service,
        "set_setting",
        lambda key, value, **kwargs: settings.append((key, value, kwargs)),
    )
    monkeypatch.setattr(
        mail_service,
        "create_mail_log",
        lambda **kwargs: logs.append(kwargs),
    )
    monkeypatch.setattr(
        mail_service,
        "db",
        SimpleNamespace(
            session=SimpleNamespace(
                commit=lambda: commits.append("commit"),
                rollback=lambda: commits.append("rollback"),
            )
        ),
    )

    result = mail_service.send_task("staff_morning", dry_run=True, actor_user_id=9)

    assert result["ok"] is True
    assert result["dry_run"] is True
    assert result["recipient_count"] == 1
    assert result["success_count"] == 1
    assert result["fail_count"] == 0
    assert result["recipients"] == ["user@example.test"]
    assert len(settings) == 3
    assert logs[0]["is_success"] is True
    assert commits == ["commit"]


def test_send_task_adds_celebration_notifications_only_for_real_send(
    monkeypatch,
) -> None:
    from app.services.cic import cic_context

    user = SimpleNamespace(id=1, email="a@example.test")
    monkeypatch.setattr(mail_service, "_recipients_for_task", lambda *_a, **_k: [user])
    monkeypatch.setattr(
        mail_service,
        "_send_task_base",
        lambda *args, **kwargs: {"ok": True, "task_key": args[0]},
    )
    monkeypatch.setattr(
        cic_context,
        "_cic_v40_create_system_notifications",
        lambda *_a, **_k: 2,
    )

    dry = mail_service.send_task("staff_birthday", dry_run=True)
    real = mail_service.send_task("staff_birthday", dry_run=False)

    assert "system_notification_count" not in dry
    assert real["system_notification_count"] == 2


def test_scheduler_config_read_and_write_contract(monkeypatch) -> None:
    values = {
        "corporate_information_center.auto_scheduler_enabled": "true",
        "corporate_information_center.auto_scheduler_weekdays_only": "false",
        "corporate_information_center.auto_scheduler_late_window_minutes": "999",
    }
    monkeypatch.setattr(
        scheduler_service,
        "get_setting",
        lambda key, default="": values.get(key, default),
    )
    cfg = scheduler_service.get_auto_scheduler_config()
    assert cfg["enabled"] is True
    assert cfg["weekdays_only"] is False
    assert cfg["late_window_minutes"] == 120

    writes: list[tuple[str, str]] = []
    monkeypatch.setattr(
        scheduler_service,
        "set_setting",
        lambda key, value, **_kwargs: writes.append((key, value)),
    )
    monkeypatch.setattr(
        scheduler_service,
        "db",
        SimpleNamespace(
            session=SimpleNamespace(commit=lambda: None, rollback=lambda: None)
        ),
    )
    scheduler_service.set_auto_scheduler_config(
        {
            "auto_scheduler_enabled": "on",
            "auto_scheduler_weekdays_only": "on",
            "auto_scheduler_late_window_minutes": "0",
        }
    )
    assert [value for _key, value in writes] == ["true", "true", "1"]


def test_scheduler_disabled_weekend_and_due_run_paths(monkeypatch) -> None:
    now = datetime(2026, 7, 20, 8, 0)
    monkeypatch.setattr(scheduler_service, "ensure_defaults", lambda **_kwargs: None)
    monkeypatch.setattr(scheduler_service, "_cic_weekday_name_tr", lambda _now: "Pazartesi")
    monkeypatch.setattr(scheduler_service, "_cic_is_weekend", lambda _now: False)
    monkeypatch.setattr(scheduler_service, "get_setting", lambda *_a, **_k: "")

    monkeypatch.setattr(
        scheduler_service,
        "get_auto_scheduler_config",
        lambda: {"enabled": False, "weekdays_only": True, "late_window_minutes": 20},
    )
    disabled = scheduler_service._run_due_tasks_base(now=now)
    assert disabled["scheduler_enabled"] is False

    monkeypatch.setattr(
        scheduler_service,
        "get_auto_scheduler_config",
        lambda: {"enabled": True, "weekdays_only": True, "late_window_minutes": 20},
    )
    monkeypatch.setattr(scheduler_service, "_cic_is_weekend", lambda _now: True)
    weekend = scheduler_service._run_due_tasks_base(now=now)
    assert weekend["weekend_blocked"] is True

    monkeypatch.setattr(scheduler_service, "_cic_is_weekend", lambda _now: False)
    tasks = {
        key: {"enabled": key == "staff_morning", "hour": 8, "minute": 0}
        for key in scheduler_service.TASK_DEFINITIONS
    }
    monkeypatch.setattr(scheduler_service, "get_config", lambda: {"tasks": tasks})
    monkeypatch.setattr(
        scheduler_service,
        "send_task",
        lambda task_key, **_kwargs: {"ok": True, "task_key": task_key},
    )
    monkeypatch.setattr(scheduler_service, "set_setting", lambda *_a, **_k: None)
    monkeypatch.setattr(
        scheduler_service,
        "db",
        SimpleNamespace(
            session=SimpleNamespace(commit=lambda: None, rollback=lambda: None)
        ),
    )
    due = scheduler_service._run_due_tasks_base(now=now)
    assert due["ran_any"] is True
    assert [row["task_key"] for row in due["ran"]] == ["staff_morning"]


def test_weekend_exception_is_owned_by_scheduler_and_celebration_service(
    monkeypatch,
) -> None:
    from app.services.cic import celebration_service

    monkeypatch.setattr(
        scheduler_service,
        "_run_due_tasks_base",
        lambda **_kwargs: {
            "weekend_blocked": True,
            "results": [],
            "ran": [],
            "ran_any": False,
        },
    )
    monkeypatch.setattr(
        celebration_service,
        "_cic_v40_run_weekend_celebrations",
        lambda *_a, **_k: [{"task_key": "staff_birthday", "action": "ran"}],
    )

    result = scheduler_service.run_due_tasks(
        now=datetime(2026, 7, 18, 9, 0),
        dry_run=True,
    )

    assert result["weekend_blocked"] is False
    assert result["ran_any"] is True
    assert result["ran"][0]["task_key"] == "staff_birthday"
