
"""BYS360 AI Karar Destek Faz 2 kategori/grup entegrasyonu.

Faz 2, personel kategori altyapısını Karar Destek Merkezi'ne bağlar.
Çıktılar kişi detayı içermez; yalnızca kategori ortalaması ve dikkat sinyali üretir.
BYS360_AI_DECISION_FAZ2_CATEGORY_GROUP_INTEGRATION
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from flask import current_app
from flask_login import current_user

from app.extensions import db
from app.models import AIRecommendation, ModuleSetting, SystemSetting
from app.services.ai_decision.category_group_center import (
    CATEGORY_PRIVACY_NOTE,
    DEFAULT_CATEGORY_LABELS,
    build_category_group_decision_payload,
    normalize_category_label,
    slugify_category_label,
)


_SETTING_ALIASES: dict[str, tuple[str, ...]] = {
    "enabled": (
        "ai_decision.category_group_enabled",
        "ai_decision.faz2_category_group_enabled",
    ),
    "create_recommendations": (
        "ai_decision.category_group_create_recommendations",
    ),
}


def _as_bool(value: Any, default: bool = True) -> bool:
    if value in (None, ""):
        return default
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on", "evet", "aktif", "açık", "acik"}:
        return True
    if text in {"0", "false", "no", "off", "hayır", "hayir", "pasif", "kapalı", "kapali"}:
        return False
    return default


def _read_first_setting(keys: Iterable[str]) -> str | None:
    key_list = [str(key).strip() for key in keys if str(key or "").strip()]
    if not key_list:
        return None
    try:
        row = ModuleSetting.query.filter(
            ModuleSetting.module_key.in_(["ai_decision", "performance"]),
            ModuleSetting.setting_key.in_(key_list),
            ModuleSetting.is_active.is_(True),
        ).order_by(ModuleSetting.id.desc()).first()
        if row and row.value_text not in (None, ""):
            return str(row.value_text)
    except Exception:
        db.session.rollback()
    try:
        row = SystemSetting.query.filter(
            SystemSetting.setting_key.in_(key_list),
            SystemSetting.is_active.is_(True),
        ).order_by(SystemSetting.id.desc()).first()
        if row and row.value_text not in (None, ""):
            return str(row.value_text)
    except Exception:
        db.session.rollback()
    return None


def _ensure_ai_access() -> Any:
    try:
        from app.services.ai.guardrails import ensure_ai_access

        return ensure_ai_access("performance", "category_group_decision_support")
    except ImportError:
        return None


def _safe_log_excerpt(payload: Mapping[str, Any]) -> str:
    text = str({
        "period_id": payload.get("period_id"),
        "summary": payload.get("summary"),
        "category_count": ((payload.get("aggregates") or {}).get("summary") or {}).get("category_count"),
        "evaluation_count": ((payload.get("aggregates") or {}).get("summary") or {}).get("evaluation_count"),
        "signal_count": len(payload.get("signals") or []),
    })
    return text[:1800]


def _log_ai_request(payload: Mapping[str, Any], user_visible: bool = True):
    try:
        from app.services.ai.audit import log_ai_request

        return log_ai_request(
            module_type="performance",
            feature_type="category_group_decision_support",
            target_table=str(payload.get("target_table") or "performance_category_groups"),
            target_id=int(payload.get("target_id") or 0),
            user_id=getattr(current_user, "id", None),
            request_text=f"category_group_payload:{_safe_log_excerpt(payload)}",
            response_text=str(payload.get("summary") or "Kategori ve grup karar destek özeti üretildi."),
            provider_name="rule_engine",
            model_name="bys360-decision-support-faz2",
            prompt_version="ai_decision_faz2_category_group_v1",
            latency_ms=0,
            token_in=0,
            token_out=max(len(str(payload.get("summary") or "")) // 4, 1),
            was_masked=True,
            was_user_visible=user_visible,
        )
    except Exception as exc:  # pragma: no cover - log sorunu karar destek akışını bozmamalı
        current_app.logger.warning("BYS360 AI decision Faz 2 log yazılamadı: %s", exc)
        db.session.rollback()
        return None


def _persist_recommendations(
    *,
    payload: Mapping[str, Any],
    ai_request_log_id: int | None,
    created_by_id: int | None,
) -> list[AIRecommendation]:
    target_table = str(payload.get("target_table") or "performance_category_groups")
    target_id = int(payload.get("target_id") or 0)
    module_type = str(payload.get("module_type") or "performance")
    created: list[AIRecommendation] = []
    try:
        existing = {
            (row.title or "").strip().lower()
            for row in AIRecommendation.query.filter_by(
                module_type=module_type,
                target_table=target_table,
                target_id=target_id,
            ).filter(AIRecommendation.status.in_(["open", "accepted"])).all()
        }
    except Exception:
        db.session.rollback()
        existing = set()

    for item in payload.get("recommendations") or []:
        if not isinstance(item, Mapping):
            continue
        title = str(item.get("title") or "").strip()
        if not title or title.lower() in existing:
            continue
        row = AIRecommendation(
            module_type=module_type,
            target_table=target_table,
            target_id=target_id,
            recommendation_type=str(item.get("recommendation_type") or "category_group_signal")[:50],
            title=title[:255],
            body=str(item.get("body") or title).strip() or title,
            severity=str(item.get("severity") or "info")[:20],
            status="open",
            ai_request_log_id=ai_request_log_id,
            created_by_id=created_by_id,
            updated_by_id=created_by_id,
        )
        db.session.add(row)
        created.append(row)
        existing.add(title.lower())
    if created:
        db.session.flush()
    return created


def build_category_group_decision_support_response(
    period_id: int | None = None,
    *,
    include_unpublished: bool = True,
    create_recommendations: bool | None = None,
) -> dict[str, Any]:
    """Kategori/grup kırılımı için Karar Destek Merkezi yanıtı üretir."""
    policy_gate = _ensure_ai_access()
    enabled = _as_bool(_read_first_setting(_SETTING_ALIASES["enabled"]), True)
    if not enabled:
        return {
            "ok": False,
            "disabled": True,
            "message": "Karar Destek Merkezi kategori ve grup analizi sistem ayarından kapalı.",
            "data": {},
        }
    if create_recommendations is None:
        create_recommendations = _as_bool(_read_first_setting(_SETTING_ALIASES["create_recommendations"]), True)

    payload = build_category_group_decision_payload(
        period_id=period_id,
        include_unpublished=include_unpublished,
    )
    request_log = _log_ai_request(payload, user_visible=bool(getattr(policy_gate, "user_visible", True)))
    created_rows: list[AIRecommendation] = []
    if create_recommendations:
        try:
            created_rows = _persist_recommendations(
                payload=payload,
                ai_request_log_id=getattr(request_log, "id", None),
                created_by_id=getattr(current_user, "id", None),
            )
        except Exception as exc:  # pragma: no cover
            current_app.logger.warning("BYS360 AI decision Faz 2 öneri yazılamadı: %s", exc)
            db.session.rollback()
            created_rows = []
    payload["ai_request_log_id"] = getattr(request_log, "id", None)
    payload["created_recommendation_ids"] = [row.id for row in created_rows]
    return {"ok": True, "data": payload}


def build_ai_decision_faz2_health_payload() -> dict[str, Any]:
    return {
        "ok": True,
        "phase": "Faz 2",
        "title": "Personel Kategori ve Grup Altyapısı",
        "engine": "bys360-decision-support-faz2-category-group",
        "external_ai_call": False,
        "default_categories": list(DEFAULT_CATEGORY_LABELS),
        "privacy_note": CATEGORY_PRIVACY_NOTE,
        "normalization_examples": {
            "guvenlik": normalize_category_label("guvenlik"),
            "teknik": normalize_category_label("teknik"),
            "diger": normalize_category_label("diger"),
        },
        "slug_examples": {
            label: slugify_category_label(label) for label in DEFAULT_CATEGORY_LABELS
        },
        "contracts": [
            "Personel kategori sözlüğü canlı omurgaya eklenir.",
            "Personel kartı ve import süreçleri kategori alanını kullanabilir.",
            "Kategori ortalaması kişi detayı göstermeden hesaplanır.",
            "Karar Destek Merkezi kategori bazlı düşük performans ve yayın riski sinyali üretir.",
            "Nihai idari karar üretmez; yalnızca karar destek notu sağlar.",
        ],
        "marker": "BYS360_AI_DECISION_FAZ2_HEALTH_OK",
    }
