from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(r"C:\bys360\project")
OUT = ROOT / "reports" / "handover"
OUT.mkdir(parents=True, exist_ok=True)

def git_files() -> list[str]:
    r = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return [x.strip() for x in r.stdout.splitlines() if x.strip()]

files = git_files()

ext_counts = {}
top_counts = {}
important_dirs = {
    "app": 0,
    "scripts": 0,
    "tests": 0,
    "docs": 0,
    "reports": 0,
    "migrations": 0,
}

for rel in files:
    p = Path(rel)
    ext = p.suffix.lower() or "[no_ext]"
    ext_counts[ext] = ext_counts.get(ext, 0) + 1

    top = p.parts[0] if p.parts else "[root]"
    top_counts[top] = top_counts.get(top, 0) + 1

    for key in important_dirs:
        if rel == key or rel.startswith(key + "/"):
            important_dirs[key] += 1

python_files = [f for f in files if f.endswith(".py")]
template_files = [f for f in files if "templates/" in f]
static_files = [f for f in files if "/static/" in f or f.startswith("app/static/")]
docs_files = [f for f in files if f.startswith("docs/") or f.startswith("app/docs/")]
script_files = [f for f in files if f.startswith("scripts/")]
test_files = [f for f in files if f.startswith("tests/")]

payload = {
    "total_files": len(files),
    "python_files": len(python_files),
    "script_files": len(script_files),
    "test_files": len(test_files),
    "template_files": len(template_files),
    "static_files": len(static_files),
    "docs_files": len(docs_files),
    "top_level_counts": dict(sorted(top_counts.items())),
    "extension_counts": dict(sorted(ext_counts.items())),
    "important_dirs": important_dirs,
}

json_path = OUT / "BYS360_HANDOVER_INVENTORY_V1.json"
md_path = OUT / "BYS360_HANDOVER_INVENTORY_V1.md"

json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

lines = [
    "# BYS360 Devir Envanteri V1",
    "",
    f"- Toplam takip edilen dosya: {payload['total_files']}",
    f"- Python dosyası: {payload['python_files']}",
    f"- Script dosyası: {payload['script_files']}",
    f"- Test dosyası: {payload['test_files']}",
    f"- Template dosyası: {payload['template_files']}",
    f"- Static dosya: {payload['static_files']}",
    f"- Dokümantasyon dosyası: {payload['docs_files']}",
    "",
    "## Ana Klasör Dağılımı",
    "",
]

for key, value in payload["top_level_counts"].items():
    lines.append(f"- `{key}`: {value}")

lines.extend(["", "## Önemli Klasörler", ""])

for key, value in payload["important_dirs"].items():
    lines.append(f"- `{key}`: {value}")

md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

print(json_path)
print(md_path)
print(json.dumps(payload, ensure_ascii=False, indent=2))
