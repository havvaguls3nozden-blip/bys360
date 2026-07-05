from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable

TEXT_EXTENSIONS = {".py", ".ps1", ".bat", ".cmd", ".sh", ".md", ".txt", ".json", ".yaml", ".yml"}

ARCHIVE_HINTS = (
    "repair_",
    "hotfix",
    "overlay",
    "fix_",
    "patch",
    "temp",
    "tmp",
    "legacy",
    "backup",
    "old_",
    "once",
    "oneoff",
)

REVIEW_HINTS = (
    "live",
    "production",
    "prod",
    "security",
    "secret",
    "csrf",
    "migration",
    "migrate",
    "db",
    "database",
    "deploy",
    "release",
    "rollback",
)

KEEP_HINTS = (
    "quality_gate",
    "secret_repo_gate",
    "tech_debt_phase",
    "phase2a",
    "phase2b",
    "score100",
    "score10",
    "audit",
    "inventory",
)

TECH_PATTERNS = {
    "print_calls": re.compile(r"(?m)^\s*print\s*\("),
    "broad_except": re.compile(r"except\s+(Exception|BaseException)\s*[: as]|except\s*:"),
    "hardcoded_localhost": re.compile(r"localhost|127\.0\.0\.1|0\.0\.0\.0|http://", re.I),
    "secret_like_text": re.compile(r"secret|password|token|api[_-]?key|private[_-]?key|authorization", re.I),
    "subprocess_shell": re.compile(r"shell\s*=\s*True|Invoke-Expression|iex\b", re.I),
    "dangerous_remove": re.compile(r"Remove-Item|shutil\.rmtree|os\.remove|del\s+", re.I),
}

@dataclass
class ScriptItem:
    rel: str
    directory: str
    name: str
    suffix: str
    size_kb: float
    lines: int
    action: str
    reason: str
    risk_score: int
    print_calls: int
    broad_except: int
    hardcoded_localhost: int
    secret_like_text: int
    subprocess_shell: int
    dangerous_remove: int


def safe_read_text(path: Path) -> str:
    try:
        data = path.read_bytes()
    except OSError:
        return ""
    if b"\x00" in data[:2048]:
        return ""
    for enc in ("utf-8", "utf-8-sig", "cp1254", "latin-1"):
        try:
            return data.decode(enc, errors="replace")
        except Exception:
            continue
    return ""


def iter_script_files(scripts_root: Path) -> Iterable[Path]:
    if not scripts_root.exists():
        return []
    for path in scripts_root.rglob("*"):
        if path.is_file():
            yield path


def classify(rel: str, suffix: str, metrics: dict[str, int]) -> tuple[str, str, int]:
    rel_l = rel.replace("\\", "/").lower()
    name_l = Path(rel_l).name
    parent = Path(rel_l).parts[0] if Path(rel_l).parts else ""

    risk = 0
    risk += metrics.get("subprocess_shell", 0) * 5
    risk += metrics.get("dangerous_remove", 0) * 3
    risk += metrics.get("secret_like_text", 0)
    risk += metrics.get("hardcoded_localhost", 0)
    risk += metrics.get("broad_except", 0)

    if any(h in rel_l for h in KEEP_HINTS):
        return "tooling_keep", "phase/quality/audit tooling; keep in repo unless replaced", risk

    if parent in {"windows", "local", "quality"} and not any(h in rel_l for h in ARCHIVE_HINTS):
        return "tooling_keep", "general tooling directory; keep or review after active list is approved", risk

    if any(h in rel_l for h in REVIEW_HINTS):
        return "review", "live/security/db/deploy/release related script; manual review before moving", risk

    if any(h in rel_l for h in ARCHIVE_HINTS):
        return "archive_candidate", "one-off repair/hotfix/overlay style script; candidate for external archive", risk

    if suffix.lower() in {".ps1", ".bat", ".cmd", ".sh"}:
        return "review", "shell script; manual review before archive", risk

    return "review", "unclassified script; needs owner/use decision", risk


def audit(project_root: Path, output_root: Path, mode: str) -> dict:
    scripts_root = project_root / "scripts"
    output_root.mkdir(parents=True, exist_ok=True)

    items: list[ScriptItem] = []
    by_dir = Counter()
    by_suffix = Counter()
    by_action = Counter()
    totals = Counter()

    for path in iter_script_files(scripts_root):
        rel = path.relative_to(scripts_root).as_posix()
        suffix = path.suffix.lower()
        size_kb = round(path.stat().st_size / 1024, 1)
        text = safe_read_text(path) if suffix in TEXT_EXTENSIONS and path.stat().st_size <= 2_000_000 else ""
        lines = text.count("\n") + (1 if text else 0)
        metrics = {key: len(pattern.findall(text)) for key, pattern in TECH_PATTERNS.items()}
        action, reason, risk_score = classify(rel, suffix, metrics)
        top_dir = rel.split("/")[0] if "/" in rel else "(root)"
        by_dir[top_dir] += 1
        by_suffix[suffix or "(none)"] += 1
        by_action[action] += 1
        totals.update(metrics)
        items.append(ScriptItem(
            rel=f"scripts/{rel}",
            directory=top_dir,
            name=path.name,
            suffix=suffix or "(none)",
            size_kb=size_kb,
            lines=lines,
            action=action,
            reason=reason,
            risk_score=risk_score,
            print_calls=metrics["print_calls"],
            broad_except=metrics["broad_except"],
            hardcoded_localhost=metrics["hardcoded_localhost"],
            secret_like_text=metrics["secret_like_text"],
            subprocess_shell=metrics["subprocess_shell"],
            dangerous_remove=metrics["dangerous_remove"],
        ))

    items.sort(key=lambda x: (x.action != "review", x.action != "archive_candidate", -x.risk_score, x.rel.lower()))

    csv_path = output_root / "BYS360_TECH_DEBT_PHASE2B_SCRIPTS_INVENTORY.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(items[0]).keys()) if items else ["rel"])
        writer.writeheader()
        for item in items:
            writer.writerow(asdict(item))

    result = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "mode": mode,
        "project_root": str(project_root),
        "scripts_total": len(items),
        "by_action": dict(by_action),
        "by_directory": dict(by_dir),
        "by_suffix": dict(by_suffix),
        "pattern_totals": dict(totals),
        "top_risk": [asdict(item) for item in sorted(items, key=lambda x: (-x.risk_score, x.rel.lower()))[:40]],
        "archive_candidates": [asdict(item) for item in items if item.action == "archive_candidate"],
        "review_candidates": [asdict(item) for item in items if item.action == "review"],
    }

    json_path = output_root / "BYS360_TECH_DEBT_PHASE2B_SCRIPTS_INVENTORY.json"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md_path = output_root / "BYS360_TECH_DEBT_PHASE2B_SCRIPTS_INVENTORY.md"
    md = []
    md.append("# BYS360 Teknik Borç Faz 2B — Scripts Envanteri\n")
    md.append(f"Oluşturma zamanı: `{result['created_at']}`  ")
    md.append(f"Mod: `{mode}`  ")
    md.append(f"Proje kökü: `{project_root}`\n")
    md.append("## Yönetici Özeti\n")
    md.append("| Ölçüm | Değer |\n|---|---:|")
    md.append(f"| scripts toplam dosya | {len(items)} |")
    for action, count in sorted(by_action.items()):
        md.append(f"| {action} | {count} |")
    md.append("")
    md.append("## Dizin Dağılımı\n")
    md.append("| Dizin | Dosya |\n|---|---:|")
    for directory, count in by_dir.most_common(30):
        md.append(f"| `{directory}` | {count} |")
    md.append("")
    md.append("## Desen Toplamları\n")
    md.append("| Desen | Adet |\n|---|---:|")
    for key in TECH_PATTERNS:
        md.append(f"| {key} | {totals.get(key, 0)} |")
    md.append("")
    md.append("## En Riskli 40 Script Adayı\n")
    md.append("| Aksiyon | Risk | Dosya | Satır | Secret | Localhost | Remove | Shell | Sebep |\n|---|---:|---|---:|---:|---:|---:|---:|---|")
    for item in sorted(items, key=lambda x: (-x.risk_score, x.rel.lower()))[:40]:
        md.append(f"| {item.action} | {item.risk_score} | `{item.rel}` | {item.lines} | {item.secret_like_text} | {item.hardcoded_localhost} | {item.dangerous_remove} | {item.subprocess_shell} | {item.reason} |")
    md.append("")
    md.append("## İlk 80 Arşiv Adayı\n")
    md.append("| Dosya | Satır | Risk | Sebep |\n|---|---:|---:|---|")
    for item in [x for x in items if x.action == "archive_candidate"][:80]:
        md.append(f"| `{item.rel}` | {item.lines} | {item.risk_score} | {item.reason} |")
    md.append("")
    md.append("## Not\n")
    md.append("Bu faz dosya taşımaz/silmez. Uygulama için ayrı apply paketi ve ayrı commit önerilir.\n")
    md_path.write_text("\n".join(md), encoding="utf-8")

    print(f"OK: Phase2B scripts inventory markdown: {md_path}")
    print(f"OK: Phase2B scripts inventory json: {json_path}")
    print(f"OK: Phase2B scripts inventory csv: {csv_path}")
    print("OK: Kod davranışı değiştirilmedi; sadece scripts klasörü okundu.")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["audit", "dry-run"], default="audit")
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    audit(Path(args.project_root), Path(args.output_root), args.mode)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
