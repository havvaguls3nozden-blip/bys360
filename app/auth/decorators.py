
"""Geriye dönük uyumluluk katmanı.

Bazı modüller hâlâ ``app.auth.decorators`` içinden ``manager_required``
ve benzeri decorator'ları import ediyor. Asıl kaynak artık
``app.route_support`` olduğu için burada yalnızca güvenli alias veriyoruz.
"""
from __future__ import annotations

from app.route_support import admin_required, manager_required, menu_key_required

__all__ = ["admin_required", "manager_required", "menu_key_required"]