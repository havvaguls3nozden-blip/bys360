from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


TARGET_REL = "app/static/js/bys360_assistant_module.js"
P14_C_REL = "reports/quality/bys360_quality_10_10_p14_c_assistant_js_helper_split_dryrun_v1.json"

GLOBAL_WATCH = [
    "window", "document", "localStorage", "sessionStorage", "fetch",
    "root", "panel", "chat", "input", "csrf", "token", "BYS360",
]

FORBIDDEN_FOR_FIRST_APPLY = [
    "fetch(", "XMLHttpRequest", "axios.", "$.ajax",
    "document.", "window.", "localStorage", "sessionStorage",
    ".innerHTML", ".outerHTML", "insertAdjacentHTML",
    "addEventListener", "removeEventListener",
    "csrf", "token", "Authorization", "credentials",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def source_by_lines(text: str, start_line: int, end_line: int) -> str:
    lines = text.splitlines()
    if start_line < 1 or end_line < start_line or end_line > len(lines):
        return ""
    return "\n".join(lines[start_line - 1:end_line]).rstrip() + "\n"


def count_name_usages(text: str, name: str) -> list[int]:
    lines = text.splitlines()
    pattern = re.compile(r"\b" + re.escape(name) + r"\b")
    hits = []
    for idx, line in enumerate(lines, start=1):
        if pattern.search(line):
            hits.append(idx)
    return hits


def detect_forbidden(source: str) -> list[str]:
    low = source.lower()
    hits = []
    for item in FORBIDDEN_FOR_FIRST_APPLY:
        if item.lower() in low:
            hits.append(item)
    return hits


def detect_globals(source: str) -> list[str]:
    hits = []
    for item in GLOBAL_WATCH:
        if re.search(r"\b" + re.escape(item) + r"\b", source, flags=re.IGNORECASE):
            hits.append(item)
    return sorted(set(hits))


def detect_candidate_calls(source: str, candidate_names: set[str], own_name: str) -> list[str]:
    calls = []
    for name in sorted(candidate_names):
        if name == own_name:
            continue
        if re.search(r"\b" + re.escape(name) + r"\s*\(", source):
            calls.append(name)
    return calls


def classify_readiness(item: dict[str, Any], source: str, all_text: str, candidate_names: set[str]) -> tuple[str, str, str, dict[str, Any]]:
    name = str(item.get("name"))
    line_count = int(item.get("line_count") or 0)
    forbidden = detect_forbidden(source)
    globals_hit = detect_globals(source)
    candidate_calls = detect_candidate_calls(source, candidate_names, name)
    usage_lines = count_name_usages(all_text, name)

    # Usages include declaration itself and calls. If only one hit, likely unused/declaration.
    call_like_usage_lines = [
        ln for ln in usage_lines
        if ln < int(item.get("start_line") or 0) or ln > int(item.get("end_line") or 0)
    ]

    meta = {
        "forbidden_hits": forbidden,
        "global_hits": globals_hit,
        "candidate_calls": candidate_calls,
        "usage_lines": usage_lines,
        "external_usage_lines": call_like_usage_lines,
        "external_usage_count": len(call_like_usage_lines),
    }

    if forbidden:
        return (
            "NOT_READY_FOR_APPLY",
            "HIGH",
            "İlk split için yasaklı/bağlı ifade içeriyor.",
            meta,
        )

    if globals_hit:
        return (
            "REVIEW_BEFORE_APPLY",
            "MEDIUM",
            "Global referans ihtimali var; elle kontrol gerekir.",
            meta,
        )

    if candidate_calls:
        return (
            "GROUPED_READY_REVIEW",
            "LOW_MEDIUM",
            "Başka seçili helper adayına bağlı; taşınacaksa birlikte taşınmalı.",
            meta,
        )

    if line_count <= 16:
        return (
            "READY_FOR_OPTIONAL_P14_E",
            "LOW",
            "Küçük, dış bağımlılığı görünmeyen yardımcı fonksiyon; opsiyonel P14-E adayı olabilir.",
            meta,
        )

    return (
        "READY_FOR_REVIEWED_P14_E",
        "LOW_MEDIUM",
        "Risk düşük ama orta boy; P14-E öncesi elle gözden geçirilmeli.",
        meta,
    )


def make_smoke_plan(selected: list[dict[str, Any]]) -> list[str]:
    helper_names = ", ".join(str(item.get("name")) for item in selected)
    return [
        "Tarayıcıda BYS360 ana sayfasını aç; konsolda JavaScript hatası olmadığını kontrol et.",
        "BYS360 Asistan panelini aç/kapat; panel konumu, sürükleme ve görünürlük davranışı bozulmamalı.",
        "Asistana basit selamlaşma sorusu sor; yerel cevap akışı çalışmalı.",
        "Asistana mevcut ekranı sor; ekran bağlamı/menü yönlendirme cevabı gelmeli.",
        "Hava durumu/yerel cevap akışını tetikleyen bir soru sor; cevap formatı bozulmamalı.",
        "Performans, personel, destek/talep ekranlarında asistan yönlendirme metinlerini test et.",
        "F12 Console’da hata, undefined helper, missing function, CSP veya fetch hatası olmamalı.",
        f"P14-E yapılırsa özellikle şu helper adaylarının çıktıları korunmalı: {helper_names}",
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    target_path = project_root / TARGET_REL
    p14_c_path = project_root / P14_C_REL

    print("BYS360_QUALITY_10_10_P14_D_ASSISTANT_JS_SPLIT_READINESS_START")
    print(f"project_root={project_root}")
    print(f"target_file={target_path}")
    print(f"p14_c_report={p14_c_path}")

    if not target_path.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target_path}")
    if not p14_c_path.exists():
        raise SystemExit(f"P14_C_REPORT_NOT_FOUND: {p14_c_path}")

    text = read_text(target_path)
    p14_c = load_json(p14_c_path)

    selected = list(p14_c.get("selected_dryrun_candidates") or [])
    if not selected:
        raise SystemExit("NO_SELECTED_DRYRUN_CANDIDATES_IN_P14_C")

    candidate_names = {str(item.get("name")) for item in selected if item.get("name")}

    readiness_items = []
    for item in selected:
        start = int(item.get("start_line") or 0)
        end = int(item.get("end_line") or 0)
        source = source_by_lines(text, start, end)
        status, risk, reason, meta = classify_readiness(item, source, text, candidate_names)

        readiness_items.append({
            "name": item.get("name"),
            "start_line": start,
            "end_line": end,
            "line_count": int(item.get("line_count") or 0),
            "domain": item.get("domain"),
            "p14_c_decision": item.get("p14_c_decision"),
            "readiness": status,
            "risk": risk,
            "reason": reason,
            "meta": meta,
            "source_preview": source[:900],
        })

    by_readiness = Counter(item["readiness"] for item in readiness_items)
    by_risk = Counter(item["risk"] for item in readiness_items)

    ready_optional = [
        item for item in readiness_items
        if item["readiness"] in {"READY_FOR_OPTIONAL_P14_E", "READY_FOR_REVIEWED_P14_E", "GROUPED_READY_REVIEW"}
    ]
    blocked = [
        item for item in readiness_items
        if item["readiness"] in {"NOT_READY_FOR_APPLY", "REVIEW_BEFORE_APPLY"}
    ]

    if blocked:
        next_decision = {
            "decision": "NO_APPLY_UNTIL_BLOCKED_REVIEWED",
            "reason": "Seçili adaylar içinde global/bağlılık incelemesi gereken fonksiyon var; önce liste sadeleştirilmeli.",
        }
    elif len(ready_optional) >= 6:
        next_decision = {
            "decision": "P14_E_OPTIONAL_HELPER_SPLIT_APPLY_CAN_BE_PREPARED",
            "reason": "Seçili adaylar düşük riskli görünüyor; P14-E yine checkpoint + apply/dry-run + smoke test şartıyla hazırlanabilir.",
        }
    else:
        next_decision = {
            "decision": "KEEP_DRYRUN_ONLY",
            "reason": "Yeterli düşük riskli aday yok; sadece karar raporu olarak kapatılmalı.",
        }

    smoke_plan = make_smoke_plan(readiness_items)

    result = {
        "mode": "READINESS_ONLY_NO_CODE_CHANGE",
        "target_file": TARGET_REL,
        "p14_c_report": P14_C_REL,
        "selected_candidate_count": len(selected),
        "ready_optional_count": len(ready_optional),
        "blocked_or_review_count": len(blocked),
        "readiness_summary": dict(by_readiness.most_common()),
        "risk_summary": dict(by_risk.most_common()),
        "readiness_items": readiness_items,
        "ready_optional_items": ready_optional,
        "blocked_or_review_items": blocked,
        "smoke_test_plan": smoke_plan,
        "next_decision": next_decision,
        "safety_rules": [
            "P14-D kod değiştirmez.",
            "P14-E hazırlanırsa önce checkpoint alınmalı.",
            "P14-E varsayılan dry-run olmalı; gerçek uygulama için açık -Apply parametresi olmalı.",
            "P14-E sonrasında JS console smoke test yapılmadan kalite kapatma yapılmamalı.",
            "Asistanın chat, ekran tanıma, yönlendirme ve hava durumu/yerel cevap akışları test edilmelidir.",
        ],
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / "bys360_quality_10_10_p14_d_assistant_js_split_readiness_v1.json"
    md_out = out_dir / "bys360_quality_10_10_p14_d_assistant_js_split_readiness_v1.md"
    smoke_out = out_dir / "bys360_quality_10_10_p14_d_assistant_js_smoke_plan_v1.md"

    write_text(json_out, json.dumps(result, ensure_ascii=False, indent=2))

    md = []
    md.append("# BYS360 P14-D Assistant JS Split Readiness")
    md.append("")
    md.append(f"- Mod: `{result['mode']}`")
    md.append(f"- Seçili aday: {len(selected)}")
    md.append(f"- Opsiyonel hazır aday: {len(ready_optional)}")
    md.append(f"- İnceleme/bloke: {len(blocked)}")
    md.append("")
    md.append("## Readiness Özeti")
    md.append("")
    for key, count in by_readiness.most_common():
        md.append(f"- {key}: {count}")
    md.append("")
    md.append("## Adaylar")
    md.append("")
    for item in readiness_items:
        md.append(f"- `{item['name']}` line {item['start_line']}-{item['end_line']} ({item['line_count']} satır): {item['readiness']} / risk={item['risk']} / {item['reason']}")
    md.append("")
    md.append("## Sonraki Karar")
    md.append("")
    md.append(f"- {next_decision['decision']}: {next_decision['reason']}")
    md.append("")
    md.append("## Güvenlik Kuralları")
    md.append("")
    for rule in result["safety_rules"]:
        md.append(f"- {rule}")
    write_text(md_out, "\n".join(md) + "\n")

    smoke_md = []
    smoke_md.append("# BYS360 P14-D Assistant JS Smoke Test Plan")
    smoke_md.append("")
    for idx, item in enumerate(smoke_plan, start=1):
        smoke_md.append(f"{idx}. {item}")
    write_text(smoke_out, "\n".join(smoke_md) + "\n")

    print(f"mode={result['mode']}")
    print(f"selected_candidate_count={len(selected)}")
    print(f"ready_optional_count={len(ready_optional)}")
    print(f"blocked_or_review_count={len(blocked)}")
    print("BYS360_QUALITY_10_10_P14_D_READINESS_SUMMARY")
    for key, count in by_readiness.most_common():
        print(f"{count:>4} | {key}")
    print("BYS360_QUALITY_10_10_P14_D_CANDIDATE_READINESS")
    for item in readiness_items:
        print(f"{item['start_line']:>5}-{item['end_line']:<5} | {item['line_count']:>4} | {item['readiness']} | {item['risk']} | {item['name']}")
    print("BYS360_QUALITY_10_10_P14_D_NEXT_DECISION")
    print(f"decision={next_decision['decision']}")
    print(f"reason={next_decision['reason']}")
    print("BYS360_QUALITY_10_10_P14_D_SMOKE_TEST_PLAN")
    for idx, item in enumerate(smoke_plan, start=1):
        print(f"{idx}. {item}")
    print(f"assistant_js_split_readiness_json={json_out}")
    print(f"assistant_js_split_readiness_md={md_out}")
    print(f"assistant_js_smoke_plan_md={smoke_out}")
    print("BYS360_QUALITY_10_10_P14_D_ASSISTANT_JS_SPLIT_READINESS_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
