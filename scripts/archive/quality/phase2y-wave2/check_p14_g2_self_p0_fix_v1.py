from __future__ import annotations

import argparse
import json
import py_compile
import re
from pathlib import Path

TARGET_REL = "scripts/quality/apply_p14_g_p0_silent_except_fix_v1.py"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def find_silent_pass(text: str) -> list[int]:
    lines = text.splitlines()
    out = []
    for i, line in enumerate(lines):
        if not re.match(r"^\s*except[^:\n]*:\s*(#.*)?$", line):
            continue
        indent = re.match(r"^(\s*)", line).group(1)
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
        useful = [b.strip() for b in body if b.strip() and not b.strip().startswith("#")]
        if useful == ["pass"]:
            out.append(i + 1)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    target = project_root / TARGET_REL

    print("BYS360_QUALITY_10_10_P14_G2_SELF_P0_FIX_CHECK_START")
    print(f"project_root={project_root}")

    if not target.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target}")

    py_compile.compile(str(target), doraise=True)
    text = read_text(target)
    silent = find_silent_pass(text)

    result = {
        "target": TARGET_REL,
        "compile_ok": True,
        "silent_pass_lines": silent,
        "has_logging_import": "import logging" in text,
        "has_logger": "LOGGER = logging.getLogger(__name__)" in text,
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if silent:
        raise SystemExit("P14_G2_CHECK_FAIL silent pass blocks remain")

    print("BYS360_QUALITY_10_10_P14_G2_SELF_P0_FIX_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
