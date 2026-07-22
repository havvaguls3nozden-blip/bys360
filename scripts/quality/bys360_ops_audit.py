from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "build",
    "dist",
    "htmlcov",
    "backups",
    "backup",
    "reports",
    "logs",
    "overlays",
    "releases",
    "archive",
}

SECRET_PATTERNS = [
    re.compile(r"(?i)(password|passwd|secret|token|api[_-]?key)\s*=\s*['\"][^'\"]{8,}['\"]"),
    re.compile(r"(?i)postgres(?:ql)?://[^\s:@]+:[^\s@]+@"),
    re.compile(r"(?i)redis://:[^\s@]+@"),
]

@dataclass
class FileFinding:
    path: str
    print_calls: int = 0
    broad_excepts: int = 0
    bare_excepts: int = 0
    syntax_error: str | None = None
    possible_secret_hits: int = 0


def iter_files(root: Path, suffixes: Iterable[str]) -> Iterable[Path]:
    suffix_set = set(suffixes)
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in suffix_set:
            yield path

def iter_source_files(root: Path, source_paths: list[str] | None, suffixes: Iterable[str]) -> Iterable[Path]:
    """Yield files from explicit source paths while preserving project-root reports.

    CI budgets must measure the living application code, not backup/release/script
    accumulation.  When --source-paths is omitted the historical full-root scan is
    preserved for backwards compatibility.
    """
    if not source_paths:
        yield from iter_files(root, suffixes)
        return

    suffix_set = set(suffixes)
    seen: set[Path] = set()
    for raw in source_paths:
        candidate = (root / raw).resolve()
        if not candidate.exists():
            continue
        if candidate.is_file():
            if candidate.suffix.lower() in suffix_set and candidate not in seen:
                seen.add(candidate)
                yield candidate
            continue
        for path in candidate.rglob("*"):
            if not path.is_file():
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.suffix.lower() in suffix_set and path not in seen:
                seen.add(path)
                yield path

def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def analyze_python(path: Path, root: Path) -> FileFinding:
    finding = FileFinding(path=rel(path, root))
    try:
        text = path.read_text(encoding="utf-8-sig")
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        finding.syntax_error = f"line {exc.lineno}: {exc.msg}"
        return finding
    except UnicodeDecodeError as exc:
        finding.syntax_error = f"decode error: {exc}"
        return finding

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "print":
                finding.print_calls += 1
        elif isinstance(node, ast.ExceptHandler):
            if node.type is None:
                finding.bare_excepts += 1
            elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
                finding.broad_excepts += 1
            elif isinstance(node.type, ast.Tuple) and any(
                isinstance(item, ast.Name) and item.id == "Exception" for item in node.type.elts
            ):
                finding.broad_excepts += 1
    return finding


def scan_possible_secrets(path: Path, root: Path) -> FileFinding | None:
    try:
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
    except OSError:
        return None
    hits = sum(len(pattern.findall(text)) for pattern in SECRET_PATTERNS)
    if hits:
        return FileFinding(path=rel(path, root), possible_secret_hits=hits)
    return None


def command_exists(name: str) -> bool:
    try:
        subprocess.run([name, "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except OSError:
        return False
    return True


def build_report(root: Path, mode: str, source_paths: list[str] | None = None) -> dict:
    py_findings = [analyze_python(p, root) for p in iter_source_files(root, source_paths, [".py"])]
    secret_findings = []
    for p in iter_files(root, [".py", ".env", ".txt", ".toml", ".yml", ".yaml", ".ini"]):
        if p.name in {".env", ".env.docker.local"}:
            # Real env files should not be committed; report existence separately instead of reading values.
            continue
        sf = scan_possible_secrets(p, root)
        if sf:
            secret_findings.append(sf)

    required_files = [
        "Dockerfile",
        ".dockerignore",
        "docker-compose.yml",
        "docker/gunicorn.conf.py",
        "docker/entrypoint.sh",
        ".env.docker.example",
        ".github/workflows/bys360-ci.yml",
    ]
    required_status = {name: (root / name).exists() for name in required_files}

    env_risks = {
        ".env_exists_in_project_root": (root / ".env").exists(),
        ".venv_exists_in_project_root": (root / ".venv").exists(),
    }

    return {
        "package": "BYS360_OPS_HARDENING_V1",
        "mode": mode,
        "generated_at": datetime.now(UTC).isoformat(),
        "root": str(root),
        "required_files": required_status,
        "env_risks": env_risks,
        "totals": {
            "python_files": len(py_findings),
            "syntax_errors": sum(1 for f in py_findings if f.syntax_error),
            "print_calls": sum(f.print_calls for f in py_findings),
            "broad_except_exception": sum(f.broad_excepts for f in py_findings),
            "bare_except": sum(f.bare_excepts for f in py_findings),
            "possible_secret_files": len(secret_findings),
            "possible_secret_hits": sum(f.possible_secret_hits for f in secret_findings),
        },
        "top_print_files": [asdict(f) for f in sorted(py_findings, key=lambda x: x.print_calls, reverse=True)[:30] if f.print_calls],
        "top_broad_except_files": [asdict(f) for f in sorted(py_findings, key=lambda x: x.broad_excepts + x.bare_excepts, reverse=True)[:30] if f.broad_excepts or f.bare_excepts],
        "syntax_error_files": [asdict(f) for f in py_findings if f.syntax_error][:50],
        "possible_secret_files": [asdict(f) for f in secret_findings[:50]],
        "tooling": {
            "docker_available": command_exists("docker"),
            "git_available": command_exists("git"),
        },
    }


def to_markdown(report: dict) -> str:
    totals = report["totals"]
    lines = [
        "# BYS360 Operasyonel Sağlamlaştırma V1 Raporu",
        "",
        f"Üretim zamanı: `{report['generated_at']}`",
        f"Proje kökü: `{report['root']}`",
        "",
        "## Özet",
        "",
        "| Kontrol | Değer |",
        "|---|---:|",
        f"| Python dosyası | {totals['python_files']} |",
        f"| Syntax hatası | {totals['syntax_errors']} |",
        f"| print() çağrısı | {totals['print_calls']} |",
        f"| except Exception | {totals['broad_except_exception']} |",
        f"| bare except | {totals['bare_except']} |",
        f"| Olası secret dosyası | {totals['possible_secret_files']} |",
        f"| Olası secret eşleşmesi | {totals['possible_secret_hits']} |",
        "",
        "## Operasyon Dosyaları",
        "",
        "| Dosya | Durum |",
        "|---|---|",
    ]
    for name, ok in report["required_files"].items():
        lines.append(f"| `{name}` | {'VAR' if ok else 'EKSİK'} |")

    lines.extend([
        "",
        "## Kök Dizin Riskleri",
        "",
        "| Risk | Durum |",
        "|---|---|",
    ])
    for name, exists in report["env_risks"].items():
        lines.append(f"| `{name}` | {'VAR — canlı/teslim paketinden çıkarılmalı' if exists else 'Yok'} |")

    if report["syntax_error_files"]:
        lines.extend(["", "## Syntax Hataları", "", "| Dosya | Hata |", "|---|---|"])
        for f in report["syntax_error_files"]:
            lines.append(f"| `{f['path']}` | {f['syntax_error']} |")

    lines.extend(["", "## En Çok print() İçeren Dosyalar", "", "| Dosya | print() |", "|---|---:|"])
    for f in report["top_print_files"][:15]:
        lines.append(f"| `{f['path']}` | {f['print_calls']} |")

    lines.extend(["", "## En Çok except Exception İçeren Dosyalar", "", "| Dosya | except Exception |", "|---|---:|"])
    for f in report["top_broad_except_files"][:15]:
        lines.append(f"| `{f['path']}` | {f['broad_excepts'] + f['bare_excepts']} |")

    lines.extend([
        "",
        "## Uygulama Notu",
        "",
        "Bu paket Docker/CI/CD eksikliğini kapatır ve print/except borcunu ölçülebilir hale getirir. ",
        "`except Exception` temizliği tek seferde otomatik yapılmamalıdır; dosya dosya, davranış bozmadan ve log seviyesi belirlenerek azaltılmalıdır.",
    ])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="BYS360 operational readiness audit")
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument("--mode", default="local", help="local/ci/audit")
    parser.add_argument("--report", default="reports/quality/BYS360_OPS_HARDENING_V1_REPORT.md")
    parser.add_argument("--json-report", default="reports/quality/BYS360_OPS_HARDENING_V1_REPORT.json")
    parser.add_argument("--max-print", type=int, default=None)
    parser.add_argument("--max-broad-except", type=int, default=None)
    parser.add_argument("--source-paths", nargs="*", default=None, help="Python source paths used for print/except budgets")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report = build_report(root, args.mode, args.source_paths)

    report_path = root / args.report
    json_path = root / args.json_report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(to_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"BYS360_OPS_AUDIT_REPORT={report_path}")
    print(f"BYS360_OPS_AUDIT_JSON={json_path}")
    print(json.dumps(report["totals"], ensure_ascii=False))

    failures: list[str] = []
    missing = [name for name, ok in report["required_files"].items() if not ok]
    if missing:
        failures.append("Eksik operasyon dosyaları: " + ", ".join(missing))
    if report["totals"]["syntax_errors"]:
        failures.append("Syntax hatası var")
    if args.strict and report["env_risks"].get(".env_exists_in_project_root"):
        failures.append("Proje kökünde .env var; temiz teslim paketine girmemeli")
    if args.max_print is not None and report["totals"]["print_calls"] > args.max_print:
        failures.append(f"print() bütçesi aşıldı: {report['totals']['print_calls']} > {args.max_print}")
    if args.max_broad_except is not None and report["totals"]["broad_except_exception"] > args.max_broad_except:
        failures.append(f"except Exception bütçesi aşıldı: {report['totals']['broad_except_exception']} > {args.max_broad_except}")

    if failures:
        for item in failures:
            print("BYS360_OPS_AUDIT_FAIL=" + item, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
