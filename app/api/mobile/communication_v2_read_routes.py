from __future__ import annotations

# BYS360 mobile communication v2 read route bridge module.
# P11-B7 kapsamında communication v2 GET okuma endpointi ayrılmıştır.
# URL path ve JSON cevap davranışı değiştirilmemelidir.

_COMMUNICATION_V2_READ_ROUTE_SOURCE = '@mobile_api_bp.get("/communication/v2/threads")\n@require_mobile_user\ndef mobile_b48_communication_v2_threads(user: User):\n    try:\n        q = MessageThread.query.join(MessageThreadParticipant, MessageThreadParticipant.thread_id == MessageThread.id).filter(\n            MessageThreadParticipant.user_id == user.id,\n            MessageThread.is_active.is_(True),\n        )\n        try:\n            q = q.filter(MessageThreadParticipant.left_at.is_(None), MessageThreadParticipant.is_archived.is_(False))\n        except Exception:\n            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/api/mobile/routes.py:1969)")\n        total = _safe_count(q)\n        try:\n            rows = q.order_by(MessageThread.last_message_at.desc().nullslast(), MessageThread.id.desc()).limit(500).all()\n        except Exception:\n            rows = q.order_by(MessageThread.id.desc()).limit(500).all()\n        threads = [_b48_thread_row(t, user) for t in rows]\n        unread_total = sum(int(t.get("unread_count") or 0) for t in threads)\n        return jsonify({\n            "source": "real_message_threads_v2",\n            "source_label": "Canlı BYS360 mesajlaşma verisi",\n            "total": total,\n            "count": len(threads),\n            "unread_total": unread_total,\n            "threads": threads,\n            "items": threads,\n            "rows": threads,\n            "metrics": [\n                _metric("Konuşma", total, "Katılımcı olduğunuz başlık", "blue", "forum"),\n                _metric("Okunmamış", unread_total, "Size gelen yeni mesajlar", "blue", "mark_unread_chat_alt"),\n                _metric("Kaynak", "Gerçek", "message_threads ve messages kayıtları", "blue", "api"),\n            ],\n        })\n    except Exception as exc:\n        current_app.logger.exception("B48 mobile communication threads failed")\n        return jsonify({\n            "source": "real_message_threads_v2_error_safe",\n            "source_label": "Canlı BYS360 mesajlaşma verisi",\n            "total": 0,\n            "count": 0,\n            "threads": [],\n            "items": [],\n            "rows": [],\n            "message": "Mesajlaşma kayıtları şu anda yüklenemedi. Sunucu logu kontrol edilmelidir.",\n            "warning": str(exc)[:240],\n        })\n'


def register_mobile_communication_v2_read_routes_v1(mobile_bp, route_globals: dict) -> None:
    """Register communication v2 read mobile route on the existing mobile blueprint."""
    if route_globals.get("_BYS360_P11_B7_COMMUNICATION_V2_READ_ROUTES_REGISTERED"):
        return

    route_globals["mobile_bp"] = mobile_bp
    exec(_COMMUNICATION_V2_READ_ROUTE_SOURCE, route_globals, route_globals)
    route_globals["_BYS360_P11_B7_COMMUNICATION_V2_READ_ROUTES_REGISTERED"] = True
