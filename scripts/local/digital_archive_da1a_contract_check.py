from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parents[2]
MODULE_DIR = ROOT / "app" / "digital_archive"
TEMPLATE_DIR = ROOT / "app" / "templates" / "digital_archive"

REQUIRED_FILES = [
    MODULE_DIR / "__init__.py",
    MODULE_DIR / "routes.py",
    MODULE_DIR / "permissions.py",
    MODULE_DIR / "services.py",
    MODULE_DIR / "models.py",
    MODULE_DIR / "forms.py",
    MODULE_DIR / "audit.py",
    TEMPLATE_DIR / "disabled.html",
]

missing = [str(path) for path in REQUIRED_FILES if not path.exists()]
if missing:
    raise SystemExit("Eksik DA-1A dosyaları:\n" + "\n".join(missing))

for py_file in MODULE_DIR.glob("*.py"):
    py_compile.compile(str(py_file), doraise=True)

forbidden_hits = []
for py_file in MODULE_DIR.glob("*.py"):
    text = py_file.read_text(encoding="utf-8")
    for forbidden in ("except Exception", "except:", "bare except"):
        if forbidden in text:
            forbidden_hits.append(f"{py_file}: {forbidden}")

if forbidden_hits:
    raise SystemExit("DA-1A modülünde yasaklı geniş except bulundu:\n" + "\n".join(forbidden_hits))

routes_text = (MODULE_DIR / "routes.py").read_text(encoding="utf-8")
if 'url_prefix="/digital-archive"' not in routes_text:
    raise SystemExit("digital_archive route prefix bulunamadı.")

permissions_text = (MODULE_DIR / "permissions.py").read_text(encoding="utf-8")
if "digital_archive_enabled" not in permissions_text:
    raise SystemExit("digital_archive_enabled ayar anahtarı bulunamadı.")

print("OK: DA-1A Dijital Arşiv pasif modül iskeleti kontrolü geçti.")
print(f"MODULE_DIR={MODULE_DIR}")
print(f"TEMPLATE_DIR={TEMPLATE_DIR}")
