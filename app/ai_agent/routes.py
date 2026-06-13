from __future__ import annotations



from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from app.services.ai_agent import (
    build_ai_agent_action_queue_summary,
    build_ai_agent_assistant_widget_summary,
    build_ai_agent_dashboard_kpi_summary,
    build_ai_agent_health_payload,
    build_ai_agent_panel_context,
    build_ai_agent_performance_summary,
    build_ai_agent_reply,
    build_ai_agent_security_policy,
    build_ai_agent_security_self_check,
    enqueue_ai_agent_suggestion,
)

ai_agent_bp = Blueprint(


"ai_agent", __name__, url_prefix="/ai-agent")







# BYS360_AG1_AG2_AI_AGENT_ROUTE_GUARD_START
@ai_agent_bp.before_request
def _bys360_ag2b_ai_agent_before_request():
    from flask import request, render_template
    from flask_login import current_user

    endpoint = request.endpoint or ""
    path = request.path or ""

    # Sağ alt widget ve API uçları oturum açmış kullanıcıda çalışmalı.
    if endpoint.endswith("healthz") or path.endswith("/healthz"):
        return None

    if not getattr(current_user, "is_authenticated", False):
        return None

    if path.startswith("/ai-agent/api/"):
        return None

    # Panel sayfası menüden gösterilmeyecek; direkt erişimde yetki varsa açılır.
    try:
        from app.services.menu_visibility import build_menu_visibility_map
        menu_map = build_menu_visibility_map(current_user)
        allowed = bool(menu_map.get("ai_agent_panel") or menu_map.get("assistant_module") or menu_map.get("ai_teaching_center") or menu_map.get("ai_knowledge_library") or menu_map.get("ai_agent_knowledge") or menu_map.get("ai_agent_teaching_center"))
    except Exception:
        # Menü servisi çalışmazsa sadece paneli kapat, widget API'ları zaten yukarıda açık.
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/ai_agent/routes.py:56")
        allowed = False

    if allowed:
        return None

    try:
        return render_template("errors/access_denied.html"), 403
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/ai_agent/routes.py:65")
        return (
            "<!doctype html><html lang='tr'><head><meta charset='utf-8'>"
            "<title>Erişim Yetkisi Yok</title></head>"
            "<body style='font-family:Arial,sans-serif;background:#f6f3f0;margin:0;padding:40px;'>"
            "<div style='max-width:760px;margin:40px auto;background:white;border-radius:18px;"
            "box-shadow:0 16px 40px rgba(0,0,0,.10);padding:32px;border-left:8px solid #8B0000;'>"
            "<h1 style='margin-top:0;color:#8B0000;'>Bu sayfaya erişim yetkiniz bulunmamaktadır.</h1>"
            "<p>BYS360 Asistanı sağ alt yardımcı panel üzerinden kullanılmalıdır.</p>"
            "</div></body></html>",
            403,
        )
# BYS360_AG1_AG2_AI_AGENT_ROUTE_GUARD_END


@ai_agent_bp.get("/healthz")
def ai_agent_public_healthz():
    """Dış smoke test için hassas veri içermeyen sağlık ucu."""
    payload = build_ai_agent_health_payload()
    public_payload = {
        "status": payload.get("status"),
        "service": payload.get("service"),
        "version": payload.get("version"),
        "mode": payload.get("mode"),
        "ag2_performance_bridge": payload.get("ag2_performance_bridge"),
        "ag3_dashboard_kpi_bridge": payload.get("ag3_dashboard_kpi_bridge"),
        "ag4_assistant_panel_bridge": payload.get("ag4_assistant_panel_bridge"),
        "ag5_action_queue_bridge": payload.get("ag5_action_queue_bridge"),
        "ag6_security_gate": payload.get("ag6_security_gate"),
    }
    return jsonify(public_payload), 200


@ai_agent_bp.get("/health")
@login_required
def ai_agent_health():
    return jsonify(build_ai_agent_health_payload()), 200


@ai_agent_bp.get("/panel")
@login_required
def ai_agent_panel():
    context = build_ai_agent_panel_context(current_user)
    return render_template("ai_agent/panel.html", **context)


@ai_agent_bp.post("/api/ask")
@login_required
def ai_agent_ask():
    payload = request.get_json(silent=True) or {}
    question = payload.get("question") or request.form.get("question") or ""
    context = payload.get("context") if isinstance(payload.get("context"), dict) else {}
    try:
        result = build_ai_agent_reply(current_user, question, context=context)
    except TypeError:
        result = build_ai_agent_reply(current_user, question)
    return jsonify(result), 200


@ai_agent_bp.get("/api/actions")
@login_required
def ai_agent_actions():
    context = build_ai_agent_panel_context(current_user)
    return jsonify({
        "ok": True,
        "version": context.get("version"),
        "counts": context.get("counts"),
        "performance_summary": context.get("performance_summary"),
        "dashboard_kpi_summary": context.get("dashboard_kpi_summary"),
        "assistant_widget_summary": context.get("assistant_widget_summary"),
        "action_queue_summary": context.get("action_queue_summary"),
        "suggested_actions": context.get("suggested_actions"),
        "actions": context.get("capabilities"),
        "notice": context.get("decision_notice"),
    }), 200


@ai_agent_bp.get("/api/performance-summary")
@login_required
def ai_agent_performance_summary():
    """AG-2: Performans modülü için yetki kontrollü sayı/özet ucu."""
    return jsonify(build_ai_agent_performance_summary(current_user)), 200


@ai_agent_bp.get("/api/dashboard-kpi-summary")
@login_required
def ai_agent_dashboard_kpi_summary():
    """AG-3: Yönetici dashboard ve KPI/Hedef için yetki kontrollü sayı/özet ucu."""
    return jsonify(build_ai_agent_dashboard_kpi_summary(current_user)), 200


@ai_agent_bp.get("/api/assistant-widget-summary")
@login_required
def ai_agent_assistant_widget_summary():
    """AG-4: Sağ alt BYS360 Asistanı paneli için güvenli kart özeti.

    Bu endpoint veri değiştirmez, hassas içerik dökmez ve idari karar üretmez.
    """
    return jsonify(build_ai_agent_assistant_widget_summary(current_user)), 200


@ai_agent_bp.get("/api/action-queue-summary")
@login_required
def ai_agent_action_queue_summary():
    """AG-5: Onaylı aksiyon kuyruğu için güvenli öneri/özet ucu.

    Bu endpoint iş verisi değiştirmez; yalnızca takip kuyruğu ve öneri kartı özeti verir.
    """
    return jsonify(build_ai_agent_action_queue_summary(current_user)), 200


@ai_agent_bp.get("/api/security-policy")
@login_required
def ai_agent_security_policy():
    """AG-6: Canlı güvenlik politikası ve endpoint sınırı özeti.

    Bu endpoint hassas veri dökmez; yalnızca login sonrası güvenlik kontrol bilgisini verir.
    """
    return jsonify(build_ai_agent_security_policy(current_user)), 200


@ai_agent_bp.get("/api/security-self-check")
@login_required
def ai_agent_security_self_check():
    """AG-6: Kullanıcı bağlamında güvenli öz denetim ucu.

    Kullanıcı adı, e-posta, sicil, mesaj içeriği, anket cevabı veya performans detayı döndürmez.
    """
    return jsonify(build_ai_agent_security_self_check(current_user)), 200


@ai_agent_bp.post("/api/action-queue-suggestion")
@login_required
def ai_agent_action_queue_suggestion():
    """AG-5: Kullanıcı isteğiyle öneriyi güvenli aksiyon kuyruğuna alır.

    Bu işlem gerçek modül aksiyonu değildir; yalnızca takip kaydı üretir.
    """
    payload = request.get_json(silent=True) or {}
    action_key = payload.get("action_key") or request.form.get("action_key") or ""
    source = payload.get("source") or request.form.get("source") or "assistant_panel"
    status_code = 200
    result = enqueue_ai_agent_suggestion(current_user, action_key, source=source)
    if not result.get("ok"):
        status_code = 400
    return jsonify(result), status_code

# BYS360_AG5_AI_TEACHING_CENTER_ROUTES_START
def _ag5_access_denied_response():
    from flask import render_template
    try:
        return render_template('errors/access_denied.html'), 403
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/ai_agent/routes.py:217")
        return ('<!doctype html><html lang="tr"><head><meta charset="utf-8"><title>Erişim Yetkisi Yok</title></head><body style="font-family:Arial,sans-serif;background:#f6f3f0;margin:0;padding:40px;"><div style="max-width:760px;margin:40px auto;background:white;border-radius:18px;box-shadow:0 16px 40px rgba(0,0,0,.10);padding:32px;border-left:8px solid #8B0000;"><h1 style="margin-top:0;color:#8B0000;">Bu sayfaya erişim yetkiniz bulunmamaktadır.</h1><p>Asistan Bilgi Bankası yalnızca yetkili kullanıcılar tarafından yönetilebilir.</p></div></body></html>', 403)


@ai_agent_bp.route('/knowledge', methods=['GET', 'POST'])
def ag5_knowledge_center():
    from flask import render_template, request, redirect, url_for, flash
    from flask_login import current_user
    if not getattr(current_user, 'is_authenticated', False):
        try:
            return redirect(url_for('main.login'))
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/ai_agent/routes.py:228")
            return _ag5_access_denied_response()
    from app.services.ai_agent.knowledge import can_manage_ai_knowledge, create_knowledge_entry, init_knowledge_table, list_knowledge_entries
    if not can_manage_ai_knowledge(current_user):
        return _ag5_access_denied_response()
    init_knowledge_table()
    if request.method == 'POST':
        try:
            create_knowledge_entry(title=request.form.get('title',''), question_patterns=request.form.get('question_patterns',''), answer=request.form.get('answer',''), tags=request.form.get('tags',''), audience=request.form.get('audience','all'), priority=request.form.get('priority',50), created_by=getattr(current_user,'id',None))
            try:
                flash("Bilgi kaydı BYS360 Asistanınına öğretildi.", 'success')
            except Exception:
                __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/ai_agent/routes.py)")
        except Exception as exc:
            try:
                flash(f'Bilgi kaydı oluşturulamadı: {exc}', 'danger')
            except Exception:
                __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/ai_agent/routes.py)")
        return redirect(url_for('.ag5_knowledge_center'))
    entries = list_knowledge_entries(include_inactive=True)
    return render_template('ai_agent/knowledge.html', entries=entries)


@ai_agent_bp.route('/knowledge/<int:entry_id>/toggle', methods=['POST'])
def ag5_knowledge_toggle(entry_id):
    from flask import redirect, url_for, flash
    from flask_login import current_user
    from app.services.ai_agent.knowledge import can_manage_ai_knowledge, toggle_knowledge_entry
    if not can_manage_ai_knowledge(current_user):
        return _ag5_access_denied_response()
    toggle_knowledge_entry(entry_id)
    try:
        flash('Bilgi kaydının durumu güncellendi.', 'success')
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/ai_agent/routes.py)")
    return redirect(url_for('.ag5_knowledge_center'))


@ai_agent_bp.route('/knowledge/<int:entry_id>/delete', methods=['POST'])
def ag5_knowledge_delete(entry_id):
    from flask import redirect, url_for, flash
    from flask_login import current_user
    from app.services.ai_agent.knowledge import can_manage_ai_knowledge, delete_knowledge_entry
    if not can_manage_ai_knowledge(current_user):
        return _ag5_access_denied_response()
    delete_knowledge_entry(entry_id)
    try:
        flash('Bilgi kaydı silindi.', 'success')
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/ai_agent/routes.py)")
    return redirect(url_for('.ag5_knowledge_center'))


@ai_agent_bp.route('/api/knowledge-search', methods=['POST'])
def ag5_knowledge_search_api():
    from flask import jsonify, request
    from flask_login import current_user
    from app.services.ai_agent.knowledge import search_knowledge_answer
    if not getattr(current_user, 'is_authenticated', False):
        return jsonify({'ok': False, 'message': 'Oturum gerekli.'}), 401
    data = request.get_json(silent=True) or {}
    matches = search_knowledge_answer(data.get('question') or data.get('q') or '', limit=3)
    return jsonify({'ok': True, 'matches': matches})


# BYS360_ASSISTANT_TEACHING_CENTER_ROUTE_V2_START
@ai_agent_bp.get('/teaching-center')
@login_required
def assistant_teaching_center():
    """BYS360 Asistanı Öğretim Merkezi: güvenli eğitim bankası ekranı."""
    return render_template('assistant_training_bank.html')
# BYS360_ASSISTANT_TEACHING_CENTER_ROUTE_V2_END

# BYS360_AG5_AI_TEACHING_CENTER_ROUTES_END

# BYS360_ASSISTANT_TABS_ROLE_MATRIX_V2_BEGIN
# BYS360 Asistanı alt sekmeleri için URL düzeyi rol matrisi koruması.
@ai_agent_bp.before_request
def _bys360_assistant_tabs_role_matrix_v2_before_request():
    endpoint = request.endpoint or ""
    path = request.path or ""
    if path.endswith("/healthz") or path.endswith("/health"):
        return None
    if not getattr(current_user, "is_authenticated", False):
        return None
    try:
        from app.services.menu_visibility import build_menu_visibility_map
        menu_map = build_menu_visibility_map(current_user)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/ai_agent/routes.py:316")
        menu_map = {}

    def _allowed(*keys):
        return any(bool(menu_map.get(key)) for key in keys)

    required = ("assistant_module", "ai_agent_panel")
    if path.startswith("/ai-agent/knowledge"):
        required = ("ai_agent_knowledge", "ai_teaching_center")
    elif path.startswith("/ai-agent/teaching-center"):
        required = ("ai_agent_teaching_center",)
    elif path.startswith("/ai-agent/panel"):
        required = ("assistant_module", "ai_agent_panel", "assistant_center")
    elif path.startswith("/ai-agent/api/"):
        required = ("assistant_module", "ai_agent_panel", "assistant_center")

    if _allowed(*required):
        return None
    return _ag5_access_denied_response()
# BYS360_ASSISTANT_TABS_ROLE_MATRIX_V2_END
