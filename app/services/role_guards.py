"""BYS360 ortak rol ve görünürlük yardımcıları.

SP route dosyalarındaki _role_name / _is_top_or_manager tekrarını tek merkezde
azaltmak için oluşturuldu. Bu dosya veri erişim yetkisini tek başına vermez;
menü/route görünürlüğü için ortak karar yardımcısıdır.
"""
from __future__ import annotations

from typing import Any

# BYS360_MAINTENANCE_10E_ROLE_GUARDS

# BYS360 DEFECT AQ: bu küme önceden TOP_OR_MANAGER_TOKENS adlı kısmi/parça
# jeton listesiyle "token in role" alt dize eşleştirmesi için kullanılıyordu
# -- bare "ik" (2 karakter) jetonu "Teknik Personel" gibi ilgisiz bir unvanı
# ("tekn-ik") da eşleştiriyordu, "baskan" jetonu ise phase6'nın kendi
# yorumunun uyardığı "Başkanlığı Uzmanı" tarzı görünüşte-benzer unvanları da
# kapsıyordu. Her jetonun karşılık geldiği kanonik rol koduna TAM eşleşme
# yapılır artık (kapsam daraltılmadı/genişletilmedi -- aynı 10 jetonun
# kendi kanonik karşılığı listelenir). "admin", "baskan", "baskan_
# yardimcisi", "grup_baskani", "mali_musavir", "koordinator",
# "birim_sorumlusu" alt kümesi zaten app/main_handlers/comparison_handlers.py
# ve app/institutional/hr_scope_helpers.py'de aynen kullanılan, kanıtlanmış
# kanonik "yönetici katmanı" kümesidir.
TOP_OR_MANAGER_ROLES = frozenset({
    "admin",
    "sistem_yoneticisi",
    "baskan",
    "baskan_yardimcisi",
    "grup_baskani",
    "koordinator",
    "performans_yetkilisi",
    "ik",
    "mali_musavir",
    "birim_sorumlusu",
})


def role_name(user: Any) -> str:
    role = getattr(user, "role", None) or getattr(user, "role_name", None) or ""
    return str(role).strip().lower()


def is_authenticated_user(user: Any) -> bool:
    return bool(user and getattr(user, "is_authenticated", False))


def is_top_or_manager(user: Any) -> bool:
    if not is_authenticated_user(user):
        return False
    role = role_name(user)
    return (
        role in TOP_OR_MANAGER_ROLES
        or bool(getattr(user, "is_admin", False))
        or bool(getattr(user, "is_superuser", False))
    )


def can_view_strategic_performance(user: Any) -> bool:
    return is_top_or_manager(user)


def can_manage_strategic_targets(user: Any) -> bool:
    return is_top_or_manager(user)
