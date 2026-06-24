from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

REQUIRED_PATHS = [
    "app/services/mail_service.py",
    "app/services/message_service.py",
    "app/services/feedback_service.py",
    "app/services/settings_service.py",
    "app/services/decision_support_service.py",
    "app/security.py",
]

REQUIRED_TOKENS = [
    "get_smtp_settings",
    "send_email",
    "build_mail_system_health_snapshot",
    "security",
    "mail",
    "quality",
]


def main() -> int:
    missing = [path for path in REQUIRED_PATHS if not (ROOT / path).exists()]
    combined = "\n".join(
        (ROOT / path).read_text(encoding="utf-8", errors="ignore")
        for path in REQUIRED_PATHS
        if (ROOT / path).exists()
    )
    missing_tokens = [token for token in REQUIRED_TOKENS if token not in combined]
    if missing or missing_tokens:
        print({"ok": False, "missing": missing, "missing_tokens": missing_tokens})
        return 1
    print({"ok": True, "gate": "check_critical_services_phase5_gate.py"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


# BYS360_A5_P2D5_PHASE5_LIVE_CONTRACTS_ANCHOR_START
LIVE_CONTRACTS = [
    "app/services/mail_service.py",
    "app/services/message_service.py",
    "app/services/feedback_service.py",
    "app/services/settings_service.py",
    "app/services/decision_support_service.py",
    "app/security.py",
]

REQUIRED_MAIL_FUNCTIONS = [
    "get_smtp_settings",
    "send_email",
    "send_bulk_assignment_reminders",
    "build_mail_system_health_snapshot",
]
# BYS360_A5_P2D5_PHASE5_LIVE_CONTRACTS_ANCHOR_END


# BYS360_A5_P2D5_PHASE5_CRITICAL_TEST_PATTERNS_ANCHOR_START
CRITICAL_TEST_PATTERNS = [
    "tests/critical/test_claude_phase5_critical_contracts.py",
    "tests/security/test_final_quality_security_source_contract.py",
    "tests/communication/test_communication_route_contracts.py",
    "tests/architecture/test_message_live_contract.py",
]

CRITICAL_SERVICE_PATTERNS = [
    "security",
    "mail",
    "settings",
    "feedback",
    "message",
    "decision_support",
]
# BYS360_A5_P2D5_PHASE5_CRITICAL_TEST_PATTERNS_ANCHOR_END


# BYS360_A5_P2D5_MAINTENANCE_PHASE5_LABEL_ANCHOR_START
PHASE5_GATE_LABEL = "BYS360 Claude Faz 5"
# BYS360_A5_P2D5_MAINTENANCE_PHASE5_LABEL_ANCHOR_END

