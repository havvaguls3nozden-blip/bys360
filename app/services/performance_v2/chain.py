from __future__ import annotations

import logging

from app import db
from app.models import User

from .dto import ChainIssue, ChainLevel, ResolvedChain
from .rules import (
    LevelMode,
    SubjectType,
    classify_subject_type,
    normalize_level_mode,
    normalize_role_token,
    resolve_chain_policy,
)

logger = logging.getLogger(__name__)


SOURCE_FIELDS = ("yonetici_sicil", "ikinci_yonetici_sicil", "ucuncu_yonetici_sicil")

_AUTHORITY_ISSUE_MAP = {
    "1. amir eksik veya pasif": ("level_1_missing", "warning"),
    "2. amir eksik veya pasif": ("level_2_missing", "warning"),
    "3. amir tanımlı ancak geçersiz/pasif": ("level_3_invalid", "warning"),
    "Aynı kişi birden fazla amir seviyesine atanmış.": ("duplicate_manager", "warning"),
    "Personel kendisine amir atanamaz.": ("self_manager", "error"),
    "Başkan kaydı bulunamadı veya pasif.": ("president_missing", "warning"),
    "Hukuk Müşaviri eksik veya pasif": ("hukuk_manager_missing", "warning"),
}


def _humanize_role(role_token: str | None, manager) -> str | None:
    if not role_token:
        text = (getattr(manager, "unvan", None) or getattr(manager, "role_label", None) or getattr(manager, "role", None) or "").strip()
        return text or None
    mapping = {
        "baskan": "Başkan",
        "baskan_yardimcisi": "Başkan Yardımcısı",
        "grup_baskani": "Grup Başkanı",
        "mali_musavir": "Mali Müşavir",
        "koordinator": "Koordinatör",
        "birim_sorumlusu": "Birim Sorumlusu",
        "hukuk_musaviri": "Hukuk Müşaviri",
        "personel": "Personel",
    }
    return mapping.get(role_token, role_token.replace("_", " ").title())


def _collect_candidates(employee) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    seen: set[str] = set()
    for field_name in SOURCE_FIELDS:
        sicil = (getattr(employee, field_name, None) or "").strip()
        if not sicil or sicil in seen:
            continue
        seen.add(sicil)
        manager = User.query.filter_by(sicil_no=sicil).first()
        candidates.append(
            {
                "source_field": field_name,
                "sicil": sicil,
                "user": manager,
                "role_token": normalize_role_token(
                    getattr(manager, "role", ""),
                    getattr(manager, "role_label", ""),
                    getattr(manager, "unvan", ""),
                ) if manager else None,
            }
        )
    return candidates


def _append_issue_once(resolved: ResolvedChain, issue: ChainIssue) -> None:
    for existing in resolved.issues:
        if existing.code == issue.code and existing.message == issue.message:
            return
    resolved.issues.append(issue)


def _issue_from_authority(raw_message: str, *, default_severity: str = "info") -> ChainIssue:
    code, severity = _AUTHORITY_ISSUE_MAP.get(raw_message, ("authority_note", default_severity))
    return ChainIssue(code=code, message=raw_message, severity=severity)


def _candidate_from_sicil(candidates: list[dict[str, object]], sicil_no: str | None):
    if not sicil_no:
        return None
    target = str(sicil_no).strip()
    return next((candidate for candidate in candidates if str(candidate.get("sicil", "")).strip() == target), None)


def _is_hukuk_subject(employee) -> bool:
    blob = ' | '.join(
        str(getattr(employee, attr, '') or '').strip().lower()
        for attr in ('role', 'role_label', 'unvan', 'birim', 'ust_birim')
    )
    return 'hukuk musavir' in blob or 'sorumlu hukuk musavir' in blob

def _is_hukuk_musaviri_subject(employee) -> bool:
    blob = ' | '.join(
        str(getattr(employee, attr, '') or '').strip().lower()
        for attr in ('role', 'role_label', 'unvan', 'birim', 'ust_birim')
    )
    return 'hukuk musavir' in blob or 'sorumlu hukuk musavir' in blob


def _single_manager_label(employee, authority, policy) -> str:
    if _is_hukuk_subject(employee):
        return 'Hukuk Müşaviri'

    issue_codes = {
        str(getattr(item, 'code', '') or '').strip().lower()
        for item in (getattr(authority, 'issues', None) or [])
    }
    issue_messages = ' | '.join(
        str(getattr(item, 'message', '') or '').strip().lower()
        for item in (getattr(authority, 'issues', None) or [])
    )
    info_blob = ' | '.join(str(note or '').strip().lower() for note in (getattr(authority, 'info_notes', None) or []))

    if 'single_manager_rule' in issue_codes or 'ozel baskanlik birimi tek amir kurali' in info_blob or 'ozel tek amir kurali' in issue_messages:
        return 'Başkan'

    return policy.labels.get(1, '1. Amir')


def _enforce_hukuk_presidency_order(resolved, employee) -> None:
    if not _is_hukuk_musaviri_subject(employee):
        return

    level1 = resolved.levels.get(1)
    level2 = resolved.levels.get(2)
    if not level1 or not level2:
        return

    role1 = str(getattr(level1, 'evaluator_role', '') or '').strip().lower()
    role2 = str(getattr(level2, 'evaluator_role', '') or '').strip().lower()

    is_level1_vp = 'başkan yardımcısı' in role1 or 'baskan yardimcisi' in role1
    is_level2_president = role2 == 'başkan' or role2 == 'baskan'

    # Ters durum: 1=Başkan Yardımcısı, 2=Başkan
    if is_level1_vp and is_level2_president:
        resolved.levels[1], resolved.levels[2] = resolved.levels[2], resolved.levels[1]
        resolved.levels[1].level = 1
        resolved.levels[2].level = 2
        resolved.levels[1].label = 'Başkan'
        resolved.levels[2].label = 'Başkan Yardımcısı'

    # Hukuk amiri özel istisnasında işlem sırası her zaman 2 -> 1.
    resolved.order = [2, 1]

def _make_chain_level(*, level: int, label: str, manager, source_field: str | None, level_mode: LevelMode) -> ChainLevel:
    role_token = normalize_role_token(
        getattr(manager, "role", ""),
        getattr(manager, "role_label", ""),
        getattr(manager, "unvan", ""),
    )
    return ChainLevel(
        level=level,
        label=label,
        evaluator_id=getattr(manager, "id", None),
        evaluator_sicil=getattr(manager, "sicil_no", None),
        evaluator_name=getattr(manager, "full_name", None) or f"{getattr(manager, 'ad', '')} {getattr(manager, 'soyad', '')}".strip(),
        evaluator_role=_humanize_role(role_token, manager),
        source_field=source_field,
        score_enabled=not (level == 3 and level_mode != LevelMode.SCORE_ENABLED),
        visible_to_next=level in {2, 3},
    )


def _apply_authoritative_chain(resolved: ResolvedChain, *, employee, period, policy, level_mode, candidates: list[dict[str, object]]) -> object | None:
    try:
        from app.services.performance.hierarchy import build_manager_chain_for_user
    except Exception:
        logger.exception("BYS360 performans modülünde beklenmeyen hata yakalandı.")
        return None

    authority = build_manager_chain_for_user(employee=employee, period=period)
    if not authority:
        return None

    subject_type = classify_subject_type(employee)
    if not getattr(authority, "manager_1_id", None) and any("Başkan performans değerlendirme zincirine dahil edilmez" in note for note in getattr(authority, "info_notes", [])):
        resolved.order = []
        _append_issue_once(
            resolved,
            ChainIssue(code="president_excluded", message="Başkan performans değerlendirme zincirine dahil edilmez.", severity="info"),
        )
        return authority

    use_authority_ids = bool(getattr(authority, "is_single_manager_case", False)) or subject_type in {
        SubjectType.COORDINATOR,
        SubjectType.GROUP_MANAGER,
        SubjectType.GROUP_STAFF,
        SubjectType.HUKUK_STAFF,
    }
    if use_authority_ids:
        if getattr(authority, "is_single_manager_case", False):
            resolved.order = [1]
            resolved.levels.clear()
            manager = db.session.get(User, getattr(authority, "manager_1_id", None)) if getattr(authority, "manager_1_id", None) else None
            if manager:
                candidate = _candidate_from_sicil(candidates, getattr(manager, "sicil_no", None))
                level_label = _single_manager_label(employee, authority, policy)
                resolved.levels[1] = _make_chain_level(
                    level=1,
                    label=level_label,
                    manager=manager,
                    source_field=(candidate or {}).get("source_field") or policy.fallback_fields.get(1),
                    level_mode=level_mode,
                )
        else:
            explicit_level3 = str(getattr(employee, 'ucuncu_yonetici_sicil', '') or '').strip()
            authority_level3_id = getattr(authority, "manager_3_id", None)
            authority_map = {
                1: getattr(authority, "manager_1_id", None),
                2: getattr(authority, "manager_2_id", None),
                3: authority_level3_id if (getattr(authority, "level_3_enabled", False) or (explicit_level3 and authority_level3_id)) else None,
            }
            for level, manager_id in authority_map.items():
                if level == 3 and level_mode == LevelMode.DISABLED:
                    continue
                if not manager_id:
                    continue
                manager = db.session.get(User, manager_id)
                if not manager:
                    continue
                candidate = _candidate_from_sicil(candidates, getattr(manager, "sicil_no", None))
                resolved.levels[level] = _make_chain_level(
                    level=level,
                    label=policy.labels.get(level, f"{level}. Amir"),
                    manager=manager,
                    source_field=(candidate or {}).get("source_field") or policy.fallback_fields.get(level),
                    level_mode=level_mode,
                )

    for raw_issue in getattr(authority, "issues", []) or []:
        raw_issue_text = str(raw_issue)
        default_severity = "info" if "3. amir" in raw_issue_text.lower() and level_mode != LevelMode.SCORE_ENABLED else "warning"
        _append_issue_once(resolved, _issue_from_authority(raw_issue_text, default_severity=default_severity))
    for note in getattr(authority, "info_notes", []) or []:
        _append_issue_once(resolved, _issue_from_authority(note, default_severity="info"))
    return authority


def _promote_explicit_third_manager_mode(employee, level_mode: LevelMode) -> LevelMode:
    explicit_level_3 = str(getattr(employee, 'ucuncu_yonetici_sicil', '') or '').strip()
    if explicit_level_3 and level_mode == LevelMode.DISABLED:
        return LevelMode.COMMENT_ONLY
    return level_mode


def build_resolved_chain(employee, period=None) -> ResolvedChain:
    policy = resolve_chain_policy(employee)
    base_level_mode = normalize_level_mode(period)
    level_mode = _promote_explicit_third_manager_mode(employee, base_level_mode)
    resolved = ResolvedChain(
        chain_type=policy.chain_type.value,
        subject_type=classify_subject_type(employee).value,
        order=list(policy.order if level_mode != LevelMode.DISABLED else [lvl for lvl in policy.order if lvl != 3]),
        level_mode=level_mode.value,
    )
    candidates = _collect_candidates(employee)
    used_sicils: set[str] = set()

    authority = _apply_authoritative_chain(
        resolved,
        employee=employee,
        period=period,
        policy=policy,
        level_mode=level_mode,
        candidates=candidates,
    )
    if base_level_mode == LevelMode.DISABLED and level_mode == LevelMode.COMMENT_ONLY and str(getattr(employee, 'ucuncu_yonetici_sicil', '') or '').strip():
        _append_issue_once(
            resolved,
            ChainIssue(code='level3_explicit_comment_mode', message='Seçili 3. amir bulunduğu için yorumcu modunda etkinleştirildi.', severity='info'),
        )
    single_manager_authority = bool(getattr(authority, "is_single_manager_case", False))

    for level, label in policy.labels.items():
        if single_manager_authority and level not in resolved.levels:
            continue
        if level == 3 and level_mode == LevelMode.DISABLED:
            continue
        if level in resolved.levels:
            existing = resolved.levels[level]
            if existing.evaluator_sicil:
                used_sicils.add(existing.evaluator_sicil)
            continue

        matched = None
        expected_roles = policy.expected_roles.get(level, ())
        for candidate in candidates:
            manager = candidate["user"]
            if not manager:
                continue
            sicil = str(candidate["sicil"])
            if sicil in used_sicils:
                continue
            if candidate["role_token"] in expected_roles:
                matched = candidate
                break
        if matched is None:
            fallback_field = policy.fallback_fields.get(level)
            matched = next(
                (
                    candidate
                    for candidate in candidates
                    if candidate["source_field"] == fallback_field and str(candidate["sicil"]) not in used_sicils
                ),
                None,
            )

        if matched is None or matched.get("user") is None:
            has_authority_level = False
            if authority:
                has_authority_level = bool(getattr(authority, f"manager_{level}_id", None))
            if has_authority_level:
                continue

            if level == 3:
                explicit_level3 = str(getattr(employee, "ucuncu_yonetici_sicil", "") or "").strip()
                # 3. amir opsiyoneldir; yalnızca kullanıcı üzerinde açıkça tanımlandıysa
                # veya authoritative zincir gerçekten seviye 3 çözüyorsa uyarı üret.
                if not explicit_level3:
                    continue
                severity = "info" if level_mode != LevelMode.SCORE_ENABLED else "warning"
            else:
                severity = "warning"

            _append_issue_once(
                resolved,
                ChainIssue(
                    code=f"level_{level}_missing",
                    message=f"{label} bulunamadı.",
                    severity=severity,
                    details={"employee_id": getattr(employee, "id", None), "level": level},
                ),
            )
            continue

        manager = matched["user"]
        manager_sicil = str(matched["sicil"])
        used_sicils.add(manager_sicil)
        if getattr(manager, "id", None) == getattr(employee, "id", None):
            _append_issue_once(
                resolved,
                ChainIssue(
                    code="self_manager",
                    message=f"{label} olarak personelin kendisi eşleşti.",
                    severity="error",
                    details={"level": level, "sicil": manager_sicil},
                ),
            )
            continue

        resolved.levels[level] = _make_chain_level(
            level=level,
            label=label,
            manager=manager,
            source_field=str(matched["source_field"]),
            level_mode=level_mode,
        )

    populated = [payload for payload in resolved.levels.values() if payload.evaluator_id]
    if len({payload.evaluator_id for payload in populated}) != len(populated):
        _append_issue_once(
            resolved,
            ChainIssue(code="duplicate_manager", message="Aynı kişi birden fazla amir seviyesine eşleşti.", severity="warning"),
        )

    # Hukuk amiri için slotlar 1=Başkan, 2=Başkan Yardımcısı olarak kalır;
    # işlem sırası ise 2 -> 1 olmalıdır. Bu çağrı yapılmazsa resolved.order
    # bazı veri setlerinde [1] kalabiliyor ve 2. amir formu açsa bile gönderim
    # sırasında "işlem sırası henüz gelmedi" blokajına düşüyor.
    _enforce_hukuk_presidency_order(resolved, employee)

    if 3 in resolved.levels and level_mode == LevelMode.COMMENT_ONLY:
        _append_issue_once(
            resolved,
            ChainIssue(code="level3_comment_only", message="3. amir yorumcu modunda çalışacak.", severity="info"),
        )

    return resolved


def build_chain_debug_payload(employee, period=None) -> dict[str, object]:
    resolved = build_resolved_chain(employee=employee, period=period)
    candidates = _collect_candidates(employee)
    return {
        "employee": {
            "id": getattr(employee, "id", None),
            "sicil_no": getattr(employee, "sicil_no", None),
            "full_name": getattr(employee, "full_name", None),
            "role": getattr(employee, "role", None),
            "unvan": getattr(employee, "unvan", None),
            "birim": getattr(employee, "birim", None),
            "ust_birim": getattr(employee, "ust_birim", None),
        },
        "explicit_manager_fields": {field: getattr(employee, field, None) for field in SOURCE_FIELDS},
        "candidates": [
            {
                "source_field": item["source_field"],
                "sicil": item["sicil"],
                "matched_user_id": getattr(item["user"], "id", None) if item["user"] else None,
                "matched_user_name": getattr(item["user"], "full_name", None) if item["user"] else None,
                "matched_role_token": item["role_token"],
            }
            for item in candidates
        ],
        "resolved_chain": resolved.to_dict(),
    }
