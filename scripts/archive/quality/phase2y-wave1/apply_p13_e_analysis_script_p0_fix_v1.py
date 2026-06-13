from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
from pathlib import Path


TARGETS = [
    {
        "path": "scripts/quality/analyze_p12_b_technical_ui_term_decision_v1.py",
        "name": "P12-B technical UI decision",
        "replacements": [
            {
                "old": "                        try:\n                            counts[sev] = int(val[sev])\n                        except Exception:\n                            pass\n",
                "new": "                        try:\n                            counts[sev] = int(val[sev])\n                        except (TypeError, ValueError) as exc:\n                            print(f\"BYS360_P12_B_SUMMARY_COUNT_PARSE_WARN sev={sev} value={val.get(sev)!r} error={exc}\")\n",
                "reason": "summary count parse hatası artık sessiz geçilmeyecek",
            }
        ],
    },
    {
        "path": "scripts/quality/analyze_p13_a_effective_p1_closure_map_v1.py",
        "name": "P13-A effective P1 closure map",
        "replacements": [
            {
                "old": "    except Exception:\n        pass\n",
                "new": "    except Exception as exc:\n        print(f\"BYS360_P13_A_P1_ANALYSIS_GENERATION_WARN error={exc}\")\n",
                "reason": "P1 analysis üretimi başarısız olursa sessiz geçilmeyecek",
            }
        ],
    },
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def scan_silent_except_pass(text: str) -> list[dict[str, int | str]]:
    pattern = re.compile(
        r"(?P<indent>^[ \t]*)except\s+[^:\n]+:\s*\n(?P=indent)[ \t]+pass\s*(?:#.*)?$",
        re.MULTILINE,
    )
    findings = []
    lines = text.splitlines()
    for match in pattern.finditer(text):
        start_line = text[:match.start()].count("\n") + 1
        snippet = "\n".join(lines[max(0, start_line - 2): min(len(lines), start_line + 3)])
        findings.append({"line": start_line, "snippet": snippet})
    return findings


def apply(project_root: Path, dry_run: bool) -> None:
    print("BYS360_QUALITY_10_10_P13_E_ANALYSIS_SCRIPT_P0_FIX_START")
    print(f"project_root={project_root}")
    print(f"mode={'DRY_RUN' if dry_run else 'APPLY'}")

    report = {
        "mode": "DRY_RUN" if dry_run else "APPLY",
        "targets": [],
        "backup_root": None,
    }

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = project_root / ".quality_backup" / f"p13_e_analysis_script_p0_fix_{stamp}"

    for target in TARGETS:
        rel = target["path"]
        path = project_root / rel
        if not path.exists():
            raise SystemExit(f"TARGET_NOT_FOUND: {path}")

        original = read_text(path)
        before_findings = scan_silent_except_pass(original)
        updated = original
        applied_replacements = []

        for repl in target["replacements"]:
            old = repl["old"]
            new = repl["new"]
            if old in updated:
                updated = updated.replace(old, new, 1)
                applied_replacements.append({
                    "reason": repl["reason"],
                    "status": "APPLIED_PATTERN",
                })
            else:
                applied_replacements.append({
                    "reason": repl["reason"],
                    "status": "PATTERN_NOT_FOUND",
                })

        after_findings = scan_silent_except_pass(updated)

        if not dry_run and updated != original:
            backup = backup_root / rel
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup)
            write_text(path, updated)

        report["targets"].append({
            "path": rel,
            "name": target["name"],
            "changed": updated != original,
            "before_silent_except_pass_count": len(before_findings),
            "after_silent_except_pass_count": len(after_findings),
            "before_findings": before_findings,
            "after_findings": after_findings,
            "replacements": applied_replacements,
        })

        print(f"TARGET {rel}")
        print(f"  changed={updated != original}")
        print(f"  before_silent_except_pass_count={len(before_findings)}")
        print(f"  after_silent_except_pass_count={len(after_findings)}")
        for item in applied_replacements:
            print(f"  replacement={item['status']} | {item['reason']}")

    if not dry_run:
        report["backup_root"] = str(backup_root)

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "dryrun" if dry_run else "applied"
    report_json = out_dir / f"bys360_quality_10_10_p13_e_analysis_script_p0_fix_{suffix}_v1.json"
    report_md = out_dir / f"bys360_quality_10_10_p13_e_analysis_script_p0_fix_{suffix}_v1.md"

    write_text(report_json, json.dumps(report, ensure_ascii=False, indent=2))

    md = []
    md.append("# BYS360 P13-E Analysis Script P0 Fix")
    md.append("")
    md.append(f"- Mod: `{report['mode']}`")
    if report["backup_root"]:
        md.append(f"- Yedek: `{report['backup_root']}`")
    md.append("")
    md.append("## Hedefler")
    md.append("")
    for item in report["targets"]:
        md.append(f"- `{item['path']}`")
        md.append(f"  - changed: {item['changed']}")
        md.append(f"  - before silent except/pass: {item['before_silent_except_pass_count']}")
        md.append(f"  - after silent except/pass: {item['after_silent_except_pass_count']}")
    report_md.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"analysis_script_p0_fix_report_json={report_json}")
    print(f"analysis_script_p0_fix_report_md={report_md}")
    print("BYS360_QUALITY_10_10_P13_E_ANALYSIS_SCRIPT_P0_FIX_OK")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    apply(Path(args.project_root).resolve(), args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
