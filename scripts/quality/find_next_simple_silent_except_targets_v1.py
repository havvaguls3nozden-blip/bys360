from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any


EXCLUDE_PARTS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".quality_backup",
    "node_modules",
    "build",
    "dist",
}

EXCLUDE_PATH_TOKENS = (
    "versions_BACKUP",
    "versions_backup",
    "BACKUP_BEFORE",
    "backup_before",
)


def is_excluded(path: Path) -> bool:
    parts = set(path.parts)
    if parts & EXCLUDE_PARTS:
        return True
    raw = str(path)
    return any(token in raw for token in EXCLUDE_PATH_TOKENS)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def has_simple_except_pass(path: Path) -> tuple[int, list[int]]:
    text = read_text(path)
    lines = text.splitlines()
    hits: list[int] = []

    try:
        ast.parse(text)
    except SyntaxError:
        return 0, []

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("except") and stripped.endswith(":"):
            j = idx + 1
            while j < len(lines) and lines[j].strip() == "":
                j += 1
            if j < len(lines) and lines[j].strip() == "pass":
                hits.append(j + 1)

    return len(hits), hits


def load_report_paths(project_root: Path) -> list[str]:
    report = project_root / "reports" / "quality" / "bys360_quality_10_10_audit_v1_clean.json"
    if not report.exists():
        return []

    try:
        data: Any = json.loads(report.read_text(encoding="utf-8"))
    except Exception:
        return []

    if isinstance(data, dict):
        findings = (
            data.get("findings")
            or data.get("items")
            or data.get("results")
            or data.get("issues")
            or data.get("violations")
            or []
        )
    elif isinstance(data, list):
        findings = data
    else:
        findings = []

    paths: list[str] = []
    for item in findings:
        if not isinstance(item, dict):
            continue
        sev = str(item.get("severity") or item.get("level") or item.get("priority") or "").upper()
        code = str(item.get("code") or item.get("type") or item.get("rule") or item.get("category") or "")
        if sev != "P0":
            continue
        if "SILENT_EXCEPT_PASS" not in code and "silent" not in json.dumps(item, ensure_ascii=False).lower():
            continue

        path = None
        for key in ("path", "file", "filename", "rel_path", "relative_path", "source", "target"):
            value = item.get(key)
            if isinstance(value, str) and value.endswith(".py"):
                path = value
                break
        if not path:
            for value in item.values():
                if isinstance(value, str) and value.endswith(".py"):
                    path = value
                    break
        if path:
            path = path.replace("\\", "/").lstrip("./")
            if path not in paths:
                paths.append(path)

    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--prefer-report", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    print("BYS360_QUALITY_10_10_P4_NEXT_TARGET_FINDER_START")
    print(f"project_root={project_root}")

    candidates: list[tuple[str, int, list[int]]] = []

    report_paths = load_report_paths(project_root) if args.prefer_report else []
    if report_paths:
        scan_paths = [(project_root / p).resolve() for p in report_paths]
    else:
        scan_paths = [
            p for p in project_root.rglob("*.py")
            if not is_excluded(p.relative_to(project_root))
        ]

    for path in scan_paths:
        try:
            rel = path.relative_to(project_root).as_posix()
        except ValueError:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (scripts/quality/find_next_simple_silent_except_targets_v1.py:142)")
            continue
        if not path.exists() or is_excluded(path.relative_to(project_root)):
            continue

        count, lines = has_simple_except_pass(path)
        if count:
            candidates.append((rel, count, lines))

    candidates.sort(key=lambda item: (item[1], len(item[0]), item[0]))

    print("BYS360_QUALITY_10_10_P4_NEXT_TARGETS")
    shown = 0
    for rel, count, lines in candidates[: args.limit]:
        line_text = ",".join(str(x) for x in lines[:10])
        print(f"{rel} | simple_blocks={count} | pass_lines={line_text}")
        shown += 1

    print(f"targets_found={len(candidates)}")
    print(f"targets_shown={shown}")
    print("BYS360_QUALITY_10_10_P4_NEXT_TARGET_FINDER_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
