from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


TARGET_REL = "app/static/js/bys360_assistant_module.js"
P14_B_REL = "reports/quality/bys360_quality_10_10_p14_b_assistant_js_split_decision_v1.json"
PROPOSED_HELPER_REL = "app/static/js/bys360_assistant_helpers_v1.js"

HARD_BLOCK_RISKS = {
    "fetch_api",
    "csrf_auth",
    "dom_write",
    "event",
    "security_dynamic",
    "assistant_flow",
    "storage",
}

SOFT_BLOCK_RISKS = {
    "dom_read",
    "timer",
}

DEFAULT_MAX_FUNCTIONS = 12


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8", errors="ignore"))


def find_function_source_by_lines(text: str, start_line: int, end_line: int) -> str:
    lines = text.splitlines()
    if start_line < 1 or end_line < start_line or end_line > len(lines):
        return ""
    return "\n".join(lines[start_line - 1:end_line]).rstrip() + "\n"


def function_name_pattern(name: str) -> re.Pattern:
    return re.compile(r"\b" + re.escape(name) + r"\s*\(")


def detect_cross_calls(candidate: dict[str, Any], all_names: set[str], source: str) -> list[str]:
    name = str(candidate.get("name") or "")
    calls = []
    for other in sorted(all_names):
        if other == name:
            continue
        if function_name_pattern(other).search(source):
            calls.append(other)
    return calls


def detect_globals(source: str) -> list[str]:
    # Lightweight scan for common global-coupling names that make helper extraction risky.
    globals_to_watch = [
        "document",
        "window",
        "root",
        "panel",
        "chat",
        "input",
        "localStorage",
        "sessionStorage",
        "fetch",
        "csrf",
        "token",
        "BYS360",
    ]
    hits = []
    for name in globals_to_watch:
        if re.search(r"\b" + re.escape(name) + r"\b", source, flags=re.IGNORECASE):
            hits.append(name)
    return sorted(set(hits))


def classify_candidate(candidate: dict[str, Any], source: str) -> tuple[str, str, str]:
    risks = set(candidate.get("risk_hits") or [])
    line_count = int(candidate.get("line_count") or 0)
    name = str(candidate.get("name") or "")
    globals_hit = detect_globals(source)

    if risks & HARD_BLOCK_RISKS:
        return (
            "BLOCKED_COUPLED_FLOW",
            "HIGH",
            "API/CSRF/DOM yazma/event/storage/asistan akışı veya güvenlik bağı var.",
        )

    if risks & SOFT_BLOCK_RISKS:
        return (
            "REVIEW_ONLY_SOFT_COUPLING",
            "MEDIUM",
            "DOM okuma/timer gibi davranış bağı olabilir; P14-C taşıma adayına alınmaz.",
        )

    if globals_hit:
        return (
            "REVIEW_GLOBAL_COUPLING",
            "MEDIUM",
            "Global DOM/window/storage veya sistem değişkeni referansı olabilir; elle kontrol gerekir.",
        )

    if line_count > 60:
        return (
            "REVIEW_TOO_LARGE_FOR_FIRST_SPLIT",
            "MEDIUM",
            "İlk split için fazla uzun; küçük yardımcılarla başlamak daha güvenli.",
        )

    if line_count <= 25:
        return (
            "SAFE_DRYRUN_MOVE_CANDIDATE",
            "LOW_MEDIUM",
            "Küçük, riskli kategori içermeyen yardımcı fonksiyon; dry-run planına alınabilir.",
        )

    return (
        "REVIEW_MEDIUM_HELPER",
        "MEDIUM",
        "Riskli kategori yok ama orta boy; ilk uygulamaya alınmadan önce elle kontrol gerekir.",
    )


def make_helper_preview(candidates: list[dict[str, Any]], target_text: str) -> str:
    chunks = []
    chunks.append("/*")
    chunks.append(" * BYS360 Assistant Helpers V1")
    chunks.append(" * P14-C dry-run preview only. This file is NOT generated into app/static/js by this package.")
    chunks.append(" * Functions below are candidate pure/small helpers selected for future review.")
    chunks.append(" */")
    chunks.append("")
    chunks.append("(function (window) {")
    chunks.append("  'use strict';")
    chunks.append("  const BYS360AssistantHelpersV1 = {};")
    chunks.append("")

    for item in candidates:
        source = find_function_source_by_lines(
            target_text,
            int(item["start_line"]),
            int(item["end_line"]),
        )
        indented = "\n".join("  " + line for line in source.splitlines())
        chunks.append(f"  // Candidate: {item['name']} lines {item['start_line']}-{item['end_line']}")
        chunks.append(indented)
        chunks.append(f"  BYS360AssistantHelpersV1.{item['name']} = {item['name']};")
        chunks.append("")

    chunks.append("  window.BYS360AssistantHelpersV1 = BYS360AssistantHelpersV1;")
    chunks.append("})(window);")
    chunks.append("")
    return "\n".join(chunks)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--max-functions", type=int, default=DEFAULT_MAX_FUNCTIONS)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    target_path = project_root / TARGET_REL
    p14_b_path = project_root / P14_B_REL

    print("BYS360_QUALITY_10_10_P14_C_ASSISTANT_JS_HELPER_SPLIT_DRYRUN_START")
    print(f"project_root={project_root}")
    print(f"target_file={target_path}")
    print(f"p14_b_report={p14_b_path}")

    if not target_path.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target_path}")
    if not p14_b_path.exists():
        raise SystemExit(f"P14_B_REPORT_NOT_FOUND: {p14_b_path}")

    target_text = read_text(target_path)
    p14_b = load_json(p14_b_path)

    low_risk = list(p14_b.get("low_risk_helper_candidates") or [])
    if not low_risk:
        raise SystemExit("NO_LOW_RISK_HELPER_CANDIDATES_IN_P14_B")

    all_candidate_names = {str(item.get("name")) for item in low_risk if item.get("name")}

    evaluated = []
    for item in low_risk:
        start = int(item.get("start_line") or 0)
        end = int(item.get("end_line") or 0)
        source = find_function_source_by_lines(target_text, start, end)
        decision, risk, reason = classify_candidate(item, source)
        cross_calls = detect_cross_calls(item, all_candidate_names, source)
        globals_hit = detect_globals(source)

        # Cross-call inside the selected low-risk helper group is okay for dry-run,
        # but it means candidates should move together. Mark separately.
        if decision == "SAFE_DRYRUN_MOVE_CANDIDATE" and cross_calls:
            decision = "SAFE_DRYRUN_GROUPED_CANDIDATE"
            reason = "Başka düşük riskli yardımcı adaya çağrı var; taşınacaksa birlikte taşınmalı."

        evaluated.append({
            "name": item.get("name"),
            "start_line": start,
            "end_line": end,
            "line_count": int(item.get("line_count") or 0),
            "domain": item.get("domain"),
            "p14_b_decision": item.get("decision"),
            "risk_hits": item.get("risk_hits") or [],
            "p14_c_decision": decision,
            "risk": risk,
            "reason": reason,
            "cross_calls_to_low_risk_candidates": cross_calls,
            "global_hits": globals_hit,
            "source_preview": source[:900],
        })

    safe_candidates = [
        item for item in evaluated
        if item["p14_c_decision"] in {"SAFE_DRYRUN_MOVE_CANDIDATE", "SAFE_DRYRUN_GROUPED_CANDIDATE"}
    ]

    # Keep first plan very small and conservative.
    selected = safe_candidates[: max(0, args.max_functions)]
    selected_names = {item["name"] for item in selected}

    # If a selected function calls another safe candidate that is not selected, pull it in if within max.
    changed = True
    while changed and len(selected) < args.max_functions:
        changed = False
        for item in list(selected):
            for callee in item["cross_calls_to_low_risk_candidates"]:
                if callee in selected_names:
                    continue
                found = next((x for x in safe_candidates if x["name"] == callee), None)
                if found is not None and len(selected) < args.max_functions:
                    selected.append(found)
                    selected_names.add(callee)
                    changed = True

    blocked_or_review = [item for item in evaluated if item not in selected]

    helper_preview = make_helper_preview(selected, target_text) if selected else ""

    by_decision = Counter(item["p14_c_decision"] for item in evaluated)
    by_domain = Counter(item["domain"] for item in evaluated)

    result = {
        "mode": "DRYRUN_PLAN_ONLY_NO_CODE_CHANGE",
        "target_file": TARGET_REL,
        "proposed_helper_file": PROPOSED_HELPER_REL,
        "p14_b_report": P14_B_REL,
        "low_risk_from_p14_b_count": len(low_risk),
        "evaluated_candidate_count": len(evaluated),
        "safe_candidate_count": len(safe_candidates),
        "selected_dryrun_move_count": len(selected),
        "max_functions": args.max_functions,
        "decision_summary": dict(by_decision.most_common()),
        "domain_summary": dict(by_domain.most_common()),
        "selected_dryrun_candidates": selected,
        "safe_candidates_all": safe_candidates,
        "blocked_or_review_candidates": blocked_or_review,
        "helper_preview_text": helper_preview,
        "next_decision": {
            "decision": "NO_APPLY_YET_REVIEW_PLAN",
            "reason": "Bu paket sadece dry-run plan üretir. Uygulama için P14-D gerekir; önce seçilen fonksiyonlar elle gözden geçirilmeli ve tarayıcı smoke planı hazırlanmalı.",
        },
        "safety_rules": [
            "P14-C kaynak JS dosyasını değiştirmez.",
            "Yeni helper dosyasını app/static/js içine yazmaz; sadece raporda preview üretir.",
            "API/fetch, CSRF/token, DOM yazma, event listener, storage ve asistan/chat akışları taşınmaz.",
            "İlk gerçek split yapılacaksa en fazla küçük saf yardımcı fonksiyonlarla başlanmalı.",
            "P14-D yapılmadan önce checkpoint, JS smoke test planı ve geri alma planı hazırlanmalı.",
        ],
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / "bys360_quality_10_10_p14_c_assistant_js_helper_split_dryrun_v1.json"
    md_out = out_dir / "bys360_quality_10_10_p14_c_assistant_js_helper_split_dryrun_v1.md"
    preview_out = out_dir / "bys360_quality_10_10_p14_c_assistant_helpers_v1_preview.js"

    write_text(json_out, json.dumps(result, ensure_ascii=False, indent=2))
    write_text(preview_out, helper_preview)

    md = []
    md.append("# BYS360 P14-C Assistant JS Helper Split Dry-Run")
    md.append("")
    md.append(f"- Mod: `{result['mode']}`")
    md.append(f"- Hedef dosya: `{TARGET_REL}`")
    md.append(f"- Önerilen helper dosyası: `{PROPOSED_HELPER_REL}`")
    md.append(f"- P14-B düşük riskli aday: {len(low_risk)}")
    md.append(f"- P14-C güvenli aday: {len(safe_candidates)}")
    md.append(f"- İlk dry-run seçimi: {len(selected)}")
    md.append("")
    md.append("## Karar Özeti")
    md.append("")
    for key, count in by_decision.most_common():
        md.append(f"- {key}: {count}")
    md.append("")
    md.append("## İlk Dry-Run Taşıma Adayları")
    md.append("")
    if selected:
        for item in selected:
            md.append(f"- `{item['name']}` line {item['start_line']}-{item['end_line']} ({item['line_count']} satır), domain={item['domain']}, decision={item['p14_c_decision']}")
    else:
        md.append("- İlk dry-run taşıma adayı seçilmedi.")
    md.append("")
    md.append("## İnceleme / Bloke Edilenler")
    md.append("")
    for item in blocked_or_review[:120]:
        md.append(f"- `{item['name']}` line {item['start_line']}-{item['end_line']} — {item['p14_c_decision']} — {item['reason']}")
    md.append("")
    md.append("## Sonraki Karar")
    md.append("")
    md.append(f"- {result['next_decision']['decision']}: {result['next_decision']['reason']}")
    md.append("")
    md.append("## Güvenlik Kuralları")
    md.append("")
    for rule in result["safety_rules"]:
        md.append(f"- {rule}")
    write_text(md_out, "\n".join(md) + "\n")

    print(f"mode={result['mode']}")
    print(f"low_risk_from_p14_b_count={len(low_risk)}")
    print(f"evaluated_candidate_count={len(evaluated)}")
    print(f"safe_candidate_count={len(safe_candidates)}")
    print(f"selected_dryrun_move_count={len(selected)}")
    print("BYS360_QUALITY_10_10_P14_C_DECISION_SUMMARY")
    for key, count in by_decision.most_common():
        print(f"{count:>4} | {key}")
    print("BYS360_QUALITY_10_10_P14_C_SELECTED_DRYRUN_CANDIDATES")
    for item in selected:
        print(f"{item['start_line']:>5}-{item['end_line']:<5} | {item['line_count']:>4} | {item['domain']} | {item['name']} | {item['p14_c_decision']}")
    print("BYS360_QUALITY_10_10_P14_C_REVIEW_OR_BLOCKED")
    for item in blocked_or_review[:args.max_functions * 4]:
        print(f"{item['start_line']:>5}-{item['end_line']:<5} | {item['line_count']:>4} | {item['domain']} | {item['name']} | {item['p14_c_decision']}")
    print("BYS360_QUALITY_10_10_P14_C_NEXT_DECISION")
    print(f"decision={result['next_decision']['decision']}")
    print(f"reason={result['next_decision']['reason']}")
    print(f"assistant_js_helper_split_dryrun_json={json_out}")
    print(f"assistant_js_helper_split_dryrun_md={md_out}")
    print(f"assistant_helpers_preview_js={preview_out}")
    print("BYS360_QUALITY_10_10_P14_C_ASSISTANT_JS_HELPER_SPLIT_DRYRUN_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
