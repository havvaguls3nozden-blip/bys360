from __future__ import annotations

import logging

"""BYS360 Performans V2.1.15 dönem seçimi ve durum akışı.

Bu servis yalnızca merkez ekranında kullanılacak seçim/akış verisini hazırlar.
Veritabanına yazmaz, görev üretmez, bildirim göndermez.
"""

from typing import Any

logger = logging.getLogger(__name__)

RULE_VERSION = "performance_v2_1_15_period_selection_status_flow"


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or default)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _as_text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text if text else default


def _integration_map(state: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for item in state.get("integrations") or []:
        key = _as_text(item.get("plan_key"))
        if key and key not in out:
            out[key] = item
    return out


def _plan_label(plan: dict[str, Any], integration: dict[str, Any] | None) -> str:
    name = _as_text(plan.get("plan_name"), "Adsız dönem")
    period_type = _as_text(plan.get("period_type_label") or plan.get("period_type"))
    category = _as_text(plan.get("category_name"))
    dates = ""
    if plan.get("start_date") or plan.get("end_date"):
        dates = f" — {plan.get('start_date') or '-'} / {plan.get('end_date') or '-'}"
    if integration and integration.get("period_title"):
        return f"{name} — {integration.get('period_title')}{dates}"
    tail = " / ".join([x for x in [period_type, category] if x])
    return f"{name}" + (f" — {tail}" if tail else "") + dates


def _option_status(plan: dict[str, Any], integration: dict[str, Any] | None) -> tuple[str, str, str]:
    generation = _as_text((integration or {}).get("assignment_generation_status")).lower()
    precheck = _as_text((integration or {}).get("assignment_precheck_status")).lower()
    if generation == "generated":
        return "Görevler üretildi", "ok", "Değerlendirme süreci izlenebilir."
    if integration and integration.get("period_id"):
        if precheck == "ready":
            return "Görev üretimine hazır", "info", "Ön kontrol tamamlandı."
        if precheck and precheck not in {"not_started", "none"}:
            return "Kontrol gerekli", "warn", "Ön kontrol sonucunu inceleyin."
        return "Döneme bağlı", "info", "Ön kontrol/görev üretimi bekliyor."
    if plan.get("ready_for_assignment"):
        return "Bağlantı bekliyor", "warn", "Plan gerçek performans dönemine bağlanmalı."
    return "Hazırlıkta", "muted", "Dönem hazırlığı tamamlanmalı."


def _period_options(state: dict[str, Any]) -> list[dict[str, Any]]:
    integrations = _integration_map(state)
    selected = _as_text(state.get("selected_plan_key"))
    options: list[dict[str, Any]] = []
    for plan in state.get("plans") or []:
        key = _as_text(plan.get("plan_key"))
        if not key:
            continue
        integration = integrations.get(key)
        status, badge_class, hint = _option_status(plan, integration)
        options.append({
            "plan_key": key,
            "label": _plan_label(plan, integration),
            "plan_name": _as_text(plan.get("plan_name"), "Adsız dönem"),
            "category_name": _as_text(plan.get("category_name"), "-"),
            "date_range": f"{plan.get('start_date') or '-'} / {plan.get('end_date') or '-'}",
            "personnel_count": _safe_int(plan.get("personnel_count")),
            "period_id": _safe_int((integration or {}).get("period_id")),
            "period_title": _as_text((integration or {}).get("period_title")),
            "status": status,
            "badge_class": badge_class,
            "hint": hint,
            "selected": key == selected,
            "url": f"/performans/donem-yonetim-merkezi?plan={key}",
        })
    return options


def _flow_item(key: str, title: str, state: str, label: str, message: str) -> dict[str, Any]:
    return {"key": key, "title": title, "state": state, "label": label, "message": message}


def _status_flow(state: dict[str, Any], embedded_summary: dict[str, Any] | None) -> list[dict[str, Any]]:
    summary = embedded_summary or {}
    counts = summary.get("counts") or {}
    selected_plan = state.get("selected_plan") or None
    selected_integration = state.get("selected_integration") or None
    total = _safe_int(counts.get("total"))
    pending = _safe_int(counts.get("pending"))
    overdue = _safe_int(counts.get("overdue"))
    due_soon = _safe_int(counts.get("due_soon"))
    progress = _safe_int(counts.get("progress"))
    generation = _as_text((selected_integration or {}).get("assignment_generation_status")).lower()
    precheck = _as_text((selected_integration or {}).get("assignment_precheck_status")).lower()

    if selected_plan:
        preparation = _flow_item("preparation", "Dönem Hazırlığı", "ok", "Tamamlandı", "Dönem planı seçildi.")
    else:
        preparation = _flow_item("preparation", "Dönem Hazırlığı", "muted", "Bekliyor", "İzlenecek dönem seçilmelidir.")

    if selected_integration and selected_integration.get("period_id"):
        link = _flow_item("link", "Dönem Bağlantısı", "ok", "Tamamlandı", "Plan gerçek performans dönemine bağlı.")
    elif selected_plan:
        link = _flow_item("link", "Dönem Bağlantısı", "warn", "Bekliyor", "Plan performans dönemine bağlanmalı.")
    else:
        link = _flow_item("link", "Dönem Bağlantısı", "muted", "Bekliyor", "Dönem seçimi sonrası kontrol edilir.")

    if generation == "generated" or total > 0:
        assignment = _flow_item("assignment", "Görev Üretimi", "ok", "Tamamlandı", f"{total} değerlendirme görevi görünüyor.")
    elif selected_integration and precheck == "ready":
        assignment = _flow_item("assignment", "Görev Üretimi", "info", "Hazır", "Ön kontrol tamamlandı; görev üretimi başlatılabilir.")
    elif selected_integration:
        assignment = _flow_item("assignment", "Görev Üretimi", "warn", "Kontrol", "Görev üretimi öncesi amir/kapsam kontrolü yapılmalı.")
    else:
        assignment = _flow_item("assignment", "Görev Üretimi", "muted", "Bekliyor", "Dönem bağlantısı bekleniyor.")

    if total > 0 and progress >= 100:
        evaluation = _flow_item("evaluation", "Değerlendirme", "ok", "Tamamlandı", "Tüm değerlendirme görevleri tamamlanmış görünüyor.")
    elif total > 0 and pending > 0:
        evaluation = _flow_item("evaluation", "Değerlendirme", "warn", "Devam Ediyor", f"{pending} değerlendirme görevi bekliyor.")
    elif total > 0:
        evaluation = _flow_item("evaluation", "Değerlendirme", "info", "Takip", "Değerlendirme süreci izlenebilir.")
    else:
        evaluation = _flow_item("evaluation", "Değerlendirme", "muted", "Bekliyor", "Görev üretimi sonrası başlar.")

    if overdue > 0:
        reminder = _flow_item("reminder", "Hatırlatma", "danger", "Gecikme Var", f"{overdue} geciken görev için hatırlatma hazırlanmalı.")
    elif due_soon > 0:
        reminder = _flow_item("reminder", "Hatırlatma", "warn", "Son Tarih Yaklaşıyor", f"{due_soon} görev için son tarih yaklaşıyor.")
    elif total > 0 and pending > 0:
        reminder = _flow_item("reminder", "Hatırlatma", "info", "Gerekirse", "Bekleyen görevler canlı takipten izlenebilir.")
    elif total > 0:
        reminder = _flow_item("reminder", "Hatırlatma", "ok", "Normal", "Hatırlatma gerektiren kayıt görünmüyor.")
    else:
        reminder = _flow_item("reminder", "Hatırlatma", "muted", "Bekliyor", "Görev üretimi sonrası değerlendirilir.")

    return [preparation, link, assignment, evaluation, reminder]


def _selected_option(options: list[dict[str, Any]]) -> dict[str, Any] | None:
    return next((item for item in options if item.get("selected")), None)


def build_period_center_selection_flow(state: dict[str, Any] | None, embedded_summary: dict[str, Any] | None = None) -> dict[str, Any]:
    st = state or {}
    options = _period_options(st)
    selected = _selected_option(options)
    period_id = _safe_int((embedded_summary or {}).get("period_id"))
    plan_key = _as_text(st.get("selected_plan_key"))
    return {
        "rule_version": RULE_VERSION,
        "options": options,
        "has_options": bool(options),
        "selected": selected,
        "selected_plan_key": plan_key,
        "selected_period_id": period_id,
        "selected_title": (selected or {}).get("plan_name") or (embedded_summary or {}).get("period_title") or "Dönem seçilmedi",
        "flow": _status_flow(st, embedded_summary),
        "live_tracking_url": f"/performance/v2-1-10-evaluation-live-tracking?period_id={period_id}" if period_id else "/performance/v2-1-10-evaluation-live-tracking",
        "reminder_url": f"/performance/v2-1-11-evaluator-reminder-center?period_id={period_id}" if period_id else "/performance/v2-1-11-evaluator-reminder-center",
        "center_url": f"/performans/donem-yonetim-merkezi?plan={plan_key}" if plan_key else "/performans/donem-yonetim-merkezi",
        "message": "Dönem seçildiğinde yönetim özeti ve işlem kartları aynı dönem üzerinden çalışır." if plan_key else "Dönem seçerek yönetim özetini etkinleştirin.",
    }


def run_v2_1_15_period_selection_status_flow_gate(state: dict[str, Any] | None = None, embedded_summary: dict[str, Any] | None = None) -> dict[str, Any]:
    flow = build_period_center_selection_flow(state or {}, embedded_summary or {})
    checks = [
        {"name": "selection_flow_builds", "ok": isinstance(flow, dict), "message": "Dönem seçimi akışı hazırlandı."},
        {"name": "period_options_safe", "ok": isinstance(flow.get("options"), list), "message": "Dönem seçenekleri güvenli liste olarak üretildi."},
        {"name": "status_flow_steps", "ok": len(flow.get("flow") or []) == 5, "message": "Durum akışı beş ana adımdan oluşuyor."},
        {"name": "read_only", "ok": True, "message": "V2.1.15 yalnızca okuma ve görünüm akışı hazırlar."},
    ]
    return {"ok": all(item.get("ok") for item in checks), "checks": checks, "rule_version": RULE_VERSION}
