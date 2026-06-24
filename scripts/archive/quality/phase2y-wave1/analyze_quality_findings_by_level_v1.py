from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_findings(data: Any, target_level: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    target_level = target_level.upper()

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            blob = json.dumps(x, ensure_ascii=False)
            level = str(
                x.get("severity")
                or x.get("level")
                or x.get("priority")
                or x.get("rank")
                or ""
            ).upper()

            path = str(
                x.get("path")
                or x.get("file")
                or x.get("filename")
                or x.get("rel_path")
                or x.get("relative_path")
                or ""
            ).replace("\\", "/").lstrip("./")

            rule = str(
                x.get("rule")
                or x.get("code")
                or x.get("type")
                or x.get("category")
                or x.get("check")
                or ""
            )

            line = x.get("line") or x.get("line_number") or x.get("lineno") or ""
            message = str(
                x.get("message")
                or x.get("detail")
                or x.get("description")
                or x.get("reason")
                or ""
            )

            # Avoid container/summary dicts with no concrete path/rule/message.
            if level == target_level and (path or rule or message):
                items.append(
                    {
                        "severity": target_level,
                        "path": path,
                        "line": line,
                        "rule": rule,
                        "message": message,
                        "raw": x,
                    }
                )

            for v in x.values():
                walk(v)

        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(data)

    seen: set[tuple[str, str, str, str]] = set()
    uniq: list[dict[str, Any]] = []
    for item in items:
        key = (
            str(item.get("path", "")),
            str(item.get("line", "")),
            str(item.get("rule", "")),
            str(item.get("message", "")),
        )
        if key not in seen:
            seen.add(key)
            uniq.append(item)

    return uniq


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--level", default="P1")
    parser.add_argument("--limit", type=int, default=80)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    report = project_root / "reports" / "quality" / "bys360_quality_10_10_audit_v1_clean.json"

    print("BYS360_QUALITY_10_10_P7_P1_ANALYSIS_START")
    print(f"project_root={project_root}")
    print(f"report={report}")

    if not report.exists():
        raise SystemExit(f"REPORT_NOT_FOUND: {report}")

    findings = collect_findings(load_json(report), args.level)
    print(f"{args.level.upper()}_findings_found={len(findings)}")

    by_rule = Counter((item.get("rule") or "NO_RULE") for item in findings)
    by_path = Counter((item.get("path") or "NO_PATH") for item in findings)

    print("BYS360_QUALITY_10_10_P7_RULE_SUMMARY")
    for rule, count in by_rule.most_common(args.limit):
        print(f"{count:>4} | {rule}")

    print("BYS360_QUALITY_10_10_P7_PATH_SUMMARY")
    for path, count in by_path.most_common(args.limit):
        print(f"{count:>4} | {path}")

    print("BYS360_QUALITY_10_10_P7_FIRST_FINDINGS")
    for i, item in enumerate(findings[: args.limit], start=1):
        print(
            f"[{i}] path={item.get('path','')} "
            f"line={item.get('line','')} "
            f"rule={item.get('rule','')}"
        )
        print(f"    message={item.get('message','')}")

    safe_keywords = (
        "TODO",
        "FIXME",
        "PRINT",
        "DEBUG",
        "COMMENT",
        "COMMENTED",
        "TRAILING",
        "WHITESPACE",
        "EMPTY",
        "DUPLICATE",
        "HARDCODED",
        "PLACEHOLDER",
        "MAINTENANCE",
        "PASS",
        "BROAD_EXCEPT",
        "EXCEPT",
        "LOG",
    )

    print("BYS360_QUALITY_10_10_P7_LIKELY_SAFE_RULES")
    for rule, count in by_rule.most_common():
        upper = str(rule).upper()
        if any(k in upper for k in safe_keywords):
            print(f"{count:>4} | {rule}")

    output_dir = project_root / "reports" / "quality"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "bys360_quality_10_10_p1_analysis_v1.json"
    output_file.write_text(
        json.dumps(
            {
                "level": args.level.upper(),
                "total": len(findings),
                "by_rule": dict(by_rule.most_common()),
                "by_path": dict(by_path.most_common()),
                "findings": findings,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"analysis_report={output_file}")
    print("BYS360_QUALITY_10_10_P7_P1_ANALYSIS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
