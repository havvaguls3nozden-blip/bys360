"""BYS360 Performans Tamamlama Faz 6 Başkan/Üst Onay ve Düşük Performans Merkezi."""
from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from typing import Any

logger = logging.getLogger(__name__)

BYS360_PERFORMANCE_COMPLETION_PHASE6_VERSION = "performance-completion-phase6-low-score-process-center-v1"
PHASE6_POLICY_MARKER = "BYS360_PERFORMANCE_COMPLETION_PHASE6_LOW_SCORE_PROCESS_CENTER"
BYS360_PERFORMANCE_COMPLETION_PHASE6_NO_FAKE_APPROVAL = True
BYS360_PERFORMANCE_COMPLETION_PHASE6_PUBLISH_LOCK = True
BYS360_PERFORMANCE_COMPLETION_PHASE6_FIRST_SECOND_TRACKING = True
BYS360_PERFORMANCE_COMPLETION_PHASE6_PROCESS_RECORD_REQUIRED = True
LOW_SCORE_THRESHOLD = 70.0
STATUS_LABELS: dict[str, str] = {
    "not_required": "Üst Onay Gerekmiyor",
    "president_pending": "Başkan/Üst Onay Bekliyor",
    "president_approval_pending": "Başkan/Üst Onay Bekliyor",
    "direct_president_pending": "Başkan/Üst Onay Bekliyor",
    "blocked_president_pending": "Başkan/Üst Onay Yayın Kilidi",
    "approved_by_president": "Başkan/Üst Onay Tamamlandı",
    "president_approved": "Başkan/Üst Onay Tamamlandı",
    "rejected_by_president": "Başkan/Üst Onay Tarafından İade Edildi",
    "president_rejected": "Başkan/Üst Onay Tarafından İade Edildi",
    "president_returned": "Başkan/Üst Onay Tarafından İade Edildi",
    "first_low_warning": "Düşük Performans Uyarısı Oluşturuldu",
    "warning_recorded": "Düşük Performans Uyarısı Oluşturuldu",
    "second_low_repeat": "Tekrarlayan Düşük Performans Süreci",
    "second_low_score_process_started": "Tekrarlayan Düşük Performans Süreci",
    "administrative_process_started": "Tekrarlayan Düşük Performans Süreci",
    "process_record_required": "Personel Süreç Kaydı Bekliyor",
    "publish_allowed": "Yayınlanabilir",
    "publish_blocked": "Yayın Kilitli",
}
PHASE6_SETTING_ROWS = (
    ("performance_phase6", "low_score_threshold", "Düşük performans eşiği", "number", "70", "Nihai puan bu değerin altındaysa üst onay ve süreç kaydı gerekir."),
    ("performance_phase6", "low_score_requires_upper_approval", "70 altı sonuçta Başkan/Üst Onay zorunlu", "bool", "true", "70 altı karne üst onay tamamlanmadan personele yayınlanamaz."),
    ("performance_phase6", "publish_block_until_upper_approval", "Üst onay tamamlanmadan yayın kilidi", "bool", "true", "Düşük performans sonucu onaysız personele açılmaz."),
    ("performance_phase6", "first_low_warning_required", "İlk 70 altı sonuçta uyarı kaydı zorunlu", "bool", "true", "Aynı yıl ilk düşük performans sonucunda uyarı/süreç kaydı oluşur."),
    ("performance_phase6", "second_low_administrative_process_required", "İkinci 70 altı sonuçta idari süreç kaydı zorunlu", "bool", "true", "Aynı yıl ikinci 70 altı otomatik işten çıkarma yapmaz; idari süreç başlatır."),
    ("performance_phase6", "fake_president_approval_forbidden", "Sahte üst onay kaydı engellensin", "bool", "true", "70 üstü veya puanı oluşmamış kayıtlar Başkan/Üst Onay ekranına düşmez."),
    ("performance_phase6", "technical_status_hidden", "Düşük performans teknik statüleri Türkçeleştirilsin", "bool", "true", "president_pending gibi teknik kodlar kullanıcıya ham gösterilmez."),
)
PROCESS_STEPS = (
    ("evaluation_completed", "Değerlendirme tamamlandı"),
    ("low_score_detected", "70 altı sonuç tespit edildi"),
    ("upper_approval", "Başkan/Üst Onay sürecine alındı"),
    ("approval_completed", "Üst onay tamamlandı"),
    ("personnel_process_record", "Personel süreç kaydı oluşturuldu"),
    ("publish_ready", "Yayın sürecine hazırlandı"),
)
@dataclass(frozen=True)
class Phase6Decision:
    low_score: bool
    approval_required: bool
    approval_status: str
    approval_label: str
    publish_blocked: bool
    publish_lock_label: str
    process_record_required: bool
    warning_level: str
    warning_label: str
    can_publish: bool
    next_action: str
    block_reason: str = ""
    def as_dict(self) -> dict[str, Any]: return asdict(self)

def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default

def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except Exception:
        return default

def _normalize(value: Any) -> str: return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")
def _has_attr_value(obj: Any, *names: str) -> bool: return any(bool(getattr(obj, name, None)) for name in names)
def phase6_status_label(status: Any) -> str:
    raw=str(status or "").strip()
    return "Süreç Durumu" if not raw else STATUS_LABELS.get(_normalize(raw), raw)
def is_phase6_low_score(score: Any, threshold: float = LOW_SCORE_THRESHOLD) -> bool:
    value=_safe_float(score)
    return bool(value is not None and value < threshold)
def score_from_evaluation(evaluation: Any) -> float | None:
    for name in ("final_score","score","total_score","average_score","nihai_puan","final_point"):
        value=_safe_float(getattr(evaluation,name,None))
        if value is not None:
            return value
    return None
def process_is_approved(process: Any) -> bool: return _has_attr_value(process,"president_approved_at","president_approved_by_id","upper_approved_at","approved_at")
def process_is_rejected(process: Any) -> bool: return _has_attr_value(process,"president_rejected_at","president_rejected_by_id","president_rejection_note","rejected_at")
def process_is_second_or_later(process: Any) -> bool: return _safe_int(getattr(process,"sequence_no",1),1) >= 2
def process_has_first_warning_record(process: Any) -> bool: return _has_attr_value(process,"warning_recorded_at","warning_recorded_by_id","warning_note")
def process_has_second_admin_record(process: Any) -> bool: return _has_attr_value(process,"administrative_process_started_at","administrative_process_started_by_id","administrative_process_note")
def classify_phase6_repeat(previous_low_count_in_year: Any = 0, sequence_no: Any = None) -> tuple[str,str]:
    if _safe_int(sequence_no,0) >= 2:
        return "second_low_repeat", STATUS_LABELS["second_low_repeat"]
    return ("first_low_warning", STATUS_LABELS["first_low_warning"]) if _safe_int(previous_low_count_in_year,0) <= 0 else ("second_low_repeat", STATUS_LABELS["second_low_repeat"])
def should_create_phase6_president_approval_record(final_score: Any, *, existing_record: bool=False, score_finalized: bool=True) -> bool:
    return bool(score_finalized and is_phase6_low_score(final_score) and not existing_record)
def resolve_phase6_low_score_process(*, final_score: Any, approval_status: Any=None, process_record_exists: bool=False, warning_record_exists: bool=False, administrative_process_exists: bool=False, previous_low_count_in_year: Any=0, sequence_no: Any=None) -> Phase6Decision:
    low=is_phase6_low_score(final_score)
    if not low:
        return Phase6Decision(False,False,"not_required",STATUS_LABELS["not_required"],False,STATUS_LABELS["publish_allowed"],False,"not_required","Düşük performans süreci gerekmiyor",True,"Yayın süreci normal akışta ilerleyebilir.")
    status=_normalize(approval_status or "president_pending")
    approved=status in {"approved_by_president","president_approved","approved","upper_approved"}
    rejected=status in {"rejected_by_president","president_rejected","president_returned","rejected","returned"}
    warning_key,warning_label=classify_phase6_repeat(previous_low_count_in_year,sequence_no)
    is_second=warning_key=="second_low_repeat"
    if rejected:
        reason="Başkan/Üst Onay tarafından iade edilen 70 altı karne personele yayınlanamaz."
        return Phase6Decision(True,True,"rejected_by_president",STATUS_LABELS["rejected_by_president"],True,STATUS_LABELS["blocked_president_pending"],True,warning_key,warning_label,False,"İade gerekçesi değerlendirilerek süreç yeniden hazırlanmalıdır.",reason)
    if not approved:
        reason="Başkan/Üst Onay tamamlanmadan 70 altı karne personele yayınlanamaz."
        return Phase6Decision(True,True,"president_pending",STATUS_LABELS["president_pending"],True,STATUS_LABELS["blocked_president_pending"],True,warning_key,warning_label,False,"Başkan/Üst Onay tamamlanmalıdır.",reason)
    if is_second and not administrative_process_exists:
        reason="Aynı yıl ikinci 70 altı sonuç için tekrarlayan düşük performans/idari süreç kaydı oluşturulmadan yayın yapılamaz."
        return Phase6Decision(True,True,"approved_by_president",STATUS_LABELS["approved_by_president"],True,STATUS_LABELS["process_record_required"],True,warning_key,warning_label,False,"Tekrarlayan düşük performans süreci kaydı oluşturulmalıdır.",reason)
    if (not is_second) and not warning_record_exists:
        reason="İlk 70 altı sonuç için düşük performans uyarı kaydı oluşturulmadan yayın yapılamaz."
        return Phase6Decision(True,True,"approved_by_president",STATUS_LABELS["approved_by_president"],True,STATUS_LABELS["process_record_required"],True,warning_key,warning_label,False,"Düşük performans uyarı kaydı oluşturulmalıdır.",reason)
    if not process_record_exists:
        reason="Onay sonrası personel süreç zinciri kaydı tamamlanmadan yayın yapılamaz."
        return Phase6Decision(True,True,"approved_by_president",STATUS_LABELS["approved_by_president"],True,STATUS_LABELS["process_record_required"],True,warning_key,warning_label,False,"Personel süreç zinciri kaydı tamamlanmalıdır.",reason)
    return Phase6Decision(True,True,"approved_by_president",STATUS_LABELS["approved_by_president"],False,STATUS_LABELS["publish_allowed"],False,warning_key,warning_label,True,"Yayın öncesi kurumsal kontrol adımına geçilebilir.")
def resolve_phase6_process_object(process: Any) -> Phase6Decision:
    final_score=getattr(process,"final_score",None)
    status="president_pending"
    if process_is_rejected(process):
        status="rejected_by_president"
    elif process_is_approved(process):
        status="approved_by_president"
    warning_exists=process_has_first_warning_record(process)
    admin_exists=process_has_second_admin_record(process)
    return resolve_phase6_low_score_process(final_score=final_score, approval_status=status, process_record_exists=bool(warning_exists or admin_exists), warning_record_exists=warning_exists, administrative_process_exists=admin_exists, sequence_no=getattr(process,"sequence_no",1))
def is_phase6_process_finalized_for_publish(process: Any) -> bool: return bool(resolve_phase6_process_object(process).can_publish)
def phase6_publish_block_reason_from_process(process: Any) -> str: return resolve_phase6_process_object(process).block_reason
def phase6_process_steps(decision: Phase6Decision) -> list[dict[str,Any]]:
    items=[]
    for idx,(key,title) in enumerate(PROCESS_STEPS,start=1):
        state="pending"
        if key=="evaluation_completed" or key=="low_score_detected" and decision.low_score:
            state="done"
        elif key=="upper_approval" and decision.approval_required:
            state="active" if decision.approval_status=="president_pending" else "done"
        elif key=="approval_completed" and decision.approval_status=="approved_by_president":
            state="done"
        elif key=="personnel_process_record" and decision.approval_status=="approved_by_president":
            state="active" if decision.process_record_required else "done"
        elif key=="publish_ready" and decision.can_publish:
            state="done"
        items.append({"order":idx,"key":key,"title":title,"state":state,"label":{"done":"Tamamlandı","active":"Devam Ediyor","pending":"Bekliyor"}.get(state,"Bekliyor")})
    return items
def filter_phase6_real_low_score_approvals(rows: Iterable[Mapping[str,Any]]) -> list[dict[str,Any]]:
    clean=[]
    for row in rows or []:
        final_score=row.get("final_score") or row.get("score") or row.get("nihai_puan")
        if not is_phase6_low_score(final_score):
            continue
        item=dict(row)
        item["approval_label"]=phase6_status_label(item.get("approval_status") or "president_pending")
        item["publish_lock_label"]=STATUS_LABELS["blocked_president_pending"]
        clean.append(item)
    return clean
def phase6_contract() -> dict[str,Any]:
    return {"version":BYS360_PERFORMANCE_COMPLETION_PHASE6_VERSION,"phase_marker":PHASE6_POLICY_MARKER,"low_score_threshold":LOW_SCORE_THRESHOLD,"fake_approval_records_forbidden":True,"publish_block_until_upper_approval":True,"first_low_warning_required":True,"second_low_administrative_process_required":True,"process_record_required_after_approval":True,"technical_status_hidden":True,"status_labels":dict(STATUS_LABELS),"settings":[{"module_key":m,"setting_key":k,"label":label,"value_type":t,"default_value":d,"description":desc} for m,k,label,t,d,desc in PHASE6_SETTING_ROWS]}
def seed_phase6_low_score_process_settings() -> dict[str,Any]:
    changed=[]
    try:
        from app import db
        try:
            from app.models import ModuleSetting
        except Exception:
            from app.models.settings_models import ModuleSetting
    except Exception as exc:
        return {"ok":False,"error":str(exc),"settings":changed}
    for module_key,setting_key,label,value_type,default_value,description in PHASE6_SETTING_ROWS:
        try:
            row=ModuleSetting.query.filter_by(module_key=module_key,setting_key=setting_key).first()
            if row is None:
                row=ModuleSetting(module_key=module_key,setting_key=setting_key)
                db.session.add(row)
            if hasattr(row,"label"):
                row.label=label
            if hasattr(row,"value_type"):
                row.value_type=value_type
            if hasattr(row,"value_text") and not getattr(row,"value_text",None):
                row.value_text=default_value
            if hasattr(row,"description"):
                row.description=description
            if hasattr(row,"is_active"):
                row.is_active=True
            changed.append(f"{module_key}.{setting_key}")
        except Exception:
            continue
    try:
        db.session.commit()
        return {"ok":True,"settings":changed}
    except Exception as exc:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        try:
            db.session.rollback()
        except Exception:
            logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
            logging.getLogger(__name__).exception("BYS360 suppressed exception captured in app/services/performance/phase6_low_score_process_center.py:175")
        return {"ok":False,"error":str(exc),"settings":changed}
