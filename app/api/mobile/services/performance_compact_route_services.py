from __future__ import annotations

from typing import Any


def phase3c_mobile_performance_approvals_service(user: Any, deps: dict[str, Any]):
    PerformancePresidentApproval = deps['PerformancePresidentApproval']
    _as_int = deps['_as_int']
    _full_name = deps['_full_name']
    _has_global_scope = deps['_has_global_scope']
    _item = deps['_item']
    _label = deps['_label']
    _metric = deps['_metric']
    _mobile_perf_safe_all = deps['_mobile_perf_safe_all']
    _mobile_perf_safe_count = deps['_mobile_perf_safe_count']
    _module_payload = deps['_module_payload']
    _period_name = deps['_period_name']

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


def phase3c_mobile_performance_criteria_service(user: Any, deps: dict[str, Any]):
    PerformanceCriteria = deps['PerformanceCriteria']
    _metric = deps['_metric']
    _mobile_perf_safe_all = deps['_mobile_perf_safe_all']
    _module_payload = deps['_module_payload']
    _v2821_criteria_item = deps['_v2821_criteria_item']
    _v2821_float = deps['_v2821_float']
    logger = deps['logger']
    mean = deps['mean']

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


def phase3c_mobile_performance_in_period_notes_legacy_service(user: Any, deps: dict[str, Any]):
    _has_global_scope = deps['_has_global_scope']
    _item = deps['_item']
    _metric = deps['_metric']
    _module_payload = deps['_module_payload']
    _v2852_items_from_models = deps['_v2852_items_from_models']

    # BYS360_SECURITY_FIX_DEFECT_O3: _v2852_items_from_models() runs a
    # zero-filter, organization-wide query across every model in its list.
    # There is no pre-existing scoped alternative for this exact legacy
    # multi-model lookup, so non-global callers are routed straight to the
    # existing empty-state placeholder instead of the unscoped shortcut.
    # The already-correctly-scoped GET /performance/in-period-notes/v2 route
    # (phase3c_mobile_performance_in_period_notes_v2853_service) remains the
    # fully functional, unaffected successor to this legacy route.
    items = _v2852_items_from_models(['PerformanceInPeriodNote', 'PerformancePeriodNote', 'PerformanceObservationNote', 'PerformanceInterimFeedback', 'FeedbackActionPlan'], ['employee_name', 'title', 'subject', 'note_type'], ['note', 'description', 'body', 'observation'], ['status', 'note_type', 'state'], ['period_name', 'created_at', 'created_by_name'], ['value'], limit=100, progress=60) if _has_global_scope(user) else []
    if not items:
        items = [_item('note-empty', 'Dönem içi not kaydı bulunmadı', 'Olumlu/olumsuz olay, başarı, gelişim ihtiyacı veya genel gözlem notu oluştuğunda burada görünür.', 'Bilgi', 'Puanı otomatik üretmez', '', 35)]
    return _module_payload([
        _metric('Not', max(0, len([i for i in items if i.get('id') != 'note-empty'])), 'Yetki kapsamındaki dönem içi not', 'blue', 'note'),
        _metric('Kural', 'Destek Bilgi', 'Bu notlar puanı otomatik oluşturmaz', 'green', 'shield'),
        _metric('Görünürlük', 'Yetki Kontrollü', 'Hassas içerik rol kapsamına göre korunur', 'red', 'lock'),
    ], items)
