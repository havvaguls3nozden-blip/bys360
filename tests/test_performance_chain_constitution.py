from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import cast

from app.services.hierarchy_rulebook_service import build_lookup, desired_manager_sicils
from app.services.performance.chain_rule_engine import (
    compute_flow_order,
    get_chain_rule_matrix_snapshot,
    resolve_authoritative_chain,
)
from app.services.performance.rules import get_authoritative_performance_rules_snapshot
from app.services.performance_v2.rules import (
    COORDINATOR_POLICY,
    GROUP_MANAGER_POLICY,
    GROUP_STAFF_POLICY,
)


def _user(**kwargs):
    base = dict(
        id=1,
        sicil_no='001',
        ad='Ada',
        soyad='Lovelace',
        full_name='',
        email='ada@example.com',
        role='personel',
        role_label='Personel',
        unvan='Uzman',
        birim='YAZILIM ÇALIŞMA GRUBU',
        ust_birim='BT GRUP BAŞKANLIĞI',
        yonetici_sicil='',
        ikinci_yonetici_sicil='',
        ucuncu_yonetici_sicil='',
        is_active=True,
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


def _people_for_rules():
    president = _user(id=90, sicil_no='090', role='baskan', role_label='Başkan', unvan='Başkan', birim='BAŞKANLIK', ust_birim='')
    vice = _user(id=20, sicil_no='020', role='baskan_yardimcisi', role_label='Başkan Yardımcısı', unvan='Başkan Yardımcısı', birim='BAŞKANLIK', ust_birim='')
    group_head = _user(id=30, sicil_no='030', role='grup_baskani', role_label='Grup Başkanı', unvan='Grup Başkanı', birim='BT GRUP BAŞKANLIĞI', ust_birim='BAŞKANLIK')
    coordinator = _user(id=10, sicil_no='010', role='koordinator', role_label='Koordinatör', unvan='Koordinatör', birim='YAZILIM ÇALIŞMA GRUBU', ust_birim='BT GRUP BAŞKANLIĞI')
    staff = _user(id=40, sicil_no='040', role='personel', role_label='Personel', unvan='Uzman', birim='YAZILIM ÇALIŞMA GRUBU', ust_birim='BT GRUP BAŞKANLIĞI')
    return president, vice, group_head, coordinator, staff


def test_group_staff_rulebook_slots_are_constitutional():
    president, vice, group_head, coordinator, staff = _people_for_rules()
    lookup = build_lookup([president, vice, group_head, coordinator, staff])

    chain = desired_manager_sicils(staff, lookup)

    assert chain.manager_1_sicil == '030'  # 1. Amir = Grup Başkanı
    assert chain.manager_2_sicil == '010'  # 2. Amir = Koordinatör
    assert chain.expected_levels == (1, 2)


def test_coordinator_rulebook_slots_are_constitutional():
    president, vice, group_head, coordinator, staff = _people_for_rules()
    lookup = build_lookup([president, vice, group_head, coordinator, staff])

    chain = desired_manager_sicils(coordinator, lookup)

    assert chain.manager_1_sicil == '020'  # 1. Amir = Başkan Yardımcısı
    assert chain.manager_2_sicil == '030'  # 2. Amir = Grup Başkanı
    assert chain.expected_levels == (1, 2)


def test_group_manager_rulebook_slots_are_constitutional():
    president, vice, group_head, coordinator, staff = _people_for_rules()
    lookup = build_lookup([president, vice, group_head, coordinator, staff])

    chain = desired_manager_sicils(group_head, lookup)

    assert chain.manager_1_sicil == '090'  # 1. Amir = Başkan
    assert chain.manager_2_sicil == '020'  # 2. Amir = Başkan Yardımcısı
    assert chain.expected_levels == (1, 2)


def test_central_rule_engine_returns_same_slots_and_flow():
    president, vice, group_head, coordinator, staff = _people_for_rules()
    resolved = resolve_authoritative_chain(staff, [president, vice, group_head, coordinator, staff])

    assert resolved.manager_1_sicil == '030'
    assert resolved.manager_2_sicil == '010'
    assert resolved.flow_order == (2, 1)

    staff.ucuncu_yonetici_sicil = '020'
    resolved_with_level3 = resolve_authoritative_chain(staff, [president, vice, group_head, coordinator, staff])
    assert resolved_with_level3.manager_3_sicil == '020'
    assert resolved_with_level3.flow_order == (3, 2, 1)


def test_flow_order_is_not_slot_order():
    assert compute_flow_order(manager_1_sicil='030', manager_2_sicil='010', manager_3_sicil=None) == (2, 1)
    assert compute_flow_order(manager_1_sicil='030', manager_2_sicil='010', manager_3_sicil='020') == (3, 2, 1)
    assert compute_flow_order(manager_1_sicil='090', manager_2_sicil=None, manager_3_sicil=None) == (1,)


def test_authoritative_snapshots_are_aligned():
    snapshot = get_authoritative_performance_rules_snapshot()
    engine = get_chain_rule_matrix_snapshot()

    authoritative_slot_matrix = cast(dict, snapshot['authoritative_slot_matrix'])
    assert authoritative_slot_matrix['coordinator'] == {'slot_1': 'baskan_yardimcisi', 'slot_2': 'grup_baskani'}
    assert authoritative_slot_matrix['group_staff'] == {'slot_1': 'grup_baskani', 'slot_2': 'koordinator', 'slot_3': 'birim_amiri_optional'}
    assert engine['slots']['group_manager'] == {1: 'baskan', 2: 'baskan_yardimcisi'}

    assert COORDINATOR_POLICY.labels[1] == 'Başkan Yardımcısı'
    assert COORDINATOR_POLICY.labels[2] == 'Grup Başkanı'
    assert COORDINATOR_POLICY.expected_roles[1] == ('baskan_yardimcisi',)
    assert COORDINATOR_POLICY.expected_roles[2] == ('grup_baskani', 'mali_musavir')

    assert GROUP_STAFF_POLICY.labels[1] == 'Grup Başkanı'
    assert GROUP_STAFF_POLICY.labels[2] == 'Koordinatör'
    assert GROUP_STAFF_POLICY.expected_roles[1] == ('grup_baskani', 'mali_musavir')
    assert GROUP_STAFF_POLICY.expected_roles[2] == ('koordinator',)

    assert GROUP_MANAGER_POLICY.labels[1] == 'Başkan'
    assert GROUP_MANAGER_POLICY.labels[2] == 'Başkan Yardımcısı'


def test_no_old_reversed_chain_tokens_remain_in_critical_services():
    root = Path(__file__).resolve().parents[1]
    haystack = '\n'.join(
        (root / rel).read_text(encoding='utf-8', errors='ignore')
        for rel in [
            'app/services/performance/assignments.py',
            'app/services/performance_v2/sync_service.py',
            'app/services/performance/chain_rule_engine.py',
            'app/services/performance/rules.py',
        ]
    ).lower()
    forbidden = [
        '1=koordinator, 2=grup baskani olarak sabitlendi',
        '1=koordinatör, 2=grup başkanı olarak sabitlendi',
        '1=grup baskani, 2=baskan yardimcisi olarak sabitlendi',
        '1=grup başkanı, 2=başkan yardımcısı olarak sabitlendi',
    ]
    for token in forbidden:
        assert token not in haystack
