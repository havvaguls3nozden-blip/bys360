from __future__ import annotations

# BYS360_P1B_MOBILE_ROUTES_SHARED_SPLIT
# Bu dosya artık mobil API endpoint sözleşmesini taşır; ortak yardımcılar shared.py içindedir.
# Amaç: god-file etkisini azaltmak, endpoint/URL sözleşmesini bozmadan P1 mimari temizliğe başlamak.

from app.api.mobile.shared import *  # noqa: F401,F403 - P1B endpoint sözleşmesi için bilinçli facade import

# BYS360_P1C_MOBILE_ROUTES_DOMAIN_SPLIT
from app.api.mobile.domains.auth import *  # noqa: F401,F403 - P1C domain route registration
from app.api.mobile.domains.dashboard import *  # noqa: F401,F403 - P1C domain route registration
from app.api.mobile.domains.personnel_read import *  # noqa: F401,F403 - P1C domain route registration
from app.api.mobile.domains.notifications import *  # noqa: F401,F403 - P1C domain route registration
from app.api.mobile.domains.support_survey_write import *  # noqa: F401,F403 - P1C domain route registration


# BYS360_P1D_MOBILE_ROUTES_COMM_ASSISTANT_SPLIT
from app.api.mobile.domains.communication_v1_write import *  # noqa: F401,F403 - P1D domain route registration
from app.api.mobile.domains.communication_v2_write import *  # noqa: F401,F403 - P1D domain route registration
from app.api.mobile.domains.assistant_chat import *  # noqa: F401,F403 - P1D domain route registration


# BYS360_P1E_MOBILE_ROUTES_PERSONNEL_KPI_SPLIT
from app.api.mobile.domains.personnel_write_all import *  # noqa: F401,F403 - P1E domain route registration
from app.api.mobile.domains.kpi_target_management import *  # noqa: F401,F403 - P1E domain route registration

# BYS360_MOBILE_V2_8_43_PERSONNEL_ALL_API

# BYS360 P1.7 service delegation - legacy implementation preserved
def _bys360_legacy_mobile_personnel_all(user: User):
    # Mobil personel listesi web uygulamasındaki canlı User/personel verisinin tamamını çeker.
    # Eski mobil listede kalan sabit 50 kayıt sınırını bypass eder; yetki kapsamı korunur.
    global_scope = _has_global_scope(user)

    def _arg_int(*names, default=0):
        for name in names:
            raw = request.args.get(name)
            if raw is None or str(raw).strip() == "":
                continue
            try:
                return int(float(raw))
            except Exception:
                __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/api/mobile/routes.py:1238)")
                continue
        return default

    requested_limit = _arg_int("limit", "length", "per_page", default=10000)
    limit = max(1, min(10000, requested_limit))
    page = max(1, _arg_int("page", default=1))
    offset = max(0, _arg_int("offset", "start", default=(page - 1) * limit))
    query_text = (request.args.get("q") or request.args.get("search") or request.args.get("query") or "").strip().lower()

    q = User.query.filter_by(is_active=True) if global_scope else User.query.filter_by(id=user.id)
    try:
        total_before_search = _safe_count(q)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/api/mobile/routes.py:56")
        total_before_search = 0

    try:
        records = q.order_by(User.ad.asc(), User.soyad.asc()).all()
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/api/mobile/routes.py:61")
        records = q.all()

    def _txt(value):
        text = str(value or "").strip()
        return "" if text.lower() == "none" else text

    def _uv(u, *attrs):
        for attr in attrs:
            text = _txt(getattr(u, attr, None))
            if text:
                return text
        return ""

    def _row(u):
        full_name = _full_name(u)
        unit_name = _uv(u, "birim", "unit_name", "organization_unit_name", "department")
        upper_unit = _uv(u, "ust_birim", "upper_unit_name", "parent_unit_name")
        registry = _uv(u, "sicil_no", "registry_no", "sicil", "employee_no")
        title = _uv(u, "unvan", "title", "title_name", "position_title", "job_title")
        duty = _uv(u, "gorev", "duty", "duty_name", "position", "role_name")
        manager = _uv(u, "manager_name", "yonetici", "supervisor_name", "first_manager_name", "amir")
        category = _uv(u, "personnel_category", "category", "kategori")
        role_label = _uv(u, "role_label", "role")
        active = bool(getattr(u, "is_active", False))
        return {
            "id": getattr(u, "id", None),
            "user_id": getattr(u, "id", None),
            "full_name": full_name,
            "display_name": full_name,
            "ad_soyad": full_name,
            "first_name": _uv(u, "ad", "first_name"),
            "last_name": _uv(u, "soyad", "last_name"),
            "registry_no": registry,
            "sicil_no": registry,
            "unit_name": unit_name,
            "birim": unit_name,
            "upper_unit_name": upper_unit,
            "ust_birim": upper_unit,
            "title_name": title,
            "unvan": title,
            "duty_name": duty,
            "gorev": duty,
            "manager_name": manager,
            "personnel_category": category,
            "category": category,
            "role_label": role_label,
            "role": _uv(u, "role"),
            "status_label": "Aktif" if active else "Pasif",
            "status": "Aktif" if active else "Pasif",
            "is_active": active,
            "subtitle": f"{unit_name or upper_unit or 'Birim yok'} / Sicil {registry or '-'}",
            "meta": category or title,
            "value": role_label,
        }

    rows = [_row(u) for u in records]
    if query_text:
        def _haystack(row):
            return " ".join(str(v or "") for v in row.values()).lower()
        rows = [row for row in rows if query_text in _haystack(row)]

    total = len(rows)
    selected = rows[offset: offset + limit]
    has_more = offset + limit < total

    items = []
    for row in selected:
        item = _item(
            row.get("id"),
            row.get("full_name") or "Personel",
            row.get("subtitle") or "",
            row.get("status_label") or "",
            row.get("meta") or "",
            row.get("value") or "",
            100 if row.get("is_active") else 0,
        )
        item.update(row)
        items.append(item)

    return jsonify({
        "source": "web_personnel_user_table_all",
        "can_create_personnel": _can_mobile_create_personnel(user),
        "scope": "Genel" if global_scope else "Kendi kaydım",
        "total": total,
        "total_count": total,
        "recordsTotal": total,
        "count": total,
        "all_active_count": total_before_search,
        "limit": limit,
        "offset": offset,
        "page": page,
        "has_more": has_more,
        "metrics": [
            _metric("Aktif Personel", total, "Yetkinize göre görünen tüm kayıt", "red", "people"),
            _metric("Kapsam", "Genel" if global_scope else "Kendi kaydım", "Rol ve menü görünürlüğüne bağlı", "red", "shield"),
            _metric("Mobil Liste", "Tümü", "50 kayıt sınırı kaldırıldı", "red", "all_inclusive"),
        ],
        "items": items,
        "rows": selected,
        "personnel": selected,
    })
# BYS360_MOBILE_V2_8_62_PERSONNEL_ROUTE_MARKER

# BYS360_MOBILE_V2_8_64_NOTIFICATIONS_COMPLETION

# BYS360_MOBILE_V2_8_65_SUPPORT_COMPLETION


# BYS360_MOBILE_V2_8_66_SURVEY_COMPLETION | Android anket cevaplama ekranları kullanıcı diliyle tamamlandı.


# BYS360_MOBILE_V2_8_67_ASSISTANT_CHAT_COMPLETION | Android BYS360 Asistanı sohbet ekranı kurumsal kullanıcı diliyle tamamlandı.

# BYS360_MOBILE_V2_8_72_REFRESH_BACKEND

# BYS360 P11-B2: utility mobile routes bridge
from app.api.mobile.utility_routes import register_mobile_utility_routes_v1 as _register_mobile_utility_routes_v1
# BYS360_P14F1_MOBILE_BLUEPRINT_RESOLVER_START
def _bys360_resolve_mobile_blueprint_for_utility_routes_v1():
    for _name in ("mobile_bp", "mobile_api_bp", "bp"):
        _candidate = globals().get(_name)
        if hasattr(_candidate, "route") and hasattr(_candidate, "add_url_rule"):
            return _candidate

    for _candidate in globals().values():
        if not (hasattr(_candidate, "route") and hasattr(_candidate, "add_url_rule")):
            continue
        _bp_name = str(getattr(_candidate, "name", "") or "").lower()
        if _bp_name.startswith(("mobile", "api_mobile", "mobile_api")):
            return _candidate

    raise RuntimeError("BYS360 mobile API Blueprint could not be resolved for utility route registration")


_bys360_mobile_utility_bp_v1 = _bys360_resolve_mobile_blueprint_for_utility_routes_v1()
# BYS360_P14F1_MOBILE_BLUEPRINT_RESOLVER_END

# BYS360_P14F2_MOBILE_ROUTE_REGISTRAR_ADAPTER_START
def _bys360_call_mobile_route_registrar_v1(_registrar, _bp, _registry=None):
    try:
        return _registrar(_bp, _registry if _registry is not None else globals())
    except TypeError as _two_arg_error:
        try:
            return _registrar(_bp)
        except TypeError:
            raise _two_arg_error
# BYS360_P14F2_MOBILE_ROUTE_REGISTRAR_ADAPTER_END
_register_mobile_utility_routes_v1(_bys360_mobile_utility_bp_v1, globals())

# BYS360 P11-B3: light read mobile routes bridge
from app.api.mobile.light_read_routes import register_mobile_light_read_routes_v1 as _register_mobile_light_read_routes_v1
_bys360_call_mobile_route_registrar_v1(_register_mobile_light_read_routes_v1, _bys360_mobile_utility_bp_v1, globals())

# BYS360 P11-B4: detail read mobile routes bridge
from app.api.mobile.detail_read_routes import register_mobile_detail_read_routes_v1 as _register_mobile_detail_read_routes_v1
_bys360_call_mobile_route_registrar_v1(_register_mobile_detail_read_routes_v1, _bys360_mobile_utility_bp_v1, globals())

# BYS360 P11-B5: support/survey read mobile routes bridge
from app.api.mobile.support_survey_read_routes import register_mobile_support_survey_read_routes_v1 as _register_mobile_support_survey_read_routes_v1
_bys360_call_mobile_route_registrar_v1(_register_mobile_support_survey_read_routes_v1, _bys360_mobile_utility_bp_v1, globals())

# BYS360 P11-B6: communication read mobile routes bridge
from app.api.mobile.communication_read_routes import register_mobile_communication_read_routes_v1 as _register_mobile_communication_read_routes_v1
_bys360_call_mobile_route_registrar_v1(_register_mobile_communication_read_routes_v1, _bys360_mobile_utility_bp_v1, globals())

# BYS360 P11-B7: communication v2 read mobile route bridge
from app.api.mobile.communication_v2_read_routes import register_mobile_communication_v2_read_routes_v1 as _register_mobile_communication_v2_read_routes_v1
_bys360_call_mobile_route_registrar_v1(_register_mobile_communication_v2_read_routes_v1, _bys360_mobile_utility_bp_v1, globals())

# BYS360 P11-B9: performance read mobile routes bridge
from app.api.mobile.performance_read_routes import register_mobile_performance_read_routes_v1 as _register_mobile_performance_read_routes_v1
from app.api.mobile.services import support_service as _mobile_support_service
_bys360_call_mobile_route_registrar_v1(_register_mobile_performance_read_routes_v1, _bys360_mobile_utility_bp_v1, globals())

