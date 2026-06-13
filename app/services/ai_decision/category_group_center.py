
"""BYS360 AI Karar Destek Faz 2 kategori/grup analiz merkezi.

Bu servis kişi detayı döndürmez. Personel kategorilerini, performans
sonuçlarını ve yayın durumunu yalnızca grup/kategori kırılımında özetler.
BYS360_AI_DECISION_FAZ2_CATEGORY_GROUP_CENTER
"""
from __future__ import annotations
from app import db

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping


DEFAULT_CATEGORY_LABELS: tuple[str, ...] = (
    "Güvenlik",
    "Temizlik",
    "İdari Personel",
    "Teknik Personel",
    "Deneme Süreli Personel",
    "Diğer",
)

CATEGORY_PRIVACY_NOTE = (
    "Kategori ve grup analizleri kişi detayı göstermez; yalnızca yetkili kapsamda "
    "toplu sayı, ortalama ve dikkat sinyali üretir."
)

_LOW_SCORE_LIMIT = 70.0
_HIGH_SCORE_LIMIT = 90.0


@dataclass
class CategoryAggregate:
    label: str
    employee_count: int = 0
    evaluation_count: int = 0
    published_count: int = 0
    unpublished_count: int = 0
    low_score_count: int = 0
    high_score_count: int = 0
    score_total: float = 0.0
    scores: list[float] = field(default_factory=list)

    @property
    def average_score(self) -> float | None:
        if not self.scores:
            return None
        return round(sum(self.scores) / len(self.scores), 2)

    @property
    def low_score_rate(self) -> float:
        if not self.evaluation_count:
            return 0.0
        return round(self.low_score_count / self.evaluation_count, 4)

    @property
    def completion_rate(self) -> float:
        if not self.evaluation_count:
            return 0.0
        return round(self.published_count / self.evaluation_count, 4)

    def to_dict(self) -> dict[str, Any]:
        return {
            "category_label": self.label,
            "employee_count": self.employee_count,
            "evaluation_count": self.evaluation_count,
            "published_count": self.published_count,
            "unpublished_count": self.unpublished_count,
            "low_score_count": self.low_score_count,
            "high_score_count": self.high_score_count,
            "average_score": self.average_score,
            "low_score_rate": self.low_score_rate,
            "completion_rate": self.completion_rate,
        }


def normalize_category_label(value: Any) -> str:
    """Kategori adını kurumsal sözlüğe göre normalize eder."""
    text = str(value or "").strip()
    if not text:
        return "Diğer"
    aliases = {
        "guvenlik": "Güvenlik",
        "güvenlik": "Güvenlik",
        "security": "Güvenlik",
        "temizlik": "Temizlik",
        "cleaning": "Temizlik",
        "idari": "İdari Personel",
        "idari personel": "İdari Personel",
        "ıdari personel": "İdari Personel",
        "administrative": "İdari Personel",
        "teknik": "Teknik Personel",
        "teknik personel": "Teknik Personel",
        "technical": "Teknik Personel",
        "deneme": "Deneme Süreli Personel",
        "deneme sureli personel": "Deneme Süreli Personel",
        "deneme süreli personel": "Deneme Süreli Personel",
        "probation": "Deneme Süreli Personel",
        "diger": "Diğer",
        "diğer": "Diğer",
        "other": "Diğer",
    }
    lookup = {item.casefold(): item for item in DEFAULT_CATEGORY_LABELS}
    return aliases.get(text.casefold(), lookup.get(text.casefold(), text[:80]))


def slugify_category_label(value: Any) -> str:
    import re

    text = normalize_category_label(value).lower()
    tr_map = {"ğ": "g", "ü": "u", "ş": "s", "ı": "i", "ö": "o", "ç": "c", "İ": "i"}
    for old, new in tr_map.items():
        text = text.replace(old, new)
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_") or "diger"


def _user_category_label(user: Any) -> str:
    rel = getattr(user, "performance_category", None)
    if rel is not None and getattr(rel, "name", None):
        return normalize_category_label(getattr(rel, "name"))
    return normalize_category_label(getattr(user, "personnel_category", None))


def _score_value(evaluation: Any) -> float | None:
    for field_name in ("final_total_100", "final_score", "score_100", "total_score"):
        value = getattr(evaluation, field_name, None)
        if value not in (None, ""):
            try:
                return float(value)
            except (TypeError, ValueError):
                __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/ai_decision/category_group_center.py:131)")
                continue
    return None


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value in (None, ""):
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "evet", "aktif", "published", "yayında", "yayinda"}


def _period_label(period: Any | None) -> str | None:
    if period is None:
        return None
    return str(getattr(period, "title", None) or getattr(period, "name", None) or f"Dönem #{getattr(period, 'id', '')}").strip() or None


def _blank_aggregates() -> dict[str, CategoryAggregate]:
    return {label: CategoryAggregate(label=label) for label in DEFAULT_CATEGORY_LABELS}


def collect_category_group_aggregates(
    *,
    period_id: int | None = None,
    include_unpublished: bool = True,
    only_active_users: bool = True,
) -> dict[str, Any]:
    """Kategori bazlı toplu performans görünümü üretir.

    Kişi ad-soyad, sicil, e-posta veya tekil puan listesi döndürmez.
    """
    from app.models import PerformanceEvaluation, PerformancePeriod, User

    aggregates = _blank_aggregates()
    users_query = User.query
    if only_active_users and hasattr(User, "is_active"):
        users_query = users_query.filter(User.is_active.is_(True))
    users = users_query.all()
    user_category_map: dict[int, str] = {}
    for user in users:
        label = _user_category_label(user)
        aggregates.setdefault(label, CategoryAggregate(label=label)).employee_count += 1
        user_category_map[int(getattr(user, "id", 0) or 0)] = label

    period = None
    evaluation_query = PerformanceEvaluation.query
    if period_id:
        evaluation_query = evaluation_query.filter(PerformanceEvaluation.period_id == int(period_id))
        period = db.session.get(PerformancePeriod, int(period_id))
    evaluations = evaluation_query.all()

    for evaluation in evaluations:
        employee_id = int(getattr(evaluation, "employee_id", 0) or 0)
        employee = getattr(evaluation, "employee", None)
        label = user_category_map.get(employee_id) or (_user_category_label(employee) if employee is not None else "Diğer")
        aggregate = aggregates.setdefault(label, CategoryAggregate(label=label))
        score = _score_value(evaluation)
        is_published = _safe_bool(getattr(evaluation, "is_published_to_employee", False))
        if not include_unpublished and not is_published:
            continue
        aggregate.evaluation_count += 1
        if is_published:
            aggregate.published_count += 1
        else:
            aggregate.unpublished_count += 1
        if score is not None and score > 0:
            aggregate.scores.append(score)
            aggregate.score_total += score
            if score < _LOW_SCORE_LIMIT:
                aggregate.low_score_count += 1
            if score > _HIGH_SCORE_LIMIT:
                aggregate.high_score_count += 1

    category_rows = [aggregates[label].to_dict() for label in sorted(aggregates, key=lambda item: (item not in DEFAULT_CATEGORY_LABELS, DEFAULT_CATEGORY_LABELS.index(item) if item in DEFAULT_CATEGORY_LABELS else 999, item))]
    summary = {
        "category_count": len(category_rows),
        "employee_count": sum(row["employee_count"] for row in category_rows),
        "evaluation_count": sum(row["evaluation_count"] for row in category_rows),
        "published_count": sum(row["published_count"] for row in category_rows),
        "unpublished_count": sum(row["unpublished_count"] for row in category_rows),
        "low_score_count": sum(row["low_score_count"] for row in category_rows),
        "high_score_count": sum(row["high_score_count"] for row in category_rows),
    }
    scored = [row["average_score"] for row in category_rows if row["average_score"] is not None]
    summary["general_average_score"] = round(sum(scored) / len(scored), 2) if scored else None
    return {
        "period_id": period_id,
        "period_label": _period_label(period),
        "summary": summary,
        "categories": category_rows,
        "privacy_note": CATEGORY_PRIVACY_NOTE,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def build_category_group_signals(aggregate_payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    summary = dict(aggregate_payload.get("summary") or {})
    categories = list(aggregate_payload.get("categories") or [])

    if summary.get("employee_count", 0) and not summary.get("evaluation_count", 0):
        signals.append({
            "code": "category_evaluation_missing",
            "title": "Kategori performans verisi henüz oluşmamış",
            "body": "Personel kategori kırılımı hazır; ancak seçilen kapsamda değerlendirme sonucu bulunmuyor.",
            "severity": "warning",
            "action": "Dönem kapsamını ve görev üretimini kontrol edin.",
        })

    for row in categories:
        label = row.get("category_label") or "Diğer"
        evaluation_count = int(row.get("evaluation_count") or 0)
        employee_count = int(row.get("employee_count") or 0)
        low_score_count = int(row.get("low_score_count") or 0)
        unpublished_count = int(row.get("unpublished_count") or 0)
        low_rate = float(row.get("low_score_rate") or 0)
        average_score = row.get("average_score")

        if employee_count and not evaluation_count:
            signals.append({
                "code": "category_scope_without_evaluation",
                "title": f"{label} kategorisinde değerlendirme bekleniyor",
                "body": "Bu kategoride aktif personel var ancak seçilen kapsamda performans değerlendirmesi görünmüyor.",
                "severity": "info",
                "action": "Kategori kapsamı ve dönem görev üretimi karşılaştırılmalı.",
            })
        if evaluation_count and low_score_count and low_rate >= 0.25:
            signals.append({
                "code": "category_low_score_concentration",
                "title": f"{label} kategorisinde düşük performans yoğunluğu",
                "body": f"Bu kategoride {low_score_count} düşük performans sonucu var; oran %{round(low_rate * 100, 1)}.",
                "severity": "danger",
                "action": "Başkan/Üst Onay ve gelişim önerisi kayıtları birlikte kontrol edilmeli.",
            })
        if evaluation_count and unpublished_count:
            signals.append({
                "code": "category_publish_pending",
                "title": f"{label} kategorisinde yayın bekleyen sonuç",
                "body": f"Bu kategoride {unpublished_count} değerlendirme sonucu henüz personele açılmamış görünüyor.",
                "severity": "warning",
                "action": "Yayın ön onayı, düşük performans kilidi ve Admin/İK final yayını kontrol edilmeli.",
            })
        if average_score is not None and float(average_score) > _HIGH_SCORE_LIMIT:
            signals.append({
                "code": "category_high_success",
                "title": f"{label} kategorisinde yüksek başarı görünümü",
                "body": f"Kategori ortalaması {average_score}; güçlü uygulamalar rapor notuna dönüştürülebilir.",
                "severity": "success",
                "action": "Güçlü yönler ve iyi uygulamalar yönetici raporunda öne alınabilir.",
            })

    if not signals:
        signals.append({
            "code": "category_group_stable",
            "title": "Kategori görünümü dengeli",
            "body": "Seçilen kapsamda kategori bazlı kritik düşük performans yoğunluğu veya yayın riski görünmüyor.",
            "severity": "success",
            "action": "Dönem tamamlanana kadar kategori ortalamaları düzenli izlenebilir.",
        })
    return signals


def build_category_group_decision_payload(
    *,
    period_id: int | None = None,
    include_unpublished: bool = True,
) -> dict[str, Any]:
    aggregates = collect_category_group_aggregates(
        period_id=period_id,
        include_unpublished=include_unpublished,
    )
    signals = build_category_group_signals(aggregates)
    severity_order = {"danger": 4, "warning": 3, "info": 2, "success": 1}
    top_signal = max(signals, key=lambda item: severity_order.get(str(item.get("severity")), 0)) if signals else None
    return {
        "module_type": "performance",
        "feature_type": "category_group_decision_support",
        "target_table": "performance_periods" if period_id else "performance_category_groups",
        "target_id": int(period_id or 0),
        "title": "Personel Kategori ve Grup Karar Desteği",
        "summary": (top_signal or {}).get("title") or "Kategori ve grup görünümü hazır.",
        "period_id": period_id,
        "period_label": aggregates.get("period_label"),
        "data_scope": "category_group_aggregate_only",
        "privacy_note": CATEGORY_PRIVACY_NOTE,
        "aggregates": aggregates,
        "signals": signals,
        "recommendations": [
            {
                "title": signal.get("title"),
                "body": signal.get("action") or signal.get("body"),
                "severity": signal.get("severity", "info"),
                "recommendation_type": "category_group_signal",
            }
            for signal in signals
            if signal.get("severity") in {"danger", "warning"}
        ],
        "contracts": [
            "Varsayılan personel kategorileri tek sözlükten yönetilir.",
            "Kategori ortalaması kişi detayı göstermeden hesaplanır.",
            "Yetkisiz kullanıcıya personel bazlı puan listesi verilmez.",
            "Karar Destek Merkezi nihai karar üretmez; dikkat sinyali üretir.",
        ],
        "marker": "BYS360_AI_DECISION_FAZ2_CATEGORY_GROUP_PAYLOAD_OK",
    }
