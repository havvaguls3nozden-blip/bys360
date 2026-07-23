from __future__ import annotations

from app.extensions import db
from app.models import (
    EvaluationAssignment,
    PerformanceCriteria,
    PerformancePeriod,
    PerformancePublishLog,
    User,
)
from app.services.performance.common import fetch_active_users
from app.services.performance.hierarchy import build_manager_chain_for_user

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


def seed_default_performance_criteria() -> int:
    defaults = [
        ("İş Kalitesi", "Görevlerin doğruluk, özen ve kalite düzeyi.", 20, 1),
        ("Zaman Yönetimi", "İşlerin zamanında ve planlı şekilde tamamlanması.", 20, 2),
        ("Sorumluluk Bilinci", "Görev sahipliği, takip ve sonuç odaklılık.", 20, 3),
        ("İletişim ve İş Birliği", "Takım çalışması, kurum içi iletişim ve uyum.", 20, 4),
        ("Gelişim ve Katkı", "Öğrenmeye açıklık, çözüm üretme ve kuruma katkı.", 20, 5),
    ]
    added_count = 0
    for name, description, weight, sort_order in defaults:
        exists = PerformanceCriteria.query.filter(PerformanceCriteria.name.ilike(name)).first()
        if exists:
            continue
        db.session.add(
            PerformanceCriteria(
                name=name,
                description=description,
                weight=weight,
                sort_order=sort_order,
                is_active=True,
            )
        )
        added_count += 1
    return added_count


def generate_evaluation_assignments_for_period(period_id: int) -> dict:
    period = db.session.get(PerformancePeriod, period_id)
    if not period:
        raise ValueError("Dönem bulunamadı.")

    users = fetch_active_users()
    users_by_sicil = {
        (getattr(user, "sicil_no", None) or "").strip(): user
        for user in users
        if (getattr(user, "sicil_no", None) or "").strip()
    }

    created_count = 0
    skipped_count = 0

    for employee in users:
        employee_sicil = (getattr(employee, "sicil_no", None) or "").strip()
        if not employee_sicil:
            skipped_count += 1
            continue

        chain = build_manager_chain_for_user(employee, users_by_sicil, period)

        assignments_to_create = []
        if chain.manager_1_id:
            assignments_to_create.append((1, chain.manager_1_id))
        if not chain.is_single_manager_case and chain.manager_2_id:
            assignments_to_create.append((2, chain.manager_2_id))
        explicit_level_3 = (getattr(employee, "ucuncu_yonetici_sicil", None) or "").strip()
        if not chain.is_single_manager_case and chain.manager_3_id and (chain.level_3_enabled or explicit_level_3):
            assignments_to_create.append((3, chain.manager_3_id))

        if not assignments_to_create:
            skipped_count += 1
            continue

        for level, evaluator_id in assignments_to_create:
            exists = EvaluationAssignment.query.filter_by(
                period_id=period.id,
                employee_id=employee.id,
                evaluator_id=evaluator_id,
                manager_level=level,
            ).first()

            if exists:
                skipped_count += 1
                continue

            assignment = EvaluationAssignment(
                period_id=period.id,
                employee_id=employee.id,
                evaluator_id=evaluator_id,
                manager_level=level,
                status="bekliyor",
            )
            db.session.add(assignment)
            created_count += 1

    db.session.commit()
    return {"created_count": created_count, "skipped_count": skipped_count}


def resolve_managers_for_user(employee):
    level_1_manager = None
    level_2_manager = None
    level_3_manager = None

    if not employee:
        return level_1_manager, level_2_manager, level_3_manager

    if employee.yonetici_sicil:
        level_1_manager = User.query.filter_by(sicil_no=employee.yonetici_sicil, is_active=True).first()

    if employee.ikinci_yonetici_sicil:
        level_2_manager = User.query.filter_by(sicil_no=employee.ikinci_yonetici_sicil, is_active=True).first()

    if employee.ucuncu_yonetici_sicil:
        level_3_manager = User.query.filter_by(sicil_no=employee.ucuncu_yonetici_sicil, is_active=True).first()

    return level_1_manager, level_2_manager, level_3_manager


def create_publish_log(period_id, actor_user_id, action_type, evaluation_id=None, employee_id=None, note=None):
    log = PerformancePublishLog(
        period_id=period_id,
        evaluation_id=evaluation_id,
        employee_id=employee_id,
        actor_user_id=actor_user_id,
        action_type=action_type,
        note=note,
    )
    db.session.add(log)
    return log