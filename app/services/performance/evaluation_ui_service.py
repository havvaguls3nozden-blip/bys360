from __future__ import annotations

import logging

from sqlalchemy import tuple_

from app.models import (
    EvaluationAssignment,
    PerformanceCriteria,
    PerformanceEvaluation,
    PerformanceEvaluationItem,
)
from app.services.performance.category_stats import build_category_average_for_evaluation
from app.services.publish_service import get_evaluation_visibility_state
from app.view_helpers import build_surface_scope_context

from .scoring import calculate_preview_total_100

logger = logging.getLogger(__name__)


def humanize_evaluation_save_error(exc: Exception) -> str:
    raw_message = str(exc).strip() or exc.__class__.__name__
    lowered = raw_message.lower()

    known_messages = (
        "en az bir kriter puanı girilmelidir.",
        "puan alanı boş bırakılamaz.",
        "geçersiz amir seviyesi.",
        "dönem bulunamadı.",
        "personel bulunamadı.",
        "bu değerlendirme görevi size ait değil veya kayıt bulunamadı.",
    )
    if raw_message in known_messages:
        return raw_message

    if "performanceevaluationitem" in lowered:
        return "Değerlendirme kalemleri kaydedilirken servis katmanında eksik model bağı tespit edildi. Hotfix uygulandıktan sonra tekrar deneyin."
    if "evaluationassignment" in lowered:
        return "Değerlendirme görevi okunurken görev kaydı bağı eksik göründü. Sayfayı yenileyip tekrar deneyin."
    if "integrityerror" in lowered or "unique constraint" in lowered:
        return "Aynı kriter için yinelenen kayıt oluştu. Sistem kayıtları tekilleştirip yeniden denemenizi bekliyor."
    if "nameerror" in lowered:
        return "Performans modülünde eksik servis bağı algılandı. Son hotfix paketi uygulanınca bu hata kaybolur."

    return raw_message


def assignment_pair_key(assignment) -> tuple[int | None, int | None]:
    return getattr(assignment, "period_id", None), getattr(assignment, "employee_id", None)


def build_assignment_visibility_context(assignments):
    pair_keys = {
        assignment_pair_key(assignment)
        for assignment in assignments
        if getattr(assignment, "period_id", None) and getattr(assignment, "employee_id", None)
    }
    if not pair_keys:
        return {"evaluation_map": {}, "level_3_pairs": set()}

    pair_rows = list(pair_keys)
    evaluation_rows = (
        PerformanceEvaluation.query
        .filter(tuple_(PerformanceEvaluation.period_id, PerformanceEvaluation.employee_id).in_(pair_rows))
        .all()
    )
    evaluation_map = {(row.period_id, row.employee_id): row for row in evaluation_rows}

    level_3_rows = (
        EvaluationAssignment.query
        .filter(
            EvaluationAssignment.manager_level == 3,
            tuple_(EvaluationAssignment.period_id, EvaluationAssignment.employee_id).in_(pair_rows),
        )
        .with_entities(EvaluationAssignment.period_id, EvaluationAssignment.employee_id)
        .all()
    )
    level_3_pairs = {(period_id, employee_id) for period_id, employee_id in level_3_rows}
    return {"evaluation_map": evaluation_map, "level_3_pairs": level_3_pairs}


def assignment_visible_for_actor(assignment, admin_mode: bool = False, visibility_ctx=None):
    if admin_mode:
        return True

    pair_key = assignment_pair_key(assignment)
    if visibility_ctx:
        evaluation = visibility_ctx.get("evaluation_map", {}).get(pair_key)
        has_level_3_assignment = pair_key in visibility_ctx.get("level_3_pairs", set())
    else:
        evaluation = PerformanceEvaluation.query.filter_by(
            period_id=assignment.period_id,
            employee_id=assignment.employee_id,
        ).first()
        has_level_3_assignment = bool(
            EvaluationAssignment.query.filter_by(
                period_id=assignment.period_id,
                employee_id=assignment.employee_id,
                manager_level=3,
            ).first()
        )

    if not evaluation:
        if assignment.manager_level == 3:
            return has_level_3_assignment
        if assignment.manager_level == 2:
            return not has_level_3_assignment
        if assignment.manager_level == 1:
            return not has_level_3_assignment
        return False

    has_level_3_actor = bool(getattr(evaluation, "level_3_evaluator_id", None)) or has_level_3_assignment
    has_level_2_actor = bool(getattr(evaluation, "level_2_evaluator_id", None))

    if assignment.manager_level == 3:
        return has_level_3_actor
    if assignment.manager_level == 2:
        return ((not has_level_3_actor) or bool(getattr(evaluation, "level_3_completed", False)))
    if assignment.manager_level == 1:
        if has_level_3_actor and not bool(getattr(evaluation, "level_3_completed", False)):
            return False
        return not (has_level_2_actor and not bool(getattr(evaluation, "level_2_completed", False)))
    return True


def filter_visible_assignments(assignments, admin_mode: bool = False):
    if admin_mode:
        return list(assignments)
    visibility_ctx = build_assignment_visibility_context(assignments)
    return [
        assignment
        for assignment in assignments
        if assignment_visible_for_actor(assignment, admin_mode=False, visibility_ctx=visibility_ctx)
    ]


def can_access_assignment_for_actor(assignment, actor) -> bool:
    if not assignment or not actor or not getattr(actor, "id", None):
        return False
    if assignment.evaluator_id == actor.id:
        return True

    role = (getattr(actor, "role", "") or "").strip().lower()
    privileged_roles = {"admin", "baskan", "baskan_yardimcisi", "grup_baskani", "mali_musavir", "koordinator", "birim_sorumlusu"}
    if role not in privileged_roles:
        return False

    scope_ctx = build_surface_scope_context(actor, None)
    allowed_employee_ids = set(scope_ctx.get("employee_ids") or [])
    if getattr(assignment, "employee_id", None) in allowed_employee_ids:
        return True

    return role in {"admin", "baskan", "baskan_yardimcisi"}


def build_employee_cards(assignments, include_coverage: bool = False):
    grouped = {}
    for assignment in assignments:
        employee = assignment.employee
        if not employee:
            continue

        card = grouped.setdefault(employee.id, {
            "employee": employee,
            "assignments": [],
            "pending_count": 0,
            "partial_count": 0,
            "completed_count": 0,
            "summary_status": "",
            "summary_label": "",
            "summary_class": "",
            "progress_percent": 0,
            "last_activity_at": None,
            "workflow_counts": {},
            "workflow_summary": "",
        })

        if include_coverage:
            card.setdefault("delegated_count", 0)
            card.setdefault("uncovered_count", 0)
            card.setdefault("direct_count", 0)
            card.setdefault("coverage_notes", [])
            card.setdefault("coverage_label", "")
            card.setdefault("coverage_class", "direct")

        card["assignments"].append(assignment)
        workflow_key = getattr(assignment, "workflow_key", "")
        if workflow_key:
            card["workflow_counts"][workflow_key] = card["workflow_counts"].get(workflow_key, 0) + 1

        if assignment.status == "bekliyor":
            card["pending_count"] += 1
        elif assignment.status == "kismen_tamamlandi":
            card["partial_count"] += 1
        elif assignment.status == "tamamlandi":
            card["completed_count"] += 1

        if include_coverage:
            if assignment.assignment_source == "delegated":
                card["delegated_count"] += 1
                if assignment.original_evaluator and assignment.evaluator:
                    card["coverage_notes"].append(
                        f"{assignment.manager_level}. amir görevi {assignment.original_evaluator.full_name} yerine {assignment.evaluator.full_name} üzerinde."
                    )
            elif assignment.assignment_source == "uncovered":
                card["uncovered_count"] += 1
                if assignment.coverage_note:
                    card["coverage_notes"].append(assignment.coverage_note)
            else:
                card["direct_count"] += 1

        candidate_dates = [
            getattr(assignment, "completed_at", None),
            getattr(assignment, "updated_at", None),
            getattr(assignment, "assigned_at", None),
            getattr(assignment, "created_at", None),
        ]
        candidate_dates = [value for value in candidate_dates if value is not None]
        if candidate_dates:
            latest = max(candidate_dates)
            if card["last_activity_at"] is None or latest > card["last_activity_at"]:
                card["last_activity_at"] = latest

    employee_cards = list(grouped.values())
    employee_cards.sort(
        key=lambda card: (
            (card["employee"].ad or "").lower(),
            (card["employee"].soyad or "").lower(),
            card["employee"].id,
        )
    )

    order_map = {3: 1, 2: 2, 1: 3}
    for card in employee_cards:
        card["assignments"].sort(key=lambda assignment: (order_map.get((assignment.manager_level or 99), 99), -(assignment.id or 0)))
        total_tasks = len(card["assignments"])
        completed_tasks = card["completed_count"]
        partial_tasks = card["partial_count"]
        pending_tasks = card["pending_count"]
        card["progress_percent"] = round(((completed_tasks + (partial_tasks * 0.5)) / total_tasks) * 100) if total_tasks > 0 else 0
        card["workflow_summary"] = max(card["workflow_counts"].items(), key=lambda item: item[1])[0] if card["workflow_counts"] else ""

        if pending_tasks == total_tasks and total_tasks > 0:
            card["summary_status"] = "danger"
            card["summary_label"] = "Tüm görevler bekliyor"
            card["summary_class"] = "danger"
        elif pending_tasks > 0:
            card["summary_status"] = "danger"
            card["summary_label"] = "Öncelikli takip gerekli"
            card["summary_class"] = "danger"
        elif partial_tasks > 0:
            card["summary_status"] = "warning"
            card["summary_label"] = "Kısmi ilerleme var"
            card["summary_class"] = "warning"
        elif completed_tasks == total_tasks and total_tasks > 0:
            card["summary_status"] = "success"
            card["summary_label"] = "Tüm görevler tamamlandı"
            card["summary_class"] = "success"
        else:
            card["summary_status"] = "neutral"
            card["summary_label"] = "Durum bilgisi yok"
            card["summary_class"] = "neutral"

        if include_coverage:
            if card["delegated_count"] and not card["uncovered_count"]:
                card["coverage_label"] = f"{card['delegated_count']} görev vekâletle ilerliyor"
                card["coverage_class"] = "delegated"
            elif card["uncovered_count"]:
                card["coverage_label"] = f"{card['uncovered_count']} görevde kapsama sorunu var"
                card["coverage_class"] = "uncovered"
            else:
                card["coverage_label"] = "Görevler doğrudan asıl amirde"
                card["coverage_class"] = "direct"
            card["coverage_notes"] = card["coverage_notes"][:3]

    return employee_cards


def build_level_total_preview(criteria_list, form_data):
    criteria_weight_map = {int(criteria.id): float(criteria.weight or 0) for criteria in criteria_list}
    item_payloads = []
    raw_scores = []
    for criteria in criteria_list:
        raw_score = form_data.get(f"score_{criteria.id}")
        if raw_score in (None, ""):
            continue
        try:
            numeric = float(raw_score)
        except (TypeError, ValueError):
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/performance/evaluation_ui_service.py:285)")
            continue
        raw_scores.append(numeric)
        item_payloads.append({
            "criteria_id": criteria.id,
            "score": numeric,
        })
    return calculate_preview_total_100(item_payloads, criteria_weight_map), raw_scores


def build_scorecard_redirect_params(scope_ctx, selected_period_id=None):
    params = {"scope": scope_ctx.get("selected_scope")}
    if selected_period_id:
        params["period_id"] = selected_period_id
    return params


def build_scorecard_detail_row(evaluation, visibility):
    items = (
        PerformanceEvaluationItem.query
        .join(PerformanceCriteria, PerformanceCriteria.id == PerformanceEvaluationItem.criteria_id)
        .filter(PerformanceEvaluationItem.evaluation_id == evaluation.id)
        .order_by(
            PerformanceEvaluationItem.manager_level.asc(),
            PerformanceCriteria.sort_order.asc(),
            PerformanceCriteria.id.asc(),
        )
        .all()
    )

    level_1_items = []
    level_2_items = []
    level_3_items = []
    for item in items:
        if item.manager_level == 1:
            level_1_items.append(item)
        elif item.manager_level == 2:
            level_2_items.append(item)
        elif item.manager_level == 3:
            level_3_items.append(item)

    return {
        "evaluation": evaluation,
        "visibility": visibility,
        "level_1_items": level_1_items,
        "level_2_items": level_2_items,
        "level_3_items": level_3_items,
        "level_1_comment": getattr(evaluation, "level_1_general_comment", None) or getattr(evaluation, "level_1_comment", None) or "",
        "level_2_comment": getattr(evaluation, "level_2_general_comment", None) or getattr(evaluation, "level_2_comment", None) or "",
        "level_3_comment": getattr(evaluation, "level_3_general_comment", None) or getattr(evaluation, "level_3_comment", None) or "",
        "category_average": build_category_average_for_evaluation(evaluation),  # BYS360_PHASE2_SCORECARD_DETAIL_CATEGORY_AVERAGE_NO_DETAILS
    }


def build_scorecard_detail_context(*, evaluation, actor, selected_scope=None, selected_period_id=None):
    scope_ctx = build_surface_scope_context(actor, selected_scope)
    allowed_employee_ids = set(scope_ctx.get("employee_ids") or [])
    visibility = get_evaluation_visibility_state(
        evaluation,
        actor,
        allowed_employee_ids=allowed_employee_ids,
    )
    # BYS360_PHASE3_6_DETAIL_PEER_PUBLISHED_GUARD
    try:
        from app.services.performance.peer_published_score_visibility import (
            enforce_peer_published_detail_visibility,
        )
        visibility = enforce_peer_published_detail_visibility(
            visibility,
            evaluation=evaluation,
            actor=actor,
            scope_ctx=scope_ctx,
        )
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        import logging
        logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/performance/evaluation_ui_service.py")
    return {
        "scope_ctx": scope_ctx,
        "allowed_employee_ids": allowed_employee_ids,
        "visibility": visibility,
        "redirect_params": build_scorecard_redirect_params(scope_ctx, selected_period_id),
        "detail_row": build_scorecard_detail_row(evaluation, visibility),
    }