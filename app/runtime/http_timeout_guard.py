"""BYS360 runtime outbound HTTP timeout guard.

Amaç: Sayfa render sırasında dış servis/AI/yardımcı HTTP çağrıları yanıtsız kalırsa
Flask isteğinin 3+ saniye beklemesini engellemek. Timeout açıkça verilmiş çağrılara dokunmaz.
"""
from __future__ import annotations

import os
from functools import wraps

_INSTALLED = False
_ORIGINAL_REQUEST = None


def _default_timeout() -> float:
    raw = os.environ.get("BYS360_OUTBOUND_HTTP_TIMEOUT", "0.85")
    try:
        value = float(raw)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/runtime/http_timeout_guard.py:19")
        value = 0.85
    return max(0.25, min(value, 5.0))


def install_default_http_timeout_guard() -> bool:
    """Install a process-wide default timeout for requests calls without timeout.

    Returns True when installed, False when requests is unavailable or already installed.
    """
    global _INSTALLED, _ORIGINAL_REQUEST
    if _INSTALLED:
        return False
    try:
        import requests
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/runtime/http_timeout_guard.py:34")
        return False

    original = requests.sessions.Session.request

    @wraps(original)
    def guarded_request(self, method, url, *args, **kwargs):
        # Explicit timeout wins. Only fill missing/None timeout.
        if kwargs.get("timeout") is None:
            kwargs["timeout"] = _default_timeout()
        return original(self, method, url, *args, **kwargs)

    requests.sessions.Session.request = guarded_request
    _ORIGINAL_REQUEST = original
    _INSTALLED = True
    return True


# BYS360_RUNTIME_COMMON_DELAY_V5_HELPER
