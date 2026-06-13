"""BYS360 Core Refactor Faz 9 route registry contract helpers.

This module is intentionally read-only. It inspects Flask's URL map after
application creation and produces deterministic route registry data for release
checks. It must not register routes, touch the database, or mutate app config.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
from typing import Any, Iterable

IGNORED_METHODS = {"HEAD", "OPTIONS"}


@dataclass(frozen=True)
class RouteRecord:
    """Stable, serializable representation of a Flask route."""

    endpoint: str
    rule: str
    methods: tuple[str, ...]
    module: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["methods"] = list(self.methods)
        return data


@dataclass(frozen=True)
class RouteConflict:
    """Represents a route-method collision across different endpoints."""

    key: str
    endpoints: tuple[str, ...]
    rule: str
    method: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["endpoints"] = list(self.endpoints)
        return data


def normalize_methods(methods: Iterable[str] | None) -> tuple[str, ...]:
    """Return deterministic route methods, excluding Flask auto methods."""

    clean = {str(method).upper() for method in (methods or []) if str(method).upper() not in IGNORED_METHODS}
    return tuple(sorted(clean))


def build_route_registry(app: Any) -> list[RouteRecord]:
    """Build a deterministic route registry from a Flask app URL map."""

    records: list[RouteRecord] = []
    for rule in sorted(app.url_map.iter_rules(), key=lambda item: (str(item.rule), str(item.endpoint))):
        endpoint = str(rule.endpoint)
        view_func = app.view_functions.get(endpoint)
        module = getattr(view_func, "__module__", "") if view_func else ""
        records.append(
            RouteRecord(
                endpoint=endpoint,
                rule=str(rule.rule),
                methods=normalize_methods(getattr(rule, "methods", None)),
                module=str(module or ""),
            )
        )
    return records


def find_route_conflicts(records: Iterable[RouteRecord]) -> list[RouteConflict]:
    """Find same rule + same HTTP method served by more than one endpoint."""

    seen: dict[tuple[str, str], set[str]] = {}
    for record in records:
        for method in record.methods:
            key = (record.rule, method)
            seen.setdefault(key, set()).add(record.endpoint)

    conflicts: list[RouteConflict] = []
    for (rule, method), endpoints in sorted(seen.items()):
        if len(endpoints) > 1:
            conflicts.append(
                RouteConflict(
                    key=f"{method} {rule}",
                    endpoints=tuple(sorted(endpoints)),
                    rule=rule,
                    method=method,
                )
            )
    return conflicts


def summarize_route_registry(records: Iterable[RouteRecord], conflicts: Iterable[RouteConflict]) -> dict[str, Any]:
    records_list = list(records)
    conflicts_list = list(conflicts)
    methods: dict[str, int] = {}
    modules: dict[str, int] = {}
    for record in records_list:
        modules[record.module or "unknown"] = modules.get(record.module or "unknown", 0) + 1
        for method in record.methods:
            methods[method] = methods.get(method, 0) + 1
    return {
        "route_count": len(records_list),
        "conflict_count": len(conflicts_list),
        "methods": dict(sorted(methods.items())),
        "top_modules": dict(sorted(modules.items(), key=lambda item: (-item[1], item[0]))[:20]),
    }


def write_route_registry_report(
    records: Iterable[RouteRecord],
    conflicts: Iterable[RouteConflict],
    json_path: str | Path,
    markdown_path: str | Path,
) -> dict[str, Any]:
    """Write JSON and Markdown reports for release evidence."""

    records_list = list(records)
    conflicts_list = list(conflicts)
    summary = summarize_route_registry(records_list, conflicts_list)
    payload = {
        "version": "2026-04-21-core-refactor-faz9-route-registry",
        "summary": summary,
        "conflicts": [conflict.to_dict() for conflict in conflicts_list],
        "routes": [record.to_dict() for record in records_list],
    }

    json_file = Path(json_path)
    md_file = Path(markdown_path)
    json_file.parent.mkdir(parents=True, exist_ok=True)
    md_file.parent.mkdir(parents=True, exist_ok=True)
    json_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 Core Refactor Faz 9 Route Registry",
        "",
        f"- Route count: {summary['route_count']}",
        f"- Conflict count: {summary['conflict_count']}",
        "",
        "## HTTP method summary",
        "",
    ]
    for method, count in summary["methods"].items():
        lines.append(f"- {method}: {count}")
    lines.extend(["", "## Conflicts", ""])
    if conflicts_list:
        for conflict in conflicts_list:
            lines.append(f"- {conflict.key}: {', '.join(conflict.endpoints)}")
    else:
        lines.append("- No route-method conflicts detected.")
    lines.extend(["", "## Routes", ""])
    for record in records_list:
        methods_text = ",".join(record.methods) or "-"
        lines.append(f"- `{methods_text}` `{record.rule}` → `{record.endpoint}` ({record.module})")
    md_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return payload
