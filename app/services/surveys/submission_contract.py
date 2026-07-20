"""Canlı anket cevaplama akışı için pasif sözleşme kontrolleri.

Faz 7 kuralı:
- `survey_submit` davranışı bu dosyaya taşınmaz.
- Canlı yazma akışı route içinde kalır.
- Bu dosya yalnızca kaynak kod sözleşmesini denetlemek ve gelecekteki güvenli taşıma
  için kırmızı çizgileri görünür yapmak amacıyla kullanılır.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class SubmissionContractCheck:
    """Kaynak kod üzerinde çalıştırılan pasif bir sözleşme kontrolü."""

    code: str
    title: str
    needle: str
    detail: str


def _find(text: str, needle: str) -> int:
    return text.find(needle)


def _line_no(text: str, index: int) -> int | None:
    if index < 0:
        return None
    return text.count("\n", 0, index) + 1


def submission_contract_checks() -> list[SubmissionContractCheck]:
    """Canlı submit akışında korunması gereken minimum sözleşme maddeleri."""

    return [
        SubmissionContractCheck(
            "submit_post_only",
            "Submit endpoint yalnızca POST kabul eder",
            '@main_bp.route("/surveys/<int:survey_id>/submit", methods=["POST"])',
            "GET veya yanlış method ile cevap kaydı açılmamalı.",
        ),
        SubmissionContractCheck(
            "submit_login_required",
            "Submit endpoint login korumalıdır",
            "@login_required\n@menu_key_required(\"surveys\")\ndef survey_submit",
            "Cevap kaydı anonim anket dışında yetkisiz kullanıcıya açık olamaz.",
        ),
        SubmissionContractCheck(
            "access_state_before_write",
            "Anket erişim durumu yazmadan önce kontrol edilir",
            "survey_ok, survey_reason = _survey_access_state(survey)",
            "Kapalı, arşivli veya erişime uygun olmayan anket yazma akışına girmemeli.",
        ),
        SubmissionContractCheck(
            "assignment_required",
            "Kullanıcı hedef kitle eşleşmesi aranır",
            "if not matched_assignment:",
            "Atanmamış kullanıcı cevap gönderememeli.",
        ),
        SubmissionContractCheck(
            "duplicate_guard",
            "Tekil cevap kuralı korunur",
            "if not survey.allow_multiple_submissions and not survey.is_anonymous:",
            "Çoklu gönderim kapalıysa tamamlanmış cevap ikinci kez alınmamalı.",
        ),
        SubmissionContractCheck(
            "form_token_consumed",
            "Form token tüketimi korunur",
            "consume_form_token(\"survey_submit\"",
            "Çift tıklama, geri tuşu ve tekrar POST senaryoları aynı yanıtı çoğaltmamalı.",
        ),
        SubmissionContractCheck(
            "response_created_after_token",
            "Yanıt kaydı token sonrası oluşturulur",
            "response = SurveyResponse(",
            "Token doğrulanmadan SurveyResponse oluşturulmamalı.",
        ),
        SubmissionContractCheck(
            "single_choice_required",
            "Tek seçimli zorunlu soru kontrolü vardır",
            "if question.is_required and not selected_option_id:",
            "Zorunlu tek seçimli soru boş geçilememeli.",
        ),
        SubmissionContractCheck(
            "single_choice_invalid_guard",
            "Tek seçimli geçersiz seçenek engellenir",
            "if selected_option_id not in allowed_option_ids:",
            "Kullanıcı formu manipüle edip ankete ait olmayan seçeneği gönderememeli.",
        ),
        SubmissionContractCheck(
            "multiple_choice_required",
            "Çok seçimli zorunlu soru kontrolü vardır",
            "if question.is_required and not selected_ids:",
            "Zorunlu çok seçimli soru boş geçilememeli.",
        ),
        SubmissionContractCheck(
            "multiple_choice_invalid_guard",
            "Çok seçimli geçersiz seçenek engellenir",
            "invalid_ids = [option_id for option_id in selected_ids if option_id not in allowed_option_ids]",
            "Manipüle edilmiş seçenek listesi kayıt altına alınmamalı.",
        ),
        SubmissionContractCheck(
            "rating_required",
            "Puanlı zorunlu soru kontrolü vardır",
            "if question.is_required and answer_number is None:",
            "Zorunlu puan sorusu boş gönderilememeli.",
        ),
        SubmissionContractCheck(
            "rating_range_guard",
            "Puan aralığı kontrol edilir",
            "if answer_number is not None and not (0 <= answer_number <= max_scale):",
            "Puan sorusunda 0-altı veya ölçek üstü değer kaydedilmemeli.",
        ),
        SubmissionContractCheck(
            "open_text_required",
            "Açık uçlu zorunlu soru kontrolü vardır",
            "if question.is_required and not answer_text:",
            "Zorunlu açık uçlu soru boş gönderilememeli.",
        ),
        SubmissionContractCheck(
            "rollback_on_error",
            "Hata halinde transaction geri alınır",
            "db.session.rollback()",
            "Kısmi cevap / yarım yanıt kaydı canlı veride kalmamalı.",
        ),
        SubmissionContractCheck(
            "commit_on_success",
            "Başarılı gönderimde tek commit vardır",
            "db.session.commit()",
            "Başarılı cevap akışı transaction sonunda kapanmalı.",
        ),
    ]


def evaluate_submission_contract(source_text: str, checks: Iterable[SubmissionContractCheck] | None = None) -> list[dict[str, object]]:
    """`survey_submit` sözleşmesini kaynak kod üzerinden pasif olarak değerlendirir."""

    checks = list(checks or submission_contract_checks())
    results: list[dict[str, object]] = []
    for check in checks:
        index = _find(source_text, check.needle)
        results.append(
            {
                "code": check.code,
                "title": check.title,
                "ok": index >= 0,
                "line": _line_no(source_text, index),
                "needle": check.needle,
                "detail": check.detail,
            }
        )
    return results


def ensure_order(source_text: str, before: str, after: str) -> bool:
    """İki kaynak parçasının beklenen sırada olduğunu kontrol eder."""

    before_index = _find(source_text, before)
    after_index = _find(source_text, after)
    return before_index >= 0 and after_index >= 0 and before_index < after_index


__all__ = [
    "SubmissionContractCheck",
    "ensure_order",
    "evaluate_submission_contract",
    "submission_contract_checks",
]
