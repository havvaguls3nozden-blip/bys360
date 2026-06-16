from __future__ import annotations

from app.core.datetime_utils import utc_now
from datetime import datetime
from typing import Any

from app.services.pilot_readiness_service import summarize_pilot_readiness


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/pilot_execution_service.py:15")
        return 0


def _scenario(*, title: str, status: str, detail: str, owner: str, action: str, href: str | None = None) -> dict[str, Any]:
    tone_map = {"ready": "ok", "watch": "watch", "blocked": "critical"}
    label_map = {"ready": "Hazır", "watch": "Takip", "blocked": "Bloke"}
    return {
        "title": title,
        "status": status,
        "tone": tone_map.get(status, "watch"),
        "status_label": label_map.get(status, "Takip"),
        "detail": detail,
        "owner": owner,
        "action": action,
        "href": href,
    }


def summarize_pilot_execution(*, active_period: Any | None = None, requests_list: list[Any] | None = None, meetings: list[Any] | None = None, now: datetime | None = None, scope_employee_ids: list[int] | None = None, report: dict[str, Any] | None = None, smoke: dict[str, Any] | None = None, **_: Any) -> dict[str, Any]:
    readiness = summarize_pilot_readiness(
        active_period=active_period,
        requests_list=requests_list,
        meetings=meetings,
        now=now or utc_now(),
        scope_employee_ids=scope_employee_ids,
        report=report,
        smoke=smoke,
    )
    summary = dict(readiness.get("summary") or {})
    blocked_count = _safe_int(summary.get("blocker_count"))
    smoke_failed = _safe_int(summary.get("smoke_failed"))
    release_score = _safe_int(summary.get("release_score"))

    scenario_rows = [
        _scenario(
            title="2025 · 1. dönem pilot veri girişi",
            status="ready" if active_period else "watch",
            detail="Pilot simülasyonun ilk turunda karne çıktıları ve görev omurgası görünür olmalı.",
            owner="İK",
            action="Personel, görev ve karne çıktısını pilot veriyle doğrula.",
            href="/performance/go-live-center/uat",
        ),
        _scenario(
            title="2025 · 2. dönem pilot veri girişi",
            status="ready" if release_score >= 70 else "watch",
            detail="İkinci turda aynı ekranların tutarlı tekrar üretildiği kontrol edilmeli.",
            owner="İK + BT",
            action="İkinci dönem verisiyle kıyas ve yayın ön kontrolünü yeniden çalıştır.",
            href="/performance/v2/faz5/publish/preflight",
        ),
        _scenario(
            title="Yönetici kıyas ve şeffaf değerlendirme provası",
            status="ready" if blocked_count == 0 else "watch",
            detail="2. yönetici görünürlüğü ve personel analizi ekranı pilot turda birlikte kontrol edilmeli.",
            owner="Yönetici + İK",
            action="Personel analizi ekranı ve örnek karneler birlikte gözden geçirilsin.",
            href="/performance/personel-analizi",
        ),
        _scenario(
            title="Koordinatör hızlı eğitim turu",
            status="watch",
            detail="10–15 dakikalık çevrim içi anlatım ve örnek değerlendirme akışı pilot kapanışın parçası olmalı.",
            owner="İK + BT",
            action="Kısa eğitim, ekran linkleri ve soru-cevap notu hazırlanmalı.",
            href=None,
        ),
        _scenario(
            title="Yayın gizliliği ve İK onayı",
            status="ready" if _safe_int(summary.get("failed_check_count")) == 0 else "watch",
            detail="Sonuçlar İK onayı gelmeden personele açılmamalı; kapanışta bu senaryo ayrıca doğrulanmalı.",
            owner="İK",
            action="Yayın ön kontrol ve görünürlük adımı kapanış listesinde imzalanmalı.",
            href="/performance/v2/faz5/publish/preflight",
        ),
        _scenario(
            title="Yönetici sunumu ve final smoke",
            status="ready" if smoke_failed == 0 else "blocked",
            detail="Yönetim sunumu öncesi final smoke listesi ve kısa yönetici notu tek pakette hazır olmalı.",
            owner="BT + İK",
            action="Smoke ekranı, issue CSV ve yönetici notu birlikte son kez çalıştırılmalı.",
            href="/performance/go-live-center/smoke-test",
        ),
    ]

    notes = [
        "2025 yılı 1. ve 2. dönem verileriyle karne çıktıları pilot turda görülmeli.",
        "Koordinatörler için 10–15 dakikalık kısa uygulamalı eğitim planı kapatılmalı.",
        "TC yerine sicil no / kurum ID kullanımı pilot veride korunmalı.",
        "İK onayı tamamlanmadan sonuçlar personele açılmamalı.",
    ]

    if any(row["status"] == "blocked" for row in scenario_rows):
        status = "blocked"
        message = "Pilot akışında blokaj oluşturan maddeler var; kapanış yapılmadan önce temizlenmeli."
    elif any(row["status"] == "watch" for row in scenario_rows):
        status = "watch"
        message = "Pilot planı yürür; ancak birkaç başlık operasyonel takip gerektiriyor."
    else:
        status = "ready"
        message = "Pilot icrası ve kullanıcı kabul turu için senaryolar hazır görünüyor."

    return {
        "status": status,
        "message": message,
        "scenario_rows": scenario_rows,
        "notes": notes,
        "summary": {
            "scenario_count": len(scenario_rows),
            "ready_count": sum(1 for row in scenario_rows if row["status"] == "ready"),
            "watch_count": sum(1 for row in scenario_rows if row["status"] == "watch"),
            "blocked_count": sum(1 for row in scenario_rows if row["status"] == "blocked"),
        },
    }


def get_pilot_execution_summary(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return summarize_pilot_execution(*args, **kwargs)


def run_pilot_execution_checks(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
    return list(summarize_pilot_execution(*args, **kwargs).get("scenario_rows") or [])


def build_pilot_execution_context(*args: Any, **kwargs: Any) -> dict[str, Any]:
    summary = summarize_pilot_execution(*args, **kwargs)
    return {
        "status": summary.get("status", "watch"),
        "message": summary.get("message", "Pilot icrası gözden geçirilmeli."),
        "summary": summary.get("summary") or {},
        "scenario_rows": summary.get("scenario_rows") or [],
        "notes": summary.get("notes") or [],
    }
