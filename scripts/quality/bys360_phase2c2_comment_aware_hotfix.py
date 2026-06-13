from pathlib import Path

path = Path("scripts/quality/bys360_phase2c2_mobile_shared_wildcard_apply.py")
text = path.read_text(encoding="utf-8")

# Wildcard sayaçlarını yorumlu satırları da sayacak hale getir.
text = text.replace(
    r'r"^\s*from\s+app\.api\.mobile\.shared\s+import\s+\*\s*$"',
    r'r"^\s*from\s+app\.api\.mobile\.shared\s+import\s+\*\s*(?:#.*)?$"',
)
text = text.replace(
    r'r"^\s*from\s+[\w\.]+\s+import\s+\*\s*$"',
    r'r"^\s*from\s+[\w\.]+\s+import\s+\*\s*(?:#.*)?$"',
)

start = text.index("def replace_import_line")
end = text.index("\ndef restore_backups", start)

new_func = r'''def replace_import_line(item: dict) -> dict:
    rel = item["file"]
    path = ROOT / rel
    line_no = int(item["line_no"])
    module = item["module"]
    suggested = item["suggested_import_line"]

    text = path.read_text(encoding="utf-8-sig", errors="ignore")
    lines = text.splitlines(keepends=True)

    if line_no < 1 or line_no > len(lines):
        return {
            "file": rel,
            "line_no": line_no,
            "changed": False,
            "reason": "line_no_out_of_range",
        }

    old_line = lines[line_no - 1]
    stripped = old_line.strip()

    expected_pattern = rf"^\s*from\s+{re.escape(module)}\s+import\s+\*\s*(?:#.*)?$"

    if not re.match(expected_pattern, stripped):
        return {
            "file": rel,
            "line_no": line_no,
            "changed": False,
            "reason": "line_content_not_expected",
            "expected_pattern": expected_pattern,
            "actual": stripped,
        }

    newline = "\n" if old_line.endswith("\n") else ""
    indent = old_line[: len(old_line) - len(old_line.lstrip())]

    lines[line_no - 1] = indent + suggested + newline
    path.write_text("".join(lines), encoding="utf-8")

    return {
        "file": rel,
        "line_no": line_no,
        "changed": True,
        "reason": "replaced_comment_aware",
        "old_line": stripped,
        "new_line": suggested,
    }

'''

text = text[:start] + new_func + text[end:]
path.write_text(text, encoding="utf-8")

print("PHASE2C2_COMMENT_AWARE_HOTFIX_OK:", True)
