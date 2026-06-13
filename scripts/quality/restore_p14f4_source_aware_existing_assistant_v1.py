from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
from pathlib import Path


BASE_REL = "app/templates/base.html"
ASSISTANT_JS_REL = "app/static/js/bys360_assistant_module.js"
HELPER_JS_REL = "app/static/js/bys360_assistant_helpers_v1.js"

CACHE_VERSION = "assistant-restore-p14f4-existing"
ROOT_LINE = '<div id="bys360-assistant-module-root" data-bys360-assistant-module="assistant-deep-knowledge-context-v27"></div>'
MODULE_SCRIPT_LINE = '<script src="{{ url_for(\'static\', filename=\'js/bys360_assistant_module.js\') }}?v=' + CACHE_VERSION + '" defer></script>'

BACKUP_PATTERNS = [
    "p14_e2_assistant_js_helper_split_*",
    "p14_e_assistant_js_helper_split_*",
    "p9_2_technical_ui_safe_false_positive_*",
    "p9_1_technical_ui_safe_text_*",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def backup_current_files(project_root: Path) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = project_root / ".quality_backup" / f"p14f4_source_aware_assistant_restore_{stamp}"
    for rel in [BASE_REL, ASSISTANT_JS_REL, HELPER_JS_REL]:
        src = project_root / rel
        if src.exists():
            dst = backup_root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    return backup_root


def find_best_assistant_js_backup(project_root: Path) -> tuple[Path | None, dict]:
    backup_root = project_root / ".quality_backup"
    report = {"candidates": []}
    if not backup_root.exists():
        return None, report

    candidates = []
    for pattern in BACKUP_PATTERNS:
        for folder in backup_root.glob(pattern):
            js = folder / ASSISTANT_JS_REL
            if not js.exists():
                continue
            text = read_text(js)
            score = 0
            if "BYS360AssistantHelpersV1" not in text:
                score += 100
            if "BYS360_ASSISTANT_VISIBILITY_RESTORE_V31_1" in text:
                score += 30
            if "BYS360_ASSISTANT_ADVANCED_INTELLIGENCE_V32" in text:
                score += 20
            if "bys360-assistant-module-root" in text:
                score += 10
            score += min(len(text.splitlines()), 7000) / 10000
            item = {
                "folder": str(folder),
                "path": str(js),
                "line_count": len(text.splitlines()),
                "contains_helper_wrapper": "BYS360AssistantHelpersV1" in text,
                "has_visibility_restore_marker": "BYS360_ASSISTANT_VISIBILITY_RESTORE_V31_1" in text,
                "score": score,
                "mtime": folder.stat().st_mtime,
            }
            report["candidates"].append(item)
            candidates.append((score, folder.stat().st_mtime, js, item))

    if not candidates:
        return None, report

    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    report["selected"] = candidates[0][3]
    return candidates[0][2], report


def sanitize_base_for_existing_assistant(base_text: str) -> tuple[str, list[str]]:
    changes: list[str] = []
    lines = base_text.splitlines()
    new_lines = []

    removed_helper = 0
    removed_module = 0
    root_seen = False
    inserted_root = False
    inserted_module = False

    for line in lines:
        if "bys360_assistant_helpers_v1.js" in line:
            removed_helper += 1
            continue
        if "bys360_assistant_module.js" in line:
            removed_module += 1
            continue
        if 'id="bys360-assistant-module-root"' in line or "id='bys360-assistant-module-root'" in line:
            root_seen = True
        new_lines.append(line)

    if removed_helper:
        changes.append(f"removed_helper_script_lines:{removed_helper}")
    if removed_module:
        changes.append(f"removed_old_module_script_lines:{removed_module}")

    # Ensure root exists before closing body, not inside comments.
    if not root_seen:
        inserted = False
        out = []
        for line in new_lines:
            if (not inserted) and re.search(r"</body\s*>", line, flags=re.IGNORECASE):
                out.append(ROOT_LINE)
                inserted = True
                inserted_root = True
            out.append(line)
        if not inserted:
            out.append(ROOT_LINE)
            inserted_root = True
        new_lines = out
    if inserted_root:
        changes.append("assistant_root_inserted")

    # Insert cache-busted module script before closing body.
    out = []
    for line in new_lines:
        if (not inserted_module) and re.search(r"</body\s*>", line, flags=re.IGNORECASE):
            out.append(MODULE_SCRIPT_LINE)
            inserted_module = True
        out.append(line)
    if not inserted_module:
        out.append(MODULE_SCRIPT_LINE)
        inserted_module = True
    new_lines = out
    changes.append("assistant_module_script_inserted_cache_busted")

    return "\n".join(new_lines) + ("\n" if base_text.endswith("\n") else ""), changes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    base_path = project_root / BASE_REL
    assistant_path = project_root / ASSISTANT_JS_REL
    helper_path = project_root / HELPER_JS_REL

    print("BYS360_P14F4_SOURCE_AWARE_ASSISTANT_RESTORE_START")
    print(f"project_root={project_root}")
    print(f"mode={'DRY_RUN' if args.dry_run else 'APPLY'}")

    if not base_path.exists():
        raise SystemExit(f"BASE_NOT_FOUND: {base_path}")

    selected_js, source_report = find_best_assistant_js_backup(project_root)
    if selected_js is None:
        raise SystemExit("NO_SUITABLE_ASSISTANT_JS_BACKUP_FOUND_IN_QUALITY_BACKUP")

    selected_js_text = read_text(selected_js)
    if "BYS360AssistantHelpersV1" in selected_js_text:
        raise SystemExit(f"SELECTED_BACKUP_STILL_CONTAINS_HELPER_WRAPPER: {selected_js}")
    if "bys360-assistant-module-root" not in selected_js_text:
        raise SystemExit(f"SELECTED_BACKUP_DOES_NOT_LOOK_LIKE_ASSISTANT_MODULE: {selected_js}")

    current_backup = None
    if not args.dry_run:
        current_backup = backup_current_files(project_root)

    base_text = read_text(base_path)
    updated_base, base_changes = sanitize_base_for_existing_assistant(base_text)

    helper_disabled = False
    helper_disabled_path = None

    if not args.dry_run:
        assistant_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(selected_js, assistant_path)
        write_text(base_path, updated_base)

        # Disable helper file so old cache/script confusion is impossible.
        if helper_path.exists():
            disabled = helper_path.with_name(helper_path.name + ".disabled_by_p14f4")
            if disabled.exists():
                disabled.unlink()
            helper_path.rename(disabled)
            helper_disabled = True
            helper_disabled_path = str(disabled)

    final_base = updated_base if args.dry_run else read_text(base_path)
    final_js = selected_js_text if args.dry_run else read_text(assistant_path)

    result = {
        "mode": "DRY_RUN" if args.dry_run else "APPLY",
        "selected_backup_js": str(selected_js),
        "current_backup": str(current_backup) if current_backup else None,
        "source_report": source_report,
        "base_changes": base_changes,
        "base_has_root": "bys360-assistant-module-root" in final_base,
        "base_has_helper_script": "bys360_assistant_helpers_v1.js" in final_base,
        "base_has_module_script": "bys360_assistant_module.js" in final_base,
        "base_has_cache_bust_version": CACHE_VERSION in final_base,
        "assistant_js_line_count": len(final_js.splitlines()),
        "assistant_js_contains_helper_wrapper": "BYS360AssistantHelpersV1" in final_js,
        "assistant_js_has_visibility_restore_marker": "BYS360_ASSISTANT_VISIBILITY_RESTORE_V31_1" in final_js,
        "helper_file_disabled": helper_disabled,
        "helper_file_disabled_path": helper_disabled_path,
        "expected_browser_action": "Hard refresh Ctrl+F5 or open incognito because the script URL was cache-busted to " + CACHE_VERSION,
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "dryrun" if args.dry_run else "applied"
    report_json = out_dir / f"bys360_p14f4_source_aware_assistant_restore_{suffix}_v1.json"
    report_md = out_dir / f"bys360_p14f4_source_aware_assistant_restore_{suffix}_v1.md"
    write_text(report_json, json.dumps(result, ensure_ascii=False, indent=2))

    md = [
        "# BYS360 P14F4 Source-Aware Existing Assistant Restore",
        "",
        f"- Mode: `{result['mode']}`",
        f"- Selected backup JS: `{result['selected_backup_js']}`",
        f"- Current backup: `{result['current_backup']}`",
        f"- Base has root: {result['base_has_root']}",
        f"- Base has helper script: {result['base_has_helper_script']}",
        f"- Base has module script: {result['base_has_module_script']}",
        f"- Cache bust version present: {result['base_has_cache_bust_version']}",
        f"- Assistant JS line count: {result['assistant_js_line_count']}",
        f"- Assistant JS contains helper wrapper: {result['assistant_js_contains_helper_wrapper']}",
        f"- Helper file disabled: {result['helper_file_disabled']}",
        "",
        "## Base changes",
    ]
    md.extend([f"- {c}" for c in base_changes])
    write_text(report_md, "\n".join(md) + "\n")

    print(f"selected_backup_js={result['selected_backup_js']}")
    print(f"current_backup={result['current_backup']}")
    print(f"base_has_root={result['base_has_root']}")
    print(f"base_has_helper_script={result['base_has_helper_script']}")
    print(f"base_has_module_script={result['base_has_module_script']}")
    print(f"base_has_cache_bust_version={result['base_has_cache_bust_version']}")
    print(f"assistant_js_line_count={result['assistant_js_line_count']}")
    print(f"assistant_js_contains_helper_wrapper={result['assistant_js_contains_helper_wrapper']}")
    print(f"assistant_js_has_visibility_restore_marker={result['assistant_js_has_visibility_restore_marker']}")
    print(f"helper_file_disabled={result['helper_file_disabled']}")
    print("BYS360_P14F4_BASE_CHANGES")
    for c in base_changes:
        print(f"- {c}")
    print(f"report_json={report_json}")
    print(f"report_md={report_md}")
    print("BYS360_P14F4_SOURCE_AWARE_ASSISTANT_RESTORE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
