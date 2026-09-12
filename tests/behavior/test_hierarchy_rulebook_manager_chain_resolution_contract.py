from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services.hierarchy_rulebook_service import (
    Lookup,
    build_lookup,
    desired_manager_sicils,
    find_coordinator,
    find_group_head,
    find_hukuk_chief,
    find_hukuk_supervisor,
    infer_role_from_profile,
    is_direct_to_president_role,
    is_hukuk_chief,
    is_hukuk_staff,
    is_president,
    is_system_user,
    is_vice_president,
    resolve_explicit_level3,
)
from app.services.personnel_sync_service import canonical_role_value


def _user(**kwargs):
    base = dict(
        id=1,
        sicil_no='001',
        ad='Ad',
        soyad='Soyad',
        full_name='',
        email='user@example.com',
        role='personel',
        role_label='Personel',
        unvan='Uzman',
        birim='Yazılım Çalışma Grubu',
        ust_birim='BT Grup Başkanlığı',
        yonetici_sicil='',
        ikinci_yonetici_sicil='',
        ucuncu_yonetici_sicil='',
        is_active=True,
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


def _bare_lookup(by_sicil):
    return Lookup(
        users=[],
        by_sicil=by_sicil,
        by_role={},
        by_unit_role={},
        by_unit_parent_role={},
        president=None,
        vice_president=None,
    )


def _base_people():
    president = _user(
        id=90, sicil_no='090', role='baskan', role_label='Başkan', unvan='Başkan',
        birim='Başkanlık', ust_birim='',
    )
    vice = _user(
        id=91, sicil_no='091', role='baskan_yardimcisi', role_label='Başkan Yardımcısı',
        unvan='Başkan Yardımcısı', birim='Başkanlık', ust_birim='',
    )
    return president, vice


# ---------------------------------------------------------------------------
# is_system_user
# ---------------------------------------------------------------------------


def test_is_system_user_none_is_treated_as_system():
    assert is_system_user(None) is True


@pytest.mark.parametrize(
    'overrides',
    [
        dict(role='admin'),
        dict(role_label='Admin'),
        dict(role_label='Sistem Yöneticisi'),
        dict(role_label='SİSTEM YÖNETİCİSİ'),  # Turkish upper-case diacritics normalize the same
        dict(role_label='System Admin'),
        dict(role_label='System Administrator'),
        dict(role_label='Super Admin'),
        dict(role_label='SuperAdmin'),
        dict(unvan='Sistem Yöneticisi'),
        dict(unvan='System Admin'),
        dict(unvan='System Administrator'),
        dict(email='admin@example.com'),
        dict(email='system@example.com'),
        dict(email='sysadmin@example.com'),
        dict(sicil_no='admin'),
        dict(sicil_no='system'),
        dict(sicil_no='sysadmin'),
        dict(birim='BYS360'),
        dict(ust_birim='bys360'),
    ],
    ids=lambda overrides: '|'.join(f'{k}={v}' for k, v in overrides.items()),
)
def test_is_system_user_detects_every_signal(overrides):
    base = dict(
        role='personel', role_label='Personel', unvan='Uzman',
        email='ok@example.com', sicil_no='777', birim='Genel', ust_birim='Ust',
    )
    base.update(overrides)
    assert is_system_user(_user(**base)) is True


def test_is_system_user_false_for_regular_staff():
    assert is_system_user(_user(role='personel', role_label='Personel', unvan='Uzman')) is False


def test_is_system_user_handles_sparse_object_without_crashing():
    sparse = SimpleNamespace(role='personel')
    assert is_system_user(sparse) is False


# ---------------------------------------------------------------------------
# is_president / is_vice_president
# ---------------------------------------------------------------------------


def test_is_president_true_via_role_field():
    assert is_president(_user(role='baskan', unvan='Genel Müdür')) is True


@pytest.mark.parametrize('title', ['Başkan', 'BAŞKAN', 'baskan'])
def test_is_president_true_via_exact_title_regardless_of_role_and_case(title):
    assert is_president(_user(role='personel', unvan=title)) is True


def test_is_president_false_for_vice_president_title():
    # Title contains the substring 'baskan' but is not an exact 'baskan' title,
    # so it must not be misclassified as the president.
    assert is_president(_user(role='baskan_yardimcisi', unvan='Başkan Yardımcısı')) is False


@pytest.mark.parametrize('title', ['Başkan Yardımcısı', 'BAŞKAN YARDIMCISI (Vekil)', 'başkan yardımcısı'])
def test_is_vice_president_detects_title_variants(title):
    assert is_vice_president(_user(role='personel', unvan=title)) is True


def test_is_vice_president_role_field_alone_is_sufficient():
    assert is_vice_president(_user(role='baskan_yardimcisi', unvan='Uzman')) is True


def test_is_vice_president_false_for_plain_president():
    assert is_vice_president(_user(role='baskan', unvan='Başkan')) is False


# ---------------------------------------------------------------------------
# is_hukuk_chief / is_hukuk_staff
# ---------------------------------------------------------------------------


def _hukuk_chief_user(**overrides):
    base = dict(
        role='mali_musavir', role_label='Mali Müşavir', unvan='Sorumlu Hukuk Müşaviri',
        birim='Hukuk Müşavirliği', ust_birim='Başkanlık',
        yonetici_sicil='', ikinci_yonetici_sicil='', ucuncu_yonetici_sicil='',
    )
    base.update(overrides)
    return _user(**base)


def test_is_hukuk_chief_true_for_sorumlu_title_without_supervisor_hint():
    assert is_hukuk_chief(_hukuk_chief_user()) is True


def test_is_hukuk_chief_true_for_plain_hukuk_role_without_hint():
    user = _hukuk_chief_user(unvan='Hukuk Müşaviri', role='mali_musavir')
    assert is_hukuk_chief(user) is True


def test_is_hukuk_chief_false_when_explicit_supervisor_hint_present():
    # An explicit üst (manager) sicil on the card demotes this record to staff,
    # even though the title/role otherwise looks like a chief.
    user = _hukuk_chief_user(yonetici_sicil='777')
    assert is_hukuk_chief(user) is False
    assert is_hukuk_staff(user) is True


def test_is_hukuk_chief_false_outside_hukuk_context():
    user = _user(role='mali_musavir', unvan='Mali Müşavir', birim='Muhasebe', ust_birim='Başkanlık')
    assert is_hukuk_chief(user) is False


def test_is_hukuk_staff_true_for_plain_hukuk_personnel():
    user = _user(role='personel', unvan='Hukuk Uzmanı', birim='Hukuk Müşavirliği', ust_birim='Başkanlık')
    assert is_hukuk_staff(user) is True
    assert is_hukuk_chief(user) is False


def test_is_hukuk_staff_false_for_president_or_vice_in_hukuk_context():
    president = _user(role='baskan', unvan='Başkan', birim='Hukuk Müşavirliği', ust_birim='')
    vice = _user(role='baskan_yardimcisi', unvan='Başkan Yardımcısı', birim='Hukuk Müşavirliği', ust_birim='')
    assert is_hukuk_staff(president) is False
    assert is_hukuk_staff(vice) is False


def test_hukuk_predicates_handle_none_user():
    assert is_hukuk_chief(None) is False
    assert is_hukuk_staff(None) is False


# ---------------------------------------------------------------------------
# is_direct_to_president_role
# ---------------------------------------------------------------------------


@pytest.mark.parametrize('unvan', ['Danışman', 'Özel Kalem Müdürü', 'İç Denetçi', 'İç Denetim Uzmanı'])
def test_is_direct_to_president_role_title_signals(unvan):
    user = _user(role='personel', unvan=unvan, birim='Genel', ust_birim='Başkanlık')
    assert is_direct_to_president_role(user) is True


@pytest.mark.parametrize(
    'field,value',
    [('birim', 'Danışmanlık'), ('birim', 'Özel Kalem'), ('birim', 'İç Denetim'), ('ust_birim', 'İç Denetim')],
)
def test_is_direct_to_president_role_unit_signals(field, value):
    base = dict(role='personel', unvan='Uzman', birim='Genel', ust_birim='Başkanlık')
    base[field] = value
    assert is_direct_to_president_role(_user(**base)) is True


def test_is_direct_to_president_role_false_for_regular_staff():
    user = _user(role='personel', unvan='Uzman', birim='Yazılım Çalışma Grubu', ust_birim='BT Grup Başkanlığı')
    assert is_direct_to_president_role(user) is False


def test_is_direct_to_president_role_none_user_is_false():
    assert is_direct_to_president_role(None) is False


# ---------------------------------------------------------------------------
# infer_role_from_profile
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    'raw_role,expected_value,expected_label',
    [
        ('admin', 'admin', 'Admin'),
        ('Başkan', 'baskan', 'Başkan'),
        ('BASKAN_YARDIMCISI', 'baskan_yardimcisi', 'Başkan Yardımcısı'),
        ('Grup Başkanı', 'grup_baskani', 'Grup Başkanı'),
        ('mali_musavir', 'mali_musavir', 'Mali Müşavir'),
        ('Koordinatör', 'koordinator', 'Koordinatör'),
        ('Birim Sorumlusu', 'birim_sorumlusu', 'Birim Sorumlusu'),
        ('personel', 'personel', 'Personel'),
    ],
)
def test_infer_role_from_profile_role_field_short_circuits_title_checks(raw_role, expected_value, expected_label):
    # unvan deliberately contradicts raw_role to prove the role branch wins outright.
    value, label = infer_role_from_profile(raw_role=raw_role, unvan='Should Not Matter', birim='X', ust_birim='Y')
    assert (value, label) == (expected_value, expected_label)


def test_infer_role_from_profile_title_exact_baskan_branch():
    value, label = infer_role_from_profile(raw_role='', unvan='Başkan', birim='Başkanlık', ust_birim='')
    assert (value, label) == ('baskan', 'Başkan')


def test_infer_role_from_profile_title_exact_baskan_yardimcisi_branch():
    value, label = infer_role_from_profile(raw_role=None, unvan='Başkan Yardımcısı', birim='Başkanlık', ust_birim='')
    assert (value, label) == ('baskan_yardimcisi', 'Başkan Yardımcısı')


def test_infer_role_from_profile_title_exact_grup_baskani_branch():
    # BYS360 DEFECT FS (Final Sweep FS-R1): this exact title was previously
    # unreachable -- any title containing "Grup Başkanı" also contains the
    # substring "baskan" without "yardim", so it was always intercepted
    # earlier by the (now-fixed) 'baskan' substring branch and misclassified
    # as the president role. Now reachable and correctly classified.
    value, label = infer_role_from_profile(raw_role=None, unvan='Grup Başkanı', birim='', ust_birim='')
    assert (value, label) == ('grup_baskani', 'Grup Başkanı')


@pytest.mark.parametrize(
    'unvan',
    [
        'Başkanlık Danışmanı',
        'Genel Başkan',
    ],
)
def test_infer_role_from_profile_title_containing_baskan_without_exact_match_does_not_become_president(unvan):
    # BYS360 DEFECT FS (Final Sweep FS-R1): titles that merely *contain*
    # "başkan" as a substring/modifier (advisor to the presidency, or a
    # non-canonical "Genel Başkan" variant) previously escalated to the
    # literal president role via 'baskan' in title. Fixed: exact match only.
    value, _label = infer_role_from_profile(raw_role=None, unvan=unvan, birim='', ust_birim='')
    assert value != 'baskan', (unvan, value)


def test_infer_role_from_profile_title_containing_baskan_yardim_without_exact_match_does_not_become_vice_president():
    # BYS360 DEFECT FS (Final Sweep FS-R1): a private-office specialist title
    # under the vice-presidency, not the vice president themselves.
    value, _label = infer_role_from_profile(
        raw_role=None, unvan='Başkan Yardımcılığı Özel Kalem Uzmanı', birim='', ust_birim='',
    )
    assert value != 'baskan_yardimcisi', value


def test_infer_role_from_profile_title_containing_grup_baskan_without_exact_match_does_not_become_grup_baskani():
    # BYS360 DEFECT FS (Final Sweep FS-R1): a data analyst working within a
    # "Grup Başkanlığı" department, not its head.
    value, _label = infer_role_from_profile(
        raw_role=None, unvan='Grup Başkanlığı Veri Analisti', birim='', ust_birim='',
    )
    assert value not in ('baskan', 'grup_baskani'), value


def test_infer_role_from_profile_title_qualifier_suffix_no_longer_exact_matches_baskan_yardimcisi():
    # A qualifier suffix ("(Vekil)" = acting/deputy) means this is no longer
    # the exact canonical "Başkan Yardımcısı" phrase, so it must not
    # auto-escalate either -- exact-phrase matching intentionally has no
    # tolerance for surrounding qualifier text.
    value, _label = infer_role_from_profile(
        raw_role=None, unvan='Başkan Yardımcısı (Vekil)', birim='Başkanlık', ust_birim='',
    )
    assert value != 'baskan_yardimcisi', value


@pytest.mark.parametrize(
    'unvan',
    [
        'Başkanlık Danışmanı',
        'Grup Başkanlığı Veri Analisti',
        'Başkan Yardımcılığı Özel Kalem Uzmanı',
        'Genel Başkan',
    ],
)
def test_infer_role_from_profile_import_persistence_path_never_persists_false_positive_privileged_role(unvan):
    """BYS360 DEFECT FS (Final Sweep FS-R1): reproduces the exact production
    persistence chain used by the bulk personnel import
    (app/admin/ops_import_services.py) and the admin user create/edit route
    (app/admin/routes.py) -- ``infer_role_from_profile()`` followed by
    ``canonical_role_value(raw_role or inferred_role or "personel")`` -- with
    a blank raw_role and a free-text title known to previously collide.
    Proves the value that would actually be written to User.role is never
    one of the three top-leadership roles for a non-leadership title."""
    raw_role = ''
    inferred_role, _inferred_role_label = infer_role_from_profile(raw_role=None, unvan=unvan, birim=None, ust_birim=None)
    persisted_role = canonical_role_value(raw_role or inferred_role or 'personel')
    assert persisted_role not in {'baskan', 'baskan_yardimcisi', 'grup_baskani'}, (unvan, persisted_role)


def test_infer_role_from_profile_direct_to_president_title_branch():
    value, label = infer_role_from_profile(raw_role=None, unvan='Danışman', birim='Genel', ust_birim='Başkanlık')
    assert (value, label) == ('birim_sorumlusu', 'Birim Sorumlusu')


def test_infer_role_from_profile_direct_to_president_unit_branch():
    # Title alone gives no signal; only the unit membership triggers this branch.
    value, label = infer_role_from_profile(raw_role=None, unvan='Uzman', birim='İç Denetim', ust_birim='Başkanlık')
    assert (value, label) == ('birim_sorumlusu', 'Birim Sorumlusu')


def test_infer_role_from_profile_hukuk_title_branch():
    value, label = infer_role_from_profile(raw_role=None, unvan='Hukuk Müşaviri', birim='Genel', ust_birim='Başkanlık')
    assert (value, label) == ('mali_musavir', 'Mali Müşavir')


def test_infer_role_from_profile_grup_baskani_unit_branch():
    # Title is generic; only the unit's "... Grup Başkanlığı" suffix triggers this branch.
    value, label = infer_role_from_profile(raw_role=None, unvan='Uzman', birim='BT Grup Başkanlığı', ust_birim='Başkanlık')
    assert (value, label) == ('grup_baskani', 'Grup Başkanı')


def test_infer_role_from_profile_koordinator_title_branch():
    value, label = infer_role_from_profile(raw_role=None, unvan='Saha Koordinatörü', birim='Saha Ekibi', ust_birim='BT Grup Başkanlığı')
    assert (value, label) == ('koordinator', 'Koordinatör')


def test_infer_role_from_profile_work_group_staff_matrix_branch():
    value, label = infer_role_from_profile(
        raw_role=None, unvan='Uzman', birim='Yazılım Çalışma Grubu', ust_birim='BT Grup Başkanlığı',
    )
    assert (value, label) == ('personel', 'Personel')


def test_infer_role_from_profile_all_missing_falls_back_to_personel_default():
    value, label = infer_role_from_profile(raw_role=None, unvan=None, birim=None, ust_birim=None)
    assert (value, label) == ('personel', 'Personel')


# ---------------------------------------------------------------------------
# build_lookup
# ---------------------------------------------------------------------------


def test_build_lookup_excludes_inactive_and_system_users_from_pool():
    president = _user(id=1, sicil_no='001', role='baskan', unvan='Başkan', is_active=True)
    inactive_staff = _user(id=2, sicil_no='002', role='personel', unvan='Uzman', is_active=False)
    admin_user = _user(id=3, sicil_no='003', role='admin', unvan='Sistem Yöneticisi', is_active=True)
    active_staff = _user(id=4, sicil_no='004', role='personel', unvan='Uzman', is_active=True)

    lookup = build_lookup([president, inactive_staff, admin_user, active_staff])

    assert '002' not in lookup.by_sicil
    assert '003' not in lookup.by_sicil
    assert '004' in lookup.by_sicil
    assert {u.sicil_no for u in lookup.users} == {'001', '004'}


def test_build_lookup_resolves_president_and_vice_president():
    president = _user(id=1, sicil_no='001', role='baskan', role_label='Başkan', unvan='Başkan')
    vice = _user(id=2, sicil_no='002', role='baskan_yardimcisi', role_label='Başkan Yardımcısı', unvan='Başkan Yardımcısı')
    staff = _user(id=3, sicil_no='003', role='personel', unvan='Uzman')

    lookup = build_lookup([president, vice, staff])

    assert lookup.president is not None
    assert lookup.vice_president is not None
    assert lookup.president.sicil_no == '001'
    assert lookup.vice_president.sicil_no == '002'


def test_build_lookup_president_absent_when_only_inactive_candidate_exists():
    inactive_president = _user(id=1, sicil_no='001', role='baskan', unvan='Başkan', is_active=False)
    staff = _user(id=2, sicil_no='002', role='personel', unvan='Uzman')

    lookup = build_lookup([inactive_president, staff])

    assert lookup.president is None


# ---------------------------------------------------------------------------
# tie-break determinism (find_group_head exercises the internal _pick_first)
# ---------------------------------------------------------------------------


def test_candidate_tie_break_by_full_name_is_deterministic_across_calls():
    ust = 'BT Grup Başkanlığı'
    candidate_a = _user(id=10, sicil_no='101', full_name='Ahmet Yilmaz', role='grup_baskani', unvan='Grup Başkanı', birim=ust, ust_birim='Başkanlık')
    candidate_b = _user(id=11, sicil_no='102', full_name='Zeynep Kaya', role='grup_baskani', unvan='Grup Başkanı', birim=ust, ust_birim='Başkanlık')
    staff = _user(id=20, sicil_no='201', role='personel', unvan='Uzman', birim='Yazılım Çalışma Grubu', ust_birim=ust)

    lookup = build_lookup([candidate_a, candidate_b, staff])

    first_pick = find_group_head(staff, lookup)
    second_pick = find_group_head(staff, lookup)

    assert first_pick is not None
    assert second_pick is not None
    assert first_pick.sicil_no == '101'  # alphabetically first full_name wins the tie
    assert second_pick.sicil_no == first_pick.sicil_no  # deterministic across repeated calls


def test_candidate_tie_break_by_sicil_when_names_match():
    ust = 'BT Grup Başkanlığı'
    candidate_a = _user(id=10, sicil_no='200', full_name='Ayşe Demir', role='grup_baskani', unvan='Grup Başkanı', birim=ust, ust_birim='Başkanlık')
    candidate_b = _user(id=11, sicil_no='100', full_name='Ayşe Demir', role='grup_baskani', unvan='Grup Başkanı', birim=ust, ust_birim='Başkanlık')
    staff = _user(id=20, sicil_no='201', role='personel', unvan='Uzman', birim='Yazılım Çalışma Grubu', ust_birim=ust)

    lookup = build_lookup([candidate_a, candidate_b, staff])

    picked_first = find_group_head(staff, lookup)
    picked_second = find_group_head(staff, lookup)

    assert picked_first is not None
    assert picked_second is not None
    assert picked_first.sicil_no == '100'
    assert picked_second.sicil_no == '100'


def test_find_group_head_returns_none_when_user_has_no_parent_unit():
    staff = _user(id=1, sicil_no='001', ust_birim='')
    lookup = build_lookup([staff])
    assert find_group_head(staff, lookup) is None


def test_find_coordinator_returns_none_when_no_candidates():
    staff = _user(id=1, sicil_no='001', birim='Yazılım Çalışma Grubu', ust_birim='BT Grup Başkanlığı')
    lookup = build_lookup([staff])
    assert find_coordinator(staff, lookup) is None


# ---------------------------------------------------------------------------
# find_hukuk_chief / find_hukuk_supervisor
# ---------------------------------------------------------------------------


def test_find_hukuk_chief_prefers_unit_scoped_match_over_a_remote_chief():
    unit_chief = _user(id=1, sicil_no='301', role='mali_musavir', unvan='Hukuk Müşaviri', birim='Hukuk Müşavirliği', ust_birim='Başkanlık')
    remote_chief = _user(id=2, sicil_no='302', role='grup_baskani', unvan='Sorumlu Hukuk Müşaviri', birim='Uzak Hukuk Birimi', ust_birim='Başkanlık')
    staff = _user(id=3, sicil_no='303', role='personel', unvan='Hukuk Uzmanı', birim='Hukuk Müşavirliği', ust_birim='Başkanlık')

    lookup = build_lookup([unit_chief, remote_chief, staff])

    chief = find_hukuk_chief(staff, lookup)

    assert chief is not None
    assert chief.sicil_no == '301'


def test_find_hukuk_chief_falls_back_to_global_search_when_no_unit_match():
    remote_chief = _user(id=1, sicil_no='301', role='mali_musavir', unvan='Hukuk Müşaviri', birim='Merkez Hukuk', ust_birim='Başkanlık')
    staff = _user(id=2, sicil_no='302', role='personel', unvan='Hukuk Uzmanı', birim='Şube Hukuk Bürosu', ust_birim='Bölge Müdürlüğü')

    lookup = build_lookup([remote_chief, staff])

    chief = find_hukuk_chief(staff, lookup)

    assert chief is not None
    assert chief.sicil_no == '301'


def test_find_hukuk_chief_excludes_self_reference():
    solo_chief = _user(id=1, sicil_no='301', role='mali_musavir', unvan='Hukuk Müşaviri', birim='Hukuk Müşavirliği', ust_birim='Başkanlık')

    lookup = build_lookup([solo_chief])

    # A hukuk chief cannot resolve to itself when it is the only candidate.
    assert find_hukuk_chief(solo_chief, lookup) is None


def test_find_hukuk_supervisor_uses_first_valid_hint_field():
    valid_supervisor = _user(id=1, sicil_no='401', role='mali_musavir', unvan='Sorumlu Hukuk Müşaviri', birim='Hukuk Müşavirliği', ust_birim='Başkanlık')
    staff = _user(
        id=2, sicil_no='402', role='personel', unvan='Hukuk Uzmanı', birim='Hukuk Müşavirliği', ust_birim='Başkanlık',
        yonetici_sicil='401',
    )

    lookup = build_lookup([valid_supervisor, staff])

    supervisor = find_hukuk_supervisor(staff, lookup)

    assert supervisor is not None
    assert supervisor.sicil_no == '401'


def test_find_hukuk_supervisor_skips_invalid_hint_and_tries_next_field():
    valid_supervisor = _user(id=1, sicil_no='401', role='mali_musavir', unvan='Sorumlu Hukuk Müşaviri', birim='Hukuk Müşavirliği', ust_birim='Başkanlık')
    staff = _user(
        id=2, sicil_no='402', role='personel', unvan='Hukuk Uzmanı', birim='Hukuk Müşavirliği', ust_birim='Başkanlık',
        yonetici_sicil='999999',  # does not resolve to any known user
        ikinci_yonetici_sicil='401',
    )

    lookup = build_lookup([valid_supervisor, staff])

    supervisor = find_hukuk_supervisor(staff, lookup)

    assert supervisor is not None
    assert supervisor.sicil_no == '401'


def test_find_hukuk_supervisor_none_outside_hukuk_context():
    plain_staff = _user(id=1, sicil_no='500', role='personel', unvan='Uzman', birim='Muhasebe', ust_birim='Başkanlık', yonetici_sicil='999')
    lookup = build_lookup([plain_staff])

    assert find_hukuk_supervisor(plain_staff, lookup) is None


def test_find_hukuk_supervisor_none_when_no_hint_fields_set():
    chief = _user(id=1, sicil_no='401', role='mali_musavir', unvan='Sorumlu Hukuk Müşaviri', birim='Hukuk Müşavirliği', ust_birim='Başkanlık')
    lookup = build_lookup([chief])

    assert find_hukuk_supervisor(chief, lookup) is None


# ---------------------------------------------------------------------------
# resolve_explicit_level3 — four independent rejection reasons + acceptance
# ---------------------------------------------------------------------------


def test_resolve_explicit_level3_accepts_valid_distinct_candidate():
    user = _user(id=1, sicil_no='001')
    candidate = _user(id=2, sicil_no='777', is_active=True, role='personel')
    lookup = _bare_lookup({'777': candidate})

    result = resolve_explicit_level3(user, lookup, '777', desired_1='030', desired_2='010')

    assert result == '777'


def test_resolve_explicit_level3_rejects_empty_or_missing_current_sicil():
    user = _user(id=1, sicil_no='001')
    lookup = _bare_lookup({})

    assert resolve_explicit_level3(user, lookup, '', desired_1=None, desired_2=None) is None
    assert resolve_explicit_level3(user, lookup, None, desired_1=None, desired_2=None) is None


def test_resolve_explicit_level3_rejects_unknown_sicil():
    user = _user(id=1, sicil_no='001')
    lookup = _bare_lookup({})

    assert resolve_explicit_level3(user, lookup, '999', desired_1=None, desired_2=None) is None


def test_resolve_explicit_level3_rejects_inactive_candidate():
    user = _user(id=1, sicil_no='001')
    inactive_candidate = _user(id=2, sicil_no='777', is_active=False)
    lookup = _bare_lookup({'777': inactive_candidate})

    assert resolve_explicit_level3(user, lookup, '777', desired_1=None, desired_2=None) is None


def test_resolve_explicit_level3_rejects_system_candidate():
    user = _user(id=1, sicil_no='001')
    system_candidate = _user(id=2, sicil_no='777', is_active=True, role='admin')
    lookup = _bare_lookup({'777': system_candidate})

    assert resolve_explicit_level3(user, lookup, '777', desired_1=None, desired_2=None) is None


def test_resolve_explicit_level3_rejects_self_reference():
    user = _user(id=1, sicil_no='777')
    self_as_candidate = _user(id=1, sicil_no='777')  # same id as user -> _same_user match
    lookup = _bare_lookup({'777': self_as_candidate})

    assert resolve_explicit_level3(user, lookup, '777', desired_1=None, desired_2=None) is None


@pytest.mark.parametrize('desired_1,desired_2', [('030', '010'), ('010', '030')])
def test_resolve_explicit_level3_rejects_duplicate_of_existing_slot(desired_1, desired_2):
    user = _user(id=1, sicil_no='001')
    candidate = _user(id=2, sicil_no='030')
    lookup = _bare_lookup({'030': candidate})

    assert resolve_explicit_level3(user, lookup, '030', desired_1=desired_1, desired_2=desired_2) is None


# ---------------------------------------------------------------------------
# desired_manager_sicils — top-level rulebook contract
# ---------------------------------------------------------------------------


def test_desired_manager_sicils_excludes_president_from_the_chain():
    president, vice = _base_people()
    lookup = build_lookup([president, vice])

    chain = desired_manager_sicils(president, lookup)

    assert chain.rule_code == 'president_excluded'
    assert chain.manager_1_sicil is None
    assert chain.manager_2_sicil is None
    assert chain.manager_3_sicil is None
    assert chain.expected_levels == ()
    assert chain.info_notes


def test_desired_manager_sicils_vice_president_reports_to_president():
    president, vice = _base_people()
    lookup = build_lookup([president, vice])

    chain = desired_manager_sicils(vice, lookup)

    assert chain.rule_code == 'vice_president_single'
    assert chain.manager_1_sicil == '090'
    assert chain.expected_levels == (1,)
    assert not chain.warnings


def test_desired_manager_sicils_vice_president_warns_when_no_president_exists():
    _, vice = _base_people()
    lookup = build_lookup([vice])

    chain = desired_manager_sicils(vice, lookup)

    assert chain.manager_1_sicil is None
    assert chain.warnings


def test_desired_manager_sicils_direct_president_role_resolves_single_slot():
    president, vice = _base_people()
    advisor = _user(id=50, sicil_no='050', role='personel', unvan='Danışman', birim='Danışmanlık', ust_birim='Başkanlık')

    lookup = build_lookup([president, vice, advisor])
    chain = desired_manager_sicils(advisor, lookup)

    assert chain.rule_code == 'direct_president_single'
    assert chain.manager_1_sicil == '090'
    assert chain.expected_levels == (1,)


def test_desired_manager_sicils_hukuk_chief_reports_to_president_and_vice():
    president, vice = _base_people()
    chief = _user(id=60, sicil_no='060', role='mali_musavir', unvan='Sorumlu Hukuk Müşaviri', birim='Hukuk Müşavirliği', ust_birim='Başkanlık')

    lookup = build_lookup([president, vice, chief])
    chain = desired_manager_sicils(chief, lookup)

    assert chain.rule_code == 'hukuk_chief_presidency_override'
    assert chain.manager_1_sicil == '090'
    assert chain.manager_2_sicil == '091'
    assert chain.expected_levels == (1, 2)


def test_desired_manager_sicils_hukuk_staff_without_hint_uses_generic_chief_lookup():
    president, vice = _base_people()
    chief = _user(id=60, sicil_no='060', role='mali_musavir', unvan='Sorumlu Hukuk Müşaviri', birim='Hukuk Müşavirliği', ust_birim='Başkanlık')
    staff = _user(id=61, sicil_no='061', role='personel', unvan='Hukuk Uzmanı', birim='Hukuk Müşavirliği', ust_birim='Başkanlık')

    lookup = build_lookup([president, vice, chief, staff])
    chain = desired_manager_sicils(staff, lookup)

    assert chain.rule_code == 'hukuk_staff_single'
    assert chain.manager_1_sicil == '060'
    assert chain.expected_levels == (1,)


def test_desired_manager_sicils_hukuk_staff_explicit_hint_overrides_generic_chief_lookup():
    president, vice = _base_people()
    generic_unit_chief = _user(id=60, sicil_no='060', role='mali_musavir', unvan='Sorumlu Hukuk Müşaviri', birim='Hukuk Müşavirliği', ust_birim='Başkanlık')
    explicit_supervisor = _user(id=62, sicil_no='062', role='personel', unvan='Hukuk Müşaviri', birim='Uzak Hukuk Birimi', ust_birim='Başkanlık')
    staff = _user(
        id=61, sicil_no='061', role='personel', unvan='Hukuk Uzmanı', birim='Hukuk Müşavirliği', ust_birim='Başkanlık',
        yonetici_sicil='062',
    )

    lookup = build_lookup([president, vice, generic_unit_chief, explicit_supervisor, staff])
    chain = desired_manager_sicils(staff, lookup)

    assert chain.rule_code == 'hukuk_supervised_single'
    assert chain.manager_1_sicil == '062'  # explicit hint wins over the unit's generic chief ('060')
    assert chain.expected_levels == (1,)
