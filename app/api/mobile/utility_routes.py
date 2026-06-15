from __future__ import annotations

# BYS360 mobile utility route bridge module.
# P11-B2 kapsamında düşük riskli mobil utility GET endpointleri ayrılmıştır.
# URL path ve JSON cevap davranışı değiştirilmemelidir.

_UTILITY_ROUTE_SOURCE = '@mobile_api_bp.get("/health")\ndef mobile_health():\n    return jsonify({"ok": True, "service": "BYS360 Mobile API", "source": "real_api"})\n\n@mobile_api_bp.get("/kpi/goals")\n@require_mobile_user\ndef mobile_kpi_goals(user: User):\n    items = []\n    active = 0\n    avg_rate = 0\n    if PerformanceTarget is not None:\n        try:\n            q = PerformanceTarget.query.order_by(PerformanceTarget.updated_at.desc().nullslast())\n            active = _safe_count(q)\n            rates = []\n            for t in q.limit(40).all():\n                rate = _as_int(getattr(t, "completion_rate", 0))\n                rates.append(rate)\n                items.append(_item(t.id, getattr(t, "target_name", "Hedef"), getattr(t, "description", "") or getattr(t, "category", ""), getattr(t, "status", ""), getattr(t, "risk_level", ""), f"%{rate}", rate))\n            avg_rate = int(mean(rates)) if rates else 0\n        except Exception:\n            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/api/mobile/routes.py:820)")\n    return _module_payload([\n        _metric("Aktif Hedef", active, "SP-1 hedef kartlarından okunur", "green", "flag"),\n        _metric("Ortalama Başarı", f"%{avg_rate}", "Gerçekleşme ortalaması", "green", "trending_up"),\n        _metric("Kaynak", "SP-1", "KPI/Hedef motoru", "green", "api"),\n    ], items)\n'


def register_mobile_utility_routes_v1(mobile_bp, route_globals: dict) -> None:
    """Register low-risk mobile utility routes on the existing mobile blueprint."""
    if route_globals.get("_BYS360_P11_B2_UTILITY_ROUTES_REGISTERED"):
        return

    route_globals["mobile_bp"] = mobile_bp
    exec(_UTILITY_ROUTE_SOURCE, route_globals, route_globals)
    route_globals["_BYS360_P11_B2_UTILITY_ROUTES_REGISTERED"] = True
