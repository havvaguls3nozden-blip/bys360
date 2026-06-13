from __future__ import annotations



from typing import Callable


def _norm(value: object) -> str:
    text = str(value or '').strip().lower()
    if not text:
        return ''
    normalized: list[str] = []
    prev_sep = False
    for ch in text:
        if ch.isalnum():
            normalized.append(ch)
            prev_sep = False
        else:
            if not prev_sep:
                normalized.append('_')
                prev_sep = True
    return ''.join(normalized).strip('_')


def _humanize(value: object) -> str:
    text = str(value or '').strip()
    if not text:
        return '-'
    text = text.replace('_', ' ').replace('-', ' ').strip()
    text = ' '.join(part for part in text.split() if part)
    return text[:1].upper() + text[1:] if text else '-'


def _map_or_humanize(value: object, mapping: dict[str, str], *, fallback: Callable[[object], str] | None = None) -> str:
    key = _norm(value)
    if not key:
        return '-'
    if key in mapping:
        return mapping[key]
    return fallback(value) if fallback else _humanize(value)


MODULE_LABELS = {
    'performance': 'Performans',
    'strategy': 'Strateji (canlı kapsam dışı)',
    'education': 'Eğitim (canlı kapsam dışı)',
    'repository': 'Belge ve Medya Deposu (canlı kapsam dışı)',
    'portal': 'İç Portal (canlı kapsam dışı)',
    'communication': 'İletişim',
    'survey': 'Anket Yönetimi',
    'feedback': 'Geri Bildirim / Nabız',
    'analysis_center': 'AI Karar Destek Merkezi',
    'messaging': 'İletişim',
    'notifications': 'Bildirimler',
    'support': 'Destek',
    'hr': 'Personel / İzin–Vekâlet',
    'leave': 'İzin ve Vekâlet',
    'general': 'Genel',
    'genel': 'Genel',
    'ai': 'YZ',
}

FEATURE_LABELS = {
    'summary': 'Özet',
    'brief': 'Yönetici özeti',
    'triage': 'Triage özeti',
    'leave_brief': 'İzin ve vekâlet özeti',
    'classification': 'Sınıflandırma',
    'meeting': 'Toplantı özeti',
    'consistency': 'Tutarlılık kontrolü',
    'team_compare': 'Personel analizi',
    'scorecard': 'Not karnesi özeti',
    'scorecard_note': 'Not karnesi notu',
    'meeting_summary': 'Toplantı özeti',
    'attendance': 'Yoklama',
    'attendance_check': 'Yoklama kontrolü',
    'tagging': 'Etiket önerisi',
    'governance': 'Yönetişim',
    'governance_alert': 'Yönetişim uyarısı',
    'notification_priority': 'Bildirim önceliği',
    'executive_brief': 'Yönetici özeti',
    'weekly_summary': 'Haftalık özet',
    'pulse_brief': 'Nabız özeti',
    'survey_summary': 'Anket özeti',
    'communication_priority': 'İletişim önceliği',
    'weekly_summary_repository_classification': 'Haftalık özet belge sınıflandırması',
    'repository_classification': 'Belge sınıflandırması',
    'strategy_meeting': 'Strateji toplantısı',
    'alert': 'Uyarı',
    'recommendations': 'Öneri üretimi',
    'consistency_risk': 'Tutarlılık riski',
    'document_summary': 'Belge özeti',
    'album_summary': 'Albüm özeti',
    'education_summary': 'Eğitim özeti',
    'performance_summary': 'Performans özeti',
    'strategy_summary': 'Strateji özeti',
    'go_live_readiness': 'Canlıya alma hazır oluşu',
    'acceptance_pack': 'Kabul paketi',
    'share_export': 'Paylaşım ve dışa aktarım',
    'review_queue': 'İnceleme kuyruğu',
    'qa_queue': 'İnceleme kuyruğu',
    'preflight': 'Ön kontrol',
    'smoke': 'Hızlı doğrulama',
}

TARGET_LABELS = {
    'documents': 'Belgeler',
    'media_albums': 'Albüm kayıtları',
    'media_assets': 'Medya kayıtları',
    'education_records': 'Eğitim kayıtları',
    'education_sessions': 'Eğitim oturumları',
    'education_participants': 'Eğitim katılımcıları',
    'strategy_plans': 'Strateji planları',
    'strategy_goals': 'Stratejik hedefler',
    'strategy_actions': 'Stratejik faaliyetler',
    'strategy_meetings': 'Strateji toplantıları',
    'performance_evaluations': 'Not karneleri',
    'performance_evaluation_items': 'Kriter puanları',
    'evaluation_assignments': 'Değerlendirme görevleri',
    'support_tickets': 'Destek talepleri',
    'messages': 'Mesajlar',
    'message_threads': 'Mesaj başlıkları',
    'surveys': 'Anketler',
    'survey_responses': 'Anket yanıtları',
    'feedback_requests': 'Geri bildirim talepleri',
    'feedback_pulse_entries': 'Nabız kayıtları',
    'ai_request_logs': 'AI istek günlükleri',
    'ai_recommendations': 'AI önerileri',
}

STATUS_LABELS = {
    'completed': 'Tamamlandı',
    'failed': 'Başarısız',
    'warning': 'Uyarı',
    'watch': 'İzleme',
    'open': 'Açık',
    'accepted': 'Kabul edildi',
    'rejected': 'Reddedildi',
    'dismissed': 'Kapatıldı',
    'pass': 'Geçti',
    'fail': 'Geçemedi',
    'warn': 'Dikkat',
    'ready': 'Hazır',
    'waiting': 'Bekliyor',
    'planned': 'Planlandı',
    'reviewing': 'İnceleniyor',
    'waiting_info': 'Bilgi bekleniyor',
    'assigned': 'Atandı',
    'resolved': 'Çözüldü',
    'closed': 'Kapatıldı',
    'success': 'Başarılı',
    'stable': 'Dengeli',
    'active': 'Aktif',
    'inactive': 'Pasif',
}

SEVERITY_LABELS = {
    'critical': 'Kritik',
    'warning': 'Uyarı',
    'watch': 'İzleme',
    'high': 'Yüksek',
    'medium': 'Orta',
    'low': 'Düşük',
    'info': 'Bilgi',
    'success': 'Olumlu',
}

SOURCE_LABELS = {
    'registry': 'Kayıt dosyası',
    'registry_record': 'Kayıt dosyası kaydı',
    'built-in': 'Yerleşik',
    'built_in': 'Yerleşik',
    'builtin': 'Yerleşik',
    'default': 'Varsayılan',
    'override': 'Üzerine yazılmış kayıt',
    'backlog': 'Açık iş yükü',
    'backlog_total': 'Açık iş yükü',
    'queue': 'Kuyruk',
    'review_queue': 'İnceleme kuyruğu',
    'qa_queue': 'İnceleme kuyruğu',
}

PROVIDER_MODE_LABELS = {
    'openai_compatible': 'OpenAI uyumlu servis',
    'openai compatible': 'OpenAI uyumlu servis',
    'internal_stub': 'Yerel taslak',
    'stub': 'Yerel taslak',
    'disabled': 'Kapalı',
}

FEEDBACK_LABELS = {
    'helpful': 'Faydalı',
    'not_helpful': 'Geliştirilmeli',
    'wrong': 'Hatalı',
    'unsafe': 'Güvensiz',
    'incorrect': 'Hatalı',
    'negative': 'Olumsuz',
    'positive': 'Olumlu',
}

RECOMMENDATION_LABELS = {
    'consistency_risk': 'Tutarlılık riski',
    'tag_suggestion': 'Etiket önerisi',
    'risk_note_update': 'Risk notu önerisi',
    'result_note_update': 'Sonuç notu önerisi',
    'follow_up_note': 'Takip notu önerisi',
    'summary_refresh': 'Özet yenileme önerisi',
}

TONE_LABELS = {
    'critical': 'Kritik',
    'warning': 'Uyarı',
    'watch': 'İzleme',
    'success': 'İyi',
    'muted': 'Nötr',
    'calm': 'İzleme',
    'info': 'Bilgi',
}

RISK_LEVEL_LABELS = {
    'high': 'Yüksek risk',
    'medium': 'Orta risk',
    'low': 'Düşük risk',
    'critical': 'Kritik',
    'warning': 'Uyarı',
    'watch': 'İzleme',
    'stable': 'Dengeli',
}

REDACTION_TYPE_LABELS = {
    'mask': 'Maskele',
    'remove': 'Kaldır',
    'hash': 'Özet değere çevir',
    'masking': 'Maskeleme',
    'role_based': 'Role göre göster',
}

PLAIN_LABELS = {
    'registry': 'Kayıt dosyası',
    'registry_record': 'Kayıt dosyası kaydı',
    'built_in': 'Yerleşik',
    'built-in': 'Yerleşik',
    'prompt': 'İstem',
    'backlog': 'Açık iş yükü',
    'backlog_total': 'Açık iş yükü',
    'queue': 'Kuyruk',
    'review_queue': 'İnceleme kuyruğu',
    'qa_queue': 'İnceleme kuyruğu',
    'share_export': 'Paylaşım ve dışa aktarım',
    'executive_brief': 'Yönetici özeti',
    'go_live_readiness': 'Canlıya alma hazır oluşu',
    'acceptance_pack': 'Kabul paketi',
    'notification_priority': 'Bildirim önceliği',
    'governance': 'Yönetişim',
    'governance_alert': 'Yönetişim uyarısı',
    'scorecard_note': 'Not karnesi notu',
    'weekly_summary_repository_classification': 'Haftalık özet belge sınıflandırması',
    'attendance': 'Yoklama',
    'alert': 'Uyarı',
    'weekly_summary': 'Haftalık özet',
    'pulse_brief': 'Nabız özeti',
    'survey_summary': 'Anket özeti',
    'communication_priority': 'İletişim önceliği',
    'repository_classification': 'Belge sınıflandırması',
    'strategy_meeting': 'Strateji toplantısı',
    'preflight': 'Ön kontrol',
    'smoke': 'Hızlı doğrulama',
    'module_type': 'Modül',
    'feature_type': 'Özellik',
    'target_table': 'Hedef kayıt',
    'mask': 'Maskele',
    'remove': 'Kaldır',
    'hash': 'Özet değere çevir',
    'masking': 'Maskeleme',
    'role_based': 'Role göre göster',
}


def ai_module_label(value: object) -> str:
    return _map_or_humanize(value, MODULE_LABELS)


def ai_feature_label(value: object) -> str:
    return _map_or_humanize(value, FEATURE_LABELS)


def ai_target_label(value: object) -> str:
    return _map_or_humanize(value, TARGET_LABELS)


def ai_status_label(value: object) -> str:
    return _map_or_humanize(value, STATUS_LABELS)


def ai_severity_label(value: object) -> str:
    return _map_or_humanize(value, SEVERITY_LABELS)


def ai_source_label(value: object) -> str:
    return _map_or_humanize(value, SOURCE_LABELS)


def ai_provider_mode_label(value: object) -> str:
    return _map_or_humanize(value, PROVIDER_MODE_LABELS)


def ai_feedback_label(value: object) -> str:
    return _map_or_humanize(value, FEEDBACK_LABELS)


def ai_recommendation_label(value: object) -> str:
    return _map_or_humanize(value, RECOMMENDATION_LABELS)


def ai_tone_label(value: object) -> str:
    return _map_or_humanize(value, TONE_LABELS)


def ai_risk_label(value: object) -> str:
    return _map_or_humanize(value, RISK_LEVEL_LABELS)


def ai_redaction_type_label(value: object) -> str:
    return _map_or_humanize(value, REDACTION_TYPE_LABELS)


def ai_plain_label(value: object) -> str:
    return _map_or_humanize(value, PLAIN_LABELS)