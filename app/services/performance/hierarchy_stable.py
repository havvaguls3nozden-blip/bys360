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

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

try:
    from flask import current_app
except Exception:  # pragma: no cover
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    current_app = None

from app.services.hierarchy_rulebook_service import is_president, is_system_user
from app.services.performance.chain_rule_engine import resolve_authoritative_chain
from .common import build_assignment_due_date

try:
    from app.extensions import db
except Exception:  # pragma: no cover
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    db = None

try:
    import app.models as models
except Exception:  # pragma: no cover
    logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
    models = None

User = getattr(models, 'User', None) if models else None
PerformancePeriod = getattr(models, 'PerformancePeriod', None) if models else None
EvaluationAssignment = getattr(models, 'EvaluationAssignment', None) if models else None
PerformanceEvaluation = getattr(models, 'PerformanceEvaluation', None) if models else None

INFO = 'info'
WARNING = 'warning'
ERROR = 'error'


@dataclass
class HierarchyIssue:
    level: str
    code: str
    message: str


@dataclass
class StableManagerChain:
    employee_id: int
    employee_name: str
    manager_1_id: Optional[int] = None
    manager_2_id: Optional[int] = None
    manager_3_id: Optional[int] = None
    manager_1_name: str = ''
    manager_2_name: str = ''
    manager_3_name: str = ''
    flow_order: Tuple[int, ...] = field(default_factory=tuple)
    issues: List[HierarchyIssue] = field(default_factory=list)


def _safe_str(value: Any) -> str:
    return str(value).strip() if value is not None else ''


def _user_name(user: Any) -> str:
    if not user:
        return ''
    for attr in ('full_name', 'display_name'):
        value = getattr(user, attr, None)
        if callable(value):
            try:
                result = value()
                if result:
                    return _safe_str(result)
            except Exception:
                logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
                import logging
                logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/hierarchy_stable.py")
        elif value:
            return _safe_str(value)
    return f"{_safe_str(getattr(user, 'ad', ''))} {_safe_str(getattr(user, 'soyad', ''))}".strip()


def _get_user_id(value: Any) -> Optional[int]:
    if value is None:
        return None
    return getattr(value, 'id', value)


def _log(level: str, message: str):
    try:
        if current_app:
            getattr(current_app.logger, level, current_app.logger.info)(message)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        import logging
        logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/hierarchy_stable.py")
def fetch_active_users() -> List[Any]:
    if not User:
        return []
    query = User.query
    if hasattr(User, 'is_active'):
        query = query.filter_by(is_active=True)
    rows = query.order_by(User.id.asc()).all()
    return [row for row in rows if not is_system_user(row)]


def build_user_maps(users: List[Any]) -> Tuple[Dict[int, Any], Dict[str, Any]]:
    by_id: Dict[int, Any] = {}
    by_sicil: Dict[str, Any] = {}
    for user in users:
        by_id[user.id] = user
        sicil = _safe_str(getattr(user, 'sicil_no', ''))
        if sicil:
            by_sicil[sicil] = user
    return by_id, by_sicil


def _find_user_by_sicil(by_sicil: Dict[str, Any], sicil: str):
    return by_sicil.get(_safe_str(sicil))


def _current_chain_tuple(user: Any) -> tuple[str | None, str | None, str | None]:
    return (
        _safe_str(getattr(user, 'yonetici_sicil', '')) or None,
        _safe_str(getattr(user, 'ikinci_yonetici_sicil', '')) or None,
        _safe_str(getattr(user, 'ucuncu_yonetici_sicil', '')) or None,
    )


def build_manager_chain_for_user(user: Any, users_by_sicil: Dict[str, Any], period: Any = None) -> StableManagerChain:
    desired = resolve_authoritative_chain(user, users_by_sicil.values(), preserve_explicit_level3=True)

    chain = StableManagerChain(
        employee_id=_get_user_id(user),
        employee_name=_user_name(user),
    )

    if is_president(user):
        chain.issues.append(HierarchyIssue(INFO, 'president_excluded', 'Başkan performans değerlendirme zincirine dahil edilmez.'))
        return chain

    if _current_chain_tuple(user) != (desired.manager_1_sicil, desired.manager_2_sicil, desired.manager_3_sicil):
        chain.issues.append(HierarchyIssue(INFO, 'manager_chain_repaired', 'Amir zinciri kurala göre onarıldı.'))

    m1 = _find_user_by_sicil(users_by_sicil, desired.manager_1_sicil or '')
    m2 = _find_user_by_sicil(users_by_sicil, desired.manager_2_sicil or '')
    m3 = _find_user_by_sicil(users_by_sicil, desired.manager_3_sicil or '')

    chain.manager_1_id = _get_user_id(m1)
    chain.manager_2_id = _get_user_id(m2)
    chain.manager_3_id = _get_user_id(m3)
    chain.manager_1_name = _user_name(m1)
    chain.manager_2_name = _user_name(m2)
    chain.manager_3_name = _user_name(m3)

    if desired.rule_code == 'hukuk_staff_single':
        chain.issues.append(HierarchyIssue(INFO, 'hukuk_single', 'Hukuk personeli tek amir kuralı uygulandı.'))
    elif desired.rule_code == 'hukuk_chief_presidency_override':
        chain.issues.append(HierarchyIssue(INFO, 'hukuk_chief_override', 'Hukuk müşaviri için 1. amir Başkan, 2. amir Başkan Yardımcısı özel kuralı uygulandı.'))
    elif desired.rule_code in {'direct_president_single', 'vice_president_single'}:
        chain.issues.append(HierarchyIssue(INFO, 'single_manager_rule', 'Özel tek amir kuralı uygulandı.'))

    for info in desired.info_notes:
        chain.issues.append(HierarchyIssue(INFO, 'info_note', info))

    if 1 in desired.expected_levels and not chain.manager_1_id:
        chain.issues.append(HierarchyIssue(WARNING, 'manager_1_required', '1. amir eksik veya pasif'))
    if 2 in desired.expected_levels and not chain.manager_2_id:
        chain.issues.append(HierarchyIssue(WARNING, 'manager_2_required', '2. amir eksik veya pasif'))
    if desired.explicit_level_3_requested and 3 in desired.expected_levels and not chain.manager_3_id:
        chain.issues.append(HierarchyIssue(WARNING, 'manager_3_invalid', '3. amir tanımlı ancak geçersiz/pasif'))

    unique_ids = [mid for mid in [chain.manager_1_id, chain.manager_2_id, chain.manager_3_id] if mid]
    if len(unique_ids) != len(set(unique_ids)):
        chain.issues.append(HierarchyIssue(WARNING, 'duplicate_manager', 'Aynı kişi birden fazla amir seviyesine atanmış.'))
    if chain.employee_id in unique_ids:
        chain.issues.append(HierarchyIssue(ERROR, 'self_manager', 'Personel kendisine amir atanamaz.'))

    if chain.manager_3_id:
        chain.flow_order = (3, 2, 1)
    elif chain.manager_2_id:
        chain.flow_order = (2, 1)
    elif chain.manager_1_id:
        chain.flow_order = (1,)
    else:
        chain.flow_order = tuple()

    return chain


def build_all_manager_chains(users: Optional[List[Any]] = None, period: Any = None) -> List[StableManagerChain]:
    users = users or fetch_active_users()
    _, users_by_sicil = build_user_maps(users)
    return [build_manager_chain_for_user(user, users_by_sicil, period) for user in users]


def analyze_hierarchy_rows(period_id: Optional[int] = None) -> List[Dict[str, Any]]:
    users = fetch_active_users()
    rows = []
    for user, chain in zip(users, build_all_manager_chains(users, period_id)):
        rows.append(
            {
                'employee_id': chain.employee_id,
                'employee_name': chain.employee_name,
                'manager_1_id': chain.manager_1_id,
                'manager_1_name': chain.manager_1_name,
                'manager_2_id': chain.manager_2_id,
                'manager_2_name': chain.manager_2_name,
                'manager_3_id': chain.manager_3_id,
                'manager_3_name': chain.manager_3_name,
                'flow_order': list(chain.flow_order),
                'issues': [{'level': item.level, 'code': item.code, 'message': item.message} for item in chain.issues],
            }
        )
    return rows


def analyze_hierarchy_gaps(period_id: Optional[int] = None) -> List[Dict[str, Any]]:
    return [row for row in analyze_hierarchy_rows(period_id) if row['issues']]


def ensure_evaluation(period_id: int, employee_id: int, chain: StableManagerChain):
    if not PerformanceEvaluation:
        return None
    row = PerformanceEvaluation.query.filter_by(period_id=period_id, employee_id=employee_id).first()
    if row:
        row.level_1_evaluator_id = chain.manager_1_id
        row.level_2_evaluator_id = chain.manager_2_id
        row.level_3_evaluator_id = chain.manager_3_id
        return row
    row = PerformanceEvaluation(
        period_id=period_id,
        employee_id=employee_id,
        level_1_evaluator_id=chain.manager_1_id,
        level_2_evaluator_id=chain.manager_2_id,
        level_3_evaluator_id=chain.manager_3_id,
        status='bekliyor',
    )
    db.session.add(row)
    db.session.flush()
    return row


def ensure_assignment(period_id: int, employee_id: int, evaluator_id: Optional[int], manager_level: int):
    if not evaluator_id or not EvaluationAssignment:
        return None
    period = db.session.get(PerformancePeriod, period_id) if db and PerformancePeriod else None
    row = EvaluationAssignment.query.filter_by(
        period_id=period_id,
        employee_id=employee_id,
        evaluator_id=evaluator_id,
        manager_level=manager_level,
    ).first()
    if row:
        expected_due_date = build_assignment_due_date(period, getattr(row, 'assigned_at', None))
        if getattr(row, 'due_date', None) != expected_due_date:
            row.due_date = expected_due_date
            db.session.add(row)
            db.session.flush()
        return row
    row = EvaluationAssignment(
        period_id=period_id,
        employee_id=employee_id,
        evaluator_id=evaluator_id,
        manager_level=manager_level,
        status='bekliyor',
        due_date=build_assignment_due_date(period, None),
    )
    db.session.add(row)
    db.session.flush()
    return row


def generate_stable_assignments(period_id: int) -> Dict[str, Any]:
    if not db:
        return {'ok': False, 'message': 'db bağlantısı yok', 'created': 0, 'issues': []}
    created = 0
    issues: List[str] = []
    users = fetch_active_users()
    chains = build_all_manager_chains(users, period_id)
    for chain in chains:
        if chain.issues:
            issues.extend([f"{chain.employee_name}: {item.message}" for item in chain.issues if item.level in {WARNING, ERROR}])
        ensure_evaluation(period_id, chain.employee_id, chain)
        before = EvaluationAssignment.query.count() if EvaluationAssignment else 0
        if chain.manager_3_id:
            ensure_assignment(period_id, chain.employee_id, chain.manager_3_id, 3)
        if chain.manager_2_id:
            ensure_assignment(period_id, chain.employee_id, chain.manager_2_id, 2)
        if chain.manager_1_id:
            ensure_assignment(period_id, chain.employee_id, chain.manager_1_id, 1)
        after = EvaluationAssignment.query.count() if EvaluationAssignment else before
        created += max(0, after - before)
    db.session.commit()
    return {
        'ok': True,
        'message': 'Hiyerarşi tabanlı stabil assignment üretimi tamamlandı.',
        'created': created,
        'issues': issues,
    }