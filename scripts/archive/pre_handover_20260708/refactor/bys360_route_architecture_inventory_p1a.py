from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

PACKAGE = "BYS360_MAINTENANCE_SCORE_UPLIFT_P1A_ARCHITECTURE_ROUTE_INVENTORY"

IGNORED_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "reports", "backups", "backup",
    "archive", "archives", "release", "releases", "dist", "build", "quarantine", ".quarantine",
}

HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}

@dataclass
class RouteInfo:
    file: str
    line: int
    function: str
    rule: str
    methods: list[str]
    blueprint_or_app: str
    endpoint_hint: str

@dataclass
class FileInfo:
    file: str
    line_count: int
    route_count: int
    blueprint_count: int
    class_count: int
    function_count: int
    is_mobile_api: bool
    size_level: str


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def should_skip(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except Exception:
        parts = path.parts
    return any(part in IGNORED_DIRS for part in parts)


def iter_py_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.py"):
        if not should_skip(path, root):
            yield path


def read_text(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def literal_str(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "<dynamic>"
    return None


def decorator_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = decorator_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Call):
        return decorator_name(node.func)
    return ""


def methods_from_call(call: ast.Call) -> list[str]:
    for kw in call.keywords:
        if kw.arg == "methods":
            value = kw.value
            if isinstance(value, (ast.List, ast.Tuple, ast.Set)):
                methods: list[str] = []
                for elt in value.elts:
                    if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                        methods.append(elt.value.upper())
                return sorted(set(m for m in methods if m in HTTP_METHODS)) or ["GET"]
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                return [value.value.upper()]
    return ["GET"]


def route_from_decorator(dec: ast.AST) -> tuple[str, str, list[str]] | None:
    if not isinstance(dec, ast.Call):
        return None
    name = decorator_name(dec.func)
    if not name.endswith(".route") and name != "route":
        return None
    rule = "<unknown>"
    if dec.args:
        maybe = literal_str(dec.args[0])
        if maybe:
            rule = maybe
    bp = name.rsplit(".", 1)[0] if "." in name else "app_or_route"
    return bp, rule, methods_from_call(dec)


def blueprint_assignments(tree: ast.AST) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            if isinstance(node.value, ast.Call) and decorator_name(node.value.func).endswith("Blueprint"):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        found.add(target.id)
    return found


def analyze_file(path: Path, root: Path) -> tuple[FileInfo, list[RouteInfo], list[str]]:
    text = read_text(path)
    lines = text.splitlines()
    rel_path = rel(path, root)
    warnings: list[str] = []
    try:
        tree = ast.parse(text, filename=rel_path)
    except SyntaxError as exc:
        info = FileInfo(rel_path, len(lines), 0, 0, 0, 0, "app/api/mobile" in rel_path, "syntax_error")
        return info, [], [f"{rel_path}:{exc.lineno}: syntax_error: {exc.msg}"]

    blueprints = blueprint_assignments(tree)
    routes: list[RouteInfo] = []
    function_count = 0
    class_count = 0

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function_count += 1
            for dec in node.decorator_list:
                route = route_from_decorator(dec)
                if route:
                    bp, rule, methods = route
                    routes.append(RouteInfo(
                        file=rel_path,
                        line=getattr(node, "lineno", 0),
                        function=node.name,
                        rule=rule,
                        methods=methods,
                        blueprint_or_app=bp,
                        endpoint_hint=f"{bp}.{node.name}" if bp else node.name,
                    ))
        elif isinstance(node, ast.ClassDef):
            class_count += 1

    line_count = len(lines)
    if line_count >= 2000:
        level = "critical_god_file"
    elif line_count >= 1000:
        level = "high_large_file"
    elif line_count >= 500:
        level = "medium_large_file"
    else:
        level = "normal"

    info = FileInfo(
        file=rel_path,
        line_count=line_count,
        route_count=len(routes),
        blueprint_count=len(blueprints),
        class_count=class_count,
        function_count=function_count,
        is_mobile_api="app/api/mobile" in rel_path,
        size_level=level,
    )
    return info, routes, warnings


def build_openapi(routes: list[RouteInfo]) -> dict[str, Any]:
    paths: dict[str, Any] = {}
    for r in routes:
        if not r.rule.startswith("/"):
            path = "/" + r.rule
        else:
            path = r.rule
        path = re.sub(r"<(?:[^:<>]+:)?([^<>]+)>", r"{\1}", path)
        item = paths.setdefault(path, {})
        for method in r.methods or ["GET"]:
            lower = method.lower()
            item[lower] = {
                "summary": f"{r.function} ({r.file})",
                "operationId": re.sub(r"[^a-zA-Z0-9_]", "_", r.endpoint_hint),
                "responses": {
                    "200": {"description": "Başarılı yanıt"},
                    "401": {"description": "Oturum veya yetki gerekli"},
                    "403": {"description": "Yetki sınırı"},
                },
            }
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "BYS360 API Taslak Envanteri",
            "version": "p1a-inventory",
            "description": "Koddan otomatik çıkarılan başlangıç OpenAPI taslağıdır; P1 fazında manuel doğrulama ile zenginleştirilecektir.",
        },
        "paths": dict(sorted(paths.items())),
    }


def markdown_report(data: dict[str, Any]) -> str:
    totals = data["totals"]
    large = data["large_files"][:30]
    mobile = data["mobile_files"]
    lines = [
        f"# BYS360 P1A Mimari Route Envanteri",
        "",
        f"Üretim zamanı: `{data['generated_at']}`",
        "",
        "## Özet",
        "",
        "| Alan | Değer |",
        "|---|---:|",
        f"| Taranan Python dosyası | {totals['python_files']} |",
        f"| Route sayısı | {totals['routes']} |",
        f"| Blueprint bulunan dosya | {totals['blueprint_files']} |",
        f"| Büyük dosya uyarısı | {totals['large_file_count']} |",
        f"| Kritik/god file | {totals['critical_god_file_count']} |",
        "",
        "## Büyük Dosya Listesi",
        "",
        "| Dosya | Satır | Route | Seviye |",
        "|---|---:|---:|---|",
    ]
    for item in large:
        lines.append(f"| `{item['file']}` | {item['line_count']} | {item['route_count']} | `{item['size_level']}` |")
    if not large:
        lines.append("| Büyük dosya yok | 0 | 0 | normal |")
    lines.extend([
        "",
        "## Mobil API Odak Alanı",
        "",
        "| Dosya | Satır | Route | Seviye |",
        "|---|---:|---:|---|",
    ])
    for item in mobile:
        lines.append(f"| `{item['file']}` | {item['line_count']} | {item['route_count']} | `{item['size_level']}` |")
    if not mobile:
        lines.append("| Mobil API dosyası bulunamadı | 0 | 0 | - |")
    lines.extend([
        "",
        "## P1B için karar notu",
        "",
        "Bu rapor kod değiştirmez. Amaç, P1B'de route parçalama ve konsolidasyon yapılırken endpoint kaybı yaşanmaması için mevcut tabloyu sabitlemektir.",
        "",
        "Öncelik sırası:",
        "1. `app/api/mobile/routes.py` ve benzeri kritik uzun dosyaları domain bazlı ayırmak.",
        "2. Endpoint isimlerini ve URL sözleşmesini bozmadan geriye uyumluluk sağlamak.",
        "3. OpenAPI taslağını doğrulanmış API dokümanına dönüştürmek.",
    ])
    return "\n".join(lines) + "\n"


def run(root: Path, mode: str) -> dict[str, Any]:
    root = root.resolve()
    report_dir = root / "reports" / "architecture"
    docs_arch = root / "docs" / "architecture"
    docs_api = root / "docs" / "api"
    if mode in {"all", "write"}:
        report_dir.mkdir(parents=True, exist_ok=True)
        docs_arch.mkdir(parents=True, exist_ok=True)
        docs_api.mkdir(parents=True, exist_ok=True)

    files: list[FileInfo] = []
    routes: list[RouteInfo] = []
    warnings: list[str] = []
    for py_file in sorted(iter_py_files(root)):
        info, file_routes, file_warnings = analyze_file(py_file, root)
        files.append(info)
        routes.extend(file_routes)
        warnings.extend(file_warnings)

    large = sorted(
        [asdict(f) for f in files if f.size_level != "normal"],
        key=lambda x: (-x["line_count"], x["file"]),
    )
    mobile = sorted([asdict(f) for f in files if f.is_mobile_api], key=lambda x: (-x["line_count"], x["file"]))
    routes_dict = [asdict(r) for r in sorted(routes, key=lambda r: (r.file, r.line, r.function))]

    data: dict[str, Any] = {
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "mode": mode,
        "ok": True,
        "totals": {
            "python_files": len(files),
            "routes": len(routes),
            "blueprint_files": sum(1 for f in files if f.blueprint_count > 0),
            "large_file_count": len(large),
            "critical_god_file_count": sum(1 for f in files if f.size_level == "critical_god_file"),
            "mobile_file_count": len(mobile),
            "syntax_warning_count": len(warnings),
        },
        "large_files": large,
        "mobile_files": mobile,
        "routes": routes_dict,
        "syntax_warnings": warnings[:100],
        "next_actions": [
            "P1B'de kritik uzun route dosyaları domain bazlı modüllere ayrılmalı.",
            "Endpoint/URL sözleşmesi korunmalı; geriye uyumluluk testleri eklenmeli.",
            "docs/api/openapi_draft.json manuel doğrulama ile resmi API dokümanına dönüştürülmeli.",
        ],
    }
    openapi = build_openapi(routes)
    md = markdown_report(data)

    if mode in {"all", "write"}:
        (report_dir / "BYS360_ROUTE_ARCHITECTURE_INVENTORY_P1A.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (report_dir / "BYS360_ROUTE_ARCHITECTURE_INVENTORY_P1A.md").write_text(md, encoding="utf-8")
        (docs_arch / "BYS360_ROUTE_ARCHITECTURE_INVENTORY_P1A.md").write_text(md, encoding="utf-8")
        (docs_api / "openapi_draft.json").write_text(
            json.dumps(openapi, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        data["written"] = [
            "reports/architecture/BYS360_ROUTE_ARCHITECTURE_INVENTORY_P1A.json",
            "reports/architecture/BYS360_ROUTE_ARCHITECTURE_INVENTORY_P1A.md",
            "docs/architecture/BYS360_ROUTE_ARCHITECTURE_INVENTORY_P1A.md",
            "docs/api/openapi_draft.json",
        ]
    else:
        data["written"] = []
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="BYS360 P1A route architecture inventory")
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument("--mode", default="audit", choices=["audit", "write", "all"])
    args = parser.parse_args()
    data = run(Path(args.root), args.mode)
    print(json.dumps({
        "ok": data["ok"],
        "package": data["package"],
        "mode": data["mode"],
        "totals": data["totals"],
        "written": data.get("written", []),
    }, ensure_ascii=False, indent=2))
    return 0 if data["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
