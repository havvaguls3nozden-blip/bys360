"""BYS360 Assistant V2 -- network independence contract.

Blocks ALL outbound socket connections for the duration of these tests
(monkeypatching `socket.socket.connect`/`connect_ex` to raise), then proves
the full BYS360-native pipeline still works end-to-end: intent resolution,
authorization (both allow and deny), a real single-module answer, and a real
cross-module answer with provenance intact. If any of this secretly depended
on reaching the network, these tests would fail with the injected
`OSError`, not with a normal assertion failure -- that distinction is the
actual proof, not just "the test passed."

Scope honesty: conversation follow-up ("conversation memory" / Phase H) is
NOT covered here because that layer does not exist in this codebase yet
(explicitly reported as remaining/next-wave work) -- there is nothing to
network-independence-test for a feature that has not been built. Everything
else the mandate asked this test to prove is covered below.
"""
from __future__ import annotations

import socket

import pytest

pytestmark = pytest.mark.ci_safe

_PASSWORD = "Assist_v2_Test_Pw_1!"
_UNIT = "AV2_NETINDEP_UNIT"


class _NetworkBlockedError(OSError):
    pass


@pytest.fixture
def block_all_outbound_network(monkeypatch):
    def _blocked_connect(self, *args, **kwargs):
        raise _NetworkBlockedError("outbound network access blocked for this test")

    monkeypatch.setattr(socket.socket, "connect", _blocked_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", _blocked_connect)
    yield


def _create_user(app, *, sicil_no, role, birim=None, password=_PASSWORD):
    from app.extensions import db
    from app.models import User

    with app.app_context():
        existing = User.query.filter_by(sicil_no=sicil_no).first()
        if existing is not None:
            return existing.id
        user = User(
            sicil_no=sicil_no,
            email=f"{sicil_no}@ktb.gov.tr",
            ad="NetIndep",
            soyad="Test",
            role=role,
            birim=birim,
            is_active=True,
            must_change_password=False,
            must_set_security_question=False,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user.id


def _get_user(app, user_id):
    from app.models import User

    return User.query.get(user_id)


def test_intent_resolution_works_with_network_blocked(block_all_outbound_network):
    from app.services.assistant_v2.intent_router import ConfidenceTier, resolve_intent

    resolution = resolve_intent("sicil kaydını göster")
    assert resolution.tier is ConfidenceTier.HIGH
    assert resolution.best_capability_key == "personnel_hr_read_personnel_record"


def test_authorization_allow_and_deny_work_with_network_blocked(app, block_all_outbound_network):
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    admin_id = _create_user(app, sicil_no="av2_netindep_admin", role="admin")
    personel_id = _create_user(app, sicil_no="av2_netindep_personel", role="personel")

    with app.app_context():
        admin = _get_user(app, admin_id)
        allowed = invoke_capability(admin, "personnel_hr_read_personnel_record", sicil_no="__nonexistent__")
        personel = _get_user(app, personel_id)
        denied = invoke_capability(personel, "personnel_hr_read_personnel_record", sicil_no="__nonexistent__")

    assert allowed.status is not AssistantResultStatus.ACCESS_DENIED
    assert denied.status is AssistantResultStatus.ACCESS_DENIED


def test_personnel_answer_works_with_network_blocked(app, block_all_outbound_network):
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.response_composer import compose_response
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    admin_id = _create_user(app, sicil_no="av2_netindep_pers_admin", role="admin")
    _create_user(app, sicil_no="av2_netindep_pers_subject", role="personel", birim=_UNIT)

    with app.test_request_context():
        admin = _get_user(app, admin_id)
        result = invoke_capability(admin, "personnel_hr_list_personnel", birim=_UNIT)
        composed = compose_response(result, question="birimimdeki personeli listele")

    assert result.status is AssistantResultStatus.DATA_FOUND
    assert composed.answer_text
    assert "Kaynak:" in composed.answer_text


def test_performance_answer_works_with_network_blocked(app, block_all_outbound_network):
    from datetime import date

    from app.extensions import db
    from app.models.performance_models import PerformancePeriod
    from app.services.assistant_v2.capability_dispatcher import invoke_capability
    from app.services.assistant_v2.response_composer import compose_response
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    admin_id = _create_user(app, sicil_no="av2_netindep_perf_admin", role="admin")
    with app.app_context():
        period = PerformancePeriod(
            title="AV2 NetIndep Period", period_type="yillik", is_active=True,
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
        )
        db.session.add(period)
        db.session.commit()

    with app.app_context():
        admin = _get_user(app, admin_id)
        result = invoke_capability(admin, "performance_mgmt_list_active_periods")
        composed = compose_response(result, question="aktif performans dönemlerini göster")

    assert result.status is AssistantResultStatus.DATA_FOUND
    assert "AV2 NetIndep Period" in composed.answer_text


def test_cross_module_answer_and_provenance_work_with_network_blocked(app, block_all_outbound_network):
    from datetime import date

    from app.extensions import db
    from app.models.performance_models import PerformanceEvaluation, PerformancePeriod
    from app.services.assistant_v2.cross_module_orchestrator import (
        personnel_pending_evaluation_in_unit,
    )
    from app.services.assistant_v2.response_composer import compose_cross_module_response
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    admin_id = _create_user(app, sicil_no="av2_netindep_xmod_admin", role="admin")
    subject_id = _create_user(app, sicil_no="av2_netindep_xmod_subject", role="personel", birim=_UNIT)

    with app.app_context():
        period = PerformancePeriod(
            title="AV2 NetIndep XMod Period", period_type="yillik", is_active=True,
            start_date=date(2026, 1, 1), end_date=date(2026, 12, 31),
        )
        db.session.add(period)
        db.session.commit()
        period_id = period.id
        db.session.add(PerformanceEvaluation(employee_id=subject_id, period_id=period_id, status="bekliyor"))
        db.session.commit()

    with app.test_request_context():
        admin = _get_user(app, admin_id)
        result = personnel_pending_evaluation_in_unit(admin, birim=_UNIT, period_id=period_id)
        composed = compose_cross_module_response(result, question="birimimde eksik değerlendirmesi olanlar")

    assert result.status is AssistantResultStatus.DATA_FOUND
    assert len(result.source_labels) == 2
    assert "Biriminizde performans değerlendirmesi tamamlanmamış" in composed.answer_text
    assert "Kaynak:" in composed.answer_text
