from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PACKAGE = "BYS360_OPS_HARDENING_V6D_PERFORMANCE_CRITICAL_EXCEPTION_CLEANUP_R2"
REPORT_NAME = "BYS360_OPS_HARDENING_V6D_PERFORMANCE_CRITICAL_EXCEPTION_CLEANUP_REPORT.md"
JSON_NAME = "BYS360_OPS_HARDENING_V6D_PERFORMANCE_CRITICAL_EXCEPTION_CLEANUP_REPORT.json"
LOGGER_LINE = "logger = logging.getLogger(__name__)\n"
BACKUP_DIR_NAMES = ["ops_hardening_v6d_hotfix", "ops_hardening_v6d", "ops_hardening_v6d_r2"]
TARGET_HINTS = (
    "performance", "evaluation", "scorecard", "criteria", "period", "assignment", "publish", "president", "approval"
)
EXCLUDE_PARTS = {".venv", "venv", "__pycache__", "site-packages", "dist", "build", "reports", "backups", "archive", "overlays"}


def is_excluded(path: Path) -> bool:
    return bool(set(path.parts) & EXCLUDE_PARTS)


def is_target(path: Path) -> bool:
    rel = str(path).replace("\\", "/").lower()
    if not rel.endswith(".py") or is_excluded(path):
        return False
    if "/scripts/" in rel and "scripts/quality" not in rel:
        return False
    return any(h in rel for h in TARGET_HINTS) and ("/app/" in rel or rel.endswith("config.py") or rel.endswith("run.py") or rel.endswith("wsgi.py"))


def parse_ok(text: str) -> tuple[bool, str]:
    try:
        ast.parse(text)
        return True, ""
    except SyntaxError as exc:
        return False, f"{exc.lineno}:{exc.msg}"


def compile_file(path: Path) -> tuple[bool, str]:
    proc = subprocess.run([sys.executable, "-m", "py_compile", str(path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode == 0, proc.stdout[-2000:]


def compile_project(root: Path) -> tuple[bool, str]:
    paths = [root / "app", root / "config.py", root / "scripts" / "quality"]
    cmd = [sys.executable, "-m", "compileall", "-q"] + [str(p) for p in paths if p.exists()]
    proc = subprocess.run(cmd, cwd=str(root), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return proc.returncode == 0, proc.stdout[-4000:]


def restore_previous_v6d_backups(root: Path) -> list[dict]:
    restored = []
    base = root / "backups"
    for backup_name in BACKUP_DIR_NAMES:
        bdir = base / backup_name
        if not bdir.exists():
            continue
        for bak in sorted(bdir.rglob("*.bak")):
            rel_with_bak = bak.relative_to(bdir)
            rel = Path(str(rel_with_bak)[:-4])
            target = root / rel
            if target.exists():
                shutil.copy2(bak, target)
                restored.append({"file": str(rel), "from": str(bak.relative_to(root))})
    return restored


def ensure_logging_safely(text: str) -> tuple[str, bool]:
    ok, _ = parse_ok(text)
    if not ok:
        return text, False
    changed = False
    lines = text.splitlines(keepends=True)

    # Insert import logging only after module docstring and future imports.
    if "import logging" not in text:
        tree = ast.parse(text)
        insert_line = 0
        if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(getattr(tree.body[0], "value", None), ast.Constant) and isinstance(tree.body[0].value.value, str):
            insert_line = int(getattr(tree.body[0], "end_lineno", tree.body[0].lineno))
        # keep future imports first
        for node in tree.body:
            if isinstance(node, ast.ImportFrom) and node.module == "__future__":
                insert_line = max(insert_line, int(getattr(node, "end_lineno", node.lineno)))
        lines.insert(insert_line, "import logging\n")
        text = "".join(lines)
        ok, _ = parse_ok(text)
        if not ok:
            return "".join(lines[:insert_line] + lines[insert_line+1:]), False
        changed = True
        lines = text.splitlines(keepends=True)

    if "logger = logging.getLogger(__name__)" not in text:
        tree = ast.parse(text)
        insert_line = 0
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                insert_line = max(insert_line, int(getattr(node, "end_lineno", node.lineno)))
            elif isinstance(node, ast.Expr) and isinstance(getattr(node, "value", None), ast.Constant) and isinstance(node.value.value, str):
                insert_line = max(insert_line, int(getattr(node, "end_lineno", node.lineno)))
            else:
                break
        lines.insert(insert_line, LOGGER_LINE)
        candidate = "".join(lines)
        ok, _ = parse_ok(candidate)
        if ok:
            text = candidate
            changed = True
    return text, changed


def clean_except_blocks(text: str) -> tuple[str, int]:
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    changed = 0
    except_re = re.compile(r"^(?P<indent>\s*)except\s+Exception(?:\s+as\s+\w+)?\s*:\s*(?:#.*)?$")
    for i, line in enumerate(lines):
        out.append(line)
        m = except_re.match(line.rstrip("\r\n"))
        if not m:
            continue
        window = "".join(lines[i + 1:i + 8])
        if "logger.exception" in window or "current_app.logger" in window or "app.logger" in window:
            continue
        body_indent = m.group("indent") + "    "
        out.append(f"{body_indent}logger.exception(\"BYS360 performans modülünde beklenmeyen hata yakalandı.\")\n")
        changed += 1
    return "".join(out), changed


def backup_original(root: Path, path: Path, original: str) -> None:
    rel = path.relative_to(root)
    backup_dir = root / "backups" / "ops_hardening_v6d_r2" / rel.parent
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / (path.name + ".bak")
    if not backup_path.exists():
        backup_path.write_text(original, encoding="utf-8")


def apply_to_file(path: Path, root: Path, apply: bool) -> dict:
    rel = str(path.relative_to(root))
    original = path.read_text(encoding="utf-8", errors="replace")
    ok, err = parse_ok(original)
    if not ok:
        return {"file": rel, "status": "skipped_source_syntax", "reason": err, "candidate_blocks": 0, "changed_blocks": 0, "changed": False}
    candidate_blocks = len(re.findall(r"^\s*except\s+Exception(?:\s+as\s+\w+)?\s*:", original, flags=re.M))
    if candidate_blocks == 0:
        return {"file": rel, "status": "no_candidate", "candidate_blocks": 0, "changed_blocks": 0, "changed": False}

    text, log_changed = ensure_logging_safely(original)
    text, changed_blocks = clean_except_blocks(text)
    if text == original:
        return {"file": rel, "status": "already_safe", "candidate_blocks": candidate_blocks, "changed_blocks": 0, "changed": False}
    ok, err = parse_ok(text)
    if not ok:
        return {"file": rel, "status": "skipped_after_change_syntax_guard", "reason": err, "candidate_blocks": candidate_blocks, "changed_blocks": changed_blocks, "changed": False}

    if apply:
        backup_original(root, path, original)
        path.write_text(text, encoding="utf-8")
        c_ok, c_err = compile_file(path)
        if not c_ok:
            path.write_text(original, encoding="utf-8")
            return {"file": rel, "status": "rolled_back_file_compile_guard", "reason": c_err, "candidate_blocks": candidate_blocks, "changed_blocks": 0, "changed": False}
    return {"file": rel, "status": "changed" if apply else "would_change", "candidate_blocks": candidate_blocks, "changed_blocks": changed_blocks, "changed": bool(apply), "logging_changed": log_changed}


def write_report(root: Path, summary: dict, details: list[dict], restored: list[dict]) -> None:
    report_dir = root / "reports" / "quality"
    report_dir.mkdir(parents=True, exist_ok=True)
    payload = {"summary": summary, "restored_from_previous_v6d": restored, "details": details}
    (report_dir / JSON_NAME).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        f"# {PACKAGE}\n",
        "\n## Özet\n",
        f"- generated_at: `{summary['generated_at']}`\n",
        f"- mode: `{summary['mode']}`\n",
        f"- restored_previous_v6d_files: `{summary['restored_previous_v6d_files']}`\n",
        f"- target_files: `{summary['target_files']}`\n",
        f"- files_changed: `{summary['files_changed']}`\n",
        f"- candidate_blocks: `{summary['candidate_blocks']}`\n",
        f"- changed_blocks: `{summary['changed_blocks']}`\n",
        f"- skipped_files: `{summary['skipped_files']}`\n",
        f"- rolled_back_files: `{summary['rolled_back_files']}`\n",
        f"- compile_ok: `{summary['compile_ok']}`\n",
    ]
    if restored:
        lines += ["\n## Önceki V6D Geri Alınan Dosyalar\n", "| Dosya | Yedek |\n", "|---|---|\n"]
        for r in restored:
            lines.append(f"| `{r['file']}` | `{r['from']}` |\n")
    lines += ["\n## Dosya Detayı\n", "| Dosya | Durum | Aday | Değişen | Not |\n", "|---|---:|---:|---:|---|\n"]
    for d in details:
        note = str(d.get("reason", "")).replace("\n", " ")[:300]
        lines.append(f"| `{d['file']}` | `{d['status']}` | {d.get('candidate_blocks', 0)} | {d.get('changed_blocks', 0)} | {note} |\n")
    if summary.get("compile_output"):
        lines += ["\n## Compile Çıktısı\n", "```text\n", summary["compile_output"], "\n```\n"]
    (report_dir / REPORT_NAME).write_text("".join(lines), encoding="utf-8")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    mode = sys.argv[2] if len(sys.argv) > 2 else "apply"
    apply = mode in {"all", "apply", "fix"}

    restored = restore_previous_v6d_backups(root) if apply else []

    files = sorted(p for p in root.rglob("*.py") if is_target(p))
    details = [apply_to_file(p, root, apply=apply) for p in files]
    compile_ok, compile_output = compile_project(root)

    # If final project compile fails, restore R2 changed files to be safe.
    if apply and not compile_ok:
        for d in details:
            if not d.get("changed"):
                continue
            target = root / d["file"]
            backup = root / "backups" / "ops_hardening_v6d_r2" / d["file"]
            backup = Path(str(backup) + ".bak")
            if backup.exists() and target.exists():
                shutil.copy2(backup, target)
                d["status"] = "rolled_back_project_compile_guard"
                d["changed"] = False
        compile_ok, compile_output = compile_project(root)

    summary = {
        "package": PACKAGE,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "mode": "apply" if apply else "audit",
        "restored_previous_v6d_files": len(restored),
        "target_files": len(files),
        "files_changed": sum(1 for d in details if d.get("changed")),
        "candidate_blocks": sum(int(d.get("candidate_blocks", 0)) for d in details),
        "changed_blocks": sum(int(d.get("changed_blocks", 0)) for d in details if d.get("changed") or d.get("status") == "would_change"),
        "skipped_files": sum(1 for d in details if str(d.get("status", "")).startswith("skipped")),
        "rolled_back_files": sum(1 for d in details if str(d.get("status", "")).startswith("rolled_back")),
        "compile_ok": compile_ok,
        "compile_output": compile_output,
    }
    write_report(root, summary, details, restored)
    print(json.dumps({k: v for k, v in summary.items() if k != "compile_output"}, ensure_ascii=False))
    print(f"BYS360_OPS_V6D_R2_REPORT={root / 'reports' / 'quality' / REPORT_NAME}")
    print(f"BYS360_OPS_V6D_R2_JSON={root / 'reports' / 'quality' / JSON_NAME}")
    return 0 if compile_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
