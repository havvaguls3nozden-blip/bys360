from __future__ import annotations

import argparse
import ast
import compileall
import datetime as _dt
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

PACKAGE = "repo_hygiene_p4_big_file_modularization_audit"
VERSION = "V1"

SKIP_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "__pycache__",
    "node_modules", "archive", "reports", "releases", "instance", ".mypy_cache",
    ".pytest_cache", ".ruff_cache",
}

# Project-level backup folders should not be used to judge active source health.
SKIP_TOP_LEVEL_NAMES = {"backups", "archive", "reports", "releases"}

ROUTE_RE = re.compile(r"^\s*@[^\n]*\.route\(", re.M)
EXCEPT_PASS_RE = re.compile(r"except\s+(?:Exception|BaseException)?[^:\n]*:\s*(?:\n\s*)?pass\b", re.M)
PRINT_RE = re.compile(r"(^|[^\w.])print\s*\(", re.M)
PHASE_RE = re.compile(r"phase\d+", re.I)


def rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def iter_python_files(project_root: Path) -> List[Path]:
    files: List[Path] = []
    app_root = project_root / "app"
    if not app_root.exists():
        return files
    for p in app_root.rglob("*.py"):
        parts = set(p.relative_to(project_root).parts)
        if parts & SKIP_DIRS:
            continue
        files.append(p)
    return sorted(files)


def count_lines(text: str) -> int:
    if not text:
        return 0
    return text.count("\n") + (0 if text.endswith("\n") else 1)


def ast_counts(text: str) -> Tuple[int, int, int, List[str], List[str]]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return 0, 0, 0, [], []
    funcs = 0
    classes = 0
    async_funcs = 0
    names: List[str] = []
    class_names: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            funcs += 1
            if len(names) < 20:
                names.append(node.name)
        elif isinstance(node, ast.AsyncFunctionDef):
            async_funcs += 1
            if len(names) < 20:
                names.append(node.name)
        elif isinstance(node, ast.ClassDef):
            classes += 1
            if len(class_names) < 20:
                class_names.append(node.name)
    return funcs, classes, async_funcs, names, class_names


def import_head(text: str, limit_lines: int = 80) -> List[str]:
    out: List[str] = []
    for line in text.splitlines()[:limit_lines]:
        s = line.strip()
        if s.startswith("import ") or s.startswith("from "):
            out.append(s)
    return out[:30]


def recommendation_for(path_rel: str, line_count: int, route_count: int, function_count: int) -> Dict[str, Any]:
    lower = path_rel.lower()
    priority = "P2"
    if line_count >= 2200 or route_count >= 25:
        priority = "P0"
    elif line_count >= 1500 or route_count >= 12:
        priority = "P1"

    if "corporate_information_center.py" in lower:
        target = "app/services/corporate_information_center/"
        slices = [
            "query_service.py: listeleme, filtreleme ve ortak sorgu yardimcilari",
            "celebration_service.py: kutlama, dogum gunu, yil donumu ve Excel import mantigi",
            "mail_scheduler_service.py: otomatik mail, hafta ici/hafta sonu kurallari ve zamanlanmis isler",
            "template_service.py: sablon ve icerik uretim mantigi",
            "repository.py: DB yazma/okuma islemlerini sade servislerden ayirma",
        ]
        strategy = "Once sadece servis fonksiyonlari tasinmali; route imzalari ve template adlari degismemeli."
    elif "mobile/routes.py" in lower:
        target = "app/api/mobile/"
        slices = [
            "auth_routes.py: login, oturum, kullanici profili",
            "dashboard_routes.py: ana sayfa ve ozet kartlari",
            "notification_routes.py: bildirim ve okunma islemleri",
            "support_routes.py: destek talebi liste/detay/cevap",
            "common_routes.py: health, config ve ortak yanit yapilari",
        ]
        strategy = "Blueprint URL prefix korunmali; once route fonksiyonlari birebir tasinip import/registration eklenmeli."
    elif "performance_routes.py" in lower:
        target = "app/api/mobile/performance/"
        slices = [
            "period_routes.py: donem liste/detay",
            "task_routes.py: gorevlerim ve amir gorevleri",
            "scorecard_routes.py: karne ve arsiv ozetleri",
            "evaluation_routes.py: puanlama ve iade/ret islemleri",
            "summary_routes.py: mobil performans dashboard ozetleri",
        ]
        strategy = "Mobil API sozlesmesi bozulmadan route bazli parcalama yapilmali."
    elif "effective_menu.py" in lower:
        target = "app/services/settings/effective_menu/"
        slices = [
            "role_policy.py: rol bazli varsayilan gorunurluk",
            "user_policy.py: kisi bazli istisna ve override",
            "unit_policy.py: birim profili ve kapsam",
            "resolver.py: nihai menu hesaplama motoru",
            "cache.py: cache anahtari, gecersiz kilma ve refresh",
        ]
        strategy = "Nihai public fonksiyonlar korunmali; once saf politika fonksiyonlari alt dosyalara alinmali."
    elif "phase" in lower:
        target = str(Path(path_rel).with_suffix("")) + "/"
        slices = [
            "policy.py: kural ve karar mantigi",
            "repository.py: DB erisimleri",
            "view_model.py: ekran/rapor icin hazir veri",
            "audit.py: rapor ve kalite kontrol yardimcilari",
        ]
        strategy = "Phase dosyasi yeni moduller icin facade olarak bir sure korunmali; cagirilar kademeli tasinmali."
    else:
        target = str(Path(path_rel).with_suffix("")) + "/"
        slices = [
            "service.py: ana is kurallari",
            "repository.py: veri erisimi",
            "schemas.py: veri sekillendirme",
            "helpers.py: saf yardimci fonksiyonlar",
        ]
        strategy = "Once disari acik fonksiyonlar sabitlenmeli, sonra 300-500 satirlik parcalara bolunmeli."

    return {
        "priority": priority,
        "target_package": target,
        "suggested_slices": slices,
        "strategy": strategy,
        "risk_note": "Audit-only rapordur; bu faz kod degistirmez. Refactor P5/P6 gibi kucuk overlaylere bolunmelidir.",
    }


def analyze_file(p: Path, root: Path) -> Dict[str, Any]:
    text = p.read_text(encoding="utf-8", errors="replace")
    path_rel = rel(p, root)
    line_count = count_lines(text)
    funcs, classes, async_funcs, func_names, class_names = ast_counts(text)
    route_count = len(ROUTE_RE.findall(text))
    except_pass_count = len(EXCEPT_PASS_RE.findall(text))
    print_count = len(PRINT_RE.findall(text))
    phase_name = bool(PHASE_RE.search(path_rel))
    score = line_count + route_count * 90 + funcs * 5 + except_pass_count * 40 + print_count * 10 + (200 if phase_name else 0)
    return {
        "path": path_rel,
        "line_count": line_count,
        "size_bytes": p.stat().st_size,
        "function_count": funcs,
        "async_function_count": async_funcs,
        "class_count": classes,
        "route_count": route_count,
        "except_pass_count": except_pass_count,
        "print_count": print_count,
        "phase_named": phase_name,
        "score": score,
        "sample_functions": func_names,
        "sample_classes": class_names,
        "imports_head": import_head(text),
        "recommendation": recommendation_for(path_rel, line_count, route_count, funcs),
    }


def compile_targets(project_root: Path) -> Dict[str, Any]:
    targets = [project_root / "app", project_root / "config.py", project_root / "scripts"]
    results = []
    ok_all = True
    for target in targets:
        if not target.exists():
            results.append({"target": str(target), "ok": None, "note": "not_found"})
            continue
        ok = compileall.compile_file(str(target), quiet=1) if target.is_file() else compileall.compile_dir(str(target), quiet=1)
        results.append({"target": str(target), "ok": bool(ok)})
        ok_all = ok_all and bool(ok)
    return {"ok": bool(ok_all), "results": results}


def make_markdown(result: Dict[str, Any]) -> str:
    lines: List[str] = []
    s = result["summary"]
    lines.append(f"# BYS360 Repo Hijyeni P4 Buyuk Dosya Modularizasyon Audit Raporu")
    lines.append("")
    lines.append("Bu rapor kod degistirmez. Amac buyuk dosyalari bolmeden once risk ve oncelik planini cikarmaktir.")
    lines.append("")
    lines.append("## Ozet")
    lines.append("")
    lines.append("| Alan | Deger |")
    lines.append("|---|---:|")
    for k in ["mode", "scanned_python_files", "large_file_count", "min_lines", "top", "compileall_ok"]:
        lines.append(f"| {k} | `{s.get(k)}` |")
    lines.append("")
    lines.append("## En Buyuk / En Riskli Dosyalar")
    lines.append("")
    lines.append("| Oncelik | Dosya | Satir | Route | Fonksiyon | except/pass | print | Onerilen hedef |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---|")
    for item in result["large_files"]:
        rec = item["recommendation"]
        lines.append(
            f"| {rec['priority']} | `{item['path']}` | {item['line_count']} | {item['route_count']} | "
            f"{item['function_count']} | {item['except_pass_count']} | {item['print_count']} | `{rec['target_package']}` |"
        )
    lines.append("")
    lines.append("## Dosya Bazli Bolme Plani")
    lines.append("")
    for item in result["large_files"]:
        rec = item["recommendation"]
        lines.append(f"### {rec['priority']} — `{item['path']}`")
        lines.append("")
        lines.append(f"- Satir: **{item['line_count']}**")
        lines.append(f"- Route: **{item['route_count']}**")
        lines.append(f"- Fonksiyon: **{item['function_count']}**")
        lines.append(f"- Onerilen hedef paket: `{rec['target_package']}`")
        lines.append(f"- Strateji: {rec['strategy']}")
        lines.append("")
        lines.append("Onerilen parcalar:")
        for sl in rec["suggested_slices"]:
            lines.append(f"- {sl}")
        lines.append("")
    lines.append("## Sonraki Adim")
    lines.append("")
    lines.append("P4 sadece plan cikardi. Bundan sonra P5 olarak tek dosya secilip kucuk, geri alinabilir bir facade refactor overlayi hazirlanmalidir. Ilk aday genellikle `app/api/mobile/routes.py` veya `app/services/corporate_information_center.py` olmalidir.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--mode", choices=["audit", "all"], default="audit")
    ap.add_argument("--min-lines", type=int, default=1000)
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--compileall", action="store_true")
    ns = ap.parse_args()

    project_root = Path(ns.project_root).resolve()
    now = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = project_root / "reports" / "repo_hygiene" / f"P4_BIG_FILE_MODULARIZATION_{now}"
    report_dir.mkdir(parents=True, exist_ok=True)

    files = iter_python_files(project_root)
    analyses = [analyze_file(p, project_root) for p in files]
    large = [a for a in analyses if a["line_count"] >= ns.min_lines]
    large.sort(key=lambda x: x["score"], reverse=True)
    large = large[: ns.top]

    compile_result = None
    if ns.compileall or ns.mode == "all":
        compile_result = compile_targets(project_root)

    result: Dict[str, Any] = {
        "ok": True,
        "package": PACKAGE,
        "version": VERSION,
        "mode": ns.mode,
        "project_root": str(project_root),
        "summary": {
            "mode": ns.mode,
            "scanned_python_files": len(files),
            "large_file_count": len([a for a in analyses if a["line_count"] >= ns.min_lines]),
            "min_lines": ns.min_lines,
            "top": ns.top,
            "compileall_ok": None if compile_result is None else compile_result["ok"],
            "p0_count": sum(1 for a in large if a["recommendation"]["priority"] == "P0"),
            "p1_count": sum(1 for a in large if a["recommendation"]["priority"] == "P1"),
            "p2_count": sum(1 for a in large if a["recommendation"]["priority"] == "P2"),
        },
        "actions": {
            "changed_files": 0,
            "note": "Audit-only: kaynak kod degistirilmedi.",
            "compileall": compile_result,
        },
        "large_files": large,
        "next_step": "P5 icin tek bir P0 dosyada facade korumali parcalama overlayi hazirlanmali.",
    }

    md = make_markdown(result)
    report_json = report_dir / "repo_hygiene_p4_report.json"
    report_md = report_dir / "repo_hygiene_p4_report.md"
    report_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    report_md.write_text(md, encoding="utf-8")
    result["report_markdown"] = str(report_md)
    result["report_json"] = str(report_json)

    # Re-write with report paths included.
    report_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
