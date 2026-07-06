import os
"""Dijital Arşiv route iskeleti.

DA-1B:
- Blueprint ana uygulama route bootstrap akışına bağlanabilir.
- Modül varsayılan kapalıdır.
- Kullanıcı login olmadan iç modül ekranına erişemez.
- Gerçek belge işlemleri DA-2 sonrasına bırakılmıştır.
"""

from flask import Blueprint, current_app, render_template
from flask_login import login_required
from flask import flash, redirect, request
from app.digital_archive.models import DigitalArchiveCategory
from app.digital_archive.write_service import build_digital_archive_write_intent
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.digital_archive.security_contract import (
    digital_archive_write_is_enabled,
    get_digital_archive_field_whitelist,
    get_digital_archive_write_operations,
    get_digital_archive_write_security_requirements,
)

from .permissions import is_digital_archive_enabled
from .model_contract import get_digital_archive_table_names

digital_archive_bp = Blueprint(
    "digital_archive",
    __name__,
    url_prefix="/digital-archive",
)


def _digital_archive_config_enabled() -> bool:
    """Dijital Arşiv UI erişim kapısı.

    Local önizleme için env değişkenleri desteklenir.
    DB yazma bu helper ile açılmaz; sadece GET ekranlarının disabled.html'e düşmesini engeller.
    """
    import os

    truthy_values = {"1", "true", "yes", "on", "enabled", "preview", "local"}

    for env_key in (
        "DIGITAL_ARCHIVE_ENABLED",
        "BYS360_DIGITAL_ARCHIVE_ENABLED",
        "BYS360_DIGITAL_ARCHIVE_LOCAL_UI_PREVIEW",
    ):
        env_value = str(os.environ.get(env_key, "")).strip().lower()
        if env_value in truthy_values:
            return True

    try:
        from flask import current_app

        config_value = current_app.config.get("DIGITAL_ARCHIVE_ENABLED")
        if isinstance(config_value, str):
            return config_value.strip().lower() in truthy_values

        return bool(config_value)
    except Exception:
        return False


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
        "module_status": "Dijital Arşiv Merkezi",
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
        "subtitle": "Belgelerin kurumsal arşiv sınıflandırmasına göre düzenli şekilde takip edildiği bölüm.",
        "preferred_columns": ["id", "code", "name", "title", "description", "is_active", "created_at", "updated_at"],
        "new_route": "/digital-archive/categories/new",
    },
    "physical_locations": {
        "table": "digital_archive_physical_locations",
        "title": "Fiziksel Konumlar",
        "subtitle": "Depo, raf, kutu ve fiziksel arşiv yerleşim bilgisinin pasif izleme ekranı.",
        "preferred_columns": ["id", "name", "code", "building", "room", "shelf", "box", "is_active", "created_at"],
        "new_route": "/digital-archive/physical-locations/new",
    },
    "retention_policies": {
        "table": "digital_archive_retention_policies",
        "title": "Saklama Süreleri",
        "subtitle": "Belge saklama süresi, imha/transfer kuralı ve arşiv mevzuatı hazırlığı için pasif liste ekranı.",
        "preferred_columns": ["id", "name", "code", "retention_years", "action", "description", "is_active", "created_at"],
        "new_route": "/digital-archive/retention-policies/new",
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
        "module_status": "Kayıt Listesi",
        "back_url": "/digital-archive/",
        "draft_form_url": spec.get("new_route"),
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

# DA-5B: Dijital Arşiv GET-only taslak form ekranları
_DIGITAL_ARCHIVE_FORM_EXCLUDED_FIELDS = {
    "id",
    "created_at",
    "updated_at",
    "deleted_at",
    "created_by_id",
    "updated_by_id",
    "deleted_by_id",
    "is_deleted",
}


def _field_input_type(column) -> str:
    column_type = column.type.__class__.__name__.lower()

    if "bool" in column_type:
        return "checkbox"
    if "integer" in column_type or "numeric" in column_type or "float" in column_type or "decimal" in column_type:
        return "number"
    if "date" in column_type:
        return "date"
    if "text" in column_type:
        return "textarea"

    return "text"


def _digital_archive_passive_form_context(list_key: str) -> dict:
    """GET-only taslak form context'i üretir; DB yazma işlemi yapmaz."""
    spec = _DIGITAL_ARCHIVE_PASSIVE_LIST_SPECS[list_key]
    table_name = spec["table"]
    table = db.metadata.tables.get(table_name)

    fields = []
    if table is not None:
        for column in table.columns:
            if column.name in _DIGITAL_ARCHIVE_FORM_EXCLUDED_FIELDS:
                continue

            fields.append(
                {
                    "name": column.name,
                    "label": column.name.replace("_", " ").title(),
                    "type": _field_input_type(column),
                    "required": (
                        not column.nullable
                        and column.default is None
                        and column.server_default is None
                    ),
                    "nullable": column.nullable,
                    "readonly_note": "Taslak alan - veri yazma kapalı",
                }
            )

    return {
        "page_title": f"{spec['title']} Taslak Formu",
        "page_subtitle": "Bu ekran yalnızca form taslağını gösterir. Kayıt işlemi henüz açılmamıştır.",
        "module_status": "GET-only taslak form",
        "table_name": table_name,
        "fields": fields,
        "field_count": len(fields),
        "list_url": spec.get("route", "/digital-archive/"),
        "back_url": "/digital-archive/",
    }


@digital_archive_bp.get("/categories/new")
@login_required
def category_draft_form():
    if not _digital_archive_config_enabled():
        return render_template("digital_archive/disabled.html")

    context = _digital_archive_passive_form_context("categories")
    return render_template("digital_archive/passive_form.html", **context)


@digital_archive_bp.get("/physical-locations/new")
@login_required
def physical_location_draft_form():
    if not _digital_archive_config_enabled():
        return render_template("digital_archive/disabled.html")

    context = _digital_archive_passive_form_context("physical_locations")
    return render_template("digital_archive/passive_form.html", **context)


@digital_archive_bp.get("/retention-policies/new")
@login_required
def retention_policy_draft_form():
    if not _digital_archive_config_enabled():
        return render_template("digital_archive/disabled.html")

    context = _digital_archive_passive_form_context("retention_policies")
    return render_template("digital_archive/passive_form.html", **context)



@digital_archive_bp.route("/retention-policies", methods=["POST"])
@login_required
def retention_policy_create_post():
    """Saklama süresi kaydı oluşturur."""
    from datetime import datetime

    from flask import current_app, flash, redirect, request
    from sqlalchemy import MetaData, Table

    from app import db

    metadata = MetaData()
    table = Table("digital_archive_retention_policies", metadata, autoload_with=db.engine)

    form_data = request.form.to_dict(flat=True)
    now = datetime.now()
    payload = {}

    def varsayilan_deger(column):
        name = column.name
        lower_name = name.lower()
        lower_type = str(column.type).lower()

        if name in {"created_at", "updated_at"}:
            return now

        if "bool" in lower_type:
            return True if name == "is_active" else False

        if "int" in lower_type:
            if lower_name in {"retention_years", "retention_period", "duration_years", "year_count"}:
                return 5
            if lower_name.endswith("_id"):
                return None
            return 0

        if "date" in lower_type or "time" in lower_type:
            return None

        if lower_name in {"code", "policy_code"}:
            return "SK-" + now.strftime("%Y%m%d%H%M%S")
        if lower_name in {"name", "title", "document_type", "policy_name"}:
            return "Genel Saklama Süresi"
        if lower_name in {"action", "disposal_action", "final_action"}:
            return "Süre sonunda değerlendir"
        if lower_name in {"description", "notes"}:
            return "Arşiv belgeleri için saklama süresi kaydı."
        if lower_name in {"legal_basis", "basis"}:
            return "Kurum arşiv düzeni"

        return None

    for column in table.columns:
        name = column.name

        if name in {"id", "deleted_at"}:
            continue

        raw_value = str(form_data.get(name, "")).strip()

        if not raw_value:
            value = varsayilan_deger(column)
            if value is not None:
                payload[name] = value
            continue

        lower_type = str(column.type).lower()

        if "int" in lower_type:
            try:
                payload[name] = int(raw_value)
            except ValueError:
                flash("Sayısal alanlar yalnızca rakam içermelidir.", "warning")
                return redirect("/digital-archive/retention-policies/new")
        elif "bool" in lower_type:
            payload[name] = raw_value.lower() in {"1", "true", "on", "yes", "evet", "aktif"}
        elif "date" in lower_type or "time" in lower_type:
            parsed_value = None
            for pattern in ("%Y-%m-%d", "%d.%m.%Y", "%Y-%m-%dT%H:%M"):
                try:
                    parsed_value = datetime.strptime(raw_value, pattern)
                    break
                except ValueError:
                    continue
            payload[name] = parsed_value
        else:
            payload[name] = raw_value

    for column in table.columns:
        name = column.name

        if name in {"id", "deleted_at"} or name in payload:
            continue

        nullable = getattr(column, "nullable", True)
        has_default = column.default is not None or column.server_default is not None

        if not nullable and not has_default:
            value = varsayilan_deger(column)
            if value is not None:
                payload[name] = value

    meaningful_payload = {
        key: value
        for key, value in payload.items()
        if key not in {"created_at", "updated_at", "is_active"} and value not in (None, "")
    }

    if not meaningful_payload:
        flash("Saklama süresi bilgisi girilmelidir.", "warning")
        return redirect("/digital-archive/retention-policies/new")

    try:
        db.session.execute(table.insert().values(**payload))
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Saklama süresi kaydı oluşturulamadı.")
        flash("Kayıt oluşturulurken beklenmeyen bir sorun oluştu.", "danger")
        return redirect("/digital-archive/retention-policies/new")

    flash("Saklama süresi kaydedildi.", "success")
    return redirect("/digital-archive/retention-policies")



# DA-23B: Belge local kayıt ekranları
def _da23_table_exists(table_name: str) -> bool:
    from sqlalchemy import inspect

    return table_name in inspect(db.engine).get_table_names()


def _da23_document_table():
    from sqlalchemy import MetaData, Table

    table_name = "digital_archive_documents"
    if not _da23_table_exists(table_name):
        raise RuntimeError("Belge tablosu bulunamadı.")

    metadata = MetaData()
    return Table(table_name, metadata, autoload_with=db.engine)


def _da23_column_label(column_name: str) -> str:
    labels = {
        "id": "No",
        "code": "Kod",
        "document_code": "Belge Kodu",
        "document_no": "Belge Sayısı",
        "document_number": "Belge Sayısı",
        "reference_no": "Referans No",
        "registry_no": "Kayıt No",
        "name": "Belge Adı",
        "title": "Belge Adı",
        "document_title": "Belge Adı",
        "subject": "Konu",
        "document_type": "Belge Türü",
        "type": "Belge Türü",
        "document_date": "Belge Tarihi",
        "date": "Belge Tarihi",
        "category_id": "Kategori",
        "physical_location_id": "Fiziksel Konum",
        "location_id": "Fiziksel Konum",
        "retention_policy_id": "Saklama Süresi",
        "retention_id": "Saklama Süresi",
        "status": "Belge Durumu",
        "status_label": "Belge Durumu",
        "confidentiality_level": "Gizlilik Düzeyi",
        "access_level": "Erişim Düzeyi",
        "description": "Açıklama",
        "notes": "Notlar",
        "is_active": "Durum",
        "created_at": "Oluşturma Tarihi",
        "updated_at": "Güncelleme Tarihi",
    }
    return labels.get(column_name, column_name.replace("_", " ").title())


def _da23_input_type(column) -> str:
    column_name = column.name.lower()
    column_type = str(column.type).lower()

    if "date" in column_name or "date" in column_type:
        return "date"

    if "time" in column_type:
        return "datetime-local"

    if "int" in column_type:
        return "number"

    if column_name in {"description", "notes", "subject"}:
        return "textarea"

    return "text"


def _da23_latest_id(table_name: str):
    from sqlalchemy import text

    if not _da23_table_exists(table_name):
        return None

    return db.session.execute(text(f"SELECT id FROM {table_name} ORDER BY id DESC LIMIT 1")).scalar_one_or_none()


def _da23_options_for(column_name: str) -> list[dict]:
    from sqlalchemy import inspect, text

    mapping = {
        "category_id": ("digital_archive_categories", ["name", "title", "code"]),
        "physical_location_id": ("digital_archive_physical_locations", ["archive_room", "cabinet_no", "box_no"]),
        "location_id": ("digital_archive_physical_locations", ["archive_room", "cabinet_no", "box_no"]),
        "retention_policy_id": ("digital_archive_retention_policies", ["name", "title", "action"]),
        "retention_id": ("digital_archive_retention_policies", ["name", "title", "action"]),
    }

    if column_name not in mapping:
        return []

    table_name, preferred_labels = mapping[column_name]
    if not _da23_table_exists(table_name):
        return []

    inspector = inspect(db.engine)
    columns = [column["name"] for column in inspector.get_columns(table_name)]

    label_column = next((item for item in preferred_labels if item in columns), "id")

    rows = db.session.execute(
        text(f"SELECT id, {label_column} AS label FROM {table_name} ORDER BY id DESC LIMIT 100")
    ).mappings().all()

    return [{"value": row["id"], "label": row["label"] or f"Kayıt {row['id']}"} for row in rows]


def _da23_document_fields() -> list[dict]:
    excluded = {
        "id",
        "created_at",
        "updated_at",
        "deleted_at",
        "created_by_id",
        "updated_by_id",
        "deleted_by_id",
        "file_path",
        "file_size",
        "mime_type",
        "original_filename",
        "stored_filename",
        "ocr_text",
        "search_text",
    }

    table = _da23_document_table()
    fields = []

    for column in table.columns:
        if column.name in excluded:
            continue

        options = _da23_options_for(column.name)

        fields.append(
            {
                "name": column.name,
                "label": _da23_column_label(column.name),
                "input_type": "select" if options else _da23_input_type(column),
                "options": options,
                "required": not bool(column.nullable) and column.default is None and column.server_default is None,
            }
        )

    return fields


def _da23_document_payload(form_data: dict):
    from datetime import datetime

    table = _da23_document_table()
    now = datetime.now()
    payload = {}

    def default_for(column):
        name = column.name
        lower_name = name.lower()
        lower_type = str(column.type).lower()

        if name in {"created_at", "updated_at"}:
            return now

        if "bool" in lower_type:
            return True if name == "is_active" else False

        if lower_name in {"category_id"}:
            return _da23_latest_id("digital_archive_categories")

        if lower_name in {"physical_location_id", "location_id"}:
            return _da23_latest_id("digital_archive_physical_locations")

        if lower_name in {"retention_policy_id", "retention_id"}:
            return _da23_latest_id("digital_archive_retention_policies")

        if "int" in lower_type:
            if lower_name.endswith("_id"):
                return None
            return 0

        if "date" in lower_type or "time" in lower_type:
            return now if not lower_name.endswith("_date") else None

        if lower_name in {"code", "document_code"}:
            return "BLG-" + now.strftime("%Y%m%d%H%M%S")

        if lower_name in {"document_no", "document_number", "reference_no", "registry_no"}:
            return now.strftime("%Y/%m/%d-%H%M%S")

        if lower_name in {"name", "title", "document_title"}:
            return "Taranmış Arşiv Belgesi"

        if lower_name in {"subject"}:
            return "Fiziksel arşivden dijital arşive aktarılacak belge"

        if lower_name in {"document_type", "type"}:
            return "Taranmış Belge"

        if lower_name in {"status"}:
            return "Hazırlanıyor"

        if lower_name in {"confidentiality_level", "access_level"}:
            return "Kurum İçi"

        if lower_name in {"description", "notes"}:
            return "Belge local geliştirme kaydı."

        return None

    for column in table.columns:
        name = column.name

        if name in {"id", "deleted_at"}:
            continue

        raw_value = str(form_data.get(name, "")).strip()

        if not raw_value:
            value = default_for(column)
            if value is not None:
                payload[name] = value
            continue

        lower_type = str(column.type).lower()

        if "int" in lower_type:
            try:
                payload[name] = int(raw_value)
            except ValueError:
                raise ValueError(f"{_da23_column_label(name)} sayısal olmalıdır.")
        elif "bool" in lower_type:
            payload[name] = raw_value.lower() in {"1", "true", "on", "yes", "evet", "aktif"}
        elif "date" in lower_type or "time" in lower_type:
            parsed_value = None
            for pattern in ("%Y-%m-%d", "%d.%m.%Y", "%Y-%m-%dT%H:%M"):
                try:
                    parsed_value = datetime.strptime(raw_value, pattern)
                    break
                except ValueError:
                    continue
            payload[name] = parsed_value
        else:
            payload[name] = raw_value

    for column in table.columns:
        name = column.name

        if name in {"id", "deleted_at"} or name in payload:
            continue

        nullable = getattr(column, "nullable", True)
        has_default = column.default is not None or column.server_default is not None

        if not nullable and not has_default:
            value = default_for(column)
            if value is not None:
                payload[name] = value

    return payload


@digital_archive_bp.get("/documents")
@login_required
def documents():
    """Belgeler arama ve filtreleme ekranı."""
    from datetime import datetime

    from flask import request
    from sqlalchemy import String, cast, desc, or_, select

    try:
        table = _da23_document_table()
        available_columns = [column.name for column in table.columns]

        q = request.args.get("q", "").strip()
        category_id = request.args.get("category_id", "").strip()
        physical_location_id = request.args.get("physical_location_id", "").strip()
        retention_policy_id = request.args.get("retention_policy_id", "").strip()
        status = request.args.get("status", "").strip()
        document_type = request.args.get("document_type", "").strip()
        date_from = request.args.get("date_from", "").strip()
        date_to = request.args.get("date_to", "").strip()

        conditions = []

        if q:
            text_conditions = []

            text_columns = [
                column.name
                for column in table.columns
                if any(token in str(column.type).lower() for token in ("char", "text", "varchar", "string"))
            ]

            if text_columns:
                text_conditions.append(
                    or_(*[
                        cast(table.c[column], String).ilike(f"%{q}%")
                        for column in text_columns
                    ])
                )

            if "id" in table.c:
                readable_text_document_ids = _da27_document_ids_for_text(q)
                if readable_text_document_ids:
                    text_conditions.append(table.c.id.in_(readable_text_document_ids))

            metadata_document_ids = _da29_document_ids_for_metadata(q)
            if metadata_document_ids:
                text_conditions.append(table.c.id.in_(metadata_document_ids))

            if text_conditions:
                conditions.append(or_(*text_conditions))

        exact_filters = {
            "category_id": category_id,
            "physical_location_id": physical_location_id,
            "retention_policy_id": retention_policy_id,
            "status": status,
            "document_type": document_type,
        }

        for column_name, value in exact_filters.items():
            if value and column_name in table.c:
                conditions.append(table.c[column_name] == value)

        if "document_date" in table.c:
            if date_from:
                try:
                    parsed_from = datetime.strptime(date_from, "%Y-%m-%d").date()
                    conditions.append(table.c.document_date >= parsed_from)
                except ValueError:
                    flash("Başlangıç tarihi uygun formatta değil.", "warning")

            if date_to:
                try:
                    parsed_to = datetime.strptime(date_to, "%Y-%m-%d").date()
                    conditions.append(table.c.document_date <= parsed_to)
                except ValueError:
                    flash("Bitiş tarihi uygun formatta değil.", "warning")

        query = select(table)

        if conditions:
            query = query.where(*conditions)

        if "id" in table.c:
            query = query.order_by(desc(table.c.id))

        query = query.limit(200)

        rows = [dict(row._mapping) for row in db.session.execute(query).all()]

        preferred_columns = [
            "id",
            "document_no",
            "title",
            "document_type",
            "document_date",
            "subject",
            "category_id",
            "physical_location_id",
            "retention_policy_id",
            "status",
            "created_at",
        ]

        display_columns = [column for column in preferred_columns if column in available_columns][:10]
        if not display_columns:
            display_columns = available_columns[:10]

        filter_options = {
            "category_id": _da23_options_for("category_id"),
            "physical_location_id": _da23_options_for("physical_location_id"),
            "retention_policy_id": _da23_options_for("retention_policy_id"),
            "status": [],
            "document_type": [],
        }

        if "status" in table.c:
            status_rows = db.session.execute(
                select(table.c.status).where(table.c.status.is_not(None)).distinct().order_by(table.c.status).limit(100)
            ).all()
            filter_options["status"] = [
                {"value": row[0], "label": row[0]}
                for row in status_rows
                if row[0]
            ]

        if "document_type" in table.c:
            type_rows = db.session.execute(
                select(table.c.document_type).where(table.c.document_type.is_not(None)).distinct().order_by(table.c.document_type).limit(100)
            ).all()
            filter_options["document_type"] = [
                {"value": row[0], "label": row[0]}
                for row in type_rows
                if row[0]
            ]

        filter_values = {
            "q": q,
            "category_id": category_id,
            "physical_location_id": physical_location_id,
            "retention_policy_id": retention_policy_id,
            "status": status,
            "document_type": document_type,
            "date_from": date_from,
            "date_to": date_to,
        }

        rows = [_da36b_enrich_document_row(row) for row in rows]
        status_summary = _da36b_status_summary(rows)

        return render_template(
            "digital_archive/document_list.html",
            title="Belgeler",
            subtitle="Fiziksel arşivden dijital arşive aktarılacak belgeler bu bölümde aranır ve filtrelenir.",
            rows=rows,
            display_columns=display_columns,
            column_labels={column: _da23_column_label(column) for column in display_columns},
            row_count=len(rows),
            filter_values=filter_values,
            filter_options=filter_options,
            status_summary=status_summary,
        )
    except Exception:
        current_app.logger.exception("Belgeler listelenemedi.")
        flash("Belgeler açılırken beklenmeyen bir sorun oluştu.", "danger")
        return redirect("/digital-archive/")


@digital_archive_bp.get("/documents/new")
@login_required
def document_new():
    """Yeni belge formu."""
    try:
        return render_template(
            "digital_archive/document_form.html",
            title="Yeni Belge",
            subtitle="Taranacak veya dijital arşive aktarılacak belgeye ait temel bilgileri doldurun.",
            fields=_da23_document_fields(),
            list_url="/digital-archive/documents",
        )
    except Exception:
        current_app.logger.exception("Belge formu açılamadı.")
        flash("Belge formu açılırken beklenmeyen bir sorun oluştu.", "danger")
        return redirect("/digital-archive/documents")


@digital_archive_bp.route("/documents", methods=["POST"])
@login_required
def document_create_post():
    """Belge kaydı oluşturur."""
    from flask import request

    try:
        table = _da23_document_table()
        payload = _da23_document_payload(request.form.to_dict(flat=True))

        meaningful_payload = {
            key: value
            for key, value in payload.items()
            if key not in {"created_at", "updated_at", "is_active"} and value not in (None, "")
        }

        if not meaningful_payload:
            flash("Belge bilgisi girilmelidir.", "warning")
            return redirect("/digital-archive/documents/new")

        result = db.session.execute(table.insert().values(**payload))
        created_document_id = None
        try:
            created_document_id = result.inserted_primary_key[0]
        except Exception:
            created_document_id = None

        if created_document_id:
            _da28_write_history(
                int(created_document_id),
                "Belge oluşturuldu",
                "Belge oluşturuldu.",
            )

        db.session.commit()
    except ValueError as exc:
        db.session.rollback()
        flash(str(exc), "warning")
        return redirect("/digital-archive/documents/new")
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Belge kaydı oluşturulamadı.")
        flash("Kayıt oluşturulurken beklenmeyen bir sorun oluştu.", "danger")
        return redirect("/digital-archive/documents/new")

    flash("Belge kaydedildi.", "success")
    return redirect("/digital-archive/documents")



# DA-24A: Taranmış belge dosyası yükleme
def _da24_file_table():
    from sqlalchemy import MetaData, Table, inspect

    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()

    preferred = [
        "digital_archive_document_versions",
        "digital_archive_document_files",
        "digital_archive_files",
        "digital_archive_attachments",
    ]

    candidates = []

    for table_name in preferred:
        if table_name in table_names:
            candidates.append(table_name)

    for table_name in table_names:
        lower_name = table_name.lower()
        if (
            table_name.startswith("digital_archive")
            and table_name not in candidates
            and ("version" in lower_name or "file" in lower_name or "attachment" in lower_name)
        ):
            candidates.append(table_name)

    for table_name in candidates:
        columns = [column["name"] for column in inspector.get_columns(table_name)]
        if "document_id" in columns:
            metadata = MetaData()
            return Table(table_name, metadata, autoload_with=db.engine)

    raise RuntimeError("Belge dosyası bağlantı alanı bulunamadı.")


def _da24_file_label(column_name: str) -> str:
    labels = {
        "id": "No",
        "document_id": "Belge",
        "version_no": "Sürüm",
        "version_number": "Sürüm",
        "original_filename": "Dosya Adı",
        "source_filename": "Dosya Adı",
        "file_name": "Dosya Adı",
        "name": "Dosya Adı",
        "stored_filename": "Kayıtlı Dosya",
        "file_path": "Dosya Yolu",
        "path": "Dosya Yolu",
        "storage_path": "Dosya Yolu",
        "mime_type": "Dosya Türü",
        "content_type": "Dosya Türü",
        "file_size": "Boyut",
        "size_bytes": "Boyut",
        "checksum_sha256": "Kontrol Kodu",
        "sha256": "Kontrol Kodu",
        "hash": "Kontrol Kodu",
        "status": "Belge Durumu",
        "description": "Açıklama",
        "notes": "Notlar",
        "is_current": "Güncel",
        "is_active": "Durum",
        "created_at": "Yükleme Tarihi",
        "uploaded_at": "Yükleme Tarihi",
        "updated_at": "Güncelleme Tarihi",
    }
    return labels.get(column_name, column_name.replace("_", " ").title())


def _da24_document_row(document_id: int):
    from sqlalchemy import select

    table = _da23_document_table()
    return db.session.execute(select(table).where(table.c.id == document_id)).mappings().first()


def _da24_document_files(document_id: int) -> tuple[list[dict], list[str], dict]:
    from sqlalchemy import desc, select

    try:
        table = _da24_file_table()
    except RuntimeError:
        return [], [], {}

    preferred_columns = [
        "id",
        "version_no",
        "version_number",
        "original_filename",
        "source_filename",
        "file_name",
        "name",
        "mime_type",
        "content_type",
        "file_size",
        "size_bytes",
        "status",
        "created_at",
        "uploaded_at",
    ]

    available_columns = [column.name for column in table.columns]
    display_columns = [column for column in preferred_columns if column in available_columns][:8]
    if not display_columns:
        display_columns = available_columns[:8]

    query = select(table).where(table.c.document_id == document_id)

    if "id" in available_columns:
        query = query.order_by(desc(table.c.id))

    rows = [dict(row._mapping) for row in db.session.execute(query).all()]
    labels = {column: _da24_file_label(column) for column in display_columns}

    return rows, display_columns, labels


def _da24_next_version_no(table, document_id: int) -> int:
    from sqlalchemy import func, select

    for column_name in ("version_no", "version_number"):
        if column_name in table.c:
            current = db.session.execute(
                select(func.max(table.c[column_name])).where(table.c.document_id == document_id)
            ).scalar_one_or_none()
            return int(current or 0) + 1

    return 1


def _da24_safe_upload_path(document_id: int, filename: str) -> tuple[str, str]:
    from datetime import datetime
    from pathlib import Path

    from flask import current_app
    from werkzeug.utils import secure_filename

    safe_name = secure_filename(filename or "taranmis-belge.pdf")
    if not safe_name:
        safe_name = "taranmis-belge.pdf"

    stored_name = datetime.now().strftime("%Y%m%d_%H%M%S_") + safe_name

    upload_root = current_app.config.get("DIGITAL_ARCHIVE_UPLOAD_ROOT")
    if not upload_root:
        upload_root = str(Path(current_app.root_path).parent / "var" / "digital_archive" / "uploads")

    target_dir = Path(upload_root) / str(document_id)
    target_dir.mkdir(parents=True, exist_ok=True)

    absolute_path = target_dir / stored_name
    relative_path = str(Path("digital_archive") / "uploads" / str(document_id) / stored_name).replace("\\", "/")

    return str(absolute_path), relative_path


def _da24_file_payload(table, document_id: int, file_storage, file_bytes: bytes, stored_filename: str, relative_path: str):
    from datetime import datetime
    import hashlib

    now = datetime.now()
    original_filename = file_storage.filename or "taranmis-belge.pdf"
    mime_type = file_storage.mimetype or "application/octet-stream"
    checksum = hashlib.sha256(file_bytes).hexdigest()
    version_no = _da24_next_version_no(table, document_id)

    def default_for(column):
        name = column.name
        lower_name = name.lower()
        lower_type = str(column.type).lower()

        if name == "document_id":
            return document_id

        if lower_name in {"version_no", "version_number"}:
            return version_no

        if lower_name in {"original_filename", "source_filename", "file_name", "name"}:
            return original_filename

        if lower_name in {"stored_filename", "stored_name"}:
            return stored_filename

        if lower_name in {"file_path", "path", "storage_path"}:
            return relative_path

        if lower_name in {"mime_type", "content_type"}:
            return mime_type

        if lower_name in {"file_size", "size_bytes", "size"}:
            return len(file_bytes)

        if lower_name in {"checksum_sha256", "sha256", "sha256_hash", "file_hash", "file_checksum", "checksum", "hash"}:
            return checksum

        if lower_name in {"status"}:
            return "Yüklendi"

        if lower_name in {"description", "notes", "version_note"}:
            return "Taranmış belge dosyası yüklendi."

        if lower_name in {"storage_backend", "storage_type"}:
            return "local"

        if lower_name in {"created_at", "uploaded_at", "updated_at"}:
            return now

        if "bool" in lower_type:
            return True if lower_name in {"is_current", "is_active"} else False

        if "int" in lower_type:
            if lower_name.endswith("_id"):
                return 0
            return 0

        if "date" in lower_type and "time" not in lower_type:
            return now.date()

        if "time" in lower_type:
            return now

        if any(token in lower_type for token in ("char", "text", "varchar", "string")):
            return original_filename

        return None

    payload = {}

    for column in table.columns:
        name = column.name

        if name in {"id", "deleted_at"}:
            continue

        value = default_for(column)
        if value is not None:
            payload[name] = value

    for column in table.columns:
        name = column.name

        if name in {"id", "deleted_at"} or name in payload:
            continue

        nullable = getattr(column, "nullable", True)
        has_default = column.default is not None or column.server_default is not None

        if not nullable and not has_default:
            value = default_for(column)
            if value is not None:
                payload[name] = value

    return payload


@digital_archive_bp.get("/documents/<int:document_id>")
@login_required
def document_detail(document_id: int):
    """Belge detay ekranı."""
    try:
        document = _da24_document_row(document_id)
        if not document:
            flash("Belge bulunamadı.", "warning")
            return redirect("/digital-archive/documents")

        document = _da36b_enrich_document_row(document)

        table = _da23_document_table()
        document_columns = [column.name for column in table.columns]
        visible_document_columns = [
            column for column in [
                "id",
                "document_no",
                "title",
                "document_type",
                "document_date",
                "subject",
                "category_id",
                "physical_location_id",
                "retention_policy_id",
                "confidentiality_level",
                "status",
                "created_at",
            ]
            if column in document_columns
        ]

        file_rows, file_columns, file_labels = _da24_document_files(document_id)
        history_rows, history_columns, history_labels = _da28_history_rows(document_id)
        metadata_rows, metadata_columns, metadata_labels = _da29_metadata_rows(document_id)

        return render_template(
            "digital_archive/document_detail.html",
            document=dict(document),
            document_columns=visible_document_columns,
            document_labels={column: _da23_column_label(column) for column in visible_document_columns},
            file_rows=file_rows,
            file_columns=file_columns,
            file_labels=file_labels,
            history_rows=history_rows,
            history_columns=history_columns,
            history_labels=history_labels,
            metadata_rows=metadata_rows,
            metadata_columns=metadata_columns,
            metadata_labels=metadata_labels,
        )
    except Exception:
        current_app.logger.exception("Belge detayı açılamadı.")
        flash("Belge detayı açılırken beklenmeyen bir sorun oluştu.", "danger")
        return redirect("/digital-archive/documents")


@digital_archive_bp.route("/documents/<int:document_id>/files", methods=["POST"])
@login_required
def document_file_upload_post(document_id: int):
    """Taranmış belge dosyasını belgeye bağlar."""
    from pathlib import Path

    from flask import request

    allowed_extensions = {"pdf", "jpg", "jpeg", "png", "tif", "tiff"}

    try:
        document = _da24_document_row(document_id)
        if not document:
            flash("Belge bulunamadı.", "warning")
            return redirect("/digital-archive/documents")

        upload_file = request.files.get("file")
        if not upload_file or not upload_file.filename:
            flash("Yüklenecek dosya seçilmelidir.", "warning")
            return redirect(f"/digital-archive/documents/{document_id}")

        extension = upload_file.filename.rsplit(".", 1)[-1].lower() if "." in upload_file.filename else ""
        if extension not in allowed_extensions:
            flash("Yalnızca PDF, JPG, PNG veya TIF dosyası yüklenebilir.", "warning")
            return redirect(f"/digital-archive/documents/{document_id}")

        file_bytes = upload_file.read()
        if not file_bytes:
            flash("Boş dosya yüklenemez.", "warning")
            return redirect(f"/digital-archive/documents/{document_id}")

        absolute_path, relative_path = _da24_safe_upload_path(document_id, upload_file.filename)
        stored_filename = Path(absolute_path).name

        Path(absolute_path).write_bytes(file_bytes)

        table = _da24_file_table()
        payload = _da24_file_payload(table, document_id, upload_file, file_bytes, stored_filename, relative_path)

        result = db.session.execute(table.insert().values(**payload))
        related_id = None
        try:
            related_id = result.inserted_primary_key[0]
        except Exception:
            related_id = None

        _da28_write_history(
            document_id,
            "Taranmış dosya yüklendi",
            f"{upload_file.filename} dosyası belgeye bağlandı.",
            related_id=related_id,
        )

        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Belge dosyası yüklenemedi.")
        flash("Dosya yüklenirken beklenmeyen bir sorun oluştu.", "danger")
        return redirect(f"/digital-archive/documents/{document_id}")

    flash("Taranmış belge dosyası belgeye bağlandı.", "success")
    return redirect(f"/digital-archive/documents/{document_id}")



# DA-25A: Belge dosyası önizleme ve indirme
def _da25_file_row(document_id: int, file_id: int):
    from sqlalchemy import select

    table = _da24_file_table()

    if "id" not in table.c:
        return None

    return db.session.execute(
        select(table).where(
            table.c.id == file_id,
            table.c.document_id == document_id,
        )
    ).mappings().first()


def _da25_file_display_name(file_row: dict) -> str:
    for key in ("original_filename", "source_filename", "file_name", "name", "stored_filename"):
        value = file_row.get(key)
        if value:
            return str(value)

    return "taranmis-belge"


def _da25_file_mime_type(file_row: dict) -> str:
    for key in ("mime_type", "content_type"):
        value = file_row.get(key)
        if value:
            return str(value)

    return "application/octet-stream"


def _da25_file_absolute_path(file_row: dict):
    from pathlib import Path

    from flask import current_app

    raw_value = (
        file_row.get("storage_path")
        or file_row.get("file_path")
        or file_row.get("path")
    )

    if not raw_value:
        return None

    raw_path = Path(str(raw_value))
    if raw_path.is_absolute():
        return raw_path

    project_root = Path(current_app.root_path).parent

    candidates = [
        project_root / "var" / raw_path,
        project_root / raw_path,
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]


@digital_archive_bp.get("/documents/<int:document_id>/files/<int:file_id>/preview")
@login_required
def document_file_preview(document_id: int, file_id: int):
    """Taranmış belge dosyasını tarayıcıda gösterir."""
    from flask import flash, redirect, send_file

    try:
        file_row = _da25_file_row(document_id, file_id)
        if not file_row:
            flash("Dosya kaydı bulunamadı.", "warning")
            return redirect(f"/digital-archive/documents/{document_id}")

        absolute_path = _da25_file_absolute_path(file_row)
        if not absolute_path or not absolute_path.exists():
            flash("Dosya klasörde bulunamadı.", "warning")
            return redirect(f"/digital-archive/documents/{document_id}")

        return send_file(
            absolute_path,
            mimetype=_da25_file_mime_type(file_row),
            as_attachment=False,
            download_name=_da25_file_display_name(file_row),
        )
    except Exception:
        current_app.logger.exception("Belge dosyası önizlenemedi.")
        flash("Dosya önizleme sırasında beklenmeyen bir sorun oluştu.", "danger")
        return redirect(f"/digital-archive/documents/{document_id}")


@digital_archive_bp.get("/documents/<int:document_id>/files/<int:file_id>/download")
@login_required
def document_file_download(document_id: int, file_id: int):
    """Taranmış belge dosyasını indirir."""
    from flask import flash, redirect, send_file

    try:
        file_row = _da25_file_row(document_id, file_id)
        if not file_row:
            flash("Dosya kaydı bulunamadı.", "warning")
            return redirect(f"/digital-archive/documents/{document_id}")

        absolute_path = _da25_file_absolute_path(file_row)
        if not absolute_path or not absolute_path.exists():
            flash("Dosya klasörde bulunamadı.", "warning")
            return redirect(f"/digital-archive/documents/{document_id}")

        return send_file(
            absolute_path,
            mimetype=_da25_file_mime_type(file_row),
            as_attachment=True,
            download_name=_da25_file_display_name(file_row),
        )
    except Exception:
        current_app.logger.exception("Belge dosyası indirilemedi.")
        flash("Dosya indirme sırasında beklenmeyen bir sorun oluştu.", "danger")
        return redirect(f"/digital-archive/documents/{document_id}")


@digital_archive_bp.get("/documents/<int:document_id>/ocr")
@login_required
def document_ocr_ready(document_id: int):
    """Belge için metin okuma hazırlık ekranı."""
    try:
        document = _da24_document_row(document_id)
        if not document:
            flash("Belge bulunamadı.", "warning")
            return redirect("/digital-archive/documents")

        file_rows, file_columns, file_labels = _da24_document_files(document_id)
        readable_rows, readable_columns, readable_labels = _da27_ocr_rows(document_id)

        return render_template(
            "digital_archive/document_ocr_ready.html",
            document=dict(document),
            file_rows=file_rows,
            file_columns=file_columns,
            file_labels=file_labels,
            readable_rows=readable_rows,
            readable_columns=readable_columns,
            readable_labels=readable_labels,
            document_id=document_id,
        )
    except Exception:
        current_app.logger.exception("Metin okuma hazırlık ekranı açılamadı.")
        flash("Metin okuma hazırlığı açılırken beklenmeyen bir sorun oluştu.", "danger")
        return redirect(f"/digital-archive/documents/{document_id}")


# DA-27B: Okunan metin belge bağlantısı
def _da27_ocr_table():
    from sqlalchemy import MetaData, Table, inspect

    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()

    candidates = []
    if "digital_archive_ocr_jobs" in table_names:
        candidates.append("digital_archive_ocr_jobs")

    for table_name in table_names:
        lower_name = table_name.lower()
        if table_name.startswith("digital_archive") and table_name not in candidates:
            if any(token in lower_name for token in ("ocr", "text", "content", "search")):
                candidates.append(table_name)

    if not candidates:
        raise RuntimeError("Metin okuma tablosu bulunamadı.")

    metadata = MetaData()
    return Table(candidates[0], metadata, autoload_with=db.engine)


def _da27_text_columns(table) -> list[str]:
    result = []

    preferred = [
        "recognized_text",
        "extracted_text",
        "ocr_text",
        "text_content",
        "content",
        "result_text",
        "raw_text",
        "search_text",
        "plain_text",
    ]

    existing = [column.name for column in table.columns]

    for name in preferred:
        if name in existing:
            result.append(name)

    if result:
        return result

    excluded = {
        "status",
        "state",
        "language",
        "lang",
        "engine",
        "method",
        "source",
        "file_name",
        "mime_type",
        "content_type",
        "error",
        "error_message",
    }

    for column in table.columns:
        name = column.name
        lower_type = str(column.type).lower()

        if name in excluded or name.endswith("_path"):
            continue

        if any(token in lower_type for token in ("char", "text", "varchar", "string")):
            result.append(name)

    return result


def _da27_latest_file_id(document_id: int):
    from sqlalchemy import desc, select

    try:
        table = _da24_file_table()
    except RuntimeError:
        return None

    if "id" not in table.c or "document_id" not in table.c:
        return None

    return db.session.execute(
        select(table.c.id)
        .where(table.c.document_id == document_id)
        .order_by(desc(table.c.id))
        .limit(1)
    ).scalar_one_or_none()


def _da27_ocr_rows(document_id: int) -> tuple[list[dict], list[str], dict]:
    from sqlalchemy import desc, select

    try:
        table = _da27_ocr_table()
    except RuntimeError:
        return [], [], {}

    available_columns = [column.name for column in table.columns]
    text_columns = _da27_text_columns(table)
    file_id = _da27_latest_file_id(document_id)

    query = select(table)

    if "document_id" in table.c:
        query = query.where(table.c.document_id == document_id)
    elif file_id and "document_version_id" in table.c:
        query = query.where(table.c.document_version_id == file_id)
    elif file_id and "file_id" in table.c:
        query = query.where(table.c.file_id == file_id)
    elif file_id and "version_id" in table.c:
        query = query.where(table.c.version_id == file_id)
    else:
        return [], [], {}

    if "id" in table.c:
        query = query.order_by(desc(table.c.id))

    rows = [dict(row._mapping) for row in db.session.execute(query.limit(50)).all()]

    preferred_columns = [
        "id",
        "status",
        "state",
        "language",
        "lang",
        *text_columns,
        "created_at",
        "updated_at",
        "completed_at",
        "finished_at",
    ]

    display_columns = []
    for column in preferred_columns:
        if column in available_columns and column not in display_columns:
            display_columns.append(column)

    display_columns = display_columns[:8]

    labels = {
        "id": "No",
        "status": "Belge Durumu",
        "state": "Durum",
        "language": "Dil",
        "lang": "Dil",
        "recognized_text": "Okunan Metin",
        "extracted_text": "Okunan Metin",
        "ocr_text": "Okunan Metin",
        "text_content": "Okunan Metin",
        "content": "Okunan Metin",
        "result_text": "Okunan Metin",
        "raw_text": "Okunan Metin",
        "search_text": "Okunan Metin",
        "plain_text": "Okunan Metin",
        "created_at": "Kayıt Tarihi",
        "updated_at": "Güncelleme Tarihi",
        "completed_at": "Tamamlanma Tarihi",
        "finished_at": "Tamamlanma Tarihi",
    }

    return rows, display_columns, labels


def _da27_ocr_payload(document_id: int, text_value: str):
    from datetime import datetime

    table = _da27_ocr_table()
    now = datetime.now()
    file_id = _da27_latest_file_id(document_id)
    text_columns = _da27_text_columns(table)

    def default_for(column):
        name = column.name
        lower_name = name.lower()
        lower_type = str(column.type).lower()

        if name == "document_id":
            return document_id

        if lower_name in {"document_version_id", "file_id", "version_id"}:
            return file_id or 0

        if lower_name in set(text_columns):
            return text_value

        if lower_name in {"status", "state"}:
            return "Tamamlandı"

        if lower_name in {"language", "lang"}:
            return "tr"

        if lower_name in {"engine", "method", "source"}:
            return "Kullanıcı girişi"

        if lower_name in {"error", "error_message"}:
            return ""

        if lower_name in {"confidence", "confidence_score", "score"}:
            return 100

        if lower_name in {"created_at", "updated_at", "started_at", "completed_at", "finished_at"}:
            return now

        if "bool" in lower_type:
            return True if lower_name in {"is_active", "is_completed", "is_success"} else False

        if "int" in lower_type:
            if lower_name.endswith("_id"):
                return 0
            return 0

        if "float" in lower_type or "numeric" in lower_type or "decimal" in lower_type:
            return 100

        if "date" in lower_type and "time" not in lower_type:
            return now.date()

        if "time" in lower_type:
            return now

        if any(token in lower_type for token in ("char", "text", "varchar", "string")):
            return text_value[:500]

        return None

    payload = {}

    for column in table.columns:
        name = column.name

        if name in {"id", "deleted_at"}:
            continue

        value = default_for(column)
        if value is not None:
            payload[name] = value

    for column in table.columns:
        name = column.name

        if name in {"id", "deleted_at"} or name in payload:
            continue

        nullable = getattr(column, "nullable", True)
        has_default = column.default is not None or column.server_default is not None

        if not nullable and not has_default:
            value = default_for(column)
            if value is not None:
                payload[name] = value

    return payload


def _da27_document_ids_for_text(search_text: str) -> list[int]:
    from sqlalchemy import String, cast, or_, select

    try:
        table = _da27_ocr_table()
    except RuntimeError:
        return []

    text_columns = _da27_text_columns(table)
    if not text_columns:
        return []

    text_condition = or_(*[
        cast(table.c[column], String).ilike(f"%{search_text}%")
        for column in text_columns
        if column in table.c
    ])

    document_ids = set()

    if "document_id" in table.c:
        rows = db.session.execute(
            select(table.c.document_id).where(text_condition).distinct().limit(500)
        ).all()

        for row in rows:
            if row[0]:
                document_ids.add(int(row[0]))

    else:
        file_id_column = None
        for candidate in ("document_version_id", "file_id", "version_id"):
            if candidate in table.c:
                file_id_column = candidate
                break

        if file_id_column:
            file_ids = [
                row[0]
                for row in db.session.execute(
                    select(table.c[file_id_column]).where(text_condition).distinct().limit(500)
                ).all()
                if row[0]
            ]

            if file_ids:
                try:
                    file_table = _da24_file_table()
                    if "id" in file_table.c and "document_id" in file_table.c:
                        rows = db.session.execute(
                            select(file_table.c.document_id).where(file_table.c.id.in_(file_ids)).distinct().limit(500)
                        ).all()

                        for row in rows:
                            if row[0]:
                                document_ids.add(int(row[0]))
                except RuntimeError:
                    pass

    return sorted(document_ids)


@digital_archive_bp.route("/documents/<int:document_id>/ocr", methods=["POST"])
@login_required
def document_ocr_text_post(document_id: int):
    """Okunan metni belgeye bağlar."""
    from flask import request

    try:
        document = _da24_document_row(document_id)
        if not document:
            flash("Belge bulunamadı.", "warning")
            return redirect("/digital-archive/documents")

        text_value = request.form.get("recognized_text", "").strip()
        if not text_value:
            flash("Okunan metin alanı boş bırakılamaz.", "warning")
            return redirect(f"/digital-archive/documents/{document_id}/ocr")

        table = _da27_ocr_table()
        payload = _da27_ocr_payload(document_id, text_value)

        result = db.session.execute(table.insert().values(**payload))
        related_id = None
        try:
            related_id = result.inserted_primary_key[0]
        except Exception:
            related_id = None

        _da28_write_history(
            document_id,
            "Okunan metin kaydedildi",
            "Okunan metin belgeye bağlandı.",
            related_id=related_id,
        )

        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Okunan metin belgeye bağlanamadı.")
        flash("Okunan metin kaydedilirken beklenmeyen bir sorun oluştu.", "danger")
        return redirect(f"/digital-archive/documents/{document_id}/ocr")

    flash("Okunan metin belgeye bağlandı.", "success")
    return redirect(f"/digital-archive/documents/{document_id}/ocr")



# DA-28B: Belge işlem geçmişi
def _da28_history_table():
    from sqlalchemy import MetaData, Table, inspect

    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()

    if "digital_archive_audit_events" not in table_names:
        raise RuntimeError("İşlem geçmişi tablosu bulunamadı.")

    metadata = MetaData()
    return Table("digital_archive_audit_events", metadata, autoload_with=db.engine)


def _da28_label(column_name: str) -> str:
    labels = {
        "id": "No",
        "action": "İşlem",
        "event": "İşlem",
        "event_type": "İşlem",
        "operation": "İşlem",
        "activity_type": "İşlem",
        "title": "Başlık",
        "name": "Başlık",
        "summary": "Özet",
        "description": "Açıklama",
        "detail": "Açıklama",
        "details": "Açıklama",
        "message": "Açıklama",
        "note": "Not",
        "notes": "Not",
        "status": "Belge Durumu",
        "state": "Durum",
        "created_at": "Tarih",
        "updated_at": "Güncelleme Tarihi",
        "event_at": "Tarih",
        "performed_at": "Tarih",
        "timestamp": "Tarih",
    }
    return labels.get(column_name, "Bilgi")


def _da28_document_id_column(table):
    for candidate in ("document_id", "record_id", "entity_id", "object_id", "target_id", "resource_id"):
        if candidate in table.c:
            return candidate
    return None


def _da28_history_rows(document_id: int) -> tuple[list[dict], list[str], dict]:
    from sqlalchemy import desc, select

    try:
        table = _da28_history_table()
    except RuntimeError:
        return [], [], {}

    available_columns = [column.name for column in table.columns]
    document_id_column = _da28_document_id_column(table)

    query = select(table)

    if document_id_column:
        query = query.where(table.c[document_id_column] == document_id)

    if "id" in table.c:
        query = query.order_by(desc(table.c.id))
    elif "created_at" in table.c:
        query = query.order_by(desc(table.c.created_at))

    rows = [dict(row._mapping) for row in db.session.execute(query.limit(50)).all()]

    preferred_columns = [
        "id",
        "action",
        "event",
        "event_type",
        "operation",
        "activity_type",
        "title",
        "summary",
        "description",
        "detail",
        "details",
        "message",
        "status",
        "state",
        "created_at",
        "event_at",
        "performed_at",
        "timestamp",
    ]

    display_columns = []
    for column in preferred_columns:
        if column in available_columns and column not in display_columns:
            display_columns.append(column)

    display_columns = display_columns[:7]

    return rows, display_columns, {column: _da28_label(column) for column in display_columns}


def _da28_history_payload(document_id: int, action: str, description: str, related_id=None):
    from datetime import datetime

    table = _da28_history_table()
    now = datetime.now()

    def default_for(column):
        name = column.name
        lower_name = name.lower()
        lower_type = str(column.type).lower()

        if name in {"document_id", "record_id", "entity_id", "object_id", "target_id", "resource_id"}:
            return document_id

        if lower_name in {"document_version_id", "file_id", "version_id", "related_id", "related_record_id"}:
            return related_id or 0

        if lower_name in {"user_id", "actor_id", "created_by_id", "performed_by_id", "updated_by_id"}:
            return 0

        if lower_name in {"action", "event", "event_type", "operation", "activity_type"}:
            return action

        if lower_name in {"title", "name", "summary"}:
            return action

        if lower_name in {"description", "detail", "details", "message", "note", "notes"}:
            return description

        if lower_name in {"entity_type", "object_type", "target_type", "resource_type", "record_type"}:
            return "Belge"

        if lower_name in {"entity_table", "table_name", "target_table", "resource_table"}:
            return "digital_archive_documents"

        if lower_name in {"module", "module_name", "scope"}:
            return "Dijital Arşiv"

        if lower_name in {"status", "state"}:
            return "Tamamlandı"

        if lower_name in {"ip_address", "user_agent", "session_id"}:
            return ""

        if lower_name in {"payload", "payload_json", "metadata", "metadata_json", "extra", "extra_json"}:
            return "{}"

        if lower_name in {"created_at", "updated_at", "event_at", "performed_at", "timestamp"}:
            return now

        if "bool" in lower_type:
            return True if lower_name in {"is_active", "success", "is_success"} else False

        if "int" in lower_type:
            return 0

        if "float" in lower_type or "numeric" in lower_type or "decimal" in lower_type:
            return 0

        if "date" in lower_type and "time" not in lower_type:
            return now.date()

        if "time" in lower_type:
            return now

        if "json" in lower_type:
            return "{}"

        if any(token in lower_type for token in ("char", "text", "varchar", "string")):
            return description[:500]

        return None

    payload = {}

    for column in table.columns:
        name = column.name

        if name in {"id", "deleted_at"}:
            continue

        value = default_for(column)
        if value is not None:
            payload[name] = value

    for column in table.columns:
        name = column.name

        if name in {"id", "deleted_at"} or name in payload:
            continue

        nullable = getattr(column, "nullable", True)
        has_default = column.default is not None or column.server_default is not None

        if not nullable and not has_default:
            value = default_for(column)
            if value is not None:
                payload[name] = value

    return payload


def _da28_write_history(document_id: int, action: str, description: str, related_id=None) -> None:
    try:
        table = _da28_history_table()
        payload = _da28_history_payload(document_id, action, description, related_id=related_id)
        db.session.execute(table.insert().values(**payload))
    except Exception:
        current_app.logger.exception("Belge işlem geçmişi yazılamadı.")



# DA-29B: Dinamik özel alanlar
def _da29_create_metadata_tables() -> None:
    from sqlalchemy import text

    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS digital_archive_metadata_fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(150) NOT NULL,
            label VARCHAR(150) NOT NULL,
            field_type VARCHAR(50) NOT NULL DEFAULT 'Metin',
            applies_to VARCHAR(100) NOT NULL DEFAULT 'Belge',
            is_required INTEGER NOT NULL DEFAULT 0,
            is_active INTEGER NOT NULL DEFAULT 1,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME
        )
    """))

    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS digital_archive_metadata_values (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            field_id INTEGER NOT NULL,
            value_text TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME
        )
    """))

    db.session.commit()


def _da29_metadata_tables(create_if_missing: bool = False):
    from sqlalchemy import MetaData, Table, inspect

    inspector = inspect(db.engine)
    table_names = set(inspector.get_table_names())

    required = {"digital_archive_metadata_fields", "digital_archive_metadata_values"}
    if not required.issubset(table_names):
        if not create_if_missing:
            raise RuntimeError("Özel alan tabloları bulunamadı.")

        _da29_create_metadata_tables()

    metadata = MetaData()
    fields_table = Table("digital_archive_metadata_fields", metadata, autoload_with=db.engine)
    values_table = Table("digital_archive_metadata_values", metadata, autoload_with=db.engine)

    return fields_table, values_table


def _da29_slug(value: str) -> str:
    import re
    import unicodedata

    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", ascii_value).strip("_").lower()

    return slug or "ozel_alan"


def _da29_active_fields() -> list[dict]:
    from sqlalchemy import select

    try:
        fields_table, _values_table = _da29_metadata_tables(create_if_missing=False)
    except RuntimeError:
        return []

    query = select(fields_table)
    if "is_active" in fields_table.c:
        query = query.where(fields_table.c.is_active == 1)

    if "sort_order" in fields_table.c:
        query = query.order_by(fields_table.c.sort_order, fields_table.c.id)
    elif "id" in fields_table.c:
        query = query.order_by(fields_table.c.id)

    return [dict(row._mapping) for row in db.session.execute(query.limit(200)).all()]


def _da29_metadata_rows(document_id: int):
    from sqlalchemy import text

    try:
        _fields_table, _values_table = _da29_metadata_tables(create_if_missing=False)
    except RuntimeError:
        return [], [], {}

    rows = db.session.execute(
        text("""
            SELECT
                v.id,
                f.label,
                f.field_type,
                v.value_text,
                v.created_at,
                v.updated_at
            FROM digital_archive_metadata_values v
            JOIN digital_archive_metadata_fields f ON f.id = v.field_id
            WHERE v.document_id = :document_id
            ORDER BY f.sort_order, f.label, v.id
        """),
        {"document_id": document_id},
    ).mappings().all()

    display_rows = [dict(row) for row in rows]
    display_columns = ["label", "field_type", "value_text", "created_at"]

    labels = {
        "label": "Alan",
        "field_type": "Tür",
        "value_text": "Değer",
        "created_at": "Kayıt Tarihi",
        "updated_at": "Güncelleme Tarihi",
    }

    return display_rows, display_columns, labels


def _da29_existing_values(document_id: int) -> dict[int, dict]:
    from sqlalchemy import select

    try:
        _fields_table, values_table = _da29_metadata_tables(create_if_missing=False)
    except RuntimeError:
        return {}

    rows = db.session.execute(
        select(values_table).where(values_table.c.document_id == document_id)
    ).all()

    result = {}
    for row in rows:
        item = dict(row._mapping)
        field_id = item.get("field_id")
        if field_id is not None:
            result[int(field_id)] = item

    return result


def _da29_document_ids_for_metadata(search_text: str) -> list[int]:
    from sqlalchemy import String, cast, select

    try:
        _fields_table, values_table = _da29_metadata_tables(create_if_missing=False)
    except RuntimeError:
        return []

    if "document_id" not in values_table.c or "value_text" not in values_table.c:
        return []

    rows = db.session.execute(
        select(values_table.c.document_id)
        .where(cast(values_table.c.value_text, String).ilike(f"%{search_text}%"))
        .distinct()
        .limit(500)
    ).all()

    return sorted({int(row[0]) for row in rows if row[0]})


@digital_archive_bp.route("/metadata-fields", methods=["GET", "POST"])
@login_required
def metadata_fields():
    """Belgeler için özel alan tanımları."""
    from datetime import datetime

    from flask import request
    from sqlalchemy import desc, select

    try:
        fields_table, _values_table = _da29_metadata_tables(create_if_missing=True)

        if request.method == "POST":
            label = request.form.get("label", "").strip()
            field_type = request.form.get("field_type", "Metin").strip() or "Metin"
            applies_to = request.form.get("applies_to", "Belge").strip() or "Belge"
            sort_order_raw = request.form.get("sort_order", "0").strip()

            if not label:
                flash("Alan adı boş bırakılamaz.", "warning")
                return redirect("/digital-archive/metadata-fields")

            try:
                sort_order = int(sort_order_raw)
            except ValueError:
                sort_order = 0

            name = _da29_slug(label)

            payload = {
                "name": name,
                "label": label,
                "field_type": field_type,
                "applies_to": applies_to,
                "is_required": 0,
                "is_active": 1,
                "sort_order": sort_order,
                "created_at": datetime.now(),
            }

            db.session.execute(fields_table.insert().values(**payload))
            db.session.commit()

            flash("Özel alan tanımı oluşturuldu.", "success")
            return redirect("/digital-archive/metadata-fields")

        rows = [dict(row._mapping) for row in db.session.execute(
            select(fields_table).order_by(desc(fields_table.c.id)).limit(200)
        ).all()]

        display_columns = ["id", "label", "field_type", "applies_to", "is_active", "created_at"]
        display_columns = [column for column in display_columns if column in fields_table.c]

        labels = {
            "id": "No",
            "label": "Alan",
            "field_type": "Tür",
            "applies_to": "Kullanım Yeri",
            "is_active": "Durum",
            "created_at": "Kayıt Tarihi",
        }

        return render_template(
            "digital_archive/metadata_fields.html",
            rows=rows,
            display_columns=display_columns,
            labels=labels,
        )
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Özel alan tanımları açılamadı.")
        flash("Özel alan tanımları açılırken beklenmeyen bir sorun oluştu.", "danger")
        return redirect("/digital-archive/")


@digital_archive_bp.route("/documents/<int:document_id>/metadata", methods=["GET", "POST"])
@login_required
def document_metadata(document_id: int):
    """Belgeye özel alan değerleri bağlar."""
    from datetime import datetime

    from flask import request
    from sqlalchemy import select, update

    try:
        document = _da24_document_row(document_id)
        if not document:
            flash("Belge bulunamadı.", "warning")
            return redirect("/digital-archive/documents")

        fields_table, values_table = _da29_metadata_tables(create_if_missing=True)

        fields = _da29_active_fields()

        if request.method == "POST":
            existing_values = _da29_existing_values(document_id)

            for field in fields:
                field_id = int(field.get("id"))
                form_key = f"field_{field_id}"
                value_text = request.form.get(form_key, "").strip()

                if not value_text:
                    continue

                if field_id in existing_values:
                    db.session.execute(
                        update(values_table)
                        .where(values_table.c.id == existing_values[field_id]["id"])
                        .values(value_text=value_text, updated_at=datetime.now())
                    )
                else:
                    db.session.execute(
                        values_table.insert().values(
                            document_id=document_id,
                            field_id=field_id,
                            value_text=value_text,
                            created_at=datetime.now(),
                        )
                    )

            try:
                _da28_write_history(
                    document_id,
                    "Özel alanlar güncellendi",
                    "Belge özel alanları güncellendi.",
                )
            except Exception:
                current_app.logger.exception("Özel alan işlem geçmişi yazılamadı.")

            db.session.commit()
            flash("Özel alanlar belgeye kaydedildi.", "success")
            return redirect(f"/digital-archive/documents/{document_id}/metadata")

        existing_values = _da29_existing_values(document_id)
        readable_rows, readable_columns, readable_labels = _da29_metadata_rows(document_id)

        return render_template(
            "digital_archive/document_metadata.html",
            document=dict(document),
            document_id=document_id,
            fields=fields,
            existing_values=existing_values,
            readable_rows=readable_rows,
            readable_columns=readable_columns,
            readable_labels=readable_labels,
        )
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Belge özel alan ekranı açılamadı.")
        flash("Belge özel alanları açılırken beklenmeyen bir sorun oluştu.", "danger")
        return redirect(f"/digital-archive/documents/{document_id}")



# DA-30A: Tarihi Alan hazır özel alan seti
def _da30_historical_field_set() -> list[dict]:
    return [
        {"label": "Muharebe Alanı", "field_type": "Metin", "sort_order": 10},
        {"label": "Cephe / Sektör", "field_type": "Metin", "sort_order": 20},
        {"label": "Tarihsel Dönem", "field_type": "Metin", "sort_order": 30},
        {"label": "İlgili Şehitlik / Anıt", "field_type": "Metin", "sort_order": 40},
        {"label": "İlgili Köy / Mevki", "field_type": "Metin", "sort_order": 50},
        {"label": "Birlik / Alay", "field_type": "Metin", "sort_order": 60},
        {"label": "Komutan / Şahıs", "field_type": "Metin", "sort_order": 70},
        {"label": "Belge Dili", "field_type": "Metin", "sort_order": 80},
        {"label": "Kaynak / Koleksiyon", "field_type": "Metin", "sort_order": 90},
        {"label": "Envanter No", "field_type": "Metin", "sort_order": 100},
        {"label": "Koruma Durumu", "field_type": "Metin", "sort_order": 110},
        {"label": "Açıklama / Tarihsel Not", "field_type": "Uzun Metin", "sort_order": 120},
    ]


@digital_archive_bp.route("/metadata-field-set", methods=["GET", "POST"])
@login_required
def metadata_field_set():
    """Tarihi Alan hazır özel alan seti."""
    from datetime import datetime

    from sqlalchemy import select

    try:
        fields_table, _values_table = _da29_metadata_tables(create_if_missing=True)
        field_set = _da30_historical_field_set()

        existing_rows = db.session.execute(
            select(fields_table.c.label)
        ).all()
        existing_labels = {row[0] for row in existing_rows if row[0]}

        if request.method == "POST":
            added_count = 0

            for item in field_set:
                label = item["label"]

                if label in existing_labels:
                    continue

                payload = {
                    "name": _da29_slug(label),
                    "label": label,
                    "field_type": item.get("field_type", "Metin"),
                    "applies_to": "Belge",
                    "is_required": 0,
                    "is_active": 1,
                    "sort_order": item.get("sort_order", 0),
                    "created_at": datetime.now(),
                }

                db.session.execute(fields_table.insert().values(**payload))
                added_count += 1

            db.session.commit()

            if added_count:
                flash(f"{added_count} özel alan tanımı eklendi.", "success")
            else:
                flash("Hazır özel alanlar zaten tanımlı.", "info")

            return redirect("/digital-archive/metadata-field-set")

        preview_rows = []
        for item in field_set:
            preview_rows.append({
                "label": item["label"],
                "field_type": item.get("field_type", "Metin"),
                "status": "Tanımlı" if item["label"] in existing_labels else "Eklenecek",
            })

        return render_template(
            "digital_archive/metadata_field_set.html",
            rows=preview_rows,
        )
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Hazır özel alan seti açılamadı.")
        flash("Hazır özel alan seti açılırken beklenmeyen bir sorun oluştu.", "danger")
        return redirect("/digital-archive/metadata-fields")



# DA-31A: Arşiv malzemesi türleri
def _da31_create_material_type_table() -> None:
    from sqlalchemy import text

    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS digital_archive_material_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(150) NOT NULL,
            description TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME
        )
    """))

    db.session.commit()


def _da31_material_type_table(create_if_missing: bool = False):
    from sqlalchemy import MetaData, Table, inspect

    inspector = inspect(db.engine)
    table_names = set(inspector.get_table_names())

    if "digital_archive_material_types" not in table_names:
        if not create_if_missing:
            raise RuntimeError("Arşiv malzemesi türleri tablosu bulunamadı.")

        _da31_create_material_type_table()

    metadata = MetaData()
    return Table("digital_archive_material_types", metadata, autoload_with=db.engine)


@digital_archive_bp.route("/material-types", methods=["GET", "POST"])
@login_required
def material_types():
    """Arşiv malzemesi türleri."""
    from datetime import datetime

    from flask import request
    from sqlalchemy import desc, select

    try:
        table = _da31_material_type_table(create_if_missing=True)

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            description = request.form.get("description", "").strip()
            sort_order_raw = request.form.get("sort_order", "0").strip()

            if not name:
                flash("Malzeme türü adı boş bırakılamaz.", "warning")
                return redirect("/digital-archive/material-types")

            try:
                sort_order = int(sort_order_raw)
            except ValueError:
                sort_order = 0

            payload = {
                "name": name,
                "description": description,
                "is_active": 1,
                "sort_order": sort_order,
                "created_at": datetime.now(),
            }

            db.session.execute(table.insert().values(**payload))
            db.session.commit()

            flash("Arşiv malzemesi türü oluşturuldu.", "success")
            return redirect("/digital-archive/material-types")

        rows = [dict(row._mapping) for row in db.session.execute(
            select(table).order_by(desc(table.c.id)).limit(200)
        ).all()]

        display_columns = ["id", "name", "description", "is_active", "created_at"]
        display_columns = [column for column in display_columns if column in table.c]

        labels = {
            "id": "No",
            "name": "Malzeme Türü",
            "description": "Açıklama",
            "is_active": "Durum",
            "created_at": "Kayıt Tarihi",
        }

        return render_template(
            "digital_archive/material_types.html",
            rows=rows,
            display_columns=display_columns,
            labels=labels,
        )
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Arşiv malzemesi türleri açılamadı.")
        flash("Arşiv malzemesi türleri açılırken beklenmeyen bir sorun oluştu.", "danger")
        return redirect("/digital-archive/")



# DA-32A: Belge arşiv malzemesi bağlantısı
def _da32_create_document_material_links_table() -> None:
    from sqlalchemy import text

    db.session.execute(text("""
        CREATE TABLE IF NOT EXISTS digital_archive_document_material_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            material_type_id INTEGER NOT NULL,
            material_quantity INTEGER NOT NULL DEFAULT 1,
            material_code VARCHAR(120),
            physical_location_note TEXT,
            description TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_by INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME
        )
    """))

    db.session.commit()


def _da32_document_material_links_table(create_if_missing: bool = False):
    from sqlalchemy import MetaData, Table, inspect

    inspector = inspect(db.engine)
    table_names = set(inspector.get_table_names())

    if "digital_archive_document_material_links" not in table_names:
        if not create_if_missing:
            raise RuntimeError("Belge malzeme bağlantı tablosu bulunamadı.")

        _da32_create_document_material_links_table()

    metadata = MetaData()
    return Table("digital_archive_document_material_links", metadata, autoload_with=db.engine)


def _da32_required_table(table_name: str):
    from sqlalchemy import MetaData, Table, inspect

    inspector = inspect(db.engine)
    table_names = set(inspector.get_table_names())

    if table_name not in table_names:
        raise RuntimeError(f"Gerekli tablo bulunamadı: {table_name}")

    metadata = MetaData()
    return Table(table_name, metadata, autoload_with=db.engine)


def _da32_row_label(row: dict, columns: set[str], candidates: list[str], fallback: str) -> str:
    for column in candidates:
        if column in columns:
            value = row.get(column)
            if value not in (None, ""):
                return str(value)

    row_id = row.get("id", "")
    return f"{fallback} #{row_id}"


@digital_archive_bp.route("/document-material-links", methods=["GET", "POST"])
@login_required
def document_material_links():
    """Belge ile arşiv malzemesi türü bağlantısı."""
    from datetime import datetime

    from flask import current_app, flash, redirect, render_template, request
    from flask_login import current_user
    from sqlalchemy import desc, func, select

    try:
        links_table = _da32_document_material_links_table(create_if_missing=True)
        documents_table = _da32_required_table("digital_archive_documents")

        if "_da31_material_type_table" in globals():
            material_types_table = _da31_material_type_table(create_if_missing=True)
        else:
            material_types_table = _da32_required_table("digital_archive_material_types")

        material_count = db.session.execute(
            select(func.count()).select_from(material_types_table)
        ).scalar_one()

        if material_count == 0:
            db.session.execute(
                material_types_table.insert().values(
                    name="Arşiv Kutusu",
                    description="Fiziksel arşivde kutu bazlı saklama ve takip için kullanılır.",
                    is_active=1,
                    sort_order=10,
                    created_at=datetime.now(),
                )
            )
            db.session.commit()

        document_columns = set(documents_table.c.keys())
        material_columns = set(material_types_table.c.keys())

        document_rows = [
            dict(row._mapping)
            for row in db.session.execute(
                select(documents_table).order_by(desc(documents_table.c.id)).limit(250)
            ).all()
        ]

        material_order = material_types_table.c.sort_order if "sort_order" in material_types_table.c else material_types_table.c.id
        material_rows = [
            dict(row._mapping)
            for row in db.session.execute(
                select(material_types_table).order_by(material_order, material_types_table.c.id).limit(250)
            ).all()
        ]

        document_options = [
            {
                "id": row.get("id"),
                "label": _da32_row_label(
                    row,
                    document_columns,
                    [
                        "title",
                        "document_title",
                        "subject",
                        "name",
                        "document_name",
                        "file_name",
                        "original_filename",
                        "reference_no",
                        "reference_number",
                        "archive_code",
                    ],
                    "Belge",
                ),
            }
            for row in document_rows
        ]

        material_options = [
            {
                "id": row.get("id"),
                "label": _da32_row_label(
                    row,
                    material_columns,
                    ["name", "title", "material_type", "description"],
                    "Malzeme Türü",
                ),
            }
            for row in material_rows
        ]

        if request.method == "POST":
            document_id_raw = request.form.get("document_id", "").strip()
            material_type_id_raw = request.form.get("material_type_id", "").strip()
            quantity_raw = request.form.get("material_quantity", "1").strip()
            material_code = request.form.get("material_code", "").strip()
            physical_location_note = request.form.get("physical_location_note", "").strip()
            description = request.form.get("description", "").strip()

            try:
                document_id = int(document_id_raw)
                material_type_id = int(material_type_id_raw)
            except ValueError:
                flash("Belge ve malzeme türü seçimi zorunludur.", "warning")
                return redirect("/digital-archive/document-material-links")

            try:
                material_quantity = int(quantity_raw)
            except ValueError:
                material_quantity = 1

            if material_quantity < 1:
                material_quantity = 1

            document_exists = db.session.execute(
                select(func.count()).select_from(documents_table).where(documents_table.c.id == document_id)
            ).scalar_one()

            material_exists = db.session.execute(
                select(func.count()).select_from(material_types_table).where(material_types_table.c.id == material_type_id)
            ).scalar_one()

            if not document_exists:
                flash("Seçilen belge bulunamadı.", "warning")
                return redirect("/digital-archive/document-material-links")

            if not material_exists:
                flash("Seçilen arşiv malzemesi türü bulunamadı.", "warning")
                return redirect("/digital-archive/document-material-links")

            created_by = getattr(current_user, "id", None)

            db.session.execute(
                links_table.insert().values(
                    document_id=document_id,
                    material_type_id=material_type_id,
                    material_quantity=material_quantity,
                    material_code=material_code,
                    physical_location_note=physical_location_note,
                    description=description,
                    is_active=1,
                    created_by=created_by,
                    created_at=datetime.now(),
                )
            )
            db.session.commit()

            flash("Belge ile arşiv malzemesi türü bağlantısı oluşturuldu.", "success")
            return redirect("/digital-archive/document-material-links")

        link_rows = [
            dict(row._mapping)
            for row in db.session.execute(
                select(links_table).order_by(desc(links_table.c.id)).limit(200)
            ).all()
        ]

        document_map = {int(option["id"]): option["label"] for option in document_options if option.get("id") is not None}
        material_map = {int(option["id"]): option["label"] for option in material_options if option.get("id") is not None}

        return render_template(
            "digital_archive/document_material_links.html",
            documents=document_options,
            material_types=material_options,
            rows=link_rows,
            document_map=document_map,
            material_map=material_map,
        )

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Belge malzeme bağlantısı açılamadı.")
        flash("Belge malzeme bağlantısı açılırken beklenmeyen bir sorun oluştu.", "danger")
        return redirect("/digital-archive/")



# DA-33A: Belge malzeme bağlantıları özeti
@digital_archive_bp.route("/documents/<int:document_id>/material-summary", methods=["GET"])
@login_required
def document_material_summary(document_id: int):
    """Belge özelinde arşiv malzemesi bağlantıları özeti."""
    from flask import current_app, flash, redirect, render_template
    from sqlalchemy import desc, select

    try:
        documents_table = _da32_required_table("digital_archive_documents")
        links_table = _da32_document_material_links_table(create_if_missing=True)

        if "_da31_material_type_table" in globals():
            material_types_table = _da31_material_type_table(create_if_missing=True)
        else:
            material_types_table = _da32_required_table("digital_archive_material_types")

        document_row = db.session.execute(
            select(documents_table).where(documents_table.c.id == document_id)
        ).first()

        if not document_row:
            flash("Belge bulunamadı.", "warning")
            return redirect("/digital-archive/documents")

        document = dict(document_row._mapping)
        document_columns = set(documents_table.c.keys())

        document_label = _da32_row_label(
            document,
            document_columns,
            [
                "title",
                "document_title",
                "subject",
                "name",
                "document_name",
                "file_name",
                "original_filename",
                "reference_no",
                "reference_number",
                "archive_code",
            ],
            "Belge",
        )

        link_rows = [
            dict(row._mapping)
            for row in db.session.execute(
                select(links_table)
                .where(links_table.c.document_id == document_id)
                .order_by(desc(links_table.c.id))
                .limit(300)
            ).all()
        ]

        material_rows = [
            dict(row._mapping)
            for row in db.session.execute(
                select(material_types_table).limit(500)
            ).all()
        ]

        material_columns = set(material_types_table.c.keys())
        material_map = {
            int(row.get("id")): _da32_row_label(
                row,
                material_columns,
                ["name", "title", "material_type", "description"],
                "Malzeme Türü",
            )
            for row in material_rows
            if row.get("id") is not None
        }

        active_count = sum(1 for row in link_rows if row.get("is_active"))
        passive_count = len(link_rows) - active_count
        total_quantity = sum(int(row.get("material_quantity") or 0) for row in link_rows)

        return render_template(
            "digital_archive/document_material_summary.html",
            document=document,
            document_id=document_id,
            document_label=document_label,
            rows=link_rows,
            material_map=material_map,
            active_count=active_count,
            passive_count=passive_count,
            total_quantity=total_quantity,
        )

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Belge malzeme özeti açılamadı.")
        flash("Belge malzeme özeti açılırken beklenmeyen bir sorun oluştu.", "danger")
        return redirect("/digital-archive/document-material-links")



# DA-34A: Belge birleşik detay görünümü
def _da34_optional_table(table_names: list[str]):
    from sqlalchemy import MetaData, Table, inspect

    inspector = inspect(db.engine)
    existing = set(inspector.get_table_names())

    for table_name in table_names:
        if table_name in existing:
            metadata = MetaData()
            return Table(table_name, metadata, autoload_with=db.engine)

    return None


def _da34_document_filter_column(table):
    candidates = [
        "document_id",
        "archive_document_id",
        "digital_archive_document_id",
        "doc_id",
    ]

    for candidate in candidates:
        if candidate in table.c:
            return table.c[candidate]

    return None


def _da34_rows_for_document(table, document_id: int, limit: int = 100) -> list[dict]:
    from sqlalchemy import desc, select

    if table is None:
        return []

    document_column = _da34_document_filter_column(table)
    if document_column is None:
        return []

    query = select(table).where(document_column == document_id)

    if "id" in table.c:
        query = query.order_by(desc(table.c.id))

    rows = db.session.execute(query.limit(limit)).all()
    return [dict(row._mapping) for row in rows]


def _da34_public_columns(row: dict) -> list[tuple[str, str]]:
    hidden = {
        "password",
        "password_hash",
        "secret",
        "token",
        "csrf_token",
        "file_path",
        "storage_path",
        "absolute_path",
    }

    labels = {
        "id": "No",
        "document_id": "Belge No",
        "archive_document_id": "Belge No",
        "digital_archive_document_id": "Belge No",
        "title": "Başlık",
        "document_title": "Başlık",
        "subject": "Konu",
        "name": "Ad",
        "document_name": "Belge Adı",
        "file_name": "Dosya Adı",
        "original_filename": "Dosya Adı",
        "archive_code": "Arşiv Kodu",
        "reference_no": "Referans No",
        "reference_number": "Referans No",
        "document_type": "Belge Türü",
        "category_id": "Kategori",
        "physical_location_id": "Fiziksel Konum",
        "retention_policy_id": "Saklama Kuralı",
        "confidentiality_level": "Gizlilik Seviyesi",
        "status": "Belge Durumu",
        "is_active": "Aktif",
        "created_at": "Kayıt Tarihi",
        "updated_at": "Güncelleme Tarihi",
        "created_by": "Kaydı Oluşturan",
        "action": "İşlem",
        "event_type": "İşlem Türü",
        "description": "Açıklama",
        "note": "Not",
        "readable_text": "Okunan Metin",
        "ocr_text": "Okunan Metin",
        "extracted_text": "Okunan Metin",
        "field_key": "Alan",
        "field_name": "Alan Adı",
        "field_value": "Değer",
        "value": "Değer",
        "material_type_id": "Malzeme Türü",
        "material_type_label": "Malzeme Türü",
        "material_quantity": "Adet",
        "material_code": "Kod",
        "physical_location_note": "Fiziksel Konum",
    }

    pairs = []
    for key, value in row.items():
        lowered = str(key).lower()
        if lowered in hidden:
            continue
        if value in (None, ""):
            continue
        pairs.append((labels.get(key, key.replace("_", " ").title()), str(value)))

    return pairs


def _da34_document_fields(document: dict) -> list[tuple[str, str]]:
    priority = [
        "id",
        "archive_code",
        "title",
        "document_title",
        "subject",
        "name",
        "document_name",
        "file_name",
        "original_filename",
        "reference_no",
        "reference_number",
        "document_type",
        "confidentiality_level",
        "status",
        "created_at",
        "updated_at",
    ]

    labels = dict(_da34_public_columns(document))
    fields = []

    for key in priority:
        if key in document and document.get(key) not in (None, ""):
            label = dict(_da34_public_columns({key: document.get(key)})).get(key, key)
            fields.append((label, str(document.get(key))))

    used_labels = {label for label, _ in fields}

    for label, value in _da34_public_columns(document):
        if label not in used_labels:
            fields.append((label, value))

    return fields


@digital_archive_bp.route("/documents/<int:document_id>/full-detail", methods=["GET"])
@login_required
def document_full_detail(document_id: int):
    """Belge için birleşik kurumsal detay ekranı."""
    from flask import current_app, flash, redirect, render_template
    from sqlalchemy import select

    try:
        documents_table = _da32_required_table("digital_archive_documents")

        document_row = db.session.execute(
            select(documents_table).where(documents_table.c.id == document_id)
        ).first()

        if not document_row:
            flash("Belge bulunamadı.", "warning")
            return redirect("/digital-archive/documents")

        document = dict(document_row._mapping)
        document = _da36b_enrich_document_row(document)
        document_columns = set(documents_table.c.keys())

        document_label = _da32_row_label(
            document,
            document_columns,
            [
                "title",
                "document_title",
                "subject",
                "name",
                "document_name",
                "file_name",
                "original_filename",
                "reference_no",
                "reference_number",
                "archive_code",
            ],
            "Belge",
        )

        material_links_table = _da34_optional_table(["digital_archive_document_material_links"])
        material_types_table = _da34_optional_table(["digital_archive_material_types"])
        material_rows = _da34_rows_for_document(material_links_table, document_id, limit=300)

        material_map = {}
        if material_types_table is not None and material_rows:
            material_type_rows = [
                dict(row._mapping)
                for row in db.session.execute(select(material_types_table).limit(500)).all()
            ]
            material_columns = set(material_types_table.c.keys())
            material_map = {
                int(row.get("id")): _da32_row_label(
                    row,
                    material_columns,
                    ["name", "title", "material_type", "description"],
                    "Malzeme Türü",
                )
                for row in material_type_rows
                if row.get("id") is not None
            }

        material_cards = []
        for row in material_rows:
            display = dict(row)
            material_type_id = row.get("material_type_id")
            if material_type_id is not None:
                try:
                    display["material_type_label"] = material_map.get(int(material_type_id), f"Malzeme Türü #{material_type_id}")
                except (TypeError, ValueError):
                    display["material_type_label"] = f"Malzeme Türü #{material_type_id}"
            material_cards.append(_da34_public_columns(display))

        history_table = _da34_optional_table([
            "digital_archive_document_history",
            "digital_archive_document_histories",
            "digital_archive_document_audit_events",
            "digital_archive_audit_events",
            "digital_archive_history_events",
        ])

        readable_text_table = _da34_optional_table([
            "digital_archive_document_readable_texts",
            "digital_archive_readable_texts",
            "digital_archive_readable_text_links",
            "digital_archive_ocr_texts",
            "digital_archive_ocr_results",
        ])

        metadata_table = _da34_optional_table([
            "digital_archive_document_metadata_values",
            "digital_archive_dynamic_metadata_values",
            "digital_archive_metadata_values",
            "digital_archive_document_custom_fields",
            "digital_archive_custom_field_values",
        ])

        history_rows = _da34_rows_for_document(history_table, document_id, limit=100)
        readable_text_rows = _da34_rows_for_document(readable_text_table, document_id, limit=50)
        metadata_rows = _da34_rows_for_document(metadata_table, document_id, limit=100)

        sections = [
            {
                "title": "Arşiv Malzemeleri",
                "description": "Belgeye bağlı kutu, klasör, dosya, fotoğraf, harita veya dijital malzeme kayıtları.",
                "rows": material_cards,
                "empty": "Bu belgeye bağlı arşiv malzemesi bulunmuyor.",
            },
            {
                "title": "İşlem Geçmişi",
                "description": "Belge üzerinde yapılan kayıt, güncelleme, görüntüleme, indirme, revizyon veya arşiv işlemleri.",
                "rows": [_da34_public_columns(row) for row in history_rows],
                "empty": "Bu belge için işlem geçmişi kaydı bulunmuyor.",
            },
            {
                "title": "Okunan Metin",
                "description": "Belgeden çıkarılan okunan metin kayıtları.",
                "rows": [_da34_public_columns(row) for row in readable_text_rows],
                "empty": "Bu belge için okunan metin kaydı bulunmuyor.",
            },
            {
                "title": "Ek Bilgiler",
                "description": "Belgeye eklenen özel alan, tarihi alan, konum, envanter ve sınıflandırma bilgileri.",
                "rows": [_da34_public_columns(row) for row in metadata_rows],
                "empty": "Bu belge için ek bilgi kaydı bulunmuyor.",
            },
        ]

        return render_template(
            "digital_archive/document_full_detail.html",
            document=document,
            document_id=document_id,
            document_label=document_label,
            document_fields=_da34_document_fields(document),
            sections=sections,
            material_count=len(material_rows),
            history_count=len(history_rows),
            readable_text_count=len(readable_text_rows),
            metadata_count=len(metadata_rows),
        )

    except Exception:
        db.session.rollback()
        current_app.logger.exception("Belge detay ekranı açılamadı.")
        flash("Belge detay ekranı açılırken beklenmeyen bir sorun oluştu.", "danger")
        return redirect("/digital-archive/documents")













# DA-43B: Rapor merkezi yönetici özeti
def _da43b_table_count(table_names: list[str]) -> int:
    from sqlalchemy import MetaData, Table, func, inspect, select

    inspector = inspect(db.engine)
    existing_tables = set(inspector.get_table_names())

    for table_name in table_names:
        if table_name not in existing_tables:
            continue

        table = Table(table_name, MetaData(), autoload_with=db.engine)
        return int(db.session.execute(select(func.count()).select_from(table)).scalar() or 0)

    return 0


def _da43b_distinct_document_count(table_names: list[str]) -> int:
    from sqlalchemy import MetaData, Table, func, inspect, select

    inspector = inspect(db.engine)
    existing_tables = set(inspector.get_table_names())

    for table_name in table_names:
        if table_name not in existing_tables:
            continue

        table = Table(table_name, MetaData(), autoload_with=db.engine)
        if "document_id" not in table.c:
            continue

        return int(
            db.session.execute(
                select(func.count(func.distinct(table.c.document_id))).select_from(table)
            ).scalar()
            or 0
        )

    return 0


def _da43b_parse_date(value):
    from datetime import datetime

    if value is None:
        return None

    if hasattr(value, "date"):
        try:
            return value.date()
        except Exception:
            return value

    text_value = str(value).strip()
    if not text_value:
        return None

    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%d.%m.%Y",
        "%d.%m.%Y %H:%M",
        "%d/%m/%Y",
        "%d/%m/%Y %H:%M",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(text_value[:19], fmt).date()
        except Exception:
            continue

    return None


def _da43b_retention_date(row: dict):
    date_keys = [
        "retention_until",
        "retention_end_date",
        "retention_date",
        "retention_expires_at",
        "expires_at",
        "archive_until",
        "destroy_after_date",
        "disposal_date",
        "review_date",
        "due_date",
    ]

    for key in date_keys:
        if key in row:
            parsed = _da43b_parse_date(row.get(key))
            if parsed:
                return parsed

    return None


def _da43b_document_rows(limit: int = 500) -> list[dict]:
    from sqlalchemy import select

    table = _da23_document_table()

    statement = select(table)
    if "created_at" in table.c:
        statement = statement.order_by(table.c.created_at.desc())
    elif "id" in table.c:
        statement = statement.order_by(table.c.id.desc())

    rows = []
    for row in db.session.execute(statement.limit(limit)).all():
        rows.append(dict(row._mapping))

    return rows


@digital_archive_bp.get("/reports/executive-summary")
@login_required
def report_executive_summary():
    """Dijital Arşiv raporları için sade yönetici özet ekranı."""
    from datetime import date

    from flask import render_template

    document_rows = _da43b_document_rows()
    enriched_rows = [_da36b_enrich_document_row(row) for row in document_rows]
    status_summary = _da36b_status_summary(enriched_rows)

    document_total = len(document_rows)
    link_total = _da43b_table_count(
        [
            "digital_archive_document_material_links",
            "digital_archive_material_links",
            "digital_archive_document_archive_links",
        ]
    )
    linked_document_total = _da43b_distinct_document_count(
        [
            "digital_archive_document_material_links",
            "digital_archive_material_links",
            "digital_archive_document_archive_links",
        ]
    )
    material_type_total = _da43b_table_count(
        [
            "digital_archive_material_types",
            "digital_archive_archive_materials",
            "digital_archive_materials",
        ]
    )

    today = date.today()
    expired_count = 0
    upcoming_count = 0
    waiting_date_count = 0

    for row in document_rows:
        target_date = _da43b_retention_date(row)
        if not target_date:
            waiting_date_count += 1
            continue

        days_left = (target_date - today).days
        if days_left < 0:
            expired_count += 1
        elif days_left <= 90:
            upcoming_count += 1

    attention_total = expired_count + upcoming_count
    unlinked_document_total = max(document_total - linked_document_total, 0)

    summary_cards = [
        {"label": "Toplam Belge", "value": document_total},
        {"label": "Bağlantı Kaydı", "value": link_total},
        {"label": "Takip Gereken", "value": attention_total},
        {"label": "Durum Başlığı", "value": len(status_summary)},
    ]

    overview_cards = [
        {
            "title": "Belge Yönetimi",
            "value": document_total,
            "description": "Dijital Arşiv bölümünde izlenen toplam belge sayısı.",
            "link": "/digital-archive/documents",
            "link_text": "Belgeleri Aç",
        },
        {
            "title": "Belge Durumları",
            "value": len(status_summary),
            "description": "Belgelerin arşiv sürecindeki durum başlıkları.",
            "link": "/digital-archive/reports/document-status",
            "link_text": "Durum Raporu",
        },
        {
            "title": "Arşiv Bağlantıları",
            "value": link_total,
            "description": "Belge ile arşiv malzemeleri arasında kurulan bağlantı kayıtları.",
            "link": "/digital-archive/reports/archive-links",
            "link_text": "Bağlantı Raporu",
        },
        {
            "title": "Saklama Süresi",
            "value": attention_total,
            "description": "Süresi dolan veya yaklaşan takip başlıkları.",
            "link": "/digital-archive/reports/retention",
            "link_text": "Saklama Raporu",
        },
    ]

    attention_items = [
        {
            "title": "Süresi Dolan Belgeler",
            "value": expired_count,
            "description": "İşlem kararı bekleyebilecek belge kayıtları.",
        },
        {
            "title": "Süresi Yaklaşan Belgeler",
            "value": upcoming_count,
            "description": "Önümüzdeki 90 gün içinde takip edilmesi gereken belge kayıtları.",
        },
        {
            "title": "Tarih Bilgisi Bekleyen Belgeler",
            "value": waiting_date_count,
            "description": "Saklama süresi hesabı için tarih bilgisi bulunmayan belge kayıtları.",
        },
        {
            "title": "Bağlantısız Belgeler",
            "value": unlinked_document_total,
            "description": "Henüz arşiv malzemesi bağlantısı görünmeyen belge kayıtları.",
        },
        {
            "title": "Tanımlı Malzeme Türü",
            "value": material_type_total,
            "description": "Sistemde izlenen arşiv malzemesi türü sayısı.",
        },
    ]

    status_cards = [
        {
            "name": str(item.get("name") or "Kayıtlı"),
            "count": int(item.get("count") or 0),
        }
        for item in status_summary
    ]

    return render_template(
        "digital_archive/report_executive_summary.html",
        summary_cards=summary_cards,
        overview_cards=overview_cards,
        attention_items=attention_items,
        status_cards=status_cards,
    )


# DA-42D: Saklama süresi takip raporu
def _da42d_parse_date(value):
    from datetime import datetime

    if value is None:
        return None

    if hasattr(value, "date"):
        try:
            return value.date()
        except Exception:
            return value

    text_value = str(value).strip()
    if not text_value:
        return None

    formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%d.%m.%Y",
        "%d.%m.%Y %H:%M",
        "%d/%m/%Y",
        "%d/%m/%Y %H:%M",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(text_value[:19], fmt).date()
        except Exception:
            continue

    return None


def _da42d_retention_date(row: dict):
    date_keys = [
        "retention_until",
        "retention_end_date",
        "retention_date",
        "retention_expires_at",
        "expires_at",
        "archive_until",
        "destroy_after_date",
        "disposal_date",
        "review_date",
        "due_date",
    ]

    for key in date_keys:
        if key in row:
            parsed = _da42d_parse_date(row.get(key))
            if parsed:
                return parsed

    return None


def _da42d_document_title(row: dict) -> str:
    for key in ["title", "name", "subject", "document_title", "archive_code", "file_code"]:
        value = row.get(key)
        if value:
            return str(value).strip()

    return "Belge"


@digital_archive_bp.get("/reports/retention")
@login_required
def retention_report():
    """Saklama süresi durumunu sade rapor ekranında gösterir."""
    from datetime import date

    from flask import render_template
    from sqlalchemy import select

    table = _da23_document_table()

    statement = select(table)
    if "created_at" in table.c:
        statement = statement.order_by(table.c.created_at.desc())
    elif "id" in table.c:
        statement = statement.order_by(table.c.id.desc())

    today = date.today()

    rows = []
    for row in db.session.execute(statement.limit(500)).all():
        data = dict(row._mapping)
        rows.append(data)

    expired = []
    upcoming = []
    no_date = []

    for row in rows:
        target_date = _da42d_retention_date(row)
        item = {
            "id": row.get("id") or "-",
            "title": _da42d_document_title(row),
            "date": target_date.strftime("%d.%m.%Y") if target_date else "-",
            "rule": str(row.get("retention_policy_id") or row.get("retention_rule") or "Belirtilmedi"),
        }

        if not target_date:
            no_date.append(item)
            continue

        days_left = (target_date - today).days
        item["days_left"] = days_left

        if days_left < 0:
            expired.append(item)
        elif days_left <= 90:
            upcoming.append(item)

    summary_cards = [
        {"label": "Toplam Belge", "value": len(rows)},
        {"label": "Süresi Dolan", "value": len(expired)},
        {"label": "Yaklaşan", "value": len(upcoming)},
        {"label": "Tarih Bekleyen", "value": len(no_date)},
    ]

    report_items = [
        {
            "title": "Süresi Dolan Belgeler",
            "value": len(expired),
            "description": "Saklama süresi geçmiş görünen ve işlem kararı bekleyen belge kayıtları.",
        },
        {
            "title": "Süresi Yaklaşan Belgeler",
            "value": len(upcoming),
            "description": "Önümüzdeki 90 gün içinde takip edilmesi gereken belge kayıtları.",
        },
        {
            "title": "Tarih Bilgisi Bekleyen Belgeler",
            "value": len(no_date),
            "description": "Saklama süresi hesabı için tarih bilgisi bulunmayan belge kayıtları.",
        },
    ]

    latest_items = expired[:10] + upcoming[:10] + no_date[:10]

    return render_template(
        "digital_archive/retention_report.html",
        summary_cards=summary_cards,
        report_items=report_items,
        latest_items=latest_items[:20],
    )


# DA-42C: Arşiv bağlantı raporu
def _da42c_table_count(table_names: list[str]) -> int:
    from sqlalchemy import MetaData, Table, func, inspect, select

    inspector = inspect(db.engine)
    existing_tables = set(inspector.get_table_names())

    for table_name in table_names:
        if table_name not in existing_tables:
            continue

        table = Table(table_name, MetaData(), autoload_with=db.engine)
        return int(db.session.execute(select(func.count()).select_from(table)).scalar() or 0)

    return 0


def _da42c_distinct_document_count(table_names: list[str]) -> int:
    from sqlalchemy import MetaData, Table, func, inspect, select

    inspector = inspect(db.engine)
    existing_tables = set(inspector.get_table_names())

    for table_name in table_names:
        if table_name not in existing_tables:
            continue

        table = Table(table_name, MetaData(), autoload_with=db.engine)
        if "document_id" not in table.c:
            continue

        return int(
            db.session.execute(
                select(func.count(func.distinct(table.c.document_id))).select_from(table)
            ).scalar()
            or 0
        )

    return 0


def _da42c_latest_link_rows(table_names: list[str], limit: int = 20) -> list[dict[str, str]]:
    from sqlalchemy import MetaData, Table, inspect, select

    inspector = inspect(db.engine)
    existing_tables = set(inspector.get_table_names())

    for table_name in table_names:
        if table_name not in existing_tables:
            continue

        table = Table(table_name, MetaData(), autoload_with=db.engine)

        statement = select(table)
        if "created_at" in table.c:
            statement = statement.order_by(table.c.created_at.desc())
        elif "id" in table.c:
            statement = statement.order_by(table.c.id.desc())

        rows = []
        for row in db.session.execute(statement.limit(limit)).all():
            data = dict(row._mapping)
            rows.append(
                {
                    "document_id": str(data.get("document_id") or "-"),
                    "material_id": str(
                        data.get("material_id")
                        or data.get("archive_material_id")
                        or data.get("material_type_id")
                        or "-"
                    ),
                    "description": str(
                        data.get("description")
                        or data.get("notes")
                        or data.get("relation_note")
                        or "Bağlantı kaydı"
                    ),
                }
            )

        return rows

    return []


@digital_archive_bp.get("/reports/archive-links")
@login_required
def archive_link_report():
    """Arşiv malzemesi bağlantılarını sade rapor ekranında gösterir."""
    from flask import render_template

    link_tables = [
        "digital_archive_document_material_links",
        "digital_archive_material_links",
        "digital_archive_document_archive_links",
    ]

    material_tables = [
        "digital_archive_material_types",
        "digital_archive_archive_materials",
        "digital_archive_materials",
    ]

    document_total = _da42c_table_count(["digital_archive_documents"])
    link_total = _da42c_table_count(link_tables)
    material_total = _da42c_table_count(material_tables)
    linked_document_total = _da42c_distinct_document_count(link_tables)
    latest_links = _da42c_latest_link_rows(link_tables)

    unlinked_document_total = max(document_total - linked_document_total, 0)

    summary_cards = [
        {"label": "Toplam Belge", "value": document_total},
        {"label": "Bağlantı Kaydı", "value": link_total},
        {"label": "Malzeme Türü", "value": material_total},
        {"label": "Bağlantılı Belge", "value": linked_document_total},
    ]

    report_items = [
        {
            "title": "Bağlantılı Belgeler",
            "value": linked_document_total,
            "description": "Arşiv malzemesiyle ilişkilendirilmiş belge sayısı.",
        },
        {
            "title": "Bağlantısız Belgeler",
            "value": unlinked_document_total,
            "description": "Henüz arşiv malzemesi bağlantısı görünmeyen belge sayısı.",
        },
        {
            "title": "Toplam Bağlantı Kaydı",
            "value": link_total,
            "description": "Belge ile kutu, klasör, dosya, fotoğraf, harita veya dijital malzeme arasında kurulan bağlantı sayısı.",
        },
        {
            "title": "Tanımlı Malzeme Türü",
            "value": material_total,
            "description": "Sistemde izlenen arşiv malzemesi türü sayısı.",
        },
    ]

    return render_template(
        "digital_archive/archive_link_report.html",
        summary_cards=summary_cards,
        report_items=report_items,
        latest_links=latest_links,
    )


# DA-42B: Belge durum raporu
def _da42b_status_description(status_name: str) -> str:
    descriptions = {
        "Taslak": "Henüz hazırlık aşamasında olan belge kayıtları.",
        "Kayıtlı": "Sisteme alınmış ve temel bilgileri kayıtlı belgeler.",
        "Arşivde": "Arşiv sürecinde izlenen ve korunacak belge kayıtları.",
        "İncelemede": "Kontrol veya değerlendirme sürecindeki belge kayıtları.",
        "Saklama Süresi Doluyor": "Saklama süresi yaklaşan ve takip edilmesi gereken belge kayıtları.",
        "Saklama Süresi Doldu": "Saklama süresi dolmuş ve işlem kararı bekleyen belge kayıtları.",
        "Devredildi": "İlgili birime veya arşiv sürecine devredilmiş belge kayıtları.",
        "İmha Edildi": "İmha süreci tamamlanmış belge kayıtları.",
    }
    return descriptions.get(status_name, "Bu durumdaki belge kayıtları raporda izlenir.")


@digital_archive_bp.get("/reports/document-status")
@login_required
def document_status_report():
    """Belgeleri durumlarına göre sade rapor ekranında gösterir."""
    from flask import render_template
    from sqlalchemy import select

    table = _da23_document_table()

    statement = select(table)
    if "created_at" in table.c:
        statement = statement.order_by(table.c.created_at.desc())
    elif "id" in table.c:
        statement = statement.order_by(table.c.id.desc())

    rows = []
    for row in db.session.execute(statement.limit(500)).all():
        try:
            data = dict(row._mapping)
        except Exception:
            data = dict(row)

        rows.append(_da36b_enrich_document_row(data))

    status_summary = _da36b_status_summary(rows)
    total_count = len(rows)

    report_items = []
    for item in status_summary:
        name = str(item.get("name") or "Kayıtlı")
        count = int(item.get("count") or 0)
        percent = round((count / total_count) * 100, 1) if total_count else 0

        report_items.append(
            {
                "name": name,
                "count": count,
                "percent": percent,
                "description": _da42b_status_description(name),
            }
        )

    summary_cards = [
        {"label": "Toplam Belge", "value": total_count},
        {"label": "Durum Başlığı", "value": len(report_items)},
        {"label": "Rapor Türü", "value": "Durum"},
        {"label": "Kayıt Limiti", "value": "500"},
    ]

    return render_template(
        "digital_archive/document_status_report.html",
        report_items=report_items,
        summary_cards=summary_cards,
        total_count=total_count,
    )


# DA-42A: Rapor merkezi ana ekranı
@digital_archive_bp.get("/report-center")
@login_required
def report_center():
    """Dijital Arşiv rapor başlıklarını sade bir merkez ekranda gösterir."""
    from flask import render_template

    report_cards = [
        {
            "title": "Yönetici Özeti",
            "description": "Belge, durum, arşiv bağlantısı ve saklama süresi başlıklarının tek yönetici ekranında özetlenmesi.",
            "status": "Hazır",
            "link": "/digital-archive/reports/executive-summary",
        },
        {
            "title": "Belge Durum Özeti",
            "description": "Belgelerin Taslak, Kayıtlı, Arşivde, İncelemede ve diğer durumlara göre izlenmesi.",
            "status": "Hazır",
            "link": "/digital-archive/document-status-guide",
        },
        {
            "title": "Arama ve Bulma Özeti",
            "description": "Belge adı, arşiv kodu, fiziksel konum, arşiv malzemesi ve tarihi alan bilgileriyle arama yaklaşımı.",
            "status": "Hazır",
            "link": "/digital-archive/document-search-guide",
        },
        {
            "title": "Genel Durum Özeti",
            "description": "Dijital Arşiv bölümünde tamamlanan ve sıradaki başlıkların tek ekranda izlenmesi.",
            "status": "Hazır",
            "link": "/digital-archive/module-status",
        },
        {
            "title": "Kullanıcı Yetki Özeti",
            "description": "Kullanıcıların görüntüleme, belge ekleme, düzenleme, rapor ve yönetim sorumluluklarının açıklaması.",
            "status": "Hazır",
            "link": "/digital-archive/permission-guide",
        },
        {
            "title": "Belge Listesi",
            "description": "Kayıtlı belgelerin liste, arama, durum ve işlem bağlantılarıyla izlenmesi.",
            "status": "Hazır",
            "link": "/digital-archive/documents",
        },
        {
            "title": "Yazdırılabilir Belge Özeti",
            "description": "Belge detayından açılan sade çıktı ekranı ile belge bilgilerinin yazdırılması.",
            "status": "Belge içinden açılır",
            "link": "/digital-archive/documents",
        },
        {
            "title": "Saklama Süresi Takibi",
            "description": "Saklama süresi yaklaşan veya dolan belgelerin ayrıca raporlanması için hazırlanacak başlık.",
            "status": "Hazır",
            "link": "/digital-archive/reports/retention",
        },
        {
            "title": "Arşiv Bağlantı Raporu",
            "description": "Kutu, klasör, dosya, fotoğraf, harita ve dijital malzeme bağlantılarının raporlanması için hazırlanacak başlık.",
            "status": "Hazır",
            "link": "/digital-archive/reports/archive-links",
        },
    ]

    summary_cards = [
        {"label": "Hazır Rapor Başlığı", "value": "6"},
        {"label": "Planlanan Rapor Başlığı", "value": "2"},
        {"label": "Rapor Merkezi", "value": "Açık"},
        {"label": "Kullanım Dili", "value": "Sade"},
    ]

    return render_template(
        "digital_archive/report_center.html",
        report_cards=report_cards,
        summary_cards=summary_cards,
    )


# DA-41A: Dijital Arşiv genel durum özeti
@digital_archive_bp.get("/module-status")
@login_required
def module_status():
    """Dijital Arşiv bölümünün genel durumunu sade Türkçe açıklar."""
    from flask import render_template

    completed_items = [
        {
            "title": "Ekran Dili Temizliği",
            "description": "Dijital Arşiv ekranlarında kullanıcıya görünen teknik ve hatalı ifadeler temizlendi.",
            "result": "Tamamlandı",
        },
        {
            "title": "Kullanıcı Akışı",
            "description": "Ana ekran, kullanıcıların belge kaydı ve arşiv bağlantısı adımlarını anlayacağı sıraya getirildi.",
            "result": "Tamamlandı",
        },
        {
            "title": "Belge Durumları",
            "description": "Taslak, Kayıtlı, Arşivde, İncelemede, Devredildi ve İmha Edildi gibi durumlar sade şekilde açıklandı.",
            "result": "Tamamlandı",
        },
        {
            "title": "Arama Rehberi",
            "description": "Belge adı, arşiv kodu, fiziksel konum, arşiv malzemesi, okunan metin ve tarihi alan bilgileriyle arama yaklaşımı açıklandı.",
            "result": "Tamamlandı",
        },
        {
            "title": "Belge Detay Özeti",
            "description": "Belge detay ekranında ilgili işlemlere tek yerden ulaşılabilecek kurumsal özet alanı hazırlandı.",
            "result": "Tamamlandı",
        },
        {
            "title": "Yazdırılabilir Özet",
            "description": "Belgeye ait temel bilgilerin yazdırılabilir sade özet ekranı eklendi.",
            "result": "Tamamlandı",
        },
        {
            "title": "Kullanıcı Yetkileri",
            "description": "Kullanıcıların hangi işlemleri yapabileceğini açıklayan sade yetki rehberi hazırlandı.",
            "result": "Tamamlandı",
        },
    ]

    next_items = [
        {
            "title": "Gerçek Yetki Bağlantısı",
            "description": "Rehberde açıklanan yetkilerin rol matrisiyle daha sıkı bağlanması.",
        },
        {
            "title": "Gelişmiş Arama",
            "description": "Belgeler sayfasındaki arama alanlarının daha kapsamlı filtrelerle güçlendirilmesi.",
        },
        {
            "title": "Rapor Merkezi",
            "description": "Arşiv, saklama süresi, belge durumu ve bağlantı özetlerinin ayrı rapor ekranlarında toplanması.",
        },
        {
            "title": "Kullanım Kontrolü",
            "description": "Kurum personelinin ekranları test ederek eksik veya anlaşılmayan alanları bildirmesi.",
        },
    ]

    summary_cards = [
        {"label": "Tamamlanan Başlık", "value": len(completed_items)},
        {"label": "Sıradaki Başlık", "value": len(next_items)},
        {"label": "Ekran Dili", "value": "Temiz"},
        {"label": "Kullanım Durumu", "value": "Yerel Kontrol"},
    ]

    return render_template(
        "digital_archive/module_status.html",
        completed_items=completed_items,
        next_items=next_items,
        summary_cards=summary_cards,
    )


# DA-40A: Kullanıcı yetki rehberi
@digital_archive_bp.get("/permission-guide")
@login_required
def permission_guide():
    """Dijital Arşiv kullanıcı yetkilerini sade Türkçe açıklamalarla gösterir."""
    from flask import render_template

    permission_groups = [
        {
            "order": "1",
            "title": "Görüntüleme",
            "description": "Belgeleri, belge detayını, arşiv bağlantılarını ve yazdırılabilir özeti görüntüleyebilir.",
            "examples": ["Belgeleri listeleme", "Belge detayını açma", "Yazdırılabilir özeti görüntüleme"],
        },
        {
            "order": "2",
            "title": "Belge Ekleme",
            "description": "Yeni belge kaydı oluşturabilir ve belgeye ait temel bilgileri girebilir.",
            "examples": ["Yeni belge oluşturma", "Başlık ve açıklama bilgisi girme", "Arşiv kodu ekleme"],
        },
        {
            "order": "3",
            "title": "Belge Düzenleme",
            "description": "Kayıtlı belgenin bilgilerini kurum ihtiyacına göre güncelleyebilir.",
            "examples": ["Belge bilgisini düzeltme", "Belge durumunu takip etme", "Eksik bilgileri tamamlama"],
        },
        {
            "order": "4",
            "title": "Arşiv Bağlantısı",
            "description": "Belgeyi kutu, klasör, dosya, fotoğraf, harita veya dijital malzeme ile ilişkilendirebilir.",
            "examples": ["Arşiv malzemesi bağlama", "Malzeme türlerini izleme", "Bağlı bilgileri kontrol etme"],
        },
        {
            "order": "5",
            "title": "Ek Bilgi Yönetimi",
            "description": "Belgelere kurum ihtiyacına göre ek bilgi alanları tanımlayabilir ve bu bilgileri takip edebilir.",
            "examples": ["Özel alan tanımlama", "Tarihi alan bilgilerini ekleme", "Belgeye açıklayıcı bilgi girme"],
        },
        {
            "order": "6",
            "title": "Rapor ve Çıktı",
            "description": "Belge özetlerini, yazdırılabilir sayfaları ve arşiv kontrol çıktısını kullanabilir.",
            "examples": ["Yazdırılabilir belge özeti", "Belge durumu kontrolü", "Arşiv bağlantı özeti"],
        },
        {
            "order": "7",
            "title": "Yönetim",
            "description": "Dijital Arşiv çalışma düzenini, kullanıcı erişimlerini ve kurum içi kullanım kurallarını yönetir.",
            "examples": ["Kullanıcı erişim düzeni", "İşlem sorumluluğu", "Kurum içi kullanım takibi"],
        },
    ]

    return render_template(
        "digital_archive/permission_guide.html",
        permission_groups=permission_groups,
    )


# DA-39A: Yazdırılabilir belge özeti
def _da39a_print_text(value) -> str:
    if value is None:
        return "-"

    if isinstance(value, bool):
        return "Evet" if value else "Hayır"

    if hasattr(value, "strftime"):
        try:
            return value.strftime("%d.%m.%Y %H:%M")
        except Exception:
            return value.strftime("%d.%m.%Y")

    text_value = str(value).strip()
    return text_value if text_value else "-"


def _da39a_document_print_fields(document: dict) -> list[dict[str, str]]:
    preferred_keys = [
        "title",
        "name",
        "subject",
        "archive_code",
        "file_code",
        "document_no",
        "category_id",
        "physical_location_id",
        "retention_policy_id",
        "status_label",
        "confidentiality_level",
        "access_level",
        "created_at",
        "updated_at",
        "description",
        "notes",
    ]

    fields: list[dict[str, str]] = []
    used = set()

    for key in preferred_keys:
        if key not in document:
            continue

        value = _da39a_print_text(document.get(key))
        if value == "-":
            continue

        fields.append(
            {
                "label": _da23_column_label(key),
                "value": value,
            }
        )
        used.add(key)

    if not fields:
        for key, value in document.items():
            if key in {"id", "status_label"}:
                continue

            clean_value = _da39a_print_text(value)
            if clean_value == "-":
                continue

            fields.append(
                {
                    "label": _da23_column_label(key),
                    "value": clean_value,
                }
            )

            if len(fields) >= 10:
                break

    return fields


def _da39a_count_by_document(table_names: list[str], document_id: int) -> int:
    from sqlalchemy import MetaData, Table, func, inspect, select

    inspector = inspect(db.engine)
    existing_tables = set(inspector.get_table_names())

    for table_name in table_names:
        if table_name not in existing_tables:
            continue

        table = Table(table_name, MetaData(), autoload_with=db.engine)
        if "document_id" not in table.c:
            continue

        try:
            return int(
                db.session.execute(
                    select(func.count()).select_from(table).where(table.c.document_id == document_id)
                ).scalar()
                or 0
            )
        except Exception:
            current_app.logger.exception("Yazdırılabilir özet sayım bilgisi alınamadı: %s", table_name)
            return 0

    return 0


@digital_archive_bp.get("/documents/<int:document_id>/print-summary")
@login_required
def document_print_summary(document_id: int):
    """Belge için yazdırılabilir kurumsal özet ekranı."""
    from datetime import datetime

    from flask import current_app, flash, redirect, render_template

    try:
        document = _da24_document_row(document_id)
        if not document:
            flash("Belge bulunamadı.", "warning")
            return redirect("/digital-archive/documents")

        document = _da36b_enrich_document_row(document)
        document_fields = _da39a_document_print_fields(document)

        summary_counts = [
            {
                "title": "Arşiv Bağlantıları",
                "count": _da39a_count_by_document(
                    ["digital_archive_document_material_links"],
                    document_id,
                ),
                "description": "Belgeye bağlı arşiv malzemesi kayıtları.",
            },
            {
                "title": "Dosyalar",
                "count": _da39a_count_by_document(
                    ["digital_archive_document_files", "digital_archive_files"],
                    document_id,
                ),
                "description": "Belgeye bağlı taranmış veya dijital dosyalar.",
            },
            {
                "title": "Ek Bilgiler",
                "count": _da39a_count_by_document(
                    [
                        "digital_archive_document_metadata_values",
                        "digital_archive_metadata_values",
                        "digital_archive_document_field_values",
                    ],
                    document_id,
                ),
                "description": "Belgeye eklenen kuruma özel açıklayıcı bilgiler.",
            },
            {
                "title": "Metin Okuma",
                "count": _da39a_count_by_document(
                    [
                        "digital_archive_document_ocr_texts",
                        "digital_archive_ocr_texts",
                        "digital_archive_document_texts",
                        "digital_archive_recognized_texts",
                    ],
                    document_id,
                ),
                "description": "Belge içeriğinden elde edilen okunan metin kayıtları.",
            },
        ]

        return render_template(
            "digital_archive/document_print_summary.html",
            document=document,
            document_fields=document_fields,
            summary_counts=summary_counts,
            prepared_at=datetime.now().strftime("%d.%m.%Y %H:%M"),
        )
    except Exception:
        current_app.logger.exception("Yazdırılabilir belge özeti açılamadı.")
        flash("Yazdırılabilir belge özeti açılırken beklenmeyen bir sorun oluştu.", "danger")
        return redirect(f"/digital-archive/documents/{document_id}")


# DA-37A: Arama rehberi
@digital_archive_bp.get("/document-search-guide")
@login_required
def document_search_guide():
    """Belge arama yöntemlerini sade Türkçe açıklamalarla gösterir."""
    from flask import render_template

    search_steps = [
        {
            "order": "1",
            "title": "Belge Adı ile Ara",
            "description": "Belgenin başlığı, konusu veya bilinen kısa adı yazılarak kayıt bulunabilir.",
            "example": "Örn. toplantı tutanağı, karar yazısı, fotoğraf listesi",
        },
        {
            "order": "2",
            "title": "Arşiv Kodu ile Ara",
            "description": "Kurumun verdiği arşiv kodu veya dosya numarası biliniyorsa doğrudan bu bilgiyle arama yapılabilir.",
            "example": "Örn. kutu, klasör veya dosya numarası",
        },
        {
            "order": "3",
            "title": "Fiziksel Konum ile Ara",
            "description": "Belgenin bulunduğu oda, raf, kutu, klasör veya dosya bilgisiyle kayıt daraltılabilir.",
            "example": "Örn. Arşiv Odası A, Raf 2, Kutu 4",
        },
        {
            "order": "4",
            "title": "Arşiv Malzemesi ile Ara",
            "description": "Belgenin bağlı olduğu kutu, klasör, fotoğraf, harita, defter veya dijital dosya türü üzerinden ilerlenebilir.",
            "example": "Örn. fotoğraf, harita, klasör, dijital dosya",
        },
        {
            "order": "5",
            "title": "Belge Durumu ile Ara",
            "description": "Taslak, Kayıtlı, Arşivde, İncelemede veya saklama süresiyle ilgili durumlar izlenebilir.",
            "example": "Örn. Arşivde, İncelemede, Saklama Süresi Doluyor",
        },
        {
            "order": "6",
            "title": "Okunan Metin ile Ara",
            "description": "Taranmış belgeden elde edilen okunan metin içinde geçen kelimelerle belgeye ulaşılabilir.",
            "example": "Örn. kişi adı, yer adı, karar konusu",
        },
        {
            "order": "7",
            "title": "Tarihi Alan Bilgileri ile Ara",
            "description": "Muharebe alanı, cephe, şehitlik, anıt, kaynak veya tarihsel not gibi kuruma özel bilgiler kullanılabilir.",
            "example": "Örn. Conkbayırı, Anafartalar, şehitlik adı",
        },
    ]

    return render_template(
        "digital_archive/document_search_guide.html",
        search_steps=search_steps,
    )


# DA-36B: Belge durumu görünür etiketleri
_DA36B_STATUS_LABELS = {
    "": "Kayıtlı",
    "draft": "Taslak",
    "taslak": "Taslak",
    "new": "Taslak",
    "registered": "Kayıtlı",
    "kayitli": "Kayıtlı",
    "kayıtlı": "Kayıtlı",
    "saved": "Kayıtlı",
    "active": "Kayıtlı",
    "aktif": "Kayıtlı",
    "archived": "Arşivde",
    "arsivde": "Arşivde",
    "arşivde": "Arşivde",
    "review": "İncelemede",
    "in_review": "İncelemede",
    "incelemede": "İncelemede",
    "expiring": "Saklama Süresi Doluyor",
    "saklama_suresi_doluyor": "Saklama Süresi Doluyor",
    "saklama süresi doluyor": "Saklama Süresi Doluyor",
    "expired": "Saklama Süresi Doldu",
    "saklama_suresi_doldu": "Saklama Süresi Doldu",
    "saklama süresi doldu": "Saklama Süresi Doldu",
    "transferred": "Devredildi",
    "devredildi": "Devredildi",
    "destroyed": "İmha Edildi",
    "imha_edildi": "İmha Edildi",
    "imha edildi": "İmha Edildi",
}


def _da36b_status_label(value) -> str:
    raw = str(value or "").strip()
    key = raw.lower().replace("-", " ").replace("_", " ")
    compact_key = raw.lower().replace("-", "_").replace(" ", "_")
    return _DA36B_STATUS_LABELS.get(key) or _DA36B_STATUS_LABELS.get(compact_key) or raw or "Kayıtlı"


def _da36b_status_source(row: dict):
    for key in ("status", "document_status", "state", "archive_status"):
        if key in row:
            return row.get(key)
    return ""


def _da36b_enrich_document_row(row):
    if row is None:
        return row

    if isinstance(row, dict):
        data = dict(row)
    elif hasattr(row, "_mapping"):
        data = dict(row._mapping)
    else:
        try:
            data = dict(row)
        except Exception:
            return row

    label = _da36b_status_label(_da36b_status_source(data))
    data["status_label"] = label

    for key in ("status", "document_status", "state", "archive_status"):
        if key in data:
            data[key] = label

    return data


def _da36b_status_summary(rows) -> list[dict[str, object]]:
    counts: dict[str, int] = {}

    for row in rows or []:
        data = row if isinstance(row, dict) else {}
        label = data.get("status_label") or _da36b_status_label(_da36b_status_source(data))
        counts[str(label)] = counts.get(str(label), 0) + 1

    order = [
        "Taslak",
        "Kayıtlı",
        "Arşivde",
        "İncelemede",
        "Saklama Süresi Doluyor",
        "Saklama Süresi Doldu",
        "Devredildi",
        "İmha Edildi",
    ]

    ordered = []
    for name in order:
        if name in counts:
            ordered.append({"name": name, "count": counts.pop(name)})

    for name, count in sorted(counts.items()):
        ordered.append({"name": name, "count": count})

    return ordered



# DA-36A: Belge durumları rehberi
@digital_archive_bp.get("/document-status-guide")
@login_required
def document_status_guide():
    """Belge durumlarını sade Türkçe açıklamalarla gösterir."""
    from flask import render_template

    statuses = [
        {
            "order": "1",
            "name": "Taslak",
            "description": "Belge hazırlık aşamasındadır. Bilgiler tamamlanmadan arşiv sürecine alınmaz.",
            "usage": "Yeni oluşturulan veya bilgileri henüz eksik olan kayıtlar için kullanılır.",
        },
        {
            "order": "2",
            "name": "Kayıtlı",
            "description": "Belge sisteme alınmıştır ve temel bilgileri tamamlanmıştır.",
            "usage": "Belge kaydı tamamlandığında kullanılır.",
        },
        {
            "order": "3",
            "name": "Arşivde",
            "description": "Belge arşiv düzenine alınmış ve konum bilgisiyle takip edilir hale gelmiştir.",
            "usage": "Kutu, klasör, raf veya dijital malzeme bağlantısı yapılmış kayıtlar için kullanılır.",
        },
        {
            "order": "4",
            "name": "İncelemede",
            "description": "Belge üzerinde kontrol, tamamlama veya değerlendirme işlemi devam etmektedir.",
            "usage": "Eksik bilgi, kontrol veya onay bekleyen kayıtlar için kullanılır.",
        },
        {
            "order": "5",
            "name": "Saklama Süresi Doluyor",
            "description": "Belgenin saklama süresi yaklaşmaktadır. Kurum tarafından kontrol edilmesi gerekir.",
            "usage": "Yaklaşan arşiv süresi takibi için kullanılır.",
        },
        {
            "order": "6",
            "name": "Saklama Süresi Doldu",
            "description": "Belgenin belirlenen saklama süresi tamamlanmıştır.",
            "usage": "Devretme, uzatma veya imha değerlendirmesi yapılacak kayıtlar için kullanılır.",
        },
        {
            "order": "7",
            "name": "Devredildi",
            "description": "Belge ilgili arşiv, birim veya kuruma devredilmiştir.",
            "usage": "Kurum içi veya kurum dışı devri tamamlanan kayıtlar için kullanılır.",
        },
        {
            "order": "8",
            "name": "İmha Edildi",
            "description": "Belge, mevzuata ve kurum kararına uygun şekilde imha sürecinden geçirilmiştir.",
            "usage": "İmha işlemi tamamlanan kayıtlar için kullanılır.",
        },
    ]

    return render_template(
        "digital_archive/document_status_guide.html",
        statuses=statuses,
    )


# DA-6C: Dijital Arşiv güvenlik durumu ekranı
@digital_archive_bp.get("/security")
@login_required
def security_status():
    if not _digital_archive_config_enabled():
        return render_template("digital_archive/disabled.html")

    operations = []
    for operation in get_digital_archive_write_operations().values():
        operations.append(
            {
                "key": operation.key,
                "table_name": operation.table_name,
                "draft_route": operation.draft_route,
                "required_permission": operation.required_permission,
                "audit_action": operation.audit_action,
                "csrf_required": operation.csrf_required,
                "transaction_required": operation.transaction_required,
                "whitelist_required": operation.whitelist_required,
                "soft_delete_required": operation.soft_delete_required,
                "field_whitelist": get_digital_archive_field_whitelist(operation.key),
            }
        )

    context = {
        "page_title": "Dijital Arşiv Güvenlik Durumu",
        "page_subtitle": "Bu ekran veri yazma açmadan güvenlik sözleşmesini ve planlanan operasyonları gösterir.",
        "write_enabled": digital_archive_write_is_enabled(),
        "operations": operations,
        "operation_count": len(operations),
        "security_requirements": get_digital_archive_write_security_requirements(),
        "back_url": "/digital-archive/",
    }

    return render_template("digital_archive/security_status.html", **context)

@digital_archive_bp.route("/categories", methods=["POST"])
@login_required
def category_create_guard_only_post():
    """Arşiv kategorisi kaydı oluşturur."""
    from flask import flash, redirect, request
    from sqlalchemy.exc import IntegrityError

    from app import db
    from app.digital_archive.models import DigitalArchiveCategory

    kod = request.form.get("code", "").strip()
    ad = request.form.get("name", "").strip()
    aciklama = request.form.get("description", "").strip()

    if not kod or not ad:
        flash("Kod ve ad alanları zorunludur.", "warning")
        return redirect("/digital-archive/categories/new")

    mevcut = DigitalArchiveCategory.query.filter_by(code=kod).first()
    if mevcut:
        flash("Bu kodla kayıtlı bir arşiv kategorisi zaten var.", "warning")
        return redirect("/digital-archive/categories/new")

    kayit = DigitalArchiveCategory(
        code=kod,
        name=ad,
        description=aciklama or None,
        is_active=True,
    )

    db.session.add(kayit)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        flash("Bu kodla kayıtlı bir arşiv kategorisi zaten var.", "warning")
        return redirect("/digital-archive/categories/new")
    except Exception:
        db.session.rollback()
        flash("Kayıt oluşturulurken beklenmeyen bir sorun oluştu.", "danger")
        return redirect("/digital-archive/categories/new")

    flash("Arşiv kategorisi kaydedildi.", "success")
    return redirect("/digital-archive/categories")

# DA-21D physical location guard-only POST route
@digital_archive_bp.route("/physical-locations", methods=["POST"])
@login_required
def digital_archive_physical_locations_guard_only_post():
    """Fiziksel arşiv konumu kaydı oluşturur."""
    from datetime import datetime

    from flask import flash, redirect, request

    from app import db
    from app.digital_archive.models import DigitalArchivePhysicalLocation

    def temiz_deger(alan: str) -> str | None:
        deger = request.form.get(alan, "").strip()
        return deger or None

    def temiz_sayi(alan: str) -> int | None:
        deger = request.form.get(alan, "").strip()
        if not deger:
            return None
        try:
            return int(deger)
        except ValueError:
            return None

    def temiz_tarih(alan: str):
        deger = request.form.get(alan, "").strip()
        if not deger:
            return None

        for bicim in ("%Y-%m-%d", "%d.%m.%Y", "%Y-%m-%dT%H:%M"):
            try:
                return datetime.strptime(deger, bicim)
            except ValueError:
                continue

        return None

    model_payload = {
        "archive_room": temiz_deger("archive_room"),
        "cabinet_no": temiz_deger("cabinet_no"),
        "shelf_no": temiz_deger("shelf_no"),
        "box_no": temiz_deger("box_no"),
        "folder_no": temiz_deger("folder_no"),
        "file_no": temiz_deger("file_no"),
        "physical_status": temiz_deger("physical_status") or "Arşivde",
        "delivered_to_user_id": temiz_sayi("delivered_to_user_id"),
        "delivered_at": temiz_tarih("delivered_at"),
        "returned_at": temiz_tarih("returned_at"),
    }

    if not any(
        model_payload.get(alan)
        for alan in ("archive_room", "cabinet_no", "shelf_no", "box_no", "folder_no", "file_no")
    ):
        flash("En az bir fiziksel konum bilgisi girilmelidir.", "warning")
        return redirect("/digital-archive/physical-locations/new")

    kayit = DigitalArchivePhysicalLocation(**model_payload)

    db.session.add(kayit)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Kayıt oluşturulurken beklenmeyen bir sorun oluştu.", "danger")
        return redirect("/digital-archive/physical-locations/new")

    flash("Fiziksel arşiv konumu kaydedildi.", "success")
    return redirect("/digital-archive/physical-locations")

# DA-21H2B security-status compatibility alias
@digital_archive_bp.route("/security-status")
@login_required
def security_status_alias_da21h2b():
    """Compatibility alias for /digital-archive/security-status."""
    return security_status()
