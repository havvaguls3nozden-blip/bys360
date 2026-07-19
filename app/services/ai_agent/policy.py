from __future__ import annotations

import re
from dataclasses import dataclass
from collections.abc import Iterable

AI_AGENT_AG1_VERSION = "AG-1 V1"
AI_AGENT_AG2_VERSION = "AG-2 V1"
AI_AGENT_AG3_VERSION = "AG-3 V1"
AI_AGENT_AG4_VERSION = "AG-4 V1"
AI_AGENT_AG5_VERSION = "AG-5 V1"
AI_AGENT_AG6_VERSION = "AG-6 V1"
AI_AGENT_MODE_LABEL = "Yetki kontrollü kurumsal BYS360 Asistanı ve onaylı aksiyon kuyruğu ile birleşik çalışma"
AI_AGENT_DECISION_NOTICE = "BYS360 Asistanı idari karar vermez; yalnızca özet, yönlendirme ve öneri üretir."
AI_AGENT_NO_AUTOMATION_NOTICE = "AG-5 aşamasında kullanıcı onayı olmadan veri değiştiren otomatik işlem yapılmaz."
AI_AGENT_PERFORMANCE_NOTICE = "Performans bağlantısı yalnızca yetki kontrollü sayı/özet üretir; puan, onay veya yayın işlemi yapmaz."
AI_AGENT_DASHBOARD_KPI_NOTICE = "KPI/Hedef bağlantısı yalnızca yönetici brifingi, risk farkındalığı ve güvenli yönlendirme üretir; hedef kapatma veya veri değiştirme işlemi yapmaz."
AI_AGENT_ASSISTANT_PANEL_NOTICE = "BYS360 Asistanı paneli hassas içerik göstermez; yalnızca güvenli özet, rehber cevap ve yönlendirme kartı sunar."
AI_AGENT_ACTION_QUEUE_NOTICE = "AG-5 onaylı aksiyon kuyruğu yalnızca öneri kaydı oluşturur; iş süreci işlemi uygulamaz."
AI_AGENT_SECURITY_NOTICE = "AG-6 canlı güvenlik kapısı; yetki, hassas veri ve public/protected endpoint sınırlarını denetler."

SENSITIVE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b[1-9][0-9]{10}\b"), "[MASKELI_TCKN]"),
    (re.compile(r"\b05\d{9}\b"), "[MASKELI_TELEFON]"),
    (re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "[MASKELI_EPOSTA]"),
)

@dataclass(frozen=True)
class AgentCapability:
    key: str
    title: str
    description: str
    route: str
    safety_level: str = "güvenli özet"


AG5_CAPABILITIES: tuple[AgentCapability, ...] = (
    AgentCapability(
        key="security_gate",
        title="Canlı güvenlik kontrolü",
        description="BYS360 Asistanı endpointleri, hassas veri sınırı ve yetki kaçakları için canlı güvenlik kontrolüne yönlendirir.",
        route="/ai-agent/panel",
        safety_level="güvenlik kontrolü",
    ),
    AgentCapability(
        key="action_queue",
        title="Onaylı aksiyon kuyruğu",
        description="BYS360 Asistanı önerileri onay bekleyen güvenli kayıtlar olarak listeler; uygulama işlemi yapmaz.",
        route="/ai-agent/panel",
        safety_level="onay gerektiren öneri",
    ),
    AgentCapability(
        key="assistant_panel",
        title="Sağ alt BYS360 Asistanı paneli",
        description="Kullanıcıya performans, KPI/Hedef ve destek özetlerini aynı panelde güvenli biçimde gösterir.",
        route="/ai-agent/panel",
    ),
    AgentCapability(
        key="executive_briefing",
        title="Başkan yönetici brifingi",
        description="Performans ve KPI/Hedef göstergelerini karar üretmeden kısa yönetici özeti haline getirir.",
        route="/ai-agent/panel",
    ),
    AgentCapability(
        key="kpi_dashboard",
        title="KPI/Hedef dashboard özeti",
        description="Hedef gerçekleşme, riskli hedef ve takip edilmesi gereken KPI sayılarını güvenli biçimde özetler.",
        route="/performans/stratejik/kpi-dashboard",
    ),
    AgentCapability(
        key="target_list",
        title="KPI ve hedef listesi",
        description="Hedef kayıtlarına güvenli yönlendirme sağlar; hedef oluşturma, kapatma veya değiştirme işlemi yapmaz.",
        route="/performans/stratejik/hedefler",
    ),
    AgentCapability(
        key="kpi_analysis",
        title="KPI analiz merkezi",
        description="Riskli, geciken veya düşük gerçekleşmeli hedefler için analiz ekranına yönlendirir.",
        route="/performans/stratejik/kpi-analiz",
    ),
    AgentCapability(
        key="performance_status",
        title="Performans süreci özeti",
        description="Bekleyen değerlendirme, dönem tamamlanma ve yayın hazırlığı için güvenli özet üretir.",
        route="/performance/dashboard",
    ),
    AgentCapability(
        key="president_approval",
        title="Başkan/Üst Onay takibi",
        description="70 altı sonuçlarda onay bekleyen süreçlere yönlendirme sağlar; onay veya ret işlemi yapmaz.",
        route="/performance/president-approvals",
    ),
    AgentCapability(
        key="publish_lock",
        title="Yayın kilidi kontrolü",
        description="Yayın bekleyen veya kilitli karneler için sayı düzeyinde güvenli özet verir.",
        route="/performance/process-tracking",
    ),
    AgentCapability(
        key="delayed_supervisors",
        title="Aksatan amir özeti",
        description="Geciken değerlendirme görevleri için kişisel detay dökmeden yönetsel takip alanına yönlendirir.",
        route="/performance/meeting-development/faz9",
    ),
    AgentCapability(
        key="performance_reports",
        title="Performans raporları",
        description="Dönem, kategori ve düşük performans yoğunluğu raporlarına güvenli geçiş sağlar.",
        route="/performance/reports",
    ),
    AgentCapability(
        key="support_triage",
        title="Destek ve talep yoğunluğu",
        description="Açık destek taleplerini sayı/özet düzeyinde ele alır; kişisel içerik dökmez.",
        route="/support",
    ),
    AgentCapability(
        key="settings_visibility",
        title="Ayar ve yetki kontrolü",
        description="Rol, menü ve modül görünürlüğü için doğru ayar ekranına yönlendirir.",
        route="/settings",
    ),
)

AG6_CAPABILITIES = AG5_CAPABILITIES

# Geriye uyumluluk adları
AG4_CAPABILITIES = AG5_CAPABILITIES
AG3_CAPABILITIES = AG5_CAPABILITIES
AG2_CAPABILITIES = AG5_CAPABILITIES
AG1_CAPABILITIES = AG5_CAPABILITIES


def redact_sensitive_text(value: object) -> str:
    """Kullanıcı metnini hassas veri açısından güvenli hâle getirir."""
    text = str(value or "")
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text.strip()


def capability_payload(capabilities: Iterable[AgentCapability] = AG4_CAPABILITIES) -> list[dict[str, str]]:
    return [
        {
            "key": item.key,
            "title": item.title,
            "description": item.description,
            "route": item.route,
            "safety_level": item.safety_level,
        }
        for item in capabilities
    ]
