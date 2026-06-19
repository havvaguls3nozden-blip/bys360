from __future__ import annotations

# BYS360 mobile detail/read route bridge module.
# P11-B4 kapsamında küçük ve düşük riskli mobil GET/detail endpointleri ayrılmıştır.
# URL path ve JSON cevap davranışı değiştirilmemelidir.

def register_mobile_detail_read_routes_v1(mobile_bp, route_globals) -> None:
    """Register small read-only detail mobile routes on the existing mobile blueprint."""
    if route_globals.get("_BYS360_P11_B4_DETAIL_READ_ROUTES_REGISTERED"):
        return

    route_globals['mobile_bp'] = mobile_bp
    route_globals.setdefault('mobile_api_bp', mobile_bp)
    globals().update(route_globals)

    @mobile_api_bp.get("/support/tickets/<int:ticket_id>")
    @require_mobile_user
    def mobile_support_ticket_detail(user: User, ticket_id: int):
        ticket = db.session.get(SupportTicket, ticket_id)
        if not ticket:
            return jsonify({"message": "Destek talebi bulunamadı."}), 404
        if not _can_mobile_view_ticket(user, ticket):
            return jsonify({"message": "Bu destek talebini görüntüleme yetkiniz bulunmamaktadır."}), 403
        return jsonify(_ticket_detail_payload(ticket, user))

    @mobile_api_bp.get("/surveys/<int:survey_id>")
    @require_mobile_user
    def mobile_survey_detail(user: User, survey_id: int):
        survey = db.session.get(Survey, survey_id)
        if not survey:
            return jsonify({"message": "Anket bulunamadı."}), 404
        if not _mobile_survey_visible(user, survey):
            return jsonify({"message": "Bu anketi görüntüleme yetkiniz bulunmamaktadır."}), 403
        return jsonify(_mobile_survey_detail_payload(survey, user))

    @mobile_api_bp.get("/communication/threads")
    @require_mobile_user
    def mobile_communication_threads(user: User):
        q = MessageThread.query.join(MessageThreadParticipant, MessageThreadParticipant.thread_id == MessageThread.id).filter(MessageThreadParticipant.user_id == user.id).order_by(MessageThread.last_message_at.desc().nullslast())
        items = [_item(t.id, getattr(t, "subject", None) or "Kurum içi konuşma", getattr(t, "badge_label", "") or getattr(t, "thread_type", ""), "Aktif" if getattr(t, "is_active", True) else "Pasif", getattr(t, "thread_type", ""), "", 60) for t in q.limit(40).all()]
        return _module_payload([
            _metric("Konuşma", _safe_count(q), "Katılımcı olduğunuz başlık", "blue", "forum"),
            _metric("Duyuru", _safe_count(Notification.query.filter_by(user_id=user.id)), "Bildirim altyapısından", "blue", "campaign"),
            _metric("Kaynak", "Gerçek", "messages/thread kayıtları", "blue", "api"),
        ], items)

    route_globals["_BYS360_P11_B4_DETAIL_READ_ROUTES_REGISTERED"] = True
