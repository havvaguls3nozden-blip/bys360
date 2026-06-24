from __future__ import annotations

import logging
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
from typing import Any, Iterable

from app.extensions import db
from app.models import User

try:
    from app.services.personnel_sync_service import canonical_role_label, canonical_role_value
except Exception:  # pragma: no cover
    def canonical_role_value(value: Any) -> str:
        return str(value or 'personel').strip().lower().replace(' ', '_') or 'personel'

    def canonical_role_label(value: Any) -> str:
        role = canonical_role_value(value)
        labels = {
            'admin': 'Admin',
            'baskan': 'Başkan',
            'baskan_yardimcisi': 'Başkan Yardımcısı',
            'grup_baskani': 'Grup Başkanı',
            'mali_musavir': 'Mali Müşavir',
            'birim_sorumlusu': 'Birim Sorumlusu',
            'koordinator': 'Koordinatör',
            'personel': 'Personel',
        }
        return labels.get(role, role.replace('_', ' ').title())

from app.services.hierarchy_rulebook_service import (
    build_lookup,
    infer_role_from_profile as _infer_role_from_profile,
    is_system_user,
)
from app.services.performance.chain_rule_engine import resolve_authoritative_desired_chain
from app.services.explicit_manager_chain_service import has_explicit_manager_fields


@dataclass(slots=True)
class AutoHierarchyResult:
    updated_count: int = 0
    skipped_count: int = 0
    warnings: list[str] | None = None


def infer_role_from_profile(*, raw_role: str | None = None, unvan: str | None = None, birim: str | None = None, ust_birim: str | None = None) -> tuple[str, str]:
    role_value, role_label = _infer_role_from_profile(raw_role=raw_role, unvan=unvan, birim=birim, ust_birim=ust_birim)
    return canonical_role_value(role_value), canonical_role_label(role_value)


def auto_apply_manager_chains(
    scope_users: Iterable[User] | None = None,
    *,
    fill_only_missing: bool = True,
    commit: bool = False,
    preserve_explicit_chain: bool = True,
) -> dict[str, Any]:
    users = User.query.order_by(User.id.asc()).all()
    normalized_targets = []
    for user in users:
        try:
            role_value, role_label = infer_role_from_profile(
                raw_role=getattr(user, 'role', None) or getattr(user, 'role_label', None),
                unvan=getattr(user, 'unvan', None),
                birim=getattr(user, 'birim', None),
                ust_birim=getattr(user, 'ust_birim', None),
            )
            if hasattr(user, 'role') and user.role != role_value:
                user.role = role_value
            if hasattr(user, 'role_label') and user.role_label != role_label:
                user.role_label = role_label
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/auto_hierarchy_service.py")
        normalized_targets.append(user)
    db.session.flush()
    lookup = build_lookup(normalized_targets)
    target_users = list(scope_users) if scope_users is not None else list(lookup.users)

    updated_count = 0
    skipped_count = 0
    warnings: list[str] = []

    for user in target_users:
        if is_system_user(user):
            continue

        if preserve_explicit_chain and has_explicit_manager_fields(user):
            skipped_count += 1
            continue

        # Otomatik yeniden kur akışında preserve_explicit_chain=False ise
        # eski / yanlış 3. amir alanları da temizlenebilmelidir.
        desired = resolve_authoritative_desired_chain(
            user,
            lookup,
            preserve_explicit_level3=preserve_explicit_chain,
            prefer_explicit_chain=preserve_explicit_chain,  # BYS360_EXPLICIT_MANAGER_CHAIN_V2
        )
        current_1 = (getattr(user, 'yonetici_sicil', None) or '').strip() or None
        current_2 = (getattr(user, 'ikinci_yonetici_sicil', None) or '').strip() or None
        current_3 = (getattr(user, 'ucuncu_yonetici_sicil', None) or '').strip() or None

        new_1 = current_1 if (fill_only_missing and current_1) else desired.manager_1_sicil
        new_2 = current_2 if (fill_only_missing and current_2) else desired.manager_2_sicil
        new_3 = current_3 if (fill_only_missing and current_3) else desired.manager_3_sicil

        if (new_1, new_2, new_3) == (current_1, current_2, current_3):
            skipped_count += 1
        else:
            user.yonetici_sicil = new_1
            user.ikinci_yonetici_sicil = new_2
            user.ucuncu_yonetici_sicil = new_3
            updated_count += 1

        display = (getattr(user, 'full_name', None) or f"{getattr(user, 'ad', '')} {getattr(user, 'soyad', '')}").strip() or f"#{getattr(user, 'id', '')}"
        for item in desired.warnings:
            warnings.append(f"{display}: {item}")

    db.session.flush()
    if commit:
        db.session.commit()

    return {
        'updated_count': updated_count,
        'skipped_count': skipped_count,
        'warnings': warnings,
    }