
"""AI öneri uygulama servisleri.

Eğitim, Strateji ve Belge/Medya Deposu modülleri canlı omurgadan çıkarıldığı için
otomatik hedef uygulama desteği kapatılmıştır. AI Karar Destek kayıt, log, özet ve
geribildirim omurgası aktif kalır; ancak kaldırılan modüllere yazma işlemi yapılmaz.
"""
from __future__ import annotations

from typing import Any

from app.models import AIRecommendation

SUPPORTED_TARGETS: tuple[tuple[str, str], ...] = ()


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def is_recommendation_supported(recommendation: AIRecommendation | None) -> bool:
    return False


def apply_recommendation(recommendation_id: int, *, acting_user: Any = None) -> dict[str, Any]:
    raise ValueError("Bu öneri tipi güncel canlı omurgada otomatik uygulanamaz.")


def list_target_recommendation_payloads(
    *,
    module_type: str,
    target_table: str,
    target_id: int,
    statuses: tuple[str, ...] = ("open", "accepted", "rejected"),
) -> list[dict[str, Any]]:
    normalized_statuses = [str(value).strip().lower() for value in statuses if str(value).strip()]
    query = (
        AIRecommendation.query.filter_by(
            module_type=(module_type or "").strip().lower(),
            target_table=(target_table or "").strip(),
            target_id=int(target_id or 0),
        )
        .order_by(AIRecommendation.created_at.desc(), AIRecommendation.id.desc())
    )
    if normalized_statuses:
        query = query.filter(AIRecommendation.status.in_(normalized_statuses))
    rows = query.all()
    return [
        {
            "id": row.id,
            "title": row.title,
            "body": row.body,
            "severity": row.severity,
            "status": row.status,
            "recommendation_type": row.recommendation_type,
            "is_supported": False,
            "reviewed_at": row.reviewed_at.isoformat() if row.reviewed_at else None,
        }
        for row in rows
    ]


def bulk_apply_recommendations(recommendation_ids: list[int], *, acting_user: Any = None) -> dict[str, Any]:
    return {
        "ok": True,
        "applied_count": 0,
        "failed_count": len(recommendation_ids or []),
        "results": [],
        "errors": [
            {"id": rid, "error": "Bu öneri tipi güncel canlı omurgada otomatik uygulanamaz."}
            for rid in (recommendation_ids or [])
        ],
    }
