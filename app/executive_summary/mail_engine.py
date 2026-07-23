from __future__ import annotations

import logging
import os
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from .service import build_executive_summary_payload, get_default_recipients

logger = logging.getLogger(__name__)


def send_executive_summary_email(report_type: str = "morning", manual: bool = False) -> dict:
    payload = build_executive_summary_payload(report_type=report_type)
    recipients = get_default_recipients()
    if not recipients:
        return _log_result(False, report_type, [], "BYS360_EXECUTIVE_SUMMARY_RECIPIENTS tanımlı değil.")

    subject = _subject(report_type, payload)
    html = render_email_html(payload, report_type=report_type)
    text = render_email_text(payload, report_type=report_type)

    host = os.getenv("MAIL_SERVER") or os.getenv("SMTP_HOST")
    port = int(os.getenv("MAIL_PORT") or os.getenv("SMTP_PORT") or "587")
    username = os.getenv("MAIL_USERNAME") or os.getenv("SMTP_USERNAME")
    password = os.getenv("MAIL_PASSWORD") or os.getenv("SMTP_PASSWORD")
    sender = os.getenv("MAIL_DEFAULT_SENDER") or username
    use_tls = (os.getenv("MAIL_USE_TLS", "true").lower() in ("1", "true", "yes", "on"))
    use_ssl = (os.getenv("MAIL_USE_SSL", "false").lower() in ("1", "true", "yes", "on"))

    if not host or not sender:
        return _log_result(False, report_type, recipients, "SMTP host veya gönderici tanımlı değil.")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        if use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=context, timeout=30) as smtp:
                if username and password:
                    smtp.login(username, password)
                smtp.sendmail(sender, recipients, msg.as_string())
        else:
            with smtplib.SMTP(host, port, timeout=30) as smtp:
                smtp.ehlo()
                if use_tls:
                    smtp.starttls(context=ssl.create_default_context())
                    smtp.ehlo()
                if username and password:
                    smtp.login(username, password)
                smtp.sendmail(sender, recipients, msg.as_string())
        return _log_result(True, report_type, recipients, "Gönderim başarılı.")
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/executive_summary/mail_engine.py | line=62")
        return _log_result(False, report_type, recipients, f"Gönderim hatası: {exc}")


def _subject(report_type: str, payload: dict) -> str:
    date = payload.get("generated_date")
    if report_type == "night":
        return f"BYS360 Gece Sistem Kontrolü ve Tarihi Alan Durum Raporu | {date}"
    if report_type == "morning":
        return f"Günaydın | BYS360 Yeni Gün Yönetici Özeti | {date}"
    return f"BYS360 Yönetici Özeti | {date}"


def render_email_text(payload: dict, report_type: str) -> str:
    w = payload["weather"]
    m = payload["metrics"]
    return f"""Sayın Yetkili,

{payload['executive_note']}

Rapor Tarihi: {payload['generated_at']}
Konum: {w['location']}
Hava Durumu: {w['status']}
Sıcaklık: {w['temperature']}
Nem: {w['humidity']}
Rüzgâr: {w['wind']}
Yağış: {w['rain']}

BYS360 Yönetici Özeti:
- Bekleyen geri bildirim: {m['pending_feedback']}
- Açık destek talebi: {m['open_support']}
- Bekleyen performans görevi: {m['pending_performance_tasks']}
- Bekleyen onay süreci: {m['pending_approvals']}
- Aktif anket: {m['active_surveys']}

Bu e-posta BYS360 tarafından otomatik oluşturulmuştur.
Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı
"""


def render_email_html(payload: dict, report_type: str) -> str:
    w = payload["weather"]
    m = payload["metrics"]
    title = "BYS360 Gece Sistem Kontrolü" if report_type == "night" else "Günaydın | BYS360 Yeni Gün Yönetici Özeti"
    return f"""<!doctype html>
<html lang="tr">
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f6f3f1;font-family:Arial,Helvetica,sans-serif;color:#242424;">
  <div style="max-width:760px;margin:0 auto;background:#ffffff;border:1px solid #eadfda;">
    <div style="background:#8B0000;color:#fff;padding:22px 28px;">
      <div style="font-size:20px;font-weight:700;">{title}</div>
      <div style="font-size:13px;opacity:.9;margin-top:6px;">{payload['generated_at']} • Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı</div>
    </div>
    <div style="padding:26px 28px;">
      <p style="font-size:15px;line-height:1.55;">Sayın Yetkili,</p>
      <p style="font-size:15px;line-height:1.55;">{payload['executive_note']}</p>
      <h3 style="color:#8B0000;margin-top:24px;">Tarihi Alan Hava Durumu</h3>
      <table width="100%" cellpadding="8" cellspacing="0" style="border-collapse:collapse;background:#fbf8f6;">
        <tr><td><b>Konum</b></td><td>{w['location']}</td></tr>
        <tr><td><b>Durum</b></td><td>{w['status']}</td></tr>
        <tr><td><b>Sıcaklık</b></td><td>{w['temperature']}</td></tr>
        <tr><td><b>Nem</b></td><td>{w['humidity']}</td></tr>
        <tr><td><b>Rüzgâr</b></td><td>{w['wind']}</td></tr>
        <tr><td><b>Yağış</b></td><td>{w['rain']}</td></tr>
      </table>
      <h3 style="color:#8B0000;margin-top:24px;">BYS360 Yönetici Özeti</h3>
      <table width="100%" cellpadding="8" cellspacing="0" style="border-collapse:collapse;">
        <tr><td>Bekleyen geri bildirim</td><td><b>{m['pending_feedback']}</b></td></tr>
        <tr><td>Açık destek talebi</td><td><b>{m['open_support']}</b></td></tr>
        <tr><td>Bekleyen performans görevi</td><td><b>{m['pending_performance_tasks']}</b></td></tr>
        <tr><td>Bekleyen onay süreci</td><td><b>{m['pending_approvals']}</b></td></tr>
        <tr><td>Aktif anket</td><td><b>{m['active_surveys']}</b></td></tr>
      </table>
      <div style="margin-top:24px;padding:14px 16px;background:#f6f3f1;border-left:4px solid #8B0000;">
        Bu e-posta BYS360 tarafından otomatik oluşturulmuştur.
      </div>
    </div>
    <div style="padding:16px 28px;background:#f6f3f1;font-size:12px;color:#666;">© 2026 Çanakkale Savaşları Gelibolu Tarihi Alan Başkanlığı. Her hakkı saklıdır.</div>
  </div>
</body>
</html>"""


def _log_result(ok: bool, report_type: str, recipients: list[str], message: str) -> dict:
    result = {
        "ok": ok,
        "report_type": report_type,
        "recipients": recipients,
        "message": message,
        "sent_at": datetime.now().isoformat(timespec="seconds"),
    }
    try:
        log_dir = Path(os.getenv("BYS360_LOG_DIR", "logs"))
        log_dir.mkdir(parents=True, exist_ok=True)
        with (log_dir / f"executive_summary_{report_type}.log").open("a", encoding="utf-8") as fh:
            fh.write(f"{result['sent_at']} | ok={ok} | recipients={';'.join(recipients)} | {message}\n")
    except Exception:
        logger.exception("BYS360 V6C guarded exception | file=app/executive_summary/mail_engine.py | line=158")
        pass
    return result
