from __future__ import annotations

import csv
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict
from collections.abc import Iterable


SPECIAL_INFO_PATTERNS = (
    "hukuk müşavirliği zinciri düzeltildi",
    "hukuk musavirligi zinciri duzeltildi",
    "tek amir kuralı",
    "tek amir kurali",
    "ast-üst tek amir",
    "ast-ust tek amir",
    "üst yönetim düğümü",
    "ust yonetim dugumu",
    "evaluator gerekmeyebilir",
)

OPTIONAL_THIRD_MANAGER_PATTERNS = (
    "3. amir",
    "birim amiri bulunamadı",
)


@dataclass
class DashboardIssue:
    person_name: str
    unit_name: str
    raw_label: str
    normalized_severity: str
    reason: str
    should_display_red: bool

def _normalize_text(value: str) -> str:
    return (value or "").strip().lower()

def normalize_issue(person_name: str, unit_name: str, raw_label: str, message: str) -> DashboardIssue:
    raw = _normalize_text(raw_label)
    detail = _normalize_text(message)

    if any(token in detail for token in SPECIAL_INFO_PATTERNS):
        return DashboardIssue(
            person_name=person_name,
            unit_name=unit_name,
            raw_label=raw_label,
            normalized_severity="info",
            reason="Kurallı istisna veya düzeltilmiş zincir bilgi notu.",
            should_display_red=False,
        )

    if all(token in detail for token in OPTIONAL_THIRD_MANAGER_PATTERNS):
        return DashboardIssue(
            person_name=person_name,
            unit_name=unit_name,
            raw_label=raw_label,
            normalized_severity="info",
            reason="Opsiyonel 3. amir alanı eksikliği kırmızı kritik olmamalı.",
            should_display_red=False,
        )

    if raw in {"critical", "kritik", "error", "danger"}:
        sev = "critical"
    elif raw in {"warning", "uyarı", "warn"}:
        sev = "warning"
    else:
        sev = "info"

    return DashboardIssue(
        person_name=person_name,
        unit_name=unit_name,
        raw_label=raw_label,
        normalized_severity=sev,
        reason="Ham UI etiketi korundu; manuel gözden geçirme gerekebilir.",
        should_display_red=sev == "critical",
    )

def export_dashboard_alignment_report(project_root: Path, issues: Iterable[DashboardIssue]) -> dict[str, Path]:
    out_dir = project_root / "reports" / "faz3_1"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = out_dir / f"faz3_1_dashboard_alignment_{ts}.csv"
    json_path = out_dir / f"faz3_1_dashboard_alignment_{ts}.json"
    txt_path = out_dir / f"faz3_1_dashboard_alignment_{ts}.txt"

    rows = [asdict(item) for item in issues]

    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "person_name",
                "unit_name",
                "raw_label",
                "normalized_severity",
                "reason",
                "should_display_red",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    json_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "row_count": len(rows),
                "rows": rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    critical = sum(1 for row in rows if row["normalized_severity"] == "critical")
    warning = sum(1 for row in rows if row["normalized_severity"] == "warning")
    info = sum(1 for row in rows if row["normalized_severity"] == "info")
    txt_path.write_text(
        "\n".join(
            [
                "BYS360 Faz 3.1 - Risk Dashboard Hizalama Özeti",
                "================================================",
                f"Üretilme zamanı: {datetime.now().isoformat(timespec='seconds')}",
                "",
                f"Toplam satır: {len(rows)}",
                f"Kritik: {critical}",
                f"Uyarı: {warning}",
                f"Bilgi: {info}",
                "",
                "Not:",
                "- Kurallı istisnalar ile opsiyonel 3. amir satırları kırmızı kritik görünmemelidir.",
            ]
        ) + "\n",
        encoding="utf-8",
    )

    return {"csv": csv_path, "json": json_path, "txt": txt_path}