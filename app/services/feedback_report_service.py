from __future__ import annotations



from collections import defaultdict
from datetime import date, timedelta
import csv
import io

from app.models import FeedbackCampaign, FeedbackPulseEntry
from app.services.feedback_service import build_campaign_pulse_context, build_campaign_results, campaign_includes_pulse


def build_pulse_trend(unit_id=None, days: int = 14):
    start_date = date.today() - timedelta(days=max(days - 1, 0))
    query = FeedbackPulseEntry.query.filter(FeedbackPulseEntry.entry_date >= start_date)
    if unit_id:
        query = query.filter(FeedbackPulseEntry.organization_unit_id == unit_id)
    rows = query.order_by(FeedbackPulseEntry.entry_date.asc(), FeedbackPulseEntry.id.asc()).all()
    buckets = defaultdict(list)
    for row in rows:
        buckets[row.entry_date.isoformat()].append(row.mood_value)
    labels = []
    values = []
    current = start_date
    while current <= date.today():
        key = current.isoformat()
        labels.append(key)
        values.append(round(sum(buckets[key]) / len(buckets[key]), 2) if buckets.get(key) else None)
        current += timedelta(days=1)
    return {"labels": labels, "values": values}


def export_campaign_results_csv(campaign: FeedbackCampaign) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Kampanya", campaign.title])
    writer.writerow(["Tür", getattr(campaign, "campaign_type", "survey")])
    writer.writerow([])
    writer.writerow(["Soru", "Tür", "Metrik", "Değer"])
    for row in build_campaign_results(campaign):
        question = row["question"]
        if row.get("average") is not None:
            writer.writerow([question.question_text, question.question_type, "Ortalama", row["average"]])
        for label, count in row.get("option_counts") or []:
            writer.writerow([question.question_text, question.question_type, label, count])
        for sample in row.get("text_samples") or []:
            writer.writerow([question.question_text, question.question_type, "Metin", sample])

    if campaign_includes_pulse(campaign):
        pulse_context = build_campaign_pulse_context(campaign)
        writer.writerow([])
        writer.writerow(["Kampanya Nabız Özeti"])
        writer.writerow(["Pencere", pulse_context.get("window_label") or "-"])
        writer.writerow(["Ortalama", pulse_context.get("average") if pulse_context.get("average") is not None else "-"])
        writer.writerow(["Trend Delta", pulse_context.get("delta") if pulse_context.get("delta") is not None else "-"])
        writer.writerow(["Kayıt", pulse_context.get("pulse_count") or 0])

    return output.getvalue().encode("utf-8-sig")