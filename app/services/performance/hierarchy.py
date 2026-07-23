from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

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

from collections.abc import (  # noqa: E402 - deferred import (staged facade/route-registration architecture)
    Iterable,  # noqa: E402 - deferred import (staged facade/route-registration architecture)
)
from dataclasses import (  # noqa: E402 - deferred import (staged facade/route-registration architecture)
    dataclass,  # noqa: E402 - deferred import (staged facade/route-registration architecture)
)
from types import (  # noqa: E402 - deferred import (staged facade/route-registration architecture)
    SimpleNamespace,  # noqa: E402 - deferred import (staged facade/route-registration architecture)
)
from typing import (  # noqa: E402 - deferred import (staged facade/route-registration architecture)
    Any,  # noqa: E402 - deferred import (staged facade/route-registration architecture)
)

try:
    import app.models as models
except Exception:  # pragma: no cover
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    models = None

User = getattr(models, "User", None) if models else None

from .reason_codes import (  # noqa: E402 - deferred import (staged facade/route-registration architecture)
    is_informational_reason,
    reason_payload,
)

ROLE_ORDER = {
    "baskan": 1,
    "baskan_yardimcisi": 2,
    "grup_baskani": 3,
    "koordinator": 4,
    "birim_amiri": 5,
    "birim_sorumlusu": 5,
    "personel": 6,
    "admin": 99,
}

SPECIAL_SINGLE_MANAGER_UNITS = {
    "DANIŞMANLIK",
    "DANISMANLIK",
    "İÇ DENETİM",
    "IC DENETIM",
    "ÖZEL KALEM",
    "OZEL KALEM",
}


@dataclass
class ChainResult:
    employee_id: int | None
    employee_name: str
    manager_1_id: int | None
    manager_2_id: int | None
    manager_3_id: int | None
    manager_1_sicil: str = ""
    manager_2_sicil: str = ""
    manager_3_sicil: str = ""
    manager_1_name: str = ""
    manager_2_name: str = ""
    manager_3_name: str = ""
    warnings: list[str] | None = None
    flow_order: list[int] | None = None
    is_single_manager_case: bool = False


def _s(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _role(value: Any) -> str:
    raw = _s(value).lower().replace('ı', 'i').replace('İ', 'i')
    mapping = {
        'başkan': 'baskan', 'baskan': 'baskan',
        'başkan yardımcısı': 'baskan_yardimcisi', 'baskan yardimcisi': 'baskan_yardimcisi', 'baskan_yardimcisi': 'baskan_yardimcisi',
        'grup başkanı': 'grup_baskani', 'grup baskani': 'grup_baskani', 'grup_baskani': 'grup_baskani',
        'mali müşavir': 'mali_musavir', 'mali musavir': 'mali_musavir', 'mali_musavir': 'mali_musavir',
        'koordinatör': 'koordinator', 'koordinator': 'koordinator',
        'birim amiri': 'birim_sorumlusu', 'birim sorumlusu': 'birim_sorumlusu', 'birim_sorumlusu': 'birim_sorumlusu',
        'personel': 'personel', 'admin': 'admin',
    }
    return mapping.get(raw, raw.replace(' ', '_'))


def _get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return getattr(value, key, default)


def _full_name(user: Any) -> str:
    if not user:
        return ""
    if isinstance(user, dict):
        full_name = _s(user.get("full_name"))
        if full_name:
            return full_name
        return f"{_s(user.get('ad'))} {_s(user.get('soyad'))}".strip()
    full_name = _s(getattr(user, "full_name", ""))
    if full_name:
        return full_name
    return f"{_s(getattr(user, 'ad', ''))} {_s(getattr(user, 'soyad', ''))}".strip()


def _ensure_iterable(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def _effective_level_3_mode(subject: Any, level_mode: str) -> str:
    explicit_level_3 = _s(_get(subject, 'ucuncu_yonetici_sicil', '') or _get(subject, 'manager_3', ''))
    normalized = _s(level_mode).lower()
    if explicit_level_3 and normalized in {'', 'off', 'disabled'}:
        return 'comment_only'
    return normalized or 'comment_only'


def fetch_active_users() -> list[Any]:
    if not User:
        return []
    query = User.query
    if hasattr(User, "is_active"):
        query = query.filter_by(is_active=True)
    rows = query.order_by(User.id.asc()).all()
    try:
        from app.services.hierarchy_rulebook_service import is_system_user
        rows = [row for row in rows if not is_system_user(row)]
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        import logging
        logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/hierarchy.py")
    return rows


def build_user_maps(users: list[Any]) -> tuple[dict[int, Any], dict[str, Any]]:
    by_id: dict[int, Any] = {}
    by_sicil: dict[str, Any] = {}
    for user in users:
        user_id = _get(user, "id", None)
        if user_id is not None:
            by_id[user_id] = user
        sicil = _s(_get(user, "sicil_no", ""))
        if sicil:
            by_sicil[sicil] = user
    return by_id, by_sicil


def is_single_manager_case(user: Any) -> bool:
    birim = _s(_get(user, "birim", "")).upper()
    role = _role(_get(user, "role", ""))
    if role == "baskan":
        return True
    if birim in SPECIAL_SINGLE_MANAGER_UNITS:
        return True

    # Hukuk Müşavirliği özel kuralı:
    # Aynı hukuk yapısında açık hukuk üstü olan kayıtlar tek amirlidir.
    if "HUKUK" in birim or "MÜŞAV" in birim or "MUSAV" in birim:
        m1 = _s(_get(user, "yonetici_sicil", "") or _get(user, "manager_1", ""))
        m2 = _s(_get(user, "ikinci_yonetici_sicil", "") or _get(user, "manager_2", ""))
        m3 = _s(_get(user, "ucuncu_yonetici_sicil", "") or _get(user, "manager_3", ""))
        if m1 and not m2 and not m3:
            return True
        if role == "personel":
            return True
    return False


def flow_order_for(user: Any, has_third: bool = False) -> list[int]:
    """
    Slot != işlem sırası.
    1. amir slotu kurumsal amirdir.
    İşlem sırası:
    - Başkanlık: 2 -> 1
    - Grup/çalışma grubu: varsa 3 -> 2 -> 1, yoksa 2 -> 1
    """
    role = _role(_get(user, "role", ""))
    birim = _s(_get(user, "birim", "")).upper()
    ust_birim = _s(_get(user, "ust_birim", "")).upper()

    if role == "baskan":
        return []
    if role == "baskan_yardimcisi":
        return [1]
    if birim == "BAŞKANLIK" or ust_birim == "BAŞKANLIK":
        return [2, 1]
    if has_third:
        return [3, 2, 1]
    return [2, 1]


def resolve_manager_chain(user: Any, by_sicil: dict[str, Any]) -> ChainResult:
    warnings: list[str] = []
    single_case = is_single_manager_case(user)
    role = _role(_get(user, "role", ""))

    m1_sicil = _s(_get(user, "yonetici_sicil", "") or _get(user, "manager_1", ""))
    m2_sicil = _s(_get(user, "ikinci_yonetici_sicil", "") or _get(user, "manager_2", ""))
    m3_sicil = _s(_get(user, "ucuncu_yonetici_sicil", "") or _get(user, "manager_3", ""))

    m1 = by_sicil.get(m1_sicil)
    m2 = by_sicil.get(m2_sicil)
    m3 = by_sicil.get(m3_sicil)

    if not m1_sicil and not single_case:
        warnings.append("1. amir eksik veya pasif")
    elif m1_sicil and not m1:
        warnings.append(f"1. amir bulunamadı: {m1_sicil}")

    if role != "baskan_yardimcisi" and not single_case:
        if not m2_sicil:
            warnings.append("2. amir eksik veya pasif")
        elif not m2:
            warnings.append(f"2. amir bulunamadı: {m2_sicil}")

    if m3_sicil and not m3:
        warnings.append(f"3. amir bulunamadı: {m3_sicil}")

    user_id = _get(user, "id", None)
    if m1 and _get(m1, "id", None) == user_id:
        warnings.append("Kişi kendisine 1. amir atanmış.")
        m1 = None
    if m2 and _get(m2, "id", None) == user_id:
        warnings.append("Kişi kendisine 2. amir atanmış.")
        m2 = None
    if m3 and _get(m3, "id", None) == user_id:
        warnings.append("Kişi kendisine 3. amir atanmış.")
        m3 = None

    return ChainResult(
        employee_id=user_id,
        employee_name=_full_name(user),
        manager_1_id=_get(m1, "id", None) if m1 else None,
        manager_2_id=_get(m2, "id", None) if m2 else None,
        manager_3_id=_get(m3, "id", None) if m3 else None,
        manager_1_sicil=m1_sicil,
        manager_2_sicil=m2_sicil,
        manager_3_sicil=m3_sicil,
        manager_1_name=_full_name(m1),
        manager_2_name=_full_name(m2),
        manager_3_name=_full_name(m3),
        warnings=warnings,
        flow_order=flow_order_for(user, bool(m3_sicil)),
        is_single_manager_case=single_case,
    )


def build_manager_chain_for_user(user: Any = None, users_by_sicil: dict[str, Any] | None = None, period: Any = None, employee: Any = None):
    """
    Geriye dönük uyumluluk katmanı.

    Eski çağrılar `build_manager_chain_for_user(user)` ve
    yeni çağrılar `build_manager_chain_for_user(employee=..., period=...)`
    biçiminde gelebiliyor. Ayrıca bazı ekranlar dict, bazı ekranlar ise
    öznitelik erişimli nesne bekliyor. Bu nedenle burada tek bir uyumlu
    nesne döndürüyoruz.
    """

    subject = employee if employee is not None else user
    if subject is None:
        return None

    try:
        from app.services.performance.hierarchy_stable import (
            build_manager_chain_for_user as _stable_build_manager_chain_for_user,
            build_user_maps as _stable_build_user_maps,
            fetch_active_users as _stable_fetch_active_users,
        )

        stable_users = _stable_fetch_active_users()
        _, stable_by_sicil = _stable_build_user_maps(stable_users)
        stable_chain = _stable_build_manager_chain_for_user(subject, stable_by_sicil, period)

        raw_issues = list(getattr(stable_chain, 'issues', []) or [])
        issue_items = [reason_payload(item) for item in raw_issues]
        issue_messages = [item.get('message', '') for item in issue_items if item.get('message')]
        info_note_items = [item for item in issue_items if is_informational_reason(item)]
        info_notes = [item.get('message', '') for item in info_note_items if item.get('message')]
        level_mode = 'comment_only'
        if period is not None:
            level_mode = str(getattr(period, 'level_3_mode', '') or '').strip().lower() or level_mode
            if level_mode not in {'comment_only', 'yorumcu', 'scoring', 'off', 'disabled'}:
                if bool(getattr(period, 'enable_level_3_scoring', False)):
                    level_mode = 'scoring'
                elif bool(getattr(period, 'enable_level_3', False)):
                    level_mode = 'comment_only'
                else:
                    level_mode = 'comment_only'

        manager_3_id = getattr(stable_chain, 'manager_3_id', None)
        level_mode = _effective_level_3_mode(subject, level_mode if manager_3_id else level_mode)
        return SimpleNamespace(
            employee_id=getattr(stable_chain, 'employee_id', None),
            employee_name=getattr(stable_chain, 'employee_name', ''),
            manager_1_id=getattr(stable_chain, 'manager_1_id', None),
            manager_2_id=getattr(stable_chain, 'manager_2_id', None),
            manager_3_id=manager_3_id,
            manager_1_name=getattr(stable_chain, 'manager_1_name', ''),
            manager_2_name=getattr(stable_chain, 'manager_2_name', ''),
            manager_3_name=getattr(stable_chain, 'manager_3_name', ''),
            manager_1_sicil=_s(getattr(subject, 'yonetici_sicil', '') or getattr(subject, 'manager_1', '')),
            manager_2_sicil=_s(getattr(subject, 'ikinci_yonetici_sicil', '') or getattr(subject, 'manager_2', '')),
            manager_3_sicil=_s(getattr(subject, 'ucuncu_yonetici_sicil', '') or getattr(subject, 'manager_3', '')),
            flow_order=list(getattr(stable_chain, 'flow_order', tuple()) or tuple()),
            issues=issue_messages,
            issue_items=issue_items,
            info_notes=info_notes,
            info_note_items=info_note_items,
            effective_severity='info' if info_note_items else ('critical' if any((item.get('code') == 'self_manager') for item in issue_items) else ('warning' if issue_messages else 'success')),
            is_single_manager_case=bool(getattr(stable_chain, 'manager_1_id', None) and not getattr(stable_chain, 'manager_2_id', None) and not manager_3_id),
            level_3_enabled=bool(manager_3_id) and level_mode not in {'off', 'disabled'},
            level_3_mode=level_mode,
        )
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        users = fetch_active_users()
        _, by_sicil = build_user_maps(users)
        chain = resolve_manager_chain(subject, by_sicil)
        fallback_level_mode = _effective_level_3_mode(subject, 'comment_only' if chain.manager_3_id else 'disabled')
        return SimpleNamespace(
            employee_id=chain.employee_id,
            employee_name=chain.employee_name,
            manager_1_id=chain.manager_1_id,
            manager_2_id=chain.manager_2_id,
            manager_3_id=chain.manager_3_id,
            manager_1_sicil=chain.manager_1_sicil,
            manager_2_sicil=chain.manager_2_sicil,
            manager_3_sicil=chain.manager_3_sicil,
            manager_1_name=chain.manager_1_name,
            manager_2_name=chain.manager_2_name,
            manager_3_name=chain.manager_3_name,
            flow_order=chain.flow_order or [],
            issues=chain.warnings or [],
            info_notes=[],
            effective_severity='info' if chain.is_single_manager_case else ('critical' if chain.warnings else 'success'),
            is_single_manager_case=chain.is_single_manager_case,
            level_3_enabled=bool(chain.manager_3_id) and fallback_level_mode not in {'off', 'disabled'},
            level_3_mode=fallback_level_mode,
        )


def build_all_manager_chains(users: list[Any] | None = None) -> list[ChainResult]:
    users = users or fetch_active_users()
    _, by_sicil = build_user_maps(users)
    return [resolve_manager_chain(user, by_sicil) for user in users]


def build_org_tree_from_units(users: list[Any] | None = None) -> dict[str, Any]:
    users = users or fetch_active_users()
    normalized = []
    for user in users:
        normalized.append(
            {
                "id": _get(user, "id", None),
                "name": _full_name(user),
                "role": _role(_get(user, "role", "")),
                "role_label": _s(_get(user, "role_label", "")) or _role(_get(user, "role", "")).title(),
                "sicil_no": _s(_get(user, "sicil_no", "")),
                "birim": _s(_get(user, "birim", "")) or "Belirsiz Çalışma Grubu",
                "ust_birim": _s(_get(user, "ust_birim", "")) or "Belirsiz Grup Başkanlığı",
                "unvan": _s(_get(user, "unvan", "")),
            }
        )

    baskanlar = [u for u in normalized if u["role"] == "baskan"]
    baskan_yardimcilari = [u for u in normalized if u["role"] == "baskan_yardimcisi"]
    grup_baskanlari = [u for u in normalized if u["role"] == "grup_baskani"]
    digerleri = [u for u in normalized if u["role"] not in {"baskan", "baskan_yardimcisi", "grup_baskani"}]

    def sort_people(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return sorted(items, key=lambda x: (ROLE_ORDER.get(x["role"], 50), x["name"].lower(), x["sicil_no"]))

    group_map: dict[str, dict[str, Any]] = {}
    for gb in grup_baskanlari:
        grup_name = gb["birim"] or gb["ust_birim"] or "Belirsiz Grup Başkanlığı"
        group_map.setdefault(grup_name, {"manager": gb, "work_groups": {}})

    for person in digerleri:
        ust_birim = person["ust_birim"] or "Belirsiz Grup Başkanlığı"
        birim = person["birim"] or "Belirsiz Çalışma Grubu"
        group_map.setdefault(ust_birim, {"manager": None, "work_groups": {}})
        group_map[ust_birim]["work_groups"].setdefault(birim, {"coordinator": None, "people": []})
        if person["role"] == "koordinator" and not group_map[ust_birim]["work_groups"][birim]["coordinator"]:
            group_map[ust_birim]["work_groups"][birim]["coordinator"] = person
        else:
            group_map[ust_birim]["work_groups"][birim]["people"].append(person)

    group_clusters = []
    for grup_name, payload in sorted(group_map.items(), key=lambda x: x[0].lower()):
        work_groups = []
        for work_name, work_data in sorted(payload["work_groups"].items(), key=lambda x: x[0].lower()):
            work_groups.append({
                "group_name": work_name,
                "coordinator": work_data["coordinator"],
                "people": sort_people(work_data["people"]),
            })
        group_clusters.append({"group_name": grup_name, "manager": payload["manager"], "work_groups": work_groups})

    return {
        "baskanlar": sort_people(baskanlar),
        "baskan_yardimcilari": sort_people(baskan_yardimcilari),
        "grup_baskanlari": sort_people(grup_baskanlari),
        "group_clusters": group_clusters,
    }


def build_assignment_rows(users: Iterable[Any] | None = None) -> list[dict[str, Any]]:
    source_users = list(_ensure_iterable(users)) if users is not None else fetch_active_users()
    _, by_sicil = build_user_maps(source_users if users is None else fetch_active_users())
    rows: list[dict[str, Any]] = []
    for user in source_users:
        chain = resolve_manager_chain(user, by_sicil)
        rows.append(
            {
                "user": user,
                "chain": {
                    "manager_1": chain.manager_1_sicil,
                    "manager_2": chain.manager_2_sicil,
                    "manager_3": chain.manager_3_sicil,
                    "manager_1_name": chain.manager_1_name,
                    "manager_2_name": chain.manager_2_name,
                    "manager_3_name": chain.manager_3_name,
                    "flow_order": chain.flow_order or [],
                },
                "issues": chain.warnings or [],
                "warnings": [],
                "effective_weights": {"evaluator_1_weight": 50.0, "evaluator_2_weight": 50.0, "evaluator_3_weight": 0.0},
                "is_single_manager_case": chain.is_single_manager_case,
                "effective_severity": "info" if chain.is_single_manager_case else ("critical" if chain.warnings else "success"),
            }
        )
    return rows


def _coerce_user_source(source: Iterable[Any] | None = None) -> list[Any] | None:
    """`analyze_hierarchy_rows(period_id)` gibi hatalı/eski çağrıları tolere et."""
    if source is None:
        return None
    if isinstance(source, int):
        return None
    if isinstance(source, (str, bytes)):
        return None
    if hasattr(source, 'all'):
        try:
            return list(source.all())
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            return None
    if isinstance(source, (list, tuple, set)):
        return list(source)
    return None


def _real_issue_messages(chain: Any) -> list[str]:
    messages: list[str] = []
    issue_items = list(getattr(chain, 'issue_items', []) or [])
    if issue_items:
        for raw in issue_items:
            payload = reason_payload(raw)
            msg = payload.get('message') or ''
            if not msg or is_informational_reason(payload):
                continue
            messages.append(msg)
        return messages

    for raw in list(getattr(chain, 'issues', []) or []):
        payload = reason_payload(raw)
        msg = payload.get('message') or ''
        if not msg or is_informational_reason(payload):
            continue
        messages.append(msg)
    return messages


def analyze_hierarchy_rows(users: Iterable[Any] | None = None) -> list[dict[str, Any]]:
    """Seçili kullanıcı kümesi için yönetici zinciri analiz satırlarını üretir.

    Dönen her kayıt; kullanıcı nesnesi, çözülmüş zincir, gerçek aksiyon gerektiren
    issue listesi, bilgi notları ve ekranların doğrudan kullanabildiği özet alanları
    içerir. Route katmanının zincir çözümleme ayrıntılarını tekrar kurmasına gerek
    bırakmayan ana okuma sözleşmesidir.
    """
    source_users = _coerce_user_source(users) or fetch_active_users()
    rows: list[dict[str, Any]] = []
    for user in source_users:
        chain = build_manager_chain_for_user(user=user)
        real_issues = _real_issue_messages(chain)
        info_note_items = list(getattr(chain, 'info_note_items', []) or [])
        if not info_note_items:
            info_note_items = [
                reason_payload(item)
                for item in list(getattr(chain, 'info_notes', []) or [])
                if _s(reason_payload(item).get('message'))
            ]
        info_notes = [item.get('message', '') for item in info_note_items if item.get('message')]

        severity = 'critical' if real_issues else ('info' if info_notes or bool(getattr(chain, 'is_single_manager_case', False)) else 'success')

        rows.append(
            {
                'user': user,
                'employee_id': getattr(chain, 'employee_id', _get(user, 'id', None)),
                'employee_name': getattr(chain, 'employee_name', _full_name(user)),
                'chain': chain,
                'issues': real_issues,
                'issue_items': [reason_payload(item) for item in list(getattr(chain, 'issue_items', []) or [])],
                'warnings': [],
                'info_notes': info_notes,
                'info_note_items': info_note_items,
                'effective_weights': {'evaluator_1_weight': 50.0, 'evaluator_2_weight': 50.0, 'evaluator_3_weight': 0.0},
                'has_level_3': bool(getattr(chain, 'manager_3_id', None)),
                'is_single_manager_case': bool(getattr(chain, 'is_single_manager_case', False)),
                'effective_severity': severity,
            }
        )
    return rows


def analyze_hierarchy_gaps(users: Iterable[Any] | None = None) -> list[dict[str, Any]]:
    """Yalnızca aksiyon gerektiren zincir boşluklarını döndürür.

    Bilgi notları ve özel tek amir senaryoları bu filtreye dahil edilmez; sonuç
    özellikle görev üretimi, ön kontrol ve yönetici uyarı panellerinde kullanılmak
    üzere daraltılmış gerçek sorun listesidir.
    """
    return [row for row in analyze_hierarchy_rows(users) if list(row.get('issues') or [])]


def get_hierarchy_assignment_rows(users: Iterable[Any] | None = None) -> list[dict[str, Any]]:
    return analyze_hierarchy_rows(users)
