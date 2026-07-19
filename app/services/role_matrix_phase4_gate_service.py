from __future__ import annotations


import logging
logger = logging.getLogger(__name__)

"""BYS360 Rol Matrisi Faz 4 kontrol servisi.

Bu servis uygulama davranışını değiştirmez. Veritabanına yazmaz, migration
çalıştırmaz ve canlı rota akışına müdahale etmez. Amacı; Faz 3 ile eklenen
Rol Matrisi UI omurgasının, rol-yetki-menü görünürlüğü ilkeleriyle tutarlı
olup olmadığını güvenli biçimde kontrol etmektir.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from collections.abc import Iterable


REQUIRED_PHASE3_FILES = [
    Path("app/admin/role_matrix_routes.py"),
    Path("app/services/role_matrix_ui_service.py"),
    Path("app/templates/admin/role_matrix_center.html"),
    Path("app/admin/route_manifest.py"),
    Path("app/templates/settings.html"),
]

REQUIRED_MODULE_KEYS = {
    "settings": "Sistem Ayarları ve Yetkilendirme",
    "personnel": "Personel Yönetimi",
    "performance": "Performans Yönetimi",
    "communication": "İletişim, Anket ve Destek",
    "ai": "AI Karar Destek",
    "reporting": "Genel, Bildirim ve Raporlama",
}

REQUIRED_UI_TERMS = [
    "Rol Matrisi",
    "Menü Görünürlüğü",
    "En az yetki",
    "audit log",
]

EXPECTED_CORE_TABLE_TERMS = [
    "user_menu_permissions",
    "role_menu_defaults",
    "unit_menu_profiles",
    "system_settings",
    "module_settings",
    "settings_change_logs",
    "audit_logs",
]

SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "node_modules",
    "backups",
    "backup",
    "release",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

SCAN_EXTENSIONS = {
    ".py",
    ".html",
    ".jinja",
    ".j2",
    ".md",
    ".txt",
    ".sql",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
}


@dataclass
class Phase4GateResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    facts: list[str] = field(default_factory=list)
    module_count: int = 0
    role_row_count: int = 0
    menu_key_count: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def iter_project_files(root: Path) -> Iterable[Path]:
    visited = 0
    for path in root.rglob("*"):
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() not in SCAN_EXTENSIONS:
            continue
        # Büyük binary/rapor kalıntılarını yanlışlıkla okumayalım.
        try:
            if path.stat().st_size > 5_000_000:
                continue
        except OSError:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/role_matrix_phase4_gate_service.py:113)")
            continue
        visited += 1
        if visited > 8000:
            break
        yield path


def _row_value(row: Any, field_name: str) -> Any:
    if isinstance(row, dict):
        return row.get(field_name)
    return getattr(row, field_name, None)


def validate_phase3_files(project_root: Path, result: Phase4GateResult) -> None:
    for rel in REQUIRED_PHASE3_FILES:
        path = project_root / rel
        if not path.exists():
            result.errors.append(f"Faz 3 zorunlu dosyasi eksik: {rel}")

    route_manifest = project_root / "app/admin/route_manifest.py"
    if route_manifest.exists() and "role_matrix_routes" not in read_text(route_manifest):
        result.errors.append("route_manifest.py icinde role_matrix_routes kaydi yok")

    settings_template = project_root / "app/templates/settings.html"
    if settings_template.exists():
        settings_text = read_text(settings_template)
        if "admin_role_matrix_center" not in settings_text or "Rol Matrisi" not in settings_text:
            result.errors.append("settings.html icinde Rol Matrisi baglantisi yok")

    route_file = project_root / "app/admin/role_matrix_routes.py"
    if route_file.exists():
        route_text = read_text(route_file)
        if '@main_bp.route("/admin/role-matrix")' not in route_text:
            result.errors.append("role_matrix_routes.py icinde /admin/role-matrix rotasi yok")
        if "admin_required" not in route_text:
            result.errors.append("Rol Matrisi rotasi admin_required korumasi icermiyor")


def validate_ui_terms(project_root: Path, result: Phase4GateResult) -> None:
    targets = [
        project_root / "app/services/role_matrix_ui_service.py",
        project_root / "app/templates/admin/role_matrix_center.html",
    ]
    for target in targets:
        if not target.exists():
            continue
        text = read_text(target)
        for term in REQUIRED_UI_TERMS:
            if term not in text:
                result.errors.append(f"Zorunlu ifade eksik: {term} -> {target.relative_to(project_root)}")


def validate_module_policies(project_root: Path, result: Phase4GateResult) -> None:
    # check script sys.path'e proje kokunu eklediği için import güvenli yapılabilir.
    try:
        from app.services.role_matrix_ui_service import MODULE_POLICIES  # type: ignore
    except Exception as exc:  # pragma: no cover - gate çıktısında görünür.
        logger.exception("BYS360 V6B guarded exception | file=app/services/role_matrix_phase4_gate_service.py | line=173")
        result.errors.append(f"MODULE_POLICIES okunamadi: {exc}")
        return

    if not isinstance(MODULE_POLICIES, list) or not MODULE_POLICIES:
        result.errors.append("MODULE_POLICIES bos veya liste degil")
        return

    seen_keys: set[str] = set()
    seen_menu_keys: set[str] = set()
    role_row_count = 0

    for module in MODULE_POLICIES:
        if not isinstance(module, dict):
            result.errors.append("MODULE_POLICIES icinde dict olmayan modul kaydi var")
            continue

        key = str(module.get("key", "")).strip()
        title = str(module.get("title", "")).strip()
        description = str(module.get("description", "")).strip()
        menu_keys = module.get("menu_keys") or []
        rows = module.get("rows") or []

        if not key:
            result.errors.append("Bir modul kaydinda key eksik")
            continue
        seen_keys.add(key)

        expected_title = REQUIRED_MODULE_KEYS.get(key)
        if expected_title and expected_title not in title:
            result.errors.append(f"Modul basligi beklenen ifadeyi icermiyor: {key} -> {expected_title}")

        if not title:
            result.errors.append(f"Modul basligi bos: {key}")
        if len(description) < 20:
            result.warnings.append(f"Modul aciklamasi kisa olabilir: {key}")
        if not isinstance(menu_keys, list) or not menu_keys:
            result.errors.append(f"menu_keys eksik veya bos: {key}")
        else:
            for menu_key in menu_keys:
                if not isinstance(menu_key, str) or not menu_key.strip():
                    result.errors.append(f"Gecersiz menu_key: {key}")
                else:
                    seen_menu_keys.add(menu_key.strip())

        if not isinstance(rows, list) or not rows:
            result.errors.append(f"Rol satirlari eksik veya bos: {key}")
            continue

        for row in rows:
            role_row_count += 1
            for field_name in ["role", "visibility", "manage", "report", "approval", "audit"]:
                value = _row_value(row, field_name)
                if value is None or str(value).strip() == "":
                    result.errors.append(f"Rol satirinda {field_name} alani eksik: {key}")

    missing_keys = [key for key in REQUIRED_MODULE_KEYS if key not in seen_keys]
    for key in missing_keys:
        result.errors.append(f"Zorunlu modul politikasi eksik: {key}")

    result.module_count = len(seen_keys)
    result.role_row_count = role_row_count
    result.menu_key_count = len(seen_menu_keys)
    result.facts.append(f"Modul politikasi sayisi: {result.module_count}")
    result.facts.append(f"Rol matrisi satir sayisi: {result.role_row_count}")
    result.facts.append(f"Tekil menu anahtari sayisi: {result.menu_key_count}")


def validate_core_terms(project_root: Path, result: Phase4GateResult) -> None:
    found: dict[str, list[str]] = {term: [] for term in EXPECTED_CORE_TABLE_TERMS}
    for path in iter_project_files(project_root):
        try:
            text = read_text(path)
        except OSError:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/role_matrix_phase4_gate_service.py:244)")
            continue
        for term in EXPECTED_CORE_TABLE_TERMS:
            if term in text:
                found[term].append(str(path.relative_to(project_root)))

    for term, paths in found.items():
        if paths:
            result.facts.append(f"{term}: bulundu ({paths[0]})")
        else:
            result.warnings.append(f"Beklenen cekirdek yapi referansi bulunamadi: {term}")


def validate_docs(project_root: Path, result: Phase4GateResult) -> None:
    docs_root = project_root / "docs/role_matrices"
    if not docs_root.exists():
        result.warnings.append("docs/role_matrices klasoru bulunamadi")
    phase4_doc = docs_root / "PHASE4_GATE.md"
    if not phase4_doc.exists():
        result.errors.append("Faz 4 dokumani eksik: docs/role_matrices/PHASE4_GATE.md")
    else:
        doc_text = read_text(phase4_doc)
        for term in ["Rol Matrisi", "Menü Görünürlüğü", "En az yetki", "audit log"]:
            if term not in doc_text:
                result.errors.append(f"Faz 4 dokumaninda ifade eksik: {term}")


def build_phase4_result(project_root: Path) -> Phase4GateResult:
    result = Phase4GateResult()
    validate_phase3_files(project_root, result)
    validate_ui_terms(project_root, result)
    validate_module_policies(project_root, result)
    validate_docs(project_root, result)
    validate_core_terms(project_root, result)
    return result


def render_markdown_report(result: Phase4GateResult) -> str:
    lines: list[str] = []
    lines.append("# BYS360 Rol Matrisi Faz 4 Gate Raporu")
    lines.append("")
    lines.append("## Sonuç")
    lines.append("")
    lines.append(f"- HATA: {len(result.errors)}")
    lines.append(f"- UYARI: {len(result.warnings)}")
    lines.append(f"- Modül politikası: {result.module_count}")
    lines.append(f"- Rol matrisi satırı: {result.role_row_count}")
    lines.append(f"- Menü anahtarı: {result.menu_key_count}")
    lines.append("")
    lines.append("## Kontrol Kapsamı")
    lines.append("")
    lines.append("- Faz 3 Rol Matrisi UI dosyaları")
    lines.append("- /admin/role-matrix rota kaydı")
    lines.append("- Ayarlar ekranı Rol Matrisi bağlantısı")
    lines.append("- Modül bazlı rol politikaları")
    lines.append("- Menü Görünürlüğü ilkeleri")
    lines.append("- En az yetki yaklaşımı")
    lines.append("- audit log vurgusu")
    lines.append("- Çekirdek yetki/ayar tablo referansları")
    lines.append("")

    if result.errors:
        lines.append("## Hatalar")
        lines.append("")
        for error in result.errors:
            lines.append(f"- {error}")
        lines.append("")

    if result.warnings:
        lines.append("## Uyarılar")
        lines.append("")
        for warning in result.warnings:
            lines.append(f"- {warning}")
        lines.append("")

    if result.facts:
        lines.append("## Bulgular")
        lines.append("")
        for fact in result.facts:
            lines.append(f"- {fact}")
        lines.append("")

    lines.append("## Not")
    lines.append("")
    lines.append("Faz 4 gate, canlı davranışı değiştirmez. Veritabanına yazmaz; yalnızca mevcut rol matrisi, menü görünürlüğü ve yetki omurgasını denetler.")
    lines.append("")
    return "\n".join(lines)
