"""SCORE 100 duplicate endpoint contract.

This test must run in the default CI path. It intentionally has no custom skip
marker and no environment flag gate.
"""

from __future__ import annotations

from collections import Counter

import pytest

pytestmark = pytest.mark.ci_safe


def _normalize_methods(methods):
    return tuple(sorted(set(methods or set()) - {"HEAD", "OPTIONS"}))


def test_app_factory_registers_routes_without_duplicate_endpoints():
    from app import create_app

    app = create_app()
    duplicates = [
        {"endpoint": endpoint, "rule": rule, "methods": methods, "count": count}
        for (endpoint, rule, methods), count in Counter(
            (rule.endpoint, rule.rule, _normalize_methods(rule.methods))
            for rule in app.url_map.iter_rules()
        ).items()
        if count > 1
    ]

    assert not duplicates, duplicates[:20]
