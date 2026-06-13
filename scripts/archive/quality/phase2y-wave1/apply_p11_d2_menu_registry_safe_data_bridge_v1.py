from __future__ import annotations

import argparse
import ast
import datetime as dt
import json
import shutil
from pathlib import Path
from typing import Any


TARGET_REL = "app/menu_registry.py"

PERFORMANCE_MODULE_REL = "app/menu_registry_data_performance.py"
PERSONNEL_MODULE_REL = "app/menu_registry_data_personnel.py"

PERFORMANCE_NAMES = [
    "ROLE_MENU_DEFAULTS",
    "_BYS360_PERFORMANCE_MAIN_SWITCH_ROLE_POLICY",
]

PERSONNEL_NAMES = [
    "_BYS360_PERSONEL_ROLE_MATRIX_CURRENT_DISALLOWED_KEYS",
    "_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_OBSOLETE_KEYS",
]

ALL_TARGET_NAMES = PERFORMANCE_NAMES + PERSONNEL_NAMES


class CallFinder(ast.NodeVisitor):
    def __init__(self) -> None:
        self.calls: list[str] = []

    def visit_Call(self, node: ast.Call) -> Any:
        self.calls.append(self._call_name(node.func))
        self.generic_visit(node)

    def _call_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return "<call>"


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


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def make_module_text(module_title: str, blocks: list[str]) -> str:
    header = [
        '"""BYS360 menu registry data bridge module.',
        "",
        f"{module_title}",
        "",
        "Bu dosya P11-D2 kapsamında app/menu_registry.py içindeki büyük ve güvenli",
        "top-level veri bloklarını aynı içerikle taşımak için oluşturulmuştur.",
        "menu_key değerleri ve veri içerikleri değiştirilmemelidir.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "",
    ]
    return "\n".join(header) + "\n\n".join(block.strip() for block in blocks) + "\n"


def import_block() -> str:
    return (
        "# BYS360 P11-D2: büyük güvenli menu registry veri blokları bridge import ile ayrıldı.\n"
        "from app.menu_registry_data_performance import (\n"
        "    ROLE_MENU_DEFAULTS,\n"
        "    _BYS360_PERFORMANCE_MAIN_SWITCH_ROLE_POLICY,\n"
        ")\n"
        "from app.menu_registry_data_personnel import (\n"
        "    _BYS360_PERSONEL_ROLE_MATRIX_CURRENT_DISALLOWED_KEYS,\n"
        "    _BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_OBSOLETE_KEYS,\n"
        ")\n"
    )


def apply(project_root: Path, dry_run: bool) -> None:
    target = project_root / TARGET_REL
    if not target.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target}")

    text = read_text(target)
    lines = text.splitlines()
    tree = ast.parse(text)

    found: dict[str, dict[str, Any]] = {}
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        names = assign_names(node)
        matched = [name for name in names if name in ALL_TARGET_NAMES]
        if not matched:
            continue

        start, end = node_lines(node)
        value = node.value if isinstance(node, (ast.Assign, ast.AnnAssign)) else None
        cf = CallFinder()
        if value is not None:
            cf.visit(value)

        if cf.calls:
            raise SystemExit(f"UNSAFE_CALL_IN_TARGET_ASSIGNMENT: {matched} calls={cf.calls}")

        for name in matched:
            found[name] = {
                "name": name,
                "start": start,
                "end": end,
                "source": segment(lines, start, end),
            }

    missing = [name for name in ALL_TARGET_NAMES if name not in found]
    if missing:
        # If already applied, menu_registry.py may only contain imports and data modules exist.
        perf_exists = (project_root / PERFORMANCE_MODULE_REL).exists()
        pers_exists = (project_root / PERSONNEL_MODULE_REL).exists()
        already_imported = "menu_registry_data_performance" in text and "menu_registry_data_personnel" in text
        if perf_exists and pers_exists and already_imported:
            print("BYS360_QUALITY_10_10_P11_D2_ALREADY_APPLIED")
            return
        raise SystemExit(f"TARGET_ASSIGNMENTS_NOT_FOUND: {missing}")

    perf_blocks = [found[name]["source"] for name in PERFORMANCE_NAMES]
    personnel_blocks = [found[name]["source"] for name in PERSONNEL_NAMES]

    ranges = sorted(
        [(int(found[name]["start"]), int(found[name]["end"]), name) for name in ALL_TARGET_NAMES],
        key=lambda x: x[0],
    )

    # Build new menu_registry.py preserving everything except target assignment blocks.
    remove_ranges = [(start, end) for start, end, _ in ranges]
    output_lines: list[str] = []
    inserted_import = False
    current_line = 1

    first_start = remove_ranges[0][0]
    for start, end, name in ranges:
        if current_line < start:
            output_lines.extend(lines[current_line - 1:start - 1])
        if not inserted_import:
            output_lines.append(import_block().rstrip("\n"))
            inserted_import = True
        else:
            output_lines.append(f"# BYS360 P11-D2: {name} veri bloğu data modülüne taşındı.")
        current_line = end + 1

    if current_line <= len(lines):
        output_lines.extend(lines[current_line - 1:])

    new_menu_text = "\n".join(output_lines).rstrip() + "\n"
    perf_text = make_module_text("Performans menü varsayılanları ve performans ana switch rol politikası.", perf_blocks)
    personnel_text = make_module_text("Personel rol matrisi görünürlük/temizlik sabitleri.", personnel_blocks)

    print("BYS360_QUALITY_10_10_P11_D2_MENU_REGISTRY_SAFE_DATA_BRIDGE_START")
    print(f"project_root={project_root}")
    print(f"target_file={target}")
    print(f"target_assignments={len(ALL_TARGET_NAMES)}")
    for start, end, name in ranges:
        print(f"MOVE_CANDIDATE {name} lines={start}-{end} count={end-start+1}")
    print(f"original_line_count={len(lines)}")
    print(f"new_menu_registry_line_count={len(new_menu_text.splitlines())}")
    print(f"performance_data_line_count={len(perf_text.splitlines())}")
    print(f"personnel_data_line_count={len(personnel_text.splitlines())}")

    if dry_run:
        print("BYS360_QUALITY_10_10_P11_D2_DRYRUN_OK")
        return

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = project_root / ".quality_backup" / f"p11_d2_menu_registry_safe_data_bridge_{stamp}"

    files_to_backup = [
        target,
        project_root / PERFORMANCE_MODULE_REL,
        project_root / PERSONNEL_MODULE_REL,
    ]
    for path in files_to_backup:
        if path.exists():
            backup = backup_root / path.relative_to(project_root)
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup)

    write_text(project_root / PERFORMANCE_MODULE_REL, perf_text)
    write_text(project_root / PERSONNEL_MODULE_REL, personnel_text)
    write_text(target, new_menu_text)

    report = {
        "target_file": TARGET_REL,
        "performance_module": PERFORMANCE_MODULE_REL,
        "personnel_module": PERSONNEL_MODULE_REL,
        "moved_assignments": [
            {"name": name, "start": start, "end": end, "lines": end - start + 1}
            for start, end, name in ranges
        ],
        "original_line_count": len(lines),
        "new_menu_registry_line_count": len(new_menu_text.splitlines()),
        "performance_data_line_count": len(perf_text.splitlines()),
        "personnel_data_line_count": len(personnel_text.splitlines()),
        "backup_root": str(backup_root),
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_json = out_dir / "bys360_quality_10_10_p11_d2_menu_registry_safe_data_bridge_v1.json"
    report_md = out_dir / "bys360_quality_10_10_p11_d2_menu_registry_safe_data_bridge_v1.md"
    write_text(report_json, json.dumps(report, ensure_ascii=False, indent=2))

    md = []
    md.append("# BYS360 P11-D2 Menu Registry Safe Data Bridge")
    md.append("")
    md.append(f"- Ana dosya: `{TARGET_REL}`")
    md.append(f"- Performans data modülü: `{PERFORMANCE_MODULE_REL}`")
    md.append(f"- Personel data modülü: `{PERSONNEL_MODULE_REL}`")
    md.append(f"- Eski menu_registry satır sayısı: {report['original_line_count']}")
    md.append(f"- Yeni menu_registry satır sayısı: {report['new_menu_registry_line_count']}")
    md.append(f"- Yedek: `{backup_root}`")
    md.append("")
    md.append("## Taşınan bloklar")
    md.append("")
    for item in report["moved_assignments"]:
        md.append(f"- `{item['name']}` satır {item['start']}-{item['end']} ({item['lines']} satır)")
    md.append("")
    md.append("## Güvenlik")
    md.append("")
    md.append("- `MENU_SECTIONS` bu pakette taşınmamıştır.")
    md.append("- `menu_key` değerleri ve veri içerikleri değiştirilmemiştir.")
    md.append("- `menu_registry.py` içinde aynı public değişken adları import bridge ile korunur.")
    write_text(report_md, "\n".join(md) + "\n")

    print(f"backup_root={backup_root}")
    print(f"safe_data_bridge_report_json={report_json}")
    print(f"safe_data_bridge_report_md={report_md}")
    print("BYS360_QUALITY_10_10_P11_D2_MENU_REGISTRY_SAFE_DATA_BRIDGE_OK")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    apply(Path(args.project_root).resolve(), args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
