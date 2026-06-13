from __future__ import annotations

import argparse
import ast
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


TARGET_REL = "app/services/settings/effective_menu.py"

RISKY_NAME_HINTS = {
    "db", "session", "request", "current_user", "g", "flash", "redirect",
    "url_for", "User", "Role", "Permission", "UserMenuPermission"
}

RISKY_TEXT_HINTS = (
    "db.session", ".query", ".filter", ".filter_by", ".join", ".all(", ".first(",
    ".one(", ".get(", "request.", "current_user", "session[", "commit(", "rollback(",
)

SAFE_EXTRACT_HINTS = (
    "normalize", "slug", "key", "map", "merge", "resolve", "fallback",
    "visible", "visibility", "allowed", "menu", "policy", "build",
)


def node_lines(node: ast.AST) -> tuple[int, int, int]:
    start = getattr(node, "lineno", 0) or 0
    end = getattr(node, "end_lineno", start) or start
    return start, end, max(0, end - start + 1)


def segment(lines: list[str], start: int, end: int) -> str:
    if start <= 0 or end <= 0:
        return ""
    return "\n".join(lines[start - 1:end])


class FunctionAnalyzer(ast.NodeVisitor):
    def __init__(self) -> None:
        self.calls: set[str] = set()
        self.names_load: set[str] = set()
        self.names_store: set[str] = set()
        self.attrs: set[str] = set()
        self.imported_names: set[str] = set()

    def visit_Call(self, node: ast.Call) -> Any:
        name = self._call_name(node.func)
        if name:
            self.calls.add(name)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> Any:
        if isinstance(node.ctx, ast.Load):
            self.names_load.add(node.id)
        elif isinstance(node.ctx, (ast.Store, ast.Del)):
            self.names_store.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> Any:
        name = self._attr_name(node)
        if name:
            self.attrs.add(name)
        self.generic_visit(node)

    def _call_name(self, node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return self._attr_name(node)
        return ""

    def _attr_name(self, node: ast.Attribute) -> str:
        parts = []
        cur: ast.AST | None = node
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
        return ".".join(reversed(parts))


def collect_module_symbols(tree: ast.Module) -> dict[str, Any]:
    functions = {}
    classes = {}
    imports = []
    assignments = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start, end, count = node_lines(node)
            functions[node.name] = {
                "name": node.name,
                "start": start,
                "end": end,
                "lines": count,
                "args": [a.arg for a in node.args.args],
                "decorators": [ast.unparse(d) for d in node.decorator_list] if hasattr(ast, "unparse") else [],
            }
        elif isinstance(node, ast.ClassDef):
            start, end, count = node_lines(node)
            classes[node.name] = {"name": node.name, "start": start, "end": end, "lines": count}
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            start, end, _ = node_lines(node)
            imports.append({"start": start, "end": end, "source": ast.unparse(node) if hasattr(ast, "unparse") else ""})
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            start, end, count = node_lines(node)
            assignments.append({"start": start, "end": end, "lines": count, "source": ast.unparse(node)[:220] if hasattr(ast, "unparse") else ""})

    return {"functions": functions, "classes": classes, "imports": imports, "assignments": assignments}


def analyze_function(fn_node: ast.AST, lines: list[str], module_function_names: set[str]) -> dict[str, Any]:
    start, end, count = node_lines(fn_node)
    src = segment(lines, start, end)
    fa = FunctionAnalyzer()
    fa.visit(fn_node)

    internal_calls = sorted(c for c in fa.calls if c in module_function_names and c != getattr(fn_node, "name", ""))
    external_calls = sorted(c for c in fa.calls if c not in module_function_names)
    risky_by_name = sorted((fa.names_load | fa.names_store) & RISKY_NAME_HINTS)
    risky_by_text = sorted(h for h in RISKY_TEXT_HINTS if h.lower() in src.lower())
    safe_hint_score = sum(1 for h in SAFE_EXTRACT_HINTS if h in getattr(fn_node, "name", "").lower() or h in src.lower())

    if risky_by_name or risky_by_text:
        decision = "KEEP_OR_REVIEW_DB_CONTEXT"
        reason = "DB/request/session/current_user veya benzeri bağlam içeriyor olabilir."
    elif count >= 80:
        decision = "EXTRACT_WITH_BRIDGE_CANDIDATE"
        reason = "Büyük ama doğrudan DB/request riski görünmüyor; bridge ile ayrı helper modüle aday."
    elif internal_calls:
        decision = "LOCAL_HELPER_DEPENDENCY"
        reason = "Başka yerel fonksiyonlara bağlı; önce bağımlılık sırası doğrulanmalı."
    elif safe_hint_score >= 2:
        decision = "PURE_HELPER_CANDIDATE"
        reason = "Saf hesaplama/policy helper adayı olabilir."
    else:
        decision = "KEEP_IN_PLACE"
        reason = "Küçük veya belirsiz; taşıma önceliği düşük."

    return {
        "name": getattr(fn_node, "name", ""),
        "start": start,
        "end": end,
        "lines": count,
        "args": [a.arg for a in fn_node.args.args] if isinstance(fn_node, (ast.FunctionDef, ast.AsyncFunctionDef)) else [],
        "internal_calls": internal_calls,
        "external_calls_sample": external_calls[:40],
        "names_load_sample": sorted(fa.names_load)[:80],
        "attrs_sample": sorted(fa.attrs)[:80],
        "risky_by_name": risky_by_name,
        "risky_by_text": risky_by_text,
        "safe_hint_score": safe_hint_score,
        "decision": decision,
        "reason": reason,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--limit", type=int, default=160)
    parser.add_argument("--target-function", default="build_menu_visibility_map")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    target = project_root / TARGET_REL

    print("BYS360_QUALITY_10_10_P11_E1_EFFECTIVE_MENU_DEPENDENCY_CANDIDATES_START")
    print(f"project_root={project_root}")
    print(f"target_file={target}")

    if not target.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target}")

    text = target.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    tree = ast.parse(text)
    symbols = collect_module_symbols(tree)
    function_names = set(symbols["functions"].keys())

    function_nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    analyses = [analyze_function(node, lines, function_names) for node in function_nodes]

    by_decision = Counter(a["decision"] for a in analyses)
    target_analysis = next((a for a in analyses if a["name"] == args.target_function), None)
    pure_candidates = [a for a in analyses if a["decision"] == "PURE_HELPER_CANDIDATE"]
    bridge_candidates = [a for a in analyses if a["decision"] == "EXTRACT_WITH_BRIDGE_CANDIDATE"]
    db_context = [a for a in analyses if a["decision"] == "KEEP_OR_REVIEW_DB_CONTEXT"]

    dependency_edges = []
    for a in analyses:
        for callee in a["internal_calls"]:
            dependency_edges.append({"caller": a["name"], "callee": callee})

    extraction_plan = [
        {
            "step": "P11-E1",
            "action": "Bu paket yalnızca dependency/candidate raporu üretir; kod değişmez.",
        },
        {
            "step": "P11-E2",
            "action": "Eğer build_menu_visibility_map DB/request riski taşımıyorsa, aynı dosyada bridge bırakılarak effective_menu_calculator.py helper fonksiyonuna alınabilir.",
        },
        {
            "step": "P11-E3",
            "action": "Policy/helper fonksiyonları küçük gruplar halinde taşınır; dış import isimleri korunur.",
        },
        {
            "step": "P11-E4",
            "action": "DB repository fonksiyonları en sona bırakılır.",
        },
    ]

    smoke_tests = [
        "python -m compileall app scripts",
        "Ayarlar sayfası açılıyor mu?",
        "Rol matrisi kaydetme çalışıyor mu?",
        "Kişi bazlı menü görünürlüğü kaydediliyor mu?",
        "Başkan Onayları sekmesi Başkan/Admin dışında gizli mi?",
        "Yetkisiz kullanıcı beyaz sayfaya düşmeden kurumsal erişim engeli görüyor mu?",
        "Kalite audit P0 sıfır kalıyor mu?",
    ]

    report = {
        "target_file": TARGET_REL,
        "line_count": len(lines),
        "function_count": len(analyses),
        "by_decision": dict(by_decision.most_common()),
        "target_function": args.target_function,
        "target_analysis": target_analysis,
        "pure_helper_candidates": pure_candidates,
        "bridge_candidates": bridge_candidates,
        "db_context_functions": db_context,
        "dependency_edges": dependency_edges,
        "extraction_plan": extraction_plan,
        "smoke_tests": smoke_tests,
        "all_functions": analyses,
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / "bys360_quality_10_10_p11_e1_effective_menu_dependency_candidates_v1.json"
    md_out = out_dir / "bys360_quality_10_10_p11_e1_effective_menu_dependency_candidates_v1.md"
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# BYS360 P11-E1 Effective Menu Dependency / Candidate Raporu")
    md.append("")
    md.append(f"- Dosya: `{TARGET_REL}`")
    md.append(f"- Satır sayısı: {len(lines)}")
    md.append(f"- Fonksiyon sayısı: {len(analyses)}")
    md.append("")
    md.append("## Karar Özeti")
    md.append("")
    for key, count in by_decision.most_common():
        md.append(f"- {key}: {count}")
    md.append("")
    md.append(f"## Hedef Fonksiyon: `{args.target_function}`")
    md.append("")
    if target_analysis:
        md.append(f"- Satır: {target_analysis['start']}-{target_analysis['end']} ({target_analysis['lines']} satır)")
        md.append(f"- Karar: {target_analysis['decision']}")
        md.append(f"- Gerekçe: {target_analysis['reason']}")
        md.append(f"- İç çağrılar: {', '.join(target_analysis['internal_calls']) if target_analysis['internal_calls'] else 'Yok'}")
        md.append(f"- Riskli isimler: {', '.join(target_analysis['risky_by_name']) if target_analysis['risky_by_name'] else 'Yok'}")
        md.append(f"- Riskli metinler: {', '.join(target_analysis['risky_by_text']) if target_analysis['risky_by_text'] else 'Yok'}")
    else:
        md.append("- Hedef fonksiyon bulunamadı.")
    md.append("")
    md.append("## Bridge ile Taşıma Adayları")
    md.append("")
    if bridge_candidates:
        for a in bridge_candidates:
            md.append(f"- `{a['name']}` satır {a['start']}-{a['end']} ({a['lines']} satır) — {a['reason']}")
    else:
        md.append("- Bridge adayı bulunmadı.")
    md.append("")
    md.append("## Saf Helper Adayları")
    md.append("")
    if pure_candidates:
        for a in pure_candidates[:80]:
            md.append(f"- `{a['name']}` satır {a['start']}-{a['end']} ({a['lines']} satır)")
    else:
        md.append("- Saf helper adayı bulunmadı.")
    md.append("")
    md.append("## DB/Request Bağlamlı Fonksiyonlar")
    md.append("")
    for a in db_context[:80]:
        md.append(f"- `{a['name']}` satır {a['start']}-{a['end']} ({a['lines']} satır)")
    md.append("")
    md.append("## Smoke Testler")
    md.append("")
    for test in smoke_tests:
        md.append(f"- {test}")
    md.append("")
    md_out.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"line_count={len(lines)}")
    print(f"function_count={len(analyses)}")
    print("BYS360_QUALITY_10_10_P11_E1_DECISION_SUMMARY")
    for key, count in by_decision.most_common():
        print(f"{count:>4} | {key}")

    print("BYS360_QUALITY_10_10_P11_E1_TARGET_FUNCTION")
    if target_analysis:
        print(f"name={target_analysis['name']}")
        print(f"lines={target_analysis['start']}-{target_analysis['end']} count={target_analysis['lines']}")
        print(f"decision={target_analysis['decision']}")
        print(f"reason={target_analysis['reason']}")
        print(f"internal_calls={','.join(target_analysis['internal_calls']) if target_analysis['internal_calls'] else '-'}")
        print(f"risky_by_name={','.join(target_analysis['risky_by_name']) if target_analysis['risky_by_name'] else '-'}")
        print(f"risky_by_text={','.join(target_analysis['risky_by_text']) if target_analysis['risky_by_text'] else '-'}")
    else:
        print("target_function_not_found")

    print("BYS360_QUALITY_10_10_P11_E1_BRIDGE_CANDIDATES")
    for a in bridge_candidates[:args.limit]:
        print(f"{a['lines']:>4} | {a['start']}-{a['end']} | {a['name']} | {a['decision']}")

    print("BYS360_QUALITY_10_10_P11_E1_PURE_HELPER_CANDIDATES")
    for a in pure_candidates[:args.limit]:
        print(f"{a['lines']:>4} | {a['start']}-{a['end']} | {a['name']} | {a['decision']}")

    print(f"dependency_candidates_json={json_out}")
    print(f"dependency_candidates_md={md_out}")
    print("BYS360_QUALITY_10_10_P11_E1_EFFECTIVE_MENU_DEPENDENCY_CANDIDATES_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
