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

def build_hr_leave_ai_panel(
    *,
    summary: dict[str, Any] | None = None,
    pressure_rows: Iterable[Any] | None = None,
    action_rows: Iterable[Any] | None = None,
    period: Any | None = None,
    scope_label: str | None = None,
) -> dict[str, Any]:
    summary = summary or {}
    pressure_rows = list(pressure_rows or [])
    action_rows = list(action_rows or [])
    pending = _to_int(summary.get("pending_leave_count"))
    manager_gap = _to_int(summary.get("manager_gap_count"))
    exemption_candidates = _to_int(summary.get("exemption_candidates"))
    active_today = _to_int(summary.get("leave_today_count"))
    tone = _tone_from_counts(critical=manager_gap, warning=pending + exemption_candidates)
    period_title = _get(period, "title", "Seçili dönem")

    if manager_gap:
        headline = f"{period_title} için vekâletsiz izin baskısı kapatılmalı"
        summary_text = "AI özeti, izin yönetiminde en kritik riskin yönetici rolünü bloke eden ama vekâletle kapanmayan kayıtlar olduğunu gösteriyor."
    elif pending:
        headline = f"{period_title} için bekleyen izin kararları birikiyor"
        summary_text = "AI özeti, onay bekleyen izin satırlarının aynı birimlerde kümelendiğini ve karar temposunun düşmemesi gerektiğini işaret ediyor."
    else:
        headline = f"{period_title} izin görünümü kontrollü"
        summary_text = "AI özeti, kritik kırmızı bayrak görmüyor; yine de birim bazlı baskı ve bakiye görünümü takip edilmeli."

    bullets = [
        f"Seçili kapsam: {scope_label or 'genel'}; bugün izinli {active_today}, bekleyen {pending}, muafiyet adayı {exemption_candidates} personel bulunuyor.",
        f"AI aksiyon planında {len(action_rows)} satır, birim baskı haritasında {len(pressure_rows)} birim öne çıktı.",
    ]
    if pressure_rows:
        top = pressure_rows[0]
        bullets.append(
            f"En yoğun baskı {top.get('unit_name') or '-'} biriminde; risk skoru {top.get('risk_score') or 0}, yönetici boşluğu {top.get('manager_gap_count') or 0}."
        )
    bullets.append("Yönetici raporu indirilebilir; Excel ve CSV çıktıları toplantı öncesi hızlı dağıtım için hazırdır.")

    actions = [
        {"label": "Vekâletsiz izin", "value": manager_gap, "tone": "critical" if manager_gap else "calm"},
        {"label": "Bekleyen karar", "value": pending, "tone": "watch" if pending else "calm"},
        {"label": "Muafiyet adayı", "value": exemption_candidates, "tone": "watch" if exemption_candidates else "calm"},
        {"label": "Baskı birimi", "value": len(pressure_rows), "tone": "watch" if pressure_rows else "calm"},
    ]
    return {
        "badge": _badge_from_tone(tone),
        "tone": tone,
        "headline": headline,
        "summary": summary_text,
        "bullets": bullets[:4],
        "actions": actions,
    }


def build_hr_attendance_ai_panel(
    *,
    summary: dict[str, Any] | None = None,
    pressure_rows: Iterable[Any] | None = None,
    action_rows: Iterable[Any] | None = None,
    period: Any | None = None,
    scope_label: str | None = None,
) -> dict[str, Any]:
    summary = summary or {}
    pressure_rows = list(pressure_rows or [])
    action_rows = list(action_rows or [])
    uncovered = _to_int(summary.get("uncovered_count"))
    manager_gap = _to_int(summary.get("manager_gap_count"))
    expiring = _to_int(summary.get("expiring_delegation_count"))
    pending = _to_int(summary.get("pending_delegation_count"))
    active_delegations = _to_int(summary.get("active_delegation_count"))
    tone = _tone_from_counts(critical=manager_gap + uncovered, warning=expiring + pending)
    period_title = _get(period, "title", "Seçili dönem")

    if manager_gap or uncovered:
        headline = f"{period_title} için devamsızlık ve vekâlet zinciri sıkı takip istiyor"
        summary_text = "AI özeti, vekâletsiz yönetici kayıtları ile açıkta atamaların aynı operasyon hattında biriktiğini gösteriyor."
    elif expiring or pending:
        headline = f"{period_title} için vekâlet süreleri yakından izlenmeli"
        summary_text = "AI özeti, aktif vekâletlerin bir bölümünün bitişe yaklaştığını ve bekleyen kararların operasyon kalitesini etkileyebileceğini söylüyor."
    else:
        headline = f"{period_title} devamsızlık ve vekâlet görünümü dengeli"
        summary_text = "AI özeti, seçili kapsamda kritik kümelenme görmüyor; günlük bakım akışı yeterli görünüyor."

    bullets = [
        f"Seçili kapsam: {scope_label or 'genel'}; aktif vekâlet {active_delegations}, açıkta atama {uncovered}, yakında bitecek vekâlet {expiring}.",
        f"AI aksiyon planında {len(action_rows)} satır, baskı haritasında {len(pressure_rows)} birim izleniyor.",
    ]
    if pressure_rows:
        top = pressure_rows[0]
        bullets.append(
            f"En yoğun baskı {top.get('unit_name') or '-'} biriminde; risk skoru {top.get('risk_score') or 0}, yönetici boşluğu {top.get('manager_gap_count') or 0}."
        )
    bullets.append("Yönetici raporu dışa aktarımıyla toplantı öncesi aynı görünüm Excel veya CSV olarak paylaşılabilir.")

    actions = [
        {"label": "Açıkta atama", "value": uncovered, "tone": "critical" if uncovered else "calm"},
        {"label": "Vekâletsiz kayıt", "value": manager_gap, "tone": "critical" if manager_gap else "calm"},
        {"label": "Yakında bitecek", "value": expiring, "tone": "watch" if expiring else "calm"},
        {"label": "Bekleyen vekâlet", "value": pending, "tone": "watch" if pending else "calm"},
    ]
    return {
        "badge": _badge_from_tone(tone),
        "tone": tone,
        "headline": headline,
        "summary": summary_text,
        "bullets": bullets[:4],
        "actions": actions,
    }

