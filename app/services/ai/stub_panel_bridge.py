# -*- coding: utf-8 -*-
"""BYS360 v60 Stub AI ekran panel köprüsü.

Bu dosya dış AI sağlayıcısına ihtiyaç duymadan mevcut StubAIClient üzerinden
sayfa bağlamından kontrollü karar destek paneli üretir. Amaç: kural motoru
çıktılarını kullanıcı ekranında kurumsal, okunabilir ve izlenebilir hale getirmek.
"""
from __future__ import annotations

from typing import Any

try:  # güvenli metin temizliği varsa kullan
    from app.services.ai.guardrails import sanitize_output_text
except Exception:  # pragma: no cover
    def sanitize_output_text(value: str) -> str:  # type: ignore[no-redef]
        return str(value or "").strip()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value or default))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value or default)
    except (TypeError, ValueError):
        return default


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _line_groups(text: str) -> tuple[str, list[str], list[str]]:
    cleaned = sanitize_output_text(text or "")
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    if not lines:
        return "Kontrollü karar destek notu hazır.", [], []
    headline = lines[0].rstrip(":")
    bullets: list[str] = []
    actions: list[str] = []
    action_mode = False
    for line in lines[1:]:
        normalized = line.lower().rstrip(":")
        if any(key in normalized for key in ("öneri", "aksiyon", "sonraki adım", "öncelik")) and len(line) < 80:
            action_mode = True
            continue
        clean = line[1:].strip() if line.startswith("-") else line
        if action_mode:
            actions.append(clean)
        else:
            bullets.append(clean)
    return headline, bullets[:8], actions[:5]


def _make_panel(*, module_type: str, feature_type: str, title: str, badge: str, payload: dict[str, Any], icon: str = "fa-solid fa-wand-magic-sparkles") -> dict[str, Any]:
    prompt_version = f"{module_type}_{feature_type}_v60"
    try:
        from app.services.ai.client import get_ai_client

        result = get_ai_client().generate(
            system_prompt=(
                "BYS360 kurumsal karar destek paneli üret. "
                "Nihai karar verme; yalnızca veriye dayalı özet, risk ve öneri sun. "
                "Teknik kod, faz dili ve geliştirici ifadesi kullanma."
            ),
            user_prompt=(
                f"Senaryo: {module_type}/{feature_type}\n"
                "Aşağıdaki gerçek sayısal bağlamı yorumla; dış kaynağa bağlanma.\n"
                f"{payload!r}"
            ),
            prompt_version=prompt_version,
        )
        text = sanitize_output_text(result.text)
        provider = result.provider_name
        model = result.model_name
        latency = result.latency_ms
    except Exception as exc:  # canlı ekran patlamasın
        text = (
            "Karar Destek Paneli:\n"
            "- AI kural motoru paneli şu anda güvenli yedek görünümde açıldı.\n"
            "- Sayfadaki gerçek veriler üzerinden işlem yapmaya devam edebilirsiniz.\n"
            "Öneri:\n"
            "- Kontrol scriptini çalıştırarak stub senaryo kayıtlarını doğrulayın."
        )
        provider = "safe_fallback"
        model = "bys360-stub-panel-fallback"
        latency = 0

    headline, bullets, actions = _line_groups(text)
    return {
        "enabled": True,
        "title": title,
        "badge": badge,
        "icon": icon,
        "headline": headline,
        "text": text,
        "bullets": bullets,
        "actions": actions,
        "payload": payload,
        "meta": {
            "module_type": module_type,
            "feature_type": feature_type,
            "prompt_version": prompt_version,
            "provider": provider,
            "model": model,
            "latency_ms": latency,
            "external_connection": False,
            "decision_boundary": "AI karar vermez; yöneticiye veri temelli destek sunar.",
        },
    }


def _selected_employee_from_context(ctx: dict[str, Any]) -> dict[str, Any]:
    meeting = _dict(ctx.get("selected_meeting") or _dict(ctx.get("detail")).get("meeting"))
    return {
        "full_name": meeting.get("employee_name") or meeting.get("personnel_name") or meeting.get("employee") or "Personel",
        "id": meeting.get("employee_id") or meeting.get("personnel_id"),
    }


def build_aftercare_ai_panel(ctx: dict[str, Any]) -> dict[str, Any]:
    preparation = _dict(ctx.get("preparation"))
    after_note = _dict(ctx.get("after_note"))
    actions = _as_list(ctx.get("actions"))
    selected_meeting = _dict(ctx.get("selected_meeting"))
    note_fields = [
        "meeting_summary", "employee_self_assessment", "manager_observation",
        "strong_points", "development_areas", "agreed_actions_summary", "employee_final_words",
    ]
    note_count = sum(1 for key in note_fields if str(after_note.get(key) or "").strip())
    open_actions = [row for row in actions if str(_dict(row).get("status") or "").lower() not in {"tamamlandi", "kapali", "closed", "iptal"}]
    payload = {
        "meeting_type": selected_meeting.get("meeting_type") or selected_meeting.get("type") or "görüşme",
        "note_count": note_count,
        "prep_note": preparation.get("purpose") or preparation.get("employee_summary") or "",
        "action_count": len(actions),
        "open_actions": len(open_actions),
        "employee": _selected_employee_from_context(ctx),
        "score": _safe_float(selected_meeting.get("score") or selected_meeting.get("final_total") or selected_meeting.get("final_score")),
    }
    return _make_panel(module_type="performance", feature_type="aftercare_coaching", title="Görüşme Koçluğu", badge="Kurallı AI · Gerçek veri", payload=payload, icon="fa-solid fa-comments")


def attach_aftercare_ai_panel(ctx: dict[str, Any]) -> dict[str, Any]:
    ctx["ai_stub_panel"] = build_aftercare_ai_panel(ctx)
    ctx["aftercare_ai_panel"] = ctx["ai_stub_panel"]
    return ctx


def build_interim_notes_ai_panel(*, page_summary: dict[str, Any] | None = None, note_items: list[Any] | None = None, employee: dict[str, Any] | None = None, period_title: str | None = None) -> dict[str, Any]:
    summary = dict(page_summary or {})
    note_items = note_items or []
    # Eski ve yeni özet anahtarlarını aynı senaryoya bağla.
    payload = {
        "summary": {
            "total": _safe_int(summary.get("total") or len(note_items)),
            "positive": _safe_int(summary.get("positive") or summary.get("type_counts", {}).get("olumlu_olay") or summary.get("type_counts", {}).get("basari")),
            "negative": _safe_int(summary.get("negative") or summary.get("type_counts", {}).get("olumsuz_olay")),
            "development": _safe_int(summary.get("development") or summary.get("type_counts", {}).get("gelisim_ihtiyaci")),
            "achievement": _safe_int(summary.get("achievement") or summary.get("type_counts", {}).get("basari")),
            "visible_on_scoring": _safe_int(summary.get("visible_on_scoring") or summary.get("scorecard")),
        },
        "employee": employee or {"full_name": "Seçili görünüm"},
        "period_title": period_title or "aktif dönem",
    }
    return _make_panel(module_type="performance", feature_type="interim_notes_pattern", title="Dönem İçi Not Analizi", badge="Kurallı AI · Denge ve trend", payload=payload, icon="fa-regular fa-note-sticky")


def build_followup_ai_panel(ctx: dict[str, Any]) -> dict[str, Any]:
    dashboard = _dict(ctx.get("dashboard"))
    payload = {
        "open_count": _safe_int(dashboard.get("open")),
        "overdue_count": _safe_int(dashboard.get("overdue")),
        "closed_count": _safe_int(dashboard.get("closed")),
        "due_soon_count": _safe_int(dashboard.get("upcoming")),
    }
    return _make_panel(module_type="performance", feature_type="followup_risk", title="Eylem Planı Gecikme Riski", badge="Kurallı AI · Takip riski", payload=payload, icon="fa-solid fa-calendar-check")


def attach_followup_ai_panel(ctx: dict[str, Any]) -> dict[str, Any]:
    ctx["ai_stub_panel"] = build_followup_ai_panel(ctx)
    ctx["followup_ai_panel"] = ctx["ai_stub_panel"]
    return ctx


def build_pipeline_ai_panel(ctx: dict[str, Any]) -> dict[str, Any]:
    summary = _dict(ctx.get("summary"))
    payload = {
        "overall_percent": _safe_int(summary.get("overall_percent")),
        "total": _safe_int(summary.get("total")),
        "ready": _safe_int(summary.get("ready")),
        "attention": _safe_int(summary.get("attention")),
        "missing": _safe_int(summary.get("missing")),
        "warning_count": _safe_int(summary.get("warning_count") or len(_as_list(ctx.get("warnings")))),
    }
    return _make_panel(module_type="performance", feature_type="pipeline_status", title="Süreç Hattı Analizi", badge="Kurallı AI · Tıkanma kontrolü", payload=payload, icon="fa-solid fa-route")


def attach_pipeline_ai_panel(ctx: dict[str, Any]) -> dict[str, Any]:
    ctx["ai_stub_panel"] = build_pipeline_ai_panel(ctx)
    ctx["pipeline_ai_panel"] = ctx["ai_stub_panel"]
    return ctx


def build_development_guidance_ai_panel(ctx: dict[str, Any]) -> dict[str, Any]:
    rows = _as_list(ctx.get("recommendation_rows"))
    scorecard_items = _as_list(ctx.get("scorecard_items"))
    weak: list[str] = []
    strong: list[str] = []
    score = 0.0
    for row_any in scorecard_items[:20]:
        row = _dict(row_any)
        label = str(row.get("criteria") or row.get("title") or row.get("label") or "Kriter").strip()
        val = _safe_float(row.get("score") or row.get("final_total") or row.get("value"))
        if val:
            score = max(score, val) if score <= 0 else score
        if val and val < 70:
            weak.append(label)
        elif val and val >= 90:
            strong.append(label)
    payload = {
        "employee": {"full_name": ctx.get("selected_employee_name") or "Seçili personel"},
        "score": _safe_float(ctx.get("selected_score") or ctx.get("final_total") or score),
        "category_label": ctx.get("selected_category_label") or "Genel",
        "weak_criteria": weak[:5],
        "strong_criteria": strong[:5],
        "existing_guidance_count": len(rows),
    }
    return _make_panel(module_type="performance", feature_type="development_guidance", title="Gelişim Rehberi Karar Desteği", badge="Kurallı AI · Gelişim odağı", payload=payload, icon="fa-solid fa-seedling")


def attach_development_guidance_ai_panel(ctx: dict[str, Any]) -> dict[str, Any]:
    ctx["ai_stub_panel"] = build_development_guidance_ai_panel(ctx)
    ctx["development_guidance_ai_panel"] = ctx["ai_stub_panel"]
    return ctx


def build_process_tracking_ai_panel(ctx: dict[str, Any]) -> dict[str, Any]:
    # Final gate ve süreç takip sayfalarında farklı anahtarlar kullanıldığı için esnek okunur.
    flows = _as_list(ctx.get("flows") or ctx.get("workflow_rows") or ctx.get("items"))
    cards = _as_list(ctx.get("cards") or ctx.get("checks"))
    summary = _dict(ctx.get("summary") or ctx.get("dashboard"))
    total = _safe_int(summary.get("total_flows") or summary.get("total") or len(flows) or len(cards))
    completed = _safe_int(summary.get("completed_flows") or summary.get("completed") or summary.get("ready"))
    pending = _safe_int(summary.get("pending_flows") or summary.get("pending") or max(total - completed, 0))
    overdue = _safe_int(summary.get("overdue_flows") or summary.get("overdue"))
    president_pending = _safe_int(summary.get("president_pending") or summary.get("president_waiting"))
    payload = {
        "total_flows": total,
        "overdue_flows": overdue,
        "pending_flows": pending,
        "completed_flows": completed,
        "president_pending": president_pending,
        "period_title": ctx.get("period_title") or ctx.get("active_period_title") or "aktif dönem",
    }
    return _make_panel(module_type="performance", feature_type="process_tracking", title="Süreç Takip Analizi", badge="Kurallı AI · Akış kontrolü", payload=payload, icon="fa-solid fa-diagram-project")


def attach_process_tracking_ai_panel(ctx: dict[str, Any]) -> dict[str, Any]:
    ctx["ai_stub_panel"] = build_process_tracking_ai_panel(ctx)
    ctx["process_tracking_ai_panel"] = ctx["ai_stub_panel"]
    return ctx


def build_archive_trend_ai_panel(*, employee: dict[str, Any] | None = None, archive_records: list[Any] | None = None) -> dict[str, Any]:
    payload = {
        "employee": employee or {"full_name": "Personel"},
        "archive_records": archive_records or [],
    }
    return _make_panel(module_type="performance", feature_type="archive_trend", title="Geçmiş Karne Trend Analizi", badge="Kurallı AI · Arşiv trendi", payload=payload, icon="fa-solid fa-chart-line")


def build_leave_detail_ai_panel(ctx: dict[str, Any]) -> dict[str, Any]:
    summary = _dict(ctx.get("summary") or ctx.get("dashboard"))
    payload = {
        "pending_count": _safe_int(summary.get("pending_count") or summary.get("pending")),
        "approved_count": _safe_int(summary.get("approved_count") or summary.get("approved")),
        "rejected_count": _safe_int(summary.get("rejected_count") or summary.get("rejected")),
        "delegation_ok": _safe_int(summary.get("delegation_ok") or summary.get("covered")),
        "delegation_gap": _safe_int(summary.get("delegation_gap") or summary.get("uncovered")),
        "department": ctx.get("department") or ctx.get("department_label") or "birim",
        "period_title": ctx.get("period_title") or "aktif dönem",
    }
    return _make_panel(module_type="hr", feature_type="leave_detail", title="İzin ve Vekâlet Analizi", badge="Kurallı AI · Personel omurgası", payload=payload, icon="fa-solid fa-user-clock")
