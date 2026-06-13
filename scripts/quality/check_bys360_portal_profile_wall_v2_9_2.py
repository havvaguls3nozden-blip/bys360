from __future__ import annotations

import re
import sys
from pathlib import Path

MARKER = "BYS360_PORTAL_PROFILE_WALL_V2_9_2"


def _extract_second_param(signature: str) -> str:
    inside = signature[signature.find("(") + 1 : signature.rfind(")")]
    params = [p.strip() for p in inside.split(",") if p.strip()]
    if len(params) < 2:
        raise RuntimeError("enrich_posts ikinci parametresi bulunamadı")
    name = params[1].split("=")[0].split(":")[0].strip()
    if not re.match(r"^[A-Za-z_]\w*$", name):
        raise RuntimeError("enrich_posts ikinci parametre adı okunamadı")
    return name


def _find_function_block(text: str) -> tuple[str, str]:
    m = re.search(r"(?m)^def\s+enrich_posts\s*\([^\n]*\):", text)
    if not m:
        raise RuntimeError("enrich_posts fonksiyonu bulunamadı")
    next_def = re.search(r"(?m)^def\s+\w+\s*\(", text[m.end():])
    end = m.end() + next_def.start() if next_def else len(text)
    return m.group(0), text[m.start():end]


def main() -> int:
    project_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd().resolve()
    path = project_root / "app" / "services" / "portal_service.py"
    text = path.read_text(encoding="utf-8")
    signature, block = _find_function_block(text)
    viewer_param = _extract_second_param(signature)
    failures = []
    if "can_user_delete_post(viewer, post)" in block:
        failures.append("viewer kaldı")
    if "can_user_delete_post(current_user, post)" in block:
        failures.append("current_user kaldı")
    if f"can_user_delete_post({viewer_param}, post)" not in block:
        failures.append("fonksiyon parametresiyle can_delete çağrısı yok")
    if failures:
        print(f"{MARKER}_QUALITY_FAIL")
        for failure in failures:
            print(" - " + failure)
        return 1
    print(f"{MARKER}_QUALITY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
