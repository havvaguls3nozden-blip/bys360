from __future__ import annotations

# Bu dosya app.services.ai.dashboard_panels dış public API'sini bozmadan ayrıştırılmıştır.


from app.services.ai.dashboard_panel_common import (
    Any,
    Iterable,
    _get,
    _to_int,
    _to_float,
    _tone_from_counts,
    _badge_from_tone,
)

def build_strategy_management_ai_panel(*, stats: Any | None = None, plans: Iterable[Any] | None = None, goals: Iterable[Any] | None = None, actions: Iterable[Any] | None = None, documents: Iterable[Any] | None = None, media: Iterable[Any] | None = None, selected_year: Any | None = None) -> dict[str, Any]:
    stats = stats or {}
    plans = list(plans or [])
    goals = list(goals or [])
    actions = list(actions or [])
    documents = list(documents or [])
    media = list(media or [])

    plan_count = _to_int((stats or {}).get('plan_count'), len(plans))
    goal_count = _to_int((stats or {}).get('goal_count'), len(goals))
    action_count = _to_int((stats or {}).get('action_count'), len(actions))
    document_count = _to_int((stats or {}).get('document_count'), len(documents))
    media_count = _to_int((stats or {}).get('media_count'), len(media))
    delayed_actions = sum(1 for row in actions if str(_get(row, 'status', '') or '').lower() in {'delayed', 'risk', 'behind'})
    completed_actions = sum(1 for row in actions if str(_get(row, 'status', '') or '').lower() in {'completed', 'done', 'tamamlandi'})
    progress_values = [_to_float(_get(row, 'progress_percent')) for row in actions if _get(row, 'progress_percent') is not None]
    avg_progress = (sum(progress_values) / len(progress_values)) if progress_values else 0.0
    goals_without_actions = 0
    for item in goals:
        row = _get(item, 'row', item)
        action_count_for_goal = _to_int(_get(item, 'action_count'))
        if action_count_for_goal == 0 and row is not None:
            goals_without_actions += 1
    tone = _tone_from_counts(critical=delayed_actions + goals_without_actions, warning=max(goal_count - completed_actions, 0))
    year_label = str(selected_year) if selected_year else 'tüm yıllar'

    if delayed_actions > 0:
        headline = 'Strateji akışında geciken faaliyetler öne çıkıyor'
        summary = 'AI özeti, OKR ve strateji tarafında önce geciken faaliyetlerin ve aksiyona dönüşmemiş hedeflerin ele alınmasını öneriyor.'
    elif goals_without_actions > 0:
        headline = 'Hedefler ile faaliyet omurgası arasında boşluklar var'
        summary = 'AI özeti, bazı hedeflerin hâlâ faaliyete bağlanmadığını; kanıt ve ilerleme takibinin bu kayıtlar üzerinden güçlendirilmesi gerektiğini gösteriyor.'
    else:
        headline = 'Strateji görünümü dengeli ilerliyor'
        summary = 'AI özeti, plan, hedef, faaliyet ve kanıt akışının aynı yüzeyde okunabildiğini; ana odakta ilerleme ritminin kaldığını gösteriyor.'

    bullets = [
        f'Seçili filtre {year_label}; {plan_count} plan, {goal_count} hedef ve {action_count} faaliyet izleniyor.',
        f'Ortalama faaliyet ilerlemesi %{avg_progress:.1f}; tamamlanan {completed_actions}, gecikme işareti taşıyan {delayed_actions} kayıt var.',
        f'{goals_without_actions} hedef için bağlı faaliyet görünmüyor; kanıt akışında {document_count} belge ve {media_count} görsel bulunuyor.',
    ]
    spotlight = []
    if goals:
        first_goal = _get(_get(goals[0], 'row', goals[0]), 'title')
        if first_goal:
            spotlight.append({'label': 'Öne çıkan hedef', 'value': str(first_goal)})
    if plans:
        first_plan = _get(plans[0], 'title')
        if first_plan:
            spotlight.append({'label': 'Üst plan', 'value': str(first_plan)})

    actions_rows = [
        {'label': 'Geciken faaliyet', 'value': delayed_actions, 'tone': 'critical' if delayed_actions else 'calm'},
        {'label': 'Faaliyetsiz hedef', 'value': goals_without_actions, 'tone': 'watch' if goals_without_actions else 'calm'},
        {'label': 'Belge kanıtı', 'value': document_count, 'tone': 'calm'},
        {'label': 'Ortalama ilerleme', 'value': f'%{avg_progress:.1f}', 'tone': 'watch' if avg_progress < 40 and action_count else 'calm'},
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets[:4],
        'actions': actions_rows,
        'spotlight': spotlight,
    }


def build_strategy_goal_ai_panel(*, goal: Any, actions: Iterable[Any] | None = None, indicators: Iterable[Any] | None = None, meetings: Iterable[Any] | None = None, documents: Iterable[Any] | None = None, media: Iterable[Any] | None = None) -> dict[str, Any]:
    actions = list(actions or [])
    indicators = list(indicators or [])
    meetings = list(meetings or [])
    documents = list(documents or [])
    media = list(media or [])

    progress_values = [_to_float(_get(row, 'progress_percent')) for row in actions if _get(row, 'progress_percent') is not None]
    avg_progress = (sum(progress_values) / len(progress_values)) if progress_values else 0.0
    delayed_actions = sum(1 for row in actions if str(_get(row, 'status', '') or '').lower() in {'delayed', 'risk', 'behind'})
    weak_indicators = sum(1 for row in indicators if _get(row, 'current_value') in (None, ''))
    tone = _tone_from_counts(critical=delayed_actions, warning=weak_indicators + (0 if meetings else 1 if actions else 0))

    if delayed_actions > 0:
        headline = 'Bu hedefte geciken faaliyetler bulunuyor'
        summary = 'AI özeti, hedefin ilerleme ritmini önce gecikme işareti taşıyan faaliyetler ve eksik gösterge okumaları üzerinden değerlendiriyor.'
    elif weak_indicators > 0:
        headline = 'Gösterge görünümü henüz tam değil'
        summary = 'AI özeti, hedef için belge ve faaliyet akışı bulunsa da bazı göstergelerin güncel değer taşımadığını işaret ediyor.'
    else:
        headline = 'Hedef görünümü kontrollü ilerliyor'
        summary = 'AI özeti, hedefe bağlı faaliyet, gösterge ve kanıt alanlarının birlikte okunabildiğini gösteriyor.'

    bullets = [
        f'Hedefe bağlı {len(actions)} faaliyet ve {len(indicators)} gösterge bulunuyor.',
        f'Ortalama faaliyet ilerlemesi %{avg_progress:.1f}; gecikme işareti taşıyan {delayed_actions} faaliyet var.',
        f'Kanıt tarafında {len(documents)} belge, {len(media)} görsel ve {len(meetings)} toplantı kaydı izleniyor.',
    ]
    if _get(goal, 'priority_level'):
        bullets.append(f'Öncelik seviyesi: {_get(goal, "priority_level")}.')

    spotlight = []
    if actions:
        spotlight.append({'label': 'İlk faaliyet', 'value': str(_get(actions[0], 'title') or '-')})
    if indicators:
        spotlight.append({'label': 'İlk gösterge', 'value': str(_get(indicators[0], 'title') or '-')})

    actions_rows = [
        {'label': 'Geciken faaliyet', 'value': delayed_actions, 'tone': 'critical' if delayed_actions else 'calm'},
        {'label': 'Eksik gösterge', 'value': weak_indicators, 'tone': 'watch' if weak_indicators else 'calm'},
        {'label': 'Belge kanıtı', 'value': len(documents), 'tone': 'calm'},
        {'label': 'Toplantı kaydı', 'value': len(meetings), 'tone': 'watch' if not meetings and actions else 'calm'},
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets[:4],
        'actions': actions_rows,
        'spotlight': spotlight,
    }


def build_education_management_ai_panel(*, stats: Any | None = None, records: Iterable[Any] | None = None, documents: Iterable[Any] | None = None, media: Iterable[Any] | None = None, selected_year: Any | None = None) -> dict[str, Any]:
    stats = stats or {}
    records = list(records or [])
    documents = list(documents or [])
    media = list(media or [])

    record_count = _to_int((stats or {}).get('record_count'), len(records))
    document_count = _to_int((stats or {}).get('document_count'), len(documents))
    media_count = _to_int((stats or {}).get('media_count'), len(media))
    participant_total = sum(_to_int(_get(item, 'participant_count')) for item in records)
    pending_scan_total = sum(_to_int(_get(item, 'review_pending_count')) for item in records)
    sheet_total = sum(_to_int(_get(item, 'sheet_count')) for item in records)
    no_participant_records = sum(1 for item in records if _to_int(_get(item, 'participant_count')) == 0)
    tone = _tone_from_counts(critical=pending_scan_total, warning=no_participant_records)
    year_label = str(selected_year) if selected_year else 'tüm yıllar'

    if pending_scan_total > 0:
        headline = 'Eğitim arşivinde işlenmeyi bekleyen imzalı föyler var'
        summary = 'AI özeti, eğitim operasyonunda önce tarama inceleme kuyruğu ve eksik kanıt alanlarının temizlenmesini öneriyor.'
    elif no_participant_records > 0:
        headline = 'Katılımcı omurgası eksik kalan eğitim kayıtları var'
        summary = 'AI özeti, bazı eğitimlerin belge ve arşiv akışı olsa da katılımcı listelerinin henüz tamamlanmadığını gösteriyor.'
    else:
        headline = 'Eğitim görünümü kontrollü ilerliyor'
        summary = 'AI özeti, kayıt, katılımcı, belge ve fotoğraf akışının aynı yüzeyde izlenebildiğini ve ana odağın arşiv kalitesinde olduğunu gösteriyor.'

    bullets = [
        f'Seçili filtre {year_label}; {record_count} eğitim kaydı, {participant_total} toplam katılımcı ve {sheet_total} yoklama föyü izleniyor.',
        f'Kanıt alanında {document_count} belge ve {media_count} görsel bulunuyor.',
        f'{pending_scan_total} tarama incelemesi bekliyor; katılımcısız kayıt sayısı {no_participant_records}.',
    ]
    spotlight = []
    if records:
        first_title = _get(_get(records[0], 'row', records[0]), 'title')
        if first_title:
            spotlight.append({'label': 'İlk eğitim kaydı', 'value': str(first_title)})

    actions_rows = [
        {'label': 'İnceleme bekleyen tarama', 'value': pending_scan_total, 'tone': 'critical' if pending_scan_total else 'calm'},
        {'label': 'Katılımcısız kayıt', 'value': no_participant_records, 'tone': 'watch' if no_participant_records else 'calm'},
        {'label': 'Belge sayısı', 'value': document_count, 'tone': 'calm'},
        {'label': 'Fotoğraf arşivi', 'value': media_count, 'tone': 'calm'},
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets[:4],
        'actions': actions_rows,
        'spotlight': spotlight,
    }


def build_education_detail_ai_panel(*, record: Any, participants: Iterable[Any] | None = None, sessions: Iterable[Any] | None = None, attendance_sheets: Iterable[Any] | None = None, documents: Iterable[Any] | None = None, media: Iterable[Any] | None = None, export_status: Any | None = None, roster_summary: Any | None = None) -> dict[str, Any]:
    participants = list(participants or [])
    sessions = list(sessions or [])
    attendance_sheets = list(attendance_sheets or [])
    documents = list(documents or [])
    media = list(media or [])
    roster_summary = roster_summary or {}
    export_status = export_status or {}

    participant_count = _to_int((roster_summary or {}).get('participant_count'), len(participants))
    sheet_count = _to_int((roster_summary or {}).get('sheet_count'), len(attendance_sheets))
    signed_scan_count = _to_int((roster_summary or {}).get('signed_scan_count'))
    review_pending_count = _to_int((roster_summary or {}).get('review_pending_count'))
    missing_identity_count = _to_int((export_status or {}).get('missing_identity_count'))
    export_ready_count = _to_int((export_status or {}).get('export_ready_count'))
    tone = _tone_from_counts(critical=review_pending_count + missing_identity_count, warning=max(sheet_count - signed_scan_count, 0))

    if missing_identity_count > 0:
        headline = 'Bakanlık dışa aktarımı öncesi kimlik tamamlama gerekiyor'
        summary = 'AI özeti, katılımcı listesinde hassas kimlik alanı eksik olan kayıtlar bulunduğunu ve dışa aktarım öncesi bunların tamamlanması gerektiğini işaret ediyor.'
    elif review_pending_count > 0:
        headline = 'İmzalı föy taramalarında inceleme kuyruğu var'
        summary = 'AI özeti, eğitim sonu kapanışında önce imzalı föy taramalarının doğrulanmasını ve arşiv durumunun netleştirilmesini öneriyor.'
    else:
        headline = 'Eğitim detay görünümü kontrollü ilerliyor'
        summary = 'AI özeti, katılımcı, oturum, belge ve arşiv akışının aynı sayfada kapanabildiğini gösteriyor.'

    bullets = [
        f'{participant_count} katılımcı, {len(sessions)} oturum ve {sheet_count} yoklama föyü bulunuyor.',
        f'İmzalı tarama {signed_scan_count}; inceleme bekleyen tarama {review_pending_count}.',
        f'Belge tarafında {len(documents)} belge, görsel tarafında {len(media)} medya kaydı izleniyor.',
    ]
    if export_ready_count or missing_identity_count:
        bullets.append(f'Bakanlık dışa aktarımına hazır {export_ready_count}, eksik hassas kimlik nedeniyle bekleyen {missing_identity_count} kayıt var.')

    spotlight = []
    if _get(record, 'trainer_name'):
        spotlight.append({'label': 'Eğitmen', 'value': str(_get(record, 'trainer_name'))})
    if participants:
        first_name = _get(participants[0], 'participant_name_snapshot') or _get(_get(participants[0], 'user'), 'full_name')
        if first_name:
            spotlight.append({'label': 'İlk katılımcı', 'value': str(first_name)})

    actions_rows = [
        {'label': 'İnceleme bekleyen tarama', 'value': review_pending_count, 'tone': 'critical' if review_pending_count else 'calm'},
        {'label': 'Eksik kimlik kaydı', 'value': missing_identity_count, 'tone': 'critical' if missing_identity_count else 'calm'},
        {'label': 'Hazır dışa aktarım', 'value': export_ready_count, 'tone': 'watch' if export_ready_count else 'calm'},
        {'label': 'Katılımcı sayısı', 'value': participant_count, 'tone': 'calm'},
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets[:4],
        'actions': actions_rows,
        'spotlight': spotlight,
    }


def build_repository_search_ai_panel(*, module_heading_label: str | None = None, query: str | None = None, tag: str | None = None, kind: str | None = None, result_counts: Any | None = None, documents: Iterable[Any] | None = None, media_items: Iterable[Any] | None = None, albums: Iterable[Any] | None = None) -> dict[str, Any]:
    result_counts = result_counts or {}
    documents = list(documents or [])
    media_items = list(media_items or [])
    albums = list(albums or [])

    document_count = _to_int(_get(result_counts, 'documents'), len(documents))
    media_count = _to_int(_get(result_counts, 'media'), len(media_items))
    album_count = _to_int(_get(result_counts, 'albums'), len(albums))
    total = document_count + media_count + album_count
    untagged_documents = sum(1 for item in documents if not list(_get(item, 'tags', []) or []))
    dominant_kind = max(
        [('Belge', document_count), ('Görsel', media_count), ('Albüm', album_count)],
        key=lambda pair: pair[1],
    )[0] if total else 'Sonuç'
    tone = _tone_from_counts(critical=int(bool(query) and total == 0), warning=untagged_documents)
    module_label = module_heading_label or 'Kurumsal Depo'
    kind_label = {'all': 'Tüm sonuçlar', 'document': 'Belge odaklı', 'media': 'Görsel odaklı', 'album': 'Albüm odaklı'}.get((kind or 'all').strip().lower(), 'Tüm sonuçlar')

    if total == 0 and (query or tag):
        headline = f'{module_label} içinde arama dar kalmış görünüyor'
        summary = 'AI özeti, sonuç dönmeyen aramada önce anahtar kelimeyi genişletmeyi ve etiket filtresini sadeleştirmeyi öneriyor.'
    elif untagged_documents > 0:
        headline = f'{module_label} sonuçlarında etiket standardı güçlendirilmeli'
        summary = 'AI özeti, arama görünümünde bulunan bazı belgelerin etiket omurgasının zayıf kaldığını ve yeniden bulunabilirlik için etiket düzeni gerektiğini gösteriyor.'
    else:
        headline = f'{module_label} arama görünümü okunaklı ilerliyor'
        summary = 'AI özeti, belge, görsel ve albüm sonuçlarının aynı yüzeyde okunabildiğini; ana odakta doğru filtre ile kısa yoldan doğru kayda gitmenin kaldığını belirtiyor.'

    bullets = [
        f'Sonuç dağılımı: {document_count} belge, {media_count} görsel ve {album_count} albüm; baskın tür {dominant_kind.lower()}.',
        f'Arama ifadesi: {query or "Yok"}; etiket filtresi: {tag or "Yok"}; görünüm: {kind_label}.',
        f'Etiketsiz belge sayısı {untagged_documents}; bu alanlar tekrar bulunabilirlik kalitesini doğrudan etkiler.',
    ]
    top_document = _get(_get(documents[0], 'document') if documents else None, 'title')
    spotlight = []
    if top_document:
        spotlight.append({'label': 'İlk belge', 'value': str(top_document)})
    if albums:
        spotlight.append({'label': 'İlk albüm', 'value': str(_get(_get(albums[0], 'album'), 'title') or '-')})

    actions = [
        {'label': 'Belge', 'value': document_count, 'tone': 'calm'},
        {'label': 'Görsel', 'value': media_count, 'tone': 'calm'},
        {'label': 'Albüm', 'value': album_count, 'tone': 'calm'},
        {'label': 'Etiketsiz belge', 'value': untagged_documents, 'tone': 'watch' if untagged_documents else 'calm'},
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets[:4],
        'actions': actions,
        'spotlight': spotlight,
    }


def build_repository_document_ai_panel(*, document: Any, versions: Iterable[Any] | None = None, download_count: int = 0, document_tags: Iterable[str] | None = None, link: Any = None, edit_history_rows: Iterable[Any] | None = None) -> dict[str, Any]:
    versions = list(versions or [])
    document_tags = list(document_tags or [])
    edit_history_rows = list(edit_history_rows or [])
    version_count = len(versions)
    latest_version = versions[0] if versions else None
    edit_count = len(edit_history_rows)
    tone = _tone_from_counts(critical=int(version_count <= 1 and not document_tags), warning=int(edit_count == 0) + int(not document_tags))

    if not document_tags:
        headline = 'Belge bulunuyor ama etiket omurgası zayıf'
        summary = 'AI özeti, belge detayında etiket alanı boş kaldığı için benzer arama ve raporlamada tekrar bulunabilirliğin zayıflayacağını işaret ediyor.'
    elif edit_count == 0:
        headline = 'Belge sürümü kayıtlı ama düzenleme izi sınırlı'
        summary = 'AI özeti, sürüm yapısının mevcut olduğunu ancak karar ve değişiklik notlarının düzenleme geçmişinde daha görünür tutulmasının fayda sağlayacağını gösteriyor.'
    else:
        headline = 'Belge detay görünümü kontrollü ilerliyor'
        summary = 'AI özeti, sürüm, etiket ve düzenleme izi bilgilerinin belgeyi hem arşiv hem denetim tarafında okunabilir kıldığını gösteriyor.'

    bullets = [
        f'{version_count} sürüm, {download_count} indirme ve {len(document_tags)} etiket ile belge dolaşımı izleniyor.',
        f'Bağlı hedef: {str(_get(link, "target_table") or "Kurumsal depo")}; modül: {str(_get(link, "module_type") or "repository")}.',
        f'Düzenleme izi {edit_count} kayıt içeriyor; güncel dosya {str(_get(latest_version, "original_filename") or _get(document, "original_filename") or "-")}.',
    ]
    if latest_version and _get(latest_version, 'change_note'):
        bullets.append(f'Son sürüm notu: {str(_get(latest_version, "change_note"))[:120]}')

    spotlight = []
    if document_tags:
        spotlight.append({'label': 'Etiketler', 'value': ', '.join(str(tag) for tag in document_tags[:4])})
    if latest_version:
        spotlight.append({'label': 'Güncel sürüm', 'value': f'v{_to_int(_get(latest_version, "version_no"), 1)}'})

    actions = [
        {'label': 'Sürüm', 'value': version_count, 'tone': 'watch' if version_count <= 1 else 'calm'},
        {'label': 'Etiket', 'value': len(document_tags), 'tone': 'watch' if not document_tags else 'calm'},
        {'label': 'İndirme', 'value': download_count, 'tone': 'calm'},
        {'label': 'Düzenleme izi', 'value': edit_count, 'tone': 'watch' if edit_count == 0 else 'calm'},
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets[:4],
        'actions': actions,
        'spotlight': spotlight,
    }


def build_strategy_plan_ai_panel(*, plan: Any, goals: Iterable[Any] | None = None, meetings: Iterable[Any] | None = None, documents: Iterable[Any] | None = None, media_items: Iterable[Any] | None = None, zip_download_count: int = 0) -> dict[str, Any]:
    goals = list(goals or [])
    meetings = list(meetings or [])
    documents = list(documents or [])
    media_items = list(media_items or [])

    goal_count = len(goals)
    meeting_count = len(meetings)
    decision_missing = sum(1 for item in meetings if not str(_get(item, 'decisions') or '').strip())
    followup_missing = sum(1 for item in meetings if not str(_get(item, 'follow_up_actions') or '').strip())
    delayed_goals = sum(1 for item in goals if str(_get(item, 'status') or '').strip().lower() in {'delayed', 'risk', 'at_risk', 'gecikiyor'})
    tone = _tone_from_counts(critical=decision_missing + delayed_goals, warning=followup_missing)

    if decision_missing > 0:
        headline = 'Toplantı-karar akışında eksik karar notları var'
        summary = 'AI özeti, strateji planına bağlı bazı toplantıların karar alanı boş kaldığı için izleme ve görev çıkarımı tarafında açıklık oluştuğunu gösteriyor.'
    elif followup_missing > 0:
        headline = 'Kararlar alınmış ama takip aksiyonları tam kapanmamış'
        summary = 'AI özeti, toplantı notları ile takip adımları arasında boşluk kaldığını; bir sonraki yönetim turunda takip aksiyonlarının netleştirilmesinin fayda sağlayacağını öneriyor.'
    else:
        headline = 'Strateji planı toplantı ve karar akışını taşıyabiliyor'
        summary = 'AI özeti, plan, hedef, toplantı ve kanıt ilişkilerinin aynı detay görünümünde okunabildiğini ve karar takibinin kurumsal hafızaya işlendiğini gösteriyor.'

    bullets = [
        f'Plan altında {goal_count} hedef, {meeting_count} toplantı, {len(documents)} belge ve {len(media_items)} görsel bulunuyor.',
        f'Karar alanı boş toplantı {decision_missing}; takip aksiyonu boş toplantı {followup_missing}.',
        f'ZIP indirme sayısı {zip_download_count}; planın arşiv dolaşımı aktif biçimde izleniyor.',
    ]
    if meetings:
        latest = meetings[0]
        latest_label = str(_get(latest, 'title') or '-')
        latest_date = _get(latest, 'meeting_date')
        bullets.append(f'En güncel toplantı: {latest_label} ({latest_date.strftime("%d.%m.%Y") if getattr(latest_date, "strftime", None) else latest_date or "tarih yok"}).')

    spotlight = []
    if goals:
        spotlight.append({'label': 'İlk hedef', 'value': str(_get(goals[0], 'title') or '-')})
    if meetings:
        spotlight.append({'label': 'İlk toplantı', 'value': str(_get(meetings[0], 'title') or '-')})

    actions = [
        {'label': 'Hedef', 'value': goal_count, 'tone': 'calm'},
        {'label': 'Toplantı', 'value': meeting_count, 'tone': 'calm'},
        {'label': 'Kararı eksik', 'value': decision_missing, 'tone': 'critical' if decision_missing else 'calm'},
        {'label': 'Takibi eksik', 'value': followup_missing, 'tone': 'watch' if followup_missing else 'calm'},
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets[:4],
        'actions': actions,
        'spotlight': spotlight,
    }


def build_repository_dashboard_ai_panel(*, education_stats: Any | None = None, strategy_stats: Any | None = None, archive_counts: dict[str, Any] | None = None, zip_stats: dict[str, Any] | None = None, popular_tags: Iterable[Any] | None = None, recent_activity: Iterable[Any] | None = None) -> dict[str, Any]:
    education_stats = education_stats or {}
    strategy_stats = strategy_stats or {}
    archive_counts = archive_counts or {}
    zip_stats = zip_stats or {}
    popular_tags = list(popular_tags or [])
    recent_activity = list(recent_activity or [])

    education_records = _to_int(_get(education_stats, 'record_count'))
    education_documents = _to_int(_get(education_stats, 'document_count'))
    strategy_plans = _to_int(_get(strategy_stats, 'plan_count'))
    strategy_actions = _to_int(_get(strategy_stats, 'action_count'))
    archive_total = sum(_to_int(value) for value in archive_counts.values())
    zip_total = sum(_to_int(value) for value in zip_stats.values())
    active_modules = sorted({str(_get(row, 'module_type') or 'repository') for row in recent_activity})
    top_tag = popular_tags[0][0] if popular_tags else None
    recent_zip_activity = sum(1 for row in recent_activity if 'zip' in str(_get(row, 'action') or '').lower() or 'zip' in str(_get(row, 'summary') or '').lower())

    tone = _tone_from_counts(critical=archive_total if archive_total > 20 else 0, warning=recent_zip_activity + max(zip_total - 15, 0))
    if archive_total > 20:
        headline = 'Depo kullanımında arşiv yükü büyüyor'
        summary = 'AI özeti, depo panelinde önce arşivde biriken belge ve medya kalemlerinin gözden geçirilmesini; ardından ZIP dolaşımı ve etiket düzeninin dengelenmesini öneriyor.'
    elif zip_total > 0:
        headline = 'Depo dolaşımı aktif ve izlenebilir durumda'
        summary = 'AI özeti, eğitim ve strateji kaynaklarının hem belge hem ZIP dolaşımıyla kullanıldığını; yönetici odağında dolaşım yoğunluğu ve etiket standardının birlikte izlenmesi gerektiğini gösteriyor.'
    else:
        headline = 'Depo paneli temel görünürlüğü taşıyor'
        summary = 'AI özeti, depo panelinde çekirdek metriklerin görünür olduğunu; bir sonraki odakta etiket standardı ve hareket ritminin güçlendirilmesi gerektiğini belirtiyor.'

    bullets = [
        f'Eğitim tarafında {education_records} kayıt ve {education_documents} belge; stratejide {strategy_plans} plan ve {strategy_actions} faaliyet izleniyor.',
        f'Arşiv yükü toplam {archive_total}; ZIP indirme toplamı {zip_total}.',
        f'Son hareket akışında {len(recent_activity)} kayıt ve {recent_zip_activity} ZIP temaslı iz düşümü var.',
        f'Öne çıkan etiket: {top_tag or "Henüz öne çıkan etiket yok"}; aktif modüller: {", ".join(active_modules[:3]) or "veri yok"}.',
    ]
    spotlight = []
    if recent_activity:
        spotlight.append({'label': 'Son hareket', 'value': str(_get(recent_activity[0], 'summary') or _get(recent_activity[0], 'action') or '-')[:120]})
    if top_tag:
        spotlight.append({'label': 'Popüler etiket', 'value': str(top_tag)})

    actions = [
        {'label': 'Arşiv yükü', 'value': archive_total, 'tone': 'critical' if archive_total > 20 else ('watch' if archive_total else 'calm')},
        {'label': 'ZIP toplamı', 'value': zip_total, 'tone': 'watch' if zip_total else 'calm'},
        {'label': 'Son hareket', 'value': len(recent_activity), 'tone': 'calm'},
        {'label': 'Etiket kümesi', 'value': len(popular_tags), 'tone': 'calm'},
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets[:4],
        'actions': actions,
        'spotlight': spotlight,
    }


def build_repository_tag_report_ai_panel(*, tag_rows: Iterable[Any] | None = None, module_filter: str | None = None) -> dict[str, Any]:
    tag_rows = list(tag_rows or [])
    total_tags = len(tag_rows)
    total_documents = sum(_to_int(_get(row, 'document_count')) for row in tag_rows)
    total_downloads = sum(_to_int(_get(row, 'download_count')) for row in tag_rows)
    weak_tags = sum(1 for row in tag_rows if _to_int(_get(row, 'document_count')) <= 1)
    cross_module = sum(1 for row in tag_rows if len(list(_get(row, 'modules') or [])) > 1)
    top_tag = _get(tag_rows[0], 'tag') if tag_rows else None
    tone = _tone_from_counts(critical=int(total_tags == 0), warning=weak_tags)

    if total_tags == 0:
        headline = 'Etiket raporunda henüz yönetsel veri oluşmamış'
        summary = 'AI özeti, etiket standardı olmadan belge tekrar bulunabilirliğinin zayıflayacağını; önce temel etiket setlerinin oluşturulması gerektiğini gösteriyor.'
    elif weak_tags > 0:
        headline = 'Etiket dağılımı geniş ama derinliği sınırlı'
        summary = 'AI özeti, bazı etiketlerin yalnızca tekil belgelerde kaldığını; ortak etiket standardı ile rapor kalitesinin güçlendirilebileceğini işaret ediyor.'
    else:
        headline = 'Etiket raporu kurumsal hafızayı destekliyor'
        summary = 'AI özeti, etiketlerin belge kümelerini görünür kıldığını ve özellikle çapraz modül kullanılan başlıkların yönetici aramalarında değer ürettiğini gösteriyor.'

    bullets = [
        f'Seçili modül: {module_filter or "Tümü"}; toplam {total_tags} etiket, {total_documents} belge ve {total_downloads} indirme ilişkisi izleniyor.',
        f'Tekil kullanımda kalan etiket sayısı {weak_tags}; çapraz modül kullanılan etiket sayısı {cross_module}.',
        f'Öne çıkan etiket: {top_tag or "Yok"}.',
    ]
    spotlight = []
    if tag_rows:
        top = tag_rows[0]
        spotlight.append({'label': 'İlk etiket', 'value': f"{_get(top, 'tag') or '-'} · {_to_int(_get(top, 'document_count'))} belge"})
        docs = list(_get(top, 'document_titles') or [])
        if docs:
            spotlight.append({'label': 'İlk belge kümesi', 'value': ', '.join(str(x) for x in docs[:2])})

    actions = [
        {'label': 'Etiket', 'value': total_tags, 'tone': 'calm'},
        {'label': 'Tekil etiket', 'value': weak_tags, 'tone': 'watch' if weak_tags else 'calm'},
        {'label': 'Çapraz modül', 'value': cross_module, 'tone': 'calm'},
        {'label': 'İndirme izi', 'value': total_downloads, 'tone': 'watch' if total_downloads else 'calm'},
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets[:4],
        'actions': actions,
        'spotlight': spotlight,
    }


def build_repository_zip_report_ai_panel(*, report_rows: Iterable[Any] | None = None, module_totals: Iterable[Any] | None = None, actor_totals: Iterable[Any] | None = None, target_totals: Iterable[Any] | None = None, stats: dict[str, Any] | None = None) -> dict[str, Any]:
    report_rows = list(report_rows or [])
    module_totals = list(module_totals or [])
    actor_totals = list(actor_totals or [])
    target_totals = list(target_totals or [])
    stats = stats or {}
    total = _to_int(stats.get('total'), len(report_rows))
    top_module = module_totals[0][0] if module_totals else None
    top_actor = actor_totals[0][0] if actor_totals else None
    repeated_targets = sum(1 for _, count in target_totals if _to_int(count) > 1)
    recent_window = report_rows[:20]
    recent_strategy = sum(1 for row in recent_window if str(_get(row, 'module_type') or '').lower() == 'strategy')
    recent_education = sum(1 for row in recent_window if str(_get(row, 'module_type') or '').lower() == 'education')
    tone = _tone_from_counts(critical=int(total == 0), warning=repeated_targets)

    if total == 0:
        headline = 'ZIP hareketinde henüz izlenecek kayıt görünmüyor'
        summary = 'AI özeti, toplu arşiv indirme geçmişi oluşmadığı için dolaşım analizinin şimdilik sınırlı kaldığını gösteriyor.'
    elif repeated_targets > 0:
        headline = 'ZIP dolaşımında tekrar eden hedefler var'
        summary = 'AI özeti, aynı hedeflere tekrarlayan ZIP indirmeleri yapıldığını; bu alanların paketleme ve paylaşım kolaylığı açısından ayrıca izlenmesi gerektiğini öneriyor.'
    else:
        headline = 'ZIP dolaşımı kontrollü ve okunabilir durumda'
        summary = 'AI özeti, modül, aktör ve hedef bazlı indirme izlerinin depo yönetimi açısından yeterli görünürlük sağladığını belirtiyor.'

    bullets = [
        f'Toplam {total} ZIP indirme izi var; son pencerede strateji {recent_strategy}, eğitim {recent_education} kayıt taşıyor.',
        f'En yoğun modül: {top_module or "Yok"}; en yoğun aktör: {top_actor or "Yok"}.',
        f'Tekrarlayan hedef sayısı {repeated_targets}; bu alanlar sık erişilen paketleri işaret ediyor.',
    ]
    spotlight = []
    if target_totals:
        spotlight.append({'label': 'En yoğun hedef', 'value': f"{target_totals[0][0]} · {_to_int(target_totals[0][1])} indirme"})
    if actor_totals:
        spotlight.append({'label': 'En yoğun kullanıcı', 'value': f"{actor_totals[0][0]} · {_to_int(actor_totals[0][1])} kayıt"})

    actions = [
        {'label': 'ZIP kayıt', 'value': total, 'tone': 'calm' if total else 'watch'},
        {'label': 'Tekrarlayan hedef', 'value': repeated_targets, 'tone': 'watch' if repeated_targets else 'calm'},
        {'label': 'Modül kümesi', 'value': len(module_totals), 'tone': 'calm'},
        {'label': 'Aktör kümesi', 'value': len(actor_totals), 'tone': 'calm'},
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets[:4],
        'actions': actions,
        'spotlight': spotlight,
    }


def build_strategy_action_ai_panel(*, action: Any, indicators: Iterable[Any] | None = None, meetings: Iterable[Any] | None = None, documents: Iterable[Any] | None = None, media_items: Iterable[Any] | None = None, zip_download_count: int = 0) -> dict[str, Any]:
    indicators = list(indicators or [])
    meetings = list(meetings or [])
    documents = list(documents or [])
    media_items = list(media_items or [])
    progress = _to_float(_get(action, 'progress_percent'))
    delayed = str(_get(action, 'status') or '').strip().lower() in {'delayed', 'risk', 'behind', 'at_risk', 'gecikiyor'}
    missing_indicator_values = sum(1 for row in indicators if _get(row, 'current_value') in (None, ''))
    low_indicator_coverage = int(bool(indicators) and missing_indicator_values == len(indicators))
    meeting_without_followup = sum(1 for row in meetings if not str(_get(row, 'follow_up_actions') or '').strip())
    tone = _tone_from_counts(critical=int(delayed) + low_indicator_coverage, warning=missing_indicator_values + meeting_without_followup)

    if delayed:
        headline = 'Faaliyet akışında gecikme işareti var'
        summary = 'AI özeti, bu faaliyette önce ilerleme ritmi ile gösterge güncelliğinin birlikte kontrol edilmesini öneriyor.'
    elif missing_indicator_values > 0:
        headline = 'Gösterge izleme görünümü eksik okumalar taşıyor'
        summary = 'AI özeti, faaliyete bağlı göstergelerin bir kısmında güncel değer bulunmadığını; karar takibinin göstergeler tamamlandığında daha güçlü hale geleceğini gösteriyor.'
    else:
        headline = 'Faaliyet ve gösterge izleme birlikte okunabiliyor'
        summary = 'AI özeti, bu faaliyet için belge, toplantı ve gösterge akışının aynı detay ekranında anlamlı bir yönetim görünümü sunduğunu belirtiyor.'

    bullets = [
        f'Faaliyet ilerlemesi %{progress:.1f}; durum etiketi: {str(_get(action, "status") or "belirtilmedi").replace("_", " ")}.',
        f'{len(indicators)} gösterge, {missing_indicator_values} eksik güncel değer ve {len(meetings)} toplantı kaydı izleniyor.',
        f'Kanıt tarafında {len(documents)} belge, {len(media_items)} görsel ve {zip_download_count} ZIP indirme kaydı var.',
    ]
    risk_note = str(_get(action, 'risk_note') or '').strip()
    if risk_note:
        bullets.append(f'Risk notu: {risk_note[:140]}')

    spotlight = []
    if indicators:
        first = indicators[0]
        spotlight.append({'label': 'İlk gösterge', 'value': str(_get(first, 'title') or '-')})
    if meetings:
        first_meeting = meetings[0]
        spotlight.append({'label': 'Son toplantı', 'value': str(_get(first_meeting, 'title') or '-')})

    actions = [
        {'label': 'İlerleme', 'value': f'%{progress:.0f}', 'tone': 'critical' if delayed else ('watch' if progress < 40 and indicators else 'calm')},
        {'label': 'Eksik gösterge', 'value': missing_indicator_values, 'tone': 'watch' if missing_indicator_values else 'calm'},
        {'label': 'Takipsiz toplantı', 'value': meeting_without_followup, 'tone': 'watch' if meeting_without_followup else 'calm'},
        {'label': 'Belge kanıtı', 'value': len(documents), 'tone': 'calm'},
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets[:4],
        'actions': actions,
        'spotlight': spotlight,
    }


def build_repository_showcase_ai_panel(*, module_heading_label: str | None = None, display_mode: str | None = None, showcase_items: Iterable[Any] | None = None, can_manage_repository: bool = False) -> dict[str, Any]:
    showcase_items = list(showcase_items or [])
    total = len(showcase_items)
    sum(1 for item in showcase_items if str(_get(_get(item, 'album'), 'showcase_status') or '').strip().lower() == 'approved')
    pending = sum(1 for item in showcase_items if str(_get(_get(item, 'album'), 'showcase_status') or '').strip().lower() in {'unit_pending', 'corporate_pending'})
    preview_missing = sum(1 for item in showcase_items if not list(_get(item, 'preview_media', []) or []))
    institution_visible = sum(1 for item in showcase_items if str(_get(_get(item, 'album'), 'visibility_level') or '').strip().lower() == 'institution')
    actionable = sum(1 for item in showcase_items if _get(_get(item, 'workflow_permissions'), 'can_submit') or _get(_get(item, 'workflow_permissions'), 'can_withdraw'))
    module_label = module_heading_label or 'Kurumsal Galeri'
    display_label = 'kurumsal vitrin' if str(display_mode or '').lower() == 'institutional' else 'birim içi galeri'
    tone = _tone_from_counts(critical=int(total == 0 and str(display_mode or '').lower() == 'institutional'), warning=pending + preview_missing)

    if total == 0 and str(display_mode or '').lower() == 'institutional':
        headline = f'{module_label} için kurumsal vitrin boş görünüyor'
        summary = 'AI özeti, kurumsal vitrine taşınmış albüm bulunmadığını; önce birim içi galeriden uygun albümlerin onay akışına alınması gerektiğini işaret ediyor.'
    elif pending > 0 and can_manage_repository:
        headline = f'{module_label} galerisinde onay akışı hareketli'
        summary = 'AI özeti, vitrin görünümünde bekleyen albümlerin bulunduğunu ve yayınlanabilir albümlerin başlık/özet kalitesinin birlikte gözden geçirilmesinin fayda sağlayacağını gösteriyor.'
    else:
        headline = f'{module_label} {display_label} dengeli ilerliyor'
        summary = 'AI özeti, albüm, hedef bağlamı ve vitrin durumunun aynı ekranda okunabildiğini; ana odakta kürasyon ve seçili albümlerin güncelliğinin kaldığını gösteriyor.'

    bullets = [
        f'Toplam {total} albüm görünür durumda; kurumsal görünürlük taşıyan {institution_visible}, onay bekleyen {pending} albüm var.',
        f'Ön izleme alanı boş kalan {preview_missing} albüm, vitrin kalitesini ve ilk bakışta anlaşılabilirliği düşürüyor.',
        f'İşlem alınabilir akış sayısı {actionable}; onay akışına uygun albümler yönetici rolüne göre değişiyor.',
    ]

    spotlight = []
    first_title = None
    if showcase_items:
        first_title = _get(_get(showcase_items[0], 'album'), 'showcase_title') or _get(_get(showcase_items[0], 'album'), 'title')
    if first_title:
        spotlight.append({'label': 'İlk albüm', 'value': str(first_title)})
    if pending:
        spotlight.append({'label': 'Bekleyen akış', 'value': f'{pending} albüm onay zincirinde'})

    actions = [
        {'label': 'Görünür albüm', 'value': total, 'tone': 'calm' if total else 'watch'},
        {'label': 'Onay bekleyen', 'value': pending, 'tone': 'watch' if pending else 'calm'},
        {'label': 'Kurumsal vitrin', 'value': institution_visible, 'tone': 'calm'},
        {'label': 'Boş ön izleme', 'value': preview_missing, 'tone': 'watch' if preview_missing else 'calm'},
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets[:4],
        'actions': actions,
        'spotlight': spotlight,
    }


def build_repository_showcase_approval_ai_panel(*, album_rows: Iterable[Any] | None = None, stats: dict[str, Any] | None = None, status: str | None = None) -> dict[str, Any]:
    album_rows = list(album_rows or [])
    stats = stats or {}
    total_pending = _to_int(stats.get('unit_pending')) + _to_int(stats.get('corporate_pending'))
    approved = _to_int(stats.get('approved'))
    rejected = _to_int(stats.get('rejected'))
    actionable = sum(1 for row in album_rows if _get(_get(row, 'permissions'), 'can_unit_approve') or _get(_get(row, 'permissions'), 'can_corporate_approve') or _get(_get(row, 'permissions'), 'can_reject'))
    missing_showcase_copy = sum(1 for row in album_rows if not str(_get(_get(row, 'album'), 'showcase_title') or '').strip() or not str(_get(_get(row, 'album'), 'showcase_summary') or '').strip())
    status_label = {
        'unit_pending': 'birim onayı bekleyenler',
        'corporate_pending': 'kurumsal onayı bekleyenler',
        'approved': 'kurumsal vitrinde olanlar',
        'rejected': 'reddedilen akışlar',
        'withdrawn': 'geri çekilenler',
    }.get(str(status or '').lower(), 'seçili akış')
    tone = _tone_from_counts(critical=int(total_pending > 0 and actionable == 0), warning=total_pending + missing_showcase_copy)

    if total_pending > 0 and actionable == 0:
        headline = 'Onay kuyruğu var ancak işlem yetkisi sınırlı'
        summary = 'AI özeti, vitrin akışında bekleyen albümler bulunduğunu fakat seçili kullanıcı görünümünde doğrudan işlem alınamayan kayıtların baskın olduğunu gösteriyor.'
    elif missing_showcase_copy > 0:
        headline = 'Vitrin onayında başlık ve özet kalitesi güçlendirilmeli'
        summary = 'AI özeti, karar ekranındaki bazı albümlerde vitrin başlığı veya açıklama alanının zayıf kaldığını; onaydan önce metin kalitesinin güçlendirilmesinin fayda sağlayacağını işaret ediyor.'
    else:
        headline = 'Yayın zinciri ve karar görünümü okunaklı'
        summary = 'AI özeti, seçili onay kuyruğunda karar almayı hızlandıracak temel görünürlüğün mevcut olduğunu gösteriyor.'

    bullets = [
        f'Seçili görünüm: {status_label}; bu ekranda {len(album_rows)} albüm listeleniyor.',
        f'Toplam bekleyen akış {total_pending}; kurumsal vitrinde {approved}, reddedilen {rejected} albüm bulunuyor.',
        f'İşlem alınabilir satır {actionable}; başlık/özet eksiği taşıyan {missing_showcase_copy} albüm var.',
    ]
    spotlight = []
    if album_rows:
        spotlight.append({'label': 'İlk satır', 'value': str(_get(_get(album_rows[0], 'album'), 'title') or '-')})
    actions = [
        {'label': 'Bekleyen akış', 'value': total_pending, 'tone': 'watch' if total_pending else 'calm'},
        {'label': 'İşlem alınabilir', 'value': actionable, 'tone': 'calm' if actionable else 'watch'},
        {'label': 'Metin eksiği', 'value': missing_showcase_copy, 'tone': 'watch' if missing_showcase_copy else 'calm'},
        {'label': 'Kurumsal vitrin', 'value': approved, 'tone': 'calm'},
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets[:4],
        'actions': actions,
        'spotlight': spotlight,
    }


def build_repository_edit_history_ai_panel(*, history_rows: Iterable[Any] | None = None, module_filter: str | None = None, entity_filter: str | None = None) -> dict[str, Any]:
    history_rows = list(history_rows or [])
    total = len(history_rows)
    document_count = sum(1 for row in history_rows if str(_get(row, 'entity_type') or '') == 'document')
    album_count = sum(1 for row in history_rows if str(_get(row, 'entity_type') or '') == 'media_album')
    archive_count = sum(1 for row in history_rows if str(_get(row, 'action') or '').lower() in {'archive', 'restore'})
    blank_notes = sum(1 for row in history_rows if not str(_get(row, 'note') or '').strip())
    actor_names = {str(_get(_get(row, 'changed_by'), 'full_name') or '-') for row in history_rows if _get(row, 'changed_by')}
    field_names = {str(_get(row, 'field_name') or '-') for row in history_rows if _get(row, 'field_name')}
    tone = _tone_from_counts(critical=int(total == 0), warning=blank_notes)

    if total == 0:
        headline = 'Düzenleme geçmişinde kayıt bulunmuyor'
        summary = 'AI özeti, seçili filtrede henüz değişiklik izi görünmediğini; denetim okunabilirliği için ilk değişikliklerden sonra alan bazlı izlerin takip edilmesi gerektiğini gösteriyor.'
    elif blank_notes > 0:
        headline = 'Düzenleme izi dolu ancak not kalitesi güçlendirilmeli'
        summary = 'AI özeti, değişiklik kaydının oluştuğunu fakat bazı satırlarda açıklayıcı not bulunmadığını; geri izleme kalitesi için özet alanının daha düzenli doldurulmasının fayda sağlayacağını işaret ediyor.'
    else:
        headline = 'Düzenleme geçmişi denetim için okunaklı'
        summary = 'AI özeti, alan bazlı değişikliklerin belge ve albüm hareketleriyle birlikte anlamlı bir denetim izi sunduğunu gösteriyor.'

    bullets = [
        f'Toplam {total} hareket; belge tarafı {document_count}, albüm tarafı {album_count} kayıt içeriyor.',
        f'Arşiv/geri yükleme etkisi {archive_count}; farklı alan başlığı sayısı {len(field_names)}.',
        f'İz bırakan kullanıcı kümesi {len(actor_names)}; boş not taşıyan satır sayısı {blank_notes}.',
    ]
    if module_filter or entity_filter:
        bullets.append(f'Etkin filtreler: modül={module_filter or "tümü"}, varlık={entity_filter or "tümü"}.')
    spotlight = []
    if history_rows:
        spotlight.append({'label': 'Son işlem', 'value': str(_get(history_rows[0], 'action') or '-')})
    if actor_names:
        spotlight.append({'label': 'Kullanıcı kümesi', 'value': ', '.join(sorted(actor_names)[:3])})
    actions = [
        {'label': 'Toplam hareket', 'value': total, 'tone': 'calm' if total else 'watch'},
        {'label': 'Belge kaydı', 'value': document_count, 'tone': 'calm'},
        {'label': 'Albüm kaydı', 'value': album_count, 'tone': 'calm'},
        {'label': 'Boş not', 'value': blank_notes, 'tone': 'watch' if blank_notes else 'calm'},
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets[:4],
        'actions': actions,
        'spotlight': spotlight,
    }


def build_education_roster_hub_ai_panel(*, roster_records: Iterable[Any] | None = None) -> dict[str, Any]:
    roster_records = list(roster_records or [])
    total_records = len(roster_records)
    participant_total = sum(_to_int(_get(item, 'participant_count')) for item in roster_records)
    sheet_total = sum(_to_int(_get(item, 'sheet_count')) for item in roster_records)
    signed_scan_total = sum(_to_int(_get(item, 'signed_scan_count')) for item in roster_records)
    pending_review_total = sum(_to_int(_get(item, 'review_pending_count')) for item in roster_records)
    missing_sheet_records = sum(1 for item in roster_records if _to_int(_get(item, 'sheet_count')) == 0)
    tone = _tone_from_counts(critical=pending_review_total, warning=missing_sheet_records)

    if pending_review_total > 0:
        headline = 'Katılımcı merkezinde tarama doğrulama kuyruğu var'
        summary = 'AI özeti, bazı eğitimlerde imzalı föylerin sisteme girdiğini ancak operatör doğrulamasının tamamlanmadığını; kapanış öncesi önce bu kuyruğun temizlenmesini öneriyor.'
    elif missing_sheet_records > 0:
        headline = 'Bazı eğitimlerde föy üretim adımı eksik'
        summary = 'AI özeti, katılımcı tanımlı olsa da henüz yazdırılabilir föy üretimi yapılmamış eğitimler bulunduğunu gösteriyor.'
    else:
        headline = 'Katılımcı ve föy merkezi dengeli ilerliyor'
        summary = 'AI özeti, eğitim bazlı katılımcı listesi, çıktı üretimi ve tarama akışının aynı merkezden takip edilebildiğini gösteriyor.'

    bullets = [
        f'{total_records} eğitim kaydında toplam {participant_total} katılımcı ve {sheet_total} föy izleniyor.',
        f'İmzalı tarama {signed_scan_total}; doğrulama bekleyen toplam tarama {pending_review_total}.',
        f'Föy üretimi yapılmamış eğitim sayısı {missing_sheet_records}.',
    ]
    spotlight = []
    sorted_records = sorted(roster_records, key=lambda item: (_to_int(_get(item, 'review_pending_count')), _to_int(_get(item, 'participant_count'))), reverse=True)
    if sorted_records:
        spotlight.append({'label': 'Öncelikli eğitim', 'value': str(_get(_get(sorted_records[0], 'row'), 'title') or '-')})
    actions = [
        {'label': 'Eğitim kaydı', 'value': total_records, 'tone': 'calm'},
        {'label': 'Katılımcı', 'value': participant_total, 'tone': 'calm'},
        {'label': 'Bekleyen inceleme', 'value': pending_review_total, 'tone': 'critical' if pending_review_total else 'calm'},
        {'label': 'Föysüz kayıt', 'value': missing_sheet_records, 'tone': 'watch' if missing_sheet_records else 'calm'},
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets[:4],
        'actions': actions,
        'spotlight': spotlight,
    }


def build_education_roster_signature_ai_panel(*, record: Any, metrics: Any | None = None, attendance_sheets: Iterable[Any] | None = None, participants: Iterable[Any] | None = None, sessions: Iterable[Any] | None = None, participant_identity_summary: Any | None = None) -> dict[str, Any]:
    metrics = metrics or {}
    attendance_sheets = list(attendance_sheets or [])
    participants = list(participants or [])
    sessions = list(sessions or [])
    participant_identity_summary = participant_identity_summary or {}
    participant_count = _to_int(_get(metrics, 'participant_count'), len(participants))
    manual_count = _to_int(_get(metrics, 'manual_count'))
    hr_count = _to_int(_get(metrics, 'hr_count'))
    missing_identity_count = _to_int(_get(metrics, 'missing_identity_count'))
    signed_count = _to_int(_get(metrics, 'signed_count'))
    review_pending = sum(1 for sheet in attendance_sheets if str(_get(sheet, 'recognition_status') or 'pending') in {'pending', 'manual_review_required'})
    signed_scan_count = sum(1 for sheet in attendance_sheets if _get(sheet, 'signed_uploaded_at') or _get(sheet, 'signed_scan_path'))
    low_identity_rate = int(bool(participant_count) and missing_identity_count >= max(2, participant_count // 3))
    tone = _tone_from_counts(critical=review_pending + missing_identity_count, warning=int(not attendance_sheets) + low_identity_rate)

    if missing_identity_count > 0:
        headline = 'Katılımcı listesinde kimlik tamamlama ihtiyacı var'
        summary = 'AI özeti, bazı katılımcılarda kimlik bilgisinin eksik kaldığını; resmi çıktı ve dışa aktarım hazırlığı için bu alanların tamamlanması gerektiğini gösteriyor.'
    elif review_pending > 0:
        headline = 'İmzalı föy taramalarında doğrulama bekleyen kayıtlar var'
        summary = 'AI özeti, tarama yükleme adımının yapıldığını ancak son operatör kontrolünün henüz tamamlanmadığını işaret ediyor.'
    else:
        headline = 'Katılımcı, föy ve tarama akışı kontrollü'
        summary = 'AI özeti, personel ekleme, elle giriş, çıktı üretimi ve tarama inceleme adımlarının aynı çalışma alanında dengeli ilerlediğini gösteriyor.'

    bullets = [
        f'{participant_count} katılımcının {hr_count} tanesi İK kaynağından, {manual_count} tanesi elle eklenmiş.',
        f'İmzası doğrulanan {signed_count}; imzalı tarama yüklenen {signed_scan_count}; inceleme bekleyen föy {review_pending}.',
        f'Oturum sayısı {len(sessions)} ve üretilen föy sayısı {len(attendance_sheets)}.',
    ]
    if missing_identity_count:
        bullets.append(f'Kimlik bilgisi eksik katılımcı sayısı {missing_identity_count}.')
    spotlight = []
    if _get(record, 'title'):
        spotlight.append({'label': 'Eğitim', 'value': str(_get(record, 'title'))})
    if participants:
        first_name = _get(participants[0], 'participant_name_snapshot') or _get(_get(participants[0], 'user'), 'full_name') or _get(participants[0], 'full_name')
        if first_name:
            spotlight.append({'label': 'İlk katılımcı', 'value': str(first_name)})
    actions = [
        {'label': 'Katılımcı', 'value': participant_count, 'tone': 'calm'},
        {'label': 'Eksik kimlik', 'value': missing_identity_count, 'tone': 'critical' if missing_identity_count else 'calm'},
        {'label': 'Bekleyen inceleme', 'value': review_pending, 'tone': 'critical' if review_pending else 'calm'},
        {'label': 'İmzalı tarama', 'value': signed_scan_count, 'tone': 'watch' if signed_scan_count and review_pending else 'calm'},
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets[:4],
        'actions': actions,
        'spotlight': spotlight,
    }


def build_education_scan_review_ai_panel(*, scan: Any, sheet: Any, record: Any, results: Iterable[Any] | None = None) -> dict[str, Any]:
    results = list(results or [])
    total = len(results)
    attended = sum(1 for row in results if str(_get(row, 'final_attendance_status') or '').lower() == 'attended')
    pending = sum(1 for row in results if str(_get(row, 'final_attendance_status') or 'pending').lower() == 'pending')
    verified = sum(1 for row in results if bool(_get(row, 'is_manually_verified')))
    auto_detected = sum(1 for row in results if bool(_get(row, 'auto_signature_detected')))
    low_confidence = sum(1 for row in results if _to_float(_get(row, 'auto_confidence')) not in {0.0} and _to_float(_get(row, 'auto_confidence')) < 60)
    tone = _tone_from_counts(critical=pending, warning=low_confidence + max(total - verified, 0))

    if pending > 0:
        headline = 'Tarama doğrulama ekranında kapanmamış satırlar var'
        summary = 'AI özeti, bazı satırlarda kesin katılım durumu seçilmediğini; kayıt kapatılmadan önce tüm satırların operatör tarafından doğrulanması gerektiğini gösteriyor.'
    elif low_confidence > 0:
        headline = 'Düşük güvenli algılamalar manuel dikkat istiyor'
        summary = 'AI özeti, otomatik imza algısının bazı satırlarda düşük güven ürettiğini; bu satırların not alanıyla birlikte ayrıca kontrol edilmesini öneriyor.'
    else:
        headline = 'Tarama doğrulama görünümü kontrollü'
        summary = 'AI özeti, otomatik algı ile manuel doğrulamanın aynı tabloda kapanabildiğini ve eğitim yoklama kararının netleştiğini gösteriyor.'

    bullets = [
        f'{total} satırdan {attended} tanesi katıldı olarak işaretli; bekleyen satır sayısı {pending}.',
        f'Otomatik olarak imza algılanan {auto_detected}, düşük güvenli {low_confidence} satır bulunuyor.',
        f'Manuel doğrulanan satır sayısı {verified}; tarama durumu {str(_get(scan, "processing_status") or "uploaded")}.'
    ]
    spotlight = []
    if _get(record, 'title'):
        spotlight.append({'label': 'Eğitim', 'value': str(_get(record, 'title'))})
    if _get(scan, 'original_filename'):
        spotlight.append({'label': 'Tarama dosyası', 'value': str(_get(scan, 'original_filename'))})
    actions = [
        {'label': 'Toplam satır', 'value': total, 'tone': 'calm'},
        {'label': 'Bekleyen', 'value': pending, 'tone': 'critical' if pending else 'calm'},
        {'label': 'Düşük güven', 'value': low_confidence, 'tone': 'watch' if low_confidence else 'calm'},
        {'label': 'Doğrulanan', 'value': verified, 'tone': 'calm'},
    ]
    return {
        'badge': _badge_from_tone(tone),
        'tone': tone,
        'headline': headline,
        'summary': summary,
        'bullets': bullets[:4],
        'actions': actions,
        'spotlight': spotlight,
    }

