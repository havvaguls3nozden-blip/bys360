"""Faz 1M communication service delegation spec."""

TARGETS = [{'imports': ['from __future__ import annotations',
              '',
              '"""Communication dashboard routes, Faz 1M service delegation ile sadeleştirildi."""',
              '',
              'from flask_login import current_user',
              'from app.route_support import safe_render',
              'from app.services.communication_phase1_service import communication_phase1_dashboard',
              'from app.services.communication_phase2_service import phase2_dashboard_snapshot',
              'from app.services.communication_phase3_service import phase3_dashboard_snapshot',
              ''],
  'include': ['communication_phase1_dashboard_view',
              'communication_phase2_dashboard_view',
              'communication_phase3_dashboard_view'],
  'target_module': 'phase_dashboard_routes',
  'target_relpath': 'app/communication/phase_dashboard_routes.py'},
 {'imports': ['from __future__ import annotations',
              '',
              '"""Communication survey routes, Faz 1M service delegation ile sadeleştirildi."""',
              '',
              'from flask import flash, redirect, request, url_for',
              'from flask_login import current_user',
              'from app.models.communication_phase2_models import CommunicationSurveyTemplate',
              'from app.route_support import safe_render',
              'from app.services.communication_phase1_service import survey_center_snapshot',
              'from app.services.communication_phase2_form_service import (',
              '    default_survey_form_state as _default_survey_form_state,',
              '    parse_questions_from_request as _parse_questions_from_request,',
              '    survey_form_state_from_request as _survey_form_state_from_request,',
              ')',
              'from app.services.communication_phase2_service import (',
              '    CommunicationPhase2Error,',
              '    SURVEY_QUESTION_TYPE_LABELS,',
              '    SURVEY_STATUS_LABELS,',
              '    archive_survey,',
              '    close_survey,',
              '    create_survey_from_template_or_builder,',
              '    duplicate_survey,',
              '    is_manager,',
              '    manager_filter_options,',
              '    publish_survey,',
              '    reopen_survey,',
              '    safe_str,',
              '    survey_builder_payload,',
              '    survey_detail_payload,',
              '    survey_manager_snapshot,',
              '    survey_results_snapshot,',
              '    upsert_survey_template,',
              '    update_survey_from_builder,',
              ')',
              'from app.services.communication_phase3_service import (',
              '    CommunicationPhase3Error,',
              '    create_survey_reminders,',
              '    get_survey_for_user,',
              '    save_or_submit_survey,',
              '    survey_center_for_user,',
              ')',
              ''],
  'include': ['communication_phase1_survey_center',
              'communication_phase2_surveys',
              'communication_phase2_survey_new',
              'communication_phase2_survey_edit',
              'communication_phase2_survey_duplicate',
              'communication_phase2_survey_archive',
              'communication_phase2_survey_reopen',
              'communication_phase2_survey_detail',
              'communication_phase2_survey_publish',
              'communication_phase2_survey_close',
              'communication_phase2_survey_results',
              'communication_phase2_survey_templates',
              'communication_phase2_survey_template_new',
              'communication_phase2_survey_template_edit',
              'communication_phase3_my_surveys',
              'communication_phase3_survey_take',
              'communication_phase3_survey_remind'],
  'target_module': 'survey_center_routes',
  'target_relpath': 'app/communication/survey_center_routes.py'},
 {'imports': ['from __future__ import annotations',
              '',
              '"""Communication notification routes, Faz 1M service delegation ile sadeleştirildi."""',
              '',
              'from flask import flash, redirect, request, url_for',
              'from flask_login import current_user',
              'from app.route_support import safe_render',
              'from app.services.communication_phase3_route_service import mark_notification_read_for_user',
              'from app.services.communication_phase3_service import mark_all_notifications_read, '
              'notification_center_snapshot',
              ''],
  'include': ['communication_phase3_notifications',
              'communication_phase3_notifications_read_all',
              'communication_phase3_notification_read'],
  'target_module': 'notification_center_routes',
  'target_relpath': 'app/communication/notification_center_routes.py'},
 {'imports': ['from __future__ import annotations',
              '',
              '"""Communication support routes, Faz 1M service delegation ile sadeleştirildi."""',
              '',
              'from flask import flash, redirect, request, url_for',
              'from flask_login import current_user',
              'from app.route_support import safe_render',
              'from app.services.communication_phase1_service import is_manager, support_center_snapshot',
              'from app.services.communication_phase3_route_service import parse_optional_assignee_user_id, '
              'request_flag',
              'from app.services.communication_phase3_service import (',
              '    CommunicationPhase3Error,',
              '    SUPPORT_STATUS_LABELS,',
              '    add_support_message,',
              '    assign_support_ticket,',
              '    help_article_detail,',
              '    help_center_snapshot,',
              '    support_detail_payload,',
              '    support_queue_snapshot,',
              '    update_support_status,',
              ')',
              ''],
  'include': ['communication_phase1_support_center',
              'communication_phase3_support_queue',
              'communication_phase3_support_detail',
              'communication_phase3_support_assign',
              'communication_phase3_support_status',
              'communication_phase3_help_center',
              'communication_phase3_help_article'],
  'target_module': 'support_center_routes',
  'target_relpath': 'app/communication/support_center_routes.py'}]

HELPER_MODULES = {'app/services/communication_phase2_form_service.py': 'from __future__ import annotations\n'
                                                      '\n'
                                                      'from flask import request\n'
                                                      '\n'
                                                      'from app.services.communication_phase2_service import safe_str\n'
                                                      '\n'
                                                      '\n'
                                                      'def parse_questions_from_request(form=None) -> list[dict]:\n'
                                                      '    form = form or request.form\n'
                                                      '    question_texts = form.getlist("question_text")\n'
                                                      '    question_types = form.getlist("question_type")\n'
                                                      '    required_flags = form.getlist("question_required")\n'
                                                      '    options_blocks = form.getlist("question_options")\n'
                                                      '\n'
                                                      '    questions: list[dict] = []\n'
                                                      '    for index, question_text in enumerate(question_texts):\n'
                                                      '        text = safe_str(question_text)\n'
                                                      '        if not text:\n'
                                                      '            continue\n'
                                                      '        question_type = safe_str(question_types[index] if index '
                                                      '< len(question_types) else "single_choice") or "single_choice"\n'
                                                      '        required_raw = safe_str(required_flags[index] if index '
                                                      '< len(required_flags) else "1")\n'
                                                      '        options_text = safe_str(options_blocks[index] if index '
                                                      '< len(options_blocks) else "")\n'
                                                      '        options = [row.strip() for row in '
                                                      'options_text.splitlines() if row and row.strip()]\n'
                                                      '        questions.append(\n'
                                                      '            {\n'
                                                      '                "question_text": text,\n'
                                                      '                "question_type": question_type,\n'
                                                      '                "is_required": required_raw not in {"0", '
                                                      '"false", "hayir", "off"},\n'
                                                      '                "options": options,\n'
                                                      '                "options_text": "\\n".join(options),\n'
                                                      '            }\n'
                                                      '        )\n'
                                                      '    return questions\n'
                                                      '\n'
                                                      '\n'
                                                      'def default_survey_form_state(blank_count: int = 4) -> dict:\n'
                                                      '    return {\n'
                                                      '        "title": "",\n'
                                                      '        "description": "",\n'
                                                      '        "survey_type": "kurum_ici",\n'
                                                      '        "target_type": "all",\n'
                                                      '        "target_values": "",\n'
                                                      '        "is_anonymous": False,\n'
                                                      '        "allow_multiple_submissions": False,\n'
                                                      '        "publish_now": False,\n'
                                                      '        "start_at": "",\n'
                                                      '        "end_at": "",\n'
                                                      '        "questions": [\n'
                                                      '            {\n'
                                                      '                "question_text": "",\n'
                                                      '                "question_type": "single_choice",\n'
                                                      '                "is_required": True,\n'
                                                      '                "options_text": "",\n'
                                                      '            }\n'
                                                      '            for _ in range(blank_count)\n'
                                                      '        ],\n'
                                                      '    }\n'
                                                      '\n'
                                                      '\n'
                                                      'def survey_form_state_from_request(form=None) -> dict:\n'
                                                      '    form = form or request.form\n'
                                                      '    questions = parse_questions_from_request(form)\n'
                                                      '    return {\n'
                                                      '        "title": form.get("title", ""),\n'
                                                      '        "description": form.get("description", ""),\n'
                                                      '        "survey_type": form.get("survey_type", "kurum_ici"),\n'
                                                      '        "target_type": form.get("target_type", "all"),\n'
                                                      '        "target_values": form.get("target_values", ""),\n'
                                                      '        "is_anonymous": bool(form.get("is_anonymous")),\n'
                                                      '        "allow_multiple_submissions": '
                                                      'bool(form.get("allow_multiple_submissions")),\n'
                                                      '        "publish_now": bool(form.get("publish_now")),\n'
                                                      '        "start_at": form.get("start_at", ""),\n'
                                                      '        "end_at": form.get("end_at", ""),\n'
                                                      '        "questions": questions or '
                                                      'default_survey_form_state()["questions"],\n'
                                                      '    }\n',
 'app/services/communication_phase3_route_service.py': 'from __future__ import annotations\n'
                                                       '\n'
                                                       'from app.extensions import db\n'
                                                       'from app.models import Notification\n'
                                                       '\n'
                                                       '\n'
                                                       'def mark_notification_read_for_user(notification_id: int, '
                                                       'user_id: int):\n'
                                                       '    row = Notification.query.filter_by(id=notification_id, '
                                                       'user_id=user_id).first_or_404()\n'
                                                       '    row.is_read = True\n'
                                                       '    row.read_at = row.read_at or row.updated_at\n'
                                                       '    db.session.add(row)\n'
                                                       '    db.session.commit()\n'
                                                       '    return row\n'
                                                       '\n'
                                                       '\n'
                                                       'def parse_optional_assignee_user_id(raw_value) -> int | None:\n'
                                                       '    raw = str(raw_value or "").strip()\n'
                                                       '    return int(raw) if raw.isdigit() else None\n'
                                                       '\n'
                                                       '\n'
                                                       'def request_flag(form, key: str) -> bool:\n'
                                                       '    return bool(form.get(key))\n'}

BACKUP_ROOT = "refactor_backups/faz1m"
STAGE_ROOT = "refactor_staging/faz1m"
REPORT_ROOT = "reports/faz1m"