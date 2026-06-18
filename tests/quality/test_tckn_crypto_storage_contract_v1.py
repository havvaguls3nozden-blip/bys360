# -*- coding: utf-8 -*-
from __future__ import annotations


def test_tckn_crypto_never_returns_plaintext_token_and_masks_identity():
    from app.security.tckn_crypto import (
        decrypt_tckn,
        encrypt_tckn,
        is_encrypted_tckn,
        mask_tckn,
    )

    plaintext = "12345678901"
    key = "bys360-test-tckn-storage-contract-key-v1"

    token = encrypt_tckn(plaintext, key=key)

    assert token
    assert token != plaintext
    assert plaintext not in token
    assert is_encrypted_tckn(token)
    assert decrypt_tckn(token, key=key) == plaintext
    assert mask_tckn(plaintext) == "12*******01"
