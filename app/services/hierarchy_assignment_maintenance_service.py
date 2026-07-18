from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.extensions import db
import app.models as models

from app.services.auto_hierarchy_service import auto_apply_manager_chains
from app.services.hierarchy_rulebook_service import build_lookup, is_system_user
from app.services.performance.chain_rule_engine import resolve_authoritative_desired_chain

User = getattr(models, 'User', None)
PerformancePeriod = getattr(models, 'PerformancePeriod', None)
EvaluationAssignment = getattr(models, 'EvaluationAssignment', None)
PerformanceEvaluation = getattr(models, 'PerformanceEvaluation', None)

OPEN_STATUSES = {'', 'bekliyor', 'taslak', 'draft', 'pending'}


@dataclass(slots=True)
class RepairDetail:
    sicil_no: str
    full_name: str
    action: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'sicil_no': self.sicil_no,
            'full_name': self.full_name,
            'action': self.action,
            'detail': self.detail,
        }


@dataclass(slots=True)
class RepairSummary:
    ok: bool
    period_id: int | None
    user_updates: int = 0
    user_skips: int = 0
    created: int = 0
    retargeted: int = 0
    deleted_open_wrong: int = 0
    locked_warnings: int = 0
    warnings: list[str] = field(default_factory=list)
    details: list[RepairDetail] = field(default_factory=list)
    message: str = ''

    def to_dict(self) -> dict[str, Any]:
        return {
            'ok': self.ok,
            'period_id': self.period_id,
            'user_updates': self.user_updates,
            'user_skips': self.user_skips,
            'created': self.created,
            'retargeted': self.retargeted,
            'deleted_open_wrong': self.deleted_open_wrong,
            'locked_warnings': self.locked_warnings,
            'warnings': list(self.warnings),
            'details': [item.to_dict() for item in self.details],
            'message': self.message,
        }


def _safe(value: Any) -> str:
    return str(value or '').strip()


def _full_name(user: Any) -> str:
    if not user:
        return ''
    full_name = _safe(getattr(user, 'full_name', ''))
    if full_name:
        return full_name
    return f"{_safe(getattr(user, 'ad', ''))} {_safe(getattr(user, 'soyad', ''))}".strip()


def _active_period() -> Any | None:
    if not PerformancePeriod:
        return None
    return (
        PerformancePeriod.query
        .filter_by(is_active=True)
        .order_by(PerformancePeriod.id.desc())
        .first()
    )


def _existing_rows(period_id: int, employee_id: int) -> list[Any]:
    if not EvaluationAssignment:
        return []
    return list(EvaluationAssignment.query.filter_by(period_id=period_id, employee_id=employee_id).all())


def _status_open(row: Any) -> bool:
    return _safe(getattr(row, 'status', '')).lower() in OPEN_STATUSES


def _find_exact(existing_rows: list[Any], level: int, evaluator_id: int | None) -> Any | None:
    if not evaluator_id:
        return None
    for row in existing_rows:
        if int(getattr(row, 'manager_level', 0) or 0) == int(level) and int(getattr(row, 'evaluator_id', 0) or 0) == int(evaluator_id):
            return row
    return None


def _find_same_level(existing_rows: list[Any], level: int) -> Any | None:
    for row in existing_rows:
        if int(getattr(row, 'manager_level', 0) or 0) == int(level):
            return row
    return None


def _ensure_evaluation(period_id: int, user: Any, desired: dict[int, Any], details: list[RepairDetail]):
    if not PerformanceEvaluation:
        return
    row = PerformanceEvaluation.query.filter_by(period_id=period_id, employee_id=user.id).first()
    if not row:
        row = PerformanceEvaluation(
            period_id=period_id,
            employee_id=user.id,
            level_1_evaluator_id=getattr(desired.get(1), 'id', None),
            level_2_evaluator_id=getattr(desired.get(2), 'id', None),
            level_3_evaluator_id=getattr(desired.get(3), 'id', None),
            status='bekliyor',
        )
        db.session.add(row)
        db.session.flush()
        details.append(RepairDetail(_safe(getattr(user, 'sicil_no', '')), _full_name(user), 'evaluation_created', 'PerformanceEvaluation kaydı oluşturuldu.'))
        return

    changed = False
    for level, attr in ((1, 'level_1_evaluator_id'), (2, 'level_2_evaluator_id'), (3, 'level_3_evaluator_id')):
        desired_id = getattr(desired.get(level), 'id', None)
        completed_attr = f'level_{level}_completed'
        if bool(getattr(row, completed_attr, False)) and getattr(row, attr) not in {None, desired_id}:
            details.append(RepairDetail(_safe(getattr(user, 'sicil_no', '')), _full_name(user), 'evaluation_locked', f'{level}. amir evaluator alanı tamamlanmış kayıt nedeniyle değiştirilmedi.'))
            continue
        if getattr(row, attr) != desired_id:
            setattr(row, attr, desired_id)
            changed = True
    if changed:
        db.session.add(row)
        db.session.flush()
        details.append(RepairDetail(_safe(getattr(user, 'sicil_no', '')), _full_name(user), 'evaluation_updated', 'PerformanceEvaluation evaluator alanları güncellendi.'))


def repair_hierarchy_and_assignments(*, apply: bool = False) -> RepairSummary:
    if not User:
        return RepairSummary(ok=False, period_id=None, message='User modeli bulunamadı.')

    period = _active_period()
    if not period:
        return RepairSummary(ok=False, period_id=None, message='Aktif dönem bulunamadı.')

    chain_result = auto_apply_manager_chains(
        fill_only_missing=True,
        commit=False,
        preserve_explicit_chain=True,  # BYS360_EXPLICIT_MANAGER_CHAIN_V2
    )
    users = [u for u in User.query.filter_by(is_active=True).order_by(User.id.asc()).all() if not is_system_user(u)]
    lookup = build_lookup(users)
    details: list[RepairDetail] = []
    warnings: list[str] = list(chain_result.get('warnings') or [])
    created = retargeted = deleted_open_wrong = locked_warnings = 0

    for user in users:
        desired_chain = resolve_authoritative_desired_chain(user, lookup, preserve_explicit_level3=True)
        desired_users = {
            1: lookup.by_sicil.get(desired_chain.manager_1_sicil or ''),
            2: lookup.by_sicil.get(desired_chain.manager_2_sicil or ''),
            3: lookup.by_sicil.get(desired_chain.manager_3_sicil or ''),
        }
        _ensure_evaluation(period.id, user, desired_users, details)

        if not EvaluationAssignment:
            continue
        existing_rows = _existing_rows(period.id, user.id)
        desired_by_level = {level: item for level, item in desired_users.items() if item}

        for level, evaluator in desired_by_level.items():
            exact = _find_exact(existing_rows, level, getattr(evaluator, 'id', None))
            if exact:
                continue
            same_level = _find_same_level(existing_rows, level)
            if same_level and _status_open(same_level):
                old_eval = getattr(same_level, 'evaluator_id', None)
                if hasattr(same_level, 'original_evaluator_id') and not getattr(same_level, 'original_evaluator_id', None):
                    same_level.original_evaluator_id = old_eval
                same_level.evaluator_id = evaluator.id
                db.session.add(same_level)
                db.session.flush()
                retargeted += 1
                details.append(RepairDetail(_safe(getattr(user, 'sicil_no', '')), _full_name(user), 'assignment_retargeted', f'{level}. seviye görev yeni evaluator ile güncellendi.'))
                continue
            if same_level and not _status_open(same_level):
                locked_warnings += 1
                warnings.append(f"{_full_name(user)} L{level}: tamamlanmış/kapalı görev olduğu için evaluator değiştirilmedi.")
                details.append(RepairDetail(_safe(getattr(user, 'sicil_no', '')), _full_name(user), 'assignment_locked', f'{level}. seviye kapalı görev değiştirilemedi.'))
                continue
            row = EvaluationAssignment(
                period_id=period.id,
                employee_id=user.id,
                evaluator_id=evaluator.id,
                manager_level=level,
                status='bekliyor',
            )
            db.session.add(row)
            db.session.flush()
            created += 1
            details.append(RepairDetail(_safe(getattr(user, 'sicil_no', '')), _full_name(user), 'assignment_created', f'{level}. seviye eksik görev oluşturuldu.'))

        set(desired_by_level.keys())
        for row in list(existing_rows):
            level = int(getattr(row, 'manager_level', 0) or 0)
            if level not in {1, 2, 3}:
                continue
            desired_eval = desired_by_level.get(level)
            if desired_eval and int(getattr(row, 'evaluator_id', 0) or 0) == int(getattr(desired_eval, 'id', 0) or 0):
                continue
            if _status_open(row):
                db.session.delete(row)
                deleted_open_wrong += 1
                details.append(RepairDetail(_safe(getattr(user, 'sicil_no', '')), _full_name(user), 'assignment_deleted', f'{level}. seviye yanlış açık görev kaldırıldı.'))
            else:
                locked_warnings += 1
                warnings.append(f"{_full_name(user)} L{level}: yanlış kapalı görev kaldı, manuel kontrol gerekli.")
                details.append(RepairDetail(_safe(getattr(user, 'sicil_no', '')), _full_name(user), 'assignment_wrong_locked', f'{level}. seviye kapalı yanlış görev manuel kontrol gerektiriyor.'))

    if apply:
        db.session.commit()
    else:
        db.session.rollback()

    return RepairSummary(
        ok=True,
        period_id=period.id,
        user_updates=int(chain_result.get('updated_count', 0) or 0),
        user_skips=int(chain_result.get('skipped_count', 0) or 0),
        created=created,
        retargeted=retargeted,
        deleted_open_wrong=deleted_open_wrong,
        locked_warnings=locked_warnings,
        warnings=warnings,
        details=details,
        message='Uygulama hotfix analizi tamamlandı.' if not apply else 'Uygulama hotfix düzeltmeleri uygulandı.',
    )