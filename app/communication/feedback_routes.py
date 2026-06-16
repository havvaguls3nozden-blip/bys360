from __future__ import annotations

from flask import Response, flash, redirect, request, session, url_for
from flask_login import current_user, login_required

from app.extensions import db

# BYS360_FEEDBACK_10_AI_IMPORTS
from app.services.ai.feedback_decision_support import (
    build_manager_decision_support,
    build_pulse_analytics_decision_support,
    build_pulse_form_guidance,
    build_results_decision_support,
)
from app.models import FeedbackActionPlan, User
from app.route_registry import main_bp
from app.route_support import manager_required, menu_key_required, safe_db_rollback, safe_render
from app.services.feedback_service import (
    build_campaign_pulse_context,
    build_campaign_results,
    build_dashboard_data,
    build_manager_summary,
    build_pulse_analytics,
    campaign_includes_pulse,
    change_campaign_status,
    create_action_plan,
    create_campaign_from_form,
    get_campaign_or_404,
    get_pulse_history,
    get_today_pulse_entry,
    get_campaign_type_label,
    has_user_submitted_campaign,
    is_manager_family,
    list_action_plans_for_user,
    list_manageable_campaigns,
    list_visible_campaigns_for_user,
    save_pulse_entry,
    submit_campaign_answers,
)
import logging
logger = logging.getLogger(__name__)


_FEEDBACK_EXPORT_RATE_LIMIT_SECONDS = 12


def _can_export_feedback_now() -> bool:
    import time

    key = f"feedback_results_export_at_{getattr(current_user, 'id', 'anonymous')}"
    now_ts = int(time.time())
    last_ts = int(session.get(key, 0) or 0)
    if last_ts and (now_ts - last_ts) < _FEEDBACK_EXPORT_RATE_LIMIT_SECONDS:
        return False
    session[key] = now_ts
    session.modified = True
    return True


@main_bp.route('/feedback')
@login_required
@menu_key_required('feedback_dashboard')
def feedback_dashboard():
    context = build_dashboard_data(current_user)
    return safe_render('feedback/dashboard.html', '<h3>Kurumsal Geri Bildirim ekranı yüklenemedi</h3>', **context)


@main_bp.route('/feedback/pulse', methods=['GET', 'POST'])
@login_required
@menu_key_required('feedback_pulse')
def feedback_pulse():
    # BYS360_FEEDBACK_AI_SCOPE_HOTFIX
    ai_results_support = None
    ai_analytics_support = None
    ai_manager_support = None
    ai_pulse_guidance = None

    if request.method == 'POST':
        try:
            mood_value = max(1, min(5, int(request.form.get('mood_value') or '3')))
            save_pulse_entry(
                user=current_user,
                mood_value=mood_value,
                short_note=request.form.get('short_note') or '',
                is_anonymous=bool(request.form.get('is_anonymous')),
            )
            flash('Günlük nabız kaydınız kaydedildi.', 'success')
            return redirect(url_for('main.feedback_pulse'))
        except Exception as exc:
            logger.exception("BYS360 V6C guarded exception | file=app/communication/feedback_routes.py | line=89")
            safe_db_rollback()
            flash(f'Nabız kaydı oluşturulamadı: {exc}', 'danger')
    today_entry = get_today_pulse_entry(current_user)
    history_preview = get_pulse_history(current_user, 7)
    ai_pulse_guidance = build_pulse_form_guidance(today_entry, history_preview)
    return safe_render(
        'feedback/pulse_form.html',
        '<h3>Nabız formu yüklenemedi</h3>',
        today_entry=today_entry,
        history_preview=history_preview,
        can_view_analytics=is_manager_family(current_user),
        ai_pulse_guidance=ai_pulse_guidance,
    )


@main_bp.route('/feedback/pulse/history')
@login_required
@menu_key_required('feedback_pulse')
def feedback_pulse_history():
    days = request.args.get('days', default=30, type=int) or 30
    days = max(7, min(days, 90))
    entries = get_pulse_history(current_user, days)
    return safe_render(
        'feedback/pulse_history.html',
        '<h3>Nabız geçmişi yüklenemedi</h3>',
        days=days,
        entries=entries,
    )


def _render_feedback_pulse_analytics():
    days = request.args.get('days', default=30, type=int) or 30
    days = max(7, min(days, 90))
    analytics = build_pulse_analytics(current_user, days)
    ai_analytics_support = build_pulse_analytics_decision_support(analytics, days)
    return safe_render(
        'feedback/pulse_analytics.html',
        '<h3>Nabız analitiği yüklenemedi</h3>',
        days=days,
        analytics=analytics,
        ai_analytics_support=ai_analytics_support,
    )


@main_bp.route('/feedback/pulse/analytics')
@login_required
@menu_key_required('feedback_manager')
@manager_required
def feedback_pulse_analytics():
    return _render_feedback_pulse_analytics()


@main_bp.route('/feedback/admin/pulse-analytics')
@login_required
@menu_key_required('feedback_manager')
@manager_required
def feedback_admin_pulse_analytics():
    # BYS360_FEEDBACK_AI_SCOPE_HOTFIX
    ai_results_support = None
    ai_analytics_support = None
    ai_manager_support = None
    ai_pulse_guidance = None

    return _render_feedback_pulse_analytics()


@main_bp.route('/feedback/campaigns')
@login_required
@menu_key_required('feedback_campaigns')
def feedback_campaigns():
    # BYS360_FEEDBACK_AI_SCOPE_HOTFIX
    ai_results_support = None
    ai_analytics_support = None
    ai_manager_support = None
    ai_pulse_guidance = None

    campaigns = list_visible_campaigns_for_user(current_user)
    return safe_render(
        'feedback/campaign_list.html',
        '<h3>Kampanya listesi yüklenemedi</h3>',
        campaigns=campaigns,
        has_user_submitted_campaign=has_user_submitted_campaign,
        get_campaign_type_label=get_campaign_type_label,
        campaign_includes_pulse=campaign_includes_pulse,
        ai_results_support=ai_results_support,
    )


@main_bp.route('/feedback/campaigns/<int:campaign_id>', methods=['GET', 'POST'])
@login_required
@menu_key_required('feedback_campaigns')
def feedback_campaign_detail(campaign_id: int):
    campaign = get_campaign_or_404(campaign_id)
    if request.method == 'POST':
        try:
            submit_campaign_answers(user=current_user, campaign=campaign, form=request.form)
            flash('Geri bildirim kaydınız alındı.', 'success')
            return redirect(url_for('main.feedback_campaigns'))
        except Exception as exc:
            logger.exception("BYS360 V6C guarded exception | file=app/communication/feedback_routes.py | line=188")
            safe_db_rollback()
            flash(str(exc), 'danger')
    return safe_render(
        'feedback/campaign_take.html',
        '<h3>Kampanya ekranı yüklenemedi</h3>',
        campaign=campaign,
        already_answered=has_user_submitted_campaign(current_user, campaign),
        includes_pulse=campaign_includes_pulse(campaign),
        campaign_type_label=get_campaign_type_label(campaign),
        today_pulse=get_today_pulse_entry(current_user),
    )


@main_bp.route('/feedback/results')
@login_required
@menu_key_required('feedback_results')
@manager_required
def feedback_results():
    # BYS360_FEEDBACK_AI_SCOPE_HOTFIX
    ai_results_support = None
    ai_analytics_support = None
    ai_manager_support = None
    ai_pulse_guidance = None

    campaign_id = request.args.get('campaign_id', type=int)
    campaigns = list_manageable_campaigns()
    selected_campaign = next((row for row in campaigns if row.id == campaign_id), campaigns[0] if campaigns else None)
    results = build_campaign_results(selected_campaign) if selected_campaign else []
    pulse_context = build_campaign_pulse_context(selected_campaign) if selected_campaign else None
    ai_results_support = build_results_decision_support(selected_campaign, results, pulse_context)
    return safe_render(
        'feedback/results.html',
        '<h3>Sonuç ekranı yüklenemedi</h3>',
        campaigns=campaigns,
        selected_campaign=selected_campaign,
        results=results,
        pulse_context=pulse_context,
        get_campaign_type_label=get_campaign_type_label,
        campaign_includes_pulse=campaign_includes_pulse,
    )


@main_bp.route('/feedback/actions', methods=['GET', 'POST'])
@login_required
@menu_key_required('feedback_actions')
@manager_required
def feedback_actions():
    if request.method == 'POST':
        action_id = request.form.get('action_id', type=int)
        action = FeedbackActionPlan.query.get_or_404(action_id)
        try:
            from app.services.feedback_service import update_action_status
            update_action_status(action_plan=action, status=request.form.get('status') or 'open', resolution_note=request.form.get('resolution_note') or '')
            flash('Aksiyon durumu güncellendi.', 'success')
            return redirect(url_for('main.feedback_actions'))
        except Exception as exc:
            logger.exception("BYS360 V6C guarded exception | file=app/communication/feedback_routes.py | line=244")
            safe_db_rollback()
            flash(f'Aksiyon güncellenemedi: {exc}', 'danger')
    actions = list_action_plans_for_user(current_user)
    campaigns = list_manageable_campaigns()
    managers = User.query.order_by(User.ad.asc(), User.soyad.asc()).all()
    return safe_render('feedback/action_list.html', '<h3>Aksiyon listesi yüklenemedi</h3>', actions=actions, campaigns=campaigns, managers=managers)


@main_bp.route('/feedback/actions/new', methods=['POST'])
@login_required
@menu_key_required('feedback_actions')
@manager_required
def feedback_action_new():
    try:
        create_action_plan(actor=current_user, form=request.form)
        flash('İyileştirme aksiyonu oluşturuldu.', 'success')
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/feedback_routes.py | line=261")
        safe_db_rollback()
        flash(f'Aksiyon oluşturulamadı: {exc}', 'danger')
    return redirect(url_for('main.feedback_actions'))


@main_bp.route('/feedback/manager')
@login_required
@menu_key_required('feedback_manager')
@manager_required
def feedback_manager():
    # BYS360_FEEDBACK_AI_SCOPE_HOTFIX
    ai_results_support = None
    ai_analytics_support = None
    ai_manager_support = None
    ai_pulse_guidance = None

    summary = build_manager_summary(current_user)
    ai_manager_support = build_manager_decision_support(summary)
    return safe_render('feedback/manager_view.html', '<h3>Yönetici görünümü yüklenemedi</h3>', summary=summary, ai_manager_support=ai_manager_support)


@main_bp.route('/feedback/admin/campaigns')
@login_required
@menu_key_required('feedback_admin')
@manager_required
def feedback_campaign_manage():
    campaigns = list_manageable_campaigns()
    return safe_render(
        'feedback/campaign_manage.html',
        '<h3>Kampanya yönetimi yüklenemedi</h3>',
        campaigns=campaigns,
        get_campaign_type_label=get_campaign_type_label,
        campaign_includes_pulse=campaign_includes_pulse,
    )


@main_bp.route('/feedback/admin/campaigns/new', methods=['GET', 'POST'])
@login_required
@menu_key_required('feedback_admin')
@manager_required
def feedback_campaign_new():
    if request.method == 'POST':
        try:
            campaign = create_campaign_from_form(form=request.form, actor=current_user)
            flash('Kampanya taslağı oluşturuldu.', 'success')
            return redirect(url_for('main.feedback_campaign_manage', campaign_id=campaign.id))
        except Exception as exc:
            logger.exception("BYS360 V6C guarded exception | file=app/communication/feedback_routes.py | line=308")
            safe_db_rollback()
            flash(f'Kampanya oluşturulamadı: {exc}', 'danger')
    return safe_render('feedback/campaign_form.html', '<h3>Kampanya formu yüklenemedi</h3>')


@main_bp.route('/feedback/admin/campaigns/<int:campaign_id>/status', methods=['POST'])
@login_required
@menu_key_required('feedback_admin')
@manager_required
def feedback_campaign_status(campaign_id: int):
    campaign = get_campaign_or_404(campaign_id)
    try:
        change_campaign_status(campaign=campaign, target_status=request.form.get('target_status') or 'draft')
        flash('Kampanya durumu güncellendi.', 'success')
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/feedback_routes.py | line=323")
        safe_db_rollback()
        flash(f'Kampanya durumu değiştirilemedi: {exc}', 'danger')
    return redirect(url_for('main.feedback_campaign_manage'))


@main_bp.route('/feedback/admin/campaigns/<int:campaign_id>/publish', methods=['POST'])
@login_required
@menu_key_required('feedback_admin')
@manager_required
def feedback_campaign_publish(campaign_id: int):
    campaign = get_campaign_or_404(campaign_id)
    try:
        change_campaign_status(campaign=campaign, target_status='published')
        flash('Kampanya yayınlandı.', 'success')
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/feedback_routes.py | line=338")
        safe_db_rollback()
        flash(f'Kampanya yayınlanamadı: {exc}', 'danger')
    return redirect(url_for('main.feedback_campaign_manage'))


@main_bp.route('/feedback/admin/campaigns/<int:campaign_id>/close', methods=['POST'])
@login_required
@menu_key_required('feedback_admin')
@manager_required
def feedback_campaign_close(campaign_id: int):
    campaign = get_campaign_or_404(campaign_id)
    try:
        change_campaign_status(campaign=campaign, target_status='closed')
        flash('Kampanya kapatıldı.', 'success')
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/feedback_routes.py | line=353")
        safe_db_rollback()
        flash(f'Kampanya kapatılamadı: {exc}', 'danger')
    return redirect(url_for('main.feedback_campaign_manage'))


@main_bp.route('/feedback/results/<int:campaign_id>/export.csv')
@login_required
@menu_key_required('feedback_results')
@manager_required
def feedback_results_export(campaign_id: int):
    from app.services.feedback_report_service import export_campaign_results_csv

    if not _can_export_feedback_now():
        flash('Dışa aktarma işlemini çok sık tetiklediniz. Birkaç saniye sonra yeniden deneyin.', 'warning')
        return redirect(url_for('main.feedback_results', campaign_id=campaign_id))

    campaign = get_campaign_or_404(campaign_id)
    payload = export_campaign_results_csv(campaign)
    filename = f'geri_bildirim_sonuclari_{campaign.id}.csv'
    return Response(
        payload,
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': f'attachment; filename={filename}'},
    )

# BYS360_FEEDBACK_10_EXPORT_ROUTES
@main_bp.route('/feedback/pulse/analytics/export.csv')
@login_required
@menu_key_required('feedback_manager')
@manager_required
def feedback_pulse_analytics_export_csv():
    from app.services.feedback_pro_export_service import export_pulse_analytics_csv
    if not _can_export_feedback_now():
        flash('Dışa aktarma işlemini çok sık tetiklediniz. Birkaç saniye sonra yeniden deneyin.', 'warning')
        return redirect(url_for('main.feedback_admin_pulse_analytics'))
    days = request.args.get('days', default=30, type=int) or 30
    days = max(7, min(days, 90))
    analytics = build_pulse_analytics(current_user, days)
    payload = export_pulse_analytics_csv(analytics, days)
    return Response(payload, mimetype='text/csv; charset=utf-8-sig', headers={'Content-Disposition': f'attachment; filename=nabiz_analitigi_{days}_gun.csv'})

@main_bp.route('/feedback/manager/export.csv')
@login_required
@menu_key_required('feedback_manager')
@manager_required
def feedback_manager_export_csv():
    from app.services.feedback_pro_export_service import export_manager_summary_csv
    if not _can_export_feedback_now():
        flash('Dışa aktarma işlemini çok sık tetiklediniz. Birkaç saniye sonra yeniden deneyin.', 'warning')
        return redirect(url_for('main.feedback_manager'))
    summary = build_manager_summary(current_user)
    payload = export_manager_summary_csv(summary)
    return Response(payload, mimetype='text/csv; charset=utf-8-sig', headers={'Content-Disposition': 'attachment; filename=yonetici_geri_bildirim_ozeti.csv'})

