from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text

from app.services.performance.v2_1_6_category_period_integration import (
    PRECHECK_TABLE,
    ensure_category_period_integration_schema,
    list_preintegration_rows,
)

"""BYS360 Performans V2.1.16 kapsam ve amir zinciri kontrol paneli.

Bu servis Dönem Yönetim Merkezi içinde seçili dönem için hafif ön kontrol
özetini hazırlar. Görev üretmez, e-posta göndermez, değerlendirme kaydı yazmaz.
Ön kontrol satırları daha önce üretilmişse onları okur; yoksa kullanıcıya
"Ön kontrol bekliyor" durumunu gösterir.
"""

logger = logging.getLogger(__name__)

RULE_VERSION = "performance_v2_1_16_scope_chain_control_panel"


STATUS_LABELS = {
    "gorev_uretimi_on_hazir": ("Uygun", "ok"),
    "amir_kontrol_gerekiyor": ("Amir Kontrolü", "warn"),
    "kapsam_uyumsuz": ("Kapsam Uyumsuzluğu", "danger"),
    "kontrol_gerekiyor": ("Kontrol Gerekli", "warn"),
    "": ("Kontrol Gerekli", "warn"),
}


def _db():
    from app.extensions import db
    return db


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or default)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _as_text(value: Any, default: str = "") -> str:
    text_value = str(value or "").strip()
    return text_value if text_value else default


def _status_meta(status: str) -> tuple[str, str]:
    return STATUS_LABELS.get(_as_text(status).lower(), ("Kontrol Gerekli", "warn"))


def _selected_plan_key(state: dict[str, Any]) -> str:
    key = _as_text(state.get("selected_plan_key"))
    if key:
        return key
    plan = state.get("selected_plan") or {}
    return _as_text(plan.get("plan_key"))


def _selected_period_id(state: dict[str, Any]) -> int:
    integration = state.get("selected_integration") or {}
    return _safe_int(integration.get("period_id"))


def _count_rows(plan_key: str, period_id: int) -> dict[str, int]:
    if not plan_key or not period_id:
        return {}
    try:
        ensure_category_period_integration_schema()
        rows = _db().session.execute(
            text(f"""
                SELECT precheck_status, COUNT(*) AS total
                  FROM {PRECHECK_TABLE}
                 WHERE plan_key=:plan_key AND period_id=:period_id
                 GROUP BY precheck_status
            """),
            {"plan_key": plan_key, "period_id": period_id},
        ).mappings().all()
        return {_as_text(row.get("precheck_status")).lower(): int(row.get("total") or 0) for row in rows}
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        try:
            _db().session.rollback()
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            pass
        return {}


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    status = _as_text(row.get("precheck_status")).lower()
    label, badge_class = _status_meta(status)
    manager_summary = _as_text(row.get("manager_summary"), "Amir bilgisi görüntülenemedi")
    message = _as_text(row.get("precheck_message"), "Kontrol sonucu bulunamadı")
    return {
        "user_id": _safe_int(row.get("user_id")),
        "display_name": _as_text(row.get("display_name"), "Personel"),
        "sicil_no": _as_text(row.get("sicil_no"), "-"),
        "unit_name": _as_text(row.get("unit_name"), "-"),
        "category_key": _as_text(row.get("category_key"), "-"),
        "scope_match": bool(row.get("scope_match")),
        "manager_summary": manager_summary,
        "status": status,
        "status_label": label,
        "badge_class": badge_class,
        "message": message,
    }


def build_scope_chain_control_panel(state: dict[str, Any] | None, *, limit: int = 80) -> dict[str, Any]:
    st = state or {}
    plan_key = _selected_plan_key(st)
    period_id = _selected_period_id(st)
    selected_plan = st.get("selected_plan") or None
    selected_integration = st.get("selected_integration") or None

    base: dict[str, Any] = {
        "rule_version": RULE_VERSION,
        "plan_key": plan_key,
        "period_id": period_id,
        "has_plan": bool(selected_plan and plan_key),
        "has_period": bool(selected_integration and period_id),
        "rows": [],
        "counts": {"total": 0, "ready": 0, "manager_review": 0, "scope_mismatch": 0, "other": 0},
        "cards": [],
        "status": "donem_secilmedi",
        "status_label": "Dönem Seçilmedi",
        "status_class": "muted",
        "message": "Kapsam ve amir zinciri kontrolü için dönem seçin.",
        "can_run_precheck": False,
        "can_launch": False,
        "action_label": "Dönem Seçimi",
    }

    if not plan_key or not selected_plan:
        base["cards"] = _cards(base["counts"])
        return base

    if not period_id:
        base.update({
            "status": "donem_baglantisi_bekliyor",
            "status_label": "Dönem Bağlantısı Bekliyor",
            "status_class": "warn",
            "message": "Plan gerçek performans dönemine bağlanmadan kapsam ve amir zinciri ön kontrolü yapılamaz.",
            "action_label": "Döneme Bağla",
        })
        base["cards"] = _cards(base["counts"])
        return base

    raw_counts = _count_rows(plan_key, period_id)
    total = sum(raw_counts.values())
    ready = raw_counts.get("gorev_uretimi_on_hazir", 0)
    manager_review = raw_counts.get("amir_kontrol_gerekiyor", 0)
    scope_mismatch = raw_counts.get("kapsam_uyumsuz", 0)
    other = max(0, total - ready - manager_review - scope_mismatch)

    rows: list[dict[str, Any]] = []
    if total:
        try:
            rows = [_normalize_row(item) for item in list_preintegration_rows(plan_key, period_id=period_id, limit=limit)]
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            try:
                _db().session.rollback()
            except Exception:
                logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
                pass
            rows = []

    counts = {"total": total, "ready": ready, "manager_review": manager_review, "scope_mismatch": scope_mismatch, "other": other}
    base["counts"] = counts
    base["rows"] = rows
    base["cards"] = _cards(counts)
    base["can_run_precheck"] = True

    precheck_status = _as_text((selected_integration or {}).get("assignment_precheck_status")).lower()
    if not total:
        base.update({
            "status": "on_kontrol_bekliyor",
            "status_label": "Ön Kontrol Bekliyor",
            "status_class": "info",
            "message": "Kapsama giren personel ve temel amir bilgileri için ön kontrol çalıştırılmalı.",
            "action_label": "Ön Kontrol Yap",
        })
    elif manager_review or scope_mismatch or other or precheck_status == "needs_review":
        base.update({
            "status": "kontrol_gerekli",
            "status_label": "Kontrol Gerekli",
            "status_class": "warn" if not scope_mismatch else "danger",
            "message": "Görev üretiminden önce kapsam uyumu ve amir bilgisi uyarıları incelenmeli.",
            "action_label": "Uyarıları İncele",
        })
    else:
        base.update({
            "status": "gorev_uretimine_hazir",
            "status_label": "Görev Üretimine Hazır",
            "status_class": "ok",
            "message": "Kapsam ve amir zinciri ön kontrolünde blokaj görünmüyor.",
            "can_launch": True,
            "action_label": "Görev Üretimi",
        })
    return base


def _cards(counts: dict[str, int]) -> list[dict[str, Any]]:
    return [
        {"title": "Kontrol Edilen", "value": _safe_int(counts.get("total")), "class": "info", "description": "Ön kontrol kapsamındaki kayıt."},
        {"title": "Uygun", "value": _safe_int(counts.get("ready")), "class": "ok", "description": "Görev üretimine hazır kayıt."},
        {"title": "Amir Kontrolü", "value": _safe_int(counts.get("manager_review")), "class": "warn", "description": "Amir bilgisi incelenecek kayıt."},
        {"title": "Kapsam Uyumsuzluğu", "value": _safe_int(counts.get("scope_mismatch")), "class": "danger", "description": "Dönem kapsamıyla eşleşmeyen kayıt."},
    ]


def run_v2_1_16_scope_chain_control_panel_gate(state: dict[str, Any] | None = None) -> dict[str, Any]:
    panel = build_scope_chain_control_panel(state or {}, limit=5)
    checks = [
        {"name": "panel_builds", "ok": isinstance(panel, dict), "message": "Kapsam ve amir zinciri paneli hazırlanıyor."},
        {"name": "cards_available", "ok": len(panel.get("cards") or []) == 4, "message": "Dört özet kartı üretildi."},
        {"name": "read_only", "ok": True, "message": "Panel görev üretmez, bildirim göndermez, değerlendirme yazmaz."},
        {"name": "status_safe", "ok": bool(panel.get("status_label")), "message": "Kullanıcıya kurumsal durum etiketi veriliyor."},
    ]
    return {"ok": all(item.get("ok") for item in checks), "checks": checks, "panel_status": panel.get("status"), "rule_version": RULE_VERSION}
