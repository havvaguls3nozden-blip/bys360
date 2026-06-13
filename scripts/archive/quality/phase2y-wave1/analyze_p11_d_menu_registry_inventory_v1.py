from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


TARGET_REL = "app/menu_registry.py"


DOMAIN_HINTS = {
    "performance": ["performance", "performans", "score", "kpi", "period", "evaluation", "degerlendirme"],
    "settings": ["settings", "ayar", "role", "permission", "yetki", "matrix", "menu_visibility"],
    "ai": ["ai", "assistant", "asistan", "decision", "karar"],
    "support": ["support", "destek", "ticket", "talep"],
    "communication": ["communication", "iletişim", "survey", "anket", "message"],
    "personnel": ["personnel", "personel", "hr", "attendance", "izin"],
    "dashboard": ["dashboard", "home", "kontrol", "panel"],
    "mobile": ["mobile", "pwa", "ios", "android"],
}


def node_lines(node: ast.AST) -> tuple[int, int, int]:
    start = getattr(node, "lineno", 0) or 0
    end = getattr(node, "end_lineno", start) or start
    return start, end, max(0, end - start + 1)


def segment(lines: list[str], start: int, end: int) -> str:
    if start <= 0 or end <= 0:
        return ""
    return "\n".join(lines[start - 1:end])


def literal_size(node: ast.AST) -> int:
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return len(node.elts)
    if isinstance(node, ast.Dict):
        return len(node.keys)
    return 0


def assign_names(node: ast.AST) -> list[str]:
    out: list[str] = []
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name):
                out.append(t.id)
            elif isinstance(t, (ast.Tuple, ast.List)):
                out.extend(e.id for e in t.elts if isinstance(e, ast.Name))
    elif isinstance(node, ast.AnnAssign):
        if isinstance(node.target, ast.Name):
            out.append(node.target.id)
    return out


def classify_text(name: str, text: str) -> str:
    low = (name + "\n" + text).lower()
    scores = Counter()
    for domain, hints in DOMAIN_HINTS.items():
        for hint in hints:
            if hint.lower() in low:
                scores[domain] += 1
    if not scores:
        return "core_or_general"
    return scores.most_common(1)[0][0]


def find_menu_key_like_strings(text: str) -> list[str]:
    # Heuristic: captures common menu_key values and string keys without trying to execute code.
    values = set()
    patterns = [
        r"menu_key\s*[=:]\s*['\"]([^'\"]+)['\"]",
        r"key\s*[=:]\s*['\"]([^'\"]+)['\"]",
        r"['\"]menu_key['\"]\s*:\s*['\"]([^'\"]+)['\"]",
        r"['\"]key['\"]\s*:\s*['\"]([^'\"]+)['\"]",
    ]
    for pat in patterns:
        for m in re.finditer(pat, text):
            val = m.group(1).strip()
            if val and len(val) <= 90:
                values.add(val)
    return sorted(values)


def analyze_assignment(node: ast.AST, lines: list[str]) -> dict[str, Any] | None:
    names = assign_names(node)
    if not names:
        return None
    start, end, count = node_lines(node)
    src = segment(lines, start, end)
    val = None
    if isinstance(node, ast.Assign):
        val = node.value
    elif isinstance(node, ast.AnnAssign):
        val = node.value
    size = literal_size(val) if val is not None else 0
    return {
        "names": names,
        "start": start,
        "end": end,
        "lines": count,
        "literal_size": size,
        "domain": classify_text(" ".join(names), src),
        "preview": src[:240].replace("\n", " "),
    }


def analyze_function(node: ast.AST, lines: list[str]) -> dict[str, Any]:
    start, end, count = node_lines(node)
    src = segment(lines, start, end)
    calls = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Call):
            func = sub.func
            if isinstance(func, ast.Name):
                calls.append(func.id)
            elif isinstance(func, ast.Attribute):
                calls.append(func.attr)
    return {
        "name": getattr(node, "name", ""),
        "start": start,
        "end": end,
        "lines": count,
        "domain": classify_text(getattr(node, "name", ""), src),
        "call_sample": sorted(set(calls))[:60],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--limit", type=int, default=160)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    target = project_root / TARGET_REL

    print("BYS360_QUALITY_10_10_P11_D_MENU_REGISTRY_INVENTORY_START")
    print(f"project_root={project_root}")
    print(f"target_file={target}")

    if not target.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target}")

    text = target.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    tree = ast.parse(text)

    imports = []
    assignments = []
    functions = []
    classes = []

    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            start, end, count = node_lines(node)
            imports.append({"start": start, "end": end, "lines": count, "source": segment(lines, start, end)})
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            a = analyze_assignment(node, lines)
            if a:
                assignments.append(a)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(analyze_function(node, lines))
        elif isinstance(node, ast.ClassDef):
            start, end, count = node_lines(node)
            classes.append({"name": node.name, "start": start, "end": end, "lines": count})

    large_assignments = [a for a in assignments if a["lines"] >= 80 or a["literal_size"] >= 20]
    large_functions = [f for f in functions if f["lines"] >= 80]
    menu_keys = find_menu_key_like_strings(text)

    assignment_domain_summary = Counter(a["domain"] for a in assignments)
    function_domain_summary = Counter(f["domain"] for f in functions)

    proposed_modules = {
        "menu_registry_core.py": ["core_or_general", "dashboard"],
        "menu_registry_performance.py": ["performance"],
        "menu_registry_settings.py": ["settings"],
        "menu_registry_ai.py": ["ai"],
        "menu_registry_support.py": ["support", "communication"],
        "menu_registry_personnel.py": ["personnel"],
        "menu_registry_mobile.py": ["mobile"],
    }

    report = {
        "target_file": TARGET_REL,
        "line_count": len(lines),
        "import_count": len(imports),
        "class_count": len(classes),
        "assignment_count": len(assignments),
        "function_count": len(functions),
        "large_assignment_count": len(large_assignments),
        "large_function_count": len(large_functions),
        "menu_key_like_count": len(menu_keys),
        "menu_key_like_sample": menu_keys[:160],
        "assignment_domain_summary": dict(assignment_domain_summary.most_common()),
        "function_domain_summary": dict(function_domain_summary.most_common()),
        "large_assignments": large_assignments,
        "large_functions": large_functions,
        "functions": functions,
        "classes": classes,
        "proposed_modules": proposed_modules,
        "safety_strategy": [
            "İlk aşamada menu_registry.py kodu değiştirilmez; kayıt defteri domain haritası çıkarılır.",
            "menu_key değerleri kesinlikle değişmemelidir.",
            "Dışarıdan import edilen fonksiyon adları korunmalıdır.",
            "İlk gerçek refactor, veri sabitlerini domain dosyalarına taşıyıp eski dosyada aynı public API ile bridge bırakmalıdır.",
            "Performans, ayarlar ve kişi bazlı görünürlük menüleri için smoke test yapılmadan ilerlenmemelidir.",
        ],
        "next_step": "P11-D1: büyük veri sabiti veya domain bloklarını güvenli bridge ile taşıma adayları; kod değiştirmeden dependency/call graph.",
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / "bys360_quality_10_10_p11_d_menu_registry_inventory_v1.json"
    md_out = out_dir / "bys360_quality_10_10_p11_d_menu_registry_inventory_v1.md"
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# BYS360 P11-D Menu Registry Envanteri")
    md.append("")
    md.append(f"- Dosya: `{TARGET_REL}`")
    md.append(f"- Satır sayısı: {len(lines)}")
    md.append(f"- Import sayısı: {len(imports)}")
    md.append(f"- Assignment/sabit blok sayısı: {len(assignments)}")
    md.append(f"- Fonksiyon sayısı: {len(functions)}")
    md.append(f"- Büyük sabit blok sayısı: {len(large_assignments)}")
    md.append(f"- Büyük fonksiyon sayısı: {len(large_functions)}")
    md.append(f"- menu_key benzeri değer sayısı: {len(menu_keys)}")
    md.append("")
    md.append("## Assignment Domain Dağılımı")
    md.append("")
    for k, v in assignment_domain_summary.most_common():
        md.append(f"- {k}: {v}")
    md.append("")
    md.append("## Fonksiyon Domain Dağılımı")
    md.append("")
    for k, v in function_domain_summary.most_common():
        md.append(f"- {k}: {v}")
    md.append("")
    md.append("## Büyük Sabit/Veri Blokları")
    md.append("")
    if large_assignments:
        for a in large_assignments[:80]:
            md.append(f"- `{', '.join(a['names'])}` satır {a['start']}-{a['end']} ({a['lines']} satır), domain={a['domain']}, size={a['literal_size']}")
    else:
        md.append("- Büyük sabit/veri bloğu bulunmadı.")
    md.append("")
    md.append("## Büyük Fonksiyonlar")
    md.append("")
    if large_functions:
        for f in large_functions:
            md.append(f"- `{f['name']}` satır {f['start']}-{f['end']} ({f['lines']} satır), domain={f['domain']}")
    else:
        md.append("- 80 satır üstü fonksiyon bulunmadı.")
    md.append("")
    md.append("## Önerilen Modül Ayrımı")
    md.append("")
    for mod, domains in proposed_modules.items():
        md.append(f"- `{mod}`: {', '.join(domains)}")
    md.append("")
    md.append("## Güvenlik Stratejisi")
    md.append("")
    for item in report["safety_strategy"]:
        md.append(f"- {item}")
    md_out.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"line_count={len(lines)}")
    print(f"import_count={len(imports)}")
    print(f"class_count={len(classes)}")
    print(f"assignment_count={len(assignments)}")
    print(f"function_count={len(functions)}")
    print(f"large_assignment_count={len(large_assignments)}")
    print(f"large_function_count={len(large_functions)}")
    print(f"menu_key_like_count={len(menu_keys)}")
    print("BYS360_QUALITY_10_10_P11_D_ASSIGNMENT_DOMAIN_SUMMARY")
    for k, v in assignment_domain_summary.most_common():
        print(f"{v:>4} | {k}")
    print("BYS360_QUALITY_10_10_P11_D_FUNCTION_DOMAIN_SUMMARY")
    for k, v in function_domain_summary.most_common():
        print(f"{v:>4} | {k}")
    print("BYS360_QUALITY_10_10_P11_D_LARGE_ASSIGNMENTS")
    for a in large_assignments[:args.limit]:
        print(f"{a['lines']:>4} | size={a['literal_size']:>4} | {a['domain']} | {a['start']}-{a['end']} | {', '.join(a['names'])}")
    print("BYS360_QUALITY_10_10_P11_D_LARGE_FUNCTIONS")
    for f in large_functions[:args.limit]:
        print(f"{f['lines']:>4} | {f['domain']} | {f['start']}-{f['end']} | {f['name']}")
    print(f"menu_registry_inventory_json={json_out}")
    print(f"menu_registry_inventory_md={md_out}")
    print("BYS360_QUALITY_10_10_P11_D_MENU_REGISTRY_INVENTORY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
