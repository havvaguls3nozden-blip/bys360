from __future__ import annotations

from typing import Iterable

from app.models import PerformanceCriteria, PerformanceEvaluation, PerformancePeriod
from app.services.performance.health_report import build_performance_task_health_report
from app.services.performance.rules import get_authoritative_performance_rules_snapshot
from app.services.performance_v2.validators import build_period_validation_report


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _label_issue_tone(issue: str) -> str:
    text = str(issue or "").strip().lower()
    if not text:
        return "info"
    if any(token in text for token in ("yayımlan", "yayın", "kilitli değil")):
        return "warning"
    return "blocker"


def _criteria_snapshot() -> dict[str, object]:
    criteria_rows = (
        PerformanceCriteria.query.filter_by(is_active=True)
        .order_by(PerformanceCriteria.sort_order.asc(), PerformanceCriteria.id.asc())
        .all()
    )
    total = round(sum(_safe_float(getattr(row, "weight", 0.0)) for row in criteria_rows), 2)
    return {
        "rows": criteria_rows,
        "count": len(criteria_rows),
        "total": total,
        "ok": abs(total - 100.0) < 0.001,
    }


def _build_release_checks(
    *,
    period_validation: dict[str, object],
    criteria_snapshot: dict[str, object],
    health_summary: dict[str, object],
) -> list[dict[str, object]]:
    weights_total = round(
        _safe_float((period_validation.get("weights") or {}).get("level_1"))
        + _safe_float((period_validation.get("weights") or {}).get("level_2"))
        + _safe_float((period_validation.get("weights") or {}).get("level_3")),
        2,
    )
    return [
        {
            "label": "Tek aktif dönem",
            "ok": not any("birden fazla aktif dönem" in str(issue).lower() for issue in (period_validation.get("issues") or [])),
            "detail": "Aynı anda sadece bir aktif dönem açık olmalı.",
        },
        {
            "label": "Ağırlık toplamı",
            "ok": abs(weights_total - 100.0) < 0.001,
            "detail": f"Mevcut toplam {weights_total:.2f}",
        },
        {
            "label": "Kriter toplamı",
            "ok": bool(criteria_snapshot.get("ok")),
            "detail": f"Aktif kriter toplamı {criteria_snapshot.get('total', 0):.2f}",
        },
        {
            "label": "Mükerrer görev",
            "ok": int(health_summary.get("duplicate_level_count") or 0) == 0,
            "detail": f"{int(health_summary.get('duplicate_level_count') or 0)} satır",
        },
        {
            "label": "Amir eşleşmesi",
            "ok": int(health_summary.get("mismatch_count") or 0) == 0,
            "detail": f"{int(health_summary.get('mismatch_count') or 0)} fark",
        },
        {
            "label": "Açıkta görev",
            "ok": int(health_summary.get("uncovered_count") or 0) == 0,
            "detail": f"{int(health_summary.get('uncovered_count') or 0)} kayıt",
        },
    ]


def preflight_has_blockers(report: dict[str, object] | None) -> bool:
    return bool((report or {}).get("blockers"))


def build_task_management_preflight_report(
    period,
    scope_user_ids: Iterable[int] | None = None,
) -> dict[str, object]:
    rules_snapshot = get_authoritative_performance_rules_snapshot()
    criteria_snapshot = _criteria_snapshot()

    if not period:
        return {
            "period": None,
            "rules_snapshot": rules_snapshot,
            "criteria_snapshot": criteria_snapshot,
            "period_validation": {
                "issue_count": 1,
                "issues": ["Aktif dönem bulunamadı."],
                "weights": {"level_1": 50.0, "level_2": 50.0, "level_3": 0.0},
            },
            "health_report": build_performance_task_health_report(None, scope_user_ids),
            "blockers": [
                {
                    "title": "Aktif dönem bulunamadı",
                    "detail": "Görev üretimi ve canlı ön kontrol aktif dönem olmadan yürütülemez.",
                }
            ],
            "warnings": [],
            "infos": [],
            "release_checks": [],
            "readiness_score": 0,
            "summary": {
                "criteria_total": criteria_snapshot.get("total", 0.0),
                "duplicate_level_count": 0,
                "mismatch_count": 0,
                "uncovered_count": 0,
                "chain_issue_count": 0,
                "orphan_total": 0,
            },
            "quick_actions": [],
        }

    scope_ids = {int(value) for value in (scope_user_ids or []) if value}
    all_periods = PerformancePeriod.query.order_by(PerformancePeriod.id.desc()).all()

    evaluations_query = PerformanceEvaluation.query.filter_by(period_id=period.id)
    if scope_ids:
        evaluations_query = evaluations_query.filter(PerformanceEvaluation.employee_id.in_(list(scope_ids)))
    evaluations = evaluations_query.all()

    period_validation = build_period_validation_report(
        period,
        all_periods=all_periods,
        evaluations=evaluations,
    )
    health_report = build_performance_task_health_report(period, scope_ids or None)
    health_summary = health_report.get("summary") or {}

    blockers: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    infos: list[dict[str, str]] = []

    for issue in period_validation.get("issues") or []:
        payload = {"title": "Dönem kural kontrolü", "detail": str(issue)}
        if _label_issue_tone(str(issue)) == "warning":
            warnings.append(payload)
        else:
            blockers.append(payload)

    if not bool(criteria_snapshot.get("ok")):
        blockers.append(
            {
                "title": "Kriter toplamı 100 değil",
                "detail": f"Aktif kriter toplamı {criteria_snapshot.get('total', 0):.2f}. Görev üretimi öncesi kriter ağırlıkları 100 olmalı.",
            }
        )

    if int(health_summary.get("duplicate_level_count") or 0) > 0:
        blockers.append(
            {
                "title": "Mükerrer görev satırı bulundu",
                "detail": f"{int(health_summary.get('duplicate_level_count') or 0)} çalışan/seviye kombinasyonunda birden fazla görev satırı var.",
            }
        )
    if int(health_summary.get("mismatch_count") or 0) > 0:
        blockers.append(
            {
                "title": "Değerlendirme ve görev amiri farklı",
                "detail": f"{int(health_summary.get('mismatch_count') or 0)} kayıtta evaluation ile assignment amiri eşleşmiyor.",
            }
        )

    orphan_total = int(health_summary.get("orphan_evaluation_count") or 0) + int(health_summary.get("orphan_assignment_count") or 0)
    if orphan_total > 0:
        blockers.append(
            {
                "title": "Yetim kayıt bulundu",
                "detail": f"{orphan_total} kayıt görev/değerlendirme eşleşmesi olmadan duruyor.",
            }
        )

    if int(health_summary.get("uncovered_count") or 0) > 0:
        blockers.append(
            {
                "title": "Açıkta kalan görev var",
                "detail": f"{int(health_summary.get('uncovered_count') or 0)} kayıtta amir/vekâlet kapsaması çözülememiş.",
            }
        )

    if int(health_summary.get("chain_conflict_count") or 0) > 0:
        blockers.append(
            {
                "title": "Amir zinciri çakışması bulundu",
                "detail": f"{int(health_summary.get('chain_conflict_count') or 0)} personelde zincir çatışması görünüyor.",
            }
        )

    if int(health_summary.get("chain_issue_count") or 0) > 0:
        warnings.append(
            {
                "title": "Zincir uyarısı bulunan kayıt var",
                "detail": f"{int(health_summary.get('chain_issue_count') or 0)} personelde eksik veya onarıma açık zincir uyarısı bulunuyor.",
            }
        )

    if int(health_summary.get("overdue_count") or 0) > 0:
        warnings.append(
            {
                "title": "Gecikmiş görev bulundu",
                "detail": f"{int(health_summary.get('overdue_count') or 0)} görev gecikmiş durumda.",
            }
        )

    if int(health_summary.get("delegated_count") or 0) > 0:
        infos.append(
            {
                "title": "Vekâletli görevler algılandı",
                "detail": f"{int(health_summary.get('delegated_count') or 0)} görev aynı seviyede vekil amire yönlenmiş.",
            }
        )

    if int(health_summary.get("balanced_chain_count") or 0) > 0 and not blockers:
        infos.append(
            {
                "title": "Zincir dengesi güçlü görünüyor",
                "detail": f"{int(health_summary.get('balanced_chain_count') or 0)} personelde zincir eksiksiz ve dengeli.",
            }
        )

    release_checks = _build_release_checks(
        period_validation=period_validation,
        criteria_snapshot=criteria_snapshot,
        health_summary=health_summary,
    )
    completed_checks = sum(1 for row in release_checks if bool(row.get("ok")))
    readiness_score = round((completed_checks / len(release_checks)) * 100) if release_checks else 0

    quick_actions = [
        {
            "label": "Görev sağlığı",
            "href": f"/performance/task-management/health?period_id={period.id}",
            "description": "Mükerrer, yetim ve amir eşleşme farklarını detaylı incele.",
        },
        {
            "label": "Atama denetimi",
            "href": f"/performance/task-management/audit?period_id={period.id}",
            "description": "Ham uyarı ve açıkta kayıt nedenlerini tek ekranda doğrula.",
        },
        {
            "label": "Görev yönetimi",
            "href": f"/performance/task-management?period_id={period.id}",
            "description": "Düzeltmelerden sonra yeniden üretim başlat.",
        },
    ]

    return {
        "period": period,
        "rules_snapshot": rules_snapshot,
        "criteria_snapshot": criteria_snapshot,
        "period_validation": period_validation,
        "health_report": health_report,
        "blockers": blockers,
        "warnings": warnings,
        "infos": infos,
        "release_checks": release_checks,
        "readiness_score": readiness_score,
        "summary": {
            "criteria_total": criteria_snapshot.get("total", 0.0),
            "duplicate_level_count": int(health_summary.get("duplicate_level_count") or 0),
            "mismatch_count": int(health_summary.get("mismatch_count") or 0),
            "uncovered_count": int(health_summary.get("uncovered_count") or 0),
            "chain_issue_count": int(health_summary.get("chain_issue_count") or 0),
            "orphan_total": orphan_total,
        },
        "quick_actions": quick_actions,
    }


__all__ = [
    "build_task_management_preflight_report",
    "preflight_has_blockers",
]