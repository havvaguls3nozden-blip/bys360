from __future__ import annotations

import logging

"""BYS360 AI Karar Destek Faz 1 performans entegrasyonu.

Bu katman mevcut performans payloadını karar motoruna verir, güvenli AI request
logu oluşturur ve isteğe bağlı olarak ai_recommendations satırlarını üretir.
Dış AI sağlayıcısı çağırmaz.

BYS360_AI_DECISION_FAZ1_PERFORMANCE_INTEGRATION
"""

from collections.abc import Iterable, Mapping
from typing import Any

from flask import current_app
from flask_login import current_user

from app.extensions import db
from app.models import AIRecommendation, ModuleSetting, SystemSetting
from app.services.ai.audit import log_ai_request
from app.services.ai.guardrails import ensure_ai_access
from app.services.ai.query_adapters import get_performance_evaluation_payload
from app.services.ai.schema_guard import ai_schema_ready
from app.services.ai_decision.decision_support_engine import DecisionPolicy, DecisionSupportEngine
from app.services.ai_decision.logging_bridge import build_ai_safe_log_excerpt

logger = logging.getLogger(__name__)


_SETTING_ALIASES: dict[str, tuple[str, ...]] = {
    "enabled": (
        "ai_decision.performance_engine_enabled",
        "ai_decision.faz1_engine_enabled",
    ),
    "require_comment_for_score_1": (
        "performance_scoring.require_comment_for_score_1",
        "performance_scoring.require_score_1_comment",
        "performance.require_score_1_comment",
    ),
    "require_comment_for_score_5": (
        "performance_scoring.require_comment_for_score_5",
        "performance_scoring.require_score_5_comment",
        "performance.require_score_5_comment",
    ),
    "require_general_comment_below_low": (
        "performance_scoring.require_general_comment_below_70",
        "performance.require_general_comment_below_70",
    ),
    "require_general_comment_above_high": (
        "performance_scoring.require_general_comment_above_90",
        "performance.require_general_comment_above_90",
    ),
    "low_score_requires_upper_approval": (
        "performance_flow.low_score_requires_president_approval",
        "performance.low_score_requires_president_approval",
    ),
    "publish_lock_for_low_score": (
        "performance_flow.low_score_publish_lock",
        "performance.low_score_publish_lock",
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


def _as_float(value: Any, default: float) -> float:
    try:
        return float(value if value not in (None, "") else default)
    except (TypeError, ValueError):
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
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        db.session.rollback()
    try:
        row = SystemSetting.query.filter(
            SystemSetting.setting_key.in_(key_list),
            SystemSetting.is_active.is_(True),
        ).order_by(SystemSetting.id.desc()).first()
        if row and row.value_text not in (None, ""):
            return str(row.value_text)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        db.session.rollback()
    return None


def build_ai_decision_policy_from_settings() -> DecisionPolicy:
    """Ayarlar tablosu varsa okur; yoksa güvenli varsayılanlarla çalışır."""
    low_threshold = _as_float(_read_first_setting(["performance_scoring.low_score_threshold", "performance.low_score_threshold"]), 70.0)
    high_threshold = _as_float(_read_first_setting(["performance_scoring.high_score_threshold", "performance.high_score_threshold"]), 90.0)
    variance_threshold = _as_float(_read_first_setting(["ai_decision.manager_score_variance_threshold"]), 3.0)
    return DecisionPolicy(
        low_score_threshold=low_threshold,
        high_score_threshold=high_threshold,
        require_general_comment_below_low=_as_bool(
            _read_first_setting(_SETTING_ALIASES["require_general_comment_below_low"]), True
        ),
        require_general_comment_above_high=_as_bool(
            _read_first_setting(_SETTING_ALIASES["require_general_comment_above_high"]), True
        ),
        require_comment_for_score_1=_as_bool(
            _read_first_setting(_SETTING_ALIASES["require_comment_for_score_1"]), True
        ),
        require_comment_for_score_5=_as_bool(
            _read_first_setting(_SETTING_ALIASES["require_comment_for_score_5"]), True
        ),
        low_score_requires_upper_approval=_as_bool(
            _read_first_setting(_SETTING_ALIASES["low_score_requires_upper_approval"]), True
        ),
        publish_lock_for_low_score=_as_bool(
            _read_first_setting(_SETTING_ALIASES["publish_lock_for_low_score"]), True
        ),
        manager_score_variance_threshold=variance_threshold,
        enabled=_as_bool(_read_first_setting(_SETTING_ALIASES["enabled"]), True),
        prompt_version="ai_decision_faz1_rule_engine_v1",
    )


def _persist_recommendations(
    *,
    result: Mapping[str, Any],
    ai_request_log_id: int | None,
    created_by_id: int | None,
) -> list[AIRecommendation]:
    if not ai_schema_ready():
        return []
    target_table = str(result.get("target_table") or "performance_evaluations")
    target_id = int(result.get("target_id") or 0)
    module_type = str(result.get("module_type") or "performance")
    created: list[AIRecommendation] = []
    existing = {
        (row.title or "").strip().lower()
        for row in AIRecommendation.query.filter_by(
            module_type=module_type,
            target_table=target_table,
            target_id=target_id,
        ).filter(AIRecommendation.status.in_(["open", "accepted"]))
    }
    for item in result.get("recommendations") or []:
        if not isinstance(item, Mapping):
            continue
        title = str(item.get("title") or "").strip()
        if not title or title.lower() in existing:
            continue
        row = AIRecommendation(
            module_type=module_type,
            target_table=target_table,
            target_id=target_id,
            recommendation_type=str(item.get("recommendation_type") or "decision_support")[:50],
            title=title[:255],
            body=str(item.get("body") or item.get("action") or title).strip() or title,
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


def build_performance_decision_support_response(
    evaluation_id: int,
    *,
    create_recommendations: bool = True,
) -> dict[str, Any]:
    """Performans değerlendirmesi için Faz 1 karar destek çıktısı üretir."""
    policy_gate = ensure_ai_access("performance", "decision_support")
    evaluation, payload = get_performance_evaluation_payload(evaluation_id)
    policy = build_ai_decision_policy_from_settings()
    if not policy.enabled:
        return {
            "ok": False,
            "disabled": True,
            "message": "Karar Destek Merkezi performans karar motoru sistem ayarından kapalı.",
            "data": {},
        }

    result = DecisionSupportEngine(policy=policy).evaluate_performance(payload).to_dict()
    request_log = None
    try:
        request_log = log_ai_request(
            module_type="performance",
            feature_type="decision_support",
            target_table="performance_evaluations",
            target_id=evaluation.id,
            user_id=getattr(current_user, "id", None),
            request_text=f"decision_engine_payload:{build_ai_safe_log_excerpt(payload)}",
            response_text=result.get("summary"),
            provider_name="rule_engine",
            model_name="bys360-decision-support-faz1",
            prompt_version=policy.prompt_version,
            latency_ms=0,
            token_in=0,
            token_out=max(len(str(result.get("summary") or "")) // 4, 1),
            was_masked=True,
            was_user_visible=policy_gate.user_visible,
        )
    except Exception as exc:  # pragma: no cover - canlıda log hatası akışı bozmamalı
        current_app.logger.warning("BYS360 AI decision Faz 1 log yazılamadı: %s", exc)
        db.session.rollback()

    created_rows: list[AIRecommendation] = []
    if create_recommendations:
        try:
            created_rows = _persist_recommendations(
                result=result,
                ai_request_log_id=getattr(request_log, "id", None),
                created_by_id=getattr(current_user, "id", None),
            )
        except Exception as exc:  # pragma: no cover
            current_app.logger.warning("BYS360 AI decision Faz 1 öneri yazılamadı: %s", exc)
            db.session.rollback()
            created_rows = []

    result["ai_request_log_id"] = getattr(request_log, "id", None)
    result["created_recommendation_ids"] = [row.id for row in created_rows]
    return {"ok": True, "data": result}


def build_ai_decision_faz1_health_payload() -> dict[str, Any]:
    policy = build_ai_decision_policy_from_settings()
    return {
        "ok": True,
        "phase": "Faz 1",
        "title": "Karar Motoru ve Performans Entegrasyonu",
        "engine": "bys360-decision-support-faz1",
        "external_ai_call": False,
        "policy": policy.to_dict(),
        "contracts": [
            "70 altı sonuç için Başkan/Üst Onay sinyali üretir.",
            "70 altı ve 90 üstü genel görüş zorunluluğunu kontrol eder.",
            "1 ve 5 puan gerekçesini sistem ayarına göre kontrol eder.",
            "AI log ve öneri tablolarına güvenli kayıt bırakır.",
            "Nihai idari karar üretmez; yalnızca karar destek notu sağlar.",
        ],
        "marker": "BYS360_AI_DECISION_FAZ1_HEALTH_OK",
    }
