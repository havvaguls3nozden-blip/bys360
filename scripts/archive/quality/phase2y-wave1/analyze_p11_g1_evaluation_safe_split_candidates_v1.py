from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


TEMPLATE_REL = "app/templates/evaluation_form.html"


DANGEROUS_HINTS = (
    "<form", "</form", "<input", "<textarea", "<select", "<button",
    "csrf", "submit", "name=", "id=", "score", "puan", "criteria", "kriter",
    "{% for", "{% endfor", "{% if", "{% endif", "{% block", "{% endblock",
    "{% extends", "{% macro", "{% endmacro",
)

SAFE_STATIC_HINTS = (
    "<style", "</style", "<script", "</script",
    "class=", "<div", "</div", "<section", "</section",
    "<h1", "<h2", "<h3", "<p", "</p",
)


def line_has_any(line: str, hints: tuple[str, ...]) -> bool:
    low = line.lower()
    return any(h.lower() in low for h in hints)


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


def classify_candidate(lines: list[str], start: int, end: int) -> tuple[str, str]:
    block = "\n".join(lines[start - 1:end])
    low = block.lower()
    if "<form" in low or "</form" in low:
        return "UNSAFE_FORM_SCOPE", "Form başlangıç/bitiş alanı; ilk partial adımı için uygun değil."
    if any(h.lower() in low for h in ("<input", "<textarea", "<select", "name=", "csrf")):
        return "UNSAFE_INPUT_SCOPE", "Input/name/CSRF içeriyor; puanlama davranışını etkileyebilir."
    if "{% for" in low or "{% if" in low or "{% block" in low:
        return "REVIEW_JINJA_SCOPE", "Jinja kontrol bloğu içeriyor; elle sınır doğrulaması gerekir."
    if "<style" in low and "</style" in low:
        return "SAFE_STYLE_BLOCK", "Inline style bloğu; partial'a taşınması görece güvenli olabilir."
    if "<script" in low and "</script" in low:
        return "REVIEW_SCRIPT_BLOCK", "Script bloğu; davranış içerdiği için önce envanterlenmeli."
    return "SAFE_STATIC_REVIEW", "Statik görsel blok olabilir; kısa bağlamla kontrol edilmeli."


def find_plain_static_runs(lines: list[str], min_lines: int = 25) -> list[dict[str, object]]:
    runs = []
    start = None
    for i, line in enumerate(lines, start=1):
        safeish = line_has_any(line, SAFE_STATIC_HINTS) and not line_has_any(line, DANGEROUS_HINTS)
        if safeish and start is None:
            start = i
        if (not safeish) and start is not None:
            if i - start >= min_lines:
                runs.append({"type": "static_run", "start": start, "end": i - 1, "lines": i - start})
            start = None
    if start is not None and len(lines) - start + 1 >= min_lines:
        runs.append({"type": "static_run", "start": start, "end": len(lines), "lines": len(lines) - start + 1})
    return runs


def extract_context(lines: list[str], start: int, end: int, pad: int = 2) -> list[str]:
    a = max(1, start - pad)
    b = min(len(lines), end + pad)
    return [f"{i}: {lines[i-1]}" for i in range(a, b + 1)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--limit", type=int, default=120)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    template = project_root / TEMPLATE_REL
    if not template.exists():
        raise SystemExit(f"TEMPLATE_NOT_FOUND: {template}")

    text = template.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    style_blocks = find_tag_blocks(lines, "<style", "</style>")
    script_blocks = find_tag_blocks(lines, "<script", "</script>")
    form_blocks = find_tag_blocks(lines, "<form", "</form>")
    static_runs = find_plain_static_runs(lines)

    raw_candidates = style_blocks + script_blocks + static_runs
    candidates = []
    for item in raw_candidates:
        start = int(item["start"])
        end = int(item["end"])
        decision, reason = classify_candidate(lines, start, end)
        candidates.append({
            **item,
            "decision": decision,
            "reason": reason,
            "first_line": lines[start - 1].strip() if 1 <= start <= len(lines) else "",
            "last_line": lines[end - 1].strip() if 1 <= end <= len(lines) else "",
            "context": extract_context(lines, start, end, 2),
        })

    safe_first = [c for c in candidates if c["decision"] == "SAFE_STYLE_BLOCK"]
    safe_static = [c for c in candidates if c["decision"] == "SAFE_STATIC_REVIEW"]
    review_script = [c for c in candidates if c["decision"] == "REVIEW_SCRIPT_BLOCK"]

    report = {
        "template_file": TEMPLATE_REL,
        "line_count": len(lines),
        "form_blocks": form_blocks,
        "style_blocks": style_blocks,
        "script_blocks": script_blocks,
        "static_runs_count": len(static_runs),
        "candidates": candidates,
        "recommended_order": [
            "Önce SAFE_STYLE_BLOCK varsa inline style bloğu partial'a alınmalı.",
            "Sonra SAFE_STATIC_REVIEW blokları elle kontrol edilerek header/personel özet partial adayına ayrılmalı.",
            "Script blokları, puanlama ve zorunluluk davranışı içerdiği için sona bırakılmalı.",
            "Form, input, name/id, CSRF ve puanlama kriter döngülerine bu aşamada dokunulmamalı.",
        ],
        "next_patch_condition": "SAFE_STYLE_BLOCK veya açık güvenli statik blok varsa P11-G2 ile sadece o blok partial'a taşınabilir.",
    }

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_out = out_dir / "bys360_quality_10_10_p11_g1_evaluation_safe_split_candidates_v1.json"
    md_out = out_dir / "bys360_quality_10_10_p11_g1_evaluation_safe_split_candidates_v1.md"
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# BYS360 P11-G1 Evaluation Form Güvenli Split Adayları")
    md.append("")
    md.append(f"- Dosya: `{TEMPLATE_REL}`")
    md.append(f"- Satır sayısı: {len(lines)}")
    md.append(f"- Form blokları: {len(form_blocks)}")
    md.append(f"- Style blokları: {len(style_blocks)}")
    md.append(f"- Script blokları: {len(script_blocks)}")
    md.append(f"- Statik run adayları: {len(static_runs)}")
    md.append("")
    md.append("## Önerilen Sıra")
    md.append("")
    for item in report["recommended_order"]:
        md.append(f"- {item}")
    md.append("")
    md.append("## Adaylar")
    md.append("")
    for idx, c in enumerate(candidates[:args.limit], 1):
        md.append(f"### {idx}. {c['decision']} — satır {c['start']}-{c['end']} ({c['lines']} satır)")
        md.append("")
        md.append(f"- Tür: `{c['type']}`")
        md.append(f"- Gerekçe: {c['reason']}")
        md.append(f"- İlk satır: `{c['first_line'][:160]}`")
        md.append(f"- Son satır: `{c['last_line'][:160]}`")
        md.append("")
    md_out.write_text("\n".join(md) + "\n", encoding="utf-8")

    print("BYS360_QUALITY_10_10_P11_G1_EVALUATION_SAFE_SPLIT_CANDIDATES_START")
    print(f"project_root={project_root}")
    print(f"template_file={template}")
    print(f"line_count={len(lines)}")
    print(f"form_blocks={len(form_blocks)}")
    print(f"style_blocks={len(style_blocks)}")
    print(f"script_blocks={len(script_blocks)}")
    print(f"static_runs={len(static_runs)}")
    print(f"safe_style_candidates={len(safe_first)}")
    print(f"safe_static_candidates={len(safe_static)}")
    print(f"review_script_candidates={len(review_script)}")
    print("BYS360_QUALITY_10_10_P11_G1_CANDIDATES")
    for idx, c in enumerate(candidates[:args.limit], 1):
        print(f"[{idx}] decision={c['decision']} type={c['type']} lines={c['start']}-{c['end']} count={c['lines']}")
        print(f"    reason={c['reason']}")
        print(f"    first={c['first_line'][:180]}")
    print(f"safe_split_candidates_json={json_out}")
    print(f"safe_split_candidates_md={md_out}")
    print("BYS360_QUALITY_10_10_P11_G1_EVALUATION_SAFE_SPLIT_CANDIDATES_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
