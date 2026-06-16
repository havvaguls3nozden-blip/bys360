from __future__ import annotations

# STATUS: ACTIVE
# BYS360_ROUTE_STATUS: ACTIVE_REQUIRED
# STATUS_SOURCE: app.admin.route_manifest REQUIRED_ROUTE_MODULES

from flask import flash, redirect, request, url_for
from flask_login import login_required

from app.route_registry import main_bp
from app.route_support import admin_required, menu_key_required, safe_render
from app.services.ai.localization import ai_feature_label, ai_module_label
from app.services.ai.prompts import (
    delete_prompt_registry_entry,
    get_prompt_registry_editor_snapshot,
    upsert_prompt_registry_entry,
)
from app.services.ai.settings import build_ai_settings_snapshot


def _option_rows(values: list[str], label_func) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for value in values:
        key = str(value or '').strip()
        if not key or key in seen:
            continue
        seen.add(key)
        rows.append({'value': key, 'label': label_func(key)})
    return rows


@main_bp.route("/admin/ai-settings")
@login_required
@admin_required
@menu_key_required("ai_center")
def admin_ai_settings():
    snapshot = build_ai_settings_snapshot()
    editor = get_prompt_registry_editor_snapshot(
        request.args.get("module_type", ""),
        request.args.get("feature_type", ""),
    )
    selected_module = str(editor.get("module_type") or "")
    selected_feature = str(editor.get("feature_type") or "")
    selected_label = (
        f"{ai_module_label(selected_module)} / {ai_feature_label(selected_feature)}"
        if selected_module and selected_feature
        else "Yeni kayıt"
    )

    prompt_rows = snapshot.get("prompt_rows") or []
    module_values = sorted({str(row.get("module_type") or "").strip() for row in prompt_rows if str(row.get("module_type") or "").strip()})
    feature_values = sorted({str(row.get("feature_type") or "").strip() for row in prompt_rows if str(row.get("feature_type") or "").strip()})

    if selected_module and selected_module not in module_values:
        module_values.append(selected_module)
    if selected_feature and selected_feature not in feature_values:
        feature_values.append(selected_feature)

    return safe_render(
        "admin_ai_settings.html",
        snapshot=snapshot,
        provider=snapshot.get("provider") or {},
        prompt_rows=prompt_rows,
        prompt_meta=snapshot.get("prompt_meta") or {},
        allowed_roles=snapshot.get("allowed_roles") or [],
        env_rows=snapshot.get("env_rows") or [],
        actions=snapshot.get("actions") or [],
        editor=editor,
        selected_label=selected_label,
        module_options=_option_rows(module_values, ai_module_label),
        feature_options=_option_rows(feature_values, ai_feature_label),
    )


@main_bp.route("/admin/ai-settings/prompt-upsert", methods=["POST"])
@login_required
@admin_required
@menu_key_required("ai_center")
def admin_ai_settings_prompt_upsert():
    module_type = str(request.form.get("module_type") or "").strip()
    feature_type = str(request.form.get("feature_type") or "").strip()
    version = str(request.form.get("version") or "").strip()
    system = str(request.form.get("system") or "").strip()

    try:
        saved = upsert_prompt_registry_entry(
            module_type=module_type,
            feature_type=feature_type,
            version=version,
            system=system,
        )
    except ValueError as exc:
        flash(str(exc), "warning")
        return redirect(
            url_for(
                "main.admin_ai_settings",
                module_type=module_type,
                feature_type=feature_type,
            )
        )
    except OSError:
        flash("İstem kaydı dosyaya yazılamadı. Dosya izinlerini kontrol edin.", "danger")
        return redirect(url_for("main.admin_ai_settings"))

    flash(
        f"İstem kaydı güncellendi: {ai_module_label(saved['module_type'])} / {ai_feature_label(saved['feature_type'])}",
        "success",
    )
    return redirect(
        url_for(
            "main.admin_ai_settings",
            module_type=saved["module_type"],
            feature_type=saved["feature_type"],
        )
    )


@main_bp.route("/admin/ai-settings/prompt-delete", methods=["POST"])
@login_required
@admin_required
@menu_key_required("ai_center")
def admin_ai_settings_prompt_delete():
    module_type = str(request.form.get("module_type") or "").strip()
    feature_type = str(request.form.get("feature_type") or "").strip()

    if not module_type or not feature_type:
        flash("Silinecek kayıt seçilemedi.", "warning")
        return redirect(url_for("main.admin_ai_settings"))

    try:
        removed = delete_prompt_registry_entry(module_type=module_type, feature_type=feature_type)
    except OSError:
        flash("Kayıt dosyası güncellenemedi. Dosya izinlerini kontrol edin.", "danger")
        return redirect(
            url_for(
                "main.admin_ai_settings",
                module_type=module_type,
                feature_type=feature_type,
            )
        )

    if removed:
        flash(f"Kayıt dosyası kaydı silindi: {ai_module_label(module_type)} / {ai_feature_label(feature_type)}", "success")
    else:
        flash("Bu kayıt yerleşik olduğu için silinecek ayrı bir kayıt dosyası girdisi bulunamadı.", "info")

    return redirect(url_for("main.admin_ai_settings"))