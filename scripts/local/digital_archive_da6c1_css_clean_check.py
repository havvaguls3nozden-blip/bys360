from pathlib import Path

ROOT = Path.cwd()
index_path = ROOT / "app" / "templates" / "digital_archive" / "index.html"

text = index_path.read_text(encoding="utf-8-sig")

block = """.da6c-security-card {
    border-left: 5px solid var(--bys-red, #8B0000) !important;
}
"""

count = text.count(block)

if count > 1:
    first = text.find(block)
    before = text[: first + len(block)]
    after = text[first + len(block):].replace(block, "")
    text = before + after
    index_path.write_text(text, encoding="utf-8")

text_after = index_path.read_text(encoding="utf-8-sig")

errors = []

if text_after.count(block) != 1:
    errors.append(f"Beklenen tek da6c-security-card CSS bloğu, bulunan: {text_after.count(block)}")

for token in [
    "/digital-archive/security",
    "Güvenlik Durumu",
    "da6c-index-panel",
    "da6c-security-card",
]:
    if token not in text_after:
        errors.append(f"index.html içinde beklenen ifade yok: {token}")

if errors:
    raise SystemExit("DA-6C1 CHECK FAIL:\n" + "\n".join(errors))

print("OK: DA-6C1 CSS tekrar temizliği kontrolü geçti.")
print("SONUC=DA6C1_SECURITY_STATUS_CSS_CLEAN_OK")
