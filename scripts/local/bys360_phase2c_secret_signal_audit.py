from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable

TEXT_SUFFIXES = {
    ".py", ".ps1", ".html", ".htm", ".js", ".css", ".json", ".md", ".txt",
    ".yml", ".yaml", ".ini", ".cfg", ".toml", ".env", ".example", ".sql",
}
EXCLUDE_DIR_NAMES = {
    ".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache", ".mypy_cache",
    "node_modules", "dist", "build", ".ruff_cache",
}
EXCLUDE_TOP_LEVEL = {
    "archive", "backups", "dist_secure", "instance", "logs",
}
EXCLUDE_REPORT_PREFIXES = (
    "reports/tech_debt_phase1",
    "reports/tech_debt_phase2",
    "reports/tech_debt_phase2_after_2a",
    "reports/tech_debt_phase2a",
    "reports/tech_debt_phase2b",
    "reports/tech_debt_phase2b_after_archive",
)

KEYWORD_RE = re.compile(
    r"(?i)\b("
    r"secret|secret_key|password|passwd|pwd|token|api[_-]?key|access[_-]?key|private[_-]?key|"
    r"client[_-]?secret|database_url|dsn|smtp|authorization|bearer|credential|csrf"
    r")\b"
)

ASSIGNMENT_RE = re.compile(
    r"""(?ix)
    (?P<key>[A-Za-z0-9_.-]*(?:secret|secret_key|password|passwd|pwd|token|api[_-]?key|access[_-]?key|private[_-]?key|client[_-]?secret|database_url|dsn|authorization|bearer|credential)[A-Za-z0-9_.-]*)
    \s*(?:=|:)\s*
    (?P<quote>["'])
    (?P<value>[^"']{4,})
    (?P=quote)
    """
)

ENV_ACCESS_RE = re.compile(r"(?i)(os\.environ|getenv|current_app\.config|config\.get|settings\.get)")
PLACEHOLDER_RE = re.compile(
    r"(?i)(your_|change[_-]?me|example|placeholder|dummy|test|fake|sample|xxx|xxxx|<.*>|"
    r"secret_key_here|replace|not[_-]?set|none|null|todo|dev|local|localhost)"
)
SAFE_CONTEXT_RE = re.compile(
    r"(?i)(csrf|secret_like|secret_repo_gate|secret signal|audit|scanner|classification|"
    r"token_matrix|role_token|auth_guard|pytest|test_|mock|fixture|expected|assert|"
    r"permission|authorization_required|endpoint|route|menu|label|placeholder)"
)

HIGH_RISK_FILE_RE = re.compile(r"(?i)(\.env$|config\.py$|settings\.py$|production|prod|deploy|live|mail|smtp|security|auth)")
COMMENT_RE = re.compile(r"^\s*(#|//|\*|<!--)")

def relpath(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()

def is_excluded(path: Path, root: Path) -> bool:
    rel = relpath(path, root)
    parts = rel.split("/")
    if any(p in EXCLUDE_DIR_NAMES for p in parts):
        return True
    if parts and parts[0] in EXCLUDE_TOP_LEVEL:
        return True
    if any(rel.startswith(prefix) for prefix in EXCLUDE_REPORT_PREFIXES):
        return True
    return False

def looks_text(path: Path) -> bool:
    if path.suffix.lower() in TEXT_SUFFIXES:
        return True
    if path.name.lower() in {".env", ".env.example", "dockerfile"}:
        return True
    return False

def shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = Counter(value)
    length = len(value)
    return -sum((c / length) * math.log2(c / length) for c in counts.values())

def redact(value: str) -> str:
    if len(value) <= 8:
        return "***"
    return value[:3] + "***" + value[-3:]

def redacted_line(line: str) -> str:
    def repl(m: re.Match) -> str:
        return f"{m.group('key')}={m.group('quote')}{redact(m.group('value'))}{m.group('quote')}"
    return ASSIGNMENT_RE.sub(repl, line.strip())

def classify_line(rel: str, line_no: int, line: str) -> tuple[str, str, str, str, str]:
    stripped = line.strip()
    keyword = KEYWORD_RE.search(line)
    signal = keyword.group(1).lower() if keyword else "unknown"

    m = ASSIGNMENT_RE.search(line)
    if m:
        key = m.group("key")
        value = m.group("value")
        entropy = shannon_entropy(value)
        if PLACEHOLDER_RE.search(value):
            return ("false_positive", "P2", signal, "assignment uses placeholder/example/local value", redacted_line(line))
        if ENV_ACCESS_RE.search(line):
            return ("false_positive", "P2", signal, "configuration reads from environment/config instead of hardcoding", redacted_line(line))
        if len(value) >= 20 and entropy >= 3.2:
            severity = "P0" if HIGH_RISK_FILE_RE.search(rel) else "P1"
            return ("needs_review", severity, signal, f"literal assignment resembles secret; entropy={entropy:.2f}", redacted_line(line))
        if len(value) >= 12 and HIGH_RISK_FILE_RE.search(rel):
            return ("needs_review", "P1", signal, "literal value in security/config/live-related file", redacted_line(line))
        return ("false_positive", "P2", signal, "short or low-entropy literal assignment", redacted_line(line))

    if COMMENT_RE.search(line):
        return ("false_positive", "P3", signal, "comment/documentation mention", stripped[:240])
    if SAFE_CONTEXT_RE.search(line):
        return ("false_positive", "P3", signal, "safe audit/test/UI/security-term context", stripped[:240])
    if ENV_ACCESS_RE.search(line):
        return ("false_positive", "P2", signal, "environment/config access without literal value", stripped[:240])
    if HIGH_RISK_FILE_RE.search(rel):
        return ("needs_review", "P2", signal, "security/config/live file mentions secret-like term", stripped[:240])
    return ("false_positive", "P3", signal, "keyword mention without literal secret", stripped[:240])

def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file() and not is_excluded(path, root) and looks_text(path):
            try:
                if path.stat().st_size <= 1_500_000:
                    yield path
            except OSError:
                continue

def read_text(path: Path) -> str:
    data = path.read_bytes()
    for enc in ("utf-8", "utf-8-sig", "cp1254", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")

def audit(root: Path) -> dict:
    rows: list[dict] = []
    files_scanned = 0
    files_with_signals = 0
    for path in iter_files(root):
        files_scanned += 1
        rel = relpath(path, root)
        try:
            text = read_text(path)
        except Exception as exc:
            rows.append({
                "classification": "read_error",
                "severity": "P2",
                "signal": "read_error",
                "rel": rel,
                "line_no": 0,
                "reason": str(exc),
                "context": "",
            })
            continue
        file_hit = False
        for idx, line in enumerate(text.splitlines(), start=1):
            if not KEYWORD_RE.search(line):
                continue
            file_hit = True
            cls, sev, sig, reason, ctx = classify_line(rel, idx, line)
            rows.append({
                "classification": cls,
                "severity": sev,
                "signal": sig,
                "rel": rel,
                "line_no": idx,
                "reason": reason,
                "context": ctx,
            })
        if file_hit:
            files_with_signals += 1

    by_class = Counter(row["classification"] for row in rows)
    by_severity = Counter(row["severity"] for row in rows)
    by_signal = Counter(row["signal"] for row in rows)
    top_files = Counter(row["rel"] for row in rows if row["classification"] == "needs_review").most_common(50)
    p0 = [r for r in rows if r["severity"] == "P0"]
    review = [r for r in rows if r["classification"] == "needs_review"]

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "files_scanned": files_scanned,
        "files_with_signals": files_with_signals,
        "total_signals": len(rows),
        "by_classification": dict(by_class),
        "by_severity": dict(by_severity),
        "by_signal": dict(by_signal),
        "needs_review_count": len(review),
        "p0_count": len(p0),
        "top_needs_review_files": [{"rel": rel, "count": count} for rel, count in top_files],
        "rows": rows,
    }

def write_outputs(result: dict, output_root: Path) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    json_path = output_root / "BYS360_TECH_DEBT_PHASE2C_SECRET_SIGNALS_AUDIT.json"
    csv_path = output_root / "BYS360_TECH_DEBT_PHASE2C_SECRET_SIGNALS_AUDIT.csv"
    md_path = output_root / "BYS360_TECH_DEBT_PHASE2C_SECRET_SIGNALS_AUDIT.md"

    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    rows = result["rows"]
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["classification", "severity", "signal", "rel", "line_no", "reason", "context"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    review_rows = [r for r in rows if r["classification"] == "needs_review"]
    p0_rows = [r for r in review_rows if r["severity"] == "P0"]

    lines: list[str] = []
    lines.append("# BYS360 Teknik Borç Faz 2C — Secret Sinyali Sınıflandırma Audit Raporu")
    lines.append("")
    lines.append(f"Oluşturma zamanı: `{result['generated_at']}`")
    lines.append(f"Proje kökü: `{result['project_root']}`")
    lines.append("")
    lines.append("## Yönetici Özeti")
    lines.append("")
    lines.append("| Ölçüm | Değer |")
    lines.append("|---|---:|")
    lines.append(f"| Taranan dosya | {result['files_scanned']} |")
    lines.append(f"| Secret-benzeri sinyal geçen dosya | {result['files_with_signals']} |")
    lines.append(f"| Toplam sinyal | {result['total_signals']} |")
    lines.append(f"| İnceleme gerektiren sinyal | {result['needs_review_count']} |")
    lines.append(f"| P0 sinyal | {result['p0_count']} |")
    lines.append("")
    lines.append("## Sınıflandırma")
    lines.append("")
    lines.append("| Sınıf | Adet |")
    lines.append("|---|---:|")
    for key, val in sorted(result["by_classification"].items()):
        lines.append(f"| {key} | {val} |")
    lines.append("")
    lines.append("## Öncelik")
    lines.append("")
    lines.append("| Öncelik | Adet |")
    lines.append("|---|---:|")
    for key, val in sorted(result["by_severity"].items()):
        lines.append(f"| {key} | {val} |")
    lines.append("")
    lines.append("## P0 İnceleme Adayları")
    lines.append("")
    if not p0_rows:
        lines.append("P0 seviyesinde literal secret adayı bulunmadı.")
    else:
        lines.append("| Dosya | Satır | Sinyal | Sebep | Bağlam |")
        lines.append("|---|---:|---|---|---|")
        for row in p0_rows[:80]:
            ctx = row["context"].replace("|", "\\|")
            reason = row["reason"].replace("|", "\\|")
            lines.append(f"| `{row['rel']}` | {row['line_no']} | {row['signal']} | {reason} | `{ctx}` |")
    lines.append("")
    lines.append("## İnceleme Gerektiren İlk 120 Sinyal")
    lines.append("")
    if not review_rows:
        lines.append("İnceleme gerektiren sinyal bulunmadı.")
    else:
        lines.append("| Öncelik | Dosya | Satır | Sinyal | Sebep | Bağlam |")
        lines.append("|---|---|---:|---|---|---|")
        for row in review_rows[:120]:
            ctx = row["context"].replace("|", "\\|")
            reason = row["reason"].replace("|", "\\|")
            lines.append(f"| {row['severity']} | `{row['rel']}` | {row['line_no']} | {row['signal']} | {reason} | `{ctx}` |")
    lines.append("")
    lines.append("## En Çok İnceleme Adayı Olan Dosyalar")
    lines.append("")
    lines.append("| Dosya | Adet |")
    lines.append("|---|---:|")
    for item in result["top_needs_review_files"][:30]:
        lines.append(f"| `{item['rel']}` | {item['count']} |")
    lines.append("")
    lines.append("## Not")
    lines.append("")
    lines.append("Bu audit dosya davranışını değiştirmez. Sadece secret-benzeri metinleri gerçek risk / false-positive ayrımı için sınıflandırır. CSV'de bağlamlar redakte edilir; gerçek değerler rapora açık yazılmaz.")
    md_path.write_text("\n".join(lines), encoding="utf-8")

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    root = Path(args.project_root).resolve()
    output_root = Path(args.output_root).resolve()
    result = audit(root)
    write_outputs(result, output_root)
    print(f"OK: Phase2C secret signals markdown: {output_root / 'BYS360_TECH_DEBT_PHASE2C_SECRET_SIGNALS_AUDIT.md'}")
    print(f"OK: Phase2C secret signals json: {output_root / 'BYS360_TECH_DEBT_PHASE2C_SECRET_SIGNALS_AUDIT.json'}")
    print(f"OK: Phase2C secret signals csv: {output_root / 'BYS360_TECH_DEBT_PHASE2C_SECRET_SIGNALS_AUDIT.csv'}")
    print("OK: Kod davranışı değiştirilmedi; sadece secret-benzeri sinyal sınıflandırması yapıldı.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())