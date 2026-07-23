from __future__ import annotations

from collections.abc import Iterable
from datetime import timedelta

from app.core.datetime_utils import utc_now
from app.models import (
    EvaluationAssignment,
    FeedbackMeeting,
    PerformanceEvaluation,
    PerformancePeriod,
    User,
)
from app.services.hierarchy_health_service import (
    build_hierarchy_health_rows,
    summarize_hierarchy_health,
)
from app.services.runtime_cache import get_or_set

"""Karar sinyalleri ve uyarilar.

Personel – saat 00:12.
Bu katmanin olayi su: ekrana bakinca sadece veri degil, neye bakman gerektigi de gorunsun.
"""

FOLLOW_UP_DAY = 7
DELAY_DAY = 14


def _age_bucket(assigned_at):
    if not assigned_at:
        return 'fresh'
    age = utc_now() - assigned_at
    if age >= timedelta(days=DELAY_DAY):
        return 'delayed'
    if age >= timedelta(days=FOLLOW_UP_DAY):
        return 'attention'
    return 'fresh'


def _build_dashboard_hierarchy_summary() -> dict[str, object]:
    rows = build_hierarchy_health_rows(
        User.query.filter(User.role != 'admin', User.is_active.is_(True)).all()
    )
    return summarize_hierarchy_health(rows)


def build_dashboard_signal_context(user) -> dict[str, object]:
    summary = get_or_set(
        'dashboard:signal:hierarchy_summary:v1',
        _build_dashboard_hierarchy_summary,
        ttl_seconds=45,
    )
    open_assignments = EvaluationAssignment.query.filter(
        EvaluationAssignment.evaluator_id == user.id,
        EvaluationAssignment.status != 'tamamlandi',
    ).all()
    delayed_count = sum(1 for assignment in open_assignments if _age_bucket(getattr(assignment, 'assigned_at', None)) == 'delayed')
    attention_count = sum(1 for assignment in open_assignments if _age_bucket(getattr(assignment, 'assigned_at', None)) == 'attention')

    today = utc_now().date()
    next_week = today + timedelta(days=7)
    meeting_count = FeedbackMeeting.query.filter(
        FeedbackMeeting.status == 'planlandi',
        FeedbackMeeting.meeting_date >= today,
        FeedbackMeeting.meeting_date <= next_week,
    ).count()
    unpublished_count = PerformanceEvaluation.query.filter(
        PerformanceEvaluation.status == 'tamamlandi',
        PerformanceEvaluation.is_published_to_employee.is_(False),
    ).count()
    active_period = PerformancePeriod.query.filter_by(is_active=True).order_by(PerformancePeriod.id.desc()).first()

    signal_items = [
        {
            'label': 'Zincir eksiği',
            'value': summary['missing_chain_count'],
            'note': 'Amiri eksik kayıtlar',
            'tone': 'danger' if summary['missing_chain_count'] else 'success',
        },
        {
            'label': 'Takip eşiği aşan görev',
            'value': delayed_count,
            'note': f'{DELAY_DAY}+ gündür açık kalan görevler',
            'tone': 'danger' if delayed_count else 'gray',
        },
        {
            'label': 'Yayın bekleyen sonuç',
            'value': unpublished_count,
            'note': 'Tamamlanmış ama personele açılmamış',
            'tone': 'warning' if unpublished_count else 'success',
        },
        {
            'label': 'Yaklaşan görüşme',
            'value': meeting_count,
            'note': '7 gün içindeki planlı görüşmeler',
            'tone': 'info' if meeting_count else 'gray',
        },
    ]
    warning_items = [
        {
            'label': 'Hiyerarşi eksiği',
            'value': summary['missing_chain_count'],
            'text': 'Amir zinciri eksik kayıtlar görev üretimi ve değerlendirme dağılımını doğrudan etkiler.',
            'tone': 'danger' if summary['missing_chain_count'] else 'success',
            'icon': 'fa-solid fa-sitemap',
            'href': '/performance/hierarchy-settings',
            'href_label': 'Hiyerarşiyi aç',
        },
        {
            'label': 'Takip isteyen görev',
            'value': delayed_count + attention_count,
            'text': 'Uzun süredir açık kalan ya da takip eşiğine gelen görevler gözden kaçmasın.',
            'tone': 'warning' if (delayed_count + attention_count) else 'gray',
            'icon': 'fa-solid fa-list-check',
            'href': '/performance/tasks',
            'href_label': 'Görevleri aç',
        },
        {
            'label': 'Aktif dönem',
            'value': getattr(active_period, 'title', '-') or '-',
            'text': 'Karar verirken bakılan tüm sayıların hangi döneme ait olduğu görünür kalsın.',
            'tone': 'info' if active_period else 'gray',
            'icon': 'fa-solid fa-calendar-days',
        },
    ]
    return {
        'dashboard_signal_items': signal_items,
        'dashboard_warning_items': warning_items,
        'dashboard_hierarchy_summary': summary,
    }


def build_task_signal_context(assignments: Iterable[EvaluationAssignment], hierarchy_summary: dict[str, object] | None = None) -> dict[str, object]:
    assignment_list = list(assignments)
    delayed_count = sum(1 for assignment in assignment_list if assignment.status != 'tamamlandi' and _age_bucket(getattr(assignment, 'assigned_at', None)) == 'delayed')
    attention_count = sum(1 for assignment in assignment_list if assignment.status != 'tamamlandi' and _age_bucket(getattr(assignment, 'assigned_at', None)) == 'attention')
    pending_count = sum(1 for assignment in assignment_list if assignment.status == 'bekliyor')
    hierarchy_summary = hierarchy_summary or {}
    chain_issue_count = int(hierarchy_summary.get('missing_chain_count') or 0) + int(hierarchy_summary.get('conflict_count') or 0)
    signal_items = [
        {'label': 'Geciken görev', 'value': delayed_count, 'note': f'{DELAY_DAY}+ gündür açık', 'tone': 'danger' if delayed_count else 'success'},
        {'label': 'Takip eşiğine gelen', 'value': attention_count, 'note': f'{FOLLOW_UP_DAY}+ gündür açık', 'tone': 'warning' if attention_count else 'gray'},
        {'label': 'Bekleyen kayıt', 'value': pending_count, 'note': 'Henüz başlanmamış görevler', 'tone': 'info' if pending_count else 'gray'},
        {'label': 'Zincir problemi', 'value': chain_issue_count, 'note': 'Görev dağılımını etkileyebilir', 'tone': 'danger' if chain_issue_count else 'success'},
    ]
    warning_items = [
        {
            'label': 'Görev sinyali',
            'value': delayed_count + attention_count,
            'text': 'Bu alan sadece görevleri değil, sorumluluk riskini de gösterir.',
            'tone': 'warning' if (delayed_count + attention_count) else 'gray',
            'icon': 'fa-solid fa-tower-broadcast',
        }
    ]
    return {'task_signal_items': signal_items, 'task_warning_items': warning_items}


def build_personnel_signal_context(summary: dict[str, object]) -> dict[str, object]:
    items = [
        {'label': 'Zincir eksiği', 'value': summary.get('missing_chain_count', 0), 'note': '1. veya 2. amiri eksik kayıtlar', 'tone': 'danger' if summary.get('missing_chain_count') else 'success'},
        {'label': 'Atama yok', 'value': summary.get('unassigned_count', 0), 'note': 'Hiç amir atanmamış kayıtlar', 'tone': 'warning' if summary.get('unassigned_count') else 'gray'},
        {'label': 'Çakışma', 'value': summary.get('conflict_count', 0), 'note': 'Aynı amir / döngü riski', 'tone': 'warning' if summary.get('conflict_count') else 'gray'},
        {'label': 'Yük sinyali', 'value': summary.get('overload_count', 0), 'note': 'Görev yükü yükselen amirler', 'tone': 'info' if summary.get('overload_count') else 'gray'},
    ]
    warnings = [
        {
            'label': 'Personel riski',
            'value': (summary.get('missing_chain_count', 0) or 0) + (summary.get('conflict_count', 0) or 0),
            'text': 'Listeye bakınca zinciri eksik, ataması boş ya da yükü artmış kayıtlar hemen görünsün diye bu alanı öne aldım.',
            'tone': 'danger' if ((summary.get('missing_chain_count', 0) or 0) + (summary.get('conflict_count', 0) or 0)) else 'gray',
            'icon': 'fa-solid fa-user-shield',
        }
    ]
    return {'personnel_signal_items': items, 'personnel_warning_items': warnings}


def build_hierarchy_signal_context(summary: dict[str, object]) -> dict[str, object]:
    items = [
        {'label': 'Zinciri eksik', 'value': summary.get('missing_chain_count', 0), 'note': 'Amir ataması tamamlanmamış', 'tone': 'danger' if summary.get('missing_chain_count') else 'success'},
        {'label': 'Çakışma', 'value': summary.get('conflict_count', 0), 'note': 'Aynı kişi / döngü riski', 'tone': 'warning' if summary.get('conflict_count') else 'gray'},
        {'label': 'Atama yok', 'value': summary.get('unassigned_count', 0), 'note': 'Hiç amir tanımı olmayan', 'tone': 'warning' if summary.get('unassigned_count') else 'gray'},
        {'label': 'Dengeli kayıt', 'value': summary.get('balanced_count', 0), 'note': 'Ek sorun görünmeyen personel', 'tone': 'success' if summary.get('balanced_count') else 'gray'},
    ]
    warnings = [
        {
            'label': 'Hiyerarşi sağlığı',
            'value': summary.get('missing_chain_count', 0),
            'text': 'Satıra geçtiğinde hangi personelin neden sorunlu olduğunu altta doğrudan gör. Burada gizli alan bırakmadım.',
            'tone': 'danger' if summary.get('missing_chain_count') else 'gray',
            'icon': 'fa-solid fa-diagram-project',
        }
    ]
    return {'hierarchy_signal_items': items, 'hierarchy_warning_items': warnings}