from __future__ import annotations

from flask import Response, current_app, flash, jsonify, redirect, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from app.extensions import db
from app.models import Survey, SurveyAssignment, SurveyQuestion, SurveyQuestionOption, SurveyResponse, User
from app.route_registry import main_bp
from app.route_support import consume_form_token, menu_key_required, safe_render
from app.services.message_service import notify_user as _notify_user
from app.services.message_service import survey_manager_allowed as _service_survey_manager_allowed
from app.services.message_service import user_matches_assignment as _service_user_matches_assignment
from app.services.surveys import (
    build_survey_state_row as _service_build_survey_state_row,
    get_assigned_surveys_for_user as _service_get_assigned_surveys_for_user,
    latest_response_for_user as _service_latest_response_for_user,
    matching_assignment_for_user as _service_matching_assignment_for_user,
    persist_survey_questions as _service_persist_survey_questions,
    survey_form_state_from_mapping as _service_survey_form_state_from_mapping,
    survey_question_attr as _service_survey_question_attr,
    survey_question_phase2_ready as _service_survey_question_phase2_ready,
    survey_response_phase2_ready as _service_survey_response_phase2_ready,
    survey_state_from_db as _service_survey_state_from_db,
    table_columns as _service_table_columns,
    has_table_columns as _service_has_table_columns,
    active_user_count as _service_active_user_count,
    distinct_user_values as _service_distinct_user_values,
    estimate_survey_target_user_ids as _service_estimate_survey_target_user_ids,
    resolve_target_user_ids as _service_resolve_target_user_ids,
    selected_user_items_by_ids as _service_selected_user_items_by_ids,
    target_user_search_items as _service_target_user_search_items,
    user_item as _service_user_item,
    build_question_payload_dicts as _service_build_question_payload_dicts,
    build_survey_results_context as _service_build_survey_results_context,
    build_survey_results_csv_text as _service_build_survey_results_csv_text,
    latest_completed_label_for_survey as _service_latest_completed_label_for_survey,
    clean_target_values as _service_clean_target_values,
    dedup_preserve as _service_dedup_preserve,
    empty_survey_counts as _service_empty_survey_counts,
    format_survey_dt as _service_format_survey_dt,
    normalize_choice as _service_normalize_choice,
    safe_any_response_count as _service_safe_any_response_count,
    safe_assignment_count as _service_safe_assignment_count,
    safe_completed_response_count as _service_safe_completed_response_count,
    safe_question_count as _service_safe_question_count,
    safe_question_options as _service_safe_question_options,
    safe_question_answers as _service_safe_question_answers,
    safe_survey_questions as _service_safe_survey_questions,
    survey_question_compat_defaults as _service_survey_question_compat_defaults,
    survey_access_state as _service_survey_access_state,
    simple_completion_trend as _service_simple_completion_trend,
    survey_local_now as _service_survey_local_now,
    submit_survey_response as _service_submit_survey_response,
    archive_survey as _service_archive_survey,
    bulk_survey_action as _service_bulk_survey_action,
    close_survey as _service_close_survey,
    delete_survey_if_allowed as _service_delete_survey_if_allowed,
    publish_survey as _service_publish_survey,
    restore_survey as _service_restore_survey,
    unpublish_survey as _service_unpublish_survey,
)

from .shared import _log_communication_exception, _normalize_text_search, _parse_datetime_input, _question_option_id_set, _utcnow
import logging
logger = logging.getLogger(__name__)


try:
    from zoneinfo import ZoneInfo as _ZoneInfo
except Exception:  # pragma: no cover
    logger.exception("BYS360 V6C guarded exception | file=app/communication/surveys_routes.py | line=71")
    _ZoneInfo = None


def _survey_local_now():
    return _service_survey_local_now()

def _format_survey_dt(value):
    return _service_format_survey_dt(value)

def _survey_access_state(survey) -> tuple[bool, str]:
    result = _service_survey_access_state(survey)
    return bool(result.allowed), str(result.message or "")

def _render_survey_take(*, survey, questions, matched_assignment):
    from app.route_support import issue_form_token

    submit_token = issue_form_token("survey_submit", scope=f"{current_user.id}:{survey.id}")
    return safe_render(
        "survey_take.html",
        "<h3>Anket</h3>",
        survey=survey,
        questions=questions,
        matched_assignment=matched_assignment,
        submit_token=submit_token,
    )


def _survey_manager_allowed() -> bool:
    return _service_survey_manager_allowed(current_user)


def _survey_session_reset() -> None:
    try:
        db.session.rollback()
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/communication/surveys_routes.py)")


_SURVEY_SCHEMA_CACHE: dict[str, set[str]] = {}


def _table_columns(table_name: str) -> set[str]:
    return set(_service_table_columns(table_name))


def _has_table_columns(table_name: str, *columns: str) -> bool:
    return _service_has_table_columns(table_name, *columns)


def _survey_response_phase2_ready() -> bool:
    return _service_survey_response_phase2_ready()


def _survey_question_phase2_ready() -> bool:
    return _service_survey_question_phase2_ready()


def _survey_question_compat_defaults(question):
    return _service_survey_question_compat_defaults(question)


def _survey_question_attr(question, attr_name: str, default=None):
    return _service_survey_question_attr(question, attr_name, default)


def _safe_completed_response_count(survey_id: int) -> int:
    return _service_safe_completed_response_count(survey_id)


def _safe_any_response_count(survey_id: int) -> int:
    return _service_safe_any_response_count(survey_id)


def _safe_assignment_count(survey_id: int) -> int:
    return _service_safe_assignment_count(survey_id)


def _safe_question_count(survey_id: int) -> int:
    return _service_safe_question_count(survey_id)


def _safe_survey_questions(survey_id: int):
    return _service_safe_survey_questions(survey_id)


def _safe_question_options(question_id: int):
    return _service_safe_question_options(question_id)


def _safe_question_answers(question_id: int):
    return _service_safe_question_answers(question_id)


def _latest_response_for_user(survey_id: int, user_id: int, *, completed_only: bool = False):
    return _service_latest_response_for_user(survey_id, user_id, completed_only=completed_only)


def _survey_distinct_user_values(column) -> list[str]:
    return _service_distinct_user_values(
        column,
        reset_callback=_survey_session_reset,
        log_callback=lambda label, exc: _log_communication_exception(label, exc),
    )


def _survey_active_user_count() -> int:
    return _service_active_user_count(
        reset_callback=_survey_session_reset,
        log_callback=lambda label, exc: _log_communication_exception(label, exc),
    )


def _survey_user_item(user) -> dict[str, str]:
    return _service_user_item(user)


def _survey_selected_user_items(raw_user_ids) -> list[dict[str, str]]:
    return _service_selected_user_items_by_ids(
        raw_user_ids,
        reset_callback=_survey_session_reset,
        log_callback=lambda label, exc: _log_communication_exception(label, exc),
    )


def _survey_resolve_target_user_ids(target_type: str, raw_values) -> list[int]:
    return _service_resolve_target_user_ids(target_type, raw_values)


def _user_matches_assignment(assignment, user) -> bool:
    return _service_user_matches_assignment(assignment, user)


def _survey_row_matches_search(row, q: str) -> bool:
    haystack = " ".join([
        str(getattr(row.get("survey"), "title", "") or ""),
        str(getattr(row.get("survey"), "description", "") or ""),
        str(getattr(row.get("matched_assignment"), "target_type", "") or ""),
    ]).lower()
    return q.lower() in haystack if q else True


def _empty_survey_counts() -> dict[str, int]:
    return _service_empty_survey_counts()

_SURVEY_ALLOWED_TYPES = {"kurum_ici", "memnuniyet", "egitim", "nabiz", "geri_bildirim"}
_SURVEY_CREATE_ALLOWED_STATUSES = {"draft", "published", "closed"}
_SURVEY_EDIT_ALLOWED_STATUSES = {"draft", "published", "closed", "archived"}
_SURVEY_ALLOWED_TARGET_TYPES = {"all", "user", "role", "unit"}
_SURVEY_ALLOWED_QUESTION_TYPES = {"text", "single_choice", "multiple_choice", "rating_5", "rating_10", "yes_no"}
_SURVEY_ALLOWED_LOGIC_MODES = {"always", "conditional"}
_SURVEY_ALLOWED_LOGIC_OPERATORS = {"answered", "selected_option", "equals", "contains", "gte", "lte"}


def _survey_normalize_choice(value, allowed_values, default_value):
    return _service_normalize_choice(value, allowed_values, default_value)

def _survey_dedup_preserve(items):
    return _service_dedup_preserve(items)

def _survey_clean_target_values(target_type: str, raw_values, *, roles=None, birimler=None) -> list[str]:
    return _service_clean_target_values(target_type, raw_values, roles=roles, birimler=birimler)

def _survey_build_question_payloads(*, question_texts, question_types, question_requireds, option_blocks, helper_texts, logic_modes, logic_sources, logic_operators, logic_values):
    return _service_build_question_payload_dicts(
        question_texts=question_texts,
        question_types=question_types,
        question_requireds=question_requireds,
        option_blocks=option_blocks,
        helper_texts=helper_texts,
        logic_modes=logic_modes,
        logic_sources=logic_sources,
        logic_operators=logic_operators,
        logic_values=logic_values,
    )

def _survey_persist_questions(*, survey_id: int, question_payloads):
    return _service_persist_survey_questions(survey_id=survey_id, question_payloads=question_payloads)

def _survey_form_state_from_request():
    return _service_survey_form_state_from_mapping(request.form)


def _survey_state_from_db(survey, current_assignments=None, current_questions=None):
    return _service_survey_state_from_db(survey, current_assignments=current_assignments, current_questions=current_questions)


def _render_surveys_page(*, survey_rows, status_counts, current_status, search_query):
    return safe_render(
        "surveys_list.html",
        "<h3>Anketler</h3>",
        survey_rows=survey_rows,
        status_counts=status_counts,
        current_status=current_status,
        search_query=search_query,
        visible_survey_count=len(survey_rows),
    )


def _build_survey_state_row(survey, response):
    return _service_build_survey_state_row(survey, response)


def _get_assigned_surveys_for_user(user):
    return _service_get_assigned_surveys_for_user(
        user,
        latest_response_resolver=_latest_response_for_user,
        question_count_resolver=_safe_question_count,
    )


def _estimate_survey_target_user_ids(survey):
    return _service_estimate_survey_target_user_ids(survey)


@main_bp.route("/surveys")
@login_required
@menu_key_required("surveys")
def surveys_list():
    current_status = (request.args.get("status") or "all").strip().lower()
    if current_status not in {"all", "active", "completed", "upcoming", "expired"}:
        current_status = "all"
    q = _normalize_text_search(request.args.get("q"))

    try:
        all_rows = _get_assigned_surveys_for_user(current_user)
        status_counts = {
            "all": len(all_rows),
            "active": sum(1 for row in all_rows if row["state"]["key"] == "active"),
            "completed": sum(1 for row in all_rows if row["state"]["key"] == "completed"),
            "upcoming": sum(1 for row in all_rows if row["state"]["key"] == "upcoming"),
            "expired": sum(1 for row in all_rows if row["state"]["key"] == "expired"),
        }

        survey_rows = [row for row in all_rows if _survey_row_matches_search(row, q)]
        if current_status != "all":
            survey_rows = [row for row in survey_rows if row["state"]["key"] == current_status]

        return _render_surveys_page(
            survey_rows=survey_rows,
            status_counts=status_counts,
            current_status=current_status,
            search_query=q,
        )
    except Exception as exc:
        current_app.logger.exception("Anket listesi acilirken hata: %s", exc)
        flash("Anketler ekranı açılırken beklenmeyen bir şey oldu. Listeyi boş ama çalışır bıraktım.", "danger")
        return _render_surveys_page(
            survey_rows=[],
            status_counts=_empty_survey_counts(),
            current_status=current_status,
            search_query=q,
        )


@main_bp.route("/surveys/<int:survey_id>/take", methods=["GET"])
@login_required
@menu_key_required("surveys")
def survey_take(survey_id):
    survey = db.session.get(Survey, survey_id)
    survey_ok, survey_reason = _survey_access_state(survey)
    if not survey_ok:
        flash(survey_reason, "danger")
        return redirect(url_for("main.surveys_list"))

    matched_assignment = _service_matching_assignment_for_user(int(survey.id), current_user)

    if not matched_assignment:
        flash("Bu ankete erişim yetkiniz yok.", "danger")
        return redirect(url_for("main.surveys_list"))

    if not survey.allow_multiple_submissions and not survey.is_anonymous:
        existing_response = _latest_response_for_user(int(survey.id), int(current_user.id), completed_only=True)
        if existing_response:
            flash("Bu anketi daha önce tamamladınız.", "info")
            return redirect(url_for("main.surveys_list"))

    questions = _safe_survey_questions(int(survey.id))
    return _render_survey_take(survey=survey, questions=questions, matched_assignment=matched_assignment)


@main_bp.route("/surveys/<int:survey_id>/submit", methods=["POST"])
@login_required
@menu_key_required("surveys")
def survey_submit(survey_id):
    survey = db.session.get(Survey, survey_id)
    survey_ok, survey_reason = _survey_access_state(survey)
    if not survey_ok:
        flash(survey_reason, "danger")
        return redirect(url_for("main.surveys_list"))

    matched_assignment = _service_matching_assignment_for_user(int(survey.id), current_user)

    if not matched_assignment:
        flash("Bu anketi cevaplama yetkiniz yok.", "danger")
        return redirect(url_for("main.surveys_list"))

    if not survey.allow_multiple_submissions and not survey.is_anonymous:
        existing_response = _latest_response_for_user(int(survey.id), int(current_user.id), completed_only=True)
        if existing_response:
            flash("Bu anketi daha önce tamamladınız.", "info")
            return redirect(url_for("main.surveys_list"))

    questions = _safe_survey_questions(int(survey.id))

    try:
        if not consume_form_token("survey_submit", request.form.get("_form_token"), scope=f"{current_user.id}:{survey.id}"):
            flash("Bu anket yanıtı zaten işleme alınmış görünüyor. Listeyi yenileyip durumu kontrol edin.", "info")
            return redirect(url_for("main.surveys_list"))

        _service_submit_survey_response(
            survey=survey,
            current_user=current_user,
            matched_assignment=matched_assignment,
            questions=questions,
            form_data=request.form,
            question_option_id_resolver=_question_option_id_set,
        )
        flash("Anket yanıtınız kaydedildi.", "success")
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/surveys_routes.py | line=390")
        db.session.rollback()
        _log_communication_exception("survey_submit", exc, survey_id=survey.id, user_id=getattr(current_user, "id", None))
        flash(f"Anket gönderilirken hata oluştu: {exc}", "danger")
        return redirect(url_for("main.survey_take", survey_id=survey.id))

    return redirect(url_for("main.surveys_list"))


@main_bp.route("/survey-target-users")
@login_required
@menu_key_required("survey_manage")
def survey_target_users():
    if not _survey_manager_allowed():
        return jsonify({"ok": False, "message": "Bu alana erişim yetkiniz yok."}), 403

    query_text = (request.args.get("q") or "").strip()
    try:
        limit = int(request.args.get("limit") or 20)
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/surveys_routes.py | line=409")
        limit = 20
    return jsonify({"ok": True, "items": _service_target_user_search_items(query_text, limit=limit)})


@main_bp.route("/survey-manage")
@login_required
@menu_key_required("survey_manage")
def survey_manage():
    _survey_session_reset()

    if not _survey_manager_allowed():
        flash("Bu alana erişim yetkiniz yok.", "danger")
        return redirect(url_for("main.dashboard"))

    current_status = (request.args.get("status") or "all").strip().lower()
    all_surveys = Survey.query.order_by(Survey.created_at.desc(), Survey.id.desc()).all()

    status_counts = {
        "all": len(all_surveys),
        "draft": sum(1 for survey in all_surveys if (survey.status or "") == "draft"),
        "published": sum(1 for survey in all_surveys if (survey.status or "") == "published"),
        "closed": sum(1 for survey in all_surveys if (survey.status or "") == "closed"),
        "archived": sum(1 for survey in all_surveys if (survey.status or "") == "archived"),
    }

    surveys = all_surveys
    if current_status in {"draft", "published", "closed", "archived"}:
        surveys = [survey for survey in all_surveys if (survey.status or "") == current_status]

    survey_ids = [int(survey.id) for survey in surveys if getattr(survey, "id", None)]
    response_counts = {}
    assignment_counts = {}
    question_counts = {}
    if survey_ids:
        try:
            response_counts = {
                int(sid): int(count or 0)
                for sid, count in (
                    db.session.query(SurveyResponse.survey_id, func.count(SurveyResponse.id))
                    .filter(SurveyResponse.survey_id.in_(survey_ids), SurveyResponse.is_completed.is_(True))
                    .group_by(SurveyResponse.survey_id)
                    .all()
                )
            }
            assignment_counts = {
                int(sid): int(count or 0)
                for sid, count in (
                    db.session.query(SurveyAssignment.survey_id, func.count(SurveyAssignment.id))
                    .filter(SurveyAssignment.survey_id.in_(survey_ids))
                    .group_by(SurveyAssignment.survey_id)
                    .all()
                )
            }
            question_counts = {
                int(sid): int(count or 0)
                for sid, count in (
                    db.session.query(SurveyQuestion.survey_id, func.count(SurveyQuestion.id))
                    .filter(SurveyQuestion.survey_id.in_(survey_ids))
                    .group_by(SurveyQuestion.survey_id)
                    .all()
                )
            }
        except Exception as exc:
            logger.exception("BYS360 V6C guarded exception | file=app/communication/surveys_routes.py | line=472")
            _survey_session_reset()
            _log_communication_exception("survey_manage_counts", exc, survey_ids=survey_ids[:20])

    rows = []
    for survey in surveys:
        survey_id = int(getattr(survey, "id", 0) or 0)
        response_count = response_counts.get(survey_id, 0)
        assignment_count = assignment_counts.get(survey_id, 0)
        question_count = question_counts.get(survey_id, 0)
        state_label = {
            "draft": "Taslak",
            "published": "Yayımlanan",
            "closed": "Kapalı",
            "archived": "Arşiv",
        }.get((survey.status or "").strip().lower(), "Diğer")
        response_rate = round((response_count / assignment_count) * 100, 1) if assignment_count else 0
        rows.append(
            {
                "survey": survey,
                "response_count": response_count,
                "assignment_count": assignment_count,
                "question_count": question_count,
                "response_rate": response_rate,
                "state_label": state_label,
            }
        )

    _survey_session_reset()
    return safe_render(
        "survey_manage.html",
        "<h3>Anket Yönetimi</h3>",
        rows=rows,
        current_status=current_status,
        status_counts=status_counts,
    )


@main_bp.route("/survey-create", methods=["GET", "POST"])
@login_required
@menu_key_required("survey_manage")
def survey_create():
    _survey_session_reset()

    if not _survey_manager_allowed():
        flash("Bu alana erişim yetkiniz yok.", "danger")
        return redirect(url_for("main.dashboard"))

    birimler = _survey_distinct_user_values(User.birim)
    roles = _survey_distinct_user_values(User.role)
    active_user_count = _survey_active_user_count()

    if request.method == "POST":
        form_state = _survey_form_state_from_request()
        title = form_state.get("title", "")
        description = form_state.get("description", "")
        survey_type = _survey_normalize_choice(form_state.get("survey_type"), _SURVEY_ALLOWED_TYPES, "kurum_ici")
        is_anonymous = bool(form_state.get("is_anonymous"))
        allow_multiple_submissions = bool(form_state.get("allow_multiple_submissions"))
        status = _survey_normalize_choice(form_state.get("status"), _SURVEY_CREATE_ALLOWED_STATUSES, "draft")
        start_at_raw = form_state.get("start_at", "")
        end_at_raw = form_state.get("end_at", "")
        target_type = _survey_normalize_choice(form_state.get("target_type"), _SURVEY_ALLOWED_TARGET_TYPES, "all")
        target_values = form_state.get("target_values", [])

        try:
            if not title:
                raise ValueError("Anket başlığı zorunludur.")
            if len(title) > 255:
                raise ValueError("Anket başlığı çok uzun. Lütfen 255 karakteri aşmayın.")

            start_at = _parse_datetime_input(start_at_raw)
            end_at = _parse_datetime_input(end_at_raw)
            if start_at and end_at and end_at < start_at:
                raise ValueError("Bitiş tarihi başlangıç tarihinden önce olamaz.")

            cleaned_target_values = _survey_clean_target_values(target_type, target_values, roles=roles, birimler=birimler)
            if target_type != "all" and not cleaned_target_values:
                raise ValueError("Hedef kitle seçimi zorunludur.")

            question_payloads = _survey_build_question_payloads(
                question_texts=request.form.getlist("question_text[]"),
                question_types=request.form.getlist("question_type[]"),
                question_requireds=request.form.getlist("question_required[]"),
                option_blocks=request.form.getlist("question_options[]"),
                helper_texts=request.form.getlist("question_helper_text[]"),
                logic_modes=request.form.getlist("question_logic_mode[]"),
                logic_sources=request.form.getlist("question_logic_source[]"),
                logic_operators=request.form.getlist("question_logic_operator[]"),
                logic_values=request.form.getlist("question_logic_value[]"),
            )

            target_user_ids = []
            if status == "published":
                target_user_ids = _survey_resolve_target_user_ids(target_type, cleaned_target_values)
                if not target_user_ids:
                    raise ValueError("Seçilen hedef kitlede aktif kullanıcı bulunamadı. Anket taslak olarak kaydedilebilir veya hedef seçimi gözden geçirilebilir.")

            survey = Survey(
                title=title,
                description=description or None,
                survey_type=survey_type,
                created_by_user_id=current_user.id,
                is_anonymous=is_anonymous,
                allow_multiple_submissions=allow_multiple_submissions,
                start_at=start_at,
                end_at=end_at,
                status=status,
            )
            db.session.add(survey)
            db.session.flush()

            if target_type == "all":
                db.session.add(SurveyAssignment(survey_id=survey.id, target_type="all", target_value=None, assigned_at=_utcnow()))
            else:
                for value in cleaned_target_values:
                    db.session.add(SurveyAssignment(survey_id=survey.id, target_type=target_type, target_value=value, assigned_at=_utcnow()))

            _survey_persist_questions(survey_id=int(survey.id), question_payloads=question_payloads)

            if status == "published":
                for user_id in target_user_ids:
                    _notify_user(
                        user_id=user_id,
                        title="Yeni anket atandı",
                        body=f'"{survey.title}" başlıklı ankete yanıt vermeniz bekleniyor.',
                        notification_type="survey_assigned",
                        source_type="survey",
                        source_id=survey.id,
                        link_url=url_for("main.survey_take", survey_id=survey.id),
                        priority="normal",
                    )

            db.session.commit()
            flash("Anket başarıyla oluşturuldu.", "success")
            return redirect(url_for("main.survey_manage"))
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "warning")
        except Exception as exc:
            logger.exception("BYS360 V6C guarded exception | file=app/communication/surveys_routes.py | line=611")
            db.session.rollback()
            _log_communication_exception(
                "survey_create",
                exc,
                title=title,
                target_type=target_type,
                status=status,
                user_id=getattr(current_user, "id", None),
            )
            flash("Anket oluşturulurken beklenmeyen bir hata oluştu. Girdileriniz korunarak sayfa yeniden açıldı.", "danger")

    return safe_render(
        "survey_create.html",
        "<h3>Anket Oluştur</h3>",
        birimler=birimler,
        roles=roles,
        active_user_count=active_user_count,
        selected_user_items=_survey_selected_user_items(_survey_form_state_from_request().get("target_values", [])) if request.method == "POST" else [],
        form_state=_survey_form_state_from_request() if request.method == "POST" else None,
    )


@main_bp.route("/survey-edit/<int:survey_id>", methods=["GET", "POST"])

@login_required
@menu_key_required("survey_manage")
def survey_edit(survey_id):
    if not _survey_manager_allowed():
        flash("Bu alana erişim yetkiniz yok.", "danger")
        return redirect(url_for("main.dashboard"))

    survey = db.session.get(Survey, survey_id)
    if not survey:
        flash("Anket bulunamadı.", "danger")
        return redirect(url_for("main.survey_manage"))

    birimler = _survey_distinct_user_values(User.birim)
    roles = _survey_distinct_user_values(User.role)
    active_user_count = _survey_active_user_count()
    has_responses = _safe_completed_response_count(int(survey.id)) > 0

    if request.method == "POST":
        form_state = _survey_form_state_from_request()
        title = form_state.get("title", "")
        description = form_state.get("description", "")
        survey_type = _survey_normalize_choice(form_state.get("survey_type") or survey.survey_type, _SURVEY_ALLOWED_TYPES, "kurum_ici")
        is_anonymous = bool(form_state.get("is_anonymous"))
        allow_multiple_submissions = bool(form_state.get("allow_multiple_submissions"))
        status = _survey_normalize_choice(form_state.get("status") or survey.status, _SURVEY_EDIT_ALLOWED_STATUSES, "draft")
        start_at_raw = form_state.get("start_at", "")
        end_at_raw = form_state.get("end_at", "")
        target_type = _survey_normalize_choice(form_state.get("target_type"), _SURVEY_ALLOWED_TARGET_TYPES, "all")
        target_values = form_state.get("target_values", [])

        try:
            if not title:
                raise ValueError("Anket başlığı zorunludur.")
            if len(title) > 255:
                raise ValueError("Anket başlığı çok uzun. Lütfen 255 karakteri aşmayın.")

            parsed_start_at = _parse_datetime_input(start_at_raw)
            parsed_end_at = _parse_datetime_input(end_at_raw)
            if parsed_start_at and parsed_end_at and parsed_end_at < parsed_start_at:
                raise ValueError("Bitiş tarihi başlangıç tarihinden önce olamaz.")

            survey.title = title
            survey.description = description or None
            survey.survey_type = survey_type
            survey.start_at = parsed_start_at
            survey.end_at = parsed_end_at
            survey.status = status

            if not has_responses:
                survey.is_anonymous = is_anonymous
                survey.allow_multiple_submissions = allow_multiple_submissions

                cleaned_target_values = _survey_clean_target_values(target_type, target_values, roles=roles, birimler=birimler)
                if target_type != "all" and not cleaned_target_values:
                    raise ValueError("Hedef kitle seçimi zorunludur.")

                question_payloads = _survey_build_question_payloads(
                    question_texts=request.form.getlist("question_text[]"),
                    question_types=request.form.getlist("question_type[]"),
                    question_requireds=request.form.getlist("question_required[]"),
                    option_blocks=request.form.getlist("question_options[]"),
                    helper_texts=request.form.getlist("question_helper_text[]"),
                    logic_modes=request.form.getlist("question_logic_mode[]"),
                    logic_sources=request.form.getlist("question_logic_source[]"),
                    logic_operators=request.form.getlist("question_logic_operator[]"),
                    logic_values=request.form.getlist("question_logic_value[]"),
                )

                target_user_ids = []
                if survey.status == "published":
                    target_user_ids = _survey_resolve_target_user_ids(target_type, cleaned_target_values)
                    if not target_user_ids:
                        raise ValueError("Seçilen hedef kitlede aktif kullanıcı bulunamadı. Anket taslak olarak güncellenebilir veya hedef seçimi gözden geçirilebilir.")

                for assignment in survey.assignments.all():
                    db.session.delete(assignment)
                for question in _safe_survey_questions(int(survey.id)):
                    db.session.delete(question)
                db.session.flush()

                if target_type == "all":
                    db.session.add(SurveyAssignment(survey_id=survey.id, target_type="all", target_value=None, assigned_at=_utcnow()))
                else:
                    for value in cleaned_target_values:
                        db.session.add(SurveyAssignment(survey_id=survey.id, target_type=target_type, target_value=value, assigned_at=_utcnow()))

                _survey_persist_questions(survey_id=int(survey.id), question_payloads=question_payloads)

                if survey.status == "published":
                    for user_id in target_user_ids:
                        _notify_user(
                            user_id=user_id,
                            title="Anket güncellendi",
                            body=f'"{survey.title}" başlıklı anket güncellendi.',
                            notification_type="survey_assigned",
                            source_type="survey",
                            source_id=survey.id,
                            link_url=url_for("main.survey_take", survey_id=survey.id),
                            priority="normal",
                        )
            db.session.commit()
            flash("Anket güncellendi.", "success")
            return redirect(url_for("main.survey_manage"))
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), "warning")
        except Exception as exc:
            logger.exception("BYS360 V6C guarded exception | file=app/communication/surveys_routes.py | line=742")
            db.session.rollback()
            _log_communication_exception(
                "survey_edit",
                exc,
                survey_id=survey.id,
                has_responses=has_responses,
                user_id=getattr(current_user, "id", None),
            )
            flash("Anket güncellenirken beklenmeyen bir hata oluştu. Girdileriniz korunarak sayfa yeniden açıldı.", "danger")

    current_assignments = survey.assignments.order_by(SurveyAssignment.id.asc()).all()
    current_questions = _safe_survey_questions(int(survey.id))
    form_state = _survey_form_state_from_request() if request.method == "POST" else None
    if not form_state:
        form_state = _survey_state_from_db(survey, current_assignments=current_assignments, current_questions=current_questions)

    selected_user_items = []
    if (form_state.get("target_type") or "all") == "user":
        selected_user_items = _survey_selected_user_items(form_state.get("target_values", []))

    return safe_render(
        "survey_edit.html",
        "<h3>Anket Düzenle</h3>",
        survey=survey,
        birimler=birimler,
        roles=roles,
        active_user_count=active_user_count,
        selected_user_items=selected_user_items,
        has_responses=has_responses,
        current_assignments=current_assignments,
        current_questions=current_questions,
        form_state=form_state,
    )


@main_bp.route("/survey-publish/<int:survey_id>", methods=["POST"])
@login_required
@menu_key_required("survey_manage")
def survey_publish(survey_id):
    if not _survey_manager_allowed():
        flash("Bu alana erişim yetkiniz yok.", "danger")
        return redirect(url_for("main.dashboard"))
    survey = db.session.get(Survey, survey_id)
    if not survey:
        flash("Anket bulunamadı.", "danger")
        return redirect(url_for("main.survey_manage"))
    if _safe_question_count(int(survey.id)) == 0:
        flash("Yayımlama için en az bir soru bulunmalıdır.", "warning")
        return redirect(url_for("main.survey_manage"))
    if survey.assignments.count() == 0:
        flash("Yayımlama için hedef kitle tanımlanmalıdır.", "warning")
        return redirect(url_for("main.survey_manage"))
    try:
        _service_publish_survey(
            survey,
            target_user_ids=_estimate_survey_target_user_ids(survey),
            notify_user=_notify_user,
            link_url=url_for("main.survey_take", survey_id=survey.id),
            now_factory=_utcnow,
        )
        flash("Anket yayımlandı.", "success")
    except ValueError as exc:
        flash(str(exc), "warning")
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/surveys_routes.py | line=806")
        db.session.rollback()
        _log_communication_exception("survey_publish", exc, survey_id=survey.id, user_id=getattr(current_user, "id", None))
        flash(f"Anket yayımlanırken hata oluştu: {exc}", "danger")
    return redirect(url_for("main.survey_manage"))


@main_bp.route("/survey-unpublish/<int:survey_id>", methods=["POST"])
@login_required
@menu_key_required("survey_manage")
def survey_unpublish(survey_id):
    if not _survey_manager_allowed():
        flash("Bu alana erişim yetkiniz yok.", "danger")
        return redirect(url_for("main.dashboard"))
    survey = db.session.get(Survey, survey_id)
    if not survey:
        flash("Anket bulunamadı.", "danger")
        return redirect(url_for("main.survey_manage"))
    try:
        _service_unpublish_survey(survey)
        flash("Anket taslak durumuna alındı.", "success")
    except ValueError as exc:
        flash(str(exc), "warning")
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/surveys_routes.py | line=829")
        db.session.rollback()
        _log_communication_exception("survey_unpublish", exc, survey_id=survey.id, user_id=getattr(current_user, "id", None))
        flash(f"Anket güncellenirken hata oluştu: {exc}", "danger")
    return redirect(url_for("main.survey_manage"))


@main_bp.route("/survey-close/<int:survey_id>", methods=["POST"])
@login_required
@menu_key_required("survey_manage")
def survey_close(survey_id):
    if not _survey_manager_allowed():
        flash("Bu alana erişim yetkiniz yok.", "danger")
        return redirect(url_for("main.dashboard"))
    survey = db.session.get(Survey, survey_id)
    if not survey:
        flash("Anket bulunamadı.", "danger")
        return redirect(url_for("main.survey_manage"))
    try:
        _service_close_survey(survey, now_factory=_survey_local_now)
        flash("Anket kapatıldı.", "success")
    except ValueError as exc:
        flash(str(exc), "warning")
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/surveys_routes.py | line=852")
        db.session.rollback()
        _log_communication_exception("survey_close", exc, survey_id=survey.id, user_id=getattr(current_user, "id", None))
        flash(f"Anket kapatılırken hata oluştu: {exc}", "danger")
    return redirect(url_for("main.survey_manage"))


@main_bp.route("/survey-archive/<int:survey_id>", methods=["POST"])
@login_required
@menu_key_required("survey_manage")
def survey_archive(survey_id):
    if not _survey_manager_allowed():
        flash("Bu alana erişim yetkiniz yok.", "danger")
        return redirect(url_for("main.dashboard"))
    survey = db.session.get(Survey, survey_id)
    if not survey:
        flash("Anket bulunamadı.", "danger")
        return redirect(url_for("main.survey_manage"))
    try:
        _service_archive_survey(survey)
        flash("Anket arşive alındı.", "success")
    except ValueError as exc:
        flash(str(exc), "warning")
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/surveys_routes.py | line=875")
        db.session.rollback()
        _log_communication_exception("survey_archive", exc, survey_id=survey.id, user_id=getattr(current_user, "id", None))
        flash(f"Anket arşive alınırken hata oluştu: {exc}", "danger")
    return redirect(url_for("main.survey_manage", status="archived"))


@main_bp.route("/survey-restore/<int:survey_id>", methods=["POST"])
@login_required
@menu_key_required("survey_manage")
def survey_restore(survey_id):
    if not _survey_manager_allowed():
        flash("Bu alana erişim yetkiniz yok.", "danger")
        return redirect(url_for("main.dashboard"))
    survey = db.session.get(Survey, survey_id)
    if not survey:
        flash("Anket bulunamadı.", "danger")
        return redirect(url_for("main.survey_manage"))
    try:
        _service_restore_survey(survey)
        flash("Anket taslak durumuna geri alındı.", "success")
    except ValueError as exc:
        flash(str(exc), "warning")
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/surveys_routes.py | line=898")
        db.session.rollback()
        _log_communication_exception("survey_restore", exc, survey_id=survey.id, user_id=getattr(current_user, "id", None))
        flash(f"Anket geri alınırken hata oluştu: {exc}", "danger")
    return redirect(url_for("main.survey_manage", status="draft"))


@main_bp.route("/survey-bulk-action", methods=["POST"])
@login_required
@menu_key_required("survey_manage")
def survey_bulk_action():
    if not _survey_manager_allowed():
        flash("Bu alana erişim yetkiniz yok.", "danger")
        return redirect(url_for("main.dashboard"))

    raw_ids = request.form.getlist("survey_ids")
    survey_ids = []
    for raw_id in raw_ids:
        try:
            survey_ids.append(int(raw_id))
        except (TypeError, ValueError):
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/communication/surveys_routes.py:916)")
            continue

    action = (request.form.get("bulk_action") or "").strip().lower()
    current_status = (request.form.get("current_status") or "all").strip().lower()

    if not survey_ids:
        flash("Toplu işlem için en az bir anket seçin.", "warning")
        return redirect(url_for("main.survey_manage", status=current_status))

    surveys = Survey.query.filter(Survey.id.in_(survey_ids)).all()
    if not surveys:
        flash("Seçilen anketler bulunamadı.", "warning")
        return redirect(url_for("main.survey_manage", status=current_status))

    try:
        result = _service_bulk_survey_action(surveys, action)
        if action == "archive":
            flash(f"{result.affected} anket arşive alındı.", "success")
        elif action == "restore":
            flash(f"{result.affected} anket taslağa geri alındı.", "success")
        elif action == "delete":
            if result.affected:
                flash(f"{result.affected} anket kalıcı olarak silindi.", "success")
            if result.skipped_with_responses:
                flash(f"{result.skipped_with_responses} anket yanıt içerdiği için silinmedi; arşivlemeyi tercih edin.", "warning")
    except ValueError as exc:
        flash(str(exc), "warning")
        return redirect(url_for("main.survey_manage", status=current_status))
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/surveys_routes.py | line=948")
        db.session.rollback()
        _log_communication_exception(
            "survey_bulk_action",
            exc,
            survey_ids=survey_ids,
            action=action,
            user_id=getattr(current_user, "id", None),
        )
        flash(f"Toplu anket işlemi sırasında hata oluştu: {exc}", "danger")

    return redirect(url_for("main.survey_manage", status=current_status))


@main_bp.route("/survey-delete/<int:survey_id>", methods=["POST"])
@login_required
@menu_key_required("survey_manage")
def survey_delete(survey_id):
    if not _survey_manager_allowed():
        flash("Bu alana erişim yetkiniz yok.", "danger")
        return redirect(url_for("main.dashboard"))

    survey = db.session.get(Survey, survey_id)
    if not survey:
        flash("Anket bulunamadı.", "danger")
        return redirect(url_for("main.survey_manage"))

    try:
        _service_delete_survey_if_allowed(survey)
        flash("Anket kalıcı olarak silindi.", "success")
    except ValueError as exc:
        flash(str(exc), "warning")
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/surveys_routes.py | line=980")
        db.session.rollback()
        _log_communication_exception("survey_delete", exc, survey_id=survey.id, user_id=getattr(current_user, "id", None))
        flash(f"Anket silinirken hata oluştu: {exc}", "danger")

    return redirect(url_for("main.survey_manage"))


def _latest_completed_label_for_survey(survey_id: int) -> str:
    return _service_latest_completed_label_for_survey(survey_id)


def _simple_completion_trend(survey_id: int) -> list[dict[str, object]]:
    return _service_simple_completion_trend(survey_id)


@main_bp.route("/survey-results/export-csv")
@login_required
@menu_key_required("survey_results")
def survey_results_export_csv():
    if not _survey_manager_allowed():
        flash("Bu alana erişim yetkiniz yok.", "danger")
        return redirect(url_for("main.dashboard"))
    survey_id = request.args.get("survey_id", type=int)
    survey = db.session.get(Survey, survey_id) if survey_id else None
    if not survey:
        flash("Anket bulunamadı.", "warning")
        return redirect(url_for("main.survey_results"))

    estimated_target_count = len(_estimate_survey_target_user_ids(survey))
    csv_text = _service_build_survey_results_csv_text(survey, estimated_target_count=estimated_target_count)
    filename = f"survey_results_{survey.id}.csv"
    return Response(csv_text, mimetype="text/csv; charset=utf-8", headers={"Content-Disposition": f'attachment; filename={filename}'})


@main_bp.route("/survey-results")
@login_required
@menu_key_required("survey_results")
def survey_results():
    _survey_session_reset()

    if not _survey_manager_allowed():
        flash("Bu alana erişim yetkiniz yok.", "danger")
        return redirect(url_for("main.dashboard"))

    survey_id = request.args.get("survey_id", type=int)
    surveys = Survey.query.order_by(Survey.created_at.desc(), Survey.id.desc()).all()
    selected_survey = db.session.get(Survey, survey_id) if survey_id else (surveys[0] if surveys else None)

    result_context = _service_build_survey_results_context(
        selected_survey,
        estimate_target_user_ids=_estimate_survey_target_user_ids,
    )

    return safe_render(
        "survey_results.html",
        "<h3>Anket Sonuçları</h3>",
        surveys=surveys,
        selected_survey=selected_survey,
        survey_phase2_ready=True,
        **result_context,
    )


__all__ = [
    "surveys_list",
    "survey_take",
    "survey_submit",
    "survey_manage",
    "survey_create",
    "survey_edit",
    "survey_publish",
    "survey_unpublish",
    "survey_close",
    "survey_archive",
    "survey_restore",
    "survey_bulk_action",
    "survey_delete",
    "survey_results",
]
