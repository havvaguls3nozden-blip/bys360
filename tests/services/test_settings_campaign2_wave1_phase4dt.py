from __future__ import annotations

import builtins
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from typing import Any


def _find_root() -> Path:
    for parent in (
        Path(__file__).resolve().parents
    ):
        if (
            parent
            / "app"
            / "services"
            / "settings"
            / "effective_menu_parts"
            / "block_context.py"
        ).exists():
            return parent

    raise RuntimeError(
        "Project root not found."
    )


ROOT = _find_root()


def _load_module(
    name: str,
    relative: str,
):
    path = ROOT / relative

    spec = (
        importlib.util
        .spec_from_file_location(
            name,
            path,
        )
    )

    if (
        spec is None
        or spec.loader is None
    ):
        raise RuntimeError(
            f"Module could not load: "
            f"{relative}"
        )

    module = (
        importlib.util
        .module_from_spec(spec)
    )

    spec.loader.exec_module(
        module
    )

    return module


block = _load_module(
    "phase4ds_block_context",
    (
        "app/services/settings/"
        "effective_menu_parts/"
        "block_context.py"
    ),
)

wrapper = _load_module(
    "phase4ds_build_wrapper_context",
    (
        "app/services/settings/"
        "effective_menu_parts/"
        "build_wrapper_context.py"
    ),
)


POLICY_NAMES = [
    "PHASE3_PERFORMANCE_MENU_POLICY",
    "PHASE3_2_PERFORMANCE_MENU_POLICY",
    "PERFORMANCE_MENU_POLICY",
    "ROLE_MENU_POLICY",
    "ROLE_MATRIX_POLICY",
]


class BadUpdate:
    def update(self, value):
        raise RuntimeError(
            "update"
        )


class BadAdd:
    def add(self, value):
        raise RuntimeError(
            "add"
        )


class BadPolicy(dict):
    def setdefault(
        self,
        key,
        default=None,
    ):
        raise RuntimeError(
            "setdefault"
        )


class BadGet(dict):
    def get(
        self,
        key,
        default=None,
    ):
        raise RuntimeError(
            "get"
        )


class Log:
    def __init__(self):
        self.messages = []

    def exception(
        self,
        message,
    ):
        self.messages.append(
            message
        )


def _mixed_policies():
    return {
        POLICY_NAMES[0]: {},
        POLICY_NAMES[1]: {
            "x": [],
        },
        POLICY_NAMES[2]: "skip",
        POLICY_NAMES[3]: {},
        POLICY_NAMES[4]: {
            "x": {
                "old",
            },
        },
    }


def test_block_daily_weather_success_and_error():
    # Deliberately heterogeneous per key (dict / str "skip" / None / set /
    # list) to exercise the production function's defensive handling of
    # malformed policy entries -- Any is the accurate type of this
    # container, not a loosened one.
    policies: dict[str, Any] = {
        POLICY_NAMES[0]: {
            "executive_summary": {
                "existing",
            },
        },
        POLICY_NAMES[1]: {
            "executive_summary": [
                "existing",
            ],
        },
        POLICY_NAMES[2]: {},
        POLICY_NAMES[3]: "skip",
        POLICY_NAMES[4]: None,
        "PHASE3_2_MANAGER_VISIBLE_KEYS": set(),
        "PHASE3_2_GENERAL_VISIBLE_KEYS": [],
        "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS": set(),
        "PERFORMANCE_ROLE_MATRIX_KEYS": set(),
    }

    block.apply_daily_weather_policy_block(
        policies,
        logging=Log(),
    )

    expected_roles = {
        "admin",
        "super_admin",
        "system_admin",
        "sistem_yoneticisi",
    }

    assert (
        policies[
            POLICY_NAMES[0]
        ]["daily_weather_mail"]
        == expected_roles
    )

    assert (
        "admin"
        in policies[
            POLICY_NAMES[0]
        ]["executive_summary"]
    )

    assert (
        "admin"
        in policies[
            POLICY_NAMES[1]
        ]["executive_summary"]
    )

    assert (
        policies[
            POLICY_NAMES[2]
        ]["executive_summary"]
        >= {
            "admin",
        }
    )

    assert (
        "daily_weather_mail"
        in policies[
            "PHASE3_2_MANAGER_VISIBLE_KEYS"
        ]
    )

    extra = {
        POLICY_NAMES[0]: {
            "executive_summary": (
                "skip",
            ),
        },
        POLICY_NAMES[1]: {
            "executive_summary": [
                "admin",
            ],
        },
    }

    block.apply_daily_weather_policy_block(
        extra,
        logging=Log(),
    )

    block.apply_daily_weather_policy_block(
        BadGet(),
        logging=Log(),
    )


def test_block_runtime_authority_success_and_error():
    values: set[str] = set()

    block.apply_role_matrix_runtime_authority_keys_block(
        values
    )

    assert (
        "ai_agent_panel"
        in values
    )

    block.apply_role_matrix_runtime_authority_keys_block(
        BadUpdate()
    )


def test_block_policy_mutators_set_list_and_skips():
    policy = {
        "x": {
            "a",
            "b",
        },
        "y": {
            "c",
        },
    }

    values = _mixed_policies()

    block.apply_performance_role_matrix_new_tab_policy_block(
        values,
        policy,
    )

    assert (
        values[
            POLICY_NAMES[0]
        ]["x"]
        == {
            "a",
            "b",
        }
    )

    assert (
        set(
            values[
                POLICY_NAMES[1]
            ]["x"]
        )
        == {
            "a",
            "b",
        }
    )

    block.apply_performance_role_matrix_new_tab_policy_block(
        {
            POLICY_NAMES[0]: {
                "x": (
                    "skip",
                ),
            },
        },
        policy,
    )

    values = _mixed_policies()

    block.apply_process_menu_policy_block(
        values,
        [
            "x",
            "y",
        ],
        {
            "r1",
            "r2",
        },
    )

    assert (
        values[
            POLICY_NAMES[0]
        ]["x"]
        == {
            "r1",
            "r2",
        }
    )

    assert (
        set(
            values[
                POLICY_NAMES[1]
            ]["x"]
        )
        == {
            "r1",
            "r2",
        }
    )

    block.apply_process_menu_policy_block(
        {
            POLICY_NAMES[0]: {
                "x": (
                    "skip",
                ),
            },
        },
        [
            "x",
        ],
        {
            "r1",
        },
    )

    values = _mixed_policies()

    block.apply_reminders_menu_policy_block(
        values,
        "remind",
        {
            "r1",
        },
    )

    assert (
        values[
            POLICY_NAMES[0]
        ]["remind"]
        == {
            "r1",
        }
    )

    values[
        POLICY_NAMES[1]
    ]["remind"] = []

    block.apply_reminders_menu_policy_block(
        values,
        "remind",
        {
            "r1",
            "r2",
        },
    )

    assert (
        set(
            values[
                POLICY_NAMES[1]
            ]["remind"]
        )
        == {
            "r1",
            "r2",
        }
    )

    block.apply_reminders_menu_policy_block(
        {
            POLICY_NAMES[0]: {
                "remind": (
                    "skip",
                ),
            },
        },
        "remind",
        {
            "r1",
        },
    )


def test_block_period_center_success_and_errors():
    core: dict[str, set[str]] = {}
    authority: set[str] = set()

    block.apply_period_center_key_roles_block(
        core,
        authority,
        {
            "key": [
                "role",
            ],
        },
        Log(),
    )

    assert authority == {
        "key",
    }

    assert core["key"] == {
        "role",
    }

    block.apply_period_center_key_roles_block(
        {},
        BadAdd(),
        {
            "key": [
                "role",
            ],
        },
        Log(),
    )

    block.apply_period_center_key_roles_block(
        BadPolicy(),
        set(),
        {
            "key": [
                "role",
            ],
        },
        Log(),
    )


def test_block_sets_and_personnel_mutators():
    values = {
        "PHASE3_2_MANAGER_VISIBLE_KEYS": set(),
        "PHASE3_2_GENERAL_VISIBLE_KEYS": [],
        "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS": "skip",
        "PERFORMANCE_ROLE_MATRIX_KEYS": set(),
    }

    policy = {
        "x": {
            "role",
        },
        "y": {
            "role",
        },
    }

    block.apply_performance_role_matrix_new_tab_sets_block(
        values,
        policy,
    )

    assert (
        values[
            "PHASE3_2_MANAGER_VISIBLE_KEYS"
        ]
        == {
            "x",
            "y",
        }
    )

    assert (
        set(
            values[
                "PHASE3_2_GENERAL_VISIBLE_KEYS"
            ]
        )
        == {
            "x",
            "y",
        }
    )

    block.apply_performance_role_matrix_new_tab_sets_block(
        {
            "PHASE3_2_MANAGER_VISIBLE_KEYS": (
                "skip",
            ),
        },
        policy,
    )

    policies = _mixed_policies()

    policies[
        POLICY_NAMES[1]
    ]["allowed"] = []

    for item in policies.values():
        if isinstance(
            item,
            dict,
        ):
            item["obsolete"] = True

    block.apply_personel_allowed_policy_block(
        policies,
        {
            "allowed": {
                "r1",
                "r2",
            },
        },
        {
            "obsolete",
        },
    )

    assert (
        "obsolete"
        not in policies[
            POLICY_NAMES[0]
        ]
    )

    assert (
        policies[
            POLICY_NAMES[0]
        ]["allowed"]
        == {
            "r1",
            "r2",
        }
    )

    assert (
        set(
            policies[
                POLICY_NAMES[1]
            ]["allowed"]
        )
        == {
            "r1",
            "r2",
        }
    )

    block.apply_personel_allowed_policy_block(
        {
            POLICY_NAMES[0]: {
                "allowed": (
                    "skip",
                ),
            },
        },
        {
            "allowed": {
                "role",
            },
        },
        set(),
    )

    policies = _mixed_policies()

    policies[
        POLICY_NAMES[1]
    ]["new"] = []

    for item in policies.values():
        if isinstance(
            item,
            dict,
        ):
            item["old"] = True

    block.apply_personel_role_matrix_visibility_v7_block(
        policies,
        [
            "new",
        ],
        {
            "manager",
        },
        [
            "old",
        ],
    )

    assert (
        policies[
            POLICY_NAMES[0]
        ]["new"]
        == {
            "manager",
        }
    )

    assert (
        policies[
            POLICY_NAMES[1]
        ]["new"]
        == [
            "manager",
        ]
    )

    block.apply_personel_role_matrix_visibility_v7_block(
        {
            POLICY_NAMES[0]: {
                "new": (
                    "skip",
                ),
            },
        },
        [
            "new",
        ],
        {
            "manager",
        },
        [],
    )

    key_sets = {
        "PHASE3_2_MANAGER_VISIBLE_KEYS": set(),
        "PHASE3_2_GENERAL_VISIBLE_KEYS": [],
        "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS": [
            "remind",
        ],
    }

    block.apply_reminders_menu_key_sets_block(
        key_sets,
        "remind",
    )

    assert (
        key_sets[
            "PHASE3_2_MANAGER_VISIBLE_KEYS"
        ]
        == {
            "remind",
        }
    )

    assert (
        key_sets[
            "PHASE3_2_GENERAL_VISIBLE_KEYS"
        ]
        == [
            "remind",
        ]
    )

    assert (
        key_sets[
            "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS"
        ]
        == [
            "remind",
        ]
    )


def _base_visibility(
    user,
    *args,
    **kwargs,
):
    return {
        "existing": True,
    }


def _normalize_role(role):
    return str(
        role
    ).strip().lower()


def _not_removed(key):
    return False


def test_wrapper_v213c_global_and_user_paths(
    monkeypatch,
):
    key = (
        "performance_personnel_category_card"
    )

    monkeypatch.setattr(
        wrapper,
        "CORE_MENU_VISIBILITY_POLICY",
        {},
        raising=False,
    )

    monkeypatch.setattr(
        wrapper,
        "PHASE3_PERFORMANCE_MENU_POLICY",
        {
            key: [],
        },
        raising=False,
    )

    monkeypatch.setattr(
        wrapper,
        "PHASE3_2_PERFORMANCE_MENU_POLICY",
        "skip",
        raising=False,
    )

    monkeypatch.setattr(
        wrapper,
        "PERFORMANCE_MENU_POLICY",
        {},
        raising=False,
    )

    monkeypatch.setattr(
        wrapper,
        "ROLE_MENU_POLICY",
        {},
        raising=False,
    )

    monkeypatch.setattr(
        wrapper,
        "ROLE_MATRIX_POLICY",
        {
            key: (
                "skip",
            ),
        },
        raising=False,
    )

    monkeypatch.setattr(
        wrapper,
        "PHASE3_2_GENERAL_VISIBLE_KEYS",
        set(),
        raising=False,
    )

    monkeypatch.setattr(
        wrapper,
        "PERFORMANCE_ROLE_MATRIX_KEYS",
        [],
        raising=False,
    )

    monkeypatch.setattr(
        wrapper,
        "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS",
        [
            key,
        ],
        raising=False,
    )

    wrapped = (
        wrapper
        .apply_v213c_category_menu_wrapper(
            _base_visibility,
            logging=Log(),
            normalize_role_name=(
                _normalize_role
            ),
            is_removed_menu_key=(
                _not_removed
            ),
        )
    )

    result = wrapped(
        SimpleNamespace(
            role="admin",
        )
    )

    assert result[key] is True

    assert (
        result["performance_module"]
        is True
    )

    assert (
        key
        in wrapper
        .PHASE3_2_GENERAL_VISIBLE_KEYS
    )

    assert (
        key
        in wrapper
        .PERFORMANCE_ROLE_MATRIX_KEYS
    )

    removed_wrapper = (
        wrapper
        .apply_v213c_category_menu_wrapper(
            _base_visibility,
            logging=Log(),
            normalize_role_name=(
                _normalize_role
            ),
            is_removed_menu_key=(
                lambda value: True
            ),
        )
    )

    assert (
        key
        not in removed_wrapper(
            SimpleNamespace(
                role="personel",
            )
        )
    )

    assert (
        key
        not in removed_wrapper(
            SimpleNamespace(
                role="admin",
            )
        )
    )

    def bad_normalize(role):
        raise RuntimeError(
            "normalize"
        )

    fallback_wrapper = (
        wrapper
        .apply_v213c_category_menu_wrapper(
            _base_visibility,
            logging=Log(),
            normalize_role_name=(
                bad_normalize
            ),
            is_removed_menu_key=(
                _not_removed
            ),
        )
    )

    assert (
        fallback_wrapper(
            SimpleNamespace(
                role="personel",
                is_admin=True,
            )
        )[key]
        is True
    )


def test_wrapper_v213c_outer_fallback(
    monkeypatch,
):
    original_globals = (
        builtins.globals
    )

    monkeypatch.setattr(
        builtins,
        "globals",
        lambda: (
            (_ for _ in ())
            .throw(
                RuntimeError(
                    "globals"
                )
            )
        ),
    )

    class BadLog:
        def exception(
            self,
            message,
        ):
            raise RuntimeError(
                "logging"
            )

    result = (
        wrapper
        .apply_v213c_category_menu_wrapper(
            _base_visibility,
            logging=BadLog(),
            normalize_role_name=(
                _normalize_role
            ),
            is_removed_menu_key=(
                _not_removed
            ),
        )
    )

    assert (
        result
        is _base_visibility
    )

    monkeypatch.setattr(
        builtins,
        "globals",
        original_globals,
    )


def _exercise_simple_wrapper(
    factory,
    key,
):
    wrapped = factory(
        _base_visibility,
        logging=Log(),
        normalize_role_name=(
            _normalize_role
        ),
        is_removed_menu_key=(
            _not_removed
        ),
    )

    assert (
        wrapped(
            SimpleNamespace(
                role="admin",
            )
        )[key]
        is True
    )

    assert (
        key
        not in wrapped(
            SimpleNamespace(
                role="personel",
            )
        )
    )

    removed_wrapper = factory(
        _base_visibility,
        logging=Log(),
        normalize_role_name=(
            _normalize_role
        ),
        is_removed_menu_key=(
            lambda value: True
        ),
    )

    assert (
        key
        not in removed_wrapper(
            SimpleNamespace(
                role="admin",
            )
        )
    )

    def bad_normalize(role):
        raise RuntimeError(
            "normalize"
        )

    fallback_wrapper = factory(
        _base_visibility,
        logging=Log(),
        normalize_role_name=(
            bad_normalize
        ),
        is_removed_menu_key=(
            _not_removed
        ),
    )

    assert (
        fallback_wrapper(
            SimpleNamespace(
                role="admin",
            )
        )[key]
        is True
    )


def test_wrapper_v215_paths_and_removed_error():
    key = (
        "performance_category_period_scope"
    )

    _exercise_simple_wrapper(
        wrapper
        .apply_v215_category_period_scope_wrapper,
        key,
    )

    def bad_removed(value):
        raise RuntimeError(
            "removed"
        )

    wrapped = (
        wrapper
        .apply_v215_category_period_scope_wrapper(
            _base_visibility,
            logging=Log(),
            normalize_role_name=(
                _normalize_role
            ),
            is_removed_menu_key=(
                bad_removed
            ),
        )
    )

    assert (
        wrapped(
            SimpleNamespace(
                role="admin",
            )
        )[key]
        is True
    )


def test_wrapper_v216_paths_and_removed_error():
    key = (
        "performance_category_period_integration"
    )

    _exercise_simple_wrapper(
        wrapper
        .apply_v216_category_period_integration_wrapper,
        key,
    )

    def bad_removed(value):
        raise RuntimeError(
            "removed"
        )

    wrapped = (
        wrapper
        .apply_v216_category_period_integration_wrapper(
            _base_visibility,
            logging=Log(),
            normalize_role_name=(
                _normalize_role
            ),
            is_removed_menu_key=(
                bad_removed
            ),
        )
    )

    assert (
        wrapped(
            SimpleNamespace(
                role="admin",
            )
        )[key]
        is True
    )


def test_wrapper_v214_paths():
    _exercise_simple_wrapper(
        wrapper
        .apply_v214_category_scope_wrapper,
        (
            "performance_"
            "category_scope_visibility"
        ),
    )
