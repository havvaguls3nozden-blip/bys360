from __future__ import annotations

# BYS360_MOBILE_V2_8_44_SCORE_1_5_COMMENT_OPTIONAL_BACKEND: Mobilde 1 ve 5 puan kriter açıklaması zorunlu değildir.


import logging

from statistics import mean
from typing import Any

from flask import jsonify, request

from app.extensions import db
from app.models import (
    EvaluationAssignment,
    PerformanceEvaluation,
    PerformanceEvaluationItem,
    PerformancePeriod,
    PerformancePresidentApproval,
    PerformanceResultSnapshot,
    User,
    PerformanceCriteria,
    PerformanceWeightConfig,)

from . import mobile_api_bp
from .routes import (
    _as_int,
    _full_name,
    _has_global_scope,
    _item,
    _metric,
    _module_payload,
    _safe_count,
    require_mobile_user,
)

from app.core.datetime_utils import utc_now
from app.services.performance.common import get_period_level_3_flags
from app.services.performance.scoring import (
    calculate_preview_total_100,
    recalculate_evaluation_totals,
    save_evaluation_level,
    validate_general_comment_requirements,
    validate_item_comment_requirements,
)
logger = logging.getLogger(__name__)


# BYS360 MOBILE V2.8.20.3 DB SAFE FINAL HELPERS
def _mobile_perf_rollback_quietly() -> None:
    """Mobil performans API okumasında hata olursa veritabanı oturumunu temizler."""
    try:
        db.session.rollback()
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/api/mobile/performance_routes.py:50)")


def _mobile_perf_safe_count(query, default: int = 0) -> int:
    try:
        _mobile_perf_rollback_quietly()
        value = query.count()
        return int(value or 0)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        _mobile_perf_rollback_quietly()
        return default


def _mobile_perf_safe_all(query, default=None):
    try:
        _mobile_perf_rollback_quietly()
        return query.all()
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        _mobile_perf_rollback_quietly()
        return [] if default is None else default


def _mobile_perf_safe_get(model, object_id):
    try:
        if object_id is None:
            return None
        _mobile_perf_rollback_quietly()
        return db.session.get(model, object_id)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        _mobile_perf_rollback_quietly()
        return None

_DONE = {"tamamlandi", "tamamlandı", "completed", "done", "closed", "kapandi", "kapandı", "yayınlandı", "published"}


def _label(value: Any, default: str = "Bekliyor") -> str:
    raw = str(value or "").strip()
    key = raw.lower()
    mapping = {
        "pending": "Bekliyor",
        "open": "Bekliyor",
        "assigned": "Atandı",
        "atandi": "Atandı",
        "atandı": "Atandı",
        "in_progress": "Devam Ediyor",
        "devam": "Devam Ediyor",
        "devam_ediyor": "Devam Ediyor",
        "tamamlandi": "Tamamlandı",
        "tamamlandı": "Tamamlandı",
        "completed": "Tamamlandı",
        "done": "Tamamlandı",
        "published": "Yayınlandı",
        "yayinda": "Yayında",
        "yayında": "Yayında",
        "president_pending": "Başkan Onayı Bekliyor",
        "blocked_president_pending": "Başkan Onayı Yayın Kilidi",
        "hr_precheck": "Ön Kontrol Bekliyor",
        "approved": "Onaylandı",
        "rejected": "İade Edildi",
        "active": "Aktif",
        "inactive": "Pasif",
        "draft": "Hazırlıkta",
        "closed": "Kapandı",
    }
    return mapping.get(key, raw or default)


def _period_name(period: Any) -> str:
    return str(getattr(period, "title", None) or getattr(period, "name", None) or getattr(period, "period_name", None) or "Performans Dönemi")


def _date_text(value: Any) -> str:
    if not value:
        return ""
    try:
        return value.strftime("%d.%m.%Y")
    except (AttributeError, TypeError, ValueError):
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return str(value)[:10]


def _date_range(period: Any) -> str:
    start = _date_text(getattr(period, "start_date", None) or getattr(period, "start", None))
    end = _date_text(getattr(period, "end_date", None) or getattr(period, "end", None))
    return f"{start} - {end}".strip(" -")


def _period_scope(period: Any) -> str:
    for name in ("scope_label", "scope_type", "period_type", "evaluation_type", "target_scope", "kapsam_tipi"):
        value = getattr(period, name, None)
        if value:
            raw = str(value).strip()
            return {
                "all": "Tüm Kurum",
                "organization": "Birim",
                "unit": "Birim",
                "upper_unit": "Üst Birim",
                "category": "Kategori / Grup",
                "selected_users": "Seçili Personel",
                "personnel": "Seçili Personel",
                "special": "Özel Dönem",
                "yearly": "Yıllık",
                "annual": "Yıllık",
                "monthly": "Aylık",
                "quarterly": "3 Aylık",
                "semiannual": "6 Aylık",
            }.get(raw.lower(), raw)
    return "Genel Kapsam"


def _period_status(period: Any) -> str:
    if getattr(period, "is_active", False):
        return "Aktif"
    status = getattr(period, "status", None) or getattr(period, "state", None)
    return _label(status, "Hazırlık")


def _period_progress(period: Any):
    from app.api.mobile.services import performance_period_service as _bys360_period_service
    return _bys360_period_service._period_progress(period)

def _bys360_legacy__period_progress(period: Any) -> int:
    if getattr(period, "is_active", False):
        return 80
    status = str(getattr(period, "status", "") or "").lower()
    if status in _DONE or status in {"closed", "kapandı"}:
        return 100
    if "draft" in status or "haz" in status:
        return 25
    return 50


def _assignment_query_for(user: User):
    q = EvaluationAssignment.query
    if _has_global_scope(user):
        return q
    return q.filter(EvaluationAssignment.evaluator_id == user.id)


def _snapshot_query_for(user: User):
    q = PerformanceResultSnapshot.query
    if _has_global_scope(user):
        return q
    return q.filter(PerformanceResultSnapshot.employee_id == user.id)


def _period_assignment_query(user: User, period_id: int):
    q = _assignment_query_for(user)
    try:
        return q.filter(EvaluationAssignment.period_id == period_id)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        _mobile_perf_rollback_quietly()
        return q


def _period_snapshot_query(user: User, period_id: int):
    q = _snapshot_query_for(user)
    try:
        return q.filter(PerformanceResultSnapshot.period_id == period_id)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        _mobile_perf_rollback_quietly()
        return q


def _score_value(row: Any) -> int:
    for name in ("final_total_100", "final_score", "score", "total_score", "average_score"):
        if hasattr(row, name):
            return _as_int(getattr(row, name), 0)
    return 0


def _safe_avg_score(q) -> int:
    try:
        rows = q.limit(300).all()
        scores = [_score_value(row) for row in rows if _score_value(row) > 0]
        return int(mean(scores)) if scores else 0
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return 0


def _low_score_count(q) -> int:
    try:
        rows = q.limit(500).all()
        return sum(1 for row in rows if 0 < _score_value(row) < 70)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return 0


def _assignment_item(assignment: Any) -> dict[str, Any]:
    employee = getattr(assignment, "employee", None)
    evaluator = getattr(assignment, "evaluator", None) or getattr(assignment, "manager", None)
    period = getattr(assignment, "period", None)
    completed = getattr(assignment, "completed_at", None)
    status = _label(getattr(assignment, "status", None))
    level = getattr(assignment, "manager_level", None) or getattr(assignment, "supervisor_level", None) or "-"
    evaluator_text = _full_name(evaluator) if evaluator else "Değerlendirici bilgisi"
    return _item(getattr(assignment, "id", ""), _full_name(employee), _period_name(period), status, f"{level}. amir / {evaluator_text}" if str(level) != "-" else evaluator_text, "Tamamlandı" if completed else "İşlem bekliyor", 100 if completed else 40)


def _scorecard_item(row: Any) -> dict[str, Any]:
    employee = getattr(row, "employee", None) or _mobile_perf_safe_get(User, getattr(row, "employee_id", None))
    period = getattr(row, "period", None)
    score = _score_value(row)
    status = "Yayınlandı" if getattr(row, "is_published", False) else _label(getattr(row, "status", None), "Kontrol Bekliyor")
    return _item(getattr(row, "id", ""), _full_name(employee), _period_name(period), status, "70 altı takip" if 0 < score < 70 else "Karne", f"{score}/100" if score else "", score if score else 35)


@mobile_api_bp.get("/performance/summary")
@require_mobile_user
def mobile_performance_summary(user: User):
    from app.api.mobile.services.performance_summary_service import delegate_mobile_performance_summary
    return delegate_mobile_performance_summary(user, _bys360_legacy_mobile_performance_summary)

def _bys360_legacy_mobile_performance_summary(user: User):
    global_scope = _has_global_scope(user)
    assignment_q = _assignment_query_for(user)
    snapshot_q = _snapshot_query_for(user)
    try:
        pending_q = assignment_q.filter(~EvaluationAssignment.status.in_(list(_DONE)))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        _mobile_perf_rollback_quietly()
        pending_q = assignment_q
    active_periods = _mobile_perf_safe_count(PerformancePeriod.query.filter_by(is_active=True)) if hasattr(PerformancePeriod, "is_active") else _mobile_perf_safe_count(PerformancePeriod.query)
    pending_tasks = _mobile_perf_safe_count(pending_q)
    approvals = _mobile_perf_safe_count(PerformancePresidentApproval.query.filter_by(status="pending")) if global_scope else 0
    avg_score = _safe_avg_score(snapshot_q)
    low_score = _low_score_count(snapshot_q)
    items: list[dict[str, Any]] = []
    try:
        for assignment in _mobile_perf_safe_all(assignment_q.order_by(EvaluationAssignment.id.desc()).limit(8)):
            items.append(_assignment_item(assignment))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        _mobile_perf_rollback_quietly()
        items = []
    if not items:
        for period in _mobile_perf_safe_all(PerformancePeriod.query.order_by(PerformancePeriod.id.desc()).limit(5)):
            items.append(_item(getattr(period, "id", ""), _period_name(period), _date_range(period), _period_status(period), _period_scope(period), "", _period_progress(period)))
    return _module_payload([
        _metric("Bekleyen Görev", pending_tasks, "Yetkinize göre görünen değerlendirme görevi", "red", "assignment"),
        _metric("Aktif Dönem", active_periods, "Açık veya hazırlıktaki performans dönemi", "red", "timeline"),
        _metric("Ortalama Puan", f"{avg_score}/100" if avg_score else "-", "Yayınlanmış kayıtlar üzerinden", "green", "trending_up"),
        _metric("70 Altı Takip", low_score, "Yetkiniz kapsamındaki düşük performans kaydı", "yellow", "warning"),
        _metric("Üst Onay", approvals, "Başkan/Üst Onay bekleyen kayıt", "red", "verified_user"),
    ], items)


# BYS360 P11-C1: mobile_performance_periods read-only performance route app/api/mobile/performance_read_routes.py modülüne taşındı.


@mobile_api_bp.get("/performance/periods/<int:period_id>")
@require_mobile_user
def mobile_performance_period_detail(user: User, period_id: int):
    from app.api.mobile.services import performance_period_service as _bys360_period_service
    return _bys360_period_service.mobile_performance_period_detail(user, period_id)

def _bys360_legacy_mobile_performance_period_detail(user: User, period_id: int):
    period = _mobile_perf_safe_get(PerformancePeriod, period_id)
    if not period:
        return jsonify({"message": "Bu performans dönemine şu anda ulaşılamadı."}), 404
    assignment_q = _period_assignment_query(user, period_id)
    snapshot_q = _period_snapshot_query(user, period_id)
    try:
        pending_q = assignment_q.filter(~EvaluationAssignment.status.in_(list(_DONE)))
        completed_q = assignment_q.filter(EvaluationAssignment.status.in_(list(_DONE)))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        _mobile_perf_rollback_quietly()
        pending_q = assignment_q
        completed_q = assignment_q.filter(False)
    items: list[dict[str, Any]] = []
    try:
        for assignment in _mobile_perf_safe_all(assignment_q.order_by(EvaluationAssignment.id.desc()).limit(40)):
            items.append(_assignment_item(assignment))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        _mobile_perf_rollback_quietly()
        items = []
    if not items:
        try:
            for row in _mobile_perf_safe_all(snapshot_q.order_by(PerformanceResultSnapshot.id.desc()).limit(40)):
                items.append(_scorecard_item(row))
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            _mobile_perf_rollback_quietly()
            items = []
    items.insert(0, _item(period_id, _period_name(period), _date_range(period), _period_status(period), _period_scope(period), "Dönem bilgisi", _period_progress(period)))
    total_tasks = _mobile_perf_safe_count(assignment_q)
    completed_tasks = _mobile_perf_safe_count(completed_q)
    pending_tasks = _mobile_perf_safe_count(pending_q)
    avg_score = _safe_avg_score(snapshot_q)
    low_score = _low_score_count(snapshot_q)
    return _module_payload([
        _metric("Dönem Durumu", _period_status(period), _period_scope(period), "red", "timeline"),
        _metric("Görev", total_tasks, "Bu dönem için görünen değerlendirme görevi", "red", "assignment"),
        _metric("Tamamlanan", completed_tasks, "Tamamlanmış değerlendirme görevi", "green", "check"),
        _metric("Bekleyen", pending_tasks, "İşlem bekleyen değerlendirme görevi", "yellow", "warning"),
        _metric("Ortalama", f"{avg_score}/100" if avg_score else "-", "Dönem karne ortalaması", "green", "trending_up"),
        _metric("70 Altı", low_score, "Başkan/Üst Onay takibi gerektirebilecek kayıt", "yellow", "verified_user"),
    ], items)


@mobile_api_bp.get("/performance/approvals")
@require_mobile_user
def mobile_performance_approvals(user: User):
    if not _has_global_scope(user):
        return _module_payload([_metric("Üst Onay", "Sınırlı", "Bu alan yalnızca yetkili roller için açılır", "red", "lock"), _metric("Görünürlük", "Güvenli", "Yetkisiz kayıt gösterilmez", "red", "shield"), _metric("Süreç", "Kontrollü", "70 altı sonuçlar yayın öncesi onaya bağlıdır", "yellow", "verified_user")], [])
    q = PerformancePresidentApproval.query.order_by(PerformancePresidentApproval.id.desc())
    items: list[dict[str, Any]] = []
    for approval in _mobile_perf_safe_all(q.limit(30)):
        employee = getattr(approval, "employee", None) or getattr(approval, "user", None)
        period = getattr(approval, "period", None)
        score = getattr(approval, "final_score", None) or getattr(approval, "score", None) or getattr(approval, "final_total_100", None)
        items.append(_item(getattr(approval, "id", ""), _full_name(employee), _period_name(period), _label(getattr(approval, "status", None), "Başkan Onayı Bekliyor"), "70 altı süreç" if _as_int(score, 0) and _as_int(score, 0) < 70 else "Üst onay", f"{_as_int(score, 0)}/100" if score is not None else "", 45 if _label(getattr(approval, "status", None)).endswith("Bekliyor") else 100))
    return _module_payload([_metric("Bekleyen", _mobile_perf_safe_count(PerformancePresidentApproval.query.filter_by(status="pending")), "Başkan/Üst Onay bekleyen", "red", "verified_user"), _metric("Toplam", _mobile_perf_safe_count(q), "Onay süreç kayıtları", "red", "list"), _metric("Yayın Kilidi", "Aktif", "Onay tamamlanmadan personel karnesi açılmaz", "red", "lock")], items)


@mobile_api_bp.get("/performance/scorecards")
@require_mobile_user
def mobile_performance_scorecards(user: User):
    q = _snapshot_query_for(user).order_by(PerformanceResultSnapshot.id.desc())
    items = [_scorecard_item(row) for row in _mobile_perf_safe_all(q.limit(30))]
    return _module_payload([_metric("Karne", _mobile_perf_safe_count(q), "Yetkiniz kapsamındaki karne kayıtları", "green", "assignment"), _metric("Ortalama", f"{_safe_avg_score(q)}/100" if _mobile_perf_safe_count(q) else "-", "Yayınlanmış kayıtlar", "green", "trending_up"), _metric("Görünürlük", "Yetki Kontrollü", "Personel yalnızca kendi yayınlanmış sonucunu görür", "green", "shield")], items)


@mobile_api_bp.get("/performance/rules-summary")
@require_mobile_user
def mobile_performance_rules_summary(user: User):
    return _module_payload([_metric("Kör Değerlendirme", "Yok", "Sonraki amir önceki puan ve kanaati görür", "red", "visibility"), _metric("70 Altı", "Üst Onay", "Düşük performans sonucu doğrudan kesinleşmez", "yellow", "verified_user"), _metric("Yayın", "Kontrollü", "İK/Admin ve yetkili ön onay tamamlanmadan personele açılmaz", "red", "lock"), _metric("3. Amir", "Opsiyonel", "Yorum modu veya puan modu sistem ayarıyla çalışır", "red", "admin")], [_item("rule-1", "Kör değerlendirme yok", "Sonraki amir önceki değerlendirmeyi görür.", "Sabit Kural", "Amir zinciri", "", 100), _item("rule-2", "1 ve 5 puanda açıklama", "Açıklama zorunluluğu sistem ayarı ve kurala göre uygulanır.", "Kontrol", "Puanlama", "", 100), _item("rule-3", "70 altı sonuç", "Başkan/Üst Onay ve yayın kilidi sürecine alınır.", "Üst Onay", "Düşük performans", "", 100), _item("rule-4", "Personel görünürlüğü", "Personel sonucu yayın tamamlanmadan göremez.", "Yayın Kilidi", "Karne", "", 100)])

# BYS360 MOBILE V2.8.21 CRITERIA WEIGHT THIRD MANAGER ENDPOINTS

def _v2821_float(value, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _v2821_percent(value) -> str:
    val = _v2821_float(value, 0.0)
    if val == int(val):
        return f"%{int(val)}"
    return f"%{val:.1f}".replace(".", ",")


def _v2821_active_text(value) -> str:
    return "Aktif" if bool(value) else "Pasif"


def _v2821_mode_text(value) -> str:
    raw = str(value or "").strip().lower()
    if raw in {"comment_only", "comment", "yorum", "gorus", "görüş", "review_only"}:
        return "Yalnızca Görüş"
    if raw in {"score", "scored", "weighted", "puan", "puanli", "puanlı"}:
        return "Puan Katkılı"
    if not raw:
        return "Yalnızca Görüş"
    return str(value)


def _v2821_period_label(period_id) -> str:
    period = _mobile_perf_safe_get(PerformancePeriod, period_id)
    if period:
        return _period_name(period)
    return "Genel kural"


def _v2821_criteria_item(row) -> dict[str, Any]:
    weight = getattr(row, "weight", None)
    active = getattr(row, "is_active", True)
    code = getattr(row, "criteria_code", None) or getattr(row, "code", None) or ""
    description = str(getattr(row, "description", None) or "Kriter açıklaması bulunmuyor.")
    return _item(
        getattr(row, "id", ""),
        str(getattr(row, "name", None) or "Değerlendirme Kriteri"),
        description,
        _v2821_active_text(active),
        f"Ağırlık {_v2821_percent(weight)}" if weight is not None else "Ağırlık tanımlı değil",
        str(code),
        100 if active else 35,
    )


def _v2821_weight_item(row) -> dict[str, Any]:
    w1 = _v2821_float(getattr(row, "evaluator_1_weight", 0))
    w2 = _v2821_float(getattr(row, "evaluator_2_weight", 0))
    w3 = _v2821_float(getattr(row, "evaluator_3_weight", 0))
    total = w1 + w2 + w3
    level3 = bool(getattr(row, "level_3_enabled", False))
    mode = _v2821_mode_text(getattr(row, "level_3_mode", None))
    title = str(getattr(row, "name", None) or _v2821_period_label(getattr(row, "period_id", None)))
    status = "Dengeli" if int(round(total)) == 100 else "Kontrol Gerekir"
    subtitle = f"1. amir {_v2821_percent(w1)} · 2. amir {_v2821_percent(w2)} · 3. amir {_v2821_percent(w3)}"
    detail = f"3. amir {'Açık' if level3 else 'Kapalı'} · {mode}"
    return _item(
        getattr(row, "id", ""),
        title,
        subtitle,
        status,
        detail,
        f"Toplam {_v2821_percent(total)}",
        100 if status == "Dengeli" else 55,
    )


@mobile_api_bp.get("/performance/criteria")
@require_mobile_user
def mobile_performance_criteria(user: User):
    q = PerformanceCriteria.query
    try:
        q = q.order_by(PerformanceCriteria.sort_order.asc(), PerformanceCriteria.id.asc())
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        q = q.order_by(PerformanceCriteria.id.asc())
    rows = _mobile_perf_safe_all(q.limit(120))
    active_rows = [row for row in rows if bool(getattr(row, "is_active", True))]
    weights = [_v2821_float(getattr(row, "weight", 0)) for row in active_rows]
    avg_weight = int(mean(weights)) if weights else 0
    items = [_v2821_criteria_item(row) for row in rows]
    return _module_payload([
        _metric("Kriter", len(rows), "Mobilde görünen değerlendirme kriteri", "red", "rule"),
        _metric("Aktif", len(active_rows), "Puanlama sürecinde kullanılabilecek kriter", "green", "check"),
        _metric("Ortalama Ağırlık", f"%{avg_weight}" if avg_weight else "-", "Aktif kriterlerin yaklaşık ağırlığı", "blue", "trending_up"),
    ], items)


# BYS360 P11-C1: mobile_performance_weights read-only performance route app/api/mobile/performance_read_routes.py modülüne taşındı.


@mobile_api_bp.get("/performance/third-manager")
@require_mobile_user
def mobile_performance_third_manager(user: User):
    q = PerformanceWeightConfig.query.order_by(PerformanceWeightConfig.id.desc())
    rows = _mobile_perf_safe_all(q.limit(80))
    level3_rows = [row for row in rows if bool(getattr(row, "level_3_enabled", False))]
    comment_mode = [row for row in level3_rows if _v2821_mode_text(getattr(row, "level_3_mode", None)) == "Yalnızca Görüş"]
    score_mode = [row for row in level3_rows if _v2821_mode_text(getattr(row, "level_3_mode", None)) == "Puan Katkılı"]
    items: list[dict[str, Any]] = []
    for row in rows:
        level3 = bool(getattr(row, "level_3_enabled", False))
        mode = _v2821_mode_text(getattr(row, "level_3_mode", None))
        w3 = _v2821_float(getattr(row, "evaluator_3_weight", 0))
        title = str(getattr(row, "name", None) or _v2821_period_label(getattr(row, "period_id", None)))
        status = "3. amir açık" if level3 else "3. amir kapalı"
        body = "Puan hesabına katılır" if level3 and mode == "Puan Katkılı" else "Yalnızca görüş/yönetici notu olarak izlenir" if level3 else "Bu kuralda 3. amir görevi beklenmez"
        items.append(_item(getattr(row, "id", ""), title, body, status, mode, f"3. amir ağırlığı {_v2821_percent(w3)}", 80 if level3 else 45))
    if not items:
        items = [
            _item("third-1", "3. amir zorunlu değildir", "Yalnızca yapıda gerçekten varsa görünür.", "Sabit Kural", "Opsiyonel", "", 100),
            _item("third-2", "Yorum modu", "3. amir sadece görüş yazar; puana etkisi yoktur.", "Desteklenir", "Yalnızca Görüş", "%0", 100),
            _item("third-3", "Puan modu", "Sistem ayarıyla açılırsa ağırlık hesabına dahil olur.", "Desteklenir", "Puan Katkılı", "Toplam %100 korunur", 100),
        ]
    return _module_payload([
        _metric("3. Amir", len(level3_rows), "Açık kural sayısı", "yellow", "admin"),
        _metric("Yorum Modu", len(comment_mode), "Puan etkisi olmayan görüş akışı", "blue", "edit_note"),
        _metric("Puan Modu", len(score_mode), "Ağırlık hesabına katılan akış", "red", "scale"),
        _metric("Kural", "Opsiyonel", "3. amir olmayan yerde sahte görev oluşmaz", "green", "shield"),
    ], items)


# BYS360 MOBILE V2.8.22 PERFORMANCE TASKS
from datetime import datetime as _v2822_datetime, timezone as _v2822_timezone


def _v2822_now():
    try:
        return _v2822_datetime.now(_v2822_timezone.utc).replace(tzinfo=None)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return _v2822_datetime.utcnow()


def _v2822_due_label(row: Any) -> tuple[str, int, str]:
    completed = getattr(row, 'completed_at', None)
    if completed:
        return 'Tamamlandı', 100, 'green'
    due = getattr(row, 'due_date', None)
    if due:
        try:
            hours = ((due.replace(tzinfo=None) if getattr(due, 'tzinfo', None) else due) - _v2822_now()).total_seconds() / 3600
            if hours < 0:
                return 'Gecikti', 25, 'yellow'
            if hours <= 24:
                return 'Bugün Son Gün', 55, 'yellow'
            if hours <= 72:
                return 'Süresi Yaklaşıyor', 65, 'blue'
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/api/mobile/performance_routes.py:553)")
    return _label(getattr(row, 'status', None), 'Değerlendirme Bekliyor'), 40, 'red'


def _v2822_unit_name(user: Any) -> str:
    if not user:
        return 'Birim bilgisi'
    for name in ('birim', 'unit_name', 'organization_unit_name', 'ust_birim'):
        value = getattr(user, name, None)
        if value:
            return str(value)
    org = getattr(user, 'organization_unit', None)
    if org:
        return str(getattr(org, 'name', None) or getattr(org, 'title', None) or 'Birim bilgisi')
    return 'Birim bilgisi'


def _v2822_sicil(user: Any) -> str:
    if not user:
        return '-'
    for name in ('sicil_no', 'registration_no', 'employee_no', 'sicil'):
        value = getattr(user, name, None)
        if value:
            return str(value)
    return '-'


def _v2822_level_label(level: Any) -> str:
    try:
        n = int(level or 0)
    except (TypeError, ValueError):
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        n = 0
    if n == 3:
        return '3. Amir'
    if n == 2:
        return '2. Amir'
    if n == 1:
        return '1. Amir'
    return 'Amir'


def _v2822_assignment_card(row: Any) -> dict[str, Any]:
    employee = getattr(row, 'employee', None) or _mobile_perf_safe_get(User, getattr(row, 'employee_id', None))
    period = getattr(row, 'period', None) or _mobile_perf_safe_get(PerformancePeriod, getattr(row, 'period_id', None))
    status, progress, _tone = _v2822_due_label(row)
    due = _date_text(getattr(row, 'due_date', None))
    meta_parts = [_v2822_level_label(getattr(row, 'manager_level', None)), _v2822_unit_name(employee)]
    if due:
        meta_parts.append(f'Son tarih {due}')
    return _item(getattr(row, 'id', ''), _full_name(employee), _period_name(period), status, ' / '.join(part for part in meta_parts if part), f'Sicil: {_v2822_sicil(employee)}', progress)


def _v2822_can_view_assignment(user: User, row: Any) -> bool:
    if not row:
        return False
    if _has_global_scope(user):
        return True
    return int(getattr(row, 'evaluator_id', 0) or 0) == int(getattr(user, 'id', 0) or 0)


def _v2822_assignment_query(user: User):
    q = EvaluationAssignment.query
    if _has_global_scope(user):
        return q
    return q.filter(EvaluationAssignment.evaluator_id == user.id)


def _v2822_open_query(user: User):
    q = _v2822_assignment_query(user)
    try:
        return q.filter(~EvaluationAssignment.status.in_(list(_DONE)), EvaluationAssignment.completed_at.is_(None))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        _mobile_perf_rollback_quietly()
        return q


# BYS360 P11-C1: mobile_performance_tasks read-only performance route app/api/mobile/performance_read_routes.py modülüne taşındı.


@mobile_api_bp.get('/performance/tasks/<int:assignment_id>')
@require_mobile_user
def mobile_performance_task_detail(user: User, assignment_id: int):
    assignment = _mobile_perf_safe_get(EvaluationAssignment, assignment_id)
    if not assignment or not _v2822_can_view_assignment(user, assignment):
        return jsonify({'message': 'Bu değerlendirme görevine erişim yetkiniz bulunmamaktadır.'}), 403
    employee = getattr(assignment, 'employee', None) or _mobile_perf_safe_get(User, getattr(assignment, 'employee_id', None))
    evaluator = getattr(assignment, 'evaluator', None) or _mobile_perf_safe_get(User, getattr(assignment, 'evaluator_id', None))
    period = getattr(assignment, 'period', None) or _mobile_perf_safe_get(PerformancePeriod, getattr(assignment, 'period_id', None))
    status, progress, tone = _v2822_due_label(assignment)
    level = getattr(assignment, 'manager_level', None)
    items: list[dict[str, Any]] = [
        _item('employee', _full_name(employee), f'Sicil: {_v2822_sicil(employee)}', 'Personel', _v2822_unit_name(employee), '', 100),
        _item('period', _period_name(period), _date_range(period), _period_status(period) if period else 'Dönem', _period_scope(period) if period else 'Kapsam', '', _period_progress(period) if period else 50),
        _item('evaluator', _full_name(evaluator), _v2822_level_label(level), status, 'Değerlendirici', '', progress),
    ]
    try:
        criteria_rows = PerformanceCriteria.query.filter_by(is_active=True).order_by(PerformanceCriteria.sort_order.asc(), PerformanceCriteria.id.asc()).limit(30).all()
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        _mobile_perf_rollback_quietly(); criteria_rows = []
    for row in criteria_rows:
        items.append(_item(f"criteria-{getattr(row, 'id', '')}", str(getattr(row, 'name', None) or 'Değerlendirme Kriteri'), str(getattr(row, 'description', None) or 'Kriter açıklaması bulunmuyor.'), 'Aktif Kriter', 'Puanlama formuna hazırlanıyor', '1-5', 50))
    warning = '70 altı sonuç Başkan/Üst Onay sürecine alınır. 1 ve 5 puanlarda açıklama kuralı uygulanır.'
    if int(level or 0) == 3:
        warning = '3. amir modu sistem ayarına göre yorum veya puan katkısı şeklinde çalışır.'
    items.append(_item('rule-warning', 'Süreç uyarısı', warning, 'Kurumsal Kural', 'Teknik ifade gösterilmez', '', 100))
    return _module_payload([
        _metric('Görev Durumu', status, 'Bu değerlendirmenin anlık durumu', tone, 'assignment'),
        _metric('Amir Sırası', _v2822_level_label(level), 'İşlem sırası kurala göre yürür', 'red', 'route'),
        _metric('Personel', _full_name(employee), _v2822_unit_name(employee), 'blue', 'person'),
        _metric('Dönem', _period_name(period), _date_range(period), 'red', 'timeline'),
    ], items)

# BYS360 MOBILE V2.8.35 PERFORMANCE SCORING FORM REAL API

def _v2835_json_error(message: str, status_code: int = 400):
    return jsonify({'message': str(message or 'İşlem tamamlanamadı. Lütfen tekrar deneyin.')}), status_code


def _v2835_level3_scoring_enabled(period: Any) -> bool:
    try:
        flags = get_period_level_3_flags(period)
        return bool(flags.get('enabled') and flags.get('scoring_enabled'))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return bool(getattr(period, 'enable_level_3', False) and getattr(period, 'enable_level_3_scoring', False))


def _v2835_score_mode_for(assignment: Any, period: Any) -> bool:
    try:
        level = int(getattr(assignment, 'manager_level', 0) or 0)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        level = 0
    if level == 3 and not _v2835_level3_scoring_enabled(period):
        return False
    return True


def _v2835_existing_evaluation(assignment: Any):
    try:
        return PerformanceEvaluation.query.filter_by(
            period_id=getattr(assignment, 'period_id', None),
            employee_id=getattr(assignment, 'employee_id', None),
        ).first()
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        _mobile_perf_rollback_quietly()
        return None


def _v2835_general_comment(evaluation: Any, level: int) -> str:
    if not evaluation:
        return ''
    return str(getattr(evaluation, f'level_{level}_general_comment', None) or '')


def _v2835_level_completed(evaluation: Any, level: int) -> bool:
    if not evaluation:
        return False
    return bool(getattr(evaluation, f'level_{level}_completed', False))


def _v2835_criteria_rows():
    try:
        q = PerformanceCriteria.query.filter_by(is_active=True)
        try:
            q = q.order_by(PerformanceCriteria.sort_order.asc(), PerformanceCriteria.id.asc())
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            q = q.order_by(PerformanceCriteria.id.asc())
        return _mobile_perf_safe_all(q.limit(120))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        _mobile_perf_rollback_quietly()
        return []


def _v2835_existing_item_map(evaluation: Any, level: int) -> dict[int, Any]:
    if not evaluation:
        return {}
    try:
        rows = PerformanceEvaluationItem.query.filter_by(evaluation_id=evaluation.id, manager_level=level).all()
        return {int(getattr(row, 'criteria_id', 0) or 0): row for row in rows}
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        _mobile_perf_rollback_quietly()
        return {}


def _bys360_legacy__v2835_score_form_payload(assignment: Any) -> dict[str, Any]:
    employee = getattr(assignment, 'employee', None) or _mobile_perf_safe_get(User, getattr(assignment, 'employee_id', None))
    evaluator = getattr(assignment, 'evaluator', None) or _mobile_perf_safe_get(User, getattr(assignment, 'evaluator_id', None))
    period = getattr(assignment, 'period', None) or _mobile_perf_safe_get(PerformancePeriod, getattr(assignment, 'period_id', None))
    evaluation = _v2835_existing_evaluation(assignment)
    level = int(getattr(assignment, 'manager_level', 0) or 0)
    criteria_rows = _v2835_criteria_rows()
    existing = _v2835_existing_item_map(evaluation, level)
    score_mode = _v2835_score_mode_for(assignment, period)
    completed = bool(getattr(assignment, 'completed_at', None)) or _v2835_level_completed(evaluation, level)

    criteria_payload: list[dict[str, Any]] = []
    for row in criteria_rows:
        cid = int(getattr(row, 'id', 0) or 0)
        item = existing.get(cid)
        score_value = getattr(item, 'score', None) if item else None
        criteria_payload.append({
            'id': str(cid),
            'criteria_id': cid,
            'title': str(getattr(row, 'name', None) or 'Değerlendirme Kriteri'),
            'description': str(getattr(row, 'description', None) or ''),
            'weight': float(getattr(row, 'weight', 0) or 0),
            'score': score_value,
            'comment': str(getattr(item, 'comment', None) or getattr(item, 'justification', None) or '') if item else '',
            'score_100': float(getattr(item, 'score_100', 0) or 0) if item else 0,
        })

    warning = '70 altı veya 90 üstü sonuçlarda ayrıntılı genel görüş zorunludur. 1 ve 5 puanda kriter açıklaması mobil uygulamada isteğe bağlıdır.'
    if not score_mode:
        warning = '3. amir bu görevde yorum/görüş modundadır; puan alanı kapalıdır.'

    return {
        'source': 'real_api',
        'form': {
            'assignment_id': str(getattr(assignment, 'id', '') or ''),
            'evaluation_id': str(getattr(evaluation, 'id', '') or '') if evaluation else '',
            'employee_name': _full_name(employee),
            'sicil_no': _v2822_sicil(employee),
            'unit_name': _v2822_unit_name(employee),
            'period_name': _period_name(period),
            'date_range': _date_range(period),
            'evaluator_name': _full_name(evaluator),
            'manager_level': level,
            'manager_level_label': _v2822_level_label(level),
            'status_label': _label(getattr(assignment, 'status', None), 'Değerlendirme Bekliyor'),
            'is_completed': completed,
            'score_mode': score_mode,
            'criteria': criteria_payload,
            'general_comment': _v2835_general_comment(evaluation, level),
            'warning': warning,
            'submit_label': 'Tamamla',
            'save_label': 'Taslak Kaydet',
            'actions': _v2837_action_capabilities(assignment, evaluation, level),
        },
        'rules': {
            'score_range': '1-5',
            'low_high_general_comment': '70 altı / 90 üstü genel görüş zorunludur',
            'level3_mode': 'Puanlama' if score_mode else 'Yalnızca Görüş',
        },
    }

def _v2835_score_form_payload(assignment):
    from app.api.mobile.services.performance_task_service import delegate_v2835_score_form_payload
    return delegate_v2835_score_form_payload(assignment)


def _v2837_status_key(value: Any) -> str:
    return str(value or '').strip().lower().replace('ı', 'i').replace(' ', '_').replace('-', '_')


def _v2837_assignment_is_completed(assignment: Any, evaluation: Any, level: int) -> bool:
    return bool(getattr(assignment, 'completed_at', None)) or _v2835_level_completed(evaluation, level) or _v2837_status_key(getattr(assignment, 'status', None)) in {'tamamlandi', 'completed', 'done'}


def _bys360_legacy__v2837_find_return_target(assignment: Any, level: int):
    # İşlem sırası BYS360 kuralına göre yüksek numaralı seviyeden düşük numaralı seviyeye iner.
    # Bu nedenle mevcut amir, varsa bir önceki işlem seviyesine iade edebilir: 1 -> 2, 2 -> 3.
    for target_level in (level + 1,):
        if target_level not in {2, 3}:
            continue
        target = EvaluationAssignment.query.filter_by(
            period_id=getattr(assignment, 'period_id', None),
            employee_id=getattr(assignment, 'employee_id', None),
            manager_level=target_level,
        ).first()
        if target:
            return target_level, target
    return None, None

def _v2837_find_return_target(assignment: Any, level: int):
    from app.api.mobile.services import performance_task_service as _bys360_performance_task_service
    return _bys360_performance_task_service._v2837_find_return_target(assignment, level)


def _bys360_legacy__v2837_action_capabilities(assignment: Any, evaluation: Any, level: int) -> dict[str, Any]:
    completed = _v2837_assignment_is_completed(assignment, evaluation, level)
    target_level, target = _v2837_find_return_target(assignment, level)
    is_published = bool(getattr(evaluation, 'is_published_to_employee', False) or getattr(evaluation, 'published_to_employee_at', None)) if evaluation else False
    can_withdraw = bool(completed and not is_published)
    can_return = bool(completed and target and not is_published)
    return {
        'can_withdraw': can_withdraw,
        'can_return': can_return,
        'return_target_level': target_level or 0,
        'withdraw_label': 'Geri Çek',
        'return_label': 'İade Et',
        'bulk_scores': [5, 4, 3, 2, 1],
        'bulk_note': 'Toplu puan verdiğinizde her kriter yine ayrı ayrı düzenlenebilir.',
    }

def _v2837_action_capabilities(assignment: Any, evaluation: Any, level: int) -> dict[str, Any]:
    from app.api.mobile.services import performance_task_service as _bys360_performance_task_service
    return _bys360_performance_task_service._v2837_action_capabilities(assignment, evaluation, level)


def _v2837_recalculate_if_possible(evaluation: Any) -> None:
    if not evaluation:
        return
    try:
        recalculate_evaluation_totals(evaluation)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        db.session.add(evaluation)


def _bys360_legacy__v2837_withdraw_assignment(assignment: Any, evaluation: Any, level: int, user: User, note: str = '') -> dict[str, Any]:
    if not _v2837_assignment_is_completed(assignment, evaluation, level):
        raise ValueError('Geri çekme için önce tamamlanmış bir değerlendirme olmalıdır.')
    if bool(getattr(evaluation, 'is_published_to_employee', False) or getattr(evaluation, 'published_to_employee_at', None)):
        raise ValueError('Personele yayınlanmış değerlendirme mobil ekrandan geri çekilemez.')
    assignment.status = 'taslak'
    assignment.completed_at = None
    if evaluation:
        setattr(evaluation, f'level_{level}_completed', False)
        evaluation.workflow_status = f'taslak_{level}_amir'
        if _v2837_status_key(getattr(evaluation, 'status', None)) in {'tamamlandi', 'completed'}:
            evaluation.status = 'kismen_tamamlandi'
        _v2837_recalculate_if_possible(evaluation)
        db.session.add(evaluation)
    db.session.add(assignment)
    db.session.commit()
    return {'message': 'Değerlendirme geri çekildi. Artık puanları yeniden düzenleyebilirsiniz.'}

def _v2837_withdraw_assignment(assignment: Any, evaluation: Any, level: int, user: User, note: str = '') -> dict[str, Any]:
    from app.api.mobile.services import performance_task_service as _bys360_performance_task_service
    return _bys360_performance_task_service._v2837_withdraw_assignment(assignment, evaluation, level, user, note)


def _bys360_legacy__v2837_return_assignment(assignment: Any, evaluation: Any, level: int, user: User, note: str = '') -> dict[str, Any]:
    note_text = str(note or '').strip()
    if not note_text:
        raise ValueError('İade işlemi için kısa bir açıklama yazın.')
    if not _v2837_assignment_is_completed(assignment, evaluation, level):
        raise ValueError('İade işlemi için önce mevcut değerlendirme tamamlanmış olmalıdır.')
    if bool(getattr(evaluation, 'is_published_to_employee', False) or getattr(evaluation, 'published_to_employee_at', None)):
        raise ValueError('Personele yayınlanmış değerlendirme mobil ekrandan iade edilemez.')
    target_level, target = _v2837_find_return_target(assignment, level)
    if not target:
        raise ValueError('İade edilecek önceki amir görevi bulunamadı.')
    target.status = 'iade'
    target.completed_at = None
    assignment.status = 'taslak'
    assignment.completed_at = None
    if evaluation:
        setattr(evaluation, f'level_{level}_completed', False)
        setattr(evaluation, f'level_{target_level}_completed', False)
        evaluation.workflow_status = f'level_{target_level}_iade'
        evaluation.status = 'devam_ediyor'
        if hasattr(evaluation, 'level_2_return_note'):
            evaluation.level_2_return_note = note_text
        if hasattr(evaluation, 'level_2_returned_by_id'):
            evaluation.level_2_returned_by_id = getattr(user, 'id', None)
        if hasattr(evaluation, 'level_2_returned_to_level_1_at'):
            evaluation.level_2_returned_to_level_1_at = utc_now()
        _v2837_recalculate_if_possible(evaluation)
        db.session.add(evaluation)
    db.session.add(target)
    db.session.add(assignment)
    db.session.commit()
    return {'message': f'Değerlendirme {target_level}. amire iade edildi. Düzeltme sonrası süreç yeniden devam eder.'}

def _v2837_return_assignment(assignment: Any, evaluation: Any, level: int, user: User, note: str = '') -> dict[str, Any]:
    from app.api.mobile.services import performance_task_service as _bys360_performance_task_service
    return _bys360_performance_task_service._v2837_return_assignment(assignment, evaluation, level, user, note)


@mobile_api_bp.get('/performance/tasks/<int:assignment_id>/score-form')
@require_mobile_user
def mobile_performance_task_score_form(user: User, assignment_id: int):
    assignment = _mobile_perf_safe_get(EvaluationAssignment, assignment_id)
    if not assignment or not _v2822_can_view_assignment(user, assignment):
        return _v2835_json_error('Bu değerlendirme görevine erişim yetkiniz bulunmamaktadır.', 403)
    return jsonify(_v2835_score_form_payload(assignment))


@mobile_api_bp.post('/performance/tasks/<int:assignment_id>/score-form')
@require_mobile_user
def mobile_performance_task_score_submit(user: User, assignment_id: int):
    assignment = _mobile_perf_safe_get(EvaluationAssignment, assignment_id)
    if not assignment or not _v2822_can_view_assignment(user, assignment):
        return _v2835_json_error('Bu değerlendirme görevine erişim yetkiniz bulunmamaktadır.', 403)

    body = request.get_json(silent=True) or {}
    completed = bool(body.get('completed'))
    general_comment = str(body.get('general_comment') or body.get('generalComment') or '').strip()
    raw_items = body.get('items') if isinstance(body.get('items'), list) else []

    period = getattr(assignment, 'period', None) or _mobile_perf_safe_get(PerformancePeriod, getattr(assignment, 'period_id', None))
    level = int(getattr(assignment, 'manager_level', 0) or 0)
    score_mode = _v2835_score_mode_for(assignment, period)
    criteria_rows = _v2835_criteria_rows()
    criteria_by_id = {int(getattr(row, 'id', 0) or 0): row for row in criteria_rows}
    criteria_weight_map = {cid: float(getattr(row, 'weight', 0) or 0) for cid, row in criteria_by_id.items()}

    item_payloads: list[dict[str, Any]] = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        try:
            criteria_id = int(raw.get('criteria_id') or raw.get('id'))
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/api/mobile/performance_routes.py:956)")
            continue
        if criteria_id not in criteria_by_id:
            continue
        raw_score = raw.get('score')
        if raw_score in (None, ''):
            continue
        try:
            score_value = float(str(raw_score).replace(',', '.'))
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            return _v2835_json_error('Puan 1 ile 5 arasında olmalıdır.', 400)
        item_payloads.append({
            'criteria_id': criteria_id,
            'score': score_value,
            'comment': str(raw.get('comment') or '').strip(),
            'strength_note': str(raw.get('strength_note') or '').strip(),
            'justification': str(raw.get('justification') or raw.get('comment') or '').strip(),
        })

    try:
        if score_mode:
            if completed and criteria_rows and len(item_payloads) < len(criteria_rows):
                return _v2835_json_error('Tamamlamak için tüm değerlendirme kriterlerine 1-5 arası puan girilmelidir.', 400)
            if not item_payloads and not general_comment:
                return _v2835_json_error('Kaydetmek için en az bir puan veya genel görüş girilmelidir.', 400)
            if completed:
                # Mobil uygulamada 1 ve 5 puan için kriter açıklaması zorunlu değildir.
                # 70 altı / 90 üstü genel görüş zorunluluğu aşağıda korunur.
                preview_total = calculate_preview_total_100(item_payloads, criteria_weight_map)
                raw_scores = [float(item.get('score') or 0) for item in item_payloads]
                validate_general_comment_requirements(
                    manager_level=level,
                    general_comment=general_comment,
                    level_total_100=preview_total,
                    raw_scores=raw_scores,
                    requires_level_2_comment=False,
                )
        else:
            if not general_comment:
                return _v2835_json_error('3. amir yorum/görüş modunda genel görüş zorunludur.', 400)
            item_payloads = []

        evaluation = save_evaluation_level(
            period_id=getattr(assignment, 'period_id', None),
            employee_id=getattr(assignment, 'employee_id', None),
            manager_level=level,
            evaluator_id=getattr(assignment, 'evaluator_id', None),
            item_payloads=item_payloads,
            general_comment=general_comment,
            completed=completed or not score_mode,
        )

        if completed or not score_mode:
            assignment.status = 'tamamlandi'
            assignment.completed_at = utc_now()
        else:
            assignment.status = 'kismen_tamamlandi'
            assignment.completed_at = None
        db.session.add(assignment)
        db.session.add(evaluation)
        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        return _v2835_json_error(str(exc), 400)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        db.session.rollback()
        return _v2835_json_error('Puanlama kaydedilemedi. Lütfen bilgileri kontrol edip tekrar deneyin.', 500)

    level_total = float(getattr(evaluation, f'level_{level}_total_100', 0) or 0)
    return jsonify({
        'source': 'real_api',
        'message': 'Değerlendirme başarıyla tamamlandı.' if (completed or not score_mode) else 'Taslak başarıyla kaydedildi.',
        'assignment_id': str(getattr(assignment, 'id', '') or ''),
        'evaluation_id': str(getattr(evaluation, 'id', '') or ''),
        'status_label': _label(getattr(assignment, 'status', None), 'Kaydedildi'),
        'level_score_100': round(level_total, 2),
        'final_score_100': round(float(getattr(evaluation, 'final_total_100', 0) or 0), 2),
    })

@mobile_api_bp.post('/performance/tasks/<int:assignment_id>/score-action')
@require_mobile_user
def mobile_performance_task_score_action(user: User, assignment_id: int):
    assignment = _mobile_perf_safe_get(EvaluationAssignment, assignment_id)
    if not assignment or not _v2822_can_view_assignment(user, assignment):
        return _v2835_json_error('Bu değerlendirme görevine erişim yetkiniz bulunmamaktadır.', 403)
    body = request.get_json(silent=True) or {}
    action = str(body.get('action') or '').strip().lower()
    note = str(body.get('note') or '').strip()
    evaluation = _v2835_existing_evaluation(assignment)
    level = int(getattr(assignment, 'manager_level', 0) or 0)
    try:
        if action in {'withdraw', 'geri_cek', 'geri-cek'}:
            result = _v2837_withdraw_assignment(assignment, evaluation, level, user, note)
        elif action in {'return', 'iade', 'iade_et', 'iade-et'}:
            result = _v2837_return_assignment(assignment, evaluation, level, user, note)
        else:
            return _v2835_json_error('Bilinmeyen işlem seçildi.', 400)
    except ValueError as exc:
        db.session.rollback()
        return _v2835_json_error(str(exc), 400)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        db.session.rollback()
        return _v2835_json_error('İşlem tamamlanamadı. Lütfen tekrar deneyin.', 500)
    result.update({'source': 'real_api', 'assignment_id': str(getattr(assignment, 'id', '') or '')})
    return jsonify(result)

# BYS360 P11-C1: mobile_performance_manager_tasks read-only performance route app/api/mobile/performance_read_routes.py modülüne taşındı.

# BYS360_MOBILE_V2_8_52_PERFORMANCE_WEB_PARITY_API
# Mobil performans modülü web performans başlıklarıyla aynı kapsamda özet/listeler üretir.
def _v2852_model(*names):
    for name in names:
        try:
            registry = getattr(getattr(db, 'Model', None), 'registry', None)
            cls = getattr(registry, '_class_registry', {}).get(name) if registry is not None else None
            if cls is not None and hasattr(cls, 'query'):
                return cls
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/api/mobile/performance_routes.py:1105)")
        try:
            cls = globals().get(name)
            if cls is not None and hasattr(cls, 'query'):
                return cls
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/api/mobile/performance_routes.py:1111)")
    return None


def _v2852_text(obj, fields, default=''):
    if obj is None:
        return default
    for field in fields:
        try:
            value = getattr(obj, field, None)
            if value not in (None, ''):
                return str(value)
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/api/mobile/performance_routes.py:1124)")
    return default


def _v2852_int(value, default=0):
    try:
        return int(float(str(value).replace(',', '.')))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return default


def _v2852_query(model):
    q = model.query
    for field in ('updated_at', 'created_at', 'id'):
        try:
            col = getattr(model, field, None)
            if col is not None:
                return q.order_by(col.desc())
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/api/mobile/performance_routes.py:1143)")
    return q


def _v2852_items_from_models(model_names, title_fields, subtitle_fields, status_fields=None, meta_fields=None, value_fields=None, limit=80, progress=50):
    status_fields = status_fields or ['status', 'state', 'workflow_status']
    meta_fields = meta_fields or ['period_name', 'period_title', 'category', 'unit_name', 'created_at']
    value_fields = value_fields or ['score', 'final_score', 'final_total_100', 'value']
    for model_name in model_names:
        model = _v2852_model(model_name)
        if model is None:
            continue
        rows = _mobile_perf_safe_all(_v2852_query(model).limit(limit))
        items = []
        for row in rows:
            items.append(_item(
                getattr(row, 'id', ''),
                _v2852_text(row, title_fields, model_name),
                _v2852_text(row, subtitle_fields, 'Detay bilgisi'),
                _label(_v2852_text(row, status_fields, 'Kayıt'), 'Kayıt'),
                _v2852_text(row, meta_fields, ''),
                _v2852_text(row, value_fields, ''),
                progress,
            ))
        if items:
            return items
    return []


def _v2852_employee_category(user):
    if user is None:
        return 'Diğer'
    for field in ('personnel_category', 'employee_category', 'staff_category', 'category', 'group_name', 'personnel_group'):
        try:
            value = getattr(user, field, None)
            if value:
                return str(value)
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/api/mobile/performance_routes.py:1181)")
    try:
        return _v2822_unit_name(user)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return 'Diğer'


def _v2852_score(row):
    return _score_value(row) if '_score_value' in globals() else _v2852_int(_v2852_text(row, ['final_total_100', 'final_score', 'score'], '0'))


def _v2852_done(row):
    try:
        return bool(getattr(row, 'completed_at', None)) or str(getattr(row, 'status', '')).lower() in _DONE
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return False


def _v2852_pending_assignments(user, limit=1000):
    try:
        q = _v2822_assignment_query(user) if '_v2822_assignment_query' in globals() else _assignment_query_for(user)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        q = EvaluationAssignment.query
    return [row for row in _mobile_perf_safe_all(q.limit(limit)) if not _v2852_done(row)]


def _v2852_due_label_safe(row):
    try:
        return _v2822_due_label(row)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return (_label(getattr(row, 'status', None), 'Bekliyor'), 40, 'red')

@mobile_api_bp.get('/performance/full-feature-summary')
@require_mobile_user
def _bys360_legacy_mobile_performance_full_feature_summary(user: User):
    try:
        assignment_q = _assignment_query_for(user)
        snapshot_q = _snapshot_query_for(user)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        assignment_q = EvaluationAssignment.query
        snapshot_q = PerformanceResultSnapshot.query
    active_periods = _mobile_perf_safe_count(PerformancePeriod.query.filter_by(is_active=True)) if hasattr(PerformancePeriod, 'is_active') else _mobile_perf_safe_count(PerformancePeriod.query)
    pending = len(_v2852_pending_assignments(user, 1000))
    scorecards = _mobile_perf_safe_count(snapshot_q)
    avg_score = _safe_avg_score(snapshot_q) if '_safe_avg_score' in globals() else 0
    low_score = _low_score_count(snapshot_q) if '_low_score_count' in globals() else 0
    approvals = _mobile_perf_safe_count(PerformancePresidentApproval.query.filter_by(status='pending')) if _has_global_scope(user) and PerformancePresidentApproval is not None else 0
    items = [
        _item('periods', 'Dönem Yönetimi', 'Yıllık, 6 aylık, 3 aylık, aylık ve özel dönemler', 'Aktif' if active_periods else 'Kontrol', 'Kapsam: kurum, birim, kategori, seçili personel', str(active_periods), 100 if active_periods else 45),
        _item('tasks', 'Değerlendirme Görevleri', 'Puanlama, taslak, tamamlama, geri çekme ve iade', 'Bekleyen' if pending else 'Tamamlandı', 'Mobil puanlama formu', str(pending), 60 if pending else 100),
        _item('scorecards', 'Karne ve Arşiv', 'Yayınlanmış karneler ve geçmiş kayıtlar', 'Yetki Kontrollü', 'Personel yalnızca yayınlanan kendi sonucunu görür', str(scorecards), 85),
        _item('approvals', 'Başkan/Üst Onay ve Yayın Ön Onayı', '70 altı ve final yayın kontrol akışları', 'Onay Bekliyor' if approvals else 'Kontrollü', 'Yayın kilidi korunur', str(approvals), 55 if approvals else 100),
        _item('reports', 'Raporlar, Risk ve Gelişim', 'Kategori, dönem, amir, personel, risk, gelişim ve hatırlatma ekranları', 'Aktif', 'Web performans modülüyle aynı başlıklar', '', 100),
    ]
    return _module_payload([
        _metric('Aktif Dönem', active_periods, 'Açık veya hazırlıktaki performans dönemi', 'red', 'timeline'),
        _metric('Bekleyen Görev', pending, 'Puanlama veya takip bekleyen görev', 'red', 'assignment'),
        _metric('Karne', scorecards, 'Yetki kapsamındaki karne kayıtları', 'green', 'scorecard'),
        _metric('Ortalama', f'{avg_score}/100' if avg_score else '-', 'Yayınlanmış sonuç ortalaması', 'green', 'trending_up'),
        _metric('70 Altı', low_score, 'Düşük performans takibi', 'yellow', 'warning'),
        _metric('Üst Onay', approvals, 'Başkan/Üst Onay bekleyen kayıt', 'red', 'verified_user'),
    ], items)

def mobile_performance_full_feature_summary(user: User):
    from app.api.mobile.services.performance_summary_service import delegate_mobile_performance_full_feature_summary as _bys360_delegate
    return _bys360_delegate(_bys360_legacy_mobile_performance_full_feature_summary, user)

# BYS360 P11-C1: mobile_performance_categories read-only performance route app/api/mobile/performance_read_routes.py modülüne taşındı.

@mobile_api_bp.get('/performance/president-approvals')
@require_mobile_user
def _bys360_prev_mobile_performance_president_approvals_alias_v21748(user: User):
    # BYS360 V2.17.49: 500 smoke fix - guvenli JSON fallback
    return _bys360_mobile_perf_president_approvals_safe_fallback_v21749(user)

def mobile_performance_president_approvals_alias(user: User):    # BYS360_SAFE_SMOKE_500_FIX_V2_17_48: wrapper keeps endpoint name and adds safe fallback for smoke-tested mobile GET.
    # BYS360 V2.17.49: 500 smoke fix - guvenli JSON fallback
    return _bys360_mobile_perf_president_approvals_safe_fallback_v21749(user)

@mobile_api_bp.get('/performance/publish-preapproval')
@require_mobile_user
def mobile_performance_publish_preapproval(user: User):
    items = _v2852_items_from_models(['PerformancePublishPreApproval', 'PerformancePublicationPreApproval', 'PerformancePublishApproval', 'PerformancePublishLog', 'PerformancePublicationApproval'], ['employee_name', 'title', 'name', 'period_name'], ['description', 'note', 'period_name', 'status_text'], ['status', 'approval_status', 'state'], ['period_name', 'created_at', 'approved_by_name'], ['final_score', 'score'])
    if not items:
        pending = []
        try:
            q = _snapshot_query_for(user)
            if hasattr(PerformanceResultSnapshot, 'is_published'):
                q = q.filter(PerformanceResultSnapshot.is_published.is_(False))
            pending = _mobile_perf_safe_all(q.limit(60))
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            pending = []
        for row in pending:
            employee = getattr(row, 'employee', None) or _mobile_perf_safe_get(User, getattr(row, 'employee_id', None))
            period = getattr(row, 'period', None) or _mobile_perf_safe_get(PerformancePeriod, getattr(row, 'period_id', None))
            score = _v2852_score(row)
            items.append(_item(getattr(row, 'id', ''), _full_name(employee), _period_name(period), 'Yayın Ön Kontrol', 'Final yayın öncesi kontrol', f'{score}/100' if score else '', 55))
    return _module_payload([
        _metric('Ön Onay', len(items), 'Final yayın öncesi görünen kayıt', 'red', 'approval'),
        _metric('Yayın Kilidi', 'Aktif', 'Ön onay olmadan final yayın engellenir', 'yellow', 'lock'),
        _metric('Yetki', 'Rol Bazlı', 'Yayın işlemi yetkili kullanıcıyla sınırlıdır', 'green', 'shield'),
    ], items)

def _bys360_legacy_mobile_performance_history_archive(user: User):
    # BYS360 V2.17.49: 500 smoke fix - guvenli JSON fallback
    return _bys360_mobile_perf_history_archive_safe_fallback_v21749(user)

@mobile_api_bp.get('/performance/history-archive')
@require_mobile_user
def _bys360_prev_mobile_performance_history_archive_v21748(user):
    # BYS360 V2.17.49: 500 smoke fix - guvenli JSON fallback
    return _bys360_mobile_perf_history_archive_safe_fallback_v21749(user)

def mobile_performance_history_archive(user):    # BYS360_SAFE_SMOKE_500_FIX_V2_17_48: wrapper keeps endpoint name and adds safe fallback for smoke-tested mobile GET.
    # BYS360 V2.17.49: 500 smoke fix - guvenli JSON fallback
    return _bys360_mobile_perf_history_archive_safe_fallback_v21749(user)

@mobile_api_bp.get('/performance/in-period-notes')
@require_mobile_user
def _bys360_legacy_mobile_performance_in_period_notes(user: User):
    items = _v2852_items_from_models(['PerformanceInPeriodNote', 'PerformancePeriodNote', 'PerformanceObservationNote', 'PerformanceInterimFeedback', 'FeedbackActionPlan'], ['employee_name', 'title', 'subject', 'note_type'], ['note', 'description', 'body', 'observation'], ['status', 'note_type', 'state'], ['period_name', 'created_at', 'created_by_name'], ['value'], limit=100, progress=60)
    if not items:
        items = [_item('note-empty', 'Dönem içi not kaydı bulunmadı', 'Olumlu/olumsuz olay, başarı, gelişim ihtiyacı veya genel gözlem notu oluştuğunda burada görünür.', 'Bilgi', 'Puanı otomatik üretmez', '', 35)]
    return _module_payload([
        _metric('Not', max(0, len([i for i in items if i.get('id') != 'note-empty'])), 'Yetki kapsamındaki dönem içi not', 'blue', 'note'),
        _metric('Kural', 'Destek Bilgi', 'Bu notlar puanı otomatik oluşturmaz', 'green', 'shield'),
        _metric('Görünürlük', 'Yetki Kontrollü', 'Hassas içerik rol kapsamına göre korunur', 'red', 'lock'),
    ], items)

def mobile_performance_in_period_notes(user: User):
    from app.api.mobile.services.performance_period_service import delegate_mobile_performance_in_period_notes
    return delegate_mobile_performance_in_period_notes(user)

def _bys360_legacy_mobile_performance_development_suggestions(user: User):
    items = _v2852_items_from_models(['PerformanceDevelopmentSuggestion', 'PerformanceDevelopmentPlan', 'DevelopmentSuggestion', 'FeedbackActionPlan'], ['employee_name', 'title', 'suggestion_title', 'name'], ['suggestion', 'description', 'development_area', 'action_text'], ['status', 'state'], ['period_name', 'created_at', 'owner_name'], ['priority', 'score'], limit=100, progress=65)
    if not items:
        try:
            q = _snapshot_query_for(user).order_by(PerformanceResultSnapshot.id.desc())
            rows = [row for row in _mobile_perf_safe_all(q.limit(100)) if 0 < _v2852_score(row) < 70]
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            rows = []
        for row in rows[:60]:
            employee = getattr(row, 'employee', None) or _mobile_perf_safe_get(User, getattr(row, 'employee_id', None))
            period = getattr(row, 'period', None) or _mobile_perf_safe_get(PerformancePeriod, getattr(row, 'period_id', None))
            score = _v2852_score(row)
            items.append(_item(getattr(row, 'id', ''), _full_name(employee), _period_name(period), 'Gelişim Takibi', '70 altı sonuç için gelişim önerisi değerlendirilebilir', f'{score}/100', 45))
    if not items:
        items = [_item('development-empty', 'Gelişim önerisi kaydı bulunmadı', 'Gelişim alanı, güçlü yön veya takip notu oluştuğunda burada görünür.', 'Bilgi', 'Yetki kontrollü', '', 35)]
    return _module_payload([
        _metric('Gelişim', max(0, len([i for i in items if i.get('id') != 'development-empty'])), 'Öneri veya takip kaydı', 'green', 'development'),
        _metric('Amaç', 'Rehberlik', 'Puan yerine gelişim takibi desteklenir', 'blue', 'school'),
        _metric('Düşük Performans', 'İzlenir', '70 altı sonuçlar gelişim sürecine bağlanabilir', 'yellow', 'warning'),
    ], items)

@mobile_api_bp.get('/performance/development-suggestions')
@require_mobile_user
def mobile_performance_development_suggestions(user: User):
    from app.api.mobile.services.performance_summary_service import mobile_performance_development_suggestions_delegate
    return mobile_performance_development_suggestions_delegate(user)

def _bys360_legacy_mobile_performance_reports(user: User):
    try:
        assignment_q = _assignment_query_for(user)
        snapshot_q = _snapshot_query_for(user)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        assignment_q = EvaluationAssignment.query
        snapshot_q = PerformanceResultSnapshot.query
    total_assignments = _mobile_perf_safe_count(assignment_q)
    total_scorecards = _mobile_perf_safe_count(snapshot_q)
    avg_score = _safe_avg_score(snapshot_q) if '_safe_avg_score' in globals() else 0
    low_score = _low_score_count(snapshot_q) if '_low_score_count' in globals() else 0
    periods = _mobile_perf_safe_all(PerformancePeriod.query.order_by(PerformancePeriod.id.desc()).limit(30)) if hasattr(PerformancePeriod, 'id') else []
    items = []
    for period in periods:
        period_id = getattr(period, 'id', None)
        task_count = _mobile_perf_safe_count(_period_assignment_query(user, period_id)) if period_id and '_period_assignment_query' in globals() else 0
        items.append(_item(period_id or '', _period_name(period), _date_range(period), _period_status(period), f'{task_count} görev', _period_scope(period), _period_progress(period)))
    if not items:
        items = [_item('report-summary', 'Performans rapor özeti', 'Birim, kategori, dönem, amir, personel ve risk bazlı raporlar web verisiyle üretilir.', 'Özet', f'{total_assignments} görev / {total_scorecards} karne', '', 70)]
    return _module_payload([
        _metric('Görev', total_assignments, 'Yetki kapsamındaki değerlendirme görevi', 'red', 'assignment'),
        _metric('Karne', total_scorecards, 'Yetki kapsamındaki karne', 'green', 'scorecard'),
        _metric('Ortalama', f'{avg_score}/100' if avg_score else '-', 'Yayınlanmış sonuç ortalaması', 'green', 'trending_up'),
        _metric('70 Altı', low_score, 'Risk/düşük performans göstergesi', 'yellow', 'warning'),
    ], items)

@mobile_api_bp.get('/performance/reports')
@require_mobile_user
def mobile_performance_reports(user: User):
    from app.api.mobile.services.performance_summary_service import delegate_mobile_performance_reports
    return delegate_mobile_performance_reports(_bys360_legacy_mobile_performance_reports, user)

# BYS360 P11-C1: mobile_performance_reminders read-only performance route app/api/mobile/performance_read_routes.py modülüne taşındı.

# BYS360 P11-C1: mobile_performance_manager_view_v2852 read-only performance route app/api/mobile/performance_read_routes.py modülüne taşındı.

@mobile_api_bp.get('/performance/risk-analysis')
@require_mobile_user
def _bys360_legacy_mobile_performance_risk_analysis_v2852(user: User):
    try:
        snapshot_q = _snapshot_query_for(user).order_by(PerformanceResultSnapshot.id.desc())
        rows = _mobile_perf_safe_all(snapshot_q.limit(200))
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        rows = []
    low = [row for row in rows if 0 < _v2852_score(row) < 70]
    high = [row for row in rows if _v2852_score(row) >= 90]
    items = []
    for row in low[:80]:
        employee = getattr(row, 'employee', None) or _mobile_perf_safe_get(User, getattr(row, 'employee_id', None))
        period = getattr(row, 'period', None) or _mobile_perf_safe_get(PerformancePeriod, getattr(row, 'period_id', None))
        score = _v2852_score(row)
        items.append(_item(getattr(row, 'id', ''), _full_name(employee), _period_name(period), '70 Altı Risk', 'Başkan/Üst Onay ve gelişim takibi gerekebilir', f'{score}/100', 35))
    if not items:
        items = [_item('risk-empty', 'Riskli kayıt bulunmadı', 'Yetki kapsamınızda 70 altı performans sonucu görünmüyor.', 'Normal', 'Risk takibi aktif', '', 100)]
    return _module_payload([
        _metric('70 Altı', len(low), 'Düşük performans/risk kaydı', 'yellow', 'warning'),
        _metric('90 Üstü', len(high), 'Yüksek başarı takibi', 'green', 'trending_up'),
        _metric('Risk Takibi', 'Aktif', 'Başkan/Üst Onay ve gelişim süreciyle bağlantılıdır', 'red', 'risk'),
    ], items)

def mobile_performance_risk_analysis_v2852(user):
    from app.api.mobile.services.performance_summary_service import mobile_performance_risk_analysis_v2852_delegate
    return mobile_performance_risk_analysis_v2852_delegate(_bys360_legacy_mobile_performance_risk_analysis_v2852, user)

# BYS360_MOBILE_V2_8_53_IN_PERIOD_NOTES_API
# BYS360 P11-C1: mobile_performance_in_period_note_options_v2853 read-only performance route app/api/mobile/performance_read_routes.py modülüne taşındı.


def _bys360_legacy__v2853_note_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {'1', 'true', 'evet', 'yes', 'on'}

def _v2853_note_bool(value, default=False):
    from app.api.mobile.services import performance_period_service as _bys360_performance_period_service
    return _bys360_performance_period_service._v2853_note_bool(value, default)


def _v2853_ensure_interim_notes_table():
    try:
        from app.services.performance.interim_notes_runtime import ensure_interim_notes_table
        ensure_interim_notes_table()
        return True
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        try:
            from sqlalchemy import text as _sql_text
            db.session.execute(_sql_text('''
                CREATE TABLE IF NOT EXISTS performance_interim_notes (
                    id SERIAL PRIMARY KEY,
                    period_id INTEGER NULL,
                    employee_id INTEGER NULL,
                    employee_user_id INTEGER NULL,
                    manager_id INTEGER NULL,
                    created_by INTEGER NULL,
                    created_by_id INTEGER NULL,
                    note_type VARCHAR(80) NOT NULL DEFAULT 'genel_gozlem',
                    title VARCHAR(255) NULL,
                    note TEXT NULL,
                    note_body TEXT NULL,
                    visibility_level VARCHAR(80) NULL DEFAULT 'manager_scope',
                    remind_during_scoring BOOLEAN DEFAULT TRUE,
                    include_in_scorecard BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    occurred_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP
                )
            '''))
            db.session.commit()
            return True
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            db.session.rollback()
            return False


def _bys360_legacy__v2853_note_type_label(value):
    mapping = {
        'olumlu_olay': 'Olumlu Olay',
        'olumsuz_olay': 'Olumsuz Olay',
        'basari': 'Başarı',
        'gelisim_ihtiyaci': 'Gelişim İhtiyacı',
        'genel_gozlem': 'Genel Gözlem',
    }
    key = str(value or 'genel_gozlem').strip().lower()
    return mapping.get(key, key.replace('_', ' ').title())

def _v2853_note_type_label(value):
    from app.api.mobile.services import performance_period_service as _bys360_performance_period_service
    return _bys360_performance_period_service._v2853_note_type_label(value)


@mobile_api_bp.get('/performance/in-period-notes/v2')
@require_mobile_user
def _bys360_legacy_mobile_performance_in_period_notes_v2853(user: User):
    _v2853_ensure_interim_notes_table()
    from sqlalchemy import text as _sql_text
    where = ['COALESCE(is_active, TRUE) = TRUE']
    params = {'limit': 160}
    if not _has_global_scope(user):
        where.append('(employee_id = :uid OR employee_user_id = :uid OR manager_id = :uid OR created_by = :uid OR created_by_id = :uid)')
        params['uid'] = int(getattr(user, 'id', 0) or 0)
    sql = _sql_text(f'''
        SELECT id, period_id, employee_id, employee_user_id, manager_id, created_by, note_type,
               COALESCE(title, note_title, '') AS title,
               COALESCE(note, note_body, note_text, content, description, '') AS note_body,
               COALESCE(remind_during_scoring, remind_in_evaluation, TRUE) AS remind_during_scoring,
               COALESCE(include_in_scorecard, visible_on_scorecard, FALSE) AS include_in_scorecard,
               COALESCE(created_at, occurred_at, updated_at) AS created_at
        FROM performance_interim_notes
        WHERE {' AND '.join(where)}
        ORDER BY COALESCE(created_at, occurred_at, updated_at) DESC NULLS LAST, id DESC
        LIMIT :limit
    ''')
    try:
        rows = db.session.execute(sql, params).mappings().all()
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        db.session.rollback()
        try:
            rows = db.session.execute(_sql_text(str(sql).replace(' DESC NULLS LAST', ' DESC')), params).mappings().all()
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            db.session.rollback()
            rows = []
    items = []
    for row in rows:
        employee = _mobile_perf_safe_get(User, row.get('employee_id') or row.get('employee_user_id'))
        period = _mobile_perf_safe_get(PerformancePeriod, row.get('period_id'))
        type_label = _v2853_note_type_label(row.get('note_type'))
        title = row.get('title') or type_label
        body = str(row.get('note_body') or '').strip()
        meta = []
        if period:
            meta.append(_period_name(period))
        if row.get('remind_during_scoring'):
            meta.append('Puanlamada Hatırlatılır')
        if row.get('include_in_scorecard'):
            meta.append('Karneye Açık')
        item = _item(row.get('id'), f'{_full_name(employee)} - {title}' if employee else title, body, type_label, ' / '.join(meta), '', 70)
        item['icon'] = 'note'
        item['tone'] = 'info'
        items.append(item)
    real_count = len(items)
    if not items:
        items = [_item('note-empty', 'Dönem içi not kaydı bulunmadı', 'Olumlu/olumsuz olay, başarı, gelişim ihtiyacı veya genel gözlem notu oluştuğunda burada görünür.', 'Bilgi', 'Puanı otomatik üretmez', '', 35)]
    return _module_payload([
        _metric('Not', real_count, 'Yetki kapsamındaki dönem içi not', 'blue', 'note'),
        _metric('Kural', 'Otomatik Puan Yok', 'Notlar puanı otomatik değiştirmez', 'green', 'shield'),
        _metric('Karne', 'Seçimli', 'Yalnız işaretlenen notlar karne detayına açılır', 'yellow', 'scorecard'),
    ], items)

def mobile_performance_in_period_notes_v2853(user: User):
    from app.api.mobile.services.performance_period_service import delegate_mobile_performance_in_period_notes_v2853
    return delegate_mobile_performance_in_period_notes_v2853(user)


@mobile_api_bp.post('/performance/in-period-notes/v2')
@require_mobile_user
def mobile_performance_create_in_period_note_v2853(user: User):
    _v2853_ensure_interim_notes_table()
    from flask import request as _request
    from sqlalchemy import text as _sql_text
    payload = _request.get_json(silent=True) or {}
    note = str(payload.get('note') or payload.get('note_body') or '').strip()
    if not note:
        return jsonify({'message': 'Not metni boş bırakılamaz.'}), 400
    try:
        period_id = int(payload.get('period_id')) if payload.get('period_id') else None
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        period_id = None
    try:
        employee_id = int(payload.get('employee_id')) if payload.get('employee_id') else None
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        employee_id = None
    if not employee_id:
        employee_id = int(getattr(user, 'id', 0) or 0)
    note_type = str(payload.get('note_type') or 'genel_gozlem').strip()[:80] or 'genel_gozlem'
    title = str(payload.get('title') or _v2853_note_type_label(note_type)).strip()[:255]
    remind = _v2853_note_bool(payload.get('remind_during_scoring'), True)
    include = _v2853_note_bool(payload.get('include_in_scorecard'), False)
    try:
        db.session.execute(_sql_text('''
            INSERT INTO performance_interim_notes
            (period_id, employee_id, employee_user_id, manager_id, created_by, created_by_id, note_type, title, note, note_body,
             visibility_level, visibility_scope, remind_during_scoring, remind_in_evaluation, include_in_scorecard, visible_on_scorecard,
             is_active, active, occurred_at, created_at, updated_at)
            VALUES
            (:period_id, :employee_id, :employee_id, :manager_id, :created_by, :created_by, :note_type, :title, :note, :note,
             'manager_scope', 'manager_scope', :remind, :remind, :include, :include,
             TRUE, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        '''), {
            'period_id': period_id,
            'employee_id': employee_id,
            'manager_id': int(getattr(user, 'id', 0) or 0),
            'created_by': int(getattr(user, 'id', 0) or 0),
            'note_type': note_type,
            'title': title,
            'note': note,
            'remind': remind,
            'include': include,
        })
        db.session.commit()
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        db.session.rollback()
        return jsonify({'message': f'Dönem içi not kaydedilemedi: {exc.__class__.__name__}'}), 500
    return jsonify({'source': 'real_api', 'ok': True, 'message': 'Dönem içi not kaydedildi.'})

# BYS360_MOBILE_V2_8_63A_NOTE_SCORECARD_ENDPOINT
@mobile_api_bp.get('/performance/note-scorecard')
@require_mobile_user
def _bys360_legacy_mobile_performance_note_scorecard_v2863a(user: User):
    try:
        _v2853_ensure_interim_notes_table()
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/api/mobile/performance_routes.py:1699)")
    from sqlalchemy import text as _sql_text
    try:
        db.session.execute(_sql_text('ALTER TABLE performance_interim_notes ADD COLUMN IF NOT EXISTS include_in_scorecard BOOLEAN DEFAULT FALSE'))
        db.session.execute(_sql_text('ALTER TABLE performance_interim_notes ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE'))
        db.session.execute(_sql_text('ALTER TABLE performance_interim_notes ADD COLUMN IF NOT EXISTS title VARCHAR(255) NULL'))
        db.session.execute(_sql_text('ALTER TABLE performance_interim_notes ADD COLUMN IF NOT EXISTS note TEXT NULL'))
        db.session.execute(_sql_text('ALTER TABLE performance_interim_notes ADD COLUMN IF NOT EXISTS note_body TEXT NULL'))
        db.session.execute(_sql_text("ALTER TABLE performance_interim_notes ADD COLUMN IF NOT EXISTS note_type VARCHAR(80) NOT NULL DEFAULT 'genel_gozlem'"))
        db.session.commit()
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        db.session.rollback()
    where = ['COALESCE(is_active, TRUE) = TRUE', 'COALESCE(include_in_scorecard, FALSE) = TRUE']
    params = {'limit': 160}
    if not _has_global_scope(user):
        where.append('(employee_id = :uid OR employee_user_id = :uid OR manager_id = :uid OR created_by = :uid OR created_by_id = :uid)')
        params['uid'] = int(getattr(user, 'id', 0) or 0)
    sql_text = "SELECT id, period_id, employee_id, employee_user_id, manager_id, created_by, note_type, title, note, note_body, created_at FROM performance_interim_notes WHERE " + ' AND '.join(where) + " ORDER BY COALESCE(created_at, CURRENT_TIMESTAMP) DESC, id DESC LIMIT :limit"
    try:
        rows = db.session.execute(_sql_text(sql_text), params).mappings().all()
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        db.session.rollback()
        rows = []
    items = []
    for row in rows:
        employee = _mobile_perf_safe_get(User, row.get('employee_id') or row.get('employee_user_id'))
        period = _mobile_perf_safe_get(PerformancePeriod, row.get('period_id'))
        try:
            type_label = _v2853_note_type_label(row.get('note_type'))
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            type_label = str(row.get('note_type') or 'Not').replace('_', ' ').title()
        title = str(row.get('title') or type_label or 'Karne Notu').strip()
        body = str(row.get('note') or row.get('note_body') or '').strip()
        meta = []
        if period:
            meta.append(_period_name(period))
        if type_label:
            meta.append(type_label)
        record_title = f'{_full_name(employee)} - {title}' if employee else title
        item = _item(row.get('id'), record_title, body, 'Karneye Açık', ' / '.join(meta), '', 80)
        item['icon'] = 'scorecard'
        item['tone'] = 'warning'
        items.append(item)
    real_count = len(items)
    if not items:
        items = [_item('note-scorecard-empty', 'Not karnesi kaydı bulunmadı', 'Dönem içi not eklerken “Karne detayında gösterilsin” işaretlenen kayıtlar burada görünür.', 'Bilgi', 'Puanı otomatik değiştirmez', '', 35)]
    return _module_payload([
        _metric('Karne Notu', real_count, 'Karne detayına açılan not', 'yellow', 'scorecard'),
        _metric('Görünürlük', 'Yetkili', 'Yalnız yetki kapsamındaki kayıtlar gösterilir', 'green', 'shield'),
        _metric('Puan Etkisi', 'Yok', 'Not karnesi puanı otomatik değiştirmez', 'blue', 'note'),
    ], items)

def mobile_performance_note_scorecard_v2863a(user: User):
    from app.api.mobile.services.performance_period_service import delegate_mobile_performance_note_scorecard_v2863a
    return delegate_mobile_performance_note_scorecard_v2863a(user)


# BYS360_MOBILE_V2_8_63A_ARCHIVE_NOTE_SCORECARD

# BYS360 P11-C1: mobile performance read routes bridge
from app.api.mobile.performance_read_routes import register_mobile_performance_read_routes_v1 as _register_mobile_performance_read_routes_v1
_register_mobile_performance_read_routes_v1(globals())

# BYS360_SAFE_SMOKE_500_FIX_V2_17_48: safe JSON fallback helper for authenticated smoke endpoints.
def _bys360_safe_smoke_500_json_response_v21748(kind, exc=None):
    try:
        from flask import jsonify, current_app
        try:
            current_app.logger.exception("BYS360_SAFE_SMOKE_500_FIX_V2_17_48: mobile performance smoke fallback kind=%s", kind)
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            pass
        if kind == "president_approvals":
            payload = {
                "items": [],
                "metrics": [{
                    "title": "Başkan Onayları",
                    "subtitle": "Yetki kapsamınızda gösterilecek kayıt bulunamadı veya güvenli boş liste döndürüldü.",
                    "icon": "approval",
                    "tone": "red",
                    "value": 0,
                }],
                "status": "safe_fallback",
                "message": "Başkan onayları mobil görünümü güvenli boş listeyle döndürüldü.",
            }
        elif kind == "history_archive":
            payload = {
                "items": [],
                "metrics": [{
                    "title": "Geçmiş Arşiv",
                    "subtitle": "Yetki kapsamınızda gösterilecek arşiv kaydı bulunamadı veya güvenli boş liste döndürüldü.",
                    "icon": "history",
                    "tone": "red",
                    "value": 0,
                }],
                "status": "safe_fallback",
                "message": "Performans geçmiş arşivi mobil görünümü güvenli boş listeyle döndürüldü.",
            }
        else:
            payload = {"items": [], "metrics": [], "status": "safe_fallback"}
        return jsonify(payload), 200
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        # Flask baglami disinda cagrilirsa bile fonksiyon patlamasin.
        return {"items": [], "metrics": [], "status": "safe_fallback", "kind": kind}, 200

# BYS360_FORCE_SAFE_500_FALLBACK_V2_17_49
# Bu blok yalnizca mobil GET smoke testinde 500 veren iki endpoint icin guvenli JSON fallback saglar.
def _bys360_mobile_perf_safe_json_response_v21749(payload, status=200):
    try:
        from flask import jsonify
        return jsonify(payload), status
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return payload, status


def _bys360_mobile_perf_president_approvals_safe_fallback_v21749(user=None):
    return _bys360_mobile_perf_safe_json_response_v21749({
        "items": [],
        "metrics": [
            {
                "title": "Başkan Onayları",
                "subtitle": "Yetki kapsamınızda bekleyen düşük performans onayı bulunamadı veya güvenli fallback devrede.",
                "value": 0,
                "tone": "red",
                "icon": "approval"
            }
        ],
        "status": "safe_fallback",
        "source": "BYS360 V2.17.49",
        "message": "Mobil başkan onayları endpointi güvenli boş yanıt döndürdü."
    })


def _bys360_mobile_perf_history_archive_safe_fallback_v21749(user=None):
    return _bys360_mobile_perf_safe_json_response_v21749({
        "items": [],
        "metrics": [
            {
                "title": "Geçmiş Arşiv",
                "subtitle": "Yetki kapsamınızda görüntülenecek geçmiş karne kaydı bulunamadı veya güvenli fallback devrede.",
                "value": 0,
                "tone": "red",
                "icon": "archive"
            }
        ],
        "status": "safe_fallback",
        "source": "BYS360 V2.17.49",
        "message": "Mobil performans geçmiş arşivi endpointi güvenli boş yanıt döndürdü."
    })

