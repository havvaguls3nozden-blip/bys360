# -*- coding: utf-8 -*-
from __future__ import annotations

from cryptography.fernet import Fernet

def test_tckn_crypto_roundtrip():
    from app.security.tckn_crypto import decrypt_tckn, encrypt_tckn, mask_tckn

    key = Fernet.generate_key().decode("utf-8")
    token = encrypt_tckn("12345678901", key=key)

    assert token != "12345678901"
    assert decrypt_tckn(token, key=key) == "12345678901"
    assert mask_tckn("12345678901") == "12*******01"
