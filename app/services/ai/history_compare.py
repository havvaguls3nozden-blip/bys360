from __future__ import annotations

import json
import re
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timedelta
from math import ceil
from pathlib import Path
from typing import Any

from sqlalchemy import func

from app.core.datetime_utils import utc_now
from app.models import AIFeedbackLog, AIRecommendation, AIRequestLog
from app.services.ai.executive_reporting import build_ai_executive_brief
from app.services.ai.go_live import build_ai_go_live_snapshot
from app.services.ai.localization import (
    ai_feature_label,
    ai_feedback_label,
    ai_module_label,
    ai_recommendation_label,
    ai_status_label,
    ai_target_label,
)
from app.services.ai.module_scope import (
    filter_visible_values,
    is_visible_ai_module,
    scope_visible_modules,
)

NEGATIVE_FEEDBACK_TYPES = {"not_helpful", "wrong", "unsafe", "incorrect", "negative"}
POSITIVE_FEEDBACK_TYPES = {"helpful", "positive"}
MANAGEMENT_TEMPLATE_FILE_NAME = "ai_management_pack_template.json"
DEFAULT_MANAGEMENT_TEMPLATE: dict[str, Any] = {
    "report_title": "BYS360 AI Yönetici Rapor Paketi",
    "report_subtitle": "Karar geçmişi, istem sürüm karşılaştırması ve yönetici görünümü",
    "distribution_plan": {
        "default_recipients": ["Üst Yönetim", "Personel/İdari İşler", "BT"],
        "default_formats": ["markdown", "json", "csv"],
        "default_note": "Rapor, insan onayı ve yönetsel gözden geçirme ile paylaşılmalıdır.",
    },
}


def _safe_int(value: Any, default: int, minimum: int = 1, maximum: int | None = None) -> int:
    try:
        parsed = int(value or default)
    except (TypeError, ValueError):
        parsed = default
    parsed = max(parsed, minimum)
    if maximum is not None:
        parsed = min(parsed, maximum)
    return parsed

def _cutoff(lookback_days: int) -> datetime:
    return utc_now() - timedelta(days=_safe_int(lookback_days, 30, 1, 365))

def _clip(text: str | None, limit: int = 180) -> str:
    value = str(text or "").strip()
    if not value:
        return "-"
    value = re.sub(r"\s+", " ", value)
    if len(value) <= limit:
        return value
    return value[: limit - 3].rstrip() + "..."

def _preview_request(row: AIRequestLog) -> str:
    if not bool(getattr(row, "was_masked", True)):
        return "Maskesiz kayıt — ayrıntı görünümü gizlendi."
    return _clip(getattr(row, "request_text", None), 180)

def _preview_response(row: AIRequestLog) -> str:
    return _clip(getattr(row, "response_text", None), 180)

def _version_key(value: str | None) -> tuple[int, ...]:
    text = str(value or "").strip().lower()
    if not text:
        return (0,)
    parts = [int(chunk) for chunk in re.findall(r"\d+", text)]
    return tuple(parts or [0])

def _status_bucket(value: str | None) -> str:
    text = str(value or "").strip().lower()
    if text in {"completed", "success", "ok"}:
        return "completed"
    if text in {"warning", "watch", "warn"}:
        return "warning"
    if text in {"failed", "error", "fail"}:
        return "failed"
    return text or "completed"

def _template_path() -> Path:
    return Path(__file__).resolve().parents[3] / "config" / MANAGEMENT_TEMPLATE_FILE_NAME

def _merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dict(merged.get(key) or {}, value)
        else:
            merged[key] = value
    return merged

def get_ai_management_template() -> dict[str, Any]:
    path = _template_path()
    if not path.exists():
        return deepcopy(DEFAULT_MANAGEMENT_TEMPLATE)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return deepcopy(DEFAULT_MANAGEMENT_TEMPLATE)
    if not isinstance(payload, dict):
        return deepcopy(DEFAULT_MANAGEMENT_TEMPLATE)
    return _merge_dict(DEFAULT_MANAGEMENT_TEMPLATE, payload)

def build_ai_decision_history_snapshot(
    *,
    lookback_days: int | None = None,
    module_type: str = "",
    feature_type: str = "",
    status: str = "",
    page: int = 1,
    per_page: int = 20,
) -> dict[str, Any]:
    lookback = _safe_int(lookback_days, 30, 1, 365)
    page = _safe_int(page, 1, 1)
    per_page = _safe_int(per_page, 20, 5, 100)
    selected_module_type = str(module_type or "").strip().lower()
    selected_feature_type = str(feature_type or "").strip().lower()
    selected_status = str(status or "").strip().lower()

    query = scope_visible_modules(AIRequestLog.query, AIRequestLog.module_type).filter(AIRequestLog.created_at >= _cutoff(lookback))
    if selected_module_type:
        if not is_visible_ai_module(selected_module_type):
            query = query.filter(False)
        else:
            query = query.filter(func.lower(AIRequestLog.module_type) == selected_module_type)
    if selected_feature_type:
        query = query.filter(func.lower(AIRequestLog.feature_type) == selected_feature_type)
    if selected_status:
        query = query.filter(func.lower(AIRequestLog.status) == selected_status)

    total = query.count()
    pages = max(ceil(total / per_page), 1)
    page = min(page, pages)
    request_rows = (
        query.order_by(AIRequestLog.created_at.desc(), AIRequestLog.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    request_ids = [row.id for row in request_rows]
    feedback_rows = (
        AIFeedbackLog.query.filter(AIFeedbackLog.ai_request_log_id.in_(request_ids)).all()
        if request_ids
        else []
    )
    recommendation_rows = (
        AIRecommendation.query.filter(AIRecommendation.ai_request_log_id.in_(request_ids)).all()
        if request_ids
        else []
    )

    feedback_map: dict[int, dict[str, Any]] = defaultdict(
        lambda: {
            "total": 0,
            "positive": 0,
            "negative": 0,
            "latest": "",
        }
    )
    for row in feedback_rows:
        bucket = feedback_map[int(row.ai_request_log_id)]
        bucket["total"] += 1
        feedback_type = str(row.feedback_type or "").strip().lower()
        if feedback_type in POSITIVE_FEEDBACK_TYPES:
            bucket["positive"] += 1
        if feedback_type in NEGATIVE_FEEDBACK_TYPES:
            bucket["negative"] += 1
        bucket["latest"] = ai_feedback_label(feedback_type)

    recommendation_map: dict[int, dict[str, Any]] = defaultdict(
        lambda: {
            "total": 0,
            "open_total": 0,
            "accepted_total": 0,
            "top_type": "",
        }
    )
    for row in recommendation_rows:
        bucket = recommendation_map[int(row.ai_request_log_id)]
        bucket["total"] += 1
        status_key = str(row.status or "").strip().lower()
        if status_key == "open":
            bucket["open_total"] += 1
        if status_key == "accepted":
            bucket["accepted_total"] += 1
        if not bucket["top_type"]:
            bucket["top_type"] = ai_recommendation_label(row.recommendation_type)

    row_payloads: list[dict[str, Any]] = []
    for row in request_rows:
        feedback = feedback_map.get(int(row.id), {})
        recommendations = recommendation_map.get(int(row.id), {})
        row_payloads.append(
            {
                "id": row.id,
                "created_at": row.created_at,
                "module_type": row.module_type,
                "module_label": ai_module_label(row.module_type),
                "feature_type": row.feature_type,
                "feature_label": ai_feature_label(row.feature_type),
                "target_table": row.target_table or "",
                "target_label": ai_target_label(row.target_table or "genel"),
                "target_id": row.target_id,
                "prompt_version": row.prompt_version or "varsayılan",
                "provider_name": row.provider_name or "-",
                "model_name": row.model_name or "-",
                "status": row.status,
                "status_label": ai_status_label(row.status),
                "latency_ms": int(row.latency_ms or 0),
                "token_in": int(row.token_in or 0),
                "token_out": int(row.token_out or 0),
                "request_preview": _preview_request(row),
                "response_preview": _preview_response(row),
                "feedback_total": int(feedback.get("total") or 0),
                "feedback_positive": int(feedback.get("positive") or 0),
                "feedback_negative": int(feedback.get("negative") or 0),
                "feedback_latest_label": feedback.get("latest") or "-",
                "recommendation_total": int(recommendations.get("total") or 0),
                "open_recommendations": int(recommendations.get("open_total") or 0),
                "accepted_recommendations": int(recommendations.get("accepted_total") or 0),
                "recommendation_top_label": recommendations.get("top_type") or "-",
                "was_user_visible": bool(getattr(row, "was_user_visible", True)),
                "was_masked": bool(getattr(row, "was_masked", True)),
                "error_message": _clip(getattr(row, "error_message", None), 140),
            }
        )

    summary_query = scope_visible_modules(AIRequestLog.query, AIRequestLog.module_type).filter(AIRequestLog.created_at >= _cutoff(lookback))
    if selected_module_type:
        if not is_visible_ai_module(selected_module_type):
            summary_query = summary_query.filter(False)
        else:
            summary_query = summary_query.filter(func.lower(AIRequestLog.module_type) == selected_module_type)
    if selected_feature_type:
        summary_query = summary_query.filter(func.lower(AIRequestLog.feature_type) == selected_feature_type)
    if selected_status:
        summary_query = summary_query.filter(func.lower(AIRequestLog.status) == selected_status)
    summary_rows = summary_query.all()
    summary_ids = [row.id for row in summary_rows]
    summary_feedback_rows = (
        AIFeedbackLog.query.filter(AIFeedbackLog.ai_request_log_id.in_(summary_ids)).all()
        if summary_ids
        else []
    )
    summary_recommendation_rows = (
        AIRecommendation.query.filter(AIRecommendation.ai_request_log_id.in_(summary_ids)).all()
        if summary_ids
        else []
    )

    completed_total = sum(1 for row in summary_rows if _status_bucket(row.status) == "completed")
    failed_total = sum(1 for row in summary_rows if _status_bucket(row.status) == "failed")
    warning_total = sum(1 for row in summary_rows if _status_bucket(row.status) == "warning")
    feedback_total = len(summary_feedback_rows)
    negative_feedback_total = sum(
        1 for row in summary_feedback_rows if str(row.feedback_type or "").strip().lower() in NEGATIVE_FEEDBACK_TYPES
    )
    open_recommendations = sum(1 for row in summary_recommendation_rows if str(row.status or "").strip().lower() == "open")

    module_options = filter_visible_values(
        row[0]
        for row in AIRequestLog.query.with_entities(AIRequestLog.module_type).distinct().order_by(AIRequestLog.module_type.asc()).all()
        if row[0]
    )
    feature_options = [
        row[0]
        for row in AIRequestLog.query.with_entities(AIRequestLog.feature_type).distinct().order_by(AIRequestLog.feature_type.asc()).all()
        if row[0]
    ]
    status_options = ["completed", "warning", "failed"]

    return {
        "page_title": "AI Karar Geçmişi",
        "page_kicker": "Denetim izi",
        "page_subtitle": "İstek, çıktı, geri bildirim ve öneri ilişkisini tek ekranda izler.",
        "lookback_days": lookback,
        "rows": row_payloads,
        "summary": {
            "request_total": len(summary_rows),
            "completed_total": completed_total,
            "failed_total": failed_total,
            "warning_total": warning_total,
            "feedback_total": feedback_total,
            "negative_feedback_total": negative_feedback_total,
            "open_recommendations": open_recommendations,
        },
        "module_options": module_options,
        "feature_options": feature_options,
        "status_options": status_options,
        "selected_module_type": selected_module_type,
        "selected_feature_type": selected_feature_type,
        "selected_status": selected_status,
        "pagination": {
            "page": page,
            "pages": pages,
            "per_page": per_page,
            "total": total,
            "has_prev": page > 1,
            "has_next": page < pages,
            "prev_num": page - 1,
            "next_num": page + 1,
        },
    }

def build_ai_prompt_compare_snapshot(
    *,
    lookback_days: int | None = None,
    module_type: str = "",
    feature_type: str = "",
) -> dict[str, Any]:
    lookback = _safe_int(lookback_days, 30, 1, 365)
    selected_module_type = str(module_type or "").strip().lower()
    selected_feature_type = str(feature_type or "").strip().lower()

    query = scope_visible_modules(AIRequestLog.query, AIRequestLog.module_type).filter(AIRequestLog.created_at >= _cutoff(lookback))
    if selected_module_type:
        if not is_visible_ai_module(selected_module_type):
            query = query.filter(False)
        else:
            query = query.filter(func.lower(AIRequestLog.module_type) == selected_module_type)
    if selected_feature_type:
        query = query.filter(func.lower(AIRequestLog.feature_type) == selected_feature_type)
    request_rows = query.order_by(AIRequestLog.created_at.desc(), AIRequestLog.id.desc()).all()
    request_ids = [row.id for row in request_rows]

    feedback_rows = (
        AIFeedbackLog.query.filter(AIFeedbackLog.ai_request_log_id.in_(request_ids)).all()
        if request_ids
        else []
    )
    recommendation_rows = (
        AIRecommendation.query.filter(AIRecommendation.ai_request_log_id.in_(request_ids)).all()
        if request_ids
        else []
    )

    feedback_map: dict[int, dict[str, int]] = defaultdict(lambda: {"positive": 0, "negative": 0})
    for row in feedback_rows:
        bucket = feedback_map[int(row.ai_request_log_id)]
        feedback_type = str(row.feedback_type or "").strip().lower()
        if feedback_type in POSITIVE_FEEDBACK_TYPES:
            bucket["positive"] += 1
        if feedback_type in NEGATIVE_FEEDBACK_TYPES:
            bucket["negative"] += 1

    recommendation_map: dict[int, dict[str, int]] = defaultdict(lambda: {"open": 0, "accepted": 0})
    for row in recommendation_rows:
        bucket = recommendation_map[int(row.ai_request_log_id)]
        status_key = str(row.status or "").strip().lower()
        if status_key == "open":
            bucket["open"] += 1
        if status_key == "accepted":
            bucket["accepted"] += 1

    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in request_rows:
        version = str(row.prompt_version or "varsayılan").strip() or "varsayılan"
        key = (
            str(row.module_type or "genel").strip().lower() or "genel",
            str(row.feature_type or "genel").strip().lower() or "genel",
            version,
        )
        bucket = grouped.setdefault(
            key,
            {
                "module_type": key[0],
                "feature_type": key[1],
                "prompt_version": version,
                "request_total": 0,
                "completed_total": 0,
                "failed_total": 0,
                "warning_total": 0,
                "feedback_positive": 0,
                "feedback_negative": 0,
                "open_recommendations": 0,
                "accepted_recommendations": 0,
                "token_in_total": 0,
                "token_out_total": 0,
                "latency_total": 0,
                "latency_count": 0,
                "last_seen_at": None,
            },
        )
        bucket["request_total"] += 1
        status_bucket = _status_bucket(row.status)
        if status_bucket == "completed":
            bucket["completed_total"] += 1
        elif status_bucket == "failed":
            bucket["failed_total"] += 1
        elif status_bucket == "warning":
            bucket["warning_total"] += 1
        bucket["feedback_positive"] += int(feedback_map[int(row.id)]["positive"])
        bucket["feedback_negative"] += int(feedback_map[int(row.id)]["negative"])
        bucket["open_recommendations"] += int(recommendation_map[int(row.id)]["open"])
        bucket["accepted_recommendations"] += int(recommendation_map[int(row.id)]["accepted"])
        bucket["token_in_total"] += int(row.token_in or 0)
        bucket["token_out_total"] += int(row.token_out or 0)
        if row.latency_ms is not None:
            bucket["latency_total"] += int(row.latency_ms or 0)
            bucket["latency_count"] += 1
        if bucket["last_seen_at"] is None or (row.created_at and row.created_at > bucket["last_seen_at"]):
            bucket["last_seen_at"] = row.created_at

    rows: list[dict[str, Any]] = []
    family_map: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in grouped.values():
        request_total = max(int(item.get("request_total") or 0), 1)
        success_rate = round((int(item.get("completed_total") or 0) / request_total) * 100)
        negative_feedback = int(item.get("feedback_negative") or 0)
        positive_feedback = int(item.get("feedback_positive") or 0)
        feedback_total = positive_feedback + negative_feedback
        feedback_balance = 100
        if feedback_total > 0:
            feedback_balance = round(max((positive_feedback - negative_feedback) / feedback_total * 100, -100))
        open_recommendations = int(item.get("open_recommendations") or 0)
        avg_latency = round(int(item.get("latency_total") or 0) / max(int(item.get("latency_count") or 0), 1)) if int(item.get("latency_count") or 0) else 0
        quality_score = max(
            0,
            min(
                100,
                round(success_rate * 0.65 + ((feedback_balance + 100) / 2) * 0.20 - open_recommendations * 3 - int(item.get("failed_total") or 0) * 4),
            ),
        )
        stability = "stable"
        if quality_score < 50 or int(item.get("failed_total") or 0) >= 3 or negative_feedback >= 3:
            stability = "critical"
        elif quality_score < 70 or open_recommendations >= 3:
            stability = "warning"

        payload = {
            **item,
            "module_label": ai_module_label(item.get("module_type") or "genel"),
            "feature_label": ai_feature_label(item.get("feature_type") or "genel"),
            "success_rate": int(success_rate),
            "feedback_total": feedback_total,
            "feedback_balance": feedback_balance,
            "avg_latency_ms": int(avg_latency),
            "quality_score": int(quality_score),
            "stability": stability,
            "stability_label": ai_status_label(stability),
            "comparison_note": "-",
            "delta_quality": None,
            "previous_version": "-",
        }
        rows.append(payload)
        family_map[(payload["module_type"], payload["feature_type"])].append(payload)

    for family_rows in family_map.values():
        family_rows.sort(key=lambda row: (_version_key(str(row.get("prompt_version") or "")), row.get("last_seen_at") or datetime.min), reverse=True)
        for index, row in enumerate(family_rows):
            previous = family_rows[index + 1] if index + 1 < len(family_rows) else None
            if previous is None:
                row["comparison_note"] = "Karşılaştırılacak önceki sürüm yok."
                row["previous_version"] = "-"
                row["delta_quality"] = None
                continue
            delta = int(row.get("quality_score") or 0) - int(previous.get("quality_score") or 0)
            row["previous_version"] = previous.get("prompt_version") or "-"
            row["delta_quality"] = delta
            if delta > 0:
                row["comparison_note"] = f"Önceki sürüme göre +{delta} kalite puanı iyileşme var."
            elif delta < 0:
                row["comparison_note"] = f"Önceki sürüme göre {delta} kalite puanı düşüş var."
            else:
                row["comparison_note"] = "Önceki sürüm ile kalite görünümü benzer seviyede."

    rows.sort(
        key=lambda row: (
            0 if row.get("stability") == "critical" else 1 if row.get("stability") == "warning" else 2,
            -(int(row.get("request_total") or 0)),
            str(row.get("module_type") or ""),
            str(row.get("feature_type") or ""),
            _version_key(str(row.get("prompt_version") or "")),
        )
    )

    stable_total = sum(1 for row in rows if row.get("stability") == "stable")
    warning_total = sum(1 for row in rows if row.get("stability") == "warning")
    critical_total = sum(1 for row in rows if row.get("stability") == "critical")

    module_options = filter_visible_values(sorted({row["module_type"] for row in rows if row.get("module_type")}))
    feature_options = sorted({row["feature_type"] for row in rows if row.get("feature_type")})

    return {
        "page_title": "AI İstem Sürüm Karşılaştırması",
        "page_kicker": "Sürüm takibi",
        "page_subtitle": "İstem sürümlerini kalite, geri bildirim ve backlog eğilimiyle kıyaslar.",
        "lookback_days": lookback,
        "rows": rows,
        "summary": {
            "version_total": len(rows),
            "stable_total": stable_total,
            "warning_total": warning_total,
            "critical_total": critical_total,
        },
        "module_options": module_options,
        "feature_options": feature_options,
        "selected_module_type": selected_module_type,
        "selected_feature_type": selected_feature_type,
    }

def build_ai_management_pack(*, lookback_days: int | None = None) -> dict[str, Any]:
    lookback = _safe_int(lookback_days, 30, 1, 365)
    template = get_ai_management_template()
    executive = build_ai_executive_brief(lookback_days=lookback)
    go_live = build_ai_go_live_snapshot(lookback_days=lookback)
    history = build_ai_decision_history_snapshot(lookback_days=lookback, page=1, per_page=12)
    prompt_compare = build_ai_prompt_compare_snapshot(lookback_days=lookback)

    exec_summary = executive.get("executive_summary") or {}
    history_summary = history.get("summary") or {}
    prompt_summary = prompt_compare.get("summary") or {}

    summary_cards = [
        {
            "label": "Yönetişim skoru",
            "value": int(exec_summary.get("governance_score") or 0),
            "tone": "critical" if int(exec_summary.get("critical_alert_total") or 0) > 0 else "info",
        },
        {
            "label": "Karar geçmişi çağrı sayısı",
            "value": int(history_summary.get("request_total") or 0),
            "tone": "info",
        },
        {
            "label": "Açık öneri",
            "value": int(history_summary.get("open_recommendations") or 0),
            "tone": "warning" if int(history_summary.get("open_recommendations") or 0) > 0 else "success",
        },
        {
            "label": "Kritik istem sürümü",
            "value": int(prompt_summary.get("critical_total") or 0),
            "tone": "critical" if int(prompt_summary.get("critical_total") or 0) > 0 else "success",
        },
    ]

    sections = {
        "executive_highlights": list(executive.get("highlights") or [])[:4],
        "risk_watch": list(executive.get("alerts") or [])[:5],
        "priority_actions": list(executive.get("actions") or [])[:5],
        "recent_decisions": list(history.get("rows") or [])[:8],
        "prompt_watch": list(prompt_compare.get("rows") or [])[:8],
        "go_live_gates": list(go_live.get("gates") or [])[:8],
    }

    blockers = [row for row in sections["go_live_gates"] if str(row.get("status") or "") == "fail"]
    risk_total = len(sections["risk_watch"])
    prompt_critical = int(prompt_summary.get("critical_total") or 0)
    open_recommendations = int(history_summary.get("open_recommendations") or 0)

    manager_note = (
        f"Son {lookback} günde AI yönetişim skoru {int(exec_summary.get('governance_score') or 0)} seviyesinde. "
        f"Açık öneri {open_recommendations}, risk maddesi {risk_total}, kritik istem sürümü {prompt_critical}. "
        f"Canlıya alma kontrolünde blokaj sayısı {len(blockers)}."
    )

    distribution_plan = dict(template.get("distribution_plan") or {})
    distribution_plan.setdefault("default_recipients", ["Üst Yönetim", "Personel/İdari İşler", "BT"])
    distribution_plan.setdefault("default_formats", ["markdown", "json", "csv"])
    distribution_plan.setdefault("default_note", "Rapor, insan onayı ve yönetsel gözden geçirme ile paylaşılmalıdır.")

    return {
        "page_title": "AI Yönetici Rapor Paketi",
        "page_kicker": "Rapor paketi",
        "page_subtitle": "Karar geçmişi, istem sürüm görünümü ve yönetişim özetini tek pakette toplar.",
        "lookback_days": lookback,
        "template": template,
        "summary_cards": summary_cards,
        "manager_note": manager_note,
        "executive": executive,
        "go_live": go_live,
        "history": history,
        "prompt_compare": prompt_compare,
        "sections": sections,
        "distribution_plan": distribution_plan,
        "generated_at": utc_now(),
    }

def render_ai_management_pack_markdown(snapshot: dict[str, Any]) -> str:
    lines: list[str] = []
    template = snapshot.get("template") or {}
    lines.append(f"# {template.get('report_title') or 'BYS360 AI Yönetici Rapor Paketi'}")
    lines.append("")
    lines.append(f"_{template.get('report_subtitle') or ''}_")
    lines.append("")
    generated_at = snapshot.get("generated_at")
    if generated_at:
        lines.append(f"- Oluşturulma: {generated_at.strftime('%d.%m.%Y %H:%M')}")
    lines.append(f"- Kapsam: Son {snapshot.get('lookback_days') or 0} gün")
    lines.append("")
    lines.append("## Yönetici Notu")
    lines.append("")
    lines.append(snapshot.get("manager_note") or "-")
    lines.append("")
    lines.append("## Özet Kartlar")
    lines.append("")
    for row in snapshot.get("summary_cards") or []:
        lines.append(f"- **{row.get('label')}**: {row.get('value')}")
    lines.append("")
    lines.append("## Öne Çıkan Başlıklar")
    lines.append("")
    for row in (snapshot.get("sections") or {}).get("executive_highlights") or []:
        lines.append(f"- **{row.get('title') or 'Başlık'}:** {row.get('body') or ''}")
    lines.append("")
    lines.append("## Öncelikli Riskler")
    lines.append("")
    for row in (snapshot.get("sections") or {}).get("risk_watch") or []:
        lines.append(f"- **{row.get('title') or 'Risk'}** ({row.get('severity') or 'bilgi'}): {row.get('body') or ''}")
    lines.append("")
    lines.append("## Son Karar Geçmişi")
    lines.append("")
    for row in (snapshot.get("sections") or {}).get("recent_decisions") or []:
        lines.append(
            f"- **{row.get('module_label')} / {row.get('feature_label')}** · {row.get('prompt_version')} · {row.get('status_label')} · geri bildirim {row.get('feedback_total')} · açık öneri {row.get('open_recommendations')}"
        )
    lines.append("")
    lines.append("## İstem Sürüm İzleme")
    lines.append("")
    for row in (snapshot.get("sections") or {}).get("prompt_watch") or []:
        lines.append(
            f"- **{row.get('module_label')} / {row.get('feature_label')} / {row.get('prompt_version')}** · kalite %{row.get('quality_score')} · başarı %{row.get('success_rate')} · {row.get('comparison_note')}"
        )
    lines.append("")
    lines.append("## Canlıya Alma Kapıları")
    lines.append("")
    for row in (snapshot.get("sections") or {}).get("go_live_gates") or []:
        lines.append(f"- **{row.get('label') or 'Kontrol'}** · {ai_status_label(row.get('status'))}: {row.get('detail') or ''}")
    lines.append("")
    plan = snapshot.get("distribution_plan") or {}
    lines.append("## Paylaşım Planı")
    lines.append("")
    lines.append(f"- Alıcı grupları: {', '.join(plan.get('default_recipients') or [])}")
    lines.append(f"- Formatlar: {', '.join(plan.get('default_formats') or [])}")
    lines.append(f"- Not: {plan.get('default_note') or '-'}")
    lines.append("")
    return "\n".join(lines)