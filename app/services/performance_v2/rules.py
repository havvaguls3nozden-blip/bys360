from __future__ import annotations



import logging
from dataclasses import dataclass
from typing import Iterable
import unicodedata

from .dto import ChainType, LevelMode, SubjectType
from .policy_flags import score_requires_criterion_comment
logger = logging.getLogger(__name__)


HUKUK_UNIT_KEYS = ('hukuk musavirligi', 'sorumlu hukuk musavirligi')
HUKUK_TITLE_KEYS = ('hukuk musavir', 'sorumlu hukuk musavir')


def _is_hukuk_context(employee) -> bool:
    blob = ' | '.join(
        _fold(getattr(employee, attr, ''))
        for attr in ('role', 'role_label', 'unvan', 'birim', 'ust_birim')
    )
    return any(token in blob for token in HUKUK_TITLE_KEYS) or any(token in blob for token in HUKUK_UNIT_KEYS)


def _has_explicit_manager_hint(employee) -> bool:
    return any(
        str(getattr(employee, field_name, '') or '').strip()
        for field_name in ('yonetici_sicil', 'ikinci_yonetici_sicil', 'ucuncu_yonetici_sicil')
    )


@dataclass(frozen=True, slots=True)
class ChainPolicy:
    subject_type: SubjectType
    chain_type: ChainType
    order: tuple[int, ...]
    labels: dict[int, str]
    expected_roles: dict[int, tuple[str, ...]]
    default_weights: dict[int, float]
    fallback_fields: dict[int, str]


PRESIDENCY_POLICY = ChainPolicy(
    subject_type=SubjectType.PRESIDENCY,
    chain_type=ChainType.PRESIDENCY,
    order=(2, 1),
    labels={1: 'Başkan', 2: 'Başkan Yardımcısı'},
    expected_roles={1: ('baskan',), 2: ('baskan_yardimcisi',)},
    default_weights={1: 50.0, 2: 50.0, 3: 0.0},
    fallback_fields={1: 'ikinci_yonetici_sicil', 2: 'yonetici_sicil'},
)

GROUP_MANAGER_POLICY = ChainPolicy(
    subject_type=SubjectType.GROUP_MANAGER,
    chain_type=ChainType.PRESIDENCY,
    order=(2, 1),
    labels={1: 'Başkan', 2: 'Başkan Yardımcısı'},
    expected_roles={1: ('baskan',), 2: ('baskan_yardimcisi',)},
    default_weights={1: 50.0, 2: 50.0, 3: 0.0},
    # Grup Başkanı / Hukuk-Mali Müşavir için güncel slot yapısı:
    # 1. amir = Başkan, 2. amir = Başkan Yardımcısı
    fallback_fields={1: 'yonetici_sicil', 2: 'ikinci_yonetici_sicil'},
)

COORDINATOR_POLICY = ChainPolicy(
    subject_type=SubjectType.COORDINATOR,
    chain_type=ChainType.GROUP,
    order=(2, 1),
    labels={1: 'Başkan Yardımcısı', 2: 'Grup Başkanı'},
    expected_roles={1: ('baskan_yardimcisi',), 2: ('grup_baskani', 'mali_musavir')},
    default_weights={1: 50.0, 2: 50.0, 3: 0.0},
    fallback_fields={1: 'yonetici_sicil', 2: 'ikinci_yonetici_sicil'},
)

GROUP_STAFF_POLICY = ChainPolicy(
    subject_type=SubjectType.GROUP_STAFF,
    chain_type=ChainType.GROUP,
    order=(3, 2, 1),
    labels={1: 'Grup Başkanı', 2: 'Koordinatör', 3: 'Birim Amiri'},
    expected_roles={
        1: ('grup_baskani', 'mali_musavir'),
        2: ('koordinator',),
        3: ('birim_sorumlusu', 'birim_amiri'),
    },
    default_weights={1: 50.0, 2: 50.0, 3: 0.0},
    fallback_fields={1: 'yonetici_sicil', 2: 'ikinci_yonetici_sicil', 3: 'ucuncu_yonetici_sicil'},
)

HUKUK_STAFF_POLICY = ChainPolicy(
    subject_type=SubjectType.HUKUK_STAFF,
    chain_type=ChainType.PRESIDENCY,
    order=(1,),
    labels={1: 'Hukuk Müşaviri'},
    expected_roles={1: ('hukuk_musaviri', 'mali_musavir', 'grup_baskani')},
    default_weights={1: 100.0, 2: 0.0, 3: 0.0},
    fallback_fields={1: 'yonetici_sicil'},
)

POLICY_BY_SUBJECT = {
    SubjectType.PRESIDENCY: PRESIDENCY_POLICY,
    SubjectType.GROUP_MANAGER: GROUP_MANAGER_POLICY,
    SubjectType.COORDINATOR: COORDINATOR_POLICY,
    SubjectType.GROUP_STAFF: GROUP_STAFF_POLICY,
    SubjectType.HUKUK_STAFF: HUKUK_STAFF_POLICY,
}


def _fold(value: object) -> str:
    text = unicodedata.normalize('NFKD', str(value or ''))
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace('ı', 'i').replace('İ', 'i').lower()
    for old, new in (
        ('ş', 's'), ('ğ', 'g'), ('ü', 'u'), ('ö', 'o'), ('ç', 'c'), ('-', ' '), ('/', ' '), ('__', '_')
    ):
        text = text.replace(old, new)
    return ' '.join(text.split())


def normalize_role_token(*values: object) -> str:
    blob = ' | '.join(_fold(value) for value in values if value)

    # Önce spesifik roller çözülsün; aksi halde "Başkanlığı / Başkan Yardımcılığı"
    # geçen birim adları yüzünden sıradan personel yanlışlıkla başkanlık seviyesine
    # sınıflanabiliyor.
    if any(token in blob for token in ('grup baskani', 'grup baskanligi')):
        return 'grup_baskani'
    if any(token in blob for token in ('baskan yardimcisi', 'bask yrd', 'bsyrd', 'baskan yrd')):
        return 'baskan_yardimcisi'
    if 'mali musavir' in blob:
        return 'mali_musavir'
    if 'koordinator' in blob:
        return 'koordinator'
    # "Sorumlu Hukuk Müşaviri" içindeki "sorumlu" kelimesi, bu unvanı
    # yanlışlıkla genel "birim_sorumlusu" rolüne düşürmemeli. Önce hukuk
    # başlıklarını çözüyoruz; aksi halde hukuk amiri 2 amirli başkanlık
    # zincirinden kopup tek amirli akışa itilerek 2. amir ekranı kilitleniyor.
    if any(token in blob for token in ('hukuk musaviri', 'sorumlu hukuk musaviri')):
        return 'hukuk_musaviri'
    if any(token in blob for token in ('birim sorumlusu', 'birim amiri', 'sorumlu')):
        return 'birim_sorumlusu'
    if 'baskan' in blob and 'yardimci' not in blob:
        return 'baskan'
    if 'admin' in blob:
        return 'admin'
    return 'personel'


def classify_subject_type(employee) -> SubjectType:
    role_token = normalize_role_token(
        getattr(employee, 'role', ''),
        getattr(employee, 'role_label', ''),
        getattr(employee, 'unvan', ''),
    )
    if role_token in {'baskan', 'baskan_yardimcisi'}:
        return SubjectType.PRESIDENCY
    if role_token == 'koordinator':
        return SubjectType.COORDINATOR

    if _is_hukuk_context(employee):
        folded_title = _fold(getattr(employee, 'unvan', ''))

        # Kalıcı hukuk istisnası:
        # Sorumlu Hukuk Müşaviri / hukuk amiri, kart üzerinde Başkan +
        # Başkan Yardımcısı slotları yazsa bile tek amirli hukuk personeli gibi
        # sınıflandırılmamalı. Aksi halde zincir order=(1,) kalıyor ve 2. amir
        # görevini açsa bile puan veremiyor.
        if 'sorumlu hukuk musavir' in folded_title:
            return SubjectType.GROUP_MANAGER

        if role_token in {'grup_baskani', 'mali_musavir'}:
            return SubjectType.GROUP_MANAGER

        # Plain hukuk müşaviri kaydı, açık bir üst/amir ipucu taşıyorsa
        # tek amirli hukuk astı kabul edilir; aksi halde hukuk amiri gibi ele alınır.
        if role_token == 'hukuk_musaviri':
            return SubjectType.HUKUK_STAFF if _has_explicit_manager_hint(employee) else SubjectType.GROUP_MANAGER

        if _has_explicit_manager_hint(employee):
            return SubjectType.HUKUK_STAFF

        return SubjectType.GROUP_MANAGER

    if role_token in {'grup_baskani', 'mali_musavir'}:
        return SubjectType.GROUP_MANAGER
    return SubjectType.GROUP_STAFF


def resolve_chain_policy(employee) -> ChainPolicy:
    return POLICY_BY_SUBJECT[classify_subject_type(employee)]


def normalize_level_mode(period) -> LevelMode:
    if not period:
        return LevelMode.COMMENT_ONLY
    # BYS360_PHASE4_THIRD_SUPERVISOR_LEVEL_MODE
    try:
        from app.services.performance.third_supervisor_policy import third_supervisor_policy_snapshot
        _phase4_policy = third_supervisor_policy_snapshot(period)
        if not _phase4_policy.get("enabled"):
            return LevelMode.DISABLED
        if _phase4_policy.get("scoring_enabled"):
            return LevelMode.SCORE_ENABLED
        return LevelMode.COMMENT_ONLY
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        import logging
        logging.getLogger(__name__).exception("BYS360_CLAUDE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance_v2/rules.py")
    raw = getattr(period, 'level_3_mode', None)
    if raw == 'scoring':
        return LevelMode.SCORE_ENABLED
    if raw in {'comment_only', 'yorumcu'}:
        return LevelMode.COMMENT_ONLY
    if raw in {'off', 'disabled'}:
        return LevelMode.DISABLED
    if bool(getattr(period, 'enable_level_3_scoring', False)):
        return LevelMode.SCORE_ENABLED
    if bool(getattr(period, 'enable_level_3', False)):
        return LevelMode.COMMENT_ONLY
    # Kurumsal varsayılan: 3. amir herkeste zorunlu değildir;
    # açık bir ayar veya gerçek bağlayıcı kayıt yoksa kapalı kabul edilir.
    return LevelMode.DISABLED


def normalize_weights(raw_weights: dict[int, float], enabled_levels: Iterable[int]) -> dict[int, float]:
    enabled = [level for level in sorted(set(enabled_levels)) if raw_weights.get(level, 0) > 0]
    if not enabled:
        return {1: 50.0, 2: 50.0, 3: 0.0}
    total = sum(float(raw_weights.get(level, 0) or 0) for level in enabled)
    if total <= 0:
        share = 100.0 / len(enabled)
        return {1: share if 1 in enabled else 0.0, 2: share if 2 in enabled else 0.0, 3: share if 3 in enabled else 0.0}
    normalized = {level: round((float(raw_weights.get(level, 0) or 0) / total) * 100.0, 2) for level in enabled}
    for level in (1, 2, 3):
        normalized.setdefault(level, 0.0)
    drift = round(100.0 - sum(normalized.values()), 2)
    if enabled and drift:
        normalized[enabled[-1]] = round(normalized[enabled[-1]] + drift, 2)
    return normalized


def visible_previous_levels(current_level: int, policy: ChainPolicy, level_mode: LevelMode) -> list[int]:
    if current_level <= 1:
        return [level for level in policy.order if level > current_level and (level != 3 or level_mode != LevelMode.DISABLED)]
    if current_level == 2:
        return [3] if 3 in policy.order and level_mode != LevelMode.DISABLED else []
    return []


def is_comment_required(score_100: float | None, raw_score: float | None) -> bool:
    return score_requires_criterion_comment(raw_score)


def default_policy_snapshot() -> dict[str, object]:
    return {
        key.value: {
            'chain_type': policy.chain_type.value,
            'order': list(policy.order),
            'labels': dict(policy.labels),
            'expected_roles': {level: list(values) for level, values in policy.expected_roles.items()},
            'default_weights': dict(policy.default_weights),
        }
        for key, policy in POLICY_BY_SUBJECT.items()
    }
