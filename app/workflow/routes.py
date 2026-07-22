from __future__ import annotations

from flask import flash, redirect, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import inspect, text

from app.extensions import db
from app.route_registry import main_bp
from app.route_support import ADMIN_FAMILY_ROLES, safe_render, user_has_any_role
from app.security.sql_identifiers import quote_sql_identifier, validate_sql_identifier

LOW_SCORE_THRESHOLD = 70.0
WORKFLOW_VIEW_ROLES = set(ADMIN_FAMILY_ROLES) | {"koordinator", "birim_sorumlusu", "grup_baskani", "baskan_yardimcisi"}
PRESIDENT_ROLES = {"baskan", "admin"}
DELAY_WARNING_DAYS = 2
DELAY_CRITICAL_DAYS = 5
DEFAULT_STEP_DUE_DAYS = 3
REMINDER_REPEAT_HOURS = 24

_GENERIC_SYNC_ALLOWED_COLUMNS = {
    "support_tickets": frozenset(
        {
            "id",
            "title",
            "subject",
            "summary",
            "created_by_id",
            "requester_id",
            "user_id",
            "owner_id",
            "status",
            "state",
        }
    ),
    "leave_requests": frozenset(
        {
            "id",
            "title",
            "leave_type",
            "request_type",
            "summary",
            "user_id",
            "employee_id",
            "personnel_id",
            "created_by_id",
            "status",
            "approval_status",
            "state",
        }
    ),
    "personnel_leaves": frozenset(
        {
            "id",
            "title",
            "leave_type",
            "summary",
            "user_id",
            "employee_id",
            "personnel_id",
            "created_by_id",
            "status",
            "approval_status",
            "state",
        }
    ),
    "surveys": frozenset(
        {
            "id",
            "title",
            "name",
            "subject",
            "created_by_id",
            "owner_id",
            "user_id",
            "status",
            "state",
            "is_active",
        }
    ),
    "announcements": frozenset(
        {
            "id",
            "title",
            "subject",
            "headline",
            "created_by_id",
            "owner_id",
            "user_id",
            "status",
            "state",
            "is_active",
        }
    ),
}


def _can_view():
    return user_has_any_role(current_user, WORKFLOW_VIEW_ROLES)


def _can_decide():
    return user_has_any_role(current_user, PRESIDENT_ROLES)


def _deny(msg="Bu sayfaya erişim yetkiniz yok."):
    flash(msg, "warning")
    return redirect(url_for("main.dashboard"))


def _full_name_expr(alias="u"):
    """Canlı users şemasına uygun güvenli ad-soyad SQL ifadesi."""
    return (
        f"COALESCE("
        f"{alias}.full_name_cache, "
        f"NULLIF(TRIM(CONCAT(COALESCE({alias}.ad,''),' ',COALESCE({alias}.soyad,''))), ''), "
        f"{alias}.email, "
        f"'-'"
        f")"
    )


def _first_president_user_id():
    return db.session.execute(text("""
        SELECT id
        FROM users
        WHERE LOWER(COALESCE(role,'')) IN ('baskan','başkan','admin')
          AND COALESCE(is_active, TRUE)=TRUE
        ORDER BY CASE WHEN LOWER(COALESCE(role,'')) IN ('baskan','başkan') THEN 0 ELSE 1 END, id ASC
        LIMIT 1
    """)).scalar()


class WorkflowSchemaNotReadyError(RuntimeError):
    """Raised when the Alembic-owned workflow schema is not ready."""


_WORKFLOW_REQUIRED_SCHEMA = {
    "workflow_instances": frozenset(
        {
            "id",
            "module",
            "entity_type",
            "entity_id",
            "title",
            "subject_user_id",
            "period_id",
            "score",
            "status",
            "current_step_name",
            "priority",
            "workflow_family",
            "delayed_step_count",
            "created_by_id",
            "created_at",
            "updated_at",
            "completed_at",
            "payload_json",
        }
    ),
    "workflow_steps": frozenset(
        {
            "id",
            "workflow_id",
            "step_order",
            "step_code",
            "step_type",
            "step_name",
            "assigned_user_id",
            "visible_to_user_id",
            "status",
            "is_active",
            "is_required",
            "started_at",
            "completed_at",
            "due_at",
            "duration_minutes",
            "delay_state",
            "delay_days",
            "escalation_level",
            "last_reminded_at",
            "reminder_count",
            "notification_status",
            "note",
        }
    ),
    "workflow_logs": frozenset(
        {
            "id",
            "workflow_id",
            "step_id",
            "user_id",
            "action",
            "old_status",
            "new_status",
            "note",
            "created_at",
        }
    ),
    "workflow_notifications": frozenset(
        {
            "id",
            "workflow_id",
            "step_id",
            "target_user_id",
            "notification_type",
            "title",
            "body",
            "status",
            "created_at",
            "delivered_at",
            "payload_json",
        }
    ),
    "performance_president_approvals": frozenset(
        {
            "id",
            "evaluation_id",
            "period_id",
            "employee_id",
            "score",
            "status",
            "workflow_id",
            "requested_by_id",
            "president_id",
            "decided_at",
            "decision_note",
            "created_at",
            "updated_at",
        }
    ),
}
_WORKFLOW_SCHEMA_REVISION = "6f2b8c4d1a90"


def _workflow_schema_gaps(schema_inspector) -> dict[str, tuple[str, ...]]:
    existing_tables = set(schema_inspector.get_table_names())
    gaps: dict[str, tuple[str, ...]] = {}
    for table_name, required_columns in _WORKFLOW_REQUIRED_SCHEMA.items():
        if table_name not in existing_tables:
            gaps[table_name] = ("<tablo eksik>",)
            continue
        existing_columns = {
            column["name"]
            for column in schema_inspector.get_columns(table_name)
        }
        missing_columns = tuple(sorted(required_columns - existing_columns))
        if missing_columns:
            gaps[table_name] = missing_columns
    return gaps


def assert_workflow_schema_ready() -> None:
    """Validate the Alembic-owned workflow schema without changing it."""
    gaps = _workflow_schema_gaps(inspect(db.engine))
    if not gaps:
        return

    details = "; ".join(
        f"{table_name}: {', '.join(missing_items)}"
        for table_name, missing_items in sorted(gaps.items())
    )
    raise WorkflowSchemaNotReadyError(
        "İş akışı veritabanı şeması hazır değil. "
        f"Alembic migrationlarını en az {_WORKFLOW_SCHEMA_REVISION} revisionına kadar "
        f"uygulayın. Eksikler: {details}"
    )


def ensure_tables() -> None:
    """Backward-compatible, read-only workflow schema readiness guard."""
    assert_workflow_schema_ready()


def _delay_case_sql():
    return """
        CASE
            WHEN status <> 'PENDING' THEN 'NORMAL'
            WHEN started_at IS NULL THEN 'NORMAL'
            WHEN EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - started_at)) / 86400 >= :critical_days THEN 'CRITICAL'
            WHEN EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - started_at)) / 86400 >= :warning_days THEN 'WARNING'
            ELSE 'NORMAL'
        END
    """


def refresh_delay_states():
    assert_workflow_schema_ready()
    db.session.execute(
        text(f"""
            UPDATE workflow_steps
            SET delay_state = {_delay_case_sql()},
                delay_days = CASE
                    WHEN status <> 'PENDING' OR started_at IS NULL THEN 0
                    ELSE ROUND((EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - started_at)) / 86400)::numeric, 2)
                END,
                due_at = COALESCE(due_at, started_at + (:due_days || ' days')::interval),
                escalation_level = CASE
                    WHEN status <> 'PENDING' THEN 'NONE'
                    WHEN EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - started_at)) / 86400 >= :critical_days THEN 'PRESIDENT_ATTENTION'
                    WHEN EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - started_at)) / 86400 >= :warning_days THEN 'MANAGER_ATTENTION'
                    ELSE 'NONE'
                END
            WHERE is_active = TRUE
        """),
        {"critical_days": DELAY_CRITICAL_DAYS, "warning_days": DELAY_WARNING_DAYS, "due_days": DEFAULT_STEP_DUE_DAYS},
    )
    db.session.execute(text("""
        UPDATE workflow_instances wi
        SET delayed_step_count = COALESCE(x.cnt,0), updated_at=CURRENT_TIMESTAMP
        FROM (
            SELECT workflow_id, COUNT(*) FILTER (WHERE delay_state IN ('WARNING','CRITICAL')) cnt
            FROM workflow_steps GROUP BY workflow_id
        ) x
        WHERE x.workflow_id=wi.id
    """))
    db.session.execute(text("""
        UPDATE workflow_instances wi SET delayed_step_count=0
        WHERE NOT EXISTS (SELECT 1 FROM workflow_steps ws WHERE ws.workflow_id=wi.id AND ws.delay_state IN ('WARNING','CRITICAL'))
    """))
    db.session.commit()


def sync_low_scores():
    """Faz 8.1: 70 altı performans kayıtları için Başkan onay akışı üretir."""
    assert_workflow_schema_ready()
    rows = db.session.execute(text(f"""
        SELECT e.id evaluation_id,
               e.period_id,
               e.employee_id,
               COALESCE(e.final_total_100,0) score,
               {_full_name_expr('u')} employee_name,
               COALESCE(p.title,'Performans Dönemi') period_title
        FROM performance_evaluations e
        LEFT JOIN users u ON u.id=e.employee_id
        LEFT JOIN performance_periods p ON p.id=e.period_id
        LEFT JOIN performance_president_approvals a ON a.evaluation_id=e.id
        WHERE COALESCE(e.final_total_100,0)>0
          AND COALESCE(e.final_total_100,0)<:t
          AND COALESCE(e.evaluation_exempted,false)=false
          AND a.id IS NULL
        ORDER BY e.period_id DESC,e.final_total_100 ASC
    """), {"t": LOW_SCORE_THRESHOLD}).mappings().all()

    president_user_id = _first_president_user_id()
    for r in rows:
        title = f"70 Altı Performans Başkan Onayı - {(r.employee_name or 'Personel').strip()}"
        wid = db.session.execute(text("""
            INSERT INTO workflow_instances(
                module, entity_type, entity_id, title, subject_user_id, period_id, score,
                status, current_step_name, priority, created_by_id, workflow_family, payload_json
            )
            VALUES(
                'performance','performance_evaluation',:eid,:title,:uid,:pid,:score,
                'ACTIVE','Başkan Onayı Bekliyor','HIGH',:by,'PERFORMANCE',
                jsonb_build_object('rule','LOW_SCORE_PRESIDENT_APPROVAL_REQUIRED','period_title',:pt,'faz','8.1')
            )
            RETURNING id
        """), {
            "eid": r.evaluation_id,
            "title": title[:255],
            "uid": r.employee_id,
            "pid": r.period_id,
            "score": r.score,
            "by": getattr(current_user, 'id', None),
            "pt": r.period_title,
        }).scalar()
        sid = db.session.execute(text("""
            INSERT INTO workflow_steps(
                workflow_id, step_order, step_code, step_type, step_name,
                assigned_user_id, visible_to_user_id, status, is_active, is_required
            )
            VALUES(
                :wid,99,'PRESIDENT_APPROVAL','PRESIDENT','Başkan Onayı',
                :president_id,:president_id,'PENDING',TRUE,TRUE
            )
            RETURNING id
        """), {"wid": wid, "president_id": president_user_id}).scalar()
        db.session.execute(text("""
            INSERT INTO performance_president_approvals(
                evaluation_id,period_id,employee_id,score,status,workflow_id,requested_by_id,president_id
            )
            VALUES(:eid,:pid,:uid,:score,'PENDING',:wid,:by,:president_id)
        """), {
            "eid": r.evaluation_id,
            "pid": r.period_id,
            "uid": r.employee_id,
            "score": r.score,
            "wid": wid,
            "by": getattr(current_user, 'id', None),
            "president_id": president_user_id,
        })
        db.session.execute(text("""
            INSERT INTO workflow_logs(workflow_id,step_id,user_id,action,new_status,note)
            VALUES(:wid,:sid,:by,'AUTO_CREATED_LOW_SCORE_APPROVAL','PENDING','Nihai puan 70 altında olduğu için Başkan onay akışı oluşturuldu.')
        """), {"wid": wid, "sid": sid, "by": getattr(current_user, 'id', None)})
    db.session.commit()
    return len(rows)

def sync_performance_timeline():
    """Faz 8.1: performans adımlarını gerçek 3→2→1 akışta izlenebilir tutar.

    Bu fonksiyon puanlama motoruna dokunmaz. Mevcut performance_evaluations
    kayıtlarından sadece okur ve workflow_instances/workflow_steps görünürlüğünü
    günceller.
    """
    assert_workflow_schema_ready()
    rows = db.session.execute(text(f"""
        SELECT e.id evaluation_id,
               e.period_id,
               e.employee_id,
               COALESCE(e.final_total_100,0) score,
               e.level_1_evaluator_id,
               e.level_2_evaluator_id,
               e.level_3_evaluator_id,
               COALESCE(e.level_1_completed,false) level_1_completed,
               COALESCE(e.level_2_completed,false) level_2_completed,
               COALESCE(e.level_3_completed,false) level_3_completed,
               COALESCE(e.workflow_status,'') workflow_status,
               {_full_name_expr('u')} employee_name,
               COALESCE(p.title,'Performans Dönemi') period_title
        FROM performance_evaluations e
        LEFT JOIN users u ON u.id=e.employee_id
        LEFT JOIN performance_periods p ON p.id=e.period_id
        ORDER BY e.period_id DESC, e.id DESC
        LIMIT 500
    """)).mappings().all()

    created = 0
    president_user_id = _first_president_user_id()

    def _upsert_step(wid, order, code, stype, name, status, active, required, assignee_id):
        existing_id = db.session.execute(text("""
            SELECT id FROM workflow_steps
            WHERE workflow_id=:wid AND step_code=:code
            ORDER BY id ASC
            LIMIT 1
        """), {"wid": wid, "code": code}).scalar()
        payload = {
            "wid": wid,
            "ord": order,
            "code": code,
            "stype": stype,
            "name": name,
            "status": status,
            "active": bool(active),
            "required": bool(required),
            "assignee": assignee_id,
        }
        if existing_id:
            db.session.execute(text("""
                UPDATE workflow_steps
                SET step_order=:ord,
                    step_type=:stype,
                    step_name=:name,
                    assigned_user_id=:assignee,
                    visible_to_user_id=:assignee,
                    status=CASE
                        WHEN status IN ('DONE','COMPLETED','APPROVED','REJECTED') THEN status
                        ELSE :status
                    END,
                    is_active=:active,
                    is_required=:required,
                    started_at=COALESCE(started_at, CURRENT_TIMESTAMP)
                WHERE id=:id
            """), {**payload, "id": existing_id})
            return existing_id
        return db.session.execute(text("""
            INSERT INTO workflow_steps(
                workflow_id, step_order, step_code, step_type, step_name,
                assigned_user_id, visible_to_user_id, status, is_active, is_required
            )
            VALUES(
                :wid, :ord, :code, :stype, :name,
                :assignee, :assignee, :status, :active, :required
            )
            RETURNING id
        """), payload).scalar()

    for r in rows:
        wid = db.session.execute(text("""
            SELECT id
            FROM workflow_instances
            WHERE module='performance'
              AND entity_type='performance_timeline'
              AND entity_id=:eid
            ORDER BY id ASC
            LIMIT 1
        """), {"eid": r.evaluation_id}).scalar()

        title = f"Performans İş Akışı - {(r.employee_name or 'Personel').strip()}"
        if not wid:
            wid = db.session.execute(text("""
                INSERT INTO workflow_instances(
                    module, entity_type, entity_id, title, subject_user_id, period_id, score,
                    status, current_step_name, priority, created_by_id, workflow_family, payload_json
                )
                VALUES(
                    'performance','performance_timeline',:eid,:title,:uid,:pid,:score,
                    'ACTIVE','Performans Akışı İzleniyor','NORMAL',:by,'PERFORMANCE',
                    jsonb_build_object('rule','PERFORMANCE_FULL_TIMELINE_3_2_1','period_title',:pt,'faz','8.1')
                )
                RETURNING id
            """), {
                "eid": r.evaluation_id,
                "title": title[:255],
                "uid": r.employee_id,
                "pid": r.period_id,
                "score": r.score,
                "by": getattr(current_user, 'id', None),
                "pt": r.period_title,
            }).scalar()
            db.session.execute(text("""
                INSERT INTO workflow_logs(workflow_id,user_id,action,new_status,note)
                VALUES(:wid,:by,'AUTO_CREATED_PERFORMANCE_TIMELINE','ACTIVE','Faz 8.1 performans 3→2→1 timeline akışı oluşturuldu.')
            """), {"wid": wid, "by": getattr(current_user, 'id', None)})
            created += 1
        else:
            db.session.execute(text("""
                UPDATE workflow_instances
                SET title=:title,
                    subject_user_id=:uid,
                    period_id=:pid,
                    score=:score,
                    workflow_family='PERFORMANCE',
                    updated_at=CURRENT_TIMESTAMP,
                    payload_json=COALESCE(payload_json, '{}'::jsonb) || jsonb_build_object('faz','8.1','rule','PERFORMANCE_FULL_TIMELINE_3_2_1')
                WHERE id=:wid
            """), {
                "wid": wid,
                "title": title[:255],
                "uid": r.employee_id,
                "pid": r.period_id,
                "score": r.score,
            })

        has_level_3 = bool(r.level_3_evaluator_id)
        level3_done = bool(r.level_3_completed)
        level2_done = bool(r.level_2_completed)
        level1_done = bool(r.level_1_completed)

        step3_status = 'DONE' if (has_level_3 and level3_done) else ('PENDING' if has_level_3 else 'WAITING_CONDITION')
        step2_status = 'DONE' if level2_done else ('WAITING_PREVIOUS' if has_level_3 and not level3_done else 'PENDING')
        step1_status = 'DONE' if level1_done else ('WAITING_PREVIOUS' if r.level_2_evaluator_id and not level2_done else 'PENDING')

        score = float(r.score or 0)
        president_required = bool(score and score < LOW_SCORE_THRESHOLD)
        approval_status = db.session.execute(text("""
            SELECT status
            FROM performance_president_approvals
            WHERE evaluation_id=:eid
            ORDER BY id DESC
            LIMIT 1
        """), {"eid": r.evaluation_id}).scalar()
        president_step_status = approval_status if approval_status else ('PENDING' if president_required else 'WAITING_CONDITION')

        step_specs = [
            (1, 'THIRD_MANAGER', 'THIRD', '3. Amir / Üst Görüş', step3_status, has_level_3, has_level_3, r.level_3_evaluator_id),
            (2, 'SECOND_MANAGER', 'SECOND', '2. Amir Değerlendirme', step2_status, bool(r.level_2_evaluator_id), bool(r.level_2_evaluator_id), r.level_2_evaluator_id),
            (3, 'FIRST_MANAGER', 'FIRST', '1. Amir Nihai Değerlendirme', step1_status, bool(r.level_1_evaluator_id), bool(r.level_1_evaluator_id), r.level_1_evaluator_id),
            (4, 'PRESIDENT_APPROVAL', 'PRESIDENT', '70 Altı Başkan Onayı', president_step_status, president_required, president_required, president_user_id),
        ]
        for spec in step_specs:
            _upsert_step(wid, *spec)

        current_step = db.session.execute(text("""
            SELECT step_name
            FROM workflow_steps
            WHERE workflow_id=:wid
              AND is_active=TRUE
              AND status NOT IN ('DONE','COMPLETED','APPROVED','REJECTED')
            ORDER BY step_order ASC, id ASC
            LIMIT 1
        """), {"wid": wid}).scalar()
        required_open = db.session.execute(text("""
            SELECT COUNT(*)
            FROM workflow_steps
            WHERE workflow_id=:wid
              AND is_active=TRUE
              AND is_required=TRUE
              AND status NOT IN ('DONE','COMPLETED','APPROVED','REJECTED')
        """), {"wid": wid}).scalar() or 0
        db.session.execute(text("""
            UPDATE workflow_instances
            SET current_step_name=:step_name,
                status=CASE WHEN :open_count=0 THEN 'COMPLETED' ELSE 'ACTIVE' END,
                completed_at=CASE WHEN :open_count=0 THEN COALESCE(completed_at, CURRENT_TIMESTAMP) ELSE NULL END,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=:wid
        """), {
            "wid": wid,
            "step_name": current_step or "Tamamlandı",
            "open_count": int(required_open),
        })

    db.session.commit()
    return created

def generate_delay_notifications(limit=200):
    assert_workflow_schema_ready()
    refresh_delay_states()
    rows = db.session.execute(text("""
        SELECT ws.id step_id, ws.workflow_id, ws.assigned_user_id, ws.step_name, ws.delay_state, ws.delay_days, wi.title
        FROM workflow_steps ws
        JOIN workflow_instances wi ON wi.id=ws.workflow_id
        WHERE wi.status='ACTIVE' AND ws.status='PENDING' AND ws.is_active=TRUE
          AND ws.delay_state IN ('WARNING','CRITICAL')
          AND (ws.last_reminded_at IS NULL OR ws.last_reminded_at < CURRENT_TIMESTAMP - (:repeat_hours || ' hours')::interval)
        ORDER BY CASE ws.delay_state WHEN 'CRITICAL' THEN 0 ELSE 1 END, ws.delay_days DESC
        LIMIT :limit
    """), {"repeat_hours": REMINDER_REPEAT_HOURS, "limit": limit}).mappings().all()
    created = 0
    for r in rows:
        ntype = 'WORKFLOW_DELAY_CRITICAL' if r.delay_state == 'CRITICAL' else 'WORKFLOW_DELAY_WARNING'
        body = f"{r.title} sürecinde {r.step_name} adımı {r.delay_days} gündür bekliyor."
        db.session.execute(text("""
            INSERT INTO workflow_notifications(workflow_id,step_id,target_user_id,notification_type,title,body,status,payload_json)
            VALUES(:wid,:sid,:target,:type,:title,:body,'PENDING',jsonb_build_object('delay_state',:state,'delay_days',:days,'faz','3'))
        """), {"wid": r.workflow_id, "sid": r.step_id, "target": r.assigned_user_id, "type": ntype, "title": "Geciken iş akışı adımı", "body": body, "state": r.delay_state, "days": float(r.delay_days or 0)})
        db.session.execute(text("""
            UPDATE workflow_steps SET last_reminded_at=CURRENT_TIMESTAMP, reminder_count=reminder_count+1, notification_status='QUEUED' WHERE id=:sid
        """), {"sid": r.step_id})
        db.session.execute(text("""
            INSERT INTO workflow_logs(workflow_id,step_id,user_id,action,new_status,note)
            VALUES(:wid,:sid,:uid,'DELAY_NOTIFICATION_QUEUED','PENDING',:note)
        """), {"wid": r.workflow_id, "sid": r.step_id, "uid": getattr(current_user, 'id', None), "note": body})
        created += 1
    db.session.commit()
    return created


@main_bp.route('/workflow/dashboard')
@login_required
def workflow_dashboard():
    if not _can_view():
        return _deny()
    created_low = sync_low_scores() if request.args.get('sync') == '1' else 0
    created_timeline = sync_performance_timeline() if request.args.get('sync_timeline') == '1' else 0
    refresh_delay_states()
    status = (request.args.get('status') or 'ACTIVE').upper()
    rows = db.session.execute(text("""
        SELECT wi.*, COALESCE(u.full_name_cache, NULLIF(TRIM(CONCAT(COALESCE(u.ad,''),' ',COALESCE(u.soyad,''))), ''), u.email, '-') employee_name,
               COALESCE(p.title,'-') period_title,
               (SELECT COUNT(*) FROM workflow_steps ws WHERE ws.workflow_id=wi.id AND ws.status='PENDING') pending_steps,
               (SELECT COUNT(*) FROM workflow_steps ws WHERE ws.workflow_id=wi.id AND ws.delay_state='CRITICAL') critical_steps,
               (SELECT COUNT(*) FROM workflow_steps ws WHERE ws.workflow_id=wi.id AND ws.delay_state='WARNING') warning_steps,
               (SELECT MAX(ws.delay_days) FROM workflow_steps ws WHERE ws.workflow_id=wi.id) max_delay_days,
               (SELECT COALESCE(SUM(ws.reminder_count),0) FROM workflow_steps ws WHERE ws.workflow_id=wi.id) reminder_count
        FROM workflow_instances wi
        LEFT JOIN users u ON u.id=wi.subject_user_id
        LEFT JOIN performance_periods p ON p.id=wi.period_id
        WHERE (:st='ALL' OR wi.status=:st)
        ORDER BY wi.updated_at DESC, wi.id DESC
        LIMIT 250
    """), {"st": status}).mappings().all()
    stats = db.session.execute(text("""
        SELECT COUNT(*) FILTER(WHERE status='ACTIVE') active_count,
               COUNT(*) FILTER(WHERE status='COMPLETED') completed_count,
               COUNT(*) FILTER(WHERE priority='HIGH' AND status='ACTIVE') high_active_count,
               COUNT(*) FILTER(WHERE delayed_step_count > 0 AND status='ACTIVE') delayed_count,
               COUNT(*) FILTER(WHERE status='ACTIVE' AND delayed_step_count > 0 AND priority='HIGH') high_delayed_count
        FROM workflow_instances
    """)).mappings().first()
    return safe_render('workflow/dashboard.html', rows=rows, stats=stats or {}, status=status, created_count=created_low, created_timeline_count=created_timeline, fallback_html='<h3>İş Akış Takip Paneli</h3>')


@main_bp.route('/workflow/<int:workflow_id>/timeline')
@login_required
def workflow_timeline(workflow_id):
    if not _can_view():
        return _deny()
    assert_workflow_schema_ready()
    refresh_delay_states()
    workflow = db.session.execute(text(f"""
        SELECT wi.*, {_full_name_expr('u')} employee_name, COALESCE(p.title,'-') period_title
        FROM workflow_instances wi
        LEFT JOIN users u ON u.id=wi.subject_user_id
        LEFT JOIN performance_periods p ON p.id=wi.period_id
        WHERE wi.id=:id
    """), {"id": workflow_id}).mappings().first()
    if not workflow:
        flash('İş akışı bulunamadı.', 'warning')
        return redirect(url_for('main.workflow_dashboard'))
    steps = db.session.execute(text(f"""
        SELECT ws.*, {_full_name_expr('u')} assigned_name
        FROM workflow_steps ws
        LEFT JOIN users u ON u.id=ws.assigned_user_id
        WHERE ws.workflow_id=:id
        ORDER BY ws.step_order ASC, ws.id ASC
    """), {"id": workflow_id}).mappings().all()
    logs = db.session.execute(text(f"""
        SELECT wl.*, {_full_name_expr('u')} actor_name
        FROM workflow_logs wl
        LEFT JOIN users u ON u.id=wl.user_id
        WHERE wl.workflow_id=:id
        ORDER BY wl.created_at DESC, wl.id DESC
        LIMIT 100
    """), {"id": workflow_id}).mappings().all()
    return safe_render('workflow/timeline.html', workflow=workflow, steps=steps, logs=logs, fallback_html='<h3>İş Akış Timeline</h3>')


@main_bp.route('/workflow/delays')
@login_required
def workflow_delays():
    if not _can_view():
        return _deny()
    refresh_delay_states()
    severity = (request.args.get('severity') or 'ALL').upper()
    rows = db.session.execute(text(f"""
        SELECT ws.*, wi.title, wi.module, wi.entity_type, wi.score, wi.priority,
               {_full_name_expr('emp')} employee_name,
               {_full_name_expr('assignee')} assigned_name,
               COALESCE(p.title,'-') period_title
        FROM workflow_steps ws
        JOIN workflow_instances wi ON wi.id=ws.workflow_id
        LEFT JOIN users emp ON emp.id=wi.subject_user_id
        LEFT JOIN users assignee ON assignee.id=ws.assigned_user_id
        LEFT JOIN performance_periods p ON p.id=wi.period_id
        WHERE wi.status='ACTIVE' AND ws.status='PENDING' AND ws.is_active=TRUE
          AND (:severity='ALL' OR ws.delay_state=:severity)
          AND ws.delay_state IN ('WARNING','CRITICAL')
        ORDER BY CASE ws.delay_state WHEN 'CRITICAL' THEN 0 ELSE 1 END, ws.delay_days DESC, ws.started_at ASC
        LIMIT 300
    """), {"severity": severity}).mappings().all()
    stats = db.session.execute(text("""
        SELECT COUNT(*) FILTER(WHERE ws.delay_state='WARNING') warning_count,
               COUNT(*) FILTER(WHERE ws.delay_state='CRITICAL') critical_count,
               COALESCE(MAX(ws.delay_days),0) max_delay_days,
               COALESCE(SUM(ws.reminder_count),0) total_reminders
        FROM workflow_steps ws JOIN workflow_instances wi ON wi.id=ws.workflow_id
        WHERE wi.status='ACTIVE' AND ws.status='PENDING' AND ws.is_active=TRUE
    """)).mappings().first()
    return safe_render('workflow/delays.html', rows=rows, stats=stats or {}, severity=severity, fallback_html='<h3>Geciken İş Akışları</h3>')


@main_bp.route('/workflow/reminders/run', methods=['POST'])
@login_required
def workflow_run_delay_reminders():
    if not _can_view():
        return _deny()
    created = generate_delay_notifications()
    flash(f'Geciken iş akışları için {created} bildirim kaydı kuyruğa alındı.', 'success')
    return redirect(url_for('main.workflow_delays'))


@main_bp.route('/workflow/notifications')
@login_required
def workflow_notifications():
    if not _can_view():
        return _deny()
    assert_workflow_schema_ready()
    rows = db.session.execute(text(f"""
        SELECT wn.*, wi.title workflow_title, {_full_name_expr('u')} target_name
        FROM workflow_notifications wn
        JOIN workflow_instances wi ON wi.id=wn.workflow_id
        LEFT JOIN users u ON u.id=wn.target_user_id
        ORDER BY wn.created_at DESC, wn.id DESC
        LIMIT 300
    """)).mappings().all()
    return safe_render('workflow/notifications.html', rows=rows, fallback_html='<h3>İş Akış Bildirim Kuyruğu</h3>')


@main_bp.route('/workflow/president-approvals')
@login_required
def workflow_president_approvals():
    if not (_can_view() or _can_decide()):
        return _deny()
    sync_low_scores()
    rows = db.session.execute(text("""
        SELECT a.*, wi.title, wi.id workflow_id,
               COALESCE(u.full_name_cache, NULLIF(TRIM(CONCAT(COALESCE(u.ad,''),' ',COALESCE(u.soyad,''))), ''), u.email, '-') employee_name,
               COALESCE(p.title,'-') period_title
        FROM performance_president_approvals a
        JOIN workflow_instances wi ON wi.id=a.workflow_id
        LEFT JOIN users u ON u.id=a.employee_id
        LEFT JOIN performance_periods p ON p.id=a.period_id
        ORDER BY CASE a.status WHEN 'PENDING' THEN 0 WHEN 'RETURNED' THEN 1 ELSE 2 END, a.created_at DESC
        LIMIT 250
    """)).mappings().all()
    return safe_render('workflow/president_approvals.html', rows=rows, is_president=_can_decide(), fallback_html='<h3>Başkan Onayları</h3>')


@main_bp.route('/workflow/president-approvals/<int:approval_id>/decide', methods=['POST'])
@login_required
def workflow_president_decide(approval_id):
    if not _can_decide():
        return _deny('Bu işlem Başkan/Admin onayı gerektirir.')
    assert_workflow_schema_ready()
    action = (request.form.get('action') or '').upper()
    note = (request.form.get('note') or '').strip()
    mapped = {'APPROVE': ('APPROVED','COMPLETED','DONE'), 'REJECT': ('REJECTED','COMPLETED','REJECTED'), 'RETURN': ('RETURNED','ACTIVE','RETURNED')}.get(action)
    if not mapped:
        flash('Geçersiz karar işlemi.', 'warning')
        return redirect(url_for('main.workflow_president_approvals'))
    new_status, inst_status, step_status = mapped
    appr = db.session.execute(text('SELECT * FROM performance_president_approvals WHERE id=:id'), {'id': approval_id}).mappings().first()
    if not appr:
        flash('Onay kaydı bulunamadı.', 'warning')
        return redirect(url_for('main.workflow_president_approvals'))
    wid = appr['workflow_id']
    db.session.execute(text("""
        UPDATE performance_president_approvals
        SET status=:st,president_id=:uid,decided_at=CURRENT_TIMESTAMP,decision_note=:note,updated_at=CURRENT_TIMESTAMP
        WHERE id=:id
    """), {'st': new_status, 'uid': getattr(current_user, 'id', None), 'note': note, 'id': approval_id})
    db.session.execute(text("""
        UPDATE workflow_steps SET status=:st,completed_at=CURRENT_TIMESTAMP,note=:note
        WHERE workflow_id=:wid AND step_code='PRESIDENT_APPROVAL'
    """), {'st': step_status, 'note': note, 'wid': wid})
    db.session.execute(text("""
        UPDATE workflow_instances
        SET status=:st,current_step_name=CASE WHEN :st='COMPLETED' THEN 'Tamamlandı' ELSE 'Başkan İncelemesine İade' END,
            completed_at=CASE WHEN :st='COMPLETED' THEN CURRENT_TIMESTAMP ELSE completed_at END,updated_at=CURRENT_TIMESTAMP
        WHERE id=:wid
    """), {'st': inst_status, 'wid': wid})
    db.session.execute(text("""
        INSERT INTO workflow_logs(workflow_id,user_id,action,old_status,new_status,note)
        VALUES(:wid,:uid,'PRESIDENT_DECISION',:old,:new,:note)
    """), {'wid': wid, 'uid': getattr(current_user, 'id', None), 'old': appr['status'], 'new': new_status, 'note': note})
    db.session.commit()
    flash('Başkan onay kararı kaydedildi ve süreç güncellendi.', 'success')
    return redirect(url_for('main.workflow_president_approvals'))

def _executive_dashboard_payload():
    assert_workflow_schema_ready()
    refresh_delay_states()

    performance_map_raw = db.session.execute(text("""
        SELECT COALESCE(NULLIF(TRIM(u.birim),''),'Birim belirtilmemiş') AS unit_name,
               COUNT(e.id) AS total,
               COUNT(e.id) FILTER (
                   WHERE COALESCE(e.level_1_completed,false)=true
                      OR COALESCE(e.status,'') IN ('tamamlandi','tamamlandı','completed')
               ) AS completed,
               COUNT(e.id) FILTER (
                   WHERE COALESCE(e.final_total_100,0)>0
                     AND COALESCE(e.final_total_100,0)<:low
               ) AS low_count,
               ROUND(AVG(NULLIF(e.final_total_100,0))::numeric,2) AS average_score
        FROM performance_evaluations e
        LEFT JOIN users u ON u.id=e.employee_id
        GROUP BY COALESCE(NULLIF(TRIM(u.birim),''),'Birim belirtilmemiş')
        ORDER BY low_count DESC, total DESC, unit_name ASC
        LIMIT 50
    """), {"low": LOW_SCORE_THRESHOLD}).mappings().all()

    delayed_managers_raw = db.session.execute(text(f"""
        SELECT {_full_name_expr('u')} AS manager_name,
               COALESCE(NULLIF(TRIM(u.birim),''),'Birim belirtilmemiş') AS unit_name,
               COUNT(ws.id) AS pending_count,
               COALESCE(CEIL(MAX(ws.delay_days)),0)::int AS max_wait_days
        FROM workflow_steps ws
        JOIN workflow_instances wi ON wi.id=ws.workflow_id
        LEFT JOIN users u ON u.id=ws.assigned_user_id
        WHERE wi.status='ACTIVE'
          AND ws.status='PENDING'
          AND ws.is_active=TRUE
          AND ws.delay_state IN ('WARNING','CRITICAL')
        GROUP BY u.id, manager_name, unit_name
        ORDER BY max_wait_days DESC, pending_count DESC
        LIMIT 20
    """)).mappings().all()

    risky_raw = db.session.execute(text(f"""
        SELECT {_full_name_expr('u')} AS personnel_name,
               COALESCE(NULLIF(TRIM(u.birim),''),'Birim belirtilmemiş') AS unit_name,
               COALESCE(e.final_total_100, a.score) AS final_score,
               COALESCE(y.low_score_count_this_year, 0) AS low_score_count_this_year,
               CASE
                   WHEN a.status='PENDING' THEN 'Başkan Onayı Bekliyor'
                   WHEN a.status='APPROVED' THEN 'Başkan Onayladı'
                   WHEN a.status='REJECTED' THEN 'Başkan Reddetti'
                   WHEN a.status='RETURNED' THEN 'Başkan İade Etti'
                   ELSE COALESCE(a.status, 'İnceleme Bekliyor')
               END AS status
        FROM performance_president_approvals a
        LEFT JOIN performance_evaluations e ON e.id=a.evaluation_id
        LEFT JOIN users u ON u.id=a.employee_id
        LEFT JOIN (
            SELECT employee_id, COUNT(*) AS low_score_count_this_year
            FROM performance_evaluations
            WHERE COALESCE(final_total_100,0)>0
              AND COALESCE(final_total_100,0)<:low
            GROUP BY employee_id
        ) y ON y.employee_id=a.employee_id
        ORDER BY CASE a.status WHEN 'PENDING' THEN 0 WHEN 'RETURNED' THEN 1 ELSE 2 END,
                 final_score ASC NULLS LAST,
                 a.created_at DESC
        LIMIT 30
    """), {"low": LOW_SCORE_THRESHOLD}).mappings().all()

    from app.services.workflow.dashboard_upgrade import (
        build_delayed_managers,
        build_performance_map,
        build_risky_personnel,
    )
    return {
        "performance_map": build_performance_map(performance_map_raw),
        "delayed_managers": build_delayed_managers(delayed_managers_raw),
        "risky_personnel": build_risky_personnel(risky_raw),
    }


@main_bp.route('/workflow/executive-dashboard')
@login_required
def workflow_executive_dashboard():
    if not _can_view():
        return _deny()
    sync_low_scores()
    sync_performance_timeline()
    payload = _executive_dashboard_payload()
    return safe_render(
        'workflow/executive_dashboard.html',
        performance_map=payload["performance_map"],
        delayed_managers=payload["delayed_managers"],
        risky_personnel=payload["risky_personnel"],
        fallback_html='<h3>Yönetici İş Akış ve Performans Paneli</h3>',
    )


@main_bp.route('/performance/workflow')
@login_required
def performance_workflow_shortcut():
    return redirect(url_for('main.workflow_dashboard', sync=1, sync_timeline=1))


@main_bp.route('/workflow/sync/performance', methods=['POST'])
@login_required
def workflow_sync_performance():
    if not _can_view():
        return _deny()
    created_low = sync_low_scores()
    created_timeline = sync_performance_timeline()
    refresh_delay_states()
    flash(f'Performans iş akışı taraması tamamlandı. Yeni Başkan onayı: {created_low}, yeni timeline: {created_timeline}', 'success')
    return redirect(url_for('main.workflow_dashboard'))

# -----------------------------------------------------------------------------
# Faz 4: Genel modül iş akış bağlantı katmanı
# Performans omurgası korunur; izin, destek, anket ve duyuru gibi canlı süreçler
# var olan tabloya göre güvenli şekilde workflow_instances içine bağlanır.
# -----------------------------------------------------------------------------

GENERIC_WORKFLOW_MODULES = {
    'support': 'Destek Talepleri',
    'leave': 'İzin / Vekâlet Süreçleri',
    'survey': 'Anket Süreçleri',
    'announcement': 'Duyuru Süreçleri',
}


def _table_exists(table_name: str) -> bool:
    return bool(db.session.execute(text("SELECT to_regclass(:t) IS NOT NULL"), {"t": table_name}).scalar())


def _column_exists(table_name: str, column_name: str) -> bool:
    return bool(db.session.execute(text("""
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = current_schema()
          AND table_name = :t
          AND column_name = :c
        LIMIT 1
    """), {"t": table_name, "c": column_name}).scalar())


def _first_existing_column(table_name: str, candidates: list[str]) -> str | None:
    for col in candidates:
        if _column_exists(table_name, col):
            return col
    return None


def _sync_generic_table(
    *,
    table_name: str,
    module: str,
    entity_type: str,
    title_prefix: str,
    title_candidates: list[str],
    subject_candidates: list[str],
    status_candidates: list[str],
    step_name: str,
    workflow_family: str,
    limit: int = 300,
) -> int:
    safe_table_name = validate_sql_identifier(
        table_name,
        allowed=_GENERIC_SYNC_ALLOWED_COLUMNS,
    )
    allowed_columns = _GENERIC_SYNC_ALLOWED_COLUMNS[safe_table_name]
    safe_title_candidates = [
        validate_sql_identifier(column, allowed=allowed_columns)
        for column in title_candidates
    ]
    safe_subject_candidates = [
        validate_sql_identifier(column, allowed=allowed_columns)
        for column in subject_candidates
    ]
    safe_status_candidates = [
        validate_sql_identifier(column, allowed=allowed_columns)
        for column in status_candidates
    ]

    if not _table_exists(safe_table_name):
        return 0

    title_col = _first_existing_column(safe_table_name, safe_title_candidates)
    subject_col = _first_existing_column(safe_table_name, safe_subject_candidates)
    status_col = _first_existing_column(safe_table_name, safe_status_candidates)

    quoted_table_name = quote_sql_identifier(
        safe_table_name,
        dialect=db.engine.dialect,
        allowed=_GENERIC_SYNC_ALLOWED_COLUMNS,
    )

    def _quoted_column(column_name: str | None) -> str | None:
        if column_name is None:
            return None
        return quote_sql_identifier(
            column_name,
            dialect=db.engine.dialect,
            allowed=allowed_columns,
        )

    quoted_title_col = _quoted_column(title_col)
    quoted_subject_col = _quoted_column(subject_col)
    quoted_status_col = _quoted_column(status_col)

    title_expr = (
        f"COALESCE(CAST(t.{quoted_title_col} AS TEXT), :fallback_title)"
        if quoted_title_col
        else ":fallback_title"
    )
    subject_expr = f"t.{quoted_subject_col}" if quoted_subject_col else "NULL"
    status_expr = (
        f"COALESCE(CAST(t.{quoted_status_col} AS TEXT), 'ACTIVE')"
        if quoted_status_col
        else "'ACTIVE'"
    )

    rows = db.session.execute(text(f"""
        SELECT t.id AS entity_id,
               {title_expr} AS source_title,
               {subject_expr} AS subject_user_id,
               {status_expr} AS source_status
        FROM {quoted_table_name} t
        LEFT JOIN workflow_instances wi
          ON wi.module = :module
         AND wi.entity_type = :entity_type
         AND wi.entity_id = t.id
        WHERE wi.id IS NULL
        ORDER BY t.id DESC
        LIMIT :limit
    """), {
        "module": module,
        "entity_type": entity_type,
        "fallback_title": title_prefix,
        "limit": limit,
    }).mappings().all()

    created = 0
    for r in rows:
        raw_status = str(r.source_status or 'ACTIVE').strip().upper()
        terminal = raw_status in {
            'CLOSED', 'CLOSE', 'COMPLETED', 'DONE', 'APPROVED', 'REJECTED',
            'CANCELLED', 'CANCELED', 'KAPALI', 'TAMAMLANDI', 'TAMAMLANDI.',
            'ONAYLANDI', 'REDDEDILDI', 'REDDEDİLDİ', 'FALSE', 'F', '0', 'PASIF', 'PASİF', 'PASSIVE'
        }
        instance_status = 'COMPLETED' if terminal else 'ACTIVE'
        step_status = 'DONE' if terminal else 'PENDING'
        title = f"{title_prefix} - {str(r.source_title or '').strip() or r.entity_id}"
        wid = db.session.execute(text("""
            INSERT INTO workflow_instances(
                module, entity_type, entity_id, title, subject_user_id, status,
                current_step_name, priority, created_by_id, workflow_family, payload_json
            )
            VALUES(
                :module, :entity_type, :entity_id, :title, :subject_user_id, :status,
                :step_name, 'NORMAL', :by, :family,
                jsonb_build_object('source_table', :table_name, 'source_status', :source_status, 'faz', '4')
            )
            RETURNING id
        """), {
            "module": module,
            "entity_type": entity_type,
            "entity_id": r.entity_id,
            "title": title[:255],
            "subject_user_id": r.subject_user_id,
            "status": instance_status,
            "step_name": 'Tamamlandı' if terminal else step_name,
            "by": getattr(current_user, 'id', None),
            "family": workflow_family,
            "table_name": safe_table_name,
            "source_status": raw_status,
        }).scalar()
        db.session.execute(text("""
            INSERT INTO workflow_steps(
                workflow_id, step_order, step_code, step_type, step_name,
                assigned_user_id, status, is_active, is_required
            )
            VALUES(:wid, 1, :step_code, :step_type, :step_name, NULL, :step_status, TRUE, TRUE)
        """), {
            "wid": wid,
            "step_code": f"{module.upper()}_MAIN_STEP",
            "step_type": module.upper(),
            "step_name": step_name,
            "step_status": step_status,
        })
        db.session.execute(text("""
            INSERT INTO workflow_logs(workflow_id, user_id, action, new_status, note)
            VALUES(:wid, :by, 'AUTO_CREATED_GENERIC_WORKFLOW', :status, :note)
        """), {
            "wid": wid,
            "by": getattr(current_user, 'id', None),
            "status": instance_status,
            "note": f"Faz 4 genel iş akış bağlantısı oluşturuldu: {safe_table_name}",
        })
        created += 1
    db.session.commit()
    return created


def sync_cross_module_workflows() -> dict[str, int]:
    assert_workflow_schema_ready()
    results = {
        'support': _sync_generic_table(
            table_name='support_tickets',
            module='support',
            entity_type='support_ticket',
            title_prefix='Destek Talebi',
            title_candidates=['title', 'subject', 'summary'],
            subject_candidates=['created_by_id', 'requester_id', 'user_id', 'owner_id'],
            status_candidates=['status', 'state'],
            step_name='Destek Talebi İncelemesi',
            workflow_family='SUPPORT',
        ),
        'leave': _sync_generic_table(
            table_name='leave_requests',
            module='leave',
            entity_type='leave_request',
            title_prefix='İzin Talebi',
            title_candidates=['title', 'leave_type', 'request_type', 'summary'],
            subject_candidates=['user_id', 'employee_id', 'personnel_id', 'created_by_id'],
            status_candidates=['status', 'approval_status', 'state'],
            step_name='İzin / Vekâlet Onayı',
            workflow_family='PERSONNEL',
        ),
        'personnel_leave': _sync_generic_table(
            table_name='personnel_leaves',
            module='leave',
            entity_type='personnel_leave',
            title_prefix='Personel İzin Kaydı',
            title_candidates=['title', 'leave_type', 'summary'],
            subject_candidates=['user_id', 'employee_id', 'personnel_id', 'created_by_id'],
            status_candidates=['status', 'approval_status', 'state'],
            step_name='Personel İzin Süreci',
            workflow_family='PERSONNEL',
        ),
        'survey': _sync_generic_table(
            table_name='surveys',
            module='survey',
            entity_type='survey',
            title_prefix='Anket Süreci',
            title_candidates=['title', 'name', 'subject'],
            subject_candidates=['created_by_id', 'owner_id', 'user_id'],
            status_candidates=['status', 'state', 'is_active'],
            step_name='Anket Yayın / Katılım Takibi',
            workflow_family='COMMUNICATION',
        ),
        'announcement': _sync_generic_table(
            table_name='announcements',
            module='announcement',
            entity_type='announcement',
            title_prefix='Duyuru Süreci',
            title_candidates=['title', 'subject', 'headline'],
            subject_candidates=['created_by_id', 'owner_id', 'user_id'],
            status_candidates=['status', 'state', 'is_active'],
            step_name='Duyuru Yayın / Görünürlük Takibi',
            workflow_family='COMMUNICATION',
        ),
    }
    refresh_delay_states()
    return results


@main_bp.route('/workflow/modules')
@login_required
def workflow_modules_dashboard():
    if not _can_view():
        return _deny()
    assert_workflow_schema_ready()
    refresh_delay_states()
    rows = db.session.execute(text("""
        SELECT module,
               workflow_family,
               COUNT(*) AS total_count,
               COUNT(*) FILTER(WHERE status='ACTIVE') AS active_count,
               COUNT(*) FILTER(WHERE status='COMPLETED') AS completed_count,
               COUNT(*) FILTER(WHERE delayed_step_count > 0 AND status='ACTIVE') AS delayed_count,
               COUNT(*) FILTER(WHERE priority='HIGH' AND status='ACTIVE') AS high_count,
               COALESCE(MAX(updated_at), MAX(created_at)) AS last_activity_at
        FROM workflow_instances
        GROUP BY module, workflow_family
        ORDER BY active_count DESC, total_count DESC, module ASC
    """)).mappings().all()
    return safe_render('workflow/modules.html', rows=rows, fallback_html='<h3>Modüller Arası İş Akışları</h3>')


@main_bp.route('/workflow/sync/modules', methods=['POST'])
@login_required
def workflow_sync_modules():
    if not _can_view():
        return _deny()
    results = sync_cross_module_workflows()
    total = sum(results.values())
    flash(f'Modüller arası iş akışı taraması tamamlandı. Yeni kayıt: {total}', 'success')
    return redirect(url_for('main.workflow_modules_dashboard'))
