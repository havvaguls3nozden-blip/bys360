
"""Analiz Merkezi güvenli özet pipeline köprüsü.

Faz 2 canlı davranış değiştirmez. Veri kaydetmez, external AI servisine istek
atmaz ve yalnızca dashboard/analiz fazları için güvenli özet hazırlığı yapar.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from typing import Any

try:
    from app.services.ai_decision.summary_cache import (
        DEFAULT_PROMPT_VERSION,
        build_ai_safe_summary_text,
        build_ai_source_hash,
        build_ai_summary_cache_lookup,
        build_ai_summary_cache_payload,
    )
except ImportError:
    from ai_decision.summary_cache import (
        DEFAULT_PROMPT_VERSION,
        build_ai_safe_summary_text,
        build_ai_source_hash,
        build_ai_summary_cache_lookup,
        build_ai_summary_cache_payload,
    )
from .live_scope import (
    ANALYTICS_SURFACE_KEYS,
    build_analytics_surface_summary,
    get_analytics_surfaces,
)


@dataclass(frozen=True)
class AnalyticsSummarySourceBundle:
    surface_key: str
    module_type: str
    source_count: int
    source_hash: str
    safe_default: str
    output_types: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["output_types"] = list(self.output_types)
        return data


def _clean(value: Any, fallback: str = "") -> str:
    text = str(value or "").strip()
    return text or fallback


def _coerce_rows(rows: Iterable[Any] | None) -> list[Any]:
    if rows is None:
        return []
    if isinstance(rows, list):
        return rows
    return list(rows)


def get_analytics_surface(surface_key: str) -> dict[str, Any] | None:
    wanted = _clean(surface_key).lower()
    for surface in get_analytics_surfaces():
        if str(surface.get("key", "")).lower() == wanted:
            return surface
    return None


def build_analytics_summary_source_bundle(
    surface_key: str,
    rows: Iterable[Any] | None,
    *,
    module_type: str | None = None,
) -> dict[str, Any]:
    surface = get_analytics_surface(surface_key) or {}
    row_list = _coerce_rows(rows)
    source_payload = {
        "surface_key": surface_key,
        "rows": row_list,
        "output_types": surface.get("output_types", []),
    }
    return AnalyticsSummarySourceBundle(
        surface_key=_clean(surface.get("key"), surface_key),
        module_type=_clean(module_type, _clean(surface.get("source_domain"), "analytics")),
        source_count=len(row_list),
        source_hash=build_ai_source_hash(source_payload),
        safe_default=_clean(surface.get("safe_default"), "Toplu ve maskelenmiş özet gösterilir."),
        output_types=tuple(surface.get("output_types", ())),
    ).to_dict()


def build_analytics_safe_summary_card(
    surface_key: str,
    rows: Iterable[Any] | None,
    *,
    redaction_rules: Iterable[Any] | None = None,
    module_type: str | None = None,
    max_chars: int = 900,
) -> dict[str, Any]:
    row_list = _coerce_rows(rows)
    bundle = build_analytics_summary_source_bundle(surface_key, row_list, module_type=module_type)
    summary = build_ai_safe_summary_text(
        row_list,
        redaction_rules=redaction_rules or [],
        module_type=str(bundle["module_type"]),
        max_chars=max_chars,
    )
    return {
        "surface_key": bundle["surface_key"],
        "module_type": bundle["module_type"],
        "source_count": bundle["source_count"],
        "source_hash": bundle["source_hash"],
        "summary_text": summary["summary_text"] if row_list else bundle["safe_default"],
        "was_masked": bool(summary["was_masked"]),
        "output_types": bundle["output_types"],
        "safe_default": bundle["safe_default"],
        "behavior_change": False,
    }


def build_analytics_summary_cache_plan(
    surface_key: str,
    rows: Iterable[Any] | None,
    *,
    target_id: int | None = None,
    summary_kind: str = "analytics_surface_summary",
    prompt_version: str = DEFAULT_PROMPT_VERSION,
    redaction_rules: Iterable[Any] | None = None,
) -> dict[str, Any]:
    row_list = _coerce_rows(rows)
    surface = get_analytics_surface(surface_key) or {}
    module_type = _clean(surface.get("source_domain"), "analytics")
    target_table = f"analytics:{_clean(surface_key, 'general')}"
    cache_payload = build_ai_summary_cache_payload(
        module_type=module_type,
        target_table=target_table,
        target_id=target_id,
        summary_kind=summary_kind,
        source_data=row_list,
        prompt_version=prompt_version,
        redaction_rules=redaction_rules or [],
        visibility_scope="internal",
    )
    lookup = build_ai_summary_cache_lookup(
        module_type=module_type,
        target_table=target_table,
        target_id=target_id,
        summary_kind=summary_kind,
        source_data=row_list,
        prompt_version=prompt_version,
    )
    return {
        "surface_key": _clean(surface_key, "general"),
        "cache_payload": cache_payload,
        "cache_lookup": lookup,
        "write_policy": "authorized_service_may_persist",
        "behavior_change": False,
    }


def build_analytics_summary_pipeline_summary() -> dict[str, Any]:
    return {
        "ok": len(ANALYTICS_SURFACE_KEYS) >= 6,
        "surface_summary": build_analytics_surface_summary(),
        "pipeline_files": [
            "app/services/ai_decision/summary_cache.py",
            "app/services/analytics_center/summary_pipeline.py",
        ],
        "external_ai_call": False,
        "database_change": False,
        "next_phase": "Faz 3 — Karar destek dashboard veri yüzeyi",
    }
