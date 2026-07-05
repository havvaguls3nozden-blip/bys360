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
