from __future__ import annotations

import argparse
import ast
import datetime as dt
import json
import shutil
from pathlib import Path
from typing import Any


TARGET_REL = "app/api/mobile/performance_routes.py"
NEW_MODULE_REL = "app/api/mobile/performance_read_routes.py"

TARGET_FUNCTIONS = [
    "mobile_performance_manager_view_v2852",
    "mobile_performance_periods",
    "mobile_performance_weights",
    "mobile_performance_tasks",
    "mobile_performance_manager_tasks",
    "mobile_performance_categories",
    "mobile_performance_reminders",
    "mobile_performance_in_period_note_options_v2853",
]

IMPORT_SENTINEL = "# BYS360 P11-C1: mobile performance read routes bridge"
CALL_LINE = "_register_mobile_performance_read_routes_v1(globals())"

BLOCKED_FUNCTIONS = {
    "mobile_performance_task_score_submit",
}

BLOCKED_SOURCE_HINTS = [
    "commit(",
    "rollback(",
    "db.session.add",
    "db.session.delete",
    ".delete(",
    "request.json",
    "request.form",
    "request.get_json",
    "set_password",
    "password",
    "publish",
    "approve",
    "onayla",
    "score_submit",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def node_start_with_decorators(node: ast.AST) -> int:
    start = getattr(node, "lineno", 0) or 0
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.decorator_list:
        dec_starts = [getattr(dec, "lineno", start) or start for dec in node.decorator_list]
        start = min([start] + dec_starts)
    return start


def node_end(node: ast.AST) -> int:
    return getattr(node, "end_lineno", getattr(node, "lineno", 0)) or 0


def segment(lines: list[str], start: int, end: int) -> str:
    return "\n".join(lines[start - 1:end]).rstrip() + "\n"


def literal_string(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return ""


def decorator_info(node: ast.AST) -> list[dict[str, Any]]:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return []

    rows: list[dict[str, Any]] = []
    for dec in node.decorator_list:
        if not isinstance(dec, ast.Call):
            continue

        func = dec.func
        decorator_name = ""
        blueprint_name = ""

        if isinstance(func, ast.Attribute):
            decorator_name = func.attr
            if isinstance(func.value, ast.Name):
                blueprint_name = func.value.id
        elif isinstance(func, ast.Name):
            decorator_name = func.id

        if decorator_name not in {"route", "get", "post", "put", "patch", "delete"}:
            continue

        route = literal_string(dec.args[0]) if dec.args else ""
        methods: list[str] = []
        for kw in dec.keywords:
            if kw.arg != "methods":
                continue
            if isinstance(kw.value, (ast.List, ast.Tuple, ast.Set)):
                for item in kw.value.elts:
                    val = literal_string(item)
                    if val:
                        methods.append(val.upper())

        if decorator_name in {"get", "post", "put", "patch", "delete"} and not methods:
            methods = [decorator_name.upper()]
        if decorator_name == "route" and not methods:
            methods = ["GET"]

        try:
            dec_text = ast.unparse(dec)
        except Exception:
            dec_text = ""

        rows.append({
            "decorator_name": decorator_name,
            "blueprint_name": blueprint_name,
            "route": route,
            "methods": sorted(set(methods)),
            "decorator": dec_text,
        })

    return rows


def validate_target(node: ast.AST, source: str) -> None:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        raise SystemExit("TARGET_IS_NOT_FUNCTION")

    if node.name in BLOCKED_FUNCTIONS:
        raise SystemExit(f"BLOCKED_FUNCTION_SELECTED: {node.name}")

    infos = decorator_info(node)
    if not infos:
        raise SystemExit(f"TARGET_HAS_NO_ROUTE_DECORATOR: {node.name}")

    for info in infos:
        methods = set(info["methods"])
        if not methods or methods - {"GET"}:
            raise SystemExit(f"TARGET_NOT_GET_ONLY: {node.name} methods={sorted(methods)}")
        if info["decorator_name"] not in {"get", "route"}:
            raise SystemExit(f"TARGET_UNSAFE_DECORATOR: {node.name} decorator={info['decorator_name']}")

    lowered = source.lower()
    hits = [hint for hint in BLOCKED_SOURCE_HINTS if hint.lower() in lowered]
    if hits:
        raise SystemExit(f"TARGET_HAS_BLOCKED_HINTS: {node.name} hits={hits}")


def make_new_module_text(function_sources: list[str]) -> str:
    source_blob = "\n\n".join(src.rstrip() for src in function_sources) + "\n"
    parts = [
        "# BYS360 mobile performance read route bridge module.",
        "# P11-C1 kapsamında küçük ve GET/read performans endpointleri ayrılmıştır.",
        "# URL path, decorator ve JSON cevap davranışı değiştirilmemelidir.",
        "",
        "from __future__ import annotations",
        "",
        "_PERFORMANCE_READ_ROUTE_SOURCE = " + repr(source_blob),
        "",
        "",
        "def register_mobile_performance_read_routes_v1(route_globals: dict) -> None:",
        "    \"\"\"Register selected read-only mobile performance routes in the original module context.\"\"\"",
        "    if route_globals.get(\"_BYS360_P11_C1_PERFORMANCE_READ_ROUTES_REGISTERED\"):",
        "        return",
        "",
        "    exec(_PERFORMANCE_READ_ROUTE_SOURCE, route_globals, route_globals)",
        "    route_globals[\"_BYS360_P11_C1_PERFORMANCE_READ_ROUTES_REGISTERED\"] = True",
        "",
    ]
    return "\n".join(parts)


def import_block() -> str:
    return (
        f"{IMPORT_SENTINEL}\n"
        "from app.api.mobile.performance_read_routes import register_mobile_performance_read_routes_v1 as _register_mobile_performance_read_routes_v1\n"
        f"{CALL_LINE}\n"
    )


def apply(project_root: Path, dry_run: bool) -> None:
    target = project_root / TARGET_REL
    new_module = project_root / NEW_MODULE_REL

    if not target.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target}")

    text = read_text(target)
    if IMPORT_SENTINEL in text and new_module.exists():
        print("BYS360_QUALITY_10_10_P11_C1_ALREADY_APPLIED")
        return

    lines = text.splitlines()
    tree = ast.parse(text)

    found: dict[str, dict[str, Any]] = {}
    route_meta: dict[str, Any] = {}

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in TARGET_FUNCTIONS:
            start = node_start_with_decorators(node)
            end = node_end(node)
            src = segment(lines, start, end)
            validate_target(node, src)
            found[node.name] = {"name": node.name, "start": start, "end": end, "source": src}
            route_meta[node.name] = decorator_info(node)

    missing = [name for name in TARGET_FUNCTIONS if name not in found]
    if missing:
        raise SystemExit(f"TARGET_FUNCTIONS_NOT_FOUND: {missing}")

    ranges = sorted([(v["start"], v["end"], k) for k, v in found.items()], key=lambda x: x[0])
    function_sources = [found[name]["source"] for name in TARGET_FUNCTIONS]
    new_module_text = make_new_module_text(function_sources)

    output_lines: list[str] = []
    current = 1
    for start, end, name in ranges:
        if current < start:
            output_lines.extend(lines[current - 1:start - 1])
        output_lines.append(f"# BYS360 P11-C1: {name} read-only performance route app/api/mobile/performance_read_routes.py modülüne taşındı.")
        current = end + 1

    if current <= len(lines):
        output_lines.extend(lines[current - 1:])

    new_routes_text = "\n".join(output_lines).rstrip() + "\n"
    new_routes_text = new_routes_text.rstrip() + "\n\n" + import_block() + "\n"

    print("BYS360_QUALITY_10_10_P11_C1_MOBILE_PERFORMANCE_READ_ROUTES_BRIDGE_START")
    print(f"project_root={project_root}")
    print(f"target_file={target}")
    for start, end, name in ranges:
        routes = []
        for info in route_meta.get(name, []):
            routes.append(f"{','.join(info['methods'])}:{info['route']}")
        print(f"MOVE_CANDIDATE {name} lines={start}-{end} count={end-start+1} routes={routes}")
    print(f"original_line_count={len(lines)}")
    print(f"new_routes_line_count={len(new_routes_text.splitlines())}")
    print(f"new_module_line_count={len(new_module_text.splitlines())}")

    if dry_run:
        print("BYS360_QUALITY_10_10_P11_C1_DRYRUN_OK")
        return

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = project_root / ".quality_backup" / f"p11_c1_mobile_performance_read_routes_bridge_{stamp}"

    for path in [target, new_module]:
        if path.exists():
            backup = backup_root / path.relative_to(project_root)
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup)

    write_text(new_module, new_module_text)
    write_text(target, new_routes_text)

    report = {
        "target_file": TARGET_REL,
        "new_module": NEW_MODULE_REL,
        "moved_functions": [
            {
                "name": name,
                "start": start,
                "end": end,
                "lines": end - start + 1,
                "routes": route_meta.get(name, []),
            }
            for start, end, name in ranges
        ],
        "blocked_functions": sorted(BLOCKED_FUNCTIONS),
        "original_line_count": len(lines),
        "new_routes_line_count": len(new_routes_text.splitlines()),
        "new_module_line_count": len(new_module_text.splitlines()),
        "backup_root": str(backup_root),
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_json = out_dir / "bys360_quality_10_10_p11_c1_mobile_performance_read_routes_bridge_v1.json"
    report_md = out_dir / "bys360_quality_10_10_p11_c1_mobile_performance_read_routes_bridge_v1.md"
    write_text(report_json, json.dumps(report, ensure_ascii=False, indent=2))

    md = []
    md.append("# BYS360 P11-C1 Mobile Performance Read Routes Bridge")
    md.append("")
    md.append(f"- Ana dosya: `{TARGET_REL}`")
    md.append(f"- Yeni modül: `{NEW_MODULE_REL}`")
    md.append(f"- Eski satır sayısı: {report['original_line_count']}")
    md.append(f"- Yeni performance_routes.py satır sayısı: {report['new_routes_line_count']}")
    md.append(f"- Yeni modül satır sayısı: {report['new_module_line_count']}")
    md.append(f"- Yedek: `{backup_root}`")
    md.append("")
    md.append("## Taşınan fonksiyonlar")
    md.append("")
    for item in report["moved_functions"]:
        md.append(f"- `{item['name']}` satır {item['start']}-{item['end']} ({item['lines']} satır)")
    md.append("")
    md.append("## Dokunulmayan kritik fonksiyonlar")
    md.append("")
    for name in sorted(BLOCKED_FUNCTIONS):
        md.append(f"- `{name}`")
    md.append("")
    md.append("## Güvenlik")
    md.append("")
    md.append("- Sadece GET/read performans endpointleri taşınmıştır.")
    md.append("- Puanlama, score submit, onay/yayın, POST ve commit/rollback işlemlerine dokunulmamıştır.")
    md.append("- Route kaynakları mevcut `performance_routes.py` global bağlamında register edilir; URL path ve JSON cevap davranışı korunur.")
    write_text(report_md, "\n".join(md) + "\n")

    print(f"backup_root={backup_root}")
    print(f"performance_read_routes_bridge_report_json={report_json}")
    print(f"performance_read_routes_bridge_report_md={report_md}")
    print("BYS360_QUALITY_10_10_P11_C1_MOBILE_PERFORMANCE_READ_ROUTES_BRIDGE_OK")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    apply(Path(args.project_root).resolve(), args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
