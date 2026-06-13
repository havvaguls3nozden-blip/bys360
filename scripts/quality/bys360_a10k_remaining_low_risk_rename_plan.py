from pathlib import Path
from datetime import datetime
import json
import re

ROOT = Path(".").resolve()

A10I_JSON = Path("reports/quality/BYS360_A10I_REMAINING_RUNTIME_RENAME_KEEP_PLAN.json")
OUT_JSON = Path("reports/quality/BYS360_A10K_REMAINING_LOW_RISK_RENAME_PLAN.json")
OUT_MD = Path("reports/quality/BYS360_A10K_REMAINING_LOW_RISK_RENAME_PLAN.md")

TARGET_DECISION = "rename_possible_but_runtime_smoke_required"

CUSTOM_RENAME_WORDS = {
    "overlay": "assets",
    "repair": "maintenance",
    "hotfix": "maintenance",
    "faz": "module",
    "phase": "module",
    "debug": "diagnostics",
    "legacy": "compat",
    "disabled": "archived",
    "tmp": "temporary",
    "temp": "temporary",
    "old": "archive",
    "bak": "backup",
}

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))

def custom_suggest(path: str):
    p = Path(path)
    name = p.name
    new_name = name

    for old, new in CUSTOM_RENAME_WORDS.items():
        new_name = re.sub(old, new, new_name, flags=re.I)

    if new_name == name:
        return None

    return str(p.with_name(new_name)).replace("\\", "/")

def main():
    if not A10I_JSON.exists():
        raise SystemExit("A10I raporu bulunamadı. Önce A10I çalışmalı.")

    a10i = read_json(A10I_JSON)

    remaining_low_risk = [
        item for item in a10i.get("plan", [])
        if item.get("a10i_decision") == TARGET_DECISION
    ]

    plan = []
    for item in remaining_low_risk:
        suggested = item.get("suggested_new_path") or custom_suggest(item.get("path", ""))

        decision = "rename_with_custom_suggestion" if suggested else "keep_allowlist_candidate"

        row = {
            "path": item.get("path"),
            "name": item.get("name"),
            "hits": item.get("hits"),
            "reference_count_now": item.get("reference_count_now"),
            "existing_suggested_new_path": item.get("suggested_new_path"),
            "custom_suggested_new_path": suggested,
            "a10k_decision": decision,
            "reason": (
                "Referans bulunmadı; özel isim önerisiyle güvenli rename yapılabilir."
                if suggested
                else "Otomatik güvenli isim önerisi üretilemedi; keep allowlist daha güvenli."
            ),
        }
        plan.append(row)

    by_decision = {}
    for row in plan:
        by_decision[row["a10k_decision"]] = by_decision.get(row["a10k_decision"], 0) + 1

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A10K_REMAINING_LOW_RISK_RENAME_PLAN",
        "mode": "plan_only",
        "remaining_low_risk_count": len(plan),
        "by_decision": by_decision,
        "plan": plan,
        "ok": len(plan) == 0,
        "next_action": "A10L: custom suggestion olanlar rename edilir; öneri üretilemeyenler keep allowlist'e alınır.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A10K Kalan Düşük Riskli Rename Planı",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Özet",
        "",
        f"- Remaining low risk count: {result['remaining_low_risk_count']}",
        f"- A10K OK: {result['ok']}",
        "",
        "## Karar Dağılımı",
        "",
        "```json",
        json.dumps(result["by_decision"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Plan",
        "",
        "```json",
        json.dumps(result["plan"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Not",
        "",
        "Bu aşama dosya değiştirmez. A10L aşamasında sadece custom suggestion üretilen düşük riskli dosyalar yedekli yeniden adlandırılacaktır.",
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("A10K_REPORT_JSON:", OUT_JSON)
    print("A10K_REPORT_MD:", OUT_MD)
    print("A10K_REMAINING_LOW_RISK_COUNT:", result["remaining_low_risk_count"])
    print("A10K_BY_DECISION:", json.dumps(result["by_decision"], ensure_ascii=False))
    print("A10K_OK:", result["ok"])

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
