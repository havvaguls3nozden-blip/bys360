
"""Communication required model bridge.

Faz 1H ile communication model omurgasini zorunlu katmana ayirir.

Wildcard import zinciri yerine acik import listesi kullanir.
Davranis amaci ayni kalir; hangi isimlerin tasindigi dosya uzerinde gorunur olur.
"""
from __future__ import annotations

from app.models.communication_phase1_models import (
    CommunicationBulletin,
    CommunicationBulletinAudience,
    CommunicationBulletinReceipt,
)
from app.models.communication_phase2_models import (
    CommunicationBulletinRevision,
    CommunicationSurveyTemplate,
    CommunicationSurveyTemplateQuestion,
)
from app.models.communication_phase3_models import (
    CommunicationHelpArticleViewLog,
    CommunicationSupportAssignmentLog,
    CommunicationSupportSlaPolicy,
    CommunicationSurveyReminderLog,
)
from app.models.communication_phase4_models import (
    CommunicationDailyMetric,
    CommunicationExecutiveReport,
    CommunicationGovernanceReview,
    CommunicationReportExportLog,
)
from app.models.communication_phase5_models import (
    CommunicationAutomationLog,
    CommunicationDigestJob,
    CommunicationEscalationRule,
    CommunicationNotificationPreference,
    CommunicationOperationHealth,
    CommunicationRetentionPolicy,
    TimestampMixin,
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
