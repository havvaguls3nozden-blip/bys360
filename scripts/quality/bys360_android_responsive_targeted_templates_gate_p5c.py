from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

PACKAGE = "BYS360_ANDROID_RESPONSIVE_TARGETED_TEMPLATES_GATE_P5C"
REPORT_REL = Path("reports/architecture/BYS360_ANDROID_RESPONSIVE_TARGETED_TEMPLATES_GATE_P5C_REPORT.json")

TARGET_TEMPLATE_HINTS = [
    "base.html",
    "dashboard",
    "performance",
    "portal",
    "file_center",
]


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def _find_templates(root: Path) -> list[Path]:
    template_root = root / "app" / "templates"
    if not template_root.exists():
        return []
    return sorted(template_root.rglob("*.html"))


def _is_target_template(path: Path) -> bool:
    normalized = str(path).replace("\\", "/").lower()
    return any(hint.lower() in normalized for hint in TARGET_TEMPLATE_HINTS)


def build_report(root: Path, write_report: bool = True) -> dict[str, Any]:
    root = root.resolve()
    templates = _find_templates(root)
    target_templates = [p for p in templates if _is_target_template(p)]

    css_files: list[Path] = []
    for css_root in [root / "app" / "static" / "css", root / "app" / "static" / "pwa"]:
        if css_root.exists():
            css_files.extend(sorted(css_root.rglob("*.css")))

    css_text = "\n".join(_read_text(path) for path in css_files)
    responsive_markers = ["@media", "max-width", "min-width", "viewport", "responsive", "mobile"]
    marker_hits = {marker: marker.lower() in css_text.lower() for marker in responsive_markers}

    target_details = []
    for path in target_templates:
        text = _read_text(path)
        target_details.append({
            "path": str(path.relative_to(root)),
            "exists": path.exists(),
            "line_count": len(text.splitlines()),
            "has_viewport": "viewport" in text.lower(),
            "has_responsive_class_hint": any(
                token in text.lower()
                for token in ["container", "row", "col-", "mobile", "responsive", "card"]
            ),
        })

    ok = bool(
        templates
        and target_templates
        and css_files
        and any(marker_hits.values())
        and all(item["exists"] for item in target_details)
    )

    report: dict[str, Any] = {
        "ok": ok,
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "template_count": len(templates),
        "target_template_count": len(target_templates),
        "css_file_count": len(css_files),
        "responsive_marker_hits": marker_hits,
        "target_templates": target_details,
        "report": str(root / REPORT_REL),
    }

    if write_report:
        report_path = root / REPORT_REL
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--no-report", action="store_true")
    args = parser.parse_args()

    report = build_report(Path(args.root), write_report=not args.no_report)
    print(json.dumps({
        "ok": report["ok"],
        "package": report["package"],
        "template_count": report["template_count"],
        "target_template_count": report["target_template_count"],
        "css_file_count": report["css_file_count"],
        "responsive_marker_hits": report["responsive_marker_hits"],
        "report": report["report"],
    }, ensure_ascii=False, indent=2))

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
