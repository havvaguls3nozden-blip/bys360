from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from app.services import corporate_information_center
from app.services.cic import (
    celebration_service,
    cic_context,
    misc_context,
    query_service,
    send_context,
)

ROOT = Path(__file__).resolve().parents[2]
MOVED_QUERY_FUNCTIONS = {
    "_active_staff_users",
    "_cic_v40_active_staff_candidates",
    "_cic_v40_special_day_users",
    "_cic_v40_upcoming_users",
    "_users_by_ids",
    "list_users",
}


class _Column:
    def __init__(self, name: str) -> None:
        self.name = name

    def is_(self, value: object) -> tuple[str, str, object]:
        return ("is", self.name, value)

    def isnot(self, value: object) -> tuple[str, str, object]:
        return ("isnot", self.name, value)

    def ilike(self, value: object) -> tuple[str, str, object]:
        return ("ilike", self.name, value)

    def in_(self, values: list[int]) -> tuple[str, str, tuple[int, ...]]:
        return ("in", self.name, tuple(values))

    def asc(self) -> tuple[str, str]:
        return ("asc", self.name)

    def __ne__(self, value: object) -> tuple[str, str, object]:
        return ("ne", self.name, value)


class _Query:
    def __init__(self, rows: list[Any]) -> None:
        self.rows = list(rows)
        self.filters: list[tuple[object, ...]] = []
        self.ordering: tuple[object, ...] = ()
        self.limit_value: int | None = None

    def filter(self, *clauses: object) -> _Query:
        self.filters.append(clauses)
        return self

    def order_by(self, *ordering: object) -> _Query:
        self.ordering = ordering
        return self

    def limit(self, value: int) -> _Query:
        self.limit_value = value
        return self

    def all(self) -> list[Any]:
        if self.limit_value is None:
            return list(self.rows)
        return list(self.rows[: self.limit_value])


class _UserModel:
    id = _Column("id")
    is_active = _Column("is_active")
    email = _Column("email")
    ad = _Column("ad")
    soyad = _Column("soyad")
    sicil_no = _Column("sicil_no")
    birim = _Column("birim")
    ust_birim = _Column("ust_birim")
    unvan = _Column("unvan")
    role_label = _Column("role_label")
    username = _Column("username")
    query = _Query([])


def _top_level_definitions(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_query_functions_have_one_canonical_definition() -> None:
    query_definitions = _top_level_definitions(
        ROOT / "app/services/cic/query_service.py"
    )
    assert query_definitions >= MOVED_QUERY_FUNCTIONS

    for relative in (
        "app/services/cic/misc_context.py",
        "app/services/cic/send_context.py",
        "app/services/cic/cic_context.py",
    ):
        assert not (
            MOVED_QUERY_FUNCTIONS & _top_level_definitions(ROOT / relative)
        )

    source = (ROOT / "app/services/cic/query_service.py").read_text(
        encoding="utf-8"
    )
    assert "corporate_information_center as _legacy" not in source
    assert "_legacy." not in source


def test_existing_modules_use_the_canonical_query_functions() -> None:
    assert misc_context.list_users is query_service.list_users
    assert misc_context._users_by_ids is query_service._users_by_ids
    assert misc_context._active_staff_users is query_service._active_staff_users
    assert not hasattr(send_context, "_cic_v40_active_staff_candidates")
    assert (
        send_context._cic_v40_special_day_users
        is query_service._cic_v40_special_day_users
    )
    assert not hasattr(cic_context, "_cic_v40_upcoming_users")
    assert not hasattr(corporate_information_center, "list_users")
    assert not hasattr(
        corporate_information_center,
        "_cic_v40_upcoming_users",
    )


def test_list_users_preserves_active_search_order_and_limit(monkeypatch) -> None:
    rows = [SimpleNamespace(id=2), SimpleNamespace(id=1)]
    query = _Query(rows)
    _UserModel.query = query

    monkeypatch.setattr(query_service, "User", _UserModel)
    monkeypatch.setattr(
        query_service,
        "or_",
        lambda *clauses: ("or", clauses),
    )

    result = query_service.list_users(" ali ", limit=1)

    assert [user.id for user in result] == [2]
    assert query.limit_value == 1
    assert query.ordering == (("asc", "id"),)
    assert query.filters[0] == (("is", "is_active", True),)
    assert query.filters[1][0][0] == "or"
    assert len(query.filters[1][0][1]) == 9


def test_user_id_and_active_staff_queries_preserve_contract(monkeypatch) -> None:
    rows = [SimpleNamespace(id=2), SimpleNamespace(id=1)]
    _UserModel.query = _Query(rows)
    monkeypatch.setattr(query_service, "User", _UserModel)

    ordered = query_service._users_by_ids([1, 2])
    assert [user.id for user in ordered] == [1, 2]

    active_query = _Query(rows)
    _UserModel.query = active_query
    active = query_service._active_staff_users()

    assert [user.id for user in active] == [2, 1]
    assert active_query.filters == [
        (("is", "is_active", True),),
        (("isnot", "email", None), ("ne", "email", "")),
    ]


def test_celebration_candidates_and_special_day_modes(monkeypatch) -> None:
    monkeypatch.setattr(
        query_service,
        "_active_staff_users",
        lambda: [
            SimpleNamespace(id=1, celebration_opt_out=False),
            SimpleNamespace(id=2, celebration_opt_out=True),
        ],
    )
    assert [
        user.id
        for user in query_service._cic_v40_active_staff_candidates()
    ] == [1]

    monkeypatch.setattr(
        send_context,
        "_cic_v40_setting_bool",
        lambda _key, _default: True,
    )
    monkeypatch.setattr(
        send_context,
        "_cic_v40_special_days_today",
        lambda _now=None: [{"date": "01-01"}],
    )
    monkeypatch.setattr(
        misc_context,
        "get_recipients",
        lambda: {"staff": ["manual-user"]},
    )
    monkeypatch.setattr(
        query_service,
        "get_setting",
        lambda _key, _default="": "manual",
    )

    assert query_service._cic_v40_special_day_users() == ["manual-user"]

    monkeypatch.setattr(
        query_service,
        "get_setting",
        lambda _key, _default="": "all_active",
    )
    monkeypatch.setattr(
        query_service,
        "_cic_v40_active_staff_candidates",
        lambda: ["active-user"],
    )
    assert query_service._cic_v40_special_day_users() == ["active-user"]


def test_upcoming_users_preserve_sorting_and_anniversary_filter(monkeypatch) -> None:
    users = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
    monkeypatch.setattr(
        query_service,
        "_cic_v40_active_staff_candidates",
        lambda: users,
    )
    monkeypatch.setattr(send_context, "_cic_v40_today", lambda: "today")
    monkeypatch.setattr(
        send_context,
        "_cic_v40_user_date",
        lambda user, *_attributes: f"date-{user.id}",
    )
    monkeypatch.setattr(send_context, "_cic_v40_mmdd", lambda value: value)
    monkeypatch.setattr(
        cic_context,
        "_cic_v40_days_until",
        lambda value, _today: {1: 5, 2: 1}[int(value.rsplit("-", 1)[-1])],
    )
    monkeypatch.setattr(
        celebration_service,
        "_cic_v40_service_year",
        lambda user, _today: {1: 3, 2: 0}[user.id],
    )

    birthdays = query_service._cic_v40_upcoming_users("birthday", days=30)
    assert [row["user"].id for row in birthdays] == [2, 1]

    anniversaries = query_service._cic_v40_upcoming_users(
        "anniversary",
        days=30,
    )
    assert [row["user"].id for row in anniversaries] == [1]
    assert anniversaries[0]["service_year"] == 3
