"""BYS360 SP-1A yetkinlik servisleri."""

DEFAULT_COMPETENCIES = [
    ("Yönetim", "Liderlik", "Ekibi yönlendirme, karar alma ve sorumluluk üstlenme becerisi."),
    ("Yönetim", "Stratejik Düşünme", "Kurumsal hedefleri uzun vadeli bakışla değerlendirme becerisi."),
    ("İletişim", "Temsil Yeteneği", "Kurumu ve birimi doğru, dengeli ve güçlü biçimde temsil etme becerisi."),
    ("İletişim", "Takım Çalışması", "Ekip içinde uyumlu, destekleyici ve sonuç odaklı çalışma becerisi."),
    ("Teknik", "Teknik Uzmanlık", "Görev alanına ilişkin teknik bilgi ve uygulama becerisi."),
    ("Operasyon", "Kriz Yönetimi", "Ani gelişen durumlarda sakin, hızlı ve doğru aksiyon alma becerisi."),
    ("Operasyon", "Süreç Takibi", "İşlerin zamanında ve doğru akışla tamamlanmasını sağlama becerisi."),
    ("Analitik", "Veri Analizi", "Veriyi yorumlama, eğilimleri fark etme ve karar desteğe dönüştürme becerisi."),
]


def normalize_competency_name(name):
    return " ".join((name or "").strip().split())


def competency_payload(category, name, description):
    return {
        "competency_category": category,
        "competency_name": normalize_competency_name(name),
        "description": description,
        "minimum_level": 1,
        "default_weight": 0,
        "active": True,
    }
