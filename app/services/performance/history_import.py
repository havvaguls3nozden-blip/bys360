from __future__ import annotations

from typing import Any
from collections.abc import Iterable

HISTORY_IMPORT_SOURCE_TYPE = "historical_excel_import"
HISTORY_IMPORT_DATA_LABEL = "gecmis_veri"
HISTORY_IMPORT_ALLOWED_EXTENSIONS = (".xlsx", ".xlsm")
HISTORY_IMPORT_REQUIRED_FIELDS = (
    "sicil_no",
    "employee_name_raw",
    "final_total_100",
)


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def parse_history_score(value: Any) -> tuple[float | None, str | None]:
    raw = _norm(value)
    if raw == "":
        return 0.0, None

    normalized = raw.replace("%", "").replace(" ", "")
    if "," in normalized and "." not in normalized:
        normalized = normalized.replace(",", ".")
    elif "," in normalized and "." in normalized:
        normalized = normalized.replace(".", "").replace(",", ".")

    try:
        numeric = round(float(normalized), 2)
    except (TypeError, ValueError):
        return None, "sayi_formati_hatasi"

    if numeric < 0 or numeric > 100:
        return None, "puan_aralik_disinda"

    return numeric, None


def normalize_history_status(value: Any) -> str:
    raw = _norm(value).lower()
    if raw in {"tamamlandi", "tamamlandı", "completed", "complete"}:
        return "tamamlandi"
    if raw in {"taslak", "draft"}:
        return "taslak"
    if raw in {"bekliyor", "beklemede", "pending"}:
        return "bekliyor"
    return raw or "tamamlandi"


def canonicalize_history_row(row_data: dict[str, Any]) -> dict[str, Any]:
    payload = {key: _norm(value) for key, value in dict(row_data or {}).items()}

    final_total, final_error = parse_history_score(payload.get("final_total_100"))
    level_1_total, level_1_error = parse_history_score(payload.get("level_1_total_100"))
    level_2_total, level_2_error = parse_history_score(payload.get("level_2_total_100"))
    level_3_total, level_3_error = parse_history_score(payload.get("level_3_total_100"))

    payload["status"] = normalize_history_status(payload.get("status"))
    payload["_history_meta"] = {
        "is_historical_data": True,
        "history_data_label": HISTORY_IMPORT_DATA_LABEL,
        "source_type": HISTORY_IMPORT_SOURCE_TYPE,
        "parsed_scores": {
            "final_total_100": final_total,
            "level_1_total_100": level_1_total,
            "level_2_total_100": level_2_total,
            "level_3_total_100": level_3_total,
        },
        "parse_errors": {
            "final_total_100": final_error,
            "level_1_total_100": level_1_error,
            "level_2_total_100": level_2_error,
            "level_3_total_100": level_3_error,
        },
        "validation_warnings": [],
    }
    return payload


def validate_history_row(row_data: dict[str, Any]) -> tuple[list[str], list[str]]:
    payload = canonicalize_history_row(row_data)
    meta = payload.get("_history_meta", {})
    parse_errors = meta.get("parse_errors", {})

    errors: list[str] = []
    warnings: list[str] = []

    if not payload.get("sicil_no"):
        errors.append("Sicil No eksik")
    if not payload.get("employee_name_raw"):
        errors.append("Ad Soyad eksik")
    if payload.get("final_total_100", "") == "":
        errors.append("Nihai puan eksik")

    for key, label in (
        ("final_total_100", "Nihai puan"),
        ("level_1_total_100", "1. amir puanı"),
        ("level_2_total_100", "2. amir puanı"),
        ("level_3_total_100", "3. amir puanı"),
    ):
        issue = parse_errors.get(key)
        if issue == "sayi_formati_hatasi":
            errors.append(f"{label} sayı formatında değil")
        elif issue == "puan_aralik_disinda":
            errors.append(f"{label} 0-100 aralığında olmalı")

    final_score = (meta.get("parsed_scores") or {}).get("final_total_100")
    if final_score is not None:
        if final_score < 70:
            warnings.append("Geçmiş veri sonucu 70 altı")
        elif final_score > 90:
            warnings.append("Geçmiş veri sonucu 90 üstü")

    level_scores = [
        (meta.get("parsed_scores") or {}).get("level_1_total_100"),
        (meta.get("parsed_scores") or {}).get("level_2_total_100"),
        (meta.get("parsed_scores") or {}).get("level_3_total_100"),
    ]
    present_level_scores = [score for score in level_scores if score not in (None, 0, 0.0)]
    if present_level_scores and final_score is not None:
        average = round(sum(present_level_scores) / len(present_level_scores), 2)
        if abs(average - final_score) > 20:
            warnings.append("Amir ortalaması ile nihai puan arasında belirgin fark var")

    meta["validation_warnings"] = warnings
    payload["_history_meta"] = meta
    return errors, warnings


def build_preview_summary(rows: Iterable[dict[str, Any]]) -> dict[str, int]:
    total = 0
    ready = 0
    errored = 0
    warned = 0
    resolved_employee = 0
    resolved_unit = 0

    for row in rows:
        total += 1
        status = _norm((row or {}).get("status"))
        if status == "hazir":
            ready += 1
        if status == "hata":
            errored += 1
        meta = (row or {}).get("_history_meta") or {}
        if meta.get("validation_warnings"):
            warned += 1
        if meta.get("resolved_employee_id"):
            resolved_employee += 1
        if meta.get("resolved_unit_id"):
            resolved_unit += 1

    return {
        "total": total,
        "ready": ready,
        "errored": errored,
        "warned": warned,
        "resolved_employee": resolved_employee,
        "resolved_unit": resolved_unit,
    }


def build_historical_snapshot_payload(
    row_data: dict[str, Any],
    *,
    batch_id: int,
    row_no: int,
    source_file: str | None,
    extra_columns: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = canonicalize_history_row(row_data)
    meta = payload.get("_history_meta", {})
    return {
        "import_batch_id": batch_id,
        "row_no": row_no,
        "criteria": [],
        "extra_columns": extra_columns or {},
        "history_data": {
            "label": HISTORY_IMPORT_DATA_LABEL,
            "source_type": HISTORY_IMPORT_SOURCE_TYPE,
            "source_file": _norm(source_file),
            "is_historical_data": True,
            "validation_warnings": list(meta.get("validation_warnings") or []),
        },
    }


def render_batch_notes(summary: dict[str, int], *, file_name: str | None = None) -> str:
    return (
        f"Geçmiş veri ön izlemesi hazır. Dosya: {_norm(file_name) or '-'} | "
        f"Toplam: {summary.get('total', 0)} | Hazır: {summary.get('ready', 0)} | "
        f"Hatalı: {summary.get('errored', 0)} | Uyarılı: {summary.get('warned', 0)} | "
        f"Personel eşleşen: {summary.get('resolved_employee', 0)} | "
        f"Birim eşleşen: {summary.get('resolved_unit', 0)}"
    )


__all__ = [
    "HISTORY_IMPORT_ALLOWED_EXTENSIONS",
    "HISTORY_IMPORT_DATA_LABEL",
    "HISTORY_IMPORT_REQUIRED_FIELDS",
    "HISTORY_IMPORT_SOURCE_TYPE",
    "build_historical_snapshot_payload",
    "build_preview_summary",
    "canonicalize_history_row",
    "normalize_history_status",
    "parse_history_score",
    "render_batch_notes",
    "validate_history_row",
]