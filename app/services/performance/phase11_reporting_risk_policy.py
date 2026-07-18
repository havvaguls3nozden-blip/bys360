# -*- coding: utf-8 -*-
"""
BYS360 Performans Tamamlama Faz 11
Raporlama, Dashboard ve Risk Analizi Politika Merkezi

Amaç:
- Yönetici dashboard'unda kurumsal performans görünürlüğünü standartlaştırmak.
- Riskli personel, aksatan amir, düşük performans ve yüksek başarı analizlerini tek sözleşmeye almak.
- Kategori/birim ortalamalarında kişi detayı sızdırmamak.
- Başkan/Admin genel görünürlük; yönetici kapsam sınırlı görünürlük; personel kişisel görünürlük.
- Raporların teknik statü değil Türkçe kurumsal ifade üretmesini sağlamak.
"""
from __future__ import annotations


import logging
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence
logger = logging.getLogger(__name__)


PHASE11_POLICY_MARKER = "BYS360_PERFORMANCE_COMPLETION_PHASE11_REPORTING_RISK_POLICY"

RISK_LOW_SCORE = "low_score"
RISK_REPEAT_LOW = "repeat_low"
RISK_MISSING_EVALUATION = "missing_evaluation"
RISK_DELAYED_MANAGER = "delayed_manager"
RISK_INCONSISTENT_SCORE = "inconsistent_score"
RISK_NONE = "none"

RISK_LABELS = {
    RISK_LOW_SCORE: "Düşük Performans Riski",
    RISK_REPEAT_LOW: "Tekrarlayan Düşük Performans Riski",
    RISK_MISSING_EVALUATION: "Eksik Değerlendirme Riski",
    RISK_DELAYED_MANAGER: "Aksayan Değerlendirme Süreci",
    RISK_INCONSISTENT_SCORE: "Puan Tutarsızlığı İncelemesi",
    RISK_NONE: "Risk Görünmüyor",
}

RISK_LEVEL_LABELS = {
    "critical": "Kritik",
    "high": "Yüksek",
    "medium": "Orta",
    "low": "Düşük",
    "none": "Risk Yok",
}

REPORT_VISIBILITY_LABELS = {
    "personal": "Kişisel Rapor",
    "scope": "Yetkili Kapsam Raporu",
    "institution": "Kurum Geneli Rapor",
    "denied": "Erişim Yetkisi Yok",
}


@dataclass(frozen=True)
class RiskDecision:
    risk_type: str
    risk_label: str
    risk_level: str
    risk_level_label: str
    score: float
    reasons: tuple[str, ...]
    recommended_action: str


@dataclass(frozen=True)
class ReportVisibilityDecision:
    allowed: bool
    scope: str
    label: str
    can_view_person_detail: bool
    can_export: bool
    reason: str


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(str(value).replace(",", "."))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _role_names(user: Any) -> set[str]:
    names: set[str] = set()
    if user is None:
        return names
    for attr in ("role", "rol", "role_name", "title", "unvan"):
        value = getattr(user, attr, None)
        if value:
            names.add(str(value).strip().lower())
    roles = getattr(user, "roles", None)
    if roles:
        try:
            for role in roles:
                for attr in ("name", "role_name", "title"):
                    value = getattr(role, attr, None)
                    if value:
                        names.add(str(value).strip().lower())
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/phase11_reporting_risk_policy.py")
    return names


def _is_admin_or_president(user: Any) -> bool:
    joined = " ".join(_role_names(user))
    return any(token in joined for token in ["admin", "sistem yöneticisi", "sistem yoneticisi", "başkan", "baskan"])


def _is_manager(user: Any) -> bool:
    joined = " ".join(_role_names(user))
    return any(token in joined for token in ["grup başkanı", "grup baskani", "koordinatör", "koordinator", "personel ve destek", "müdür", "mudur"])


def resolve_report_visibility(
    *,
    viewer: Any,
    target_employee_id: Any = None,
    scope_employee_ids: Optional[Sequence[Any]] = None,
    report_type: str = "dashboard",
) -> ReportVisibilityDecision:
    viewer_id = _to_int(getattr(viewer, "id", None), 0)
    target_id = _to_int(target_employee_id, 0)
    scope_ids = {str(x) for x in (scope_employee_ids or []) if str(x or "").strip()}

    if _is_admin_or_president(viewer):
        return ReportVisibilityDecision(
            allowed=True,
            scope="institution",
            label=REPORT_VISIBILITY_LABELS["institution"],
            can_view_person_detail=True,
            can_export=True,
            reason="Başkan/Admin kurum geneli rapor ve analiz görünürlüğüne sahiptir.",
        )

    if _is_manager(viewer):
        if target_id and str(target_id) not in scope_ids:
            return ReportVisibilityDecision(
                allowed=False,
                scope="denied",
                label=REPORT_VISIBILITY_LABELS["denied"],
                can_view_person_detail=False,
                can_export=False,
                reason="Bu personel yetkili rapor kapsamınızda değildir.",
            )
        return ReportVisibilityDecision(
            allowed=True,
            scope="scope",
            label=REPORT_VISIBILITY_LABELS["scope"],
            can_view_person_detail=True,
            can_export=True,
            reason="Yönetici yalnızca yetkili organizasyon kapsamındaki raporları görebilir.",
        )

    if viewer_id and target_id and viewer_id == target_id:
        return ReportVisibilityDecision(
            allowed=True,
            scope="personal",
            label=REPORT_VISIBILITY_LABELS["personal"],
            can_view_person_detail=False,
            can_export=False,
            reason="Personel yalnızca kendi kişisel performans özetini görebilir.",
        )

    return ReportVisibilityDecision(
        allowed=False,
        scope="denied",
        label=REPORT_VISIBILITY_LABELS["denied"],
        can_view_person_detail=False,
        can_export=False,
        reason="Bu rapora erişim yetkiniz bulunmamaktadır.",
    )


def classify_score_band(score: Any) -> str:
    value = _to_float(score, 0.0)
    if value < 70:
        return "Düşük Performans"
    if value >= 90:
        return "Çok Başarılı"
    return "Beklenen Düzey"


def classify_risk(row: Mapping[str, Any]) -> RiskDecision:
    final_score = _to_float(row.get("final_score") or row.get("score") or row.get("nihai_puan"), 0.0)
    low_count = _to_int(row.get("low_score_count_in_year") or row.get("repeat_low_count"), 0)
    missing_count = _to_int(row.get("missing_evaluation_count") or row.get("missing_count"), 0)
    overdue_days = _to_int(row.get("max_overdue_days") or row.get("overdue_days"), 0)
    score_spread = _to_float(row.get("manager_score_spread") or row.get("score_spread"), 0.0)

    reasons: List[str] = []
    risk_type = RISK_NONE
    level = "none"
    risk_score = 0.0
    action = "Standart izleme yeterlidir."

    if low_count >= 2:
        risk_type = RISK_REPEAT_LOW
        level = "critical"
        risk_score = 95.0
        reasons.append("Aynı takvim yılında tekrarlayan düşük performans kaydı var.")
        action = "Tekrarlayan düşük performans süreci yetkili onaya taşınmalıdır."
    elif final_score and final_score < 70:
        risk_type = RISK_LOW_SCORE
        level = "high"
        risk_score = 85.0
        reasons.append("Nihai puan 70'in altında.")
        action = "Düşük performans üst onay ve gelişim süreci izlenmelidir."
    elif missing_count > 0:
        risk_type = RISK_MISSING_EVALUATION
        level = "medium"
        risk_score = min(70.0, 40.0 + missing_count * 10.0)
        reasons.append("Eksik değerlendirme görevi bulunuyor.")
        action = "Eksik değerlendirme görevleri tamamlatılmalıdır."
    elif overdue_days > 0:
        risk_type = RISK_DELAYED_MANAGER
        level = "medium" if overdue_days < 7 else "high"
        risk_score = min(80.0, 35.0 + overdue_days * 5.0)
        reasons.append("Değerlendirme sürecinde gecikme var.")
        action = "Aksatan amir bildirimi ve süreç takibi yapılmalıdır."
    elif score_spread >= 30:
        risk_type = RISK_INCONSISTENT_SCORE
        level = "medium"
        risk_score = min(75.0, score_spread * 2.0)
        reasons.append("Amir puanları arasında yüksek fark var.")
        action = "Puan tutarlılığı yönetici tarafından incelenmelidir."

    return RiskDecision(
        risk_type=risk_type,
        risk_label=RISK_LABELS[risk_type],
        risk_level=level,
        risk_level_label=RISK_LEVEL_LABELS[level],
        score=round(risk_score, 2),
        reasons=tuple(reasons),
        recommended_action=action,
    )


def build_risk_rows(rows: Iterable[Mapping[str, Any]], *, include_none: bool = False) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for row in rows or []:
        decision = classify_risk(row)
        if decision.risk_type == RISK_NONE and not include_none:
            continue
        item = dict(row)
        item.update(
            {
                "risk_type": decision.risk_type,
                "risk_label": decision.risk_label,
                "risk_level": decision.risk_level,
                "risk_level_label": decision.risk_level_label,
                "risk_score": decision.score,
                "risk_reasons": list(decision.reasons),
                "recommended_action": decision.recommended_action,
            }
        )
        result.append(item)
    return sorted(result, key=lambda x: x.get("risk_score", 0), reverse=True)


def summarize_dashboard(rows: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    rows = list(rows or [])
    scores: List[float] = []
    low_count = 0
    high_count = 0
    missing_count = 0
    overdue_manager_count = 0

    for row in rows:
        score = _to_float(row.get("final_score") or row.get("score"), 0.0)
        if score:
            scores.append(score)
            if score < 70:
                low_count += 1
            if score >= 90:
                high_count += 1
        missing_count += _to_int(row.get("missing_evaluation_count") or row.get("missing_count"), 0)
        if _to_int(row.get("max_overdue_days") or row.get("overdue_days"), 0) > 0:
            overdue_manager_count += 1

    avg = round(sum(scores) / len(scores), 2) if scores else None
    risk_rows = build_risk_rows(rows)

    return {
        "total_records": len(rows),
        "scored_records": len(scores),
        "average_score": avg,
        "low_score_count": low_count,
        "high_score_count": high_count,
        "missing_evaluation_count": missing_count,
        "overdue_manager_count": overdue_manager_count,
        "risk_count": len(risk_rows),
    }


def summarize_category_averages(rows: Iterable[Mapping[str, Any]], *, min_group_size: int = 2) -> List[Dict[str, Any]]:
    """
    Kategori ortalamaları kişi detayı sızdırmadan hesaplanır.
    min_group_size altındaki gruplar anonimleştirilir.
    """
    bucket: Dict[str, List[float]] = {}
    for row in rows or []:
        category = str(row.get("category") or row.get("personnel_category") or row.get("kategori") or "Diğer").strip() or "Diğer"
        score = _to_float(row.get("final_score") or row.get("score"), 0.0)
        if score:
            bucket.setdefault(category, []).append(score)

    result: List[Dict[str, Any]] = []
    for category, scores in bucket.items():
        if len(scores) < min_group_size:
            result.append(
                {
                    "category": category,
                    "record_count": len(scores),
                    "average_score": None,
                    "privacy_label": "Kişi detayı gizlendi",
                }
            )
        else:
            result.append(
                {
                    "category": category,
                    "record_count": len(scores),
                    "average_score": round(sum(scores) / len(scores), 2),
                    "privacy_label": "Anonim ortalama",
                }
            )
    return sorted(result, key=lambda x: (x["average_score"] is not None, x["average_score"] or 0), reverse=True)


def build_delayed_manager_summary(rows: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for row in rows or []:
        pending = _to_int(row.get("pending_count"), 0)
        overdue = _to_int(row.get("overdue_count"), 0)
        max_days = _to_int(row.get("max_overdue_days"), 0)
        if pending <= 0 and overdue <= 0:
            continue
        result.append(
            {
                "manager_id": row.get("manager_id"),
                "manager_name": row.get("manager_name") or "Değerlendirici",
                "pending_count": pending,
                "overdue_count": overdue,
                "max_overdue_days": max_days,
                "status_label": "Aksatan Amir" if overdue else "Bekleyen Görev Var",
            }
        )
    return sorted(result, key=lambda x: (x["overdue_count"], x["max_overdue_days"], x["pending_count"]), reverse=True)


def build_report_export_contract(*, visibility: ReportVisibilityDecision, report_type: str = "dashboard") -> Dict[str, Any]:
    return {
        "allowed": visibility.allowed and visibility.can_export,
        "scope": visibility.scope,
        "report_type": report_type,
        "label": visibility.label,
        "file_label": "BYS360 Performans Raporu",
        "contains_person_detail": bool(visibility.can_view_person_detail),
        "reason": visibility.reason if not (visibility.allowed and visibility.can_export) else "Rapor dışa aktarım için hazır.",
    }


def phase11_reporting_contract() -> Dict[str, Any]:
    return {
        "executive_dashboard": True,
        "risk_analysis": True,
        "delayed_manager_summary": True,
        "category_average_privacy": True,
        "scope_limited_reports": True,
        "president_admin_full_visibility": True,
        "personnel_personal_summary_only": True,
        "report_export_contract": True,
        "technical_status_hidden": True,
        "phase_marker": PHASE11_POLICY_MARKER,
    }

# BYS360_PERFORMANCE_COMPLETION_PHASE11_REPORTING_RISK_BOUND
# Raporlama, dashboard ve risk analizi phase11_reporting_risk_policy sözleşmesini kullanır.
