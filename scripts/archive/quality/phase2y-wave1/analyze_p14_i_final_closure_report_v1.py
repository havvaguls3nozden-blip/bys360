from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


EXPECTED_RULES = {
    "TECHNICAL_UI_TERM": 45,
    "LARGE_FILE_HARD": 4,
    "MANY_REPAIR_SCRIPTS": 1,
}

EXPECTED_P0 = 0
EXPECTED_P1 = 50

ACCEPTED_DECISIONS = {
    "TECHNICAL_UI_TERM": {
        "decision": "ACCEPTED_FALSE_POSITIVE_BY_P12_B",
        "reason": "P12-B teknik UI terim karar raporu ile kullanıcı yüzüne yansıyan gerçek teknik dil riski olarak kabul edilmedi.",
    },
    "LARGE_FILE_HARD": {
        "decision": "ACCEPTED_GOVERNED_REFACTOR_PLAN",
        "reason": "P13/P14 kararlarında 4 büyük dosya bilinçli refactor/gözetim planına bağlandı; yüksek riskli dosyalar doğrudan bölünmeyecek.",
    },
    "MANY_REPAIR_SCRIPTS": {
        "decision": "ACCEPTED_GOVERNANCE_ARCHIVE_PLAN",
        "reason": "Repair/fix/hotfix script yoğunluğu CI/arşiv yönetimi maddesi olarak izlenecek; canlı fonksiyon hatası değildir.",
    },
}


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def run_cmd(project_root: Path, cmd: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        cmd,
        cwd=str(project_root),
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "cmd": cmd,
        "returncode": completed.returncode,
        "stdout": completed.stdout or "",
        "stderr": completed.stderr or "",
    }


def parse_clean_audit(stdout: str) -> dict[str, int]:
    for line in stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("{") and '"P0"' in stripped and '"P1"' in stripped:
            return json.loads(stripped)
    return {}


def parse_p7(stdout: str) -> dict[str, Any]:
    parsed: dict[str, Any] = {
        "p1_findings_found": None,
        "rule_summary": {},
        "path_summary": {},
    }
    mode = None
    for line in stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("P1_findings_found="):
            try:
                parsed["p1_findings_found"] = int(stripped.split("=", 1)[1])
            except ValueError:
                parsed["p1_findings_found"] = None
            continue

        if stripped == "BYS360_QUALITY_10_10_P7_RULE_SUMMARY":
            mode = "rule"
            continue
        if stripped == "BYS360_QUALITY_10_10_P7_PATH_SUMMARY":
            mode = "path"
            continue
        if stripped.startswith("BYS360_QUALITY_10_10_P7_FIRST_FINDINGS"):
            mode = None
            continue
        if stripped.startswith("BYS360_QUALITY_10_10_P7_") and stripped not in {
            "BYS360_QUALITY_10_10_P7_RULE_SUMMARY",
            "BYS360_QUALITY_10_10_P7_PATH_SUMMARY",
        }:
            mode = None
            continue

        if mode in {"rule", "path"} and "|" in line:
            left, right = line.split("|", 1)
            left = left.strip()
            right = right.strip()
            if left.isdigit():
                parsed[f"{mode}_summary"][right] = int(left)

    return parsed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    print("BYS360_QUALITY_10_10_P14_I_FINAL_CLOSURE_REPORT_START")
    print(f"project_root={project_root}")

    clean_script = project_root / "scripts/windows/check_bys360_quality_10_10_p3_clean_audit.ps1"
    p7_script = project_root / "scripts/windows/analyze_bys360_quality_10_10_p7_findings.ps1"

    if not clean_script.exists():
        raise SystemExit(f"CLEAN_AUDIT_SCRIPT_NOT_FOUND: {clean_script}")
    if not p7_script.exists():
        raise SystemExit(f"P7_SCRIPT_NOT_FOUND: {p7_script}")

    clean_result = run_cmd(project_root, [
        "powershell",
        "-ExecutionPolicy", "Bypass",
        "-File", str(clean_script),
        "-ProjectRoot", str(project_root),
        "-FailOn", "never",
    ])
    p7_result = run_cmd(project_root, [
        "powershell",
        "-ExecutionPolicy", "Bypass",
        "-File", str(p7_script),
        "-ProjectRoot", str(project_root),
        "-Level", "P1",
        "-Limit", "240",
    ])

    clean_summary = parse_clean_audit(clean_result["stdout"])
    p7_summary = parse_p7(p7_result["stdout"])
    rule_summary = p7_summary.get("rule_summary") or {}

    closure_items = []
    for rule, expected_count in EXPECTED_RULES.items():
        actual_count = int(rule_summary.get(rule, 0))
        decision = ACCEPTED_DECISIONS[rule]
        closure_items.append({
            "rule": rule,
            "expected_count": expected_count,
            "actual_count": actual_count,
            "matches_expected": actual_count == expected_count,
            **decision,
        })

    unexpected_rules = {
        rule: count
        for rule, count in rule_summary.items()
        if rule not in EXPECTED_RULES
    }

    p0_ok = clean_summary.get("P0") == EXPECTED_P0
    p1_ok = clean_summary.get("P1") == EXPECTED_P1 and p7_summary.get("p1_findings_found") == EXPECTED_P1
    rule_ok = all(item["matches_expected"] for item in closure_items) and not unexpected_rules
    closure_ok = bool(p0_ok and p1_ok and rule_ok)

    result = {
        "closure_ok": closure_ok,
        "clean_audit": {
            "returncode": clean_result["returncode"],
            "summary": clean_summary,
        },
        "p7": {
            "returncode": p7_result["returncode"],
            "summary": p7_summary,
        },
        "expected": {
            "P0": EXPECTED_P0,
            "P1": EXPECTED_P1,
            "rules": EXPECTED_RULES,
        },
        "closure_items": closure_items,
        "unexpected_rules": unexpected_rules,
        "final_decision": {
            "decision": "QUALITY_10_10_CLOSURE_ACCEPTED" if closure_ok else "QUALITY_10_10_CLOSURE_NEEDS_REVIEW",
            "reason": (
                "P0 sıfır, P1 yalnızca karar/plan kapsamındaki 50 kalemden oluşuyor."
                if closure_ok
                else "Beklenen P0/P1 veya kural dağılımı ile mevcut dağılım arasında fark var."
            ),
        },
        "next_steps": [
            "Bu noktada kod değişikliği yapılmadan checkpoint alınmalı.",
            "Asistanın görünürlük/konum smoke testi tekrar yapılmalı.",
            "Waitress başlangıç logunda yeni ERROR oluşup oluşmadığı kontrol edilmeli.",
            "Mobil API optional startup hatası görünüyorsa ayrı takip edilmeli; kalite kapanışını bozmadığı ayrıca not edilmeli.",
            "Sonraki aşama olarak P15 script arşiv/CI düzen planı hazırlanabilir; doğrudan dosya silinmemeli.",
        ],
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    report_json = out_dir / "bys360_quality_10_10_p14_i_final_closure_report_v1.json"
    report_md = out_dir / "bys360_quality_10_10_p14_i_final_closure_report_v1.md"
    raw_clean = out_dir / "bys360_quality_10_10_p14_i_clean_audit_stdout_v1.txt"
    raw_p7 = out_dir / "bys360_quality_10_10_p14_i_p7_stdout_v1.txt"

    write_text(report_json, json.dumps(result, ensure_ascii=False, indent=2))
    write_text(raw_clean, clean_result["stdout"] + ("\nSTDERR:\n" + clean_result["stderr"] if clean_result["stderr"] else ""))
    write_text(raw_p7, p7_result["stdout"] + ("\nSTDERR:\n" + p7_result["stderr"] if p7_result["stderr"] else ""))

    md = []
    md.append("# BYS360 Quality 10/10 P14-I Final Closure Report")
    md.append("")
    md.append(f"- Closure OK: {closure_ok}")
    md.append(f"- Clean audit: {clean_summary}")
    md.append(f"- P1 findings: {p7_summary.get('p1_findings_found')}")
    md.append("")
    md.append("## Rule Summary")
    md.append("")
    for item in closure_items:
        md.append(
            f"- {item['rule']}: actual={item['actual_count']} expected={item['expected_count']} "
            f"decision={item['decision']}"
        )
        md.append(f"  - {item['reason']}")
    if unexpected_rules:
        md.append("")
        md.append("## Unexpected Rules")
        for rule, count in unexpected_rules.items():
            md.append(f"- {rule}: {count}")
    md.append("")
    md.append("## Final Decision")
    md.append("")
    md.append(f"- {result['final_decision']['decision']}: {result['final_decision']['reason']}")
    md.append("")
    md.append("## Next Steps")
    md.append("")
    for step in result["next_steps"]:
        md.append(f"- {step}")

    write_text(report_md, "\n".join(md) + "\n")

    print(f"closure_ok={closure_ok}")
    print("BYS360_QUALITY_10_10_P14_I_CLEAN_AUDIT")
    print(json.dumps(clean_summary, ensure_ascii=False))
    print("BYS360_QUALITY_10_10_P14_I_RULE_SUMMARY")
    for item in closure_items:
        print(
            f"{item['actual_count']:>4} | {item['rule']} | expected={item['expected_count']} | "
            f"decision={item['decision']} | ok={item['matches_expected']}"
        )
    print("BYS360_QUALITY_10_10_P14_I_UNEXPECTED_RULES")
    if unexpected_rules:
        for rule, count in unexpected_rules.items():
            print(f"{count:>4} | {rule}")
    else:
        print("-")
    print("BYS360_QUALITY_10_10_P14_I_FINAL_DECISION")
    print(f"decision={result['final_decision']['decision']}")
    print(f"reason={result['final_decision']['reason']}")
    print(f"final_closure_json={report_json}")
    print(f"final_closure_md={report_md}")
    print("BYS360_QUALITY_10_10_P14_I_FINAL_CLOSURE_REPORT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
