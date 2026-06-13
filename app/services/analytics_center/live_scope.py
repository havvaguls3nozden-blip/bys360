
"""Analiz Merkezi canlı kapsam ve veri yüzeyi sözleşmesi."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Final


@dataclass(frozen=True)
class AnalyticsSurface:
    key: str
    label: str
    source_domain: str
    output_types: tuple[str, ...]
    safe_default: str
    export_policy: str = "authorized_export_only"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


ANALYTICS_SURFACES: Final[tuple[AnalyticsSurface, ...]] = (
    AnalyticsSurface(
        key="executive_overview",
        label="Yönetici Genel Bakış",
        source_domain="live_core",
        output_types=("kpi_card", "trend_summary", "risk_badge", "action_note"),
        safe_default="Toplu veri ve anonimleştirilmiş özet gösterilir.",
    ),
    AnalyticsSurface(
        key="performance_insights",
        label="Performans İçgörüleri",
        source_domain="performance",
        output_types=("period_comparison", "publication_status", "assignment_risk", "score_distribution"),
        safe_default="Personel görünürlüğü yayın ve yetki kapısına bağlıdır.",
    ),
    AnalyticsSurface(
        key="personnel_structure",
        label="Personel ve Organizasyon Yapısı",
        source_domain="personnel",
        output_types=("unit_distribution", "missing_manager_signal", "role_distribution", "org_history_signal"),
        safe_default="Kimlik alanları maskelenir; toplu sayısal özet önceliklidir.",
    ),
    AnalyticsSurface(
        key="survey_feedback_pulse",
        label="Anket / Geri Bildirim / Nabız",
        source_domain="survey_feedback",
        output_types=("theme_summary", "sentiment_hint", "response_rate", "priority_signal"),
        safe_default="Açık uçlu yanıtlar prompt öncesi maskelenir.",
    ),
    AnalyticsSurface(
        key="communication_support_signal",
        label="İletişim ve Destek Sinyali",
        source_domain="communication_support",
        output_types=("ticket_volume", "topic_cluster", "message_load", "support_sla_hint"),
        safe_default="Mesaj içeriği yerine konu/yoğunluk özeti tercih edilir.",
    ),
    AnalyticsSurface(
        key="excel_preview",
        label="Excel Ön İzleme",
        source_domain="uploaded_analysis_file",
        output_types=("schema_preview", "column_quality", "chart_suggestion", "safe_import_warning"),
        safe_default="Dosya verisi kalıcı yazılmadan önce ön izleme ve maskeleme yapılır.",
    ),
)

ANALYTICS_SURFACE_KEYS: Final[tuple[str, ...]] = tuple(surface.key for surface in ANALYTICS_SURFACES)


def get_analytics_surfaces() -> list[dict[str, object]]:
    return [surface.to_dict() for surface in ANALYTICS_SURFACES]


def build_analytics_surface_summary() -> dict[str, object]:
    return {
        "surface_count": len(ANALYTICS_SURFACES),
        "surfaces": get_analytics_surfaces(),
        "safe_mode": True,
        "database_change": False,
        "route_change": False,
        "next_phase": "Faz 1 — AI log / request / redaction servis köprüsü",
    }
