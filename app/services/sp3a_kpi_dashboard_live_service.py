"""
BYS360 SP-3A KPI Dashboard Live Service V2

Şema uyumlu çalışır:
- SP-1 hedef/KPI tabloları varsa gerçek veriyi okur.
- Tablo/kolon yoksa ekranı kırmaz; kurumsal boş durum üretir.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from sqlalchemy import inspect, text

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from flask_sqlalchemy import SQLAlchemy

db: SQLAlchemy | None
try:
    from app import db
except Exception:  # pragma: no cover
    db = None


TARGET_TABLE_CANDIDATES = [
    "strategic_targets",
    "kpi_targets",
    "target_cards",
    "performance_targets",
    "sp1_target_cards",
    "sp1_targets",
]


def _has_global_kpi_scope(user: Any) -> bool:
    # BYS360 DEFECT AR: bu ekrana erisim is_top_or_manager ile kapiliyor
    # (admin, sistem_yoneticisi, baskan, baskan_yardimcisi, grup_baskani,
    # koordinator, performans_yetkilisi, ik, mali_musavir, birim_sorumlusu)
    # -- ama bu roller kurum genelinde ayni gorunurluge sahip degil. Yeni
    # bir rol/kapsam ayrimi icat etmek yerine, uygulamada zaten kurulu ve
    # denetlenmis olan ayni ayrim yeniden kullanilir (role_group_for
    # "global" donenler organizasyon capinda; digerleri kendi
    # kapsamlariyla sinirli).
    try:
        from app.services.ai_decision.visibility_scope import role_group_for

        return role_group_for(user) == "global"
    except Exception:
        logger.exception("BYS360 SP3A KPI rol kapsami belirlenemedi.")
        return False


def _safe_tables() -> set[str]:
    if db is None:
        return set()
    try:
        return set(inspect(db.engine).get_table_names())
    except Exception:
        return set()


def _safe_columns(table_name: str) -> set[str]:
    if db is None:
        return set()
    try:
        return {col["name"] for col in inspect(db.engine).get_columns(table_name)}
    except Exception:
        return set()


def _first_existing_table(candidates: list[str]) -> str | None:
    tables = _safe_tables()
    for table in candidates:
        if table in tables:
            return table
    return None


def _col(cols: set[str], *names: str) -> str | None:
    for name in names:
        if name in cols:
            return name
    return None


def _number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _status_from_rate(rate: float) -> str:
    if rate >= 90:
        return "İyi Gidiyor"
    if rate >= 70:
        return "Takip Edilmeli"
    return "Riskli"


def _risk_from_rate(rate: float) -> str:
    if rate >= 90:
        return "Düşük"
    if rate >= 70:
        return "Orta"
    return "Yüksek"


def _normalize_risk(value: Any) -> str:
    text_value = str(value or "").strip().lower()
    if text_value in {"yüksek", "yuksek", "high", "riskli", "kritik"}:
        return "Yüksek"
    if text_value in {"orta", "medium", "takip", "izlem"}:
        return "Orta"
    return "Düşük"


def _normalize_status(value: Any) -> str:
    text_value = str(value or "").strip().lower()
    if text_value in {"riskli", "kritik", "gecikti", "gecikmiş", "gecikmis"}:
        return "Riskli"
    if text_value in {"takip", "takip edilmeli", "devam", "devam ediyor"}:
        return "Takip Edilmeli"
    return "İyi Gidiyor"


def _build_ai_notes(total: int, average: float, risky: list[dict], watch: list[dict], strong: list[dict]) -> list[str]:
    if total == 0:
        return [
            "Henüz aktif KPI veya hedef kaydı bulunmadığı için yönetici analizi beklemede.",
            "İlk hedefler girildiğinde risk, gerçekleşme ve ağırlık dengesi bu alanda özetlenecek.",
        ]

    notes = [f"Aktif hedeflerin ortalama gerçekleşme oranı %{average} seviyesinde."]
    if risky:
        notes.append(f"{len(risky)} hedef yüksek riskte görünüyor; bu hedefler için yönetici takibi önerilir.")
    if watch:
        notes.append(f"{len(watch)} hedef orta risk bandında; dönem bitmeden gerçekleşme verileri güncellenmelidir.")
    if strong:
        notes.append(f"{len(strong)} hedef güçlü performans bandında; iyi uygulama örnekleri raporlanabilir.")
    if not risky and average >= 90:
        notes.append("Genel tablo güçlü görünüyor; odak noktası sürdürülebilirlik ve kanıt kayıtları olmalıdır.")
    return notes[:4]


def _empty_context(message: str) -> dict[str, Any]:
    return {
        "page_title": "KPI Dashboardu",
        "summary": {
            "total_targets": 0,
            "average_completion": 0,
            "weighted_completion": 0,
            "risk_targets": 0,
            "watch_targets": 0,
            "strong_targets": 0,
        },
        "risk_counts": {"Düşük": 0, "Orta": 0, "Yüksek": 0},
        "status_counts": {"İyi Gidiyor": 0, "Takip Edilmeli": 0, "Riskli": 0},
        "targets": [],
        "risky_targets": [],
        "watch_targets": [],
        "strong_targets": [],
        "ai_notes": [
            message,
            "KPI/Hedef kayıtları oluşturulduğunda bu ekran otomatik olarak dolacaktır.",
        ],
        "data_note": message,
        "empty_state": True,
    }


def build_sp3a_kpi_dashboard_context(current_user=None) -> dict[str, Any]:
    target_table = _first_existing_table(TARGET_TABLE_CANDIDATES)
    if not target_table:
        return _empty_context("KPI/Hedef veri tablosu henüz canlı veriye bağlanmamış.")

    cols = _safe_columns(target_table)
    id_col = _col(cols, "id")
    name_col = _col(cols, "target_name", "hedef_adi", "name", "title", "label")
    code_col = _col(cols, "target_code", "hedef_kodu", "code")
    status_col = _col(cols, "status", "durum")
    risk_col = _col(cols, "risk_level", "risk_seviyesi", "risk")
    target_value_col = _col(cols, "target_value", "hedef_deger", "goal_value", "expected_value")
    actual_value_col = _col(cols, "actual_value", "gerceklesen", "current_value", "realized_value")
    weight_col = _col(cols, "weight", "agirlik")
    active_col = _col(cols, "is_active", "active")
    owner_col = _col(cols, "owner_name", "owner", "sahip", "unit_name", "birim_adi")
    owner_id_col = _col(cols, "owner_user_id", "user_id", "created_by_id", "assigned_to_id", "sahip_id")
    due_col = _col(cols, "end_date", "bitis", "due_date")

    if not id_col or not name_col:
        return _empty_context(f"{target_table} tablosu dashboard için gerekli alanları taşımıyor.")

    select_parts = [f"{id_col} AS id", f"{name_col} AS name"]
    select_parts.append(f"{code_col} AS code" if code_col else "NULL AS code")
    select_parts.append(f"{status_col} AS status" if status_col else "NULL AS status")
    select_parts.append(f"{risk_col} AS risk_level" if risk_col else "NULL AS risk_level")
    select_parts.append(f"{target_value_col} AS target_value" if target_value_col else "NULL AS target_value")
    select_parts.append(f"{actual_value_col} AS actual_value" if actual_value_col else "NULL AS actual_value")
    select_parts.append(f"{weight_col} AS weight" if weight_col else "NULL AS weight")
    select_parts.append(f"{owner_col} AS owner_name" if owner_col else "NULL AS owner_name")
    select_parts.append(f"{due_col} AS due_date" if due_col else "NULL AS due_date")

    where_parts = []
    params: dict[str, Any] = {}
    if active_col:
        where_parts.append(f"COALESCE({active_col}, true) = true")
    # BYS360 DEFECT AR: current_user parametresi eskiden hic kullanilmiyordu --
    # koordinator/grup_baskani/birim_sorumlusu gibi orta kademe yoneticiler
    # (is_top_or_manager kapisindan gecen ama gercek Baskan/Admin/IK
    # yetkisine sahip olmayan roller) her istekte tum kurumun KPI/hedef
    # verisini goruyordu -- bu uygulamada baska yerde (ai_decision.
    # visibility_scope.role_group_for) zaten kurulu olan global/manager_scope
    # ayrimiyla tutarsizdi. Global-olmayan roller icin, tablo bir sahip-id
    # kolonu tasiyorsa sonuc o kullanicinin kendi kayitlariyla sinirlanir.
    if owner_id_col and not _has_global_kpi_scope(current_user):
        current_user_id = getattr(current_user, "id", None)
        if current_user_id is not None:
            where_parts.append(f"{owner_id_col} = :current_user_id")
            params["current_user_id"] = int(current_user_id)
        else:
            # Kimlik cikarilamiyorsa (beklenmeyen kullanici nesnesi), yedek
            # olarak sinirsiz sonuc DONMEZ -- kapsamsiz bir cikti asla
            # verilmez; guvenli varsayilan bos sonuctur.
            where_parts.append("1 = 0")

    where_clause = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
    sql = f"""
        SELECT {", ".join(select_parts)}
        FROM {target_table}
        {where_clause}
        ORDER BY id DESC
        LIMIT 50
    """

    try:
        rows = db.session.execute(text(sql), params).mappings().all()  # type: ignore[union-attr]
    except Exception as exc:
        logger.exception("BYS360 SP3A KPI verisi okunamadı | exc=%s", exc)
        return _empty_context("KPI verisi okunurken sorun oluştu.")

    targets: list[dict[str, Any]] = []
    total_rate = 0.0
    weighted_sum = 0.0
    weight_total = 0.0
    risk_counts = {"Düşük": 0, "Orta": 0, "Yüksek": 0}
    status_counts = {"İyi Gidiyor": 0, "Takip Edilmeli": 0, "Riskli": 0}

    for row in rows:
        target_value = _number(row.get("target_value"), 0.0)
        actual_value = _number(row.get("actual_value"), 0.0)
        weight = _number(row.get("weight"), 0.0)

        completion = max(0.0, min(150.0, (actual_value / target_value) * 100.0)) if target_value > 0 else 0.0
        status = _normalize_status(row.get("status") or _status_from_rate(completion))
        risk = _normalize_risk(row.get("risk_level") or _risk_from_rate(completion))

        risk_counts[risk] = risk_counts.get(risk, 0) + 1
        status_counts[status] = status_counts.get(status, 0) + 1
        total_rate += completion
        if weight > 0:
            weighted_sum += completion * weight
            weight_total += weight

        targets.append({
            "id": row.get("id"),
            "code": row.get("code") or f"KPI-{row.get('id')}",
            "name": row.get("name") or "Adsız Hedef",
            "owner_name": row.get("owner_name") or "Kurumsal",
            "target_value": round(target_value, 2),
            "actual_value": round(actual_value, 2),
            "completion_rate": round(completion, 1),
            "weight": round(weight, 1),
            "status": status,
            "risk_level": risk,
            "due_date": row.get("due_date"),
        })

    total = len(targets)
    average_completion = round(total_rate / total, 1) if total else 0
    weighted_completion = round(weighted_sum / weight_total, 1) if weight_total else average_completion

    risky_targets = [t for t in targets if t["risk_level"] == "Yüksek" or t["completion_rate"] < 70]
    watch_targets = [t for t in targets if t["risk_level"] == "Orta" or 70 <= t["completion_rate"] < 90]
    strong_targets = [t for t in targets if t["completion_rate"] >= 90]

    return {
        "page_title": "KPI Dashboardu",
        "summary": {
            "total_targets": total,
            "average_completion": average_completion,
            "weighted_completion": weighted_completion,
            "risk_targets": len(risky_targets),
            "watch_targets": len(watch_targets),
            "strong_targets": len(strong_targets),
        },
        "risk_counts": risk_counts,
        "status_counts": status_counts,
        "targets": targets[:20],
        "risky_targets": risky_targets[:8],
        "watch_targets": watch_targets[:8],
        "strong_targets": strong_targets[:8],
        "ai_notes": _build_ai_notes(total, average_completion, risky_targets, watch_targets, strong_targets),
        "data_note": "Dashboard canlı KPI/Hedef veri tablolarından beslenir.",
        "empty_state": total == 0,
    }
