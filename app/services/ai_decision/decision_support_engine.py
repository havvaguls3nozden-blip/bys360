
"""BYS360 AI Karar Destek Faz 1 karar motoru.

Bu motor dış yapay zekâ çağrısı yapmaz. Performans, yayın ve açıklama
kurallarını deterministik biçimde değerlendirir; çıktı yalnızca karar destek
notudur. Nihai idari karar insandadır.

BYS360_AI_DECISION_FAZ1_DECISION_ENGINE
"""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DecisionPolicy:
    """Karar motorunun ayarlanabilir politika sözleşmesi."""

    low_score_threshold: float = 70.0
    high_score_threshold: float = 90.0
    require_general_comment_below_low: bool = True
    require_general_comment_above_high: bool = True
    require_comment_for_score_1: bool = True
    require_comment_for_score_5: bool = True
    low_score_requires_upper_approval: bool = True
    publish_lock_for_low_score: bool = True
    manager_score_variance_threshold: float = 3.0
    enabled: bool = True
    prompt_version: str = "ai_decision_faz1_rule_engine_v1"

    def to_dict(self) -> dict[str, Any]:
        return {
            "low_score_threshold": self.low_score_threshold,
            "high_score_threshold": self.high_score_threshold,
            "require_general_comment_below_low": self.require_general_comment_below_low,
            "require_general_comment_above_high": self.require_general_comment_above_high,
            "require_comment_for_score_1": self.require_comment_for_score_1,
            "require_comment_for_score_5": self.require_comment_for_score_5,
            "low_score_requires_upper_approval": self.low_score_requires_upper_approval,
            "publish_lock_for_low_score": self.publish_lock_for_low_score,
            "manager_score_variance_threshold": self.manager_score_variance_threshold,
            "enabled": self.enabled,
            "prompt_version": self.prompt_version,
        }


@dataclass(frozen=True)
class DecisionSignal:
    code: str
    title: str
    body: str
    severity: str = "info"
    category: str = "control"
    action: str | None = None
    weight: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "title": self.title,
            "body": self.body,
            "severity": self.severity,
            "category": self.category,
            "action": self.action,
            "weight": self.weight,
        }


@dataclass(frozen=True)
class DecisionRecommendation:
    title: str
    body: str
    severity: str = "info"
    recommendation_type: str = "decision_support"
    action: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "body": self.body,
            "severity": self.severity,
            "recommendation_type": self.recommendation_type,
            "action": self.action,
        }


@dataclass
class DecisionResult:
    module_type: str
    target_table: str
    target_id: int | None
    summary: str
    tone: str
    score_band: str
    decision_note: str
    risk_score: float
    signals: list[DecisionSignal] = field(default_factory=list)
    recommendations: list[DecisionRecommendation] = field(default_factory=list)
    policy: DecisionPolicy = field(default_factory=DecisionPolicy)
    metrics: dict[str, Any] = field(default_factory=dict)
    safeguards: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "module_type": self.module_type,
            "target_table": self.target_table,
            "target_id": self.target_id,
            "summary": self.summary,
            "tone": self.tone,
            "score_band": self.score_band,
            "decision_note": self.decision_note,
            "risk_score": self.risk_score,
            "signals": [signal.to_dict() for signal in self.signals],
            "recommendations": [item.to_dict() for item in self.recommendations],
            "policy": self.policy.to_dict(),
            "metrics": self.metrics,
            "safeguards": self.safeguards,
            "engine_version": "BYS360_AI_DECISION_FAZ1_RULE_ENGINE_V1",
        }


class DecisionSupportEngine:
    """Kurallı, kayıtlı ve insan denetimli karar destek motoru."""

    def __init__(self, policy: DecisionPolicy | None = None) -> None:
        self.policy = policy or DecisionPolicy()

    def evaluate_performance(self, payload: Mapping[str, Any]) -> DecisionResult:
        policy = self.policy
        evaluation_id = _int_or_none(payload.get("evaluation_id"))
        final_score = _float(payload.get("final_total_100"))
        published = bool(payload.get("published"))
        status = _text(payload.get("status"), "belirsiz")
        workflow_status = _text(payload.get("workflow_status"), "belirsiz")
        employee = payload.get("employee") or {}
        employee_name = _text(employee.get("full_name"), "Personel") if isinstance(employee, Mapping) else "Personel"
        items = _iter_mappings(payload.get("items"))
        general_comments = payload.get("general_comments") or {}
        if not isinstance(general_comments, Mapping):
            general_comments = {}
        general_comment_exists = any(_text(general_comments.get(key), "") for key in ("level_1", "level_2", "level_3"))

        signals: list[DecisionSignal] = []
        recommendations: list[DecisionRecommendation] = []

        score_band = self._score_band(final_score)
        if final_score < policy.low_score_threshold:
            signals.append(
                DecisionSignal(
                    code="low_score_upper_approval_required",
                    title="Başkan/Üst Onay Gerektiren Düşük Performans",
                    body=(
                        f"Nihai puan {final_score:.2f}. Bu sonuç {policy.low_score_threshold:.0f} eşiğinin altında olduğu için "
                        "doğrudan kesinleşmiş/yayınlanmış sonuç gibi ele alınmamalıdır."
                    ),
                    severity="critical",
                    category="approval",
                    action="Başkan/Üst Onay süreci ve personel süreç zinciri kontrol edilmelidir.",
                    weight=35,
                )
            )
            recommendations.append(
                DecisionRecommendation(
                    title="Düşük performans onay akışını başlat",
                    body=(
                        "70 altı sonuç için karne personele açılmadan önce Başkan/Üst Onay, süreç kaydı ve yayın kilidi "
                        "kontrolü tamamlanmalıdır."
                    ),
                    severity="critical",
                    recommendation_type="low_score_process",
                    action="Başkan/Üst Onay ekranında ilgili karneyi incele.",
                )
            )

        if final_score < policy.low_score_threshold and policy.require_general_comment_below_low and not general_comment_exists:
            signals.append(
                DecisionSignal(
                    code="missing_low_score_general_comment",
                    title="70 Altı Genel Görüş Eksik",
                    body="Düşük performans sonucunda ayrıntılı genel görüş bulunmuyor.",
                    severity="high",
                    category="explanation",
                    action="Amir genel görüşü tamamlanmadan yayın öncesi kontrol geçilmemelidir.",
                    weight=22,
                )
            )
        if final_score >= policy.high_score_threshold and policy.require_general_comment_above_high and not general_comment_exists:
            signals.append(
                DecisionSignal(
                    code="missing_high_score_general_comment",
                    title="90 Üstü Genel Görüş Eksik",
                    body="Çok başarılı sonuçlarda kurumsal gerekçelendirme için ayrıntılı genel görüş beklenir.",
                    severity="medium",
                    category="explanation",
                    action="Güçlü performans gerekçesi genel görüş alanına eklenmelidir.",
                    weight=12,
                )
            )

        missing_extreme_comments = self._find_missing_extreme_item_comments(items)
        if missing_extreme_comments:
            signals.append(
                DecisionSignal(
                    code="missing_extreme_score_justification",
                    title="1/5 Puan Gerekçesi Eksik",
                    body=f"{missing_extreme_comments} kriter satırında uç puan için açıklama/gerekçe kontrolü gerekiyor.",
                    severity="high",
                    category="explanation",
                    action="1 ve 5 puan verilen kriterlerde gerekçe alanları kontrol edilmelidir.",
                    weight=min(25, 8 + missing_extreme_comments * 3),
                )
            )

        variance_count = self._manager_variance_count(items)
        if variance_count:
            signals.append(
                DecisionSignal(
                    code="manager_score_variance",
                    title="Amirler Arası Puan Farkı",
                    body=f"{variance_count} kriterde amirler arası puan farkı dikkat çekici seviyede.",
                    severity="medium",
                    category="consistency",
                    action="Önceki amir görüşleriyle nihai kanaat birlikte incelenmelidir.",
                    weight=min(18, 6 + variance_count * 2),
                )
            )

        if final_score < policy.low_score_threshold and published and policy.publish_lock_for_low_score:
            signals.append(
                DecisionSignal(
                    code="low_score_published_visibility_risk",
                    title="Düşük Performans Yayın Görünürlüğü Kontrolü",
                    body="70 altı kaydın yayınlanmış görünmesi halinde onay ve süreç zinciri mutlaka doğrulanmalıdır.",
                    severity="critical",
                    category="visibility",
                    action="Başkan/Üst Onay ve yayın kilidi geçmişi kontrol edilmelidir.",
                    weight=30,
                )
            )

        if not signals:
            signals.append(
                DecisionSignal(
                    code="no_blocking_signal",
                    title="Engelleyici Sinyal Görünmüyor",
                    body="Mevcut kurallara göre belirgin açıklama, görünürlük veya eşik riski saptanmadı.",
                    severity="info",
                    category="control",
                    action="Yine de nihai karar öncesi ilgili modül ekranındaki gerçek kayıtlar kontrol edilmelidir.",
                    weight=0,
                )
            )

        risk_score = _clip(sum(max(0, int(signal.weight or 0)) for signal in signals), 0, 100)
        tone = self._tone(risk_score, final_score)
        if not recommendations and risk_score >= 40:
            recommendations.append(
                DecisionRecommendation(
                    title="Yayın öncesi kontrolü ayrıntılı yap",
                    body="Karar destek motoru açıklama, görünürlük veya tutarlılık açısından izleme gerektiren sinyaller buldu.",
                    severity="warning",
                    recommendation_type="publish_preflight",
                    action="Karne, amir görüşleri ve süreç geçmişi birlikte incelenmelidir.",
                )
            )
        elif not recommendations:
            recommendations.append(
                DecisionRecommendation(
                    title="Karne kaydını rutin yayın kontrolüne al",
                    body="Bu çıktı engelleyici karar değildir; mevcut veriler rutin kontrolle ilerlenebilir görünmektedir.",
                    severity="info",
                    recommendation_type="routine_review",
                    action="Yetkili kullanıcı karne detayını açıp son kontrolü yapmalıdır.",
                )
            )

        summary = self._build_summary(
            employee_name=employee_name,
            final_score=final_score,
            score_band=score_band,
            signal_count=len([s for s in signals if s.code != "no_blocking_signal"]),
            risk_score=risk_score,
            status=status,
        )
        return DecisionResult(
            module_type="performance",
            target_table="performance_evaluations",
            target_id=evaluation_id,
            summary=summary,
            tone=tone,
            score_band=score_band,
            decision_note=(
                "Bu çıktı idari karar değildir. Karar Destek Merkezi yalnızca mevcut BYS360 verisine göre "
                "dikkat edilmesi gereken alanları görünür kılar; nihai değerlendirme yetkili insandadır."
            ),
            risk_score=round(float(risk_score), 2),
            signals=signals,
            recommendations=recommendations,
            policy=policy,
            metrics={
                "final_score": round(final_score, 2),
                "published": published,
                "status": status,
                "workflow_status": workflow_status,
                "general_comment_exists": general_comment_exists,
                "item_count": len(items),
                "missing_extreme_item_comments": missing_extreme_comments,
                "manager_variance_count": variance_count,
            },
            safeguards=[
                "Dış AI çağrısı yapılmadı.",
                "Kişisel/hassas veri loglaması mevcut AI maskeleme katmanından geçirilmelidir.",
                "Karar değil, insan denetimli karar destek notu üretildi.",
                "Yetki kontrolü çağıran route/servis katmanında uygulanır.",
            ],
        )

    def _find_missing_extreme_item_comments(self, items: list[Mapping[str, Any]]) -> int:
        missing = 0
        for item in items:
            score = _int_or_none(item.get("score"))
            if score == 1 and not self.policy.require_comment_for_score_1:
                continue
            if score == 5 and not self.policy.require_comment_for_score_5:
                continue
            if score in {1, 5} and not _text(item.get("justification") or item.get("comment"), ""):
                missing += 1
        return missing

    def _manager_variance_count(self, items: list[Mapping[str, Any]]) -> int:
        grouped: dict[str, list[float]] = defaultdict(list)
        for item in items:
            key = _text(item.get("criteria"), "Kriter")
            score = _float(item.get("score"), default=-1)
            if score >= 0:
                grouped[key].append(score)
        return sum(
            1
            for scores in grouped.values()
            if len(scores) >= 2 and (max(scores) - min(scores)) >= self.policy.manager_score_variance_threshold
        )

    def _score_band(self, final_score: float) -> str:
        if final_score < self.policy.low_score_threshold:
            return "Düşük performans bandı"
        if final_score >= self.policy.high_score_threshold:
            return "Çok başarılı performans bandı"
        return "Standart performans bandı"

    @staticmethod
    def _tone(risk_score: float, final_score: float) -> str:
        if risk_score >= 70 or final_score < 70:
            return "danger"
        if risk_score >= 35:
            return "warning"
        return "success"

    @staticmethod
    def _build_summary(*, employee_name: str, final_score: float, score_band: str, signal_count: int, risk_score: float, status: str) -> str:
        if signal_count:
            return (
                f"{employee_name} için karar destek kontrolü tamamlandı. Nihai puan {final_score:.2f}; "
                f"sonuç {score_band.lower()} içinde. {signal_count} dikkat sinyali ve {risk_score:.0f}/100 risk göstergesi üretildi. "
                f"Süreç durumu: {status}."
            )
        return (
            f"{employee_name} için karar destek kontrolü tamamlandı. Nihai puan {final_score:.2f}; "
            f"sonuç {score_band.lower()} içinde. Engelleyici sinyal görünmüyor; süreç durumu: {status}."
        )


def _text(value: Any, fallback: str = "-") -> str:
    text = str(value or "").strip()
    return text or fallback


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value if value not in (None, "") else default)
    except (TypeError, ValueError):
        return default


def _int_or_none(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _clip(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _iter_mappings(value: Any) -> list[Mapping[str, Any]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def build_performance_decision_support(payload: Mapping[str, Any], policy: DecisionPolicy | None = None) -> dict[str, Any]:
    """Fonksiyonel çağrı isteyen eski servisler için kısa yardımcı."""
    return DecisionSupportEngine(policy=policy).evaluate_performance(payload).to_dict()
