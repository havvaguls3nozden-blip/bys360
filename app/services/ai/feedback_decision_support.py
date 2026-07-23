from __future__ import annotations

import logging
from statistics import mean
from typing import Any

logger = logging.getLogger(__name__)


def _get(o: Any, k: str, d: Any = None) -> Any:
    if o is None:
        return d
    return o.get(k, d) if isinstance(o, dict) else getattr(o, k, d)

def _f(v: Any, d: float | None = None) -> float | None:
    try:
        return d if v in (None, '') else float(v)
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/ai/feedback_decision_support.py | line=15")
        return d

def _i(v: Any, d: int = 0) -> int:
    try:
        return d if v in (None, '') else int(v)
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/services/ai/feedback_decision_support.py | line=21")
        return d

def tone(avg: float | None) -> str:
    if avg is None:
        return 'neutral'
    if avg >= 4.25:
        return 'good'
    if avg >= 3.45:
        return 'stable'
    if avg >= 2.75:
        return 'watch'
    return 'risk'

def title_for(t: str) -> str:
    return {'good':'Güçlü ve olumlu iklim','stable':'Dengeli ve yönetilebilir seyir','watch':'Yakın izleme bandı','risk':'Yönetici müdahalesi önerilir','neutral':'Veri olgunlaşması bekleniyor'}.get(t,'Veri olgunlaşması bekleniyor')

def build_pulse_form_guidance(today_entry: Any, history_preview: list[Any] | None) -> dict[str, Any]:
    vals = [_i(_get(x,'mood_value')) for x in (history_preview or []) if _i(_get(x,'mood_value'))]
    avg = round(mean(vals), 2) if vals else None
    cur = _i(_get(today_entry,'mood_value')) if today_entry else None
    t = tone(avg if avg is not None else (_f(cur) if cur else None))
    if cur and cur <= 2:
        summary = 'Bugünkü düşük sinyal önemli. Kısa not, kişiyi ifşa etmeden iyileştirme başlığına dönüşür.'
    elif cur and cur >= 4:
        summary = 'Bugünkü olumlu sinyal güçlü. İyi giden uygulamayı not edersen kurumsal iyi örnek üretir.'
    else:
        summary = 'Düzenli nabız kaydı ekip ikliminin yönünü ve tekrar eden ihtiyaçları görünür hale getirir.'
    return {'title': title_for(t), 'tone': t, 'summary': summary, 'average': avg, 'actions': ['Kısa notlar konu başlığı üretimini güçlendirir.', 'Anonim kayıtlar yalnızca toplu eğilimde kullanılır.', 'Düşük sinyal tekrarı yönetici ekranında erken uyarı üretir.']}

def build_pulse_analytics_decision_support(analytics: dict[str, Any] | None, days: int = 30) -> dict[str, Any]:
    a = analytics or {}
    avg = _f(_get(a,'average'))
    delta = _f(_get(a,'delta'), 0)
    cov = _f(_get(a,'coverage_rate'))
    risk = _i(_get(a,'risk_user_count'))
    eligible = bool(_get(a,'eligible'))
    t = tone(avg)
    if not eligible:
        summary = f"Son {days} gün için gizlilik eşiği henüz tamamlanmadı. AI yorum kapsamı mahremiyet için sınırlı tutulur."
        actions = ['Nabız kullanımını kısa duyuru ile artırın.', 'Küçük grupta kişi yorumu üretmeyin.', 'Eşik tamamlanmadan idari karar vermeyin.']
    elif t == 'risk' or risk:
        summary = 'Düşük ortalama veya tekrar eden düşük nabız serileri var. İş yükü, rol netliği ve iletişim başlıkları kontrol edilmeli.'
        actions = ['Kişiyi ifşa etmeyen yönetici görüşmesi planlayın.', 'İş yükü ve görev dağılımını kontrol edin.', 'Aksiyon planı açıp termin belirleyin.']
    elif t == 'watch' or (delta is not None and delta < -0.35):
        summary = 'Genel iklim izleme bandında. Küçük ve erken müdahale ile risk büyümeden yönetilebilir.'
        actions = ['Haftalık kısa toplantıda engelleri toplayın.', 'Düşüş günlerini takvimle karşılaştırın.', 'Bir sonraki hafta aynı metriklerle kontrol edin.']
    else:
        summary = 'İklim yönetilebilir seviyede. İyi uygulamaları korumak ve katılım sürekliliğini artırmak önerilir.'
        actions = ['Olumlu günlerin nedenlerini kaydedin.', 'Katılım düşükse nazik hatırlatma yapın.', 'Notları aylık konu başlıklarına ayırın.']
    flags = []
    if cov is not None and cov < 40:
        flags.append('Kapsama oranı düşük; temkinli yorumlanmalı.')
    if delta is not None and delta < -0.5:
        flags.append('Son 7 gün eğilimi belirgin düşüş gösteriyor.')
    if risk:
        flags.append(f'{risk} risk serisi izleniyor.')
    if not flags:
        flags.append('Kritik otomatik uyarı yok.')
    return {'title': title_for(t), 'tone': t, 'summary': summary, 'actions': actions, 'flags': flags, 'score': avg, 'delta': delta, 'coverage': cov}

def build_results_decision_support(campaign: Any, results: list[dict[str, Any]] | None, pulse_context: dict[str, Any] | None) -> dict[str, Any]:
    rows = results or []
    avgs = [_f(r.get('average')) for r in rows if _f(r.get('average')) is not None]
    scale_avg = round(mean(avgs), 2) if avgs else None
    total = max([_i(r.get('submission_count')) for r in rows] or [0])
    low, high = [], []
    for r in rows:
        avg = _f(r.get('average'))
        q = str(_get(r.get('question'),'question_text','Soru'))
        if avg is not None and avg <= 2.7:
            low.append(q)
        if avg is not None and avg >= 4.2:
            high.append(q)
    t = tone(scale_avg if scale_avg is not None else _f(_get(pulse_context or {}, 'average')))
    if not campaign:
        return {'title':'Kampanya seçimi bekleniyor','tone':'neutral','summary':'AI özeti için kampanya seçin.','actions':['Kampanya seçin.'],'flags':['Veri yok.'],'scale_average':None,'total_answers':0,'low_questions':[],'high_questions':[]}
    if low:
        summary='Düşük bantta soru var. Kök neden ve aksiyon planı önerilir.'
        actions=['Düşük ortalamalı soruları aksiyona dönüştürün.','Metin yanıtlarında tekrar eden konuları çıkarın.','Sonraki kampanyada takip sorusu açın.']
    else:
        summary='Sonuçlar yönetilebilir görünüyor. Güçlü alanlar iyi uygulama olarak işaretlenebilir.'
        actions=['Güçlü alanları iyi uygulama olarak kaydedin.','Katılım düşükse hatırlatma yapın.','Metinleri olumlu/iyileştirme başlığına ayırın.']
    flags=[]
    if total < 5:
        flags.append('Yanıt sayısı düşük; genelleme sınırlı.')
    if low:
        flags.append(f'Düşük bantta {len(low)} soru var.')
    if high:
        flags.append(f'Güçlü bantta {len(high)} soru var.')
    if not flags:
        flags.append('Kritik sonuç uyarısı yok.')
    return {'title': title_for(t), 'tone': t, 'summary': summary, 'actions': actions, 'flags': flags, 'scale_average': scale_avg, 'total_answers': total, 'low_questions': low[:4], 'high_questions': high[:4]}

def build_manager_decision_support(summary: dict[str, Any] | None) -> dict[str, Any]:
    s = summary or {}
    base = build_pulse_analytics_decision_support(s.get('analytics') or {}, 30)
    completion = s.get('campaign_completion') or []
    zero = [str(_get(r.get('campaign') if isinstance(r,dict) else None,'title','Kampanya')) for r in completion if isinstance(r,dict) and _i(r.get('submission_count')) == 0]
    actions = list(base.get('actions') or [])
    if zero:
        actions.insert(0, 'Yanıt almayan kampanyaların hedef kitle ve duyuru görünürlüğünü kontrol edin.')
    flags = list(base.get('flags') or [])
    if zero:
        flags.append(f'Yanıt almayan kampanya sayısı: {len(zero)}')
    return {**base, 'campaign_count': len(completion), 'zero_submission_campaigns': zero[:4], 'actions': actions[:6], 'flags': flags[:6]}
