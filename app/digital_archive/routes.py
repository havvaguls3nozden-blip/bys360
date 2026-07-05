"""Dijital Arşiv route iskeleti.

DA-1B:
- Blueprint ana uygulama route bootstrap akışına bağlanabilir.
- Modül varsayılan kapalıdır.
- Kullanıcı login olmadan iç modül ekranına erişemez.
- Gerçek belge işlemleri DA-2 sonrasına bırakılmıştır.
"""

from flask import Blueprint, current_app, render_template
from flask_login import login_required
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import db

from .permissions import is_digital_archive_enabled
from .model_contract import get_digital_archive_table_names

digital_archive_bp = Blueprint(
    "digital_archive",
    __name__,
    url_prefix="/digital-archive",
)


def _digital_archive_config_enabled() -> bool:
    """Config üzerinden geçici modül açık/kapalı durumunu okur.

    DA-1B'de DB ayarı okunmaz. Varsayılan kapalıdır.
    DA-2/DA-3 aşamasında module_settings entegrasyonu eklenecektir.
    """
    value = current_app.config.get("DIGITAL_ARCHIVE_ENABLED", False)
    return is_digital_archive_enabled(value)

# DA-3B: Dijital Arşiv Yönetim Merkezi pasif dashboard yardımcıları
_DIGITAL_ARCHIVE_TABLE_LABELS = {
    "digital_archive_access_rules": "Erişim Kuralları",
    "digital_archive_audit_events": "Denetim Kayıtları",
    "digital_archive_categories": "Arşiv Kategorileri",
    "digital_archive_document_versions": "Belge Versiyonları",
    "digital_archive_documents": "Belgeler",
    "digital_archive_entity_links": "Bağlı Kayıtlar",
    "digital_archive_ocr_jobs": "OCR İşleri",
    "digital_archive_physical_locations": "Fiziksel Konumlar",
    "digital_archive_retention_policies": "Saklama Politikaları",
}


def _safe_table_count(table_name: str) -> int | None:
    """Dijital Arşiv dashboard için salt-okunur tablo sayımı yapar."""
    allowed_tables = set(get_digital_archive_table_names())
    if table_name not in allowed_tables:
        return None

    try:
        query = text(f'SELECT COUNT(*) FROM "{table_name}"')
        value = db.session.execute(query).scalar_one()
        return int(value)
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.warning(
            "Dijital Arşiv dashboard tablo sayımı okunamadı: %s",
            table_name,
            exc_info=True,
        )
        return None


def _digital_archive_dashboard_context() -> dict:
    """Yönetim Merkezi için pasif dashboard verisini hazırlar."""
    table_cards = []
    ready_count = 0

    for table_name in sorted(get_digital_archive_table_names()):
        count = _safe_table_count(table_name)
        is_ready = count is not None
        if is_ready:
            ready_count += 1

        table_cards.append(
            {
                "name": table_name,
                "label": _DIGITAL_ARCHIVE_TABLE_LABELS.get(table_name, table_name),
                "count": count,
                "is_ready": is_ready,
            }
        )

    summary = {
        "table_count": len(table_cards),
        "ready_table_count": ready_count,
        "document_count": _safe_table_count("digital_archive_documents") or 0,
        "category_count": _safe_table_count("digital_archive_categories") or 0,
        "location_count": _safe_table_count("digital_archive_physical_locations") or 0,
        "retention_policy_count": _safe_table_count("digital_archive_retention_policies") or 0,
    }

    return {
        "page_title": "Dijital Arşiv Yönetim Merkezi",
        "module_status": "Pasif güvenli ekran",
        "summary": summary,
        "table_cards": table_cards,
    }



@digital_archive_bp.get("/")
@login_required
def index():
    """Dijital Arşiv ana giriş ekranı."""
    if not _digital_archive_config_enabled():
        return render_template("digital_archive/disabled.html")

    dashboard_context = _digital_archive_dashboard_context()
    return render_template("digital_archive/index.html", **dashboard_context)

# DA-4B: Dijital Arşiv pasif liste ekranları
_DIGITAL_ARCHIVE_PASSIVE_LIST_SPECS = {
    "categories": {
        "table": "digital_archive_categories",
        "title": "Arşiv Kategorileri",
        "subtitle": "Belgelerin kurumsal arşiv sınıflandırmasına göre izlenmesi için pasif liste ekranı.",
        "preferred_columns": ["id", "code", "name", "title", "description", "is_active", "created_at", "updated_at"],
    },
    "physical_locations": {
        "table": "digital_archive_physical_locations",
        "title": "Fiziksel Konumlar",
        "subtitle": "Depo, raf, kutu ve fiziksel arşiv yerleşim bilgisinin pasif izleme ekranı.",
        "preferred_columns": ["id", "name", "code", "building", "room", "shelf", "box", "is_active", "created_at"],
    },
    "retention_policies": {
        "table": "digital_archive_retention_policies",
        "title": "Saklama Politikaları",
        "subtitle": "Belge saklama süresi, imha/transfer kuralı ve arşiv mevzuatı hazırlığı için pasif liste ekranı.",
        "preferred_columns": ["id", "name", "code", "retention_years", "action", "description", "is_active", "created_at"],
    },
}


def _display_columns_for_table(table_name: str, preferred_columns: list[str]) -> list[str]:
    table = db.metadata.tables.get(table_name)
    if table is None:
        return []

    available_columns = [column.name for column in table.columns]
    selected_columns = [column for column in preferred_columns if column in available_columns]

    if "id" in available_columns and "id" not in selected_columns:
        selected_columns.insert(0, "id")

    return (selected_columns or available_columns[:8])[:8]


def _safe_table_rows(table_name: str, columns: list[str], limit: int = 50) -> tuple[list[dict], str | None]:
    allowed_tables = {spec["table"] for spec in _DIGITAL_ARCHIVE_PASSIVE_LIST_SPECS.values()}

    if table_name not in allowed_tables:
        return [], "Tablo pasif liste whitelist içinde değil."

    table = db.metadata.tables.get(table_name)
    if table is None:
        return [], "Tablo metadata içinde bulunamadı."

    available_columns = {column.name for column in table.columns}
    safe_columns = [column for column in columns if column in available_columns]

    if not safe_columns:
        return [], "Görüntülenecek güvenli kolon bulunamadı."

    quoted_columns = ", ".join(f'"{column}"' for column in safe_columns)
    order_column = "id" if "id" in available_columns else safe_columns[0]

    try:
        query = text(
            f'SELECT {quoted_columns} FROM "{table_name}" '
            f'ORDER BY "{order_column}" DESC LIMIT :limit'
        )
        rows = db.session.execute(query, {"limit": limit}).mappings().all()
        return [dict(row) for row in rows], None
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.warning(
            "Dijital Arşiv pasif liste okunamadı: %s",
            table_name,
            exc_info=True,
        )
        return [], "Liste verisi okunamadı."


def _digital_archive_passive_list_context(list_key: str) -> dict:
    spec = _DIGITAL_ARCHIVE_PASSIVE_LIST_SPECS[list_key]
    table_name = spec["table"]
    columns = _display_columns_for_table(table_name, spec["preferred_columns"])
    rows, error_message = _safe_table_rows(table_name, columns)

    return {
        "page_title": spec["title"],
        "page_subtitle": spec["subtitle"],
        "table_name": table_name,
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "error_message": error_message,
        "module_status": "Pasif liste ekranı",
        "back_url": "/digital-archive/",
    }


@digital_archive_bp.get("/categories")
@login_required
def categories():
    if not _digital_archive_config_enabled():
        return render_template("digital_archive/disabled.html")

    context = _digital_archive_passive_list_context("categories")
    return render_template("digital_archive/passive_list.html", **context)


@digital_archive_bp.get("/physical-locations")
@login_required
def physical_locations():
    if not _digital_archive_config_enabled():
        return render_template("digital_archive/disabled.html")

    context = _digital_archive_passive_list_context("physical_locations")
    return render_template("digital_archive/passive_list.html", **context)


@digital_archive_bp.get("/retention-policies")
@login_required
def retention_policies():
    if not _digital_archive_config_enabled():
        return render_template("digital_archive/disabled.html")

    context = _digital_archive_passive_list_context("retention_policies")
    return render_template("digital_archive/passive_list.html", **context)

