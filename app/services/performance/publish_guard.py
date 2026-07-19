from __future__ import annotations

import logging
from typing import Any

from app.models import PerformanceEvaluation

logger = logging.getLogger(__name__)
# BYS360_PHASE6_2_PUBLISH_PREFLIGHT_LAZY_IMPORT
# publish_guard uygulama açılışında publish_preflight_rules import etmez.
# Böylece visibility_guard -> publish_preflight_rules -> publish_guard döngüsü kırılır.
PUBLISH_PREFLIGHT_RULE_VERSION = "phase1.4b-personnel-support-publish-approval-v1"


def _phase6_2_publish_preflight_rules():
    from app.services.performance import publish_preflight_rules as _rules
    return _rules


def validate_evaluation_for_publish(period, evaluation):
    return _phase6_2_publish_preflight_rules().validate_evaluation_for_publish(period, evaluation)

def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return 0


def _safe_float(value: Any) -> float:
    try:
        return float(value or 0)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return 0.0


def publish_preflight_has_blockers(report: dict[str, Any] | None) -> bool:
    return bool((report or {}).get("blockers") or [])


def _finding(title: str, detail: str, *, code: str = "publish_guard", evaluation_id: int | None = None, employee_id: int | None = None) -> dict[str, Any]:
    row = {"title": title, "detail": detail, "code": code}
    if evaluation_id is not None:
        row["evaluation_id"] = evaluation_id
    if employee_id is not None:
        row["employee_id"] = employee_id
    return row


def _period_evaluations(period: Any | None) -> list[Any]:
    if not period or not getattr(period, "id", None):
        return []
    try:
        return (
            PerformanceEvaluation.query
            .filter_by(period_id=period.id)
            .order_by(PerformanceEvaluation.id.asc())
            .all()
        )
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return []


def _strict_period_findings(period: Any | None, *, limit: int = 12) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    blocked_count = 0

    for evaluation in _period_evaluations(period):
        result = validate_evaluation_for_publish(period, evaluation)
        if result.infos and not result.blockers and not result.ok:
            # Başkan gibi yayın dışı istisnalar blokaj listesine şişirme yapmasın.
            continue
        if result.blockers:
            blocked_count += 1
            for item in result.blockers:
                if len(blockers) >= limit:
                    break
                blockers.append(
                    _finding(
                        "Yayın ön kontrol blokajı",
                        item.message,
                        code=item.code,
                        evaluation_id=getattr(evaluation, "id", None),
                        employee_id=getattr(evaluation, "employee_id", None),
                    )
                )
        if result.warnings:
            for item in result.warnings:
                if len(warnings) >= limit:
                    break
                warnings.append(
                    _finding(
                        "Yayın ön kontrol uyarısı",
                        item.message,
                        code=item.code,
                        evaluation_id=getattr(evaluation, "id", None),
                        employee_id=getattr(evaluation, "employee_id", None),
                    )
                )

    if blocked_count > limit:
        blockers.append(_finding("Ek blokaj var", f"İlk {limit} kayıt gösterildi; toplam {blocked_count} değerlendirme yayın ön kontrolüne takıldı.", code="more_blockers"))

    return blockers, warnings, blocked_count


def build_publish_preflight_report(*, period=None, scorecard: dict[str, Any] | None = None, publish_summary: dict[str, Any] | None = None) -> dict[str, Any]:
    scorecard = scorecard or {}
    publish_summary = publish_summary or {}

    total_count = _safe_int(scorecard.get("count") if scorecard else publish_summary.get("total_count"))
    published_count = _safe_int(scorecard.get("published_count") if scorecard else publish_summary.get("published_count"))
    completed_count = _safe_int(scorecard.get("completed_count") if scorecard else publish_summary.get("completed_count"))
    ready_count = _safe_int(publish_summary.get("ready_count"))
    summary_blocked_count = _safe_int(publish_summary.get("blocked_count"))
    internal_preview_count = _safe_int(publish_summary.get("internal_preview_count"))
    publish_rate = _safe_float(publish_summary.get("publish_rate"))

    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    infos: list[dict[str, Any]] = []
    actions: list[dict[str, Any]] = []

    if not period:
        blockers.append(_finding("Dönem seçilmedi", "Yayın işlemi için önce geçerli bir performans dönemi seçilmelidir.", code="missing_period"))
    if total_count <= 0:
        blockers.append(_finding("Sonuç kaydı yok", "Seçili dönem için yayınlanabilecek veya incelenebilecek karne kaydı bulunamadı.", code="no_results"))
    if total_count > 0 and completed_count <= 0:
        blockers.append(_finding("Tamamlanmış sonuç yok", "Tamamlanmamış değerlendirmeler personele açılamaz.", code="no_completed_results"))

    strict_blockers, strict_warnings, strict_blocked_count = _strict_period_findings(period)
    blockers.extend(strict_blockers)
    warnings.extend(strict_warnings)

    blocked_count = max(summary_blocked_count, strict_blocked_count)

    if total_count > 0 and completed_count > 0 and ready_count <= 0 and published_count <= 0:
        blockers.append(_finding("Yayın için hazır kayıt yok", "Tamamlanmış kayıtlar olsa da yayın koşullarını geçen bir sonuç görünmüyor.", code="no_ready_results"))

    if blocked_count > 0 and not strict_blockers:
        warnings.append(_finding("Bloke kayıtlar var", f"{blocked_count} kayıt yayın sırasında atlanacaktır. Önce blok nedenleri gözden geçirilmelidir.", code="summary_blockers"))
    if internal_preview_count > 0:
        warnings.append(_finding("İç kullanımda bekleyen sonuçlar var", f"{internal_preview_count} tamamlanmış kayıt yalnızca iç kullanım görünümünde duruyor.", code="internal_preview"))
    if published_count > 0 and publish_rate < 100:
        warnings.append(_finding("Kısmi yayın durumu", f"Dönemde sonuçların yalnızca %{publish_rate:.1f} kadarı personele açık görünüyor.", code="partial_publish"))

    if total_count > 0:
        infos.append({"title": "Toplam sonuç", "detail": str(total_count)})
        infos.append({"title": "Tamamlanan", "detail": str(completed_count)})
        infos.append({"title": "Personele açık", "detail": str(published_count)})
        infos.append({"title": "Hemen yayımlanabilir", "detail": str(ready_count)})
        infos.append({"title": "Yayın ön kontrol sürümü", "detail": PUBLISH_PREFLIGHT_RULE_VERSION})

    if blockers:
        readiness_label = "Blokaj var"
        readiness_tone = "critical"
    elif warnings:
        readiness_label = "Kontrollü ilerleyin"
        readiness_tone = "watch"
    else:
        readiness_label = "Yayın için uygun"
        readiness_tone = "calm"

    actions.append({"label": "Hazır kayıt", "value": ready_count, "tone": "calm"})
    actions.append({"label": "Bloke kayıt", "value": blocked_count, "tone": "critical" if blocked_count else "calm"})
    actions.append({"label": "Personele açık", "value": published_count, "tone": "calm"})
    actions.append({"label": "İç kullanım", "value": internal_preview_count, "tone": "watch" if internal_preview_count else "calm"})

    return {
        "period": period,
        "readiness_label": readiness_label,
        "readiness_tone": readiness_tone,
        "blockers": blockers,
        "warnings": warnings,
        "infos": infos,
        "actions": actions,
        "ready_count": ready_count,
        "blocked_count": blocked_count,
        "published_count": published_count,
        "completed_count": completed_count,
        "internal_preview_count": internal_preview_count,
        "readiness_score": max(0, min(100, int(round((ready_count / total_count) * 100)))) if total_count else 0,
    }


def build_scorecard_visibility_summary(scorecard: dict[str, Any] | None) -> dict[str, Any]:
    rows = list((scorecard or {}).get("rows") or [])
    employee_visible = 0
    internal_preview = 0
    locked = 0
    viewed = 0
    acknowledged = 0
    reason_counts: dict[tuple[str, str], int] = {}

    for row in rows:
        visibility = row.get("visibility") or {}
        state = (visibility.get("publish_state") or "").strip().lower()
        if state == "published":
            employee_visible += 1
        elif state == "internal_preview":
            internal_preview += 1
        else:
            locked += 1
            reason_code = str(visibility.get("reason_code") or "locked").strip() or "locked"
            reason_label = str(visibility.get("reason") or "Kilit nedeni belirtilmedi.").strip() or "Kilit nedeni belirtilmedi."
            key = (reason_code, reason_label)
            reason_counts[key] = reason_counts.get(key, 0) + 1

        if row.get("employee_viewed_at"):
            viewed += 1
        if row.get("employee_acknowledged_at"):
            acknowledged += 1

    top_reasons = [
        {"code": code, "label": label, "count": count}
        for (code, label), count in sorted(reason_counts.items(), key=lambda item: (-item[1], item[0][1].lower()))[:6]
    ]

    count = _safe_int((scorecard or {}).get("count"))
    return {
        "count": count,
        "employee_visible": employee_visible,
        "internal_preview": internal_preview,
        "locked": locked,
        "viewed": viewed,
        "acknowledged": acknowledged,
        "top_reasons": top_reasons,
    }


# BYS360_A5_P2D3_PUBLISH_GUARD_STRICT_BLOCKERS_LOCK_START
# Static contract anchor: 2026-04-18-publish-preflight-lock-v1
PUBLISH_GUARD_STRICT_BLOCKERS_LOCK_ID = "2026-04-18-publish-preflight-lock-v1"
# BYS360_A5_P2D3_PUBLISH_GUARD_STRICT_BLOCKERS_LOCK_END

