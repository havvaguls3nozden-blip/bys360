from __future__ import annotations



from dataclasses import dataclass, field
from typing import Literal

MessageMethod = Literal["GET", "POST"]


@dataclass(frozen=True)
class MessageEndpointContract:
    """Canli mesaj endpoint sozlesmesi.

    Bu sinif Flask rota kaydi yapmaz. Sadece Faz 2 servis iskeletinde,
    sonraki tasimalarda korunmasi gereken endpoint/method/menu sozlesmesini
    temsil eder.
    """

    rule: str
    endpoint: str
    methods: tuple[MessageMethod, ...] = ("GET",)
    requires_login: bool = True
    menu_key: str = "messages"
    writes_data: bool = False
    touches_attachments: bool = False
    touches_notifications: bool = False
    ajax_supported: bool = False


@dataclass(frozen=True)
class MessageLiveContract:
    """Mesajlasma refactoru icin kirilmayacak canli davranis listesi."""

    endpoints: tuple[MessageEndpointContract, ...]
    protected_tables: tuple[str, ...]
    invariants: tuple[str, ...] = field(default_factory=tuple)


def build_message_live_contract() -> MessageLiveContract:
    return MessageLiveContract(
        endpoints=(
            MessageEndpointContract("/messages", "messages_inbox", ajax_supported=True),
            MessageEndpointContract("/messages/new", "messages_new", ("GET", "POST"), writes_data=True, touches_notifications=True),
            MessageEndpointContract("/messages/thread/<int:thread_id>", "messages_thread", ajax_supported=True),
            MessageEndpointContract("/messages/thread/<int:thread_id>/activity", "messages_thread_activity", ajax_supported=True),
            MessageEndpointContract("/messages/thread/<int:thread_id>/live", "messages_thread_live", ajax_supported=True),
            MessageEndpointContract("/messages/thread/<int:thread_id>/typing", "messages_thread_typing", ("POST",), writes_data=True, ajax_supported=True),
            MessageEndpointContract("/messages/<int:message_id>/react", "messages_react", ("POST",), writes_data=True, ajax_supported=True),
            MessageEndpointContract("/messages/thread/<int:thread_id>/send", "messages_send", ("POST",), writes_data=True, touches_attachments=True, touches_notifications=True, ajax_supported=True),
            MessageEndpointContract("/messages/thread/<int:thread_id>/mark-read", "messages_mark_read", ("POST",), writes_data=True, ajax_supported=True),
            MessageEndpointContract("/messages/thread/<int:thread_id>/mute-toggle", "messages_toggle_mute", ("POST",), writes_data=True, ajax_supported=True),
            MessageEndpointContract("/messages/thread/<int:thread_id>/archive-toggle", "messages_toggle_archive", ("POST",), writes_data=True, ajax_supported=True),
            MessageEndpointContract("/messages/thread/<int:thread_id>/pin-toggle", "messages_toggle_pin", ("POST",), writes_data=True, ajax_supported=True),
            MessageEndpointContract("/messages/<int:message_id>/edit", "messages_edit", ("POST",), writes_data=True, ajax_supported=True),
            MessageEndpointContract("/messages/<int:message_id>/delete", "messages_delete", ("POST",), writes_data=True, ajax_supported=True),
            MessageEndpointContract("/messages/attachments/<filename>", "message_attachment_download", touches_attachments=True),
        ),
        protected_tables=(
            "messages",
            "message_threads",
            "message_thread_participants",
            "message_attachments",
            "message_reactions",
            "message_typing_states",
        ),
        invariants=(
            "Kullanici yalnizca katilimcisi oldugu threadleri gorebilir.",
            "Silinen mesaj canli akista normal mesaj gibi gosterilmez.",
            "Ek indirme islemi kullanici yetkisi dogrulanmadan dosya dondurmez.",
            "Mesaj gonderme akisi bos mesaj + bos ek kombinasyonunu kabul etmez.",
            "AJAX cevaplari mevcut template ve mobil akisi bozmadan JSON donebilmelidir.",
        ),
    )
