from __future__ import annotations

import argparse
import ast
import datetime as dt
import json
import shutil
from pathlib import Path
from typing import Any


TARGET_REL = "app/api/mobile/routes.py"
NEW_MODULE_REL = "app/api/mobile/support_survey_read_routes.py"

TARGET_FUNCTIONS = [
    "mobile_support_tickets",
    "mobile_surveys",
]

IMPORT_SENTINEL = "# BYS360 P11-B5: support/survey read mobile routes bridge"
CALL_LINE = "_register_mobile_support_survey_read_routes_v1(mobile_bp, globals())"


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


def decorator_names(node: ast.AST) -> list[str]:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return []
    names = []
    for dec in node.decorator_list:
        func = dec.func if isinstance(dec, ast.Call) else dec
        if isinstance(func, ast.Attribute):
            names.append(func.attr)
        elif isinstance(func, ast.Name):
            names.append(func.id)
    return names


def validate_target(node: ast.AST, source: str) -> None:
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        raise SystemExit("TARGET_IS_NOT_FUNCTION")

    names = decorator_names(node)
    if not any(name in {"get", "route"} for name in names):
        raise SystemExit(f"TARGET_NOT_SAFE_GET_ROUTE: {node.name} decorators={names}")

    lowered = source.lower()
    risky = [
        "commit(",
        "rollback(",
        "set_password",
        "password",
        "db.session.add",
        "db.session.delete",
        "delete(",
        ".delete(",
        "jwt",
        "token",
        "request.json",
        "request.form",
    ]
    hits = [h for h in risky if h in lowered]
    if hits:
        raise SystemExit(f"TARGET_HAS_WRITE_OR_AUTH_RISK: {node.name} hits={hits}")


def make_new_module_text(function_sources: list[str]) -> str:
    source_blob = "\n\n".join(src.rstrip() for src in function_sources) + "\n"
    parts = [
        "# BYS360 mobile support/survey read route bridge module.",
        "# P11-B5 kapsamında destek ve anket GET listeleme endpointleri ayrılmıştır.",
        "# URL path ve JSON cevap davranışı değiştirilmemelidir.",
        "",
        "from __future__ import annotations",
        "",
        "_SUPPORT_SURVEY_READ_ROUTE_SOURCE = " + repr(source_blob),
        "",
        "",
        "def register_mobile_support_survey_read_routes_v1(mobile_bp, route_globals: dict) -> None:",
        "    \"\"\"Register support/survey read mobile routes on the existing mobile blueprint.\"\"\"",
        "    if route_globals.get(\"_BYS360_P11_B5_SUPPORT_SURVEY_READ_ROUTES_REGISTERED\"):",
        "        return",
        "",
        "    route_globals[\"mobile_bp\"] = mobile_bp",
        "    exec(_SUPPORT_SURVEY_READ_ROUTE_SOURCE, route_globals, route_globals)",
        "    route_globals[\"_BYS360_P11_B5_SUPPORT_SURVEY_READ_ROUTES_REGISTERED\"] = True",
        "",
    ]
    return "\n".join(parts)


def import_block() -> str:
    return (
        f"{IMPORT_SENTINEL}\n"
        "from app.api.mobile.support_survey_read_routes import register_mobile_support_survey_read_routes_v1 as _register_mobile_support_survey_read_routes_v1\n"
        f"{CALL_LINE}\n"
    )


def apply(project_root: Path, dry_run: bool) -> None:
    target = project_root / TARGET_REL
    new_module = project_root / NEW_MODULE_REL

    if not target.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target}")

    text = read_text(target)
    if IMPORT_SENTINEL in text and new_module.exists():
        print("BYS360_QUALITY_10_10_P11_B5_ALREADY_APPLIED")
        return

    lines = text.splitlines()
    tree = ast.parse(text)

    found: dict[str, dict[str, Any]] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in TARGET_FUNCTIONS:
            start = node_start_with_decorators(node)
            end = node_end(node)
            src = segment(lines, start, end)
            validate_target(node, src)
            found[node.name] = {"name": node.name, "start": start, "end": end, "source": src}

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
        output_lines.append(f"# BYS360 P11-B5: {name} support/survey read route app/api/mobile/support_survey_read_routes.py modülüne taşındı.")
        current = end + 1
    if current <= len(lines):
        output_lines.extend(lines[current - 1:])

    new_routes_text = "\n".join(output_lines).rstrip() + "\n"
    new_routes_text = new_routes_text.rstrip() + "\n\n" + import_block() + "\n"

    print("BYS360_QUALITY_10_10_P11_B5_MOBILE_SUPPORT_SURVEY_READ_ROUTES_BRIDGE_START")
    print(f"project_root={project_root}")
    print(f"target_file={target}")
    for start, end, name in ranges:
        print(f"MOVE_CANDIDATE {name} lines={start}-{end} count={end-start+1}")
    print(f"original_line_count={len(lines)}")
    print(f"new_routes_line_count={len(new_routes_text.splitlines())}")
    print(f"new_module_line_count={len(new_module_text.splitlines())}")

    if dry_run:
        print("BYS360_QUALITY_10_10_P11_B5_DRYRUN_OK")
        return

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = project_root / ".quality_backup" / f"p11_b5_mobile_support_survey_read_routes_bridge_{stamp}"

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
            {"name": name, "start": start, "end": end, "lines": end - start + 1}
            for start, end, name in ranges
        ],
        "original_line_count": len(lines),
        "new_routes_line_count": len(new_routes_text.splitlines()),
        "new_module_line_count": len(new_module_text.splitlines()),
        "backup_root": str(backup_root),
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_json = out_dir / "bys360_quality_10_10_p11_b5_mobile_support_survey_read_routes_bridge_v1.json"
    report_md = out_dir / "bys360_quality_10_10_p11_b5_mobile_support_survey_read_routes_bridge_v1.md"
    write_text(report_json, json.dumps(report, ensure_ascii=False, indent=2))

    md = []
    md.append("# BYS360 P11-B5 Mobile Support/Survey Read Routes Bridge")
    md.append("")
    md.append(f"- Ana dosya: `{TARGET_REL}`")
    md.append(f"- Yeni modül: `{NEW_MODULE_REL}`")
    md.append(f"- Eski satır sayısı: {report['original_line_count']}")
    md.append(f"- Yeni routes.py satır sayısı: {report['new_routes_line_count']}")
    md.append(f"- Yeni modül satır sayısı: {report['new_module_line_count']}")
    md.append(f"- Yedek: `{backup_root}`")
    md.append("")
    md.append("## Taşınan fonksiyonlar")
    md.append("")
    for item in report["moved_functions"]:
        md.append(f"- `{item['name']}` satır {item['start']}-{item['end']} ({item['lines']} satır)")
    md.append("")
    md.append("## Güvenlik")
    md.append("")
    md.append("- Sadece GET destek/anket listeleme endpointleri taşınmıştır.")
    md.append("- Auth, token, personel oluşturma, password, commit/rollback ve POST endpointlere dokunulmamıştır.")
    md.append("- Route kaynakları mevcut `routes.py` global bağlamında register edilir; URL path ve JSON cevap davranışı korunur.")
    write_text(report_md, "\n".join(md) + "\n")

    print(f"backup_root={backup_root}")
    print(f"support_survey_read_routes_bridge_report_json={report_json}")
    print(f"support_survey_read_routes_bridge_report_md={report_md}")
    print("BYS360_QUALITY_10_10_P11_B5_MOBILE_SUPPORT_SURVEY_READ_ROUTES_BRIDGE_OK")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    apply(Path(args.project_root).resolve(), args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
