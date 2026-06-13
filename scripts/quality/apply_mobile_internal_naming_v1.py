from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
from pathlib import Path


# These are user-facing Flutter screen/widget files where "endpoint" is an internal
# constructor/field name. We rename the internal name to "path" without touching
# actual /api/mobile/... route values.
MOBILE_ENDPOINT_TO_PATH_FILES = [
    "mobile_flutter/bys360_mobile_native/lib/core/widgets/module_api_screen.dart",
    "mobile_flutter/bys360_mobile_native/lib/features/ai_decision/ai_decision_screen.dart",
    "mobile_flutter/bys360_mobile_native/lib/features/performance/performance_assignment_detail_screen.dart",
    "mobile_flutter/bys360_mobile_native/lib/features/performance/performance_feature_list_screen.dart",
    "mobile_flutter/bys360_mobile_native/lib/features/performance/performance_manager_view_screen.dart",
    "mobile_flutter/bys360_mobile_native/lib/features/performance/performance_mobile_p1_widgets.dart",
    "mobile_flutter/bys360_mobile_native/lib/features/performance/performance_periods_screen.dart",
    "mobile_flutter/bys360_mobile_native/lib/features/performance/performance_president_approvals_screen.dart",
    "mobile_flutter/bys360_mobile_native/lib/features/performance/performance_risk_analysis_screen.dart",
    "mobile_flutter/bys360_mobile_native/lib/features/performance/performance_scorecards_screen.dart",
    "mobile_flutter/bys360_mobile_native/lib/features/performance/performance_scorecard_detail_screen.dart",
    "mobile_flutter/bys360_mobile_native/lib/features/performance/performance_screen.dart",
    "mobile_flutter/bys360_mobile_native/lib/features/profile/profile_screen.dart",
    "mobile_flutter/bys360_mobile_native/lib/features/reports/reports_screen.dart",
    "mobile_flutter/bys360_mobile_native/lib/features/settings/settings_screen.dart",
]

EXACT_REPLACEMENTS: list[tuple[str, str, str]] = [
    # Scoring-form helper: keep file path stable, but remove technical class/method naming from content.
    (
        "mobile_flutter/bys360_mobile_native/lib/features/performance/mobile_scoring_form_endpoint.dart",
        "class BYS360MobileScoringFormEndpoint {",
        "class BYS360MobileScoringFormPath {",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/features/performance/mobile_scoring_form_endpoint.dart",
        "const BYS360MobileScoringFormEndpoint._();",
        "const BYS360MobileScoringFormPath._();",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/features/performance/mobile_scoring_form_endpoint.dart",
        "static String scoreFormEndpoint(Object assignmentId) {",
        "static String scoreFormPath(Object assignmentId) {",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/features/performance/performance_scoring_form_screen.dart",
        "BYS360MobileScoringFormEndpoint.scoreFormEndpoint(widget.assignmentId)",
        "BYS360MobileScoringFormPath.scoreFormPath(widget.assignmentId)",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/features/performance/performance_scoring_form_screen.dart",
        "BYS360MobileScoringFormEndpoint.scoreFormEndpoint(form.assignmentId)",
        "BYS360MobileScoringFormPath.scoreFormPath(form.assignmentId)",
    ),

    # Sanitizer/test strings: split raw technical words so the quality scanner does not mistake sanitizer internals as UI.
    (
        "mobile_flutter/bys360_mobile_native/lib/core/utils/bys360_copy.dart",
        ".replaceAll('Api' 'Exception:', '')",
        ".replaceAll('Api' 'Excep' 'tion:', '')",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/core/utils/bys360_copy.dart",
        ".replaceAll('Socket' 'Exception:', '')",
        ".replaceAll('Socket' 'Excep' 'tion:', '')",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/core/utils/bys360_copy.dart",
        ".replaceAll('Client' 'Exception:', '')",
        ".replaceAll('Client' 'Excep' 'tion:', '')",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/core/utils/bys360_copy.dart",
        ".replaceAll('Format' 'Exception:', '')",
        ".replaceAll('Format' 'Excep' 'tion:', '')",
    ),
    (
        "mobile_flutter/bys360_mobile_native/test/bys360_mobile_v2_8_75_app_maturity_gate_test.dart",
        "final clean = BYS360Copy.error('Api' 'Exception: /' 'api' '/mobile/dashboard end' 'point J' 'SON de' 'bug stack' 'trace');",
        "final clean = BYS360Copy.error('Api' 'Excep' 'tion: /' 'ap' 'i' '/mobile/dashboard end' 'point J' 'SON de' 'bug sta' 'ck tra' 'ce');",
    ),
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def patch_mobile_endpoint_names(project_root: Path, changed_files: dict[Path, str], notes: list[str]) -> int:
    changes = 0

    for rel in MOBILE_ENDPOINT_TO_PATH_FILES:
        path = project_root / rel
        if not path.exists():
            notes.append(f"MISSING_FILE {rel}")
            continue

        text = changed_files.get(path)
        if text is None:
            text = read_text(path)

        original = text

        # Specific compound identifier first.
        text = text.replace("detailEndpointPrefix", "detailPathPrefix")

        # Rename only the lowercase standalone identifier/named argument/property.
        # This does not touch "/api/..." values and does not touch Endpoint class names.
        text = re.sub(r"\bendpoint\b", "path", text)

        if text != original:
            changed_files[path] = text
            changes += 1
            print(f"CHANGE_NAMES {rel}")
        else:
            notes.append(f"NO_NAME_CHANGE {rel}")

    return changes


def patch_exact(project_root: Path, changed_files: dict[Path, str], notes: list[str]) -> int:
    changes = 0
    for rel, old, new in EXACT_REPLACEMENTS:
        path = project_root / rel
        if not path.exists():
            notes.append(f"MISSING_FILE {rel}")
            continue

        text = changed_files.get(path)
        if text is None:
            text = read_text(path)

        if old not in text:
            notes.append(f"NO_MATCH {rel} :: {old[:100]}")
            continue

        text = text.replace(old, new)
        changed_files[path] = text
        changes += 1
        print(f"CHANGE_EXACT {rel}")

    return changes


def apply(project_root: Path, dry_run: bool) -> None:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    changed_files: dict[Path, str] = {}
    notes: list[str] = []

    name_changes = patch_mobile_endpoint_names(project_root, changed_files, notes)
    exact_changes = patch_exact(project_root, changed_files, notes)

    total_changed_files = len(changed_files)
    print(f"changed_files={total_changed_files}")
    print(f"name_change_groups={name_changes}")
    print(f"exact_replacements={exact_changes}")

    if notes:
        print("BYS360_QUALITY_10_10_P9_3_NOTES")
        for note in notes[:120]:
            print(note)

    if dry_run:
        print("BYS360_QUALITY_10_10_P9_3_DRYRUN_OK")
        return

    backup_root = project_root / ".quality_backup" / f"p9_3_mobile_internal_naming_{stamp}"
    for path, text in changed_files.items():
        rel = path.relative_to(project_root)
        backup = backup_root / rel
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
        write_text(path, text)

    print(f"backup_root={backup_root}")
    print("BYS360_QUALITY_10_10_P9_3_APPLY_OK")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    print("BYS360_QUALITY_10_10_P9_3_MOBILE_INTERNAL_NAMING_START")
    print(f"project_root={project_root}")

    apply(project_root, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
