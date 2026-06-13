from __future__ import annotations

import argparse
import json
import py_compile
import re
from pathlib import Path

TARGET_REL = "scripts/quality/apply_p14_h_p1_cleanup_v1.py"


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
    target = project_root / TARGET_REL

    print("BYS360_QUALITY_10_10_P14_H2_SELF_EXCEPT_FIX_CHECK_START")
    print(f"project_root={project_root}")

    if not target.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target}")

    py_compile.compile(str(target), doraise=True)
    text = read_text(target)
    unlogged = unlogged_except_lines(text)

    result = {
        "target": TARGET_REL,
        "compile_ok": True,
        "unlogged_except_lines": unlogged,
        "has_logging_import": "import logging" in text,
        "has_logger": "LOGGER = logging.getLogger(__name__)" in text,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if unlogged:
        raise SystemExit("P14_H2_CHECK_FAIL unlogged except remains")

    print("BYS360_QUALITY_10_10_P14_H2_SELF_EXCEPT_FIX_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
