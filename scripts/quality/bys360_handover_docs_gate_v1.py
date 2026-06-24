#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

PACKAGE = "BYS360_HANDOVER_DOCS_GATE_V1"

REQUIRED_FILES = [
    "DEPLOYMENT.md",
    "BACKUP_RUNBOOK.md",
    "SECURITY.md",
    "docs/handover/README.md",
    "docs/handover/BYS360_DEVIR_PAKETI_V1.md",
    "docs/handover/BYS360_KURULUM_REHBERI.md",
    "docs/handover/BYS360_CANLIYA_ALMA_REHBERI.md",
    "docs/handover/BYS360_BAKIM_RUNBOOK.md",
    "docs/handover/BYS360_GUVENLIK_KVKK_NOTLARI.md",
    "docs/handover/BYS360_MODUL_ENVANTERI.md",
    "docs/handover/BYS360_RISK_VE_SUREKLILIK_PLANI.md",
]

REQUIRED_TERMS = {
    "DEPLOYMENT.md": ["Canlıya", "Rollback", "Temiz release"],
    "BACKUP_RUNBOOK.md": ["PostgreSQL", "Restore", "Yedek"],
    "SECURITY.md": [".env", "Release", "Yetki", "AI karar vermez"],
    "docs/handover/BYS360_MODUL_ENVANTERI.md": ["Personel", "Performans", "İletişim", "AI"],
    "docs/handover/BYS360_RISK_VE_SUREKLILIK_PLANI.md": ["Tek geliştirici", "Süreklilik", "100/100"],
}

SECRET_PATTERN = re.compile(r"(?i)(DATABASE_URL|SECRET_KEY|PASSWORD|TOKEN|API_KEY)\s*=\s*([^\s#'\"]{12,})")
PLACEHOLDER_OK = ("example", "placeholder", "change_me", "changeme", "dummy", "sample", "your_", "not_real", "buraya", "<", "***", "%DATABASE_URL%")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--output-dir", default="reports/handover/handover_docs_gate_v1")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "package": PACKAGE,
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "project_root": str(root),
        "status": "PASS",
        "failures": [],
        "passes": [],
    }

    for rel in REQUIRED_FILES:
        path = root / rel
        if not path.exists():
            report["failures"].append({"type": "missing_file", "path": rel})
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if len(text.strip()) < 400:
            report["failures"].append({"type": "too_short", "path": rel, "chars": len(text.strip())})
        else:
            report["passes"].append({"type": "file_present", "path": rel, "chars": len(text.strip())})
        for term in REQUIRED_TERMS.get(rel, []):
            if term not in text:
                report["failures"].append({"type": "missing_required_term", "path": rel, "term": term})
        for match in SECRET_PATTERN.finditer(text):
            preview = match.group(0)
            low = preview.lower()
            if any(token in low for token in PLACEHOLDER_OK):
                continue
            line = text.count("\n", 0, match.start()) + 1
            report["failures"].append({"type": "possible_secret_literal", "path": rel, "line": line, "preview": preview[:120]})

    if report["failures"]:
        report["status"] = "FAIL"

    json_path = out_dir / "BYS360_HANDOVER_DOCS_GATE_V1_REPORT.json"
    md_path = out_dir / "BYS360_HANDOVER_DOCS_GATE_V1_REPORT.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [f"# {PACKAGE} Raporu", "", f"- Durum: **{report['status']}**", f"- PASS: {len(report['passes'])}", f"- FAIL: {len(report['failures'])}", ""]
    if report["failures"]:
        lines.append("## Eksikler")
        for item in report["failures"]:
            lines.append(f"- `{item.get('path')}` — {item.get('type')} {item.get('term', '')}")
    else:
        lines.append("## Sonuç")
        lines.append("Devir, kurulum, canlıya alma, bakım, güvenlik, modül envanteri ve süreklilik dokümanları mevcut.")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"status": report["status"], "failures": len(report["failures"]), "reports": {"json": str(json_path), "md": str(md_path)}}, ensure_ascii=False, indent=2))
    return 1 if report["status"] != "PASS" else 0


if __name__ == "__main__":
    raise SystemExit(main())
