from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from app.core.datetime_utils import utc_now

try:
    from .live_scope import ANALYTICS_SURFACE_KEYS, get_analytics_surfaces
    from .summary_pipeline import build_analytics_safe_summary_card
except ImportError:  # python -S gate bağımsız çalıştırması
    from analytics_center.live_scope import (  # type: ignore[no-redef]
        ANALYTICS_SURFACE_KEYS,
        get_analytics_surfaces,
    )
    from analytics_center.summary_pipeline import (  # type: ignore[no-redef]
        build_analytics_safe_summary_card,
    )

"""Karar Destek Dashboard veri yüzeyi servisleri.

Faz 3 notu:
- Bu dosya veritabanına yazmaz; commit yapmaz.
- Route/template davranışını değiştirmez.
- Dış AI servisine istek yapmaz; external_ai_call her zaman False sözleşmesiyle çalışır.
- Açık metinler dashboard yüzeyine çıkmadan önce güvenli özet/maskeleme hattından geçirilir.
"""


@dataclass(frozen=True)
class DashboardMetricCard:
    key: str
    title: str
    value: int | float | str
    unit: str = "adet"
    status: str = "neutral"
    description: str = ""
    source_domain: str = "live_core"
    visibility_scope: str = "manager"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DashboardSignalCard:
    key: str
    title: str
    summary: str
    severity: str = "info"
    source_domain: str = "live_core"
    action_hint: str = "İnsan onayıyla değerlendiriniz."
    visibility_scope: str = "manager"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


STATUS_VALUES = {"good", "warning", "danger", "neutral", "info"}
SEVERITY_VALUES = {"low", "medium", "high", "critical", "info"}


def coerce_dashboard_number(value: Any, default: int = 0) -> int | float:
    """Dashboard kartları için güvenli sayı dönüştürür."""
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return value
    try:
        text = str(value).strip().replace("%", "").replace(",", ".")
        number = float(text)
        return int(number) if number.is_integer() else number
    except Exception:
        return default


def normalize_dashboard_status(status: Any) -> str:
    value = str(status or "neutral").strip().lower()
    return value if value in STATUS_VALUES else "neutral"


def normalize_dashboard_severity(severity: Any) -> str:
    value = str(severity or "info").strip().lower()
    return value if value in SEVERITY_VALUES else "info"


def build_dashboard_metric_card(
    *,
    key: str,
    title: str,
    value: Any,
    unit: str = "adet",
    status: str = "neutral",
    description: str = "",
    source_domain: str = "live_core",
    visibility_scope: str = "manager",
) -> dict[str, Any]:
    """Tek dashboard KPI kartı üretir."""
    return DashboardMetricCard(
        key=str(key or "metric").strip() or "metric",
        title=str(title or "Gösterge").strip() or "Gösterge",
        value=coerce_dashboard_number(value, default=0),
        unit=str(unit or "adet"),
        status=normalize_dashboard_status(status),
        description=str(description or ""),
        source_domain=str(source_domain or "live_core"),
        visibility_scope=str(visibility_scope or "manager"),
    ).to_dict()


def build_dashboard_signal_card(
    *,
    key: str,
    title: str,
    summary: Any,
    severity: str = "info",
    source_domain: str = "live_core",
    action_hint: str = "İnsan onayıyla değerlendiriniz.",
    visibility_scope: str = "manager",
) -> dict[str, Any]:
    """AI karar destek sinyal kartı üretir."""
    safe_summary = build_analytics_safe_summary_card(
        "executive_overview",
        [{"summary": str(summary or "")}],
        module_type=source_domain,
    )
    return DashboardSignalCard(
        key=str(key or "signal").strip() or "signal",
        title=str(title or "Karar Destek Sinyali").strip() or "Karar Destek Sinyali",
        summary=str(safe_summary.get("summary_text") or "Güvenli özet hazırlanamadı."),
        severity=normalize_dashboard_severity(severity),
        source_domain=str(source_domain or "live_core"),
        action_hint=str(action_hint or "İnsan onayıyla değerlendiriniz."),
        visibility_scope=str(visibility_scope or "manager"),
    ).to_dict()


def build_dashboard_source_health_cards(source_counts: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Canlı veri alanlarının dashboard kaynak sağlık kartlarını döndürür."""
    counts = source_counts or {}
    cards: list[dict[str, Any]] = []
    for surface in get_analytics_surfaces():
        domain = str(surface.get("source_domain") or surface.get("key") or "live_core")
        count = coerce_dashboard_number(counts.get(domain, counts.get(str(surface.get("key") or ""), 0)))
        cards.append(
            build_dashboard_metric_card(
                key=f"source_{surface.get('key')}",
                title=str(surface.get("label") or surface.get("key") or "Veri kaynağı"),
                value=count,
                unit="kayıt",
                status="good" if count else "neutral",
                description=str(surface.get("safe_default") or "Yetkiye bağlı güvenli özet."),
                source_domain=domain,
            )
        )
    return cards


def build_default_dashboard_metrics(raw_metrics: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Karar destek dashboard başlangıç metriklerini üretir."""
    data = raw_metrics or {}
    return [
        build_dashboard_metric_card(key="personnel_total", title="Personel görünümü", value=data.get("personnel_total", 0), unit="kişi", status="info", description="Personel ve organizasyon sinyallerinin toplu görünümü.", source_domain="personnel"),
        build_dashboard_metric_card(key="performance_pending", title="Performans takip sinyali", value=data.get("performance_pending", 0), unit="işlem", status="warning" if coerce_dashboard_number(data.get("performance_pending", 0)) else "good", description="Yayın, görev veya değerlendirme bekleyen kayıtlar için yüzey.", source_domain="performance"),
        build_dashboard_metric_card(key="survey_response_rate", title="Anket / geri bildirim oranı", value=data.get("survey_response_rate", 0), unit="%", status="info", description="Anket, nabız ve geri bildirim katılım özeti.", source_domain="survey_feedback"),
        build_dashboard_metric_card(key="support_open_items", title="Destek ve iletişim yükü", value=data.get("support_open_items", 0), unit="kayıt", status="warning" if coerce_dashboard_number(data.get("support_open_items", 0)) else "good", description="Destek, mesajlaşma ve yoğunluk sinyallerinin toplu izlenmesi.", source_domain="communication_support"),
    ]


def build_default_dashboard_signals(raw_signals: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Karar destek dashboard için güvenli sinyal kartları üretir."""
    signals = raw_signals or [
        {"key": "publication_readiness", "title": "Yayın öncesi kontrol", "summary": "Performans sonuçları yayınlanmadan önce İK/Admin kontrolü korunmalıdır.", "severity": "medium", "source_domain": "performance"},
        {"key": "data_minimization", "title": "KVKK veri minimizasyonu", "summary": "Dashboard yüzeyi toplu ve maskelenmiş özet göstermelidir; açık kişisel veri rapora taşınmamalıdır.", "severity": "info", "source_domain": "live_core"},
    ]
    return [build_dashboard_signal_card(**signal) for signal in signals]


def build_ai_decision_dashboard_surface(
    *,
    raw_metrics: dict[str, Any] | None = None,
    raw_signals: list[dict[str, Any]] | None = None,
    source_counts: dict[str, Any] | None = None,
    user_scope: str = "manager",
) -> dict[str, Any]:
    """AI Karar Destek dashboard veri yüzeyi üretir; kayıt oluşturmaz, commit yapmaz."""
    metrics = build_default_dashboard_metrics(raw_metrics)
    signals = build_default_dashboard_signals(raw_signals)
    source_health = build_dashboard_source_health_cards(source_counts)
    return {
        "module": "ai_decision_analytics_center",
        "phase": "faz3_dashboard_data_surface",
        "generated_at_utc": utc_now().isoformat(timespec="seconds"),
        "behavior_change": False,
        "database_change": False,
        "route_change": False,
        "external_ai_call": False,
        "user_scope": str(user_scope or "manager"),
        "surface_keys": list(ANALYTICS_SURFACE_KEYS),
        "metric_cards": metrics,
        "signal_cards": signals,
        "source_health_cards": source_health,
        "counts": {"metric_cards": len(metrics), "signal_cards": len(signals), "source_health_cards": len(source_health)},
        "safe_visibility_note": "Yetkiye bağlı, toplu ve maskelenmiş karar destek yüzeyi.",
    }


def build_ai_decision_dashboard_context(
    raw_metrics: dict[str, Any] | None = None,
    raw_signals: list[dict[str, Any]] | None = None,
    source_counts: dict[str, Any] | None = None,
    user_scope: str = "manager",
) -> dict[str, Any]:
    """Template/route entegrasyonu için hazır dashboard context döndürür."""
    surface = build_ai_decision_dashboard_surface(raw_metrics=raw_metrics, raw_signals=raw_signals, source_counts=source_counts, user_scope=user_scope)
    return {
        "ai_decision_dashboard": surface,
        "ai_decision_dashboard_ready": True,
        "ai_decision_dashboard_safe_mode": True,
        "ai_decision_dashboard_generated_at": surface["generated_at_utc"],
    }


def build_ai_decision_dashboard_readiness_summary() -> dict[str, Any]:
    surface = build_ai_decision_dashboard_surface(
        raw_metrics={"personnel_total": 12, "performance_pending": 3, "survey_response_rate": 80, "support_open_items": 2},
        source_counts={"personnel": 12, "performance": 3, "survey_feedback": 5, "communication_support": 2},
    )
    return {
        "ok": surface["counts"]["metric_cards"] >= 4 and surface["counts"]["signal_cards"] >= 2,
        "phase": surface["phase"],
        "surface_keys": surface["surface_keys"],
        "counts": surface["counts"],
        "external_ai_call": surface["external_ai_call"],
        "message": "Karar Destek Dashboard veri yüzeyi hazır.",
        "next_phase": "Faz 4 — Personel / performans içgörü motoru",
    }
