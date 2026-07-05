from pathlib import Path
from datetime import datetime

from app import create_app
from app.digital_archive.model_contract import get_digital_archive_table_names
from app.digital_archive import models as _digital_archive_models  # noqa: F401


ROOT = Path.cwd()
STAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
REPORT_DIR = Path(r"C:\bys360\reports") / f"digital_archive_da3c_management_center_render_smoke_{STAMP}"
REPORT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH = REPORT_DIR / "DA3C_MANAGEMENT_CENTER_RENDER_SMOKE.md"

TARGET_PATH = "/digital-archive/"

errors = []

app = create_app()
app.config["TESTING"] = True
app.config["LOGIN_DISABLED"] = True

client = app.test_client()

with app.app_context():
    expected_tables = set(get_digital_archive_table_names())
    metadata_tables = set(app.extensions["sqlalchemy"].metadata.tables.keys())
    missing_metadata = sorted(expected_tables.difference(metadata_tables))

    if missing_metadata:
        errors.append("Metadata eksik: " + ", ".join(missing_metadata))

    # 1) Modül kapalıyken disabled ekranı dönmeli.
    app.config["DIGITAL_ARCHIVE_ENABLED"] = False
    disabled_response = client.get(TARGET_PATH)
    disabled_status = disabled_response.status_code
    disabled_text = disabled_response.get_data(as_text=True)

    if disabled_status != 200:
        errors.append(f"Modül kapalı GET {TARGET_PATH} beklenen 200 değil: {disabled_status}")

    if "Dijital Arşiv" not in disabled_text:
        errors.append("Modül kapalı response içinde 'Dijital Arşiv' ifadesi bulunamadı.")

    # 2) Modül açıkken yönetim merkezi render olmalı.
    app.config["DIGITAL_ARCHIVE_ENABLED"] = True
    enabled_response = client.get(TARGET_PATH)
    enabled_status = enabled_response.status_code
    enabled_text = enabled_response.get_data(as_text=True)

    if enabled_status != 200:
        errors.append(f"Modül açık GET {TARGET_PATH} beklenen 200 değil: {enabled_status}")

    required_enabled_tokens = [
        "Dijital Arşiv",
        "Altyapı Durumu",
        "Canlı işlem yok",
        "Veritabanı altyapısı",
        "digital_archive_documents",
    ]

    for token in required_enabled_tokens:
        if token not in enabled_text:
            errors.append(f"Modül açık response içinde beklenen ifade yok: {token}")

    # Salt-okunur dashboard tablo sayıları 0 olsa da ekran dönmeli.
    if "Hazır Tablo" not in enabled_text:
        errors.append("Modül açık response içinde 'Hazır Tablo' göstergesi bulunamadı.")

lines = [
    "# BYS360 DA-3C Dijital Arşiv Yönetim Merkezi Render Smoke",
    "",
    "Bu kontrol dosya veya DB değiştirmez. Flask test client ile lokal render doğrulaması yapar.",
    "",
    f"- Zaman: `{datetime.now().isoformat(timespec='seconds')}`",
    f"- Test path: `{TARGET_PATH}`",
    f"- Expected table count: `{len(get_digital_archive_table_names())}`",
    "",
    "## Modül kapalı kontrolü",
    f"- HTTP status: `{disabled_status}`",
    "- Beklenti: `disabled.html` güvenli ekranı render olmalı.",
    "",
    "## Modül açık kontrolü",
    f"- HTTP status: `{enabled_status}`",
    "- Beklenti: `digital_archive/index.html` yönetim merkezi render olmalı.",
    "",
    "## Hatalar",
]

if errors:
    lines.extend([f"- {error}" for error in errors])
else:
    lines.append("- Yok")

lines.extend([
    "",
    "## Sonuç",
    "OK: DA-3C render smoke başarılı." if not errors else "FAIL: DA-3C render smoke başarısız.",
])

REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

if errors:
    print("DA-3C RENDER SMOKE FAIL")
    print(f"REPORT={REPORT_PATH}")
    for error in errors:
        print("ERROR=", error)
    raise SystemExit(1)

print("OK: DA-3C render smoke geçti.")
print(f"REPORT={REPORT_PATH}")
print("DISABLED_STATUS=", disabled_status)
print("ENABLED_STATUS=", enabled_status)
print("EXPECTED_TABLE_COUNT=", len(get_digital_archive_table_names()))
print("SONUC=DA3C_RENDER_SMOKE_OK")
