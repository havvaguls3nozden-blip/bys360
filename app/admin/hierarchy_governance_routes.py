from __future__ import annotations



import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from flask import Blueprint, current_app, flash, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required

from app.services.hierarchy_excel_preview_service import HierarchyExcelPreviewService
from app.services.hierarchy_settings_service import HierarchySettingsService


hierarchy_governance_bp = Blueprint(
    "hierarchy_governance",
    __name__,
    url_prefix="/admin/hierarchy-governance",
    template_folder="../templates",
)


def _is_admin_like() -> bool:
    return getattr(current_user, "role", "") in {"admin", "baskan", "baskan_yardimcisi"}


@hierarchy_governance_bp.before_request
@login_required
def require_access():
    if not _is_admin_like():
        flash("Bu ekrana erişim yetkiniz yok.", "danger")
        return redirect(url_for("main.index"))


@hierarchy_governance_bp.get("")
def settings_panel():
    service = HierarchySettingsService()
    config = service.load()
    preview_summary = current_app.config.get("HIERARCHY_PREVIEW_LAST_SUMMARY")
    return render_template("admin/hierarchy_governance.html", config=config, preview_summary=preview_summary)


@hierarchy_governance_bp.post("/save")
def save_settings():
    service = HierarchySettingsService()
    config = service.load()
    config["default_weights"] = {
        "manager_1": int(request.form.get("manager_1", config["default_weights"]["manager_1"])),
        "manager_2": int(request.form.get("manager_2", config["default_weights"]["manager_2"])),
        "manager_3": int(request.form.get("manager_3", config["default_weights"]["manager_3"])),
    }
    config["third_manager_defaults"] = {
        "enabled": request.form.get("third_enabled") == "on",
        "mode": request.form.get("third_mode", config["third_manager_defaults"]["mode"]),
    }
    service.save(config)
    flash("Amir zinciri ayarları kaydedildi.", "success")
    return redirect(url_for("hierarchy_governance.settings_panel"))


@hierarchy_governance_bp.post("/preview")
def preview_excel():
    uploaded = request.files.get("excel_file")
    if not uploaded or not uploaded.filename:
        flash("Önizleme için Excel dosyası seçin.", "warning")
        return redirect(url_for("hierarchy_governance.settings_panel"))

    with NamedTemporaryFile(delete=False, suffix=Path(uploaded.filename).suffix or ".xlsx") as tmp:
        uploaded.save(tmp.name)
        service = HierarchyExcelPreviewService(report_dir=Path(current_app.root_path).parent / "reports" / "faz3_6")
        summary = service.preview_excel(tmp.name)

    current_app.config["HIERARCHY_PREVIEW_LAST_SUMMARY"] = summary
    flash("Excel önizleme raporu üretildi.", "success")
    return redirect(url_for("hierarchy_governance.settings_panel"))


@hierarchy_governance_bp.get("/download-last-json")
def download_last_json():
    summary = current_app.config.get("HIERARCHY_PREVIEW_LAST_SUMMARY")
    if not summary:
        flash("İndirilecek önizleme raporu yok.", "warning")
        return redirect(url_for("hierarchy_governance.settings_panel"))
    return send_file(summary["json_path"], as_attachment=True)