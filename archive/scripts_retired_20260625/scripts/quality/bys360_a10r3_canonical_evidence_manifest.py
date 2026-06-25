from pathlib import Path
from datetime import datetime
import json
import zipfile
import hashlib
from collections import Counter

ROOT = Path(".").resolve()
RELEASES = Path("C:/bys360/releases")
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")

A10R_JSON = Path("reports/quality/BYS360_A10R_FINAL_TECH_DEBT_EVIDENCE.json")
A10R2_JSON = Path("reports/quality/BYS360_A10R2_FINAL_TECH_DEBT_EVIDENCE_CLEAN_ZIP.json")

OUT_JSON = Path("reports/quality/BYS360_A10R3_CANONICAL_EVIDENCE_MANIFEST.json")
OUT_MD = Path("reports/quality/BYS360_A10R3_CANONICAL_EVIDENCE_MANIFEST.md")
OUT_ZIP = RELEASES / f"BYS360_A10R3_CANONICAL_TECH_DEBT_EVIDENCE_{STAMP}.zip"

def rel(path: Path):
    return str(path.resolve().relative_to(ROOT)).replace("\\", "/")

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))

def sha256_file(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def collect_evidence_files():
    files = []

    for pattern in [
        "reports/quality/BYS360_A10*.json",
        "reports/quality/BYS360_A10*.md",
        "scripts/quality/bys360_a10*.py",
    ]:
        for path in ROOT.glob(pattern):
            if not path.exists() or not path.is_file():
                continue

            # A10R2 MD içinde eski pre-final SHA kaldığı için canonical ZIP'e alınmıyor.
            # A10R3 dış manifestleri de ZIP içine alınmıyor; hash dışarıda sabit kalacak.
            if path.name in {
                "BYS360_A10R2_FINAL_TECH_DEBT_EVIDENCE_CLEAN_ZIP.md",
                "BYS360_A10R3_CANONICAL_EVIDENCE_MANIFEST.json",
                "BYS360_A10R3_CANONICAL_EVIDENCE_MANIFEST.md",
            }:
                continue

            files.append(path)

    by_rel = {}
    for path in files:
        by_rel[rel(path)] = path

    return [by_rel[k] for k in sorted(by_rel)]

def build_internal_manifest(evidence_files):
    lines = [
        "# BYS360 A10R3 Canonical ZIP Internal Manifest",
        "",
        "Bu dosya ZIP içeriğini listeler.",
        "ZIP SHA256 değeri self-referential olmaması için ZIP dışında üretilen dış manifestte tutulur.",
        "",
        "## Files",
        "",
    ]

    for path in evidence_files:
        lines.append(f"- {rel(path)}")

    return "\n".join(lines)

def main():
    if not A10R_JSON.exists():
        raise SystemExit("A10R JSON bulunamadı.")
    if not A10R2_JSON.exists():
        raise SystemExit("A10R2 JSON bulunamadı.")

    RELEASES.mkdir(parents=True, exist_ok=True)

    a10r = read_json(A10R_JSON)
    a10r2 = read_json(A10R2_JSON)

    evidence_files = collect_evidence_files()
    internal_manifest = build_internal_manifest(evidence_files)

    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in evidence_files:
            zf.write(path, rel(path))
        zf.writestr("CANONICAL_ZIP_INTERNAL_MANIFEST.md", internal_manifest)

    with zipfile.ZipFile(OUT_ZIP, "r") as zf:
        names = zf.namelist()

    duplicate_names = sorted([name for name, count in Counter(names).items() if count > 1])
    sha = sha256_file(OUT_ZIP)

    ok = (
        a10r.get("ok") is True
        and a10r2.get("ok") is True
        and len(duplicate_names) == 0
        and OUT_ZIP.exists()
        and OUT_ZIP.stat().st_size > 0
    )

    result = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "phase": "A10R3_CANONICAL_TECH_DEBT_EVIDENCE",
        "ok": ok,
        "decision": "A10R3_CANONICAL_EVIDENCE_GREEN" if ok else "A10R3_CANONICAL_EVIDENCE_NOT_GREEN",
        "source_a10r_ok": a10r.get("ok"),
        "source_a10r_decision": a10r.get("decision"),
        "source_a10r2_ok": a10r2.get("ok"),
        "source_a10r2_decision": a10r2.get("decision"),
        "evidence_zip": str(OUT_ZIP),
        "evidence_zip_sha256": sha,
        "evidence_file_count": len(evidence_files),
        "zip_entry_count": len(names),
        "duplicate_zip_entry_count": len(duplicate_names),
        "duplicate_zip_entries": duplicate_names,
        "source_a10r_final_counts": a10r.get("final_counts"),
        "source_a10r_pytest_summary": a10r.get("pytest_summary"),
        "canonical_rule": "ZIP SHA256 değeri ZIP dışındaki A10R3 manifestte tutulur. ZIP içine self-referential SHA yazılmaz.",
        "next_phase": "A11_WARNING_ZERO",
    }

    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        "# BYS360 A10R3 Canonical Teknik Borç Evidence Manifest",
        "",
        f"Tarih: {result['generated_at']}",
        "",
        "## Sonuç",
        "",
        f"- OK: {ok}",
        f"- Karar: {result['decision']}",
        f"- Source A10R OK: {result['source_a10r_ok']}",
        f"- Source A10R2 OK: {result['source_a10r2_ok']}",
        f"- ZIP: `{OUT_ZIP}`",
        f"- SHA256: `{sha}`",
        f"- Evidence file count: {result['evidence_file_count']}",
        f"- ZIP entry count: {result['zip_entry_count']}",
        f"- Duplicate ZIP entry count: {result['duplicate_zip_entry_count']}",
        "",
        "## Canonical Kural",
        "",
        result["canonical_rule"],
        "",
        "## Final A10 Sayımları",
        "",
        "```json",
        json.dumps(result["source_a10r_final_counts"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Pytest Özeti",
        "",
        "```json",
        json.dumps(result["source_a10r_pytest_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Duplicate Entries",
        "",
        "```json",
        json.dumps(duplicate_names, ensure_ascii=False, indent=2),
        "```",
        "",
        "## Sonraki Faz",
        "",
        result["next_phase"],
    ]

    OUT_MD.write_text("\n".join(md_lines), encoding="utf-8")

    print("A10R3_REPORT_JSON:", OUT_JSON)
    print("A10R3_REPORT_MD:", OUT_MD)
    print("A10R3_EVIDENCE_ZIP:", OUT_ZIP)
    print("A10R3_EVIDENCE_ZIP_SHA256:", sha)
    print("A10R3_EVIDENCE_FILE_COUNT:", result["evidence_file_count"])
    print("A10R3_ZIP_ENTRY_COUNT:", result["zip_entry_count"])
    print("A10R3_DUPLICATE_ZIP_ENTRY_COUNT:", result["duplicate_zip_entry_count"])
    print("A10R3_OK:", ok)

    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
