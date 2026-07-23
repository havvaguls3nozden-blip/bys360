from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from .hierarchy_rule_engine_service import HierarchyRuleEngineService, UserRow

# --- BYS360 third-manager Excel import compatibility patch ---


THIRD_MANAGER_STANDARD_KEY = "ucuncu_yonetici_sicil"
THIRD_MANAGER_HEADER_ALIASES = [
    "ucuncu_yonetici_sicil",
    "üçüncü yönetici sicil",
    "ucuncu yonetici sicil",
    "3. amir sicil",
    "3 amir sicil",
    "new_y3",
]


class HierarchyExcelPreviewService:
    def __init__(self, report_dir: str | Path | None = None, config_path: str | Path | None = None):
        self.engine = HierarchyRuleEngineService(config_path=config_path)
        self.report_dir = Path(report_dir or (Path.cwd() / "reports" / "faz3_6"))
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def preview_excel(self, excel_path: str | Path) -> dict[str, Any]:
        users = self._read_excel(excel_path)
        resolved = self.engine.resolve_many(users)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = self.report_dir / f"faz3_6_preview_{timestamp}.json"
        csv_path = self.report_dir / f"faz3_6_preview_{timestamp}.csv"
        txt_path = self.report_dir / f"faz3_6_preview_{timestamp}.txt"

        summary = {
            "ok": True,
            "input_count": len(users),
            "resolved_count": len(resolved),
            "warning_count": sum(len(r.get("warnings", [])) for r in resolved),
            "info_count": sum(len(r.get("info", [])) for r in resolved),
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "rows": resolved,
        }
        json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        self._write_csv(csv_path, resolved)
        txt_path.write_text(self._build_txt(summary), encoding="utf-8")
        summary.update({"json_path": str(json_path), "csv_path": str(csv_path), "txt_path": str(txt_path)})
        return summary

    def _read_excel(self, excel_path: str | Path) -> list[UserRow]:
        wb = load_workbook(filename=str(excel_path), data_only=True)
        ws = wb.active
        headers = [self._norm(h) for h in next(ws.iter_rows(min_row=1, max_row=1, values_only=True))]
        rows: list[UserRow] = []
        for values in ws.iter_rows(min_row=2, values_only=True):
            payload = {headers[i]: values[i] for i in range(min(len(headers), len(values)))}
            if not str(payload.get("sicil_no") or "").strip():
                continue
            full_name = str(payload.get("full_name") or payload.get("ad_soyad") or payload.get("ad soyad") or payload.get("adi_soyadi") or "").strip()
            if not full_name:
                ad = str(payload.get("ad") or "").strip()
                soyad = str(payload.get("soyad") or "").strip()
                full_name = f"{ad} {soyad}".strip()
            row = UserRow(
                id=None,
                sicil_no=str(payload.get("sicil_no") or "").strip(),
                full_name=full_name,
                role=str(payload.get("role") or payload.get("rol") or "").strip().lower(),
                unvan=str(payload.get("unvan") or "").strip(),
                birim=str(payload.get("birim") or "").strip(),
                ust_birim=str(payload.get("ust_birim") or payload.get("üst_birim") or payload.get("ust birim") or payload.get("üst birim") or "").strip(),
                yonetici_sicil=str(payload.get("yonetici_sicil") or payload.get("1_amir_sicil") or payload.get("1. amir") or "").strip(),
                ikinci_yonetici_sicil=str(payload.get("ikinci_yonetici_sicil") or payload.get("2_amir_sicil") or payload.get("2. amir") or "").strip(),
                ucuncu_yonetici_sicil=str(payload.get("ucuncu_yonetici_sicil") or payload.get("3_amir_sicil") or payload.get("3. amir") or "").strip(),
                source="excel",
                raw={k: ("" if v is None else v) for k, v in payload.items()},
            )
            rows.append(row)
        return rows

    @staticmethod
    def _norm(value: Any) -> str:
        return str(value or "").strip().lower().replace(" ", "_")

    @staticmethod
    def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
        fieldnames = [
            "sicil_no", "full_name", "role", "unvan", "birim", "ust_birim",
            "rule_key", "chain_type", "order",
            "manager_1_sicil", "manager_1_name",
            "manager_2_sicil", "manager_2_name",
            "manager_3_sicil", "manager_3_name",
            "warnings", "info",
        ]
        with path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                out = {k: row.get(k, "") for k in fieldnames}
                out["warnings"] = " | ".join(row.get("warnings", []))
                out["info"] = " | ".join(row.get("info", []))
                writer.writerow(out)

    @staticmethod
    def _build_txt(summary: dict[str, Any]) -> str:
        lines = [
            "BYS360 Faz 3.6 - Amir Zinciri Ayar Paneli / Excel Önizleme",
            "=" * 72,
            f"Üretilme zamanı: {summary['generated_at']}",
            "",
            "Özet",
            f"- Girdi satırı: {summary['input_count']}",
            f"- Çözümlenen satır: {summary['resolved_count']}",
            f"- Warning: {summary['warning_count']}",
            f"- Info: {summary['info_count']}",
            "",
            "İlk 10 satır özeti",
        ]
        for row in summary["rows"][:10]:
            lines.append(
                f"- {row.get('full_name','')} | {row.get('rule_key','')} | 1={row.get('manager_1_name','-')} | 2={row.get('manager_2_name','-')} | 3={row.get('manager_3_name','-')}"
            )
        return "\n".join(lines) + "\n"