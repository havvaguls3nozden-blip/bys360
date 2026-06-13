
"""Query sagligi sabitleri.

Bu katman liste ekranlarindaki filtre / rozet dilini tek yerde tutsun diye ayrildi.
"""
from __future__ import annotations

ALLOWED_ASSIGNMENT_STATUSES = {"bekliyor", "kismen_tamamlandi", "tamamlandi"}

WORKFLOW_FILTERS = {
    "bekliyor_3_amir",
    "tamamlandi_3_amir",
    "taslak_1_amir",
    "gonderildi_2_amir",
    "goruldu_2_amir",
    "iade_1_amir",
    "yeniden_gonderildi_2_amir",
    "geri_cekildi_1_amir",
    "tamamlandi_2_amir",
}

WORKFLOW_BADGE_CLASS_MAP = {
    "bekliyor_3_amir": "warning",
    "tamamlandi_3_amir": "info",
    "taslak_1_amir": "neutral",
    "gonderildi_2_amir": "info",
    "goruldu_2_amir": "warning",
    "iade_1_amir": "danger",
    "yeniden_gonderildi_2_amir": "info",
    "geri_cekildi_1_amir": "neutral",
    "tamamlandi_2_amir": "success",
}

WORKFLOW_FILTER_ORDER = [
    ("", "Tüm İş Akışları", "neutral"),
    ("bekliyor_3_amir", "3. Amir Bekleniyor", "warning"),
    ("tamamlandi_3_amir", "3. Amir Tamamladı", "info"),
    ("taslak_1_amir", "1. Amir Taslak", "neutral"),
    ("gonderildi_2_amir", "2. Amire Gönderildi", "info"),
    ("goruldu_2_amir", "2. Amir Gördü", "warning"),
    ("iade_1_amir", "İade Edildi", "danger"),
    ("yeniden_gonderildi_2_amir", "Yeniden Gönderildi", "info"),
    ("geri_cekildi_1_amir", "1. Amir Geri Çekti", "neutral"),
    ("tamamlandi_2_amir", "2. Amir Tamamladı", "success"),
]