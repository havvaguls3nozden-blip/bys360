"""Canonical CIC template rendering, persistence and quality service."""

from __future__ import annotations

from typing import Any

from app.extensions import db
from app.models import User
from app.services.cic.config_context import (
    _now,
    _weather,
    get_config,
    get_setting,
    set_setting,
)
from app.services.cic.task_contract import BASE_KEY, TASK_DEFINITIONS

__all__ = [
    "_cic_phase6_item",
    "_cic_phase6_status",
    "_cic_phase6_template_quality",
    "_dashboard_counts",
    "_render_template_text",
    "_render_template_text_base",
    "_user_name",
    "get_template",
    "save_templates",
]


def _user_name(user: User | None) -> str:
    if not user:
        return "-"
    return (
        f"{getattr(user, 'ad', '') or ''} "
        f"{getattr(user, 'soyad', '') or ''}"
    ).strip() or (
        getattr(user, "full_name_cache", None)
        or getattr(user, "email", None)
        or f"Kullanıcı #{getattr(user, 'id', '-')}"
    )


def _dashboard_counts() -> dict[str, str | int]:
    try:
        if hasattr(User, "is_active"):
            active_count = User.query.filter(User.is_active.is_(True)).count()
        else:
            active_count = User.query.count()
    except Exception:
        __import__("logging").getLogger(__name__).exception(
            "BYS360 SAFE V5: sessiz except loglandi: "
            "app/services/corporate_information_center.py:468"
        )
        active_count = "-"
    return {
        "aktif_personel_sayisi": active_count,
        "son_gonderim_durumu": get_setting(
            f"{BASE_KEY}.last_status",
            "Henüz gönderim yapılmadı",
        )
        or "Henüz gönderim yapılmadı",
        "gunun_notu": (
            "BYS360 süreçlerinin gün içinde düzenli izlenmesi önerilir."
        ),
        "yarin_yonetici_notu": (
            "Ertesi gün için bekleyen görev ve geri bildirimlerin "
            "kontrol edilmesi önerilir."
        ),
    }


def _render_template_text_base(
    text: str,
    user: User | None,
    task_key: str,
) -> str:
    cfg = get_config()
    if task_key.startswith("staff_"):
        weather = _weather()
    else:
        weather = {
            "bugun_hava": "-",
            "yarin_hava": "-",
            "kiyafet_onerisi": "-",
            "yarin_oneri": "-",
        }
    context = {
        "ad_soyad": _user_name(user),
        "email": getattr(user, "email", "") if user else "",
        "tarih": _now().strftime("%d.%m.%Y"),
        "saat": _now().strftime("%H:%M"),
        "konum": cfg["location_name"],
        "bys360_baglanti": (
            "https://bys360.canakkaletarihialan.gov.tr/"
        ),
        "geri_bildirim_baglantisi": (
            "https://bys360.canakkaletarihialan.gov.tr/feedback"
        ),
        **weather,
        **_dashboard_counts(),
    }
    rendered = text or ""
    for key, value in context.items():
        rendered = rendered.replace("{" + key + "}", str(value))
    return rendered


def _render_template_text(
    text: str,
    user: User | None,
    task_key: str,
) -> str:
    from app.services.cic.celebration_dates import _cic_v40_special_days_today
    from app.services.cic.celebration_service import _cic_v40_service_year

    rendered = _render_template_text_base(text, user, task_key)
    special_names = ", ".join(
        str(day.get("name")) for day in _cic_v40_special_days_today()
    ) or "Özel Gün"
    service_year = _cic_v40_service_year(user) if user is not None else 0
    extra = {
        "ozel_gun_adi": special_names,
        "hizmet_yili": service_year or "değerli",
        "kutlama_notu": (
            "Yaş bilgisi gösterilmeden, KVKK uyumlu kutlama metni "
            "oluşturulmuştur."
        ),
    }
    for key, value in extra.items():
        rendered = rendered.replace("{" + key + "}", str(value))
    return rendered


def get_template(task_key: str) -> dict[str, str]:
    meta = TASK_DEFINITIONS[task_key]
    subject = get_setting(
        f"{BASE_KEY}.template.{task_key}.subject",
        meta["subject"],
    )
    body = get_setting(
        f"{BASE_KEY}.template.{task_key}.body",
        meta["body"],
    )
    return {
        "subject": subject or meta["subject"],
        "body": body or meta["body"],
    }


def save_templates(
    payload: dict[str, Any],
    actor_user_id: int | None = None,
) -> None:
    for key, meta in TASK_DEFINITIONS.items():
        subject = (payload.get(f"subject_{key}") or meta["subject"]).strip()
        body = (payload.get(f"body_{key}") or meta["body"]).strip()
        set_setting(
            f"{BASE_KEY}.template.{key}.subject",
            subject,
            label=f"{meta['label']} konusu",
            actor_user_id=actor_user_id,
        )
        set_setting(
            f"{BASE_KEY}.template.{key}.body",
            body,
            label=f"{meta['label']} metni",
            value_type="text",
            actor_user_id=actor_user_id,
        )
    db.session.commit()


def _cic_phase6_status(ok: bool, warn: bool = False) -> str:
    if ok:
        return "ok"
    return "warn" if warn else "danger"


def _cic_phase6_item(
    title: str,
    ok: bool,
    detail: str,
    warn: bool = False,
) -> dict[str, Any]:
    status = _cic_phase6_status(ok, warn)
    return {
        "title": title,
        "detail": detail,
        "status": status,
        "label": (
            "Geçti"
            if status == "ok"
            else ("Kontrol" if status == "warn" else "Engel")
        ),
        "icon": (
            "fa-circle-check"
            if status == "ok"
            else (
                "fa-triangle-exclamation"
                if status == "warn"
                else "fa-circle-xmark"
            )
        ),
    }


def _cic_phase6_template_quality(
    tasks: list[dict[str, Any]],
) -> dict[str, Any]:
    empty_subject = sum(
        1 for task in tasks if not (task.get("subject") or "").strip()
    )
    short_body = sum(
        1
        for task in tasks
        if len((task.get("body") or "").strip()) < 60
    )
    technical_terms = [
        "traceback",
        "exception",
        "endpoint",
        "csrf",
        "debug",
        "workflow",
        "sync",
        "phase",
    ]
    technical = 0
    for task in tasks:
        content = (
            (task.get("subject") or "")
            + " "
            + (task.get("body") or "")
        ).lower()
        if any(term in content for term in technical_terms):
            technical += 1
    items = [
        _cic_phase6_item(
            "Konu kontrolü",
            empty_subject == 0,
            f"{empty_subject} görevde konu eksik.",
            warn=True,
        ),
        _cic_phase6_item(
            "Metin uzunluğu",
            short_body == 0,
            f"{short_body} şablon çok kısa görünüyor.",
            warn=True,
        ),
        _cic_phase6_item(
            "Teknik dil",
            technical == 0,
            f"{technical} şablonda teknik ifade riski var.",
            warn=True,
        ),
    ]
    problems = empty_subject + short_body + technical
    return {
        "status": "ok" if problems == 0 else "warn",
        "label": (
            "Şablonlar hazır"
            if problems == 0
            else "Şablonları kontrol et"
        ),
        "items": items,
        "problem_count": problems,
    }
