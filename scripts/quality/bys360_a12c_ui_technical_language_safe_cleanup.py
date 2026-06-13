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

A12B_JSON = Path("reports/quality/BYS360_A12B_UI_TECHNICAL_LANGUAGE_PRECISION_AUDIT.json")

OUT_JSON = Path("reports/quality/BYS360_A12C_UI_TECHNICAL_LANGUAGE_SAFE_CLEANUP.json")
OUT_MD = Path("reports/quality/BYS360_A12C_UI_TECHNICAL_LANGUAGE_SAFE_CLEANUP.md")
BACKUP_ROOT = RELEASES / f"A12C_UI_TECHNICAL_LANGUAGE_SAFE_CLEANUP_BACKUP_{STAMP}"

REPLACEMENTS = {
    "app/templates/communication/phase9_release_center.html": [
        ("Hotfix ve rollback kararı yazılı kayıtla yönetilir.", "Acil düzeltme ve geri dönüş kararı yazılı kayıtla yönetilir."),
    ],
    "app/templates/communication/phase9b_dashboard.html": [
        ("Veri geçişi, migration görünürlüğü, sicil omurgası ve güvenlik kapıları için canlı öncesi kontrol merkezi.", "Veri geçişi, kayıt görünürlüğü, sicil omurgası ve güvenlik kontrolleri için canlı öncesi kontrol merkezi."),
        ("Versiyon klasörü:", "Kayıt klasörü:"),
        ("Versiyon dosyası", "Kayıt dosyası"),
        ("SQL hotfix dosyası", "Veri düzeltme dosyası"),
    ],
    "app/templates/communication/phase9b_transition_center.html": [
        ("Sicil omurgası, migration görünürlüğü, env sertleştirmesi ve güvenlik denetimi aynı ekranda yönetilir.", "Sicil omurgası, kayıt görünürlüğü, ortam ayarları ve güvenlik denetimi aynı ekranda yönetilir."),
    ],
    "app/templates/communication/phase9d_dashboard.html": [
        ("İlk 72 saat stabilizasyonu, sıcak izleme sinyalleri, hotfix baskısı ve kapanış kararları için merkezi görünüm.", "İlk 72 saat stabilizasyonu, sıcak izleme sinyalleri, acil düzeltme ihtiyacı ve kapanış kararları için merkezi görünüm."),
        ("Son hotfix kayıtları", "Son acil düzeltme kayıtları"),
        ("Henüz hotfix kaydı bulunmuyor.", "Henüz acil düzeltme kaydı bulunmuyor."),
    ],
    "app/templates/communication/phase9d_stabilization_center.html": [
        ("İlk 72 saatte check-in, hotfix ve saha sinyalleri aynı merkezden kayıt altına alınır.", "İlk 72 saatte günlük kontrol, acil düzeltme ve saha sinyalleri aynı merkezden kayıt altına alınır."),
        ("Hotfix kaydı", "Acil düzeltme kaydı"),
        ("Hotfix kaydet", "Acil düzeltme kaydet"),
    ],
    "app/static/js/bys360_ai_everywhere_v1.js": [
        ("route erişim kontrolünü", "sayfa erişim kontrolünü"),
    ],
    "app/templates/admin/performance_menu_visibility_settings.html": [
        ("route ve backend yetki kontrolleri", "sayfa ve sistem yetki kontrolleri"),
    ],
    "app/templates/admin_system_scan.html": [
        ("route yogunlugu", "ekran yogunlugu"),
    ],
}

OLD_VISIBLE_PHRASES = []
for items in REPLACEMENTS.values():
    for old, _new in items:
        OLD_VISIBLE_PHRASES.append(old)

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))

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
        "combined": ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-18000:],
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

def apply_replacements():
    BACKUP_ROOT.mkdir(parents=True, exist_ok=True)

    operations = []
    total_replacements = 0

    for rel_path, items in REPLACEMENTS.items():
        path = ROOT / rel_path

        if not path.exists():
            operations.append({
                "path": rel_path,
                "status": "missing",
                "replacement_count": 0,
            })
            continue

        original = path.read_text(encoding="utf-8-sig", errors="ignore")
        updated = original
        per_file_count = 0
        details = []

        for old, new in items:
            count = updated.count(old)
            if count:
                updated = updated.replace(old, new)
                per_file_count += count
            details.append({
                "old": old,
                "new": new,
                "count": count,
            })

        if updated != original:
            backup_path = BACKUP_ROOT / rel_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup_path)
            path.write_text(updated, encoding="utf-8")
            status = "patched"
        else:
            backup_path = None
            status = "no_change"

        total_replacements += per_file_count

        operations.append({
            "path": rel_path,
            "status": status,
            "replacement_count": per_file_count,
            "backup": str(backup_path) if backup_path else None,
            "details": details,
        })

    return operations, total_replacements

def scan_remaining_old_phrases():
    remaining = []

    for rel_path in REPLACEMENTS:
        path = ROOT / rel_path
        if not path.exists():
            continue

        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        lines = text.splitlines()

        for line_no, line in enumerate(lines, start=1):
            for phrase in OLD_VISIBLE_PHRASES:
                if phrase in line:
                    remaining.append({
                        "path": rel_path,
                        "line_no": line_no,
                        "phrase": phrase,
                        "line": line.strip()[:500],
                    })

    return remaining

def main():
    if not A12B_JSON.exists():
        raise SystemExit("A12B JSON bulunamadı. Önce A12B çalışmalı.")

    a12b = read_json(A12B_JSON)

    operations, total_replacements = apply_replacements()
    remaining_old_phrases = scan_remaining_old_phrases()

    compile_result = run_cmd([
        str(ROOT / ".venv" / "Scripts" / "python.exe"),
        "-m",
        "compileall",
        "-q",
        "app",
        "scripts",
        "migrations",
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
    ])

    pytest_summary = parse_pytest_summary(pytest_result["combined"])

    ok = (
        a12b.get("ok") is True
        and total_replacements >= 10
        and len(remaining_old_phrases) == 0
        and compile_result["returncode"] == 0
        and pytest_result["returncode"] == 0
        and pytest_summary.get("failed", 0) == 0
        and pytest_summary.get("errors", 0) == 0
        and pytest_summary.get("passed", 0) >= 700
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A12C_UI_TECHNICAL_LANGUAGE_SAFE_CLEANUP",
        "ok": ok,
        "decision": "A12C_SAFE_CLEANUP_GREEN" if ok else "A12C_SAFE_CLEANUP_NOT_GREEN",
        "source_a12b_ok": a12b.get("ok"),
        "backup_root": str(BACKUP_ROOT),
        "target_file_count": len(REPLACEMENTS),
        "total_replacements": total_replacements,
        "operations": operations,
        "remaining_old_phrase_count": len(remaining_old_phrases),
        "remaining_old_phrases": remaining_old_phrases,
        "compileall_returncode": compile_result["returncode"],
        "pytest_returncode": pytest_result["returncode"],
        "pytest_summary": pytest_summary,
        "pytest_tail": pytest_result["combined"],
        "next_action": "A12D: Kullanıcıya görünen teknik dil için final doğrulama ve evidence paketi üretilecek.",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A12C UI Teknik Dil Güvenli Temizlik",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {ok}",
        f"- Karar: {result['decision']}",
        f"- Source A12B OK: {result['source_a12b_ok']}",
        f"- Backup root: `{result['backup_root']}`",
        f"- Target file count: {result['target_file_count']}",
        f"- Total replacements: {result['total_replacements']}",
        f"- Remaining old phrase count: {result['remaining_old_phrase_count']}",
        f"- Compileall returncode: {result['compileall_returncode']}",
        f"- Pytest returncode: {result['pytest_returncode']}",
        "",
        "## Pytest Summary",
        "",
        "```json",
        json.dumps(pytest_summary, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Operations",
        "",
        "```json",
        json.dumps(operations, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Remaining Old Phrases",
        "",
        "```json",
        json.dumps(remaining_old_phrases, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sonraki Adım",
        "",
        result["next_action"],
    ]

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print("A12C_REPORT_JSON:", OUT_JSON)
    print("A12C_REPORT_MD:", OUT_MD)
    print("A12C_BACKUP_ROOT:", result["backup_root"])
    print("A12C_TARGET_FILE_COUNT:", result["target_file_count"])
    print("A12C_TOTAL_REPLACEMENTS:", result["total_replacements"])
    print("A12C_REMAINING_OLD_PHRASE_COUNT:", result["remaining_old_phrase_count"])
    print("A12C_COMPILEALL_RETURN_CODE:", result["compileall_returncode"])
    print("A12C_PYTEST_RETURN_CODE:", result["pytest_returncode"])
    print("A12C_PYTEST_SUMMARY:", json.dumps(pytest_summary, ensure_ascii=False))
    print("A12C_OK:", ok)

    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
