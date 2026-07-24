"""
BYS360 TCKN alan bazlı şifreleme yardımcıları.
Bu modül tek başına migration yapmaz ve mevcut veriyi dönüştürmez.
"""
from __future__ import annotations

import base64
import hashlib
import os
import re
from functools import lru_cache
from typing import Final

try:
    from cryptography.fernet import Fernet, InvalidToken
except Exception:  # pragma: no cover
    Fernet = None  # type: ignore[assignment,misc]
    InvalidToken = Exception  # type: ignore[assignment,misc]

_TCKN_RE: Final[re.Pattern[str]] = re.compile(r"^\d{11}$")

class TcknCryptoError(RuntimeError):
    """TCKN şifreleme/çözme işlemi yapılamadığında yükseltilir."""

def normalize_tckn(value: str | int | None) -> str:
    raw = "" if value is None else str(value).strip()
    digits = re.sub(r"\D+", "", raw)
    if not digits:
        return ""
    if not _TCKN_RE.match(digits):
        raise ValueError("TCKN 11 haneli sayısal değer olmalıdır.")
    return digits

def mask_tckn(value: str | int | None) -> str:
    digits = normalize_tckn(value)
    if not digits:
        return ""
    return f"{digits[:2]}*******{digits[-2:]}"

def _derive_fernet_key(raw_key: str) -> bytes:
    raw_key = (raw_key or "").strip()
    if not raw_key:
        raise TcknCryptoError("TCKN_ENCRYPTION_KEY tanımlı değil.")
    try:
        decoded = base64.urlsafe_b64decode(raw_key.encode("utf-8"))
        if len(decoded) == 32:
            return raw_key.encode("utf-8")
    except Exception:
        pass
    digest = hashlib.sha256(raw_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)

@lru_cache(maxsize=4)
def _fernet_from_key(raw_key: str):
    if Fernet is None:
        raise TcknCryptoError("cryptography.fernet yüklenemedi.")
    return Fernet(_derive_fernet_key(raw_key))

def _get_config_key(explicit_key: str | None = None) -> str:
    if explicit_key:
        return explicit_key.strip()
    try:
        from flask import current_app
        key = current_app.config.get("TCKN_ENCRYPTION_KEY")
        if key:
            return str(key).strip()
    except Exception:
        pass
    return os.getenv("TCKN_ENCRYPTION_KEY", "").strip()

def encrypt_tckn(value: str | int | None, *, key: str | None = None) -> str:
    digits = normalize_tckn(value)
    if not digits:
        return ""
    fernet = _fernet_from_key(_get_config_key(key))
    return fernet.encrypt(digits.encode("utf-8")).decode("utf-8")

def decrypt_tckn(token: str | None, *, key: str | None = None) -> str:
    raw = "" if token is None else str(token).strip()
    if not raw:
        return ""
    fernet = _fernet_from_key(_get_config_key(key))
    try:
        return normalize_tckn(fernet.decrypt(raw.encode("utf-8")).decode("utf-8"))
    except InvalidToken as exc:
        raise TcknCryptoError("TCKN şifreli değer çözülemedi.") from exc

def is_encrypted_tckn(value: str | None) -> bool:
    raw = "" if value is None else str(value).strip()
    return raw.startswith("gAAAAA") and len(raw) > 80
