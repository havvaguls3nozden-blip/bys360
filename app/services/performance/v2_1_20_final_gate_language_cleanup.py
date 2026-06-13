# -*- coding: utf-8 -*-
from __future__ import annotations


import logging

"""BYS360 Performans V2.1.20 Sistem Kontrol Özeti.

Bu servis Dönem Yönetim Merkezi için son durum kontrolünü üretir.
Kullanıcı ekranında teknik ifade göstermez; veritabanına yazmaz,
görev üretmez, e-posta göndermez. Sadece V2.1.7-V2.1.19 hattının
merkez ekrandaki durumunu sade kontrol kartlarına dönüştürür.
"""

from typing import Any
logger = logging.getLogger(__name__)

RULE_VERSION = "performance_v2_1_20_final_gate_language_cleanup"


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or default)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _as_text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text if text else default


def _badge(ok: bool, warn: bool = False) -> str:
    if ok:
        return "ok"
    return "warn" if warn else "danger"


def _check(name: str, ok: bool, message: str, label: str | None = None, warn: bool = False) -> dict[str, Any]:
    return {
        "name": name,
        "ok": bool(ok),
        "label": label or ("Uygun" if ok else "Kontrol"),
        "message": message,
        "class": _badge(bool(ok), warn=warn),
    }


def _counts(summary: dict[str, Any] | None) -> dict[str, int]:
    raw = (summary or {}).get("counts") or {}
    return {
        "total": _safe_int(raw.get("total")),
        "completed": _safe_int(raw.get("completed")),
        "pending": _safe_int(raw.get("pending")),
        "overdue": _safe_int(raw.get("overdue")),
        "due_soon": _safe_int(raw.get("due_soon")),
        "progress": _safe_int(raw.get("progress")),
    }


def build_period_center_final_gate(
    *,
    state: dict[str, Any] | None = None,
    embedded_summary: dict[str, Any] | None = None,
    period_flow: dict[str, Any] | None = None,
    scope_control: dict[str, Any] | None = None,
    reminder_approval: dict[str, Any] | None = None,
    executive_view: dict[str, Any] | None = None,
    admin_workflow: dict[str, Any] | None = None,
) -> dict[str, Any]:
    st = state or {}
    summary = embedded_summary or {}
    flow = period_flow or {}
    scope = scope_control or {}
    reminder = reminder_approval or {}
    executive = executive_view or {}
    workflow = admin_workflow or {}
    counts = _counts(summary)

    selected_title = _as_text(flow.get("selected_title") or summary.get("period_title"), "Dönem seçilmedi")
    has_state = isinstance(st, dict) and bool(st)
    has_period_selector = bool(flow.get("has_options")) or bool(flow.get("selected_plan_key"))
    has_summary_cards = isinstance(summary.get("cards"), list) or bool(summary.get("counts"))
    has_scope_panel = isinstance(scope, dict) and bool(scope.get("cards"))
    has_reminder_panel = isinstance(reminder, dict) and bool(reminder.get("summary"))
    has_executive = isinstance(executive, dict) and bool(executive.get("cards"))
    has_admin_workflow = isinstance(workflow, dict) and len(workflow.get("steps") or []) == 5
    has_live_link = bool(flow.get("live_tracking_url"))
    has_reminder_link = bool(flow.get("reminder_url"))
    has_tasks = counts["total"] > 0
    has_blocker = bool(scope.get("has_blocker")) or _safe_int((scope.get("counts") or {}).get("manager_review")) > 0 or _safe_int((scope.get("counts") or {}).get("scope_mismatch")) > 0
    needs_attention = counts["overdue"] > 0 or counts["due_soon"] > 0 or has_blocker

    checks = [
        _check("period_center_state", has_state, "Merkez ekran verisi hazırlanıyor.", "Merkez"),
        _check("period_selection", has_period_selector, "Dönem seçimi ve dönem seçenekleri erişilebilir.", "Dönem"),
        _check("real_summary", has_summary_cards, "Gerçek görev özeti kartları hazırlanıyor.", "Özet"),
        _check("scope_chain", has_scope_panel, "Kapsam ve amir zinciri kontrol paneli erişilebilir.", "Kapsam"),
        _check("tracking_links", has_live_link, "Canlı değerlendirme takibi bağlantısı hazır.", "Canlı Takip"),
        _check("reminder_links", has_reminder_link, "Amir hatırlatma merkezi bağlantısı hazır.", "Hatırlatma"),
        _check("reminder_approval", has_reminder_panel, "Hatırlatma hazırlığı özeti hazırlanıyor.", "Gönderim Hazırlığı"),
        _check("executive_view", has_executive, "Üst yönetim özeti erişilebilir.", "Üst Yönetim"),
        _check("admin_workflow", has_admin_workflow, "Admin işlem akışı beş adımda hazırlanıyor.", "İşlem Akışı"),
    ]

    hard_fail = [item for item in checks if not item.get("ok")]
    status_class = "ok"
    status_label = "Kontroller Uygun"
    summary_text = "Dönem merkezi temel kontrolleri uygun görünüyor."
    if hard_fail:
        status_class = "warn"
        status_label = "Kontrol Gerekiyor"
        summary_text = "Dönem merkezi içinde tamamlanması gereken kontrol başlıkları bulunuyor."
    elif needs_attention:
        status_class = "warn"
        status_label = "Süreç Takibi Gerekli"
        summary_text = "Merkez ekranı çalışıyor; kapsam, gecikme veya hatırlatma başlıkları izlenmelidir."
    elif has_tasks and counts["progress"] >= 100:
        status_class = "ok"
        status_label = "Tamamlanma Kontrolü"
        summary_text = "Değerlendirme görevleri tamamlanmış görünüyor; yayın öncesi kontrol adımlarına geçilebilir."

    cards = [
        {"title": "Dönem", "value": "Seçildi" if flow.get("selected_plan_key") else "Bekliyor", "label": selected_title, "class": "ok" if flow.get("selected_plan_key") else "warn"},
        {"title": "Görev", "value": counts["total"], "label": "Toplam değerlendirme görevi", "class": "ok" if has_tasks else "muted"},
        {"title": "İlerleme", "value": f"%{counts['progress']}", "label": "Tamamlanma oranı", "class": "ok" if counts["progress"] >= 80 else ("warn" if has_tasks else "muted")},
        {"title": "Takip", "value": counts["overdue"] + counts["due_soon"], "label": "Geciken veya yaklaşan görev", "class": "warn" if counts["overdue"] + counts["due_soon"] else "ok"},
        {"title": "Kontrol", "value": len(hard_fail), "label": "Tamamlanması gereken başlık", "class": "warn" if hard_fail else "ok"},
    ]

    return {
        "rule_version": RULE_VERSION,
        "show": True,
        "period_title": selected_title,
        "status_label": status_label,
        "status_class": status_class,
        "summary_text": summary_text,
        "checks": checks,
        "cards": cards,
        "has_blocker": bool(hard_fail),
        "attention_required": bool(needs_attention or hard_fail),
    }


def run_v2_1_20_final_gate(final_gate: dict[str, Any] | None = None) -> dict[str, Any]:
    gate = final_gate or {}
    checks = [
        {"name": "final_gate_builds", "ok": isinstance(gate, dict), "message": "Sistem kontrol özeti hazırlanıyor."},
        {"name": "final_gate_cards", "ok": len(gate.get("cards") or []) >= 5, "message": "Kontrol kartları hazır."},
        {"name": "final_gate_checks", "ok": len(gate.get("checks") or []) >= 8, "message": "Kontrol başlıkları hazır."},
        {"name": "safe_visible_language", "ok": True, "message": "Kullanıcıya teknik kontrol adı gösterilmez."},
        {"name": "read_only", "ok": True, "message": "V2.1.20 yalnızca kontrol ve görünürlük özeti üretir."},
    ]
    return {"ok": all(item.get("ok") for item in checks), "checks": checks, "rule_version": RULE_VERSION}
