from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_PATHS = [
    "app/error_handlers.py",
    "app/services/settings/catalog.py",
    "scripts/windows/claude_phase7_final_quality.ps1",
]

REQUIRED_TOKENS = [
    "check_claude_phase7_final_gate.py",
    "claude_phase7_final_quality.ps1",
    "quality",
]


def main() -> int:
    missing = [path for path in REQUIRED_PATHS if not (ROOT / path).exists()]
    print({
        "ok": not missing,
        "gate": "check_claude_phase7_final_gate.py",
        "missing": missing,
        "tokens": REQUIRED_TOKENS,
    })
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
