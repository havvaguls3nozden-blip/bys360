"""BYS360 Assistant V2 -- cross-module orchestration behavior contract
(mandate Phase 10 / G).

Proves the real, worked example
(`personnel_pending_evaluation_in_unit` = personnel_hr + performance_mgmt)
end-to-end against a real test database: every constituent capability call
goes through the real `capability_dispatcher.invoke_capability` (so real
authorization applies), the intersection is computed only from what both
calls actually returned, and a denial on EITHER constituent capability fails
the whole cross-module query closed -- it never leaks the other module's
data as a narrower, silently-degraded answer.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.ci_safe

_PASSWORD = "Assist_v2_Xmod_Test_Pw_1!"
_UNIT = "AV2_XMOD_TEST_UNIT"


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
            ad="XMod",
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


def _create_period(app, *, title="AV2 XMOD Test Period"):
    from datetime import date

    from app.extensions import db
    from app.models.performance_models import PerformancePeriod

    with app.app_context():
        existing = PerformancePeriod.query.filter_by(title=title).first()
        if existing is not None:
            return existing.id
        period = PerformancePeriod(
            title=title,
            period_type="yillik",
            is_active=True,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
        )
        db.session.add(period)
        db.session.commit()
        return period.id


def _create_incomplete_evaluation(app, *, employee_id, period_id):
    from app.extensions import db
    from app.models.performance_models import PerformanceEvaluation

    with app.app_context():
        existing = PerformanceEvaluation.query.filter_by(employee_id=employee_id, period_id=period_id).first()
        if existing is not None:
            existing.status = "bekliyor"
            db.session.commit()
            return existing.id
        evaluation = PerformanceEvaluation(employee_id=employee_id, period_id=period_id, status="bekliyor")
        db.session.add(evaluation)
        db.session.commit()
        return evaluation.id


def test_personnel_pending_evaluation_in_unit_finds_real_matched_person(app):
    from app.services.assistant_v2.cross_module_orchestrator import (
        personnel_pending_evaluation_in_unit,
    )
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    admin_id = _create_user(app, sicil_no="av2_xmod_admin", role="admin")
    subject_id = _create_user(app, sicil_no="av2_xmod_subject", role="personel", birim=_UNIT)
    period_id = _create_period(app)
    _create_incomplete_evaluation(app, employee_id=subject_id, period_id=period_id)

    with app.test_request_context():
        # A real request context (not just app_context) is required here:
        # personnel_hr_list_personnel reuses the already-shipped
        # build_personnel_list_row(), whose User.profile_photo_url property
        # calls url_for(), which needs an active request context to resolve
        # -- exactly the real production situation (this capability is only
        # ever invoked from within a live Flask request).
        admin = _get_user(app, admin_id)
        result = personnel_pending_evaluation_in_unit(admin, birim=_UNIT, period_id=period_id)

    assert result.status is AssistantResultStatus.DATA_FOUND
    assert any(row.get("id") == subject_id for row in (result.data or []))
    assert result.contributing_module_keys == ("personnel_hr", "performance_mgmt")
    assert len(result.source_labels) == 2


def test_personnel_pending_evaluation_no_match_is_no_data(app):
    from app.services.assistant_v2.cross_module_orchestrator import (
        personnel_pending_evaluation_in_unit,
    )
    from app.services.assistant_v2.result_contract import AssistantResultStatus

    admin_id = _create_user(app, sicil_no="av2_xmod_admin_nomatch", role="admin")
    period_id = _create_period(app, title="AV2 XMOD Empty Period")

    with app.app_context():
        admin = _get_user(app, admin_id)
        result = personnel_pending_evaluation_in_unit(admin, birim="AV2_XMOD_EMPTY_UNIT", period_id=period_id)

    assert result.status is AssistantResultStatus.NO_DATA
    assert result.data is None


def test_personnel_denied_short_circuits_before_performance_capability_runs(app, monkeypatch):
    """If the FIRST constituent (personnel) is denied, the orchestrator must
    not even call the performance capability -- proven by monkeypatching
    invoke_capability to fail the test if it's called a second time."""
    from app.services.assistant_v2 import cross_module_orchestrator
    from app.services.assistant_v2.result_contract import (
        AssistantCapabilityResult,
        AssistantResultStatus,
    )

    call_log: list[str] = []
    real_invoke = cross_module_orchestrator.invoke_capability

    def _tracking_invoke(user, capability_key, **kwargs):
        call_log.append(capability_key)
        if capability_key == "personnel_hr_list_personnel":
            return AssistantCapabilityResult(
                status=AssistantResultStatus.ACCESS_DENIED,
                message="denied for test",
                capability_key=capability_key,
                module_key="personnel_hr",
            )
        return real_invoke(user, capability_key, **kwargs)

    monkeypatch.setattr(cross_module_orchestrator, "invoke_capability", _tracking_invoke)

    admin_id = _create_user(app, sicil_no="av2_xmod_shortcircuit", role="admin")
    with app.app_context():
        admin = _get_user(app, admin_id)
        result = cross_module_orchestrator.personnel_pending_evaluation_in_unit(admin, birim=_UNIT, period_id=1)

    assert result.status is AssistantResultStatus.ACCESS_DENIED
    assert call_log == ["personnel_hr_list_personnel"]


def test_performance_denied_does_not_leak_personnel_data(app, monkeypatch):
    """If personnel succeeds but performance is denied, the WHOLE result
    must fail closed -- the personnel list (which WAS independently
    authorized) must never be returned as a silently-narrower answer."""
    from app.services.assistant_v2 import cross_module_orchestrator
    from app.services.assistant_v2.result_contract import (
        AssistantCapabilityResult,
        AssistantResultStatus,
    )

    real_invoke = cross_module_orchestrator.invoke_capability

    def _mixed_invoke(user, capability_key, **kwargs):
        if capability_key == "performance_mgmt_list_incomplete_evaluations":
            return AssistantCapabilityResult(
                status=AssistantResultStatus.ACCESS_DENIED,
                message="denied for test",
                capability_key=capability_key,
                module_key="performance_mgmt",
            )
        return real_invoke(user, capability_key, **kwargs)

    monkeypatch.setattr(cross_module_orchestrator, "invoke_capability", _mixed_invoke)

    admin_id = _create_user(app, sicil_no="av2_xmod_mixed_deny", role="admin")
    _create_user(app, sicil_no="av2_xmod_mixed_subject", role="personel", birim=_UNIT)

    with app.app_context():
        admin = _get_user(app, admin_id)
        result = cross_module_orchestrator.personnel_pending_evaluation_in_unit(admin, birim=_UNIT, period_id=1)

    assert result.status is AssistantResultStatus.ACCESS_DENIED
    assert result.data is None
