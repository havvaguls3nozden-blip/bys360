from __future__ import annotations



from app.core.datetime_utils import utc_now
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class SmokeScenario:
    key: str
    label: str
    role: str
    path: str
    goal: str
    expected: str
    tone: str = "info"
    priority: int = 50



SCENARIOS: tuple[SmokeScenario, ...] = (
    SmokeScenario(
        key="dashboard_admin",
        label="Ana dashboard AI görünümü",
        role="admin",
        path="/dashboard",
        goal="Dashboard açıldığında ortak AI operasyon kartlarının görünmesi",
        expected="Performans, HR, açık öneriler ve yönetişim kartları görünmeli; yetkili kullanıcı AI operasyon raporuna geçebilmelidir.",
        tone="critical",
        priority=10,
    ),
    SmokeScenario(
        key="ai_center",
        label="AI kontrol merkezi",
        role="admin",
        path="/admin/ai-center",
        goal="AI log, öneri, geri bildirim, modül sağlığı ve preflight linklerinin açılması",
        expected="Sayfa kırılmadan açılmalı; korumalı mod varsa da nedenini net göstermelidir.",
        tone="critical",
        priority=15,
    ),
    SmokeScenario(
        key="ai_preflight",
        label="AI preflight",
        role="admin",
        path="/admin/ai-preflight",
        goal="Şema, import, endpoint ve şablon kontrollerinin tek yerde görünmesi",
        expected="Hazırlık skoru, warning sayısı ve smoke yolu listesi görünmelidir.",
        tone="critical",
        priority=20,
    ),
    SmokeScenario(
        key="ai_operations",
        label="AI operasyon raporu",
        role="admin",
        path="/admin/ai-operations-report",
        goal="Modüller arası risk ve operasyon odağının yönetici ekranında görünmesi",
        expected="En az performans ve hr modülleri görünmeli; export bağlantısı çalışmalıdır.",
        tone="critical",
        priority=25,
    ),
    SmokeScenario(
        key="performance_recommendations",
        label="Performans AI öneri merkezi",
        role="admin/amir",
        path="/performance/task-management/recommendations",
        goal="Öneri listesi, tek tık filtreler ve export aksiyonlarının açılması",
        expected="Liste kırılmadan gelmeli; AI operasyon raporu butonu görünmelidir.",
        tone="watch",
        priority=30,
    ),
    SmokeScenario(
        key="hr_leave",
        label="İzin yönetimi AI özeti",
        role="admin/ik",
        path="/hr-management/leave",
        goal="İzin baskı özeti, öncelikli aksiyon ve AI rapor export'un görünmesi",
        expected="AI yönetici özeti görünmeli; sayfa AI şema eksikse de güvenli kalmalıdır.",
        tone="watch",
        priority=35,
    ),
    SmokeScenario(
        key="hr_attendance",
        label="Devamsızlık & vekâlet AI özeti",
        role="admin/ik",
        path="/hr-management/attendance",
        goal="Vekâlet baskısı ve yakında bitecek kayıtların özetlenmesi",
        expected="AI rapor export'u ve yönetişim köprüsü görünmelidir.",
        tone="watch",
        priority=40,
    ),
    SmokeScenario(
        key="role_guard",
        label="Rol bazlı görünürlük kontrolü",
        role="personel",
        path="/dashboard",
        goal="Yetkisiz kullanıcıların admin AI ekranlarına güvenli şekilde erişememesi",
        expected="Admin olmayan kullanıcı admin AI ekranlarına gidememeli; dashboard kırılmamalıdır.",
        tone="critical",
        priority=70,
    ),
)


def build_ai_smoke_snapshot() -> dict[str, Any]:
    ordered = sorted(SCENARIOS, key=lambda item: item.priority)
    by_role: dict[str, list[dict[str, Any]]] = {}
    rows: list[dict[str, Any]] = []
    for item in ordered:
        row = {
            "key": item.key,
            "label": item.label,
            "role": item.role,
            "path": item.path,
            "goal": item.goal,
            "expected": item.expected,
            "tone": item.tone,
            "priority": item.priority,
        }
        rows.append(row)
        by_role.setdefault(item.role, []).append(row)

    summary = {
        "scenario_total": len(rows),
        "critical_total": sum(1 for row in rows if row["tone"] == "critical"),
        "watch_total": sum(1 for row in rows if row["tone"] == "watch"),
        "info_total": sum(1 for row in rows if row["tone"] == "info"),
        "role_total": len(by_role),
    }

    top_notes = [
        {
            "title": "Önce admin omurgasını dolaşın",
            "body": "Dashboard, AI kontrol merkezi, preflight ve operasyon raporu ilk dört kontrol olarak tamamlanmalı.",
            "tone": "critical",
        },
        {
            "title": "Sonra işlem üreten modülleri açın",
            "body": "Performans AI önerileri ile HR izin/vekâlet özetleri export akışlarıyla birlikte kontrol edilmeli.",
            "tone": "watch",
        },
        {
            "title": "En sonda görünürlük ve rol kısıtlarını doğrulayın",
            "body": "Yetkisiz kullanıcıların admin AI ekranlarına erişemediği mutlaka kontrol edilmeli.",
            "tone": "critical",
        },
    ]

    return {
        "generated_at": utc_now(),
        "summary": summary,
        "rows": rows,
        "by_role": by_role,
        "top_notes": top_notes,
    }