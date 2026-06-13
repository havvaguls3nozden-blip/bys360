from __future__ import annotations

# --- BYS360 third-manager Excel import compatibility patch ---


THIRD_MANAGER_STANDARD_KEY = "ucuncu_yonetici_sicil"
THIRD_MANAGER_HEADER_ALIASES = [
    "ucuncu_yonetici_sicil",
    "üçüncü yönetici sicil",
    "ucuncu yonetici sicil",
    "3. amir sicil",
    "3 amir sicil",
    "new_y3",
]

from dataclasses import dataclass
from typing import Any, Optional


def _safe(value: Any) -> str:
    return str(value or '').strip()


@dataclass(slots=True)
class ExplicitManagerTuple:
    manager_1_sicil: str | None
    manager_2_sicil: str | None
    manager_3_sicil: str | None

    def as_tuple(self) -> tuple[str | None, str | None, str | None]:
        return (self.manager_1_sicil, self.manager_2_sicil, self.manager_3_sicil)


def current_manager_tuple(user: Any) -> ExplicitManagerTuple:
    return ExplicitManagerTuple(
        manager_1_sicil=_safe(getattr(user, 'yonetici_sicil', None)) or None,
        manager_2_sicil=_safe(getattr(user, 'ikinci_yonetici_sicil', None)) or None,
        manager_3_sicil=_safe(getattr(user, 'ucuncu_yonetici_sicil', None)) or None,
    )


def has_explicit_manager_fields(user: Any) -> bool:
    current = current_manager_tuple(user)
    return any(current.as_tuple())


def explicit_manager_count(user: Any) -> int:
    return sum(1 for item in current_manager_tuple(user).as_tuple() if item)