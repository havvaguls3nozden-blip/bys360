from pathlib import Path
from datetime import datetime
import argparse
import hashlib
import json
import re
import shutil
import zipfile

ROOT = Path(".").resolve()
RELEASES = Path("C:/bys360/releases")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

OUT_JSON = Path("reports/quality/BYS360_A85G_REPO_CLEANUP_AUDIT.json")
OUT_MD = Path("reports/quality/BYS360_A85G_REPO_CLEANUP_AUDIT.md")

KEEP_PS1_NAME_HINTS = {
    "a8_live_cutover_guard.ps1",
    "pre_live_backup_plan.ps1",
    "claude_phase7_final_quality.ps1",
}

KEEP_KEYWORDS = [
    "backup",
    "rollback",
    "restore",
    "live",
    "cutover",
    "guard",
    "smoke",
    "service",
    "task",
    "deploy",
]

RISKY_PS1_KEYWORDS = [
    "repair_",
    "hotfix",
    "overlay",
    "cleanup",
    "v1",
    "v2",
    "v3",
    "v4",
    "v5",
    "v6",
    "v7",
    "v8",
    "v9",
    "v10",
    "v11",
    "v12",
    "v13",
    "v14",
    "v15",
    "v16",
    "v17",
]


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest().upper()


def latest_a85_zip():
    if not RELEASES.exists():
        return None
    zips = sorted(
        RELEASES.glob("BYS360_A85_CI_GREEN_EVIDENCE_*.zip"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return zips[0] if zips else None


def inspect_zip_for_leaks(path: Path):
    bad = []
    names = []
    if not path or not path.exists():
        return {"exists": False, "entry_count": 0, "bad_entries": ["ZIP_NOT_FOUND"], "names_sample": []}

    with zipfile.ZipFile(path, "r") as zf:
        names = zf.namelist()

    bad_patterns = [
        r"(^|/)\.env($|[./])",
        r"(^|/)logs?/",
        r"\.log$",
        r"\.bak$",
        r"secret",
        r"password",
        r"private[_-]?key",
        r"credential",
    ]

    for name in names:
        low = name.lower().replace("\\", "/")
        if any(re.search(pattern, low) for pattern in bad_patterns):
            bad.append(name)

    return {
        "exists": True,
        "entry_count": len(names),
        "bad_entries": bad,
        "names_sample": names[:120],
    }


def archive_status():
    archive = ROOT / "tests" / "_archive_a5_obsolete"
    files = []
    if archive.exists():
        files = [p for p in archive.rglob("*") if p.is_file()]
    return {
        "exists": archive.exists(),
        "file_count": len(files),
        "sample": [rel(p) for p in files[:100]],
    }


def ps1_inventory():
    ps1_files = []
    for p in ROOT.rglob("*.ps1"):
        parts = set(p.parts)
        if ".venv" in parts or "__pycache__" in parts:
            continue
        ps1_files.append(p)

    keep = []
    candidates = []

    for p in ps1_files:
        name = p.name.lower()
        path_text = rel(p).lower()

        explicit_keep = name in KEEP_PS1_NAME_HINTS
        keyword_keep = any(k in name for k in KEEP_KEYWORDS)
        risky = any(k in name for k in RISKY_PS1_KEYWORDS)

        # Canlı/yedek/rollback türü scriptleri koru.
        if explicit_keep or (keyword_keep and not name.startswith("repair_")):
            keep.append(p)
        elif risky or "scripts/windows" in path_text:
            candidates.append(p)
        else:
            candidates.append(p)

    return {
        "total": len(ps1_files),
        "keep_count": len(keep),
        "cleanup_candidate_count": len(candidates),
        "keep_sample": [rel(p) for p in keep[:120]],
        "cleanup_candidate_sample": [rel(p) for p in candidates[:200]],
    }


def decision_status():
    decision = ROOT / "reports" / "quality" / "BYS360_A85F_FINAL_CI_GREEN_DECISION.json"
    if not decision.exists():
        return {"exists": False, "ok": False, "decision": "MISSING"}
    try:
        data = json.loads(decision.read_text(encoding="utf-8-sig", errors="ignore"))
    except Exception as exc:
        return {"exists": True, "ok": False, "decision": f"JSON_ERROR: {exc}"}

    return {
        "exists": True,
        "ok": data.get("ok") is True,
        "decision": data.get("decision"),
        "passed": data.get("passed"),
        "failed": data.get("failed"),
        "errors": data.get("errors"),
        "warnings": data.get("warnings"),
    }


def write_reports(result):
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# BYS360 A8.5G Final Depo Temizlik Audit",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Karar",
        "",
        f"- Mode: `{result['mode']}`",
        f"- A85F decision OK: {result['a85f_decision']['ok']}",
        f"- Archive exists: {result['archive']['exists']}",
        f"- Archive file count: {result['archive']['file_count']}",
        f"- PS1 total: {result['ps1']['total']}",
        f"- PS1 keep count: {result['ps1']['keep_count']}",
        f"- PS1 cleanup candidate count: {result['ps1']['cleanup_candidate_count']}",
        f"- Latest A85 zip: `{result['latest_a85_zip']}`",
        f"- Latest A85 zip SHA256: `{result['latest_a85_sha256']}`",
        f"- Zip leak bad entry count: {len(result['zip_inspection']['bad_entries'])}",
        f"- A85G OK: {result['ok']}",
        "",
        "## A85F Decision",
        "",
        "```json",
        json.dumps(result["a85f_decision"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## ZIP Leak Kontrolü",
        "",
        "```json",
        json.dumps(result["zip_inspection"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Archive Durumu",
        "",
        "```json",
        json.dumps(result["archive"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## PS1 Keep Sample",
        "",
        "```text",
        "\n".join(result["ps1"]["keep_sample"]),
        "```",
        "",
        "## PS1 Cleanup Candidate Sample",
        "",
        "```text",
        "\n".join(result["ps1"]["cleanup_candidate_sample"]),
        "```",
    ]

    if result.get("quarantine"):
        lines.extend([
            "",
            "## Quarantine",
            "",
            "```json",
            json.dumps(result["quarantine"], ensure_ascii=False, indent=2),
            "```",
        ])

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def run(mode: str):
    a85f = decision_status()
    archive = archive_status()
    ps1 = ps1_inventory()
    latest_zip = latest_a85_zip()
    zip_info = inspect_zip_for_leaks(latest_zip) if latest_zip else {"exists": False, "entry_count": 0, "bad_entries": ["NO_A85_ZIP"], "names_sample": []}

    quarantine = None

    if mode == "quarantine":
        qroot = RELEASES / f"A85G_QUARANTINE_{STAMP}"
        qroot.mkdir(parents=True, exist_ok=True)

        moved = []

        archive_path = ROOT / "tests" / "_archive_a5_obsolete"
        if archive_path.exists():
            dst = qroot / "tests__archive_a5_obsolete"
            if dst.exists():
                shutil.rmtree(dst)
            shutil.move(str(archive_path), str(dst))
            moved.append({"type": "archive", "from": rel(archive_path), "to": str(dst)})

        # PS1 için kalıcı silme yok: repo dışına karantina.
        for item in ps1_inventory()["cleanup_candidate_sample"]:
            src = ROOT / item
            if not src.exists():
                continue
            dst = qroot / "ps1" / item
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            moved.append({"type": "ps1", "from": item, "to": str(dst)})

        quarantine = {
            "root": str(qroot),
            "moved_count": len(moved),
            "moved_sample": moved[:250],
            "note": "Kalıcı silme yapılmadı; dosyalar C:/bys360/releases altındaki karantina klasörüne taşındı.",
        }

        archive = archive_status()
        ps1 = ps1_inventory()

    ok = (
        a85f.get("ok") is True
        and zip_info.get("exists") is True
        and len(zip_info.get("bad_entries", [])) == 0
        and archive.get("exists") is False
        and ps1.get("cleanup_candidate_count", 0) == 0
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A85G_REPO_CLEANUP_AUDIT",
        "mode": mode,
        "a85f_decision": a85f,
        "archive": archive,
        "ps1": ps1,
        "latest_a85_zip": str(latest_zip) if latest_zip else "",
        "latest_a85_sha256": sha256(latest_zip) if latest_zip and latest_zip.exists() else "",
        "zip_inspection": zip_info,
        "quarantine": quarantine,
        "ok": ok,
        "next_action": "quarantine çalıştır ve tekrar audit al" if not ok and mode == "audit" else "tamam",
    }

    write_reports(result)

    print("A85G_REPORT_JSON:", OUT_JSON)
    print("A85G_REPORT_MD:", OUT_MD)
    print("A85G_MODE:", mode)
    print("A85G_A85F_OK:", a85f.get("ok"))
    print("A85G_ARCHIVE_EXISTS:", archive.get("exists"))
    print("A85G_ARCHIVE_FILE_COUNT:", archive.get("file_count"))
    print("A85G_PS1_TOTAL:", ps1.get("total"))
    print("A85G_PS1_KEEP_COUNT:", ps1.get("keep_count"))
    print("A85G_PS1_CLEANUP_CANDIDATE_COUNT:", ps1.get("cleanup_candidate_count"))
    print("A85G_ZIP:", str(latest_zip) if latest_zip else "")
    print("A85G_ZIP_SHA256:", sha256(latest_zip) if latest_zip and latest_zip.exists() else "")
    print("A85G_ZIP_LEAK_BAD_ENTRY_COUNT:", len(zip_info.get("bad_entries", [])))
    if quarantine:
        print("A85G_QUARANTINE_ROOT:", quarantine["root"])
        print("A85G_QUARANTINE_MOVED_COUNT:", quarantine["moved_count"])
    print("A85G_OK:", ok)

    return 0 if ok else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["audit", "quarantine"], default="audit")
    args = parser.parse_args()
    raise SystemExit(run(args.mode))

