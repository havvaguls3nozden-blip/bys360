from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
from pathlib import Path


TEMPLATE_REL = "app/templates/settings.html"
PARTIAL_REL = "app/templates/partials/settings/_settings_styles.html"
INCLUDE_LINE = "{% include 'partials/settings/_settings_styles.html' %}"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def count_lines(text: str) -> int:
    return len(text.splitlines())


def find_style_block(text: str) -> tuple[int, int, str] | None:
    match = re.search(r"(?is)<style\b[^>]*>.*?</style>", text)
    if not match:
        return None
    return match.start(), match.end(), match.group(0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    template = project_root / TEMPLATE_REL
    partial = project_root / PARTIAL_REL

    print("BYS360_QUALITY_10_10_P11_F1_SETTINGS_STYLE_PARTIAL_START")
    print(f"project_root={project_root}")
    print(f"template_file={template}")
    print(f"partial_file={partial}")

    if not template.exists():
        raise SystemExit(f"TEMPLATE_NOT_FOUND: {template}")

    text = read_text(template)

    if INCLUDE_LINE in text and not re.search(r"(?is)<style\b[^>]*>.*?</style>", text):
        print("BYS360_QUALITY_10_10_P11_F1_ALREADY_APPLIED")
        return 0

    style = find_style_block(text)
    if not style:
        raise SystemExit("STYLE_BLOCK_NOT_FOUND")

    start, end, style_block = style
    original_line_count = count_lines(text)
    style_line_count = count_lines(style_block)

    before = text[:start].rstrip()
    after = text[end:].lstrip("\r\n")
    new_text = before + "\n" + INCLUDE_LINE + "\n" + after

    new_line_count = count_lines(new_text)
    expected_reduction = original_line_count - new_line_count

    print(f"original_line_count={original_line_count}")
    print(f"style_line_count={style_line_count}")
    print(f"new_line_count={new_line_count}")
    print(f"expected_reduction={expected_reduction}")

    # Safety guards.
    lowered = style_block.lower()
    if style_line_count < 100:
        raise SystemExit("STYLE_BLOCK_TOO_SMALL_FOR_P11_F1")
    if "<script" in lowered or "fetch(" in lowered or "addeventlistener" in lowered:
        raise SystemExit("STYLE_BLOCK_CONTAINS_SCRIPT_HINT_UNSAFE")
    if "<form" in lowered or "csrf" in lowered or "name=" in lowered:
        raise SystemExit("STYLE_BLOCK_CONTAINS_FORM_HINT_UNSAFE")
    if expected_reduction < 500:
        raise SystemExit("EXPECTED_REDUCTION_TOO_SMALL")

    if args.dry_run:
        print("BYS360_QUALITY_10_10_P11_F1_DRYRUN_OK")
        return 0

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = project_root / ".quality_backup" / f"p11_f1_settings_style_partial_{stamp}"

    for path in [template, partial]:
        if path.exists():
            backup = backup_root / path.relative_to(project_root)
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup)

    partial.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "{# BYS360 P11-F1: settings.html inline style bloğu güvenli partial olarak ayrıldı. #}\n"
        "{# Rol matrisi, form/input/name/id, CSRF ve script davranışları bu dosyaya taşınmamıştır. #}\n"
    )
    write_text(partial, header + style_block.strip() + "\n")
    write_text(template, new_text)

    report = {
        "template_file": TEMPLATE_REL,
        "partial_file": PARTIAL_REL,
        "original_line_count": original_line_count,
        "style_line_count": style_line_count,
        "new_line_count": new_line_count,
        "expected_reduction": expected_reduction,
        "backup_root": str(backup_root),
        "include_line": INCLUDE_LINE,
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_json = out_dir / "bys360_quality_10_10_p11_f1_settings_style_partial_v1.json"
    report_md = out_dir / "bys360_quality_10_10_p11_f1_settings_style_partial_v1.md"
    report_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# BYS360 P11-F1 Settings Style Partial")
    md.append("")
    md.append(f"- Template: `{TEMPLATE_REL}`")
    md.append(f"- Partial: `{PARTIAL_REL}`")
    md.append(f"- Eski satır sayısı: {original_line_count}")
    md.append(f"- Taşınan style bloğu: {style_line_count} satır")
    md.append(f"- Yeni template satır sayısı: {new_line_count}")
    md.append(f"- Yaklaşık düşüş: {expected_reduction} satır")
    md.append(f"- Yedek: `{backup_root}`")
    md.append("")
    md.append("Bu işlem yalnızca inline `<style>` bloğunu partial dosyaya taşır. Rol matrisi, kişi bazlı menü görünürlüğü, form/input/name/id, CSRF ve script davranışlarına dokunmaz.")
    report_md.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"backup_root={backup_root}")
    print(f"style_partial_report_json={report_json}")
    print(f"style_partial_report_md={report_md}")
    print("BYS360_QUALITY_10_10_P11_F1_SETTINGS_STYLE_PARTIAL_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
