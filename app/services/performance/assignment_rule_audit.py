
"""Performans görev üretimi için anayasa kuralı ön kontrol kapısı.

Başkan görev üretimi subject listesinden çıkarılır; ancak lookup havuzunda kalır.
Bu sayede Grup Başkanı / özel başkanlık istisnaları için 1. Amir = Başkan zinciri
bozulmaz. Tamamlanmış görevlerle çakışma varsa otomatik görev üretimi durdurulur.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.extensions import db
from app.models import EvaluationAssignment, PerformancePeriod, User
from app.services.hierarchy_rulebook_service import build_lookup
from app.services.performance.chain_rule_engine import resolve_authoritative_desired_chain
from app.services.performance.common import is_president
from app.services.performance.period_scope_assignment import filter_period_scope_employees
from app.services.performance.selected_scope_assessor_policy import (
    is_specific_period_scope,
    split_scored_employees_from_assessor_only,
)

_COMPLETED_STATUSES = {"tamamlandi", "tamamlandı", "submitted", "completed", "onaylandi", "onaylandı"}
_INACTIVE_STATUSES = {"pasif", "muaf", "iptal", "cancelled", "canceled", "silindi"}


@dataclass(slots=True)
class AssignmentRuleIssue:
    employee_id: int
    employee_name: str
    level: int | None
    issue_type: str
    severity: str
    message: str
    expected_evaluator_id: int | None = None
    current_evaluator_id: int | None = None
    assignment_id: int | None = None
    completed: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "employee_id": self.employee_id,
            "employee_name": self.employee_name,
            "level": self.level,
            "issue_type": self.issue_type,
            "severity": self.severity,
            "message": self.message,
            "expected_evaluator_id": self.expected_evaluator_id,
            "current_evaluator_id": self.current_evaluator_id,
            "assignment_id": self.assignment_id,
            "completed": self.completed,
        }


@dataclass(slots=True)
class AssignmentRuleAuditResult:
    ok: bool
    period_id: int | None
    period_title: str = ""
    employee_count: int = 0
    issue_count: int = 0
    blocking_issue_count: int = 0
    completed_conflict_count: int = 0
    missing_count: int = 0
    stale_count: int = 0
    duplicate_count: int = 0
    wrong_slot_count: int = 0
    president_lookup_available: bool = False
    president_excluded_from_subjects: bool = True
    issues: list[AssignmentRuleIssue] = field(default_factory=list)
    message: str = ""

    @property
    def can_auto_repair(self) -> bool:
        return self.blocking_issue_count == 0 and self.completed_conflict_count == 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "period_id": self.period_id,
            "period_title": self.period_title,
            "employee_count": self.employee_count,
            "issue_count": self.issue_count,
            "blocking_issue_count": self.blocking_issue_count,
            "completed_conflict_count": self.completed_conflict_count,
            "missing_count": self.missing_count,
            "stale_count": self.stale_count,
            "duplicate_count": self.duplicate_count,
            "wrong_slot_count": self.wrong_slot_count,
            "president_lookup_available": self.president_lookup_available,
            "president_excluded_from_subjects": self.president_excluded_from_subjects,
            "can_auto_repair": self.can_auto_repair,
            "issues": [issue.as_dict() for issue in self.issues],
            "message": self.message,
        }


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _display_name(user: Any) -> str:
    return _text(getattr(user, "full_name", "")) or f"{_text(getattr(user, 'ad', ''))} {_text(getattr(user, 'soyad', ''))}".strip() or "Personel"


def _status(row: Any) -> str:
    return _text(getattr(row, "status", "")).lower()


def _is_completed(row: Any) -> bool:
    return bool(getattr(row, "completed_at", None)) or _status(row) in _COMPLETED_STATUSES


def _is_inactive(row: Any) -> bool:
    return _status(row) in _INACTIVE_STATUSES


def _active_period(period_id: int | None = None) -> PerformancePeriod | None:
    if period_id:
        return db.session.get(PerformancePeriod, period_id)
    return PerformancePeriod.query.filter_by(is_active=True).order_by(PerformancePeriod.id.desc()).first()


def _subject_users() -> list[User]:
    return User.query.filter(User.is_active.is_(True), User.role != "admin").order_by(User.ad.asc(), User.soyad.asc()).all()

def _scored_subject_users_for_period(period: PerformancePeriod, subject_users: list[User]) -> tuple[list[User], list[User]]:
    """Ön kontrolü dönem kapsamındaki puanlanacak personele indirger.

    Genel/Tüm Kurum döneminde eski davranış korunur. Birim, üst birim, kategori
    veya seçili personel özel dönemlerinde ise amirler yalnızca değerlendirici
    olarak kalır; preflight onları puanlanacak personel gibi eksik görev riski
    üretmez.
    """
    if not is_specific_period_scope(period):
        return list(subject_users or []), []
    matched = filter_period_scope_employees(subject_users or [], period)
    scored, assessor_only = split_scored_employees_from_assessor_only(period, matched)
    return scored, assessor_only


def _assignment_current_evaluator(row: EvaluationAssignment) -> int | None:
    return getattr(row, "original_evaluator_id", None) or getattr(row, "evaluator_id", None)


def _expected_level_map(employee: User, lookup) -> dict[int, int | None]:
    desired = resolve_authoritative_desired_chain(employee, lookup, preserve_explicit_level3=True)
    expected: dict[int, int | None] = {}
    for level, sicil in ((1, desired.manager_1_sicil), (2, desired.manager_2_sicil), (3, desired.manager_3_sicil)):
        sicil_text = _text(sicil)
        if not sicil_text:
            continue
        manager = lookup.by_sicil.get(sicil_text)
        expected[level] = getattr(manager, "id", None) if manager else None
    return expected


def build_assignment_generation_preflight(period_id: int | None = None, *, limit: int = 500) -> dict[str, Any]:
    return audit_assignment_rule_alignment(period_id=period_id, limit=limit).as_dict()


def audit_assignment_rule_alignment(period_id: int | None = None, *, limit: int = 500) -> AssignmentRuleAuditResult:
    period = _active_period(period_id)
    if period is None:
        return AssignmentRuleAuditResult(ok=False, period_id=None, message="Aktif/geçerli performans dönemi bulunamadı.", blocking_issue_count=1)

    all_users = _subject_users()
    lookup = build_lookup(all_users)  # Başkan lookup içinde kalmalıdır.
    raw_subject_users = [user for user in all_users if not is_president(user)]
    subject_users, assessor_only_users = _scored_subject_users_for_period(period, raw_subject_users)

    result = AssignmentRuleAuditResult(
        ok=True,
        period_id=period.id,
        period_title=_text(getattr(period, "title", "")),
        employee_count=len(subject_users),
        president_lookup_available=bool(getattr(lookup, "president", None)),
        president_excluded_from_subjects=all(not is_president(user) for user in subject_users),
    )

    if assessor_only_users:
        result.issues.append(AssignmentRuleIssue(
            0,
            "Sistem",
            None,
            "assessor_only_excluded",
            "info",
            f"Özel dönem kapsamında {len(assessor_only_users)} amir yalnızca değerlendirici olarak tutuldu; puanlanacak personel ön kontrolüne alınmadı.",
        ))

    if not result.president_lookup_available:
        result.issues.append(AssignmentRuleIssue(0, "Sistem", None, "president_lookup_missing", "error", "Başkan lookup havuzunda bulunamadı; Grup Başkanı zinciri eksik üretilebilir."))
        result.blocking_issue_count += 1
    if not result.president_excluded_from_subjects:
        result.issues.append(AssignmentRuleIssue(0, "Sistem", None, "president_subject_not_excluded", "error", "Başkan görev üretim öznesi olarak listeye girmiş görünüyor."))
        result.blocking_issue_count += 1

    for employee in subject_users:
        employee_name = _display_name(employee)
        expected = _expected_level_map(employee, lookup)
        rows = EvaluationAssignment.query.filter_by(period_id=period.id, employee_id=employee.id).order_by(EvaluationAssignment.manager_level.asc(), EvaluationAssignment.id.desc()).all()
        active_rows = [row for row in rows if not _is_inactive(row)]
        by_level: dict[int, list[EvaluationAssignment]] = {}
        for row in active_rows:
            by_level.setdefault(int(getattr(row, "manager_level", 0) or 0), []).append(row)

        for level, expected_id in expected.items():
            current_rows = by_level.get(level, [])
            if not expected_id:
                result.missing_count += 1
                result.issues.append(AssignmentRuleIssue(employee.id, employee_name, level, "expected_manager_missing", "warning", f"{level}. amir sicili çözüldü ancak aktif kullanıcı bulunamadı."))
                continue
            if not current_rows:
                result.missing_count += 1
                result.issues.append(AssignmentRuleIssue(employee.id, employee_name, level, "assignment_missing", "warning", f"{level}. amir için görev kaydı yok; görev üretimiyle oluşturulmalı.", expected_evaluator_id=expected_id))
                continue
            if len(current_rows) > 1:
                result.duplicate_count += 1
                result.issues.append(AssignmentRuleIssue(employee.id, employee_name, level, "duplicate_level_assignment", "warning", f"{level}. amir seviyesinde birden fazla aktif görev var; senkronla tekilleştirilmeli.", expected_evaluator_id=expected_id, assignment_id=getattr(current_rows[0], "id", None), completed=any(_is_completed(row) for row in current_rows)))
            keeper = current_rows[0]
            current_id = _assignment_current_evaluator(keeper)
            if current_id != expected_id:
                completed = _is_completed(keeper)
                result.wrong_slot_count += 1
                if completed:
                    result.completed_conflict_count += 1
                    result.blocking_issue_count += 1
                result.issues.append(AssignmentRuleIssue(employee.id, employee_name, level, "wrong_manager_slot", "error" if completed else "warning", f"{level}. amir görevi anayasa zinciriyle uyuşmuyor. Beklenen kullanıcı id={expected_id}, mevcut/asıl id={current_id}.", expected_evaluator_id=expected_id, current_evaluator_id=current_id, assignment_id=getattr(keeper, "id", None), completed=completed))

        for level, current_rows in by_level.items():
            if level in expected:
                continue
            for row in current_rows:
                completed = _is_completed(row)
                result.stale_count += 1
                if completed:
                    result.completed_conflict_count += 1
                    result.blocking_issue_count += 1
                result.issues.append(AssignmentRuleIssue(employee.id, employee_name, level, "stale_unexpected_assignment", "error" if completed else "warning", f"{level}. amir seviyesinde beklenmeyen eski görev kaydı var.", current_evaluator_id=_assignment_current_evaluator(row), assignment_id=getattr(row, "id", None), completed=completed))

    if limit and len(result.issues) > limit:
        result.issues = result.issues[:limit]
    result.issue_count = result.missing_count + result.stale_count + result.duplicate_count + result.wrong_slot_count + result.blocking_issue_count
    if result.blocking_issue_count:
        result.ok = False
        result.message = "Görev üretimi ön kontrolünde tamamlanmış kayıtlarla çakışan veya bloklayan zincir sorunu var."
    elif result.issue_count:
        result.message = "Görev üretimi ön kontrolünde onarılabilir zincir farkları bulundu."
    else:
        result.message = "Görev üretimi ön kontrolü temiz."
    return result


__all__ = ["AssignmentRuleAuditResult", "AssignmentRuleIssue", "audit_assignment_rule_alignment", "build_assignment_generation_preflight"]
