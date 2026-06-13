from __future__ import annotations

from pathlib import Path
import argparse
import json
import re
import urllib.request
import urllib.error
from datetime import datetime

ROOT = Path(".").resolve()
OUT_JSON = Path("reports/live_readiness/BYS360_A7D_LOCAL_SMOKE_TEST_CONTRACT.json")
OUT_MD = Path("reports/live_readiness/BYS360_A7D_LOCAL_SMOKE_TEST_CONTRACT.md")

ROUTE_CONTRACTS = [
    {
        "name": "Ana sayfa / giriş yönlendirme",
        "path": "/",
        "expected_statuses": [200, 302, 401, 403],
        "evidence_terms": ["@main", "route(\"/\"", "route('/')", "index"],
        "files": ["app/main_handlers", "app/main.py", "app/routes.py", "app/__init__.py"],
        "severity": "high",
    },
    {
        "name": "Login",
        "path": "/login",
        "expected_statuses": [200, 302],
        "evidence_terms": ["login", "auth"],
        "files": ["app/auth", "app/templates"],
        "severity": "high",
    },
    {
        "name": "Dashboard",
        "path": "/dashboard",
        "expected_statuses": [200, 302, 401, 403],
        "evidence_terms": ["dashboard"],
        "files": ["app/dashboard", "app/templates/dashboard"],
        "severity": "high",
    },
    {
        "name": "Portal",
        "path": "/portal",
        "expected_statuses": [200, 302, 401, 403],
        "evidence_terms": ["portal"],
        "files": ["app/portal", "app/templates/portal"],
        "severity": "medium",
    },
    {
        "name": "Geri Bildirim",
        "path": "/feedback/gonder",
        "expected_statuses": [200, 302, 401, 403],
        "evidence_terms": ["feedback", "gonder", "geri"],
        "files": ["app/templates/feedback", "app/support", "app/communication", "app"],
        "severity": "medium",
    },
    {
        "name": "404 hata şablonu",
        "path": "/__bys360_missing_smoke_page__",
        "expected_statuses": [404],
        "evidence_terms": ["404"],
        "files": ["app/templates/errors/404.html"],
        "severity": "medium",
    },
    {
        "name": "500 hata şablonu",
        "path": "/__bys360_500_template_check__",
        "expected_statuses": [],
        "evidence_terms": ["500"],
        "files": ["app/templates/errors/500.html"],
        "severity": "medium",
    },
    {
        "name": "Static CSS",
        "path": "/static/css",
        "expected_statuses": [200, 301, 302, 403, 404],
        "evidence_terms": [".css"],
        "files": ["app/static/css"],
        "severity": "low",
    },
    {
        "name": "Mobil API kökü",
        "path": "/api/mobile",
        "expected_statuses": [200, 302, 401, 403, 404, 405],
        "evidence_terms": ["mobile_api_bp", "api/mobile", "mobile"],
        "files": ["app/api/mobile"],
        "severity": "medium",
    },
]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig", errors="ignore")
    except Exception:
        return ""


def collect_text(paths: list[str]) -> tuple[bool, str, list[str]]:
    existing = []
    chunks = []

    for item in paths:
        p = Path(item)
        if p.is_file():
            existing.append(str(p).replace("\\", "/"))
            chunks.append(read_text(p))
        elif p.is_dir():
            existing.append(str(p).replace("\\", "/"))
            for child in p.rglob("*"):
                if child.is_file() and child.suffix.lower() in {".py", ".html", ".jinja", ".jinja2", ".js", ".css"}:
                    chunks.append(read_text(child))
        else:
            # glob-like fallback
            matches = list(ROOT.glob(item))
            for match in matches:
                if match.exists():
                    existing.append(str(match).replace("\\", "/"))
                    if match.is_file():
                        chunks.append(read_text(match))

    return bool(existing), "\n".join(chunks), sorted(set(existing))[:40]


def http_check(base_url: str, path: str, timeout: int = 8) -> dict:
    url = base_url.rstrip("/") + path
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BYS360-A7D-Smoke/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {
                "url": url,
                "ok": True,
                "status": int(resp.status),
                "error": "",
            }
    except urllib.error.HTTPError as exc:
        return {
            "url": url,
            "ok": True,
            "status": int(exc.code),
            "error": "",
        }
    except Exception as exc:
        return {
            "url": url,
            "ok": False,
            "status": None,
            "error": repr(exc),
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="", help="Örn: http://127.0.0.1:5000. Boşsa HTTP smoke çalışmaz.")
    args = parser.parse_args()

    findings = []

    for contract in ROUTE_CONTRACTS:
        exists, text, existing_paths = collect_text(contract["files"])
        lower_text = text.lower()
        term_hits = [term for term in contract["evidence_terms"] if term.lower() in lower_text]
        contract_ok = exists and bool(term_hits)
        if any(str(x).replace('\\', '/').endswith(('app/templates/errors/404.html', 'app/templates/errors/500.html')) for x in contract.get('files', [])):
            contract_ok = exists

        http_result = None
        http_ok = None

        if args.base_url.strip():
            http_result = http_check(args.base_url.strip(), contract["path"])
            expected = contract["expected_statuses"]
            if expected:
                http_ok = http_result["ok"] and http_result["status"] in expected
            else:
                http_ok = http_result["ok"]

        final_ok = contract_ok if http_ok is None else (contract_ok and http_ok)

        findings.append({
            "name": contract["name"],
            "path": contract["path"],
            "severity": contract["severity"],
            "contract_ok": contract_ok,
            "evidence_paths_found": exists,
            "existing_paths": existing_paths,
            "term_hits": term_hits,
            "expected_statuses": contract["expected_statuses"],
            "http_result": http_result,
            "http_ok": http_ok,
            "ok": final_ok,
        })

    failed = [f for f in findings if not f["ok"] and f["severity"] in {"high", "medium"}]
    warnings = [f for f in findings if not f["ok"] and f["severity"] == "low"]
    passed = [f for f in findings if f["ok"]]

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A7D_LOCAL_SMOKE_TEST_CONTRACT",
        "base_url": args.base_url,
        "http_mode": bool(args.base_url.strip()),
        "ok": len(failed) == 0,
        "passed": len(passed),
        "warnings": len(warnings),
        "failed": len(failed),
        "findings": findings,
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 Aşama 7D Local Smoke Test Sözleşmesi",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Özet",
        "",
        f"- OK: {result['ok']}",
        f"- HTTP modu: {result['http_mode']}",
        f"- Base URL: `{result['base_url']}`",
        f"- Passed: {result['passed']}",
        f"- Warnings: {result['warnings']}",
        f"- Failed: {result['failed']}",
        "",
        "## Smoke Kalemleri",
        "",
    ]

    for f in findings:
        lines.extend([
            f"### {'PASS' if f['ok'] else 'FAIL'} — {f['name']}",
            f"- Yol: `{f['path']}`",
            f"- Seviye: {f['severity']}",
            f"- Contract OK: {f['contract_ok']}",
            f"- Kanıt yolları bulundu: {f['evidence_paths_found']}",
            f"- Terim eşleşmeleri: {f['term_hits']}",
            f"- Dosya kanıtları: {f['existing_paths']}",
        ])

        if f["http_result"] is not None:
            lines.extend([
                f"- HTTP URL: `{f['http_result']['url']}`",
                f"- HTTP status: `{f['http_result']['status']}`",
                f"- HTTP OK: {f['http_ok']}",
                f"- HTTP hata: `{f['http_result']['error']}`",
            ])

        lines.append("")

    lines.extend([
        "## Karar",
        "",
    ])

    if result["ok"]:
        lines.append("A7D sonucu: Local smoke test sözleşmesi oluşturuldu ve kritik/orta seviye smoke kalemlerinde blocker bulunmadı.")
    else:
        lines.append("A7D sonucu: Kritik/orta seviye smoke kalemlerinde eksik var; canlı öncesi tamamlanmalı.")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("A7D_SMOKE_CONTRACT_JSON:", OUT_JSON)
    print("A7D_SMOKE_CONTRACT_MD:", OUT_MD)
    print("A7D_OK:", result["ok"])
    print("A7D_HTTP_MODE:", result["http_mode"])
    print("A7D_PASSED:", result["passed"])
    print("A7D_WARNINGS:", result["warnings"])
    print("A7D_FAILED:", result["failed"])

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
