from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


TEMPLATE_REL = "app/templates/evaluation_form.html"


SECTION_HINTS = [
    ("header", ["başlık", "header", "page-title", "breadcrumb", "karne", "değerlendirme"]),
    ("personnel_info", ["personel", "sicil", "birim", "unvan", "amir", "employee", "manager"]),
    ("criteria", ["kriter", "criteria", "criterion", "puan", "score", "rating"]),
    ("comments", ["görüş", "yorum", "kanaat", "comment", "note", "notes"]),
    ("warnings", ["70", "90", "zorunlu", "uyarı", "warning", "alert", "required"]),
    ("actions", ["button", "submit", "kaydet", "onay", "iptal", "actions"]),
    ("scripts", ["<script", "function", "const ", "let ", "var ", "addEventListener"]),
    ("styles", ["<style", "class=", "style="]),
]


def classify_line(line: str) -> str:
    low = line.lower()
    scores = Counter()
    for kind, hints in SECTION_HINTS:
        for hint in hints:
            if hint in low:
                scores[kind] += 1
    if "<script" in low or "function " in low or "addeventlistener" in low:
        scores["scripts"] += 3
    if "<form" in low or "<input" in low or "<textarea" in low or "<select" in low:
        scores["criteria"] += 1
    if not scores:
        return "general"
    return scores.most_common(1)[0][0]


def find_blocks(lines: list[str]) -> list[dict[str, object]]:
    blocks = []
    current_kind = None
    start = 1
    counts = Counter()

    for idx, line in enumerate(lines, start=1):
        kind = classify_line(line)
        counts[kind] += 1
        if current_kind is None:
            current_kind = kind
            start = idx
            continue
        if kind != current_kind:
            blocks.append({"kind": current_kind, "start": start, "end": idx - 1, "lines": idx - start})
            current_kind = kind
            start = idx
    if current_kind is not None:
        blocks.append({"kind": current_kind, "start": start, "end": len(lines), "lines": len(lines) - start + 1})
    return blocks


def extract_tokens(text: str) -> dict[str, object]:
    return {
        "forms": re.findall(r"<form\b[^>]*>", text, flags=re.I),
        "inputs": re.findall(r"<input\b[^>]*>", text, flags=re.I),
        "textareas": re.findall(r"<textarea\b[^>]*>", text, flags=re.I),
        "selects": re.findall(r"<select\b[^>]*>", text, flags=re.I),
        "buttons": re.findall(r"<button\b[^>]*>", text, flags=re.I),
        "jinja_for": re.findall(r"{%\s*for\b.*?%}", text),
        "jinja_if": re.findall(r"{%\s*if\b.*?%}", text),
        "includes": re.findall(r"{%\s*include\s+['\"]([^'\"]+)['\"]\s*%}", text),
        "blocks": re.findall(r"{%\s*block\s+([a-zA-Z0-9_]+)\s*%}", text),
        "ids": re.findall(r'\bid=["\']([^"\']+)["\']', text),
        "names": re.findall(r'\bname=["\']([^"\']+)["\']', text),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--limit", type=int, default=160)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    template = project_root / TEMPLATE_REL

    print("BYS360_QUALITY_10_10_P11_G_EVALUATION_TEMPLATE_INVENTORY_START")
    print(f"project_root={project_root}")
    print(f"template_file={template}")

    if not template.exists():
        raise SystemExit(f"TEMPLATE_NOT_FOUND: {template}")

    text = template.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    tokens = extract_tokens(text)
    blocks = find_blocks(lines)

    by_kind = Counter(block["kind"] for block in blocks)
    line_by_kind = Counter()
    for block in blocks:
        line_by_kind[str(block["kind"])] += int(block["lines"])

    proposed_partials = {
        "_evaluation_header.html": ["header", "personnel_info"],
        "_evaluation_criteria.html": ["criteria"],
        "_evaluation_comments.html": ["comments", "warnings"],
        "_evaluation_actions.html": ["actions"],
        "_evaluation_scripts.html": ["scripts"],
    }

    report = {
        "template_file": TEMPLATE_REL,
        "line_count": len(lines),
        "form_count": len(tokens["forms"]),
        "input_count": len(tokens["inputs"]),
        "textarea_count": len(tokens["textareas"]),
        "select_count": len(tokens["selects"]),
        "button_count": len(tokens["buttons"]),
        "jinja_for_count": len(tokens["jinja_for"]),
        "jinja_if_count": len(tokens["jinja_if"]),
        "include_count": len(tokens["includes"]),
        "block_count": len(tokens["blocks"]),
        "ids_count": len(tokens["ids"]),
        "names_count": len(tokens["names"]),
        "ids_sample": tokens["ids"][:60],
        "names_sample": tokens["names"][:60],
        "by_block_kind": dict(by_kind.most_common()),
        "line_by_kind": dict(line_by_kind.most_common()),
        "proposed_partials": proposed_partials,
        "safety_strategy": [
            "İlk aşamada dosya parçalanmayacak; form input name/id değerleri envanterlenecek.",
            "Partial split yapılırsa route, form action, input name, CSRF ve submit davranışları değişmemeli.",
            "Jinja for/if blokları ortadan kesilmemeli.",
            "İlk gerçek split sadece görsel header/personnel_info bölümüyle başlamalı.",
            "Kriter puan inputları, açıklama zorunluluğu ve form submit en sona bırakılmalı.",
        ],
        "next_step": "P11-G1 güvenli template partial split planı: sadece header/personnel summary bloğunu partial yapma veya önce marker tabanlı blok çıkarma.",
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / "bys360_quality_10_10_p11_g_evaluation_template_inventory_v1.json"
    md_out = out_dir / "bys360_quality_10_10_p11_g_evaluation_template_inventory_v1.md"
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# BYS360 P11-G Evaluation Form Template Envanteri")
    md.append("")
    md.append(f"- Dosya: `{TEMPLATE_REL}`")
    md.append(f"- Satır sayısı: {len(lines)}")
    md.append(f"- Form sayısı: {report['form_count']}")
    md.append(f"- Input sayısı: {report['input_count']}")
    md.append(f"- Textarea sayısı: {report['textarea_count']}")
    md.append(f"- Select sayısı: {report['select_count']}")
    md.append(f"- Button sayısı: {report['button_count']}")
    md.append(f"- Jinja for sayısı: {report['jinja_for_count']}")
    md.append(f"- Jinja if sayısı: {report['jinja_if_count']}")
    md.append("")
    md.append("## Blok Türleri")
    md.append("")
    for key, count in line_by_kind.most_common():
        md.append(f"- {key}: {count} satır")
    md.append("")
    md.append("## Önerilen Partial Adayları")
    md.append("")
    for partial, kinds in proposed_partials.items():
        md.append(f"- `{partial}`: {', '.join(kinds)}")
    md.append("")
    md.append("## Güvenlik Stratejisi")
    md.append("")
    for item in report["safety_strategy"]:
        md.append(f"- {item}")
    md.append("")
    md.append("## İlk Bloklar")
    md.append("")
    for block in blocks[:40]:
        md.append(f"- `{block['kind']}` satır {block['start']}-{block['end']} ({block['lines']} satır)")
    md.append("")
    md_out.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"line_count={len(lines)}")
    print(f"form_count={report['form_count']}")
    print(f"input_count={report['input_count']}")
    print(f"textarea_count={report['textarea_count']}")
    print(f"select_count={report['select_count']}")
    print(f"button_count={report['button_count']}")
    print(f"jinja_for_count={report['jinja_for_count']}")
    print(f"jinja_if_count={report['jinja_if_count']}")
    print("BYS360_QUALITY_10_10_P11_G_LINE_KIND_SUMMARY")
    for key, count in line_by_kind.most_common():
        print(f"{count:>4} | {key}")
    print("BYS360_QUALITY_10_10_P11_G_BLOCK_KIND_SUMMARY")
    for key, count in by_kind.most_common():
        print(f"{count:>4} | {key}")
    print(f"evaluation_inventory_json={json_out}")
    print(f"evaluation_inventory_md={md_out}")
    print("BYS360_QUALITY_10_10_P11_G_EVALUATION_TEMPLATE_INVENTORY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
