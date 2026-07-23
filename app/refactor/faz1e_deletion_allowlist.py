from __future__ import annotations

import fnmatch
from pathlib import PurePosixPath

AUTO_QUARANTINE_EXACT = {
    "app/portal/helpers_import_fix_snippet.py",
    "app/portal/portal_story_new_fixed_snippet.py",
    "app/schema_guard_faz81_snippet.py",
    "app/schema_guard_phase7_approval_hotfix_snippet.py",
    "app/schema_guard_phase7_snippet.py",
    "app/schema_guard_phase8_snippet.py",
    "app/services/performance/admin_ai_count_patch.py",
    "app/services/performance/common_admin_scope_hotfix.py",
}

REVIEW_ONLY_GLOBS = {
    "app/communication/phase*_routes.py",
    "app/institutional/*phase*_routes.py",
    "app/services/*phase*_service.py",
    "app/models/*phase*_models.py",
    "app/models/*phase*.py",
    "app/routes/*phase*_patch.py",
    "app/*phase*_hotfix.py",
    "app/config/*patch.py",
    "app/services/performance_v2/*patch.py",
    "app/templates/**/*phase*",
    "app/docs/**/*FAZ*",
    "app/docs/**/*faz*",
    "sql/*phase*",
    "scripts/*hotfix*.py",
    "scripts/*patch*.py",
    "tests/*hotfix*.py",
    "tests/**/*hotfix*.py",
}

PROTECTED_PREFIXES = (
    ".venv/",
    "venv/",
    "backups/",
    "reports/",
    "refactor_quarantine/",
    "migrations/",
    "instance/",
)

PROTECTED_SUBSTRINGS = (
    "__pycache__/",
)

KEYWORDS = ("snippet", "hotfix", "patch")
PHASE_MARKERS = ("phase", "faz")


def normalize(path: str) -> str:
    return PurePosixPath(path.replace("\\", "/")).as_posix().lstrip("./")


def is_protected(path: str) -> bool:
    p = normalize(path)
    if any(p.startswith(prefix) for prefix in PROTECTED_PREFIXES):
        return True
    return any(part in p for part in PROTECTED_SUBSTRINGS)


def is_review_only(path: str) -> bool:
    p = normalize(path)
    return any(fnmatch.fnmatch(p, pattern) for pattern in REVIEW_ONLY_GLOBS)


def looks_like_candidate(path: str) -> bool:
    p = normalize(path)
    base = PurePosixPath(p).name.lower()
    return any(k in base for k in KEYWORDS)


def is_auto_quarantine(path: str) -> bool:
    p = normalize(path)
    base = PurePosixPath(p).name.lower()

    if p in AUTO_QUARANTINE_EXACT:
        return True

    if p.startswith("app/portal/") and base.endswith("_snippet.py"):
        return True

    if p.startswith("app/") and base.startswith("schema_guard_") and "snippet" in base and p.endswith(".py"):
        return True

    return p.startswith("app/services/performance/") and p.endswith(".py") and any(k in base for k in KEYWORDS)


def classify(path: str) -> str:
    p = normalize(path)
    if is_protected(p):
        return "protected"
    if not looks_like_candidate(p):
        return "ignore"
    if is_review_only(p):
        return "review_only"
    if is_auto_quarantine(p):
        return "auto_quarantine"
    if any(marker in PurePosixPath(p).name.lower() for marker in PHASE_MARKERS):
        return "review_only"
    return "review_only"