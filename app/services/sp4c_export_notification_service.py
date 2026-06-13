from __future__ import annotations

# -*- coding: utf-8 -*-



import csv
import json
import os
import zipfile
from datetime import datetime
from html import escape
from pathlib import Path


def sample_rows():
    return [
        {"kod": "KPI-2026-01", "hedef": "Ziyaretçi memnuniyet oranı", "birim": "Eğitim ve Performans", "oran": 82, "risk": "Orta"},
        {"kod": "KPI-2026-02", "hedef": "Eğitim tamamlama oranı", "birim": "Personel ve Destek", "oran": 94, "risk": "Düşük"},
        {"kod": "KPI-2026-03", "hedef": "Geciken görevlerin azaltılması", "birim": "Koordinatörler", "oran": 66, "risk": "Yüksek"},
    ]


def write_csv(out_dir: Path, rows):
    path = out_dir / "sp4c_kpi_export_test.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
    return path


def xlsx_cell(col_idx, row_idx, value):
    col = ""
    n = col_idx
    while n:
        n, rem = divmod(n - 1, 26)
        col = chr(65 + rem) + col
    return f'<c r="{col}{row_idx}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>'


def write_xlsx(out_dir: Path, rows):
    path = out_dir / "sp4c_kpi_export_test.xlsx"
    headers = list(rows[0].keys())
    sheet_rows = ['<row r="1">' + ''.join(xlsx_cell(i + 1, 1, h) for i, h in enumerate(headers)) + '</row>']
    for r, row in enumerate(rows, start=2):
        sheet_rows.append('<row r="%s">%s</row>' % (r, ''.join(xlsx_cell(c + 1, r, row.get(h, "")) for c, h in enumerate(headers))))
    sheet = '<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>' + ''.join(sheet_rows) + '</sheetData></worksheet>'
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr("xl/workbook.xml", '<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="SP4C" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels", '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    return path


def pdf_escape(s):
    return str(s).encode("latin-1", "replace").decode("latin-1").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_pdf(out_dir: Path, rows):
    path = out_dir / "sp4c_kpi_export_test.pdf"
    lines = ["BYS360 SP-4C Export Test", "PDF / Excel / CSV cikti testi", datetime.now().strftime("%Y-%m-%d %H:%M")]
    lines += [f"{r['kod']} | {r['hedef']} | %{r['oran']} | {r['risk']}" for r in rows]
    commands = ["BT", "/F1 11 Tf", "50 790 Td"]
    for i, line in enumerate(lines):
        if i:
            commands.append("0 -18 Td")
        commands.append(f"({pdf_escape(line)}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("latin-1", "replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    data = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(data))
        data += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(data)
    data += f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode()
    for off in offsets[1:]:
        data += f"{off:010d} 00000 n \n".encode()
    data += f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    path.write_bytes(bytes(data))
    return path


def generate_export_test_files(out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = sample_rows()
    files = {
        "csv": str(write_csv(out_dir, rows)),
        "xlsx": str(write_xlsx(out_dir, rows)),
        "pdf": str(write_pdf(out_dir, rows)),
    }
    (out_dir / "sp4c_export_manifest.json").write_text(json.dumps({"files": files, "row_count": len(rows)}, ensure_ascii=False, indent=2), encoding="utf-8")
    return files


def email_readiness():
    host = os.environ.get("MAIL_SERVER") or os.environ.get("SMTP_HOST")
    port = os.environ.get("MAIL_PORT") or os.environ.get("SMTP_PORT")
    sender = os.environ.get("MAIL_DEFAULT_SENDER") or os.environ.get("SMTP_SENDER") or os.environ.get("MAIL_USERNAME") or os.environ.get("SMTP_USERNAME")
    return {
        "configured": bool(host and port and sender),
        "mode": "smtp_ready" if host and port and sender else "system_notification_ready_smtp_external",
        "note": "SMTP hazır." if host and port and sender else "Sistem içi bildirim hazır; SMTP bilgileri canlı ortamda tanımlanmalıdır.",
    }
