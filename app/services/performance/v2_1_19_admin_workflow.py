# -*- coding: utf-8 -*-
from __future__ import annotations


import logging

"""BYS360 Performans V2.1.19 Admin / Performans Yetkilisi işlem akışı.

Bu servis Dönem Yönetim Merkezi içinde Admin ve Performans Yetkilisi için
sıradaki işlem adımını sadeleştirir. Veritabanına yazmaz; görev üretmez,
bildirim göndermez, dönem oluşturmaz. Sadece mevcut merkez verilerinden
okunabilir iş akışı üretir.
"""

from typing import Any
logger = logging.getLogger(__name__)

RULE_VERSION = "performance_v2_1_19_admin_workflow"


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or default)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _as_text(value: Any, default: str = "") -> str:
    text = str(value or "").strip()
    return text if text else default


def _card(title: str, value: Any, label: str, klass: str = "muted") -> dict[str, Any]:
    return {"title": title, "value": value, "label": label, "class": klass}


def _step(key: str, title: str, label: str, message: str, klass: str, action_label: str, action_url: str) -> dict[str, Any]:
    return {
        "key": key,
        "title": title,
        "label": label,
        "message": message,
        "class": klass,
        "action_label": action_label,
        "action_url": action_url,
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


def build_period_center_admin_workflow(
    *,
    state: dict[str, Any] | None = None,
    embedded_summary: dict[str, Any] | None = None,
    period_flow: dict[str, Any] | None = None,
    scope_control: dict[str, Any] | None = None,
    reminder_approval: dict[str, Any] | None = None,
    executive_view: dict[str, Any] | None = None,
) -> dict[str, Any]:
    st = state or {}
    summary = embedded_summary or {}
    flow = period_flow or {}
    scope = scope_control or {}
    reminder = reminder_approval or {}
    executive = executive_view or {}
    counts = _counts(summary)
    reminder_summary = reminder.get("summary") or {}
    scope_counts = scope.get("counts") or {}

    plan_key = _as_text(flow.get("selected_plan_key") or st.get("selected_plan_key"))
    period_id = _safe_int(flow.get("selected_period_id") or summary.get("period_id"))
    selected_title = _as_text(flow.get("selected_title") or summary.get("period_title"), "Dönem seçilmedi")
    has_plan = bool(plan_key)
    has_period = bool(period_id)
    has_tasks = counts["total"] > 0
    progress = counts["progress"]
    pending = counts["pending"]
    overdue = counts["overdue"]
    due_soon = counts["due_soon"]
    manager_review = _safe_int(scope_counts.get("manager_review"))
    scope_mismatch = _safe_int(scope_counts.get("scope_mismatch"))
    ready = _safe_int(scope_counts.get("ready"))
    reminder_targets = _safe_int(reminder_summary.get("target_evaluators"))
    can_launch = bool(scope.get("can_launch"))
    can_run_precheck = bool(scope.get("can_run_precheck"))

    # 1. Dönem hazırlığı
    if has_plan:
        prep_step = _step("preparation", "Dönem Hazırlığı", "Tamamlandı", selected_title, "ok", "Dönemi İncele", flow.get("center_url") or f"/performans/donem-yonetim-merkezi?plan={plan_key}")
    else:
        prep_step = _step("preparation", "Dönem Hazırlığı", "Bekliyor", "Yeni dönem hazırlığı oluşturulmalıdır.", "warn", "Dönem Hazırla", "#donem-hazirla")

    # 2. Kapsam ve amir zinciri kontrolü
    if not has_plan:
        scope_step = _step("scope", "Kapsam Kontrolü", "Bekliyor", "Dönem seçimi sonrası kontrol edilir.", "muted", "Dönem Seç", "#donem-secimi")
    elif not has_period:
        scope_step = _step("scope", "Kapsam Kontrolü", "Dönem Bağlantısı", "Plan gerçek performans dönemine bağlanmalıdır.", "warn", "Bağlantıyı Tamamla", "#donem-secimi")
    elif scope_mismatch > 0:
        scope_step = _step("scope", "Kapsam Kontrolü", "Kapsam Uyumsuzluğu", f"{scope_mismatch} kayıt kapsam kontrolü gerektiriyor.", "danger", "Kontrol Paneli", "#kapsam-amir-kontrolu")
    elif manager_review > 0:
        scope_step = _step("scope", "Kapsam Kontrolü", "Amir Kontrolü", f"{manager_review} kayıt amir kontrolü gerektiriyor.", "warn", "Kontrol Paneli", "#kapsam-amir-kontrolu")
    elif ready > 0:
        scope_step = _step("scope", "Kapsam Kontrolü", "Uygun", f"{ready} kayıt görev üretimine uygun görünüyor.", "ok", "Kontrol Paneli", "#kapsam-amir-kontrolu")
    elif can_run_precheck:
        scope_step = _step("scope", "Kapsam Kontrolü", "Ön Kontrol", "Ön kontrol çalıştırılarak kapsam ve amir zinciri doğrulanmalıdır.", "info", "Ön Kontrole Git", "#kapsam-amir-kontrolu")
    else:
        scope_step = _step("scope", "Kapsam Kontrolü", "Bekliyor", "Kapsam ve amir bilgileri dönem bağlantısı sonrası izlenir.", "muted", "Kontrol Paneli", "#kapsam-amir-kontrolu")

    # 3. Görev üretimi
    if has_tasks:
        assignment_step = _step("assignment", "Görev Üretimi", "Tamamlandı", f"{counts['total']} değerlendirme görevi görünüyor.", "ok", "Canlı Takip", flow.get("live_tracking_url") or "/performance/v2-1-10-evaluation-live-tracking")
    elif can_launch:
        assignment_step = _step("assignment", "Görev Üretimi", "Hazır", "Ön kontrol uygun; görev üretimi başlatılabilir.", "info", "Görev Üretimine Geç", "#gorev-uretimi")
    elif has_period:
        assignment_step = _step("assignment", "Görev Üretimi", "Kontrol", "Görev üretimi için kapsam ve amir kontrolü tamamlanmalıdır.", "warn", "Kontrol Paneli", "#kapsam-amir-kontrolu")
    else:
        assignment_step = _step("assignment", "Görev Üretimi", "Bekliyor", "Dönem bağlantısı tamamlanmadan görev üretimi başlatılmaz.", "muted", "Dönem Seçimi", "#donem-secimi")

    # 4. Canlı takip
    if not has_tasks:
        tracking_step = _step("tracking", "Canlı Takip", "Bekliyor", "Değerlendirme görevleri üretildikten sonra izlenir.", "muted", "Canlı Takip", flow.get("live_tracking_url") or "/performance/v2-1-10-evaluation-live-tracking")
    elif progress >= 100:
        tracking_step = _step("tracking", "Canlı Takip", "Tamamlandı", "Değerlendirme görevleri tamamlanmış görünüyor.", "ok", "Canlı Takip", flow.get("live_tracking_url") or "/performance/v2-1-10-evaluation-live-tracking")
    elif overdue > 0:
        tracking_step = _step("tracking", "Canlı Takip", "Gecikme Var", f"{overdue} geciken görev bulunuyor.", "danger", "Canlı Takip", flow.get("live_tracking_url") or "/performance/v2-1-10-evaluation-live-tracking")
    elif pending > 0:
        tracking_step = _step("tracking", "Canlı Takip", "Devam Ediyor", f"{pending} görev bekliyor. İlerleme: %{progress}.", "warn", "Canlı Takip", flow.get("live_tracking_url") or "/performance/v2-1-10-evaluation-live-tracking")
    else:
        tracking_step = _step("tracking", "Canlı Takip", "İzlenebilir", f"İlerleme: %{progress}.", "info", "Canlı Takip", flow.get("live_tracking_url") or "/performance/v2-1-10-evaluation-live-tracking")

    # 5. Hatırlatma hazırlığı
    if not has_tasks:
        reminder_step = _step("reminder", "Hatırlatma", "Bekliyor", "Görev üretimi sonrası hatırlatma hedefleri oluşur.", "muted", "Hatırlatma Merkezi", flow.get("reminder_url") or "/performance/v2-1-11-evaluator-reminder-center")
    elif overdue > 0 or due_soon > 0 or reminder_targets > 0:
        cls = "danger" if overdue > 0 else "warn"
        label = "Öncelikli" if overdue > 0 else "Hazırlık"
        reminder_step = _step("reminder", "Hatırlatma", label, f"{reminder_targets} amir hatırlatma listesine alınabilir.", cls, "Hatırlatma Hazırlığı", "#hatirlatma-gonderim-hazirligi")
    else:
        reminder_step = _step("reminder", "Hatırlatma", "Normal", "Öncelikli hatırlatma ihtiyacı görünmüyor.", "ok", "Hatırlatma Merkezi", flow.get("reminder_url") or "/performance/v2-1-11-evaluator-reminder-center")

    steps = [prep_step, scope_step, assignment_step, tracking_step, reminder_step]
    # Sıradaki işlem: ilk ok olmayan adım
    next_step = next((item for item in steps if item.get("class") not in {"ok"}), steps[-1])

    status_class = "ok"
    status_label = "Akış Olağan"
    if any(item.get("class") == "danger" for item in steps):
        status_class = "danger"
        status_label = "Öncelikli Kontrol"
    elif any(item.get("class") == "warn" for item in steps):
        status_class = "warn"
        status_label = "İşlem Bekliyor"
    elif any(item.get("class") == "info" for item in steps):
        status_class = "info"
        status_label = "Süreç Devam Ediyor"

    return {
        "rule_version": RULE_VERSION,
        "show": not bool(executive.get("is_executive_mode")),
        "period_title": selected_title,
        "status_label": status_label,
        "status_class": status_class,
        "next_step": next_step,
        "steps": steps,
        "cards": [
            _card("Seçili Dönem", "Var" if has_plan else "Yok", "İşlem akışı seçili dönem üzerinden çalışır.", "ok" if has_plan else "warn"),
            _card("Dönem Bağlantısı", "Var" if has_period else "Yok", "Gerçek performans dönemi bağlantısı.", "ok" if has_period else "warn"),
            _card("Görev", counts["total"], "Üretilmiş değerlendirme görevi.", "ok" if has_tasks else "muted"),
            _card("Bekleyen", pending, "Tamamlanmamış görev.", "warn" if pending else "ok"),
            _card("Hatırlatma", reminder_targets, "Hatırlatma hedefi.", "warn" if reminder_targets else "ok"),
        ],
    }


def run_v2_1_19_admin_workflow_gate(admin_workflow: dict[str, Any] | None = None) -> dict[str, Any]:
    flow = admin_workflow or {}
    checks = [
        {"name": "admin_workflow_builds", "ok": isinstance(flow, dict), "message": "Admin işlem akışı hazırlanıyor."},
        {"name": "workflow_steps_available", "ok": len(flow.get("steps") or []) == 5, "message": "Beş ana işlem adımı üretildi."},
        {"name": "next_step_available", "ok": bool((flow.get("next_step") or {}).get("title")), "message": "Sıradaki işlem üretildi."},
        {"name": "cards_available", "ok": len(flow.get("cards") or []) >= 5, "message": "İşlem özeti kartları hazır."},
        {"name": "read_only", "ok": True, "message": "V2.1.19 yalnızca yönlendirme/akış verisi üretir."},
    ]
    return {"ok": all(item.get("ok") for item in checks), "checks": checks, "rule_version": RULE_VERSION}
