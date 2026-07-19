from __future__ import annotations

# Bu dosya app.services.ai.dashboard_panels dış public API'sini bozmadan ayrıştırılmıştır.


from app.services.ai.dashboard_panel_common import (
    Any,
    _get,
    _to_int,
    _tone_from_counts,
    _safe_len,
    _safe_bool,
    _safe_title_case,
    _compose_standard_panel,
)

def build_message_compose_ai_panel(*, users=None, selected_recipient_user_id: str | None = None, body: str = "", badge_label: str = "", icon_name: str = "", accent_color: str = "") -> dict[str, Any]:
    users = list(users or [])
    recipient_selected = bool(str(selected_recipient_user_id or "").strip())
    body_length = len((body or "").strip())
    tone = _tone_from_counts(critical=0, warning=0 if recipient_selected and body_length >= 20 else 1)
    headline = "Mesaj taslağı gönderime hazır" if recipient_selected and body_length >= 20 else "Mesaj taslağında birkaç dokunuş gerekebilir"
    summary = "AI özeti, alıcı seçimi ve mesaj gövdesine göre gönderim öncesi netlik kontrolü yapıyor."
    bullets = [
        f"Seçilebilir alıcı havuzu {len(users)} kişi; {'bir alıcı seçildi' if recipient_selected else 'henüz alıcı seçilmedi'}.",
        f"Mesaj gövdesi {body_length} karakter; kısa not yerine yönlendirici bir metin tercih edilebilir.",
        f"Rozet '{badge_label or 'standart'}', ikon '{icon_name or 'varsayılan'}' ve vurgu rengi '{accent_color or 'kurumsal'}' olarak görünüyor.",
    ]
    actions = [
        {"label": "Alıcı", "value": "Hazır" if recipient_selected else "Eksik"},
        {"label": "Karakter", "value": body_length},
        {"label": "Rozet", "value": badge_label or "Standart"},
        {"label": "Renk", "value": accent_color or "Kurumsal"},
    ]
    spotlight = [
        {"label": "Gönderim sinyali", "value": "Hazır" if recipient_selected and body_length >= 20 else "Kontrol et"},
        {"label": "Mesaj tonu", "value": "Açıklayıcı" if body_length >= 120 else "Kısa / hızlı" if body_length >= 20 else "Çok kısa"},
    ]
    return _compose_standard_panel(tone=tone, headline=headline, summary=summary, bullets=bullets, actions=actions, spotlight=spotlight)


def build_message_inbox_ai_panel(*, thread_cards=None, selected_thread_card=None, selected_messages=None) -> dict[str, Any]:
    thread_cards = list(thread_cards or [])
    selected_messages = list(selected_messages or [])
    unread_threads = sum(1 for card in thread_cards if _to_int(_get(card, "unread_count")) > 0)
    pinned_threads = sum(1 for card in thread_cards if _safe_bool(_get(card, "is_pinned")))
    archived_threads = sum(1 for card in thread_cards if _safe_bool(_get(card, "is_archived")))
    selected_title = _get(selected_thread_card, "title") or _get(selected_thread_card, "display_name") or "Mesaj akışı"
    tone = _tone_from_counts(critical=unread_threads, warning=pinned_threads)
    headline = "Mesaj kutusunda önceliklenmesi gereken konuşmalar var" if unread_threads else "Mesaj kutusu dengeli görünüyor"
    summary = f"AI özeti, görünen {len(thread_cards)} konuşma içinden okunmamış ve sabitlenmiş başlıkları öne çıkarıyor."
    bullets = [
        f"Okunmamış konuşma sayısı {unread_threads}; sabitlenmiş {pinned_threads}, arşivlenmiş {archived_threads} başlık var.",
        f"Seçili konuşma: {selected_title}; ekranda {len(selected_messages)} mesaj gösteriliyor.",
        "Kritik yazışmalar için sabitleme ve arşiv ayrımını birlikte kullanmak görünürlüğü güçlendirir.",
    ]
    actions = [
        {"label": "Konuşma", "value": len(thread_cards)},
        {"label": "Okunmamış", "value": unread_threads},
        {"label": "Sabit", "value": pinned_threads},
        {"label": "Seçili mesaj", "value": len(selected_messages)},
    ]
    return _compose_standard_panel(tone=tone, headline=headline, summary=summary, bullets=bullets, actions=actions)


def build_message_thread_ai_panel(*, selected_thread=None, selected_thread_card=None, selected_messages=None, selected_participants=None) -> dict[str, Any]:
    selected_messages = list(selected_messages or [])
    selected_participants = list(selected_participants or [])
    unread_count = _to_int(_get(selected_thread_card, "unread_count"))
    attachment_count = sum(1 for msg in selected_messages if _safe_len(_get(msg, "attachments")) > 0)
    participant_count = max(len(selected_participants), 1)
    title = _get(selected_thread_card, "title") or _get(selected_thread, "subject") or "Konuşma detayı"
    tone = _tone_from_counts(critical=unread_count, warning=attachment_count)
    headline = f"{title} konuşmasında bağlam ve aksiyon birlikte izleniyor"
    summary = "AI özeti, seçili konuşmadaki mesaj yoğunluğu, katılımcı sayısı ve ek varlığını aynı panelde topluyor."
    bullets = [
        f"Konuşmada {len(selected_messages)} mesaj ve {participant_count} aktif katılımcı görünüyor.",
        f"Ek içeren mesaj sayısı {attachment_count}; okunmamış gösterge {unread_count} olarak taşınıyor.",
        "Uzayan konuşmalarda karar gerektiren mesajları alıntılayarak ilerlemek geri dönüşleri hızlandırır.",
    ]
    actions = [
        {"label": "Mesaj", "value": len(selected_messages)},
        {"label": "Katılımcı", "value": participant_count},
        {"label": "Ek", "value": attachment_count},
        {"label": "Okunmamış", "value": unread_count},
    ]
    return _compose_standard_panel(tone=tone, headline=headline, summary=summary, bullets=bullets, actions=actions)


def build_notification_priority_ai_panel(*, notifications=None, unread_count: int = 0, read_count: int = 0, priority_count: int = 0, today_count: int = 0, current_view: str = "all", filter_counts=None) -> dict[str, Any]:
    notifications = list(notifications or [])
    filter_counts = filter_counts or {}
    tone = _tone_from_counts(critical=_to_int(priority_count), warning=_to_int(unread_count))
    headline = "Bildirim kutusunda öncelik sinyalleri öne çıkıyor" if priority_count else "Bildirim akışı kontrol altında"
    summary = f"AI özeti, {current_view} görünümünde {len(notifications)} kaydı ve filtre yoğunluklarını birlikte okuyor."
    bullets = [
        f"Okunmamış {unread_count}, okunmuş {read_count}, öncelikli {priority_count}, bugün gelen {today_count} kayıt var.",
        f"Mesaj filtresi { _to_int(_get(filter_counts, 'messages')) }, anket filtresi { _to_int(_get(filter_counts, 'surveys')) }, sistem filtresi { _to_int(_get(filter_counts, 'system')) } kayıt gösteriyor.",
        "Öncelikli uyarılar temizlendikten sonra toplu okundu işlemi dikkat dağınıklığını azaltır.",
    ]
    actions = [
        {"label": "Görünen", "value": len(notifications)},
        {"label": "Öncelikli", "value": priority_count},
        {"label": "Okunmamış", "value": unread_count},
        {"label": "Bugün", "value": today_count},
    ]
    return _compose_standard_panel(tone=tone, headline=headline, summary=summary, bullets=bullets, actions=actions)


def build_announcements_ai_panel(*, incoming_rows=None, outgoing_rows=None, unread_rows=None, overall_read_rate: float = 0.0, total_outgoing_reads: int = 0, total_outgoing_recipients: int = 0, current_view: str = "all") -> dict[str, Any]:
    incoming_rows = list(incoming_rows or [])
    outgoing_rows = list(outgoing_rows or [])
    unread_rows = list(unread_rows or [])
    tone = _tone_from_counts(critical=len(unread_rows), warning=max(len(outgoing_rows) - len(incoming_rows), 0))
    headline = "Duyuru görünümünde erişim ve okuma dengesi izleniyor" if outgoing_rows else "Duyuru ekranı gelen kutu odağında ilerliyor"
    summary = f"AI özeti, {current_view} görünümünde gelen ve giden duyuru hareketlerini okuma oranıyla birlikte topluyor."
    bullets = [
        f"Görünen gelen duyuru {len(incoming_rows)}, giden duyuru {len(outgoing_rows)}, okunmamış duyuru {len(unread_rows)}.",
        f"Toplam gönderimlerde {total_outgoing_reads} okuma / {total_outgoing_recipients} alıcı üzerinden %{overall_read_rate:.1f} okuma oranı hesaplandı.",
        "Düşük okuma oranlı duyurular için hedef grup daraltma veya tekrar hatırlatma stratejisi düşünülebilir.",
    ]
    actions = [
        {"label": "Gelen", "value": len(incoming_rows)},
        {"label": "Giden", "value": len(outgoing_rows)},
        {"label": "Okunmamış", "value": len(unread_rows)},
        {"label": "Okuma %", "value": f"{overall_read_rate:.1f}"},
    ]
    return _compose_standard_panel(tone=tone, headline=headline, summary=summary, bullets=bullets, actions=actions)


def build_announcement_form_ai_panel(*, users=None, preview_counts=None, target_type: str = "all", target_values=None, subject: str = "", body: str = "") -> dict[str, Any]:
    users = list(users or [])
    target_values = list(target_values or [])
    preview_counts = preview_counts or {}
    subject_len = len((subject or "").strip())
    body_len = len((body or "").strip())
    estimated = _to_int(_get(_get(preview_counts, target_type, {}), target_values[0] if target_values else ""), len(users) if target_type == "all" else len(target_values))
    tone = _tone_from_counts(critical=0, warning=0 if subject_len >= 8 and body_len >= 40 else 1)
    headline = "Duyuru taslağı hedef kitleyle uyumlu görünüyor" if subject_len >= 8 and body_len >= 40 else "Duyuru taslağını göndermeden önce içerik netleştirilebilir"
    summary = "AI özeti, başlık, içerik boyu ve hedefleme tipini aynı teslim görünümünde değerlendiriyor."
    bullets = [
        f"Hedefleme tipi '{target_type}' ve seçili hedef sayısı {len(target_values)}; tahmini erişim {estimated} kişi civarında.",
        f"Başlık {subject_len}, içerik {body_len} karakter. Kurumsal duyurularda konu satırının açık kalması okunurluğu artırır.",
        f"Toplam kullanıcı havuzu {len(users)} kişi; hedef kitlenin daraltılması gürültüyü azaltabilir.",
    ]
    actions = [
        {"label": "Tahmini erişim", "value": estimated},
        {"label": "Başlık", "value": subject_len},
        {"label": "İçerik", "value": body_len},
        {"label": "Hedef", "value": _safe_title_case(target_type, 'Tümü')},
    ]
    return _compose_standard_panel(tone=tone, headline=headline, summary=summary, bullets=bullets, actions=actions)


def build_portal_feed_ai_panel(*, feed_rows=None, story_rows=None, featured_rows=None, groups=None, live_counts=None, weekly_box=None, portal_pref=None) -> dict[str, Any]:
    feed_rows = list(feed_rows or [])
    story_rows = list(story_rows or [])
    featured_rows = list(featured_rows or [])
    groups = list(groups or [])
    live_counts = live_counts or {}
    unread = _to_int(_get(live_counts, "unread_notifications"))
    tone = _tone_from_counts(critical=unread, warning=len(featured_rows))
    headline = "Portal ana akışında içerik ve bildirim yoğunluğu birlikte ilerliyor"
    summary = "AI özeti; akış, story, vitrindeki duyuru ve grup kapsamasını tek bakışta toparlıyor."
    bullets = [
        f"Akışta {len(feed_rows)} paylaşım, {len(story_rows)} story ve {len(featured_rows)} öne çıkan duyuru var.",
        f"Görünür grup sayısı {len(groups)}; okunmamış portal bildirimi {unread}.",
        f"Ana sayfa tercihi '{_get(portal_pref, 'homepage_scope', 'all')}' olarak izleniyor; haftalık kutu {'hazır' if weekly_box else 'boş'} durumda.",
    ]
    actions = [
        {"label": "Paylaşım", "value": len(feed_rows)},
        {"label": "Story", "value": len(story_rows)},
        {"label": "Duyuru", "value": len(featured_rows)},
        {"label": "Bildirim", "value": unread},
    ]
    return _compose_standard_panel(tone=tone, headline=headline, summary=summary, bullets=bullets, actions=actions)


def build_portal_notifications_ai_panel(*, summary=None, notification_rows=None, filter_name: str = "all") -> dict[str, Any]:
    summary = summary or {}
    notification_rows = list(notification_rows or [])
    unread = _to_int(_get(summary, "unread_count"))
    total = _to_int(_get(summary, "total_count"), len(notification_rows))
    priority = _to_int(_get(summary, "priority_count"))
    tone = _tone_from_counts(critical=priority, warning=unread)
    headline = "Portal bildirimleri için öncelik sıralaması görünür" if priority else "Portal bildirim akışı dengeli"
    summary_text = f"AI özeti, {filter_name} filtresinde görünen {len(notification_rows)} bildirim ile genel kutu özetini birlikte sunuyor."
    bullets = [
        f"Toplam kutu {total}, okunmamış {unread}, öncelikli {priority} bildirim içeriyor.",
        f"Ekranda filtre sonrası {len(notification_rows)} satır görünüyor.",
        "Toplu okundu işlemi öncesinde öncelikli bildirimlerin ayrı ele alınması tavsiye edilir.",
    ]
    actions = [
        {"label": "Toplam", "value": total},
        {"label": "Görünen", "value": len(notification_rows)},
        {"label": "Okunmamış", "value": unread},
        {"label": "Öncelikli", "value": priority},
    ]
    return _compose_standard_panel(tone=tone, headline=headline, summary=summary_text, bullets=bullets, actions=actions)


def build_portal_search_ai_panel(*, query: str = "", results=None) -> dict[str, Any]:
    results = results or {}
    posts = list(_get(results, "posts", []) or [])
    groups = list(_get(results, "groups", []) or [])
    users = list(_get(results, "users", []) or [])
    documents = list(_get(results, "documents", []) or [])
    media = list(_get(results, "media", []) or [])
    hashtags = list(_get(results, "hashtags", []) or [])
    total = len(posts) + len(groups) + len(users) + len(documents) + len(media) + len(hashtags)
    tone = _tone_from_counts(critical=0, warning=0 if query else 1)
    headline = "Portal arama sonuçları bağlamsal olarak kümelendi" if query else "Arama başlatıldığında sonuç kümeleri burada okunur"
    summary = f"AI özeti, '{query or 'boş sorgu'}' araması için içerikleri tür bazında topluyor."
    bullets = [
        f"Toplam {total} sonuç; paylaşım {len(posts)}, grup {len(groups)}, kullanıcı {len(users)} olarak ayrışıyor.",
        f"Belge {len(documents)}, medya {len(media)}, etiket {len(hashtags)} sonucu bulundu.",
        "Net bir sorgu ile başlamak özellikle belge ve kişi sonuçlarında gürültüyü azaltır.",
    ]
    actions = [
        {"label": "Toplam", "value": total},
        {"label": "Paylaşım", "value": len(posts)},
        {"label": "Belge", "value": len(documents)},
        {"label": "Etiket", "value": len(hashtags)},
    ]
    return _compose_standard_panel(tone=tone, headline=headline, summary=summary, bullets=bullets, actions=actions)


def build_portal_hashtag_ai_panel(*, tag: str, feed_rows=None) -> dict[str, Any]:
    feed_rows = list(feed_rows or [])
    tone = _tone_from_counts(critical=0, warning=len(feed_rows))
    headline = f"#{tag} etiketi altında görünür içerik akışı toplandı"
    summary = "AI özeti, etiket sayfasında içerik yoğunluğunu ve tekrar kullanım sinyalini özetliyor."
    bullets = [
        f"Etiket altında {len(feed_rows)} paylaşım bulundu.",
        "Etiket akışı güçlü olduğunda grup veya kampanya bazlı içerik kümeleri daha görünür olur.",
        "Tekrarlayan etiketler için kurumsal kullanım standardı belirlemek aramayı güçlendirir.",
    ]
    actions = [
        {"label": "Paylaşım", "value": len(feed_rows)},
        {"label": "Etiket", "value": f"#{tag}"},
        {"label": "Durum", "value": "Aktif" if feed_rows else "Yeni"},
        {"label": "Akış", "value": "Var" if feed_rows else "Boş"},
    ]
    return _compose_standard_panel(tone=tone, headline=headline, summary=summary, bullets=bullets, actions=actions)


def build_portal_groups_ai_panel(*, groups=None) -> dict[str, Any]:
    groups = list(groups or [])
    public_count = sum(1 for group in groups if _safe_bool(_get(group, 'is_public')))
    moderated_count = sum(1 for group in groups if _safe_bool(_get(group, 'requires_approval')))
    tone = _tone_from_counts(critical=0, warning=moderated_count)
    headline = "Portal gruplarında erişim ve moderasyon dengesi görünür"
    summary = "AI özeti, grup listesinde açıklık ve onay gerektiren alanları birlikte okuyor."
    bullets = [
        f"Toplam {len(groups)} grup bulunuyor; açık grup {public_count}, onaylı katılım isteyen grup {moderated_count}.",
        "Farklı amaçlı grup kümeleri, moderasyon yükünü dağıtmak için kategorik olarak ayrıştırılabilir.",
        "Açık ve kontrollü grupların dengeli kullanımı kurumsal akışı daha düzenli tutar.",
    ]
    actions = [
        {"label": "Grup", "value": len(groups)},
        {"label": "Açık", "value": public_count},
        {"label": "Onaylı", "value": moderated_count},
        {"label": "Kapsam", "value": "Kurumsal"},
    ]
    return _compose_standard_panel(tone=tone, headline=headline, summary=summary, bullets=bullets, actions=actions)


def build_portal_group_detail_ai_panel(*, group=None, feed_rows=None, membership=None, pending_request_count: int = 0, can_manage_group: bool = False) -> dict[str, Any]:
    feed_rows = list(feed_rows or [])
    membership_status = _get(membership, 'status', 'yok')
    tone = _tone_from_counts(critical=_to_int(pending_request_count) if can_manage_group else 0, warning=len(feed_rows))
    headline = f"{_get(group, 'name', 'Grup')} grubu için içerik ve katılım sinyali toplandı"
    summary = "AI özeti, grup detayında içerik hacmi, üyelik durumu ve yönetici aksiyon ihtiyacını aynı kartta gösteriyor."
    bullets = [
        f"Grup akışında {len(feed_rows)} paylaşım var; üyelik durumu '{membership_status}'.",
        f"Bekleyen katılım talebi {pending_request_count}; yönetim yetkisi {'var' if can_manage_group else 'yok'}.",
        "Yoğun gruplarda sabit içerik ve duyuru ayrımı, akış okunabilirliğini güçlendirir.",
    ]
    actions = [
        {"label": "Paylaşım", "value": len(feed_rows)},
        {"label": "Talep", "value": pending_request_count},
        {"label": "Üyelik", "value": membership_status},
        {"label": "Yönetim", "value": "Açık" if can_manage_group else "Pasif"},
    ]
    return _compose_standard_panel(tone=tone, headline=headline, summary=summary, bullets=bullets, actions=actions)


def build_portal_post_detail_ai_panel(*, post=None, comments=None, post_row=None, ordered_attachments=None) -> dict[str, Any]:
    comments = list(comments or [])
    ordered_attachments = list(ordered_attachments or [])
    reaction_count = _to_int(_get(post_row, 'reaction_count'))
    comment_count = _to_int(_get(post_row, 'comment_count'), len(comments))
    tone = _tone_from_counts(critical=0, warning=comment_count)
    headline = "Paylaşım detayı etkileşim yoğunluğunu görünür kılıyor"
    summary = "AI özeti, yorum, tepki ve ek varlığını birlikte okuyarak paylaşımın yankısını özetliyor."
    bullets = [
        f"Yorum {comment_count}, tepki {reaction_count}, ek dosya {len(ordered_attachments)} olarak görünüyor.",
        f"İçerik tipi '{_get(post, 'post_type', 'post')}' ve görünür grup '{_get(_get(post, 'group', None), 'name', 'Genel')}'.",
        "Etkileşimi yüksek paylaşımlarda özet veya sabit yanıt yaklaşımı tekrar soruları azaltabilir.",
    ]
    actions = [
        {"label": "Yorum", "value": comment_count},
        {"label": "Tepki", "value": reaction_count},
        {"label": "Ek", "value": len(ordered_attachments)},
        {"label": "Tip", "value": _safe_title_case(_get(post, 'post_type', 'post'), 'Post')},
    ]
    return _compose_standard_panel(tone=tone, headline=headline, summary=summary, bullets=bullets, actions=actions)


def build_portal_file_share_ai_panel(*, groups=None, documents=None, media_assets=None, search: str = "") -> dict[str, Any]:
    groups = list(groups or [])
    documents = list(documents or [])
    media_assets = list(media_assets or [])
    tone = _tone_from_counts(critical=0, warning=0 if documents or media_assets else 1)
    headline = "Dosya paylaşım ekranında kaynak havuzu hazır" if (documents or media_assets) else "Dosya paylaşımı öncesi kaynak havuzu dar görünüyor"
    summary = "AI özeti, paylaşılabilir belge ve medya havuzunu grup kapsamıyla birlikte özetliyor."
    bullets = [
        f"Seçilebilir grup {len(groups)}, belge {len(documents)}, medya {len(media_assets)} kaydı var.",
        f"Arama ifadesi '{search or 'yok'}' olarak çalışıyor.",
        "Dosya paylaşımında belge ve görseli aynı anda daraltmak hedef kitleye uygun akış kurulmasını kolaylaştırır.",
    ]
    actions = [
        {"label": "Grup", "value": len(groups)},
        {"label": "Belge", "value": len(documents)},
        {"label": "Medya", "value": len(media_assets)},
        {"label": "Arama", "value": search or "Yok"},
    ]
    return _compose_standard_panel(tone=tone, headline=headline, summary=summary, bullets=bullets, actions=actions)


def build_portal_analytics_ai_panel(*, analytics=None) -> dict[str, Any]:
    analytics = analytics or {}
    posts = _to_int(_get(analytics, 'posts_count'))
    comments = _to_int(_get(analytics, 'comments_count'))
    reactions = _to_int(_get(analytics, 'reactions_count'))
    active_users = _to_int(_get(analytics, 'active_users_count'))
    tone = _tone_from_counts(critical=0, warning=0 if posts else 1)
    headline = "Portal analitiğinde etkileşim ve kullanım yoğunluğu okunuyor"
    summary = "AI özeti, içerik üretimi ile kullanıcı etkileşimini aynı analitik yüzeyde topluyor."
    bullets = [
        f"Paylaşım {posts}, yorum {comments}, tepki {reactions}, aktif kullanıcı {active_users}.",
        "Tepki ve yorum oranları birlikte okunursa içeriklerin yankısı daha sağlıklı değerlendirilir.",
        "Aktif kullanıcı düşük kaldığında kampanya veya duyuru takvimi ile akış desteklenebilir.",
    ]
    actions = [
        {"label": "Paylaşım", "value": posts},
        {"label": "Yorum", "value": comments},
        {"label": "Tepki", "value": reactions},
        {"label": "Aktif kullanıcı", "value": active_users},
    ]
    spotlight = [
        {"label": "Etkileşim oranı", "value": f"{round(((comments + reactions) / posts), 1) if posts else 0} / paylaşım"},
        {"label": "Kullanım görünümü", "value": "Güçlü" if active_users >= 10 else "Geliştirilebilir"},
    ]
    return _compose_standard_panel(tone=tone, headline=headline, summary=summary, bullets=bullets, actions=actions, spotlight=spotlight)


def build_portal_moderation_ai_panel(*, report=None, panel=None, selected_days: int = 30) -> dict[str, Any]:
    report = report or {}
    panel = panel or {}
    flagged = _to_int(_get(report, 'flagged_count'))
    hidden = _to_int(_get(report, 'hidden_count'))
    pending = _to_int(_get(report, 'pending_review_count'))
    moderators = _to_int(_get(panel, 'moderator_count'))
    tone = _tone_from_counts(critical=flagged + pending, warning=hidden)
    headline = f"Son {selected_days} günde moderasyon baskısı görünür hale getirildi"
    summary = "AI özeti, rapor ve yönetim panelini birleştirerek bekleyen inceleme yükünü topluyor."
    bullets = [
        f"İşaretli içerik {flagged}, gizlenen içerik {hidden}, bekleyen inceleme {pending}.",
        f"Yetkili moderatör sayısı {moderators}.",
        "Bekleyen inceleme yükü arttığında grup bazlı yönlendirme ve otomatik sınıflama akışı değerlendirilebilir.",
    ]
    actions = [
        {"label": "İşaretli", "value": flagged},
        {"label": "Bekleyen", "value": pending},
        {"label": "Gizlenen", "value": hidden},
        {"label": "Moderatör", "value": moderators},
    ]
    spotlight = [{"label": "Dönem", "value": f"{selected_days} gün"}]
    return _compose_standard_panel(tone=tone, headline=headline, summary=summary, bullets=bullets, actions=actions, spotlight=spotlight)


def build_portal_announcement_center_ai_panel(*, summary=None, rows=None) -> dict[str, Any]:
    summary = summary or {}
    rows = list(rows or [])
    published = _to_int(_get(summary, 'published_count'))
    drafts = _to_int(_get(summary, 'draft_count'))
    required_ack = _to_int(_get(summary, 'ack_required_count'))
    tone = _tone_from_counts(critical=required_ack, warning=drafts)
    headline = "Portal duyuru vitrini için yayın ve alındı dengesi okunuyor"
    summary_text = "AI özeti, duyuru merkezindeki yayın, taslak ve alındı gerektiren içerikleri aynı çizgide topluyor."
    bullets = [
        f"Liste görünümünde {len(rows)} duyuru satırı, özet kutusunda yayımlı {published} ve taslak {drafts} kayıt var.",
        f"Alındı zorunlu duyuru sayısı {required_ack}.",
        "Kritik duyurularda alındı takibini ayrı izlemek yönetsel görünürlüğü artırır.",
    ]
    actions = [
        {"label": "Duyuru", "value": len(rows)},
        {"label": "Yayımlı", "value": published},
        {"label": "Taslak", "value": drafts},
        {"label": "Alındı gerekli", "value": required_ack},
    ]
    return _compose_standard_panel(tone=tone, headline=headline, summary=summary_text, bullets=bullets, actions=actions)


def build_portal_announcement_receipts_ai_panel(*, report=None, status: str = 'all', selected_post_id: int | None = None) -> dict[str, Any]:
    report = report or {}
    rows = list(_get(report, 'rows', []) or [])
    acked = _to_int(_get(report, 'ack_count'))
    pending = _to_int(_get(report, 'pending_count'))
    total = _to_int(_get(report, 'total_count'), len(rows))
    tone = _tone_from_counts(critical=pending, warning=acked)
    headline = "Duyuru alındı raporunda bekleyen kullanıcılar öne çıkıyor" if pending else "Duyuru alındı raporu dengeli"
    summary = f"AI özeti, {status} filtresinde alındı durumunu ve seçili duyurunun dağıtım takibini gösteriyor."
    bullets = [
        f"Toplam {total} kayıt; onaylanan {acked}, bekleyen {pending}.",
        f"Rapor satırı {len(rows)} ve seçili duyuru kimliği {selected_post_id or 'tümü'} olarak çalışıyor.",
        "Bekleyen alındılar için tekrar hatırlatma veya hedef kitle daraltma seçenekleri değerlendirilebilir.",
    ]
    actions = [
        {"label": "Toplam", "value": total},
        {"label": "Onay", "value": acked},
        {"label": "Bekleyen", "value": pending},
        {"label": "Filtre", "value": status},
    ]
    return _compose_standard_panel(tone=tone, headline=headline, summary=summary, bullets=bullets, actions=actions)

