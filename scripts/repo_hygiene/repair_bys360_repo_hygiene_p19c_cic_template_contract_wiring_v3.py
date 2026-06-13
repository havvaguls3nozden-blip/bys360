from __future__ import annotations

import argparse
import ast
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

PACKAGE = "repo_hygiene_p19c_cic_template_contract_wiring"
VERSION = "V3"

TASK_CONTRACT_IMPORT = "from app.services.cic.task_contract import BASE_KEY, TASK_DEFINITIONS"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("/", "\\")
    except Exception:
        return str(path)


def parse_python_text(text: str) -> str | None:
    try:
        ast.parse(text)
        return None
    except SyntaxError as exc:
        return f"{exc.__class__.__name__}: {exc.msg} (line {exc.lineno})"
    except Exception as exc:
        return repr(exc)


def parse_python(path: Path) -> tuple[ast.Module | None, str | None]:
    try:
        return ast.parse(read_text(path)), None
    except SyntaxError as exc:
        return None, f"{exc.__class__.__name__}: {exc.msg} (line {exc.lineno})"
    except Exception as exc:
        return None, repr(exc)


def import_rows(path: Path) -> list[dict[str, Any]]:
    tree, err = parse_python(path)
    if err:
        return [{"path": str(path), "parse_error": err}]
    rows: list[dict[str, Any]] = []
    assert tree is not None
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
    return sorted(rows, key=lambda r: (r.get("lineno") or 0, r.get("module") or ""))


def file_info(root: Path, path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": rel(root, path), "exists": False, "line_count": 0}
    return {"path": rel(root, path), "exists": True, "line_count": len(read_text(path).splitlines())}


def find_legacy_names_list(text: str) -> dict[str, Any]:
    """Inspect only the P8 legacy bridge list. P19C V3 permits legacy bridge for non-constant names."""
    out: dict[str, Any] = {"exists": False, "names": [], "constant_names": [], "lineno": None}
    m = re.search(r"^_P8_LEGACY_NAMES\s*=\s*(\[[\s\S]*?\])\s*$", text, flags=re.M)
    if not m:
        return out
    out["exists"] = True
    out["lineno"] = text[:m.start()].count("\n") + 1
    try:
        value = ast.literal_eval(m.group(1))
        if isinstance(value, list):
            names = [str(x) for x in value]
            out["names"] = names
            out["constant_names"] = [x for x in names if x in {"BASE_KEY", "TASK_DEFINITIONS"}]
    except Exception as exc:
        out["parse_error"] = repr(exc)
    return out


def count_patterns(text: str) -> dict[str, Any]:
    legacy_module_imports = re.findall(
        r"^\s*from\s+app\.services\s+import\s+corporate_information_center\s+as\s+([A-Za-z_][A-Za-z0-9_]*)\s*$",
        text,
        flags=re.M,
    )
    direct_legacy_constant_import_count = len(re.findall(
        r"^\s*from\s+app\.services\.corporate_information_center\s+import\s+[^\n]*(?:BASE_KEY|TASK_DEFINITIONS)[^\n]*$",
        text,
        flags=re.M,
    ))
    task_contract_import_count = len(re.findall(
        r"^\s*from\s+(?:app\.services\.cic\.task_contract|\.task_contract)\s+import\s+[^\n]*(?:BASE_KEY|TASK_DEFINITIONS)[^\n]*$",
        text,
        flags=re.M,
    ))
    alias_group = "|".join(map(re.escape, legacy_module_imports or ["_legacy_cic", "_legacy"]))
    legacy_getattr_constant_count = len(re.findall(
        r"getattr\(\s*(?:" + alias_group + r")\s*,\s*[\"'](?:BASE_KEY|TASK_DEFINITIONS)[\"']",
        text,
    ))
    constant_ref_count = len(re.findall(r"\b(?:BASE_KEY|TASK_DEFINITIONS)\b", text))
    legacy_names_list = find_legacy_names_list(text)
    return {
        "direct_legacy_constant_import_count": direct_legacy_constant_import_count,
        "task_contract_import_count": task_contract_import_count,
        "legacy_getattr_constant_count": legacy_getattr_constant_count,
        "legacy_module_import_count": len(legacy_module_imports),
        "legacy_module_aliases": legacy_module_imports,
        "constant_ref_count": constant_ref_count,
        "legacy_bridge_constant_name_count": len(legacy_names_list.get("constant_names") or []),
        "legacy_bridge_constant_names": legacy_names_list.get("constant_names") or [],
        "legacy_bridge_names": legacy_names_list,
    }


def analyze(root: Path) -> dict[str, Any]:
    legacy = root / "app" / "services" / "corporate_information_center.py"
    task_contract = root / "app" / "services" / "cic" / "task_contract.py"
    template = root / "app" / "services" / "cic" / "template_service.py"
    facade = root / "app" / "services" / "cic" / "facade.py"
    mail_scheduler = root / "app" / "services" / "cic" / "mail_scheduler_service.py"
    files = {
        "legacy_service": file_info(root, legacy),
        "task_contract": file_info(root, task_contract),
        "template_service": file_info(root, template),
        "facade": file_info(root, facade),
        "mail_scheduler_service": file_info(root, mail_scheduler),
    }
    files_ok = all(files[k]["exists"] for k in ["legacy_service", "task_contract", "template_service"])
    text = read_text(template) if template.exists() else ""
    _, parse_error = parse_python(template) if template.exists() else (None, "template_service.py missing")
    pattern_counts = count_patterns(text)
    parse_errors = []
    if parse_error:
        parse_errors.append({"path": rel(root, template), "parse_error": parse_error})
    task_contract_ready = task_contract.exists()
    constants_not_used = pattern_counts["constant_ref_count"] == 0
    uses_task_contract = pattern_counts["task_contract_import_count"] > 0
    # Important P19C V3 rule:
    # _legacy_cic may remain for non-constant helpers. Only BASE_KEY/TASK_DEFINITIONS must no longer be sourced from legacy.
    no_legacy_constant_source = (
        pattern_counts["direct_legacy_constant_import_count"] == 0
        and pattern_counts["legacy_getattr_constant_count"] == 0
        and pattern_counts["legacy_bridge_constant_name_count"] == 0
    )
    template_wiring_ready = (
        files_ok and not parse_errors and task_contract_ready and no_legacy_constant_source and (constants_not_used or uses_task_contract)
    )
    return {
        "files": files,
        "imports": {"template_imports": import_rows(template) if template.exists() else [], "parse_errors": parse_errors},
        "counts": {**pattern_counts, "parse_error_count": len(parse_errors)},
        "flags": {
            "files_ok": files_ok,
            "task_contract_ready": task_contract_ready,
            "template_constants_not_used": constants_not_used,
            "template_uses_task_contract": uses_task_contract,
            "template_wiring_ready": template_wiring_ready,
            "legacy_module_allowed_for_non_constant_helpers": True,
        },
        "top_preview": text.splitlines()[:34],
    }


def ensure_task_contract_import(text: str, notes: list[str]) -> str:
    if TASK_CONTRACT_IMPORT in text:
        return text
    lines = text.splitlines()
    insert_at = None
    # Prefer after repository import block.
    for idx, line in enumerate(lines):
        if line.strip() == ")" and idx > 0 and "from app.services.cic.repository import (" in "\n".join(lines[max(0, idx-5):idx+1]):
            insert_at = idx + 1
            break
    if insert_at is None:
        for idx, line in enumerate(lines):
            if line.startswith("from __future__ import"):
                insert_at = idx + 1
                break
    if insert_at is None:
        insert_at = 0
    lines.insert(insert_at, TASK_CONTRACT_IMPORT)
    notes.append("task_contract import inserted")
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def remove_constants_from_p8_bridge(text: str, notes: list[str]) -> str:
    m = re.search(r"^_P8_LEGACY_NAMES\s*=\s*(\[[\s\S]*?\])\s*$", text, flags=re.M)
    if not m:
        return text
    try:
        names = ast.literal_eval(m.group(1))
    except Exception as exc:
        notes.append(f"_P8_LEGACY_NAMES could not be parsed: {exc!r}")
        return text
    if not isinstance(names, list):
        return text
    new_names = [str(x) for x in names if str(x) not in {"BASE_KEY", "TASK_DEFINITIONS"}]
    if new_names == names:
        return text
    replacement = "_P8_LEGACY_NAMES = " + repr(new_names)
    text = text[:m.start()] + replacement + text[m.end():]
    notes.append("BASE_KEY/TASK_DEFINITIONS removed from _P8_LEGACY_NAMES bridge")
    return text


def patch_template(root: Path) -> dict[str, Any]:
    template = root / "app" / "services" / "cic" / "template_service.py"
    original = read_text(template)
    text = original
    notes: list[str] = []

    text = ensure_task_contract_import(text, notes)
    text = remove_constants_from_p8_bridge(text, notes)

    # Remove direct legacy constant import only if it exists.
    lines = []
    removed_direct = 0
    for line in text.splitlines():
        if re.match(r"\s*from\s+app\.services\.corporate_information_center\s+import\s+", line) and ("BASE_KEY" in line or "TASK_DEFINITIONS" in line):
            removed_direct += 1
            continue
        lines.append(line)
    if removed_direct:
        text = "\n".join(lines) + ("\n" if original.endswith("\n") else "")
        notes.append(f"direct legacy constant import removed: {removed_direct}")

    # Convert explicit constant references through legacy alias, but preserve alias itself for non-constant helper bridge.
    aliases = re.findall(
        r"^\s*from\s+app\.services\s+import\s+corporate_information_center\s+as\s+([A-Za-z_][A-Za-z0-9_]*)\s*$",
        text,
        flags=re.M,
    ) or ["_legacy_cic", "_legacy"]
    for alias in sorted(set(aliases), key=len, reverse=True):
        before = text
        text = re.sub(rf"getattr\(\s*{re.escape(alias)}\s*,\s*[\"']BASE_KEY[\"']\s*,\s*[^\)]*\)", "BASE_KEY", text)
        text = re.sub(rf"getattr\(\s*{re.escape(alias)}\s*,\s*[\"']TASK_DEFINITIONS[\"']\s*,\s*[^\)]*\)", "TASK_DEFINITIONS", text)
        text = re.sub(rf"\b{re.escape(alias)}\.BASE_KEY\b", "BASE_KEY", text)
        text = re.sub(rf"\b{re.escape(alias)}\.TASK_DEFINITIONS\b", "TASK_DEFINITIONS", text)
        if text != before:
            notes.append(f"legacy constant references converted for alias {alias}")

    text = re.sub(r"\n{4,}", "\n\n\n", text)
    changed = text != original
    if changed:
        err = parse_python_text(text)
        if err:
            return {"changed": False, "error": f"patched template would not parse: {err}", "notes": notes}
        write_text(template, text)
    return {"changed": changed, "notes": notes}


def compile_targets(root: Path) -> dict[str, Any]:
    targets = [root / "app", root / "config.py", root / "scripts"]
    results = []
    ok = True
    for target in targets:
        if not target.exists():
            results.append({"target": str(target), "ok": True, "skipped": True})
            continue
        proc = subprocess.run([sys.executable, "-m", "compileall", "-q", str(target)], cwd=str(root), capture_output=True, text=True)
        item = {"target": str(target), "ok": proc.returncode == 0, "stdout_tail": proc.stdout[-1000:], "stderr_tail": proc.stderr[-1000:]}
        results.append(item)
        ok = ok and item["ok"]
    return {"ok": ok, "results": results}


def smoke(root: Path) -> dict[str, Any]:
    code = """
import json
out = {\"mail_functions_invoked\": False}
try:
    import app.services.cic.task_contract as tc
    import app.services.cic.template_service as tmpl
    out[\"task_contract_import_ok\"] = True
    out[\"template_import_ok\"] = True
    out[\"template_has_get_template\"] = callable(getattr(tmpl, \"get_template\", None))
    out[\"template_has_save_templates\"] = callable(getattr(tmpl, \"save_templates\", None))
    out[\"template_base_key_matches_contract\"] = (not hasattr(tmpl, \"BASE_KEY\")) or (getattr(tmpl, \"BASE_KEY\") == tc.BASE_KEY)
    out[\"template_task_keys_match_contract\"] = (not hasattr(tmpl, \"TASK_DEFINITIONS\")) or (set(getattr(tmpl, \"TASK_DEFINITIONS\", {}).keys()) == set(tc.TASK_DEFINITIONS.keys()))
    out[\"ok\"] = all(bool(out.get(k)) for k in [\"task_contract_import_ok\", \"template_import_ok\", \"template_has_get_template\", \"template_has_save_templates\", \"template_base_key_matches_contract\", \"template_task_keys_match_contract\"])
except Exception as exc:
    out[\"ok\"] = False
    out[\"error\"] = repr(exc)
print(json.dumps(out, ensure_ascii=False))
raise SystemExit(0 if out.get(\"ok\") else 1)
"""
    proc = subprocess.run([sys.executable, "-c", code], cwd=str(root), capture_output=True, text=True)
    parsed: dict[str, Any] = {"attempted": True, "returncode": proc.returncode, "stdout_tail": proc.stdout[-1000:], "stderr_tail": proc.stderr[-1000:]}
    try:
        parsed.update(json.loads(proc.stdout.strip().splitlines()[-1]))
    except Exception:
        parsed["ok"] = False
        parsed["parse_stdout_error"] = True
    return parsed


def write_report(root: Path, report: dict[str, Any]) -> None:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = root / "reports" / "repo_hygiene" / f"P19C_CIC_TEMPLATE_CONTRACT_WIRING_{ts}"
    outdir.mkdir(parents=True, exist_ok=True)
    json_path = outdir / "repo_hygiene_p19c_cic_template_contract_wiring_report.json"
    md_path = outdir / "repo_hygiene_p19c_cic_template_contract_wiring_report.md"
    report["report_json"] = str(json_path)
    report["report_markdown"] = str(md_path)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text("\n".join([
        f"# BYS360 Repo Hijyeni P19C CIC Template Contract Wiring {VERSION}",
        "",
        f"- ok: `{report.get('ok')}`",
        f"- mode: `{report.get('mode')}`",
        f"- changed_files: `{report.get('summary', {}).get('changed_files')}`",
        f"- template_wiring_ready_after: `{report.get('summary', {}).get('template_wiring_ready_after')}`",
        f"- compileall_ok: `{report.get('summary', {}).get('compileall_ok')}`",
        "",
    ]), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ProjectRoot", required=True)
    ap.add_argument("--Mode", choices=["audit", "all"], default="audit")
    ap.add_argument("--CompileAll", action="store_true")
    args = ap.parse_args()
    root = Path(args.ProjectRoot).resolve()
    before = analyze(root)
    changed: list[str] = []
    backup_root = None
    patch_result = None
    if args.Mode == "all":
        template = root / "app" / "services" / "cic" / "template_service.py"
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_root = root / "archive" / f"BYS360_REPO_HYGIENE_P19C_CIC_TEMPLATE_CONTRACT_WIRING_{ts}"
        backup_path = backup_root / "app" / "services" / "cic"
        backup_path.mkdir(parents=True, exist_ok=True)
        if template.exists():
            shutil.copy2(template, backup_path / "template_service.py")
        patch_result = patch_template(root)
        if patch_result.get("changed"):
            changed.append("app\\services\\cic\\template_service.py")
    after = analyze(root)
    smoke_result = {"attempted": False, "ok": None, "skipped_reason": "Mode audit olduğu için smoke çalıştırılmadı."}
    if args.Mode == "all":
        smoke_result = smoke(root)
    compile_result = None
    if args.Mode == "all" and args.CompileAll:
        compile_result = compile_targets(root)
    summary = {
        "files_ok": after["flags"]["files_ok"],
        "audit_only": args.Mode == "audit",
        "changed_files": len(changed),
        "direct_legacy_constant_import_count_before": before["counts"]["direct_legacy_constant_import_count"],
        "direct_legacy_constant_import_count_after": after["counts"]["direct_legacy_constant_import_count"],
        "task_contract_import_count_before": before["counts"]["task_contract_import_count"],
        "task_contract_import_count_after": after["counts"]["task_contract_import_count"],
        "legacy_getattr_constant_count_before": before["counts"]["legacy_getattr_constant_count"],
        "legacy_getattr_constant_count_after": after["counts"]["legacy_getattr_constant_count"],
        "legacy_module_import_count_before": before["counts"]["legacy_module_import_count"],
        "legacy_module_import_count_after": after["counts"]["legacy_module_import_count"],
        "legacy_bridge_constant_name_count_before": before["counts"]["legacy_bridge_constant_name_count"],
        "legacy_bridge_constant_name_count_after": after["counts"]["legacy_bridge_constant_name_count"],
        "parse_error_count_before": before["counts"]["parse_error_count"],
        "parse_error_count_after": after["counts"]["parse_error_count"],
        "template_constants_not_used_after": after["flags"]["template_constants_not_used"],
        "template_uses_task_contract_after": after["flags"]["template_uses_task_contract"],
        "template_wiring_ready_after": after["flags"]["template_wiring_ready"],
        "template_smoke_attempted": smoke_result.get("attempted"),
        "template_smoke_ok": smoke_result.get("ok"),
        "mail_functions_invoked": bool(smoke_result.get("mail_functions_invoked", False)),
        "compileall_ok": None if compile_result is None else compile_result.get("ok"),
    }
    ok = bool(summary["files_ok"] and (args.Mode == "audit" or (summary["template_wiring_ready_after"] and summary["template_smoke_ok"] and (summary["compileall_ok"] is not False))))
    report = {
        "ok": ok,
        "package": PACKAGE,
        "version": VERSION,
        "mode": args.Mode,
        "project_root": str(root),
        "summary": summary,
        "actions": {"changed_files": len(changed), "changed": changed, "backup_root": str(backup_root) if backup_root else None, "patch_result": patch_result, "compileall": compile_result},
        "before": before,
        "after": after,
        "template_smoke": smoke_result,
        "decision": {
            "legacy_behavior_changed": False,
            "mail_send_functions_migrated": False,
            "legacy_module_import_retained_for_non_constant_helpers": True,
            "ready_for_p20": bool(args.Mode == "all" and ok),
            "recommended_sequence": [
                "P19C temizse P20: send_task/run_due_tasks override zinciri audit-only raporlanmalıdır.",
                "Legacy corporate_information_center.py dosyasında silme/taşıma, override zinciri raporu olmadan yapılmamalıdır.",
            ],
        },
        "next_step": "P19C temizse P20 icin send_task/run_due_tasks override chain audit overlay hazirlanmalidir.",
    }
    write_report(root, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
