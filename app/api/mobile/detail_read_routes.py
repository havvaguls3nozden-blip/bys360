from __future__ import annotations

# BYS360 mobile detail/read route bridge module.
# P11-B4 kapsamında küçük ve düşük riskli mobil GET/detail endpointleri ayrılmıştır.
# URL path ve JSON cevap davranışı değiştirilmemelidir.

_DETAIL_READ_ROUTE_SOURCE = '@mobile_api_bp.get("/support/tickets/<int:ticket_id>")\n@require_mobile_user\ndef mobile_support_ticket_detail(user: User, ticket_id: int):\n    ticket = db.session.get(SupportTicket, ticket_id)\n    if not ticket:\n        return jsonify({"message": "Destek talebi bulunamadı."}), 404\n    if not _can_mobile_view_ticket(user, ticket):\n        return jsonify({"message": "Bu destek talebini görüntüleme yetkiniz bulunmamaktadır."}), 403\n    return jsonify(_ticket_detail_payload(ticket, user))\n\n@mobile_api_bp.get("/surveys/<int:survey_id>")\n@require_mobile_user\ndef mobile_survey_detail(user: User, survey_id: int):\n    survey = db.session.get(Survey, survey_id)\n    if not survey:\n        return jsonify({"message": "Anket bulunamadı."}), 404\n    if not _mobile_survey_visible(user, survey):\n        return jsonify({"message": "Bu anketi görüntüleme yetkiniz bulunmamaktadır."}), 403\n    return jsonify(_mobile_survey_detail_payload(survey, user))\n\n@mobile_api_bp.get("/communication/threads")\n@require_mobile_user\ndef mobile_communication_threads(user: User):\n    q = MessageThread.query.join(MessageThreadParticipant, MessageThreadParticipant.thread_id == MessageThread.id).filter(MessageThreadParticipant.user_id == user.id).order_by(MessageThread.last_message_at.desc().nullslast())\n    items = [_item(t.id, getattr(t, "subject", None) or "Kurum içi konuşma", getattr(t, "badge_label", "") or getattr(t, "thread_type", ""), "Aktif" if getattr(t, "is_active", True) else "Pasif", getattr(t, "thread_type", ""), "", 60) for t in q.limit(40).all()]\n    return _module_payload([\n        _metric("Konuşma", _safe_count(q), "Katılımcı olduğunuz başlık", "blue", "forum"),\n        _metric("Duyuru", _safe_count(Notification.query.filter_by(user_id=user.id)), "Bildirim altyapısından", "blue", "campaign"),\n        _metric("Kaynak", "Gerçek", "messages/thread kayıtları", "blue", "api"),\n    ], items)\n'


def register_mobile_detail_read_routes_v1(mobile_bp, route_globals: dict) -> None:
    """Register small read-only detail mobile routes on the existing mobile blueprint."""
    if route_globals.get("_BYS360_P11_B4_DETAIL_READ_ROUTES_REGISTERED"):
        return

    route_globals["mobile_bp"] = mobile_bp
    exec(_DETAIL_READ_ROUTE_SOURCE, route_globals, route_globals)
    route_globals["_BYS360_P11_B4_DETAIL_READ_ROUTES_REGISTERED"] = True
