from __future__ import annotations

import argparse
import csv
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class TestRow:
    status: str
    category: str
    file: str
    classname: str
    test: str
    detail: str


def _text(v: object) -> str:
    return "" if v is None else str(v)


def classify_category(text: str) -> str:
    t = text.lower()
    if "sprint3" in t:
        return "sprint3_integration"
    if "sprint2" in t:
        return "sprint2_integration"
    if "ai_agent" in t or "agent" in t or "repository" in t:
        return "ai_agent_repository"
    if "realdb" in t or "postgres" in t or "database" in t or "db" in t or "sqlite" in t:
        return "database_contract"
    if "live" in t or "external" in t or "network" in t:
        return "live_external"
    if "auth" in t or "login" in t or "csrf" in t or "session" in t:
        return "auth_session"
    if "performance" in t or "performans" in t:
        return "performance"
    if "portal" in t:
        return "portal"
    if "communication" in t or "cic" in t or "mail" in t or "email" in t or "message" in t or "survey" in t:
        return "communication_mail"
    if "mobile" in t or "android" in t or "ios" in t or "pwa" in t:
        return "mobile_pwa"
    if "quality" in t or "gate" in t or "release" in t or "faz" in t or "phase" in t:
        return "quality_release"
    return "other"


def load_rows_from_csv(path: Path) -> list[TestRow]:
    rows: list[TestRow] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(TestRow(
                status=_text(r.get("status")),
                category=_text(r.get("category")) or classify_category(" ".join(_text(r.get(k)) for k in ("file", "classname", "test", "detail"))),
                file=_text(r.get("file")),
                classname=_text(r.get("classname")),
                test=_text(r.get("test")),
                detail=_text(r.get("detail")),
            ))
    return rows


def load_rows_from_junit(path: Path) -> list[TestRow]:
    tree = ET.parse(path)
    cases = tree.findall(".//testcase")
    rows: list[TestRow] = []
    for tc in cases:
        name = tc.get("name") or ""
        classname = tc.get("classname") or ""
        file_attr = tc.get("file") or ""
        detail = ""
        status = "passed"
        failure = tc.find("failure")
        error = tc.find("error")
        skipped = tc.find("skipped")
        if failure is not None:
            status = "failed"
            detail = (failure.get("message") or failure.text or "").replace("\n", " ")[:1200]
        elif error is not None:
            status = "error"
            detail = (error.get("message") or error.text or "").replace("\n", " ")[:1200]
        elif skipped is not None:
            status = "skipped"
            detail = (skipped.get("message") or skipped.text or "").replace("\n", " ")[:1200]
        category = classify_category(f"{file_attr} {classname} {name} {detail}")
        rows.append(TestRow(status, category, file_attr, classname, name, detail))
    return rows


def combined(row: TestRow) -> str:
    return f"{row.file} {row.classname} {row.test} {row.detail}".lower()


def decide(row: TestRow) -> tuple[str, str, str]:
    """Return action, priority, reason."""
    t = combined(row)
    if row.status not in {"failed", "error"}:
        return "keep", "P4", "passing_or_skipped"

    if "fixture 'app' not found" in t or "fixture \"app\" not found" in t:
        return "fix_test_infra", "P0", "pytest app/client fixture missing; many critical errors likely share one root cause"

    obsolete_patterns = [
        "sprint2", "sprint3", "closure", "freeze", "pilot", "uat", "faz", "phase",
        "release_evidence", "release_candidate", "release_manifest", "evidence_bundle",
        "quality_chain", "final_quality", "phase11", "phase5", "phase6", "phase7",
        "gate script exists", "doc exists", "missing", "filenotfounderror",
    ]
    if row.category in {"quality_release", "sprint3_integration", "sprint2_integration"}:
        return "archive_or_delete_obsolete_contract", "P1", "phase/evidence/release contract test appears to validate historical artifacts rather than current runtime behavior"
    if any(p in t for p in obsolete_patterns) and ("test_" in row.classname or "tests." in row.classname):
        return "archive_or_delete_obsolete_contract", "P1", "historical phase/evidence artifact contract; remove or move to tests/archive with explicit rationale"

    if row.category in {"live_external"}:
        return "move_to_live_realdb_slow_marker", "P1", "test depends on live/external/deployment semantics; keep out of default CI unless isolated"

    if "no such table" in t or "operationalerror" in t or "sqlite" in t or "database" in t or "db.session" in t:
        return "fix_or_mark_realdb_contract", "P1", "database contract/schema/write-flow issue; either create isolated fixture or mark realdb"

    if "return_500" in t or "do_not_return_500" in t or "route" in t or "login" in t or "csrf" in t or "session" in t:
        return "fix_runtime_or_route_contract", "P1", "route/auth/session behavior test; likely useful for pilot stability"

    if row.category in {"auth_session", "performance", "portal", "communication_mail", "ai_agent_repository"}:
        return "fix_runtime_or_contract", "P2", "module-level contract likely still valuable; review and update implementation or test expectation"

    if row.category in {"mobile_pwa"}:
        return "archive_or_split_mobile_evidence", "P2", "mobile evidence/gate test should be separated from web CI unless it checks current mobile runtime"

    return "manual_review", "P3", "cannot safely classify automatically"


def normalize_file(row: TestRow) -> str:
    if row.file:
        return row.file
    return row.classname.replace(".", "/") + ".py" if row.classname else ""


def write_reports(rows: list[TestRow], root: Path) -> dict[str, object]:
    out_dir = root / "reports" / "quality"
    out_dir.mkdir(parents=True, exist_ok=True)
    decision_csv = out_dir / "BYS360_A5_TEST_TRIAGE_DECISIONS.csv"
    action_md = out_dir / "BYS360_A5_TEST_TRIAGE_ACTION_PLAN.md"
    summary_json = out_dir / "BYS360_A5_TEST_TRIAGE_SUMMARY.json"
    archive_list = out_dir / "BYS360_A5_ARCHIVE_OR_DELETE_CANDIDATES.txt"
    fix_list = out_dir / "BYS360_A5_FIX_FIRST_CANDIDATES.txt"
    marker_list = out_dir / "BYS360_A5_MARKER_MOVE_CANDIDATES.txt"

    decision_rows = []
    action_counts = Counter()
    status_counts = Counter(r.status for r in rows)
    category_counts = Counter((r.status, r.category) for r in rows)
    action_by_category = Counter()
    by_action: dict[str, list[dict[str, str]]] = defaultdict(list)

    for r in rows:
        action, priority, reason = decide(r)
        file_name = normalize_file(r)
        rec = {
            "status": r.status,
            "category": r.category,
            "action": action,
            "priority": priority,
            "reason": reason,
            "file": file_name,
            "classname": r.classname,
            "test": r.test,
            "detail": r.detail,
        }
        decision_rows.append(rec)
        if r.status in {"failed", "error"}:
            action_counts[action] += 1
            action_by_category[(action, r.category)] += 1
            by_action[action].append(rec)

    with decision_csv.open("w", newline="", encoding="utf-8") as f:
        fieldnames = ["status", "category", "action", "priority", "reason", "file", "classname", "test", "detail"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(decision_rows)

    def write_action_list(path: Path, actions: Iterable[str]) -> None:
        selected = [r for r in decision_rows if r["action"] in set(actions)]
        with path.open("w", encoding="utf-8") as f:
            for r in selected:
                f.write(f'{r["priority"]}\t{r["action"]}\t{r["category"]}\t{r["classname"]}::{r["test"]}\n')
                if r["reason"]:
                    f.write(f'    reason: {r["reason"]}\n')
                if r["detail"]:
                    f.write(f'    detail: {r["detail"][:300]}\n')

    write_action_list(archive_list, {"archive_or_delete_obsolete_contract", "archive_or_split_mobile_evidence"})
    write_action_list(fix_list, {"fix_test_infra", "fix_runtime_or_route_contract", "fix_runtime_or_contract", "fix_or_mark_realdb_contract", "manual_review"})
    write_action_list(marker_list, {"move_to_live_realdb_slow_marker", "fix_or_mark_realdb_contract"})

    summary = {
        "package": "BYS360_A5_TEST_TRIAGE_SAFE_V1",
        "ok": True,
        "total_cases": len(rows),
        "status_counts": dict(status_counts),
        "failed_error_total": status_counts.get("failed", 0) + status_counts.get("error", 0),
        "action_counts": dict(action_counts),
        "status_category_counts": {f"{s}:{c}": n for (s, c), n in sorted(category_counts.items())},
        "action_category_counts": {f"{a}:{c}": n for (a, c), n in sorted(action_by_category.items())},
        "outputs": {
            "decisions_csv": str(decision_csv),
            "action_plan_md": str(action_md),
            "summary_json": str(summary_json),
            "archive_or_delete_candidates": str(archive_list),
            "fix_first_candidates": str(fix_list),
            "marker_move_candidates": str(marker_list),
        },
        "recommended_next_step": "Start with P0 fix_test_infra, then archive/delete obsolete phase-evidence contracts, then move live/realdb tests behind explicit markers.",
    }

    with summary_json.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    with action_md.open("w", encoding="utf-8") as f:
        f.write("# BYS360 Aşama 5 Test Triage Aksiyon Planı\n\n")
        f.write("Bu rapor testleri otomatik silmez veya değiştirmez. Ama başarısız/hatalı testleri güvenli aksiyon sınıflarına ayırır.\n\n")
        f.write("## Genel Durum\n\n")
        f.write(f"- Toplam test case: **{len(rows)}**\n")
        for k, v in sorted(status_counts.items()):
            f.write(f"- {k}: **{v}**\n")
        f.write(f"- Failed + Error: **{summary['failed_error_total']}**\n\n")
        f.write("## Aksiyon Sayıları\n\n")
        for action, count in action_counts.most_common():
            f.write(f"- {action}: **{count}**\n")
        f.write("\n## Öncelik Sırası\n\n")
        f.write("### P0 — Test altyapısını düzelt\n")
        f.write("`fixture 'app' not found` hataları çok sayıda testi tek kökten bozuyor. Önce `tests/critical/conftest.py` veya kök `tests/conftest.py` altında `app` ve `client` fixture sözleşmesi netleştirilmeli.\n\n")
        f.write("### P1 — Eski faz/evidence sözleşmelerini arşivle veya sil\n")
        f.write("Sprint2/Sprint3/Faz/Release evidence testlerinin çoğu bugünkü runtime kalitesini değil geçmiş dosya varlığını test ediyor. Geçersiz olanlar `tests/archive/` altına alınmalı veya silinmeli.\n\n")
        f.write("### P1 — live/realdb/slow marker ayrımı\n")
        f.write("Canlı, dış servis, deployment, PostgreSQL veya gerçek DB isteyen testler varsayılan CI’dan çıkarılıp açık marker ile çalıştırılmalı.\n\n")
        f.write("### P2 — Gerçek runtime/modül sözleşmelerini düzelt\n")
        f.write("Auth, feedback, performance, portal, communication ve AI repository testlerinden gerçekten canlı davranışı ölçenler korunmalı ve düzeltilmeli.\n\n")
        f.write("## Üretilen Dosyalar\n\n")
        for k, v in summary["outputs"].items():
            f.write(f"- {k}: `{v}`\n")

    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--csv", default="reports/quality/BYS360_A5_TEST_FAILURE_TRIAGE.csv")
    parser.add_argument("--junit", default="reports/quality/BYS360_A5_FULL_TESTS_JUNIT.xml")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    csv_path = root / args.csv
    junit_path = root / args.junit

    if csv_path.exists():
        rows = load_rows_from_csv(csv_path)
        source = str(csv_path)
    elif junit_path.exists():
        rows = load_rows_from_junit(junit_path)
        source = str(junit_path)
    else:
        raise SystemExit(f"Triage source not found: {csv_path} or {junit_path}")

    summary = write_reports(rows, root)
    summary["source"] = source
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
