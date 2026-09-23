"""BYS360 Performans Tamamlama Faz 12: Final Gate ve %100 kapanış merkezi.

Bu merkez, Performans Yönetimi tamamlama programında Faz 1-11 arasında kurulan
kural, kategori, görünürlük, 3. amir, karne UI, düşük performans, arşiv,
dönem içi not, gelişim önerisi, hatırlatma ve dönem/kapsam/görev üretimi
kontrollerini tek final kapısında toplar.

Kritik sınırlar:
- Faz 12 yeni idari karar veya puan üretmez.
- Önceki fazların kapanış durumunu denetler, raporlar ve devre hazır hale getirir.
- Eksik faz varsa %100 tamamlandı denmez; açık madde olarak rapora düşer.
- Kullanıcı ekranında teknik workflow/debug/endpoint dili gösterilmez.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

BYS360_PERFORMANCE_COMPLETION_PHASE12_FINAL_GATE = True
BYS360_PERFORMANCE_COMPLETION_PHASE12_VERSION = "performance-completion-phase12-final-gate-v1"
BYS360_PERFORMANCE_COMPLETION_PHASE12_NO_NEW_SCORE = True
BYS360_PERFORMANCE_COMPLETION_PHASE12_NO_ADMIN_DECISION = True
BYS360_PERFORMANCE_COMPLETION_PHASE12_ALL_PHASE_GATE = True
BYS360_PERFORMANCE_COMPLETION_PHASE12_DEVIR_READY_REPORT = True
BYS360_PERFORMANCE_COMPLETION_PHASE12_TECHNICAL_LANGUAGE_CLEAN = True

PHASE12_REPORT_TABLE_NAME = "performance_completion_final_gate_reports"

PHASE12_PHASES: list[dict[str, Any]] = [
    {
        "no": 1,
        "name": "Kural Motoru ve Ayar Merkezi",
        "service_files": [
            "app/services/performance/phase1_rule_center.py",
            "app/performance/services/performance_rule_engine.py",
        ],
        "check_script": "scripts/performance/check_bys360_performance_completion_phase1_rule_center.py",
        "markers": ["BYS360_PERFORMANCE_COMPLETION_PHASE1_RULE_CENTER_DELEGATION"],
        "target": "70 altı, 90 üstü ve 1/5 açıklama kurallarının merkezi yönetimi",
    },
    {
        "no": 2,
        "name": "Personel Kategori ve Grup Altyapısı",
        "service_files": ["app/services/performance/phase2_category_center.py"],
        "check_script": "scripts/performance/check_bys360_performance_completion_phase2_category_center.py",
        "markers": ["BYS360_PERFORMANCE_COMPLETION_PHASE2_CATEGORY_CENTER"],
        "target": "Kategori, import ve kişi detayı göstermeyen ortalama yapısı",
    },
    {
        "no": 3,
        "name": "Görünürlük ve Yetki Sınırları",
        "service_files": [
            "app/services/performance/completion_phase3_visibility_scope.py",
            "app/services/performance/phase3_backend_route_guard.py",
        ],
        "check_script": "scripts/performance/check_bys360_performance_completion_phase3_visibility_center.py",
        "markers": ["BYS360_PERFORMANCE_COMPLETION_PHASE3_VISIBILITY_SCOPE"],
        "target": "Menü görünürlüğü, route yetkisi ve veri kapsamı kilidi",
    },
    {
        "no": 4,
        "name": "3. Amir Opsiyonelliği ve Akış Temizliği",
        "service_files": ["app/services/performance/completion_phase4_third_manager_center.py"],
        "check_script": "scripts/performance/check_bys360_performance_completion_phase4_third_manager_center.py",
        "markers": ["BYS360_PERFORMANCE_COMPLETION_PHASE4_THIRD_MANAGER_CENTER"],
        "target": "3. amir yoksa sahte görev/statü yok; yorum ve puan modu ayrımı",
    },
    {
        "no": 5,
        "name": "Karne ve Puanlama Ekranları Kurumsal UI",
        "service_files": ["app/services/performance/phase5_scorecard_ui_policy.py"],
        "check_script": "scripts/performance/check_bys360_performance_completion_phase5_scorecard_ui_center.py",
        "markers": ["BYS360_PERFORMANCE_COMPLETION_PHASE5_SCORECARD_UI_CENTER"],
        "target": "Karne, amir görüşleri, süreç geçmişi ve teknik dil temizliği",
    },
    {
        "no": 6,
        "name": "Başkan/Üst Onayları ve Düşük Performans Süreci",
        "service_files": ["app/services/performance/phase6_low_score_process_center.py"],
        "check_script": "scripts/performance/check_bys360_performance_completion_phase6_low_score_process_center.py",
        "markers": ["BYS360_PERFORMANCE_COMPLETION_PHASE6_LOW_SCORE_PROCESS_CENTER"],
        "target": "70 altı yayın kilidi, ilk/ikinci düşük performans süreci",
    },
    {
        "no": 7,
        "name": "Geçmiş Yıl Karne / Puan Arşivi",
        "service_files": ["app/services/performance/phase7_scorecard_archive_center.py"],
        "check_script": "scripts/performance/check_bys360_performance_completion_phase7_scorecard_archive_center.py",
        "markers": ["BYS360_PERFORMANCE_COMPLETION_PHASE7_SCORECARD_ARCHIVE_CENTER"],
        "target": "Eski puan, manuel/import arşiv ve yetki bazlı geçmiş görünürlüğü",
    },
    {
        "no": 8,
        "name": "Dönem İçi Notlar ve Ara Geri Bildirim",
        "service_files": ["app/services/performance/phase8_midterm_feedback_center.py"],
        "check_script": "scripts/performance/check_bys360_performance_completion_phase8_midterm_feedback_center.py",
        "markers": ["BYS360_PERFORMANCE_COMPLETION_PHASE8_MIDTERM_FEEDBACK_CENTER"],
        "target": "Dönem içi notların puan üretmeden karne/amir bağlamına alınması",
    },
    {
        "no": 9,
        "name": "Gelişim Önerisi ve Rehber Alanı",
        "service_files": ["app/services/performance/phase9_development_guidance_center.py"],
        "check_script": "scripts/performance/check_bys360_performance_completion_phase9_development_guidance_center.py",
        "markers": ["BYS360_PERFORMANCE_COMPLETION_PHASE9_DEVELOPMENT_GUIDANCE_CENTER"],
        "target": "Güçlü yön/gelişim önerisi; otomatik puan/idari karar üretmeme",
    },
    {
        "no": 10,
        "name": "Otomatik Hatırlatma, Aksatan Amir ve Süreç Bildirimleri",
        "service_files": ["app/services/performance/phase10_reminder_notification_center.py"],
        "check_script": "scripts/performance/check_bys360_performance_completion_phase10_reminder_notification_center.py",
        "markers": ["BYS360_PERFORMANCE_COMPLETION_PHASE10_REMINDER_NOTIFICATION_CENTER"],
        "target": "Bekleyen görev, geciken amir, hafta içi mail ve log kontrolü",
    },
    {
        "no": 11,
        "name": "Çoklu Dönem, Özel Kapsam ve Görev Üretimi Final Kontrolü",
        "service_files": ["app/services/performance/phase11_period_scope_assignment_center.py"],
        "check_script": "scripts/performance/check_bys360_performance_completion_phase11_period_scope_assignment_final.py",
        "markers": ["BYS360_PERFORMANCE_COMPLETION_PHASE11_PERIOD_SCOPE_ASSIGNMENT_FINAL"],
        "target": "Dönem türü, kapsam tipi, çakışma ve sahte görev engeli",
    },
]

PHASE12_SETTING_ROWS = [
    ("performance_phase12", "final_gate_enabled", "Performans final gate aktif", "bool", "true", "Faz 1-11 kapanış kontrollerini tek final kapısında doğrular."),
    ("performance_phase12", "require_all_phase_checks", "Tüm faz kontrolleri zorunlu", "bool", "true", "Eksik veya başarısız faz varsa performans %100 kapanmış sayılmaz."),
    ("performance_phase12", "save_final_gate_report", "Final gate raporu saklansın", "bool", "true", "Final kontrol sonucu tabloya ve rapor dosyasına yazılabilir."),
    ("performance_phase12", "technical_language_clean", "Final raporda teknik dil temizliği aktif", "bool", "true", "Workflow/debug/endpoint gibi ifadeler kullanıcı raporunda sadeleştirilir."),
    ("performance_phase12", "devir_ready_report", "Devir hazır raporu üret", "bool", "true", "Performans modülü devir dokümantasyonuna hazır özet üretir."),
]

TECHNICAL_REPLACEMENTS = {
    "workflow": "süreç",
    "endpoint": "bağlantı",
    "debug": "teknik kayıt",
    "traceback": "hata izi",
    "exception": "hata kaydı",
    "authorized_scope": "yetki kapsamı",
    "raw json": "ham veri",
    "json": "veri",
    "stacktrace": "hata izi",
    "phase sync": "süreç eşleşmesi",
}

@dataclass(frozen=True)
class Phase12PhaseStatus:
    no: int
    name: str
    ok: bool
    status_label: str
    missing_files: list[str]
    marker_results: dict[str, bool]
    check_ok: bool | None
    target: str
    note: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "no": self.no,
            "name": self.name,
            "ok": self.ok,
            "status_label": self.status_label,
            "missing_files": list(self.missing_files),
            "marker_results": dict(self.marker_results),
            "check_ok": self.check_ok,
            "target": self.target,
            "note": self.note,
        }


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def phase12_clean_text(value: Any) -> str:
    text_value = _as_text(value)
    for old, new in TECHNICAL_REPLACEMENTS.items():
        text_value = text_value.replace(old, new)
        text_value = text_value.replace(old.upper(), new)
    return text_value


def phase12_file_text(root: str | Path, rel: str) -> str:
    path = Path(root) / rel
    if not path.exists():
        return ""
    try:
        return path.read_text(encoding="utf-8-sig")
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            return ""


def phase12_basic_phase_status(root: str | Path, phase: dict[str, Any], check_ok: bool | None = None) -> Phase12PhaseStatus:
    project_root = Path(root)
    required_files = list(phase.get("service_files", [])) + [phase.get("check_script", "")]
    required_files = [rel for rel in required_files if rel]
    missing = [rel for rel in required_files if not (project_root / rel).exists()]
    marker_results: dict[str, bool] = {}
    for marker in phase.get("markers", []):
        marker_results[marker] = any(marker in phase12_file_text(project_root, rel) for rel in phase.get("service_files", []))
    markers_ok = all(marker_results.values()) if marker_results else True
    file_ok = not missing
    if check_ok is None:
        ok = file_ok and markers_ok
        note = "Dosya ve marker kontrolü tamamlandı." if ok else "Eksik dosya veya marker var."
    else:
        ok = file_ok and markers_ok and bool(check_ok)
        note = "Alt faz kalite kapısı geçti." if ok else "Alt faz kalite kapısı veya dosya/marker kontrolü başarısız."
    return Phase12PhaseStatus(
        no=int(phase.get("no", 0)),
        name=_as_text(phase.get("name")),
        ok=ok,
        status_label="Tamamlandı" if ok else "Kontrol Gerekiyor",
        missing_files=missing,
        marker_results=marker_results,
        check_ok=check_ok,
        target=_as_text(phase.get("target")),
        note=note,
    )


def phase12_completion_score(phase_statuses: list[dict[str, Any]] | list[Phase12PhaseStatus]) -> float:
    if not phase_statuses:
        return 0.0
    ok_count = 0
    for item in phase_statuses:
        if isinstance(item, Phase12PhaseStatus):
            ok_count += 1 if item.ok else 0
        else:
            ok_count += 1 if item.get("ok") else 0
    return round((ok_count / len(phase_statuses)) * 100, 2)


def phase12_final_status_label(score: float) -> str:
    if score >= 100:
        return "Performans Modülü %100 Kapanışa Hazır"
    if score >= 90:
        return "Kapanışa Çok Yakın - Küçük Kontrol Gerekli"
    if score >= 75:
        return "Büyük Ölçüde Tamamlandı - Eksik Faz Kontrolü Gerekli"
    return "Kapanış İçin Eksik Fazlar Var"


def phase12_contract() -> dict[str, Any]:
    return {
        "version": BYS360_PERFORMANCE_COMPLETION_PHASE12_VERSION,
        "markers": {
            "final_gate": BYS360_PERFORMANCE_COMPLETION_PHASE12_FINAL_GATE,
            "no_new_score": BYS360_PERFORMANCE_COMPLETION_PHASE12_NO_NEW_SCORE,
            "no_admin_decision": BYS360_PERFORMANCE_COMPLETION_PHASE12_NO_ADMIN_DECISION,
            "all_phase_gate": BYS360_PERFORMANCE_COMPLETION_PHASE12_ALL_PHASE_GATE,
            "devir_ready_report": BYS360_PERFORMANCE_COMPLETION_PHASE12_DEVIR_READY_REPORT,
        },
        "phase_count": len(PHASE12_PHASES),
        "settings": [
            {
                "module_key": module_key,
                "setting_key": setting_key,
                "label": label,
                "value_type": value_type,
                "default_value": default_value,
                "description": description,
            }
            for module_key, setting_key, label, value_type, default_value, description in PHASE12_SETTING_ROWS
        ],
        "rules": [
            "Faz 1-11 kapanış kontrolleri geçmeden performans modülü %100 kapanmış sayılmaz.",
            "Faz 12 yeni puan, ceza, idari karar veya personel sonucu üretmez.",
            "Final rapor eksik fazları açık şekilde gösterir.",
            "Devir dokümantasyonu için sade Türkçe kapanış özeti üretir.",
        ],
    }


def phase12_generate_markdown_report(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# BYS360 Performans Yönetimi Faz 12 Final Gate Raporu")
    lines.append("")
    lines.append(f"Oluşturulma: {report.get('generated_at', '')}")
    lines.append(f"Genel Durum: {report.get('status_label', '')}")
    lines.append(f"Tamamlanma: %{report.get('completion_score', 0)}")
    lines.append("")
    lines.append("## Faz Kontrol Özeti")
    lines.append("")
    lines.append("| Faz | İş Paketi | Durum | Not |")
    lines.append("|---:|---|---|---|")
    for phase in report.get("phases", []):
        lines.append(f"| {phase.get('no')} | {phase.get('name')} | {phase.get('status_label')} | {phase12_clean_text(phase.get('note'))} |")
    lines.append("")
    if report.get("open_items"):
        lines.append("## Açık Maddeler")
        lines.append("")
        for item in report.get("open_items", []):
            lines.append(f"- Faz {item.get('no')}: {item.get('name')} — {phase12_clean_text(item.get('reason'))}")
        lines.append("")
    else:
        lines.append("## Açık Madde")
        lines.append("")
        lines.append("Açık madde bulunmamaktadır. Performans modülü final kapanışa hazırdır.")
        lines.append("")
    lines.append("## Kapanış Notu")
    lines.append("")
    lines.append("Bu rapor, performans modülünün Faz 1-11 kapanış kontrollerini tek merkezden doğrulamak için üretilmiştir. Faz 12 yalnızca doğrulama ve raporlama katmanıdır; puan, ceza veya idari karar üretmez.")
    lines.append("")
    return "\n".join(lines)


def phase12_build_report(root: str | Path, phase_statuses: list[Phase12PhaseStatus]) -> dict[str, Any]:
    phases = [item.as_dict() for item in phase_statuses]
    score = phase12_completion_score(phases)
    open_items = []
    for item in phases:
        if not item.get("ok"):
            reason_parts = []
            if item.get("missing_files"):
                reason_parts.append("Eksik dosya: " + ", ".join(item.get("missing_files", [])))
            if item.get("check_ok") is False:
                reason_parts.append("Alt kalite kontrol başarısız")
            if any(v is False for v in item.get("marker_results", {}).values()):
                reason_parts.append("Marker kontrolü eksik")
            open_items.append({"no": item.get("no"), "name": item.get("name"), "reason": "; ".join(reason_parts) or "Kontrol gerekiyor"})
    return {
        "package": "performance_completion_phase12_final_gate",
        "version": BYS360_PERFORMANCE_COMPLETION_PHASE12_VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "project_root": str(Path(root)),
        "completion_score": score,
        "status_label": phase12_final_status_label(score),
        "ok": score >= 100 and not open_items,
        "phase_count": len(phases),
        "completed_phase_count": sum(1 for item in phases if item.get("ok")),
        "open_items": open_items,
        "phases": phases,
        "contract": phase12_contract(),
    }


# BYS360 DEFECT AR: ensure_phase12_tables()/seed_phase12_final_gate_settings()/
# save_phase12_final_gate_report() kaldirildi -- repo genelinde (app/,
# tests/, scripts/) hicbir gercek cagirani yoktu (yalnizca artik silinmis
# olan performance_completion_final_gate.py bridge dosyasi re-export
# ediyordu, o da hicbir yerden import edilmiyordu).
