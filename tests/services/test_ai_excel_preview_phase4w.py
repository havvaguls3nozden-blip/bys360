from __future__ import annotations

import sys
from pathlib import Path

PHASE4W_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PHASE4W_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PHASE4W_PROJECT_ROOT))
import io
from datetime import date, datetime
from decimal import Decimal

import pytest
from werkzeug.datastructures import FileStorage

from app.services.ai import excel_preview as svc


def test_phase4w_safety_flags_and_basic_converters() -> None:
    assert svc.GERCEK_ICE_AKTARIM_YOK is True
    assert svc.DB_WRITE_ENABLED is False
    assert svc.ALLOWED_ANALYSIS_EXTENSIONS == {"xlsx", "csv"}

    assert svc._safe_int("12", default=8, minimum=3, maximum=25) == 12
    assert svc._safe_int("999", default=8, minimum=3, maximum=25) == 25
    assert svc._safe_int("bozuk", default=8, minimum=3, maximum=25) == 8
    assert svc._safe_int("1", default=8, minimum=3, maximum=25) == 3

    assert svc.normalize_header(" TC-Kimlik.No ") == "tc kimlik no"
    assert svc.normalize_header("E_Posta") == "e posta"

    assert svc._cell_to_text(None) == ""
    assert svc._cell_to_text(date(2026, 7, 11)) == "11.07.2026"
    assert svc._cell_to_text(datetime(2026, 7, 11, 14, 30)) == "11.07.2026 14:30"
    assert svc._cell_to_text(Decimal("123.4500")) == "123.4500"
    assert svc._cell_to_text(12.0) == "12"

    long_value = "A" * (svc.MAX_CELL_TEXT + 5)
    assert len(svc._cell_to_text(long_value)) == svc.MAX_CELL_TEXT + 1


def test_phase4w_sensitivity_and_masking_helpers() -> None:
    assert svc._is_formula_text("=SUM(A1:A2)") is True
    assert svc._is_formula_text("+A1") is True
    assert svc._is_formula_text("normal metin") is False
    assert svc._is_formula_text("") is False

    high_level, high_reason = svc._header_sensitivity("tc kimlik no")
    medium_level, medium_reason = svc._header_sensitivity("personel birim")
    low_level, low_reason = svc._header_sensitivity("genel konu")

    assert high_level == "yüksek"
    assert "veri" in high_reason.lower()
    assert medium_level == "orta"
    assert "personel" in medium_reason.lower()
    assert low_level == "düşük"
    assert "düşük" in low_reason.lower()

    assert svc._value_sensitivity("TR330006100519786457841326")[0] == "yüksek"
    assert svc._value_sensitivity("12345678901")[0] == "yüksek"
    assert svc._value_sensitivity("ada@example.com")[0] == "yüksek"
    assert svc._value_sensitivity("05321234567")[0] == "yüksek"
    assert svc._value_sensitivity("1234567")[0] == "orta"
    assert svc._value_sensitivity("sade metin") == (None, None)

    assert svc._merge_sensitivity("düşük", None) == "düşük"
    assert svc._merge_sensitivity("orta", None) == "orta"
    assert svc._merge_sensitivity("düşük", "yüksek") == "yüksek"

    assert "FORM" in svc.mask_cell_value("=SUM(A1:A2)").upper()
    assert "***@" in svc.mask_cell_value("ada@example.com")
    assert "*" in svc.mask_cell_value("12345678901")
    assert "…" in svc.mask_cell_value("123456789")


def test_phase4w_dataclass_to_dict_metrics_and_empty_context() -> None:
    high_column = svc.ColumnProfile(
        index=0,
        header="TC Kimlik",
        normalized_header="tc kimlik",
        inferred_type="metin",
        sensitivity="yüksek",
        kvkk_reason="TC kimlik sinyali",
        non_empty_count=2,
        empty_count=0,
        formula_count=0,
        sample_values=["12*******01"],
    )
    low_column = svc.ColumnProfile(
        index=1,
        header="Açıklama",
        normalized_header="aciklama",
        inferred_type="metin",
        sensitivity="düşük",
        kvkk_reason="Düşük sinyal",
        non_empty_count=1,
        empty_count=1,
        formula_count=1,
        sample_values=["not"],
    )

    assert high_column.to_dict()["header"] == "TC Kimlik"
    assert high_column.to_dict()["sensitivity"] == "yüksek"

    result = svc.SafeExcelPreviewResult(
        ok=True,
        import_enabled=False,
        db_write_enabled=False,
        original_filename="ornek.csv",
        extension="csv",
        detected_mime="text/csv",
        file_size=128,
        sheet_name="CSV",
        sheet_names=["CSV"],
        header_row_index=1,
        row_count_visible=2,
        row_count_estimated=2,
        column_count=2,
        preview_limit=8,
        scan_limit=250,
        truncated=False,
        columns=[high_column, low_column],
        preview_rows=[{"row_number": 1, "cells": []}],
        warnings=["CSV kodlaması utf-8 olarak okundu."],
        kvkk_warnings=["KVKK uyarısı"],
        security_findings=[],
        duplicate_headers=[],
        empty_headers=[],
        formula_cells=1,
    )

    assert result.sensitive_column_count == 1
    assert result.metrics["sensitive_column_count"] == 1
    assert result.metrics["formula_cells"] == 1

    as_dict = result.to_dict()
    assert as_dict["ok"] is True
    assert as_dict["import_enabled"] is False
    assert as_dict["db_write_enabled"] is False
    assert as_dict["columns"][0]["header"] == "TC Kimlik"
    assert as_dict["metrics"]["column_count"] == 2

    empty_context = svc.build_empty_excel_preview_context()
    assert empty_context["preview"] is None
    assert empty_context["import_enabled"] is False
    assert empty_context["db_write_enabled"] is False
    assert "csv" in empty_context["allowed_extensions"]
    assert "xlsx" in empty_context["allowed_extensions"]


def test_phase4w_matrix_profiles_and_preview_rows() -> None:
    headers = ["TC Kimlik", "E posta", "Puan", ""]
    rows = [
        ["12345678901", "ada@example.com", 85, "=SUM(A1:A2)"],
        ["", "veli@example.com", 90, "normal not"],
    ]

    normalized_headers, normalized_rows = svc._normalize_matrix_width(headers, rows)
    assert len(normalized_headers) == 4
    assert all(len(row) == 4 for row in normalized_rows)

    columns, duplicate_headers, empty_headers, formula_cells = svc._build_profiles(
        normalized_headers,
        normalized_rows,
    )

    assert len(columns) == 4
    assert duplicate_headers == []
    assert empty_headers == [4]
    assert formula_cells == 1
    assert columns[0].sensitivity == "yüksek"
    assert columns[1].sensitivity == "yüksek"
    assert columns[3].header == "Kolon 4"

    preview_rows = svc._build_preview_rows(normalized_headers, normalized_rows, sample_limit=1)
    assert len(preview_rows) == 1
    assert preview_rows[0]["row_number"] == 1
    assert len(preview_rows[0]["cells"]) == 4
    assert any("FORM" in cell["value"].upper() for cell in preview_rows[0]["cells"])


def test_phase4w_csv_reader_and_safe_preview_with_patched_upload_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = (
        "TC Kimlik;E posta;Puan;Not\n"
        "12345678901;ada@example.com;85;=SUM(A1:A2)\n"
        "98765432109;veli@example.com;90;normal not\n"
    ).encode("utf-8")

    headers, data_rows, warnings, header_index, estimated, truncated = svc._read_csv_rows(
        payload,
        scan_limit=50,
    )

    assert headers == ["TC Kimlik", "E posta", "Puan", "Not"]
    assert len(data_rows) == 2
    assert header_index == 1
    assert estimated == 3
    assert truncated is False
    assert any("CSV" in warning for warning in warnings)

    def fake_validate_upload(file, *, allowed_extensions, max_size):
        assert allowed_extensions == {"xlsx", "csv"}
        assert max_size == svc.MAX_ANALYSIS_FILE_SIZE
        return {
            "extension": "csv",
            "original_filename": file.filename,
            "detected_mime": "text/csv",
            "size": len(payload),
        }

    monkeypatch.setattr(svc, "validate_upload", fake_validate_upload)

    file_storage = FileStorage(
        stream=io.BytesIO(payload),
        filename="ornek.csv",
        content_type="text/csv",
    )

    result = svc.build_safe_excel_preview(
        file_storage,
        sample_limit="5",
        scan_limit="50",
    )

    assert result.ok is True
    assert result.import_enabled is False
    assert result.db_write_enabled is False
    assert result.extension == "csv"
    assert result.sheet_name == "CSV"
    assert result.sheet_names == ["CSV"]
    assert result.column_count == 4
    assert result.row_count_visible == 2
    assert result.preview_limit == 5
    assert result.scan_limit == 50
    assert result.formula_cells == 1
    assert result.sensitive_column_count >= 2
    assert result.kvkk_warnings
    assert result.preview_rows
    assert result.to_dict()["metrics"]["column_count"] == 4


def test_phase4w_csv_validation_errors_are_safe() -> None:
    with pytest.raises(svc.ExcelPreviewValidationError):
        svc._first_non_empty_row([[None, ""], ["", None]])

    with pytest.raises(svc.ExcelPreviewValidationError):
        svc._normalize_matrix_width([], [])

    with pytest.raises(svc.ExcelPreviewValidationError):
        svc._read_csv_rows(b"", scan_limit=50)


