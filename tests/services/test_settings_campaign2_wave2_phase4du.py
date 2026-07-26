from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


class Query:
    def __init__(self, rows=None, error=None):
        self.rows = list(rows or [])
        self.error = error
        self.filters = []

    def filter_by(self, **kwargs):
        self.filters.append(kwargs)
        return self

    def all(self):
        if self.error:
            raise self.error
        return list(self.rows)


class Model:
    query = Query()


removed: set[str] = set()

def is_removed(key):
    return key in removed


app = types.ModuleType("app")
app.__path__ = []
# These stand-ins have no fixed attribute contract -- their entire purpose is
# to receive whatever ad hoc symbols the loaded production module imports at
# runtime, exactly like a real module's namespace after exec. `Any` is the
# accurate type here, not a loosened one.
config: Any = types.ModuleType("app.config")
config.is_removed_menu_key = is_removed
menu_registry: Any = types.ModuleType("app.menu_registry")
menu_registry.flatten_menu_definitions = lambda *a, **k: []
models: Any = types.ModuleType("app.models")
models.UserMenuPermission = type("UserMenuPermission", (), {"query": Query()})
models.RoleMenuDefault = type("RoleMenuDefault", (), {"query": Query()})
models.UnitMenuProfile = type("UnitMenuProfile", (), {"query": Query()})
services = types.ModuleType("app.services")
services.__path__ = []
settings_pkg = types.ModuleType("app.services.settings")
settings_pkg.__path__ = []
settings_service: Any = types.ModuleType("app.services.settings_service")
settings_service.build_effective_user_menu_context = lambda *a, **k: {}
settings_service.get_role_default_menu_keys = lambda role: []
STUB_MODULES = {
    "app": app,
    "app.config": config,
    "app.menu_registry": menu_registry,
    "app.models": models,
    "app.services": services,
    "app.services.settings": settings_pkg,
    "app.services.settings_service": settings_service,
}
SAVED_MODULES = {name: sys.modules.get(name) for name in STUB_MODULES}
for name, module in STUB_MODULES.items():
    sys.modules[name] = module


def load(name, relative):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bys = load("wave2_bys360", "app/services/settings/effective_menu_parts/bys360_context.py")
build = load("wave2_build", "app/services/settings/effective_menu_parts/build_context.py")
for name, previous in SAVED_MODULES.items():
    if previous is None:
        sys.modules.pop(name, None)
    else:
        sys.modules[name] = previous


class BadAttr:
    def __getattribute__(self, name):
        if name.startswith("__"):
            return object.__getattribute__(self, name)
        raise RuntimeError(name)


class BadOrg:
    birim = ""
    unit_name = ""
    department = ""
    organization_unit_name = ""
    @property
    def organization_unit(self):
        raise RuntimeError("organization_unit")


class BadItem:
    def get(self, *a, **k):
        raise RuntimeError("get")


class Log:
    def __init__(self):
        self.messages = []
    def warning(self, *args, **kwargs):
        self.messages.append((args, kwargs))
    def exception(self, *args, **kwargs):
        self.messages.append((args, kwargs))


def test_bys_basic_loaders_and_rows(monkeypatch):
    assert bys.normalize_role_name(" Admin ") == "admin"
    bys._rollback(None)
    called = []
    bys._rollback(lambda: called.append(1))
    assert called == [1]
    bys._rollback(lambda: (_ for _ in ()).throw(RuntimeError("x")))

    assert bys._safe_query_all(Query([1, 2])) == [1, 2]
    called.clear()
    assert bys._safe_query_all(Query(error=RuntimeError("x")), rollback=lambda: called.append(1)) == []
    assert called == [1]

    assert bys._get_unit_name_for_authority(SimpleNamespace(birim=" Unit ")) == "Unit"
    assert bys._get_unit_name_for_authority(SimpleNamespace(birim="", unit_name="X")) == "X"
    assert bys._get_unit_name_for_authority(SimpleNamespace(organization_unit=SimpleNamespace(name=" Org "))) == "Org"
    assert bys._get_unit_name_for_authority(BadOrg()) == ""
    assert bys._get_unit_name_for_authority(SimpleNamespace()) == ""

    removed.clear()
    removed.add("gone")
    rows = [SimpleNamespace(menu_key="", is_visible=True), SimpleNamespace(menu_key="gone", is_visible=True), SimpleNamespace(menu_key="ok", is_visible=1)]
    assert bys._row_map_by_key(rows) == {"ok": True}
    assert bys._row_map_by_key([]) == {}

    assert bys._load_role_matrix_state("") == {}
    models.RoleMenuDefault.query = Query([SimpleNamespace(menu_key="r", is_visible=False)])
    assert bys._load_role_matrix_state(" Admin ") == {"r": False}

    assert bys._load_unit_profile_state(SimpleNamespace()) == {}
    monkeypatch.setitem(sys.modules, "app.models", models)
    models.UnitMenuProfile.query = Query([SimpleNamespace(menu_key="u", is_visible=True)])
    assert bys._load_unit_profile_state(SimpleNamespace(birim="A")) == {"u": True}

    assert bys._load_user_override_state(SimpleNamespace(id=None)) == {}
    models.UserMenuPermission.query = Query([SimpleNamespace(menu_key="p", is_visible=True)])
    assert bys._load_user_override_state(SimpleNamespace(id=3)) == {"p": True}


def test_bys_unit_import_error_and_portal_existing(monkeypatch):
    monkeypatch.setitem(sys.modules, "app.models", types.ModuleType("app.models"))
    assert bys._load_unit_profile_state(SimpleNamespace(birim="A")) == {}

    monkeypatch.setattr(bys, "_load_role_matrix_state", lambda *a, **k: {})
    monkeypatch.setattr(bys, "_load_unit_profile_state", lambda *a, **k: {})
    monkeypatch.setattr(bys, "_load_user_override_state", lambda *a, **k: {})
    existing = {key: False for key in bys.PORTAL_ROLE_MATRIX_V2_12_KEYS}
    out = bys._bys360_portal_role_matrix_v2_12_apply(existing, SimpleNamespace(role="personel"))
    assert out == existing


def test_bys_role_and_performance_helpers(monkeypatch):
    assert bys._bys360_press_news_role(" \u0130 \u015e\u011e\u00dc\u00d6\u00c7-A ") == "i\u0307_sguoc_a"
    monkeypatch.setattr(bys, "_load_role_matrix_state", lambda *a, **k: {"x": True})
    assert bys._bys360_performance_role_state("A") == {"x": True}
    monkeypatch.setattr(bys, "_load_role_matrix_state", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x")))
    assert bys._bys360_performance_role_state("A") == {}

    monkeypatch.setattr(bys, "_bys360_performance_role_state", lambda *a, **k: {"performance_module": False})
    vis = {"performance_tasks": True}
    out = bys._bys360_apply_performance_main_switch(vis, None, "x")
    assert out["performance_module"] is False and out["performance_tasks"] is False
    monkeypatch.setattr(bys, "_bys360_performance_role_state", lambda *a, **k: {})
    out = bys._bys360_apply_performance_main_switch({"performance_tasks": True}, None, "x")
    assert out["performance_module"] is True

    vis = bys._bys360_restore_general_section_v4({"general_section": False, "home": True}, None)
    assert vis["general_section"] is False
    vis = bys._bys360_restore_general_section_v4({}, None)
    assert vis["home"] and vis["dashboard"]

    out = bys._bys360_apply_performance_shortcut_gate_v4({"performance_module": False, "performance_tasks": True})
    assert out["performance_tasks"] is False
    out = bys._bys360_apply_performance_shortcut_gate_v4({"performance_module": True, "performance_tasks": True})
    assert out["performance_tasks"] is True
    assert bys._bys360_perf_rm_v8_norm_role(" A ") == "a"


def test_bys_v8_state_aliases_and_gate():
    assert bys._bys360_perf_rm_v8_state_for_keys([], {}, {}, {}) is None
    assert bys._bys360_perf_rm_v8_state_for_keys(["x"], {"x": False}, {"x": True}, {"x": True}) is False
    assert bys._bys360_perf_rm_v8_state_for_keys(["x"], {"x": True}, {"x": False}, {"x": True}) is True
    assert bys._bys360_perf_rm_v8_state_for_keys(["x"], {}, {"x": True}, {}) is True

    original = bys._BYS360_PERF_RM_V8_ALIAS_GROUPS
    bys._BYS360_PERF_RM_V8_ALIAS_GROUPS = {"canon": ["canon", "alias"]}
    try:
        out = bys._bys360_perf_rm_v8_apply_aliases({}, {"alias": False}, {}, {})
        assert out == {"canon": False, "alias": False}
        out = bys._bys360_perf_rm_v8_apply_aliases({"alias": True}, {}, {}, {})
        assert out == {"alias": True, "canon": True}
        out = bys._bys360_perf_rm_v8_apply_aliases({}, {}, {}, {})
        assert out == {}
    finally:
        bys._BYS360_PERF_RM_V8_ALIAS_GROUPS = original

    old_groups = bys._BYS360_PERF_RM_V8_ALIAS_GROUPS
    old_canon = bys._BYS360_PERF_RM_V8_CANONICAL_CHILD_KEYS
    old_children = bys._BYS360_PERF_RM_V8_CHILD_KEYS
    old_main = bys._BYS360_PERF_RM_V8_MAIN_KEYS
    bys._BYS360_PERF_RM_V8_ALIAS_GROUPS = {"child": ["child", "alias"]}
    bys._BYS360_PERF_RM_V8_CANONICAL_CHILD_KEYS = {"child"}
    bys._BYS360_PERF_RM_V8_CHILD_KEYS = {"child", "alias"}
    bys._BYS360_PERF_RM_V8_MAIN_KEYS = {"main"}
    try:
        assert bys._bys360_perf_rm_v8_apply_main_gate({"child": True}, {}, {}, {})["main"] is True
        assert bys._bys360_perf_rm_v8_apply_main_gate({}, {"child": True}, {}, {})["main"] is True
        assert bys._bys360_perf_rm_v8_apply_main_gate({}, {"main": True}, {}, {})["main"] is True
        out = bys._bys360_perf_rm_v8_apply_main_gate({"child": True, "alias": True}, {"main": False}, {}, {})
        assert out["main"] is True
        out = bys._bys360_perf_rm_v8_apply_main_gate({}, {}, {}, {})
        assert out["main"] is False and out["child"] is False
    finally:
        bys._BYS360_PERF_RM_V8_ALIAS_GROUPS = old_groups
        bys._BYS360_PERF_RM_V8_CANONICAL_CHILD_KEYS = old_canon
        bys._BYS360_PERF_RM_V8_CHILD_KEYS = old_children
        bys._BYS360_PERF_RM_V8_MAIN_KEYS = old_main


def test_bys_person_and_general_helpers(monkeypatch):
    assert bys._bys360_person_matrix_user_is_admin_v1(SimpleNamespace(role="admin"))
    assert bys._bys360_person_matrix_user_is_admin_v1(SimpleNamespace(role="x", is_admin=True))
    assert not bys._bys360_person_matrix_user_is_admin_v1(SimpleNamespace(role="x"))
    removed.clear()
    removed.add("gone")
    assert not bys._bys360_person_matrix_can_open_v1("", {}, SimpleNamespace(role="admin"))
    assert not bys._bys360_person_matrix_can_open_v1("gone", {}, SimpleNamespace(role="admin"))
    assert not bys._bys360_person_matrix_can_open_v1("x", {"admin_only": True}, SimpleNamespace(role="personel"))
    assert bys._bys360_person_matrix_can_open_v1("x", None, SimpleNamespace(role="personel"))
    for value in [True, "1", "yes", "acik", "a\u00e7\u0131k"]:
        assert bys._bys360_general_category_bool_v1(value)
    assert not bys._bys360_general_category_bool_v1("no")

    monkeypatch.setattr(bys, "_load_role_matrix_state", lambda *a, **k: {"r": 1})
    monkeypatch.setattr(bys, "_load_unit_profile_state", lambda *a, **k: {"u": 1})
    monkeypatch.setattr(bys, "_load_user_override_state", lambda *a, **k: {"p": 1})
    assert bys._bys360_general_category_state_v1(None, "x") == {"r": 1, "u": 1, "p": 1}
    for target in ["_load_role_matrix_state", "_load_unit_profile_state", "_load_user_override_state"]:
        monkeypatch.setattr(bys, target, lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x")))
    assert bys._bys360_general_category_state_v1(None, "x") == {}

    monkeypatch.setattr(bys, "_bys360_general_category_state_v1", lambda *a, **k: {"general": True})
    out = bys._bys360_apply_general_category_visibility_fix_v1({}, SimpleNamespace(role="x"))
    assert out["general_section"] and out["home"] and out["dashboard"]
    monkeypatch.setattr(bys, "_bys360_general_category_state_v1", lambda *a, **k: {"general": True, "home": False, "dashboard": False})
    out = bys._bys360_apply_general_category_visibility_fix_v1({}, None)
    assert "home" not in out and "dashboard" not in out
    monkeypatch.setattr(bys, "_bys360_general_category_state_v1", lambda *a, **k: {})
    out = bys._bys360_apply_general_category_visibility_fix_v1({"home": True}, None)
    assert out["general_section"]

    monkeypatch.setattr(bys, "normalize_role_name", lambda x: (_ for _ in ()).throw(RuntimeError("x")))
    out = bys._bys360_apply_general_category_visibility_fix_v1({}, SimpleNamespace(role=" X "))
    assert out["account"] and out["logout"]
    out = bys._bys360_force_home_menu_visible_v1({}, None)
    assert all(out[k] for k in ["general_section", "genel", "general", "home", "account", "logout"])


def test_bys_portal_exec_and_admin(monkeypatch):
    monkeypatch.setattr(bys, "_load_role_matrix_state", lambda *a, **k: {"portal_feed": False, "portal_people": True})
    monkeypatch.setattr(bys, "_load_unit_profile_state", lambda *a, **k: {"portal_feed": True, "portal_profiles": True})
    monkeypatch.setattr(bys, "_load_user_override_state", lambda *a, **k: {"portal_feed": True, "portal_people": False})
    out = bys._bys360_portal_role_matrix_v2_12_apply({}, SimpleNamespace(role="personel"))
    assert out["portal_feed"] is False and out["portal_people"] is False and out["portal_profiles"] is True
    monkeypatch.setattr(bys, "_load_role_matrix_state", lambda *a, **k: {})
    monkeypatch.setattr(bys, "_load_unit_profile_state", lambda *a, **k: {})
    monkeypatch.setattr(bys, "_load_user_override_state", lambda *a, **k: {})
    out = bys._bys360_portal_role_matrix_v2_12_apply({}, SimpleNamespace(role="admin"))
    assert all(out[k] for k in bys.PORTAL_ROLE_MATRIX_V2_12_KEYS)
    for target in ["_load_role_matrix_state", "_load_unit_profile_state", "_load_user_override_state"]:
        monkeypatch.setattr(bys, target, lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x")))
    out = bys._bys360_portal_role_matrix_v2_12_apply({}, None)
    assert out

    monkeypatch.setattr(bys, "normalize_role_name", lambda x: " admin ")
    assert bys._bys360_exec_norm("x") == "admin"
    monkeypatch.setattr(bys, "normalize_role_name", lambda x: (_ for _ in ()).throw(RuntimeError("x")))
    assert bys._bys360_exec_norm(" A-B ") == "a_b"
    assert not bys._bys360_is_exec_summary_menu_key("")
    for key in ["executive_summary", "foo_executive-summary", "yonetici_ozeti_x", "daily_weather_mail_x"]:
        assert bys._bys360_is_exec_summary_menu_key(key)
    assert not bys._bys360_is_exec_summary_menu_key("other")
    assert bys._bys360_exec_item_matches({"key": "executive_summary"})
    assert bys._bys360_exec_item_matches({"key": "x", "url": "/executive-summary/a"})
    assert bys._bys360_exec_item_matches({"key": "x", "label": "yonetici ozeti"})
    assert not bys._bys360_exec_item_matches({"key": "x"})
    assert not bys._bys360_exec_item_matches(BadItem())

    assert bys._bys360_admin_period_reminder_norm_v1(" Y\u00f6netici-\u011e ") == "yonetici_g"
    assert not bys._bys360_admin_period_reminder_is_admin_v1(None)
    assert bys._bys360_admin_period_reminder_is_admin_v1(SimpleNamespace(is_admin=True))
    assert bys._bys360_admin_period_reminder_is_admin_v1(SimpleNamespace(role="Y\u00f6netici"))
    role_obj = SimpleNamespace(name="administrator", role_name="")
    assert bys._bys360_admin_period_reminder_is_admin_v1(SimpleNamespace(role=role_obj))
    assert not bys._bys360_admin_period_reminder_is_admin_v1(BadAttr())


def make_effective_module():
    # Same rationale as the STUB_MODULES stand-ins above: this module object
    # exists solely to receive an ad hoc set of dynamically-assigned
    # attributes, so `Any` is its accurate type, not a loosened one.
    m: Any = types.ModuleType("app.services.settings.effective_menu")
    m.Any = object
    m.PORTAL_MENU_VISIBILITY_POLICY = {"portal": {"admin"}}
    m.UserMenuPermission = type("UP", (), {"query": Query()})
    m._BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_KEYS = {"admin_users", "custom"}
    m._BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_MANAGER_ROLES = {"admin"}
    m._BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_OBSOLETE_KEYS = {"obsolete"}
    m._active_menu_items = lambda: [{"key": "home"}, {"key": "surveys"}, {"key": "custom"}, {"key": "performance_module"}, {"key": "performance_tasks"}, {"key": "assistant_module"}, {"key": "ai_agent_panel"}, {"key": "executive_summary", "url": "/executive-summary"}, {"key": "portal"}]
    def identity(visibility, *a, **k):
        return visibility
    for name in [
        "_apply_bys360_press_news_admin_only_policy", "_apply_bys360_settings_live_authority_v1", "_apply_core_menu_visibility_policy", "_apply_phase3_2_performance_menu_visibility", "_apply_phase3_performance_menu_policy", "_apply_role_matrix_closed_guard", "_bys360_apply_general_category_visibility_fix_v1", "_bys360_apply_performance_main_switch", "_bys360_apply_performance_shortcut_gate_v4", "_bys360_force_home_menu_visible_v1", "_bys360_perf_rm_v8_apply_aliases", "_bys360_perf_rm_v8_apply_main_gate", "_bys360_portal_role_matrix_v2_12_apply", "_bys360_restore_general_section_v4",
    ]:
        setattr(m, name, identity)
    m._apply_role_gate = lambda visibility, *a, **k: None
    m._bys360_exec_item_matches = lambda item: "executive" in str(item.get("key"))
    m._bys360_exec_norm = lambda role: str(role).lower()
    m._bys360_is_exec_summary_menu_key = lambda key: "executive" in str(key)
    m._bys360_perf_rm_v8_norm_role = lambda role: str(role).lower()
    m._load_role_matrix_state = lambda *a, **k: {}
    m._load_unit_profile_state = lambda *a, **k: {}
    m._load_user_override_state = lambda *a, **k: {}
    m._log_warning = lambda *a, **k: None
    m._phase3_2_normalize_role_name = lambda role: str(role).lower()
    m._role_allowed_for_menu = lambda item, role: True
    m._rollback = lambda cb: cb() if cb else None
    m._user_has_any_assigned_survey = lambda *a, **k: True
    m.build_effective_user_menu_context = lambda user, items: {"effective_rule_map": {"custom": True, "performance_tasks": True, "ai_agent_panel": True}, "source_map": {}}
    m.get_role_default_menu_keys = lambda role: ["home", "gone"]
    m.is_removed_menu_key = is_removed
    m.normalize_role_name = lambda role: str(role).lower()
    return m


def test_build_no_user_and_success(monkeypatch):
    m = make_effective_module()
    sys.modules[m.__name__] = m
    out = build.build_menu_visibility_map(None)
    assert out["home"] and out["account"] and out["logout"]

    build._BYS360_EXEC_ADMIN_ONLY_ROLES = {"admin"}
    build._BYS360_EXEC_KNOWN_KEYS = {"executive_summary"}
    out = build.build_menu_visibility_map(SimpleNamespace(id=1, role="admin"))
    assert out["custom"] and out["surveys"]
    assert out["performance_module"] and out["assistant_module"]
    assert out["executive_summary"]
    assert out["portal"] is False
    assert out["account"] and out["logout"]


def test_build_fallback_rows_and_errors(monkeypatch):
    m = make_effective_module()
    sys.modules[m.__name__] = m
    removed.clear()
    removed.add("gone")
    m.build_effective_user_menu_context = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x"))
    m.UserMenuPermission.query = Query([SimpleNamespace(menu_key="custom", is_visible=False), SimpleNamespace(menu_key="gone", is_visible=True)])
    out = build.build_menu_visibility_map(SimpleNamespace(id=2, role="personel"), rollback=lambda: None)
    assert out["home"] and out["custom"] is False

    m.UserMenuPermission.query = Query(error=RuntimeError("db"))
    out = build.build_menu_visibility_map(SimpleNamespace(id=2, role="personel"), rollback=lambda: None)
    assert out["home"]


def test_build_survey_and_exec_edge_paths(monkeypatch):
    m = make_effective_module()
    monkeypatch.setitem(sys.modules, m.__name__, m)
    build._BYS360_EXEC_ADMIN_ONLY_ROLES = {"admin"}
    build._BYS360_EXEC_KNOWN_KEYS = {"absent_exec"}

    m.build_effective_user_menu_context = lambda user, items: {"effective_rule_map": {"surveys": True}, "source_map": {}}
    out = build.build_menu_visibility_map(SimpleNamespace(id=8, role="personel"))
    assert out["surveys"] is True and "absent_exec" not in out

    m.build_effective_user_menu_context = lambda user, items: {"effective_rule_map": {}, "source_map": {}}
    m._role_allowed_for_menu = lambda *a, **k: False
    out = build.build_menu_visibility_map(SimpleNamespace(id=9, role="personel"))
    assert out["surveys"] is False

    m._role_allowed_for_menu = lambda *a, **k: True
    m._user_has_any_assigned_survey = lambda *a, **k: False
    out = build.build_menu_visibility_map(SimpleNamespace(id=10, role="personel"))
    assert out["surveys"] is False

    m._BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_KEYS = {"custom", "admin_users"}
    m._load_role_matrix_state = lambda *a, **k: {}
    m._load_unit_profile_state = lambda *a, **k: {"custom": True}
    m._load_user_override_state = lambda *a, **k: {"admin_users": True}
    out = build.build_menu_visibility_map(SimpleNamespace(id=11, role="personel"))
    assert out["custom"] is True and out["admin_users"] is True

    m._bys360_exec_norm = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("exec"))
    out = build.build_menu_visibility_map(SimpleNamespace(id=12, role="personel"))
    assert out["account"] is True


def test_build_inline_state_and_exception_paths(monkeypatch):
    m = make_effective_module()
    sys.modules[m.__name__] = m
    build._BYS360_EXEC_ADMIN_ONLY_ROLES = set()
    build._BYS360_EXEC_KNOWN_KEYS = {"executive_summary"}
    m._BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_KEYS = {"admin_users", "custom"}
    m._load_role_matrix_state = lambda *a, **k: {"custom": False, "admin_users": False}
    m._load_unit_profile_state = lambda *a, **k: {"custom": True, "admin_users": True}
    m._load_user_override_state = lambda *a, **k: {"custom": True, "admin_users": False, "performance_tasks": True, "unknown": True}
    out = build.build_menu_visibility_map(SimpleNamespace(id=3, role="personel"))
    assert out["custom"] is True and out["admin_users"] is False
    assert out["performance_module"] is True
    assert out["executive_summary"] is False

    calls = {"role": 0, "unit": 0, "user": 0, "active": 0}
    def fail_role(*a, **k):
        calls["role"] += 1
        if calls["role"] >= 2:
            raise RuntimeError("role")
        return {}
    def fail_unit(*a, **k):
        calls["unit"] += 1
        if calls["unit"] >= 2:
            raise RuntimeError("unit")
        return {}
    def fail_user(*a, **k):
        calls["user"] += 1
        if calls["user"] >= 2:
            raise RuntimeError("user")
        return {}
    def fail_active():
        calls["active"] += 1
        if calls["active"] >= 2:
            raise RuntimeError("active")
        return [{"key": "home"}, {"key": "executive_summary"}]
    m._load_role_matrix_state = fail_role
    m._load_unit_profile_state = fail_unit
    m._load_user_override_state = fail_user
    m._active_menu_items = fail_active
    m._bys360_perf_rm_v8_apply_aliases = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("alias")) if False else a[0]
    out = build.build_menu_visibility_map(SimpleNamespace(id=4, role="personel"))
    assert out["account"] and out["logout"]
