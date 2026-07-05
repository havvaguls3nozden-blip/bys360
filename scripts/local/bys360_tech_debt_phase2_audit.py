from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterable

# BYS360 Teknik Borç Faz 2 Audit
# Bu script local proje üzerinde yalnızca okuma yapar.
# Amaç: Kod davranışını değiştirmeden teknik borç alanlarını sınıflandırmak.

SOURCE_TEXT_EXTENSIONS = {
    ".py", ".html", ".css", ".js", ".ts", ".json", ".md", ".txt", ".sql",
    ".ps1", ".yml", ".yaml", ".toml", ".ini", ".cfg", ".mako", ".dart", ".xml",
}

SKIP_DIR_NAMES = {
    ".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".tox", ".nox", "node_modules", ".dart_tool", ".gradle", "build",
    "dist", "dist_secure", "archive", "backups", "logs", "instance", ".idea", ".vscode",
    "BYS360_CLEAN_SOURCE_PHASE1_20260705_092003",
}

BINARY_SUFFIXES = {
    ".pyc", ".pyo", ".pyd", ".log", ".sqlite", ".sqlite3", ".db", ".zip", ".7z",
    ".rar", ".tar", ".gz", ".dll", ".exe", ".dill", ".bin", ".lock", ".apk", ".aab",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".pdf", ".docx", ".xlsx",
}

# Kullanıcıya görünen teknik dil borcu için kasıtlı olarak geniş tutuldu; Faz 2 sadece sınıflandırır.
TECHNICAL_UI_PATTERNS = {
    "debug": r"\bdebug\b|hata ayıklama",
    "traceback": r"traceback|stack trace",
    "exception": r"\bexception\b|istisna",
    "endpoint": r"\bendpoint\b",
    "unauthorized_scope": r"unauthorized_scope|authorized_scope",
    "workflow_state": r"workflow[_\s-]?state",
    "phase_sync": r"phase\s*sync|faz\s*sync|sync\b|senkron",
    "raw_error": r"raw\s*error|json\s*error|api\s*hatas",
    "placeholder": r"placeholder|todo|fixme|hack",
    "localhost_visible": r"localhost|127\.0\.0\.1|192\.168\.",
}

PATTERN_DEFS = {
    "broad_except": r"except\s+(Exception|BaseException)?\s*:",
    "bare_except": r"except\s*:",
    "print_calls": r"(?m)^\s*print\s*\(",
    "debug_trace": r"pdb\.set_trace\(|breakpoint\s*\(",
    "hardcoded_localhost": r"localhost|127\.0\.0\.1|192\.168\.",
    "todo_fixme_hack": r"TODO|FIXME|HACK|XXX",
    "secret_like_text": r"SECRET_KEY|DATABASE_URL|SENTRY_DSN|MAIL_PASSWORD|SMTP_PASSWORD|API_KEY|TOKEN|PASSWORD",
    "route_defs": r"@[^\n]*\.route\s*\(",
    "blueprint_defs": r"Blueprint\s*\(",
    "raw_sql_execute": r"\.execute\s*\(\s*f?[\"'].*(SELECT|INSERT|UPDATE|DELETE)",
}

LARGE_LINE_LIMITS = {
    ".py": 900,
    ".html": 700,
    ".js": 1200,
    ".css": 1400,
    ".dart": 1000,
    ".ps1": 500,
}

PRIORITY_RULES = [
    ("P0", "Güvenlik/secret sinyali", lambda row: row.get("secret_like_text", 0) > 0 and row["rel"].startswith(("app/", "config", "scripts/"))),
    ("P0", "Canlı/yerel adres riski", lambda row: row.get("hardcoded_localhost", 0) > 0 and row["rel"].startswith(("app/", "config", "scripts/"))),
    ("P1", "Kullanıcıya teknik dil sızma riski", lambda row: row.get("technical_ui_words", 0) > 0 and ("templates" in row["rel"] or "static" in row["rel"])),
    ("P1", "Büyük Python dosyası", lambda row: row["suffix"] == ".py" and row["lines"] >= LARGE_LINE_LIMITS[".py"]),
    ("P1", "Route yoğunluğu", lambda row: row.get("route_defs", 0) >= 15),
    ("P2", "Print/log standardizasyonu", lambda row: row.get("print_calls", 0) > 0 and row["rel"].startswith("app/")),
    ("P2", "Broad except azaltma", lambda row: row.get("broad_except", 0) > 0 and row["rel"].startswith("app/")),
]

@dataclass
class Phase2Result:
    generated_at: str
    project_root: str
    scanned_files: int
    scanned_bytes: int
    skipped_dirs: dict[str, int]
    file_type_counts: dict[str, int]
    aggregate_patterns: dict[str, int]
    technical_ui_breakdown: dict[str, int]
    reports_quality: dict[str, object]
    scripts_summary: dict[str, object]
    large_files: list[dict[str, object]]
    route_hotspots: list[dict[str, object]]
    top_pattern_files: list[dict[str, object]]
    priority_candidates: list[dict[str, object]]


def rel_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def safe_read_text(path: Path, max_bytes: int = 2_000_000) -> str:
    try:
        size = path.stat().st_size
        if size > max_bytes:
            return ""
        data = path.read_bytes()
    except OSError:
        return ""
    for enc in ("utf-8", "utf-8-sig", "cp1254", "latin-1"):
        try:
            return data.decode(enc, errors="replace")
        except Exception:
            continue
    return data.decode("utf-8", errors="replace")


def line_count(text: str) -> int:
    if not text:
        return 0
    return text.count("\n") + 1


def iter_source_files(root: Path) -> Iterable[Path]:
    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        kept = []
        for d in dirnames:
            # Reports klasörünü tamamen atlamıyoruz; sadece reports/quality için ayrıca path-level sayım yapacağız.
            if d in SKIP_DIR_NAMES:
                continue
            kept.append(d)
        dirnames[:] = kept
        for filename in filenames:
            path = current / filename
            suffix = path.suffix.lower()
            if suffix in BINARY_SUFFIXES:
                continue
            if suffix not in SOURCE_TEXT_EXTENSIONS:
                continue
            rel = rel_path(path, root)
            # reports içeriğini kod borcu taramasına dahil etme; rapor kalabalığı ayrıca sayılacak.
            if rel.startswith("reports/"):
                continue
            yield path


def count_skipped_dirs(root: Path) -> Counter[str]:
    counter: Counter[str] = Counter()
    root = root.resolve()
    for dirpath, dirnames, _ in os.walk(root):
        kept = []
        for d in dirnames:
            if d in SKIP_DIR_NAMES:
                counter[d] += 1
            else:
                kept.append(d)
        dirnames[:] = kept
    return counter


def summarize_reports_quality(root: Path) -> dict[str, object]:
    rq = root / "reports" / "quality"
    summary: dict[str, object] = {"exists": rq.exists(), "file_count": 0, "total_mb": 0.0, "top_prefixes": [], "top_suffixes": [], "largest_files": []}
    if not rq.exists():
        return summary
    files = [p for p in rq.rglob("*") if p.is_file()]
    total_bytes = sum((p.stat().st_size if p.exists() else 0) for p in files)
    prefix_counter: Counter[str] = Counter()
    suffix_counter: Counter[str] = Counter()
    largest = []
    for p in files:
        name = p.name
        prefix = name.split("_")[0] if "_" in name else name.split(".")[0]
        if name.startswith("BYS360_A"):
            m = re.match(r"BYS360_(A\d+[A-Z0-9]*)", name)
            prefix = m.group(1) if m else "BYS360_A"
        elif name.startswith("BASELINE_"):
            prefix = "BASELINE"
        elif name.startswith("BYS360_S"):
            m = re.match(r"BYS360_(S\d+[A-Z0-9]*)", name)
            prefix = m.group(1) if m else "BYS360_S"
        prefix_counter[prefix] += 1
        suffix_counter[p.suffix.lower() or "[no_ext]"] += 1
        largest.append((p.stat().st_size, rel_path(p, root)))
    summary["file_count"] = len(files)
    summary["total_mb"] = round(total_bytes / 1024 / 1024, 2)
    summary["top_prefixes"] = prefix_counter.most_common(25)
    summary["top_suffixes"] = suffix_counter.most_common(20)
    summary["largest_files"] = [{"size_kb": round(size / 1024, 1), "rel": rel} for size, rel in sorted(largest, reverse=True)[:30]]
    return summary


def summarize_scripts(root: Path) -> dict[str, object]:
    scripts = root / "scripts"
    summary: dict[str, object] = {"exists": scripts.exists(), "file_count": 0, "by_dir": [], "by_suffix": [], "largest_files": []}
    if not scripts.exists():
        return summary
    files = [p for p in scripts.rglob("*") if p.is_file() and p.suffix.lower() not in BINARY_SUFFIXES]
    by_dir: Counter[str] = Counter()
    by_suffix: Counter[str] = Counter()
    largest = []
    for p in files:
        try:
            rel_parts = p.relative_to(root).parts
            group = "/".join(rel_parts[:2]) if len(rel_parts) >= 2 else rel_parts[0]
        except Exception:
            group = "scripts"
        by_dir[group] += 1
        by_suffix[p.suffix.lower() or "[no_ext]"] += 1
        try:
            size = p.stat().st_size
        except OSError:
            size = 0
        largest.append((size, rel_path(p, root)))
    summary["file_count"] = len(files)
    summary["by_dir"] = by_dir.most_common(30)
    summary["by_suffix"] = by_suffix.most_common(20)
    summary["largest_files"] = [{"size_kb": round(size / 1024, 1), "rel": rel} for size, rel in sorted(largest, reverse=True)[:30]]
    return summary


def classify_priority(row: dict[str, object]) -> tuple[str, str] | None:
    for level, reason, pred in PRIORITY_RULES:
        try:
            if pred(row):
                return level, reason
        except Exception:
            continue
    return None


def audit(root: Path) -> tuple[Phase2Result, list[dict[str, object]]]:
    root = root.resolve()
    aggregate: Counter[str] = Counter()
    tech_breakdown: Counter[str] = Counter()
    file_type_counts: Counter[str] = Counter()
    skipped_dirs = count_skipped_dirs(root)
    file_rows: list[dict[str, object]] = []
    scanned_files = 0
    scanned_bytes = 0

    compiled = {k: re.compile(v, flags=re.IGNORECASE | re.MULTILINE) for k, v in PATTERN_DEFS.items()}
    tech_compiled = {k: re.compile(v, flags=re.IGNORECASE | re.MULTILINE) for k, v in TECHNICAL_UI_PATTERNS.items()}

    for path in iter_source_files(root):
        rel = rel_path(path, root)
        suffix = path.suffix.lower()
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        text = safe_read_text(path)
        if text == "" and size > 0:
            # very large or unreadable; still count file, not patterns.
            lines = 0
        else:
            lines = line_count(text)
        scanned_files += 1
        scanned_bytes += size
        file_type_counts[suffix or "[no_ext]"] += 1

        row: dict[str, object] = {
            "rel": rel,
            "suffix": suffix,
            "size_kb": round(size / 1024, 1),
            "lines": lines,
        }
        technical_total = 0
        for key, regex in compiled.items():
            count = len(regex.findall(text)) if text else 0
            if count:
                row[key] = count
                aggregate[key] += count
        for key, regex in tech_compiled.items():
            count = len(regex.findall(text)) if text else 0
            if count:
                tech_breakdown[key] += count
                technical_total += count
        row["technical_ui_words"] = technical_total
        aggregate["technical_ui_words"] += technical_total
        pr = classify_priority(row)
        if pr:
            row["priority"] = pr[0]
            row["priority_reason"] = pr[1]
        file_rows.append(row)

    large_files = []
    for row in file_rows:
        limit = LARGE_LINE_LIMITS.get(str(row["suffix"]), 999999)
        if int(row["lines"]) >= limit:
            large_files.append({"rel": row["rel"], "suffix": row["suffix"], "lines": row["lines"], "size_kb": row["size_kb"]})
    large_files = sorted(large_files, key=lambda r: (int(r["lines"]), float(r["size_kb"])), reverse=True)[:80]

    route_hotspots = [
        {"rel": row["rel"], "route_defs": row.get("route_defs", 0), "lines": row["lines"]}
        for row in file_rows if int(row.get("route_defs", 0) or 0) > 0
    ]
    route_hotspots = sorted(route_hotspots, key=lambda r: (int(r["route_defs"]), int(r["lines"])), reverse=True)[:60]

    def pattern_score(row: dict[str, object]) -> int:
        return int(row.get("secret_like_text", 0) or 0) * 20 + int(row.get("hardcoded_localhost", 0) or 0) * 10 + int(row.get("technical_ui_words", 0) or 0) + int(row.get("broad_except", 0) or 0) + int(row.get("print_calls", 0) or 0)

    top_pattern_files = []
    for row in sorted(file_rows, key=pattern_score, reverse=True)[:100]:
        score = pattern_score(row)
        if score <= 0:
            continue
        top_pattern_files.append({
            "rel": row["rel"],
            "score": score,
            "lines": row["lines"],
            "broad_except": row.get("broad_except", 0),
            "print_calls": row.get("print_calls", 0),
            "hardcoded_localhost": row.get("hardcoded_localhost", 0),
            "secret_like_text": row.get("secret_like_text", 0),
            "technical_ui_words": row.get("technical_ui_words", 0),
        })

    priority_candidates = []
    priority_rank = {"P0": 0, "P1": 1, "P2": 2}
    for row in file_rows:
        if "priority" in row:
            priority_candidates.append({
                "priority": row["priority"],
                "reason": row["priority_reason"],
                "rel": row["rel"],
                "lines": row["lines"],
                "route_defs": row.get("route_defs", 0),
                "broad_except": row.get("broad_except", 0),
                "print_calls": row.get("print_calls", 0),
                "hardcoded_localhost": row.get("hardcoded_localhost", 0),
                "secret_like_text": row.get("secret_like_text", 0),
                "technical_ui_words": row.get("technical_ui_words", 0),
            })
    priority_candidates = sorted(priority_candidates, key=lambda r: (priority_rank.get(str(r["priority"]), 9), -int(r.get("technical_ui_words", 0) or 0), str(r["rel"])))[:150]

    result = Phase2Result(
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        project_root=str(root),
        scanned_files=scanned_files,
        scanned_bytes=scanned_bytes,
        skipped_dirs=dict(skipped_dirs),
        file_type_counts=dict(file_type_counts),
        aggregate_patterns=dict(aggregate),
        technical_ui_breakdown=dict(tech_breakdown),
        reports_quality=summarize_reports_quality(root),
        scripts_summary=summarize_scripts(root),
        large_files=large_files,
        route_hotspots=route_hotspots,
        top_pattern_files=top_pattern_files,
        priority_candidates=priority_candidates,
    )
    return result, file_rows


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "priority", "priority_reason", "rel", "suffix", "size_kb", "lines", "route_defs",
        "broad_except", "bare_except", "print_calls", "debug_trace", "hardcoded_localhost",
        "secret_like_text", "technical_ui_words", "todo_fixme_hack", "raw_sql_execute",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def md_table(rows: list[dict[str, object]], columns: list[tuple[str, str]], limit: int = 30) -> str:
    if not rows:
        return "_Kayıt yok._\n"
    out = []
    out.append("| " + " | ".join(title for title, _ in columns) + " |")
    out.append("|" + "|".join("---" for _ in columns) + "|")
    for row in rows[:limit]:
        vals = []
        for _, key in columns:
            val = row.get(key, "")
            vals.append(str(val).replace("|", "\\|"))
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out) + "\n"


def write_report(path: Path, result: Phase2Result) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    agg = result.aggregate_patterns
    rq = result.reports_quality
    scripts = result.scripts_summary
    lines: list[str] = []
    lines.append("# BYS360 Teknik Borç Faz 2 Audit Raporu")
    lines.append("")
    lines.append(f"Oluşturma zamanı: `{result.generated_at}`")
    lines.append(f"Proje kökü: `{result.project_root}`")
    lines.append("")
    lines.append("## Yönetici Özeti")
    lines.append("")
    lines.append("| Ölçüm | Değer |")
    lines.append("|---|---:|")
    lines.append(f"| Taranan kaynak dosya | {result.scanned_files} |")
    lines.append(f"| Taranan kaynak boyutu | {round(result.scanned_bytes / 1024 / 1024, 2)} MB |")
    lines.append(f"| reports/quality dosya sayısı | {rq.get('file_count', 0)} |")
    lines.append(f"| reports/quality toplam boyut | {rq.get('total_mb', 0)} MB |")
    lines.append(f"| scripts dosya sayısı | {scripts.get('file_count', 0)} |")
    lines.append(f"| Büyük dosya adayı | {len(result.large_files)} |")
    lines.append(f"| Route hotspot adayı | {len(result.route_hotspots)} |")
    lines.append(f"| Öncelikli borç adayı | {len(result.priority_candidates)} |")
    lines.append("")
    lines.append("Bu faz kod davranışını değiştirmez. Amaç büyük borç alanlarını P0/P1/P2 olarak sınıflandırmaktır.")
    lines.append("")
    lines.append("## Desen Sayımları")
    lines.append("")
    lines.append("| Desen | Adet |")
    lines.append("|---|---:|")
    for key in sorted(agg):
        lines.append(f"| {key} | {agg[key]} |")
    lines.append("")
    lines.append("## Teknik UI Dili Kırılımı")
    lines.append("")
    lines.append("| Desen | Adet |")
    lines.append("|---|---:|")
    for key, val in sorted(result.technical_ui_breakdown.items(), key=lambda kv: kv[1], reverse=True):
        lines.append(f"| {key} | {val} |")
    if not result.technical_ui_breakdown:
        lines.append("| - | 0 |")
    lines.append("")
    lines.append("## P0/P1/P2 Öncelikli Adaylar")
    lines.append("")
    lines.append(md_table(result.priority_candidates, [
        ("Öncelik", "priority"), ("Sebep", "reason"), ("Dosya", "rel"), ("Satır", "lines"),
        ("Route", "route_defs"), ("Tech UI", "technical_ui_words"), ("Localhost", "hardcoded_localhost"), ("Secret", "secret_like_text"),
    ], 80))
    lines.append("")
    lines.append("## Büyük Dosya Adayları")
    lines.append("")
    lines.append(md_table(result.large_files, [("Dosya", "rel"), ("Uzantı", "suffix"), ("Satır", "lines"), ("KB", "size_kb")], 60))
    lines.append("")
    lines.append("## Route Hotspot Adayları")
    lines.append("")
    lines.append(md_table(result.route_hotspots, [("Dosya", "rel"), ("Route", "route_defs"), ("Satır", "lines")], 60))
    lines.append("")
    lines.append("## En Yüksek Desen Skorlu Dosyalar")
    lines.append("")
    lines.append(md_table(result.top_pattern_files, [
        ("Dosya", "rel"), ("Skor", "score"), ("Satır", "lines"), ("Except", "broad_except"),
        ("Print", "print_calls"), ("Localhost", "hardcoded_localhost"), ("Secret", "secret_like_text"), ("Tech UI", "technical_ui_words"),
    ], 80))
    lines.append("")
    lines.append("## reports/quality Kalabalığı")
    lines.append("")
    lines.append(f"Dosya sayısı: `{rq.get('file_count', 0)}`  ")
    lines.append(f"Toplam boyut: `{rq.get('total_mb', 0)} MB`")
    lines.append("")
    lines.append("### En Yoğun Prefixler")
    lines.append("")
    prefix_rows = [{"prefix": k, "count": v} for k, v in rq.get("top_prefixes", [])]
    lines.append(md_table(prefix_rows, [("Prefix", "prefix"), ("Adet", "count")], 25))
    lines.append("")
    lines.append("### En Büyük reports/quality Dosyaları")
    lines.append("")
    lines.append(md_table(rq.get("largest_files", []), [("Dosya", "rel"), ("KB", "size_kb")], 30))
    lines.append("")
    lines.append("## scripts Klasörü Özeti")
    lines.append("")
    lines.append(f"Script dosya sayısı: `{scripts.get('file_count', 0)}`")
    lines.append("")
    by_dir_rows = [{"dir": k, "count": v} for k, v in scripts.get("by_dir", [])]
    lines.append(md_table(by_dir_rows, [("Klasör", "dir"), ("Adet", "count")], 30))
    lines.append("")
    lines.append("## Önerilen Faz 2 Sırası")
    lines.append("")
    lines.append("1. P0 adayları: secret sinyali ve canlı/yerel adres riski tek tek doğrulanacak.")
    lines.append("2. P1 adayları: kullanıcıya görünen teknik dil ve büyük route dosyaları sınıflandırılacak.")
    lines.append("3. reports/quality arşiv politikası belirlenecek; geçmiş kanıtlar korunup aktif repo kalabalığı azaltılacak.")
    lines.append("4. scripts klasörü aktif/legacy/one-shot olarak ayrılacak.")
    lines.append("5. print/broad except azaltımı düşük riskli dalgalar halinde yapılacak.")
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BYS360 Teknik Borç Faz 2 Audit")
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--mode", choices=["audit"], default="audit")
    args = parser.parse_args(argv)

    project_root = Path(args.project_root)
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    result, rows = audit(project_root)
    report_path = output_root / "BYS360_TECH_DEBT_PHASE2_REPORT.md"
    json_path = output_root / "BYS360_TECH_DEBT_PHASE2_AUDIT.json"
    csv_path = output_root / "BYS360_TECH_DEBT_PHASE2_FILE_CANDIDATES.csv"

    write_report(report_path, result)
    write_json(json_path, asdict(result))
    # CSV: priority rows first, then scored rows. Keep only rows with at least one relevant signal.
    useful_rows = [r for r in rows if any(int(r.get(k, 0) or 0) > 0 for k in ["route_defs", "broad_except", "print_calls", "hardcoded_localhost", "secret_like_text", "technical_ui_words", "todo_fixme_hack", "raw_sql_execute"])]
    priority_order = {"P0": 0, "P1": 1, "P2": 2}
    useful_rows = sorted(useful_rows, key=lambda r: (priority_order.get(str(r.get("priority", "Z")), 9), str(r.get("rel", ""))))
    write_csv(csv_path, useful_rows)

    print(f"OK: Faz 2 audit raporu üretildi: {report_path}")
    print(f"OK: Faz 2 JSON raporu üretildi: {json_path}")
    print(f"OK: Faz 2 aday CSV üretildi: {csv_path}")
    print("OK: Kod davranışı değiştirilmedi; sadece okuma/audit yapıldı.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
