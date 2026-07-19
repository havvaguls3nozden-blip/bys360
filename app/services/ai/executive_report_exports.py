from __future__ import annotations

from app.core.datetime_utils import utc_now
"""Faz 11: AI yönetici ekranı ve güvenli rapor export servisi.

Bu servis yalnızca okuma ve güvenli raporlama yapar. Ham AI istem/yanıt
metinlerini, kişisel verileri ve gerçek içe aktarım satırlarını dışa vermez.
Faz 10 görünürlük/maskeleme kapısı ile uyumlu çalışır; AI nihai karar vermez,
öneri uygulamaz, kayıt oluşturmaz ve kayıt güncellemez.
"""

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any
import json
import re

from sqlalchemy import func

from app.models import AIFeedbackLog, AIRecommendation, AIRequestLog, AIRedactionRule, AISummaryCache
from app.services.ai.module_scope import is_visible_ai_module
try:  # Faz 10 overlay uygulanmışsa güvenli export politikası oradan okunur.
    from app.services.ai.visibility_gate import build_ai_visibility_gate_snapshot
except Exception:  # pragma: no cover - eski canlı paketlerde güvenli geri dönüş
    build_ai_visibility_gate_snapshot = None

# Faz 11 güvenlik sözleşmesi
DB_WRITE_ENABLED = False
AI_FINAL_DECISION_ENABLED = False
AI_AUTO_APPLY_ENABLED = False
RAW_AI_PAYLOAD_EXPORT_ENABLED = False
RAW_AI_PAYLOAD_VISIBLE = False
PERSONAL_DATA_EXPORT_ENABLED = False
SAFE_REPORT_EXPORT_ENABLED = True
KVKK_MASKING_REQUIRED = True
REAL_IMPORT_ENABLED = False
HUMAN_REVIEW_REQUIRED = True
DEFAULT_LOOKBACK_DAYS = 30
MAX_LOOKBACK_DAYS = 180
SLOW_LATENCY_MS = 1800

LIVE_MODULE_ORDER = ("performance", "hr", "survey", "feedback", "communication", "support", "analysis_center", "dashboard")
REMOVED_MODULES = ("education", "strategy", "repository", "portal")
NEGATIVE_FEEDBACK_TYPES = {"not_helpful", "wrong", "unsafe", "incorrect", "negative"}
POSITIVE_FEEDBACK_TYPES = {"helpful", "positive"}

MODULE_LABELS = {
    "performance": "Performans",
    "hr": "Personel / İzin",
    "survey": "Anket",
    "feedback": "Geri Bildirim / Nabız",
    "communication": "İletişim",
    "support": "Yardım Merkezi",
    "analysis_center": "Analiz Merkezi",
    "dashboard": "Dashboard",
    "general": "Genel",
    "genel": "Genel",
    "": "Genel",
}

STATUS_LABELS = {
    "completed": "Tamamlandı",
    "success": "Başarılı",
    "ok": "Başarılı",
    "warning": "Uyarı",
    "watch": "İzleme",
    "failed": "Hata",
    "error": "Hata",
    "open": "Açık",
    "reviewed": "İncelendi",
    "accepted": "Onaylandı",
    "dismissed": "Kapatıldı",
}

SEVERITY_LABELS = {
    "critical": "Kritik",
    "high": "Yüksek",
    "medium": "Orta",
    "low": "Düşük",
    "info": "Bilgi",
    "warning": "Uyarı",
}

EXPORT_COLUMNS = [
    "bolum",
    "modul",
    "gosterge",
    "deger",
    "risk",
    "oncelik",
    "not",
]


def _safe_int(value: Any, default: int, minimum: int = 1, maximum: int = MAX_LOOKBACK_DAYS) -> int:
    try:
        parsed = int(value or default)
    except (TypeError, ValueError):
        parsed = default
    return max(min(parsed, maximum), minimum)


def _clean_key(value: Any, fallback: str = "general") -> str:
    key = str(value or "").strip().lower()
    return key or fallback


def _module_label(value: Any) -> str:
    key = _clean_key(value)
    return MODULE_LABELS.get(key, key.replace("_", " ").title())


def _status_bucket(value: Any) -> str:
    key = _clean_key(value, "completed")
    if key in {"completed", "success", "ok"}:
        return "completed"
    if key in {"failed", "error", "fail"}:
        return "failed"
    if key in {"warning", "watch", "warn"}:
        return "warning"
    return key


def _status_label(value: Any) -> str:
    return STATUS_LABELS.get(_clean_key(value), str(value or "-").title())


def _severity_label(value: Any) -> str:
    return SEVERITY_LABELS.get(_clean_key(value, "info"), str(value or "Bilgi").title())


def _ratio(part: int, whole: int) -> int:
    if not whole:
        return 0
    return int(round((int(part or 0) / int(whole or 1)) * 100))


def _avg(values: list[int]) -> int:
    values = [int(v or 0) for v in values if v is not None]
    if not values:
        return 0
    return int(round(sum(values) / len(values)))


def _safe_text(value: Any, limit: int = 160) -> str:
    text = " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())
    if not text:
        return "-"
    text = re.sub(r"\b\d{11}\b", "***********", text)
    text = re.sub(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", "***@***", text)
    text = re.sub(r"\bTR\d{2}[0-9A-Z]{20,}\b", "TR**********************", text, flags=re.I)
    if len(text) > limit:
        return text[: max(limit - 1, 0)].rstrip() + "…"
    return text


def _since(days: int) -> datetime:
    return utc_now() - timedelta(days=_safe_int(days, DEFAULT_LOOKBACK_DAYS))


def _visible_query(query, column):
    hidden = [key for key in REMOVED_MODULES if not is_visible_ai_module(key)]
    if hidden:
        query = query.filter(func.lower(func.coalesce(column, "")).notin_(hidden))
    return query


def _request_rows(since: datetime, module_type: str = "") -> list[AIRequestLog]:
    query = AIRequestLog.query.filter(AIRequestLog.created_at >= since)
    query = _visible_query(query, AIRequestLog.module_type)
    if module_type:
        query = query.filter(func.lower(AIRequestLog.module_type) == module_type)
    return query.order_by(AIRequestLog.created_at.desc()).limit(5000).all()


def _recommendation_rows(since: datetime, module_type: str = "") -> list[AIRecommendation]:
    query = AIRecommendation.query.filter(AIRecommendation.created_at >= since)
    query = _visible_query(query, AIRecommendation.module_type)
    if module_type:
        query = query.filter(func.lower(AIRecommendation.module_type) == module_type)
    return query.order_by(AIRecommendation.created_at.desc(), AIRecommendation.id.desc()).limit(5000).all()


def _feedback_rows(since: datetime, module_type: str = "") -> list[AIFeedbackLog]:
    query = (
        AIFeedbackLog.query
        .join(AIRequestLog, AIFeedbackLog.ai_request_log_id == AIRequestLog.id)
        .filter(AIFeedbackLog.created_at >= since)
    )
    query = _visible_query(query, AIRequestLog.module_type)
    if module_type:
        query = query.filter(func.lower(AIRequestLog.module_type) == module_type)
    return query.order_by(AIFeedbackLog.created_at.desc()).limit(5000).all()


def _redaction_count(module_type: str = "") -> int:
    query = AIRedactionRule.query.filter(AIRedactionRule.is_active.is_(True))
    query = _visible_query(query, AIRedactionRule.module_type)
    if module_type:
        query = query.filter(func.lower(AIRedactionRule.module_type) == module_type)
    return int(query.count() or 0)


def _summary_cache_count(module_type: str = "") -> int:
    query = AISummaryCache.query
    query = _visible_query(query, AISummaryCache.module_type)
    if module_type:
        query = query.filter(func.lower(AISummaryCache.module_type) == module_type)
    return int(query.count() or 0)


def _risk_label(score: int) -> str:
    if score >= 80:
        return "Kritik"
    if score >= 60:
        return "Yüksek"
    if score >= 35:
        return "Orta"
    return "Düşük"


def _risk_tone(score: int) -> str:
    if score >= 80:
        return "danger"
    if score >= 60:
        return "warning"
    if score >= 35:
        return "calm"
    return "success"


def _export_policy(current_user: Any | None, lookback_days: int, module_type: str) -> dict[str, Any]:
    if build_ai_visibility_gate_snapshot is None:
        return {
            "can_export_safe_csv": True,
            "kvkk_masking_required": True,
            "raw_payload_visible": False,
            "note": "Faz 10 servisi bulunamadı; güvenli varsayılan export politikası uygulandı.",
        }
    try:
        snapshot = build_ai_visibility_gate_snapshot(
            current_user=current_user,
            lookback_days=lookback_days,
            module_type=module_type,
            role_name="",
        )
        policy = dict(snapshot.get("current_policy") or {})
    except Exception:
        policy = {}
    return {
        "can_export_safe_csv": bool(policy.get("can_export_safe_csv", True)),
        "kvkk_masking_required": True,
        "raw_payload_visible": False,
        "note": policy.get("note") or "Faz 10 görünürlük kapısı güvenli export sınırını belirler.",
    }


def _module_rows(requests: list[AIRequestLog], recommendations: list[AIRecommendation], feedbacks: list[AIFeedbackLog]) -> list[dict[str, Any]]:
    request_by_module: dict[str, list[AIRequestLog]] = defaultdict(list)
    for row in requests:
        request_by_module[_clean_key(row.module_type)].append(row)

    recommendation_by_module: Counter[str] = Counter()
    critical_recommendation_by_module: Counter[str] = Counter()
    open_recommendation_by_module: Counter[str] = Counter()
    for row in recommendations:
        module = _clean_key(row.module_type)
        recommendation_by_module[module] += 1
        if _clean_key(row.status, "open") == "open":
            open_recommendation_by_module[module] += 1
        if _clean_key(row.severity, "info") in {"critical", "high", "warning"}:
            critical_recommendation_by_module[module] += 1

    feedback_by_module: Counter[str] = Counter()
    # AIFeedbackLog üzerinde modül yok; ilişki varsa güvenli okunur.
    for row in feedbacks:
        request = getattr(row, "ai_request_log", None)
        module = _clean_key(getattr(request, "module_type", "general"))
        if _clean_key(row.feedback_type) in NEGATIVE_FEEDBACK_TYPES:
            feedback_by_module[module] += 1

    module_keys = list(LIVE_MODULE_ORDER)
    for key in sorted(set(request_by_module) | set(recommendation_by_module) | set(feedback_by_module)):
        if key not in module_keys and is_visible_ai_module(key):
            module_keys.append(key)

    rows: list[dict[str, Any]] = []
    for key in module_keys:
        reqs = request_by_module.get(key, [])
        total = len(reqs)
        failed = sum(1 for row in reqs if _status_bucket(row.status) == "failed")
        warning = sum(1 for row in reqs if _status_bucket(row.status) == "warning")
        masked = sum(1 for row in reqs if bool(getattr(row, "was_masked", True)))
        unmasked = max(total - masked, 0)
        slow = sum(1 for row in reqs if int(row.latency_ms or 0) >= SLOW_LATENCY_MS)
        avg_latency = _avg([int(row.latency_ms or 0) for row in reqs])
        open_rec = int(open_recommendation_by_module.get(key) or 0)
        critical_rec = int(critical_recommendation_by_module.get(key) or 0)
        negative = int(feedback_by_module.get(key) or 0)
        risk_score = min(
            100,
            _ratio(failed, total) * 2
            + _ratio(unmasked, total) * 2
            + min(open_rec * 5, 25)
            + min(critical_rec * 9, 25)
            + min(negative * 7, 20)
            + min(slow * 4, 15),
        )
        rows.append(
            {
                "module_type": key,
                "module_label": _module_label(key),
                "request_total": total,
                "failed_total": failed,
                "warning_total": warning,
                "masked_rate": _ratio(masked, total),
                "unmasked_total": unmasked,
                "avg_latency_ms": avg_latency,
                "slow_total": slow,
                "open_recommendations": open_rec,
                "critical_recommendations": critical_rec,
                "negative_feedback": negative,
                "risk_score": int(risk_score),
                "risk_label": _risk_label(int(risk_score)),
                "tone": _risk_tone(int(risk_score)),
                "progress_width": max(int(risk_score), 4 if risk_score else 0),
                "action_note": _module_action_note(key, int(risk_score), failed, unmasked, open_rec, critical_rec, negative),
            }
        )
    return sorted(rows, key=lambda item: (item["risk_score"], item["open_recommendations"], item["request_total"]), reverse=True)


def _module_action_note(module: str, score: int, failed: int, unmasked: int, open_rec: int, critical_rec: int, negative: int) -> str:
    if unmasked:
        return "Maskeleme kapısı ve export kapsamı öncelikli kontrol edilmeli."
    if failed:
        return "Hatalı AI çağrıları ve sağlayıcı/istem konfigürasyonu gözden geçirilmeli."
    if critical_rec or open_rec >= 3:
        return "Açık öneriler yönetici inceleme kuyruğunda önceliklendirilmeli."
    if negative:
        return "Negatif geri bildirimler örnek kayıtlarla birlikte kalite panosunda incelenmeli."
    if score >= 35:
        return "Düzenli izleme ve haftalık rapor akışına alınmalı."
    return "Aktif kritik risk görünmüyor; standart izleme yeterli."


def _executive_cards(summary: dict[str, int]) -> list[dict[str, Any]]:
    return [
        {
            "label": "Yönetici görünümü",
            "value": summary["request_total"],
            "note": "Son dönem AI işlem hacmi. Ham istem/yanıt metni gösterilmez.",
            "tone": "calm",
            "icon": "fa-chart-line",
        },
        {
            "label": "Güvenli maskeleme",
            "value": f"%{summary['masked_rate']}",
            "note": f"Maskeli {summary['masked_total']} · maskesiz {summary['unmasked_total']} kayıt.",
            "tone": "success" if summary["unmasked_total"] == 0 else "warning",
            "icon": "fa-user-shield",
        },
        {
            "label": "Açık öneri",
            "value": summary["open_recommendations"],
            "note": "AI önerileri insan onayı olmadan uygulanmaz.",
            "tone": "warning" if summary["open_recommendations"] else "success",
            "icon": "fa-list-check",
        },
        {
            "label": "Export güvenliği",
            "value": "Güvenli",
            "note": "CSV/JSON/MD çıktıları kişisel veri ve ham AI metni içermez.",
            "tone": "success",
            "icon": "fa-file-export",
        },
    ]


def _action_queue(module_rows: list[dict[str, Any]], summary: dict[str, int]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    if summary["unmasked_total"]:
        actions.append({
            "priority": "Kritik",
            "title": "Maskesiz AI kayıtları kontrol edilmeli",
            "body": "Faz 10 görünürlük kapısı ve redaction kuralları yeniden doğrulanmalı.",
            "tone": "danger",
        })
    for row in module_rows[:6]:
        if row["risk_score"] >= 35 or row["open_recommendations"] or row["failed_total"]:
            actions.append({
                "priority": row["risk_label"],
                "title": f"{row['module_label']} için yönetici incelemesi",
                "body": row["action_note"],
                "tone": row["tone"],
            })
    if not actions:
        actions.append({
            "priority": "İzleme",
            "title": "Kritik aksiyon görünmüyor",
            "body": "AI rapor kartları haftalık yönetici rapor akışında izlenmeye devam etmeli.",
            "tone": "success",
        })
    return actions[:8]


def _recommendation_cards(recommendations: list[AIRecommendation]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for row in recommendations[:12]:
        status = _clean_key(row.status, "open")
        severity = _clean_key(row.severity, "info")
        if status not in {"open", "review", "pending"} and severity not in {"critical", "high", "warning"}:
            continue
        cards.append(
            {
                "module_label": _module_label(row.module_type),
                "title": _safe_text(row.title, 120),
                "body": _safe_text(row.body, 200),
                "status_label": _status_label(row.status),
                "severity_label": _severity_label(row.severity),
                "tone": "danger" if severity == "critical" else "warning" if severity in {"high", "warning"} else "calm",
            }
        )
    return cards[:8]


def build_ai_executive_report_snapshot(
    *,
    current_user: Any | None = None,
    lookback_days: Any = DEFAULT_LOOKBACK_DAYS,
    module_type: str = "",
) -> dict[str, Any]:
    """Faz 11 yönetici ekranı için salt-okunur rapor bağlamı üretir."""
    days = _safe_int(lookback_days, DEFAULT_LOOKBACK_DAYS)
    module = _clean_key(module_type, "") if module_type else ""
    if module and not is_visible_ai_module(module):
        module = ""
    cutoff = _since(days)

    requests = _request_rows(cutoff, module)
    recommendations = _recommendation_rows(cutoff, module)
    feedbacks = _feedback_rows(cutoff, module)
    active_redaction_rules = _redaction_count(module)
    summary_cache_total = _summary_cache_count(module)

    request_total = len(requests)
    completed_total = sum(1 for row in requests if _status_bucket(row.status) == "completed")
    failed_total = sum(1 for row in requests if _status_bucket(row.status) == "failed")
    warning_total = sum(1 for row in requests if _status_bucket(row.status) == "warning")
    masked_total = sum(1 for row in requests if bool(getattr(row, "was_masked", True)))
    unmasked_total = max(request_total - masked_total, 0)
    slow_total = sum(1 for row in requests if int(row.latency_ms or 0) >= SLOW_LATENCY_MS)
    avg_latency_ms = _avg([int(row.latency_ms or 0) for row in requests])
    open_recommendations = sum(1 for row in recommendations if _clean_key(row.status, "open") == "open")
    critical_recommendations = sum(1 for row in recommendations if _clean_key(row.severity, "info") in {"critical", "high", "warning"})
    negative_feedback = sum(1 for row in feedbacks if _clean_key(row.feedback_type) in NEGATIVE_FEEDBACK_TYPES)
    positive_feedback = sum(1 for row in feedbacks if _clean_key(row.feedback_type) in POSITIVE_FEEDBACK_TYPES)

    summary = {
        "request_total": request_total,
        "completed_total": completed_total,
        "failed_total": failed_total,
        "warning_total": warning_total,
        "masked_total": masked_total,
        "unmasked_total": unmasked_total,
        "masked_rate": _ratio(masked_total, request_total),
        "avg_latency_ms": avg_latency_ms,
        "slow_total": slow_total,
        "recommendation_total": len(recommendations),
        "open_recommendations": open_recommendations,
        "critical_recommendations": critical_recommendations,
        "feedback_total": len(feedbacks),
        "negative_feedback": negative_feedback,
        "positive_feedback": positive_feedback,
        "active_redaction_rules": active_redaction_rules,
        "summary_cache_total": summary_cache_total,
    }
    module_rows = _module_rows(requests, recommendations, feedbacks)
    visibility_policy = _export_policy(current_user, days, module)
    module_options = [
        {"value": key, "label": _module_label(key)}
        for key in LIVE_MODULE_ORDER
        if is_visible_ai_module(key)
    ]
    return {
        "page_title": "AI Yönetici Rapor ve Export Merkezi",
        "page_kicker": "Faz 11 · Yönetici ekranları",
        "page_subtitle": "AI sinyallerini yönetici özetine, güvenli rapor kartlarına ve KVKK uyumlu export çıktısına dönüştürür.",
        "lookback_days": days,
        "selected_module_type": module,
        "module_options": module_options,
        "summary": summary,
        "executive_cards": _executive_cards(summary),
        "module_rows": module_rows,
        "action_queue": _action_queue(module_rows, summary),
        "recommendation_cards": _recommendation_cards(recommendations),
        "visibility_policy": visibility_policy,
        "export_formats": [
            {"label": "CSV", "href_suffix": "csv", "note": "Tablo ve aksiyon satırları"},
            {"label": "JSON", "href_suffix": "json", "note": "Sistem entegrasyonu için güvenli özet"},
            {"label": "MD", "href_suffix": "md", "note": "Yönetici notu / rapor metni"},
        ],
        "safety_contract": {
            "db_write_enabled": DB_WRITE_ENABLED,
            "raw_ai_payload_visible": RAW_AI_PAYLOAD_VISIBLE,
            "raw_ai_payload_export_enabled": RAW_AI_PAYLOAD_EXPORT_ENABLED,
            "personal_data_export_enabled": PERSONAL_DATA_EXPORT_ENABLED,
            "kvkk_masking_required": KVKK_MASKING_REQUIRED,
            "human_review_required": HUMAN_REVIEW_REQUIRED,
            "real_import_enabled": REAL_IMPORT_ENABLED,
        },
        "generated_at": utc_now(),
    }


def build_ai_executive_report_export_rows(snapshot: dict[str, Any]) -> list[list[Any]]:
    """Ham AI metni veya kişisel veri içermeyen güvenli export satırları."""
    rows: list[list[Any]] = []
    summary = snapshot.get("summary") or {}
    rows.append(["özet", "Genel", "Toplam AI işlem", summary.get("request_total", 0), "-", "İzleme", "Ham AI metni dahil değildir."])
    rows.append(["özet", "Genel", "Maskeleme oranı", f"%{summary.get('masked_rate', 0)}", "KVKK", "Yüksek", "Maskesiz kayıt varsa Faz 10 görünürlük kapısı kontrol edilmeli."])
    rows.append(["özet", "Genel", "Açık öneri", summary.get("open_recommendations", 0), "İş yükü", "Orta", "AI önerileri insan onayı olmadan uygulanmaz."])
    for row in snapshot.get("module_rows") or []:
        rows.append([
            "modül",
            row.get("module_label"),
            "Risk skoru",
            row.get("risk_score"),
            row.get("risk_label"),
            row.get("risk_label"),
            row.get("action_note"),
        ])
        rows.append([
            "modül",
            row.get("module_label"),
            "Açık öneri / hata / maskeleme",
            f"{row.get('open_recommendations', 0)} / {row.get('failed_total', 0)} / %{row.get('masked_rate', 0)}",
            row.get("risk_label"),
            row.get("risk_label"),
            "Güvenli metrik satırı; kişisel veri içermez.",
        ])
    for action in snapshot.get("action_queue") or []:
        rows.append([
            "aksiyon",
            "Yönetici",
            action.get("title"),
            action.get("priority"),
            action.get("priority"),
            action.get("priority"),
            action.get("body"),
        ])
    return rows


def render_ai_executive_report_markdown(snapshot: dict[str, Any]) -> str:
    summary = snapshot.get("summary") or {}
    lines = [
        "# BYS360 AI Yönetici Rapor ve Export Merkezi",
        "",
        f"Dönem: Son {snapshot.get('lookback_days')} gün",
        "",
        "> Bu rapor ham AI istem/yanıt metni ve kişisel veri içermez. AI nihai idari karar vermez; yönetici incelemesi için güvenli sinyal üretir.",
        "",
        "## Özet",
        f"- Toplam AI işlem: {summary.get('request_total', 0)}",
        f"- Maskeleme oranı: %{summary.get('masked_rate', 0)}",
        f"- Açık öneri: {summary.get('open_recommendations', 0)}",
        f"- Hata/Uyarı: {summary.get('failed_total', 0)} / {summary.get('warning_total', 0)}",
        f"- Ortalama gecikme: {summary.get('avg_latency_ms', 0)} ms",
        "",
        "## Modül bazlı risk",
    ]
    for row in snapshot.get("module_rows") or []:
        lines.append(f"- **{row.get('module_label')}** — risk {row.get('risk_score')} ({row.get('risk_label')}): {row.get('action_note')}")
    lines.extend(["", "## Yönetici aksiyonları"])
    for action in snapshot.get("action_queue") or []:
        lines.append(f"- **{action.get('priority')}** · {action.get('title')}: {action.get('body')}")
    lines.extend(["", "## Güvenlik sözleşmesi", "- DB yazımı yok", "- Ham AI metni export edilmez", "- KVKK maskeleme zorunlu", "- İnsan onayı zorunlu"])
    return "\n".join(lines) + "\n"


def to_safe_json_payload(snapshot: dict[str, Any]) -> dict[str, Any]:
    """JSON export için tarihleri stringe çevirir ve ham metin alanlarını dışarıda bırakır."""
    return {
        "page_title": snapshot.get("page_title"),
        "lookback_days": snapshot.get("lookback_days"),
        "selected_module_type": snapshot.get("selected_module_type"),
        "summary": snapshot.get("summary") or {},
        "module_rows": snapshot.get("module_rows") or [],
        "action_queue": snapshot.get("action_queue") or [],
        "visibility_policy": snapshot.get("visibility_policy") or {},
        "safety_contract": snapshot.get("safety_contract") or {},
        "generated_at": str(snapshot.get("generated_at") or ""),
    }


def dumps_safe_json(snapshot: dict[str, Any]) -> str:
    return json.dumps(to_safe_json_payload(snapshot), ensure_ascii=False, indent=2, default=str)
