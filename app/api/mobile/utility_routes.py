from __future__ import annotations

# ruff: noqa: F821 - mobile bridge routes resolve legacy names from route_globals at registration time.

# BYS360 mobile utility route bridge module.
# P11-B2 kapsamında düşük riskli mobil utility GET endpointleri ayrılmıştır.
# URL path ve JSON cevap davranışı değiştirilmemelidir.

def register_mobile_utility_routes_v1(mobile_bp, route_globals) -> None:
    """Register low-risk mobile utility routes on the existing mobile blueprint."""
    if route_globals.get("_BYS360_P11_B2_UTILITY_ROUTES_REGISTERED"):
        return

    route_globals['mobile_bp'] = mobile_bp
    route_globals.setdefault('mobile_api_bp', mobile_bp)
    globals().update(route_globals)

    @mobile_api_bp.get("/health")
    def mobile_health():
        return jsonify({"ok": True, "service": "BYS360 Mobile API", "source": "real_api"})

    @mobile_api_bp.get("/kpi/goals")
    @require_mobile_user
    def mobile_kpi_goals(user: User):
        items = []
        active = 0
        avg_rate = 0
        if PerformanceTarget is not None:
            try:
                q = PerformanceTarget.query.order_by(PerformanceTarget.updated_at.desc().nullslast())
                # BYS360 SECURITY FIX (Defect P): reuse the same PerformanceTarget
                # visibility contract as GET /kpi/target-management -- global-scope
                # callers keep the unscoped view, everyone else is restricted to
                # their own owner_user_id. Applied before both the row list AND
                # the active-count metric so neither leaks organization-wide data.
                if not _has_global_scope(user) and hasattr(PerformanceTarget, "owner_user_id"):
                    q = q.filter(PerformanceTarget.owner_user_id == int(getattr(user, "id", 0) or 0))
                active = _safe_count(q)
                rates = []
                for t in q.limit(40).all():
                    rate = _as_int(getattr(t, "completion_rate", 0))
                    rates.append(rate)
                    items.append(_item(t.id, getattr(t, "target_name", "Hedef"), getattr(t, "description", "") or getattr(t, "category", ""), getattr(t, "status", ""), getattr(t, "risk_level", ""), f"%{rate}", rate))
                avg_rate = int(mean(rates)) if rates else 0
            except Exception:
                __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/api/mobile/routes.py:820)")
        return _module_payload([
            _metric("Aktif Hedef", active, "SP-1 hedef kartlarından okunur", "green", "flag"),
            _metric("Ortalama Başarı", f"%{avg_rate}", "Gerçekleşme ortalaması", "green", "trending_up"),
            _metric("Kaynak", "SP-1", "KPI/Hedef motoru", "green", "api"),
        ], items)

    route_globals["_BYS360_P11_B2_UTILITY_ROUTES_REGISTERED"] = True
