from __future__ import annotations
import argparse, json, py_compile, shutil, datetime as dt
from pathlib import Path
from typing import Any

RULE = "SILENT_EXCEPT_PASS"

def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def collect(data: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    def walk(x: Any) -> None:
        if isinstance(x, dict):
            blob = json.dumps(x, ensure_ascii=False).lower()
            sev = str(x.get("severity") or x.get("level") or x.get("priority") or x.get("rank") or "").upper()
            rule = str(x.get("rule") or x.get("code") or x.get("type") or x.get("category") or x.get("check") or "")
            path = str(x.get("path") or x.get("file") or x.get("filename") or x.get("rel_path") or x.get("relative_path") or "")
            line = x.get("line") or x.get("line_number") or x.get("lineno")
            if (sev == "P0" or '"p0"' in blob) and (RULE in rule or RULE.lower() in blob) and path and line:
                try:
                    line_no = int(line)
                except Exception:
                    line_no = 0
                if line_no > 0:
                    found.append({
                        "path": path.replace("\\", "/").lstrip("./"),
                        "line": line_no,
                        "rule": rule or RULE,
                        "message": str(x.get("message") or x.get("detail") or x.get("description") or x.get("reason") or "")
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

def patch(project_root: Path, rel: str, line_no: int, dry_run: bool) -> bool:
    target = (project_root / rel).resolve()
    if not target.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {rel}")
    text = target.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines(keepends=True)
    if line_no < 1 or line_no > len(lines):
        raise SystemExit(f"LINE_OUT_OF_RANGE: {rel}:{line_no}")
    selected_line = line_no
    raw = lines[selected_line - 1]
    if raw.strip() != "pass":
        print(f"TARGET_LINE_NOT_PASS path={rel} line={line_no} content={raw.strip()!r}")
        start, end = max(1, line_no - 8), min(len(lines), line_no + 8)
        for i in range(start, end + 1):
            if lines[i - 1].strip() == "pass":
                selected_line = i
                raw = lines[i - 1]
                print(f"NEARBY_PASS_SELECTED path={rel} requested_line={line_no} selected_line={selected_line}")
                break
    if raw.strip() != "pass":
        print("BYS360_QUALITY_10_10_P6_EXACT_LINE_NO_CHANGE")
        return False
    indent = raw[: len(raw) - len(raw.lstrip())]
    lines[selected_line - 1] = (
        f'{indent}__import__("logging").getLogger(__name__).exception('
        f'"BYS360 kalite denetimi: sessiz except/pass yakalandi ({rel}:{selected_line})")\n'
    )
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = project_root / ".quality_backup" / f"p6_exact_line_{stamp}" / rel
    print(f"selected_target={rel}")
    print(f"selected_line={selected_line}")
    print(f"backup_file={backup}")
    if dry_run:
        print("BYS360_QUALITY_10_10_P6_EXACT_LINE_DRYRUN_OK")
        return True
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target, backup)
    target.write_text("".join(lines), encoding="utf-8", newline="")
    try:
        py_compile.compile(str(target), doraise=True)
    except Exception as exc:
        shutil.copy2(backup, target)
        print("BYS360_QUALITY_10_10_P6_EXACT_LINE_ROLLED_BACK")
        raise SystemExit(f"COMPILE_FAIL_RESTORED: {exc}") from exc
    print("BYS360_QUALITY_10_10_P6_EXACT_LINE_OK")
    return True

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--target", default="")
    ap.add_argument("--line", type=int, default=0)
    ap.add_argument("--list-only", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    report = root / "reports" / "quality" / "bys360_quality_10_10_audit_v1_clean.json"
    print("BYS360_QUALITY_10_10_P6_EXACT_LINE_START")
    print(f"project_root={root}")
    if not report.exists():
        raise SystemExit(f"REPORT_NOT_FOUND: {report}")

    items = collect(read_json(report))
    if args.target:
        t = args.target.replace("\\", "/").lstrip("./")
        items = [x for x in items if x["path"] == t]
    if args.line > 0:
        items = [x for x in items if int(x["line"]) == args.line]

    print(f"remaining_silent_p0_found={len(items)}")
    for i, item in enumerate(items, 1):
        print(f"[{i}] path={item['path']} line={item['line']} rule={item['rule']} message={item['message']}")
    if args.list_only:
        print("BYS360_QUALITY_10_10_P6_EXACT_LINE_LIST_OK")
        return 0
    if not items:
        print("BYS360_QUALITY_10_10_P6_EXACT_LINE_NO_TARGET")
        return 0
    patch(root, items[0]["path"], int(items[0]["line"]), args.dry_run)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
