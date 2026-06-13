from __future__ import annotations

import argparse
import json
import py_compile
import re
from pathlib import Path

TARGETS = [
    "app/services/performance/period_delete_service.py",
    "scripts/quality/apply_p14f1_mobile_api_blueprint_name_fix_v1.py",
    "scripts/quality/apply_p14f2_mobile_api_route_registrar_adapter_v1.py",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def silent_pass_blocks(text: str) -> list[int]:
    lines = text.splitlines()
    found = []
    for i, line in enumerate(lines):
        if not re.match(r"^\s*except[^:\n]*:\s*(#.*)?$", line):
            continue
        j = i + 1
        body = []
        indent = re.match(r"^(\s*)", line).group(1)
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
            found.append(i + 1)
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()

    print("BYS360_QUALITY_10_10_P14_G_P0_SILENT_EXCEPT_FIX_CHECK_START")
    print(f"project_root={project_root}")

    result = {}
    failed = False

    for rel in TARGETS:
        path = project_root / rel
        if not path.exists():
            raise SystemExit(f"TARGET_NOT_FOUND: {path}")
        py_compile.compile(str(path), doraise=True)
        text = read_text(path)
        silent = silent_pass_blocks(text)
        result[rel] = {
            "compile_ok": True,
            "silent_pass_lines": silent,
            "has_logging_import": "import logging" in text,
            "has_logger": "LOGGER = logging.getLogger(__name__)" in text,
        }
        if silent:
            failed = True

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if failed:
        raise SystemExit("P14_G_CHECK_FAIL silent pass blocks remain")

    print("BYS360_QUALITY_10_10_P14_G_P0_SILENT_EXCEPT_FIX_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
