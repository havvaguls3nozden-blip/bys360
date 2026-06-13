from __future__ import annotations



import csv
import io
from typing import Any


def _pill(ok: bool) -> str:
    return "Geçti" if ok else "Açık"


def build_go_live_smoke_report(report: dict[str, Any]) -> dict[str, Any]:
    cards = dict(report.get("cards") or {})
    summary = dict(report.get("summary") or {})
    signoff = dict(report.get("signoff") or {})
    publish_summary = dict(report.get("publish_summary") or {})

    rows: list[dict[str, Any]] = []

    def add_row(*, code: str, title: str, ok: bool, detail: str, action: str, category: str) -> None:
        rows.append(
            {
                "code": code,
                "title": title,
                "ok": bool(ok),
                "status_label": _pill(bool(ok)),
                "severity": "ok" if ok else "critical",
                "detail": detail,
                "action": action,
                "category": category,
            }
        )

    active_period_ok = (cards.get("active_period") or "").strip() not in {"", "Aktif dönem yok"}
    add_row(
        code="active_period",
        title="Aktif dönem tanımı",
        ok=active_period_ok,
        detail="Görev, yayın ve geri bildirim akışının gerçek dönem üstünde çalıştığı doğrulanır.",
        action="Yanlışsa önce doğru dönemi aktif hale getir.",
        category="donem",
    )

    add_row(
        code="release_score",
        title="Canlı skoru taban eşiği",
        ok=int(cards.get("release_score") or 0) >= 70,
        detail="70 altı skor canlı kararını zayıflatır; 90 ve üzeri daha güvenli kabul edilir.",
        action="Skoru düşüren blokaj ve açık kontrolleri kapat.",
        category="hazirlik",
    )

    add_row(
        code="failed_checks",
        title="Açık canlı kontrol maddesi",
        ok=int(summary.get("failed_check_count") or 0) == 0,
        detail="UAT listesindeki ana kontrollerin açık kalıp kalmadığı okunur.",
        action="Canlı kontrol listesinde açık görünen maddeleri tamamla.",
        category="uat",
    )

    add_row(
        code="critical_blockers",
        title="Kritik blokaj yok",
        ok=int(summary.get("blocker_count") or 0) == 0,
        detail="Blokajlar kapanmadan canlıya geçiş önerilmez.",
        action="Önce blokajları temizle; ardından tekrar ölç.",
        category="blokaj",
    )

    add_row(
        code="overdue_assignments",
        title="Geciken görev yok",
        ok=int(cards.get("overdue_assignments") or 0) == 0,
        detail="Geciken değerlendirme görevleri ilk kullanım deneyimini doğrudan bozar.",
        action="Görev yönetimi ekranından ilgili amirleri kapat.",
        category="gorev",
    )

    add_row(
        code="critical_requests",
        title="Kritik yaşa ulaşan talep yok",
        ok=int(cards.get("critical_feedback_requests") or 0) == 0,
        detail="5 gün ve üzeri açık talepler canlı memnuniyetini düşüren ana sinyaldir.",
        action="Talep detaylarından uygun randevu ya da kapanış işlemini yap.",
        category="geri_bildirim",
    )

    add_row(
        code="overdue_meetings",
        title="Durumu kapanmamış eski görüşme yok",
        ok=int(cards.get("overdue_meetings") or 0) == 0,
        detail="Eski planlı veya ertelenmiş görüşmeler audit görünümünü kirletir.",
        action="Görüşme detayına girip sonucu güncelle.",
        category="gorusme",
    )

    add_row(
        code="publish_block",
        title="Yayın bloklu sonuç kalmadı",
        ok=int(summary.get("blocked_publish") or 0) == 0,
        detail="Açıklama ve yayın kuralı eksikleri sonucu personele açılmayı engeller.",
        action="Yayın ön kontrol ekranında blok nedenlerini tek tek kapat.",
        category="yayin",
    )

    add_row(
        code="publish_visibility",
        title="Personele görünürlük dengesi",
        ok=(int(summary.get("employee_visible") or 0) == 0) or (int(publish_summary.get("ready_count") or 0) >= 0),
        detail="Personele açık sonuçlar ile iç kullanımda kalanlar aynı kapanış notunda okunur.",
        action="Gerekirse yayın planını kademeli uygula ve İK onayı sonrası aç.",
        category="gorunurluk",
    )

    passed = sum(1 for row in rows if row["ok"])
    failed = len(rows) - passed

    if failed == 0 and (signoff.get("label") or "") == "Hazır":
        decision = {
            "label": "Sunuma Hazır",
            "tone": "ok",
            "detail": "Yönetici sunumunda performans modülü için final kabul önerisi güvenle verilebilir.",
        }
    elif failed <= 2:
        decision = {
            "label": "Koşullu Sunum",
            "tone": "watch",
            "detail": "Sunum yapılabilir; ancak açık kalan küçük başlıklar not edilerek kontrollü onay istenmelidir.",
        }
    else:
        decision = {
            "label": "Sunum Öncesi Kapanış Gerekli",
            "tone": "critical",
            "detail": "Yönetim sunumundan önce açık başlıkları azaltmak daha güvenli olur.",
        }

    return {
        "rows": rows,
        "summary": {
            "passed": passed,
            "failed": failed,
            "total": len(rows),
        },
        "decision": decision,
    }


def export_go_live_smoke_csv(smoke: dict[str, Any]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["kod", "kategori", "durum", "baslik", "detay", "onerilen_adim"])
    for row in smoke.get("rows") or []:
        writer.writerow(
            [
                row.get("code") or "-",
                row.get("category") or "genel",
                row.get("status_label") or "-",
                row.get("title") or "-",
                row.get("detail") or "-",
                row.get("action") or "-",
            ]
        )
    return buffer.getvalue()



def export_go_live_management_brief_txt(report: dict[str, Any], smoke: dict[str, Any]) -> str:
    cards = report.get("cards") or {}
    signoff = report.get("signoff") or {}
    summary = report.get("summary") or {}
    smoke_summary = smoke.get("summary") or {}
    smoke_decision = smoke.get("decision") or {}
    generated_at = report.get("generated_at")
    generated_text = generated_at.strftime("%d.%m.%Y %H:%M") if generated_at else "-"

    headline = "Performans modülü canlı öncesi final görünümü"
    if smoke_decision.get("label") == "Sunuma Hazır":
        executive_line = "Modülün çekirdek akışları yönetim sunumuna uygun seviyede toparlanmış görünüyor."
    elif smoke_decision.get("label") == "Koşullu Sunum":
        executive_line = "Sunum yapılabilir; ancak açık başlıklar not edilerek kontrollü ilerlenmesi daha doğru olur."
    else:
        executive_line = "Sunum öncesinde birkaç kritik ve görünür başlığın kapatılması daha güvenli olacaktır."

    lines = [
        "BYS360 Performans Modülü | Faz M Yönetici Sunum Notu",
        f"Üretim Zamanı: {generated_text}",
        f"Aktif Dönem: {cards.get('active_period') or '-'}",
        f"Canlı Skoru: {cards.get('release_score') or 0} / 100",
        f"UAT Kararı: {signoff.get('label') or '-'}",
        f"Sunum Kararı: {smoke_decision.get('label') or '-'}",
        "",
        headline,
        executive_line,
        "",
        "Yöneticiye Tek Cümlelik Özet",
        f"- {signoff.get('detail') or '-'}",
        f"- {smoke_decision.get('detail') or '-'}",
        "",
        "Kritik Sayılar",
        f"- Açık canlı kontrol: {summary.get('failed_check_count') or 0}",
        f"- Blokaj: {summary.get('blocker_count') or 0}",
        f"- Uyarı: {summary.get('warning_count') or 0}",
        f"- Yayın bloklu sonuç: {summary.get('blocked_publish') or 0}",
        f"- Personele açık sonuç: {summary.get('employee_visible') or 0}",
        f"- Smoke test geçen: {smoke_summary.get('passed') or 0} / {smoke_summary.get('total') or 0}",
        "",
        "Sunumda Özellikle Söylenecekler",
        "- Kör değerlendirme yok; sonraki amir önceki amirin puanını ve kanaatini görebilir.",
        "- Sonuçlar İK onayı olmadan personele açılmaz.",
        "- 1 ve 5 puanlarda gerekçe; 70 altı ve 90 üstü sonuçlarda ayrıntılı genel görüş zorunludur.",
        "- 3. amir yorumcu olarak çalışır; puan etkisi varsayılan senaryoda %0’dır.",
        "",
        "Sunum Öncesi Son Adımlar",
    ]
    for row in [r for r in (smoke.get("rows") or []) if not r.get("ok")][:5]:
        lines.append(f"- {row.get('title')}: {row.get('action')}")

    return "\n".join(lines).strip() + "\n"