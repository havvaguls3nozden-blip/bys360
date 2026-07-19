"""BYS360 SP-1H KPI Performans bağlantı servisi.
İlk fazda KPI verisi nihai performans puanını otomatik değiştirmez; analiz ve karar destek katkısı üretir.
"""
import logging

logger = logging.getLogger(__name__)

def calculate_kpi_completion(target_value, current_value):
    try:
        target=float(target_value or 0); current=float(current_value or 0)
        if target <= 0: return 0.0
        return round(min((current/target)*100, 100), 2)
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return 0.0

def classify_kpi_risk(completion_rate):
    rate=float(completion_rate or 0)
    if rate >= 90: return 'Düşük'
    if rate >= 70: return 'Normal'
    if rate >= 50: return 'Riskli'
    return 'Kritik'

def build_performance_kpi_summary(targets):
    items=[]
    for t in targets or []:
        rate=calculate_kpi_completion(getattr(t,'target_value',0), getattr(t,'current_value',0))
        items.append({'target_name': getattr(t,'target_name','Hedef'), 'completion_rate': rate, 'risk_level': classify_kpi_risk(rate)})
    return items
