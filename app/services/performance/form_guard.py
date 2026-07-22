from __future__ import annotations

from typing import Any

from .policy_flags import is_level_2_comment_required_when_level_1_score_is_three


def build_form_guard_state(
    *,
    manager_level: int,
    requires_level_2_comment: bool,
    level_3_scoring_enabled: bool,
    evaluation_window: dict[str, Any] | None,
    workflow_status_label: str,
    saved: bool,
) -> dict[str, Any]:
    level_label = {1: '1. Amir', 2: '2. Amir', 3: '3. Amir'}.get(manager_level, 'Amir')
    window = evaluation_window or {}
    can_submit = bool(window.get('can_submit', True))

    rule_cards: list[dict[str, str]] = [
        {
            'title': 'Uç puan açıklaması',
            'body': '1 ve 5 puan verilen her kriterde açıklama zorunludur.',
            'tone': 'danger',
        },
        {
            'title': 'Genel görüş eşiği',
            'body': '70 altı ve 90 üstü sonuçlarda ayrıntılı genel görüş yazılmalıdır.',
            'tone': 'warning',
        },
    ]

    if (
        manager_level == 2
        and requires_level_2_comment
        and is_level_2_comment_required_when_level_1_score_is_three()
    ):
        rule_cards.append({
            'title': '3 puan açıklaması',
            'body': '1. amirin herhangi bir kriterde 3 vermesi halinde 2. amir genel görüş yazmalıdır.',
            'tone': 'warning',
        })

    if manager_level == 3:
        if level_3_scoring_enabled:
            rule_cards.append({
                'title': '3. amir modu',
                'body': 'Bu dönemde 3. amir puan verebilir; kayıt zincirde sonraki amiri açar.',
                'tone': 'info',
            })
        else:
            rule_cards.append({
                'title': '3. amir modu',
                'body': 'Bu dönemde 3. amir yalnızca üst görüş yazar; puan alanı kapalıdır.',
                'tone': 'info',
            })

    blockers: list[str] = []
    if not can_submit:
        if window.get('not_started'):
            blockers.append('Puanlama takvimi henüz başlamadığı için kayıt gönderilemez.')
        elif window.get('expired'):
            blockers.append('Puanlama takvimi sona erdiği için yeni kayıt açılamaz.')
        else:
            blockers.append('Puanlama takvimi şu an işlem kabul etmiyor.')

    return {
        'level_label': level_label,
        'workflow_status_label': workflow_status_label or '-',
        'saved': bool(saved),
        'can_submit': can_submit,
        'rule_cards': rule_cards,
        'blockers': blockers,
    }


def build_form_actions(
    *,
    manager_level: int,
    can_withdraw_level_1: bool,
    can_return_to_level_1: bool,
    level_3_scoring_enabled: bool,
    evaluation_window: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    can_submit = bool((evaluation_window or {}).get('can_submit', True))
    actions: list[dict[str, Any]] = [
        {
            'type': 'link',
            'kind': 'secondary',
            'icon': 'fa-solid fa-arrow-left',
            'label': 'Listeye Dön',
        },
        {
            'type': 'link',
            'kind': 'secondary',
            'icon': 'fa-solid fa-timeline',
            'label': 'Süreç Geçmişi',
        },
    ]

    if manager_level == 1:
        if can_return_to_level_1:
            actions.append({
                'type': 'submit',
                'kind': 'secondary',
                'icon': 'fa-solid fa-reply',
                'label': '2. Amire İade Et',
                'value': 'return_to_level_1',
                'disabled': not can_submit,
            })
        actions.extend([
            {
                'type': 'submit',
                'kind': 'secondary',
                'icon': 'fa-solid fa-floppy-disk',
                'label': 'Taslak Kaydet',
                'value': 'save',
                'disabled': not can_submit,
            },
            {
                'type': 'submit',
                'kind': 'primary',
                'icon': 'fa-solid fa-check',
                'label': 'Onayla ve Tamamla',
                'value': 'complete_level_2',
                'disabled': not can_submit,
            },
        ])
    elif manager_level == 2:
        actions.extend([
            {
                'type': 'submit',
                'kind': 'secondary',
                'icon': 'fa-solid fa-floppy-disk',
                'label': 'Taslak Kaydet',
                'value': 'save',
                'disabled': not can_submit,
            },
            {
                'type': 'submit',
                'kind': 'primary',
                'icon': 'fa-solid fa-paper-plane',
                'label': '1. Amire Gönder',
                'value': 'submit_to_level_2',
                'disabled': not can_submit,
            },
        ])
        if can_withdraw_level_1:
            actions.append({
                'type': 'submit',
                'kind': 'secondary',
                'icon': 'fa-solid fa-rotate-left',
                'label': 'Geri Çek',
                'value': 'withdraw_level_1',
                'disabled': not can_submit,
            })
    else:
        actions.append({
            'type': 'submit',
            'kind': 'primary',
            'icon': 'fa-solid fa-floppy-disk',
            'label': 'Kaydet ve Zinciri Aç' if level_3_scoring_enabled else 'Üst Görüşü Kaydet',
            'value': 'save_level_3',
            'disabled': not can_submit,
        })

    return actions


__all__ = ['build_form_guard_state', 'build_form_actions']
