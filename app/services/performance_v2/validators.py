from __future__ import annotations



from collections.abc import Iterable

from .policy_flags import score_requires_criterion_comment


def _as_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def validate_period_ready(period, *, allow_locked: bool = False) -> list[str]:
    """Backward-compatible readiness guard used by sync services.

    Default behavior stays strict: inactive or locked periods are blocked.
    Faz B adds the optional ``allow_locked`` flag so audit/report tools can
    inspect a locked period without being treated as a hard blocker.
    """
    issues: list[str] = []
    if not period:
        issues.append('Aktif dönem bulunamadı.')
        return issues
    if not getattr(period, 'is_active', False):
        issues.append('Seçilen dönem aktif değil.')
    if getattr(period, 'is_locked', False) and not allow_locked:
        issues.append('Seçilen dönem kilitli.')
    return issues


def validate_weight_configuration(period) -> list[str]:
    issues: list[str] = []
    if not period:
        return ['Dönem bulunamadı.']

    level_1 = _as_float(getattr(period, 'level_1_weight', 50.0), 50.0)
    level_2 = _as_float(getattr(period, 'level_2_weight', 50.0), 50.0)
    level_3 = _as_float(getattr(period, 'level_3_weight', 0.0), 0.0)
    total = round(level_1 + level_2 + level_3, 2)

    if any(weight < 0 for weight in (level_1, level_2, level_3)):
        issues.append('Amir ağırlıkları negatif olamaz.')
    if round(total, 2) != 100.00:
        issues.append(f'Amir ağırlıkları toplamı 100 olmalı. Mevcut toplam: {total:.2f}')

    level_3_enabled = bool(getattr(period, 'enable_level_3', False))
    level_3_scoring = bool(getattr(period, 'enable_level_3_scoring', False)) or str(getattr(period, 'level_3_mode', '')).strip().lower() == 'scoring'

    if not level_3_enabled and level_3 != 0.0:
        issues.append('3. amir kapalıyken 3. amir ağırlığı 0 olmalı.')
    if level_3_enabled and not level_3_scoring and level_3 != 0.0:
        issues.append('3. amir sadece yorumcu modundaysa ağırlığı 0 olmalı.')
    if not level_3_enabled and (round(level_1, 2), round(level_2, 2), round(level_3, 2)) != (50.0, 50.0, 0.0):
        issues.append('Varsayılan iki amirli yapı 50 / 50 / 0 olmalı.')
    return issues


def validate_single_active_period(periods: Iterable[object]) -> list[str]:
    active_periods = [item for item in periods if bool(getattr(item, 'is_active', False))]
    if len(active_periods) <= 1:
        return []
    labels = ', '.join(str(getattr(item, 'title', getattr(item, 'id', '?'))) for item in active_periods)
    return [f'Aynı anda birden fazla aktif dönem var: {labels}']


def validate_publish_guard(period, evaluations: Iterable[object] | None = None) -> list[str]:
    issues: list[str] = []
    if not period:
        return ['Dönem bulunamadı.']

    if getattr(period, 'results_published', False) and not getattr(period, 'is_locked', False):
        issues.append('Sonuçları yayımlanmış dönem kilitli değil. Yayın sonrası dönem kilitlenmeli.')

    if evaluations is None:
        return issues

    period_published = bool(getattr(period, 'results_published', False))
    published_without_period = [
        item for item in evaluations
        if bool(getattr(item, 'is_published_to_employee', False)) and not period_published
    ]
    if published_without_period:
        issues.append(
            'Dönem sonuçları yayımlanmadan personele açık değerlendirme kayıtları bulundu: '
            f'{len(published_without_period)} adet'
        )
    return issues


def validate_score_comment_rules(*, raw_score: float | int | None, score_100: float | int | None = None, general_comment: str | None = None) -> list[str]:
    issues: list[str] = []
    comment = (general_comment or '').strip()
    normalized_raw = None
    try:
        normalized_raw = int(float(raw_score)) if raw_score is not None else None
    except (TypeError, ValueError):
        normalized_raw = None
    score100 = _as_float(score_100, 0.0)

    if score_requires_criterion_comment(normalized_raw) and not comment:
        issues.append('Bu puan için sistem ayarında açıklama zorunluluğu aktiftir.')
    if (score100 < 70.0 or score100 > 90.0) and not comment:
        issues.append('70 altı ve 90 üstü sonuçlarda genel görüş zorunlu.')
    return issues


def build_period_validation_report(period, *, all_periods: Iterable[object] | None = None, evaluations: Iterable[object] | None = None) -> dict[str, object]:
    issues: list[str] = []
    issues.extend(validate_period_ready(period, allow_locked=True))
    issues.extend(validate_weight_configuration(period))
    issues.extend(validate_publish_guard(period, evaluations=evaluations))
    if all_periods is not None:
        issues.extend(validate_single_active_period(all_periods))

    return {
        'period_id': getattr(period, 'id', None),
        'period_title': getattr(period, 'title', None),
        'is_active': bool(getattr(period, 'is_active', False)),
        'is_locked': bool(getattr(period, 'is_locked', False)),
        'results_published': bool(getattr(period, 'results_published', False)),
        'weights': {
            'level_1': _as_float(getattr(period, 'level_1_weight', 50.0), 50.0),
            'level_2': _as_float(getattr(period, 'level_2_weight', 50.0), 50.0),
            'level_3': _as_float(getattr(period, 'level_3_weight', 0.0), 0.0),
        },
        'issue_count': len(issues),
        'issues': issues,
    }