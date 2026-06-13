from __future__ import annotations



ROUTE_FAMILY = "communication"

REQUIRED_ROUTE_MODULES = [
    "announcements_routes",
    "announcement_popup_routes",
    "feedback_routes",
    "messages_routes",
    "notifications_routes",
    "phase1_routes",
    "phase2_routes",
    "phase3_routes",
    "phase4_routes",
    "phase5_routes",
    "surveys_routes",
]

OPTIONAL_ROUTE_MODULES = [
    "daily_weather_mail_routes",
    "phase8_routes",
    "phase9_routes",
    "phase9a_routes",
    "phase9b_routes",
    "phase9c_routes",
    "phase9d_routes",
]

ROUTE_OWNERSHIP = {
    "messages_routes": ["mesajlaşma", "thread", "attachment", "pin", "mute", "archive"],
    "notifications_routes": ["bildirim", "okundu", "bulk", "sayım"],
    "surveys_routes": ["anket", "yayınla", "kapat", "sonuç"],
    "announcements_routes": ["duyuru", "yeni duyuru"],
    "announcement_popup_routes": [
        "video pop-up duyuru",
        "duyuru yönetimi",
        "ana ekran pop-up",
        "okundu/kapatıldı kayıt akışı",
        "güvenli video/medya gömme",
        "kurum videosu servis yüzeyi",
        "okunma raporu ve CSV dışa aktarım",
    ],
    "feedback_routes": ["geri bildirim"],
}
