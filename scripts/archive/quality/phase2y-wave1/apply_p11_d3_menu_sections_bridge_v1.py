from __future__ import annotations

import argparse
import ast
import datetime as dt
import json
import shutil
from pathlib import Path
from typing import Any


TARGET_REL = "app/menu_registry.py"
DATA_MODULE_REL = "app/menu_registry_data_sections.py"

PRIMARY_NAMES = ["ANNOUNCEMENT_TOOL_ROLES", "MENU_SECTIONS"]
ALLOWED_CALLS = {"sorted", "list", "tuple", "set", "dict"}
ALLOWED_LOAD_NAMES = {"True", "False", "None", "sorted", "list", "tuple", "set", "dict", "ANNOUNCEMENT_TOOL_ROLES"}


class ExprVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.calls: set[str] = set()
        self.load_names: set[str] = set()
        self.comprehension_targets: set[str] = set()

    def visit_Call(self, node: ast.Call) -> Any:
        name = self._call_name(node.func)
        if name:
            self.calls.add(name)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> Any:
        if isinstance(node.ctx, ast.Load):
            self.load_names.add(node.id)
        elif isinstance(node.ctx, ast.Store):
            self.comprehension_targets.add(node.id)
        self.generic_visit(node)

    def visit_comprehension(self, node: ast.comprehension) -> Any:
        for name in self._target_names(node.target):
            self.comprehension_targets.add(name)
        self.generic_visit(node)

    def _target_names(self, node: ast.AST) -> list[str]:
        if isinstance(node, ast.Name):
            return [node.id]
        if isinstance(node, (ast.Tuple, ast.List)):
            out: list[str] = []
            for item in node.elts:
                out.extend(self._target_names(item))
            return out
        return []

    def _call_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return "<call>"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def target_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, (ast.Tuple, ast.List)):
        out: list[str] = []
        for item in node.elts:
            out.extend(target_names(item))
        return out
    return []


def assign_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Assign):
        out: list[str] = []
        for t in node.targets:
            out.extend(target_names(t))
        return out
    if isinstance(node, ast.AnnAssign):
        return target_names(node.target)
    return []


def node_lines(node: ast.AST) -> tuple[int, int]:
    start = getattr(node, "lineno", 0) or 0
    end = getattr(node, "end_lineno", start) or start
    return start, end


def segment(lines: list[str], start: int, end: int) -> str:
    return "\n".join(lines[start - 1:end]).rstrip() + "\n"


def find_assignments(tree: ast.Module, lines: list[str]) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue

        names = assign_names(node)
        matched = [n for n in names if n in PRIMARY_NAMES]
        if not matched:
            continue

        start, end = node_lines(node)
        value = node.value if isinstance(node, (ast.Assign, ast.AnnAssign)) else None
        ev = ExprVisitor()
        if value is not None:
            ev.visit(value)

        for name in matched:
            found[name] = {
                "name": name,
                "start": start,
                "end": end,
                "source": segment(lines, start, end),
                "calls": sorted(ev.calls),
                "load_names": sorted(ev.load_names),
                "comprehension_targets": sorted(ev.comprehension_targets),
            }
    return found


def validate(found: dict[str, dict[str, Any]]) -> None:
    missing = [name for name in PRIMARY_NAMES if name not in found]
    if missing:
        raise SystemExit(f"TARGET_ASSIGNMENTS_NOT_FOUND: {missing}")

    announcement = found["ANNOUNCEMENT_TOOL_ROLES"]
    menu = found["MENU_SECTIONS"]

    # ANNOUNCEMENT_TOOL_ROLES should be a simple constant/list/set/tuple/dict style block.
    ann_calls = set(announcement["calls"])
    if ann_calls - ALLOWED_CALLS:
        raise SystemExit(f"UNSAFE_CALLS_IN_ANNOUNCEMENT_TOOL_ROLES: {sorted(ann_calls)}")

    menu_calls = set(menu["calls"])
    if menu_calls - ALLOWED_CALLS:
        raise SystemExit(f"UNSAFE_CALLS_IN_MENU_SECTIONS: {sorted(menu_calls)}")

    menu_loads = set(menu["load_names"]) - set(menu["comprehension_targets"])
    unsafe_loads = menu_loads - ALLOWED_LOAD_NAMES
    if unsafe_loads:
        raise SystemExit(f"UNSAFE_LOAD_NAMES_IN_MENU_SECTIONS: {sorted(unsafe_loads)}")

    if "ANNOUNCEMENT_TOOL_ROLES" not in menu_loads:
        raise SystemExit("EXPECTED_DEPENDENCY_NOT_FOUND: MENU_SECTIONS should depend on ANNOUNCEMENT_TOOL_ROLES")


def data_module_text(blocks: list[str]) -> str:
    header = [
        '"""BYS360 menu registry section data bridge module.',
        "",
        "P11-D3 kapsamında `app/menu_registry.py` içindeki `MENU_SECTIONS`",
        "ve ona bağlı `ANNOUNCEMENT_TOOL_ROLES` veri blokları bu modüle taşınmıştır.",
        "",
        "menu_key değerleri, sıralama mantığı ve veri içeriği değiştirilmemelidir.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "",
    ]
    return "\n".join(header) + "\n\n".join(block.strip() for block in blocks) + "\n"


def import_block() -> str:
    return (
        "# BYS360 P11-D3: menü section veri blokları bridge import ile ayrıldı.\n"
        "from app.menu_registry_data_sections import (\n"
        "    ANNOUNCEMENT_TOOL_ROLES,\n"
        "    MENU_SECTIONS,\n"
        ")\n"
    )


def apply(project_root: Path, dry_run: bool) -> None:
    target = project_root / TARGET_REL
    data_module = project_root / DATA_MODULE_REL

    if not target.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target}")

    text = read_text(target)
    tree = ast.parse(text)
    lines = text.splitlines()

    if "menu_registry_data_sections" in text and data_module.exists():
        print("BYS360_QUALITY_10_10_P11_D3_ALREADY_APPLIED")
        return

    found = find_assignments(tree, lines)
    validate(found)

    ranges = sorted(
        [(int(found[name]["start"]), int(found[name]["end"]), name) for name in PRIMARY_NAMES],
        key=lambda item: item[0],
    )

    blocks = [found[name]["source"] for name in PRIMARY_NAMES]

    output_lines: list[str] = []
    inserted_import = False
    current_line = 1

    for start, end, name in ranges:
        if current_line < start:
            output_lines.extend(lines[current_line - 1:start - 1])
        if not inserted_import:
            output_lines.append(import_block().rstrip("\n"))
            inserted_import = True
        else:
            output_lines.append(f"# BYS360 P11-D3: {name} veri bloğu data modülüne taşındı.")
        current_line = end + 1

    if current_line <= len(lines):
        output_lines.extend(lines[current_line - 1:])

    new_menu_text = "\n".join(output_lines).rstrip() + "\n"
    new_data_text = data_module_text(blocks)

    print("BYS360_QUALITY_10_10_P11_D3_MENU_SECTIONS_BRIDGE_START")
    print(f"project_root={project_root}")
    print(f"target_file={target}")
    for start, end, name in ranges:
        info = found[name]
        print(f"MOVE_CANDIDATE {name} lines={start}-{end} count={end-start+1} calls={info['calls']}")
    print(f"original_line_count={len(lines)}")
    print(f"new_menu_registry_line_count={len(new_menu_text.splitlines())}")
    print(f"sections_data_line_count={len(new_data_text.splitlines())}")

    if dry_run:
        print("BYS360_QUALITY_10_10_P11_D3_DRYRUN_OK")
        return

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = project_root / ".quality_backup" / f"p11_d3_menu_sections_bridge_{stamp}"

    for path in [target, data_module]:
        if path.exists():
            backup = backup_root / path.relative_to(project_root)
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup)

    write_text(data_module, new_data_text)
    write_text(target, new_menu_text)

    report = {
        "target_file": TARGET_REL,
        "data_module": DATA_MODULE_REL,
        "moved_assignments": [
            {"name": name, "start": start, "end": end, "lines": end - start + 1, "calls": found[name]["calls"]}
            for start, end, name in ranges
        ],
        "original_line_count": len(lines),
        "new_menu_registry_line_count": len(new_menu_text.splitlines()),
        "sections_data_line_count": len(new_data_text.splitlines()),
        "backup_root": str(backup_root),
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_json = out_dir / "bys360_quality_10_10_p11_d3_menu_sections_bridge_v1.json"
    report_md = out_dir / "bys360_quality_10_10_p11_d3_menu_sections_bridge_v1.md"

    write_text(report_json, json.dumps(report, ensure_ascii=False, indent=2))

    md = []
    md.append("# BYS360 P11-D3 Menu Sections Bridge")
    md.append("")
    md.append(f"- Ana dosya: `{TARGET_REL}`")
    md.append(f"- Data modülü: `{DATA_MODULE_REL}`")
    md.append(f"- Eski menu_registry satır sayısı: {report['original_line_count']}")
    md.append(f"- Yeni menu_registry satır sayısı: {report['new_menu_registry_line_count']}")
    md.append(f"- Data modülü satır sayısı: {report['sections_data_line_count']}")
    md.append(f"- Yedek: `{backup_root}`")
    md.append("")
    md.append("## Taşınan bloklar")
    md.append("")
    for item in report["moved_assignments"]:
        md.append(f"- `{item['name']}` satır {item['start']}-{item['end']} ({item['lines']} satır), calls={item['calls']}")
    md.append("")
    md.append("## Güvenlik")
    md.append("")
    md.append("- `MENU_SECTIONS` yalnızca izin verilen `sorted/list/tuple/set/dict` çağrılarını içerirse taşınır.")
    md.append("- `MENU_SECTIONS` için beklenen tek yerel bağımlılık `ANNOUNCEMENT_TOOL_ROLES` olmalıdır.")
    md.append("- Public değişken adları `menu_registry.py` içinde import bridge ile korunur.")
    write_text(report_md, "\n".join(md) + "\n")

    print(f"backup_root={backup_root}")
    print(f"menu_sections_bridge_report_json={report_json}")
    print(f"menu_sections_bridge_report_md={report_md}")
    print("BYS360_QUALITY_10_10_P11_D3_MENU_SECTIONS_BRIDGE_OK")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    apply(Path(args.project_root).resolve(), args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
