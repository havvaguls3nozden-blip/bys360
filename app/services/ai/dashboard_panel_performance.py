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

def build_dashboard_ai_panel(context: dict[str, Any] | None) -> dict[str, Any]:
    context = context or {}
    overdue = _to_int(context.get("my_overdue_tasks"))
    pending = _to_int(context.get("my_pending_tasks"))
    completed = _to_int(context.get("my_completed_tasks"))
    pending_feedback = _to_int(context.get("pending_feedback_requests"))
    meetings = _to_int(context.get("upcoming_meetings_count"))
    uncovered = _to_int(_get(context.get("coverage_summary") or {}, "uncovered"))
    delegated = _to_int(_get(context.get("coverage_summary") or {}, "delegated"))
    risk_score = _to_int(context.get("coverage_risk_score"))
    completion_rate = _to_float(context.get("completion_rate"))

    critical = overdue + uncovered
    warning = pending_feedback + max(risk_score - 50, 0)
    tone = _tone_from_counts(critical=critical, warning=warning)

    if overdue > 0 or uncovered > 0:
        headline = "Öncelik geciken görevler ve kapsama boşlukları"
        summary = "AI özeti, canlı akışta önce zaman aşımına giden görevler ile açıkta kalan amir zincirlerinin ele alınmasını öneriyor."
    elif pending_feedback > 0 or meetings > 0:
        headline = "Geri bildirim ve görüşme akışı aktif"
        summary = "AI özeti, performans akışının yanında geri bildirim taleplerinin ve yaklaşan görüşmelerin birlikte izlenmesini öneriyor."
    else:
        headline = "Gösterim alanı dengeli görünüyor"
        summary = "AI özeti, mevcut görünümde acil kırmızı bayrak oluşmadığını; ritmin korunmasının yeterli olduğunu söylüyor."

    bullets = [
        f"{overdue} geciken görev var; önce görevlerim ekranındaki zaman aşımı listesi temizlenmeli.",
        f"{uncovered} açıkta zincir ve {delegated} vekâletli görev son kapsam koşusundan taşınıyor.",
        f"Tamamlama oranı %{completion_rate:.1f}; bekleyen {pending} göreve karşılık tamamlanan {completed} kayıt görünüyor.",
    ]
    if pending_feedback or meetings:
        bullets.append(f"{pending_feedback} bekleyen geri bildirim talebi ve {meetings} yaklaşan görüşme yönetici takvimine temas ediyor.")

    actions = [
        {"label": "Geciken görev", "value": overdue, "tone": "critical" if overdue else "calm"},
        {"label": "Açıkta zincir", "value": uncovered, "tone": "critical" if uncovered else "calm"},
        {"label": "Bekleyen geri bildirim", "value": pending_feedback, "tone": "watch" if pending_feedback else "calm"},
        {"label": "Yaklaşan görüşme", "value": meetings, "tone": "watch" if meetings else "calm"},
    ]

    return {
        "badge": _badge_from_tone(tone),
        "tone": tone,
        "headline": headline,
        "summary": summary,
        "bullets": bullets[:4],
        "actions": actions,
    }


def build_management_ai_panel(dashboard: Any, publish_summary: Any, period: Any = None) -> dict[str, Any]:
    dashboard = dashboard or {}
    publish_summary = publish_summary or {}

    assignment_total = _to_int(_get(dashboard, "assignment_total"))
    assignment_overdue = _to_int(_get(dashboard, "assignment_overdue"))
    completion_rate = _to_float(_get(dashboard, "completion_rate"))
    publish_rate = _to_float(_get(dashboard, "publish_rate"))
    low_count = _to_int(_get(_get(dashboard, "scorecard", {}), "low_count"))
    high_count = _to_int(_get(_get(dashboard, "scorecard", {}), "high_count"))
    ready_count = _to_int(_get(publish_summary, "ready_count"))
    blocked_count = _to_int(_get(publish_summary, "blocked_count"))
    blocked_reasons = _top_reason_pairs(_get(publish_summary, "blocked_reasons_summary"), limit=3)

    tone = _tone_from_counts(critical=assignment_overdue + blocked_count + low_count, warning=max(ready_count - blocked_count, 0))
    period_title = _get(period, "title", "Seçili dönem")

    if blocked_count > 0:
        headline = f"{period_title} için yayın öncesi bloke kayıtlar öncelikli"
        summary = "AI özeti, yayın ekranındaki tıkanmanın önce bloke nedenleri ve geciken görevler üzerinden çözülmesini öneriyor."
    elif assignment_overdue > 0:
        headline = f"{period_title} için tamamlanma ritmi hızlandırılmalı"
        summary = "AI özeti, yayıma yakın dönemde zaman aşımına giden görevlerin yönetici bazında kapatılmasını öneriyor."
    else:
        headline = f"{period_title} görünümü kontrollü ilerliyor"
        summary = "AI özeti, görev ve yayın akışının birlikte okunabildiğini; ana odakta hazırlık ve duyuru temposunun kaldığını gösteriyor."

    bullets = [
        f"Toplam {assignment_total} görevin %{completion_rate:.1f} kadarı tamamlanmış durumda.",
        f"Yayın oranı %{publish_rate:.1f}; personele açılmaya hazır {ready_count} kayıt var.",
        f"{blocked_count} bloke kayıt ve {assignment_overdue} geciken görev, karar masasında ilk iki risk başlığı olarak öne çıkıyor.",
    ]
    if low_count or high_count:
        bullets.append(f"Scorecard görünümünde 70 altı {low_count}, 90 üstü {high_count} kayıt bulunuyor.")

    actions = [
        {"label": "Bloke kayıt", "value": blocked_count, "tone": "critical" if blocked_count else "calm"},
        {"label": "Geciken görev", "value": assignment_overdue, "tone": "critical" if assignment_overdue else "calm"},
        {"label": "Yayıma hazır", "value": ready_count, "tone": "watch" if ready_count else "calm"},
        {"label": "70 altı", "value": low_count, "tone": "watch" if low_count else "calm"},
    ]

    return {
        "badge": _badge_from_tone(tone),
        "tone": tone,
        "headline": headline,
        "summary": summary,
        "bullets": bullets[:4],
        "actions": actions,
        "reason_rows": blocked_reasons,
    }


def build_scorecard_ai_panel(scorecard: Any, period: Any = None, scope_label: str | None = None) -> dict[str, Any]:
    scorecard = scorecard or {}
    rows = list(_get(scorecard, "rows", []) or [])
    count = _to_int(_get(scorecard, "count"))
    published_count = _to_int(_get(scorecard, "published_count"))
    completed_count = _to_int(_get(scorecard, "completed_count"))
    hidden_count = _to_int(_get(scorecard, "hidden_count"))
    low_count = _to_int(_get(scorecard, "low_count"))
    high_count = _to_int(_get(scorecard, "high_count"))
    avg_score = _to_float(_get(scorecard, "avg_score"))
    internal_preview = max(completed_count - published_count, 0)
    tone = _tone_from_counts(critical=hidden_count + low_count, warning=internal_preview)
    period_title = _get(period, "title", "Seçili dönem")

    if hidden_count > 0:
        headline = f"{period_title} karnelerinde görünürlük kuralları baskın"
        summary = "AI özeti, aynı tabloda tamamlanmış ama yetki ve yayın politikası nedeniyle gizli tutulan kayıtlar bulunduğunu işaret ediyor."
    elif internal_preview > 0:
        headline = f"{period_title} için iç kullanım ile personel görünümü ayrışıyor"
        summary = "AI özeti, tamamlanmış kayıtların bir kısmının henüz personele açılmadığını ve yayın ritminin ayrıca izlenmesi gerektiğini gösteriyor."
    else:
        headline = f"{period_title} karne görünümü dengeli"
        summary = "AI özeti, görünür kayıtların yayın ve final sonuç tarafında aynı çizgiye yaklaştığını belirtiyor."

    top_names = [str(item.get("display_name") or "-") for item in rows[:2]]
    low_names = [str(item.get("display_name") or "-") for item in rows[-2:]] if len(rows) > 1 else top_names[:]
    bullets = [
        f"Seçili görünüm: {scope_label or 'Kendi görünümüm'}; toplam {count} karne görünüyor.",
        f"Ortalama puan {avg_score:.2f}; 70 altı {low_count}, 90 üstü {high_count} kayıt var.",
        f"Yayımlanan {published_count}, tamamlanan {completed_count}; iç kullanım önizlemesinde {internal_preview} kayıt öne çıkıyor.",
    ]
    if hidden_count:
        bullets.append(f"{hidden_count} kayıt görünürlük ve yetki kuralları nedeniyle tabloda gizli kalıyor.")

    actions = [
        {"label": "Yayımlanan", "value": published_count, "tone": "calm"},
        {"label": "İç kullanım", "value": internal_preview, "tone": "watch" if internal_preview else "calm"},
        {"label": "Gizli kayıt", "value": hidden_count, "tone": "critical" if hidden_count else "calm"},
        {"label": "70 altı", "value": low_count, "tone": "watch" if low_count else "calm"},
    ]

    spotlight = []
    if top_names:
        spotlight.append({"label": "Üst bant örnekleri", "value": ", ".join(top_names)})
    if low_names:
        spotlight.append({"label": "Alt bant örnekleri", "value": ", ".join(low_names)})

    return {
        "badge": _badge_from_tone(tone),
        "tone": tone,
        "headline": headline,
        "summary": summary,
        "bullets": bullets[:4],
        "actions": actions,
        "spotlight": spotlight,
    }


def build_publish_ai_panel(scorecard: Any, publish_summary: Any, period: Any = None) -> dict[str, Any]:
    scorecard = scorecard or {}
    publish_summary = publish_summary or {}

    total_count = _to_int(_get(scorecard, "count"))
    published_count = _to_int(_get(scorecard, "published_count"))
    ready_count = _to_int(_get(publish_summary, "ready_count"))
    blocked_count = _to_int(_get(publish_summary, "blocked_count"))
    blocked_reasons = _top_reason_pairs(_get(publish_summary, "blocked_reasons_summary"), limit=4)
    publish_rate = _to_float(_get(publish_summary, "publish_rate"))
    internal_gap = max(total_count - published_count, 0)
    tone = _tone_from_counts(critical=blocked_count + internal_gap, warning=ready_count)
    period_title = _get(period, "title", "Seçili dönem")

    if blocked_count > 0:
        headline = f"{period_title} için yayın öncesi blokeler çözülmeli"
        summary = "AI özeti, sonuç yayını öncesinde bloke nedenlerinin azaltılmasını ve eksik akışların kapatılmasını öneriyor."
    elif internal_gap > 0:
        headline = f"{period_title} için iç görünüm ile personel görünümü arasında fark var"
        summary = "AI özeti, tamamlanan sonuçların bir bölümünün henüz personele açılmadığını ve duyuru ritminin planlı ilerlemesi gerektiğini söylüyor."
    else:
        headline = f"{period_title} yayın görünümü dengeli"
        summary = "AI özeti, yayın yüzeyinde belirgin bir tıkanma olmadığını ve işlemlerin kontrollü ilerlediğini gösteriyor."

    bullets = [
        f"Toplam {total_count} sonuç içinde {published_count} kayıt şu an personele görünür durumda.",
        f"Yayıma hazır {ready_count} kayıt ve bloke olan {blocked_count} kayıt birlikte izlenmeli.",
        f"Yayın oranı %{publish_rate:.1f}; iç görünümde bekleyen {internal_gap} kayıt bulunuyor.",
    ]
    if blocked_reasons:
        bullets.append("En baskın bloke başlıkları: " + ", ".join(f"{row['label']} ({row['value']})" for row in blocked_reasons[:3]))

    actions = [
        {"label": "Bloke kayıt", "value": blocked_count, "tone": "critical" if blocked_count else "calm"},
        {"label": "Yayıma hazır", "value": ready_count, "tone": "watch" if ready_count else "calm"},
        {"label": "Personelde görünür", "value": published_count, "tone": "calm"},
        {"label": "İç görünüm farkı", "value": internal_gap, "tone": "watch" if internal_gap else "calm"},
    ]

    return {
        "badge": _badge_from_tone(tone),
        "tone": tone,
        "headline": headline,
        "summary": summary,
        "bullets": bullets[:4],
        "actions": actions,
        "reason_rows": blocked_reasons,
    }


def build_periods_ai_panel(period_rows: Iterable[Any] | None, totals: dict[str, Any] | None = None, selected_status: str | None = None, q: str | None = None) -> dict[str, Any]:
    rows = list(period_rows or [])
    totals = totals or {}
    total_count = _to_int(totals.get("total_count"))
    active_count = _to_int(totals.get("active_count"))
    published_count = _to_int(totals.get("published_count"))
    locked_count = _to_int(totals.get("locked_count"))

    uncovered_total = 0
    delegated_total = 0
    completed_total = 0
    evaluation_total = 0
    active_titles: list[str] = []
    for row in rows:
        period = _get(row, "period")
        if _get(period, "is_active"):
            active_titles.append(str(_get(period, "title") or f"Dönem #{_get(period, 'id', '-') }"))
        coverage = _get(row, "coverage_summary", {}) or {}
        uncovered_total += _to_int(_get(coverage, "uncovered"))
        delegated_total += _to_int(_get(coverage, "delegated"))
        completed_total += _to_int(_get(row, "completed_count"))
        evaluation_total += _to_int(_get(row, "evaluation_count"))

    completion_rate = (_to_float(completed_total) / evaluation_total * 100.0) if evaluation_total else 0.0
    tone = _tone_from_counts(critical=max(active_count - 1, 0) + uncovered_total, warning=locked_count + max(total_count - published_count, 0))

    if active_count > 1:
        headline = "Birden fazla aktif dönem görünüyor"
        summary = "AI özeti, aynı anda tek aktif dönem kuralının tekrar kontrol edilmesini öneriyor."
    elif uncovered_total > 0:
        headline = "Dönem yönetiminde kapsama boşlukları öne çıkıyor"
        summary = "AI özeti, dönem listesinde önce açıkta zincir ve görev kapsam boşluklarının temizlenmesini öneriyor."
    else:
        headline = "Aktif dönem yönetimi kontrollü ilerliyor"
        summary = "AI özeti, aktiflik, kilit ve yayın adımlarının dönem yüzeyinden güvenli biçimde yönetilebildiğini gösteriyor."

    bullets = [
        f"Toplam {total_count} dönem içinde {active_count} aktif, {published_count} yayında ve {locked_count} kilitli kayıt bulunuyor.",
        f"Seçili filtre: {selected_status or 'Tümü'}; arama ifadesi: {q or 'Yok'}.",
        f"Canlı kapsama özeti toplamında açıkta {uncovered_total}, vekâletli {delegated_total} kayıt görülüyor.",
        f"Tamamlanan değerlendirme oranı %{completion_rate:.1f}; toplam {completed_total} / {evaluation_total} kapanmış kayıt izleniyor.",
    ]

    spotlight = []
    if active_titles:
        spotlight.append({"label": "Aktif dönem", "value": ", ".join(active_titles[:2])})
    if rows:
        first_period = _get(_get(rows[0], "period"), "title")
        if first_period:
            spotlight.append({"label": "Listede ilk dönem", "value": str(first_period)})

    actions = [
        {"label": "Aktif dönem", "value": active_count, "tone": "critical" if active_count > 1 else ("watch" if active_count == 0 else "calm")},
        {"label": "Açıkta zincir", "value": uncovered_total, "tone": "critical" if uncovered_total else "calm"},
        {"label": "Kilitli", "value": locked_count, "tone": "watch" if locked_count else "calm"},
        {"label": "Yayında", "value": published_count, "tone": "calm"},
    ]

    return {
        "badge": _badge_from_tone(tone),
        "tone": tone,
        "headline": headline,
        "summary": summary,
        "bullets": bullets,
        "actions": actions,
        "spotlight": spotlight,
    }


def build_period_form_ai_panel(period: Any = None) -> dict[str, Any]:
    period_type = str(_get(period, "period_type") or "Yeni dönem")
    start_date = _get(period, "start_date")
    end_date = _get(period, "end_date")
    eval_start = _get(period, "evaluation_window_start")
    eval_end = _get(period, "evaluation_window_end")
    due_days = _to_int(_get(period, "evaluation_due_days"))
    active = bool(_get(period, "is_active", False))
    published = bool(_get(period, "results_published", False))
    locked = bool(_get(period, "is_locked", False))

    tone = _tone_from_counts(critical=int(active and locked), warning=int(published))
    headline = "AI yapılandırma rehberi"
    summary = "Bu panel, dönem kartını kaydetmeden önce takvim, görünürlük ve kilit etkilerini aynı bakışta kontrol etmenize yardımcı olur."

    bullets = [
        f"Dönem türü: {period_type}. Tarih aralığı planlanırken görev üretimi ve puanlama penceresi birlikte düşünülmeli.",
        f"Puanlama penceresi: {(eval_start.strftime('%d.%m.%Y') if eval_start else 'belirlenmedi')} - {(eval_end.strftime('%d.%m.%Y') if eval_end else 'belirlenmedi')}; görev süresi {due_days or 0} gün.",
        f"Durum özeti: {'Aktif' if active else 'Pasif'} · {'Yayında' if published else 'Yayında değil'} · {'Kilitli' if locked else 'Kilitsiz'}.",
        f"Dönem takvimi: {(start_date.strftime('%d.%m.%Y') if start_date else 'başlangıç yok')} - {(end_date.strftime('%d.%m.%Y') if end_date else 'bitiş yok')}.",
    ]

    actions = [
        {"label": "Aktiflik", "value": 1 if active else 0, "tone": "watch" if active else "calm"},
        {"label": "Yayın", "value": 1 if published else 0, "tone": "watch" if published else "calm"},
        {"label": "Kilit", "value": 1 if locked else 0, "tone": "critical" if locked else "calm"},
        {"label": "Görev süresi", "value": due_days or 0, "tone": "calm"},
    ]

    return {
        "badge": _badge_from_tone(tone),
        "tone": tone,
        "headline": headline,
        "summary": summary,
        "bullets": bullets,
        "actions": actions,
    }


def build_task_generation_ai_panel(*, stats: Any = None, coverage_summary: Any = None, latest_log_summary: Any = None, period: Any = None) -> dict[str, Any]:
    stats = stats or {}
    coverage_summary = coverage_summary or {}
    latest_log_summary = latest_log_summary or {}

    total = _to_int(_get(stats, "total"))
    pending = _to_int(_get(stats, "pending"))
    partial = _to_int(_get(stats, "partial"))
    completed = _to_int(_get(stats, "completed"))
    delegated = _to_int(_get(coverage_summary, "delegated"))
    uncovered = _to_int(_get(coverage_summary, "uncovered"))
    exempted = _to_int(_get(latest_log_summary, "exempted"))
    chain_issue = _to_int(_get(latest_log_summary, "chain_issue"))
    special_case = _to_int(_get(latest_log_summary, "special_case"))
    generated = _to_int(_get(latest_log_summary, "generated"))
    period_title = _get(period, "title", "Seçili dönem")

    progress_base = max(total, completed + pending + partial)
    completion_rate = round((completed / progress_base) * 100, 1) if progress_base > 0 else 0.0
    critical = uncovered + chain_issue
    warning = pending + partial + exempted
    tone = _tone_from_counts(critical=critical, warning=warning)

    if uncovered or chain_issue:
        headline = f"{period_title} için görev üretimi öncesi zincir düzeltmesi öne çıkıyor"
        summary = "AI özeti, görev üretimini yeniden çalıştırmadan önce açıkta kalan görevler ile zincir problemi taşıyan personellerin temizlenmesini öneriyor."
    elif pending or partial:
        headline = f"{period_title} için üretim zemini hazır ama görev ritmi tamamlanmadı"
        summary = "AI özeti, yeni üretimden çok mevcut görevlerin kapatılması ve kısmi kayıtların tamamlanmasının değer üreteceğini gösteriyor."
    else:
        headline = f"{period_title} görev üretim görünümü dengeli"
        summary = "AI özeti, seçili dönemde görev üretimi ile canlı kapsama görünümünün aynı çizgide ilerlediğini söylüyor."

    bullets = [
        f"Toplam {total} görevde tamamlama oranı %{completion_rate:.1f}; bekleyen {pending}, kısmi {partial}, tamamlanan {completed} kayıt var.",
        f"Canlı kapsamada {delegated} vekâletli ve {uncovered} açıkta görev görünüyor; üretim kalitesi bu iki sayaçla doğrudan etkileniyor.",
        f"Son üretim koşusunda muaf {exempted}, zincir sorunu {chain_issue}, istisna bilgisi {special_case} kayıt tutuldu.",
    ]
    if generated:
        bullets.append(f"Son koşu logunda {generated} üretilen kayıt işlenmiş görünüyor; yeniden üretimden önce tablo temizliği gerekmiyorsa aynı dönem üstünde güvenle devam edilebilir.")

    actions = [
        {"label": "Bekleyen", "value": pending, "tone": "watch" if pending else "calm"},
        {"label": "Açıkta", "value": uncovered, "tone": "critical" if uncovered else "calm"},
        {"label": "Zincir sorunu", "value": chain_issue, "tone": "critical" if chain_issue else "calm"},
        {"label": "Vekâlet", "value": delegated, "tone": "watch" if delegated else "calm"},
    ]

    return {
        "badge": _badge_from_tone(tone),
        "tone": tone,
        "headline": headline,
        "summary": summary,
        "bullets": bullets[:4],
        "actions": actions,
    }


def build_task_preflight_ai_panel(*, alert_summary: Any = None, coverage_summary: Any = None, latest_log_summary: Any = None, period: Any = None) -> dict[str, Any]:
    alert_summary = alert_summary or {}
    coverage_summary = coverage_summary or {}
    latest_log_summary = latest_log_summary or {}

    total_users = _to_int(_get(alert_summary, "total_users"))
    problematic = _to_int(_get(alert_summary, "problematic_users"))
    ok_users = _to_int(_get(alert_summary, "ok_users"))
    uncovered = _to_int(_get(coverage_summary, "uncovered"))
    delegated = _to_int(_get(coverage_summary, "delegated"))
    exempted = _to_int(_get(latest_log_summary, "exempted"))
    chain_issue = _to_int(_get(latest_log_summary, "chain_issue"))
    is_active = bool(_get(period, "is_active", False))
    is_locked = bool(_get(period, "is_locked", False))
    is_published = bool(_get(period, "results_published", False))
    period_title = _get(period, "title", "Seçili dönem")

    coverage_rate = round((ok_users / total_users) * 100, 1) if total_users > 0 else 0.0
    critical = problematic + uncovered + (1 if is_locked else 0)
    warning = delegated + exempted + chain_issue
    tone = _tone_from_counts(critical=critical, warning=warning)

    if problematic or uncovered:
        headline = f"{period_title} ön kontrolünde önce zincir bütünlüğü doğrulanmalı"
        summary = "AI özeti, görev üretimi veya yeniden üretim öncesinde eksik zincirler ile vekâletsiz açıkta kalan görevlerin temizlenmesini öneriyor."
    elif is_locked:
        headline = f"{period_title} ön kontrolü kilitli durumda"
        summary = "AI özeti, dönem kilitli olduğu için üretim ve müdahale akışında önce yönetim kararının netleştirilmesini öneriyor."
    else:
        headline = f"{period_title} ön kontrol zemini kullanılabilir"
        summary = "AI özeti, seçili dönemin aktiflik ve kapsama görünümünün görev üretimi için büyük ölçüde hazır olduğunu gösteriyor."

    bullets = [
        f"Toplam {total_users} personelin %{coverage_rate:.1f} kadarı zincir açısından temiz görünüyor; sorunlu kayıt sayısı {problematic}.",
        f"Canlı kapsam tarafında {delegated} vekâletli ve {uncovered} açıkta görev var; açıkta sayaç üretim öncesi ilk kontrol noktası olmalı.",
        f"Dönem durumu: {'aktif' if is_active else 'pasif'}, {'kilitli' if is_locked else 'kilitsiz'}, {'yayında' if is_published else 'yayında değil'}.",
    ]
    if exempted or chain_issue:
        bullets.append(f"Son kayıt özetinde muaf {exempted} ve zincir sorunu {chain_issue} personel görüldü; bu dağılım preflight notuna eklenmeli.")

    actions = [
        {"label": "Sorunlu zincir", "value": problematic, "tone": "critical" if problematic else "calm"},
        {"label": "Zinciri tam", "value": ok_users, "tone": "calm"},
        {"label": "Açıkta", "value": uncovered, "tone": "critical" if uncovered else "calm"},
        {"label": "Dönem kilidi", "value": 1 if is_locked else 0, "tone": "watch" if is_locked else "calm"},
    ]

    spotlight = [
        {"label": "Kapsama oranı", "value": f"%{coverage_rate:.1f}"},
        {"label": "Muaf kayıt", "value": exempted},
    ]

    return {
        "badge": _badge_from_tone(tone),
        "tone": tone,
        "headline": headline,
        "summary": summary,
        "bullets": bullets[:4],
        "actions": actions,
        "spotlight": spotlight,
    }


def build_hierarchy_ai_panel(*, analysis_rows: Iterable[Any] | None = None, missing_count: int = 0, complete_count: int = 0, period: Any = None, level_3_mode: str | None = None, scope_label: str | None = None) -> dict[str, Any]:
    rows = list(analysis_rows or [])
    total_count = len(rows)
    missing_count = _to_int(missing_count)
    complete_count = _to_int(complete_count)
    warning_count = 0
    level_3_count = 0
    single_count = 0
    chain_buckets: dict[str, int] = {}
    for row in rows:
        if _has_real_hierarchy_warning(row):
            warning_count += 1
        if _has_level_3_binding(row):
            level_3_count += 1
        if bool(_get(row, "is_single_manager_case")):
            single_count += 1
        chain_type = str(_get(row, "chain_type_label") or "-")
        chain_buckets[chain_type] = chain_buckets.get(chain_type, 0) + 1

    coverage_rate = round((complete_count / total_count) * 100, 1) if total_count else 0.0
    period_title = _get(period, "title", "Seçili dönem")
    tone = _tone_from_counts(critical=missing_count, warning=warning_count)
    scope_text = scope_label or "Seçili kapsam"

    if missing_count > 0:
        headline = f"{period_title} için zincir düzeltmesi öncelikli"
        summary = "AI özeti, görev üretimi ve değerlendirme akışı öncesi eksik amir bağlantılarının temizlenmesini öneriyor."
    elif warning_count > 0:
        headline = f"{period_title} zinciri genel olarak sağlam, ancak dikkat isteyen kayıtlar var"
        summary = "AI özeti, eksik zincir oluşmasa da uyarı taşıyan kayıtların ve özel akışların yeniden gözden geçirilmesini öneriyor."
    else:
        headline = f"{period_title} hiyerarşi görünümü dengeli"
        summary = "AI özeti, seçili kapsamda görev üretimini bloke edecek görünür zincir boşluğu olmadığını gösteriyor."

    bullets = [
        f"{scope_text} içinde toplam {total_count} personelin %{coverage_rate:.1f} kadarı tam zincirli görünüyor.",
        f"Eksik zincir {missing_count}, uyarı taşıyan kayıt {warning_count}; bunlar görev üretimi öncesi ilk kontrol alanı.",
        f"3. amirli kayıt {level_3_count}, tek amirli özel kayıt {single_count}; mod: {str(level_3_mode or 'off').replace('_', ' ')}.",
    ]
    if chain_buckets:
        top_bucket = sorted(chain_buckets.items(), key=lambda item: (-item[1], item[0]))[:2]
        bullets.append("Zincir tipinde öne çıkan dağılım: " + ", ".join(f"{label} {count}" for label, count in top_bucket) + ".")

    actions = [
        {"label": "Eksik zincir", "value": missing_count, "tone": "critical" if missing_count else "calm"},
        {"label": "Uyarılı kayıt", "value": warning_count, "tone": "watch" if warning_count else "calm"},
        {"label": "3. amirli", "value": level_3_count, "tone": "watch" if level_3_count else "calm"},
        {"label": "Tam zincir", "value": complete_count, "tone": "calm"},
    ]

    spotlight = [{"label": label, "value": count} for label, count in sorted(chain_buckets.items(), key=lambda item: (-item[1], item[0]))[:3]]

    return {
        "badge": _badge_from_tone(tone),
        "tone": tone,
        "headline": headline,
        "summary": summary,
        "bullets": bullets[:4],
        "actions": actions,
        "spotlight": spotlight,
    }


def build_mail_reminder_ai_panel(*, manager_summary: Iterable[Any] | None = None, total_pending: int = 0, selected_period: Any = None) -> dict[str, Any]:
    rows = list(manager_summary or [])
    total_pending = _to_int(total_pending)
    manager_count = len(rows)
    missing_email = 0
    heavy_load = 0
    max_pending = 0
    top_manager_name = "-"

    for item in rows:
        manager = _get(item, "manager")
        pending = _to_int(_get(item, "count"))
        email = (_get(manager, "email") or "").strip()
        if not email:
            missing_email += 1
        if pending >= 10:
            heavy_load += 1
        if pending > max_pending:
            max_pending = pending
            top_manager_name = f"{_get(manager, 'ad', '')} {_get(manager, 'soyad', '')}".strip() or "-"

    avg_pending = round(total_pending / manager_count, 1) if manager_count else 0.0
    period_title = _get(selected_period, "title", "Seçili dönem")
    tone = _tone_from_counts(critical=missing_email, warning=heavy_load)

    if missing_email > 0:
        headline = f"{period_title} hatırlatma akışında iletişim eksiği var"
        summary = "AI özeti, toplu gönderim öncesi e-posta alanı boş yöneticilerin tamamlanmasını öneriyor."
    elif heavy_load > 0:
        headline = f"{period_title} için yoğun bekleyen görev kümeleri oluşmuş"
        summary = "AI özeti, kişi bazlı önceliklendirme ile yüksek yük taşıyan yöneticilere önce temas edilmesini öneriyor."
    elif manager_count > 0:
        headline = f"{period_title} hatırlatma listesi gönderime hazır"
        summary = "AI özeti, seçili dönemde toplu hatırlatma için görünür bir iletişim engeli bulunmadığını gösteriyor."
    else:
        headline = f"{period_title} için hatırlatma gerektiren açık görev görünmüyor"
        summary = "AI özeti, bu dönemde bekleyen görev kümelenmesi oluşmadığı için toplu gönderim baskısının düşük olduğunu söylüyor."

    bullets = [
        f"Toplam {manager_count} yönetici için {total_pending} bekleyen görev izleniyor; yönetici başına ortalama {avg_pending:.1f} görev düşüyor.",
        f"E-posta alanı eksik yönetici {missing_email}; yoğun yük taşıyan yönetici {heavy_load}.",
    ]
    if manager_count:
        bullets.append(f"En yüksek yük {max_pending} görev ile {top_manager_name} üzerinde görünüyor.")
        bullets.append("Önizleme metni seçili dönem için üretildi; toplu gönderim öncesi örnek metin tekrar okunmalı.")

    actions = [
        {"label": "Mail gidecek", "value": manager_count, "tone": "calm"},
        {"label": "Eksik e-posta", "value": missing_email, "tone": "critical" if missing_email else "calm"},
        {"label": "Yoğun yönetici", "value": heavy_load, "tone": "watch" if heavy_load else "calm"},
        {"label": "Bekleyen görev", "value": total_pending, "tone": "watch" if total_pending else "calm"},
    ]

    spotlight = []
    if manager_count:
        spotlight.append({"label": "En yüksek yük", "value": f"{top_manager_name} · {max_pending}"})
        spotlight.append({"label": "Ortalama yük", "value": f"{avg_pending:.1f} görev"})

    return {
        "badge": _badge_from_tone(tone),
        "tone": tone,
        "headline": headline,
        "summary": summary,
        "bullets": bullets[:4],
        "actions": actions,
        "spotlight": spotlight,
    }


def build_feedback_requests_ai_panel(requests_list: list[Any] | None, *, current_user: Any | None = None) -> dict[str, Any]:
    rows = list(requests_list or [])
    total = len(rows)
    waiting_count = sum(1 for row in rows if (_get(row, "status", "") or "") == "bekliyor")
    scheduled_count = sum(1 for row in rows if (_get(row, "status", "") or "") in {"randevulandi", "randevu_ertelendi"})
    answered_count = sum(1 for row in rows if (_get(row, "status", "") or "") in {"cevaplandi", "gorusme_tamamlandi", "kapatildi"})
    my_employee_count = 0
    my_manager_queue = 0
    current_user_id = _get(current_user, "id")
    for row in rows:
        if current_user_id and _to_int(_get(row, "employee_id")) == _to_int(current_user_id):
            my_employee_count += 1
        if current_user_id and current_user_id in {
            _get(row, "level_1_manager_id"),
            _get(row, "level_2_manager_id"),
            _get(row, "level_3_manager_id"),
        } and (_get(row, "status", "") or "") == "bekliyor":
            my_manager_queue += 1

    tone = _tone_from_counts(critical=waiting_count, warning=scheduled_count)
    if waiting_count > 0:
        headline = "Geri bildirim kuyruğunda bekleyen talepler öne çıkıyor"
        summary = "AI özeti, önce açıkta bekleyen taleplerin ve manager kuyruğunun temizlenmesini; ardından randevuya dönüşen kayıtların kapanışını öneriyor."
    elif scheduled_count > 0:
        headline = "Talep hattı görüşmeye dönüşmüş durumda"
        summary = "AI özeti, kuyruğun önemli kısmının randevuya geçtiğini ve şimdi odakta planlanan görüşmelerin tamamlanmasının olduğunu söylüyor."
    else:
        headline = "Talep hattı dengeli görünüyor"
        summary = "AI özeti, açık bekleme baskısının düşük kaldığını ve akışın daha çok kapanış ve geri bildirim diline odaklanabileceğini belirtiyor."

    bullets = [
        f"Toplam {total} talebin {waiting_count} adedi ilk cevap veya değerlendirme bekliyor.",
        f"{scheduled_count} talep randevu aşamasına taşınmış; {answered_count} kayıt kapanış veya cevap safhasına gelmiş durumda.",
        f"Bu görünümde kullanıcıyla doğrudan ilişkili bekleyen yönetici kuyruğu {my_manager_queue}, personel tarafındaki talepler {my_employee_count} olarak izleniyor.",
    ]

    actions = [
        {"label": "Bekleyen talep", "value": waiting_count, "tone": "critical" if waiting_count else "calm"},
        {"label": "Randevulu", "value": scheduled_count, "tone": "watch" if scheduled_count else "calm"},
        {"label": "Kapanan/Cevap", "value": answered_count, "tone": "calm"},
        {"label": "Yönetici kuyruğu", "value": my_manager_queue, "tone": "watch" if my_manager_queue else "calm"},
    ]
    return {
        "badge": _badge_from_tone(tone),
        "tone": tone,
        "headline": headline,
        "summary": summary,
        "bullets": bullets,
        "actions": actions,
    }


def build_feedback_schedule_ai_panel(req: Any, *, actor: Any | None = None) -> dict[str, Any]:
    manager_count = sum(1 for value in [_get(req, "level_1_manager_id"), _get(req, "level_2_manager_id"), _get(req, "level_3_manager_id")] if value)
    reason_text = (_get(req, "reason") or _get(req, "request_text") or "").strip()
    reason_length = len(reason_text)
    employee_name = (
        _get(_get(req, "employee"), "full_name")
        or f"{_get(_get(req, 'employee'), 'ad', '')} {_get(_get(req, 'employee'), 'soyad', '')}".strip()
        or "Personel"
    )
    tone = _tone_from_counts(critical=0, warning=1 if manager_count > 1 else 0)
    if manager_count >= 3:
        headline = f"{employee_name} için randevu planı çok seviyeli akışa temas ediyor"
        summary = "AI özeti, randevu saatinin net ve çakışmasız belirlenmesini; not alanında da görüşmenin hangi amir akışı için açıldığının kısa yazılmasını öneriyor."
    elif manager_count == 2:
        headline = f"{employee_name} için standart iki amirli görüşme planı"
        summary = "AI özeti, tarih-saat netliğinin ve kısa görüşme amacının yazılmasının, sonraki kapatma adımını hızlandıracağını söylüyor."
    else:
        headline = f"{employee_name} için sade görüşme planı"
        summary = "AI özeti, bu taleplerde en çok tarih-saat-konum netliğinin fark yarattığını; uzun açıklama yerine kısa ve uygulanabilir notların yeterli olduğunu belirtiyor."

    bullets = [
        f"Talepte {manager_count} amir seviyesi görünür; planlanan oturum bu zincirin görünür tarafında ilerleyecek.",
        f"Talep açıklama uzunluğu yaklaşık {reason_length} karakter; randevu notunda bunu tekrar etmek yerine görüşme amacı kısa yazılmalı.",
        "Online görüşmede bağlantı, yüz yüze görüşmede oda/konum alanı boş bırakılmamalı.",
    ]
    actions = [
        {"label": "Amir seviyesi", "value": manager_count, "tone": "watch" if manager_count > 1 else "calm"},
        {"label": "Talep notu", "value": reason_length, "tone": "calm"},
        {"label": "Planlama odağı", "value": 3, "tone": "watch"},
    ]
    return {
        "badge": _badge_from_tone(tone),
        "tone": tone,
        "headline": headline,
        "summary": summary,
        "bullets": bullets,
        "actions": actions,
    }


def build_feedback_meetings_ai_panel(meetings: list[Any] | None, *, current_user: Any | None = None, next_meeting: Any | None = None) -> dict[str, Any]:
    rows = list(meetings or [])
    total = len(rows)
    sum(1 for row in rows if (_get(row, "meeting_date") is not None))
    planned = sum(1 for row in rows if (_get(row, "status", "") or "") == "planlandi")
    completed = sum(1 for row in rows if (_get(row, "status", "") or "") == "tamamlandi")
    delayed = sum(1 for row in rows if (_get(row, "status", "") or "") == "ertelendi")
    cancelled = sum(1 for row in rows if (_get(row, "status", "") or "") == "iptal_edildi")
    current_user_id = _get(current_user, "id")
    managed = sum(1 for row in rows if current_user_id and _to_int(_get(row, "manager_id")) == _to_int(current_user_id))
    attended = sum(1 for row in rows if current_user_id and _to_int(_get(row, "employee_id")) == _to_int(current_user_id))
    tone = _tone_from_counts(critical=delayed + cancelled, warning=planned)
    if delayed or cancelled:
        headline = "Randevu akışında ertelenen veya iptal edilen kayıtlar var"
        summary = "AI özeti, planlı görüşme sayısından çok ertelenen ve iptal edilen başlıkların kısa sürede temizlenmesini öneriyor."
    elif planned > 0:
        headline = "Görüşme hattı planlı ilerliyor"
        summary = "AI özeti, yaklaşan randevuların takvim ritmini koruduğunu; kapanış tarafında tamamlandı statüsüne hızlı geçmenin faydalı olacağını gösteriyor."
    else:
        headline = "Randevu akışı sakin görünüyor"
        summary = "AI özeti, seçili görünümde aktif toplantı baskısının düşük olduğunu ve geçmiş kayıtların daha çok arşiv takibi niteliğinde kaldığını belirtiyor."

    next_label = "-"
    if next_meeting is not None:
        next_label = (
            _get(_get(next_meeting, "employee"), "full_name")
            or f"{_get(_get(next_meeting, 'employee'), 'ad', '')} {_get(_get(next_meeting, 'employee'), 'soyad', '')}".strip()
            or "Yaklaşan görüşme"
        )
    bullets = [
        f"Toplam {total} görünür kaydın {planned} adedi planlandı, {completed} adedi tamamlandı statüsünde.",
        f"Ertelenen {delayed} ve iptal edilen {cancelled} kayıt, randevu hattının baskı noktalarını oluşturuyor.",
        f"Kullanıcının yönettiği {managed} ve katıldığı {attended} görüşme aynı görünümde izleniyor; sıradaki toplantı: {next_label}.",
    ]
    actions = [
        {"label": "Planlandı", "value": planned, "tone": "watch" if planned else "calm"},
        {"label": "Tamamlandı", "value": completed, "tone": "calm"},
        {"label": "Ertelendi", "value": delayed, "tone": "critical" if delayed else "calm"},
        {"label": "İptal", "value": cancelled, "tone": "critical" if cancelled else "calm"},
    ]
    return {
        "badge": _badge_from_tone(tone),
        "tone": tone,
        "headline": headline,
        "summary": summary,
        "bullets": bullets,
        "actions": actions,
    }


def build_portal_admin_ai_panel(panel: Any) -> dict[str, Any]:
    panel = panel or {}
    editorial = _get(panel, "editorial_summary", {}) or {}
    total_editorial = _to_int(_get(editorial, "total"))
    announcements = _to_int(_get(editorial, "announcements"))
    headlines = _to_int(_get(editorial, "headlines"))
    banners = _to_int(_get(editorial, "banners"))
    pending_group_requests = _to_int(_get(panel, "pending_group_requests"))
    receipt_backlog = _to_int(_get(panel, "receipt_backlog"))
    hidden_posts = _to_int(_get(panel, "hidden_posts"))
    locked_posts = _to_int(_get(panel, "locked_posts"))
    group_count = len(list(_get(panel, "group_rows", []) or []))
    tone = _tone_from_counts(critical=total_editorial + receipt_backlog, warning=pending_group_requests + hidden_posts + locked_posts)
    if total_editorial > 0:
        headline = "Portal yönetiminde editoryal kuyruk öncelikli"
        summary = "AI özeti, duyuru-manşet-banner hattının aynı anda açık olduğunu; editoryal akış temizlenmeden vitrin ve moderasyon baskısının artacağını söylüyor."
    elif receipt_backlog > 0 or pending_group_requests > 0:
        headline = "Portalda operasyonel takip başlıkları öne çıkıyor"
        summary = "AI özeti, onay bekleyen alındılar ve grup taleplerinin yönetim dikkatini istediğini; içerik kuyruğunun ise daha sakin kaldığını gösteriyor."
    else:
        headline = "Portal yönetim yüzeyi dengeli"
        summary = "AI özeti, yönetim ekranında kırmızı baskının düşük olduğunu; bu nedenle moderasyon ve grup yaşam döngüsünün rutin şekilde izlenmesinin yeterli olacağını belirtiyor."

    bullets = [
        f"Editoryal toplam {total_editorial}; duyuru {announcements}, manşet {headlines}, banner {banners} olarak dağılıyor.",
        f"Bekleyen grup talebi {pending_group_requests}, alındı kuyruğu {receipt_backlog}, gizlenen paylaşım {hidden_posts} ve yorumu kilitli kayıt {locked_posts} olarak izleniyor.",
        f"Yönetilen aktif grup kartı görünümü {group_count} satır taşıyor; bu alan hızlı operasyon bağlantısı olarak kullanılabilir.",
    ]
    actions = [
        {"label": "Editoryal", "value": total_editorial, "tone": "critical" if total_editorial else "calm"},
        {"label": "Alındı kuyruğu", "value": receipt_backlog, "tone": "critical" if receipt_backlog else "calm"},
        {"label": "Grup talepleri", "value": pending_group_requests, "tone": "watch" if pending_group_requests else "calm"},
        {"label": "Moderasyon izi", "value": hidden_posts + locked_posts, "tone": "watch" if hidden_posts + locked_posts else "calm"},
    ]
    return {
        "badge": _badge_from_tone(tone),
        "tone": tone,
        "headline": headline,
        "summary": summary,
        "bullets": bullets,
        "actions": actions,
    }


def build_portal_digest_ai_panel(digest: Any) -> dict[str, Any]:
    digest = digest or {}
    summary = _get(digest, "summary", {}) or {}
    posts = _to_int(_get(summary, "posts"))
    comments = _to_int(_get(summary, "comments"))
    reactions = _to_int(_get(summary, "reactions"))
    pending_ack = _to_int(_get(summary, "pending_ack"))
    upcoming_events = _to_int(_get(summary, "upcoming_events"))
    top_groups = list(_get(digest, "top_groups", []) or [])
    top_authors = list(_get(digest, "top_authors", []) or [])
    top_hashtags = list(_get(digest, "top_hashtags", []) or [])
    engagement_load = comments + reactions
    tone = _tone_from_counts(critical=pending_ack, warning=upcoming_events)
    if pending_ack > 0:
        headline = "Portal özetinde bekleyen alındılar dikkat istiyor"
        summary_text = "AI özeti, paylaşım ve etkileşim hacmi iyi görünse de resmi duyuru tarafında bekleyen alındıların yönetici görünümünde ayrı izlenmesini öneriyor."
    elif upcoming_events > 0:
        headline = "Portal hareketi etkinlik takvimiyle birlikte okunmalı"
        summary_text = "AI özeti, içerik ritminin yaklaşan etkinliklerle desteklendiğini; bu yüzden özet ekranının takvim bağlantısıyla birlikte kullanılmasının verimli olacağını söylüyor."
    else:
        headline = "Portal nabzı dengeli"
        summary_text = "AI özeti, paylaşımlar ve etkileşimlerin dengeli ilerlediğini; izleme odağının daha çok öne çıkan kişi ve grup trendlerine kayabileceğini belirtiyor."

    group_label = ", ".join(str(_get(item, "label")) for item in top_groups[:2]) or "Grup verisi yok"
    author_label = ", ".join(str(_get(item, "label")) for item in top_authors[:2]) or "Yazar verisi yok"
    tag_label = ", ".join(str(_get(item, "label")) for item in top_hashtags[:2]) or "Etiket verisi yok"
    bullets = [
        f"Seçili pencerede {posts} paylaşım, {comments} yorum ve {reactions} tepki kaydı var; toplam etkileşim yükü {engagement_load} olarak okunuyor.",
        f"Bekleyen alındı {pending_ack}, yaklaşan etkinlik {upcoming_events}; bu iki başlık portal özetinin operasyon tarafını belirliyor.",
        f"Öne çıkanlar: gruplar {group_label}; kişiler {author_label}; trend etiketler {tag_label}.",
    ]
    actions = [
        {"label": "Paylaşım", "value": posts, "tone": "calm"},
        {"label": "Etkileşim", "value": engagement_load, "tone": "watch" if engagement_load else "calm"},
        {"label": "Bekleyen alındı", "value": pending_ack, "tone": "critical" if pending_ack else "calm"},
        {"label": "Etkinlik", "value": upcoming_events, "tone": "watch" if upcoming_events else "calm"},
    ]
    return {
        "badge": _badge_from_tone(tone),
        "tone": tone,
        "headline": headline,
        "summary": summary_text,
        "bullets": bullets,
        "actions": actions,
    }

