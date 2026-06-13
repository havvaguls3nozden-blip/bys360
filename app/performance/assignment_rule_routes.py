from __future__ import annotations



from flask import redirect, request, url_for
from flask_login import login_required

from app.models import PerformancePeriod
from app.route_registry import main_bp
from app.route_support import admin_required, safe_render
from app.services.performance.assignment_rule_audit import build_assignment_generation_preflight


@main_bp.route('/performance/assignments/rule-audit', methods=['GET'])
@main_bp.route('/performance/evaluation-tasks/rule-audit', methods=['GET'])
@login_required
@admin_required
def performance_assignment_rule_audit():
    periods = PerformancePeriod.query.order_by(PerformancePeriod.start_date.desc()).all()
    period_id = request.args.get('period_id', type=int)
    if not period_id:
        active = PerformancePeriod.query.filter_by(is_active=True).order_by(PerformancePeriod.id.desc()).first()
        period_id = getattr(active, 'id', None)
    if not period_id:
        return redirect(url_for('main.performance_generate_assignments'))
    audit = build_assignment_generation_preflight(period_id=period_id, limit=800)
    return safe_render('assignment_rule_audit.html', '<h3>Performans Zincir Ön Kontrol</h3>', periods=periods, selected_period_id=period_id, audit=audit)
