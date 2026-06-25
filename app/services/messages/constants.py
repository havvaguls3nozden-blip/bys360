
"""Mesajlasma modulu icin sabit sozlesmeler.

Bu dosya Mesajlasma Faz 2 kapsaminda eklendi. Rota dosyalari henuz bu
paketi kullanmaya zorlanmaz; amac canli modul refactoru oncesinde sabitleri
tek yerde toplamak ve ileride route dosyasini inceltirken ayni degerlerin
korunmasini saglamaktir.
"""
from __future__ import annotations

REACTION_OPTIONS: list[str] = ["👍", "👎", "❤️", "👏", "✅", "👀", "🙏"]  # BYS360_MESSAGE_INTERACTIONS_V1

INBOX_THREAD_FETCH_LIMIT = 60
INBOX_THREAD_FETCH_LIMIT_SEARCH = 180
THREAD_MESSAGE_SOFT_LIMIT = 200
COMPOSE_USER_SOFT_LIMIT = 180

MESSAGE_LIVE_ENDPOINTS: tuple[str, ...] = (
    "/messages",
    "/messages/new",
    "/messages/thread/<int:thread_id>",
    "/messages/thread/<int:thread_id>/activity",
    "/messages/thread/<int:thread_id>/live",
    "/messages/thread/<int:thread_id>/typing",
    "/messages/<int:message_id>/react",
    "/messages/<int:message_id>/comment",  # BYS360_MESSAGE_INTERACTIONS_V1
    "/messages/thread/<int:thread_id>/send",
    "/messages/thread/<int:thread_id>/mark-read",
    "/messages/thread/<int:thread_id>/mute-toggle",
    "/messages/thread/<int:thread_id>/archive-toggle",
    "/messages/thread/<int:thread_id>/pin-toggle",
    "/messages/<int:message_id>/edit",
    "/messages/<int:message_id>/delete",
    "/messages/attachments/<filename>",
)

MESSAGE_REQUIRED_MODEL_NAMES: tuple[str, ...] = (
    "Message",
    "MessageAttachment",
    "MessageReaction",
    "MessageComment",  # BYS360_MESSAGE_INTERACTIONS_V1
    "MessageThread",
    "MessageThreadParticipant",
    "MessageTypingState",
    "User",
)
