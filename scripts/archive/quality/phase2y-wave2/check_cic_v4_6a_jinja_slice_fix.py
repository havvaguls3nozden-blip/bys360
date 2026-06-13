
from __future__ import annotations
import argparse, sys
from pathlib import Path

MARK = "BYS360_CIC_V4_6A_JINJA_SLICE_FIX"
INVALID = [
    "_c.upcoming_birthdays|default([], true)[:8]",
    "_c.upcoming_anniversaries|default([], true)[:8]",
    "_c.upcoming_special_days|default([], true)[:8]",
]
VALID = [
    "(_c.upcoming_birthdays|default([], true))[:8]",
    "(_c.upcoming_anniversaries|default([], true))[:8]",
    "(_c.upcoming_special_days|default([], true))[:8]",
]

def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""

def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--project-root", required=True); ns=ap.parse_args(); root=Path(ns.project_root)
    path=root/"app/templates/corporate_information_center/celebrations.html"
    text=read(path)
    errors=[]
    if not path.exists(): errors.append("celebrations.html bulunamadi")
    for s in INVALID:
        if s in text: errors.append("invalid jinja slice remains: "+s)
    for s in VALID:
        if s not in text: errors.append("fixed jinja slice missing: "+s)
    # Jinja syntax parse kontrolu: render degil, sadece parse.
    try:
        from jinja2 import Environment
        Environment().parse(text)
    except Exception as exc:
        errors.append("jinja parse failed: "+repr(exc))
    if errors:
        print(MARK+"_CHECK_FAIL")
        for e in errors: print("ERROR=", e)
        return 1
    print(MARK+"_CHECK_OK")
    return 0
if __name__ == "__main__":
    sys.exit(main())
