from __future__ import annotations

from app.core.datetime_utils import utc_now
"""Faz 12: AI Karar Destek / Analiz Merkezi final canlı sertleştirme servisi.

Bu servis kapanış raporu, kalite kapısı ve canlı güvenlik duruşunu salt-okunur
şekilde üretir. Veritabanına yazmaz, migration çalıştırmaz, gerçek içe aktarım
yapmaz, ham AI istem/yanıt metnini panelde veya export içinde açmaz.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
import json

from flask import current_app
from sqlalchemy import func

from app.models import AIFeedbackLog, AIRecommendation, AIRequestLog, AIRedactionRule, AISummaryCache
from app.security_audit import build_security_audit_summary
from app.services.ai.module_scope import is_visible_ai_module, scope_visible_modules
from app.services.ai.schema_guard import get_ai_schema_status
try:
    from app.services.ai.visibility_gate import build_ai_visibility_gate_snapshot
except Exception:  # pragma: no cover - Faz 10 öncesi paketlerde güvenli geri dönüş
    build_ai_visibility_gate_snapshot = None

# Faz 12 güvenlik sözleşmesi
DB_WRITE_ENABLED = False
MIGRATION_INCLUDED = False
ENV_FILE_INCLUDED = False
REAL_IMPORT_ENABLED = False
AI_FINAL_DECISION_ENABLED = False
AI_AUTO_APPLY_ENABLED = False
RAW_AI_PAYLOAD_VISIBLE = False
RAW_AI_PAYLOAD_EXPORT_ENABLED = False
PERSONAL_DATA_EXPORT_ENABLED = False
KVKK_MASKING_REQUIRED = True
HUMAN_REVIEW_REQUIRED = True
SAFE_EXPORT_ENABLED = True
LIVE_HARDENING_GATE_ENABLED = True
STARTUP_WARNING_FIX_APPLIED = True
DEFAULT_LOOKBACK_DAYS = 30
MAX_LOOKBACK_DAYS = 180
SLOW_LATENCY_MS = 1800

LIVE_MODULE_LABELS = {
    "performance": "Performans",
    "hr": "Personel / izin-vekalet",
    "survey": "Anket",
    "feedback": "Geri bildirim / nabız",
    "communication": "İletişim",
    "support": "Yardım merkezi",
    "analysis_center": "Analiz Merkezi",
    "dashboard": "Dashboard",
}

REMOVED_MODULES = {"education", "strategy", "repository", "portal"}
EXPORT_COLUMNS = [
    "kapı",
    "durum",
    "risk",
    "bulgu",
    "aksiyon",
]


def _safe_int(value: Any, default: int = DEFAULT_LOOKBACK_DAYS, minimum: int = 1, maximum: int = MAX_LOOKBACK_DAYS) -> int:
    try:
        parsed = int(value or default)
    except (TypeError, ValueError):
        parsed = default
    return max(min(parsed, maximum), minimum)


def _lower(value: Any) -> str:
    return str(value or "").strip().lower()


def _pct(part: int, total: int) -> int:
    if not total:
        return 100
    return int(round((part / total) * 100))


def _tone_from_score(score: int) -> str:
    if score >= 90:
        return "success"
    if score >= 75:
        return "calm"
    if score >= 55:
        return "warning"
    return "danger"


def _module_label(module_type: Any) -> str:
    key = _lower(module_type)
    return LIVE_MODULE_LABELS.get(key, key.replace("_", " ").title() if key else "Genel")


def _now() -> datetime:
    return utc_now()


def _security_snapshot() -> dict[str, Any]:
    summary = build_security_audit_summary(current_app.config)
    counts = dict(summary.get("counts") or {})
    findings = list(summary.get("findings") or [])
    warnings = [item for item in findings if item.get("level") == "warning"]
    criticals = [item for item in findings if item.get("level") == "critical"]
    infos = [item for item in findings if item.get("level") == "info"]
    return {
        "counts": counts,
        "findings": findings,
        "warnings": warnings,
        "criticals": criticals,
        "infos": infos,
        "warning_count": int(counts.get("warning") or 0),
        "critical_count": int(counts.get("critical") or 0),
        "info_count": int(counts.get("info") or 0),
    }


def _visibility_policy(current_user: Any) -> dict[str, Any]:
    if build_ai_visibility_gate_snapshot is None:
        return {
            "can_export_safe_csv": True,
            "raw_payload_visible": False,
            "kvkk_masking_required": True,
            "note": "Faz 10 görünürlük kapısı bulunamadı; Faz 12 güvenli varsayılanlarla çalışıyor.",
        }
    try:
        snapshot = build_ai_visibility_gate_snapshot(current_user=current_user, module_type="analysis_center")
        return dict(snapshot.get("current_policy") or {}) | {
            "raw_payload_visible": False,
            "kvkk_masking_required": True,
        }
    except Exception:
        return {
            "can_export_safe_csv": True,
            "raw_payload_visible": False,
            "kvkk_masking_required": True,
            "note": "Faz 10 görünürlük kapısı okunamadı; güvenli export sınırı korunuyor.",
        }


def _phase_gate_rows(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    phase_specs = [
        (7, "Excel yükleme ve güvenli veri ön izleme", "scripts/check_ai_decision_analytics_faz7_gate.py"),
        (8, "Grafik / rapor kartları", "scripts/check_ai_decision_analytics_faz8_gate.py"),
        (9, "AI öneri motoru ve risk öncelik paneli", "scripts/check_ai_decision_analytics_faz9_gate.py"),
        (10, "Yetki, KVKK maskeleme ve görünürlük kapısı", "scripts/check_ai_decision_analytics_faz10_gate.py"),
        (11, "Yönetici ekranları ve güvenli export", "scripts/check_ai_decision_analytics_faz11_gate.py"),
        (12, "Final canlı sertleştirme ve kapanış raporu", "scripts/check_ai_decision_analytics_faz12_gate.py"),
    ]
    for phase, title, rel in phase_specs:
        exists = (root / rel).exists()
        rows.append(
            {
                "phase": phase,
                "title": title,
                "command": f"python -S {rel}",
                "status": "hazır" if exists or phase == 12 else "kontrol edilmeli",
                "tone": "success" if exists or phase == 12 else "warning",
                "note": "Gate dosyası mevcut." if exists else "Overlay sonrası gate dosyası beklenir.",
            }
        )
    return rows


def _module_rows(requests: list[AIRequestLog], recommendations: list[AIRecommendation], feedbacks: list[AIFeedbackLog]) -> list[dict[str, Any]]:
    req_by_module: dict[str, list[AIRequestLog]] = defaultdict(list)
    rec_by_module: dict[str, list[AIRecommendation]] = defaultdict(list)
    fb_by_module: dict[str, list[AIFeedbackLog]] = defaultdict(list)
    for row in requests:
        key = _lower(row.module_type) or "genel"
        if is_visible_ai_module(key):
            req_by_module[key].append(row)
    for row in recommendations:
        key = _lower(row.module_type) or "genel"
        if is_visible_ai_module(key):
            rec_by_module[key].append(row)
    for row in feedbacks:
        req = getattr(row, "ai_request_log", None)
        key = _lower(getattr(req, "module_type", "")) or "genel"
        if is_visible_ai_module(key):
            fb_by_module[key].append(row)

    modules = sorted(set(req_by_module) | set(rec_by_module) | set(fb_by_module))
    output: list[dict[str, Any]] = []
    for module in modules:
        reqs = req_by_module.get(module, [])
        recs = rec_by_module.get(module, [])
        fbs = fb_by_module.get(module, [])
        request_total = len(reqs)
        failed_total = sum(1 for row in reqs if _lower(row.status) in {"failed", "error", "warning"})
        unmasked_total = sum(1 for row in reqs if getattr(row, "was_masked", True) is False)
        slow_total = sum(1 for row in reqs if int(row.latency_ms or 0) >= SLOW_LATENCY_MS)
        open_recommendations = sum(1 for row in recs if _lower(row.status) == "open")
        critical_recommendations = sum(1 for row in recs if _lower(row.severity) in {"critical", "high"})
        negative_feedback = sum(1 for row in fbs if _lower(row.feedback_type) in {"not_helpful", "wrong", "negative"})
        risk_score = min(100, failed_total * 18 + unmasked_total * 25 + slow_total * 8 + open_recommendations * 9 + critical_recommendations * 16 + negative_feedback * 12)
        quality_score = max(0, 100 - risk_score)
        output.append(
            {
                "module_type": module,
                "module_label": _module_label(module),
                "request_total": request_total,
                "failed_total": failed_total,
                "unmasked_total": unmasked_total,
                "slow_total": slow_total,
                "open_recommendations": open_recommendations,
                "critical_recommendations": critical_recommendations,
                "negative_feedback": negative_feedback,
                "risk_score": risk_score,
                "quality_score": quality_score,
                "tone": _tone_from_score(quality_score),
                "status_label": "Temiz" if risk_score == 0 else "İzlenmeli" if risk_score < 45 else "Öncelikli kontrol",
                "action": "Kritik veri yazımı yok; ilgili panelden insan incelemesi yapılmalı." if risk_score else "Düzenli izleme yeterli.",
            }
        )
    return sorted(output, key=lambda item: (item["risk_score"], item["request_total"]), reverse=True)


def _readiness_gates(*, security: dict[str, Any], schema_status: dict[str, Any], summary: dict[str, Any], visibility_policy: dict[str, Any]) -> list[dict[str, Any]]:
    gates = [
        {
            "key": "schema",
            "label": "AI şema kapısı",
            "ok": bool(schema_status.get("ready")),
            "finding": schema_status.get("message") or "Şema kontrolü okunamadı.",
            "action": "Eksik tablo/kolon varsa migration/onarım tamamlanmalı.",
        },
        {
            "key": "security",
            "label": "Runtime güvenlik özeti",
            "ok": security.get("critical_count", 0) == 0 and security.get("warning_count", 0) == 0,
            "finding": f"critical={security.get('critical_count', 0)} warning={security.get('warning_count', 0)} info={security.get('info_count', 0)}",
            "action": "Warning kalırsa Faz 12 uyarı tanı ekranından kodu ve düzeltme notunu kontrol et.",
        },
        {
            "key": "kvkk",
            "label": "KVKK maskeleme",
            "ok": int(summary.get("unmasked_requests") or 0) == 0 and KVKK_MASKING_REQUIRED,
            "finding": f"Maskesiz AI kayıt: {summary.get('unmasked_requests', 0)}",
            "action": "Maskesiz kayıt varsa redaction kuralı ve üretim akışı gözden geçirilmeli.",
        },
        {
            "key": "visibility",
            "label": "Güvenli görünürlük kapısı",
            "ok": not bool(visibility_policy.get("raw_payload_visible")) and bool(visibility_policy.get("kvkk_masking_required", True)),
            "finding": "Ham AI metni kapalı; güvenli export politikası aktif.",
            "action": "Rapor/export yalnız rol bazlı yönetici görünürlüğünde kalmalı.",
        },
        {
            "key": "readonly",
            "label": "Salt-okunur sözleşme",
            "ok": not DB_WRITE_ENABLED and not REAL_IMPORT_ENABLED and not AI_AUTO_APPLY_ENABLED,
            "finding": "DB yazımı, gerçek içe aktarım ve otomatik uygulama kapalı.",
            "action": "Bu faz yalnız kapanış raporu ve kalite kapısı üretir.",
        },
        {
            "key": "export",
            "label": "Güvenli export",
            "ok": SAFE_EXPORT_ENABLED and not RAW_AI_PAYLOAD_EXPORT_ENABLED and not PERSONAL_DATA_EXPORT_ENABLED,
            "finding": "Export ham istem/yanıt ve kişisel veri içermez.",
            "action": "CSV/JSON/MD çıktıları yalnız özet, risk, metrik ve aksiyon satırı vermeli.",
        },
        {
            "key": "human_review",
            "label": "İnsan onayı",
            "ok": HUMAN_REVIEW_REQUIRED and not AI_FINAL_DECISION_ENABLED,
            "finding": "AI nihai karar vermez; öneri otomatik uygulanmaz.",
            "action": "Yönetsel karar insan onayıyla verilmelidir.",
        },
    ]
    for gate in gates:
        gate["status"] = "Geçti" if gate["ok"] else "Kontrol"
        gate["tone"] = "success" if gate["ok"] else "warning"
    return gates


def _action_queue(readiness_gates: list[dict[str, Any]], security: dict[str, Any], summary: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for item in readiness_gates:
        if not item.get("ok"):
            actions.append({"priority": "Yüksek", "tone": "warning", "title": item["label"], "body": item["action"]})
    for finding in security.get("warnings") or []:
        actions.append({"priority": "Yüksek", "tone": "warning", "title": finding.get("code", "security_warning"), "body": finding.get("action") or finding.get("message")})
    if summary.get("open_recommendations"):
        actions.append({"priority": "Orta", "tone": "calm", "title": "Açık AI önerileri", "body": f"{summary.get('open_recommendations')} açık öneri yönetici incelemesine alınmalı."})
    if not actions:
        actions.append({"priority": "Düşük", "tone": "success", "title": "Faz 12 kapanış durumu temiz", "body": "Kritik veya uyarı seviyesinde açık kapı görünmüyor; düzenli izleme yeterli."})
    return actions[:8]


def build_ai_final_live_hardening_snapshot(*, current_user: Any, lookback_days: Any = DEFAULT_LOOKBACK_DAYS) -> dict[str, Any]:
    lookback_days = _safe_int(lookback_days)
    cutoff = _now() - timedelta(days=lookback_days)
    root = Path(current_app.root_path).resolve().parent

    request_query = scope_visible_modules(AIRequestLog.query.filter(AIRequestLog.created_at >= cutoff), AIRequestLog.module_type)
    recommendation_query = scope_visible_modules(AIRecommendation.query.filter(AIRecommendation.created_at >= cutoff), AIRecommendation.module_type)
    feedback_query = AIFeedbackLog.query.join(AIRequestLog, AIFeedbackLog.ai_request_log_id == AIRequestLog.id).filter(AIFeedbackLog.created_at >= cutoff)
    feedback_query = scope_visible_modules(feedback_query, AIRequestLog.module_type)

    requests = request_query.order_by(AIRequestLog.created_at.desc(), AIRequestLog.id.desc()).limit(500).all()
    recommendations = recommendation_query.order_by(AIRecommendation.created_at.desc(), AIRecommendation.id.desc()).limit(500).all()
    feedbacks = feedback_query.order_by(AIFeedbackLog.created_at.desc(), AIFeedbackLog.id.desc()).limit(500).all()

    request_total = request_query.count()
    completed_total = request_query.filter(func.lower(AIRequestLog.status) == "completed").count()
    failed_total = request_query.filter(func.lower(AIRequestLog.status).in_(["failed", "error", "warning"])).count()
    unmasked_requests = request_query.filter(AIRequestLog.was_masked.is_(False)).count()
    masked_requests = max(request_total - unmasked_requests, 0)
    open_recommendations = recommendation_query.filter(func.lower(AIRecommendation.status) == "open").count()
    critical_recommendations = recommendation_query.filter(func.lower(func.coalesce(AIRecommendation.severity, "info")).in_(["critical", "high"])).count()
    active_rules = AIRedactionRule.query.filter(AIRedactionRule.is_active.is_(True)).count()
    feedback_negative = feedback_query.filter(func.lower(AIFeedbackLog.feedback_type).in_(["not_helpful", "wrong", "negative"])).count()
    stale_cache = AISummaryCache.query.filter(AISummaryCache.expires_at.isnot(None), AISummaryCache.expires_at < _now()).count()
    avg_latency = request_query.with_entities(func.avg(AIRequestLog.latency_ms)).scalar() or 0
    slow_total = request_query.filter(AIRequestLog.latency_ms >= SLOW_LATENCY_MS).count()
    prompt_versions = request_query.with_entities(AIRequestLog.prompt_version).distinct().count()

    security = _security_snapshot()
    schema_status = get_ai_schema_status()
    visibility_policy = _visibility_policy(current_user)

    summary = {
        "request_total": int(request_total or 0),
        "completed_total": int(completed_total or 0),
        "failed_total": int(failed_total or 0),
        "masked_requests": int(masked_requests or 0),
        "unmasked_requests": int(unmasked_requests or 0),
        "masked_rate": _pct(int(masked_requests or 0), int(request_total or 0)),
        "open_recommendations": int(open_recommendations or 0),
        "critical_recommendations": int(critical_recommendations or 0),
        "active_rules": int(active_rules or 0),
        "feedback_negative": int(feedback_negative or 0),
        "stale_cache": int(stale_cache or 0),
        "avg_latency_ms": int(round(float(avg_latency or 0))),
        "slow_total": int(slow_total or 0),
        "prompt_versions": int(prompt_versions or 0),
    }
    readiness_gates = _readiness_gates(security=security, schema_status=schema_status, summary=summary, visibility_policy=visibility_policy)
    passed = sum(1 for row in readiness_gates if row["ok"])
    total = len(readiness_gates)
    readiness_score = int(round((passed / total) * 100)) if total else 0

    warning_fix_note = "Development ortamındaki kısa SECRET_KEY artık canlı warning gibi sayılmaz; production/staging için uyarı korunur."
    return {
        "page_title": "AI Final Canlı Sertleştirme ve Kapanış Raporu",
        "page_kicker": "Faz 12 · Kalite kapısı",
        "page_subtitle": "AI Karar Destek / Analiz Merkezi fazlarını canlıya hazırlayan son kontrol, güvenlik uyarı tanısı ve kapanış raporu.",
        "lookback_days": lookback_days,
        "summary": summary,
        "security": security,
        "schema_status": schema_status,
        "visibility_policy": visibility_policy,
        "readiness_gates": readiness_gates,
        "readiness_score": readiness_score,
        "readiness_tone": _tone_from_score(readiness_score),
        "phase_gate_rows": _phase_gate_rows(root),
        "module_rows": _module_rows(requests, recommendations, feedbacks),
        "action_queue": _action_queue(readiness_gates, security, summary),
        "warning_fix_note": warning_fix_note,
        "contract": {
            "db_write": DB_WRITE_ENABLED,
            "migration_included": MIGRATION_INCLUDED,
            "env_file_included": ENV_FILE_INCLUDED,
            "real_import": REAL_IMPORT_ENABLED,
            "raw_payload_export": RAW_AI_PAYLOAD_EXPORT_ENABLED,
            "personal_data_export": PERSONAL_DATA_EXPORT_ENABLED,
            "human_review_required": HUMAN_REVIEW_REQUIRED,
        },
    }


def build_ai_final_live_hardening_export_rows(snapshot: dict[str, Any]) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for gate in snapshot.get("readiness_gates") or []:
        rows.append([
            gate.get("label"),
            gate.get("status"),
            gate.get("tone"),
            gate.get("finding"),
            gate.get("action"),
        ])
    for finding in (snapshot.get("security") or {}).get("findings") or []:
        rows.append([
            f"Güvenlik: {finding.get('code')}",
            finding.get("level"),
            finding.get("level"),
            finding.get("message"),
            finding.get("action"),
        ])
    return rows


def _safe_snapshot_for_export(snapshot: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "page_title",
        "lookback_days",
        "summary",
        "security",
        "schema_status",
        "readiness_gates",
        "readiness_score",
        "phase_gate_rows",
        "module_rows",
        "action_queue",
        "warning_fix_note",
        "contract",
    }
    payload = {key: snapshot.get(key) for key in allowed}
    # Export ham AI istem/yanıt, kullanıcı notu veya kişisel veri içermez.
    return payload


def dumps_safe_json(snapshot: dict[str, Any]) -> str:
    return json.dumps(_safe_snapshot_for_export(snapshot), ensure_ascii=False, indent=2, default=str)


def render_ai_final_live_hardening_markdown(snapshot: dict[str, Any]) -> str:
    lines = [
        "# BYS360 AI Karar Destek / Analiz Merkezi Faz 12 Kapanış Raporu",
        "",
        f"Hazır oluş skoru: {snapshot.get('readiness_score', 0)}/100",
        f"Dönem: Son {snapshot.get('lookback_days', 30)} gün",
        "",
        "## Güvenli sözleşme",
        "- DB yazımı yoktur.",
        "- Migration yoktur.",
        "- .env yoktur.",
        "- Gerçek içe aktarım yoktur.",
        "- Ham AI istem/yanıt metni panelde ve exportta açılmaz.",
        "- AI nihai karar vermez, öneriyi otomatik uygulamaz.",
        "- İnsan onayı zorunludur.",
        "",
        "## Kalite kapıları",
    ]
    for gate in snapshot.get("readiness_gates") or []:
        lines.append(f"- **{gate.get('status')}** — {gate.get('label')}: {gate.get('finding')}")
    lines.extend(["", "## Aksiyon kuyruğu"])
    for item in snapshot.get("action_queue") or []:
        lines.append(f"- {item.get('priority')} — {item.get('title')}: {item.get('body')}")
    lines.extend(["", "## Warning düzeltme notu", str(snapshot.get("warning_fix_note") or "")])
    return "\n".join(lines) + "\n"
