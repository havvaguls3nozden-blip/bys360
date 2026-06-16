from __future__ import annotations

import secrets
import string

UPPER = string.ascii_uppercase
LOWER = string.ascii_lowercase
DIGITS = string.digits
SYMBOLS = "!@#$%*-_+?"
ALL_CHARS = UPPER + LOWER + DIGITS + SYMBOLS


def generate_secure_temporary_password(length: int = 14) -> str:
    if length < 12:
        length = 12
    chars = [
        secrets.choice(UPPER),
        secrets.choice(LOWER),
        secrets.choice(DIGITS),
        secrets.choice(SYMBOLS),
    ]
    while len(chars) < length:
        chars.append(secrets.choice(ALL_CHARS))
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)