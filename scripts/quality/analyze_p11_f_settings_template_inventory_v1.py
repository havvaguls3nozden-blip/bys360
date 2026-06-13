from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path


TEMPLATE_REL = "app/templates/settings.html"


SECTION_HINTS = [
    ("header", ["ayarlar", "başlık", "header", "page-title", "breadcrumb"]),
    ("role_matrix", ["rol", "role", "matrix", "matris", "yetki", "permission"]),
    ("menu_visibility", ["menü", "menu", "visibility", "görünür", "visible", "sidebar"]),
    ("person_based", ["kişi", "person", "user", "kullanıcı", "sicil", "personel"]),
    ("security", ["güvenlik", "security", "captcha", "şifre", "password", "login"]),
    ("forms", ["<form", "<input", "<select", "<textarea", "csrf", "submit", "kaydet"]),
    ("tables", ["<table", "<thead", "<tbody", "<tr", "<td", "<th"]),
    ("scripts", ["<script", "function", "const ", "let ", "var ", "addEventListener", "fetch("]),
    ("styles", ["<style", "</style", "style=", "class="]),
    ("actions", ["button", "submit", "kaydet", "save", "reset", "iptal"]),
]


DANGEROUS_SPLIT_HINTS = (
    "<form", "</form", "<input", "<select", "<textarea", "name=", "id=", "csrf",
    "{% for", "{% endfor", "{% if", "{% endif", "{% block", "{% endblock",
    "<script", "</script", "fetch(", "addEventListener",
)


def classify_line(line: str) -> str:
    low = line.lower()
    scores = Counter()
    for kind, hints in SECTION_HINTS:
        for hint in hints:
            if hint.lower() in low:
                scores[kind] += 1
    if not scores:
        return "general"
    return scores.most_common(1)[0][0]


def extract_tokens(text: str) -> dict[str, object]:
    return {
        "forms": re.findall(r"<form\b[^>]*>", text, flags=re.I),
        "inputs": re.findall(r"<input\b[^>]*>", text, flags=re.I),
        "textareas": re.findall(r"<textarea\b[^>]*>", text, flags=re.I),
        "selects": re.findall(r"<select\b[^>]*>", text, flags=re.I),
        "buttons": re.findall(r"<button\b[^>]*>", text, flags=re.I),
        "tables": re.findall(r"<table\b[^>]*>", text, flags=re.I),
        "scripts": re.findall(r"<script\b[^>]*>", text, flags=re.I),
        "styles": re.findall(r"<style\b[^>]*>", text, flags=re.I),
        "jinja_for": re.findall(r"{%\s*for\b.*?%}", text),
        "jinja_if": re.findall(r"{%\s*if\b.*?%}", text),
        "jinja_include": re.findall(r"{%\s*include\s+['\"]([^'\"]+)['\"]\s*%}", text),
        "jinja_blocks": re.findall(r"{%\s*block\s+([a-zA-Z0-9_]+)\s*%}", text),
        "ids": re.findall(r'\bid=["\']([^"\']+)["\']', text),
        "names": re.findall(r'\bname=["\']([^"\']+)["\']', text),
    }


def find_tag_blocks(lines: list[str], open_tag: str, close_tag: str) -> list[dict[str, object]]:
    blocks = []
    inside = False
    start = 0
    for i, line in enumerate(lines, start=1):
        low = line.lower()
        if not inside and open_tag in low:
            inside = True
            start = i
        if inside and close_tag in low:
            blocks.append({"type": open_tag.strip("<"), "start": start, "end": i, "lines": i - start + 1})
            inside = False
    return blocks


def find_kind_runs(lines: list[str]) -> list[dict[str, object]]:
    runs = []
    current = None
    start = 1
    for i, line in enumerate(lines, start=1):
        kind = classify_line(line)
        if current is None:
            current = kind
            start = i
            continue
        if kind != current:
            runs.append({"kind": current, "start": start, "end": i - 1, "lines": i - start})
            current = kind
            start = i
    if current is not None:
        runs.append({"kind": current, "start": start, "end": len(lines), "lines": len(lines) - start + 1})
    return runs


def split_safety_for_range(lines: list[str], start: int, end: int) -> tuple[str, str]:
    block = "\n".join(lines[start - 1:end])
    low = block.lower()
    if "<script" in low or "fetch(" in low or "addeventlistener" in low:
        return "UNSAFE_SCRIPT_BEHAVIOR", "Script veya fetch davranışı içeriyor; ilk split için uygun değil."
    if "<form" in low or "</form" in low or "csrf" in low:
        return "UNSAFE_FORM_SCOPE", "Form/CSRF kapsamı içeriyor; route ve kayıt davranışı etkilenebilir."
    if "<input" in low or "<select" in low or "<textarea" in low or "name=" in low:
        return "UNSAFE_INPUT_SCOPE", "Input/name/select içeriyor; ayar kaydetme davranışı etkilenebilir."
    if "{% for" in low or "{% if" in low or "{% block" in low:
        return "REVIEW_JINJA_SCOPE", "Jinja kontrol bloğu içeriyor; elle sınır doğrulaması gerekir."
    if "<style" in low and "</style" in low:
        return "SAFE_STYLE_BLOCK", "Inline style bloğu; partial'a taşınması görece güvenli olabilir."
    return "SAFE_STATIC_REVIEW", "Statik görsel/açıklama bloğu olabilir; bağlamla doğrulanmalı."


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--limit", type=int, default=160)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    template = project_root / TEMPLATE_REL

    print("BYS360_QUALITY_10_10_P11_F_SETTINGS_TEMPLATE_INVENTORY_START")
    print(f"project_root={project_root}")
    print(f"template_file={template}")

    if not template.exists():
        raise SystemExit(f"TEMPLATE_NOT_FOUND: {template}")

    text = template.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    tokens = extract_tokens(text)
    runs = find_kind_runs(lines)

    line_by_kind = Counter()
    run_by_kind = Counter()
    for run in runs:
        line_by_kind[str(run["kind"])] += int(run["lines"])
        run_by_kind[str(run["kind"])] += 1

    style_blocks = find_tag_blocks(lines, "<style", "</style>")
    script_blocks = find_tag_blocks(lines, "<script", "</script>")
    form_blocks = find_tag_blocks(lines, "<form", "</form>")

    candidates = []
    for block in style_blocks + script_blocks + form_blocks:
        decision, reason = split_safety_for_range(lines, int(block["start"]), int(block["end"]))
        candidates.append({
            **block,
            "decision": decision,
            "reason": reason,
            "first_line": lines[int(block["start"]) - 1].strip(),
            "last_line": lines[int(block["end"]) - 1].strip(),
        })

    # Add long static-ish runs that may be extractable.
    for run in runs:
        if int(run["lines"]) >= 40 and run["kind"] in {"header", "general", "styles"}:
            decision, reason = split_safety_for_range(lines, int(run["start"]), int(run["end"]))
            candidates.append({
                "type": "kind_run",
                **run,
                "decision": decision,
                "reason": reason,
                "first_line": lines[int(run["start"]) - 1].strip(),
                "last_line": lines[int(run["end"]) - 1].strip(),
            })

    report = {
        "template_file": TEMPLATE_REL,
        "line_count": len(lines),
        "form_count": len(tokens["forms"]),
        "input_count": len(tokens["inputs"]),
        "textarea_count": len(tokens["textareas"]),
        "select_count": len(tokens["selects"]),
        "button_count": len(tokens["buttons"]),
        "table_count": len(tokens["tables"]),
        "script_count": len(tokens["scripts"]),
        "style_count": len(tokens["styles"]),
        "jinja_for_count": len(tokens["jinja_for"]),
        "jinja_if_count": len(tokens["jinja_if"]),
        "include_count": len(tokens["jinja_include"]),
        "block_count": len(tokens["jinja_blocks"]),
        "ids_count": len(tokens["ids"]),
        "names_count": len(tokens["names"]),
        "ids_sample": tokens["ids"][:80],
        "names_sample": tokens["names"][:80],
        "line_by_kind": dict(line_by_kind.most_common()),
        "run_by_kind": dict(run_by_kind.most_common()),
        "style_blocks": style_blocks,
        "script_blocks": script_blocks,
        "form_blocks": form_blocks,
        "split_candidates": candidates,
        "recommended_order": [
            "İlk aşamada settings.html doğrudan parçalanmamalı; rol matrisi ve kişi bazlı menü kaydetme davranışları kritiktir.",
            "SAFE_STYLE_BLOCK varsa önce yalnızca style bloğu partial'a taşınabilir.",
            "Form/input/name/id/CSRF içeren bloklara dokunulmamalı.",
            "Script/fetch davranışları ayrı JS envanteri yapılmadan taşınmamalı.",
            "Rol matrisi, menü görünürlüğü ve kişi bazlı ayarlar için ayrı smoke test listesi hazırlanmalı.",
        ],
        "next_step": "P11-F1 safe split candidates analizi veya güvenli style partial taşıma.",
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / "bys360_quality_10_10_p11_f_settings_template_inventory_v1.json"
    md_out = out_dir / "bys360_quality_10_10_p11_f_settings_template_inventory_v1.md"
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# BYS360 P11-F Settings Template Envanteri")
    md.append("")
    md.append(f"- Dosya: `{TEMPLATE_REL}`")
    md.append(f"- Satır sayısı: {len(lines)}")
    md.append(f"- Form sayısı: {report['form_count']}")
    md.append(f"- Input sayısı: {report['input_count']}")
    md.append(f"- Textarea sayısı: {report['textarea_count']}")
    md.append(f"- Select sayısı: {report['select_count']}")
    md.append(f"- Button sayısı: {report['button_count']}")
    md.append(f"- Table sayısı: {report['table_count']}")
    md.append(f"- Script bloğu: {report['script_count']}")
    md.append(f"- Style bloğu: {report['style_count']}")
    md.append(f"- Jinja for: {report['jinja_for_count']}")
    md.append(f"- Jinja if: {report['jinja_if_count']}")
    md.append("")
    md.append("## Satır Türü Dağılımı")
    md.append("")
    for key, count in line_by_kind.most_common():
        md.append(f"- {key}: {count} satır")
    md.append("")
    md.append("## Güvenlik Notu")
    md.append("")
    for item in report["recommended_order"]:
        md.append(f"- {item}")
    md.append("")
    md.append("## Split Adayları")
    md.append("")
    for idx, c in enumerate(candidates[:args.limit], 1):
        md.append(f"### {idx}. {c['decision']} — satır {c['start']}-{c['end']} ({c['lines']} satır)")
        md.append(f"- Tür: `{c['type']}`")
        md.append(f"- Gerekçe: {c['reason']}")
        md.append(f"- İlk satır: `{str(c['first_line'])[:180]}`")
        md.append("")
    md_out.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"line_count={len(lines)}")
    print(f"form_count={report['form_count']}")
    print(f"input_count={report['input_count']}")
    print(f"textarea_count={report['textarea_count']}")
    print(f"select_count={report['select_count']}")
    print(f"button_count={report['button_count']}")
    print(f"table_count={report['table_count']}")
    print(f"script_count={report['script_count']}")
    print(f"style_count={report['style_count']}")
    print(f"jinja_for_count={report['jinja_for_count']}")
    print(f"jinja_if_count={report['jinja_if_count']}")
    print("BYS360_QUALITY_10_10_P11_F_LINE_KIND_SUMMARY")
    for key, count in line_by_kind.most_common():
        print(f"{count:>4} | {key}")
    print("BYS360_QUALITY_10_10_P11_F_RUN_KIND_SUMMARY")
    for key, count in run_by_kind.most_common():
        print(f"{count:>4} | {key}")
    print("BYS360_QUALITY_10_10_P11_F_SPLIT_CANDIDATES")
    for idx, c in enumerate(candidates[:args.limit], 1):
        print(f"[{idx}] decision={c['decision']} type={c['type']} lines={c['start']}-{c['end']} count={c['lines']}")
        print(f"    reason={c['reason']}")
        print(f"    first={str(c['first_line'])[:180]}")
    print(f"settings_inventory_json={json_out}")
    print(f"settings_inventory_md={md_out}")
    print("BYS360_QUALITY_10_10_P11_F_SETTINGS_TEMPLATE_INVENTORY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
