
"""BYS360 Asistan canlı özet ve güvenli yönlendirme servisi.

Bu servis yalnızca oturum açmış kullanıcının yetkili olduğu alanlar için sayı ve
kısa durum üretir. İçerik, puan, değerlendirme açıklaması, anket cevabı veya
mesaj metni döndürmez. Hata durumunda uygulamayı düşürmez; ilgili kartı
"kontrol edilemedi" olarak işaretler.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, inspect, or_, text
from sqlalchemy.exc import SQLAlchemyError


@dataclass(frozen=True)
class AssistantSummaryCard:
    key: str
    label: str
    count: int | None
    hint: str
    url: str
    icon: str = "circle-info"
    status: str = "ok"


def _safe_count(fn) -> tuple[int | None, str]:
    try:
        value = fn()
        return int(value or 0), "ok"
    except (SQLAlchemyError, AttributeError, RuntimeError, ValueError, TypeError):
        return None, "unavailable"


def _card(key: str, label: str, count: int | None, hint: str, url: str, icon: str, status: str) -> AssistantSummaryCard:
    return AssistantSummaryCard(key=key, label=label, count=count, hint=hint, url=url, icon=icon, status=status)


def _user_id(user: Any) -> int | None:
    try:
        return int(getattr(user, "id", None) or 0) or None
    except (TypeError, ValueError):
        return None


def _user_text_values(user: Any) -> dict[str, str]:
    return {
        "id": str(getattr(user, "id", "") or "").strip(),
        "sicil_no": str(getattr(user, "sicil_no", "") or "").strip(),
        "email": str(getattr(user, "email", "") or "").strip(),
        "role": str(getattr(user, "role", "") or "").strip(),
        "birim": str(getattr(user, "birim", "") or "").strip(),
        "ust_birim": str(getattr(user, "ust_birim", "") or "").strip(),
    }

def _normalize(value: Any) -> str:
    raw = str(value or "").strip().lower()
    tr_map = str.maketrans("çğıöşüâîûİ", "cgiosuaiui")
    return raw.translate(tr_map).replace(" ", "_").replace("-", "_")


def _role_context(user: Any) -> str:
    parts = []
    for attr in ("role", "role_name", "user_type", "unvan", "title", "position", "gorev"):
        value = getattr(user, attr, None)
        if value:
            parts.append(_normalize(value))
    return "_".join(parts)


def _is_privileged_user(user: Any) -> bool:
    if bool(getattr(user, "is_admin", False)) or bool(getattr(user, "is_superuser", False)):
        return True
    ctx = _role_context(user)
    markers = (
        "admin", "sistem", "super", "baskan", "baskan_yardimcisi",
        "grup_baskani", "koordinator", "mali_musavir", "ik",
        "insan_kaynaklari", "personel_yonetimi", "performans_yetkilisi",
        "birim_sorumlusu", "personel_ve_destek", "personel_destek",
    )
    return any(marker in ctx for marker in markers)


def _is_president_like_user(user: Any) -> bool:
    if bool(getattr(user, "is_admin", False)) or bool(getattr(user, "is_superuser", False)):
        return True
    ctx = _role_context(user)
    return any(marker in ctx for marker in ("baskan", "ust_yonetim", "super", "sistem"))


def _is_personnel_support_publish_user(user: Any) -> bool:
    if bool(getattr(user, "is_admin", False)) or bool(getattr(user, "is_superuser", False)):
        return True
    ctx = _role_context(user)
    return ("personel" in ctx and ("destek" in ctx or "idari" in ctx) and "baskan" in ctx)


def _table_exists(db: Any, table_name: str) -> bool:
    try:
        return bool(inspect(db.engine).has_table(table_name))
    except Exception:
        __import__("logging").getLogger(__name__).exception("BYS360 SAFE V4: sessiz except loglandi: app/services/assistant_live_summary_service.py:107")
        return False

def build_assistant_live_summary(user: Any) -> dict[str, Any]:
    """Return safe dashboard-style summary for current user.

    The return value is JSON-ready and intentionally count-only.
    """
    uid = _user_id(user)
    values = _user_text_values(user)
    if not uid:
        return {
            "ok": False,
            "mode": "managed-summary",
            "message": "Oturum bilgisi doğrulanamadı.",
            "cards": [],
        }

    from app.models import (  # imported lazily so startup remains tolerant
        EvaluationAssignment,
        MessageThread,
        MessageThreadParticipant,
        Notification,
        PersonnelCategory,
        PerformanceArchivedResult,
        PerformanceLowScoreProcess,
        PerformancePresidentApproval,
        PerformanceProcessFlow,
        PerformanceProcessNotification,
        SupportTicket,
        Survey,
        SurveyAssignment,
        SurveyResponse,
    )
    from app.models import db

    privileged = _is_privileged_user(user)
    president_like = _is_president_like_user(user)
    personnel_support_publish = _is_personnel_support_publish_user(user)

    pending_assignment_count, pending_assignment_status = _safe_count(
        lambda: EvaluationAssignment.query.filter(
            EvaluationAssignment.evaluator_id == uid,
            EvaluationAssignment.completed_at.is_(None),
            ~func.lower(EvaluationAssignment.status).in_(("tamamlandi", "tamamlandı", "completed", "done", "closed")),
        ).count()
    )

    unread_notification_count, unread_notification_status = _safe_count(
        lambda: Notification.query.filter(
            Notification.user_id == uid,
            Notification.is_read.is_(False),
        ).count()
    )

    unread_thread_count, unread_thread_status = _safe_count(
        lambda: db.session.query(MessageThreadParticipant)
        .join(MessageThread, MessageThreadParticipant.thread_id == MessageThread.id)
        .filter(
            MessageThreadParticipant.user_id == uid,
            MessageThreadParticipant.left_at.is_(None),
            MessageThreadParticipant.is_archived.is_(False),
            MessageThread.is_active.is_(True),
            MessageThread.last_message_at.isnot(None),
            or_(
                MessageThreadParticipant.last_read_at.is_(None),
                MessageThread.last_message_at > MessageThreadParticipant.last_read_at,
            ),
        )
        .count()
    )

    open_ticket_count, open_ticket_status = _safe_count(
        lambda: SupportTicket.query.filter(
            SupportTicket.created_by_user_id == uid,
            ~func.lower(SupportTicket.status).in_(("closed", "resolved", "rejected", "kapatildi", "kapatıldı", "cozuldu", "çözüldü")),
        ).count()
    )

    def _survey_count() -> int:
        target_values = [v for v in (values["id"], values["sicil_no"], values["email"], values["role"], values["birim"], values["ust_birim"]) if v]
        assignment_filter = or_(
            func.lower(SurveyAssignment.target_type) == "all",
            and_(func.lower(SurveyAssignment.target_type) == "user", SurveyAssignment.target_value.in_(target_values)),
            and_(func.lower(SurveyAssignment.target_type) == "role", SurveyAssignment.target_value.in_(target_values)),
            and_(func.lower(SurveyAssignment.target_type) == "unit", SurveyAssignment.target_value.in_(target_values)),
            and_(func.lower(SurveyAssignment.target_type) == "birim", SurveyAssignment.target_value.in_(target_values)),
        )
        completed = db.session.query(SurveyResponse.survey_id).filter(
            SurveyResponse.user_id == uid,
            SurveyResponse.is_completed.is_(True),
        )
        now = datetime.utcnow()
        return db.session.query(func.count(func.distinct(SurveyAssignment.survey_id)))\
            .join(Survey, SurveyAssignment.survey_id == Survey.id)\
            .filter(assignment_filter)\
            .filter(~SurveyAssignment.survey_id.in_(completed))\
            .filter(func.lower(Survey.status).in_(("active", "published", "open", "aktif", "yayinlandi", "yayinda", "yayında")))\
            .filter(or_(Survey.start_at.is_(None), Survey.start_at <= now))\
            .filter(or_(Survey.end_at.is_(None), Survey.end_at >= now))\
            .scalar() or 0

    survey_count, survey_status = _safe_count(_survey_count)

    pending_president_count, pending_president_status = _safe_count(
        lambda: PerformancePresidentApproval.query.filter(
            func.lower(PerformancePresidentApproval.status).in_(("pending", "president_pending", "approval_pending", "bekliyor"))
        ).count()
    ) if president_like else (None, "hidden")

    pending_low_score_count, pending_low_score_status = _safe_count(
        lambda: PerformanceLowScoreProcess.query.filter(
            PerformanceLowScoreProcess.president_approved_at.is_(None),
            PerformanceLowScoreProcess.president_rejected_at.is_(None),
            ~func.lower(PerformanceLowScoreProcess.status).in_(("approved", "rejected", "closed", "published", "tamamlandi", "tamamlandı")),
        ).count()
    ) if president_like else (None, "hidden")

    def _personnel_support_publish_count() -> int:
        table_name = "performance_personnel_support_publish_approvals"
        if not _table_exists(db, table_name):
            raise RuntimeError("publish approval table unavailable")
        return db.session.execute(
            text(f"SELECT COUNT(*) FROM {table_name} WHERE lower(status) IN ('pending', 'bekliyor', 'ready_for_approval')")
        ).scalar() or 0

    pending_support_publish_count, pending_support_publish_status = _safe_count(_personnel_support_publish_count) if personnel_support_publish else (None, "hidden")

    own_archive_count, own_archive_status = _safe_count(
        lambda: PerformanceArchivedResult.query.filter(PerformanceArchivedResult.employee_id == uid).count()
    )

    active_flow_count, active_flow_status = _safe_count(
        lambda: PerformanceProcessFlow.query.filter(
            PerformanceProcessFlow.is_finalized.is_(False),
            ~func.lower(PerformanceProcessFlow.current_status).in_(("completed", "closed", "published", "tamamlandi", "tamamlandı")),
        ).count()
    ) if privileged else (None, "hidden")

    process_notification_count, process_notification_status = _safe_count(
        lambda: PerformanceProcessNotification.query.filter(
            PerformanceProcessNotification.recipient_id == uid,
            func.lower(PerformanceProcessNotification.delivery_status).in_(("pending", "sent", "delivered")),
            PerformanceProcessNotification.read_at.is_(None),
        ).count()
    )

    category_count, category_status = _safe_count(
        lambda: PersonnelCategory.query.filter(PersonnelCategory.is_active.is_(True)).count()
    ) if privileged else (None, "hidden")

    cards = [
        _card("performance", "Bekleyen performans görevi", pending_assignment_count, "Tamamlanmamış değerlendirme görevleri", "/performance/tasks", "clipboard-check", pending_assignment_status),
        _card("notifications", "Okunmamış bildirim", unread_notification_count, "Sistem içi okunmamış bildirimler", "/notifications", "bell", unread_notification_status),
        _card("messages", "Okunmamış sohbet", unread_thread_count, "Yeni mesaj içeren konuşmalar", "/messages", "envelope", unread_thread_status),
        _card("surveys", "Yanıt bekleyen anket", survey_count, "Size atanmış ve tamamlanmamış anketler", "/surveys", "square-poll-vertical", survey_status),
        _card("support", "Açık destek talebi", open_ticket_count, "Tarafınızdan açılmış kapanmamış talepler", "/support/my-tickets", "life-ring", open_ticket_status),
        _card("process_notification", "Performans süreç bildirimi", process_notification_count, "Size yönelen süreç takip bildirimleri", "/notifications", "timeline", process_notification_status),
        _card("archive", "Geçmiş karne/puan kaydı", own_archive_count, "Kendi geçmiş performans arşiv kayıtlarınız", "/performance/archive", "box-archive", own_archive_status),
    ]

    if president_like:
        cards.extend([
            _card("president_approval", "Başkan/Üst Onay bekleyen kayıt", pending_president_count, "70 altı onay sürecindeki gerçek kayıtlar", "/performance/president-approvals", "stamp", pending_president_status),
            _card("low_score_process", "Düşük performans süreç kaydı", pending_low_score_count, "Başkan/Üst Onay bekleyen düşük performans süreçleri", "/performance/president-approvals", "triangle-exclamation", pending_low_score_status),
        ])

    if personnel_support_publish:
        cards.append(
            _card("personnel_support_publish", "Yayın ön onayı bekleyen karne", pending_support_publish_count, "Personel ve Destek Hizmetleri Grup Başkanı kontrolündeki kayıtlar", "/performance/personnel-support-publish-approvals", "file-signature", pending_support_publish_status)
        )

    if privileged:
        cards.extend([
            _card("process_tracking", "Açık performans süreç akışı", active_flow_count, "Finalleşmemiş değerlendirme süreçleri", "/performance/process-tracking", "timeline", active_flow_status),
            _card("personnel_category", "Aktif personel kategorisi", category_count, "Kategori/grup bazlı dönem ve rapor altyapısı", "/performance/reports", "users-viewfinder", category_status),
        ])

    return {
        "ok": True,
        "mode": "managed-summary",
        "version": "v9",
        "privacy": "Sadece sayı/özet döner; puan, kanaat, mesaj metni, anket cevabı veya kişisel açıklama göstermez.",
        "cards": [card.__dict__ for card in cards],
    }


def build_summary_text(summary: dict[str, Any]) -> str:
    """Turn summary cards into a short assistant answer."""
    if not summary.get("ok"):
        return "Oturum özeti şu anda hazırlanamadı. Lütfen sayfayı yenileyip tekrar deneyin."
    lines = ["Yetkiniz dahilindeki güvenli özet aşağıdadır. İçerik veya hassas veri göstermiyorum; yalnızca sayı bilgisi paylaşıyorum:"]
    for card in summary.get("cards", []):
        count = card.get("count")
        label = card.get("label") or "Kayıt"
        status = card.get("status")
        if status != "ok" or count is None:
            lines.append(f"• {label}: kontrol edilemedi")
        else:
            lines.append(f"• {label}: {count}")
    lines.append("Detay için ilgili ekrana geçebilirsiniz; asistan idari karar veya performans yorumu üretmez.")
    return "\n".join(lines)


def _safe_action(label: str, url: str, hint: str, icon: str, priority: str = "normal") -> dict[str, str]:
    clean_url = str(url or "")
    if not clean_url.startswith("/") or clean_url.startswith("//"):
        clean_url = "/support"
    return {
        "label": str(label),
        "url": clean_url,
        "hint": str(hint),
        "icon": str(icon or "arrow-right"),
        "priority": str(priority or "normal"),
    }


def build_assistant_action_plan(summary: dict[str, Any]) -> dict[str, Any]:
    """Build safe next-step cards from count-only summary.

    This does not inspect content. It only turns safe counts into internal links.
    """
    if not summary.get("ok"):
        return {
            "ok": False,
            "mode": "managed-safe-actions",
            "version": "v9",
            "title": "Yönlendirme hazırlanamadı",
            "message": "Oturum özeti alınamadığı için öncelikli yönlendirme üretilemedi.",
            "actions": [_safe_action("Yardım Merkezi", "/support", "Destek ve kullanım rehberleri", "circle-question")],
        }

    cards = list(summary.get("cards") or [])
    active_cards = [card for card in cards if card.get("status") == "ok" and isinstance(card.get("count"), int) and card.get("count", 0) > 0]
    unavailable_cards = [card for card in cards if card.get("status") != "ok"]

    actions: list[dict[str, str]] = []
    for card in sorted(active_cards, key=lambda item: int(item.get("count") or 0), reverse=True):
        count = int(card.get("count") or 0)
        label = f"{card.get('label', 'Kayıt')} ({count})"
        hint = "Öncelikli kontrol önerilir; detay ilgili ekranda görüntülenir."
        actions.append(_safe_action(label, str(card.get("url") or "/support"), hint, str(card.get("icon") or "arrow-right"), "high"))

    if not actions:
        actions.extend([
            _safe_action("Bildirimler", "/notifications", "Yeni sistem bildirimleri için kontrol edilebilir", "bell"),
            _safe_action("Yardım Merkezi", "/support", "Kullanım rehberi ve destek talebi alanı", "circle-question"),
            _safe_action("Ana Sayfa", "/home", "Genel durum ekranına dön", "house"),
        ])

    if unavailable_cards:
        actions.append(_safe_action("Destek talebi aç", "/support/new", "Kontrol edilemeyen özet alanları için destek alınabilir", "life-ring", "info"))

    return {
        "ok": True,
        "mode": "managed-safe-actions",
        "version": "v9",
        "title": "Öncelikli yönlendirmeler",
        "message": "Bu liste yalnızca güvenli sayı/özet kartlarına göre hazırlanır; içerik veya hassas veri göstermez.",
        "actions": actions[:6],
    }


def build_action_plan_text(action_plan: dict[str, Any]) -> str:
    """Turn safe action plan into a short assistant answer."""
    if not action_plan.get("ok"):
        return action_plan.get("message") or "Öncelikli yönlendirme şu anda hazırlanamadı."
    lines = ["Güvenli yönlendirme kartlarını hazırladım. İçerik veya hassas veri göstermeden yalnızca ilgili ekrana yönlendiriyorum:"]
    for action in action_plan.get("actions", [])[:5]:
        lines.append(f"• {action.get('label')}: {action.get('hint')}")
    lines.append("Detayları yalnızca ilgili ekranda, kendi yetkiniz kapsamında görebilirsiniz.")
    return "\n".join(lines)
