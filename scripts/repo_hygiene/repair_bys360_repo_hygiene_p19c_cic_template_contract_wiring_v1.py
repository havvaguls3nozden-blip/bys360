from __future__ import annotations

import argparse
import ast
import json
import os
import py_compile
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PACKAGE = "repo_hygiene_p19c_cic_template_contract_wiring"
VERSION = "V1"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("/", "\\")
    except Exception:
        return str(path)


def file_info(root: Path, path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": rel(root, path), "exists": False, "line_count": 0}
    try:
        line_count = len(read_text(path).splitlines())
    except Exception:
        line_count = None
    return {"path": rel(root, path), "exists": True, "line_count": line_count}


def ast_scan_imports(path: Path) -> dict[str, Any]:
    text = read_text(path) if path.exists() else ""
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return {
            "ok": False,
            "parse_error": f"{exc.__class__.__name__}: {exc.msg} (line {exc.lineno})",
            "imports": [],
        }
    rows: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            rows.append({
                "lineno": getattr(node, "lineno", None),
                "end_lineno": getattr(node, "end_lineno", None),
                "module": node.module,
                "level": node.level,
                "names": [a.asname or a.name for a in node.names],
                "raw_names": [a.name for a in node.names],
            })
        elif isinstance(node, ast.Import):
            rows.append({
                "lineno": getattr(node, "lineno", None),
                "end_lineno": getattr(node, "end_lineno", None),
                "module": None,
                "level": 0,
                "names": [a.asname or a.name for a in node.names],
                "raw_names": [a.name for a in node.names],
            })
    return {"ok": True, "parse_error": None, "imports": rows}


def summarize(root: Path) -> dict[str, Any]:
    legacy = root / "app" / "services" / "corporate_information_center.py"
    task_contract = root / "app" / "services" / "cic" / "task_contract.py"
    template = root / "app" / "services" / "cic" / "template_service.py"
    facade = root / "app" / "services" / "cic" / "facade.py"
    mail = root / "app" / "services" / "cic" / "mail_scheduler_service.py"

    files = {
        "legacy_service": file_info(root, legacy),
        "task_contract": file_info(root, task_contract),
        "template_service": file_info(root, template),
        "facade": file_info(root, facade),
        "mail_scheduler_service": file_info(root, mail),
    }

    text = read_text(template) if template.exists() else ""
    scan = ast_scan_imports(template)
    imports = scan.get("imports", [])

    direct_legacy_constant_imports = []
    task_contract_imports = []
    for row in imports:
        names = set(row.get("raw_names") or []) | set(row.get("names") or [])
        if row.get("module") == "app.services.corporate_information_center" and {"BASE_KEY", "TASK_DEFINITIONS"} & names:
            direct_legacy_constant_imports.append(row)
        if (row.get("module") in {"app.services.cic.task_contract", "task_contract"} or (row.get("module") == "task_contract" and row.get("level") == 1)) and {"BASE_KEY", "TASK_DEFINITIONS"} & names:
            task_contract_imports.append(row)

    legacy_getattr_constant_count = len(re.findall(r"getattr\s*\(\s*[^,]+,\s*[\"'](?:BASE_KEY|TASK_DEFINITIONS)[\"']", text))
    legacy_module_import_count = len(re.findall(r"from\s+app\.services\s+import\s+corporate_information_center\s+as\s+\w+", text))
    constant_ref_count = len(re.findall(r"\b(?:BASE_KEY|TASK_DEFINITIONS)\b", text))
    parse_error_count = 0 if scan.get("ok") else 1

    template_constants_not_used = constant_ref_count == 0
    template_uses_task_contract = bool(task_contract_imports)
    template_wiring_ready = (
        files["task_contract"]["exists"]
        and parse_error_count == 0
        and not direct_legacy_constant_imports
        and legacy_getattr_constant_count == 0
        and (template_uses_task_contract or template_constants_not_used)
    )

    return {
        "files": files,
        "imports": {
            "template_imports": imports if scan.get("ok") else [{"parse_error": scan.get("parse_error"), "path": rel(root, template)}],
            "direct_legacy_constant_imports": direct_legacy_constant_imports,
            "task_contract_imports": task_contract_imports,
            "parse_errors": ([] if scan.get("ok") else [{"path": rel(root, template), "parse_error": scan.get("parse_error")}]),
        },
        "counts": {
            "direct_legacy_constant_import_count": len(direct_legacy_constant_imports),
            "task_contract_import_count": len(task_contract_imports),
            "legacy_getattr_constant_count": legacy_getattr_constant_count,
            "legacy_module_import_count": legacy_module_import_count,
            "constant_ref_count": constant_ref_count,
            "parse_error_count": parse_error_count,
        },
        "flags": {
            "files_ok": all(files[k]["exists"] for k in ["task_contract", "template_service"]),
            "task_contract_ready": files["task_contract"]["exists"],
            "template_constants_not_used": template_constants_not_used,
            "template_uses_task_contract": template_uses_task_contract,
            "template_wiring_ready": template_wiring_ready,
        },
        "top_preview": text.splitlines()[:24],
    }


def insert_import_after_future(text: str, import_line: str) -> str:
    if import_line in text:
        return text
    lines = text.splitlines()
    idx = 0
    if lines and lines[0].startswith("from __future__ import"):
        idx = 1
        if idx < len(lines) and lines[idx].strip() == "":
            idx += 1
    lines.insert(idx, import_line)
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def patch_template(root: Path) -> dict[str, Any]:
    template = root / "app" / "services" / "cic" / "template_service.py"
    text = read_text(template)
    original = text
    notes: list[str] = []
    import_line = "from app.services.cic.task_contract import BASE_KEY, TASK_DEFINITIONS  # type: ignore"

    # Replace any direct legacy constant import.
    text2 = re.sub(
        r"^\s*from\s+app\.services\.corporate_information_center\s+import\s+BASE_KEY\s*,\s*TASK_DEFINITIONS\s*(?:#.*)?$",
        import_line,
        text,
        flags=re.M,
    )
    if text2 != text:
        notes.append("direct legacy constant import replaced with task_contract import")
        text = text2

    # Replace legacy getattr assignments with direct task_contract constants.
    text2 = re.sub(
        r"^\s*BASE_KEY\s*=\s*getattr\s*\(\s*[^,]+,\s*[\"']BASE_KEY[\"']\s*,\s*[\"'][^\"']*[\"']\s*\)\s*$",
        "BASE_KEY = BASE_KEY",
        text,
        flags=re.M,
    )
    if text2 != text:
        notes.append("legacy BASE_KEY getattr assignment neutralized")
        text = text2

    text2 = re.sub(
        r"^\s*TASK_DEFINITIONS\s*=\s*getattr\s*\(\s*[^,]+,\s*[\"']TASK_DEFINITIONS[\"']\s*,\s*\{\}\s*\)\s*$",
        "TASK_DEFINITIONS = TASK_DEFINITIONS",
        text,
        flags=re.M,
    )
    if text2 != text:
        notes.append("legacy TASK_DEFINITIONS getattr assignment neutralized")
        text = text2

    # If constants are referenced but task_contract import is missing, add it.
    if re.search(r"\b(?:BASE_KEY|TASK_DEFINITIONS)\b", text) and "app.services.cic.task_contract import BASE_KEY, TASK_DEFINITIONS" not in text:
        text = insert_import_after_future(text, import_line)
        notes.append("task_contract import inserted")

    # If no constants are referenced, do not force an import.
    if text != original:
        write_text(template, text)
    return {"changed": text != original, "notes": notes}


def run_compileall(root: Path) -> dict[str, Any]:
    results = []
    overall = True
    for target in [root / "app", root / "config.py", root / "scripts"]:
        if not target.exists():
            results.append({"target": str(target), "ok": True, "skipped": True})
            continue
        proc = subprocess.run([sys.executable, "-m", "compileall", "-q", str(target)], cwd=str(root), text=True, capture_output=True)
        ok = proc.returncode == 0
        overall = overall and ok
        results.append({
            "target": str(target),
            "ok": ok,
            "stdout_tail": proc.stdout[-1200:],
            "stderr_tail": proc.stderr[-1200:],
        })
    return {"ok": overall, "results": results}


def smoke(root: Path) -> dict[str, Any]:
    code = r'''
import json
result = {"mail_functions_invoked": False}
try:
    from app.services.cic import task_contract
    result["task_contract_import_ok"] = True
    from app.services.cic import template_service
    result["template_service_import_ok"] = True
    # If the template module uses the constants, verify equality.
    if hasattr(template_service, "BASE_KEY"):
        result["template_base_key_matches_contract"] = template_service.BASE_KEY == task_contract.BASE_KEY
    else:
        result["template_base_key_matches_contract"] = True
    if hasattr(template_service, "TASK_DEFINITIONS"):
        result["template_task_keys_match_contract"] = set(template_service.TASK_DEFINITIONS.keys()) == set(task_contract.TASK_DEFINITIONS.keys())
    else:
        result["template_task_keys_match_contract"] = True
    result["ok"] = all(v is True for k, v in result.items() if k != "mail_functions_invoked") and result["mail_functions_invoked"] is False
except Exception as exc:
    result["ok"] = False
    result["error"] = repr(exc)
print(json.dumps(result, ensure_ascii=False))
raise SystemExit(0 if result.get("ok") else 1)
'''
    proc = subprocess.run([sys.executable, "-c", code], cwd=str(root), text=True, capture_output=True)
    data: dict[str, Any] = {"attempted": True, "returncode": proc.returncode, "stdout_tail": proc.stdout[-1200:], "stderr_tail": proc.stderr[-1200:]}
    try:
        parsed = json.loads((proc.stdout or "{}").strip().splitlines()[-1])
        data.update(parsed)
    except Exception as exc:
        data["ok"] = False
        data["parse_error"] = repr(exc)
    return data


def make_backup(root: Path, paths: list[Path]) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = root / "archive" / f"BYS360_REPO_HYGIENE_P19C_CIC_TEMPLATE_CONTRACT_WIRING_{stamp}"
    for path in paths:
        if path.exists():
            dest = backup_root / path.relative_to(root)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
    return str(backup_root)


def write_report(root: Path, result: dict[str, Any]) -> None:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = root / "reports" / "repo_hygiene" / f"P19C_CIC_TEMPLATE_CONTRACT_WIRING_{stamp}"
    report_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / "repo_hygiene_p19c_cic_template_contract_wiring_report.json"
    md_path = report_dir / "repo_hygiene_p19c_cic_template_contract_wiring_report.md"
    result["report_json"] = str(json_path)
    result["report_markdown"] = str(md_path)
    json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(
        "# BYS360 Repo Hijyeni P19C CIC Template Contract Wiring V1\n\n" +
        f"- ok: `{result.get('ok')}`\n" +
        f"- mode: `{result.get('mode')}`\n" +
        f"- changed_files: `{result.get('summary', {}).get('changed_files')}`\n" +
        f"- template_wiring_ready_after: `{result.get('summary', {}).get('template_wiring_ready_after')}`\n" +
        f"- compileall_ok: `{result.get('summary', {}).get('compileall_ok')}`\n",
        encoding="utf-8",
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--mode", choices=["audit", "all"], default="audit")
    ap.add_argument("--compile-all", action="store_true")
    args = ap.parse_args()
    root = Path(args.project_root).resolve()

    before = summarize(root)
    changed: list[str] = []
    backup_root = None
    patch_result = None

    if args.mode == "all":
        template = root / "app" / "services" / "cic" / "template_service.py"
        backup_root = make_backup(root, [template])
        patch_result = patch_template(root)
        if patch_result.get("changed"):
            changed.append(rel(root, template))

    after = summarize(root)
    compile_result = None
    if args.compile_all:
        compile_result = run_compileall(root)
    smoke_result = {"attempted": False, "ok": None, "skipped_reason": "Mode audit olduğu için smoke çalıştırılmadı."}
    if args.mode == "all":
        smoke_result = smoke(root)

    summary = {
        "files_ok": after["flags"]["files_ok"],
        "audit_only": args.mode == "audit",
        "changed_files": len(changed),
        "direct_legacy_constant_import_count_before": before["counts"]["direct_legacy_constant_import_count"],
        "direct_legacy_constant_import_count_after": after["counts"]["direct_legacy_constant_import_count"],
        "task_contract_import_count_before": before["counts"]["task_contract_import_count"],
        "task_contract_import_count_after": after["counts"]["task_contract_import_count"],
        "legacy_getattr_constant_count_before": before["counts"]["legacy_getattr_constant_count"],
        "legacy_getattr_constant_count_after": after["counts"]["legacy_getattr_constant_count"],
        "parse_error_count_before": before["counts"]["parse_error_count"],
        "parse_error_count_after": after["counts"]["parse_error_count"],
        "template_constants_not_used_after": after["flags"]["template_constants_not_used"],
        "template_uses_task_contract_after": after["flags"]["template_uses_task_contract"],
        "template_wiring_ready_after": after["flags"]["template_wiring_ready"],
        "template_smoke_attempted": smoke_result.get("attempted"),
        "template_smoke_ok": smoke_result.get("ok"),
        "mail_functions_invoked": smoke_result.get("mail_functions_invoked", False),
        "compileall_ok": None if compile_result is None else compile_result.get("ok"),
    }

    ok = bool(summary["files_ok"] and summary["template_wiring_ready_after"])
    if args.mode == "all":
        ok = ok and bool(smoke_result.get("ok"))
    if compile_result is not None:
        ok = ok and bool(compile_result.get("ok"))

    result = {
        "ok": ok,
        "package": PACKAGE,
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(root),
        "summary": summary,
        "actions": {
            "changed_files": len(changed),
            "changed": changed,
            "backup_root": backup_root,
            "patch_result": patch_result,
            "compileall": compile_result,
        },
        "before": before,
        "after": after,
        "template_smoke": smoke_result,
        "decision": {
            "legacy_behavior_changed": False,
            "mail_send_functions_migrated": False,
            "ready_for_p20": ok,
            "recommended_sequence": [
                "P19C temizse P20: send_task/run_due_tasks override zinciri audit-only raporlanmalıdır.",
                "Legacy corporate_information_center.py dosyasında silme/taşıma, override zinciri raporu olmadan yapılmamalıdır.",
            ],
        },
        "next_step": "P19C temizse P20 icin send_task/run_due_tasks override chain audit overlay hazirlanmalidir.",
    }
    write_report(root, result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
