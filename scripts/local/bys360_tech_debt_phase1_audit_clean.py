from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

TEXT_EXTENSIONS = {
    ".py", ".html", ".css", ".js", ".json", ".md", ".txt", ".sql", ".ps1",
    ".yml", ".yaml", ".toml", ".ini", ".cfg", ".mako", ".dart", ".xml",
}

EXCLUDED_DIR_NAMES = {
    ".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".tox", ".nox", "node_modules", ".dart_tool", ".gradle", "build",
    "dist", "dist_secure", "archive", "backups", "logs", "instance",
}

# Generated reports are useful for diagnosis, but they should not live inside clean source packages.
EXCLUDED_TOP_LEVEL_DIRS = {"reports"}

EXCLUDED_FILE_NAMES = {
    ".env", ".env.local", ".env.production", ".env.development", ".DS_Store", "Thumbs.db",
}

EXCLUDED_SUFFIXES = {
    ".pyc", ".pyo", ".pyd", ".log", ".sqlite", ".sqlite3", ".db", ".zip", ".7z", ".rar",
    ".tar", ".gz", ".dll", ".exe", ".dill", ".bin", ".lock",
}

SECRET_PATTERNS = [
    re.compile(r"(?i)\b(SECRET_KEY|DATABASE_URL|SENTRY_DSN|MAIL_PASSWORD|SMTP_PASSWORD|API_KEY|TOKEN|PASSWORD)\s*=\s*[^\r\n]+"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
]

SCAN_PATTERNS = {
    "todo_fixme_hack": re.compile(r"\b(TODO|FIXME|HACK)\b", re.I),
    "print_calls": re.compile(r"(?m)^\s*print\s*\("),
    "broad_except": re.compile(r"except\s+(Exception|BaseException)?\s*:"),
    "debug_trace": re.compile(r"traceback\.print_exc|debug\s*=\s*True|pdb\.set_trace", re.I),
    "technical_ui_words": re.compile(r"workflow|phase|sync|unauthorized_scope|endpoint|exception|debug", re.I),
    "hardcoded_localhost": re.compile(r"localhost|127\.0\.0\.1|0\.0\.0\.0|192\.168\.", re.I),
    "secret_like_text": re.compile(r"(?i)\b(SECRET_KEY|DATABASE_URL|SENTRY_DSN|MAIL_PASSWORD|SMTP_PASSWORD|API_KEY|TOKEN|PASSWORD)\s*="),
}

@dataclass
class AuditResult:
    project_root: Path
    generated_at: str
    total_files: int
    total_bytes: int
    clean_candidate_files: int
    excluded_files: int
    risky_files: dict[str, list[str]]
    pattern_counts: dict[str, int]
    app_python: dict[str, int]
    largest_files: list[tuple[int, str]]
    top_app_python_files: list[tuple[int, str]]
    clean_exclusion_summary: dict[str, int]


def rel_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def is_under_excluded_top_level(path: Path, root: Path) -> bool:
    try:
        parts = path.relative_to(root).parts
    except ValueError:
        return True
    return bool(parts) and parts[0] in EXCLUDED_TOP_LEVEL_DIRS


def exclusion_reason(path: Path, root: Path) -> str | None:
    try:
        rel_parts = path.relative_to(root).parts
    except ValueError:
        return "outside_project_root"

    if not rel_parts:
        return None

    if rel_parts[0] in EXCLUDED_TOP_LEVEL_DIRS:
        return f"top_level_{rel_parts[0]}"

    if any(part in EXCLUDED_DIR_NAMES for part in rel_parts[:-1]):
        for part in rel_parts[:-1]:
            if part in EXCLUDED_DIR_NAMES:
                return f"dir_{part}"

    name = path.name
    suffix = path.suffix.lower()

    if name in EXCLUDED_FILE_NAMES:
        return f"file_{name}"
    if suffix in EXCLUDED_SUFFIXES:
        return f"suffix_{suffix}"
    if name.endswith(".log") or ".log." in name:
        return "log_rotation_file"
    if name.endswith(".sqlite3") or name.endswith(".sqlite"):
        return "local_database_file"

    return None


def iter_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        current = Path(dirpath)
        # Avoid descending into obviously excluded directories; still counted later when walking from root? no.
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIR_NAMES]
        for filename in filenames:
            yield current / filename


def iter_all_files_including_excluded(root: Path) -> Iterable[Path]:
    for dirpath, _, filenames in os.walk(root):
        current = Path(dirpath)
        for filename in filenames:
            yield current / filename


def safe_read_text(path: Path, max_bytes: int = 2_000_000) -> str | None:
    try:
        if path.stat().st_size > max_bytes:
            return None
        data = path.read_bytes()
        if b"\x00" in data[:4096]:
            return None
        return data.decode("utf-8", "ignore")
    except OSError:
        return None


def audit(project_root: Path) -> AuditResult:
    project_root = project_root.resolve()
    all_files = list(iter_all_files_including_excluded(project_root))
    total_bytes = sum(p.stat().st_size for p in all_files if p.exists())
    risky: dict[str, list[str]] = {
        "env_files": [],
        "git_history": [],
        "virtualenv": [],
        "local_database": [],
        "logs": [],
        "nested_archives": [],
        "build_cache": [],
        "python_cache": [],
        "secret_like_files": [],
    }
    exclusion_counts: Counter[str] = Counter()
    clean_candidate_files = 0
    excluded_files = 0
    pattern_counts: Counter[str] = Counter()
    app_python = Counter()
    largest: list[tuple[int, str]] = []
    top_app_py: list[tuple[int, str]] = []

    for path in all_files:
        rel = rel_path(path, project_root)
        parts = path.relative_to(project_root).parts
        suffix = path.suffix.lower()
        size = path.stat().st_size
        largest.append((size, rel))

        reason = exclusion_reason(path, project_root)
        if reason:
            excluded_files += 1
            exclusion_counts[reason] += 1
        else:
            clean_candidate_files += 1

        if path.name == ".env" or path.name.startswith(".env."):
            risky["env_files"].append(rel)
        if ".git" in parts:
            risky["git_history"].append(rel)
        if ".venv" in parts or "venv" in parts:
            risky["virtualenv"].append(rel)
        if suffix in {".sqlite", ".sqlite3", ".db"}:
            risky["local_database"].append(rel)
        if suffix == ".log" or ".log." in path.name or "logs" in parts:
            risky["logs"].append(rel)
        if suffix in {".zip", ".7z", ".rar", ".tar", ".gz"}:
            risky["nested_archives"].append(rel)
        if ".dart_tool" in parts or ".gradle" in parts or "build" in parts:
            risky["build_cache"].append(rel)
        if "__pycache__" in parts or suffix in {".pyc", ".pyo"}:
            risky["python_cache"].append(rel)

        # Hızlı audit: teknik desen ve secret taramasını yalnızca temiz kaynak adayı dosyalarda yap.
        # .venv, .git, build/cache, logs, reports ve arşiv dosyalarını okumaya çalışma.
        if reason is None and suffix in TEXT_EXTENSIONS and size <= 2_000_000:
            text = safe_read_text(path)
            if text is not None:
                for key, pattern in SCAN_PATTERNS.items():
                    pattern_counts[key] += len(pattern.findall(text))
                if any(p.search(text) for p in SECRET_PATTERNS):
                    risky["secret_like_files"].append(rel)

        if "app" in parts and suffix == ".py" and reason is None:
            text = safe_read_text(path, max_bytes=4_000_000) or ""
            lines = text.count("\n") + 1 if text else 0
            app_python["files"] += 1
            app_python["lines"] += lines
            app_python["route_defs"] += len(re.findall(r"@\w+\.route\s*\(|@(?:app|bp|blueprint)\.route\s*\(", text))
            app_python["class_defs"] += len(re.findall(r"(?m)^class\s+\w+", text))
            app_python["function_defs"] += len(re.findall(r"(?m)^def\s+\w+", text))
            top_app_py.append((lines, rel))

    largest = sorted(largest, reverse=True)[:50]
    top_app_py = sorted(top_app_py, reverse=True)[:50]
    risky = {k: v[:100] for k, v in risky.items() if v}

    return AuditResult(
        project_root=project_root,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        total_files=len(all_files),
        total_bytes=total_bytes,
        clean_candidate_files=clean_candidate_files,
        excluded_files=excluded_files,
        risky_files=risky,
        pattern_counts=dict(pattern_counts),
        app_python=dict(app_python),
        largest_files=largest,
        top_app_python_files=top_app_py,
        clean_exclusion_summary=dict(exclusion_counts),
    )


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_clean(project_root: Path, output_root: Path, make_zip: bool = True) -> dict[str, object]:
    project_root = project_root.resolve()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_dir = output_root.resolve() / f"BYS360_CLEAN_SOURCE_PHASE1_{stamp}"
    clean_dir.mkdir(parents=True, exist_ok=False)

    copied = 0
    skipped = Counter()
    manifest = []

    for path in iter_all_files_including_excluded(project_root):
        reason = exclusion_reason(path, project_root)
        rel = rel_path(path, project_root)
        if reason:
            skipped[reason] += 1
            continue
        dst = clean_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dst)
        copied += 1
        try:
            manifest.append({"path": rel, "size": dst.stat().st_size, "sha256": sha256_file(dst)})
        except OSError:
            manifest.append({"path": rel, "size": None, "sha256": None})

    manifest_path = clean_dir / "BYS360_CLEAN_SOURCE_PHASE1_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    zip_path = None
    if make_zip:
        zip_path = output_root.resolve() / f"BYS360_CLEAN_SOURCE_PHASE1_{stamp}.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for file in clean_dir.rglob("*"):
                if file.is_file():
                    zf.write(file, file.relative_to(clean_dir).as_posix())

    return {
        "clean_dir": str(clean_dir),
        "zip_path": str(zip_path) if zip_path else None,
        "copied_files": copied,
        "skipped_summary": dict(skipped),
    }


def write_reports(result: AuditResult, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "BYS360_TECH_DEBT_PHASE1_AUDIT.json"
    md_path = output_dir / "BYS360_TECH_DEBT_PHASE1_REPORT.md"
    payload = {
        "project_root": str(result.project_root),
        "generated_at": result.generated_at,
        "total_files": result.total_files,
        "total_mb": round(result.total_bytes / 1024 / 1024, 2),
        "clean_candidate_files": result.clean_candidate_files,
        "excluded_files": result.excluded_files,
        "risky_files": result.risky_files,
        "pattern_counts": result.pattern_counts,
        "app_python": result.app_python,
        "largest_files": result.largest_files,
        "top_app_python_files": result.top_app_python_files,
        "clean_exclusion_summary": result.clean_exclusion_summary,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def sample_list(items: list[str], limit: int = 12) -> str:
        if not items:
            return "Yok"
        return "\n".join(f"- `{x}`" for x in items[:limit])

    risks_md = []
    for key, items in result.risky_files.items():
        risks_md.append(f"### {key}\n\nToplam örnek: {len(items)}\n\n{sample_list(items)}")

    largest_md = "\n".join(f"- {size/1024/1024:.2f} MB — `{path}`" for size, path in result.largest_files[:20])
    app_top_md = "\n".join(f"- {lines} satır — `{path}`" for lines, path in result.top_app_python_files[:20])
    pattern_md = "\n".join(f"| {k} | {v} |" for k, v in sorted(result.pattern_counts.items()))
    exclusion_md = "\n".join(f"| {k} | {v} |" for k, v in sorted(result.clean_exclusion_summary.items()))

    md = f"""# BYS360 Teknik Borç Faz 1 Audit Raporu

Oluşturma zamanı: `{result.generated_at}`  
Proje kökü: `{result.project_root}`

## Yönetici Özeti

| Ölçüm | Değer |
|---|---:|
| Toplam dosya | {result.total_files} |
| Toplam boyut | {result.total_bytes/1024/1024:.2f} MB |
| Temiz kaynak adayı | {result.clean_candidate_files} |
| Temiz paketten hariç tutulacak dosya | {result.excluded_files} |

Bu fazın amacı kod davranışını değiştirmek değil; kaynak kodu, yedekleri, logları, yerel veritabanını, sanal ortamı ve build/cache dosyalarını birbirinden ayırmaktır.

## Kod Göstergeleri

| Ölçüm | Değer |
|---|---:|
| `app` Python dosyası | {result.app_python.get('files', 0)} |
| `app` Python satırı | {result.app_python.get('lines', 0)} |
| Route tanımı | {result.app_python.get('route_defs', 0)} |
| Fonksiyon tanımı | {result.app_python.get('function_defs', 0)} |
| Class tanımı | {result.app_python.get('class_defs', 0)} |

## Desen Sayımları

| Desen | Adet |
|---|---:|
{pattern_md}

## Riskli Dosya Aileleri

{chr(10).join(risks_md)}

## En Büyük Dosyalar

{largest_md}

## En Büyük `app/*.py` Dosyaları

{app_top_md}

## Temiz Kopyadan Hariç Tutma Özeti

| Neden | Adet |
|---|---:|
{exclusion_md}

## Faz 1 Kararı

1. `.env`, canlı/yedek logları, yerel SQLite, `.git`, `.venv`, build cache ve nested zip dosyaları temiz kaynak paketine alınmayacak.
2. Temiz kaynak ayrı klasöre üretilecek; mevcut proje klasörü silinmeyecek.
3. Kod/mimari refactor Faz 2'ye bırakılacak.
4. Canlıya uygulanacak değişiklik ayrı release ve yedek kuralıyla yapılacak.
"""
    md_path.write_text(md, encoding="utf-8")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="BYS360 Teknik Borç Faz 1 audit ve temiz kaynak üretimi")
    parser.add_argument("--project-root", default=".", help="BYS360 proje kökü, örn. C:\\bys360\\project")
    parser.add_argument("--mode", choices=["audit", "clean-copy", "audit-and-clean"], default="audit")
    parser.add_argument("--output-root", default=None, help="Rapor/temiz kopya çıktı klasörü")
    parser.add_argument("--no-zip", action="store_true", help="clean-copy modunda zip üretme")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    if not project_root.exists():
        print(f"HATA: Proje kökü bulunamadı: {project_root}", file=sys.stderr)
        return 2

    output_root = Path(args.output_root).resolve() if args.output_root else project_root / "reports" / "tech_debt_phase1"
    output_root.mkdir(parents=True, exist_ok=True)

    result = audit(project_root)
    json_path, md_path = write_reports(result, output_root)
    print(f"OK: Audit raporu üretildi: {md_path}")
    print(f"OK: JSON raporu üretildi: {json_path}")

    if args.mode in {"clean-copy", "audit-and-clean"}:
        clean_result = copy_clean(project_root, output_root, make_zip=not args.no_zip)
        clean_json = output_root / "BYS360_TECH_DEBT_PHASE1_CLEAN_RESULT.json"
        clean_json.write_text(json.dumps(clean_result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"OK: Temiz kaynak klasörü: {clean_result['clean_dir']}")
        if clean_result.get("zip_path"):
            print(f"OK: Temiz kaynak ZIP: {clean_result['zip_path']}")
        print(f"OK: Temiz kopya sonucu: {clean_json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
