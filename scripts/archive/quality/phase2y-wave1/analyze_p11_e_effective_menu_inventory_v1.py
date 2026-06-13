from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter
from pathlib import Path


TARGET_REL = "app/services/settings/effective_menu.py"


DOMAIN_HINTS = {
    "db_repository": ["query", "filter", "db.", "session", "execute", "commit", "rollback", "UserMenu", "Permission", "Role"],
    "policy": ["visible", "visibility", "allowed", "can_", "permission", "role", "admin", "başkan", "baskan", "authorized"],
    "calculator": ["build", "map", "effective", "merge", "resolve", "fallback", "normalize", "compute", "calculate"],
    "menu_registry": ["menu_registry", "menu_key", "registry", "sidebar", "module", "section"],
    "logging": ["logger", "log.", "warning", "error", "exception"],
    "compatibility": ["legacy", "fallback", "backward", "safe", "guard"],
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def safe_ast(text: str) -> ast.Module | None:
    try:
        return ast.parse(text)
    except SyntaxError:
        return None


def node_lines(node: ast.AST) -> tuple[int, int, int]:
    start = getattr(node, "lineno", 0) or 0
    end = getattr(node, "end_lineno", start) or start
    return start, end, max(0, end - start + 1)


def classify_function(name: str, source: str) -> str:
    low = (name + "\n" + source).lower()
    scores = Counter()
    for kind, hints in DOMAIN_HINTS.items():
        for hint in hints:
            if hint.lower() in low:
                scores[kind] += 1
    if not scores:
        return "general"
    return scores.most_common(1)[0][0]


def get_source_segment(lines: list[str], start: int, end: int) -> str:
    if start <= 0 or end <= 0:
        return ""
    return "\n".join(lines[start - 1:end])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--limit", type=int, default=160)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    target = project_root / TARGET_REL

    print("BYS360_QUALITY_10_10_P11_E_EFFECTIVE_MENU_INVENTORY_START")
    print(f"project_root={project_root}")
    print(f"target_file={target}")

    if not target.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target}")

    text = read_text(target)
    lines = text.splitlines()
    tree = safe_ast(text)
    if tree is None:
        raise SystemExit("AST_PARSE_FAILED")

    imports = []
    functions = []
    classes = []
    constants = []

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            start, end, count = node_lines(node)
            imports.append({"line": start, "source": get_source_segment(lines, start, end)})
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start, end, count = node_lines(node)
            source = get_source_segment(lines, start, end)
            functions.append({
                "name": node.name,
                "start": start,
                "end": end,
                "lines": count,
                "args": [a.arg for a in node.args.args],
                "kind": classify_function(node.name, source),
                "decorators": [ast.unparse(d) if hasattr(ast, "unparse") else "" for d in node.decorator_list],
            })
        elif isinstance(node, ast.ClassDef):
            start, end, count = node_lines(node)
            classes.append({"name": node.name, "start": start, "end": end, "lines": count})
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            start, end, count = node_lines(node)
            constants.append({"line": start, "source": get_source_segment(lines, start, end)[:180]})

    function_kind_summary = Counter(f["kind"] for f in functions)
    large_functions = [f for f in functions if f["lines"] >= 80]
    risky_lines = []
    for i, line in enumerate(lines, start=1):
        low = line.lower()
        if any(h in low for h in ["db.session", ".query", "current_user", "request.", "session[", "commit(", "rollback("]):
            risky_lines.append({"line": i, "content": line.strip()})

    proposed_modules = {
        "effective_menu_repository.py": ["db_repository"],
        "effective_menu_policy.py": ["policy"],
        "effective_menu_calculator.py": ["calculator", "menu_registry", "compatibility"],
        "effective_menu_logging.py": ["logging"],
    }

    report = {
        "target_file": TARGET_REL,
        "line_count": len(lines),
        "import_count": len(imports),
        "class_count": len(classes),
        "function_count": len(functions),
        "constant_like_count": len(constants),
        "function_kind_summary": dict(function_kind_summary.most_common()),
        "large_functions": large_functions,
        "functions": functions,
        "classes": classes,
        "imports_sample": imports[:80],
        "risky_db_or_request_lines": risky_lines[:120],
        "proposed_modules": proposed_modules,
        "safety_strategy": [
            "İlk aşamada kod taşınmayacak; yalnızca fonksiyon/domain haritası çıkarılacak.",
            "Veritabanı erişimi yapan fonksiyonlar repository modülüne en son taşınmalı.",
            "Menü görünürlüğü ve kişi bazlı yetki hesapları önce saf calculator/policy fonksiyonlarına ayrılmalı.",
            "menu_key değerleri ve dışarıdan import edilen fonksiyon adları korunmalı.",
            "Her gerçek refactor sonrası Ayarlar, Rol Matrisi, kişi bazlı menü görünürlüğü ve yetkisiz menü gizleme smoke test edilmeli.",
        ],
        "next_step": "P11-E1: sadece saf yardımcı hesaplama fonksiyonları için taşıma aday listesi; kod değiştirmeden dependency graph çıkarma.",
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / "bys360_quality_10_10_p11_e_effective_menu_inventory_v1.json"
    md_out = out_dir / "bys360_quality_10_10_p11_e_effective_menu_inventory_v1.md"
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# BYS360 P11-E Effective Menu Envanteri")
    md.append("")
    md.append(f"- Dosya: `{TARGET_REL}`")
    md.append(f"- Satır sayısı: {len(lines)}")
    md.append(f"- Import sayısı: {len(imports)}")
    md.append(f"- Class sayısı: {len(classes)}")
    md.append(f"- Fonksiyon sayısı: {len(functions)}")
    md.append("")
    md.append("## Fonksiyon Tür Dağılımı")
    md.append("")
    for key, count in function_kind_summary.most_common():
        md.append(f"- {key}: {count}")
    md.append("")
    md.append("## Büyük Fonksiyonlar")
    md.append("")
    if large_functions:
        for f in large_functions:
            md.append(f"- `{f['name']}` satır {f['start']}-{f['end']} ({f['lines']} satır) — {f['kind']}")
    else:
        md.append("- 80 satır üstü fonksiyon bulunmadı.")
    md.append("")
    md.append("## Önerilen Modül Ayrımı")
    md.append("")
    for mod, kinds in proposed_modules.items():
        md.append(f"- `{mod}`: {', '.join(kinds)}")
    md.append("")
    md.append("## Güvenlik Stratejisi")
    md.append("")
    for item in report["safety_strategy"]:
        md.append(f"- {item}")
    md.append("")
    md.append("## İlk Fonksiyonlar")
    md.append("")
    for f in functions[:60]:
        md.append(f"- `{f['name']}` satır {f['start']}-{f['end']} ({f['lines']} satır) — {f['kind']}")
    md_out.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"line_count={len(lines)}")
    print(f"import_count={len(imports)}")
    print(f"class_count={len(classes)}")
    print(f"function_count={len(functions)}")
    print(f"large_function_count={len(large_functions)}")
    print(f"risky_db_or_request_line_count={len(risky_lines)}")
    print("BYS360_QUALITY_10_10_P11_E_FUNCTION_KIND_SUMMARY")
    for key, count in function_kind_summary.most_common():
        print(f"{count:>4} | {key}")
    print("BYS360_QUALITY_10_10_P11_E_LARGE_FUNCTIONS")
    for f in large_functions[:args.limit]:
        print(f"{f['lines']:>4} | {f['kind']} | {f['start']}-{f['end']} | {f['name']}")
    print(f"effective_menu_inventory_json={json_out}")
    print(f"effective_menu_inventory_md={md_out}")
    print("BYS360_QUALITY_10_10_P11_E_EFFECTIVE_MENU_INVENTORY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
