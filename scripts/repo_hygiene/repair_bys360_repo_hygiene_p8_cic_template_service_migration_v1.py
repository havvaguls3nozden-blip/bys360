from __future__ import annotations
import argparse, ast, compileall, json, shutil
from datetime import datetime
from pathlib import Path
from typing import Any
PACKAGE = "repo_hygiene_p8_cic_template_service_migration"
VERSION = "V1"
FUNCTIONS_TO_MIGRATE = ["_render_template_text", "get_template", "save_templates", "_cic_phase6_template_quality"]
REPO_IMPORTED_NAMES = {"get_setting", "set_setting", "_loads_json", "_dumps_json", "_now", "_clean_ids"}
COMMON_GLOBALS = {"Any","dict","list","str","int","float","bool","len","range","enumerate","sum","min","max","sorted","set","tuple","isinstance","Exception","ValueError","TypeError","KeyError","print","json","logging","datetime","timedelta","current_app","db","SystemSetting","User","or_","logger","Path","True","False","None"}

def rel(path: Path, root: Path) -> str:
    try: return str(path.relative_to(root)).replace("/", "\\")
    except Exception: return str(path)

def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def parse_functions(path: Path) -> dict[str, dict[str, Any]]:
    text = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(text)
    lines = text.splitlines(keepends=True)
    out: dict[str, dict[str, Any]] = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno
            if getattr(node, "decorator_list", None): start = min(d.lineno for d in node.decorator_list)
            end = getattr(node, "end_lineno", node.lineno)
            out[node.name] = {"name": node.name, "start": start, "end": end, "source": "".join(lines[start-1:end]), "node": node}
    return out

def load_names_for_function(fn_node: ast.AST) -> set[str]:
    loads, stores, params = set(), set(), set()
    for n in ast.walk(fn_node):
        if isinstance(n, ast.Name):
            if isinstance(n.ctx, ast.Load): loads.add(n.id)
            elif isinstance(n.ctx, (ast.Store, ast.Del)): stores.add(n.id)
        elif isinstance(n, ast.arg): params.add(n.arg)
        elif isinstance(n, ast.alias): stores.add((n.asname or n.name.split('.')[0]))
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n is not fn_node: stores.add(n.name)
    return loads - stores - params

def target_has_migration_marker(target_text: str, name: str) -> bool:
    return f"# BYS360 P8 migrated: {name}" in target_text

def ensure_target_header(text: str) -> str:
    if not text.strip(): text = "from __future__ import annotations\n\n"
    if "# BYS360 P8 template migration imports" not in text:
        insert = '''
# BYS360 P8 template migration imports
import logging
import json
from typing import Any
try:
    from flask import current_app
except Exception:  # pragma: no cover - optional Flask context
    current_app = None  # type: ignore
from app.services.cic.repository import (
    get_setting, set_setting, _loads_json, _dumps_json, _now, _clean_ids,
)
logger = logging.getLogger(__name__)

'''
        if text.startswith("from __future__ import annotations"):
            i = text.find("\n"); text = text[:i+1] + insert + text[i+1:]
        else: text = insert + text
    return text

def legacy_dependency_block(names: list[str]) -> str:
    filtered = [n for n in names if n not in REPO_IMPORTED_NAMES and n not in FUNCTIONS_TO_MIGRATE and n not in COMMON_GLOBALS and not n.startswith('__')]
    if not filtered: return ""
    return "\n".join(["\n# BYS360 P8 migrated legacy dependency bridge","try:","    from app.services import corporate_information_center as _legacy_cic","except Exception:  # pragma: no cover","    _legacy_cic = None  # type: ignore",f"_P8_LEGACY_NAMES = {filtered!r}","for _p8_name in _P8_LEGACY_NAMES:","    if _p8_name not in globals() and _legacy_cic is not None and hasattr(_legacy_cic, _p8_name):","        globals()[_p8_name] = getattr(_legacy_cic, _p8_name)","\n"])

def make_wrapper(name: str) -> str:
    return f"def {name}(*args: Any, **kwargs: Any) -> Any:\n    # Compatibility wrapper moved by BYS360 P8.\n    from app.services.cic.template_service import {name} as _impl\n    return _impl(*args, **kwargs)\n"

def replace_functions_with_wrappers(legacy_text: str, funcs: dict[str, dict[str, Any]], names: list[str]) -> str:
    lines = legacy_text.splitlines(keepends=True)
    edits = [(funcs[name]["start"], funcs[name]["end"], make_wrapper(name)) for name in names]
    for start, end, wrapper in sorted(edits, reverse=True): lines[start-1:end] = [wrapper + "\n"]
    return "".join(lines)

def run_compileall(project_root: Path) -> dict[str, Any]:
    targets = [project_root/"app", project_root/"config.py", project_root/"scripts"]
    results=[]; all_ok=True
    for target in targets:
        if target.exists():
            ok = compileall.compile_file(str(target), quiet=1) if target.is_file() else compileall.compile_dir(str(target), quiet=1)
            results.append({"target": str(target), "ok": bool(ok)}); all_ok = all_ok and bool(ok)
    return {"ok": all_ok, "results": results}

def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--project-root", required=True); parser.add_argument("--mode", choices=["audit","all"], default="audit"); parser.add_argument("--compileall", action="store_true"); args=parser.parse_args()
    project_root=Path(args.project_root).resolve(); legacy_file=project_root/"app/services/corporate_information_center.py"; target_file=project_root/"app/services/cic/template_service.py"
    report_dir=project_root/"reports/repo_hygiene"/f"P8_CIC_TEMPLATE_SERVICE_MIGRATION_{now_stamp()}"; report_dir.mkdir(parents=True, exist_ok=True)
    legacy_text=legacy_file.read_text(encoding="utf-8-sig") if legacy_file.exists() else ""; target_text=target_file.read_text(encoding="utf-8-sig") if target_file.exists() else ""
    funcs=parse_functions(legacy_file) if legacy_file.exists() else {}; available=[n for n in FUNCTIONS_TO_MIGRATE if n in funcs]; already=[n for n in FUNCTIONS_TO_MIGRATE if target_has_migration_marker(target_text,n)]; planned=[n for n in available if n not in already]
    changed=[]; backup_root=None; compile_result=None; migrated_count=0; result_ok=True
    if args.mode=="all" and planned:
        backup_root=project_root/"archive"/f"BYS360_REPO_HYGIENE_P8_CIC_TEMPLATE_SERVICE_MIGRATION_{now_stamp()}"
        for src in [legacy_file,target_file]:
            if src.exists():
                dst=backup_root/rel(src,project_root); dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src,dst)
        target_file.parent.mkdir(parents=True, exist_ok=True); new_target=ensure_target_header(target_text); deps=set(); parts=[]
        for name in planned:
            meta=funcs[name]; deps.update(load_names_for_function(meta["node"])); parts.append(f"\n# BYS360 P8 migrated: {name}\n"+meta["source"].rstrip()+"\n")
        bridge=legacy_dependency_block(sorted(deps))
        if bridge and "# BYS360 P8 migrated legacy dependency bridge" not in new_target: new_target += bridge
        new_target += "\n# ---------------------------------------------------------------------------\n# BYS360 P8 - migrated template service functions\n# ---------------------------------------------------------------------------\n" + "\n".join(parts) + "\n"
        target_file.write_text(new_target, encoding="utf-8"); changed.append(rel(target_file,project_root))
        new_legacy=replace_functions_with_wrappers(legacy_text, funcs, planned)
        if "from typing import Any" not in new_legacy:
            lines=new_legacy.splitlines(keepends=True); insert_at=1 if lines and lines[0].startswith("from __future__") else 0; lines.insert(insert_at,"from typing import Any\n"); new_legacy="".join(lines)
        legacy_file.write_text(new_legacy, encoding="utf-8"); changed.append(rel(legacy_file,project_root)); migrated_count=len(planned)
        if args.compileall:
            compile_result=run_compileall(project_root)
            if not compile_result["ok"]:
                for changed_rel in changed:
                    src_backup=backup_root/changed_rel; dst_file=project_root/changed_rel
                    if src_backup.exists(): shutil.copy2(src_backup,dst_file)
                compile_result["rolled_back"]=True; result_ok=False
    report={"ok":result_ok,"package":PACKAGE,"version":VERSION,"mode":args.mode,"project_root":str(project_root),"legacy_file":rel(legacy_file,project_root),"target_file":rel(target_file,project_root),"summary":{"available_functions":len(available),"already_migrated_before":len(already),"planned_to_migrate":len(planned),"migrated_count":migrated_count,"compileall_ok":None if compile_result is None else compile_result["ok"]},"actions":{"changed_files":len(changed),"changed":changed,"backup_root":None if backup_root is None else str(backup_root),"compileall":compile_result},"available_functions":available,"already_migrated_before":already,"migrated_or_planned":planned,"next_step":"P8 gectiyse CIC template ekranlari icin smoke test kosulmali; ardindan P9 mail scheduler fonksiyonlari daha kucuk gruplarla tasinabilir."}
    report_json=report_dir/"repo_hygiene_p8_cic_template_service_migration_report.json"; report_md=report_dir/"repo_hygiene_p8_cic_template_service_migration_report.md"; report["report_json"]=str(report_json); report["report_markdown"]=str(report_md)
    report_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"); report_md.write_text("# BYS360 Repo Hijyeni P8 CIC Template Service Migration\n\n"+f"- ok: `{report['ok']}`\n- mode: `{args.mode}`\n- planned_to_migrate: `{len(planned)}`\n- migrated_count: `{migrated_count}`\n- compileall_ok: `{report['summary']['compileall_ok']}`\n\n## Fonksiyonlar\n"+"\n".join(f"- `{name}`" for name in planned)+"\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2)); return 0 if report["ok"] else 1
if __name__=="__main__": raise SystemExit(main())
