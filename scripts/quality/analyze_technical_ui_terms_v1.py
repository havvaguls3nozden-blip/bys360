from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


RULE = "TECHNICAL_UI_TERM"

TECH_TERMS = [
    "api", "endpoint", "debug", "gate", "workflow", "phase", "sync",
    "contract", "hardening", "exception", "stack", "trace", "raw",
    "unauthorized", "authorized_scope", "json", "token", "jwt", "http",
    "request", "response", "server", "client", "build", "release",
    "preflight", "migration", "seed", "schema", "route", "blueprint",
]

USER_SURFACE_PATTERNS = [
    "app/templates/",
    "app/static/js/",
    "app/static/css/",
    "mobile_flutter/bys360_mobile_native/lib/features/",
    "mobile_flutter/bys360_mobile_native/lib/core/widgets/",
    "mobile_flutter/bys360_mobile_native/lib/core/utils/bys360_copy.dart",
    "mobile_flutter/bys360_mobile_native/lib/core/hardening/mobile_error_texts.dart",
]

LIKELY_INTERNAL_PATTERNS = [
    "mobile_flutter/bys360_mobile_native/test/",
    "mobile_flutter/bys360_mobile_native/lib/core/api/",
    "mobile_flutter/bys360_mobile_native/lib/core/network/",
    "mobile_flutter/bys360_mobile_native/lib/core/config/",
    "mobile_flutter/bys360_mobile_native/lib/core/hardening/",
    "mobile_flutter/bys360_mobile_native/lib/core/diagnostics/",
    "mobile_flutter/bys360_mobile_native/lib/core/distribution/",
    "scripts",
]

SAFE_TEXT_HINTS = [
    "Text(", "const Text(", "label:", "title:", "subtitle:", "hintText:",
    "helperText:", "errorText:", "SnackBar", "content:", "Tooltip",
    "aria-label", "placeholder", "data-label", "innerText", "textContent",
    "{% block title %}", "<h1", "<h2", "<h3", "<p", "<span", "<div",
]

HIGH_RISK_CODE_HINTS = [
    "import ", "from ", "class ", "def ", "function ", "const ", "final ",
    "var ", "static const", "enum ", "Route", "path:", "name:",
    "Uri.", "http.", "Dio", "Future<", "Map<", "List<",
]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_findings(data: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            level = str(x.get("severity") or x.get("level") or x.get("priority") or x.get("rank") or "").upper()
            rule = str(x.get("rule") or x.get("code") or x.get("type") or x.get("category") or x.get("check") or "")
            path = str(x.get("path") or x.get("file") or x.get("filename") or x.get("rel_path") or x.get("relative_path") or "")
            line = x.get("line") or x.get("line_number") or x.get("lineno") or ""
            msg = str(x.get("message") or x.get("detail") or x.get("description") or x.get("reason") or "")
            if level == "P1" and rule == RULE and path and line:
                try:
                    line_no = int(line)
                except Exception:
                    line_no = 0
                if line_no > 0:
                    found.append({
                        "path": path.replace("\\", "/").lstrip("./"),
                        "line": line_no,
                        "rule": rule,
                        "message": msg,
                    })
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(data)

    seen = set()
    out = []
    for item in found:
        key = (item["path"], item["line"], item["rule"])
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def read_line(project_root: Path, rel: str, line_no: int) -> str:
    target = project_root / rel
    if not target.exists():
        return "<DOSYA BULUNAMADI>"
    lines = target.read_text(encoding="utf-8", errors="ignore").splitlines()
    if line_no < 1 or line_no > len(lines):
        return "<SATIR BULUNAMADI>"
    return lines[line_no - 1].strip()


def classify_path(path: str) -> str:
    lower = path.lower()
    is_surface = any(p.lower() in lower for p in USER_SURFACE_PATTERNS)
    is_internal = any(p.lower() in lower for p in LIKELY_INTERNAL_PATTERNS)
    if is_surface and not is_internal:
        return "USER_SURFACE_REVIEW"
    if is_surface and is_internal:
        if "mobile_error_texts.dart" in lower or "core/widgets/" in lower or "bys360_copy.dart" in lower:
            return "USER_SURFACE_REVIEW"
        return "LIKELY_INTERNAL_REVIEW"
    if is_internal:
        return "LIKELY_INTERNAL_OR_TEST"
    return "MIXED_REVIEW"


def classify_line(line: str) -> str:
    stripped = line.strip()
    low = stripped.lower()
    has_tech = any(re.search(rf"\b{re.escape(term)}\b", low) for term in TECH_TERMS)

    if stripped.startswith("//") or stripped.startswith("#") or stripped.startswith("/*") or stripped.startswith("*"):
        return "COMMENT_OR_DOC"
    if any(hint.lower() in low for hint in SAFE_TEXT_HINTS):
        return "LIKELY_VISIBLE_TEXT"
    if any(hint.lower() in low for hint in HIGH_RISK_CODE_HINTS):
        return "CODE_IDENTIFIER_OR_ROUTE"
    if "'" in stripped or '"' in stripped or "`" in stripped:
        return "STRING_REVIEW" if has_tech else "STRING_NO_TECH"
    return "UNKNOWN_REVIEW"


def visible_text_candidate(line_kind: str, path_kind: str) -> bool:
    return path_kind in {"USER_SURFACE_REVIEW", "MIXED_REVIEW"} and line_kind in {
        "LIKELY_VISIBLE_TEXT", "STRING_REVIEW", "COMMENT_OR_DOC"
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--limit", type=int, default=220)
    ap.add_argument("--show-lines", action="store_true")
    args = ap.parse_args()

    project_root = Path(args.project_root).resolve()
    report = project_root / "reports" / "quality" / "bys360_quality_10_10_audit_v1_clean.json"
    if not report.exists():
        raise SystemExit(f"REPORT_NOT_FOUND: {report}")

    findings = collect_findings(load_json(report))
    rows = []
    for item in findings:
        content = read_line(project_root, item["path"], int(item["line"]))
        path_kind = classify_path(item["path"])
        line_kind = classify_line(content)
        rows.append({
            **item,
            "path_kind": path_kind,
            "line_kind": line_kind,
            "candidate": visible_text_candidate(line_kind, path_kind),
            "content": content,
        })

    print("BYS360_QUALITY_10_10_P9_TECHNICAL_UI_ANALYSIS_START")
    print(f"project_root={project_root}")
    print(f"technical_ui_findings_found={len(rows)}")

    print("BYS360_QUALITY_10_10_P9_PATH_KIND_SUMMARY")
    for key, count in Counter(r["path_kind"] for r in rows).most_common():
        print(f"{count:>4} | {key}")

    print("BYS360_QUALITY_10_10_P9_LINE_KIND_SUMMARY")
    for key, count in Counter(r["line_kind"] for r in rows).most_common():
        print(f"{count:>4} | {key}")

    print("BYS360_QUALITY_10_10_P9_TOP_PATHS")
    for key, count in Counter(r["path"] for r in rows).most_common(80):
        print(f"{count:>4} | {key}")

    candidates = [r for r in rows if r["candidate"]]
    print(f"BYS360_QUALITY_10_10_P9_VISIBLE_TEXT_CANDIDATES={len(candidates)}")

    print("BYS360_QUALITY_10_10_P9_VISIBLE_TEXT_FIRST")
    for i, r in enumerate(candidates[: args.limit], 1):
        print(f"[{i}] path={r['path']} line={r['line']} path_kind={r['path_kind']} line_kind={r['line_kind']}")
        print(f"    content={r['content']}")

    if args.show_lines:
        print("BYS360_QUALITY_10_10_P9_ALL_LINES")
        for i, r in enumerate(rows[: args.limit], 1):
            print(f"[{i}] path={r['path']} line={r['line']} path_kind={r['path_kind']} line_kind={r['line_kind']} candidate={r['candidate']}")
            print(f"    content={r['content']}")

    output = project_root / "reports" / "quality" / "bys360_quality_10_10_p9_technical_ui_analysis_v1.json"
    output.write_text(json.dumps({
        "total": len(rows),
        "path_kind_summary": dict(Counter(r["path_kind"] for r in rows).most_common()),
        "line_kind_summary": dict(Counter(r["line_kind"] for r in rows).most_common()),
        "top_paths": dict(Counter(r["path"] for r in rows).most_common()),
        "visible_text_candidates": candidates,
        "all": rows,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"analysis_report={output}")
    print("BYS360_QUALITY_10_10_P9_TECHNICAL_UI_ANALYSIS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
