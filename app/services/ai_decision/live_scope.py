
"""AI Karar Destek / Analiz Merkezi canlı kapsam sözleşmesi.

Faz 0 davranış değiştirmez. Bu dosya yalnızca canlıda kalacak AI tablo,
modül ve veri alanlarını tek kaynak olarak tarif eder. Sonraki fazlarda
request logging, redaction, cache, dashboard ve analiz motorları bu sözleşmeye
bağlanacaktır.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Final


@dataclass(frozen=True)
class AITableContract:
    table_name: str
    purpose: str
    required_columns: tuple[str, ...]
    sensitivity: str = "internal"
    write_policy: str = "service_only"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class AIDataDomain:
    key: str
    label: str
    source_tables: tuple[str, ...]
    ai_use: tuple[str, ...]
    visibility: str
    pii_policy: str = "redact_before_prompt"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


LIVE_AI_TABLES: Final[tuple[AITableContract, ...]] = (
    AITableContract(
        table_name="ai_request_logs",
        purpose="AI istekleri, yanıtları, model ve prompt sürümü için denetlenebilir kayıt.",
        required_columns=(
            "module_type",
            "feature_type",
            "target_table",
            "target_id",
            "user_id",
            "request_text",
            "response_text",
            "provider_name",
            "model_name",
            "prompt_version",
            "status",
            "latency_ms",
            "token_in",
            "token_out",
            "was_masked",
            "was_user_visible",
            "error_message",
        ),
        sensitivity="confidential",
    ),
    AITableContract(
        table_name="ai_recommendations",
        purpose="AI önerilerinin hedef kayıt, önem ve inceleme durumu ile saklanması.",
        required_columns=(
            "module_type",
            "target_table",
            "target_id",
            "recommendation_type",
            "title",
            "body",
            "severity",
            "status",
            "ai_request_log_id",
            "reviewed_by_user_id",
            "reviewed_at",
        ),
        sensitivity="internal",
    ),
    AITableContract(
        table_name="ai_redaction_rules",
        purpose="Alan bazlı maskeleme kuralları ve güvenli prompt hazırlığı.",
        required_columns=(
            "module_type",
            "field_name",
            "redaction_type",
            "replacement_text",
            "is_active",
        ),
        sensitivity="confidential",
    ),
    AITableContract(
        table_name="ai_summary_cache",
        purpose="Tekrarlı özetler için güvenli cache, kaynak hash ve süre yönetimi.",
        required_columns=(
            "module_type",
            "target_table",
            "target_id",
            "summary_kind",
            "summary_text",
            "source_hash",
            "expires_at",
        ),
        sensitivity="internal",
    ),
    AITableContract(
        table_name="ai_feedback_logs",
        purpose="AI çıktılarının kullanıcı geri bildirimi ve kalite takibi.",
        required_columns=(
            "ai_request_log_id",
            "user_id",
            "feedback_type",
            "feedback_note",
        ),
        sensitivity="internal",
    ),
)

LIVE_AI_TABLE_NAMES: Final[tuple[str, ...]] = tuple(table.table_name for table in LIVE_AI_TABLES)

LIVE_AI_DATA_DOMAINS: Final[tuple[AIDataDomain, ...]] = (
    AIDataDomain(
        key="personnel",
        label="Personel Yönetimi",
        source_tables=(
            "users",
            "organization_units",
            "organization_unit_versions",
            "employee_org_assignment_history",
        ),
        ai_use=("özet", "organizasyon sinyali", "eksik veri uyarısı"),
        visibility="admin_hr_manager",
    ),
    AIDataDomain(
        key="performance",
        label="Performans Yönetimi",
        source_tables=(
            "performance_periods",
            "evaluation_assignments",
            "performance_evaluations",
            "performance_evaluation_items",
            "performance_result_snapshots",
            "assignment_coverage_logs",
            "evaluation_publish_logs",
            "performance_publish_logs",
        ),
        ai_use=("karar destek", "risk önceliklendirme", "yayın öncesi kontrol", "özet"),
        visibility="admin_hr_manager_authorized_supervisor",
    ),
    AIDataDomain(
        key="leave_delegation",
        label="İzin / Devamsızlık / Vekâlet",
        source_tables=(
            "attendance_events",
            "attendance_exceptions",
            "leave_balances",
            "leave_records",
            "leave_requests",
            "personnel_leaves",
            "delegation_assignments",
        ),
        ai_use=("süreç etkisi", "vekalet sinyali", "performans entegrasyon notu"),
        visibility="admin_hr_manager",
    ),
    AIDataDomain(
        key="communication",
        label="İletişim",
        source_tables=(
            "messages",
            "message_threads",
            "message_thread_participants",
            "message_attachments",
            "message_reactions",
            "message_typing_states",
        ),
        ai_use=("kurumsal sinyal", "yoğunluk analizi", "destek yönlendirme"),
        visibility="authorized_admin_only",
    ),
    AIDataDomain(
        key="survey_feedback",
        label="Anket / Geri Bildirim / Nabız",
        source_tables=(
            "surveys",
            "survey_questions",
            "survey_assignments",
            "survey_responses",
            "survey_answers",
            "feedback_campaigns",
            "feedback_pulse_entries",
            "feedback_questions",
            "feedback_submissions",
        ),
        ai_use=("tema çıkarımı", "eğilim özeti", "kurumsal nabız", "öncelik önerisi"),
        visibility="admin_authorized_report_viewer",
    ),
    AIDataDomain(
        key="support",
        label="Yardım Merkezi / Destek",
        source_tables=(
            "support_categories",
            "support_tickets",
            "support_ticket_messages",
            "support_ticket_attachments",
            "support_ticket_status_history",
            "support_feedback_ratings",
        ),
        ai_use=("triyaj", "sık sorun özeti", "yanıt önerisi", "SLA sinyali"),
        visibility="support_admin_authorized_manager",
    ),
)

LIVE_AI_DOMAIN_KEYS: Final[tuple[str, ...]] = tuple(domain.key for domain in LIVE_AI_DATA_DOMAINS)

AI_DECISION_PHASES: Final[tuple[str, ...]] = (
    "Faz 0 — Envanter, canlı kapsam ve güvenli AI servis iskeleti",
    "Faz 1 — AI log / request / redaction servis köprüsü",
    "Faz 2 — AI özet cache ve güvenli özetleme altyapısı",
    "Faz 3 — Karar destek dashboard veri yüzeyi",
    "Faz 4 — Personel / performans içgörü motoru",
    "Faz 5 — Anket / geri bildirim / nabız analiz motoru",
    "Faz 6 — İletişim ve destek kayıtlarından kurumsal sinyal analizi",
    "Faz 7 — Analiz Merkezi Excel yükleme ve veri ön izleme",
    "Faz 8 — Görselleştirme / grafik / rapor kartları",
    "Faz 9 — AI öneri motoru ve risk/önceliklendirme paneli",
    "Faz 10 — Yetki, KVKK maskeleme ve güvenli görünürlük kapısı",
    "Faz 11 — UI profesyonelleştirme, yönetici ekranları ve rapor export",
    "Faz 12 — Final canlı sertleştirme, kalite kapısı ve kapanış raporu",
)


def get_live_ai_table_contracts() -> list[dict[str, object]]:
    return [table.to_dict() for table in LIVE_AI_TABLES]


def get_live_ai_data_domains() -> list[dict[str, object]]:
    return [domain.to_dict() for domain in LIVE_AI_DATA_DOMAINS]
