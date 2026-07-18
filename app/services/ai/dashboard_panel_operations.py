from __future__ import annotations

# Bu dosya app.services.ai.dashboard_panels dış public API'sini bozmadan ayrıştırılmıştır.
from app.services.ai.dashboard_panel_common import (
    logging,
    THIRD_MANAGER_STANDARD_KEY,
    THIRD_MANAGER_HEADER_ALIASES,
    Any,
    Iterable,
    unicodedata,
    current_app,
    url_for,
    func,
    BuildError,
    db,
    AIFeedbackLog,
    AIRecommendation,
    AIRequestLog,
    AISummaryCache,
    get_ai_schema_status,
    _get,
    _to_int,
    _to_float,
    _tone_from_counts,
    _badge_from_tone,
    _top_reason_pairs,
    _normalize_text,
    _is_informational_hierarchy_reason,
    _extract_hierarchy_issue_messages,
    _has_real_hierarchy_warning,
    _is_hierarchy_missing_exempt,
    _has_first_manager_binding,
    _has_level_3_binding,
    _safe_url_for,
    _safe_len,
    _safe_bool,
    _safe_title_case,
    _compose_standard_panel,
)

DASHBOARD_AI_MODULE_META = [
    {"module_type": "performance", "label": "Performans AI", "page_label": "Performans görünümü", "page_href": "main.performance_reports", "icon": "fa-chart-line"},
    {"module_type": "dashboard", "label": "Dashboard AI", "page_label": "Dashboard", "page_href": "main.dashboard", "icon": "fa-gauge-high"},
    {"module_type": "hr", "label": "Personel / İzin AI", "page_label": "Personel raporları", "page_href": "main.hr_reports", "icon": "fa-user-clock"},
    {"module_type": "communication", "label": "İletişim AI", "page_label": "Bildirimler", "page_href": "main.notifications_list", "icon": "fa-bell"},
    {"module_type": "survey", "label": "Anket AI", "page_label": "Anketler", "page_href": "main.surveys", "icon": "fa-square-poll-vertical"},
    {"module_type": "feedback", "label": "Geri Bildirim AI", "page_label": "Geri bildirim", "page_href": "main.feedback_dashboard", "icon": "fa-comments"},
    {"module_type": "support", "label": "Destek AI", "page_label": "Yardım merkezi", "page_href": "main.support_index", "icon": "fa-headset"},
]


def build_dashboard_ai_operations_bridge(*, can_view_admin_ai: bool = False) -> dict[str, Any] | None:
    schema_status = get_ai_schema_status()
    if not schema_status.get("ready"):
        return {
            "badge": "Korumalı mod",
            "tone": "muted",
            "headline": "AI operasyon görünümü korumalı moda alındı",
            "summary": schema_status.get("message") or "AI şeması hazır olmadığı için ortak AI kartları pasif gösteriliyor.",
            "totals": {
                "requests": 0,
                "open_recommendations": 0,
                "negative_feedback": 0,
                "unmasked_requests": 0,
                "summary_cache": 0,
                "active_module_count": 0,
            },
            "cards": [
                {
                    "title": "AI şema hazırlığı",
                    "value": int(schema_status.get("error_count") or 0),
                    "meta": "Eksik tablo / kolon kontrolü önce tamamlanmalı",
                    "tone": "watch",
                    "module_type": "governance",
                    "button_label": "Yönetim detayını aç" if can_view_admin_ai else "Migration tamamla",
                    "href": _safe_url_for("main.admin_ai_center") if can_view_admin_ai else None,
                    "icon": "fa-shield-halved",
                }
            ],
        }
    try:
        module_types = tuple(item["module_type"] for item in DASHBOARD_AI_MODULE_META)
        request_rows = (
            db.session.query(AIRequestLog.module_type, func.count(AIRequestLog.id))
            .filter(AIRequestLog.module_type.in_(module_types))
            .group_by(AIRequestLog.module_type)
            .all()
        )
        request_counts = {str(key or "genel"): _to_int(value) for key, value in request_rows}

        cache_rows = (
            db.session.query(AISummaryCache.module_type, func.count(AISummaryCache.id))
            .filter(AISummaryCache.module_type.in_(module_types))
            .group_by(AISummaryCache.module_type)
            .all()
        )
        cache_counts = {str(key or "genel"): _to_int(value) for key, value in cache_rows}

        recommendation_rows = (
            db.session.query(AIRecommendation.module_type, func.count(AIRecommendation.id))
            .filter(AIRecommendation.module_type.in_(module_types), AIRecommendation.status == "open")
            .group_by(AIRecommendation.module_type)
            .all()
        )
        recommendation_counts = {str(key or "genel"): _to_int(value) for key, value in recommendation_rows}

        feedback_rows = (
            db.session.query(AIRequestLog.module_type, func.count(AIFeedbackLog.id))
            .join(AIFeedbackLog, AIFeedbackLog.ai_request_log_id == AIRequestLog.id)
            .filter(
                AIRequestLog.module_type.in_(module_types),
                AIFeedbackLog.feedback_type.in_(["not_helpful", "incorrect", "negative"]),
            )
            .group_by(AIRequestLog.module_type)
            .all()
        )
        feedback_counts = {str(key or "genel"): _to_int(value) for key, value in feedback_rows}

        unmasked_rows = (
            db.session.query(AIRequestLog.module_type, func.count(AIRequestLog.id))
            .filter(AIRequestLog.module_type.in_(module_types), AIRequestLog.was_masked.is_(False))
            .group_by(AIRequestLog.module_type)
            .all()
        )
        unmasked_counts = {str(key or "genel"): _to_int(value) for key, value in unmasked_rows}

        total_requests = sum(request_counts.get(module, 0) for module in module_types)
        total_open = sum(recommendation_counts.get(module, 0) for module in module_types)
        total_feedback = sum(feedback_counts.get(module, 0) for module in module_types)
        total_unmasked = sum(unmasked_counts.get(module, 0) for module in module_types)
        total_cache = sum(cache_counts.get(module, 0) for module in module_types)

        tone = _tone_from_counts(critical=total_unmasked + total_feedback, warning=total_open)
        active_modules = [item for item in DASHBOARD_AI_MODULE_META if request_counts.get(item["module_type"], 0) or cache_counts.get(item["module_type"], 0) or recommendation_counts.get(item["module_type"], 0)]
        active_module_count = len(active_modules)
        if total_unmasked > 0 or total_feedback > 0:
            headline = "AI operasyon görünümünde yönetişim takibi öne çıkıyor"
            summary = "Performans, personel/izin, iletişim, anket, geri bildirim, dashboard ve yardım merkezi tarafındaki AI çıktıları aynı karar yüzeyinde toplanıyor; maskesiz kayıtlar ve olumsuz geri bildirimler önce ele alınmalı."
        elif total_open > 0:
            headline = "AI önerileri modüller arasında karar masasında birikiyor"
            summary = "Açık AI önerileri performans, personel/izin, iletişim, anket, geri bildirim, dashboard ve yardım merkezi akışlarında aynı operasyon ritminde izlenebilir durumda."
        else:
            headline = "Modüller arası AI akışı dengeli görünüyor"
            summary = f"Toplam {active_module_count} aktif alanda görünür AI izleri okunuyor; yönetim görünümü yalnız canlı kapsamda kalan modülleri izliyor."

        cards: list[dict[str, Any]] = []
        for item in DASHBOARD_AI_MODULE_META:
            module = item["module_type"]
            request_total = request_counts.get(module, 0)
            open_total = recommendation_counts.get(module, 0)
            feedback_total = feedback_counts.get(module, 0)
            unmasked_total = unmasked_counts.get(module, 0)
            cache_total = cache_counts.get(module, 0)
            cards.append(
                {
                    "title": item["label"],
                    "value": request_total,
                    "meta": f"Açık öneri {open_total} · Özet cache {cache_total}",
                    "tone": "critical" if feedback_total or unmasked_total else ("watch" if open_total else "calm"),
                    "module_type": module,
                    "button_label": f"{item['label'].split()[0]} AI raporu" if can_view_admin_ai else item["page_label"],
                    "href": _safe_url_for("main.admin_ai_operations_report", module_type=module) if can_view_admin_ai else _safe_url_for(item["page_href"]),
                    "icon": item["icon"],
                }
            )

        cards.append(
            {
                "title": "Yönetişim uyarısı",
                "value": total_feedback + total_unmasked,
                "meta": f"Negatif geri bildirim {total_feedback} · Maskesiz {total_unmasked}",
                "tone": "critical" if (total_feedback + total_unmasked) else "calm",
                "module_type": "governance",
                "button_label": "Yönetişim merkezini aç" if can_view_admin_ai else "Durumu izle",
                "href": _safe_url_for("main.admin_ai_center") if can_view_admin_ai else None,
                "icon": "fa-shield-halved",
            }
        )

        return {
            "badge": _badge_from_tone(tone),
            "tone": tone,
            "headline": headline,
            "summary": summary,
            "totals": {
                "requests": total_requests,
                "open_recommendations": total_open,
                "negative_feedback": total_feedback,
                "unmasked_requests": total_unmasked,
                "summary_cache": total_cache,
                "active_module_count": active_module_count,
            },
            "cards": cards,
        }
    except Exception as exc:
        try:
            db.session.rollback()
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/ai/dashboard_panel_operations.py")
        try:
            current_app.logger.warning("AI dashboard bridge devre disi birakildi: %s", exc, exc_info=True)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360_MAINTENANCE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/ai/dashboard_panel_operations.py")
        return None

