from __future__ import annotations

from typing import Any


def phase3c_mobile_performance_third_manager_service(user: Any, deps: dict[str, Any]):
    PerformanceWeightConfig = deps['PerformanceWeightConfig']
    _item = deps['_item']
    _metric = deps['_metric']
    _mobile_perf_safe_all = deps['_mobile_perf_safe_all']
    _module_payload = deps['_module_payload']
    _v2821_float = deps['_v2821_float']
    _v2821_mode_text = deps['_v2821_mode_text']
    _v2821_percent = deps['_v2821_percent']
    _v2821_period_label = deps['_v2821_period_label']

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


def phase3c_mobile_performance_task_detail_service(user: Any, assignment_id: int, deps: dict[str, Any]):
    EvaluationAssignment = deps['EvaluationAssignment']
    PerformanceCriteria = deps['PerformanceCriteria']
    PerformancePeriod = deps['PerformancePeriod']
    User = deps['User']
    _date_range = deps['_date_range']
    _full_name = deps['_full_name']
    _item = deps['_item']
    _metric = deps['_metric']
    _mobile_perf_rollback_quietly = deps['_mobile_perf_rollback_quietly']
    _mobile_perf_safe_get = deps['_mobile_perf_safe_get']
    _module_payload = deps['_module_payload']
    _period_name = deps['_period_name']
    _period_progress = deps['_period_progress']
    _period_scope = deps['_period_scope']
    _period_status = deps['_period_status']
    _v2822_can_view_assignment = deps['_v2822_can_view_assignment']
    _v2822_due_label = deps['_v2822_due_label']
    _v2822_level_label = deps['_v2822_level_label']
    _v2822_sicil = deps['_v2822_sicil']
    _v2822_unit_name = deps['_v2822_unit_name']
    jsonify = deps['jsonify']
    logger = deps['logger']

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
        _mobile_perf_rollback_quietly()
        criteria_rows = []
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
