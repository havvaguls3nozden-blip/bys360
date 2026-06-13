# BYS360 Faz 2C2 Mobile Shared Wildcard Import Apply

Tarih: 2026-06-13T10:50:32

## Sonuç

- OK: False
- Karar: PHASE2C2_ROLLBACK_OR_REVIEW_REQUIRED
- Backup root: `C:\bys360\releases\PHASE2C2_MOBILE_SHARED_WILDCARD_IMPORT_BACKUP_20260613_104715`
- Restore script: `C:\bys360\releases\PHASE2C2_MOBILE_SHARED_WILDCARD_IMPORT_BACKUP_20260613_104715\RESTORE_PHASE2C2_MOBILE_SHARED_WILDCARD_IMPORT.ps1`
- Candidate count: 11
- Changed count: 11
- Operation error count: 0
- Before all wildcards: 72
- Final all wildcards: 72
- Before mobile shared wildcards: 11
- Final mobile shared wildcards: 11
- Expected reduction: 11
- Actual reduction: 11
- Rollback performed: True
- Compileall returncode: 0
- Contract pytest returncode: 0
- Pytest quality smoke returncode: 0
- Pytest default returncode: 1
- Phase2C1 rerun returncode: 1

## Operations

```json
[
  {
    "file": "app/api/mobile/domains/assistant_chat.py",
    "line_no": 8,
    "changed": true,
    "reason": "replaced_comment_aware",
    "old_line": "from app.api.mobile.shared import *  # noqa: F401,F403 - BYS360 P1D domain endpoint importu",
    "new_line": "from app.api.mobile.shared import EvaluationAssignment, Notification, SupportTicket, User, jsonify, mobile_api_bp, request, require_mobile_user"
  },
  {
    "file": "app/api/mobile/domains/auth.py",
    "line_no": 8,
    "changed": true,
    "reason": "replaced_comment_aware",
    "old_line": "from app.api.mobile.shared import *  # noqa: F401,F403 - BYS360 P1C domain endpoint importu",
    "new_line": "from app.api.mobile.shared import User, mobile_api_bp, mobile_login_response, mobile_me_response, mobile_refresh_response, request, require_mobile_user"
  },
  {
    "file": "app/api/mobile/domains/communication_v1_write.py",
    "line_no": 8,
    "changed": true,
    "reason": "replaced_comment_aware",
    "old_line": "from app.api.mobile.shared import *  # noqa: F401,F403 - BYS360 P1D domain endpoint importu",
    "new_line": "from app.api.mobile.shared import MessageThread, MessageThreadParticipant, User, datetime, db, jsonify, mobile_api_bp, request, require_mobile_user, timezone"
  },
  {
    "file": "app/api/mobile/domains/communication_v2_write.py",
    "line_no": 8,
    "changed": true,
    "reason": "replaced_comment_aware",
    "old_line": "from app.api.mobile.shared import *  # noqa: F401,F403 - BYS360 P1D domain endpoint importu",
    "new_line": "from app.api.mobile.shared import MessageThread, MessageThreadParticipant, User, current_app, datetime, db, jsonify, mobile_api_bp, request, require_mobile_user, timezone"
  },
  {
    "file": "app/api/mobile/domains/dashboard.py",
    "line_no": 8,
    "changed": true,
    "reason": "replaced_comment_aware",
    "old_line": "from app.api.mobile.shared import *  # noqa: F401,F403 - BYS360 P1C domain endpoint importu",
    "new_line": "from app.api.mobile.shared import AIRecommendation, EvaluationAssignment, MessageThreadParticipant, Notification, PerformancePresidentApproval, SupportTicket, User, db, jsonify, mean, mobile_api_bp, require_mobile_user"
  },
  {
    "file": "app/api/mobile/domains/kpi_target_management.py",
    "line_no": 8,
    "changed": true,
    "reason": "replaced_comment_aware",
    "old_line": "from app.api.mobile.shared import *  # noqa: F401,F403 - BYS360 P1E domain endpoint importu",
    "new_line": "from app.api.mobile.shared import User, db, jsonify, mean, mobile_api_bp, request, require_mobile_user"
  },
  {
    "file": "app/api/mobile/domains/notifications.py",
    "line_no": 8,
    "changed": true,
    "reason": "replaced_comment_aware",
    "old_line": "from app.api.mobile.shared import *  # noqa: F401,F403 - BYS360 P1C domain endpoint importu",
    "new_line": "from app.api.mobile.shared import Notification, User, datetime, db, jsonify, mobile_api_bp, require_mobile_user, timezone"
  },
  {
    "file": "app/api/mobile/domains/personnel_read.py",
    "line_no": 8,
    "changed": true,
    "reason": "replaced_comment_aware",
    "old_line": "from app.api.mobile.shared import *  # noqa: F401,F403 - BYS360 P1C domain endpoint importu",
    "new_line": "from app.api.mobile.shared import User, mobile_api_bp, require_mobile_user"
  },
  {
    "file": "app/api/mobile/domains/personnel_write_all.py",
    "line_no": 8,
    "changed": true,
    "reason": "replaced_comment_aware",
    "old_line": "from app.api.mobile.shared import *  # noqa: F401,F403 - BYS360 P1E domain endpoint importu",
    "new_line": "from app.api.mobile.shared import Any, IntegrityError, User, current_app, db, get_default_first_login_password, jsonify, mobile_api_bp, request, require_mobile_user"
  },
  {
    "file": "app/api/mobile/domains/support_survey_write.py",
    "line_no": 8,
    "changed": true,
    "reason": "replaced_comment_aware",
    "old_line": "from app.api.mobile.shared import *  # noqa: F401,F403 - BYS360 P1C domain endpoint importu",
    "new_line": "from app.api.mobile.shared import Any, SupportTicket, SupportTicketMessage, SupportTicketStatusHistory, Survey, SurveyAnswer, SurveyResponse, User, datetime, db, jsonify, mobile_api_bp, notify_support_ticket_comment, notify_support_ticket_created, request, require_mobile_user, timezone"
  },
  {
    "file": "app/api/mobile/routes.py",
    "line_no": 7,
    "changed": true,
    "reason": "replaced_comment_aware",
    "old_line": "from app.api.mobile.shared import *  # noqa: F401,F403 - P1B endpoint sözleşmesi için bilinçli facade import",
    "new_line": "from app.api.mobile.shared import User, jsonify, request"
  }
]
```

## Validation

```json
{
  "compileall_returncode": 0,
  "contract_pytest_returncode": 0,
  "contract_pytest_summary": {
    "passed": 2,
    "failed": 0,
    "errors": 0,
    "skipped": 0,
    "deselected": 0,
    "warnings": 0
  },
  "pytest_quality_smoke_returncode": 0,
  "pytest_quality_smoke_summary": {
    "passed": 5,
    "failed": 0,
    "errors": 0,
    "skipped": 0,
    "deselected": 0,
    "warnings": 0
  },
  "pytest_default_returncode": 1,
  "pytest_default_summary": {
    "warnings": 0,
    "failed": 13,
    "passed": 733,
    "skipped": 2,
    "deselected": 34,
    "errors": 0
  },
  "phase2c1_rerun_returncode": 1
}
```

## Phase2C1 After

```json
{
  "wildcard_import_count": 72,
  "ready_for_explicit_import_count": 31,
  "manual_review_count": 41,
  "first_apply_candidate_count": 11,
  "ok": true
}
```

## Sonraki Adım

Rapor incelenmeli; rollback yapıldıysa dosyalar eski halindedir.