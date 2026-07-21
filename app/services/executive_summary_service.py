from __future__ import annotations

import json
import os
import urllib.request
from datetime import timedelta
from typing import Any

from flask import current_app
from sqlalchemy import func

from app.core.datetime_utils import utc_now
from app.extensions import db
from app.models import MailLog, User
from app.services.mail_core import create_mail_log, send_email

EXECUTIVE_SUMMARY_MAIL_TYPE = "executive_daily_summary"
REPORT_TYPES = {
    "night": {
        "label": "Gece Sistem Kontrolü",
        "hour_label": "00:01",
        "subject_prefix": "BYS360 Gece Sistem Kontrolü ve Tarihi Alan Durum Raporu",
        "opening": "Bu e-posta BYS360 tarafından gece sistem kontrolü, mail altyapısı doğrulaması ve günlük kapanış özeti amacıyla otomatik oluşturulmuştur.",
        "manager_note": "Gece kontrolünde sistemin temel çalışma durumu, e-posta gönderimi ve kritik süreç göstergeleri izlenmiştir.",
    },
    "morning": {
        "label": "Günaydın Yeni Gün Raporu",
        "hour_label": "08:30",
        "subject_prefix": "Günaydın | BYS360 Yeni Gün Yönetici Özeti",
        "opening": "Günaydın. Bu e-posta BYS360 tarafından yeni gün başlangıcı için yönetici özeti, Tarihi Alan hava durumu ve bekleyen süreç bilgilendirmesi amacıyla otomatik oluşturulmuştur.",
        "manager_note": "Yeni güne başlarken bekleyen süreçler, geri bildirimler, destek talepleri ve performans görevleri özetlenmiştir.",
    },
}


def _first_existing_model(name: str):
    try:
        import app.models as models
        return getattr(models, name, None)
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/executive_summary_service.py:42")
        return None


def _model_count(model: Any, *criteria: Any) -> int:
    if model is None:
        return 0
    try:
        query = model.query
        for item in criteria:
            query = query.filter(item)
        return int(query.count() or 0)
    except Exception:
        current_app.logger.warning("Yönetici özeti sayacı güvenli modda atlandı: %s", getattr(model, "__name__", model), exc_info=True)
        return 0


def _safe_status_count(model: Any, statuses: list[str]) -> int:
    if model is None or not hasattr(model, "status"):
        return 0
    try:
        return _model_count(model, model.status.in_(statuses))
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/executive_summary_service.py:64")
        return 0


def _dt_text(value: Any) -> str:
    try:
        return value.strftime("%d.%m.%Y %H:%M")
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/executive_summary_service.py:71")
        return "-"


def _today_text() -> str:
    return utc_now().strftime("%d.%m.%Y")


def _weather_summary() -> dict[str, Any]:
    """Tarihi Alan hava durumu. Dış servis çalışmazsa ekran/mail bozulmaz."""
    lat = os.getenv("BYS360_WEATHER_LAT", "40.145").strip()
    lon = os.getenv("BYS360_WEATHER_LON", "26.405").strip()
    url = (
        "https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        "&current=temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,precipitation"
        "&timezone=Europe%2FIstanbul"
    )
    try:
        with urllib.request.urlopen(url, timeout=8) as response:
            payload = json.loads(response.read().decode("utf-8"))
        current = payload.get("current") or {}
        return {
            "status": "Güncel veri alındı",
            "temperature": current.get("temperature_2m"),
            "feels_like": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "wind": current.get("wind_speed_10m"),
            "precipitation": current.get("precipitation"),
            "source": "Open-Meteo",
        }
    except Exception as exc:
        current_app.logger.warning("Yönetici özeti hava durumu güvenli moda geçti: %s", exc)
        return {
            "status": "Hava verisi geçici olarak alınamadı",
            "temperature": None,
            "feels_like": None,
            "humidity": None,
            "wind": None,
            "precipitation": None,
            "source": "Güvenli mod",
        }


def _full_name(user: User) -> str:
    val = getattr(user, "full_name", None)
    if val:
        return str(val)
    return f"{getattr(user, 'ad', '') or ''} {getattr(user, 'soyad', '') or ''}".strip()


def _find_target_recipients() -> list[User]:
    """Önce .env alıcılarını, sonra kullanıcı tablosunda Mustafa Bektaş ve Gülsen kayıtlarını kullanır."""
    users: list[User] = []
    seen_emails: set[str] = set()

    extra = (os.getenv("BYS360_EXECUTIVE_SUMMARY_RECIPIENTS", "") or "").strip()
    for email in [x.strip() for x in extra.replace(";", ",").split(",") if x.strip()]:
        if "@" not in email:
            continue
        key = email.lower()
        if key in seen_emails:
            continue
        dummy = User(sicil_no=f"external-{email}", email=email, ad=email, soyad="", password_hash="-")
        dummy.id = None
        users.append(dummy)
        seen_emails.add(key)

    target_names = [("mustafa", "bektaş"), ("mustafa", "bektas"), ("gülsen", "özden"), ("gulsen", "ozden"), ("gülsen", ""), ("gulsen", "")]
    try:
        for first, last in target_names:
            query = User.query
            query = query.filter(func.lower(User.ad).like(f"%{first.lower()}%"))
            if last:
                query = query.filter(func.lower(User.soyad).like(f"%{last.lower()}%"))
            for user in query.limit(10).all():
                email = (getattr(user, "email", "") or "").strip()
                if email and email.lower() not in seen_emails:
                    users.append(user)
                    seen_emails.add(email.lower())
    except Exception:
        current_app.logger.warning("Yönetici özeti alıcıları kullanıcı tablosundan okunamadı", exc_info=True)
    return users


def build_executive_summary_context(report_type: str = "night") -> dict[str, Any]:
    report_type = report_type if report_type in REPORT_TYPES else "night"
    since = utc_now() - timedelta(hours=24)

    SupportTicket = _first_existing_model("SupportTicket")
    FeedbackSubmission = _first_existing_model("FeedbackSubmission")
    FeedbackCampaign = _first_existing_model("FeedbackCampaign")
    EvaluationAssignment = _first_existing_model("EvaluationAssignment")
    PerformanceLowScoreProcess = _first_existing_model("PerformanceLowScoreProcess")
    SurveyAssignment = _first_existing_model("SurveyAssignment")

    recent_mail = []
    try:
        recent_mail = (
            MailLog.query.filter(MailLog.mail_type == EXECUTIVE_SUMMARY_MAIL_TYPE)
            .order_by(MailLog.sent_at.desc(), MailLog.id.desc())
            .limit(12)
            .all()
        )
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V5: sessiz except loglandi: app/services/executive_summary_service.py:175")
        recent_mail = []

    metrics = {
        "active_users": _model_count(User, User.is_active.is_(True)) if hasattr(User, "is_active") else _model_count(User),
        "support_open": _safe_status_count(SupportTicket, ["open", "pending", "in_progress", "new", "acik", "bekliyor"]),
        "feedback_last_24h": _model_count(FeedbackSubmission, FeedbackSubmission.created_at >= since) if FeedbackSubmission and hasattr(FeedbackSubmission, "created_at") else 0,
        "active_feedback_campaigns": _model_count(FeedbackCampaign, FeedbackCampaign.is_active.is_(True)) if FeedbackCampaign and hasattr(FeedbackCampaign, "is_active") else 0,
        "pending_performance_tasks": _safe_status_count(EvaluationAssignment, ["pending", "assigned", "bekliyor", "taslak"]),
        "pending_low_score_approvals": _safe_status_count(PerformanceLowScoreProcess, ["president_approval_pending", "president_pending", "blocked_president_pending", "ust_onay_bekliyor"]),
        "pending_surveys": _safe_status_count(SurveyAssignment, ["pending", "assigned", "bekliyor"]),
    }
    critical = int(metrics.get("pending_low_score_approvals") or 0)
    open_work = int(metrics.get("support_open") or 0) + int(metrics.get("pending_performance_tasks") or 0) + int(metrics.get("pending_surveys") or 0)
    health = "Sağlıklı" if critical == 0 else "Dikkat Gerektiriyor"
    attention = "Kritik uyarı bulunmuyor." if critical == 0 else f"Başkan/Üst Onay bekleyen {critical} düşük performans süreci bulunuyor."
    if open_work > 0 and critical == 0:
        attention = f"Açık destek, performans veya anket kapsamında takip edilecek {open_work} işlem bulunuyor."

    return {
        "generated_at": utc_now(),
        "today_text": _today_text(),
        "weather": _weather_summary(),
        "metrics": metrics,
        "health": health,
        "attention": attention,
        "recent_mail_logs": recent_mail,
        "recipients": _find_target_recipients(),
        "report_type": report_type,
        "report_meta": REPORT_TYPES[report_type],
    }


def build_executive_summary_mail_body(context: dict[str, Any]) -> str:
    m = context.get("metrics") or {}
    w = context.get("weather") or {}
    meta = context.get("report_meta") or REPORT_TYPES["night"]
    return f"""Sayın Mustafa Bektaş,

{meta.get('opening')}

RAPOR BİLGİSİ
- Rapor Türü: {meta.get('label')}
- Planlanan Gönderim Saati: {meta.get('hour_label')}
- Rapor Tarihi: {context.get('today_text')}
- Oluşturma Saati: {_dt_text(context.get('generated_at'))}

TARİHİ ALAN HAVA DURUMU
- Durum: {w.get('status') or '-'}
- Sıcaklık: {w.get('temperature') if w.get('temperature') is not None else '-'} °C
- Hissedilen: {w.get('feels_like') if w.get('feels_like') is not None else '-'} °C
- Nem: {w.get('humidity') if w.get('humidity') is not None else '-'} %
- Rüzgâr: {w.get('wind') if w.get('wind') is not None else '-'} km/sa
- Yağış: {w.get('precipitation') if w.get('precipitation') is not None else '-'} mm

BYS360 YÖNETİCİ ÖZETİ
- Aktif kullanıcı: {m.get('active_users', 0)}
- Açık destek talebi: {m.get('support_open', 0)}
- Son 24 saat geri bildirim kaydı: {m.get('feedback_last_24h', 0)}
- Aktif geri bildirim kampanyası: {m.get('active_feedback_campaigns', 0)}
- Bekleyen performans görevi: {m.get('pending_performance_tasks', 0)}
- Bekleyen Başkan/Üst Onay: {m.get('pending_low_score_approvals', 0)}
- Bekleyen anket görevi: {m.get('pending_surveys', 0)}

YÖNETİCİ NOTU
{meta.get('manager_note')}
{context.get('attention')}

SİSTEM SAĞLIK DURUMU
- Genel Durum: {context.get('health')}
- E-posta Görevi: Bu gönderim mail log kaydına işlenmiştir.
- Güvenli Çalışma: Hava servisi veya sayaçlardan biri geçici erişilemezse rapor güvenli modda tamamlanır.

Bu e-posta otomatik oluşturulmuştur.

BYS360 Bütünleşik Yönetim Sistemi
Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı
© 2026 Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı. Her hakkı saklıdır.
"""


def send_executive_summary_mail(*, report_type: str = "night", actor_user_id: int | None = None) -> dict[str, Any]:
    context = build_executive_summary_context(report_type=report_type)
    recipients = context.get("recipients") or []
    meta = context.get("report_meta") or REPORT_TYPES["night"]
    subject = f"{meta.get('subject_prefix')} | {context.get('today_text')}"
    body = build_executive_summary_mail_body(context)
    results = []
    success = failed = 0

    if not recipients:
        msg = "Mustafa Bektaş/Gülsen için e-posta bulunamadı. BYS360_EXECUTIVE_SUMMARY_RECIPIENTS ayarıyla alıcı ekleyin."
        create_mail_log(mail_type=EXECUTIVE_SUMMARY_MAIL_TYPE, recipient_email="alici-tanimli-degil", subject=subject, body=body, sent_by_id=actor_user_id, is_success=False, error_message=msg)
        db.session.commit()
        return {"ok": False, "message": msg, "success_count": 0, "failed_count": 1, "results": [], "report_type": report_type}

    for user in recipients:
        email = (getattr(user, "email", "") or "").strip()
        if not email:
            continue
        ok, message = send_email(email, subject, body)
        create_mail_log(
            mail_type=EXECUTIVE_SUMMARY_MAIL_TYPE,
            recipient_email=email,
            subject=subject,
            body=body,
            user_id=getattr(user, "id", None),
            sent_by_id=actor_user_id,
            is_success=ok,
            error_message=None if ok else message,
        )
        results.append({"email": email, "name": _full_name(user), "ok": ok, "message": message})
        success += 1 if ok else 0
        failed += 0 if ok else 1
    db.session.commit()
    return {"ok": failed == 0, "message": "Yönetici özeti gönderimi tamamlandı.", "success_count": success, "failed_count": failed, "results": results, "report_type": report_type}
