from __future__ import annotations

import logging
from typing import Any

from .repository import count_table, insert_agent_audit_log, table_columns, table_exists

logger = logging.getLogger(__name__)

# BYS360 DEFECT AQ: bu küme önceden "keyword in role_text" biçiminde alt
# dize eşleştirmesi için kullanılıyordu -- ör. "sistem" jetonu, ilgisiz
# "Sistem Destek Uzmanı" gibi bir unvanı da kapsıyordu. Artık her rol
# alanı AYRI AYRI normalize edilip bu kümeyle TAM eşleştiriliyor (bkz.
# has_performance_overview_permission), bu yüzden hem Türkçe hem ASCII
# yazımları burada tam değer olarak listelenir.
PRIVILEGED_ROLE_VALUES = frozenset({
    "admin",
    "sistem_yoneticisi", "sistem yöneticisi", "sistem yoneticisi",
    "başkan", "baskan",
    "üst yönetim", "ust yonetim", "ust_yonetim",
    "ik",
    "insan kaynakları", "insan kaynaklari", "insan_kaynaklari",
    "personel ve destek", "personel_ve_destek",
    "grup başkanı", "grup baskani", "grup_baskani",
    "koordinatör", "koordinator",
})

PENDING_STATUSES = "'pending', 'assigned', 'waiting', 'bekliyor', 'in_progress'"
PRESIDENT_STATUSES = "'president_pending', 'blocked_president_pending', 'Başkan Onayı Bekliyor', 'baskan_onayi_bekliyor'"
LOCKED_STATUSES = "'blocked_president_pending', 'publish_locked', 'Başkan Onayı Yayın Kilidi', 'yayin_kilidi'"


def _user_id(user: Any) -> int | None:
    try:
        return int(getattr(user, "id", None) or 0) or None
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return None


def _role_values(user: Any) -> list[str]:
    values: list[str] = []
    for attr in ("role", "role_name", "user_role", "role_key", "title", "unvan", "position"):
        value = getattr(user, attr, None)
        if value:
            values.append(str(value).strip().lower())
    roles = getattr(user, "roles", None)
    if roles:
        try:
            for role in roles:
                values.append(str(getattr(role, "name", role)).strip().lower())
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            values.append(str(roles).strip().lower())
    return values


def has_performance_overview_permission(user: Any) -> bool:
    # BYS360 DEFECT AQ: her rol/unvan alanı KENDİ TEK BAŞINA değeriyle
    # PRIVILEGED_ROLE_VALUES'a karşı TAM eşleştirilir -- birleştirilmiş tek
    # bir metin üzerinde alt dize aranmaz. "Başkanlığı Uzmanı" gibi bir
    # unvan artık "baskan" içerdiği için değil, kendisi tam olarak
    # kümedeki bir değere eşit OLMADIĞI için reddedilir.
    if any(value in PRIVILEGED_ROLE_VALUES for value in _role_values(user)):
        return True
    for attr in ("is_admin", "is_superuser", "is_system_admin", "is_president", "is_manager"):
        try:
            if bool(getattr(user, attr, False)):
                return True
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: sessiz except/pass yakalandi (app/services/ai_agent/performance_bridge.py)")
    return False


def _count_user_assignments(user_id: int | None) -> int:
    if not user_id or not table_exists("evaluation_assignments"):
        return 0
    columns = table_columns("evaluation_assignments")
    candidate_columns = [
        col for col in ("evaluator_id", "assigned_to_id", "supervisor_id", "user_id", "manager_id") if col in columns
    ]
    if not candidate_columns:
        return 0
    status_filter = f"COALESCE(status, '') IN ({PENDING_STATUSES})" if "status" in columns else "1=1"
    owner_filter = " OR ".join(f"{col} = :user_id" for col in candidate_columns)
    return count_table("evaluation_assignments", f"({owner_filter}) AND {status_filter}", {"user_id": user_id})


def _count_evaluations_by_status(status_sql: str) -> int:
    if not table_exists("performance_evaluations"):
        return 0
    columns = table_columns("performance_evaluations")
    if "status" not in columns:
        return 0
    return count_table("performance_evaluations", f"COALESCE(status, '') IN ({status_sql})")


def _count_low_scores() -> int:
    if not table_exists("performance_evaluations"):
        return 0
    columns = table_columns("performance_evaluations")
    score_col = None
    for candidate in ("final_score", "score", "total_score", "calculated_score", "final_point", "result_score"):
        if candidate in columns:
            score_col = candidate
            break
    if not score_col:
        return 0
    return count_table("performance_evaluations", f"{score_col} IS NOT NULL AND {score_col} < 70")


def _count_pending_assignments() -> int:
    if not table_exists("evaluation_assignments"):
        return 0
    columns = table_columns("evaluation_assignments")
    if "status" not in columns:
        return count_table("evaluation_assignments")
    return count_table("evaluation_assignments", f"COALESCE(status, '') IN ({PENDING_STATUSES})")


def _count_delayed_assignments() -> int:
    if not table_exists("evaluation_assignments"):
        return 0
    columns = table_columns("evaluation_assignments")
    if "due_date" in columns and "status" in columns:
        return count_table("evaluation_assignments", f"due_date < NOW() AND COALESCE(status, '') IN ({PENDING_STATUSES})")
    if "deadline" in columns and "status" in columns:
        return count_table("evaluation_assignments", f"deadline < NOW() AND COALESCE(status, '') IN ({PENDING_STATUSES})")
    return 0


def _count_active_periods() -> int:
    if not table_exists("performance_periods"):
        return 0
    columns = table_columns("performance_periods")
    if "is_active" in columns:
        return count_table("performance_periods", "COALESCE(is_active, false) = true")
    if "status" in columns:
        return count_table("performance_periods", "COALESCE(status, '') IN ('active', 'aktif', 'open')")
    return count_table("performance_periods")


def build_performance_summary_for_user(user: Any) -> dict[str, Any]:
    """AG-2 performans bağlantısı.

    Genel sayılar yalnızca üst yetki sinyali olan kullanıcıya gösterilir. Standart kullanıcıda
    sadece kendisine bağlı bekleyen görev sayısı döner. Bu fonksiyon veri değiştirmez.
    """
    user_id = _user_id(user)
    privileged = has_performance_overview_permission(user)

    summary: dict[str, Any] = {
        "ok": True,
        "scope": "genel_yetkili_ozet" if privileged else "kullanici_ozeti",
        "can_view_global_summary": privileged,
        "decision_notice": "BYS360 Asistanı performans kararı, onay, ret veya yayın işlemi yapmaz.",
        "action_notice": "Bu özet yalnızca sayı ve yönlendirme amacıyla üretilmiştir.",
        "counts": {
            "my_pending_assignments": _count_user_assignments(user_id),
        },
        "cards": [],
    }

    if privileged:
        summary["counts"].update({
            "active_periods": _count_active_periods(),
            "pending_assignments": _count_pending_assignments(),
            "delayed_assignments": _count_delayed_assignments(),
            "president_approval_waiting": _count_evaluations_by_status(PRESIDENT_STATUSES),
            "publish_locked_scorecards": _count_evaluations_by_status(LOCKED_STATUSES),
            "low_score_records": _count_low_scores(),
        })
        summary["cards"] = [
            {
                "key": "president_approval_waiting",
                "title": "Başkan/Üst Onay Bekleyenler",
                "value": summary["counts"].get("president_approval_waiting", 0),
                "route": "/performance/president-approvals",
                "description": "70 altı süreçlerde üst onay bekleyen kayıtların sayı düzeyi özeti.",
            },
            {
                "key": "publish_locked_scorecards",
                "title": "Yayın Kilidindeki Karneler",
                "value": summary["counts"].get("publish_locked_scorecards", 0),
                "route": "/performance/process-tracking",
                "description": "Onay veya süreç kaydı tamamlanmadan personele açılmaması gereken karneler.",
            },
            {
                "key": "delayed_assignments",
                "title": "Geciken Değerlendirme Görevleri",
                "value": summary["counts"].get("delayed_assignments", 0),
                "route": "/performance/meeting-development/faz9",
                "description": "Aksatan amir takibine konu olabilecek bekleyen görev özeti.",
            },
            {
                "key": "performance_reports",
                "title": "Performans Raporları",
                "value": summary["counts"].get("pending_assignments", 0),
                "route": "/performance/reports",
                "description": "Dönem, kategori, amir ve düşük performans raporlarına yönlendirme.",
            },
        ]
    else:
        summary["cards"] = [
            {
                "key": "my_pending_assignments",
                "title": "Bana Atanan Bekleyen Görevler",
                "value": summary["counts"].get("my_pending_assignments", 0),
                "route": "/performance/dashboard",
                "description": "Yalnızca kullanıcıya bağlı görev sayısı gösterilir; genel kurum özeti gizlidir.",
            }
        ]

    insert_agent_audit_log(
        user_id=user_id,
        action_key="ag2_performance_summary",
        detail=f"scope={summary['scope']} counts={summary['counts']}",
    )
    return summary
