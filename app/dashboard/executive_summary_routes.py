from __future__ import annotations

# BYS360_EXECUTIVE_SUMMARY_V3_LOCAL_PRO_UI



from functools import wraps
from typing import Any

from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

try:
    from app.dashboard import bp
except Exception:
    from app.routes import main_bp as bp  # type: ignore

from app.services.executive_summary_service import build_executive_summary_context, send_executive_summary_mail

_ADMIN_ROLE_TOKENS = {
    "admin",
    "administrator",
    "sistem_yoneticisi",
    "sistem yöneticisi",
    "sistem yoneticisi",
    "system_admin",
    "super_admin",
}


def _normalize(value: Any) -> str:
    text = str(value or "").strip().lower()
    tr = str.maketrans("ğüşıöçİĞÜŞÖÇ", "gusiocigusoc")
    return text.translate(tr).replace("-", "_").replace(" ", "_")


def _safe_actor_id():
    try:
        return int(current_user.id) if current_user and current_user.is_authenticated else None
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/dashboard/executive_summary_routes.py:40")
        return None


def _is_system_admin_user() -> bool:
    """Yönetici Özeti yönetim paneli sadece sistem yöneticisi/admin kullanıcısına açıktır."""
    if not current_user or not getattr(current_user, "is_authenticated", False):
        return False
    probes = []
    for attr in ("role", "role_name", "user_role", "permission_role", "yetki", "yetki_adi", "gorev", "title", "unvan"):
        try:
            probes.append(getattr(current_user, attr, ""))
        except Exception:
            __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/dashboard/executive_summary_routes.py:52")
            pass
    try:
        roles = getattr(current_user, "roles", None)
        if roles:
            for r in roles:
                probes.append(getattr(r, "name", r))
                probes.append(getattr(r, "code", ""))
        role = getattr(current_user, "role", None)
        if role is not None:
            probes.append(getattr(role, "name", role))
            probes.append(getattr(role, "code", ""))
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/dashboard/executive_summary_routes.py:64")
        pass
    for p in probes:
        normalized = _normalize(p)
        if normalized in {_normalize(x) for x in _ADMIN_ROLE_TOKENS}:
            return True
        if "admin" in normalized or "sistem_yoneticisi" in normalized or "sistem_yonetici" in normalized:
            return True
    return False


def system_admin_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not _is_system_admin_user():
            flash("Bu sayfaya erişim yetkiniz bulunmamaktadır.", "warning")
            try:
                return redirect(url_for("main.dashboard"))
            except Exception:
                __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/dashboard/executive_summary_routes.py:82")
                return redirect("/")
        return view(*args, **kwargs)
    return wrapper


def _v3_enrich_context(context: dict[str, Any]) -> dict[str, Any]:
    metrics = context.get("metrics") or {}
    recent_mail_logs = context.get("recent_mail_logs") or []
    recipients = context.get("recipients") or []
    success_logs = [x for x in recent_mail_logs if getattr(x, "is_success", False)]
    fail_logs = [x for x in recent_mail_logs if not getattr(x, "is_success", False)]
    open_work = int(metrics.get("support_open") or 0) + int(metrics.get("pending_performance_tasks") or 0) + int(metrics.get("pending_surveys") or 0)
    context.update({
        "v3_panel_title": "Yönetici Özeti Merkezi",
        "v3_panel_subtitle": "Otomatik e-postalar, mail logları, zamanlanmış işler, test gönderimi ve günlük personel bilgilendirme yönetimi tek ekranda toplanır.",
        "v3_open_work": open_work,
        "v3_success_log_count": len(success_logs),
        "v3_fail_log_count": len(fail_logs),
        "v3_recipient_count": len(recipients),
        "v3_admin_only": True,
        "v3_schedules": [
            {"name": "Gece Yönetici Özeti", "time": "00:01", "status": "Planlı", "desc": "Gün kapanışı, sistem sağlığı ve kritik süreç özeti."},
            {"name": "Sabah Yönetici Özeti", "time": "08:30", "status": "Planlı", "desc": "Yeni gün, bekleyen işler, hava durumu ve operasyon özeti."},
            {"name": "Günlük Personel Bilgilendirme", "time": "08:15", "status": "Seçili personele", "desc": "Güncel hava durumu, ertesi gün tahmini ve kıyafet önerisi."},
        ],
        "v3_anchor_cards": [
            {"anchor": "otomatik-epostalar", "title": "Otomatik E-postalar", "desc": "Sabah, gece ve personel bilgilendirme gönderimlerini yönet."},
            {"anchor": "mail-loglari", "title": "Mail Logları", "desc": "Başarılı ve hatalı gönderimleri denetle."},
            {"anchor": "zamanlanmis-isler", "title": "Zamanlanmış İşler", "desc": "Planlı görev saatlerini ve kapsamlarını izle."},
            {"anchor": "test-gonderimi", "title": "Test Gönderimi", "desc": "Canlıya almadan önce mail üretimini dene."},
        ],
    })
    return context


@bp.route('/dashboard/yonetici-ozeti', methods=['GET'])
@login_required
@system_admin_required
def executive_summary_dashboard():
    context = build_executive_summary_context(report_type='morning')
    context = _v3_enrich_context(context)
    return render_template('dashboard/executive_summary.html', **context)


@bp.route('/dashboard/yonetici-ozeti/send-test', methods=['POST'])
@login_required
@system_admin_required
def executive_summary_send_mail():
    report_type = (request.form.get('report_type') or 'morning').strip()
    if report_type not in ('night', 'morning'):
        report_type = 'morning'
    result = send_executive_summary_mail(report_type=report_type, actor_user_id=_safe_actor_id())
    category = 'success' if result.get('ok') else 'warning'
    flash(f"Yönetici özeti gönderildi. Başarılı: {result.get('success_count',0)} / Hatalı: {result.get('failed_count',0)}", category)
    return redirect(url_for('main.executive_summary_dashboard') + '#test-gonderimi')

# BYS360_DAILY_MAIL_TASKS_V1_3_1_ROUTE START
@bp.route("/executive-summary/daily-weather-mail", methods=["GET", "POST"])
@bp.route("/yonetici-ozeti/gunluk-hava-maili", methods=["GET", "POST"])
def executive_summary_daily_weather_mail_tasks_v1_3_1():
    """Yönetici Özeti - Günlük mail görevleri yönetim ekranı."""
    return render_template("executive_summary/daily_weather_mail_tasks.html")
# BYS360_DAILY_MAIL_TASKS_V1_3_1_ROUTE END

