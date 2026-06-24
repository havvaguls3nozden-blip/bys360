from __future__ import annotations

import argparse
import json
import py_compile
import re
from datetime import datetime
from pathlib import Path
from typing import Any

PACKAGE = "BYS360_MAINTENANCE_SCORE_UPLIFT_P1C_MOBILE_ROUTES_DOMAIN_SPLIT"
MARKER = "# BYS360_P1C_MOBILE_ROUTES_DOMAIN_SPLIT"
P1B_MARKER = "# BYS360_P1B_MOBILE_ROUTES_SHARED_SPLIT"
ROUTE_DECORATOR_RE = re.compile(r"^\s*@mobile_api_bp\.(route|get|post|put|patch|delete)\s*\(", re.M)
ROUTE_RULE_RE = re.compile(r"^\s*@mobile_api_bp\.(?:route|get|post|put|patch|delete)\s*\(([^\n]*)", re.M)


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
    return len(ROUTE_DECORATOR_RE.findall(text))


def route_fingerprint(text: str) -> list[str]:
    # Decorator satırındaki rule/metot imzasını sözleşme karşılaştırması için saklar.
    values: list[str] = []
    for m in ROUTE_RULE_RE.finditer(text):
        line = m.group(0).strip()
        values.append(re.sub(r"\s+", " ", line))
    return values


def compile_file(path: Path) -> dict[str, Any]:
    try:
        py_compile.compile(str(path), doraise=True)
        return {"file": str(path), "ok": True, "error": ""}
    except Exception as exc:  # pragma: no cover - raporlama amaçlı
        return {"file": str(path), "ok": False, "error": str(exc)}


def find_range(text: str, start_pat: str, end_pat: str) -> tuple[int, int] | None:
    start = re.search(start_pat, text, flags=re.M)
    if not start:
        return None
    end = re.search(end_pat, text[start.start() + 1 :], flags=re.M)
    if not end:
        return None
    return start.start(), start.start() + 1 + end.start()


def find_range_to_marker(text: str, start_pat: str, end_pat: str) -> tuple[int, int] | None:
    return find_range(text, start_pat, end_pat)


def module_text(domain: str, body: str) -> str:
    clean = body.strip("\n") + "\n"
    return (
        "from __future__ import annotations\n\n"
        f"{MARKER}\n"
        f"# Domain: {domain}\n"
        "# Bu modül mobil API endpoint sözleşmesini domain bazlı taşır.\n"
        "# URL/endpoint isimleri korunur; ortak yardımcılar shared.py içinden gelir.\n\n"
        "from app.api.mobile.shared import *  # noqa: F401,F403 - BYS360 P1C domain endpoint importu\n\n\n"
        + clean
        + "\n"
    )


def ensure_domain_imports(routes_text: str, domains: list[str]) -> str:
    imports = []
    for domain in domains:
        imports.append(f"from app.api.mobile.domains.{domain} import *  # noqa: F401,F403 - P1C domain route registration")
    block = MARKER + "\n" + "\n".join(imports) + "\n"
    if MARKER in routes_text:
        return routes_text
    shared_import = "from app.api.mobile.shared import *  # noqa: F401,F403 - P1B endpoint sözleşmesi için bilinçli facade import"
    if shared_import in routes_text:
        return routes_text.replace(shared_import, shared_import + "\n\n" + block, 1)
    # Beklenmeyen durumda en üste ekle ama sözleşmeyi bozma.
    return block + "\n" + routes_text


def split_domains(original: str) -> tuple[str, dict[str, str], list[str]]:
    # P1C bilinçli olarak düşük riskli ilk domainleri taşır: auth, dashboard, personnel read, notifications.
    # Kalan büyük iletişim/destek/performans blokları P1D/P1E'de contract smoke sonrası ayrılacaktır.
    specs = [
        (
            "auth",
            r"^@mobile_api_bp\.post\([\"']/auth/login[\"']\)",
            r"^@mobile_api_bp\.get\([\"']/dashboard/summary[\"']\)",
        ),
        (
            "dashboard",
            r"^@mobile_api_bp\.get\([\"']/dashboard/summary[\"']\)",
            r"^@mobile_api_bp\.get\([\"']/personnel/list[\"']\)",
        ),
        (
            "personnel_read",
            r"^@mobile_api_bp\.get\([\"']/personnel/list[\"']\)",
            r"^# BYS360_MOBILE_V2_8_64_NOTIFICATION_ACTIONS",
        ),
        (
            "notifications",
            r"^# BYS360_MOBILE_V2_8_64_NOTIFICATION_ACTIONS",
            r"^def _mobile_support_status_label",
        ),
        (
            "support_survey_write",
            r"^def _mobile_support_status_label",
            r"^# BYS360_MOBILE_V2_8_43_PERSONNEL_ALL_API",
        ),
    ]
    ranges: list[tuple[int, int, str]] = []
    missing: list[str] = []
    for domain, start_pat, end_pat in specs:
        rng = find_range_to_marker(original, start_pat, end_pat)
        if rng is None:
            missing.append(domain)
            continue
        ranges.append((rng[0], rng[1], domain))
    if missing:
        return original, {}, missing
    # Aralıkların çakışmadığını güvenceye al.
    ranges.sort()
    for idx in range(1, len(ranges)):
        if ranges[idx][0] < ranges[idx - 1][1]:
            return original, {}, ["range_overlap"]
    modules: dict[str, str] = {}
    pieces: list[str] = []
    last = 0
    for start, end, domain in ranges:
        pieces.append(original[last:start])
        chunk = original[start:end]
        modules[domain] = module_text(domain, chunk)
        last = end
    pieces.append(original[last:])
    new_routes = "".join(pieces)
    new_routes = ensure_domain_imports(new_routes, list(modules.keys()))
    # Fazla boşlukları biraz toparla ama içeriği agresif değiştirme.
    new_routes = re.sub(r"\n{5,}", "\n\n\n", new_routes)
    return new_routes, modules, []


def collect_mobile_contract(root: Path) -> list[str]:
    paths = [root / "app" / "api" / "mobile" / "routes.py"]
    domain_dir = root / "app" / "api" / "mobile" / "domains"
    if domain_dir.exists():
        paths.extend(sorted(domain_dir.glob("*.py")))
    contract: list[str] = []
    for path in paths:
        if path.exists() and path.name != "__init__.py":
            contract.extend(route_fingerprint(read_text(path)))
    return sorted(contract)


def run(root: Path, mode: str) -> dict[str, Any]:
    root = root.resolve()
    routes = root / "app" / "api" / "mobile" / "routes.py"
    domain_dir = root / "app" / "api" / "mobile" / "domains"
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
    before_routes_lines = line_count(original)
    before_contract = collect_mobile_contract(root)
    before_route_count = len(before_contract)
    already_split = MARKER in original and domain_dir.exists()
    changed: list[str] = []
    missing: list[str] = []
    compile_results: list[dict[str, Any]] = []

    if mode in {"all", "write"} and not already_split:
        if P1B_MARKER not in original:
            # Yine de çalışabilir; fakat P1B olmadan riskli kabul ediyoruz.
            missing.append("p1b_marker_missing")
        new_routes, modules, split_missing = split_domains(original)
        missing.extend(split_missing)
        if not missing and modules:
            write_text(domain_dir / "__init__.py", "from __future__ import annotations\n\n# BYS360 P1C mobile API domain modules.\n")
            changed.append("app/api/mobile/domains/__init__.py")
            for domain, text in modules.items():
                target = domain_dir / f"{domain}.py"
                write_text(target, text)
                changed.append(str(target.relative_to(root)).replace("\\", "/"))
            write_text(routes, new_routes)
            changed.append("app/api/mobile/routes.py")

    current_routes = read_text(routes)
    after_contract = collect_mobile_contract(root)
    after_route_count = len(after_contract)
    route_contract_unchanged = before_contract == after_contract if before_contract else after_route_count > 0
    routes_py_lines_after = line_count(current_routes)
    domain_files = sorted([p for p in domain_dir.glob("*.py") if p.name != "__init__.py"]) if domain_dir.exists() else []

    if mode in {"all", "write"}:
        compile_targets = [routes] + domain_files
        compile_results = [compile_file(p) for p in compile_targets]
    compile_ok = all(item.get("ok") for item in compile_results) if compile_results else True

    checks = {
        "p1b_marker_present": P1B_MARKER in current_routes or (root / "app" / "api" / "mobile" / "shared.py").exists(),
        "domain_dir_exists": domain_dir.exists(),
        "domain_files_created": len(domain_files) >= 5,
        "route_contract_unchanged": route_contract_unchanged,
        "route_count_unchanged": before_route_count == after_route_count,
        "routes_py_reduced": routes_py_lines_after < before_routes_lines,
        "routes_py_under_1500_lines": routes_py_lines_after < 1500,
        "compile_ok": compile_ok,
    }
    data = {
        "ok": bool(not missing and all(checks.values())),
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "mode": mode,
        "changed_count": len(changed),
        "changed": changed,
        "already_split": already_split,
        "missing_or_blocked": missing,
        "before": {
            "routes_py_lines": before_routes_lines,
            "mobile_contract_route_count": before_route_count,
        },
        "after": {
            "routes_py_lines": routes_py_lines_after,
            "mobile_contract_route_count": after_route_count,
            "domain_files": [str(p.relative_to(root)).replace("\\", "/") for p in domain_files],
        },
        "checks": checks,
        "compile_results": compile_results,
        "report": str(report_dir / "BYS360_MOBILE_ROUTES_DOMAIN_SPLIT_P1C_REPORT.json"),
        "next_actions": [
            "P1D'de communication v1/v2 ve assistant endpoint blokları ayrı domain modüllerine taşınmalı.",
            "P1E'de personnel create/all ve KPI blokları ayrılarak routes.py 1000 satır altına indirilmeli.",
            "Her domain split sonrası app factory smoke ve mobil auth/dashboard smoke testleri çalıştırılmalıdır.",
        ],
    }
    write_outputs(report_dir, docs_dir, data)
    return data


def markdown(data: dict[str, Any]) -> str:
    before = data.get("before", {})
    after = data.get("after", {})
    checks = data.get("checks", {})
    lines = [
        "# BYS360 P1C Mobil API Domain Split Raporu",
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
        f"| Mobil route sözleşmesi önce | {before.get('mobile_contract_route_count', 0)} |",
        f"| Mobil route sözleşmesi sonra | {after.get('mobile_contract_route_count', 0)} |",
        "",
        "## Kontroller",
        "",
        "| Kontrol | Durum |",
        "|---|---:|",
    ]
    for key, value in checks.items():
        lines.append(f"| `{key}` | `{value}` |")
    domain_files = after.get("domain_files", [])
    if domain_files:
        lines.extend(["", "## Domain Dosyaları", ""])
        for item in domain_files:
            lines.append(f"- `{item}`")
    if data.get("missing_or_blocked"):
        lines.extend(["", "## Engelleyen Durumlar", ""])
        for item in data.get("missing_or_blocked", []):
            lines.append(f"- `{item}`")
    lines.extend([
        "",
        "## Not",
        "",
        "Bu faz, P1B ile küçültülen `app/api/mobile/routes.py` dosyasından düşük riskli ilk endpoint alanlarını domain modüllerine taşır. URL ve endpoint sözleşmesi korunur; route decorator sayısı değişmemelidir.",
    ])
    return "\n".join(lines) + "\n"


def write_outputs(report_dir: Path, docs_dir: Path, data: dict[str, Any]) -> None:
    report = report_dir / "BYS360_MOBILE_ROUTES_DOMAIN_SPLIT_P1C_REPORT.json"
    report_md = report_dir / "BYS360_MOBILE_ROUTES_DOMAIN_SPLIT_P1C_REPORT.md"
    docs_md = docs_dir / "BYS360_MOBILE_ROUTES_DOMAIN_SPLIT_P1C_REPORT.md"
    data["report"] = str(report)
    report.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    md = markdown(data)
    report_md.write_text(md, encoding="utf-8")
    docs_md.write_text(md, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--mode", choices=["audit", "write", "all"], default="all")
    args = parser.parse_args()
    data = run(Path(args.root), args.mode)
    print(json.dumps({
        "ok": data.get("ok"),
        "package": data.get("package"),
        "mode": data.get("mode"),
        "changed_count": data.get("changed_count"),
        "before": data.get("before"),
        "after": data.get("after"),
        "checks": data.get("checks"),
        "missing_or_blocked": data.get("missing_or_blocked"),
        "report": data.get("report"),
    }, ensure_ascii=False, indent=2))
    if not data.get("ok"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
