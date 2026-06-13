from __future__ import annotations

from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
import json
import os
import re
import subprocess

ROOT = Path(".").resolve()
QUALITY = ROOT / "reports" / "quality"

A12F_JSON = QUALITY / "BYS360_A12F_UI_TECHNICAL_LANGUAGE_FINAL_EVIDENCE.json"

OUT_JSON = QUALITY / "BYS360_A13A_UI_DESIGN_SYSTEM_INVENTORY.json"
OUT_MD = QUALITY / "BYS360_A13A_UI_DESIGN_SYSTEM_INVENTORY.md"

SCAN_ROOTS = [
    Path("app/templates"),
    Path("app/static/css"),
    Path("app/static/js"),
]

INCLUDE_SUFFIXES = {".html", ".jinja", ".jinja2", ".css", ".js"}

EXCLUDE_PARTS = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    "reports",
    "logs",
    "tests",
    "migrations",
    "scripts",
    ".venv",
}

COMPONENT_HINTS = [
    "btn",
    "button",
    "card",
    "panel",
    "box",
    "tile",
    "badge",
    "chip",
    "pill",
    "alert",
    "modal",
    "table",
    "form",
    "input",
    "dropdown",
    "tab",
    "accordion",
]

DESIGN_RISK_PATTERNS = {
    "inline_style": r"\sstyle\s*=",
    "hardcoded_hex_color": r"#[0-9a-fA-F]{3,8}\b",
    "hardcoded_rgb_color": r"\brgba?\s*\(",
    "important_css": r"!important\b",
    "pixel_fixed_width": r"\bwidth\s*:\s*\d{3,}px\b",
    "pixel_fixed_height": r"\bheight\s*:\s*\d{3,}px\b",
    "absolute_position": r"\bposition\s*:\s*absolute\b",
    "negative_margin": r"\bmargin[-\w]*\s*:\s*-\d",
}

SAFE_FALSE_POSITIVE = [
    "csrf",
    "sha256",
    "hash",
    "data-color-id",
]


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))
    except Exception as exc:
        return {"_read_error": str(exc), "_path": str(path)}


def run_cmd(cmd, timeout=1800):
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="ignore",
        env={
            **os.environ,
            "PYTHONIOENCODING": "utf-8",
            "BYS360_RUN_LEGACY_ARCHITECTURE_TESTS": "1",
        },
        timeout=timeout,
    )
    return {
        "cmd": " ".join(map(str, cmd)),
        "returncode": proc.returncode,
        "combined": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-20000:],
    }


def parse_pytest_summary(text: str) -> dict:
    summary = {}
    pattern = r"(\d+)\s+(failed|passed|error|errors|skipped|deselected|warning|warnings)\b"
    for num, key in re.findall(pattern, text or "", flags=re.IGNORECASE):
        key = key.lower()
        if key == "error":
            key = "errors"
        if key == "warning":
            key = "warnings"
        summary[key] = int(num)

    for key in ["failed", "passed", "errors", "skipped", "deselected", "warnings"]:
        summary.setdefault(key, 0)

    return summary


def should_scan(path: Path) -> bool:
    if not path.is_file():
        return False
    if path.suffix.lower() not in INCLUDE_SUFFIXES:
        return False
    if set(path.parts) & EXCLUDE_PARTS:
        return False
    return True


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def is_safe_false_positive(line: str) -> bool:
    low = line.lower()
    return any(x in low for x in SAFE_FALSE_POSITIVE)


def extract_classes_from_line(line: str) -> list[str]:
    classes = []
    for match in re.finditer(r'class\s*=\s*["\']([^"\']+)["\']', line, flags=re.IGNORECASE):
        raw = match.group(1)
        for cls in raw.split():
            cls = cls.strip()
            if cls and "{{" not in cls and "{%" not in cls:
                classes.append(cls)
    return classes


def classify_component_class(cls: str) -> str | None:
    low = cls.lower()
    for hint in COMPONENT_HINTS:
        if hint in low:
            return hint
    return None


def scan_file(path: Path) -> tuple[list[dict], list[dict], Counter]:
    findings = []
    component_rows = []
    component_counter = Counter()

    text = path.read_text(encoding="utf-8-sig", errors="ignore")
    suffix = path.suffix.lower()

    for line_no, line in enumerate(text.splitlines(), start=1):
        if not is_safe_false_positive(line):
            for risk_name, pattern in DESIGN_RISK_PATTERNS.items():
                if re.search(pattern, line, flags=re.IGNORECASE):
                    findings.append({
                        "path": rel(path),
                        "line_no": line_no,
                        "risk": risk_name,
                        "line": line.strip()[:700],
                    })

        if suffix in {".html", ".jinja", ".jinja2"}:
            classes = extract_classes_from_line(line)
            for cls in classes:
                component_type = classify_component_class(cls)
                if component_type:
                    component_counter[(component_type, cls)] += 1
                    component_rows.append({
                        "path": rel(path),
                        "line_no": line_no,
                        "component_type": component_type,
                        "class": cls,
                    })

    return findings, component_rows, component_counter


def scan_css_selectors() -> tuple[Counter, list[dict]]:
    selector_counter = Counter()
    selector_locations = defaultdict(list)

    for root in SCAN_ROOTS:
        if not root.exists():
            continue

        for path in sorted(root.rglob("*")):
            if not should_scan(path):
                continue
            if path.suffix.lower() != ".css":
                continue

            text = path.read_text(encoding="utf-8-sig", errors="ignore")
            for line_no, line in enumerate(text.splitlines(), start=1):
                if "{" not in line:
                    continue

                selector = line.split("{", 1)[0].strip()
                if not selector:
                    continue
                if selector.startswith("@"):
                    continue

                selector_counter[selector] += 1
                selector_locations[selector].append({
                    "path": rel(path),
                    "line_no": line_no,
                })

    duplicates = []
    for selector, count in selector_counter.items():
        if count > 1:
            duplicates.append({
                "selector": selector,
                "count": count,
                "locations": selector_locations[selector][:20],
            })

    duplicates.sort(key=lambda x: x["count"], reverse=True)
    return selector_counter, duplicates


def main() -> int:
    QUALITY.mkdir(parents=True, exist_ok=True)

    a12f = read_json(A12F_JSON)

    scan_files = []
    for root in SCAN_ROOTS:
        if root.exists():
            scan_files.extend([p for p in root.rglob("*") if should_scan(p)])

    findings = []
    component_rows = []
    component_counter = Counter()

    for path in sorted(scan_files):
        file_findings, file_components, file_component_counter = scan_file(path)
        findings.extend(file_findings)
        component_rows.extend(file_components)
        component_counter.update(file_component_counter)

    risk_by_type = Counter(item["risk"] for item in findings)
    risk_by_path = Counter(item["path"] for item in findings)

    component_by_type = Counter()
    component_class_counter = Counter()

    for (component_type, cls), count in component_counter.items():
        component_by_type[component_type] += count
        component_class_counter[cls] += count

    css_selector_counter, duplicate_selectors = scan_css_selectors()

    compile_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "compileall",
        "-q",
        "app",
        "scripts",
        "migrations",
    ])

    pytest_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "pytest",
        "tests",
        "--ignore=tests/_archive_a5_obsolete",
        "-m",
        "not live and not realdb and not slow",
        "-q",
        "-ra",
    ])

    pytest_summary = parse_pytest_summary(pytest_result["combined"])

    tests_ok = (
        compile_result["returncode"] == 0
        and pytest_result["returncode"] == 0
        and pytest_summary.get("failed", 0) == 0
        and pytest_summary.get("errors", 0) == 0
        and pytest_summary.get("warnings", 0) == 0
        and pytest_summary.get("passed", 0) >= 700
    )

    ok = (
        a12f.get("ok") is True
        and tests_ok
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A13A_UI_DESIGN_SYSTEM_INVENTORY",
        "mode": "audit_only_no_code_change",
        "ok": ok,
        "decision": "A13A_INVENTORY_COMPLETED" if ok else "A13A_BLOCKED_TEST_OR_SOURCE_FAILURE",
        "source_a12f_ok": a12f.get("ok"),
        "scanned_file_count": len(scan_files),
        "design_risk_count": len(findings),
        "risk_by_type": dict(risk_by_type),
        "risk_by_path_top_80": dict(risk_by_path.most_common(80)),
        "component_occurrence_count": len(component_rows),
        "component_by_type": dict(component_by_type),
        "component_class_top_120": dict(component_class_counter.most_common(120)),
        "duplicate_css_selector_count": len(duplicate_selectors),
        "duplicate_css_selectors_top_120": duplicate_selectors[:120],
        "design_risks_top_500": findings[:500],
        "component_rows_top_500": component_rows[:500],
        "compileall_returncode": compile_result["returncode"],
        "pytest_returncode": pytest_result["returncode"],
        "pytest_summary": pytest_summary,
        "next_action": "A13B: tasarım sistemi hedef sınıfları ve güvenli konsolidasyon planı hazırlanacak.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 A13A UI Design System Envanteri",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Source A12F OK: {result['source_a12f_ok']}",
        f"- Taranan dosya sayısı: {result['scanned_file_count']}",
        f"- Design risk count: {result['design_risk_count']}",
        f"- Component occurrence count: {result['component_occurrence_count']}",
        f"- Duplicate CSS selector count: {result['duplicate_css_selector_count']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Pytest returncode: {result['pytest_returncode']}",
        "",
        "## Pytest Summary",
        "",
        "```json",
        json.dumps(pytest_summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Risk by Type",
        "",
        "```json",
        json.dumps(result["risk_by_type"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Risk by Path",
        "",
        "```json",
        json.dumps(result["risk_by_path_top_80"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Component by Type",
        "",
        "```json",
        json.dumps(result["component_by_type"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Component Class Top 120",
        "",
        "```json",
        json.dumps(result["component_class_top_120"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Duplicate CSS Selectors Top 120",
        "",
        "```json",
        json.dumps(result["duplicate_css_selectors_top_120"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Design Risks Top 500",
        "",
        "```json",
        json.dumps(result["design_risks_top_500"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("A13A_REPORT_JSON:", OUT_JSON)
    print("A13A_REPORT_MD:", OUT_MD)
    print("A13A_SOURCE_A12F_OK:", result["source_a12f_ok"])
    print("A13A_SCANNED_FILE_COUNT:", result["scanned_file_count"])
    print("A13A_DESIGN_RISK_COUNT:", result["design_risk_count"])
    print("A13A_RISK_BY_TYPE:", json.dumps(result["risk_by_type"], ensure_ascii=False))
    print("A13A_COMPONENT_OCCURRENCE_COUNT:", result["component_occurrence_count"])
    print("A13A_COMPONENT_BY_TYPE:", json.dumps(result["component_by_type"], ensure_ascii=False))
    print("A13A_DUPLICATE_CSS_SELECTOR_COUNT:", result["duplicate_css_selector_count"])
    print("A13A_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("A13A_PYTEST_RETURN_CODE:", result["pytest_returncode"])
    print("A13A_PYTEST_SUMMARY:", json.dumps(pytest_summary, ensure_ascii=False))
    print("A13A_OK:", result["ok"])

    return 0 if tests_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
