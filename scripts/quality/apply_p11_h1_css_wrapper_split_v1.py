from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
from pathlib import Path


CSS_REL = "app/static/css/performance_phase3.css"
PARTS_DIR_NAME = "performance_phase3_parts"
MAX_CHUNK_LINES = 450


def split_css_preserve_order(css_text: str, max_chunk_lines: int = MAX_CHUNK_LINES) -> list[str]:
    lines = css_text.splitlines(keepends=True)
    chunks: list[list[str]] = []
    current: list[str] = []
    depth = 0

    for line in lines:
        current.append(line)

        # Lightweight brace depth; enough for ordinary CSS and @media blocks.
        depth += line.count("{") - line.count("}")

        # Split only at top-level boundaries so we do not cut a CSS block or @media block.
        if depth <= 0 and len(current) >= max_chunk_lines:
            chunks.append(current)
            current = []
            depth = 0

    if current:
        chunks.append(current)

    return ["".join(chunk) for chunk in chunks]


def wrapper_css(parts: list[str]) -> str:
    header = [
        "/* BYS360 Performans CSS wrapper.",
        "   Bu dosya P11-H1 kapsamında cascade sırası korunarak parçalara ayrılmıştır.",
        "   HTML referansları değişmemeli; parçalar aşağıdaki sırayla yüklenmelidir. */",
        "",
    ]
    imports = [f'@import url("./{PARTS_DIR_NAME}/{name}");' for name in parts]
    return "\n".join(header + imports) + "\n"


def validate_chunks(chunks: list[str], original: str) -> dict[str, object]:
    joined = "".join(chunks)
    return {
        "chunk_count": len(chunks),
        "original_chars": len(original),
        "joined_chars": len(joined),
        "same_content": joined == original,
        "chunk_line_counts": [len(c.splitlines()) for c in chunks],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-chunk-lines", type=int, default=MAX_CHUNK_LINES)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    css_file = project_root / CSS_REL
    if not css_file.exists():
        raise SystemExit(f"CSS_NOT_FOUND: {css_file}")

    original = css_file.read_text(encoding="utf-8", errors="ignore")
    chunks = split_css_preserve_order(original, args.max_chunk_lines)
    validation = validate_chunks(chunks, original)

    part_names = [f"performance_phase3_part_{i:02d}.css" for i in range(1, len(chunks) + 1)]
    new_wrapper = wrapper_css(part_names)

    print("BYS360_QUALITY_10_10_P11_H1_CSS_WRAPPER_SPLIT_START")
    print(f"project_root={project_root}")
    print(f"css_file={css_file}")
    print(f"original_lines={len(original.splitlines())}")
    print(f"chunk_count={validation['chunk_count']}")
    print(f"same_content={validation['same_content']}")
    print("BYS360_QUALITY_10_10_P11_H1_CHUNKS")
    for name, count in zip(part_names, validation["chunk_line_counts"]):
        print(f"{name} | lines={count}")

    if not validation["same_content"]:
        raise SystemExit("CSS_SPLIT_VALIDATION_FAILED: chunks do not reconstruct original content")

    if args.dry_run:
        print("BYS360_QUALITY_10_10_P11_H1_DRYRUN_OK")
        return 0

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = project_root / ".quality_backup" / f"p11_h1_css_wrapper_split_{stamp}"
    backup_css = backup_root / CSS_REL
    backup_css.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(css_file, backup_css)

    parts_dir = css_file.parent / PARTS_DIR_NAME
    if parts_dir.exists():
        backup_parts = backup_root / "existing_performance_phase3_parts"
        shutil.copytree(parts_dir, backup_parts, dirs_exist_ok=True)
        shutil.rmtree(parts_dir)
    parts_dir.mkdir(parents=True, exist_ok=True)

    for name, chunk in zip(part_names, chunks):
        (parts_dir / name).write_text(chunk, encoding="utf-8", newline="")

    css_file.write_text(new_wrapper, encoding="utf-8", newline="")

    report = {
        "css_file": CSS_REL,
        "parts_dir": str(parts_dir.relative_to(project_root)).replace("\\", "/"),
        "part_files": part_names,
        "original_lines": len(original.splitlines()),
        "wrapper_lines": len(new_wrapper.splitlines()),
        "chunk_line_counts": validation["chunk_line_counts"],
        "backup_root": str(backup_root),
        "validation": validation,
    }
    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_json = out_dir / "bys360_quality_10_10_p11_h1_css_wrapper_split_v1.json"
    report_md = out_dir / "bys360_quality_10_10_p11_h1_css_wrapper_split_v1.md"
    report_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# BYS360 P11-H1 CSS Wrapper Split")
    md.append("")
    md.append(f"- Ana CSS: `{CSS_REL}`")
    md.append(f"- Eski satır sayısı: {report['original_lines']}")
    md.append(f"- Yeni wrapper satır sayısı: {report['wrapper_lines']}")
    md.append(f"- Parça sayısı: {len(part_names)}")
    md.append(f"- Yedek: `{backup_root}`")
    md.append("")
    md.append("## Parçalar")
    md.append("")
    for name, count in zip(part_names, validation["chunk_line_counts"]):
        md.append(f"- `{PARTS_DIR_NAME}/{name}` — {count} satır")
    md.append("")
    md.append("## Güvenlik Notu")
    md.append("")
    md.append("Bu işlem CSS cascade sırasını korumak için parçaları orijinal sırada `@import` eder. HTML dosyalarında CSS referansı değiştirilmemiştir.")
    report_md.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"backup_root={backup_root}")
    print(f"split_report_json={report_json}")
    print(f"split_report_md={report_md}")
    print("BYS360_QUALITY_10_10_P11_H1_CSS_WRAPPER_SPLIT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
