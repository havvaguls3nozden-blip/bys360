
"""Communication phase model bridge.

Secili canonical importlar icin ortak model girisi olur.

Wildcard import zinciri yerine acik import listesi kullanir.
Davranis amaci ayni kalir; hangi isimlerin tasindigi dosya uzerinde gorunur olur.
"""
from __future__ import annotations

from app.models.communication_phase1_models import CommunicationBulletin, CommunicationBulletinAudience, CommunicationBulletinReceipt

from app.models.communication_phase2_models import CommunicationBulletinRevision, CommunicationSurveyTemplate, CommunicationSurveyTemplateQuestion

from app.models.communication_phase3_models import (
    CommunicationSupportSlaPolicy,
    CommunicationSupportAssignmentLog,
    CommunicationSurveyReminderLog,
    CommunicationHelpArticleViewLog,
)

from app.models.communication_phase4_models import (
    CommunicationExecutiveReport,
    CommunicationReportExportLog,
    CommunicationGovernanceReview,
    CommunicationDailyMetric,
)

from app.models.communication_phase5_models import (
    TimestampMixin,
    CommunicationNotificationPreference,
    CommunicationDigestJob,
    CommunicationEscalationRule,
    CommunicationRetentionPolicy,
    CommunicationOperationHealth,
    CommunicationAutomationLog,
)

__all__ = [
    "CommunicationBulletin",
    "CommunicationBulletinAudience",
    "CommunicationBulletinReceipt",
    "CommunicationBulletinRevision",
    "CommunicationSurveyTemplate",
    "CommunicationSurveyTemplateQuestion",
    "CommunicationSupportSlaPolicy",
    "CommunicationSupportAssignmentLog",
    "CommunicationSurveyReminderLog",
    "CommunicationHelpArticleViewLog",
    "CommunicationExecutiveReport",
    "CommunicationReportExportLog",
    "CommunicationGovernanceReview",
    "CommunicationDailyMetric",
    "TimestampMixin",
    "CommunicationNotificationPreference",
    "CommunicationDigestJob",
    "CommunicationEscalationRule",
    "CommunicationRetentionPolicy",
    "CommunicationOperationHealth",
    "CommunicationAutomationLog",
]
