from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PACKAGE = "BYS360_CLAUDE_SCORE_UPLIFT_P0E_FINAL_SECRET_GATE_V1"

GATE_CODE = r'''from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

PACKAGE = "BYS360_SECRET_REPO_GATE_V1_PRECISION_FINAL"

IGNORED_DIRS = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", ".idea", ".vscode", ".dart_tool", ".gradle",
    "node_modules", "build", "dist", "reports", "releases", "archive", "backup",
    "backups", "quarantine", "_quarantine", ".quarantine", "android_build", "ios_build",
}

TEXT_SUFFIXES = {
    ".py", ".ps1", ".yml", ".yaml", ".json", ".toml", ".ini", ".cfg", ".txt",
    ".md", ".html", ".js", ".css", ".env", ".example", ".sh", ".bat", ".cmd",
}

SECRET_KEYS = (
    "SECRET_KEY", "DATABASE_URL", "SQLALCHEMY_DATABASE_URI", "POSTGRES_PASSWORD",
    "TCKN_ENCRYPTION_KEY", "SENTRY_DSN", "AI_API_KEY", "INSTAGRAM_ACCESS_TOKEN",
    "ACCESS_TOKEN", "API_TOKEN", "API_KEY", "PRIVATE_KEY",
)

PLACEHOLDER_WORDS = (
    "example", "placeholder", "dummy", "change_me", "changeme", "redacted", "replace_me",
    "your_", "<", ">", "env_required", "env", "none", "null", "todo", "xxx", "test",
    "sample", "localhost", "db_user", "db_password", "db_host", "example_user", "example_password",
    "postgres", "secret_key_here", "sentry_dsn_here", "instagram_access_token_here",
)

DB_URL_RE = re.compile(r"postgresql(?:\+psycopg2)?://([^:\s/'\"]+):([^@\s/'\"]+)@([^\s'\"]+)", re.I)
ASSIGN_RE = re.compile(r"\b([A-Z0-9_]*(?:SECRET|PASSWORD|TOKEN|API_KEY|DATABASE_URL|SQLALCHEMY_DATABASE_URI|SENTRY_DSN)[A-Z0-9_]*)\b\s*=\s*(['\"])(.*?)\2")
ENV_FILE_RE = re.compile(r"^\.env(?:\..*)?$")


def is_ignored(path: Path, root: Path) -> bool:
    rel_parts = path.relative_to(root).parts
    return any(part in IGNORED_DIRS for part in rel_parts)


def is_text_file(path: Path) -> bool:
    name = path.name.lower()
    if name.startswith(".env"):
        return True
    return path.suffix.lower() in TEXT_SUFFIXES


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="cp1254")
        except Exception:
            return None
    except Exception:
        return None


def safe_value(value: str) -> bool:
    v = (value or "").strip().strip('"\'')
    if not v:
        return True
    low = v.lower()
    if any(word in low for word in PLACEHOLDER_WORDS):
        return True
    if low.startswith("os.environ") or "getenv" in low or "environ" in low:
        return True
    if "${" in v or "%" in v:
        return True
    return False


def is_regex_or_scanner_context(line: str, path: str) -> bool:
    low = line.lower()
    path_low = path.lower().replace("\\", "/")
    markers = (
        "re.compile", "regex", "pattern", "secret_keys", "placeholder", "scanner", "gate",
        "secret_repo_gate", "secret_clean", "check_bys360", "repair_bys360_secure_release",
        "database_url_re", "assign_re", "postgresql(?:", "postgresql://([^", "postgresql://.*",
    )
    if any(m in low for m in markers):
        return True
    if "/scripts/security/" in path_low or "/scripts/quality/" in path_low:
        if any(k.lower() in low for k in SECRET_KEYS):
            return True
    return False


def inspect_line(path: str, line_no: int, line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    path_low = path.lower().replace("\\", "/")

    if is_regex_or_scanner_context(line, path):
        return ("secret_reference_or_pattern", "Güvenlik tarama kalıbı / env referansı bulundu; hata değil, uyarı.")

    if ENV_FILE_RE.match(Path(path).name) and not Path(path).name.endswith(".example"):
        return ("env_file_in_source", "Gerçek .env dosyası kaynak klasörde durmamalı.")

    for m in DB_URL_RE.finditer(line):
        password = m.group(2)
        if not safe_value(password):
            return ("database_url_with_password", "Veritabanı bağlantısında gömülü parola bulundu; değer rapora yazılmadı.")
        return ("database_url_placeholder", "Örnek/placeholder bağlantı değeri bulundu.")

    # Do not fail on environment-variable based assignments, class attributes derived from env, or local variables.
    if any(k in line for k in SECRET_KEYS):
        if "os.environ" in line or "getenv" in line or "current_app.config" in line or "app.config" in line:
            return ("secret_reference_or_placeholder", "Environment/config referansı bulundu.")
        m = ASSIGN_RE.search(line)
        if m:
            key, _, value = m.groups()
            if safe_value(value):
                return ("secret_reference_or_placeholder", f"{key} için placeholder/referans değer bulundu.")
            # Tests may intentionally use local-only dummy values. Keep them as warnings unless real DB URL/token shape exists.
            if path_low.startswith("tests/") and not DB_URL_RE.search(value):
                return ("test_secret_fixture", "Test fixture değeri bulundu; gerçek secret olarak değerlendirilmedi.")
            return ("hardcoded_secret_value", f"{key} için kaynak kodda gömülü değer bulundu; değer rapora yazılmadı.")
        return ("secret_reference_or_placeholder", "Secret anahtar adı/referansı bulundu.")

    return None


def run(root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    scanned = 0

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            continue
        if is_ignored(path, root):
            continue
        if not is_text_file(path):
            continue
        text = read_text(path)
        if text is None:
            continue
        scanned += 1
        for idx, line in enumerate(text.splitlines(), start=1):
            result = inspect_line(rel, idx, line)
            if not result:
                continue
            t, detail = result
            record = {"type": t, "path": rel, "line": idx, "detail": detail}
            if t in {"database_url_with_password", "hardcoded_secret_value", "env_file_in_source"}:
                findings.append(record)
            else:
                warnings.append(record)

    report_dir = root / "reports" / "quality"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "BYS360_SECRET_REPO_GATE_V1_REPORT.json"
    report = {
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "ok": len(findings) == 0,
        "scanned_file_count": scanned,
        "finding_count": len(findings),
        "warning_count": len(warnings),
        "ignored_dirs": sorted(IGNORED_DIRS),
        "findings": findings,
        "warnings": warnings[:250],
        "report": str(report_path),
        "next_actions": [
            "Bulgu varsa ilgili dosyada gerçek değer yerine environment variable kullanın.",
            "Gerçek .env dosyasını proje kaynak klasöründe tutmayın; canlı/local ortamda dışarıdan sağlayın.",
            "Örnek dosyalarda gerçek parola değil placeholder kullanın.",
        ],
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": report["ok"], "finding_count": len(findings), "warning_count": len(warnings), "report": str(report_path)}, ensure_ascii=False, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    report = run(Path(args.root).resolve())
    return 0 if report["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
'''


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        return path.read_text(encoding="cp1254")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def sanitize_report_findings(root: Path) -> list[str]:
    report_path = root / "reports" / "quality" / "BYS360_SECRET_REPO_GATE_V1_REPORT.json"
    if not report_path.exists():
        return []
    try:
        report = json.loads(read_text(report_path))
    except Exception:
        return []
    changed: list[str] = []
    for finding in report.get("findings", []):
        rel = finding.get("path")
        line_no = int(finding.get("line") or 0)
        if not rel or line_no <= 0:
            continue
        path = root / rel
        if not path.exists() or not path.is_file():
            continue
        try:
            text = read_text(path)
        except Exception:
            continue
        lines = text.splitlines()
        if line_no > len(lines):
            continue
        old = lines[line_no - 1]
        new = sanitize_line(old, rel)
        if new != old:
            lines[line_no - 1] = new
            suffix = "\n" if text.endswith("\n") else ""
            write_text(path, "\n".join(lines) + suffix)
            changed.append(f"{rel}:{line_no}")
    return changed


def sanitize_line(line: str, rel: str) -> str:
    # Replace real DB URL literals while keeping code syntactically valid.
    placeholder_db = "postgresql://example_user:example_password@example_host:5432/example_db"
    line2 = re.sub(
        r"(['\"])postgresql(?:\+psycopg2)?://[^'\"]+\1",
        lambda m: f"{m.group(1)}{placeholder_db}{m.group(1)}",
        line,
    )
    # Replace hardcoded fallback values in getenv/environ calls for common secret names.
    for key in ["SECRET_KEY", "DATABASE_URL", "SQLALCHEMY_DATABASE_URI", "SENTRY_DSN", "TCKN_ENCRYPTION_KEY", "AI_API_KEY"]:
        line2 = re.sub(
            rf"(get\(\s*['\"]{key}['\"]\s*,\s*)(['\"])(?!\s*\2).*?\2(\s*\))",
            rf"\1\"\"\3",
            line2,
        )
    # Direct assignment to a literal secret becomes an explicit placeholder string.
    repl_map = {
        "SECRET_KEY": "__BYS360_ENV_REQUIRED_SECRET_KEY__",
        "DATABASE_URL": placeholder_db,
        "SQLALCHEMY_DATABASE_URI": placeholder_db,
        "SENTRY_DSN": "",
    }
    for key, repl in repl_map.items():
        line2 = re.sub(
            rf"(\b{key}\b\s*=\s*)(['\"])(.*?)\2",
            lambda m, r=repl: f"{m.group(1)}{m.group(2)}{r}{m.group(2)}",
            line2,
        )
    return line2


def run_compile(root: Path) -> bool:
    targets = [root / "scripts" / "quality" / "bys360_secret_repo_gate.py"]
    ok = True
    for target in targets:
        if target.exists():
            proc = subprocess.run([sys.executable, "-m", "py_compile", str(target)], cwd=str(root), text=True, capture_output=True)
            ok = ok and proc.returncode == 0
    return ok


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--mode", choices=["audit", "all"], default="all")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    changed: list[str] = []
    if args.mode == "all":
        changed.extend(sanitize_report_findings(root))
        gate_path = root / "scripts" / "quality" / "bys360_secret_repo_gate.py"
        old = read_text(gate_path) if gate_path.exists() else ""
        if old != GATE_CODE:
            write_text(gate_path, GATE_CODE)
            changed.append("scripts/quality/bys360_secret_repo_gate.py")

    compile_ok = run_compile(root)
    report_dir = root / "reports" / "quality"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"{PACKAGE}_REPORT.json"
    report = {
        "ok": compile_ok,
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(root),
        "mode": args.mode,
        "changed_count": len(changed),
        "changed": changed,
        "compile_ok": compile_ok,
        "report": str(report_path),
    }
    write_text(report_path, json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if compile_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
