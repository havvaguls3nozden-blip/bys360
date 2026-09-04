from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any

from app.services.personnel_sync_service import canonical_role_value
from app.services.role_display import ROLE_DISPLAY_LABELS, UNKNOWN_ROLE_DISPLAY_LABEL

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

try:
    from app.models import User
except Exception:  # pragma: no cover
    __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/hierarchy_rulebook_service.py:23")
    User = Any  # type: ignore

TR_MAP = str.maketrans({
    'ç': 'c', 'Ç': 'c',
    'ğ': 'g', 'Ğ': 'g',
    'ı': 'i', 'I': 'i', 'İ': 'i',
    'ö': 'o', 'Ö': 'o',
    'ş': 's', 'Ş': 's',
    'ü': 'u', 'Ü': 'u',
})

HUKUK_UNIT_KEYS = {'hukuk musavirligi', 'sorumlu hukuk musavirligi'}
HUKUK_TITLE_KEYS = {'hukuk musavir', 'sorumlu hukuk musavir'}
DIRECT_TO_PRESIDENT_UNIT_KEYS = {'danismanlik', 'ozel kalem', 'ic denetim'}
DIRECT_TO_PRESIDENT_TITLE_KEYS = {'danisman', 'ozel kalem', 'ic denetci', 'ic denetim'}
SYSTEM_UNIT_KEYS = {'bys360'}


@dataclass(slots=True)
class DesiredChain:
    manager_1_sicil: str | None = None
    manager_2_sicil: str | None = None
    manager_3_sicil: str | None = None
    expected_levels: tuple[int, ...] = field(default_factory=tuple)
    explicit_level_3_requested: bool = False
    rule_code: str = ''
    info_notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Lookup:
    users: list[Any]
    by_sicil: dict[str, Any]
    by_role: dict[str, list[Any]]
    by_unit_role: dict[tuple[str, str], list[Any]]
    by_unit_parent_role: dict[tuple[str, str, str], list[Any]]
    president: Any | None
    vice_president: Any | None


def _safe(value: Any) -> str:
    return str(value or '').strip()


def _norm(value: Any) -> str:
    text = _safe(value).translate(TR_MAP).lower()
    return ' '.join(text.replace('_', ' ').split())


def _role(user: Any) -> str:
    raw_role = getattr(user, 'role', '') or getattr(user, 'role_label', '') or getattr(user, 'unvan', '')
    return canonical_role_value(raw_role)


def _sicil(user: Any) -> str:
    return _safe(getattr(user, 'sicil_no', ''))


def _is_active(user: Any) -> bool:
    return bool(user and getattr(user, 'is_active', False))


def _full_name(user: Any) -> str:
    if not user:
        return ''
    full_name = _safe(getattr(user, 'full_name', ''))
    if full_name:
        return full_name
    return f"{_safe(getattr(user, 'ad', ''))} {_safe(getattr(user, 'soyad', ''))}".strip()


def is_system_user(user: Any) -> bool:
    if not user:
        return True
    role = _role(user)
    role_label = _norm(getattr(user, 'role_label', ''))
    title = _norm(getattr(user, 'unvan', ''))
    email = _norm(getattr(user, 'email', ''))
    sicil_no = _norm(getattr(user, 'sicil_no', ''))
    if role == 'admin':
        return True
    if role_label in {'admin', 'sistem yoneticisi', 'system admin', 'system administrator', 'super admin', 'superadmin'}:
        return True
    if title in {'sistem yoneticisi', 'system admin', 'system administrator'}:
        return True
    if email.startswith('admin@') or email.startswith('system@') or email.startswith('sysadmin@'):
        return True
    if sicil_no in {'admin', 'system', 'sysadmin'}:
        return True
    if _norm(getattr(user, 'birim', '')) in SYSTEM_UNIT_KEYS:
        return True
    return _norm(getattr(user, 'ust_birim', '')) in SYSTEM_UNIT_KEYS


def is_president(user: Any) -> bool:
    role = _role(user)
    title = _norm(getattr(user, 'unvan', ''))
    return role == 'baskan' or title == 'baskan'


def is_vice_president(user: Any) -> bool:
    role = _role(user)
    title = _norm(getattr(user, 'unvan', ''))
    return role == 'baskan_yardimcisi' or 'baskan yardim' in title


def is_hukuk_context(user: Any) -> bool:
    birim = _norm(getattr(user, 'birim', ''))
    ust_birim = _norm(getattr(user, 'ust_birim', ''))
    title = _norm(getattr(user, 'unvan', ''))
    return (
        any(token in title for token in HUKUK_TITLE_KEYS)
        or any(token in birim for token in HUKUK_UNIT_KEYS)
        or any(token in ust_birim for token in HUKUK_UNIT_KEYS)
    )


def _has_explicit_hukuk_supervisor_hint(user: Any) -> bool:
    if not user:
        return False
    for field_name in ('yonetici_sicil', 'ikinci_yonetici_sicil', 'ucuncu_yonetici_sicil'):
        if _safe(getattr(user, field_name, '')):
            return True
    return False


def is_hukuk_chief(user: Any) -> bool:
    if not user or not is_hukuk_context(user):
        return False
    title = _norm(getattr(user, 'unvan', ''))
    role = _role(user)

    # En güvenli ayırım: kullanıcı kartında açık bir hukuk üstü tanımlıysa
    # bu kayıt başkana değil, o hukuk amirine bağlı ast kayıt olarak ele alınır.
    if _has_explicit_hukuk_supervisor_hint(user):
        return False

    # Sorumlu hukuk müşaviri başlıkları daima hukuk amiri kabul edilir.
    if 'sorumlu hukuk musavir' in title:
        return True

    # Kurumdaki mevcut veri yapısında plain "Hukuk Müşaviri" kayıtları bazen
    # role alanında mali_musavir'e normalize ediliyor. Açık üst bilgisi yoksa
    # bu kayıt hukuk amiri kabul edilir. Açık üst bilgisi olan kayıtlar yukarıda
    # zaten ast olarak ayrılmıştır.
    return role in {'mali_musavir', 'grup_baskani'} or any(token in title for token in HUKUK_TITLE_KEYS)


def is_hukuk_staff(user: Any) -> bool:
    return bool(
        user
        and is_hukuk_context(user)
        and not is_hukuk_chief(user)
        and not is_president(user)
        and not is_vice_president(user)
    )


def is_direct_to_president_role(user: Any) -> bool:
    if not user:
        return False
    birim = _norm(getattr(user, 'birim', ''))
    ust_birim = _norm(getattr(user, 'ust_birim', ''))
    title = _norm(getattr(user, 'unvan', ''))
    if any(key in title for key in DIRECT_TO_PRESIDENT_TITLE_KEYS):
        return True
    return birim in DIRECT_TO_PRESIDENT_UNIT_KEYS or ust_birim in DIRECT_TO_PRESIDENT_UNIT_KEYS


def infer_role_from_profile(*, raw_role: Any = None, unvan: Any = None, birim: Any = None, ust_birim: Any = None) -> tuple[str, str]:
    role = _norm(raw_role)
    title = _norm(unvan)
    unit = _norm(birim)
    parent = _norm(ust_birim)

    if role in {'admin', 'baskan', 'baskan yardimcisi', 'baskan_yardimcisi', 'grup baskani', 'grup_baskani', 'mali musavir', 'mali_musavir', 'koordinator', 'birim sorumlusu', 'birim_sorumlusu', 'personel'}:
        final = canonical_role_value(role)
        return final, role_label(final)

    if title == 'baskan' or ('baskan' in title and 'yardim' not in title):
        return 'baskan', role_label('baskan')
    if 'baskan yardim' in title:
        return 'baskan_yardimcisi', role_label('baskan_yardimcisi')
    if is_direct_title(title) or unit in DIRECT_TO_PRESIDENT_UNIT_KEYS:
        return 'birim_sorumlusu', role_label('birim_sorumlusu')
    if any(token in title for token in HUKUK_TITLE_KEYS):
        return 'mali_musavir', role_label('mali_musavir')
    if 'grup baskan' in title or (unit.endswith('grup baskanligi') and 'calisma grubu' not in unit):
        return 'grup_baskani', role_label('grup_baskani')
    if 'koordinator' in title:
        return 'koordinator', role_label('koordinator')
    if parent.endswith('grup baskanligi') and unit.endswith('calisma grubu'):
        return 'personel', role_label('personel')
    return 'personel', role_label('personel')


def is_direct_title(title: str) -> bool:
    return any(key in title for key in DIRECT_TO_PRESIDENT_TITLE_KEYS)


def role_label(value: str) -> str:
    if not value:
        return ''
    return ROLE_DISPLAY_LABELS.get(value, UNKNOWN_ROLE_DISPLAY_LABEL)


def build_lookup(users: Iterable[Any]) -> Lookup:
    pool = [u for u in users if _is_active(u) and not is_system_user(u)]
    by_sicil: dict[str, Any] = {}
    by_role: dict[str, list[Any]] = {}
    by_unit_role: dict[tuple[str, str], list[Any]] = {}
    by_unit_parent_role: dict[tuple[str, str, str], list[Any]] = {}
    for user in pool:
        sicil = _sicil(user)
        if sicil:
            by_sicil[sicil] = user
        role = _role(user)
        birim = _norm(getattr(user, 'birim', ''))
        ust = _norm(getattr(user, 'ust_birim', ''))
        by_role.setdefault(role, []).append(user)
        by_unit_role.setdefault((birim, role), []).append(user)
        by_unit_parent_role.setdefault((birim, ust, role), []).append(user)
    president = _pick_first(by_role.get('baskan', [])) or _pick_first([u for u in pool if is_president(u)])
    vice = _pick_first(by_role.get('baskan_yardimcisi', [])) or _pick_first([u for u in pool if is_vice_president(u)])
    return Lookup(
        users=pool,
        by_sicil=by_sicil,
        by_role=by_role,
        by_unit_role=by_unit_role,
        by_unit_parent_role=by_unit_parent_role,
        president=president,
        vice_president=vice,
    )


def _pick_first(users: Iterable[Any]) -> Any | None:
    ordered = sorted(
        list(users),
        key=lambda u: (
            0 if _is_active(u) else 1,
            _norm(getattr(u, 'unvan', '')),
            _full_name(u).lower(),
            _sicil(u),
        ),
    )
    return ordered[0] if ordered else None


def _same_user(a: Any, b: Any) -> bool:
    return bool(a and b and getattr(a, 'id', None) == getattr(b, 'id', None))


def find_group_head(user: Any, lookup: Lookup) -> Any | None:
    ust = _norm(getattr(user, 'ust_birim', ''))
    if not ust:
        return None
    return (
        _pick_first(lookup.by_unit_role.get((ust, 'grup_baskani'), []))
        or _pick_first(lookup.by_unit_role.get((ust, 'mali_musavir'), []))
    )


def find_coordinator(user: Any, lookup: Lookup) -> Any | None:
    birim = _norm(getattr(user, 'birim', ''))
    ust = _norm(getattr(user, 'ust_birim', ''))
    return (
        _pick_first(lookup.by_unit_parent_role.get((birim, ust, 'koordinator'), []))
        or _pick_first(lookup.by_unit_role.get((birim, 'koordinator'), []))
    )


def find_hukuk_chief(user: Any, lookup: Lookup) -> Any | None:
    birim = _norm(getattr(user, 'birim', ''))
    ust = _norm(getattr(user, 'ust_birim', ''))
    candidates: list[Any] = []
    candidates.extend(lookup.by_unit_parent_role.get((birim, ust, 'mali_musavir'), []))
    candidates.extend(lookup.by_unit_role.get((birim, 'mali_musavir'), []))
    candidates.extend(lookup.by_unit_parent_role.get((birim, ust, 'grup_baskani'), []))
    candidates.extend(lookup.by_unit_role.get((birim, 'grup_baskani'), []))
    filtered = [u for u in candidates if is_hukuk_chief(u) and not _same_user(u, user)]
    chief = _pick_first(filtered)
    if chief:
        return chief
    filtered = [u for u in lookup.users if is_hukuk_chief(u) and not _same_user(u, user)]
    return _pick_first(filtered)


def find_hukuk_supervisor(user: Any, lookup: Lookup) -> Any | None:
    """
    Aynı hukuk yapısında bir hukuk müşaviri başka bir hukuk müşavirine bağlıysa,
    kurum kuralına göre tek amirli çalışır. Bu nedenle kullanıcı kartındaki açık
    amir alanlarında geçen hukuk üstünü öncelikle ararız.
    """
    if not user or not is_hukuk_context(user):
        return None
    for field_name in ('yonetici_sicil', 'ikinci_yonetici_sicil', 'ucuncu_yonetici_sicil'):
        sicil = _safe(getattr(user, field_name, ''))
        if not sicil:
            continue
        candidate = lookup.by_sicil.get(sicil)
        if not candidate or not _is_active(candidate) or is_system_user(candidate) or _same_user(candidate, user):
            continue
        if is_hukuk_chief(candidate) or is_hukuk_context(candidate):
            return candidate
    return None


def resolve_explicit_level3(user: Any, lookup: Lookup, current_sicil: Any, desired_1: str | None, desired_2: str | None) -> str | None:
    sicil = _safe(current_sicil)
    if not sicil:
        return None
    candidate = lookup.by_sicil.get(sicil)
    if not candidate or is_system_user(candidate) or not _is_active(candidate):
        return None
    if _same_user(candidate, user):
        return None
    if sicil in {desired_1, desired_2}:
        return None
    return sicil


def _attach_explicit_level3(result: DesiredChain, user: Any, lookup: Lookup, *, preserve_explicit_level3: bool = True) -> DesiredChain:
    """
    Excel veya manuel kartta açıkça seçilmiş 3. amiri korur.

    Bu kural sadece çalışma grubu personeli için değil, anayasanın izin verdiği
    koordinatör ve grup başkanı / mali müşavir seviyeleri için de geçerlidir.
    Son zipteki kırılma, fonksiyonun yalnızca genel personel kolunda çağrılmasıydı;
    bu yüzden Excel'de dolu olan 3. amir bazı rollerde sessizce düşüyordu.
    """
    if not preserve_explicit_level3:
        return result

    explicit_raw = _safe(getattr(user, 'ucuncu_yonetici_sicil', None))
    if not explicit_raw:
        return result

    result.explicit_level_3_requested = True
    resolved = resolve_explicit_level3(
        user,
        lookup,
        explicit_raw,
        result.manager_1_sicil,
        result.manager_2_sicil,
    )
    result.manager_3_sicil = resolved
    if resolved:
        if 3 not in result.expected_levels:
            result.expected_levels = tuple(list(result.expected_levels) + [3])
    else:
        result.warnings.append('3. amir tanımlı ancak geçersiz/pasif.')
    return result


def desired_manager_sicils(user: Any, lookup: Lookup, *, preserve_explicit_level3: bool = True) -> DesiredChain:
    role = _role(user)
    result = DesiredChain()

    if is_president(user):
        result.rule_code = 'president_excluded'
        result.info_notes.append('Başkan performans değerlendirme zincirine dahil edilmez.')
        return result

    president = lookup.president
    vice = lookup.vice_president

    if is_vice_president(user):
        result.manager_1_sicil = _sicil(president) if president and not _same_user(president, user) else None
        result.expected_levels = (1,)
        result.rule_code = 'vice_president_single'
        if not result.manager_1_sicil:
            result.warnings.append('Başkan bulunamadı.')
        return result

    if is_direct_to_president_role(user):
        result.manager_1_sicil = _sicil(president) if president and not _same_user(president, user) else None
        result.expected_levels = (1,)
        result.rule_code = 'direct_president_single'
        result.info_notes.append('Özel başkanlık birimi tek amir kuralı uygulandı.')
        if not result.manager_1_sicil:
            result.warnings.append('Başkan bulunamadı.')
        return result

    hukuk_supervisor = find_hukuk_supervisor(user, lookup) if is_hukuk_context(user) else None
    if hukuk_supervisor:
        result.manager_1_sicil = _sicil(hukuk_supervisor) if not _same_user(hukuk_supervisor, user) else None
        result.expected_levels = (1,)
        result.rule_code = 'hukuk_supervised_single'
        result.info_notes.append('Hukuk Müşavirliği ast-üst tek amir kuralı uygulandı.')
        if not result.manager_1_sicil:
            result.warnings.append('Hukuk Müşaviri bulunamadı.')
        return result

    if is_hukuk_chief(user):
        # Kalıcı özel istisna:
        # Hukuk müşaviri / sorumlu hukuk müşaviri için slot yapısı
        # 1. amir = Başkan, 2. amir = Başkan Yardımcısıdır.
        # İşlem sırası yine 2 -> 1 olarak çalışır; yani önce 2. amir, sonra 1. amir.
        result.manager_1_sicil = _sicil(president) if president and not _same_user(president, user) else None
        result.manager_2_sicil = _sicil(vice) if vice and not _same_user(vice, user) else None
        result.expected_levels = (1, 2)
        result.rule_code = 'hukuk_chief_presidency_override'
        result.info_notes.append('Hukuk müşaviri için özel başkanlık istisnası uygulandı.')
        if not result.manager_1_sicil:
            result.warnings.append('Başkan bulunamadı.')
        if not result.manager_2_sicil:
            result.warnings.append('Başkan Yardımcısı bulunamadı.')
        return result

    if role in {'grup_baskani', 'mali_musavir'}:
        # Grup Başkanı / Mali Müşavir slot yapısı:
        # 1. amir = Başkan, 2. amir = Başkan Yardımcısıdır.
        # İşlem sırası yine 2 -> 1 olarak çalışır; yani önce 2. amir, sonra 1. amir.
        result.manager_1_sicil = _sicil(president) if president and not _same_user(president, user) else None
        result.manager_2_sicil = _sicil(vice) if vice and not _same_user(vice, user) else None
        result.expected_levels = (1, 2)
        result.rule_code = 'department_head_2_1'
        result = _attach_explicit_level3(result, user, lookup, preserve_explicit_level3=preserve_explicit_level3)
        if not result.manager_1_sicil:
            result.warnings.append('Başkan bulunamadı.')
        if not result.manager_2_sicil:
            result.warnings.append('Başkan Yardımcısı bulunamadı.')
        return result

    if role == 'koordinator':
        group_head = find_group_head(user, lookup)
        # Nihai anayasa matrisi:
        # Koordinatörün 1. amiri Başkan Yardımcısı, 2. amiri Grup Başkanıdır.
        # İşlem sırası yine 2 -> 1 olarak çalışır; yani önce Grup Başkanı, sonra Başkan Yardımcısı ilerler.
        result.manager_1_sicil = _sicil(vice) if vice and not _same_user(vice, user) else None
        result.manager_2_sicil = _sicil(group_head) if group_head and not _same_user(group_head, user) else None
        result.expected_levels = (1, 2)
        result.rule_code = 'coordinator_2_1'
        result.info_notes.append('Koordinatör zinciri anayasa matrisine göre 1=Başkan Yardımcısı, 2=Grup Başkanı olarak sabitlendi.')
        result = _attach_explicit_level3(result, user, lookup, preserve_explicit_level3=preserve_explicit_level3)
        if not result.manager_1_sicil:
            result.warnings.append('Başkan Yardımcısı bulunamadı.')
        if not result.manager_2_sicil:
            result.warnings.append('Grup Başkanı bulunamadı.')
        return result

    if is_hukuk_staff(user):
        chief = find_hukuk_chief(user, lookup)
        result.manager_1_sicil = _sicil(chief) if chief and not _same_user(chief, user) else None
        result.expected_levels = (1,)
        result.rule_code = 'hukuk_staff_single'
        result.info_notes.append('Hukuk personeli tek amir kuralı uygulandı.')
        if not result.manager_1_sicil:
            result.warnings.append('Hukuk Müşaviri bulunamadı.')
        return result

    group_head = find_group_head(user, lookup)
    coordinator = find_coordinator(user, lookup)
    # Nihai matris:
    # Çalışma grubu personelinde 1. amir Grup Başkanı, 2. amir Koordinatördür.
    # Açık bir 3. amir varsa yalnızca ayrıca istenir; akış slotları değişmez.
    result.manager_1_sicil = _sicil(group_head) if group_head and not _same_user(group_head, user) else None
    result.manager_2_sicil = _sicil(coordinator) if coordinator and not _same_user(coordinator, user) else None
    result.expected_levels = (1, 2)
    result.rule_code = 'general_staff_3_2_1'
    result.info_notes.append('Çalışma grubu personeli zinciri anayasa matrisine göre 1=Grup Başkanı, 2=Koordinatör olarak sabitlendi.')
    result = _attach_explicit_level3(result, user, lookup, preserve_explicit_level3=preserve_explicit_level3)
    if not result.manager_1_sicil:
        result.warnings.append('Grup Başkanı bulunamadı.')
    if not result.manager_2_sicil:
        result.warnings.append('Koordinatör bulunamadı.')
    return result
