from __future__ import annotations

import argparse
import json
import py_compile
import re
from datetime import datetime
from pathlib import Path
from typing import Any

PACKAGE = "BYS360_CLAUDE_SCORE_UPLIFT_P1B_MOBILE_ROUTES_SHARED_SPLIT"
MARKER = "# BYS360_P1B_MOBILE_ROUTES_SHARED_SPLIT"
ROUTE_DECORATOR_RE = re.compile(r"^\s*@mobile_api_bp\.(route|get|post|put|patch|delete)\s*\(", re.M)
ROUTE_COUNT_RE = re.compile(r"^\s*@mobile_api_bp\.(route|get|post|put|patch|delete)\s*\(", re.M)


def read_text(path: Path) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def line_count(text: str) -> int:
    return len(text.splitlines())


def route_count(text: str) -> int:
    return len(ROUTE_COUNT_RE.findall(text))


def first_route_index(text: str) -> int | None:
    match = ROUTE_DECORATOR_RE.search(text)
    return match.start() if match else None


def remove_future_import(text: str) -> str:
    return re.sub(r"^from __future__ import annotations\s*\n+", "", text, count=1, flags=re.M)


def build_shared_text(prefix: str) -> str:
    prefix = prefix.rstrip() + "\n\n"
    if MARKER not in prefix:
        prefix = prefix.replace("from __future__ import annotations\n", "from __future__ import annotations\n\n" + MARKER + "\n", 1) if prefix.startswith("from __future__ import annotations") else "from __future__ import annotations\n\n" + MARKER + "\n\n" + prefix
    all_block = """
# Import-star bu dosyada bilinçli kullanılır: routes.py içinde eski yardımcı isimlerin
# tamamı aynı adlarla görünür kalır; URL/endpoint sözleşmesi değişmez.
__all__ = [name for name in globals() if not name.startswith("__")]
"""
    if "__all__ = [name for name in globals()" not in prefix:
        prefix += all_block
    return prefix


def build_routes_text(body: str) -> str:
    body = body.lstrip("\n")
    return (
        "from __future__ import annotations\n\n"
        f"{MARKER}\n"
        "# Bu dosya artık mobil API endpoint sözleşmesini taşır; ortak yardımcılar shared.py içindedir.\n"
        "# Amaç: god-file etkisini azaltmak, endpoint/URL sözleşmesini bozmadan P1 mimari temizliğe başlamak.\n\n"
        "from app.api.mobile.shared import *  # noqa: F401,F403 - P1B endpoint sözleşmesi için bilinçli facade import\n\n\n"
        + body
    )


def compile_file(path: Path) -> dict[str, Any]:
    try:
        py_compile.compile(str(path), doraise=True)
        return {"file": str(path), "ok": True, "error": ""}
    except Exception as exc:  # pragma: no cover - raporlama amaçlı
        return {"file": str(path), "ok": False, "error": str(exc)}


def run(root: Path, mode: str) -> dict[str, Any]:
    root = root.resolve()
    routes = root / "app" / "api" / "mobile" / "routes.py"
    shared = root / "app" / "api" / "mobile" / "shared.py"
    report_dir = root / "reports" / "architecture"
    docs_dir = root / "docs" / "architecture"
    report_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    if not routes.exists():
        data = {
            "ok": False,
            "package": PACKAGE,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "root": str(root),
            "mode": mode,
            "error": "app/api/mobile/routes.py bulunamadı",
        }
        write_outputs(report_dir, docs_dir, data)
        return data

    original = read_text(routes)
    before_lines = line_count(original)
    before_routes = route_count(original)
    already_split = MARKER in original and shared.exists()
    changed: list[str] = []
    compile_results: list[dict[str, Any]] = []

    if mode in {"all", "write"} and not already_split:
        idx = first_route_index(original)
        if idx is None:
            data = {
                "ok": False,
                "package": PACKAGE,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "root": str(root),
                "mode": mode,
                "error": "mobile_api_bp route decorator bulunamadı; split uygulanmadı",
                "before": {"routes_py_lines": before_lines, "route_decorator_count": before_routes},
            }
            write_outputs(report_dir, docs_dir, data)
            return data
        prefix = original[:idx]
        body = original[idx:]
        shared_text = build_shared_text(prefix)
        routes_text = build_routes_text(body)
        write_text(shared, shared_text)
        write_text(routes, routes_text)
        changed.extend(["app/api/mobile/shared.py", "app/api/mobile/routes.py"])

    current_routes = read_text(routes)
    current_shared = read_text(shared) if shared.exists() else ""
    after_lines = line_count(current_routes)
    after_routes = route_count(current_routes)
    shared_lines = line_count(current_shared) if current_shared else 0
    split_ok = shared.exists() and MARKER in current_routes and "from app.api.mobile.shared import *" in current_routes
    route_contract_ok = before_routes == after_routes if before_routes else after_routes > 0

    if mode in {"all", "write"}:
        compile_results = [compile_file(shared), compile_file(routes)] if shared.exists() else [compile_file(routes)]
    compile_ok = all(item.get("ok") for item in compile_results) if compile_results else True

    data = {
        "ok": bool(split_ok and route_contract_ok and compile_ok and after_lines < max(before_lines, 2000)),
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "mode": mode,
        "changed_count": len(changed),
        "changed": changed,
        "already_split": already_split,
        "before": {"routes_py_lines": before_lines, "route_decorator_count": before_routes},
        "after": {"routes_py_lines": after_lines, "shared_py_lines": shared_lines, "route_decorator_count": after_routes},
        "checks": {
            "shared_exists": shared.exists(),
            "routes_facade_import": "from app.api.mobile.shared import *" in current_routes,
            "marker": MARKER in current_routes,
            "route_contract_unchanged": route_contract_ok,
            "routes_py_under_2000_lines": after_lines < 2000,
            "compile_ok": compile_ok,
        },
        "compile_results": compile_results,
        "report": str(report_dir / "BYS360_MOBILE_ROUTES_SHARED_SPLIT_P1B_REPORT.json"),
        "next_actions": [
            "P1C'de app/api/mobile/routes.py içindeki endpointler auth/dashboard/notifications/support/surveys/performance/personnel/asistan alanlarına ayrılmalı.",
            "P1B facade yapısı URL/endpoint sözleşmesini koruduğu için canlı risk düşük tutulmuştur.",
            "P1C öncesi flask app factory ve mobil smoke testleri çalıştırılmalıdır.",
        ],
    }
    write_outputs(report_dir, docs_dir, data)
    return data


def markdown(data: dict[str, Any]) -> str:
    before = data.get("before", {})
    after = data.get("after", {})
    checks = data.get("checks", {})
    lines = [
        "# BYS360 P1B Mobil Route Shared Split Raporu",
        "",
        f"Üretim zamanı: `{data.get('generated_at','')}`",
        "",
        "## Özet",
        "",
        "| Alan | Değer |",
        "|---|---:|",
        f"| İşlem sonucu | `{data.get('ok')}` |",
        f"| Değişen dosya | {data.get('changed_count', 0)} |",
        f"| routes.py önce | {before.get('routes_py_lines', 0)} satır |",
        f"| routes.py sonra | {after.get('routes_py_lines', 0)} satır |",
        f"| shared.py | {after.get('shared_py_lines', 0)} satır |",
        f"| Route decorator sayısı önce | {before.get('route_decorator_count', 0)} |",
        f"| Route decorator sayısı sonra | {after.get('route_decorator_count', 0)} |",
        "",
        "## Kontroller",
        "",
        "| Kontrol | Durum |",
        "|---|---:|",
    ]
    for key, value in checks.items():
        lines.append(f"| `{key}` | `{value}` |")
    lines.extend([
        "",
        "## Not",
        "",
        "Bu faz mobil API dosyasındaki ortak yardımcıları `shared.py` dosyasına alır. Endpoint decorator'ları `routes.py` içinde kaldığı için URL ve endpoint sözleşmesi korunur. Amaç, P1C'de yapılacak domain bazlı ayrıştırmaya güvenli bir ara basamak oluşturmaktır.",
    ])
    return "\n".join(lines) + "\n"


def write_outputs(report_dir: Path, docs_dir: Path, data: dict[str, Any]) -> None:
    report = report_dir / "BYS360_MOBILE_ROUTES_SHARED_SPLIT_P1B_REPORT.json"
    report_md = report_dir / "BYS360_MOBILE_ROUTES_SHARED_SPLIT_P1B_REPORT.md"
    docs_md = docs_dir / "BYS360_MOBILE_ROUTES_SHARED_SPLIT_P1B_REPORT.md"
    data["report"] = str(report)
    report.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    md = markdown(data)
    report_md.write_text(md, encoding="utf-8")
    docs_md.write_text(md, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="BYS360 P1B mobile routes shared split")
    parser.add_argument("--root", default=".")
    parser.add_argument("--mode", choices=["audit", "write", "all"], default="all")
    args = parser.parse_args()
    data = run(Path(args.root), args.mode)
    print(json.dumps({
        "ok": data.get("ok"),
        "package": data.get("package"),
        "mode": data.get("mode"),
        "changed_count": data.get("changed_count", 0),
        "before": data.get("before"),
        "after": data.get("after"),
        "checks": data.get("checks"),
        "report": data.get("report"),
    }, ensure_ascii=False, indent=2))
    return 0 if data.get("ok") else 1

if __name__ == "__main__":
    raise SystemExit(main())
