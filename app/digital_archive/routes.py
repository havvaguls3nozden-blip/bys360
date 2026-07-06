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
