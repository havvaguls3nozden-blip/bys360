from __future__ import annotations

from flask import flash, redirect, request, url_for
from flask_login import current_user

from app.extensions import db
from app.services.evaluation_workflow_service import (
    can_level_1_edit,
    complete_level_2,
    complete_level_3,
    return_to_level_1,
    submit_to_level_2,
    withdraw_from_level_2,
)
from app.services.performance.history import log_evaluation_action
from app.services.performance_service import (
    save_evaluation_level,
    validate_general_comment_requirements,
    validate_score_value,
)

from .evaluation_ui_service import build_level_total_preview


def redirect_to_assignment_form(assignment_id: int, *, saved: bool = False):
    params = {"assignment_id": assignment_id}
    if saved:
        params["saved"] = 1
    return redirect(url_for("main.performance_evaluate", **params))


def handle_pre_save_workflow_action(*, action, evaluation, assignment, level_1_assignment, level_2_assignment):
    if action == "withdraw_level_1":
        previous_workflow_status = getattr(evaluation, "workflow_status", None)
        if assignment.manager_level != 2 or not level_1_assignment:
            flash("Geri çekme işlemi için uygun görev bulunamadı.", "warning")
            return redirect(request.url)
        withdraw_note = (request.form.get("withdraw_note") or "").strip()
        withdraw_from_level_2(evaluation, level_1_assignment, level_2_assignment or assignment)
        log_evaluation_action(
            evaluation,
            action_type="WITHDRAWN",
            actor_user_id=current_user.id,
            actor_level=2,
            from_status=previous_workflow_status,
            to_status=evaluation.workflow_status,
            note=withdraw_note or "2. amir gönderimi geri çekti.",
        )
        db.session.commit()
        flash("1. amir görmeden önce kayıt geri çekildi. Şimdi tekrar düzenleyebilirsiniz.", "success")
        return redirect_to_assignment_form(assignment.id)

    if action == "return_to_level_1":
        previous_workflow_status = getattr(evaluation, "workflow_status", None)
        if assignment.manager_level != 1 or not level_1_assignment or not level_2_assignment:
            flash("İade işlemi için gerekli zincir bulunamadı.", "warning")
            return redirect(request.url)
        return_note = (request.form.get("return_note") or "").strip()
        return_to_level_1(evaluation, level_1_assignment, level_2_assignment, current_user.id, return_note)
        log_evaluation_action(
            evaluation,
            action_type="RETURNED_BY_LEVEL_1",
            actor_user_id=current_user.id,
            actor_level=1,
            from_status=previous_workflow_status,
            to_status=evaluation.workflow_status,
            note=return_note,
        )
        db.session.commit()
        flash("Değerlendirme 2. amire iade edildi.", "success")
        return redirect(url_for("main.performance_tasks"))

    return None


def handle_level_3_comment_only(*, evaluation, assignment, general_comment):
    if not general_comment:
        flash("3. amir yorumcu modunda genel görüş zorunludur.", "warning")
        return redirect(request.url)

    previous_workflow_status = getattr(evaluation, "workflow_status", None)
    evaluation = save_evaluation_level(
        period_id=assignment.period_id,
        employee_id=assignment.employee_id,
        manager_level=3,
        evaluator_id=assignment.evaluator_id,
        item_payloads=[],
        general_comment=general_comment,
        completed=True,
    )
    complete_level_3(evaluation, assignment)
    log_evaluation_action(
        evaluation,
        action_type="COMPLETED_BY_LEVEL_3",
        actor_user_id=current_user.id,
        actor_level=3,
        from_status=previous_workflow_status,
        to_status=evaluation.workflow_status,
        note=general_comment,
    )
    db.session.commit()
    next_label = "2. amire" if bool(getattr(evaluation, "level_2_evaluator_id", None)) else "1. amire"
    flash(f"3. amir üst görüşü kaydedildi ve zincir {next_label} açıldı.", "success")
    return redirect(url_for("main.performance_tasks"))


def collect_item_payloads(criteria_list, form_data):
    item_payloads = []
    for criteria in criteria_list:
        raw_score = form_data.get(f"score_{criteria.id}")
        item_comment = (form_data.get(f"comment_{criteria.id}") or "").strip()
        if raw_score in (None, ""):
            continue
        try:
            score_value = validate_score_value(float(raw_score))
        except ValueError as exc:
            flash(str(exc), "warning")
            return None
        if score_value in (1.0, 5.0) and not item_comment:
            flash(f"{criteria.name} kriterinde 1 veya 5 puan için açıklama zorunludur.", "warning")
            return None
        item_payloads.append({
            "criteria_id": criteria.id,
            "score": score_value,
            "comment": item_comment,
            "strength_note": "",
            "justification": item_comment,
        })
    return item_payloads


def validate_save_request(*, assignment, evaluation, criteria_list, requires_level_2_comment, level_3_scoring_enabled: bool = False):
    general_comment = (request.form.get("general_comment") or "").strip()

    if assignment.manager_level == 1 and not can_level_1_edit(evaluation):
        flash("2. amir değerlendirmeyi gördüğü için 1. amir kaydı artık doğrudan değiştirilemez. 2. amirin iadesi gerekir.", "warning")
        return None, None, None, redirect(request.url)

    item_payloads = collect_item_payloads(criteria_list, request.form)
    if item_payloads is None:
        return None, None, None, redirect(request.url)

    if not item_payloads and (assignment.manager_level != 3 or level_3_scoring_enabled):
        flash("En az bir kriter için puan girmelisiniz.", "warning")
        return None, None, None, redirect(request.url)

    preview_level_total, preview_raw_scores = build_level_total_preview(criteria_list, request.form)
    try:
        validate_general_comment_requirements(
            manager_level=assignment.manager_level,
            general_comment=general_comment,
            level_total_100=preview_level_total,
            raw_scores=preview_raw_scores,
            requires_level_2_comment=requires_level_2_comment,
        )
    except ValueError as exc:
        flash(str(exc), "warning")
        return None, None, None, redirect(request.url)

    return general_comment, item_payloads, preview_level_total, None


def persist_level_save(*, action, evaluation, assignment, item_payloads, general_comment, level_1_assignment, level_2_assignment):
    completed_flag = action in {"submit_to_level_2", "complete_level_2", "save_level_3"}
    previous_workflow_status = getattr(evaluation, "workflow_status", None)
    evaluation = save_evaluation_level(
        period_id=assignment.period_id,
        employee_id=assignment.employee_id,
        manager_level=assignment.manager_level,
        evaluator_id=assignment.evaluator_id,
        item_payloads=item_payloads,
        general_comment=general_comment,
        completed=completed_flag if assignment.manager_level in {1, 2} else True,
    )

    if assignment.manager_level == 1:
        if action == "complete_level_2":
            complete_level_2(evaluation, assignment)
            log_evaluation_action(
                evaluation,
                action_type="COMPLETED_BY_LEVEL_1",
                actor_user_id=current_user.id,
                actor_level=1,
                from_status=previous_workflow_status,
                to_status=evaluation.workflow_status,
                note=general_comment,
            )
            db.session.commit()
            flash("1. amir değerlendirmesi tamamlandı.", "success")
            return redirect_to_assignment_form(assignment.id, saved=True)

        assignment.status = "kismen_tamamlandi"
        assignment.completed_at = None
        db.session.add(assignment)
        log_evaluation_action(
            evaluation,
            action_type="SAVED_BY_LEVEL_1",
            actor_user_id=current_user.id,
            actor_level=1,
            from_status=previous_workflow_status,
            to_status=getattr(evaluation, "workflow_status", None),
            note=general_comment,
        )
        db.session.commit()
        flash("1. amir taslağı kaydedildi.", "success")
        return redirect_to_assignment_form(assignment.id, saved=True)

    if assignment.manager_level == 2:
        if action == "submit_to_level_2":
            submit_to_level_2(evaluation, level_1_assignment, level_2_assignment or assignment)
            log_evaluation_action(
                evaluation,
                action_type="SUBMITTED_TO_LEVEL_1",
                actor_user_id=current_user.id,
                actor_level=2,
                from_status=previous_workflow_status,
                to_status=evaluation.workflow_status,
                note=general_comment,
            )
            db.session.commit()
            flash("2. amir notu 1. amire gönderildi.", "success")
            return redirect_to_assignment_form(assignment.id, saved=True)

        assignment.status = "kismen_tamamlandi"
        db.session.add(assignment)
        log_evaluation_action(
            evaluation,
            action_type="SAVED_BY_LEVEL_2",
            actor_user_id=current_user.id,
            actor_level=2,
            from_status=previous_workflow_status,
            to_status=getattr(evaluation, "workflow_status", None),
            note=general_comment,
        )
        db.session.commit()
        flash("2. amir taslağı kaydedildi.", "success")
        return redirect_to_assignment_form(assignment.id, saved=True)

    complete_level_3(evaluation, assignment)
    log_evaluation_action(
        evaluation,
        action_type="COMPLETED_BY_LEVEL_3",
        actor_user_id=current_user.id,
        actor_level=3,
        from_status=previous_workflow_status,
        to_status=evaluation.workflow_status,
        note=general_comment,
    )
    db.session.commit()
    next_label = "2. amire" if bool(getattr(evaluation, "level_2_evaluator_id", None)) else "1. amire"
    flash(f"3. amir değerlendirmesi kaydedildi ve zincir {next_label} açıldı.", "success")
    return redirect(url_for("main.performance_tasks"))