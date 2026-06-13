from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


CSS_REL = "app/static/css/performance_phase3.css"


SECTION_HINTS = [
    ("layout", ["layout", "container", "grid", "wrapper", "shell", "page", "section"]),
    ("cards", ["card", "panel", "tile", "box", "summary", "metric"]),
    ("tables", ["table", "thead", "tbody", "tr", "td", "th", "list"]),
    ("forms", ["form", "input", "select", "textarea", "button", "field"]),
    ("scorecard", ["score", "scorecard", "puan", "rating", "criteria", "criterion"]),
    ("workflow", ["workflow", "timeline", "step", "status", "badge", "chip"]),
    ("dashboard", ["dashboard", "kpi", "chart", "analytics", "report"]),
    ("mobile", ["@media", "mobile", "responsive", "max-width", "min-width"]),
    ("print", ["@media print", "print"]),
]


def strip_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def extract_rules(css: str) -> list[dict[str, str]]:
    # Lightweight CSS block extractor, sufficient for inventory. It does not modify code.
    rules = []
    i = 0
    n = len(css)
    while i < n:
        start = css.find("{", i)
        if start == -1:
            break

        selector = css[i:start].strip()
        depth = 1
        j = start + 1
        while j < n and depth:
            if css[j] == "{":
                depth += 1
            elif css[j] == "}":
                depth -= 1
            j += 1

        body = css[start + 1:j - 1].strip()
        if selector:
            rules.append({"selector": selector, "body": body})
        i = j
    return rules


def classify_selector(selector: str) -> str:
    s = selector.lower()
    scores = Counter()
    for name, hints in SECTION_HINTS:
        for hint in hints:
            if hint in s:
                scores[name] += 1
    if not scores:
        return "general"
    return scores.most_common(1)[0][0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--limit", type=int, default=160)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    css_path = project_root / CSS_REL

    print("BYS360_QUALITY_10_10_P11_H_CSS_INVENTORY_START")
    print(f"project_root={project_root}")
    print(f"css_file={css_path}")

    if not css_path.exists():
        raise SystemExit(f"CSS_NOT_FOUND: {css_path}")

    css = css_path.read_text(encoding="utf-8", errors="ignore")
    lines = css.splitlines()
    no_comments = strip_comments(css)
    rules = extract_rules(no_comments)

    comments = re.findall(r"/\*(.*?)\*/", css, flags=re.S)
    media_count = len(re.findall(r"@media\b", css))
    keyframes_count = len(re.findall(r"@keyframes\b", css))
    import_count = len(re.findall(r"@import\b", css))

    classified = []
    for r in rules:
        kind = classify_selector(r["selector"])
        classified.append({**r, "kind": kind})

    by_kind = Counter(r["kind"] for r in classified)
    top_prefixes = Counter()
    for r in classified:
        sel = r["selector"].split(",")[0].strip()
        m = re.search(r"\.([a-zA-Z0-9_-]+)", sel)
        if m:
            prefix = m.group(1).split("-")[0]
            top_prefixes[prefix] += 1

    proposed_files = {
        "performance_phase3_base.css": ["general", "layout"],
        "performance_phase3_cards.css": ["cards", "dashboard"],
        "performance_phase3_tables.css": ["tables"],
        "performance_phase3_forms.css": ["forms", "scorecard", "workflow"],
        "performance_phase3_responsive.css": ["mobile", "print"],
    }

    plan = {
        "css_file": CSS_REL,
        "line_count": len(lines),
        "rule_count": len(rules),
        "comment_blocks": len(comments),
        "media_count": media_count,
        "keyframes_count": keyframes_count,
        "import_count": import_count,
        "by_kind": dict(by_kind.most_common()),
        "top_class_prefixes": dict(top_prefixes.most_common(40)),
        "proposed_files": proposed_files,
        "safety_strategy": [
            "İlk adımda CSS dosyası bölünmeyecek; sadece envanter alınacak.",
            "Bölme yapılırsa mevcut performance_phase3.css dosyası wrapper olarak kalmalı.",
            "Yeni parçalar @import ile mevcut dosyadan çağrılmalı; HTML referansları değiştirilmemeli.",
            "Sınıf adları, selector adları ve cascade sırası korunmalı.",
            "Görsel fark riski nedeniyle önce yerel ekran kontrolü yapılmalı.",
        ],
        "recommended_next_step": "P11-H1 safe CSS wrapper split: performance_phase3.css dosyasını yedekleyip aynı sırayla parça dosyalara ayıran dry-run destekli script.",
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / "bys360_quality_10_10_p11_h_css_inventory_v1.json"
    md_out = out_dir / "bys360_quality_10_10_p11_h_css_inventory_v1.md"

    json_out.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# BYS360 P11-H Performans CSS Envanteri")
    md.append("")
    md.append(f"- Dosya: `{CSS_REL}`")
    md.append(f"- Satır sayısı: {len(lines)}")
    md.append(f"- CSS blok/rule sayısı: {len(rules)}")
    md.append(f"- Yorum bloğu: {len(comments)}")
    md.append(f"- @media sayısı: {media_count}")
    md.append(f"- @keyframes sayısı: {keyframes_count}")
    md.append("")
    md.append("## Blok Türleri")
    md.append("")
    for k, v in by_kind.most_common():
        md.append(f"- {k}: {v}")
    md.append("")
    md.append("## Önerilen Dosya Ayrımı")
    md.append("")
    for file, kinds in proposed_files.items():
        md.append(f"- `{file}`: {', '.join(kinds)}")
    md.append("")
    md.append("## Güvenli Strateji")
    md.append("")
    for s in plan["safety_strategy"]:
        md.append(f"- {s}")
    md.append("")
    md.append("## İlk 40 Selector")
    md.append("")
    for i, r in enumerate(classified[:40], 1):
        selector = " ".join(r["selector"].split())
        md.append(f"{i}. `{r['kind']}` — `{selector[:180]}`")
    md.append("")
    md_out.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"line_count={len(lines)}")
    print(f"rule_count={len(rules)}")
    print(f"comment_blocks={len(comments)}")
    print(f"media_count={media_count}")
    print(f"keyframes_count={keyframes_count}")
    print("BYS360_QUALITY_10_10_P11_H_KIND_SUMMARY")
    for k, v in by_kind.most_common():
        print(f"{v:>4} | {k}")
    print("BYS360_QUALITY_10_10_P11_H_TOP_PREFIXES")
    for k, v in top_prefixes.most_common(40):
        print(f"{v:>4} | {k}")
    print(f"css_inventory_json={json_out}")
    print(f"css_inventory_md={md_out}")
    print("BYS360_QUALITY_10_10_P11_H_CSS_INVENTORY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
