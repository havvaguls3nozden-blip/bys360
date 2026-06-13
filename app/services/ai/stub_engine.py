from __future__ import annotations



import logging
import ast
from collections import defaultdict
from typing import Any

# BYS360_STUB_AI_V60_EXTENSION_IMPORT
try:
    from .stub_engine_extension import (
        NEW_SCENARIO_BUILDERS,
        NEW_SCENARIO_HINTS,
        NEW_STUB_SCENARIOS,
    )
except Exception:  # pragma: no cover - canlı import güvenliği
    NEW_STUB_SCENARIOS = ()
    NEW_SCENARIO_BUILDERS = {}
    NEW_SCENARIO_HINTS = {}
# /BYS360_STUB_AI_V60_EXTENSION_IMPORT

SUPPORTED_STUB_SCENARIOS: tuple[tuple[str, str], ...] = (
    ("performance", "summary"),
    ("performance", "consistency"),
    ("dashboard", "brief"),
    ("support", "triage"),
    ("hr", "leave_brief"),
    ("communication", "priority"),
    ("survey", "summary"),
    ("feedback", "pulse_brief"),
    ("analysis_center", "governance"),
)

# BYS360_STUB_AI_V60_SCENARIO_MERGE
_SUPPORTED_BASE_SCENARIOS = SUPPORTED_STUB_SCENARIOS
SUPPORTED_STUB_SCENARIOS = tuple(dict.fromkeys(_SUPPORTED_BASE_SCENARIOS + tuple(NEW_STUB_SCENARIOS)))
# /BYS360_STUB_AI_V60_SCENARIO_MERGE


def get_stub_engine_snapshot() -> dict[str, Any]:
    return {
        "intelligence_level": "advanced_plus_v60",
        "scenario_count": len(SUPPORTED_STUB_SCENARIOS),
        "supported_features": [f"{module}/{feature}" for module, feature in SUPPORTED_STUB_SCENARIOS],
    }


def build_stub_response(*, system_prompt: str, user_prompt: str, prompt_version: str | None = None) -> str:
    module_type, feature_type = _infer_scenario(
        prompt_version=prompt_version,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
    payload = _extract_payload(user_prompt)
    builder = _SCENARIO_BUILDERS.get((module_type, feature_type), _build_generic_response)
    return builder(payload=payload, user_prompt=user_prompt, prompt_version=prompt_version)


def _infer_scenario(*, prompt_version: str | None, system_prompt: str, user_prompt: str) -> tuple[str, str]:
    version = _norm(prompt_version)
    for module_type, feature_type in SUPPORTED_STUB_SCENARIOS:
        version_flat = version.replace("_", "")
        if module_type in version and (
            feature_type in version or feature_type.replace("_", "") in version_flat
        ):
            return module_type, feature_type

    joined = f"{system_prompt}\n{user_prompt}".lower()
    hints = {
        ("performance", "summary"): ["performans kaydı", "yönetici özeti"],
        ("performance", "consistency"): ["tutarlılık kontrolü", "yayın öncesi"],
        ("dashboard", "brief"): ["dashboard görünümü", "bugün için öneri"],
        ("support", "triage"): ["destek talebi", "triage"],
        ("hr", "leave_brief"): ["izin ve vekâlet", "yönetici özeti"],
        ("communication", "priority"): ["iletişim", "öncelik"],
        ("survey", "summary"): ["anket", "özet"],
        ("feedback", "pulse_brief"): ["geri bildirim", "nabız"],
        ("analysis_center", "governance"): ["ai", "yönetişim"],
    }
    # BYS360_STUB_AI_V60_HINTS_MERGE
    try:
        hints.update(NEW_SCENARIO_HINTS)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("BYS360_CLAUDE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/ai/stub_engine.py")
    for key, tokens in hints.items():
        if all(token in joined for token in tokens):
            return key
    return ("general", "summary")


def _extract_payload(user_prompt: str) -> Any:
    text = str(user_prompt or "").strip()
    start = text.find("{")
    end = text.rfind("}")
    if 0 <= start < end:
        candidate = text[start : end + 1]
        try:
            return ast.literal_eval(candidate)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360_CLAUDE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/ai/stub_engine.py")
    start = text.find("[")
    end = text.rfind("]")
    if 0 <= start < end:
        candidate = text[start : end + 1]
        try:
            return ast.literal_eval(candidate)
        except Exception:
            import logging
            logging.getLogger(__name__).exception("BYS360_CLAUDE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/ai/stub_engine.py")
    return {}


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


def _text(value: Any, fallback: str = "-") -> str:
    text = str(value or "").strip()
    return text or fallback


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value or default)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value or default))
    except (TypeError, ValueError):
        return default


def _lines(*rows: str) -> str:
    return "\n".join(row for row in rows if str(row or "").strip())


def _build_performance_summary(*, payload: Any, user_prompt: str, prompt_version: str | None) -> str:
    if not isinstance(payload, dict):
        return _build_generic_response(
            payload=payload,
            user_prompt=user_prompt,
            prompt_version=prompt_version,
        )
    final_total = _safe_float(payload.get("final_total_100"))
    status = _text(payload.get("status"), "belirsiz")
    published = bool(payload.get("published"))
    employee = payload.get("employee") or {}
    employee_name = _text(employee.get("full_name"), "Personel")
    level_totals = payload.get("level_totals") or {}
    items = list(payload.get("items") or [])

    grouped: dict[str, list[float]] = defaultdict(list)
    missing_justification = 0
    for item in items:
        criteria = _text((item or {}).get("criteria"), "Kriter")
        grouped[criteria].append(_safe_float((item or {}).get("score")))
        score = _safe_int((item or {}).get("score"))
        if score in {1, 5} and not str((item or {}).get("justification") or "").strip():
            missing_justification += 1

    variance_count = sum(1 for scores in grouped.values() if scores and (max(scores) - min(scores) >= 2))
    band_text = "dengeli görünümde"
    if final_total < 70:
        band_text = "risk bandında"
    elif final_total >= 90:
        band_text = "güçlü performans bandında"
    publish_text = "yayına kapalı" if not published else "yayınlanmış"

    return _lines(
        "Genel Durum:",
        f"- {employee_name} için nihai görünüm {final_total:.2f} puan ve kayıt {band_text}.",
        f"- Süreç durumu {status}; kayıt şu an {publish_text} ve seviye toplamları {_safe_float(level_totals.get('level_1')):.1f} / {_safe_float(level_totals.get('level_2')):.1f} / {_safe_float(level_totals.get('level_3')):.1f}.",
        "Dikkat Noktaları:",
        (
            f"- {missing_justification} kriterde 1 veya 5 puan için gerekçe kontrolü gerekiyor."
            if missing_justification
            else "- 1 ve 5 puanlı kalemlerde belirgin gerekçe eksiği görünmüyor."
        ),
        (
            f"- {variance_count} kriterde amirler arası puan farkı izlenmeli."
            if variance_count
            else "- Amir seviyeleri arasında belirgin puan sapması görünmüyor."
        ),
        "Yönetici İçin Öneri:",
        (
            "- Nihai yorumu yayınlamadan önce düşük bant veya yüksek bant gerekçelerini ekip kıyas görünümüyle birlikte doğrulayın."
            if final_total < 70 or final_total >= 90
            else "- Bu kaydı ekip kıyas görünümündeki benzer sonuçlarla kısa biçimde karşılaştırıp yayın sırasına alın."
        ),
        "- AI çıktısını karar destek notu olarak kullanın; nihai idari kanaat amirde kalsın.",
    )


def _build_performance_consistency(*, payload: Any, user_prompt: str, prompt_version: str | None) -> str:
    if not isinstance(payload, dict):
        return _build_generic_response(
            payload=payload,
            user_prompt=user_prompt,
            prompt_version=prompt_version,
        )
    items = list(payload.get("items") or [])
    comments = payload.get("general_comments") or {}
    final_total = _safe_float(payload.get("final_total_100"))
    missing_justification = 0
    grouped: dict[str, list[float]] = defaultdict(list)
    for item in items:
        score = _safe_int((item or {}).get("score"))
        if score in {1, 5} and not str((item or {}).get("justification") or "").strip():
            missing_justification += 1
        grouped[_text((item or {}).get("criteria"), "Kriter")].append(_safe_float((item or {}).get("score")))
    variance_count = sum(1 for scores in grouped.values() if scores and (max(scores) - min(scores) >= 3))
    general_comment_exists = any(str(comments.get(key) or "").strip() for key in ("level_1", "level_2", "level_3"))
    extreme_needs_comment = final_total < 70 or final_total >= 90

    return _lines(
        "Kritik Kontroller:",
        f"- Nihai puan {final_total:.2f}; {'genel görüş mevcut' if general_comment_exists else 'genel görüş görünmüyor'}.",
        f"- {len(items)} kriter satırı ve {variance_count} dikkat isteyen seviye farkı tespit edildi.",
        "Eksik / Riskli Alanlar:",
        (
            f"- {missing_justification} kalemde 1 veya 5 puan gerekçesi eksik olabilir."
            if missing_justification
            else "- 1 ve 5 puanlarda belirgin gerekçe açığı görünmüyor."
        ),
        (
            "- 70 altı veya 90 üstü sonuçta ayrıntılı genel görüş beklenir; bu alanı ayrıca doğrulayın."
            if extreme_needs_comment and not general_comment_exists
            else "- Uç bant sonuçlara ait genel görüş görünümü temel kontrolü karşılıyor."
        ),
        "Yayın Öncesi Öneri:",
        "- Önce açıklama ve puan farkı taşıyan kriterleri düzeltip sonra yayımlama ön kontrolünü çalıştırın.",
        "- 3. amir yorum modundaysa puan etkisi varmış gibi değerlendirme yapmayın.",
    )


def _build_dashboard_brief(*, payload: Any, user_prompt: str, prompt_version: str | None) -> str:
    if not isinstance(payload, dict):
        return _build_generic_response(
            payload=payload,
            user_prompt=user_prompt,
            prompt_version=prompt_version,
        )
    overdue = _safe_int(payload.get("my_overdue_tasks"))
    pending_feedback = _safe_int(payload.get("pending_feedback_requests"))
    meetings = _safe_int(payload.get("upcoming_meetings_count"))
    unpublished = _safe_int(payload.get("unpublished_results_count"))
    risk_score = _safe_float(payload.get("coverage_risk_score"))
    completion_rate = _safe_float(payload.get("completion_rate"))
    active_period = _text(payload.get("active_period"), "Aktif dönem bekleniyor")
    tone = "dengeli"
    if overdue or unpublished or risk_score >= 70:
        tone = "dikkat yoğun"
    elif pending_feedback or meetings:
        tone = "takip isteyen"

    return _lines(
        "Genel Durum:",
        f"- {active_period} görünümü {tone}; tamamlanma oranı %{completion_rate:.1f} ve kapsama risk skoru {risk_score:.1f}.",
        f"- Üzerinizde {overdue} geciken görev, {pending_feedback} bekleyen geri bildirim talebi ve {meetings} yaklaşan görüşme görünüyor.",
        "Dikkat Gerektirenler:",
        (
            f"- Yayına açılmamış {unpublished} sonuç bulunuyor; personel görünürlüğü öncesi idari kontrol sürmeli."
            if unpublished
            else "- Yayın bekleyen kritik sonuç birikimi görünmüyor."
        ),
        (
            "- Görev gecikmeleri ve kapsama riskleri aynı dönemde büyürse ekip kıyas ve hiyerarşi ekranı birlikte kontrol edilmeli."
            if overdue or risk_score >= 70
            else "- Bugün için belirgin kırmızı alarm görünmüyor; akış ritmi korunabilir."
        ),
        "Bugün İçin Öneri:",
        "- Önce geciken görevleri ve yayın bekleyen sonuçları kapatın, sonra geri bildirim toplantı akışını planlayın.",
        "- Dashboard özetini karar destek notu gibi kullanın; işlem başlatmadan önce ilgili modül ekranına geçin.",
    )


def _build_support_triage(*, payload: Any, user_prompt: str, prompt_version: str | None) -> str:
    if not isinstance(payload, dict):
        return _build_generic_response(
            payload=payload,
            user_prompt=user_prompt,
            prompt_version=prompt_version,
        )
    title = _text(payload.get("title"), "Destek talebi")
    priority = _norm(payload.get("priority")) or "normal"
    status = _text(payload.get("status"), "belirsiz")
    module_name = _text(payload.get("module_name"), "genel")
    attachment_count = _safe_int(payload.get("attachment_count"))
    message_count = _safe_int(payload.get("message_count"))
    assigned_to = _text(payload.get("assigned_to"), "henüz atanmamış")
    if priority in {"critical", "urgent", "high"}:
        queue_note = "hızlı müdahale kuyruğuna alınmalı"
    elif message_count >= 4 or attachment_count >= 2:
        queue_note = "inceleme gerektiren detaylı kayıt gibi görünüyor"
    else:
        queue_note = "normal operasyon akışında çözülebilir"

    return _lines(
        "Talep Özeti:",
        f"- {title} başlıklı kayıt {module_name} alanına ait ve mevcut durum {status}.",
        f"- Kayıtta {message_count} mesaj ve {attachment_count} ek bulunuyor; sorumlu görünümü {assigned_to}.",
        "Öncelik Yorumu:",
        f"- Mevcut öncelik {priority}; kayıt {queue_note}.",
        "Yönlendirme Önerisi:",
        "- Önce kategori ve son durum notunu doğrulayıp doğru kişiye atayın; ardından kullanıcıya kısa dönüş planı verin.",
        "İlk İşlem Adımı:",
        "- Son mesaj ve ekleri kontrol edip eksik bilgi varsa tek seferde isteyin; tekrar yazışma sayısını azaltın.",
    )


def _build_hr_leave_brief(*, payload: Any, user_prompt: str, prompt_version: str | None) -> str:
    if not isinstance(payload, dict):
        return _build_generic_response(
            payload=payload,
            user_prompt=user_prompt,
            prompt_version=prompt_version,
        )
    summary = payload.get("summary") or {}
    health = payload.get("health") or {}
    coverage = health.get("coverage_summary") or {}
    pending = _safe_int(summary.get("pending_count") or summary.get("pending_leave_count"))
    active_delegations = _safe_int(summary.get("delegation_count") or payload.get("active_delegation_count"))
    uncovered = _safe_int(coverage.get("uncovered"))
    delegated_open = _safe_int(health.get("delegated_open_assignments"))
    period_title = _text(payload.get("period_title"), "aktif görünüm")
    leave_modes = payload.get("leave_modes") or {}
    partial_mode = _safe_int(leave_modes.get("partial"))
    informational_mode = _safe_int(leave_modes.get("informational"))

    return _lines(
        "İzin Durumu:",
        f"- {period_title} içinde bekleyen izin sayısı {pending}, aktif vekâlet sayısı {active_delegations} ve delegasyon üzerinden yürüyen açık görev {delegated_open}.",
        f"- Muafiyet dışı kısmi değerlendirme kayıtları {partial_mode}, yalnız bilgi amaçlı kayıtlar {informational_mode} olarak izleniyor.",
        "Kritik Sinyaller:",
        (
            f"- {uncovered} zincirde vekâletsiz veya açıkta kalan amir sinyali görünüyor."
            if uncovered
            else "- Vekâletsiz kritik zincir sinyali görünmüyor; akış temel olarak korunuyor."
        ),
        (
            "- Bekleyen izin talepleri artarsa aynı dönemde performans görev dağılımı ve vekâlet planı birlikte kontrol edilmeli."
            if pending
            else "- Bekleyen karar baskısı düşük; ana odak kapsama ve süre bitişleri olmalı."
        ),
        "Yönetici İçin Aksiyon:",
        "- Önce vekâletsiz zincirleri ve bekleyen izinleri kapatın, sonra delegasyon etkisini görev üretimi üzerinde doğrulayın.",
        "- HR ekranındaki statik paneli hızlı görünüm, bu AI özetini ise karar öncesi ikinci kontrol olarak kullanın.",
    )


def _build_generic_response(*, payload: Any, user_prompt: str, prompt_version: str | None) -> str:
    return _lines(
        "Özet:",
        "- AI servisi kontrollü gelişmiş stub modunda çalıştı ve güvenli bir kurumsal cevap üretti.",
        "- Bu senaryo için özel kural motoru tanımlı değilse çıktı varsayılan karar destek notu olarak yorumlanmalıdır.",
        "Not:",
        "- Nihai işlem ve onay yetkisi her zaman ilgili kullanıcı ve yönetici rollerinde kalır.",
    )


_SCENARIO_BUILDERS = {
    ("performance", "summary"): _build_performance_summary,
    ("performance", "consistency"): _build_performance_consistency,
    ("dashboard", "brief"): _build_dashboard_brief,
    ("support", "triage"): _build_support_triage,
    ("hr", "leave_brief"): _build_hr_leave_brief,
    ("communication", "priority"): _build_generic_response,
    ("survey", "summary"): _build_generic_response,
    ("feedback", "pulse_brief"): _build_generic_response,
    ("analysis_center", "governance"): _build_generic_response,
}

# BYS360_STUB_AI_V60_BUILDER_MERGE
try:
    _SCENARIO_BUILDERS.update(NEW_SCENARIO_BUILDERS)
except Exception:
    import logging
    logging.getLogger(__name__).exception("BYS360_CLAUDE_V13_P1_SILENT_EXCEPTION_LOGGER | app/services/ai/stub_engine.py")
