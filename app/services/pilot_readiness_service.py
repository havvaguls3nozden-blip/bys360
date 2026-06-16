from __future__ import annotations

from app.core.datetime_utils import utc_now
from datetime import datetime
from typing import Any


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360 SAFE V6: sessiz yakalanan hata loglandi.")
        return 0


def _safe_title(period: Any | None) -> str:
    title = getattr(period, "title", None)
    return str(title).strip() if title else "Aktif dönem yok"


def _status_meta(status: str) -> dict[str, str]:
    mapping = {
        "ready": {"label": "Hazır", "tone": "ok"},
        "watch": {"label": "Koşullu Hazır", "tone": "watch"},
        "blocked": {"label": "Hazır Değil", "tone": "critical"},
    }
    return mapping.get(status, {"label": "Belirsiz", "tone": "info"})


def _ensure_report(*, active_period: Any | None, requests_list: list[Any] | None, meetings: list[Any] | None, now: datetime | None, scope_employee_ids: list[int] | None, report: dict[str, Any] | None) -> dict[str, Any]:
    if report is not None:
        return report
    from app.services.performance.uat_service import build_go_live_uat_report

    return build_go_live_uat_report(
        active_period=active_period,
        requests_list=list(requests_list or []),
        meetings=list(meetings or []),
        now=now or utc_now(),
        scope_employee_ids=scope_employee_ids,
    )


def _ensure_smoke(report: dict[str, Any], smoke: dict[str, Any] | None) -> dict[str, Any]:
    if smoke is not None:
        return smoke
    from app.services.performance.final_pack_service import build_go_live_smoke_report

    return build_go_live_smoke_report(report)


def summarize_pilot_readiness(*, active_period: Any | None = None, requests_list: list[Any] | None = None, meetings: list[Any] | None = None, now: datetime | None = None, scope_employee_ids: list[int] | None = None, report: dict[str, Any] | None = None, smoke: dict[str, Any] | None = None, **_: Any) -> dict[str, Any]:
    report = _ensure_report(
        active_period=active_period,
        requests_list=requests_list,
        meetings=meetings,
        now=now,
        scope_employee_ids=scope_employee_ids,
        report=report,
    )
    smoke = _ensure_smoke(report, smoke)

    cards = dict(report.get("cards") or {})
    summary = dict(report.get("summary") or {})
    signoff = dict(report.get("signoff") or {})
    smoke_summary = dict(smoke.get("summary") or {})
    smoke_decision = dict(smoke.get("decision") or {})

    blocker_count = _safe_int(summary.get("blocker_count"))
    failed_count = _safe_int(summary.get("failed_check_count"))
    warning_count = _safe_int(summary.get("warning_count"))
    smoke_failed = _safe_int(smoke_summary.get("failed"))
    release_score = _safe_int(cards.get("release_score"))

    if blocker_count or failed_count or smoke_failed:
        status = "blocked"
        message = "Pilot başlamadan önce kritik başlıkları kapatmak gerekiyor."
    elif warning_count or release_score < 90:
        status = "watch"
        message = "Pilot koşullu hazır görünüyor; kalan uyarılar kapanırsa ilk kullanım daha temiz olur."
    else:
        status = "ready"
        message = "Pilot ve kullanıcı kabul turu için çekirdek akışlar hazır görünüyor."

    checks = [
        {
            "title": "Aktif dönem ve görev omurgası",
            "ok": bool(active_period),
            "status_label": "Geçti" if active_period else "Açık",
            "severity": "ok" if active_period else "critical",
            "detail": _safe_title(active_period),
            "action": "Aktif dönem yoksa önce doğru dönemi etkinleştir.",
        },
        {
            "title": "Canlı/UAT hazırlık skoru",
            "ok": release_score >= 70,
            "status_label": "Yeterli" if release_score >= 70 else "Düşük",
            "severity": "ok" if release_score >= 90 else ("watch" if release_score >= 70 else "critical"),
            "detail": f"Skor: {release_score} / 100",
            "action": "Skoru düşüren blokaj ve açık kontrolleri önce kapat.",
        },
        {
            "title": "Kritik blokajlar",
            "ok": blocker_count == 0,
            "status_label": "Temiz" if blocker_count == 0 else f"{blocker_count} açık",
            "severity": "ok" if blocker_count == 0 else "critical",
            "detail": "Pilot öncesi kapatılması gereken başlık sayısı.",
            "action": "UAT özeti ve görev/geri bildirim ekranlarından blokajları çöz.",
        },
        {
            "title": "Final smoke testi",
            "ok": smoke_failed == 0,
            "status_label": smoke_decision.get("label") or ("Temiz" if smoke_failed == 0 else "Açık"),
            "severity": "ok" if smoke_failed == 0 else "critical",
            "detail": smoke_decision.get("detail") or "Final doğrulama özeti okunamadı.",
            "action": "Yönetici sunumu öncesi smoke turunu tekrar koş.",
        },
        {
            "title": "Yayın gizliliği ve İK kontrolü",
            "ok": _safe_int(summary.get("employee_visible")) == 0,
            "status_label": "Kontrollü" if _safe_int(summary.get("employee_visible")) == 0 else "Açık",
            "severity": "ok" if _safe_int(summary.get("employee_visible")) == 0 else "watch",
            "detail": "Sonuçlar İK onayı tamamlanmadan personele açılmamalı.",
            "action": "Yayın ön kontrol ekranından görünürlük planını doğrula.",
        },
    ]

    warnings = list(report.get("warnings") or [])
    errors = list(report.get("blockers") or [])
    meta = _status_meta(status)
    return {
        "status": status,
        "label": meta["label"],
        "tone": meta["tone"],
        "message": message,
        "checks": checks,
        "warnings": warnings,
        "errors": errors,
        "summary": {
            "active_period": _safe_title(active_period),
            "release_score": release_score,
            "blocker_count": blocker_count,
            "failed_check_count": failed_count,
            "warning_count": warning_count,
            "smoke_failed": smoke_failed,
            "scope_count": len(scope_employee_ids or []),
            "signoff_label": signoff.get("label") or "-",
        },
    }


def get_pilot_readiness_summary(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return summarize_pilot_readiness(*args, **kwargs)


def run_pilot_readiness_checks(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
    return list(summarize_pilot_readiness(*args, **kwargs).get("checks") or [])


def build_pilot_readiness_context(*args: Any, **kwargs: Any) -> dict[str, Any]:
    summary = summarize_pilot_readiness(*args, **kwargs)
    return {
        "status": summary.get("status", "watch"),
        "label": summary.get("label", "Koşullu Hazır"),
        "tone": summary.get("tone", "watch"),
        "message": summary.get("message", "Pilot hazırlığı gözden geçirilmeli."),
        "summary": summary.get("summary") or {},
        "items": summary.get("checks") or [],
        "warnings": summary.get("warnings") or [],
        "errors": summary.get("errors") or [],
    }