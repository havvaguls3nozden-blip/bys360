
"""BYS360 AI Karar Destek Faz 4 3. amir entegrasyon servisi.

Bu servis performans değerlendirme kaydına 3. amir akış temizliği açısından
kurumsal karar destek notu ekler. Çıktı karar değildir; yalnızca yetkili
kullanıcıya süreç sağlığı sinyali verir.

BYS360_AI_DECISION_FAZ4_THIRD_SUPERVISOR_INTEGRATION
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .third_supervisor_policy import (
    ThirdSupervisorPolicy,
    build_third_supervisor_flow_summary,
    build_third_supervisor_policy,
    build_third_supervisor_status,
    evaluate_weight_contract,
    third_supervisor_comment,
    third_supervisor_score,
)


def _safe_id(obj: Any) -> Any:
    if isinstance(obj, Mapping):
        return obj.get("id")
    return getattr(obj, "id", None)


def _safe_period_id(obj: Any) -> Any:
    if isinstance(obj, Mapping):
        return obj.get("period_id")
    return getattr(obj, "period_id", None)


def _build_signal(code: str, title: str, body: str, severity: str = "info", action: str | None = None) -> dict[str, Any]:
    return {"code": code, "title": title, "body": body, "severity": severity, "action": action}


def build_third_supervisor_decision_payload(
    evaluation: Any,
    settings: Mapping[str, Any] | None = None,
    weights: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Tek performans kaydı için 3. amir karar destek yüzeyi üretir."""
    policy = build_third_supervisor_policy(settings)
    status = build_third_supervisor_status(policy, evaluation)
    weight_contract = evaluate_weight_contract(policy, weights)
    signals: list[dict[str, Any]] = []

    if not status.has_third_supervisor:
        signals.append(_build_signal("third_supervisor_not_required", "3. amir gerekmiyor", "Bu kayıt için 3. amir tanımı bulunmadığından boş sütun veya bekleme görevi gösterilmemelidir."))
    elif status.expected_action == "comment":
        signals.append(_build_signal("third_supervisor_comment_mode", "3. amir görüş modunda", "3. amir yalnızca görüş yazar; nihai puana katkı vermez."))
    elif status.expected_action == "score":
        signals.append(_build_signal("third_supervisor_score_mode", "3. amir puan modunda", "3. amir puana katkı verir; ağırlık toplamı 100 olacak şekilde kontrol edilmelidir.", "warning" if not weight_contract["ok"] else "info"))

    for warning in status.warnings:
        signals.append(_build_signal("third_supervisor_flow_warning", "3. amir akışı kontrol edilmeli", warning, "warning", "Akış ve görev üretimi ekranında ilgili kayıt kontrol edilmelidir."))

    for warning in weight_contract["warnings"]:
        signals.append(_build_signal("third_supervisor_weight_warning", "3. amir ağırlığı kontrol edilmeli", warning, "warning", "Ayarlar bölümündeki amir ağırlıkları gözden geçirilmelidir."))

    summary = status.status_label
    if signals and any(item["severity"] == "warning" for item in signals):
        summary = "3. amir akışında kontrol gerektiren kayıt var"

    return {
        "ok": True,
        "module": "AI Karar Destek - 3. Amir Opsiyonelliği ve Akış Temizliği",
        "evaluation_id": _safe_id(evaluation),
        "period_id": _safe_period_id(evaluation),
        "summary": summary,
        "policy": policy.to_dict(),
        "status": status.to_dict(),
        "weight_contract": weight_contract,
        "signals": signals,
        "recommendations": build_third_supervisor_recommendations(status.to_dict(), weight_contract),
        "safe_preview": {
            "third_supervisor_comment_exists": bool(third_supervisor_comment(evaluation)),
            "third_supervisor_score_exists": third_supervisor_score(evaluation) not in (None, ""),
        },
        "safeguards": [
            "3. amir olmayan kayıtta boş sütun gösterilmez.",
            "Yorum modunda 3. amir puana etki etmez.",
            "Puan modunda ağırlık toplamı 100 olarak kontrol edilir.",
            "Karar destek çıktısı idari karar yerine geçmez.",
        ],
        "marker": "BYS360_AI_DECISION_FAZ4_THIRD_SUPERVISOR_PAYLOAD_OK",
    }


def build_third_supervisor_recommendations(status: Mapping[str, Any], weight_contract: Mapping[str, Any]) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    if not status.get("has_third_supervisor"):
        recommendations.append({"title": "Boş 3. amir alanı gösterilmesin", "body": "Bu kayıt 3. amir gerektirmediği için ekranda bekleme, puan veya görüş alanı açılmamalıdır.", "severity": "info"})
    if status.get("warnings"):
        recommendations.append({"title": "3. amir görev üretimi kontrol edilsin", "body": "Kayıtta bekleme veya puan izi varsa amir zinciri ve dönem görevleri yeniden kontrol edilmelidir.", "severity": "warning"})
    if not weight_contract.get("ok", True):
        recommendations.append({"title": "Amir ağırlıkları dengelensin", "body": "3. amir puan modunda kullanılıyorsa toplam ağırlık 100 olmalı; yorum modunda 3. amir ağırlığı 0 kalmalıdır.", "severity": "warning"})
    if not recommendations:
        recommendations.append({"title": "3. amir akışı uygun", "body": "Kayıt mevcut ayarlara göre tutarlı görünüyor.", "severity": "info"})
    return recommendations


def build_third_supervisor_bulk_payload(evaluations: Iterable[Any], settings: Mapping[str, Any] | None = None) -> dict[str, Any]:
    policy: ThirdSupervisorPolicy = build_third_supervisor_policy(settings)
    summary = build_third_supervisor_flow_summary(evaluations, policy)
    return {
        "ok": True,
        "module": "AI Karar Destek - 3. Amir Toplu Akış Özeti",
        "summary": summary,
        "recommendations": [
            {"title": "3. amir sütunu yalnızca gerekli kayıt varsa açılsın", "body": "Toplu listelerde 3. amir olmayan kayıtlar için boş alan ve bekleme statüsü gösterilmemelidir.", "severity": "info"}
        ],
        "marker": "BYS360_AI_DECISION_FAZ4_THIRD_SUPERVISOR_BULK_OK",
    }
