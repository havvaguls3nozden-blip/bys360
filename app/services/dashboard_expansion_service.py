from __future__ import annotations

from typing import Any


def build_dashboard_catalog() -> dict[str, Any]:
    widgets = [
        {
            'slug': 'performance-period-health',
            'title': 'Performans Dönem Sağlığı',
            'source': 'Faz 6 readiness + Faz 7 pilot metrikleri',
            'target_role': ['admin', 'ik', 'group_head'],
        },
        {
            'slug': 'pilot-kpi-summary',
            'title': 'Pilot KPI Özeti',
            'source': 'pilot_execution_report.json',
            'target_role': ['admin', 'system_manager'],
        },
        {
            'slug': 'education-participation',
            'title': 'Eğitim Katılım ve Sertifika Durumu',
            'source': 'education_attendance_service',
            'target_role': ['admin', 'education_manager'],
        },
        {
            'slug': 'strategy-document-health',
            'title': 'Strateji Belge ve Arşiv Durumu',
            'source': 'repository/media manifest',
            'target_role': ['admin', 'strategy_manager'],
        },
        {
            'slug': 'portal-engagement',
            'title': 'Portal Etkileşim Özeti',
            'source': 'portal ve communication servisleri',
            'target_role': ['admin', 'communication_manager'],
        },
    ]
    return {
        'widget_count': len(widgets),
        'widgets': widgets,
        'note': 'Bu katalog Faz 8 sonrası dashboard genişletme backlogunu tek yerde toplar.',
    }