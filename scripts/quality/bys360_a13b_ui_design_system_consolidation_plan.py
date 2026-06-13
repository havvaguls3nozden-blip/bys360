from __future__ import annotations

from pathlib import Path
from datetime import datetime
from collections import Counter
import json
import os
import re
import subprocess

ROOT = Path(".").resolve()
QUALITY = ROOT / "reports" / "quality"

A13A_JSON = QUALITY / "BYS360_A13A_UI_DESIGN_SYSTEM_INVENTORY.json"

OUT_JSON = QUALITY / "BYS360_A13B_UI_DESIGN_SYSTEM_CONSOLIDATION_PLAN.json"
OUT_MD = QUALITY / "BYS360_A13B_UI_DESIGN_SYSTEM_CONSOLIDATION_PLAN.md"

CANONICAL_COMPONENTS = {
    "card": {
        "target": "bys-card",
        "variants": ["bys-card", "bys-card--soft", "bys-card--glass", "bys-card--metric", "bys-card--section"],
        "sources": ["glass-card", "card", "panel-card", "stat-card", "ai-card", "summary-card", "bys-md-card", "portal-card", "pmc-card"],
    },
    "button": {
        "target": "bys-btn",
        "variants": ["bys-btn", "bys-btn--primary", "bys-btn--secondary", "bys-btn--danger", "bys-btn--ghost", "bys-btn--sm"],
        "sources": ["btn", "btn-soft", "mini-btn", "pmc-btn", "pub-btn", "performance-btn", "btn-danger", "btn-sm"],
    },
    "badge": {
        "target": "bys-badge",
        "variants": ["bys-badge", "bys-badge--success", "bys-badge--warning", "bys-badge--danger", "bys-badge--info", "bys-badge--muted"],
        "sources": ["badge", "ai-badge", "bys-md-badge", "pmc-badge"],
    },
    "pill_chip": {
        "target": "bys-pill",
        "variants": ["bys-pill", "bys-pill--soft", "bys-chip", "bys-chip--active"],
        "sources": ["pill", "bys-pill", "matrix-pill", "tone-pill", "wf-pill", "chip"],
    },
    "form": {
        "target": "bys-form",
        "variants": ["bys-form", "bys-form-grid", "bys-input", "bys-select", "bys-label"],
        "sources": ["form-group", "form-label", "form-control", "form-input", "form-select", "form-grid"],
    },
    "table": {
        "target": "bys-table",
        "variants": ["bys-table", "bys-table-wrap", "bys-table--clean", "bys-table--responsive"],
        "sources": ["table", "table-wrap", "table-responsive", "table-clean", "ai-table-wrap"],
    },
    "alert": {
        "target": "bys-alert",
        "variants": ["bys-alert", "bys-alert--info", "bys-alert--success", "bys-alert--warning", "bys-alert--danger"],
        "sources": ["alert"],
    },
}

RISK_WEIGHTS = {
    "important_css": 10,
    "hardcoded_hex_color": 8,
    "hardcoded_rgb_color": 8,
    "inline_style": 7,
    "pixel_fixed_width": 6,
    "pixel_fixed_height": 6,
    "absolute_position": 5,
    "negative_margin": 4,
}

PHASES = [
    {
        "phase": "A13C",
        "title": "Design token temeli",
        "goal": "Renk, radius, shadow, spacing ve font token dosyasını oluşturmak.",
        "safe_change": True,
        "expected_files": ["app/static/css/bys360_design_tokens_v1.css"],
    },
    {
        "phase": "A13D",
        "title": "Ortak component sözleşmesi",
        "goal": "Kart, buton, badge, pill, form ve tablo için ortak sınıf hedeflerini belgelemek.",
        "safe_change": True,
        "expected_files": ["reports/quality", "app/static/css/bys360_components_v1.css"],
    },
    {
        "phase": "A13E",
        "title": "CSS duplicate selector temizlik planı",
        "goal": "Tekrar eden selectorları risk sırasına göre gruplayıp ilk güvenli temizlik dalgasını hazırlamak.",
        "safe_change": False,
        "expected_files": ["app/static/css"],
    },
    {
        "phase": "A13F",
        "title": "Inline style azaltma",
        "goal": "Template içindeki inline style kullanımını parça parça ortak sınıflara almak.",
        "safe_change": False,
        "expected_files": ["app/templates"],
    },
    {
        "phase": "A13G",
        "title": "Mobil CSS sadeleştirme",
        "goal": "iOS/Android responsive dosyalarındaki tekrarları tek mobil standart altında toplamak.",
        "safe_change": False,
        "expected_files": ["app/static/css/bys360_mobile_*", "app/static/css/bys360_ios_*", "app/static/css/bys360_android_*"],
    },
]


def read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))
    except Exception as exc:
        return {"_read_error": str(exc), "_path": str(path)}


def run_cmd(cmd, timeout=1800):
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="ignore",
        env={
            **os.environ,
            "PYTHONIOENCODING": "utf-8",
            "BYS360_RUN_LEGACY_ARCHITECTURE_TESTS": "1",
        },
        timeout=timeout,
    )
    return {
        "cmd": " ".join(map(str, cmd)),
        "returncode": proc.returncode,
        "combined": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-20000:],
    }


def parse_pytest_summary(text: str) -> dict:
    summary = {}
    pattern = r"(\d+)\s+(failed|passed|error|errors|skipped|deselected|warning|warnings)\b"
    for num, key in re.findall(pattern, text or "", flags=re.IGNORECASE):
        key = key.lower()
        if key == "error":
            key = "errors"
        if key == "warning":
            key = "warnings"
        summary[key] = int(num)

    for key in ["failed", "passed", "errors", "skipped", "deselected", "warnings"]:
        summary.setdefault(key, 0)

    return summary


def build_risk_priority(a13a: dict) -> list[dict]:
    risk_by_path = a13a.get("risk_by_path_top_80", {})
    risks = a13a.get("design_risks_top_500", [])

    by_path_type = {}
    for item in risks:
        path = item.get("path")
        risk = item.get("risk")
        if not path or not risk:
            continue
        by_path_type.setdefault(path, Counter())[risk] += 1

    rows = []
    for path, count in risk_by_path.items():
        type_counter = by_path_type.get(path, Counter())
        weighted = 0
        for risk_type, risk_count in type_counter.items():
            weighted += RISK_WEIGHTS.get(risk_type, 1) * risk_count

        rows.append({
            "path": path,
            "risk_count": count,
            "weighted_priority_score": weighted or count,
            "risk_types": dict(type_counter),
            "recommended_action": recommend_action_for_path(path),
        })

    rows.sort(key=lambda x: (x["weighted_priority_score"], x["risk_count"]), reverse=True)
    return rows


def recommend_action_for_path(path: str) -> str:
    low = path.lower()

    if "mobile" in low or "ios" in low or "android" in low:
        return "Mobil responsive dosyaları A13G dalgasına alınmalı."
    if low.endswith(".css"):
        return "CSS token ve component sınıflarına taşınmalı."
    if "templates" in low:
        return "Inline style ve tekrar eden component sınıfları parça parça sadeleştirilmeli."
    return "A13C sonrası yeniden değerlendirme yapılmalı."


def build_component_mapping(a13a: dict) -> list[dict]:
    top_classes = a13a.get("component_class_top_120", {})
    rows = []

    for group, spec in CANONICAL_COMPONENTS.items():
        source_hits = []
        total = 0

        for source in spec["sources"]:
            count = top_classes.get(source, 0)
            if count:
                source_hits.append({"class": source, "count": count})
                total += count

        rows.append({
            "group": group,
            "target": spec["target"],
            "variants": spec["variants"],
            "source_hits": source_hits,
            "top120_detected_count": total,
            "strategy": "Önce yeni standart sınıf eklenecek; mevcut sınıflar hemen silinmeyecek. Kırılma riskini azaltmak için alias yaklaşımı kullanılacak.",
        })

    rows.sort(key=lambda x: x["top120_detected_count"], reverse=True)
    return rows


def build_selector_plan(a13a: dict) -> list[dict]:
    duplicates = a13a.get("duplicate_css_selectors_top_120", [])
    rows = []

    for item in duplicates[:80]:
        selector = item.get("selector", "")
        count = item.get("count", 0)
        locations = item.get("locations", [])

        rows.append({
            "selector": selector,
            "count": count,
            "location_count_sample": len(locations),
            "first_locations": locations[:5],
            "recommended_action": "Aynı selector için son yazılan kural davranışı bozmadan incelenmeli; birebir aynı property setleri varsa tek dosyaya alınmalı.",
        })

    return rows


def main() -> int:
    QUALITY.mkdir(parents=True, exist_ok=True)

    a13a = read_json(A13A_JSON)

    compile_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "compileall",
        "-q",
        "app",
        "scripts",
        "migrations",
    ])

    pytest_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "pytest",
        "tests",
        "--ignore=tests/_archive_a5_obsolete",
        "-m",
        "not live and not realdb and not slow",
        "-q",
        "-ra",
    ])

    pytest_summary = parse_pytest_summary(pytest_result["combined"])

    tests_ok = (
        compile_result["returncode"] == 0
        and pytest_result["returncode"] == 0
        and pytest_summary.get("failed", 0) == 0
        and pytest_summary.get("errors", 0) == 0
        and pytest_summary.get("warnings", 0) == 0
        and pytest_summary.get("passed", 0) >= 700
    )

    risk_priority = build_risk_priority(a13a)
    component_mapping = build_component_mapping(a13a)
    selector_plan = build_selector_plan(a13a)

    ok = (
        a13a.get("ok") is True
        and tests_ok
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A13B_UI_DESIGN_SYSTEM_CONSOLIDATION_PLAN",
        "mode": "plan_only_no_code_change",
        "ok": ok,
        "decision": "A13B_PLAN_COMPLETED" if ok else "A13B_BLOCKED_TEST_OR_SOURCE_FAILURE",
        "source_a13a_ok": a13a.get("ok"),
        "source_design_risk_count": a13a.get("design_risk_count"),
        "source_component_occurrence_count": a13a.get("component_occurrence_count"),
        "source_duplicate_css_selector_count": a13a.get("duplicate_css_selector_count"),
        "canonical_components": CANONICAL_COMPONENTS,
        "component_mapping_plan": component_mapping,
        "risk_priority_top_80": risk_priority[:80],
        "duplicate_selector_plan_top_80": selector_plan[:80],
        "recommended_phases": PHASES,
        "guardrails": [
            "A13B kod değiştirmez.",
            "A13C önce token ve yeni component CSS dosyası eklemeli; mevcut sınıflar silinmemeli.",
            "İlk uygulama dalgasında yalnızca alias ve düşük riskli ekleme yapılmalı.",
            "Template class değişimleri ayrı fazda ve küçük gruplarla yapılmalı.",
            "Her faz sonunda compileall ve pytest zorunlu.",
            "Mobil responsive dosyaları ayrı dalga olarak ele alınmalı.",
            "inline style temizliği tek seferde yapılmamalı.",
        ],
        "compileall_returncode": compile_result["returncode"],
        "pytest_returncode": pytest_result["returncode"],
        "pytest_summary": pytest_summary,
        "next_action": "A13C: design token + ortak component CSS temel dosyası güvenli şekilde eklenecek.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md = [
        "# BYS360 A13B UI Design System Konsolidasyon Planı",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {result['ok']}",
        f"- Karar: {result['decision']}",
        f"- Source A13A OK: {result['source_a13a_ok']}",
        f"- Source design risk count: {result['source_design_risk_count']}",
        f"- Source component occurrence count: {result['source_component_occurrence_count']}",
        f"- Source duplicate CSS selector count: {result['source_duplicate_css_selector_count']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Pytest returncode: {result['pytest_returncode']}",
        "",
        "## Pytest Summary",
        "",
        "```json",
        json.dumps(pytest_summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Önerilen Fazlar",
        "",
        "```json",
        json.dumps(PHASES, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Component Mapping Plan",
        "",
        "```json",
        json.dumps(component_mapping, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Risk Priority Top 80",
        "",
        "```json",
        json.dumps(risk_priority[:80], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Duplicate Selector Plan Top 80",
        "",
        "```json",
        json.dumps(selector_plan[:80], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Guardrails",
        "",
        "```json",
        json.dumps(result["guardrails"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(md), encoding="utf-8")

    print("A13B_REPORT_JSON:", OUT_JSON)
    print("A13B_REPORT_MD:", OUT_MD)
    print("A13B_SOURCE_A13A_OK:", result["source_a13a_ok"])
    print("A13B_SOURCE_DESIGN_RISK_COUNT:", result["source_design_risk_count"])
    print("A13B_SOURCE_COMPONENT_OCCURRENCE_COUNT:", result["source_component_occurrence_count"])
    print("A13B_SOURCE_DUPLICATE_CSS_SELECTOR_COUNT:", result["source_duplicate_css_selector_count"])
    print("A13B_COMPONENT_MAPPING_GROUP_COUNT:", len(component_mapping))
    print("A13B_RISK_PRIORITY_COUNT:", len(risk_priority))
    print("A13B_DUPLICATE_SELECTOR_PLAN_COUNT:", len(selector_plan))
    print("A13B_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("A13B_PYTEST_RETURN_CODE:", result["pytest_returncode"])
    print("A13B_PYTEST_SUMMARY:", json.dumps(pytest_summary, ensure_ascii=False))
    print("A13B_OK:", result["ok"])

    return 0 if tests_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
