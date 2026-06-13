from __future__ import annotations

import argparse
import json
import py_compile
import re
from pathlib import Path

TARGETS = [
    "app/services/performance/period_delete_service.py",
    "app/services/performance/scoring_window_policy.py",
    "scripts/quality/apply_p14_e2_assistant_js_helper_split_safe_apply_v1.py",
]

PREVIEW_FILES = [
    "reports/quality/bys360_quality_10_10_p14_e2_assistant_module_applied_preview.js",
    "reports/quality/bys360_quality_10_10_p14_e2_assistant_module_dryrun_preview.js",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def unlogged_except_lines(text: str) -> list[int]:
    lines = text.splitlines()
    found = []
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(\s*)except[^:\n]*:\s*(#.*)?$", line)
        if not m:
            i += 1
            continue
        indent = m.group(1)
        j = i + 1
        body = []
        while j < len(lines):
            ln = lines[j]
            if ln.strip() == "":
                body.append(ln)
                j += 1
                continue
            if ln.startswith(indent + " ") or ln.startswith(indent + "\t"):
                body.append(ln)
                j += 1
                continue
            break
        body_text = "\n".join(body).lower()
        if "logger." not in body_text and "logging." not in body_text and re.search(r"^\s*raise\b", "\n".join(body), flags=re.MULTILINE) is None:
            found.append(i + 1)
        i = j
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()

    print("BYS360_QUALITY_10_10_P14_H_P1_CLEANUP_CHECK_START")
    print(f"project_root={project_root}")

    result = {"targets": {}, "preview_files": {}}
    failed = False

    for rel in TARGETS:
        path = project_root / rel
        if not path.exists():
            raise SystemExit(f"TARGET_NOT_FOUND: {path}")
        py_compile.compile(str(path), doraise=True)
        text = read_text(path)
        unlogged = unlogged_except_lines(text)
        result["targets"][rel] = {
            "compile_ok": True,
            "unlogged_except_lines": unlogged,
        }
        if unlogged:
            failed = True

    for rel in PREVIEW_FILES:
        exists = (project_root / rel).exists()
        result["preview_files"][rel] = {"exists": exists}
        if exists:
            failed = True

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if failed:
        raise SystemExit("P14_H_CHECK_FAIL unlogged except or preview file remains")

    print("BYS360_QUALITY_10_10_P14_H_P1_CLEANUP_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
