from __future__ import annotations



from flask import abort, flash, redirect, render_template, request
from flask_login import current_user, login_required
from jinja2 import TemplateNotFound

from app.route_registry import main_bp
import logging
logger = logging.getLogger(__name__)

_SERVICE_ERROR = ""
try:
    from app.services.daily_weather_mail import (  # type: ignore
        DAILY_WEATHER_MENU_KEY,
        current_config,
        ensure_daily_weather_defaults,
        get_recent_logs,
        get_recipient_users,
        list_active_users_for_selection,
        preview_daily_weather_mail,
        run_daily_weather_mail,
        save_config,
    )
except Exception as exc:  # Service yoksa sayfa yine açılsın, sistem düşmesin.
    logger.exception("BYS360 V6C guarded exception | file=app/communication/daily_weather_mail_routes.py | line=24")
    _SERVICE_ERROR = str(exc)
    DAILY_WEATHER_MENU_KEY = "executive_summary_daily_weather_mail"

    def ensure_daily_weather_defaults(actor_user_id=None):
        return None

    def current_config():
        return {
            "enabled": False,
            "run_hour": 9,
            "run_minute": 0,
            "city": "Çanakkale",
            "latitude": "40.1553",
            "longitude": "26.4142",
            "include_tomorrow": True,
            "include_clothing": True,
            "include_motivation": True,
            "recipient_user_ids": [],
        }

    def get_recent_logs(limit=25):
        return []

    def get_recipient_users():
        return []

    def list_active_users_for_selection():
        return []

    def preview_daily_weather_mail(user):
        return {
            "subject": "Günlük personel bilgilendirme maili",
            "body": "Mail servisi henüz local projede tam bağlı değil. Route aktif; servis bağlantısı kontrol edilmeli.",
        }

    def run_daily_weather_mail(actor_user_id=None, force=False, dry_run=False):
        return {
            "ok": False,
            "skipped": True,
            "reason": "Günlük hava maili servisi local projede yüklenemedi: " + _SERVICE_ERROR,
            "sent": 0,
            "failed": 0,
            "recipient_count": 0,
        }

    def save_config(payload, actor_user_id=None):
        raise RuntimeError("Günlük hava maili servisi local projede yüklenemedi: " + _SERVICE_ERROR)


_ALLOWED_ROLES = {
    "admin",
    "super_admin",
    "system_admin",
    "sistem_yoneticisi",
}


def _role_name() -> str:
    return str(getattr(current_user, "role", "") or "").strip().lower()


def _can_manage_daily_weather_mail() -> bool:
    if not getattr(current_user, "is_authenticated", False):
        return False
    return _role_name() in _ALLOWED_ROLES


def _require_manage_permission() -> None:
    if not _can_manage_daily_weather_mail():
        abort(403)


def _fallback_html(config, logs, selected_users, preview_error=""):
    service_note = _SERVICE_ERROR or "Servis bağlı."
    return f"""
    <main style='font-family:Arial,sans-serif;max-width:980px;margin:32px auto;padding:24px;border:1px solid #eee;border-radius:18px'>
      <h1 style='color:#8B0000;margin-top:0'>Günlük Personel Bilgilendirme Maili</h1>
      <p>Bu sayfa local ortamda route olarak aktif hale getirildi.</p>
      <p><strong>Durum:</strong> {service_note}</p>
      <p><strong>Şehir:</strong> {config.get('city','Çanakkale')}</p>
      <p><strong>Planlı saat:</strong> {config.get('run_hour',9)}:{str(config.get('run_minute',0)).zfill(2)}</p>
      <p><strong>Seçili alıcı:</strong> {len(selected_users or [])}</p>
      <p><strong>Son log:</strong> {len(logs or [])} kayıt</p>
      <p style='color:#8B0000'>{preview_error}</p>
      <p>Template veya servis bağlantısı tamamlandığında bu ekran kurumsal ayar formuyla açılır.</p>
    </main>
    """


@main_bp.get("/executive-summary/daily-weather-mail")
@main_bp.get("/yonetici-ozeti/gunluk-hava-maili")
@main_bp.get("/communication/daily-weather-mail")
@main_bp.get("/iletisim/gunluk-hava-maili")
@login_required
def daily_weather_mail_settings():
    _require_manage_permission()
    ensure_daily_weather_defaults(actor_user_id=getattr(current_user, "id", None))
    config = current_config()
    selected_ids = set(config.get("recipient_user_ids") or [])
    users = list_active_users_for_selection()
    selected_users = get_recipient_users()
    logs = get_recent_logs(limit=25)
    preview = None
    preview_error = _SERVICE_ERROR
    if request.args.get("preview") == "1":
        try:
            preview = preview_daily_weather_mail(selected_users[0] if selected_users else current_user)
        except Exception as exc:
            logger.exception("BYS360 V6C guarded exception | file=app/communication/daily_weather_mail_routes.py | line=132")
            preview_error = str(exc)
    try:
        return render_template("executive_summary/mail_center/overview.html",
            config=config,
            users=users,
            selected_ids=selected_ids,
            selected_users=selected_users,
            logs=logs,
            preview=preview,
            preview_error=preview_error,
            menu_key=DAILY_WEATHER_MENU_KEY,
        )
    except TemplateNotFound:
        return _fallback_html(config, logs, selected_users, preview_error)


@main_bp.post("/executive-summary/daily-weather-mail/settings")
@main_bp.post("/yonetici-ozeti/gunluk-hava-maili/ayarlar")
@main_bp.post("/communication/daily-weather-mail/settings")
@main_bp.post("/iletisim/gunluk-hava-maili/ayarlar")
@login_required
def daily_weather_mail_save_settings():
    _require_manage_permission()
    payload = {
        "enabled": request.form.get("enabled"),
        "run_hour": request.form.get("run_hour"),
        "run_minute": request.form.get("run_minute"),
        "city": request.form.get("city"),
        "latitude": request.form.get("latitude"),
        "longitude": request.form.get("longitude"),
        "include_tomorrow": request.form.get("include_tomorrow"),
        "include_clothing": request.form.get("include_clothing"),
        "include_motivation": request.form.get("include_motivation"),
        "recipient_user_ids": request.form.getlist("recipient_user_ids"),
    }
    try:
        save_config(payload, actor_user_id=getattr(current_user, "id", None))
        flash("Günlük personel bilgilendirme maili ayarları kaydedildi.", "success")
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/daily_weather_mail_routes.py | line=171")
        flash(f"Ayarlar kaydedilemedi: {exc}", "danger")
    return redirect("/executive-summary/daily-weather-mail")


@main_bp.post("/executive-summary/daily-weather-mail/send-now")
@main_bp.post("/yonetici-ozeti/gunluk-hava-maili/simdi-gonder")
@main_bp.post("/communication/daily-weather-mail/send-now")
@main_bp.post("/iletisim/gunluk-hava-maili/simdi-gonder")
@login_required
def daily_weather_mail_send_now():
    _require_manage_permission()
    try:
        result = run_daily_weather_mail(actor_user_id=getattr(current_user, "id", None), force=True, dry_run=False)
        if result.get("skipped"):
            flash(result.get("reason") or "Gönderim yapılmadı.", "warning")
        elif result.get("ok"):
            flash(f"Günlük bilgilendirme maili gönderildi. Başarılı: {result.get('sent', 0)}", "success")
        else:
            flash(f"Gönderim tamamlandı ancak hata var. Başarılı: {result.get('sent', 0)}, Hatalı: {result.get('failed', 0)}", "warning")
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/daily_weather_mail_routes.py | line=191")
        flash(f"Gönderim başlatılamadı: {exc}", "danger")
    return redirect("/executive-summary/daily-weather-mail")


@main_bp.post("/executive-summary/daily-weather-mail/dry-run")
@main_bp.post("/yonetici-ozeti/gunluk-hava-maili/kuru-calisma")
@main_bp.post("/communication/daily-weather-mail/dry-run")
@main_bp.post("/iletisim/gunluk-hava-maili/kuru-calisma")
@login_required
def daily_weather_mail_dry_run():
    _require_manage_permission()
    try:
        result = run_daily_weather_mail(actor_user_id=getattr(current_user, "id", None), force=True, dry_run=True)
        if result.get("skipped"):
            flash(result.get("reason") or "Kuru çalışma yapılmadı.", "warning")
        else:
            flash(f"Kuru çalışma tamamlandı. Alıcı sayısı: {result.get('recipient_count', 0)}. Gerçek mail gönderilmedi.", "info")
    except Exception as exc:
        logger.exception("BYS360 V6C guarded exception | file=app/communication/daily_weather_mail_routes.py | line=209")
        flash(f"Kuru çalışma başlatılamadı: {exc}", "danger")
    return redirect("/executive-summary/daily-weather-mail")



