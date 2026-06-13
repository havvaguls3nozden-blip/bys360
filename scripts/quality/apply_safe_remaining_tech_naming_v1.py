from __future__ import annotations

import argparse
import datetime as dt
import shutil
from pathlib import Path


TEXT_REPLACEMENTS: list[tuple[str, str, str]] = [
    (
        "mobile_flutter/bys360_mobile_native/lib/features/communication/communication_screen.dart",
        "_threadsEndpoint",
        "_threadsPath",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/features/personnel/personnel_mobile_p1_screen.dart",
        "_buildEndpointAttempts",
        "_buildPathAttempts",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/features/performance/performance_scoring_form_screen.dart",
        "import 'mobile_scoring_form_endpoint.dart';",
        "import 'mobile_scoring_form_path.dart';",
    ),
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def apply(project_root: Path, dry_run: bool) -> None:
    print("BYS360_QUALITY_10_10_P10_1_SAFE_REMAINING_TECH_NAMING_START")
    print(f"project_root={project_root}")

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = project_root / ".quality_backup" / f"p10_1_safe_remaining_tech_naming_{stamp}"

    changed: dict[Path, str] = {}
    notes: list[str] = []
    replacements = 0

    for rel, old, new in TEXT_REPLACEMENTS:
        path = project_root / rel
        if not path.exists():
            notes.append(f"MISSING_FILE {rel}")
            continue

        text = changed.get(path)
        if text is None:
            text = read_text(path)

        if old not in text:
            notes.append(f"NO_MATCH {rel} :: {old}")
            continue

        text = text.replace(old, new)
        changed[path] = text
        replacements += 1
        print(f"CHANGE {rel} :: {old} -> {new}")

    old_rel = "mobile_flutter/bys360_mobile_native/lib/features/performance/mobile_scoring_form_endpoint.dart"
    new_rel = "mobile_flutter/bys360_mobile_native/lib/features/performance/mobile_scoring_form_path.dart"
    old_file = project_root / old_rel
    new_file = project_root / new_rel

    move_file = False
    if old_file.exists():
        old_text = changed.get(old_file) or read_text(old_file)
        # P9.3 already renamed class/method inside this file. If not, make it safe here too.
        old_text = old_text.replace("BYS360MobileScoringFormEndpoint", "BYS360MobileScoringFormPath")
        old_text = old_text.replace("scoreFormEndpoint", "scoreFormPath")
        changed[new_file] = old_text
        move_file = True
        print(f"MOVE {old_rel} -> {new_rel}")
    elif new_file.exists():
        notes.append(f"ALREADY_MOVED {new_rel}")
    else:
        notes.append(f"SCORING_FORM_FILE_NOT_FOUND {old_rel}")

    print(f"planned_text_replacements={replacements}")
    print(f"planned_file_move={move_file}")
    if notes:
        print("BYS360_QUALITY_10_10_P10_1_NOTES")
        for note in notes:
            print(note)

    if dry_run:
        print("BYS360_QUALITY_10_10_P10_1_DRYRUN_OK")
        return

    for path in set(list(changed.keys()) + ([old_file] if move_file else [])):
        if path.exists():
            rel = path.relative_to(project_root)
            backup = backup_root / rel
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup)

    for path, text in changed.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        write_text(path, text)

    if move_file and old_file.exists():
        old_file.unlink()

    print(f"backup_root={backup_root}")
    print("BYS360_QUALITY_10_10_P10_1_SAFE_REMAINING_TECH_NAMING_OK")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    apply(Path(args.project_root).resolve(), args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
