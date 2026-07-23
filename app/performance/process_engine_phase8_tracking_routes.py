from __future__ import annotations

import logging
from urllib.parse import urlencode

from flask import abort, redirect, render_template, request
from flask_login import current_user, login_required

from app.route_registry import main_bp
from app.services.performance.process_engine_phase8_tracking import (
    build_process_tracking_workspace,
    can_manage_process_tracking,
    can_view_process_tracking,
    delete_process_tracking_flow,
    delete_visible_process_tracking_flows,
    synchronize_phase8_tracking,
)

logger = logging.getLogger(__name__)


@main_bp.route("/performans/surec-takibi", methods=["GET"])
@main_bp.route("/performance/process-tracking", endpoint="performance_process_tracking")
@login_required
def performance_process_tracking():
    if not can_view_process_tracking(current_user):
        abort(403)
    status_filter = (request.args.get("status") or "all").strip()
    search = (request.args.get("q") or "").strip()

    refresh_done = False
    refresh_summary = None
    if (request.args.get("refresh") or "").strip() == "1":
        sync_result = synchronize_phase8_tracking(limit=500)
        refresh_done = True
        refresh_summary = {
            "checked": sync_result.flows_checked,
            "updated": sync_result.flows_updated,
        }

    workspace = build_process_tracking_workspace(
        current_user,
        status_filter=status_filter,
        search=search,
    )
    workspace["refresh_done"] = refresh_done
    workspace["refresh_summary"] = refresh_summary
    workspace["can_manage_process_tracking"] = can_manage_process_tracking(current_user)
    workspace["deleted_count"] = request.args.get("deleted")
    workspace["delete_error"] = request.args.get("delete_error")
    return render_template("performance/process_engine_tracking.html", **workspace)

def _process_tracking_redirect(**extra):
    params = {
        "status": (request.form.get("status") or request.args.get("status") or "all").strip() or "all",
        "q": (request.form.get("q") or request.args.get("q") or "").strip(),
    }
    params.update({key: value for key, value in extra.items() if value is not None})
    return redirect("/performans/surec-takibi?" + urlencode(params))


@main_bp.route("/performans/surec-takibi/kayit-sil", methods=["POST"])
@login_required
def performance_process_tracking_delete_record():
    if not can_manage_process_tracking(current_user):
        abort(403)
    flow_id = request.form.get("flow_id")
    if not str(flow_id or "").isdigit():
        return _process_tracking_redirect(delete_error="GecersizKayit")
    try:
        deleted = delete_process_tracking_flow(int(flow_id), current_user)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return _process_tracking_redirect(delete_error="SilmeBasarisiz")
    return _process_tracking_redirect(deleted=str(deleted))


@main_bp.route("/performans/surec-takibi/listeyi-temizle", methods=["POST"])
@login_required
def performance_process_tracking_delete_visible_records():
    if not can_manage_process_tracking(current_user):
        abort(403)
    status_filter = (request.form.get("status") or "all").strip() or "all"
    search = (request.form.get("q") or "").strip()
    try:
        deleted = delete_visible_process_tracking_flows(
            current_user,
            status_filter=status_filter,
            search=search,
            limit=300,
        )
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return _process_tracking_redirect(delete_error="SilmeBasarisiz")
    return _process_tracking_redirect(deleted=str(deleted))

# BYS360_PHASE12_ROUTE_ALIAS_REPAIR

# BYS360_PHASE12_ROUTE_ALIAS_STABLE_REPAIR
# BYS360_MAINTENANCE_10E_DUPLICATE_ROUTE_CLEANED
