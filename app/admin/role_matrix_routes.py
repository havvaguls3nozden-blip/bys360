
"""BYS360 Rol Matrisi yönetim ekranı rotaları.

Faz 3: Ayarlar/Yetkilendirme modülü altında rol matrisi ve menü görünürlüğü
politikasını okunabilir, denetlenebilir bir UI omurgasına taşır.
"""
from __future__ import annotations

from flask import request
from flask_login import login_required

from app.route_registry import main_bp
from app.route_support import admin_required, safe_render
from app.services.role_matrix_ui_service import build_role_matrix_ui_context


@main_bp.route("/admin/role-matrix")
@login_required
@admin_required
def admin_role_matrix_center():
    selected_module = request.args.get("module", "tum")
    context = build_role_matrix_ui_context(selected_module)
    return safe_render(
        "admin/role_matrix_center.html",
        "<h3>BYS360 Rol Matrisi</h3><p>Rol Matrisi ekranı yüklenemedi.</p>",
        **context,
    )
