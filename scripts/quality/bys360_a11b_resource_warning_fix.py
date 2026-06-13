from pathlib import Path
from datetime import datetime
import json
import subprocess
import os
import re
import shutil

ROOT = Path(".").resolve()
RELEASES = Path("C:/bys360/releases")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

TARGET = Path("app/bootstrap/operational_logging.py")
BACKUP_ROOT = RELEASES / f"A11B_RESOURCE_WARNING_FIX_BACKUP_{STAMP}"

OUT_JSON = Path("reports/quality/BYS360_A11B_RESOURCE_WARNING_FIX.json")
OUT_MD = Path("reports/quality/BYS360_A11B_RESOURCE_WARNING_FIX.md")

MARKER = "A11B_RESOURCE_WARNING_FIX"

def run_cmd(cmd, timeout=1800):
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="ignore",
        env={
            **os.environ,
            "PYTHONIOENCODING": "utf-8",
            "BYS360_RUN_LEGACY_ARCHITECTURE_TESTS": "1",
        },
        timeout=timeout,
    )
    return {
        "cmd": " ".join(map(str, cmd)),
        "returncode": proc.returncode,
        "combined": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-16000:],
    }

def parse_pytest_summary(text: str):
    summary = {}
    for num, key in re.findall(r"(\d+)\s+(failed|passed|error|errors|skipped|deselected|warnings|warning)", text or ""):
        key = key.lower()
        if key == "error":
            key = "errors"
        if key == "warning":
            key = "warnings"
        summary[key] = int(num)
    return summary

def patch_operational_logging():
    target_path = ROOT / TARGET
    if not target_path.exists():
        return {
            "patched": False,
            "status": "target_missing",
            "target": str(TARGET),
        }

    original = target_path.read_text(encoding="utf-8-sig", errors="ignore")

    backup_path = BACKUP_ROOT / TARGET
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target_path, backup_path)

    if MARKER in original:
        return {
            "patched": False,
            "status": "already_patched",
            "target": str(TARGET),
            "backup": str(backup_path),
        }

    if "def configure_operational_logging(app: Flask) -> None:" not in original:
        return {
            "patched": False,
            "status": "function_not_found",
            "target": str(TARGET),
            "backup": str(backup_path),
        }

    new_function = '''def _has_rotating_file_handler(logger: logging.Logger, file_path: Path) -> bool:
    """Aynı log dosyası için daha önce handler eklenmiş mi kontrol eder."""
    try:
        target = str(file_path.resolve())
    except Exception:
        target = str(file_path)

    for handler in logger.handlers:
        if not isinstance(handler, RotatingFileHandler):
            continue

        base_filename = getattr(handler, "baseFilename", "") or ""
        try:
            current = str(Path(base_filename).resolve())
        except Exception:
            current = str(base_filename)

        if current == target:
            return True

    return False


def _ensure_rotating_file_handler(
    logger: logging.Logger,
    file_path: Path,
    *,
    level: int,
    formatter: logging.Formatter,
    request_filter: logging.Filter,
    max_bytes: int,
    backup_count: int,
) -> None:
    """{marker}

    Handler zaten varsa yeni RotatingFileHandler oluşturmaz.
    Böylece test/app factory tekrarlarında kullanılmadan boşa düşen dosya nesnesi oluşmaz.
    """
    if _has_rotating_file_handler(logger, file_path):
        return

    handler = RotatingFileHandler(
        file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
        delay=True,
    )
    handler.setLevel(level)
    handler.setFormatter(formatter)
    handler.addFilter(request_filter)
    logger.addHandler(handler)


def configure_operational_logging(app: Flask) -> None:
    """Uygulama ve operasyon loglarini dosya handler'lariyla hazirlar."""
    log_folder = Path(app.config.get("LOG_FOLDER") or "logs")
    log_folder.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(request_id)s | %(remote_addr)s | %(name)s | %(message)s"
    )
    request_filter = RequestContextFilter()

    configured_level_name = str(app.config.get("LOG_LEVEL") or "INFO").strip().upper() or "INFO"
    configured_level = getattr(logging, configured_level_name, logging.INFO)

    app_log_max_bytes = int(app.config.get("APP_LOG_FILE_MAX_BYTES") or 2_000_000)
    app_log_backup_count = int(app.config.get("APP_LOG_BACKUP_COUNT") or 5)
    ops_log_max_bytes = int(app.config.get("OPS_LOG_FILE_MAX_BYTES") or 2_000_000)
    ops_log_backup_count = int(app.config.get("OPS_LOG_BACKUP_COUNT") or 5)

    app_log_path = log_folder / "bys360-app.log"
    ops_log_path = log_folder / "bys360-ops.log"

    _ensure_rotating_file_handler(
        app.logger,
        app_log_path,
        level=configured_level,
        formatter=formatter,
        request_filter=request_filter,
        max_bytes=app_log_max_bytes,
        backup_count=app_log_backup_count,
    )
    app.logger.setLevel(configured_level)

    ops_logger = logging.getLogger("bys360.ops")
    ops_logger.setLevel(configured_level)
    ops_logger.propagate = False

    _ensure_rotating_file_handler(
        ops_logger,
        ops_log_path,
        level=configured_level,
        formatter=formatter,
        request_filter=request_filter,
        max_bytes=ops_log_max_bytes,
        backup_count=ops_log_backup_count,
    )

    app.extensions["ops_logger"] = ops_logger
'''.format(marker=MARKER)

    patched = re.sub(
        r"def configure_operational_logging\\(app: Flask\\) -> None:\\n[\\s\\S]*\\Z",
        new_function,
        original,
        count=1,
    )

    if patched == original:
        return {
            "patched": False,
            "status": "regex_patch_no_change",
            "target": str(TARGET),
            "backup": str(backup_path),
        }

    target_path.write_text(patched, encoding="utf-8")

    return {
        "patched": True,
        "status": "patched",
        "target": str(TARGET),
        "backup": str(backup_path),
    }

def main():
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

    patch_result = patch_operational_logging()

    compile_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "compileall",
        "-q",
        "app",
        "scripts",
        "migrations",
    ])

    import_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-c",
        "from app.bootstrap.operational_logging import configure_operational_logging; print('A11B_IMPORT_OK')",
    ])

    pytest_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "pytest",
        "tests",
        "--ignore=tests/_archive_a5_obsolete",
        "-m",
        "not live and not realdb and not slow",
        "-q",
        "-ra",
    ], timeout=1800)

    strict_resource_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "pytest",
        "tests",
        "--ignore=tests/_archive_a5_obsolete",
        "-m",
        "not live and not realdb and not slow",
        "-q",
        "-ra",
        "-W",
        "error::ResourceWarning",
    ], timeout=1800)

    pytest_summary = parse_pytest_summary(pytest_result["combined"])
    strict_summary = parse_pytest_summary(strict_resource_result["combined"])

    warnings_count = pytest_summary.get("warnings", 0)

    ok = (
        patch_result.get("status") in {"patched", "already_patched"}
        and compile_result["returncode"] == 0
        and import_result["returncode"] == 0
        and pytest_result["returncode"] == 0
        and strict_resource_result["returncode"] == 0
        and pytest_summary.get("failed", 0) == 0
        and pytest_summary.get("errors", 0) == 0
        and pytest_summary.get("passed", 0) >= 700
        and strict_summary.get("failed", 0) == 0
        and strict_summary.get("errors", 0) == 0
        and strict_summary.get("passed", 0) >= 700
        and warnings_count == 0
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A11B_RESOURCE_WARNING_FIX",
        "ok": ok,
        "decision": "A11B_RESOURCE_WARNING_FIX_GREEN" if ok else "A11B_RESOURCE_WARNING_FIX_NOT_GREEN",
        "patch_result": patch_result,
        "compileall_returncode": compile_result["returncode"],
        "import_returncode": import_result["returncode"],
        "import_tail": import_result["combined"],
        "pytest_returncode": pytest_result["returncode"],
        "pytest_summary": pytest_summary,
        "pytest_tail": pytest_result["combined"],
        "strict_resource_returncode": strict_resource_result["returncode"],
        "strict_resource_summary": strict_summary,
        "strict_resource_tail": strict_resource_result["combined"],
        "warnings_after": warnings_count,
        "backup_root": str(BACKUP_ROOT),
        "next_action": "A11C: A11B sonrası warning audit tekrar çalıştırılacak ve warning count 0 ise A11 final evidence üretilecek.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A11B ResourceWarning Fix",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {ok}",
        f"- Karar: {result['decision']}",
        f"- Patch status: {patch_result.get('status')}",
        f"- Backup root: `{result['backup_root']}`",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Import returncode: {result['import_returncode']}",
        f"- Pytest returncode: {result['pytest_returncode']}",
        f"- Strict ResourceWarning returncode: {result['strict_resource_returncode']}",
        f"- Warnings after: {result['warnings_after']}",
        "",
        "## Patch Result",
        "",
        "```json",
        json.dumps(patch_result, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Pytest Summary",
        "",
        "```json",
        json.dumps(pytest_summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Strict ResourceWarning Summary",
        "",
        "```json",
        json.dumps(strict_summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Strict ResourceWarning Tail",
        "",
        "```text",
        strict_resource_result["combined"],
        "```",
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("A11B_REPORT_JSON:", OUT_JSON)
    print("A11B_REPORT_MD:", OUT_MD)
    print("A11B_PATCH_STATUS:", patch_result.get("status"))
    print("A11B_BACKUP_ROOT:", result["backup_root"])
    print("A11B_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("A11B_IMPORT_RETURN_CODE:", result["import_returncode"])
    print("A11B_PYTEST_RETURN_CODE:", result["pytest_returncode"])
    print("A11B_PYTEST_SUMMARY:", json.dumps(pytest_summary, ensure_ascii=False))
    print("A11B_STRICT_RESOURCE_RETURN_CODE:", result["strict_resource_returncode"])
    print("A11B_STRICT_RESOURCE_SUMMARY:", json.dumps(strict_summary, ensure_ascii=False))
    print("A11B_WARNINGS_AFTER:", result["warnings_after"])
    print("A11B_OK:", ok)

    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
