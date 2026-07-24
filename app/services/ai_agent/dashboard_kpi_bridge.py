from __future__ import annotations

from typing import Any

from sqlalchemy import text

from app.extensions import db

from .performance_bridge import has_performance_overview_permission
from .repository import insert_agent_audit_log, table_columns, table_exists

TARGET_TABLE_CANDIDATES = (
    "performance_targets",
    "strategic_targets",
    "kpi_targets",
    "target_cards",
    "sp1_target_cards",
    "sp1_targets",
)


def _user_id(user: Any) -> int | None:
    try:
        return int(getattr(user, "id", None) or 0) or None
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return None


def _first_existing_table() -> str | None:
    for table_name in TARGET_TABLE_CANDIDATES:
        if table_exists(table_name):
            return table_name
    return None


def _pick(columns: set[str], *names: str) -> str | None:
    for name in names:
        if name in columns:
            return name
    return None


def _number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _normalize_risk(value: Any, completion_rate: float) -> str:
    text_value = str(value or "").strip().lower()
    if text_value in {"yüksek", "yuksek", "high", "riskli", "kritik"} or completion_rate < 70:
        return "Yüksek"
    if text_value in {"orta", "medium", "takip", "izlem", "izlenecek"} or completion_rate < 90:
        return "Orta"
    return "Düşük"


def _normalize_status(value: Any, completion_rate: float) -> str:
    text_value = str(value or "").strip().lower()
    if text_value in {"riskli", "kritik", "gecikti", "gecikmiş", "gecikmis"} or completion_rate < 70:
        return "Riskli"
    if text_value in {"takip", "takip edilmeli", "devam", "devam ediyor"} or completion_rate < 90:
        return "Takip Edilmeli"
    return "İyi Gidiyor"


def _empty_summary(message: str, *, privileged: bool, user_id: int | None) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "ok": True,
        "scope": "yonetici_kpi_ozeti" if privileged else "kullanici_kpi_ozeti",
        "can_view_global_summary": privileged,
        "decision_notice": "BYS360 Asistanı KPI/Hedef kararı vermez; hedef kapatmaz veya veri değiştirmez.",
        "data_note": message,
        "counts": {
            "total_targets": 0,
            "average_completion": 0,
            "weighted_completion": 0,
            "risky_targets": 0,
            "watch_targets": 0,
            "strong_targets": 0,
            "overdue_targets": 0,
        },
        "cards": [],
        "briefing_notes": [
            message,
            "KPI/Hedef kayıtları oluştukça AG-3 ajan özeti otomatik dolacaktır.",
        ],
        "risk_titles": [],
    }
    if privileged:
        summary["cards"] = [
            {"key": "total_targets", "title": "Toplam Hedef", "value": 0, "route": "/performans/stratejik/kpi-dashboard", "description": "Canlı KPI/Hedef kaydı bekleniyor."},
            {"key": "risky_targets", "title": "Riskli Hedef", "value": 0, "route": "/performans/stratejik/kpi-analiz", "description": "Riskli hedef görünmüyor veya veri henüz yok."},
            {"key": "average_completion", "title": "Ortalama Gerçekleşme", "value": "%0", "route": "/performans/stratejik/kpi-dashboard", "description": "Gerçekleşme oranı için hedef verisi bekleniyor."},
        ]
    insert_agent_audit_log(
        user_id=user_id,
        action_key="ag3_dashboard_kpi_summary",
        detail=f"scope={summary['scope']} empty=true message={message}",
    )
    return summary


def build_dashboard_kpi_summary_for_user(user: Any) -> dict[str, Any]:
    """AG-3 KPI/Hedef ve yönetici dashboard bağlantısı.

    Bu fonksiyon yalnızca güvenli sayı/özet ve brifing notu üretir. Hedef kapatma,
    veri güncelleme veya idari karar işlemi yapmaz.
    """
    user_id = _user_id(user)
    privileged = has_performance_overview_permission(user)
    target_table = _first_existing_table()
    if not target_table:
        return _empty_summary(
            "KPI/Hedef veri tablosu bulunamadı; stratejik performans bağlantısı boş durumla güvenli çalışıyor.",
            privileged=privileged,
            user_id=user_id,
        )

    columns = table_columns(target_table)
    id_col = _pick(columns, "id")
    name_col = _pick(columns, "target_name", "hedef_adi", "name", "title", "label")
    code_col = _pick(columns, "target_code", "hedef_kodu", "code")
    status_col = _pick(columns, "status", "durum")
    risk_col = _pick(columns, "risk_level", "risk_seviyesi", "risk")
    target_value_col = _pick(columns, "target_value", "hedef_deger", "goal_value", "expected_value")
    actual_value_col = _pick(columns, "actual_value", "gerceklesen", "current_value", "realized_value")
    completion_col = _pick(columns, "completion_rate", "basari_orani", "completion", "progress")
    weight_col = _pick(columns, "weight", "agirlik")
    active_col = _pick(columns, "is_active", "active")
    owner_user_col = _pick(columns, "owner_user_id", "user_id", "personnel_id")
    owner_unit_col = _pick(columns, "owner_unit_id", "unit_id", "organization_unit_id")
    owner_name_col = _pick(columns, "owner_name", "owner", "sahip", "unit_name", "birim_adi")
    due_col = _pick(columns, "end_date", "bitis", "due_date")

    if not id_col or not name_col:
        return _empty_summary(
            f"{target_table} tablosu AG-3 KPI özeti için gerekli temel alanları taşımıyor.",
            privileged=privileged,
            user_id=user_id,
        )

    select_parts = [f"{id_col} AS id", f"{name_col} AS name"]
    select_parts.append(f"{code_col} AS code" if code_col else "NULL AS code")
    select_parts.append(f"{status_col} AS status" if status_col else "NULL AS status")
    select_parts.append(f"{risk_col} AS risk_level" if risk_col else "NULL AS risk_level")
    select_parts.append(f"{target_value_col} AS target_value" if target_value_col else "NULL AS target_value")
    select_parts.append(f"{actual_value_col} AS actual_value" if actual_value_col else "NULL AS actual_value")
    select_parts.append(f"{completion_col} AS completion_rate" if completion_col else "NULL AS completion_rate")
    select_parts.append(f"{weight_col} AS weight" if weight_col else "NULL AS weight")
    select_parts.append(f"{owner_name_col} AS owner_name" if owner_name_col else "NULL AS owner_name")
    select_parts.append(f"{owner_user_col} AS owner_user_id" if owner_user_col else "NULL AS owner_user_id")
    select_parts.append(f"{owner_unit_col} AS owner_unit_id" if owner_unit_col else "NULL AS owner_unit_id")
    select_parts.append(f"{due_col} AS due_date" if due_col else "NULL AS due_date")

    where_parts = []
    params: dict[str, Any] = {}
    if active_col:
        where_parts.append(f"COALESCE({active_col}, true) = true")
    if not privileged:
        if owner_user_col and user_id:
            where_parts.append(f"{owner_user_col} = :user_id")
            params["user_id"] = user_id
        else:
            return _empty_summary(
                "Standart kullanıcı için kişi bazlı KPI alanı bulunmadığından genel stratejik özet gizlendi.",
                privileged=False,
                user_id=user_id,
            )
    where_clause = "WHERE " + " AND ".join(where_parts) if where_parts else ""
    sql = f"""
        SELECT {", ".join(select_parts)}
        FROM {target_table}
        {where_clause}
        ORDER BY {id_col} DESC
        LIMIT 200
    """

    try:
        rows = db.session.execute(text(sql), params).mappings().all()
    except Exception as exc:
        return _empty_summary(
            f"KPI/Hedef verisi okunurken güvenli boş durum üretildi: {exc}",
            privileged=privileged,
            user_id=user_id,
        )

    targets: list[dict[str, Any]] = []
    total_rate = 0.0
    weighted_sum = 0.0
    weight_total = 0.0
    overdue_targets = 0
    for row in rows:
        target_value = _number(row.get("target_value"), 0.0)
        actual_value = _number(row.get("actual_value"), 0.0)
        direct_completion = row.get("completion_rate")
        completion = _number(direct_completion, -1.0)
        if completion < 0:
            completion = max(0.0, min(150.0, (actual_value / target_value) * 100.0)) if target_value > 0 else 0.0
        completion = max(0.0, min(150.0, completion))
        weight = _number(row.get("weight"), 0.0)
        status = _normalize_status(row.get("status"), completion)
        risk = _normalize_risk(row.get("risk_level"), completion)
        due_date = row.get("due_date")
        is_overdue = False
        # SQL tarafında tarih karşılaştırması şema farkları nedeniyle burada sade tutulur.
        if due_date and completion < 100 and str(status).lower() in {"riskli", "takip edilmeli"}:
            is_overdue = False
        if is_overdue:
            overdue_targets += 1
        total_rate += completion
        if weight > 0:
            weighted_sum += completion * weight
            weight_total += weight
        targets.append({
            "id": row.get("id"),
            "code": row.get("code") or f"KPI-{row.get('id')}",
            "title": row.get("name") or "Adsız Hedef",
            "owner_name": row.get("owner_name") or "Kurumsal",
            "completion_rate": round(completion, 1),
            "weight": round(weight, 1),
            "status": status,
            "risk_level": risk,
            "due_date": str(due_date or ""),
        })

    total = len(targets)
    average_completion = round(total_rate / total, 1) if total else 0
    weighted_completion = round(weighted_sum / weight_total, 1) if weight_total else average_completion
    risky_targets = [target for target in targets if target["risk_level"] == "Yüksek" or target["completion_rate"] < 70]
    watch_targets = [target for target in targets if target["risk_level"] == "Orta" or 70 <= target["completion_rate"] < 90]
    strong_targets = [target for target in targets if target["completion_rate"] >= 90]

    briefing_notes: list[str] = []
    if total == 0:
        briefing_notes.append("Yetki kapsamında aktif KPI/Hedef kaydı bulunmuyor.")
    else:
        briefing_notes.append(f"Yetki kapsamındaki {total} hedefin ortalama gerçekleşmesi %{average_completion} seviyesinde.")
        if risky_targets:
            briefing_notes.append(f"{len(risky_targets)} hedef yüksek risk bandında; yönetici takibi önerilir.")
        if watch_targets:
            briefing_notes.append(f"{len(watch_targets)} hedef takip bandında; dönem bitmeden gerçekleşme verisi güncellenmelidir.")
        if strong_targets and average_completion >= 90:
            briefing_notes.append("Genel KPI görünümü güçlü; iyi uygulama örnekleri raporlanabilir.")
        if not risky_targets and total > 0:
            briefing_notes.append("Yüksek riskli hedef görünmüyor; düzenli güncelleme ve kanıt kayıtları sürdürülmelidir.")

    counts = {
        "total_targets": total,
        "average_completion": average_completion,
        "weighted_completion": weighted_completion,
        "risky_targets": len(risky_targets),
        "watch_targets": len(watch_targets),
        "strong_targets": len(strong_targets),
        "overdue_targets": overdue_targets,
    }

    cards = [
        {
            "key": "total_targets",
            "title": "Toplam Hedef",
            "value": total,
            "route": "/performans/stratejik/kpi-dashboard",
            "description": "Yetki kapsamındaki KPI/Hedef kayıtlarının toplamı.",
        },
        {
            "key": "average_completion",
            "title": "Ortalama Gerçekleşme",
            "value": f"%{average_completion}",
            "route": "/performans/stratejik/kpi-dashboard",
            "description": "Hedef gerçekleşme oranlarının güvenli özet ortalaması.",
        },
        {
            "key": "risky_targets",
            "title": "Riskli Hedef",
            "value": len(risky_targets),
            "route": "/performans/stratejik/kpi-analiz",
            "description": "Yüksek risk veya düşük gerçekleşme bandındaki hedef sayısı.",
        },
        {
            "key": "watch_targets",
            "title": "Takip Edilecek Hedef",
            "value": len(watch_targets),
            "route": "/performans/stratejik/hedefler",
            "description": "Orta risk bandındaki hedeflerin sayı düzeyi özeti.",
        },
    ]

    summary: dict[str, Any] = {
        "ok": True,
        "scope": "yonetici_kpi_ozeti" if privileged else "kullanici_kpi_ozeti",
        "can_view_global_summary": privileged,
        "decision_notice": "BYS360 Asistanı KPI/Hedef kararı vermez; hedef kapatmaz veya veri değiştirmez.",
        "data_note": f"AG-3 özeti {target_table} tablosundan güvenli sayı düzeyinde üretildi.",
        "counts": counts,
        "cards": cards,
        "briefing_notes": briefing_notes[:5],
        "risk_titles": [
            {"title": item["title"], "completion_rate": item["completion_rate"], "risk_level": item["risk_level"]}
            for item in risky_targets[:5]
        ] if privileged else [],
    }
    insert_agent_audit_log(
        user_id=user_id,
        action_key="ag3_dashboard_kpi_summary",
        detail=f"scope={summary['scope']} counts={counts}",
    )
    return summary
