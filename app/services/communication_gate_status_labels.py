"""Ortak "hazırlık/kapı" (gate) ve karar durumu görüntüleme etiketleri.

BYS360'ın Faz 8-9D canlıya geçiş/pilot izleme modülleri
(communication_phase8_service.py, communication_phase9*_service.py) aynı
küçük durum kelime dağarcığını (pass/warn/fail/...) birbirinden bağımsız
yerel `_gate()`/`_pilot_gate()`/`_env_row()`/`_path_row()` fabrikalarında
üretiyor ve bu ham İngilizce değerler doğrudan kullanıcıya (Başkanlık/BT
canlıya geçiş ekranları) gösteriliyordu.

Bu modül o kelimelerin TEK, tutarlı Türkçe karşılığını sağlar. Ham `status`
değeri -- CSS rengi ve karar mantığı ("pass"/"warn"/"fail" karşılaştırmaları)
için hâlâ gerekli -- hiçbir yerde değişmez; yalnızca görüntüleme için ayrı
bir `status_label` alanı eklenir.
"""
from __future__ import annotations

GATE_STATUS_LABELS: dict[str, str] = {
    "pass": "Geçti",
    "warn": "Uyarı",
    "warning": "Uyarı",
    "fail": "Başarısız",
    "danger": "Başarısız",
    "ready": "Hazır",
    "done": "Tamamlandı",
    "hold": "Beklemede",
    "pending": "Bekliyor",
    "watch": "İzleniyor",
    "risk": "Riskli",
    "critical": "Kritik",
    "low": "Düşük",
    "medium": "Orta",
    "high": "Yüksek",
    "controlled": "Kontrollü",
    "stable": "Stabil",
    "success": "Başarılı",
    "approved": "Onaylandı",
    "blocked": "Engellendi",
    "paused": "Duraklatıldı",
}


def gate_status_label(value: str | None) -> str:
    clean = (value or "").strip().lower()
    return GATE_STATUS_LABELS.get(clean, "Bilinmiyor")
