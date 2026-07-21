from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Any

from app.core.datetime_utils import utc_now
from app.services.performance.go_live_service import build_performance_go_live_center


def _severity_rank(value: str) -> int:
    mapping = {"critical": 0, "warning": 1, "info": 2}
    return mapping.get(str(value or "").strip().lower(), 9)


def _status_bundle(report: dict[str, Any]) -> tuple[str, str, str]:
    blocker_count = int(report.get("blocker_count") or 0)
    failed_checks = int(report.get("failed_check_count") or 0)
    warning_count = int(report.get("warning_count") or 0)
    release_score = int(((report.get("cards") or {}).get("release_score") or 0))

    if blocker_count or failed_checks:
        return (
            "Hazır Değil",
            "critical",
            "Kritik blokajlar kapanmadan veya başarısız maddeler temizlenmeden canlıya geçilmemeli.",
        )
    if warning_count or release_score < 100:
        return (
            "Koşullu Hazır",
            "watch",
            "Çekirdek akış çalışır durumda; yine de uyarılar kapatılırsa ilk kullanım kalitesi belirgin biçimde artar.",
        )
    return (
        "Hazır",
        "ok",
        "Canlı öncesi kritik kontroller temiz görünüyor. Kalan iş daha çok operasyon takibi seviyesinde.",
    )


def build_go_live_uat_report(
    *,
    active_period: Any | None,
    requests_list: list[Any],
    meetings: list[Any],
    now: datetime | None = None,
    scope_employee_ids: list[int] | None = None,
) -> dict[str, Any]:
    now = now or utc_now()
    base = build_performance_go_live_center(
        active_period=active_period,
        requests_list=requests_list,
        meetings=meetings,
        now=now,
        scope_employee_ids=scope_employee_ids,
    )

    cards = dict(base.get("cards") or {})
    blockers = list(base.get("blockers") or [])
    warnings = list(base.get("warnings") or [])
    release_checks = list(base.get("release_checks") or [])
    action_items = list(base.get("action_items") or [])
    publish_summary = dict(base.get("publish_summary") or {})

    checklist_rows: list[dict[str, Any]] = []
    for row in release_checks:
        ok = bool(row.get("ok"))
        checklist_rows.append(
            {
                "title": row.get("label") or "Kontrol",
                "detail": row.get("detail") or "-",
                "status_label": "Geçti" if ok else "Açık",
                "severity": "ok" if ok else "critical",
                "category": "canli_kontrol",
            }
        )

    issue_rows: list[dict[str, Any]] = []
    for item in blockers:
        issue_rows.append(
            {
                "severity": "critical",
                "category": "blokaj",
                "title": item.get("title") or "Blokaj",
                "detail": item.get("detail") or "-",
                "action": item.get("action") or "İlgili ekranda kontrol et.",
            }
        )
    for item in warnings:
        issue_rows.append(
            {
                "severity": "warning",
                "category": "uyari",
                "title": item.get("title") or "Uyarı",
                "detail": item.get("detail") or "-",
                "action": item.get("action") or "Uygun ekranda gözden geçir.",
            }
        )
    for reason, count in (publish_summary.get("blocked_reasons_summary") or []):
        issue_rows.append(
            {
                "severity": "warning",
                "category": "yayin_blokaji",
                "title": f"Yayın blokaj nedeni · {count} kayıt",
                "detail": reason,
                "action": "Yayın ön kontrol ekranından ilgili kayıtları kapat.",
            }
        )

    issue_rows.sort(key=lambda row: (_severity_rank(str(row.get("severity"))), str(row.get("title") or "").lower()))

    status_label, status_tone, status_detail = _status_bundle(
        {
            "blocker_count": len(blockers),
            "failed_check_count": sum(1 for row in release_checks if not row.get("ok")),
            "warning_count": len(warnings),
            "cards": cards,
        }
    )

    summary = {
        "passed_check_count": sum(1 for row in release_checks if row.get("ok")),
        "failed_check_count": sum(1 for row in release_checks if not row.get("ok")),
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "issue_count": len(issue_rows),
        "ready_to_publish": int(publish_summary.get("ready_count") or 0),
        "blocked_publish": int(publish_summary.get("blocked_count") or 0),
        "employee_visible": int(cards.get("published_to_employee") or 0),
        "internal_preview": int(publish_summary.get("internal_preview_count") or 0),
    }

    signoff = {
        "label": status_label,
        "tone": status_tone,
        "detail": status_detail,
    }

    return {
        **base,
        "generated_at": now,
        "summary": summary,
        "signoff": signoff,
        "checklist_rows": checklist_rows,
        "issue_rows": issue_rows,
        "next_actions": action_items[:6],
    }


def export_go_live_uat_txt(report: dict[str, Any]) -> str:
    generated_at = report.get("generated_at")
    generated_text = generated_at.strftime("%d.%m.%Y %H:%M") if generated_at else "-"
    summary = report.get("summary") or {}
    signoff = report.get("signoff") or {}
    cards = report.get("cards") or {}
    lines = [
        "BYS360 Performans Modülü | Faz L UAT Özeti",
        f"Üretim Zamanı: {generated_text}",
        f"Aktif Dönem: {cards.get('active_period') or '-'}",
        f"Canlı Skoru: {cards.get('release_score') or 0} / 100",
        f"Sonuç: {signoff.get('label') or '-'}",
        f"Açıklama: {signoff.get('detail') or '-'}",
        "",
        "Özet Sayaçlar",
        f"- Geçen kontrol: {summary.get('passed_check_count') or 0}",
        f"- Açık kontrol: {summary.get('failed_check_count') or 0}",
        f"- Blokaj: {summary.get('blocker_count') or 0}",
        f"- Uyarı: {summary.get('warning_count') or 0}",
        f"- Hemen açılabilir sonuç: {summary.get('ready_to_publish') or 0}",
        f"- Yayın bloklu sonuç: {summary.get('blocked_publish') or 0}",
        "",
        "Canlı Kontrol Maddeleri",
    ]
    for row in report.get("checklist_rows") or []:
        lines.append(f"- [{row.get('status_label')}] {row.get('title')}: {row.get('detail')}")
    issue_rows = report.get("issue_rows") or []
    if issue_rows:
        lines.extend(["", "Kapatılacak Başlıklar"])
        for row in issue_rows:
            lines.append(
                f"- ({row.get('category')}) {row.get('title')}: {row.get('detail')} | Adım: {row.get('action')}"
            )
    next_actions = report.get("next_actions") or []
    if next_actions:
        lines.extend(["", "Önerilen Son Adımlar"])
        for row in next_actions:
            lines.append(f"- {row.get('title')}: {row.get('detail')}")
    return "\n".join(lines).strip() + "\n"


def export_go_live_issues_csv(report: dict[str, Any]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["seviye", "kategori", "baslik", "detay", "onerilen_adim"])
    for row in report.get("issue_rows") or []:
        writer.writerow(
            [
                row.get("severity") or "info",
                row.get("category") or "genel",
                row.get("title") or "-",
                row.get("detail") or "-",
                row.get("action") or "-",
            ]
        )
    return buffer.getvalue()


def export_go_live_release_packet_txt(report: dict[str, Any]) -> str:
    generated_at = report.get("generated_at")
    generated_text = generated_at.strftime("%d.%m.%Y %H:%M") if generated_at else "-"
    signoff = report.get("signoff") or {}
    cards = report.get("cards") or {}
    publish_summary = report.get("publish_summary") or {}
    lines = [
        "BYS360 Performans Modülü | Faz L Canlı Öncesi Paket",
        f"Üretim Zamanı: {generated_text}",
        f"Aktif Dönem: {cards.get('active_period') or '-'}",
        f"Canlı Skoru: {cards.get('release_score') or 0} / 100",
        f"Karar: {signoff.get('label') or '-'}",
        "",
        "Yayın Özeti",
        f"- Hemen açılabilir: {publish_summary.get('ready_count') or 0}",
        f"- Bloklu: {publish_summary.get('blocked_count') or 0}",
        f"- İç kullanım: {publish_summary.get('internal_preview_count') or 0}",
        f"- Personele açık: {publish_summary.get('published_count') or cards.get('published_to_employee') or 0}",
        "",
        "Blokaj ve Uyarılar",
    ]
    for row in report.get("issue_rows") or []:
        lines.append(f"- [{row.get('severity')}] {row.get('title')}: {row.get('detail')}")
    lines.extend(["", "Hazır Aksiyonlar"])
    for row in report.get("next_actions") or []:
        lines.append(f"- {row.get('title')} -> {row.get('href') or '-'}")
    return "\n".join(lines).strip() + "\n"