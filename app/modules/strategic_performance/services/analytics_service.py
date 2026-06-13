"""BYS360 SP-1A stratejik analiz yardımcıları."""
from .kpi_service import enrich_target


def summarize_targets(targets):
    total = 0
    completed = 0
    risky = 0
    critical = 0
    rate_sum = 0.0

    for target in targets or []:
        total += 1
        info = enrich_target(target)
        rate_sum += info["completion_rate"]
        if info["status"] == "completed":
            completed += 1
        elif info["status"] == "at_risk":
            risky += 1
        elif info["status"] == "critical":
            critical += 1

    average = round(rate_sum / total, 2) if total else 0.0
    return {
        "total_targets": total,
        "completed_targets": completed,
        "risky_targets": risky,
        "critical_targets": critical,
        "average_completion_rate": average,
    }


def ai_safe_summary(targets):
    """AI karar destek için kişisel ham yorum içermeyen özet veri üretir."""
    summary = summarize_targets(targets)
    return {
        "hedef_sayisi": summary["total_targets"],
        "tamamlanan_hedef": summary["completed_targets"],
        "riskli_hedef": summary["risky_targets"],
        "kritik_hedef": summary["critical_targets"],
        "ortalama_gerceklesme": summary["average_completion_rate"],
    }
