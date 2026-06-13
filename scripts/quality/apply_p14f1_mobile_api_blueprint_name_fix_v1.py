from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import py_compile
from pathlib import Path
import logging

LOGGER = logging.getLogger(__name__)


TARGET_REL = "app/api/mobile/routes.py"

OLD_CALL = "_register_mobile_utility_routes_v1(mobile_bp, globals())"
NEW_CALL = "_register_mobile_utility_routes_v1(_bys360_mobile_utility_bp_v1, globals())"
MARKER = "BYS360_P14F1_MOBILE_BLUEPRINT_RESOLVER"

RESOLVER_BLOCK = """
# BYS360_P14F1_MOBILE_BLUEPRINT_RESOLVER_START
def _bys360_resolve_mobile_blueprint_for_utility_routes_v1():
    for _name in ("mobile_bp", "mobile_api_bp", "bp"):
        _candidate = globals().get(_name)
        if hasattr(_candidate, "route") and hasattr(_candidate, "add_url_rule"):
            return _candidate

    for _candidate in globals().values():
        if not (hasattr(_candidate, "route") and hasattr(_candidate, "add_url_rule")):
            continue
        _bp_name = str(getattr(_candidate, "name", "") or "").lower()
        if _bp_name.startswith(("mobile", "api_mobile", "mobile_api")):
            return _candidate

    raise RuntimeError("BYS360 mobile API Blueprint could not be resolved for utility route registration")


_bys360_mobile_utility_bp_v1 = _bys360_resolve_mobile_blueprint_for_utility_routes_v1()
# BYS360_P14F1_MOBILE_BLUEPRINT_RESOLVER_END
"""


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def apply_patch(project_root: Path, dry_run: bool) -> dict:
    target = project_root / TARGET_REL
    if not target.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target}")

    original = read_text(target)
    updated = original
    changes = []

    if OLD_CALL not in updated and MARKER not in updated and NEW_CALL not in updated:
        raise SystemExit(f"EXPECTED_CALL_NOT_FOUND_AND_MARKER_ABSENT: {OLD_CALL}")

    if MARKER not in updated:
        updated = updated.replace(OLD_CALL, RESOLVER_BLOCK.strip() + "\n" + OLD_CALL, 1)
        changes.append("resolver_block_inserted")

    updated = updated.replace(OLD_CALL, NEW_CALL)

    if OLD_CALL in updated:
        raise SystemExit("OLD_MOBILE_BP_CALL_STILL_PRESENT")

    tmp = project_root / "reports" / "quality" / "_p14f1_routes_py_compile_check.py"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    write_text(tmp, updated)
    try:
        py_compile.compile(str(tmp), doraise=True)
        compile_ok = True
        compile_error = ""
    except Exception as exc:
        compile_ok = False
        compile_error = repr(exc)
    finally:
        try:
            tmp.unlink()
        except Exception as exc:
            LOGGER.warning("BYS360 p14f1_mobile_blueprint_fix yardımcı işleminde bastırılan hata loglandı: %r", exc)
    if not compile_ok:
        raise SystemExit(f"UPDATED_ROUTES_PY_COMPILE_FAILED: {compile_error}")

    backup_root = None
    if not dry_run and updated != original:
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_root_path = project_root / ".quality_backup" / f"p14f1_mobile_api_blueprint_name_fix_{stamp}"
        backup = backup_root_path / TARGET_REL
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup)
        write_text(target, updated)
        backup_root = str(backup_root_path)

    return {
        "target": TARGET_REL,
        "mode": "DRY_RUN" if dry_run else "APPLY",
        "changed": updated != original,
        "changes": changes,
        "old_call_present_after": OLD_CALL in updated,
        "new_call_present_after": NEW_CALL in updated,
        "resolver_marker_present_after": MARKER in updated,
        "compile_ok": compile_ok,
        "backup_root": backup_root,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()

    print("BYS360_P14F1_MOBILE_API_BLUEPRINT_NAME_FIX_START")
    print(f"project_root={project_root}")
    print(f"mode={'DRY_RUN' if args.dry_run else 'APPLY'}")

    result = apply_patch(project_root, dry_run=args.dry_run)

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "dryrun" if args.dry_run else "applied"
    report_json = out_dir / f"bys360_p14f1_mobile_api_blueprint_name_fix_{suffix}_v1.json"
    report_md = out_dir / f"bys360_p14f1_mobile_api_blueprint_name_fix_{suffix}_v1.md"

    write_text(report_json, json.dumps(result, ensure_ascii=False, indent=2))

    md = []
    md.append("# BYS360 P14F1 Mobile API Blueprint Name Fix")
    md.append("")
    md.append(f"- Mod: `{result['mode']}`")
    md.append(f"- Hedef: `{TARGET_REL}`")
    md.append(f"- Değişti: {result['changed']}")
    md.append(f"- Compile OK: {result['compile_ok']}")
    md.append(f"- Eski `mobile_bp` çağrısı kaldı mı: {result['old_call_present_after']}")
    md.append(f"- Yeni resolver çağrısı var mı: {result['new_call_present_after']}")
    md.append(f"- Resolver marker var mı: {result['resolver_marker_present_after']}")
    if result["backup_root"]:
        md.append(f"- Yedek: `{result['backup_root']}`")
    write_text(report_md, "\n".join(md) + "\n")

    print(f"changed={result['changed']}")
    print(f"old_call_present_after={result['old_call_present_after']}")
    print(f"new_call_present_after={result['new_call_present_after']}")
    print(f"resolver_marker_present_after={result['resolver_marker_present_after']}")
    print(f"compile_ok={result['compile_ok']}")
    if result["backup_root"]:
        print(f"backup_root={result['backup_root']}")
    print(f"report_json={report_json}")
    print(f"report_md={report_md}")
    print("BYS360_P14F1_MOBILE_API_BLUEPRINT_NAME_FIX_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
