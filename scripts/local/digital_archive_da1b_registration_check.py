from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parents[2]
ROUTE_BOOTSTRAP = ROOT / "app" / "bootstrap" / "route_bootstrap.py"
MODULE_DIR = ROOT / "app" / "digital_archive"
ROUTES = MODULE_DIR / "routes.py"

required_files = [
    ROUTE_BOOTSTRAP,
    MODULE_DIR / "__init__.py",
    ROUTES,
    MODULE_DIR / "permissions.py",
    MODULE_DIR / "services.py",
    MODULE_DIR / "models.py",
    MODULE_DIR / "forms.py",
    MODULE_DIR / "audit.py",
]

missing = [str(path) for path in required_files if not path.exists()]
if missing:
    raise SystemExit("Eksik DA-1B dosyaları:\n" + "\n".join(missing))

for py_file in [ROUTE_BOOTSTRAP, *MODULE_DIR.glob("*.py")]:
    py_compile.compile(str(py_file), doraise=True)

bootstrap_text = ROUTE_BOOTSTRAP.read_text(encoding="utf-8")
required_tokens = [
    'key="digital_archive"',
    'module_path="app.digital_archive.routes"',
    'attribute_name="digital_archive_bp"',
    "BYS360_DA1B_DIGITAL_ARCHIVE_ROUTE_BOOTSTRAP",
]
for token in required_tokens:
    if token not in bootstrap_text:
        raise SystemExit(f"route_bootstrap.py içinde beklenen kayıt yok: {token}")

routes_text = ROUTES.read_text(encoding="utf-8")
for token in [
    'url_prefix="/digital-archive"',
    "@login_required",
    "DIGITAL_ARCHIVE_ENABLED",
    "is_digital_archive_enabled",
]:
    if token not in routes_text:
        raise SystemExit(f"routes.py içinde beklenen DA-1B token yok: {token}")

forbidden_hits = []
for py_file in MODULE_DIR.glob("*.py"):
    text = py_file.read_text(encoding="utf-8")
    for forbidden in ("except Exception", "except:", "bare except"):
        if forbidden in text:
            forbidden_hits.append(f"{py_file}: {forbidden}")

if forbidden_hits:
    raise SystemExit("Dijital Arşiv modülünde yasaklı geniş except bulundu:\n" + "\n".join(forbidden_hits))

print("OK: DA-1B Dijital Arşiv route bootstrap sözleşmesi geçti.")
print(f"ROUTE_BOOTSTRAP={ROUTE_BOOTSTRAP}")
print(f"MODULE_DIR={MODULE_DIR}")
