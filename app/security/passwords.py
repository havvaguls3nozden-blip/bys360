"""BYS360 secure password helpers."""
from __future__ import annotations

import secrets
import string


def generate_initial_password(length: int = 14) -> str:
    """Generate a strong temporary password for new users."""
    length = max(12, int(length or 14))
    alphabet = string.ascii_letters + string.digits + "!@#$%*-_"
    while True:
        value = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(c.islower() for c in value)
            and any(c.isupper() for c in value)
            and any(c.isdigit() for c in value)
            and any(c in "!@#$%*-_" for c in value)
        ):
            return value
