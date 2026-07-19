from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional
import unicodedata

from app.extensions import db
from app.models import (
    AssignmentCoverageLog,
    EvaluationAssignment,
    PerformanceEvaluation,
    PerformanceEvaluationItem,
    User,
)
from app.services.availability_service import (
    DelegationResolution,
    apply_availability_snapshot_to_evaluation,
    resolve_effective_manager,
)
from .common import (
    ManagerChain,
    _safe_str,
    build_assignment_due_date,
    get_period,
)
from .rules import (
    WARNING_REASON_DUPLICATE_MANAGER,
    WARNING_REASON_MANAGER_1_MISSING,
    WARNING_REASON_MANAGER_2_MISSING,
    WARNING_REASON_MANAGER_3_INVALID,
    WARNING_REASON_PRESIDENT_MISSING,
    WARNING_REASON_SELF_MANAGER,
)

TR_ASCII_MAP = str.maketrans({
    "ç": "c", "Ç": "c",
    "ğ": "g", "Ğ": "g",
    "ı": "i", "İ": "i", "I": "i",
    "ö": "o", "Ö": "o",
    "ş": "s", "Ş": "s",
    "ü": "u", "Ü": "u",
})


def _normalize_reason_text(value: Any) -> str:
    text = _safe_str(value)
    if not text:
        return ""

    # Türkçe özel harfleri önce açıkça ASCII karşılıklarına çeviriyoruz.
    # NFKD tek başına özellikle dotless-ı için yeterli olmadığı için
    # "müşavirliği / kuralı / başkanlık" gibi kayıtlar bazen eşleşmiyordu.
    translated = text.translate(TR_ASCII_MAP)
    folded = unicodedata.normalize("NFKD", translated)
    plain = "".join(ch for ch in folded if not unicodedata.combining(ch))
    plain = plain.replace("–", "-").replace("—", "-")
    plain = plain.replace(".", " ").replace(":", " ").replace(";", " ")
    return " ".join(plain.lower().split())


def is_informational_special_case(
    reason: str | None = None,
    event_type: str | None = None,
    manager_level: int | None = None,
) -> bool:
    """Return True for non-actionable informational rows.

    Bu sürüm noktalama, Türkçe karakter ve eski log metin varyasyonlarını
    normalize ederek değerlendirir. Özel tek amir / başkanlık / hukuk /
    3. amir yorumcu / vekâlet bilgi kayıtları risk sayılmaz.
    """
    reason_text = _normalize_reason_text(reason)
    event_text = _normalize_reason_text(event_type)
    try:
        level = int(manager_level) if manager_level is not None and _safe_str(manager_level) else None
    except (TypeError, ValueError):
        level = None

    if event_text in {"special_case", "info_note"}:
        return True

    if level == 3 and (
        "birim amiri bulunamadi" in reason_text
        or reason_text == WARNING_REASON_MANAGER_3_INVALID.lower()
    ):
        return True

    info_tokens = [
        "baskan performans degerlendirme zincirine dahil edilmez",
        "ozel tek amir",
        "tek amir kurali uygulandi",
        "hukuk musavirligi ast-ust tek amir kurali uygulandi",
        "amir zinciri kurala gore onarildi",
        "eksik amir zinciri kurala gore dolduruldu",
        "ozel tek amir kurali uygulandi",
        "ozel baskanlik birimi tek amir kurali uygulandi",
        "tek amir kurali uygulandi",
        "hukuk personeli tek amir kurali uygulandi",
        "hukuk musavirligi tek amir kurali uygulandi",
        "hukuk musavirligi ast-ust tek amir kurali uygulandi",
        "3. amir yorumcu modunda",
        "3 amir yorumcu modunda",
        "ozel kural geregi 1. amir baskan olarak duzeltildi",
        "ozel kural geregi zincir kurumsal siraya gore duzeltildi",
        "koordinator zinciri anayasa matrisine gore 1. amir baskan yardimcisi, 2. amir grup baskani olarak duzeltildi",
        "koordinator zinciri anayasa matrisine gore 1=başkan yardimcisi, 2=grup baskani olarak sabitlendi",
        "koordinator zinciri anayasa matrisine gore 1=baskan yardimcisi, 2=grup baskani olarak sabitlendi",
        "calisma grubu personeli zinciri anayasa matrisine gore 1=grup baskani, 2=koordinator olarak sabitlendi",
        "calisma grubu personeli zinciri faz 4 nihai matrise gore 1=grup baskani, 2=koordinator olarak sabitlendi",
        "hukuk musaviri icin ozel baskanlik istisnasi uygulandi",
        "hukuk musaviri icin 1. amir baskan, 2. amir baskan yardimcisi ozel kurali uygulandi",
        "vekalet nedeniyle gorev ayni seviyede vekile yonlendirildi",
    ]
    return any(token in reason_text for token in info_tokens)


def _split_chain_issues(issue_list: list[str] | None) -> tuple[list[str], list[str]]:
    issues = [item for item in (issue_list or []) if _safe_str(item)]
    fatal_issue_keys = {
        WARNING_REASON_MANAGER_1_MISSING.lower(),
        WARNING_REASON_MANAGER_2_MISSING.lower(),
        WARNING_REASON_MANAGER_3_INVALID.lower(),
        WARNING_REASON_DUPLICATE_MANAGER.lower(),
        WARNING_REASON_SELF_MANAGER.lower(),
        WARNING_REASON_PRESIDENT_MISSING.lower(),
    }

    fatal: list[str] = []
    nonfatal: list[str] = []

    for raw_issue in issues:
        issue_key = _safe_str(raw_issue).lower()
        if issue_key in fatal_issue_keys:
            fatal.append(raw_issue)
            continue
        nonfatal.append(raw_issue)

    return fatal, nonfatal


def _enforce_required_chain_levels(chain: ManagerChain, fatal_issues: list[str] | None, nonfatal_issues: list[str] | None) -> tuple[list[str], list[str]]:
    """Enforce the expected 3→2→1 / 2→1 / 1 chain semantics.

    - 2. amir eksikliği yalnızca gerçek tek-amir özel kuralında nonfatal kalır.
    - 3. amir geçersizliği yalnızca 3. amir aktif zincirdeyse fatal sayılır.
    - Diğer kritik zincir kırıkları fatal kalır.
    """
    fatal = [item for item in (fatal_issues or []) if _safe_str(item)]
    nonfatal = [item for item in (nonfatal_issues or []) if _safe_str(item)]

    def _move(issue: str, *, make_fatal: bool) -> None:
        while issue in fatal:
            fatal.remove(issue)
        while issue in nonfatal:
            nonfatal.remove(issue)
        target = fatal if make_fatal else nonfatal
        if issue not in target:
            target.append(issue)

    if WARNING_REASON_MANAGER_2_MISSING in fatal or WARNING_REASON_MANAGER_2_MISSING in nonfatal:
        _move(WARNING_REASON_MANAGER_2_MISSING, make_fatal=not bool(getattr(chain, "is_single_manager_case", False)))

    if WARNING_REASON_MANAGER_3_INVALID in fatal or WARNING_REASON_MANAGER_3_INVALID in nonfatal:
        _move(WARNING_REASON_MANAGER_3_INVALID, make_fatal=bool(getattr(chain, "level_3_enabled", False)))

    return fatal, nonfatal

def _dedupe_assignment_rows(period_id: int, employee_id: int, manager_level: int) -> int:
    rows = (
        EvaluationAssignment.query
        .filter_by(
            period_id=period_id,
            employee_id=employee_id,
            manager_level=manager_level,
        )
        .order_by(EvaluationAssignment.id.desc())
        .all()
    )

    if len(rows) <= 1:
        return 0

    kept = rows[0]
    removed = 0

    for row in rows[1:]:
        if row.id != kept.id:
            db.session.delete(row)
            removed += 1

    db.session.flush()
    return removed

def _dedupe_item_rows(evaluation_id: int, criteria_id: int, manager_level: int) -> int:
    rows = (
        PerformanceEvaluationItem.query
        .filter_by(
            evaluation_id=evaluation_id,
            criteria_id=criteria_id,
            manager_level=manager_level,
        )
        .order_by(PerformanceEvaluationItem.id.desc())
        .all()
    )

    if len(rows) <= 1:
        return 0

    kept = rows[0]
    removed = 0

    for row in rows[1:]:
        if row.id != kept.id:
            db.session.delete(row)
            removed += 1

    db.session.flush()
    return removed

def ensure_evaluation_record(
    period_id: int,
    employee_id: int,
    chain: ManagerChain | None = None,
) -> PerformanceEvaluation:
    evaluation = PerformanceEvaluation.query.filter_by(
        period_id=period_id,
        employee_id=employee_id,
    ).first()

    if not evaluation:
        evaluation = PerformanceEvaluation(
            period_id=period_id,
            employee_id=employee_id,
            status="bekliyor",
            level_1_total_100=0.0,
            level_2_total_100=0.0,
            level_3_total_100=0.0,
            final_total_100=0.0,
            level_1_completed=False,
            level_2_completed=False,
            level_3_completed=False,
            workflow_status="taslak_1_amir",
            is_published_to_employee=False,
        )
        db.session.add(evaluation)
        db.session.flush()

    if chain:
        evaluation.level_1_evaluator_id = chain.manager_1_id
        evaluation.level_2_evaluator_id = chain.manager_2_id
        evaluation.level_3_evaluator_id = chain.manager_3_id if chain.level_3_enabled else None
        db.session.add(evaluation)

    return evaluation

def apply_effective_chain_to_evaluation(
    evaluation: PerformanceEvaluation,
    chain: ManagerChain,
    coverage_resolutions: dict[int, DelegationResolution] | None = None,
) -> PerformanceEvaluation:
    coverage_resolutions = coverage_resolutions or {}
    evaluation.level_1_evaluator_id = (coverage_resolutions.get(1).acting_manager_id if coverage_resolutions.get(1) else chain.manager_1_id)
    evaluation.level_2_evaluator_id = (coverage_resolutions.get(2).acting_manager_id if coverage_resolutions.get(2) else chain.manager_2_id)
    evaluation.level_3_evaluator_id = (coverage_resolutions.get(3).acting_manager_id if coverage_resolutions.get(3) else chain.manager_3_id) if chain.level_3_enabled else None
    db.session.add(evaluation)
    return evaluation

def ensure_assignment(
    period_id: int,
    employee_id: int,
    evaluator_id: int | None,
    manager_level: int,
    period=None,
    original_evaluator_id: int | None = None,
    delegation_id: int | None = None,
    assignment_source: str = "direct",
    coverage_note: str | None = None,
) -> EvaluationAssignment | None:
    if not evaluator_id:
        return None

    _dedupe_assignment_rows(period_id, employee_id, manager_level)

    existing_rows = (
        EvaluationAssignment.query
        .filter_by(
            period_id=period_id,
            employee_id=employee_id,
            manager_level=manager_level,
        )
        .order_by(EvaluationAssignment.id.desc())
        .all()
    )

    if existing_rows:
        row = existing_rows[0]
        changed = False
        if row.evaluator_id != evaluator_id:
            row.evaluator_id = evaluator_id
            changed = True
        if getattr(row, "original_evaluator_id", None) != (original_evaluator_id or evaluator_id):
            row.original_evaluator_id = original_evaluator_id or evaluator_id
            changed = True
        if getattr(row, "delegation_id", None) != delegation_id:
            row.delegation_id = delegation_id
            changed = True
        if getattr(row, "assignment_source", None) != assignment_source:
            row.assignment_source = assignment_source
            changed = True
        if getattr(row, "coverage_note", None) != coverage_note:
            row.coverage_note = coverage_note
            changed = True
        if not row.status:
            row.status = "bekliyor"
            changed = True
        expected_due_date = build_assignment_due_date(period, getattr(row, "assigned_at", None)) if period is not None else getattr(row, 'due_date', None)
        if getattr(row, "due_date", None) != expected_due_date:
            row.due_date = expected_due_date
            changed = True
        if changed:
            db.session.add(row)
            db.session.flush()
        return row

    assignment = EvaluationAssignment(
        period_id=period_id,
        employee_id=employee_id,
        evaluator_id=evaluator_id,
        original_evaluator_id=original_evaluator_id or evaluator_id,
        delegation_id=delegation_id,
        assignment_source=assignment_source,
        coverage_note=coverage_note,
        manager_level=manager_level,
        status="bekliyor",
        due_date=build_assignment_due_date(period, None) if period is not None else None,
    )
    db.session.add(assignment)
    db.session.flush()
    return assignment

def create_assignment_coverage_log(
    *,
    period_id: int,
    employee_id: int,
    event_type: str,
    reason: str | None = None,
    manager_level: int | None = None,
    event_scope: str = "generation",
    severity: str = "warning",
    run_key: str | None = None,
    original_evaluator_id: int | None = None,
    acting_evaluator_id: int | None = None,
    delegation_id: int | None = None,
    created_by_user_id: int | None = None,
) -> AssignmentCoverageLog:
    row = AssignmentCoverageLog(
        period_id=period_id,
        employee_id=employee_id,
        manager_level=manager_level,
        event_scope=event_scope or "generation",
        event_type=event_type,
        severity=severity or "warning",
        reason=reason or None,
        run_key=run_key or None,
        original_evaluator_id=original_evaluator_id,
        acting_evaluator_id=acting_evaluator_id,
        delegation_id=delegation_id,
        created_by_user_id=created_by_user_id,
    )
    db.session.add(row)
    return row

def build_assignment_log_severity_summary(log_rows: list[AssignmentCoverageLog]) -> dict[str, int]:
    summary = {'info': 0, 'warning': 0, 'error': 0}
    for row in log_rows:
        severity = _safe_str(getattr(row, 'severity', None)).lower() or 'warning'
        if severity not in summary:
            severity = 'warning'
        summary[severity] += 1
    return summary


def build_assignment_log_summary(log_rows: list[AssignmentCoverageLog]) -> dict[str, int]:
    summary = {
        "delegated": 0,
        "uncovered": 0,
        "exempted": 0,
        "chain_issue": 0,
        "warning": 0,
        "generated": 0,
        "cleared": 0,
        "special_case": 0,
    }
    for row in log_rows:
        key = _safe_str(getattr(row, "event_type", "")).lower()
        if is_informational_special_case(getattr(row, "reason", None), key):
            summary["special_case"] += 1
            continue
        if key in summary:
            summary[key] += 1
    return summary

def get_latest_assignment_generation_logs(
    period_id: int,
    limit: int = 200,
    employee_ids: list[int] | None = None,
) -> dict[str, Any]:
    latest = (
        AssignmentCoverageLog.query
        .filter_by(period_id=period_id, event_scope="generation")
        .order_by(AssignmentCoverageLog.created_at.desc(), AssignmentCoverageLog.id.desc())
        .first()
    )
    if not latest:
        return {"run_key": None, "created_at": None, "rows": [], "summary": build_assignment_log_summary([]), "severity_summary": build_assignment_log_severity_summary([])}

    if employee_ids is not None and not employee_ids:
        return {
            "run_key": _safe_str(getattr(latest, "run_key", "")) or None,
            "created_at": getattr(latest, "created_at", None),
            "rows": [],
            "summary": build_assignment_log_summary([]),
            "severity_summary": build_assignment_log_severity_summary([]),
        }

    query = (
        AssignmentCoverageLog.query
        .filter_by(period_id=period_id, event_scope="generation")
        .order_by(AssignmentCoverageLog.created_at.desc(), AssignmentCoverageLog.id.desc())
    )
    latest_run_key = _safe_str(getattr(latest, "run_key", ""))
    if latest_run_key:
        query = query.filter(AssignmentCoverageLog.run_key == latest_run_key)
    if employee_ids is not None:
        query = query.filter(AssignmentCoverageLog.employee_id.in_(employee_ids))

    rows = query.limit(limit).all()
    return {
        "run_key": latest_run_key or None,
        "created_at": getattr(latest, "created_at", None),
        "rows": rows,
        "summary": build_assignment_log_summary(rows),
        "severity_summary": build_assignment_log_severity_summary(rows),
    }

def build_assignment_unit_summary(
    log_rows: list[AssignmentCoverageLog],
    top_n: int | None = 10,
) -> list[dict[str, Any]]:
    buckets: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "unit_name": "Tanımsız",
        "log_count": 0,
        "delegated": 0,
        "uncovered": 0,
        "exempted": 0,
        "chain_issue": 0,
        "warning": 0,
        "generated": 0,
        "cleared": 0,
        "special_case": 0,
        "risk_score": 0,
    })

    for row in log_rows:
        employee = getattr(row, "employee", None)
        unit_name = (
            _safe_str(getattr(employee, "birim", None))
            or _safe_str(getattr(employee, "ust_birim", None))
            or "Tanımsız"
        )
        bucket = buckets[unit_name]
        bucket["unit_name"] = unit_name
        bucket["log_count"] += 1

        event_key = _safe_str(getattr(row, "event_type", "")).lower()
        if is_informational_special_case(getattr(row, "reason", None), event_key):
            bucket["special_case"] += 1
            continue
        if event_key in bucket:
            bucket[event_key] += 1

    rows = []
    for bucket in buckets.values():
        bucket["risk_score"] = (
            int(bucket.get("uncovered", 0)) * 4
            + int(bucket.get("chain_issue", 0)) * 3
            + int(bucket.get("exempted", 0)) * 2
            + int(bucket.get("warning", 0))
        )
        rows.append(bucket)

    rows.sort(
        key=lambda item: (
            int(item.get("risk_score", 0)),
            int(item.get("uncovered", 0)),
            int(item.get("chain_issue", 0)),
            int(item.get("exempted", 0)),
            int(item.get("log_count", 0)),
            item.get("unit_name", "").lower(),
        ),
        reverse=True,
    )
    return rows[:top_n] if top_n else rows

def sync_assignments_for_employee(
    period_id: int,
    employee: User,
    chain: ManagerChain,
    coverage_resolutions: dict[int, DelegationResolution] | None = None,
) -> int:
    created = 0
    coverage_resolutions = coverage_resolutions or {}
    original_map = {
        1: chain.manager_1_id,
        2: chain.manager_2_id,
        3: chain.manager_3_id if chain.level_3_enabled else None,
    }
    wanted = {
        level: (
            coverage_resolutions.get(level).acting_manager_id
            if coverage_resolutions.get(level)
            else original_id
        )
        for level, original_id in original_map.items()
    }

    existing = EvaluationAssignment.query.filter_by(period_id=period_id, employee_id=employee.id).all()
    for row in existing:
        if wanted.get(row.manager_level) != row.evaluator_id:
            db.session.delete(row)

    for level, evaluator_id in wanted.items():
        resolution = coverage_resolutions.get(level)
        row = ensure_assignment(
            period_id,
            employee.id,
            evaluator_id,
            level,
            original_evaluator_id=(resolution.original_manager_id if resolution else original_map.get(level)),
            delegation_id=(resolution.delegation_id if resolution else None),
            assignment_source=(resolution.source if resolution else "direct"),
            coverage_note=(resolution.note if resolution else None),
            period=get_period(period_id),
        )
        if row and row.id:
            created += 1

    return created

def generate_assignments_for_active_period(period_id: int | None = None, actor_user_id: int | None = None) -> dict[str, Any]:
    """Legacy public entrypoint backed by the V2 assignment synchronizer.

    Bu import bilerek fonksiyon icine alindi. Uygulama acilisinda
    app.services.performance.assignments -> app.services.performance_v2 ->
    publish_preflight_rules -> app.performance route zinciri birbirini erken
    yuklediginde circular import olusuyordu. Lazy import sayesinde app/flask db
    acilisi once tamamlanir; V2 senkron yalnizca gorev uretimi cagrilinca yuklenir.
    """

    from app.services.performance_v2 import sync_assignments_v2_for_period
    return sync_assignments_v2_for_period(period_id=period_id, actor_user_id=actor_user_id)

__all__ = [
    '_dedupe_assignment_rows', '_dedupe_item_rows', 'ensure_evaluation_record',
    'ensure_assignment', 'create_assignment_coverage_log', 'build_assignment_log_summary', 'build_assignment_log_severity_summary',
    'get_latest_assignment_generation_logs', 'build_assignment_unit_summary',
    'sync_assignments_for_employee', 'generate_assignments_for_active_period',
    '_split_chain_issues', '_enforce_required_chain_levels',
]