from __future__ import annotations

import argparse
import json
import os
import py_compile
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PACKAGE = "BYS360_CLAUDE_SCORE_UPLIFT_P1D_MOBILE_ROUTES_COMM_ASSISTANT_SPLIT"
MARKER = "# BYS360_P1D_MOBILE_ROUTES_COMM_ASSISTANT_SPLIT"
P1C_MARKER = "# BYS360_P1C_MOBILE_ROUTES_DOMAIN_SPLIT"
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
    values: list[str] = []
    for m in ROUTE_RULE_RE.finditer(text):
        values.append(re.sub(r"\s+", " ", m.group(0).strip()))
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


def module_text(domain: str, body: str) -> str:
    clean = body.strip("\n") + "\n"
    return (
        "from __future__ import annotations\n\n"
        f"{MARKER}\n"
        f"# Domain: {domain}\n"
        "# Bu modül mobil API endpoint sözleşmesini domain bazlı taşır.\n"
        "# URL/endpoint isimleri korunur; ortak yardımcılar shared.py içinden gelir.\n\n"
        "from app.api.mobile.shared import *  # noqa: F401,F403 - BYS360 P1D domain endpoint importu\n\n\n"
        + clean
        + "\n"
    )


def ensure_domain_imports(routes_text: str, domains: list[str]) -> str:
    if MARKER in routes_text:
        return routes_text
    imports = [
        f"from app.api.mobile.domains.{domain} import *  # noqa: F401,F403 - P1D domain route registration"
        for domain in domains
    ]
    block = MARKER + "\n" + "\n".join(imports) + "\n"
    if P1C_MARKER in routes_text:
        # P1C import bloğunun hemen ardından ekle.
        lines = routes_text.splitlines()
        insert_at = None
        for idx, line in enumerate(lines):
            if P1C_MARKER in line:
                insert_at = idx + 1
                continue
            if insert_at is not None:
                if line.startswith("from app.api.mobile.domains.") or not line.strip():
                    insert_at = idx + 1
                    continue
                break
        if insert_at is not None:
            lines[insert_at:insert_at] = ["", block.rstrip("\n"), ""]
            return "\n".join(lines) + "\n"
    shared_import = "from app.api.mobile.shared import *  # noqa: F401,F403 - P1B endpoint sözleşmesi için bilinçli facade import"
    if shared_import in routes_text:
        return routes_text.replace(shared_import, shared_import + "\n\n" + block, 1)
    return block + "\n" + routes_text


def split_domains(original: str) -> tuple[str, dict[str, str], list[str]]:
    # P1D: P1C sonrası kalan iletişim/asistan bloklarını taşır.
    # Personel create/all ve KPI blokları P1E'ye bırakılır.
    specs = [
        (
            "communication_v1_write",
            r"^# BYS360_MOBILE_V2_8_46_COMMUNICATION_MESSAGES_API",
            r"^# BYS360_MOBILE_V2_8_48_COMMUNICATION_V2_API",
        ),
        (
            "communication_v2_write",
            r"^# BYS360_MOBILE_V2_8_48_COMMUNICATION_V2_API",
            r"^# BYS360_MOBILE_V2_8_49_ASSISTANT_CHAT_API",
        ),
        (
            "assistant_chat",
            r"^# BYS360_MOBILE_V2_8_49_ASSISTANT_CHAT_API",
            r"^# BYS360_MOBILE_V2_8_53_KPI_TARGET_MANAGEMENT_API",
        ),
    ]
    ranges: list[tuple[int, int, str]] = []
    missing: list[str] = []
    for domain, start_pat, end_pat in specs:
        rng = find_range(original, start_pat, end_pat)
        if rng is None:
            missing.append(domain)
            continue
        ranges.append((rng[0], rng[1], domain))
    if missing:
        return original, {}, missing
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


def run_subprocess(root: Path, command: list[str], env_extra: dict[str, str] | None = None) -> dict[str, Any]:
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    try:
        proc = subprocess.run(
            command,
            cwd=str(root),
            text=True,
            capture_output=True,
            timeout=90,
            env=env,
        )
        return {
            "returncode": proc.returncode,
            "stdout_tail": proc.stdout[-4000:],
            "stderr_tail": proc.stderr[-4000:],
            "ok": proc.returncode == 0,
        }
    except Exception as exc:  # pragma: no cover - raporlama amaçlı
        return {"returncode": -1, "stdout_tail": "", "stderr_tail": str(exc), "ok": False}


def parse_last_json(text: str) -> dict[str, Any]:
    matches = list(re.finditer(r"\{", text or ""))
    for match in reversed(matches):
        chunk = text[match.start():].strip()
        try:
            return json.loads(chunk)
        except Exception:
            continue
    return {}


def run(root: Path, mode: str, run_app_factory_smoke: bool, run_secret_gate: bool) -> dict[str, Any]:
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
    already_split = MARKER in original and (domain_dir / "assistant_chat.py").exists()
    changed: list[str] = []
    missing: list[str] = []

    if mode in {"all", "write"} and not already_split:
        if P1C_MARKER not in original:
            missing.append("p1c_marker_missing")
        new_routes, modules, split_missing = split_domains(original)
        missing.extend(split_missing)
        if not missing and modules:
            init_path = domain_dir / "__init__.py"
            if not init_path.exists():
                write_text(init_path, "from __future__ import annotations\n\n# BYS360 mobile API domain modules.\n")
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

    compile_targets = [routes] + domain_files
    compile_results = [compile_file(p) for p in compile_targets]
    compile_ok = all(item.get("ok") for item in compile_results)

    app_factory_smoke: dict[str, Any] | None = None
    if run_app_factory_smoke:
        app_factory_smoke = run_subprocess(
            root,
            [sys.executable, "-c", "from app import create_app; app=create_app(); print('APP_FACTORY_OK')"],
            env_extra={
                "APP_ENV": os.environ.get("APP_ENV", "development"),
                "FLASK_ENV": os.environ.get("FLASK_ENV", "development"),
            },
        )

    secret_gate: dict[str, Any] | None = None
    if run_secret_gate:
        gate = root / "scripts" / "quality" / "bys360_secret_repo_gate.py"
        if gate.exists():
            secret_gate = run_subprocess(root, [sys.executable, str(gate), "--root", str(root)])
            parsed = parse_last_json(secret_gate.get("stdout_tail", ""))
            secret_gate["parsed"] = parsed
            secret_gate["ok"] = bool(parsed.get("ok", secret_gate.get("ok")))
        else:
            secret_gate = {"ok": False, "returncode": -1, "stdout_tail": "", "stderr_tail": "secret gate script bulunamadı", "parsed": {}}

    checks = {
        "p1c_marker_present": P1C_MARKER in current_routes or (domain_dir / "auth.py").exists(),
        "domain_dir_exists": domain_dir.exists(),
        "p1d_domain_files_created": all((domain_dir / f"{name}.py").exists() for name in ["communication_v1_write", "communication_v2_write", "assistant_chat"]),
        "route_contract_unchanged": route_contract_unchanged,
        "route_count_unchanged": before_route_count == after_route_count,
        "routes_py_reduced": routes_py_lines_after < before_routes_lines or already_split,
        "routes_py_under_1000_lines": routes_py_lines_after < 1000,
        "compile_ok": compile_ok,
        "app_factory_ok": True if not run_app_factory_smoke else bool(app_factory_smoke and app_factory_smoke.get("ok")),
        "secret_gate_ok": True if not run_secret_gate else bool(secret_gate and secret_gate.get("ok")),
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
        "app_factory_smoke": app_factory_smoke,
        "secret_gate": secret_gate,
        "report": str(report_dir / "BYS360_MOBILE_ROUTES_COMM_ASSISTANT_SPLIT_P1D_REPORT.json"),
        "next_actions": [
            "P1E'de personnel create/all ve KPI blokları ayrılarak routes.py 700 satır altına indirilmeli.",
            "P1D sonrası mobil auth/dashboard/communication/assistant smoke testleri çalıştırılmalıdır.",
            "Domain split zincirinde URL/endpoint sözleşmesi korunmaya devam etmelidir.",
        ],
    }
    write_outputs(report_dir, docs_dir, data)
    return data


def markdown(data: dict[str, Any]) -> str:
    before = data.get("before", {})
    after = data.get("after", {})
    checks = data.get("checks", {})
    lines = [
        "# BYS360 P1D Mobil API İletişim ve Asistan Domain Split Raporu",
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
        "Bu faz, P1C sonrası kalan iletişim V1/V2 ve BYS360 Asistanı mobil endpoint bloklarını domain modüllerine taşır. URL/endpoint sözleşmesi korunur; canlandırma app factory smoke ve secret gate ile desteklenir.",
    ])
    return "\n".join(lines) + "\n"


def write_outputs(report_dir: Path, docs_dir: Path, data: dict[str, Any]) -> None:
    report = report_dir / "BYS360_MOBILE_ROUTES_COMM_ASSISTANT_SPLIT_P1D_REPORT.json"
    report_md = report_dir / "BYS360_MOBILE_ROUTES_COMM_ASSISTANT_SPLIT_P1D_REPORT.md"
    docs_md = docs_dir / "BYS360_MOBILE_ROUTES_COMM_ASSISTANT_SPLIT_P1D_REPORT.md"
    data["report"] = str(report)
    report.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    md = markdown(data)
    report_md.write_text(md, encoding="utf-8")
    docs_md.write_text(md, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--mode", choices=["audit", "write", "all"], default="all")
    parser.add_argument("--run-app-factory-smoke", action="store_true")
    parser.add_argument("--run-secret-gate", action="store_true")
    args = parser.parse_args()
    data = run(Path(args.root), args.mode, args.run_app_factory_smoke, args.run_secret_gate)
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
