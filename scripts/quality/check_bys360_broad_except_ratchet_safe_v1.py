#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
import argparse
import json
import re

EXCLUDE = {'.git', '.venv', 'venv', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', 'node_modules', 'backups', 'releases', '.quarantine', 'archive'}
BROAD_RE = re.compile(r"\bexcept\s+Exception\b|\bexcept\s*:")

def iter_py(root: Path):
    for d, dirs, files in __import__('os').walk(root):
        p = Path(d)
        parts = set(p.relative_to(root).parts) if p != root else set()
        if parts & EXCLUDE:
            dirs[:] = []
            continue
        dirs[:] = [x for x in dirs if x not in EXCLUDE]
        for f in files:
            if f.endswith('.py'):
                yield p / f

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--project-root', default='.')
    ap.add_argument('--max-broad-except', type=int, required=True)
    args = ap.parse_args()
    root = Path(args.project_root).resolve()
    total = 0
    by_file = []
    for f in iter_py(root):
        text = f.read_text(encoding='utf-8', errors='ignore')
        c = len(BROAD_RE.findall(text))
        total += c
        if c:
            by_file.append({'path': f.relative_to(root).as_posix(), 'count': c})
    by_file.sort(key=lambda x: x['count'], reverse=True)
    ok = total <= args.max_broad_except
    print(json.dumps({'ok': ok, 'broad_except_total': total, 'max_broad_except': args.max_broad_except, 'top_files': by_file[:25]}, ensure_ascii=False, indent=2))
    raise SystemExit(0 if ok else 1)

if __name__ == '__main__':
    main()
