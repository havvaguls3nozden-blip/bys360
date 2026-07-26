from __future__ import annotations

import importlib.util
import sys
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]
APPLY_REL = 'app/services/settings/effective_menu_parts/apply_context.py'
RUNTIME_REL = 'app/services/settings/effective_menu_parts/runtime_policy_context.py'

_SENTINEL = object()


def _package(name: str) -> ModuleType:
    mod = ModuleType(name)
    mod.__path__ = []
    return mod


@contextmanager
def _temporary_modules(mapping: dict[str, ModuleType]):
    previous: dict[str, ModuleType | object] = {name: sys.modules.get(name, _SENTINEL) for name in mapping}
    sys.modules.update(mapping)
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is _SENTINEL:
                sys.modules.pop(name, None)
            else:
                # `value` came from sys.modules.get(...) in the branch that
                # is not the `_SENTINEL` placeholder, so it is always a real
                # module here.
                assert isinstance(value, ModuleType)
                sys.modules[name] = value


def _module(name: str, **attrs) -> ModuleType:
    mod = ModuleType(name)
    for key, value in attrs.items():
        setattr(mod, key, value)
    return mod


def _dummy(*args, **kwargs):
    return None


def _load_apply():
    app = _package('app')
    services = _package('app.services')
    settings = _package('app.services.settings')
    parts = _package('app.services.settings.effective_menu_parts')

    config = _module('app.config', is_removed_menu_key=lambda key: False)
    registry = _module('app.menu_registry', flatten_menu_definitions=lambda *a, **k: [])

    class Model:
        pass
    models = _module('app.models', UserMenuPermission=Model, RoleMenuDefault=Model)
    settings_service = _module(
        'app.services.settings_service',
        build_effective_user_menu_context=_dummy,
        get_role_default_menu_keys=lambda *a, **k: set(),
    )

    def normalize(value):
        return str(value or '').strip().lower().replace('-', '_').replace(' ', '_')

    def _rollback_hook(hook: Callable[[], Any] | None = None) -> Any:
        return hook() if hook else None

    bys_attrs = {
        '_rollback': _rollback_hook,
        'normalize_role_name': normalize,
        '_load_role_matrix_state': lambda *a, **k: {},
        '_load_unit_profile_state': lambda *a, **k: {},
        '_load_user_override_state': lambda *a, **k: {},
        '_bys360_person_matrix_can_open_v1': lambda *a, **k: True,
        '_bys360_press_news_role': normalize,
    }
    names = [
        '_bys360_admin_period_reminder_is_admin_v1',
        '_bys360_admin_period_reminder_norm_v1',
        '_bys360_apply_general_category_visibility_fix_v1',
        '_bys360_apply_performance_main_switch',
        '_bys360_apply_performance_shortcut_gate_v4',
        '_bys360_exec_item_matches',
        '_bys360_exec_norm',
        '_bys360_force_home_menu_visible_v1',
        '_bys360_general_category_bool_v1',
        '_bys360_general_category_state_v1',
        '_bys360_is_exec_summary_menu_key',
        '_bys360_perf_rm_v8_apply_aliases',
        '_bys360_perf_rm_v8_apply_main_gate',
        '_bys360_perf_rm_v8_norm_role',
        '_bys360_perf_rm_v8_state_for_keys',
        '_bys360_performance_role_state',
        '_bys360_person_matrix_user_is_admin_v1',
        '_bys360_portal_role_matrix_v2_12_apply',
        '_bys360_restore_general_section_v4',
        '_get_unit_name_for_authority',
        '_row_map_by_key',
        '_safe_query_all',
    ]
    for name in names:
        bys_attrs[name] = _dummy
    bys = _module('app.services.settings.effective_menu_parts.bys360_context', **bys_attrs)

    mapping = {
        'app': app,
        'app.services': services,
        'app.services.settings': settings,
        'app.services.settings.effective_menu_parts': parts,
        'app.config': config,
        'app.menu_registry': registry,
        'app.models': models,
        'app.services.settings_service': settings_service,
        'app.services.settings.effective_menu_parts.bys360_context': bys,
    }
    with _temporary_modules(mapping):
        path = ROOT / APPLY_REL
        spec = importlib.util.spec_from_file_location('phase4dv_apply_context', path)
        assert spec is not None and spec.loader is not None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod


def _load_runtime():
    path = ROOT / RUNTIME_REL
    spec = importlib.util.spec_from_file_location('phase4dv_runtime_policy_context', path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


apply = _load_apply()
runtime = _load_runtime()


class Field:
    def __eq__(self, other): return ('eq', other)
    def in_(self, other): return ('in', tuple(other))
    def is_(self, other): return ('is', other)


class Query:
    def __init__(self, rows=None, fail=False):
        self.rows = rows or []
        self.fail = fail
    def filter(self, *args):
        if self.fail:
            raise RuntimeError('filter')
        return self
    def all(self):
        return self.rows


def test_apply_role_matrix_query_guard_and_helpers(monkeypatch):
    rollback = []
    fake_model = SimpleNamespace(
        role_name=Field(), menu_key=Field(), is_visible=Field(),
        query=Query([SimpleNamespace(menu_key='x'), SimpleNamespace(menu_key=''), SimpleNamespace(menu_key=None)]),
    )
    monkeypatch.setattr(apply, 'RoleMenuDefault', fake_model)
    monkeypatch.setattr(apply, 'normalize_role_name', lambda value: str(value or '').strip().lower())
    assert apply._get_role_matrix_closed_keys_for_role('') == set()
    assert apply._get_role_matrix_closed_keys_for_role('ADMIN') == {'x'}

    fake_model.query = Query(fail=True)
    assert apply._get_role_matrix_closed_keys_for_role('admin', rollback=lambda: rollback.append(True)) == set()
    assert rollback == [True]

    monkeypatch.setattr(apply, '_get_role_matrix_closed_keys_for_role', lambda *a, **k: {'x', 'absent'})
    visibility = {'x': True}
    source = {'seed': 'value'}
    assert apply._apply_role_matrix_closed_guard(visibility, 'admin', source_map=source) is visibility
    assert visibility['x'] is False and source['x'] == 'role_matrix_closed'

    assert apply._role_matrix_runtime_closed({'x': 'role_matrix_closed'}, 'x') is True
    assert apply._role_matrix_runtime_closed(None, 'x') is False
    assert apply._menu_item_by_key([{}, {'key': 'x'}]) == {'x': {'key': 'x'}}
    assert apply._settings_explicitly_controls_key('x', {'x': True}, {}, {}) is True
    assert apply._settings_explicitly_controls_key('x', {}, {}, {}) is False


def test_apply_role_policy_normalization_and_static_helpers(monkeypatch):
    assert apply._role_allowed_for_menu({}, 'admin') is False
    assert apply._role_allowed_for_menu({'admin_only': True}, 'personel') is False
    assert apply._role_allowed_for_menu({'required_roles': ['admin']}, 'personel') is False
    assert apply._role_allowed_for_menu({'required_roles': ['admin']}, 'admin') is True
    assert apply._phase3_2_ascii_tr('\u0130\u015e\u011e\u00dc\u00d6\u00c7\u0131') == 'isguoci'
    assert apply._phase3_2_normalize_role_name('Ba\u015fkan Yard\u0131mc\u0131s\u0131') == 'baskan_yardimcisi'

    monkeypatch.setattr(apply, 'normalize_role_name', lambda value: (_ for _ in ()).throw(RuntimeError('normalize')))
    assert apply._phase3_2_normalize_role_name('BA\u015eKAN YARDIMCISI') == 'baskan_yardimcisi'

    monkeypatch.setattr(apply, 'normalize_role_name', lambda value: str(value or '').strip().lower())
    items = {'x': {'key': 'x', 'required_roles': ['admin']}}
    assert apply._allowed_by_static_gate('missing', 'admin', items) is False
    assert apply._allowed_by_static_gate('x', 'personel', items) is False
    assert apply._allowed_by_static_gate('x', 'admin', items) is True


def test_apply_core_and_performance_policies(monkeypatch):
    monkeypatch.setattr(apply, 'normalize_role_name', lambda value: str(value or '').lower())
    visibility = {'messages': True, 'notifications': False, 'surveys': False, 'performance_reports': True, 'feedback_admin': True}
    source = {'messages': 'role_matrix_closed', 'performance_reports': 'role_matrix_closed', 'feedback_admin': 'user_override'}
    result = apply._apply_core_menu_visibility_policy(visibility, 'admin', source_map=source)
    assert result['messages'] is False
    assert result['notifications'] is True
    assert result['surveys'] is True
    assert result['performance_reports'] is False
    assert result['feedback_admin'] is True

    role_visibility = {'no_key': True, 'denied': True, 'allowed': True}
    apply._apply_role_gate(
        role_visibility,
        [{}, {'key': 'denied', 'admin_only': True}, {'key': 'allowed', 'required_roles': ['personel']}],
        'personel',
    )
    assert role_visibility['denied'] is False
    assert role_visibility['allowed'] is True

    monkeypatch.setattr(apply, 'PHASE3_PERFORMANCE_MENU_POLICY', {'a': {'admin'}, 'b': {'personel'}})
    p = {'a': True, 'b': True, 'other': True}
    assert apply._apply_phase3_performance_menu_policy(p, 'admin') == {'a': True, 'b': False, 'other': True}

    monkeypatch.setattr(apply, 'PHASE3_2_PERFORMANCE_MENU_POLICY', {'a': {'ba\u015fkan'}, 'b': {'personel'}})
    p2 = {'a': False, 'b': True}
    assert apply._apply_phase3_2_performance_menu_visibility(p2, 'Ba\u015fkan') == {'a': True, 'b': False}


def test_apply_press_news_paths(monkeypatch):
    user = SimpleNamespace(role='personel', is_admin=False, is_superuser=False)
    untouched = {'x': True}
    assert apply._apply_bys360_press_news_admin_only_policy(untouched, user) is untouched

    monkeypatch.setattr(apply, '_bys360_press_news_role', lambda value: str(value).lower())
    visibility = {'portal_press_news': True}
    apply._apply_bys360_press_news_admin_only_policy(visibility, user)
    assert visibility['portal_press_news'] is False
    user.is_admin = True
    apply._apply_bys360_press_news_admin_only_policy(visibility, user)
    assert visibility['portal_press_news'] is True


def test_apply_live_authority_all_decision_layers(monkeypatch):
    role_state = {
        'role_true': True,
        'role_false_block': False,
        'role_false_override': False,
        'not_in_visibility': False,
    }
    unit_state = {
        'unknown_unit': True,
        'role_false_block': True,
        'unit_false': False,
        'unit_true': True,
    }
    user_state = {
        'unknown_user': True,
        'deny_user': True,
        'allow_user': True,
        'user_false': False,
        'role_false_override': True,
    }
    monkeypatch.setattr(apply, 'normalize_role_name', lambda value: str(value or '').lower())
    monkeypatch.setattr(apply, '_load_role_matrix_state', lambda *a, **k: role_state)
    monkeypatch.setattr(apply, '_load_unit_profile_state', lambda *a, **k: unit_state)
    monkeypatch.setattr(apply, '_load_user_override_state', lambda *a, **k: user_state)
    monkeypatch.setattr(apply, '_bys360_person_matrix_can_open_v1', lambda key, item, user: key != 'deny_user')
    monkeypatch.setattr(apply, 'is_removed_menu_key', lambda key: key == 'removed')

    items = [
        {'key': key, 'required_roles': roles}
        for key, roles in [
            ('role_true', ['personel']),
            ('role_false_block', ['personel']),
            ('role_false_override', ['personel']),
            ('unit_false', ['personel']),
            ('unit_true', ['personel']),
            ('deny_user', ['personel']),
            ('allow_user', ['personel']),
            ('user_false', ['personel']),
            ('removed', ['personel']),
            ('static_denied', ['admin']),
            ('static_allowed', ['personel']),
        ]
    ]
    visibility = {
        'role_true': False,
        'role_false_block': True,
        'role_false_override': False,
        'unit_false': True,
        'unit_true': False,
        'deny_user': True,
        'allow_user': False,
        'user_false': True,
        'removed': True,
        'static_denied': True,
        'static_allowed': True,
        'orphan': True,
        'already_false': False,
    }
    result = apply._apply_bys360_settings_live_authority_v1(
        visibility,
        SimpleNamespace(id=1, role='personel'),
        'personel',
        items,
    )
    assert result['role_true'] is True
    assert result['role_false_block'] is False
    assert result['role_false_override'] is True
    assert result['unit_false'] is False
    assert result['unit_true'] is True
    assert result['deny_user'] is False
    assert result['allow_user'] is True
    assert result['user_false'] is False
    assert result['removed'] is False
    assert result['static_denied'] is False
    assert result['static_allowed'] is True
    assert result['orphan'] is True
    assert result['account'] is True and result['logout'] is True


class HybridList(list):
    def update(self, values):
        for value in values:
            if value not in self:
                self.append(value)
    def add(self, value):
        if value not in self:
            self.append(value)
    def difference_update(self, values):
        self[:] = [value for value in self if value not in set(values)]


class LineFailAuthority(set):
    def __init__(self, fail_line=None):
        super().__init__()
        self.fail_line = fail_line

    def _maybe_fail(self):
        import inspect
        frame = inspect.currentframe()
        assert frame is not None
        caller = frame.f_back
        assert caller is not None
        grandcaller = caller.f_back
        assert grandcaller is not None
        line = grandcaller.f_lineno
        if line == self.fail_line:
            raise RuntimeError(f"authority line {line}")

    def update(self, *values):
        self._maybe_fail()
        return super().update(*values)

    def add(self, value):
        self._maybe_fail()
        return super().add(value)

    def difference_update(self, *values):
        self._maybe_fail()
        return super().difference_update(*values)


class LineFailCore(dict):
    def __init__(self, fail_line=None):
        super().__init__()
        self.fail_line = fail_line

    def setdefault(self, key, default=None):
        import inspect
        frame = inspect.currentframe()
        assert frame is not None
        caller = frame.f_back
        assert caller is not None
        line = caller.f_lineno
        if line == self.fail_line:
            raise RuntimeError(f"core line {line}")
        return super().setdefault(key, default)


class FailDifferenceSet(set):
    def difference_update(self, *values):
        raise RuntimeError('difference')


class FailUpdateSet(set):
    def update(self, *values):
        raise RuntimeError('update')


def _constant_values(*, fail_constant_mutation=False):
    values = {
        '_BYS360_AG5E_AI_TEACHING_MENU_KEY': 'ai_teaching',
        '_BYS360_AG5E_AI_TEACHING_ROLES': {'admin'},
        '_BYS360_ALL_MENU_ROLE_MATRIX_AUTHORITY_KEYS': {'all_key'},
        '_BYS360_ALL_MENU_ROLE_MATRIX_POLICY': {'all_key': {'admin'}},
        '_BYS360_ASSISTANT_TAB_AUTHORITY_KEYS': {'assistant_key'},
        '_BYS360_ASSISTANT_TAB_POLICY': {'assistant_key': {'admin'}},
        '_BYS360_EXEC_ADMIN_ONLY_ROLES': {'admin'},
        '_BYS360_EXEC_KNOWN_KEYS': {'exec'},
        '_BYS360_EXEC_URL_MARKERS': {'/exec'},
        '_BYS360_GENERAL_CATEGORY_CHILD_KEYS_V1': {'general_child'},
        '_BYS360_GENERAL_CATEGORY_SECTION_KEYS_V1': {'general_section'},
        '_BYS360_GENERAL_CORE_KEYS_V4': {'general_core'},
        '_BYS360_MANUAL_POLICY': {'manual': {'admin'}},
        '_BYS360_MANUAL_ROLE_MENU_ADDITIONS': {'personel': ['manual', 'manual_added']},
        '_BYS360_PERFORMANCE_ALL_KEYS': {'performance_all'},
        '_BYS360_PERFORMANCE_CHILD_KEYS': {'performance_child'},
        '_BYS360_PERFORMANCE_CHILD_KEYS_V4': {'performance_child_v4'},
        '_BYS360_PERFORMANCE_GENERAL_SHORTCUT_KEYS_V4': {'shortcut'},
        '_BYS360_PERFORMANCE_MAIN_KEYS': {'performance_main'},
        '_BYS360_PERFORMANCE_MAIN_KEYS_V4': {'performance_main_v4'},
        '_BYS360_PERFORMANCE_MAIN_SWITCH_POLICY': {'performance_all': {'admin'}},
        '_BYS360_PERFORMANCE_ROLE_MATRIX_NEW_TAB_POLICY': {'new_tab': {'admin'}},
        '_BYS360_PERF_RM_V8_ALIAS_GROUPS': {'alias': {'canonical'}},
        '_BYS360_PERF_RM_V8_ALL_AUTH_ROLES': {'admin'},
        '_BYS360_PERF_RM_V8_ALL_KEYS': {'perf_v8'},
        '_BYS360_PERF_RM_V8_CANONICAL_CHILD_KEYS': {'canonical'},
        '_BYS360_PERF_RM_V8_CHILD_KEYS': {'child'},
        '_BYS360_PERF_RM_V8_MAIN_KEYS': {'main'},
        '_BYS360_PERF_RM_V8_MANAGER_ROLES': {'manager'},
        '_BYS360_PERF_RM_V8_ROLE_POLICY': {'perf_v8': {'admin'}},
        '_BYS360_PERIOD_CENTER_DEFAULT_ROLES_V221': {'admin'},
        '_BYS360_PERIOD_CENTER_MENU_KEY_V221': 'period_center',
        '_BYS360_PERSONEL_ALLOWED_POLICY': {'hr_leave_tracking': {'admin'}},
        '_BYS360_PERSONEL_DISALLOWED_POLICY_KEYS': {'hr_old'},
        '_BYS360_PERSONEL_ROLE_MATRIX_CURRENT_ALLOWED_KEYS': {'hr_leave_tracking'},
        '_BYS360_PERSONEL_ROLE_MATRIX_CURRENT_MANAGER_ROLES': {'admin'},
        '_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_KEYS': {'hr_v7'},
        '_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_MANAGER_ROLES': {'admin'},
        '_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_OBSOLETE_KEYS': {'hr_obsolete'},
        '_BYS360_PROCESS_MENU_KEYS': {'process_key'},
        '_BYS360_PROCESS_MENU_ROLES': {'admin'},
        '_BYS360_REMINDERS_ALLOWED_ROLES': {'admin'},
        '_BYS360_REMINDERS_MENU_KEY': 'reminders',
        '_BYS360_ROLE_MATRIX_V12_AUTHORITY_KEYS': {'v12'},
        '_BYS360_ROLE_MATRIX_V12_POLICY': {'v12': {'admin'}},
        '_BYS360_V223_PERIOD_CENTER_KEY_ROLES': {'period': {'admin'}},
    }
    if fail_constant_mutation:
        values['_BYS360_PERSONEL_DISALLOWED_POLICY_KEYS'] = FailDifferenceSet({'hr_old'})
        values['_BYS360_PERSONEL_ROLE_MATRIX_CURRENT_ALLOWED_KEYS'] = FailUpdateSet({'hr_leave_tracking'})
    return values


def _block_module():
    names = [
        'apply_reminders_menu_policy_block',
        'apply_reminders_menu_key_sets_block',
        'apply_process_menu_policy_block',
        'apply_performance_role_matrix_new_tab_policy_block',
        'apply_performance_role_matrix_new_tab_sets_block',
        'apply_role_matrix_runtime_authority_keys_block',
        'apply_personel_allowed_policy_block',
        'apply_personel_role_matrix_visibility_v7_block',
        'apply_daily_weather_policy_block',
    ]
    return _module(
        'app.services.settings.effective_menu_parts.block_context',
        **{name: _dummy for name in names},
    )


@contextmanager
def _runtime_modules(*, fail_constant_mutation=False):
    app = _package('app')
    services = _package('app.services')
    settings = _package('app.services.settings')
    parts = _package('app.services.settings.effective_menu_parts')
    constants = _module(
        'app.services.settings.effective_menu_parts.bys360_constants',
        **_constant_values(fail_constant_mutation=fail_constant_mutation),
    )
    mapping = {
        'app': app,
        'app.services': services,
        'app.services.settings': settings,
        'app.services.settings.effective_menu_parts': parts,
        'app.services.settings.effective_menu_parts.bys360_constants': constants,
        'app.services.settings.effective_menu_parts.block_context': _block_module(),
    }
    with _temporary_modules(mapping):
        yield constants


def _policy_keys(constants):
    keys = set(constants._BYS360_MANUAL_POLICY)
    keys.update(constants._BYS360_ROLE_MATRIX_V12_POLICY)
    keys.add(constants._BYS360_AG5E_AI_TEACHING_MENU_KEY)
    keys.update(constants._BYS360_ALL_MENU_ROLE_MATRIX_POLICY)
    keys.update(constants._BYS360_ASSISTANT_TAB_POLICY)
    keys.update(constants._BYS360_PERFORMANCE_MAIN_SWITCH_POLICY)
    keys.update(constants._BYS360_PERF_RM_V8_ROLE_POLICY)
    return keys


def _ns(constants, *, lists=False, authority=None, core=None):
    if lists:
        policies: dict[str, list[str]] = {name: [] for name in _policy_keys(constants)}

        def make_policy():
            return {key: [] for key in policies}

        def make_keys():
            return HybridList(['hr_old'])
        authority_value = authority if authority is not None else HybridList(['hr_old'])
    else:
        make_policy = dict
        make_keys = set
        authority_value = authority if authority is not None else set()
    return {
        'CORE_MENU_VISIBILITY_POLICY': core if core is not None else {},
        'ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS': authority_value,
        'PHASE3_PERFORMANCE_MENU_POLICY': make_policy(),
        'PHASE3_2_PERFORMANCE_MENU_POLICY': make_policy(),
        'PERFORMANCE_MENU_POLICY': make_policy(),
        'ROLE_MENU_POLICY': make_policy(),
        'ROLE_MATRIX_POLICY': make_policy(),
        'PHASE3_2_MANAGER_VISIBLE_KEYS': make_keys(),
        'PHASE3_2_GENERAL_VISIBLE_KEYS': make_keys(),
        'PERFORMANCE_ROLE_MATRIX_KEYS': make_keys(),
    }


class Log:
    def exception(self, *args, **kwargs):
        return None


def test_runtime_success_set_and_list_paths():
    with _runtime_modules() as constants:
        ns = _ns(constants, lists=False)
        runtime.apply_runtime_policy_blocks(ns, logging=Log())
        assert 'portal_feed' in ns['CORE_MENU_VISIBILITY_POLICY']
        assert 'PORTAL_ROLE_MATRIX_V2_12_KEYS' in ns
    with _runtime_modules() as constants:
        ns = _ns(constants, lists=True)
        runtime.apply_runtime_policy_blocks(ns, logging=Log())
        assert 'manual' in ns['PHASE3_2_MANAGER_VISIBLE_KEYS']
        assert 'process_key' in ns['PHASE3_2_GENERAL_VISIBLE_KEYS']
        assert 'perf_v8' in ns['PERFORMANCE_ROLE_MATRIX_KEYS']


@pytest.mark.parametrize('fail_line', [166, 200, 249, 265, 292, 316, 345, 359, 396, 476, 503])
def test_runtime_authority_fallbacks(fail_line):
    with _runtime_modules() as constants:
        ns = _ns(constants, authority=LineFailAuthority(fail_line=fail_line))
        runtime.apply_runtime_policy_blocks(ns, logging=Log())
        assert 'PORTAL_MENU_VISIBILITY_POLICY' in ns


def test_runtime_authority_difference_fallback():
    with _runtime_modules() as constants:
        ns = _ns(constants, authority=LineFailAuthority(fail_line=360))
        runtime.apply_runtime_policy_blocks(ns, logging=Log())


@pytest.mark.parametrize('fail_line', [189, 204, 256, 299, 367, 403])
def test_runtime_core_policy_fallbacks(fail_line):
    with _runtime_modules() as constants:
        ns = _ns(constants, core=LineFailCore(fail_line))
        runtime.apply_runtime_policy_blocks(ns, logging=Log())
        assert 'PORTAL_ROLE_MATRIX_V2_12_DEFAULTS' in ns


def test_runtime_constant_mutation_fallback():
    with _runtime_modules(fail_constant_mutation=True) as constants:
        ns = _ns(constants)
        runtime.apply_runtime_policy_blocks(ns, logging=Log())
        assert 'PORTAL_MENU_VISIBILITY_POLICY' in ns


def test_apply_loop_false_paths(monkeypatch):
    monkeypatch.setattr(
        apply,
        'CORE_MENU_VISIBILITY_POLICY',
        {'messages': set(), 'notifications': set(), 'surveys': set()},
    )
    visibility = {'messages': True, 'notifications': True, 'surveys': True}
    apply._apply_core_menu_visibility_policy(visibility, 'nobody')
    assert visibility == {'messages': True, 'notifications': True, 'surveys': True}

    monkeypatch.setattr(apply, 'PHASE3_PERFORMANCE_MENU_POLICY', {'present': {'admin'}, 'absent': {'admin'}})
    assert apply._apply_phase3_performance_menu_policy({'present': False}, 'admin')['present'] is True

    monkeypatch.setattr(apply, 'PHASE3_2_PERFORMANCE_MENU_POLICY', {'present': {'admin'}, 'absent': {'admin'}})
    assert apply._apply_phase3_2_performance_menu_visibility({'present': False}, 'admin')['present'] is True


def test_runtime_non_dict_and_neither_collection_branches():
    with _runtime_modules() as constants:
        ns = _ns(constants)
        for key in [
            'PHASE3_PERFORMANCE_MENU_POLICY',
            'PHASE3_2_PERFORMANCE_MENU_POLICY',
            'PERFORMANCE_MENU_POLICY',
            'ROLE_MENU_POLICY',
            'ROLE_MATRIX_POLICY',
        ]:
            ns[key] = 'skip'
        runtime.apply_runtime_policy_blocks(ns, logging=Log())

    with _runtime_modules() as constants:
        all_keys = _policy_keys(constants)
        ns = _ns(constants)
        for key in [
            'PHASE3_PERFORMANCE_MENU_POLICY',
            'PHASE3_2_PERFORMANCE_MENU_POLICY',
            'PERFORMANCE_MENU_POLICY',
            'ROLE_MENU_POLICY',
            'ROLE_MATRIX_POLICY',
        ]:
            ns[key] = {item: ('skip',) for item in all_keys}
        ns['PHASE3_2_MANAGER_VISIBLE_KEYS'] = ('skip',)
        ns['PHASE3_2_GENERAL_VISIBLE_KEYS'] = ('skip',)
        ns['PERFORMANCE_ROLE_MATRIX_KEYS'] = ('skip',)
        runtime.apply_runtime_policy_blocks(ns, logging=Log())
