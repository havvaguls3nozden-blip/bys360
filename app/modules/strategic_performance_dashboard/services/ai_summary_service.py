"""BYS360 SP-1B AI Özet Servisi."""
from __future__ import annotations

from typing import Any, Dict, List


def build_ai_safe_summary(dashboard_summary: dict[str, Any]) -> list[str]:
    total = dashboard_summary.get("total_targets", 0)
    risky = dashboard_summary.get("risky_targets", 0)
    critical = dashboard_summary.get("critical_targets", 0)
    notes = ["Bu alan karar üretmez; yalnızca yöneticinin dikkat etmesi gereken başlıkları özetler."]
    if total == 0:
        notes.append("Henüz analiz edilecek hedef/KPI kaydı bulunmuyor.")
    else:
        notes.append(f"Toplam {total} hedef içinde {risky} riskli ve {critical} kritik kayıt izleniyor.")
    return notes
