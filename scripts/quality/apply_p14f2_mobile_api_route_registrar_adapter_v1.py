from __future__ import annotations

import argparse
import datetime as dt
import json
import py_compile
import re
import shutil
from pathlib import Path
import logging

LOGGER = logging.getLogger(__name__)


TARGET_REL = "app/api/mobile/routes.py"

BLUEPRINT_MARKER = "BYS360_P14F1_MOBILE_BLUEPRINT_RESOLVER"
ADAPTER_MARKER = "BYS360_P14F2_MOBILE_ROUTE_REGISTRAR_ADAPTER"

# Calls known to appear after route split/refactor. P14F2 makes them signature-safe.
CALL_PATTERNS = [
    (
        "_register_mobile_performance_read_routes_v1(mobile_bp, globals())",
        "_bys360_call_mobile_route_registrar_v1(_register_mobile_performance_read_routes_v1, _bys360_mobile_utility_bp_v1, globals())",
    ),
    (
        "_register_mobile_performance_read_routes_v1(_bys360_mobile_utility_bp_v1, globals())",
        "_bys360_call_mobile_route_registrar_v1(_register_mobile_performance_read_routes_v1, _bys360_mobile_utility_bp_v1, globals())",
    ),
    (
        "_register_mobile_performance_read_routes_v1(mobile_bp)",
        "_bys360_call_mobile_route_registrar_v1(_register_mobile_performance_read_routes_v1, _bys360_mobile_utility_bp_v1, globals())",
    ),
    (
        "_register_mobile_performance_read_routes_v1(_bys360_mobile_utility_bp_v1)",
        "_bys360_call_mobile_route_registrar_v1(_register_mobile_performance_read_routes_v1, _bys360_mobile_utility_bp_v1, globals())",
    ),
]

ADAPTER_BLOCK = """
# BYS360_P14F2_MOBILE_ROUTE_REGISTRAR_ADAPTER_START
def _bys360_call_mobile_route_registrar_v1(_registrar, _bp, _registry=None):
    try:
        return _registrar(_bp, _registry if _registry is not None else globals())
    except TypeError as _two_arg_error:
        try:
            return _registrar(_bp)
        except TypeError:
            raise _two_arg_error
# BYS360_P14F2_MOBILE_ROUTE_REGISTRAR_ADAPTER_END
"""


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def ensure_blueprint_resolver_present(text: str) -> str:
    # If P14F1 is not present for any reason, create a compact resolver before the first affected call.
    if "_bys360_mobile_utility_bp_v1" in text and BLUEPRINT_MARKER in text:
        return text

    compact_resolver = """
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
    raise RuntimeError("BYS360 mobile API Blueprint could not be resolved for route registration")

_bys360_mobile_utility_bp_v1 = _bys360_resolve_mobile_blueprint_for_utility_routes_v1()
# BYS360_P14F1_MOBILE_BLUEPRINT_RESOLVER_END
"""

    insertion_candidates = [
        "_register_mobile_performance_read_routes_v1(",
        "_register_mobile_utility_routes_v1(",
    ]

    for marker in insertion_candidates:
        idx = text.find(marker)
        if idx >= 0:
            line_start = text.rfind("\n", 0, idx) + 1
            return text[:line_start] + compact_resolver.strip() + "\n" + text[line_start:]

    raise SystemExit("NO_ROUTE_REGISTRATION_CALL_FOUND_FOR_BLUEPRINT_RESOLVER_INSERTION")


def insert_adapter(text: str) -> str:
    if ADAPTER_MARKER in text:
        return text

    # Put adapter immediately after blueprint resolver if possible.
    resolver_end = "# BYS360_P14F1_MOBILE_BLUEPRINT_RESOLVER_END"
    idx = text.find(resolver_end)
    if idx >= 0:
        insert_at = text.find("\n", idx)
        if insert_at >= 0:
            return text[:insert_at + 1] + "\n" + ADAPTER_BLOCK.strip() + "\n" + text[insert_at + 1:]

    # Fallback: before performance read route registration call.
    marker = "_register_mobile_performance_read_routes_v1("
    idx = text.find(marker)
    if idx >= 0:
        line_start = text.rfind("\n", 0, idx) + 1
        return text[:line_start] + ADAPTER_BLOCK.strip() + "\n" + text[line_start:]

    raise SystemExit("NO_INSERTION_POINT_FOR_REGISTRAR_ADAPTER")


def replace_calls(text: str) -> tuple[str, list[dict]]:
    updated = text
    changes = []

    for old, new in CALL_PATTERNS:
        if old in updated:
            count = updated.count(old)
            updated = updated.replace(old, new)
            changes.append({"old": old, "new": new, "count": count})

    # Generic safety: if a remaining _register_mobile_*_routes_v1(mobile_bp, globals()) call exists
    # and is NOT the utility registrar already adapted by P14F1, adapt it too.
    generic_re = re.compile(
        r"(?P<fn>_register_mobile_[A-Za-z0-9_]*routes_v1)\s*\(\s*mobile_bp\s*,\s*globals\(\)\s*\)"
    )

    def repl(match: re.Match) -> str:
        fn = match.group("fn")
        return f"_bys360_call_mobile_route_registrar_v1({fn}, _bys360_mobile_utility_bp_v1, globals())"

    updated2, generic_count = generic_re.subn(repl, updated)
    if generic_count:
        changes.append({"old": "generic mobile_bp, globals() registrar calls", "new": "adapter call", "count": generic_count})
        updated = updated2

    return updated, changes


def apply_patch(project_root: Path, dry_run: bool) -> dict:
    target = project_root / TARGET_REL
    if not target.exists():
        raise SystemExit(f"TARGET_NOT_FOUND: {target}")

    original = read_text(target)
    updated = original

    updated = ensure_blueprint_resolver_present(updated)
    updated = insert_adapter(updated)
    updated, changes = replace_calls(updated)

    if "_register_mobile_performance_read_routes_v1(mobile_bp, globals())" in updated:
        raise SystemExit("OLD_PERFORMANCE_READ_TWO_ARG_MOBILE_BP_CALL_STILL_PRESENT")
    if "_register_mobile_performance_read_routes_v1(_bys360_mobile_utility_bp_v1, globals())" in updated:
        raise SystemExit("OLD_PERFORMANCE_READ_TWO_ARG_RESOLVED_BP_CALL_STILL_PRESENT")
    if "_bys360_call_mobile_route_registrar_v1(_register_mobile_performance_read_routes_v1" not in updated:
        raise SystemExit("ADAPTED_PERFORMANCE_READ_REGISTRAR_CALL_NOT_FOUND")

    tmp = project_root / "reports" / "quality" / "_p14f2_routes_py_compile_check.py"
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
            LOGGER.warning("BYS360 p14f2_mobile_registrar_adapter yardımcı işleminde bastırılan hata loglandı: %r", exc)
    if not compile_ok:
        raise SystemExit(f"UPDATED_ROUTES_PY_COMPILE_FAILED: {compile_error}")

    backup_root = None
    if not dry_run and updated != original:
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_root_path = project_root / ".quality_backup" / f"p14f2_mobile_api_route_registrar_adapter_{stamp}"
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
        "blueprint_resolver_present": "_bys360_mobile_utility_bp_v1" in updated,
        "adapter_present": ADAPTER_MARKER in updated,
        "performance_read_adapted": "_bys360_call_mobile_route_registrar_v1(_register_mobile_performance_read_routes_v1" in updated,
        "compile_ok": compile_ok,
        "backup_root": backup_root,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()

    print("BYS360_P14F2_MOBILE_API_ROUTE_REGISTRAR_ADAPTER_START")
    print(f"project_root={project_root}")
    print(f"mode={'DRY_RUN' if args.dry_run else 'APPLY'}")

    result = apply_patch(project_root, dry_run=args.dry_run)

    out_dir = project_root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = "dryrun" if args.dry_run else "applied"
    report_json = out_dir / f"bys360_p14f2_mobile_api_route_registrar_adapter_{suffix}_v1.json"
    report_md = out_dir / f"bys360_p14f2_mobile_api_route_registrar_adapter_{suffix}_v1.md"

    write_text(report_json, json.dumps(result, ensure_ascii=False, indent=2))

    md = []
    md.append("# BYS360 P14F2 Mobile API Route Registrar Adapter")
    md.append("")
    md.append(f"- Mod: `{result['mode']}`")
    md.append(f"- Hedef: `{TARGET_REL}`")
    md.append(f"- Değişti: {result['changed']}")
    md.append(f"- Blueprint resolver var: {result['blueprint_resolver_present']}")
    md.append(f"- Adapter var: {result['adapter_present']}")
    md.append(f"- Performance read adapted: {result['performance_read_adapted']}")
    md.append(f"- Compile OK: {result['compile_ok']}")
    if result["backup_root"]:
        md.append(f"- Yedek: `{result['backup_root']}`")
    md.append("")
    md.append("## Değişiklikler")
    for change in result["changes"]:
        md.append(f"- {change['count']} adet: `{change['old']}` → `{change['new']}`")
    write_text(report_md, "\n".join(md) + "\n")

    print(f"changed={result['changed']}")
    print(f"blueprint_resolver_present={result['blueprint_resolver_present']}")
    print(f"adapter_present={result['adapter_present']}")
    print(f"performance_read_adapted={result['performance_read_adapted']}")
    print(f"compile_ok={result['compile_ok']}")
    if result["backup_root"]:
        print(f"backup_root={result['backup_root']}")
    print(f"report_json={report_json}")
    print(f"report_md={report_md}")
    print("BYS360_P14F2_MOBILE_API_ROUTE_REGISTRAR_ADAPTER_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
