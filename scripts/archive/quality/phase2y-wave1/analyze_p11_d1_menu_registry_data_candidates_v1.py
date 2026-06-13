from __future__ import annotations

import argparse
import ast
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


TARGET_REL = "app/menu_registry.py"

LARGE_ASSIGNMENT_NAMES = {
    "ROLE_MENU_DEFAULTS",
    "MENU_SECTIONS",
    "_BYS360_PERSONEL_ROLE_MATRIX_CURRENT_DISALLOWED_KEYS",
    "_BYS360_PERFORMANCE_MAIN_SWITCH_ROLE_POLICY",
    "_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_OBSOLETE_KEYS",
    "_BYS360_PERF_RM_V8_MENU_ITEMS",
}

DOMAIN_HINTS = {
    "performance": ["performance", "performans", "score", "kpi", "period", "evaluation", "degerlendirme", "perf"],
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


def assign_names(node: ast.AST) -> list[str]:
    names: list[str] = []
    if isinstance(node, ast.Assign):
        for target in node.targets:
            names.extend(target_names(target))
    elif isinstance(node, ast.AnnAssign):
        names.extend(target_names(node.target))
    return names


def target_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, (ast.Tuple, ast.List)):
        out: list[str] = []
        for item in node.elts:
            out.extend(target_names(item))
        return out
    return []


class ExprNameVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.load_names: set[str] = set()
        self.calls: set[str] = set()
        self.attrs: set[str] = set()
        self.string_count = 0
        self.dict_count = 0
        self.list_count = 0
        self.tuple_count = 0
        self.call_count = 0

    def visit_Name(self, node: ast.Name) -> Any:
        if isinstance(node.ctx, ast.Load):
            self.load_names.add(node.id)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> Any:
        self.call_count += 1
        name = self.call_name(node.func)
        if name:
            self.calls.add(name)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> Any:
        name = self.attr_name(node)
        if name:
            self.attrs.add(name)
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> Any:
        if isinstance(node.value, str):
            self.string_count += 1
        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict) -> Any:
        self.dict_count += 1
        self.generic_visit(node)

    def visit_List(self, node: ast.List) -> Any:
        self.list_count += 1
        self.generic_visit(node)

    def visit_Tuple(self, node: ast.Tuple) -> Any:
        self.tuple_count += 1
        self.generic_visit(node)

    def call_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return self.attr_name(node)
        return ""

    def attr_name(self, node: ast.Attribute) -> str:
        parts = []
        cur: ast.AST | None = node
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        return ".".join(reversed(parts))


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


def literal_top_size(node: ast.AST | None) -> int:
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return len(node.elts)
    if isinstance(node, ast.Dict):
        return len(node.keys)
    return 0


def get_value_node(node: ast.AST) -> ast.AST | None:
    if isinstance(node, ast.Assign):
        return node.value
    if isinstance(node, ast.AnnAssign):
        return node.value
    return None


def function_references(tree: ast.Module, assignment_names: set[str]) -> dict[str, list[str]]:
    refs: dict[str, set[str]] = defaultdict(set)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names = {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
            for assigned in assignment_names:
                if assigned in names:
                    refs[assigned].add(node.name)
    return {k: sorted(v) for k, v in refs.items()}


def module_level_references(tree: ast.Module, assignment_names: set[str]) -> dict[str, list[int]]:
    refs: dict[str, list[int]] = defaultdict(list)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        names = {n.id for n in ast.walk(node) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
        line = getattr(node, "lineno", 0) or 0
        for assigned in assignment_names:
            if assigned in names:
                refs[assigned].append(line)
    return dict(refs)


def import_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                names.add(alias.asname or alias.name)
    return names


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--limit", type=int, default=160)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    target = project_root / TARGET_REL

    print("BYS360_QUALITY_10_10_P11_D1_MENU_REGISTRY_DATA_CANDIDATES_START")
    print(f"project_root={project_root}")
    print(f"target_file={target}")

    if not target.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target}")

    text = target.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    tree = ast.parse(text)
    imported = import_names(tree)

    assignment_nodes: list[ast.AST] = [
        node for node in tree.body if isinstance(node, (ast.Assign, ast.AnnAssign)) and assign_names(node)
    ]
    all_assignment_names = set()
    for node in assignment_nodes:
        all_assignment_names.update(assign_names(node))

    fn_refs = function_references(tree, all_assignment_names)
    module_refs = module_level_references(tree, all_assignment_names)

    candidates = []
    for node in assignment_nodes:
        names = assign_names(node)
        if not names:
            continue
        start, end, count = node_lines(node)
        src = segment(lines, start, end)
        val = get_value_node(node)
        visitor = ExprNameVisitor()
        if val is not None:
            visitor.visit(val)

        names_set = set(names)
        external_loads = sorted(visitor.load_names - names_set)
        dependency_on_local_assignments = sorted(set(external_loads) & all_assignment_names)
        dependency_on_imports = sorted(set(external_loads) & imported)
        unresolved_names = sorted(set(external_loads) - all_assignment_names - imported - {"True", "False", "None"})

        name_join = ", ".join(names)
        is_large = count >= 80 or literal_top_size(val) >= 20 or bool(set(names) & LARGE_ASSIGNMENT_NAMES)
        domain = classify_text(name_join, src)

        if visitor.call_count > 0:
            decision = "REVIEW_CALLS_IN_DATA"
            reason = "Assignment değeri çağrı/call içeriyor; dış modüle taşımadan önce import bağımlılıkları doğrulanmalı."
        elif dependency_on_local_assignments:
            decision = "REVIEW_LOCAL_DEPENDENCY"
            reason = "Başka top-level sabitlere bağlı; taşıma sırası ve import köprüsü gerekir."
        elif is_large:
            decision = "BRIDGE_DATA_MODULE_CANDIDATE"
            reason = "Büyük veri/sabit bloğu; aynı isimle import bridge bırakılarak dış modüle taşınabilir."
        else:
            decision = "KEEP_IN_PLACE"
            reason = "Küçük sabit; taşıma önceliği düşük."

        candidates.append({
            "names": names,
            "start": start,
            "end": end,
            "lines": count,
            "domain": domain,
            "literal_top_size": literal_top_size(val),
            "string_count": visitor.string_count,
            "dict_count": visitor.dict_count,
            "list_count": visitor.list_count,
            "tuple_count": visitor.tuple_count,
            "call_count": visitor.call_count,
            "calls": sorted(visitor.calls),
            "external_loads": external_loads,
            "dependency_on_local_assignments": dependency_on_local_assignments,
            "dependency_on_imports": dependency_on_imports,
            "unresolved_names": unresolved_names,
            "function_references": {name: fn_refs.get(name, []) for name in names},
            "module_level_reference_lines": {name: module_refs.get(name, []) for name in names},
            "is_large": is_large,
            "decision": decision,
            "reason": reason,
            "preview": src[:260].replace("\n", " "),
        })

    by_decision = Counter(c["decision"] for c in candidates)
    by_domain = Counter(c["domain"] for c in candidates)
    bridge = [c for c in candidates if c["decision"] == "BRIDGE_DATA_MODULE_CANDIDATE"]
    review = [c for c in candidates if c["decision"].startswith("REVIEW")]

    proposed_files = {
        "app/menu_registry_data_performance.py": [
            "ROLE_MENU_DEFAULTS",
            "MENU_SECTIONS",
            "_BYS360_PERFORMANCE_MAIN_SWITCH_ROLE_POLICY",
            "_BYS360_PERF_RM_V8_MENU_ITEMS",
        ],
        "app/menu_registry_data_personnel.py": [
            "_BYS360_PERSONEL_ROLE_MATRIX_CURRENT_DISALLOWED_KEYS",
            "_BYS360_PERSONEL_ROLE_MATRIX_VISIBILITY_V7_OBSOLETE_KEYS",
        ],
    }

    report = {
        "target_file": TARGET_REL,
        "line_count": len(lines),
        "assignment_count": len(candidates),
        "by_decision": dict(by_decision.most_common()),
        "by_domain": dict(by_domain.most_common()),
        "bridge_candidates": bridge,
        "review_candidates": review,
        "all_candidates": candidates,
        "proposed_files": proposed_files,
        "safety_strategy": [
            "İlk gerçek refactor yalnızca BRIDGE_DATA_MODULE_CANDIDATE kararındaki sabitleri taşımalı.",
            "menu_registry.py içinde aynı public değişken adları import bridge ile kalmalı.",
            "menu_key değerleri ve dict/list içerikleri byte-for-byte korunmalı.",
            "Review/call/local dependency içeren assignmentlar sonraya bırakılmalı.",
            "Taşıma sonrası role/menu smoke test ve kalite audit çalıştırılmalı.",
        ],
        "next_step": "P11-D2: dependency-free bridge data module extraction için dry-run destekli patch.",
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / "bys360_quality_10_10_p11_d1_menu_registry_data_candidates_v1.json"
    md_out = out_dir / "bys360_quality_10_10_p11_d1_menu_registry_data_candidates_v1.md"
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# BYS360 P11-D1 Menu Registry Data Candidate Raporu")
    md.append("")
    md.append(f"- Dosya: `{TARGET_REL}`")
    md.append(f"- Satır sayısı: {len(lines)}")
    md.append(f"- Assignment/sabit sayısı: {len(candidates)}")
    md.append("")
    md.append("## Karar Özeti")
    md.append("")
    for k, v in by_decision.most_common():
        md.append(f"- {k}: {v}")
    md.append("")
    md.append("## Bridge Data Module Adayları")
    md.append("")
    if bridge:
        for c in bridge:
            md.append(f"- `{', '.join(c['names'])}` satır {c['start']}-{c['end']} ({c['lines']} satır), domain={c['domain']}, size={c['literal_top_size']}")
    else:
        md.append("- Bridge adayı bulunmadı.")
    md.append("")
    md.append("## İnceleme Gerektirenler")
    md.append("")
    if review:
        for c in review:
            md.append(f"- `{', '.join(c['names'])}` satır {c['start']}-{c['end']} decision={c['decision']} reason={c['reason']}")
    else:
        md.append("- İnceleme gerektiren assignment yok.")
    md.append("")
    md.append("## Önerilen Dosyalar")
    md.append("")
    for file, names in proposed_files.items():
        md.append(f"- `{file}`: {', '.join(names)}")
    md.append("")
    md.append("## Güvenlik Stratejisi")
    md.append("")
    for item in report["safety_strategy"]:
        md.append(f"- {item}")
    md_out.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"line_count={len(lines)}")
    print(f"assignment_count={len(candidates)}")
    print("BYS360_QUALITY_10_10_P11_D1_DECISION_SUMMARY")
    for k, v in by_decision.most_common():
        print(f"{v:>4} | {k}")
    print("BYS360_QUALITY_10_10_P11_D1_DOMAIN_SUMMARY")
    for k, v in by_domain.most_common():
        print(f"{v:>4} | {k}")
    print("BYS360_QUALITY_10_10_P11_D1_BRIDGE_CANDIDATES")
    for c in bridge[:args.limit]:
        print(f"{c['lines']:>4} | size={c['literal_top_size']:>4} | {c['domain']} | {c['start']}-{c['end']} | {', '.join(c['names'])}")
        print(f"     refs={c['function_references']}")
    print("BYS360_QUALITY_10_10_P11_D1_REVIEW_CANDIDATES")
    for c in review[:args.limit]:
        print(f"{c['lines']:>4} | {c['decision']} | {c['start']}-{c['end']} | {', '.join(c['names'])}")
        print(f"     reason={c['reason']}")
        print(f"     calls={','.join(c['calls']) if c['calls'] else '-'}")
        print(f"     local_deps={','.join(c['dependency_on_local_assignments']) if c['dependency_on_local_assignments'] else '-'}")
    print(f"data_candidates_json={json_out}")
    print(f"data_candidates_md={md_out}")
    print("BYS360_QUALITY_10_10_P11_D1_MENU_REGISTRY_DATA_CANDIDATES_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
