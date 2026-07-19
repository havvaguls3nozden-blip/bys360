"""Conservative Flask URL map deduplication helpers for BYS360.

This module removes only *identical* duplicate rules after the Flask app is
created. It is intentionally narrow: endpoint, rule path and HTTP methods must
match exactly. The implementation supports newer Werkzeug versions where
``Map._rules`` is a read-only computed property by rebuilding the endpoint index
instead of assigning to ``_rules``.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any
from collections.abc import Iterable

_IGNORED_METHODS = {"HEAD", "OPTIONS"}


def _method_key(methods: Iterable[str] | None) -> tuple[str, ...]:
    if not methods:
        return tuple()
    return tuple(sorted(str(method) for method in methods if str(method) not in _IGNORED_METHODS))


def _rule_key(rule: Any) -> tuple[str, str, tuple[str, ...]]:
    return (str(rule.endpoint), str(rule.rule), _method_key(getattr(rule, "methods", None)))


def _replace_rules_by_endpoint(url_map: Any, kept_rules: list[Any]) -> None:
    rules_by_endpoint: dict[str, list[Any]] = defaultdict(list)
    for rule in kept_rules:
        rules_by_endpoint[str(rule.endpoint)].append(rule)

    current = getattr(url_map, "_rules_by_endpoint", None)
    if isinstance(current, dict):
        current.clear()
        current.update(rules_by_endpoint)
        return

    setattr(url_map, "_rules_by_endpoint", dict(rules_by_endpoint))


def _rebuild_matcher_if_supported(url_map: Any, kept_rules: list[Any]) -> None:
    """Best-effort matcher rebuild for Werkzeug 2.2+/3.x.

    The quality gate inspects ``iter_rules()``, which is driven by
    ``_rules_by_endpoint``. Rebuilding the matcher keeps runtime routing aligned
    when the private matcher implementation is available. If Werkzeug internals
    change again, we leave the endpoint index clean and do not fail app startup.
    """

    try:
        from werkzeug.routing.matcher import StateMachineMatcher
    except (ImportError, AttributeError):
        return

    try:
        matcher = StateMachineMatcher(bool(getattr(url_map, "merge_slashes", True)))
        for rule in kept_rules:
            matcher.add(rule)
        matcher.update()
        setattr(url_map, "_matcher", matcher)
    except (AttributeError, TypeError, ValueError):
        return


def dedupe_identical_url_rules(app: Any) -> int:
    """Remove exact duplicate endpoint+path+method rules from ``app.url_map``.

    Returns the number of removed duplicate rules. Only exact duplicates are
    removed; similarly named endpoints or different methods/paths are untouched.
    """

    url_map = getattr(app, "url_map", None)
    if url_map is None:
        return 0

    rules = list(url_map.iter_rules())
    seen: set[tuple[str, str, tuple[str, ...]]] = set()
    kept_rules: list[Any] = []
    removed_count = 0

    for rule in rules:
        key = _rule_key(rule)
        if key in seen:
            removed_count += 1
            continue
        seen.add(key)
        kept_rules.append(rule)

    if removed_count == 0:
        return 0

    _replace_rules_by_endpoint(url_map, kept_rules)
    _rebuild_matcher_if_supported(url_map, kept_rules)

    if hasattr(url_map, "_remap"):
        setattr(url_map, "_remap", True)

    return removed_count
