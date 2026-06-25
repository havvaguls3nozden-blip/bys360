from pathlib import Path
from datetime import datetime
import json

ROOT = Path(".").resolve()

A10B_JSON = Path("reports/quality/BYS360_A10B_PHASE_DEV_DEBUG_PRECISION_AUDIT.json")
OUT_JSON = Path("reports/quality/BYS360_A10C_HARD_UI_TECHNICAL_LANGUAGE_PLAN.json")
OUT_MD = Path("reports/quality/BYS360_A10C_HARD_UI_TECHNICAL_LANGUAGE_PLAN.md")

TERM_REPLACEMENTS = {
    "traceback": "İşlem sırasında teknik bir hata oluştu. Lütfen sistem yöneticisine bildiriniz.",
    "stacktrace": "İşlem sırasında teknik bir hata oluştu. Lütfen sistem yöneticisine bildiriniz.",
    "unauthorized_scope": "Bu işlem için yetkiniz bulunmamaktadır.",
    "raw error": "İşlem tamamlanamadı. Lütfen tekrar deneyiniz.",
    "api error": "Servise şu anda ulaşılamadı. Lütfen tekrar deneyiniz.",
    "exception": "Beklenmeyen bir hata oluştu.",
    "pytest": "Kalite kontrol",
    "ruff": "Kod kalite kontrolü",
    "compileall": "Derleme kontrolü",
    "endpoint": "Servis bağlantısı",
    "workflow state": "Süreç durumu",
}

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))

def suggest_for_term(term: str):
    low = str(term).lower()
    for key, value in TERM_REPLACEMENTS.items():
        if key in low:
            return value
    return "Teknik ifade yerine sade ve kurumsal Türkçe mesaj kullanılmalıdır."

def main():
    if not A10B_JSON.exists():
        raise SystemExit("A10B raporu bulunamadı. Önce A10B çalışmalı.")

    a10b = read_json(A10B_JSON)
    hard_files = a10b.get("hard_ui_files", [])

    plan = []

    for item in hard_files:
        path = item.get("path")
        hard_hits = item.get("hard_hits", [])

        suggestions = []
        for hit in hard_hits:
            term = hit.get("term", "")
            suggestions.append({
                "line": hit.get("line"),
                "term": term,
                "sample": hit.get("sample"),
                "suggested_message": suggest_for_term(term),
            })

        plan.append({
            "path": path,
            "hard_count": item.get("hard_count"),
            "suggestions": suggestions,
        })

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A10C_HARD_UI_TECHNICAL_LANGUAGE_PLAN",
        "mode": "plan_only",
        "hard_ui_file_count": len(plan),
        "hard_ui_hit_total": sum(len(x["suggestions"]) for x in plan),
        "plan": plan,
        "ok": len(plan) == 0,
        "next_action": "A10D aşamasında güvenli otomatik metin dönüşümü veya manuel patch uygulanmalı.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A10C Hard UI Teknik Dil Düzeltme Planı",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Özet",
        "",
        f"- Hard UI file count: {result['hard_ui_file_count']}",
        f"- Hard UI hit total: {result['hard_ui_hit_total']}",
        f"- A10C OK: {result['ok']}",
        "",
        "## Düzeltme Planı",
        "",
        "```json",
        json.dumps(result["plan"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Not",
        "",
        "Bu aşama dosya değiştirmez. A10D aşamasında yedek alınarak güvenli dönüşüm uygulanacaktır.",
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("A10C_REPORT_JSON:", OUT_JSON)
    print("A10C_REPORT_MD:", OUT_MD)
    print("A10C_HARD_UI_FILE_COUNT:", result["hard_ui_file_count"])
    print("A10C_HARD_UI_HIT_TOTAL:", result["hard_ui_hit_total"])
    print("A10C_OK:", result["ok"])

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
