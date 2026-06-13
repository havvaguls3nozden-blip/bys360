from __future__ import annotations

import argparse
import ast
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

EXCLUDED_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules",
    "dist", "build", "backups", "backup", ".mypy_cache", ".ruff_cache",
}
COMMENT_MARKERS = ("BYS360_CLAUDE_", "Claude", "CLAUDE_")
TECHNICAL_UI_TERMS = (
    "workflow state", "authorized_scope", "phase sync", "Faz 3 senkronu", "endpoint", "raw error",
    "traceback", "exception", "debug", "unauthorized_scope",
)

@dataclass
class Finding:
    severity: str
    code: str
    path: str
    message: str
    line: int | None = None


def iter_files(root: Path, suffixes: tuple[str, ...]):
    for p in root.rglob("*"):
        if any(part in EXCLUDED_DIRS for part in p.parts):
            continue
        if p.is_file() and p.suffix.lower() in suffixes:
            yield p


def rel(root: Path, p: Path) -> str:
    try:
        return str(p.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def count_lines(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())
    except Exception:
        return 0


def scan_large_files(root: Path, findings: list[Finding], soft_limit: int, hard_limit: int) -> None:
    for p in iter_files(root, (".py", ".dart", ".html", ".js", ".css")):
        lines = count_lines(p)
        rp = rel(root, p)
        if lines >= hard_limit:
            findings.append(Finding("P1", "LARGE_FILE_HARD", rp, f"Dosya {lines} satır. Domain bazlı parçalama planlanmalı."))
        elif lines >= soft_limit:
            findings.append(Finding("P2", "LARGE_FILE_SOFT", rp, f"Dosya {lines} satır. Bakım kolaylığı için izlenmeli."))


def scan_silent_except(root: Path, findings: list[Finding]) -> None:
    for p in iter_files(root, (".py",)):
        text = p.read_text(encoding="utf-8", errors="ignore")
        try:
            tree = ast.parse(text)
        except SyntaxError as exc:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (scripts/quality/bys360_quality_audit_v1.py:66)")
            findings.append(Finding("P0", "PY_SYNTAX_ERROR", rel(root, p), f"Python sözdizimi okunamadı: {exc}", exc.lineno))
            continue
        lines = text.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    findings.append(Finding("P0", "SILENT_EXCEPT_PASS", rel(root, p), "except bloğu hatayı loglamadan pass ediyor.", node.lineno))
                # except block only contains continue/pass-like no logging
                body_src = "\n".join("\n".join(lines[getattr(stmt, "lineno", node.lineno)-1:getattr(stmt, "end_lineno", getattr(stmt, "lineno", node.lineno))]) for stmt in node.body)
                if "logger" not in body_src and "log" not in body_src and "raise" not in body_src:
                    if any(isinstance(stmt, (ast.Pass, ast.Continue)) for stmt in node.body):
                        findings.append(Finding("P1", "EXCEPT_WITHOUT_LOG", rel(root, p), "except bloğunda log/raise yok; canlı tanılama zayıflayabilir.", node.lineno))


def scan_comments(root: Path, findings: list[Finding]) -> None:
    for p in iter_files(root, (".py", ".dart", ".html", ".js", ".css", ".ps1", ".md")):
        text = p.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(text.splitlines(), start=1):
            if any(marker in line for marker in COMMENT_MARKERS):
                findings.append(Finding("P2", "CLAUDE_OR_DEV_MARKER", rel(root, p), "Geliştirme/Claude etiketi ADR veya changelog'a taşınmalı.", i))


def scan_technical_ui_terms(root: Path, findings: list[Finding]) -> None:
    pattern = re.compile("|".join(re.escape(x) for x in TECHNICAL_UI_TERMS), re.IGNORECASE)
    for p in iter_files(root, (".html", ".dart", ".js")):
        text = p.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                findings.append(Finding("P1", "TECHNICAL_UI_TERM", rel(root, p), "Kullanıcı yüzünde teknik ifade olabilir; kurumsal Türkçe metne çevrilmeli.", i))


def scan_repair_scripts(root: Path, findings: list[Finding]) -> None:
    script_dirs = [root / "scripts", root / "tools" / "scripts"]
    repair_files: list[Path] = []
    for d in script_dirs:
        if d.exists():
            repair_files.extend([p for p in d.rglob("*.ps1") if re.search(r"repair|fix|hotfix", p.name, re.I)])
            repair_files.extend([p for p in d.rglob("*.py") if re.search(r"repair|fix|hotfix", p.name, re.I)])
    if len(repair_files) >= 40:
        findings.append(Finding("P1", "MANY_REPAIR_SCRIPTS", "scripts", f"{len(repair_files)} repair/fix/hotfix scripti bulundu; CI ve arşiv planı yapılmalı."))
    elif repair_files:
        findings.append(Finding("INFO", "REPAIR_SCRIPT_COUNT", "scripts", f"{len(repair_files)} repair/fix/hotfix scripti bulundu."))


def scan_tests(root: Path, findings: list[Finding]) -> None:
    tests_dir = root / "tests"
    if not tests_dir.exists():
        findings.append(Finding("P0", "TESTS_DIR_MISSING", "tests", "tests klasörü bulunamadı."))
        return
    test_files = list(tests_dir.rglob("test_*.py"))
    if not test_files:
        findings.append(Finding("P0", "NO_TEST_FILES", "tests", "test_*.py dosyası bulunamadı."))
        return
    integration_like = [p for p in test_files if re.search(r"integration|e2e|flow|scenario|api|db|auth|performance", str(p), re.I)]
    ratio = len(integration_like) / max(1, len(test_files))
    if ratio < 0.20:
        findings.append(Finding("P1", "LOW_INTEGRATION_TEST_RATIO", "tests", f"{len(test_files)} test dosyasının yalnızca {len(integration_like)} tanesi entegrasyon/e2e akışına benziyor."))


def summarize(findings: list[Finding]) -> dict[str, int]:
    out = {"P0": 0, "P1": 0, "P2": 0, "INFO": 0}
    for f in findings:
        out[f.severity] = out.get(f.severity, 0) + 1
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="BYS360 10/10 kalite denetimi")
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--json-out", default="")
    ap.add_argument("--soft-line-limit", type=int, default=900)
    ap.add_argument("--hard-line-limit", type=int, default=1500)
    ap.add_argument("--fail-on", choices=["P0", "P1", "P2", "never"], default="P0")
    args = ap.parse_args()

    root = Path(args.project_root).resolve()
    findings: list[Finding] = []
    scan_large_files(root, findings, args.soft_line_limit, args.hard_line_limit)
    scan_silent_except(root, findings)
    scan_comments(root, findings)
    scan_technical_ui_terms(root, findings)
    scan_repair_scripts(root, findings)
    scan_tests(root, findings)

    data = {"project_root": str(root), "summary": summarize(findings), "findings": [asdict(f) for f in findings]}
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print("BYS360_QUALITY_10_10_AUDIT_SUMMARY")
    print(json.dumps(data["summary"], ensure_ascii=False))
    for f in findings[:80]:
        line = f":{f.line}" if f.line else ""
        print(f"[{f.severity}] {f.code} {f.path}{line} - {f.message}")
    if len(findings) > 80:
        print(f"... {len(findings)-80} ek bulgu JSON raporunda.")

    fail_levels = {
        "P0": {"P0"},
        "P1": {"P0", "P1"},
        "P2": {"P0", "P1", "P2"},
        "never": set(),
    }[args.fail_on]
    return 1 if any(f.severity in fail_levels for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
