
"""BYS360 UTC zaman yardimcilari.

Mevcut veritabani kolonlarinin onemli bolumu timezone-aware degil. Bu nedenle
varsayilan uygulama zamani naive UTC olarak dondurulur; yeni ihtiyaclar icin
ayrica aware UTC yardimcisi da vardir.
"""
from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Schema degisikligi gerektirmeden naive UTC datetime dondurur."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utc_now_aware() -> datetime:
    """Timezone-aware UTC datetime dondurur."""
    return datetime.now(timezone.utc)


def utc_today():
    return utc_now().date()


__all__ = ["utc_now", "utc_now_aware", "utc_today"]
