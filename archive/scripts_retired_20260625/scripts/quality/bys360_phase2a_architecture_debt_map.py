from __future__ import annotations

from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
import ast
import json
import os
import re
import subprocess

ROOT = Path(".").resolve()
QUALITY = ROOT / "reports" / "quality"
ARCH = ROOT / "reports" / "architecture"
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

OUT_JSON = ARCH / "BYS360_PHASE2A_ARCHITECTURE_DEBT_MAP.json"
OUT_MD = ARCH / "BYS360_PHASE2A_ARCHITECTURE_DEBT_MAP.md"

EXCLUDED_DIR_PARTS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "reports",
    "releases",
    "archive",
    "backups",
}

DOMAIN_KEYWORDS = {
    "performance": [
        "performans", "performance", "kpi", "hedef", "goal", "evaluation",
        "degerlendirme", "puan", "score", "period", "donem", "amir"
    ],
    "hr": [
        "personel", "personnel", "employee", "staff", "sicil", "izin",
        "birim", "unit", "departman", "department", "user", "profile"
    ],
    "communication": [
        "communication", "iletisim", "anket", "survey", "message", "mesaj",
        "mail", "email", "bildirim", "notification", "cic", "corporate_information"
    ],
    "admin": [
        "admin", "settings", "ayar", "role", "rol", "permission", "yetki",
        "rbac", "config", "system"
    ],
    "portal": [
        "portal", "news", "haber", "press", "basin", "people", "groups",
        "duvar", "feed"
    ],
    "feedback": [
        "feedback", "geri_bildirim", "geribildirim", "support", "destek",
        "ticket"
    ],
    "assistant": [
        "assistant", "asistan", "ai", "karar", "decision", "chat", "llm"
    ],
}


def should_skip(path: Path) -> bool:
    rel_parts = path.relative_to(ROOT).parts
    lowered = {part.lower() for part in rel_parts}
    return bool(EXCLUDED_DIR_PARTS & lowered)


def py_files() -> list[Path]:
    files = []
    for path in ROOT.rglob("*.py"):
        if should_skip(path):
            continue
        files.append(path)
    return sorted(files)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="ignore")


def run_cmd(cmd, timeout=1800):
    try:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            text=True,
            capture_output=True,
            encoding="utf-8",
            errors="ignore",
            env={
                **os.environ,
                "PYTHONIOENCODING": "utf-8",
                "BYS360_RUN_LEGACY_ARCHITECTURE_TESTS": "1",
            },
            timeout=timeout,
        )
        return {
            "cmd": " ".join(map(str, cmd)),
            "returncode": proc.returncode,
            "stdout": proc.stdout or "",
            "stderr": proc.stderr or "",
            "combined_tail": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-30000:],
        }
    except FileNotFoundError as exc:
        return {
            "cmd": " ".join(map(str, cmd)),
            "returncode": 127,
            "stdout": "",
            "stderr": str(exc),
            "combined_tail": str(exc)[-30000:],
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="ignore")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="ignore")
        return {
            "cmd": " ".join(map(str, cmd)),
            "returncode": 124,
            "stdout": stdout,
            "stderr": stderr,
            "combined_tail": (stdout + "\n" + stderr + "\nTIMEOUT")[-30000:],
        }


def parse_pytest_summary(text: str) -> dict:
    summary = {}
    pattern = r"(\d+)\s+(failed|passed|error|errors|skipped|deselected|warning|warnings)\b"
    for num, key in re.findall(pattern, text or "", flags=re.IGNORECASE):
        key = key.lower()
        if key == "error":
            key = "errors"
        if key == "warning":
            key = "warnings"
        summary[key] = int(num)

    for key in ["failed", "passed", "errors", "skipped", "deselected", "warnings"]:
        summary.setdefault(key, 0)

    return summary


def ast_parse(path: Path):
    try:
        return ast.parse(read_text(path), filename=str(path))
    except SyntaxError as exc:
        return exc
    except Exception as exc:
        return exc


def literal_or_repr(node) -> str | None:
    if isinstance(node, ast.Constant):
        return str(node.value)
    try:
        return ast.unparse(node)
    except Exception:
        return None


def dotted_name(node) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    if isinstance(node, ast.Call):
        return dotted_name(node.func)
    return ""


def infer_domain(*parts: str) -> str:
    haystack = " ".join(part or "" for part in parts).lower()

    scores = {}
    for domain, keywords in DOMAIN_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in haystack)
        if score:
            scores[domain] = score

    if not scores:
        return "main_or_unclear"

    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))[0][0]


def scan_blueprints_and_routes(files: list[Path]) -> dict:
    blueprints = []
    routes = []

    for path in files:
        tree = ast_parse(path)
        if not isinstance(tree, ast.Module):
            continue

        rel = path.relative_to(ROOT).as_posix()

        blueprint_vars = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                func_name = dotted_name(node.value.func)
                if func_name.endswith("Blueprint"):
                    var_names = [
                        target.id for target in node.targets
                        if isinstance(target, ast.Name)
                    ]
                    bp_name = None
                    url_prefix = None

                    if node.value.args:
                        bp_name = literal_or_repr(node.value.args[0])

                    for kw in node.value.keywords:
                        if kw.arg == "url_prefix":
                            url_prefix = literal_or_repr(kw.value)

                    for var in var_names:
                        blueprint_vars[var] = {
                            "var": var,
                            "name": bp_name,
                            "url_prefix": url_prefix,
                        }
                        blueprints.append({
                            "file": rel,
                            "line_no": node.lineno,
                            "var": var,
                            "name": bp_name,
                            "url_prefix": url_prefix,
                            "domain_guess": infer_domain(rel, var, bp_name or "", url_prefix or ""),
                        })

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            for dec in node.decorator_list:
                call = dec if isinstance(dec, ast.Call) else None
                if call is None:
                    continue

                func = call.func
                if not isinstance(func, ast.Attribute):
                    continue

                if func.attr not in {"route", "get", "post", "put", "patch", "delete"}:
                    continue

                decorator_owner = dotted_name(func.value)
                route_path = None
                methods = []

                if call.args:
                    route_path = literal_or_repr(call.args[0])

                for kw in call.keywords:
                    if kw.arg == "methods":
                        try:
                            methods_raw = ast.literal_eval(kw.value)
                            if isinstance(methods_raw, (list, tuple)):
                                methods = [str(x) for x in methods_raw]
                        except Exception:
                            methods = [literal_or_repr(kw.value) or "UNKNOWN"]

                bp_info = blueprint_vars.get(decorator_owner, {})
                bp_name = bp_info.get("name") or decorator_owner
                url_prefix = bp_info.get("url_prefix")

                domain_guess = infer_domain(
                    rel,
                    decorator_owner,
                    bp_name or "",
                    url_prefix or "",
                    route_path or "",
                    node.name,
                )

                routes.append({
                    "file": rel,
                    "line_no": node.lineno,
                    "function": node.name,
                    "decorator_owner": decorator_owner,
                    "blueprint_name": bp_name,
                    "url_prefix": url_prefix,
                    "route_path": route_path,
                    "methods": methods,
                    "domain_guess": domain_guess,
                    "is_main_or_unclear": domain_guess == "main_or_unclear" or bp_name in {"main", "main_bp", "bp"},
                })

    by_domain = Counter(route["domain_guess"] for route in routes)
    by_blueprint = Counter(str(route["blueprint_name"]) for route in routes)
    main_like_routes = [
        route for route in routes
        if route["is_main_or_unclear"]
        or str(route["blueprint_name"]).lower() in {"main", "main_bp", "bp"}
        or str(route["decorator_owner"]).lower() in {"main", "main_bp", "bp"}
    ]

    return {
        "blueprint_count": len(blueprints),
        "blueprints": blueprints,
        "route_count": len(routes),
        "routes": routes,
        "route_count_by_domain": dict(by_domain),
        "route_count_by_blueprint_top_50": dict(by_blueprint.most_common(50)),
        "main_like_route_count": len(main_like_routes),
        "main_like_routes_top_200": main_like_routes[:200],
    }


def scan_imports(files: list[Path]) -> dict:
    wildcard_imports = []
    import_from_count = 0

    for path in files:
        tree = ast_parse(path)
        if not isinstance(tree, ast.Module):
            continue

        rel = path.relative_to(ROOT).as_posix()

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                import_from_count += 1
                names = [alias.name for alias in node.names]
                if "*" in names:
                    wildcard_imports.append({
                        "file": rel,
                        "line_no": node.lineno,
                        "module": node.module,
                        "level": node.level,
                    })

    by_file = Counter(item["file"] for item in wildcard_imports)

    return {
        "import_from_count": import_from_count,
        "wildcard_import_count": len(wildcard_imports),
        "wildcard_imports": wildcard_imports,
        "wildcard_import_count_by_file": dict(by_file.most_common(80)),
    }


def scan_god_files(files: list[Path]) -> dict:
    rows = []

    for path in files:
        text = read_text(path)
        line_count = text.count("\n") + (1 if text else 0)
        if line_count >= 1000:
            rows.append({
                "file": path.relative_to(ROOT).as_posix(),
                "line_count": line_count,
                "domain_guess": infer_domain(path.relative_to(ROOT).as_posix()),
            })

    rows.sort(key=lambda item: item["line_count"], reverse=True)

    return {
        "god_file_threshold": 1000,
        "god_file_count": len(rows),
        "god_files": rows,
        "top_20": rows[:20],
    }


def scan_broad_excepts(files: list[Path]) -> dict:
    findings = []

    for path in files:
        tree = ast_parse(path)
        if not isinstance(tree, ast.Module):
            continue

        rel = path.relative_to(ROOT).as_posix()

        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    findings.append({
                        "file": rel,
                        "line_no": node.lineno,
                        "type": "bare_except",
                    })
                    continue

                type_name = dotted_name(node.type)
                if type_name in {"Exception", "BaseException"}:
                    findings.append({
                        "file": rel,
                        "line_no": node.lineno,
                        "type": type_name,
                    })

    by_file = Counter(item["file"] for item in findings)

    return {
        "broad_except_count": len(findings),
        "by_type": dict(Counter(item["type"] for item in findings)),
        "by_file_top_80": dict(by_file.most_common(80)),
        "findings_top_300": findings[:300],
        "ratchet_recommendation": {
            "current": len(findings),
            "phase2_first_target": max(0, len(findings) - 100),
            "phase2_safe_target": max(0, len(findings) - 250),
            "note": "Öneri: CI eşiği bir anda sıfıra değil, sprint bazlı düşürülmeli.",
        },
    }


def scan_cic_mail_hotspot(files: list[Path]) -> dict:
    candidates = []
    terms = [
        "mail", "email", "subject", "body", "template", "mesaj", "gönder",
        "gonder", "smtp", "recipient", "alıcı", "alici"
    ]

    for path in files:
        rel = path.relative_to(ROOT).as_posix()
        if "corporate_information_center" not in rel.lower() and "/cic/" not in rel.lower():
            continue

        text = read_text(path)
        line_count = text.count("\n") + (1 if text else 0)
        term_hits = {term: len(re.findall(re.escape(term), text, flags=re.IGNORECASE)) for term in terms}
        long_string_hits = len(re.findall(r'("""[\s\S]{120,?}"""|\'\'\'[\s\S]{120,?}\'\'\')', text))

        candidates.append({
            "file": rel,
            "line_count": line_count,
            "mail_term_hit_count": sum(term_hits.values()),
            "term_hits": term_hits,
            "long_triple_string_block_count_estimate": long_string_hits,
            "recommendation": (
                "Mail içerikleri ayrı content/template katmanına alınmalı."
                if sum(term_hits.values()) >= 20 or line_count >= 1000
                else "Düşük/orta yoğunluk; refactor önceliği rapora göre değerlendirilmeli."
            ),
        })

    candidates.sort(key=lambda item: (item["mail_term_hit_count"], item["line_count"]), reverse=True)

    return {
        "cic_hotspot_count": len(candidates),
        "cic_hotspots": candidates,
    }


def run_ruff_f405() -> dict:
    commands = [
        [str(ROOT / ".venv" / "Scripts" / "ruff.exe"), "check", ".", "--select", "F405", "--output-format=json"],
        ["ruff", "check", ".", "--select", "F405", "--output-format=json"],
    ]

    attempts = []

    for cmd in commands:
        result = run_cmd(cmd, timeout=1200)
        attempts.append({
            "cmd": result["cmd"],
            "returncode": result["returncode"],
            "tail": result["combined_tail"][-3000:],
        })

        raw = result["stdout"].strip()
        if not raw:
            continue

        try:
            data = json.loads(raw)
        except Exception:
            continue

        if isinstance(data, list):
            by_file = Counter()
            for item in data:
                filename = item.get("filename")
                if filename:
                    try:
                        rel = Path(filename).resolve().relative_to(ROOT).as_posix()
                    except Exception:
                        rel = str(filename)
                    by_file[rel] += 1

            return {
                "available": True,
                "returncode": result["returncode"],
                "f405_count": len(data),
                "by_file_top_80": dict(by_file.most_common(80)),
                "findings_top_200": data[:200],
                "attempts": attempts,
            }

    return {
        "available": False,
        "returncode": 127,
        "f405_count": None,
        "by_file_top_80": {},
        "findings_top_200": [],
        "attempts": attempts,
    }


def build_refactor_plan(route_scan: dict, import_scan: dict, god_scan: dict, except_scan: dict, cic_scan: dict) -> list[dict]:
    plan = []

    plan.append({
        "order": 1,
        "phase": "Faz 2B",
        "title": "Blueprint route split contract tests",
        "goal": "Route taşıma başlamadan önce mevcut endpoint/url/permission davranışını kilitlemek.",
        "risk": "low",
        "entry_condition": "S0Z green",
        "exit_evidence": "Route snapshot ve role/permission smoke testleri yeşil.",
    })

    plan.append({
        "order": 2,
        "phase": "Faz 2C",
        "title": "Wildcard import audit and first replacements",
        "goal": f"{import_scan['wildcard_import_count']} wildcard import için explicit import planı üretmek.",
        "risk": "medium",
        "entry_condition": "F405 haritası hazır",
        "exit_evidence": "İlk düşük riskli dosya grubunda F405 azalır, testler yeşil kalır.",
    })

    domain_counts = route_scan.get("route_count_by_domain", {})
    for domain in ["feedback", "assistant", "portal", "communication", "hr", "performance", "admin"]:
        count = domain_counts.get(domain, 0)
        if count <= 0:
            continue

        risk = "low" if domain in {"feedback", "assistant"} else "medium"
        if domain in {"performance", "admin"}:
            risk = "high"

        plan.append({
            "order": len(plan) + 1,
            "phase": "Faz 2D",
            "title": f"{domain} blueprint extraction candidate",
            "goal": f"{domain} alanındaki yaklaşık {count} route için ayrı blueprint/url_prefix hazırlığı.",
            "risk": risk,
            "entry_condition": "Route snapshot testi mevcut.",
            "exit_evidence": f"{domain} endpointleri aynı davranışla yeşil.",
        })

    if cic_scan["cic_hotspot_count"]:
        plan.append({
            "order": len(plan) + 1,
            "phase": "Faz 2E",
            "title": "Corporate Information Center mail content extraction",
            "goal": "E-posta konu/gövde içeriklerini servis dosyasından content/template katmanına taşımak.",
            "risk": "medium",
            "entry_condition": "Mail render smoke testi mevcut.",
            "exit_evidence": "Mail preview/test gönderim davranışı değişmeden yeşil.",
        })

    plan.append({
        "order": len(plan) + 1,
        "phase": "Faz 2F",
        "title": "Broad except ratchet",
        "goal": f"Broad except sayısını {except_scan['broad_except_count']} seviyesinden kontrollü düşürmek.",
        "risk": "medium",
        "entry_condition": "Mevcut sayı raporlandı.",
        "exit_evidence": "CI ratchet eşiği sprint bazlı düşer; testler yeşil kalır.",
    })

    return plan


def main() -> int:
    QUALITY.mkdir(parents=True, exist_ok=True)
    ARCH.mkdir(parents=True, exist_ok=True)

    files = py_files()

    route_scan = scan_blueprints_and_routes(files)
    import_scan = scan_imports(files)
    god_scan = scan_god_files(files)
    except_scan = scan_broad_excepts(files)
    cic_scan = scan_cic_mail_hotspot(files)
    ruff_f405 = run_ruff_f405()

    refactor_plan = build_refactor_plan(route_scan, import_scan, god_scan, except_scan, cic_scan)

    py = ROOT / ".venv" / "Scripts" / "python.exe"

    compile_result = run_cmd([
        str(py),
        "-m",
        "compileall",
        "-q",
        "config.py",
        "app",
        "scripts",
        "migrations",
    ])

    quality_smoke = run_cmd([
        str(py),
        "-m",
        "pytest",
        "tests/quality",
        "-m",
        "ci_safe",
        "-q",
        "-ra",
    ], timeout=900)

    default_pytest = run_cmd([
        str(py),
        "-m",
        "pytest",
        "-m",
        "not live and not realdb and not slow",
        "-q",
        "-ra",
    ], timeout=1800)

    quality_summary = parse_pytest_summary(quality_smoke["combined_tail"])
    default_summary = parse_pytest_summary(default_pytest["combined_tail"])

    ok = (
        compile_result["returncode"] == 0
        and quality_smoke["returncode"] == 0
        and default_pytest["returncode"] == 0
        and default_summary.get("failed", 0) == 0
        and default_summary.get("errors", 0) == 0
        and default_summary.get("passed", 0) >= 700
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "PHASE2A_ARCHITECTURE_DEBT_MAP",
        "mode": "inventory_only_no_code_change",
        "ok": ok,
        "decision": "PHASE2A_MAP_READY" if ok else "PHASE2A_REVIEW_REQUIRED",
        "python_file_count": len(files),
        "route_scan": route_scan,
        "import_scan": import_scan,
        "ruff_f405": ruff_f405,
        "god_file_scan": god_scan,
        "broad_except_scan": except_scan,
        "cic_mail_hotspot_scan": cic_scan,
        "refactor_plan": refactor_plan,
        "compileall_returncode": compile_result["returncode"],
        "pytest_quality_smoke_returncode": quality_smoke["returncode"],
        "pytest_quality_smoke_summary": quality_summary,
        "pytest_default_returncode": default_pytest["returncode"],
        "pytest_default_summary": default_summary,
        "next_action": "Faz 2B route snapshot ve blueprint extraction contract testleri yazılabilir." if ok else "Faz 2A raporu incelenmeli.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 Faz 2A Mimari Borç Haritası",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Python file count: {result['python_file_count']}",
        f"- Blueprint count: {route_scan['blueprint_count']}",
        f"- Route count: {route_scan['route_count']}",
        f"- Main-like route count: {route_scan['main_like_route_count']}",
        f"- Wildcard import count: {import_scan['wildcard_import_count']}",
        f"- Ruff F405 available: {ruff_f405['available']}",
        f"- Ruff F405 count: {ruff_f405['f405_count']}",
        f"- God-file count >=1000 lines: {god_scan['god_file_count']}",
        f"- Broad except count: {except_scan['broad_except_count']}",
        f"- CIC hotspot count: {cic_scan['cic_hotspot_count']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Pytest quality smoke returncode: {result['pytest_quality_smoke_returncode']}",
        f"- Pytest default returncode: {result['pytest_default_returncode']}",
        "",
        "## Route Count By Domain",
        "",
        "```json",
        json.dumps(route_scan["route_count_by_domain"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Route Count By Blueprint Top 50",
        "",
        "```json",
        json.dumps(route_scan["route_count_by_blueprint_top_50"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Wildcard Imports",
        "",
        "```json",
        json.dumps(import_scan["wildcard_imports"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Ruff F405 Summary",
        "",
        "```json",
        json.dumps({
            "available": ruff_f405["available"],
            "returncode": ruff_f405["returncode"],
            "f405_count": ruff_f405["f405_count"],
            "by_file_top_80": ruff_f405["by_file_top_80"],
        }, ensure_ascii=False, indent=2),
        "```",
        "",
        "## God Files Top 20",
        "",
        "```json",
        json.dumps(god_scan["top_20"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Broad Except Top Files",
        "",
        "```json",
        json.dumps({
            "broad_except_count": except_scan["broad_except_count"],
            "by_type": except_scan["by_type"],
            "by_file_top_80": except_scan["by_file_top_80"],
            "ratchet_recommendation": except_scan["ratchet_recommendation"],
        }, ensure_ascii=False, indent=2),
        "```",
        "",
        "## CIC Mail Hotspots",
        "",
        "```json",
        json.dumps(cic_scan["cic_hotspots"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Önerilen Refactor Sırası",
        "",
        "```json",
        json.dumps(refactor_plan, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Pytest Default Summary",
        "",
        "```json",
        json.dumps(default_summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("PHASE2A_REPORT_JSON:", OUT_JSON)
    print("PHASE2A_REPORT_MD:", OUT_MD)
    print("PHASE2A_PYTHON_FILE_COUNT:", result["python_file_count"])
    print("PHASE2A_BLUEPRINT_COUNT:", route_scan["blueprint_count"])
    print("PHASE2A_ROUTE_COUNT:", route_scan["route_count"])
    print("PHASE2A_MAIN_LIKE_ROUTE_COUNT:", route_scan["main_like_route_count"])
    print("PHASE2A_ROUTE_COUNT_BY_DOMAIN:", json.dumps(route_scan["route_count_by_domain"], ensure_ascii=False))
    print("PHASE2A_WILDCARD_IMPORT_COUNT:", import_scan["wildcard_import_count"])
    print("PHASE2A_RUFF_F405_AVAILABLE:", ruff_f405["available"])
    print("PHASE2A_RUFF_F405_COUNT:", ruff_f405["f405_count"])
    print("PHASE2A_GOD_FILE_COUNT:", god_scan["god_file_count"])
    print("PHASE2A_BROAD_EXCEPT_COUNT:", except_scan["broad_except_count"])
    print("PHASE2A_CIC_HOTSPOT_COUNT:", cic_scan["cic_hotspot_count"])
    print("PHASE2A_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("PHASE2A_PYTEST_QUALITY_SMOKE_RETURN_CODE:", result["pytest_quality_smoke_returncode"])
    print("PHASE2A_PYTEST_DEFAULT_RETURN_CODE:", result["pytest_default_returncode"])
    print("PHASE2A_PYTEST_DEFAULT_SUMMARY:", json.dumps(default_summary, ensure_ascii=False))
    print("PHASE2A_OK:", result["ok"])

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
