from __future__ import annotations

# BYS360 mobile communication v2 read route bridge module.
# P11-B7 kapsamında communication v2 GET okuma endpointi ayrılmıştır.
# URL path ve JSON cevap davranışı değiştirilmemelidir.

def register_mobile_communication_v2_read_routes_v1(mobile_bp, route_globals) -> None:
    """Register communication v2 read mobile route on the existing mobile blueprint."""
    if route_globals.get("_BYS360_P11_B7_COMMUNICATION_V2_READ_ROUTES_REGISTERED"):
        return

    route_globals['mobile_bp'] = mobile_bp
    route_globals.setdefault('mobile_api_bp', mobile_bp)
    globals().update(route_globals)

    @mobile_api_bp.get("/communication/v2/threads")
    @require_mobile_user
    def mobile_b48_communication_v2_threads(user: User):
        try:
            q = MessageThread.query.join(MessageThreadParticipant, MessageThreadParticipant.thread_id == MessageThread.id).filter(
                MessageThreadParticipant.user_id == user.id,
                MessageThread.is_active.is_(True),
            )
            try:
                q = q.filter(MessageThreadParticipant.left_at.is_(None), MessageThreadParticipant.is_archived.is_(False))
            except Exception:
                __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/api/mobile/routes.py:1969)")
            total = _safe_count(q)
            try:
                rows = q.order_by(MessageThread.last_message_at.desc().nullslast(), MessageThread.id.desc()).limit(500).all()
            except Exception:
                rows = q.order_by(MessageThread.id.desc()).limit(500).all()
            threads = [_b48_thread_row(t, user) for t in rows]
            unread_total = sum(int(t.get("unread_count") or 0) for t in threads)
            return jsonify({
                "source": "real_message_threads_v2",
                "source_label": "Canlı BYS360 mesajlaşma verisi",
                "total": total,
                "count": len(threads),
                "unread_total": unread_total,
                "threads": threads,
                "items": threads,
                "rows": threads,
                "metrics": [
                    _metric("Konuşma", total, "Katılımcı olduğunuz başlık", "blue", "forum"),
                    _metric("Okunmamış", unread_total, "Size gelen yeni mesajlar", "blue", "mark_unread_chat_alt"),
                    _metric("Kaynak", "Gerçek", "message_threads ve messages kayıtları", "blue", "api"),
                ],
            })
        except Exception as exc:
            current_app.logger.exception("B48 mobile communication threads failed")
            return jsonify({
                "source": "real_message_threads_v2_error_safe",
                "source_label": "Canlı BYS360 mesajlaşma verisi",
                "total": 0,
                "count": 0,
                "threads": [],
                "items": [],
                "rows": [],
                "message": "Mesajlaşma kayıtları şu anda yüklenemedi. Sunucu logu kontrol edilmelidir.",
                "warning": str(exc)[:240],
            })

    route_globals["_BYS360_P11_B7_COMMUNICATION_V2_READ_ROUTES_REGISTERED"] = True
