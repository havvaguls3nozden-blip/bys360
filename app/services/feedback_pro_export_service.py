from __future__ import annotations

import csv
import io


def _csv(rows):
    out = io.StringIO()
    w = csv.writer(out, delimiter=';')
    for r in rows:
        w.writerow(['' if x is None else x for x in r])
    return '\ufeff' + out.getvalue()

def export_pulse_analytics_csv(a, days):
    a = a or {}
    rows = [['BYS360 Nabız Analitiği'], ['Pencere', f'Son {days} gün'], ['Katılımcı', a.get('participant_count',0)], ['Ortalama', a.get('average','')], ['Delta', a.get('delta','')], ['Kapsama', a.get('coverage_rate','')], [], ['Dağılım'], ['Puan','Etiket','Kayıt']]
    for x in a.get('distribution',[]) or []:
        rows.append([x.get('value'), x.get('label'), x.get('count')])
    rows += [[], ['Günlük Ortalama'], ['Tarih','Ortalama']]
    for label,v in zip(a.get('daily_labels',[]) or [], a.get('daily_values',[]) or [], strict=False):
        rows.append([label,v])
    return _csv(rows)

def export_manager_summary_csv(s):
    s = s or {}
    a = s.get('analytics') or {}
    rows = [['BYS360 Yönetici Geri Bildirim Özeti'], ['Nabız ortalaması', s.get('pulse_average','')], ['Katılımcı', a.get('participant_count',0)], ['Risk serisi', a.get('risk_user_count',0)], [], ['Kampanya','Durum','Yanıt']]
    for r in s.get('campaign_completion',[]) or []:
        c = r.get('campaign') if isinstance(r,dict) else None
        rows.append([getattr(c,'title','Kampanya'), getattr(c,'status',''), r.get('submission_count',0) if isinstance(r,dict) else 0])
    return _csv(rows)
