from __future__ import annotations



from typing import Any

from app.config.live_scope import get_live_scope_summary


_AREA_LABELS: dict[str, str] = {
    "dashboard": "Dashboard",
    "personel_yetki": "Personel ve Yetki",
    "organizasyon_hiyerarsi": "Organizasyon ve Hiyerarşi",
    "performance": "Performans Yönetimi",
    "izin_vekalet": "İzin ve Vekâlet",
    "iletisim_bildirim": "İletişim ve Bildirim",
    "raporlama_karar_destek": "Temel Raporlar ve Karar Destek",
}

_REMOVED_LABELS: dict[str, str] = {
    "repository": "Belge–Medya",
    "education": "Eğitim",
    "strategy": "Strateji",
    "portal": "İç Portal",
}


def _area_label(key: str) -> str:
    return _AREA_LABELS.get(str(key or '').strip(), str(key or '').replace('_', ' ').title())


def _removed_label(key: str) -> str:
    return _REMOVED_LABELS.get(str(key or '').strip(), str(key or '').replace('_', ' ').title())


def build_live_dashboard_surface_context(context: dict[str, Any] | None = None) -> dict[str, Any]:
    context = dict(context or {})
    summary = get_live_scope_summary()
    active_core = [
        {
            "title": _area_label(area),
            "note": "Canlı kullanıcı yüzeyinde aktif tutulur.",
        }
        for area in (summary.get("active_core_areas") or [])
    ]
    return {
        "headline": "Canlı kapsam özeti",
        "subtitle": "Dashboard yalnız çekirdek omurgayı ve aktif karar yüzeylerini gösterir.",
        "chips": [
            {"label": "Aktif çekirdek", "value": int(summary.get("active_core_count") or 0)},
            {"label": "Bekleyen onay", "value": int(context.get("pending_feedback_requests") or 0)},
            {"label": "Kapsama riski", "value": int(context.get("coverage_risk_score") or 0)},
        ],
        "active_core": active_core,
        "removed_modules": [],
    }


def build_live_report_surface_context(*, scope: dict[str, Any] | None = None, stats: dict[str, Any] | None = None, selected_period: Any = None) -> dict[str, Any]:
    summary = get_live_scope_summary()
    stats = dict(stats or {})
    scope = dict(scope or {})
    exports = [
        {"title": "Excel", "note": "Temel performans listesini dışa aktarır."},
        {"title": "PDF Özeti", "note": "Seçili görünümün yönetici özetini üretir."},
        {"title": "Liste Yazdır", "note": "Kurumsal yazdırma görünümünü açar."},
    ]
    focus_rows = [
        {"title": "Seçili kapsam", "value": scope.get("scope_label") or "Kurum geneli"},
        {"title": "Görünür personel", "value": int(scope.get("scope_user_count") or 0)},
        {"title": "Toplam dönem", "value": int(stats.get("total_periods") or 0)},
        {"title": "Yayındaki dönem", "value": int(stats.get("published_period_count") or 0)},
        {"title": "Rapor odağı", "value": getattr(selected_period, 'title', None) or 'Tüm dönemler'},
    ]
    return {
        "headline": "Canlı rapor yüzeyi",
        "subtitle": "Rapor alanı yalnız performans çekirdeği, kapsama logları ve temel dışa aktarma seçenekleriyle sınırlandırıldı. Geniş raporlama varyasyonları sonraki modül fazına bırakıldı.",
        "exports": exports,
        "focus_rows": focus_rows,
        "removed_modules": [_removed_label(module) for module in (summary.get("removed_modules") or [])],
    }
