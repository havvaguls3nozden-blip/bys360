"""BYS360 performans karne görünürlük anayasası davranış sözleşmesi testleri.

Kapsam: app/services/performance/visibility_guard.py -- get_evaluation_visibility_state,
can_employee_view_evaluation, is_privileged_scorecard_viewer, is_employee_visible,
build_evaluation_form_visibility_context ve completed_previous_levels_for_form.

Bu dosya SADECE visibility_guard.py'nin KENDİ karar/dallanma mantığını doğrular.
Modülün dış bağımlılığı olan düşük performans yayın kilidi fonksiyonu
(get_low_score_employee_publish_lock_reason) tek noktada mock'lanır; böylece
low_score_process_service.py'nin kendi davranışı bu dosyanın testlerine
sızmaz (o davranış tests/behavior/test_low_score_process_service_workflow_contract.py'de
doğrudan test edilir). Bu dosyanın yazıldığı sırada low_score_process_service.py'de
ayrı/bilinen bir hata vardı (ensure=False ile zaten var olan bir
PerformanceLowScoreProcess kaydını doğru çözememesi); o hata BYS360 DEFECT AR
kapsamında düzeltildi -- ama bu dosya zaten o fonksiyonu hiçbir zaman gerçek
haliyle çağırmadığı için (her zaman mock), bu düzeltme bu dosyadaki testleri
etkilemedi.

Hiçbir test gerçek Flask app/DB gerektirmez: hedef fonksiyonların tamamı ya saf
öznitelik okuması (getattr tabanlı duck typing) yapar ya da kendi içindeki
try/except sınırlarıyla DB/app-context'siz ortamda güvenli şekilde varsayılana
düşen (visibility_guard.py'nin kendi _safe_phase6_2_* sarmalayıcıları) bir zincire
bağlıdır. Bu yüzden `types.SimpleNamespace` girdileri yeterlidir ve app.models /
create_app() hiçbir yerde çağrılmaz.
"""
from __future__ import annotations

import types

import pytest

from app.services.performance import visibility_guard

EMPLOYEE_ID = 501
OTHER_EMPLOYEE_ID = 9001
MANAGER_ID = 777


def _make_period(*, results_published: bool) -> types.SimpleNamespace:
    return types.SimpleNamespace(results_published=results_published)


def _make_evaluation(
    *,
    employee_id: int = EMPLOYEE_ID,
    status: str = "tamamlandi",
    is_published_to_employee: bool = False,
    period: types.SimpleNamespace | None = None,
) -> types.SimpleNamespace:
    return types.SimpleNamespace(
        employee_id=employee_id,
        status=status,
        is_published_to_employee=is_published_to_employee,
        period=period if period is not None else _make_period(results_published=False),
    )


def _make_viewer(*, id: int, role: str = "", is_authenticated: bool = True) -> types.SimpleNamespace:
    return types.SimpleNamespace(id=id, role=role, is_authenticated=is_authenticated)


def _stub_low_score_lock(monkeypatch: pytest.MonkeyPatch, reason: str | None) -> None:
    """visibility_guard'ın tek dış bağımlılığını (düşük performans yayın kilidi
    nedeni) belirlenimli biçimde kontrol eder. reason=None -> kilit yok,
    reason=<str> -> kilit var."""

    def _fake(evaluation=None, *, ensure: bool = False):
        return reason

    monkeypatch.setattr(visibility_guard, "get_low_score_employee_publish_lock_reason", _fake)


def _explode_if_low_score_lock_called(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bir kod yolunun düşük performans kilidi bağımlılığına HİÇ ulaşmaması
    gerektiğini (kısa devre) kanıtlamak için kullanılır."""

    def _fake(evaluation=None, *, ensure: bool = False):
        raise AssertionError("low-score lock dependency must not be reached on this path")

    monkeypatch.setattr(visibility_guard, "get_low_score_employee_publish_lock_reason", _fake)


# ---------------------------------------------------------------------------
# is_employee_visible
# ---------------------------------------------------------------------------


def test_is_employee_visible_false_for_none_evaluation_without_touching_dependency(monkeypatch):
    _explode_if_low_score_lock_called(monkeypatch)
    assert visibility_guard.is_employee_visible(None) is False


def test_is_employee_visible_false_when_not_completed(monkeypatch):
    _stub_low_score_lock(monkeypatch, None)
    evaluation = _make_evaluation(
        status="taslak",
        is_published_to_employee=True,
        period=_make_period(results_published=True),
    )
    assert visibility_guard.is_employee_visible(evaluation) is False


def test_is_employee_visible_true_when_completed_published_and_unlocked(monkeypatch):
    _stub_low_score_lock(monkeypatch, None)
    evaluation = _make_evaluation(
        status="completed",
        is_published_to_employee=True,
        period=_make_period(results_published=True),
    )
    assert visibility_guard.is_employee_visible(evaluation) is True


def test_is_employee_visible_false_when_period_not_published(monkeypatch):
    _stub_low_score_lock(monkeypatch, None)
    evaluation = _make_evaluation(
        status="completed",
        is_published_to_employee=True,
        period=_make_period(results_published=False),
    )
    assert visibility_guard.is_employee_visible(evaluation) is False


def test_is_employee_visible_false_when_employee_not_published(monkeypatch):
    _stub_low_score_lock(monkeypatch, None)
    evaluation = _make_evaluation(
        status="completed",
        is_published_to_employee=False,
        period=_make_period(results_published=True),
    )
    assert visibility_guard.is_employee_visible(evaluation) is False


def test_is_employee_visible_false_when_low_score_lock_present_despite_all_published(monkeypatch):
    """Düşük performans yayın kilidi, diğer tüm bayraklar 'yayında' dese bile
    kendi-sonuç görünürlüğünü geçersiz kılmalıdır."""
    _stub_low_score_lock(monkeypatch, "Başkan onayı bekliyor.")
    evaluation = _make_evaluation(
        status="completed",
        is_published_to_employee=True,
        period=_make_period(results_published=True),
    )
    assert visibility_guard.is_employee_visible(evaluation) is False


# ---------------------------------------------------------------------------
# is_privileged_scorecard_viewer
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("role", sorted(visibility_guard.PRIVILEGED_SCORECARD_ROLES))
def test_is_privileged_scorecard_viewer_true_for_each_known_privileged_role(role):
    viewer = _make_viewer(id=MANAGER_ID, role=role)
    assert visibility_guard.is_privileged_scorecard_viewer(viewer) is True


def test_is_privileged_scorecard_viewer_true_case_insensitive():
    viewer = _make_viewer(id=MANAGER_ID, role="ADMIN")
    assert visibility_guard.is_privileged_scorecard_viewer(viewer) is True


def test_is_privileged_scorecard_viewer_false_for_non_privileged_role():
    viewer = _make_viewer(id=EMPLOYEE_ID, role="calisan")
    assert visibility_guard.is_privileged_scorecard_viewer(viewer) is False


def test_is_privileged_scorecard_viewer_false_when_not_authenticated():
    viewer = _make_viewer(id=MANAGER_ID, role="admin", is_authenticated=False)
    assert visibility_guard.is_privileged_scorecard_viewer(viewer) is False


def test_is_privileged_scorecard_viewer_false_when_authenticated_callable_returns_false():
    viewer = types.SimpleNamespace(id=MANAGER_ID, role="admin", is_authenticated=lambda: False)
    assert visibility_guard.is_privileged_scorecard_viewer(viewer) is False


def test_is_privileged_scorecard_viewer_false_for_none_viewer():
    assert visibility_guard.is_privileged_scorecard_viewer(None) is False


# ---------------------------------------------------------------------------
# can_employee_view_evaluation
# ---------------------------------------------------------------------------


def test_can_employee_view_evaluation_true_for_self_when_visible(monkeypatch):
    _stub_low_score_lock(monkeypatch, None)
    evaluation = _make_evaluation(
        status="completed",
        is_published_to_employee=True,
        period=_make_period(results_published=True),
    )
    employee = _make_viewer(id=EMPLOYEE_ID, role="")
    assert visibility_guard.can_employee_view_evaluation(evaluation, employee) is True


def test_can_employee_view_evaluation_false_for_different_employee_without_touching_dependency(monkeypatch):
    """Kimlik uyuşmazlığı, düşük performans kilidi bağımlılığına hiç ulaşmadan
    kısa devre ile reddedilmelidir."""
    _explode_if_low_score_lock_called(monkeypatch)
    evaluation = _make_evaluation(
        status="completed",
        is_published_to_employee=True,
        period=_make_period(results_published=True),
    )
    other_viewer = _make_viewer(id=OTHER_EMPLOYEE_ID, role="")
    assert visibility_guard.can_employee_view_evaluation(evaluation, other_viewer) is False


def test_can_employee_view_evaluation_false_when_low_score_locked(monkeypatch):
    _stub_low_score_lock(monkeypatch, "Başkan onayı bekliyor.")
    evaluation = _make_evaluation(
        status="completed",
        is_published_to_employee=True,
        period=_make_period(results_published=True),
    )
    employee = _make_viewer(id=EMPLOYEE_ID, role="")
    assert visibility_guard.can_employee_view_evaluation(evaluation, employee) is False


def test_can_employee_view_evaluation_false_when_not_completed(monkeypatch):
    _stub_low_score_lock(monkeypatch, None)
    evaluation = _make_evaluation(
        status="taslak",
        is_published_to_employee=True,
        period=_make_period(results_published=True),
    )
    employee = _make_viewer(id=EMPLOYEE_ID, role="")
    assert visibility_guard.can_employee_view_evaluation(evaluation, employee) is False


def test_can_employee_view_evaluation_false_for_missing_evaluation_or_employee(monkeypatch):
    _explode_if_low_score_lock_called(monkeypatch)
    evaluation = _make_evaluation(
        status="completed",
        is_published_to_employee=True,
        period=_make_period(results_published=True),
    )
    employee = _make_viewer(id=EMPLOYEE_ID, role="")
    assert visibility_guard.can_employee_view_evaluation(None, employee) is False
    assert visibility_guard.can_employee_view_evaluation(evaluation, None) is False


# ---------------------------------------------------------------------------
# get_evaluation_visibility_state
# ---------------------------------------------------------------------------


def test_visibility_state_missing_evaluation_returns_fixed_locked_defaults(monkeypatch):
    _explode_if_low_score_lock_called(monkeypatch)
    state = visibility_guard.get_evaluation_visibility_state(None, None)
    assert state == {
        "rule_version": visibility_guard.VISIBILITY_RULE_VERSION,
        "can_view": False,
        "can_view_unpublished": False,
        "employee_visible": False,
        "same_employee": False,
        "viewer_is_privileged": False,
        "completed": False,
        "period_published": False,
        "employee_published": False,
        "own_result_locked": False,
        "publish_state": "missing",
        "publish_label": "Kayıt Yok",
        "publish_badge_class": "locked",
        "reason": "Değerlendirme bulunamadı.",
        "reason_code": "missing_evaluation",
        "lock_reason": "Değerlendirme bulunamadı.",
        "next_action": "İlgili karne kaydını yeniden oluşturun ya da dönemi kontrol edin.",
        "publishable": False,
    }


@pytest.mark.parametrize(
    "viewer",
    [
        _make_viewer(id=EMPLOYEE_ID, role=""),
        _make_viewer(id=MANAGER_ID, role="admin"),
        None,
    ],
    ids=["self", "privileged_admin", "anonymous"],
)
def test_visibility_state_incomplete_evaluation_never_visible_regardless_of_viewer(monkeypatch, viewer):
    """Tamamlanmamış bir değerlendirme; ne personel, ne de yetkili bir amir için
    -- kapsam/rol ne olursa olsun -- görünür olamaz. Tamamlanma, geri kalan tüm
    kuralların önündeki tek geçerli ilk kapıdır."""
    _stub_low_score_lock(monkeypatch, None)
    evaluation = _make_evaluation(
        status="taslak",
        is_published_to_employee=True,
        period=_make_period(results_published=True),
    )
    state = visibility_guard.get_evaluation_visibility_state(
        evaluation, viewer, allowed_employee_ids={EMPLOYEE_ID}
    )
    assert state["completed"] is False
    assert state["employee_visible"] is False
    assert state["can_view_unpublished"] is False
    assert state["can_view"] is False
    assert state["publish_state"] == "not_completed"
    assert state["reason_code"] == "not_completed"


def test_visibility_state_self_view_published_and_unlocked(monkeypatch):
    _stub_low_score_lock(monkeypatch, None)
    evaluation = _make_evaluation(
        status="completed",
        is_published_to_employee=True,
        period=_make_period(results_published=True),
    )
    viewer = _make_viewer(id=EMPLOYEE_ID, role="")
    state = visibility_guard.get_evaluation_visibility_state(
        evaluation, viewer, allowed_employee_ids={EMPLOYEE_ID}
    )
    assert state["employee_visible"] is True
    assert state["can_view"] is True
    assert state["can_view_unpublished"] is False
    assert state["same_employee"] is True
    assert state["own_result_locked"] is False
    assert state["publish_state"] == "published"
    # Bu dal için reason/next_action visibility_guard içinde sabit literal
    # değerlerdir; dış yayın ön kontrol zincirine bağlı değildir.
    assert state["reason"] == ""
    assert state["reason_code"] == "published"
    assert state["next_action"] == "Karne görüntülenebilir durumda."


def test_visibility_state_privileged_manager_preview_in_scope_via_allowed_list(monkeypatch):
    """Genel rol ailesinde olmayan (koordinator) yetkili bir amir, tamamlanmış
    ama henüz yayınlanmamış bir karneyi -- yalnızca allowed_employee_ids
    kapsamına dahilse -- iç kullanım (preview) olarak görebilir."""
    _stub_low_score_lock(monkeypatch, None)
    evaluation = _make_evaluation(
        status="completed",
        is_published_to_employee=False,
        period=_make_period(results_published=False),
    )
    manager = _make_viewer(id=MANAGER_ID, role="koordinator")
    state = visibility_guard.get_evaluation_visibility_state(
        evaluation, manager, allowed_employee_ids={EMPLOYEE_ID}
    )
    assert state["viewer_is_privileged"] is True
    assert state["same_employee"] is False
    assert state["employee_visible"] is False
    assert state["can_view_unpublished"] is True
    assert state["can_view"] is True
    assert state["publish_state"] == "internal_preview"


def test_visibility_state_privileged_manager_out_of_scope_denied(monkeypatch):
    """Aynı yetkili amir (koordinator), personel allowed_employee_ids kapsamı
    dışındaysa ve genel rol ailesinde de değilse -- iç kullanım önizlemesi de
    dahil -- hiçbir görünürlük kazanmaz."""
    _stub_low_score_lock(monkeypatch, None)
    evaluation = _make_evaluation(
        status="completed",
        is_published_to_employee=False,
        period=_make_period(results_published=False),
    )
    manager = _make_viewer(id=MANAGER_ID, role="koordinator")
    state = visibility_guard.get_evaluation_visibility_state(
        evaluation, manager, allowed_employee_ids=set()
    )
    assert state["viewer_is_privileged"] is True
    assert state["can_view_unpublished"] is False
    assert state["employee_visible"] is False
    assert state["can_view"] is False
    assert state["publish_state"] == "locked"


def test_visibility_state_general_role_admin_bypasses_allowed_list(monkeypatch):
    """admin/baskan gibi genel rol ailesi, allowed_employee_ids boş olsa bile
    kapsam içi sayılır (phase3_general_scope)."""
    _stub_low_score_lock(monkeypatch, None)
    evaluation = _make_evaluation(
        status="completed",
        is_published_to_employee=False,
        period=_make_period(results_published=False),
    )
    admin = _make_viewer(id=MANAGER_ID, role="admin")
    state = visibility_guard.get_evaluation_visibility_state(
        evaluation, admin, allowed_employee_ids=set()
    )
    assert state["can_view_unpublished"] is True
    assert state["can_view"] is True
    assert state["publish_state"] == "internal_preview"


def test_visibility_state_non_privileged_out_of_scope_viewer_denied_preview(monkeypatch):
    """Yetkisiz, kendisi olmayan ve kapsam dışı bir görüntüleyici, henüz
    yayınlanmamış bir karneyi hiçbir şekilde göremez."""
    _stub_low_score_lock(monkeypatch, None)
    evaluation = _make_evaluation(
        status="completed",
        is_published_to_employee=False,
        period=_make_period(results_published=False),
    )
    stranger = _make_viewer(id=OTHER_EMPLOYEE_ID, role="calisan")
    state = visibility_guard.get_evaluation_visibility_state(
        evaluation, stranger, allowed_employee_ids={EMPLOYEE_ID}
    )
    assert state["viewer_is_privileged"] is False
    assert state["same_employee"] is False
    assert state["can_view_unpublished"] is False
    assert state["employee_visible"] is False
    assert state["can_view"] is False
    assert state["publish_state"] == "locked"


def test_visibility_state_privileged_viewer_previewing_own_unpublished_evaluation_uses_self_rule(monkeypatch):
    """KRİTİK: Yetkili bir amir/admin KENDİ tamamlanmış-ama-yayınlanmamış
    karnesini önizlerken 'yönetici önizleme' istisnasından yararlanamaz;
    same_employee, can_view_unpublished dalını dışlar (kaynak: `not same_employee`
    koşulu). Kendi sonuç görünürlüğü her zaman normal kendi-sonuç/kilit
    kurallarına tabidir."""
    _stub_low_score_lock(monkeypatch, None)
    evaluation = _make_evaluation(
        status="completed",
        is_published_to_employee=False,
        period=_make_period(results_published=False),
    )
    self_admin = _make_viewer(id=EMPLOYEE_ID, role="admin")
    state = visibility_guard.get_evaluation_visibility_state(
        evaluation, self_admin, allowed_employee_ids={EMPLOYEE_ID}
    )
    assert state["viewer_is_privileged"] is True
    assert state["same_employee"] is True
    assert state["can_view_unpublished"] is False
    assert state["employee_visible"] is False
    assert state["can_view"] is False
    assert state["own_result_locked"] is True
    assert state["publish_state"] == "employee_locked"


def test_visibility_state_self_view_low_score_lock_overrides_published_flags(monkeypatch):
    """Düşük performans yayın kilidi (mock'lanmış), kendi-sonuç dalında diğer
    tüm bayraklar 'yayında' dese bile durumu kilitli olarak raporlamalıdır.
    reason/reason_code burada doğrudan mock'lanan değere bağlı olduğu için
    (dış preflight zincirinden bağımsız) kesin olarak doğrulanabilir."""
    lock_reason = "Başkan onayı bekliyor. Başkan/Üst Onay Yayın Kilidi"
    _stub_low_score_lock(monkeypatch, lock_reason)
    evaluation = _make_evaluation(
        status="completed",
        is_published_to_employee=True,
        period=_make_period(results_published=True),
    )
    viewer = _make_viewer(id=EMPLOYEE_ID, role="")
    state = visibility_guard.get_evaluation_visibility_state(
        evaluation, viewer, allowed_employee_ids={EMPLOYEE_ID}
    )
    assert state["employee_visible"] is False
    assert state["can_view"] is False
    assert state["own_result_locked"] is True
    assert state["low_score_publish_locked"] is True
    assert state["low_score_publish_lock_reason"] == lock_reason
    assert state["publish_state"] == "low_score_publish_locked"
    assert state["reason"] == lock_reason
    assert state["reason_code"] == "low_score_publish_lock"
    assert visibility_guard.is_employee_visible(evaluation) is False


def test_visibility_state_none_viewer_has_no_self_match_or_privilege(monkeypatch):
    _stub_low_score_lock(monkeypatch, None)
    evaluation = _make_evaluation(
        status="completed",
        is_published_to_employee=False,
        period=_make_period(results_published=False),
    )
    state = visibility_guard.get_evaluation_visibility_state(
        evaluation, None, allowed_employee_ids={EMPLOYEE_ID}
    )
    assert state["same_employee"] is False
    assert state["viewer_is_privileged"] is False
    assert state["can_view_unpublished"] is False
    assert state["can_view"] is False
    assert state["publish_state"] == "locked"


def test_visibility_state_published_can_view_is_not_re_scoped_by_viewer_once_employee_visible(monkeypatch):
    """Belgelenen gözlem (kaynak davranışı, hata değil): employee_visible True
    olduğunda can_view, evaluation'ın kendisinin yayın durumuna bağlıdır --
    get_evaluation_visibility_state bu dalda görüntüleyici kimliğine göre
    tekrar kapsam daraltması yapmaz (viewer scope daraltması yalnızca
    can_view_unpublished/preview dalında uygulanır). Belirli bir personelin
    kendi sonucuna kimin erişebileceğinin kimlik kontrolü ayrı bir fonksiyon
    olan can_employee_view_evaluation ile (self-view için) yapılır -- bkz.
    test_can_employee_view_evaluation_false_for_different_employee_*. Bu test,
    bu ayrımın visibility_guard.py'de gerçekten var olduğunu kanıtlar; ileride
    bu davranış sessizce değişirse regresyon olarak yakalanır."""
    _stub_low_score_lock(monkeypatch, None)
    evaluation = _make_evaluation(
        status="completed",
        is_published_to_employee=True,
        period=_make_period(results_published=True),
    )
    unrelated_viewer = _make_viewer(id=OTHER_EMPLOYEE_ID, role="calisan")
    state = visibility_guard.get_evaluation_visibility_state(
        evaluation, unrelated_viewer, allowed_employee_ids=set()
    )
    assert state["employee_visible"] is True
    assert state["can_view"] is True
    # Ama gerçek self-view kapısı (can_employee_view_evaluation) kimlik
    # uyuşmazlığında yine de reddeder:
    assert visibility_guard.can_employee_view_evaluation(evaluation, unrelated_viewer) is False


# ---------------------------------------------------------------------------
# completed_previous_levels_for_form
# ---------------------------------------------------------------------------


def test_completed_previous_levels_for_form_returns_only_completed_earlier_levels():
    evaluation = types.SimpleNamespace(level_3_completed=True, level_2_completed=False, level_1_completed=True)
    assert visibility_guard.completed_previous_levels_for_form(evaluation, 1) == [3]


def test_completed_previous_levels_for_form_all_previous_completed_ordered_desc():
    evaluation = types.SimpleNamespace(level_3_completed=True, level_2_completed=True)
    assert visibility_guard.completed_previous_levels_for_form(evaluation, 1) == [3, 2]


def test_completed_previous_levels_for_form_level_zero_returns_empty():
    evaluation = types.SimpleNamespace(level_3_completed=True, level_2_completed=True)
    assert visibility_guard.completed_previous_levels_for_form(evaluation, 0) == []


def test_completed_previous_levels_for_form_none_level_returns_empty():
    evaluation = types.SimpleNamespace(level_3_completed=True)
    assert visibility_guard.completed_previous_levels_for_form(evaluation, None) == []


def test_completed_previous_levels_for_form_non_numeric_level_returns_empty():
    evaluation = types.SimpleNamespace(level_3_completed=True)
    # "not-a-level" is a deliberately wrong-typed input (fail-closed check).
    assert visibility_guard.completed_previous_levels_for_form(evaluation, "not-a-level") == []  # type: ignore[arg-type]


def test_completed_previous_levels_for_form_highest_level_has_no_previous():
    evaluation = types.SimpleNamespace(level_3_completed=True, level_2_completed=True, level_1_completed=True)
    assert visibility_guard.completed_previous_levels_for_form(evaluation, 3) == []


# ---------------------------------------------------------------------------
# build_evaluation_form_visibility_context
# ---------------------------------------------------------------------------


def test_build_evaluation_form_visibility_context_with_previous_completed_levels():
    evaluation = types.SimpleNamespace(level_3_completed=True, level_2_completed=True)
    assignment = types.SimpleNamespace(manager_level=1)
    context = visibility_guard.build_evaluation_form_visibility_context(evaluation, assignment)
    assert context["rule_version"] == visibility_guard.VISIBILITY_RULE_VERSION
    assert context["current_level"] == 1
    assert context["visible_previous_levels"] == [3, 2]
    assert context["blind_review_allowed"] is False
    assert context["can_see_previous_scores"] is True
    assert (
        context["previous_score_hint"]
        == "Kör değerlendirme yok; tamamlanmış önceki amir puan ve kanaatleri görünür."
    )


def test_build_evaluation_form_visibility_context_no_previous_levels_hint():
    evaluation = types.SimpleNamespace()
    assignment = types.SimpleNamespace(manager_level=3)
    context = visibility_guard.build_evaluation_form_visibility_context(evaluation, assignment)
    assert context["visible_previous_levels"] == []
    assert context["can_see_previous_scores"] is False
    assert context["previous_score_hint"] == "Önceki tamamlanmış amir kaydı yok."


def test_build_evaluation_form_visibility_context_none_assignment_has_no_current_level():
    evaluation = types.SimpleNamespace(level_3_completed=True)
    context = visibility_guard.build_evaluation_form_visibility_context(evaluation, None)
    assert context["current_level"] is None
    assert context["visible_previous_levels"] == []
    assert context["can_see_previous_scores"] is False
