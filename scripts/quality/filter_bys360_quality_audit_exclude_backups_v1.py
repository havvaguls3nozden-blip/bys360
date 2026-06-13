from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXCLUDE_TOKENS = (
    ".quality_backup",
    "\\.quality_backup\\",
    "/.quality_backup/",
    "versions_BACKUP",
    "versions_backup",
    "BACKUP_BEFORE",
    "backup_before",
    "__pycache__",
    "\\build\\",
    "/build/",
    "\\dist\\",
    "/dist/",
    "\\.venv\\",
    "/.venv/",
    "\\venv\\",
    "/venv/",
    "node_modules",
)


def _norm(value: str) -> str:
    return value.replace("/", "\\").lower()


def _is_excluded_path(value: str) -> bool:
    if not value:
        return False
    raw = value.replace("/", "\\")
    low = raw.lower()
    for token in EXCLUDE_TOKENS:
        if token.lower().replace("/", "\\") in low:
            return True
    return False


def _finding_path(finding: dict[str, Any]) -> str:
    for key in ("path", "file", "filename", "rel_path", "relative_path", "source", "target"):
        value = finding.get(key)
        if isinstance(value, str) and value:
            return value
    # Fallback: scan all short string values for path-like content
    for value in finding.values():
        if isinstance(value, str) and ("\\" in value or "/" in value or value.endswith(".py")):
            return value
    return ""


def _severity(finding: dict[str, Any]) -> str:
    for key in ("severity", "level", "priority"):
        value = finding.get(key)
        if isinstance(value, str) and value:
            return value.upper()
    return "INFO"


def _find_findings_container(data: Any) -> tuple[list[dict[str, Any]] | None, str | None]:
    if isinstance(data, dict):
        for key in ("findings", "items", "results", "issues", "violations"):
            value = data.get(key)
            if isinstance(value, list) and all(isinstance(x, dict) for x in value):
                return value, key
    if isinstance(data, list) and all(isinstance(x, dict) for x in data):
        return data, None
    return None, None


def _count_by_severity(findings: list[dict[str, Any]]) -> dict[str, int]:
    counts = {"P0": 0, "P1": 0, "P2": 0, "INFO": 0}
    for finding in findings:
        sev = _severity(finding)
        if sev not in counts:
            counts[sev] = 0
        counts[sev] += 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--input", default="reports/quality/bys360_quality_10_10_audit_v1.json")
    parser.add_argument("--output", default="reports/quality/bys360_quality_10_10_audit_v1_clean.json")
    parser.add_argument("--fail-on", choices=["never", "P0", "P1", "P2"], default="never")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    input_path = (project_root / args.input).resolve()
    output_path = (project_root / args.output).resolve()

    if not input_path.exists():
        raise SystemExit(f"Rapor bulunamadı: {input_path}")

    data = json.loads(input_path.read_text(encoding="utf-8"))
    findings, key = _find_findings_container(data)

    if findings is None:
        raise SystemExit("Rapor yapısı anlaşılamadı: findings/items/results/issues/violations listesi bulunamadı.")

    kept: list[dict[str, Any]] = []
    removed: list[dict[str, Any]] = []

    for finding in findings:
        path = _finding_path(finding)
        if _is_excluded_path(path):
            removed.append(finding)
        else:
            kept.append(finding)

    if isinstance(data, dict) and key is not None:
        clean_data = dict(data)
        clean_data[key] = kept
        clean_data["summary_clean"] = _count_by_severity(kept)
        clean_data["excluded_backup_findings"] = len(removed)
    else:
        clean_data = kept

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(clean_data, ensure_ascii=False, indent=2), encoding="utf-8")

    counts = _count_by_severity(kept)
    print("BYS360_QUALITY_10_10_CLEAN_AUDIT_SUMMARY")
    print(json.dumps(counts, ensure_ascii=False))
    print(f"excluded_backup_findings={len(removed)}")
    print(f"clean_report={output_path}")

    if args.fail_on != "never":
        order = {"P0": 0, "P1": 1, "P2": 2}
        threshold = order[args.fail_on]
        failing = sum(count for sev, count in counts.items() if sev in order and order[sev] <= threshold)
        if failing > 0:
            raise SystemExit(f"BYS360_QUALITY_10_10_CLEAN_AUDIT_STRICT_FAIL fail_on={args.fail_on} count={failing}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
