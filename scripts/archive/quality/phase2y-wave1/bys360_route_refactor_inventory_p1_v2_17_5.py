# -*- coding: utf-8 -*-
"""
BYS360 Route Refactor Inventory P1 V2.17.5
Safe inventory only: does not modify application files.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

VERSION = "V2.17.5"
REPORT_BASE = "bys360_route_refactor_inventory_p1_v2_17_5"
EXCLUDED_PARTS = {
    ".venv", "venv", "env", "__pycache__", ".git", ".mypy_cache", ".pytest_cache",
    "node_modules", "build", "dist", ".dart_tool", ".idea", ".vscode",
    "_local_quarantine", "reports", "logs", "instance", "uploads"
}
EXCLUDED_ROOT_NAMES = {"project"}
LARGE_BYTES = 50 * 1024
VERY_LARGE_BYTES = 100 * 1024
PHASE_RE = re.compile(r"(?i)(phase\d+|phase_\d+|faz\d+|v\d+_\d+|v\d+\.\d+)")
ROUTE_DECORATOR_RE = re.compile(r"@[^\n]*\.route\s*\(")
BLUEPRINT_RE = re.compile(r"\bBlueprint\s*\(")
SECRET_PATTERNS = [
    re.compile(r"(?i)\b(secret|password|passwd|pwd|token|api[_-]?key|private[_-]?key|dsn)\b"),
    re.compile(r"(?i)postgresql.*://"),
    re.compile(r"(?i)smtp.*password"),
]

@dataclass
class PyFileInfo:
    path: str
    size_kb: float
    line_count: int
    function_count: int
    class_count: int
    route_decorator_count: int
    blueprint_count: int
    import_count: int
    has_phase_name: bool
    is_route_file: bool
    category: str
    risk: str
    recommendation: str


def rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def should_skip(path: Path, root: Path) -> bool:
    try:
        r = path.relative_to(root)
    except ValueError:
        return True
    parts = set(r.parts)
    if parts & EXCLUDED_PARTS:
        return True
    if r.parts and r.parts[0] in EXCLUDED_ROOT_NAMES:
        return True
    return False


def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc, errors="replace")
        except Exception:
            continue
    return ""


def classify_file(path: Path, root: Path, text: str, tree: ast.AST | None) -> PyFileInfo:
    p = rel(path, root)
    size = path.stat().st_size
    line_count = text.count("\n") + (1 if text else 0)
    func_count = 0
    class_count = 0
    import_count = 0
    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_count += 1
            elif isinstance(node, ast.ClassDef):
                class_count += 1
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                import_count += 1
    route_count = len(ROUTE_DECORATOR_RE.findall(text))
    bp_count = len(BLUEPRINT_RE.findall(text))
    name = path.name.lower()
    has_phase = bool(PHASE_RE.search(p))
    is_route_file = name == "routes.py" or name.endswith("_routes.py") or route_count > 0

    if p.startswith("app/"):
        category = "active_app"
    elif p.startswith("scripts/"):
        category = "maintenance_script"
    elif p.startswith("mobile_flutter/"):
        category = "mobile"
    else:
        category = "other"

    risk = "low"
    rec = "Takip yeterli."
    if is_route_file and size >= VERY_LARGE_BYTES:
        risk = "high"
        rec = "P1 refactor adayı: endpointleri konu bazlı blueprint/service katmanına böl."
    elif is_route_file and size >= LARGE_BYTES:
        risk = "medium"
        rec = "P1 izleme adayı: route yoğunluğu ve servis ayrımı kontrol edilmeli."
    elif has_phase and category == "active_app":
        risk = "medium"
        rec = "Aktif app içinde phase isimli dosya: kalıcı isimlendirme veya arşiv kararı verilmeli."
    elif has_phase and category == "maintenance_script":
        risk = "low"
        rec = "Bakım scripti olabilir; devir paketinde docs/scripts altında ayrıştırılmalı."
    if route_count >= 20:
        risk = "high" if risk != "high" else risk
        rec = "Çok sayıda route decorator var; blueprint bölme planına alınmalı."

    return PyFileInfo(
        path=p,
        size_kb=round(size / 1024, 1),
        line_count=line_count,
        function_count=func_count,
        class_count=class_count,
        route_decorator_count=route_count,
        blueprint_count=bp_count,
        import_count=import_count,
        has_phase_name=has_phase,
        is_route_file=is_route_file,
        category=category,
        risk=risk,
        recommendation=rec,
    )


def scan(root: Path) -> dict[str, Any]:
    infos: list[PyFileInfo] = []
    syntax_errors: list[dict[str, str]] = []
    secret_hits: list[dict[str, Any]] = []
    for path in root.rglob("*.py"):
        if should_skip(path, root):
            continue
        text = read_text(path)
        tree = None
        try:
            tree = ast.parse(text or "", filename=str(path))
        except SyntaxError as e:
            syntax_errors.append({"path": rel(path, root), "line": str(e.lineno), "error": str(e)})
        infos.append(classify_file(path, root, text, tree))
        # only count, do not expose values
        for i, line in enumerate(text.splitlines(), start=1):
            if any(pat.search(line) for pat in SECRET_PATTERNS):
                # ignore obvious safe examples/readme-like lines less aggressively? keep location only.
                secret_hits.append({"path": rel(path, root), "line": i})
    route_files = [x for x in infos if x.is_route_file]
    large_route_files = [x for x in route_files if x.size_kb >= 50]
    high_route_files = [x for x in route_files if x.risk == "high"]
    phase_files = [x for x in infos if x.has_phase_name]
    active_phase_files = [x for x in phase_files if x.category == "active_app"]
    maintenance_phase_files = [x for x in phase_files if x.category == "maintenance_script"]
    top_large = sorted(infos, key=lambda x: x.size_kb, reverse=True)[:50]
    top_routes = sorted(route_files, key=lambda x: (x.route_decorator_count, x.size_kb), reverse=True)[:50]
    return {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "summary": {
            "python_files_scanned": len(infos),
            "route_file_count": len(route_files),
            "large_route_file_count": len(large_route_files),
            "high_route_file_count": len(high_route_files),
            "phase_file_count": len(phase_files),
            "active_app_phase_file_count": len(active_phase_files),
            "maintenance_phase_file_count": len(maintenance_phase_files),
            "syntax_error_count": len(syntax_errors),
            "possible_secret_location_count": len(secret_hits),
        },
        "large_route_files": [asdict(x) for x in sorted(large_route_files, key=lambda y: y.size_kb, reverse=True)],
        "top_route_density": [asdict(x) for x in top_routes],
        "active_phase_files": [asdict(x) for x in sorted(active_phase_files, key=lambda y: y.path)[:300]],
        "maintenance_phase_files_sample": [asdict(x) for x in sorted(maintenance_phase_files, key=lambda y: y.path)[:300]],
        "top_large_python_files": [asdict(x) for x in top_large],
        "syntax_errors": syntax_errors,
        "possible_secret_locations_sample": secret_hits[:300],
    }


def run_cmd(root: Path, args: list[str], timeout: int = 180) -> dict[str, Any]:
    try:
        cp = subprocess.run(
            args,
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        return {
            "ok": cp.returncode == 0,
            "returncode": cp.returncode,
            "stdout_tail": (cp.stdout or "")[-4000:],
            "stderr_tail": (cp.stderr or "")[-4000:],
        }
    except Exception as e:
        return {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": repr(e)}


def health(root: Path) -> dict[str, Any]:
    compile_res = run_cmd(root, [sys.executable, "-m", "compileall", "app", "config.py", "scripts"])
    factory_res = run_cmd(root, [
        sys.executable, "-c",
        "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"
    ])
    return {
        "compileall_ok": bool(compile_res.get("ok")),
        "app_factory_ok": bool(factory_res.get("ok")) and "BYS360_APP_CREATE_OK" in factory_res.get("stdout_tail", ""),
        "overall_ok": bool(compile_res.get("ok")) and bool(factory_res.get("ok")) and "BYS360_APP_CREATE_OK" in factory_res.get("stdout_tail", ""),
        "compileall": compile_res,
        "app_factory": factory_res,
    }


def write_reports(root: Path, data: dict[str, Any]) -> tuple[Path, Path]:
    out_dir = root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{REPORT_BASE}_report.json"
    md_path = out_dir / f"{REPORT_BASE}_report.md"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    s = data.get("summary", {})
    lines = [
        f"# BYS360 Route Refactor Inventory P1 {VERSION}",
        "",
        "Bu rapor yalnızca envanter çıkarır; uygulama dosyalarını değiştirmez.",
        "",
        "## Özet",
        f"- Python dosyası: {s.get('python_files_scanned', 0)}",
        f"- Route dosyası: {s.get('route_file_count', 0)}",
        f"- Büyük route dosyası: {s.get('large_route_file_count', 0)}",
        f"- Yüksek öncelikli route refactor adayı: {s.get('high_route_file_count', 0)}",
        f"- Phase isimli dosya: {s.get('phase_file_count', 0)}",
        f"- Aktif app içinde phase dosyası: {s.get('active_app_phase_file_count', 0)}",
        f"- Bakım scripti phase dosyası: {s.get('maintenance_phase_file_count', 0)}",
        f"- Syntax hatası: {s.get('syntax_error_count', 0)}",
        f"- Olası secret konumu: {s.get('possible_secret_location_count', 0)}",
        "",
        "## Büyük Route Dosyaları",
    ]
    large_routes = data.get("large_route_files", [])
    if not large_routes:
        lines.append("Büyük route dosyası bulunmadı.")
    else:
        lines.append("| Yol | KB | Satır | Route | Fonksiyon | Risk | Öneri |")
        lines.append("|---|---:|---:|---:|---:|---|---|")
        for x in large_routes[:30]:
            lines.append(f"| `{x['path']}` | {x['size_kb']} | {x['line_count']} | {x['route_decorator_count']} | {x['function_count']} | {x['risk']} | {x['recommendation']} |")
    lines += ["", "## Route Yoğunluğu İlk 30", "| Yol | Route | KB | Risk |", "|---|---:|---:|---|"]
    for x in data.get("top_route_density", [])[:30]:
        lines.append(f"| `{x['path']}` | {x['route_decorator_count']} | {x['size_kb']} | {x['risk']} |")
    lines += ["", "## Aktif App İçindeki Phase Dosyaları İlk 80"]
    active_phase = data.get("active_phase_files", [])
    if active_phase:
        for x in active_phase[:80]:
            lines.append(f"- `{x['path']}` — {x['recommendation']}")
    else:
        lines.append("Aktif app içinde phase isimli dosya bulunmadı.")
    lines += ["", "## Sonraki Güvenli Refactor Sırası", "1. Büyük route dosyalarını gerçek endpoint yoğunluğuna göre sırala.", "2. Önce servis fonksiyonlarını route dosyasından ayır; URL ve endpoint adını değiştirme.", "3. Blueprint kayıt adlarını koru.", "4. Her dosya ayrımından sonra `compileall` ve `create_app` testi çalıştır.", "5. Canlıya çıkmadan önce smoke test ve rollback notu hazırla."]
    if data.get("health"):
        h = data["health"]
        lines += ["", "## Sağlık Kontrolü", f"- compileall_ok: {h.get('compileall_ok')}", f"- app_factory_ok: {h.get('app_factory_ok')}", f"- overall_ok: {h.get('overall_ok')}"]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--mode", choices=["audit", "health", "all"], default="audit")
    ns = ap.parse_args()
    root = Path(ns.project_root).resolve()
    data: dict[str, Any] = {"version": VERSION, "mode": ns.mode, "project_root": str(root)}
    if ns.mode in ("audit", "all"):
        data.update(scan(root))
    if ns.mode in ("health", "all"):
        data["health"] = health(root)
    json_path, md_path = write_reports(root, data)
    data["json_report"] = str(json_path.relative_to(root)).replace("\\", "/")
    data["md_report"] = str(md_path.relative_to(root)).replace("\\", "/")
    print(json.dumps({k: data[k] for k in ("version", "mode", "project_root", "summary", "health", "json_report", "md_report") if k in data}, ensure_ascii=False, indent=2))
    if ns.mode in ("health", "all") and not data.get("health", {}).get("overall_ok", False):
        print(f"BYS360_ROUTE_REFACTOR_INVENTORY_P1_{VERSION}_HEALTH_FAIL")
        return 1
    if ns.mode in ("health", "all"):
        print(f"BYS360_ROUTE_REFACTOR_INVENTORY_P1_{VERSION}_HEALTH_OK")
    print(f"BYS360_ROUTE_REFACTOR_INVENTORY_P1_{VERSION}_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
