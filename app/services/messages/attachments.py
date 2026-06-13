
"""Mesaj ekleri icin servis iskeleti.

Faz 2'de route davranisi degismez. Bu dosya mevcut
``app.services.message_service`` yardimcilarina guvenli isimler uzerinden
kopru kurar; sonraki fazlarda route dosyasi bu pakete kademeli baglanabilir.
"""
from __future__ import annotations

from app.services.message_service import (  # noqa: F401
    attachment_icon_class,
    attachment_is_image,
    attachment_is_video,
    format_attachment_file_size,
    get_message_attachment_for_user,
    normalize_incoming_message_files,
    remove_message_attachment_file,
    save_message_attachment,
)
