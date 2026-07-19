from __future__ import annotations

from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.route_registry import main_bp
from app.route_support import manager_required
from app.services.performance.meeting_final_closure import build_final_closure_context, run_final_closure_check


@main_bp.route('/performance/meeting-development/final-closure', endpoint='performance_meeting_final_closure')
@main_bp.route('/performans/toplanti-gelistirme/final-kapanis', endpoint='performance_meeting_final_closure_tr')
@login_required
@manager_required
def performance_meeting_final_closure():
    return render_template('performance/meeting_final_closure.html', **build_final_closure_context(viewer=current_user))


@main_bp.route('/performance/meeting-development/final-closure/check', methods=['POST'], endpoint='performance_meeting_final_closure_check')
@main_bp.route('/performans/toplanti-gelistirme/final-kapanis/kontrol', methods=['POST'], endpoint='performance_meeting_final_closure_check_tr')
@login_required
@manager_required
def performance_meeting_final_closure_check():
    result = run_final_closure_check()
    flash(result['message'], 'success' if result['ok'] else 'warning')
    for item in result.get('missing', []):
        flash(item, 'warning')
    return redirect(url_for('main.performance_meeting_final_closure'))
