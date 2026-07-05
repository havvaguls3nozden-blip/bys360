
from pathlib import Path

ROOT = Path.cwd()
INDEX_TEMPLATE = ROOT / "app" / "templates" / "digital_archive" / "index.html"
PASSIVE_TEMPLATE = ROOT / "app" / "templates" / "digital_archive" / "passive_list.html"

errors = []

index_text = INDEX_TEMPLATE.read_text(encoding="utf-8-sig")
passive_text = PASSIVE_TEMPLATE.read_text(encoding="utf-8-sig")

for token in [
    "DA-4C BYS360 brand alignment",
    "var(--bys-red",
    "var(--bys-red-soft",
    "var(--bys-text",
    "var(--bys-muted",
]:
    if token not in index_text:
        errors.append(f"index.html içinde BYS360 marka tokenı yok: {token}")

for token in [
    "DA-4C BYS360 passive list brand alignment",
    "var(--bys-red",
    "var(--bys-red-soft",
    "var(--bys-text",
    "var(--bys-muted",
]:
    if token not in passive_text:
        errors.append(f"passive_list.html içinde BYS360 marka tokenı yok: {token}")

for forbidden in [
    "rgba(30, 64, 175",
    "#1d4ed8",
    "#eff6ff",
]:
    if forbidden in index_text:
        errors.append(f"index.html içinde mavi tasarım izi kaldı: {forbidden}")
    if forbidden in passive_text:
        errors.append(f"passive_list.html içinde mavi tasarım izi kaldı: {forbidden}")

if errors:
    raise SystemExit("DA-4C BRAND CHECK FAIL:\n" + "\n".join(errors))

print("OK: DA-4C BYS360 marka renk uyumu kontrolü geçti.")
print("SONUC=DA4C_BYS360_BRAND_ALIGNMENT_OK")
