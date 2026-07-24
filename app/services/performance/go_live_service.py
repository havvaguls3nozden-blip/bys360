from __future__ import annotations

from collections import Counter
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.core.datetime_utils import utc_now
from app.models import (
    EvaluationAssignment,
    FeedbackMeeting,
    PerformanceEvaluation,
    PerformancePeriod,
)
from app.services.performance_v2.reporting_workspace import build_publish_workspace_context

OPEN_ASSIGNMENT_STATUSES = {"bekliyor", "atandi", "devam_ediyor", "iade"}
COMPLETED_ASSIGNMENT_STATUSES = {"tamamlandi", "onaylandi"}
OPEN_REQUEST_STATUSES = {"bekliyor", "incelendi", "randevulandi", "randevu_ertelendi"}
ACTIVE_MEETING_STATUSES = {"planlandi", "ertelendi"}


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        if isinstance(value, Decimal):
            return float(value)
        return float(value)
    except (TypeError, ValueError):
        return default


def _full_name(user: Any) -> str:
    if not user:
        return "-"
    return (
        getattr(user, "full_name", None)
        or f"{getattr(user, 'ad', '')} {getattr(user, 'soyad', '')}".strip()
        or getattr(user, "email", None)
        or "-"
    )


def _meeting_start_text(meeting: FeedbackMeeting) -> str:
    meeting_date = getattr(meeting, "meeting_date", None)
    meeting_start = getattr(meeting, "meeting_start", None)
    if not meeting_date or not meeting_start:
        return "-"
    return datetime.combine(meeting_date, meeting_start).strftime("%d.%m.%Y %H:%M")


def _period_weight_sum(period: PerformancePeriod | None) -> float:
    if not period:
        return 0.0
    return round(
        _as_float(getattr(period, "level_1_weight", 0))
        + _as_float(getattr(period, "level_2_weight", 0))
        + _as_float(getattr(period, "level_3_weight", 0)),
        2,
    )


def build_performance_go_live_center(
    *,
    active_period: PerformancePeriod | None,
    requests_list: list[Any],
    meetings: list[Any],
    now: datetime | None = None,
    scope_employee_ids: list[int] | None = None,
) -> dict[str, Any]:
    now = now or utc_now()
    cards: dict[str, Any] = {
        "active_period": getattr(active_period, "title", None) or "Aktif dönem yok",
        "open_assignments": 0,
        "overdue_assignments": 0,
        "completed_evaluations": 0,
        "waiting_publish": 0,
        "published_to_employee": 0,
        "pending_acknowledgement": 0,
        "open_feedback_requests": 0,
        "critical_feedback_requests": 0,
        "active_meetings": 0,
        "overdue_meetings": 0,
        "ready_to_publish": 0,
        "blocked_publish": 0,
        "release_score": 0,
    }
    blockers: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    highlights: list[dict[str, Any]] = []
    endpoint_checks: list[dict[str, Any]] = []
    action_items: list[dict[str, Any]] = []
    manager_rows: list[dict[str, Any]] = []
    request_rows: list[dict[str, Any]] = []

    scoped_employee_ids = sorted({int(item) for item in (scope_employee_ids or []) if item is not None})
    assignments: list[EvaluationAssignment] = []
    evaluations: list[PerformanceEvaluation] = []
    if active_period is not None:
        assignment_query = EvaluationAssignment.query.filter_by(period_id=active_period.id)
        evaluation_query = PerformanceEvaluation.query.filter_by(period_id=active_period.id)
        if scoped_employee_ids:
            assignment_query = assignment_query.filter(EvaluationAssignment.employee_id.in_(scoped_employee_ids))
            evaluation_query = evaluation_query.filter(PerformanceEvaluation.employee_id.in_(scoped_employee_ids))
        assignments = assignment_query.all()
        evaluations = evaluation_query.all()

    publish_summary: dict[str, Any] = build_publish_workspace_context(
        active_period,
        allowed_employee_ids=scoped_employee_ids,
        limit=6,
    ) if active_period is not None else {
        "ready_count": 0,
        "blocked_count": 0,
        "blocked_reasons_summary": [],
        "blocked_rows": [],
        "publish_rate": 0.0,
        "internal_preview_count": 0,
        "published_count": 0,
    }

    cards["open_assignments"] = sum(1 for row in assignments if (getattr(row, "status", "") or "").strip().lower() in OPEN_ASSIGNMENT_STATUSES)
    cards["overdue_assignments"] = sum(1 for row in assignments if bool(getattr(row, "is_overdue", False)))
    cards["completed_evaluations"] = sum(1 for row in evaluations if str(getattr(row, "status", "")).strip().lower() == "tamamlandi")
    cards["waiting_publish"] = sum(1 for row in evaluations if str(getattr(row, "status", "")).strip().lower() == "tamamlandi" and not bool(getattr(row, "is_published_to_employee", False)))
    cards["published_to_employee"] = sum(1 for row in evaluations if bool(getattr(row, "is_published_to_employee", False)))
    cards["pending_acknowledgement"] = sum(1 for row in evaluations if bool(getattr(row, "is_published_to_employee", False)) and not bool(getattr(row, "employee_score_acknowledged_at", None)))
    cards["ready_to_publish"] = int(publish_summary.get("ready_count") or 0)
    cards["blocked_publish"] = int(publish_summary.get("blocked_count") or 0)

    open_requests = [row for row in requests_list if (getattr(row, "status", "") or "").strip().lower() in OPEN_REQUEST_STATUSES]
    critical_requests = []
    for row in open_requests:
        requested_at = getattr(row, "requested_at", None) or now
        age_days = max(int((now - requested_at).total_seconds() // 86400), 0)
        if age_days >= 5:
            critical_requests.append((row, age_days))
    cards["open_feedback_requests"] = len(open_requests)
    cards["critical_feedback_requests"] = len(critical_requests)

    active_meetings = [row for row in meetings if (getattr(row, "status", "") or "").strip().lower() in ACTIVE_MEETING_STATUSES]
    overdue_meetings = []
    for row in active_meetings:
        meeting_date = getattr(row, "meeting_date", None)
        meeting_end = getattr(row, "meeting_end", None)
        if meeting_date and meeting_end:
            end_dt = datetime.combine(meeting_date, meeting_end)
            if end_dt < now:
                overdue_meetings.append(row)
    cards["active_meetings"] = len(active_meetings)
    cards["overdue_meetings"] = len(overdue_meetings)

    weight_sum = _period_weight_sum(active_period)
    weights_ok = abs(weight_sum - 100.0) < 0.001 if active_period else False

    if active_period is None:
        blockers.append({"title": "Aktif performans dönemi bulunamadı", "detail": "Görev, yayın ve geri bildirim akışı aktif dönem olmadan canlıda izlenemez.", "action": "Önce doğru dönemi aktif hale getir."})
    else:
        if not weights_ok:
            blockers.append({"title": "Dönem ağırlıkları 100 etmiyor", "detail": f"Mevcut toplam {weight_sum:.2f}. Canlıda nihai puan tutarlılığı için toplam 100 olmalı.", "action": "Dönem ağırlıklarını 50/50/0 veya kurallı kombinasyona çek."})
        if not bool(getattr(active_period, "allow_feedback_requests", False)):
            warnings.append({"title": "Geri bildirim talebi kapalı", "detail": "Sonuçlar yayınlandıktan sonra personel talep açamayabilir.", "action": "Canlıya çıkmadan önce dönem ayarında geri bildirim talebini gözden geçir."})

    if cards["overdue_assignments"]:
        blockers.append({"title": "Geciken değerlendirme görevi var", "detail": f"Aktif dönemde {cards['overdue_assignments']} görev gecikmiş görünüyor.", "action": "Görev Sağlık Raporu ve Görev Yönetimi ekranından ilgili amirlere odaklan."})
    if cards["waiting_publish"]:
        warnings.append({"title": "Yayın bekleyen tamamlanmış değerlendirme var", "detail": f"{cards['waiting_publish']} kayıt tamamlanmış ama personele açılmamış durumda.", "action": "Yayın Yönetimi ekranında kontrollü yayın planını netleştir."})
    if cards["blocked_publish"]:
        blockers.append({"title": "Yayın kurallarına takılan kayıtlar var", "detail": f"{cards['blocked_publish']} kayıt açıklama, tamamlanma veya yayın kuralı nedeniyle personele açılamıyor.", "action": "Yayın ön kontrol ekranında blok nedenlerini tek tek kapat."})
    if cards["critical_feedback_requests"]:
        blockers.append({"title": "Kritik yaşa ulaşan geri bildirim talebi var", "detail": f"5 gün ve üzeri bekleyen {cards['critical_feedback_requests']} talep canlı memnuniyetini düşürür.", "action": "Takip ve Uyarı ile Operasyon Panelini birlikte kullanıp randevuya bağla."})
    if cards["overdue_meetings"]:
        warnings.append({"title": "Durumu kapanmamış eski görüşme var", "detail": f"Planlı/ertelenmiş statüde kalmış {cards['overdue_meetings']} görüşme bulundu.", "action": "Randevu detaylarına girip sonuç durumlarını güncelle."})
    if cards["pending_acknowledgement"]:
        warnings.append({"title": "Notu görüp onaylamayan personel var", "detail": f"{cards['pending_acknowledgement']} yayınlanmış sonuç henüz personel tarafından onaylanmamış.", "action": "Yayın sonrası hatırlatma veya yönetsel takip planı oluştur."})

    assignment_counter = Counter((getattr(row, "employee_id", None), getattr(row, "manager_level", None), getattr(row, "evaluator_id", None)) for row in assignments)
    duplicate_assignments = sum(1 for count in assignment_counter.values() if count > 1)
    if duplicate_assignments:
        blockers.append({"title": "Mükerrer görev kaydı şüphesi var", "detail": f"Aynı çalışan-seviye-değerlendirici kombinasyonunda {duplicate_assignments} mükerrer örüntü bulundu.", "action": "Görev Sağlık Raporu ile assignment üretimini tekrar doğrula."})

    manager_counter: Counter[str] = Counter()
    for row in open_requests:
        for manager in (getattr(row, "level_1_manager", None), getattr(row, "level_2_manager", None), getattr(row, "level_3_manager", None)):
            name = _full_name(manager)
            if name != "-":
                manager_counter[name] += 1
    for name, total in manager_counter.most_common(6):
        manager_rows.append({"manager_name": name, "open_request_count": total})

    for row, age_days in sorted(critical_requests, key=lambda pair: (-pair[1], getattr(getattr(pair[0], 'employee', None), 'full_name', '') or ''))[:6]:
        request_rows.append({
            "request_id": getattr(row, "id", None),
            "employee_name": _full_name(getattr(row, "employee", None)),
            "period_title": getattr(getattr(row, "period", None), "title", None) or "-",
            "status": getattr(row, "status", None) or "-",
            "age_days": age_days,
            "manager_text": ", ".join([name for name in [_full_name(getattr(row, "level_1_manager", None)), _full_name(getattr(row, "level_2_manager", None)), _full_name(getattr(row, "level_3_manager", None))] if name != "-"]) or "Yönetici çözümlenemedi",
        })

    release_checks = [
        {"label": "Aktif dönem", "ok": active_period is not None, "detail": getattr(active_period, "title", None) or "Aktif dönem bulunamadı"},
        {"label": "Ağırlık toplamı", "ok": weights_ok, "detail": f"Toplam {weight_sum:.2f}" if active_period else "Dönem yok"},
        {"label": "Görev gecikmesi", "ok": cards["overdue_assignments"] == 0, "detail": f"{cards['overdue_assignments']} geciken görev"},
        {"label": "Kritik talep", "ok": cards["critical_feedback_requests"] == 0, "detail": f"{cards['critical_feedback_requests']} kritik talep"},
        {"label": "Mükerrer görev", "ok": duplicate_assignments == 0, "detail": f"{duplicate_assignments} örüntü"},
        {"label": "Yayın bekleyen kayıt", "ok": cards["waiting_publish"] == 0, "detail": f"{cards['waiting_publish']} yayın bekleyen değerlendirme"},
        {"label": "Yayın blokajı", "ok": cards["blocked_publish"] == 0, "detail": f"{cards['blocked_publish']} bloklu kayıt"},
    ]

    action_items.extend([
        {"title": "UAT özetini aç", "detail": "Canlı öncesi son kabul görünümünü tek sayfada doğrula.", "href": "/performance/go-live-center/uat"},
        {"title": "Görev Sağlık Raporunu çalıştır", "detail": "Eksik veya mükerrer görevleri canlı öncesi sıfırla.", "href": "/performance/task-management/health"},
        {"title": "Takip ve Uyarı merkezini çalıştır", "detail": "Açık talep ve randevu uyarılarını canlıya çıkmadan önce üret.", "href": "/performance/feedback-watch"},
        {"title": "Yönetici özetini gözden geçir", "detail": "Günlük/haftalık özet metni ve alıcı önerilerini kontrol et.", "href": "/performance/feedback-executive-summary"},
        {"title": "Audit panelinde izleri doğrula", "detail": "Talep ve randevu akışında olay izi kesintisiz görünüyor mu bak.", "href": "/performance/feedback-audit"},
        {"title": "Yayın ön kontrolünü çalıştır", "detail": "Bloke nedenlerini kapatmadan canlı yayın adımına geçmeyin.", "href": "/performance/v2/faz5/publish/preflight"},
    ])

    endpoint_checks.extend([
        {"label": "UAT Özeti", "href": "/performance/go-live-center/uat", "status": "hazır"},
        {"label": "Randevu Sistemi", "href": "/performance/feedback-meetings", "status": "hazır"},
        {"label": "Operasyon Paneli", "href": "/performance/feedback-ops", "status": "hazır"},
        {"label": "Takip ve Uyarı", "href": "/performance/feedback-watch", "status": "hazır"},
        {"label": "Yönetici Özeti", "href": "/performance/feedback-executive-summary", "status": "hazır"},
        {"label": "Audit ve SLA", "href": "/performance/feedback-audit", "status": "hazır"},
        {"label": "Görev Sağlık Raporu", "href": "/performance/task-management/health", "status": "hazır"},
        {"label": "Yayın Ön Kontrol", "href": "/performance/v2/faz5/publish/preflight", "status": "hazır"},
        {"label": "Issue CSV", "href": "/performance/go-live-center/issues.csv", "status": "hazır"},
    ])

    done_count = sum(1 for item in release_checks if item["ok"])
    cards["release_score"] = round((done_count / len(release_checks)) * 100) if release_checks else 0

    if cards["release_score"] >= 90:
        highlights.append({"tone": "ok", "title": "Canlıya çıkış skoru güçlü", "detail": "Kalan maddeler daha çok operasyon takibi seviyesinde görünüyor."})
    elif cards["release_score"] >= 70:
        highlights.append({"tone": "watch", "title": "Canlıya yakın ama kontrol gerekiyor", "detail": "Blokajları kapatmadan yayın yapmak ileride ek iş çıkarabilir."})
    else:
        highlights.append({"tone": "critical", "title": "Canlıya çıkış için erken", "detail": "Blokajlar kapanmadan yayın riskli görünüyor."})

    return {
        "generated_at": now,
        "cards": cards,
        "blockers": blockers,
        "warnings": warnings,
        "highlights": highlights,
        "release_checks": release_checks,
        "endpoint_checks": endpoint_checks,
        "action_items": action_items,
        "manager_rows": manager_rows,
        "request_rows": request_rows,
        "publish_summary": publish_summary,
    }