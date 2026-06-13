from __future__ import annotations

from types import SimpleNamespace

import pytest


def test_campaign_assignment_all_user_role_and_unit_behavior():
    from app.services.feedback_service import user_can_see_campaign

    user = SimpleNamespace(id=7, sicil_no="123", role="koordinator", organization_unit_id=44, birim="Eğitim")

    class Assignments:
        def __init__(self, rows):
            self._rows = rows
        def all(self):
            return self._rows

    assert user_can_see_campaign(user, SimpleNamespace(assignments=Assignments([SimpleNamespace(target_type="all", target_value=None)]))) is True
    assert user_can_see_campaign(user, SimpleNamespace(assignments=Assignments([SimpleNamespace(target_type="user", target_value="7")]))) is True
    assert user_can_see_campaign(user, SimpleNamespace(assignments=Assignments([SimpleNamespace(target_type="user", target_value="123")]))) is True
    assert user_can_see_campaign(user, SimpleNamespace(assignments=Assignments([SimpleNamespace(target_type="role", target_value="KOORDINATOR")]))) is True
    assert user_can_see_campaign(user, SimpleNamespace(assignments=Assignments([SimpleNamespace(target_type="unit", target_value="44")]))) is True
    assert user_can_see_campaign(user, SimpleNamespace(assignments=Assignments([SimpleNamespace(target_type="unit", target_value="eğitim")]))) is True
    assert user_can_see_campaign(user, SimpleNamespace(assignments=Assignments([SimpleNamespace(target_type="role", target_value="personel")]))) is False


def test_anonymous_campaign_submission_does_not_store_user_id(monkeypatch):
    import app.services.feedback_service as svc

    captured = {"objects": []}

    class FakeSession:
        def add(self, obj):
            captured["objects"].append(obj)
        def flush(self):
            for obj in captured["objects"]:
                if obj.__class__.__name__ == "FakeSubmission" and getattr(obj, "id", None) is None:
                    obj.id = 101
        def commit(self):
            captured["committed"] = True
        def rollback(self):
            captured["rolled_back"] = True

    class FakeSubmission:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
            self.id = None

    class FakeAnswer:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class FakeQuestions:
        def __init__(self, rows):
            self._rows = rows
        def order_by(self, *args, **kwargs):
            return self
        def all(self):
            return self._rows

    monkeypatch.setattr(svc, "FeedbackSubmission", FakeSubmission)
    monkeypatch.setattr(svc, "FeedbackAnswer", FakeAnswer)
    monkeypatch.setattr(svc.db, "session", FakeSession())
    monkeypatch.setattr(svc, "campaign_is_open", lambda campaign: True)
    monkeypatch.setattr(svc, "user_can_see_campaign", lambda user, campaign: True)
    monkeypatch.setattr(svc, "has_user_submitted_campaign", lambda user, campaign: False)
    monkeypatch.setattr(svc, "campaign_includes_pulse", lambda campaign: False)

    user = SimpleNamespace(id=55, organization_unit_id=8)
    question = SimpleNamespace(id=1, is_required=True, question_text="Memnuniyet", question_type="text")
    campaign = SimpleNamespace(id=9, is_anonymous=True, allow_multiple_submissions=False, questions=FakeQuestions([question]))

    submission = svc.submit_campaign_answers(user=user, campaign=campaign, form={"question_1": "İyi"})

    assert submission.user_id is None
    assert submission.anonymous_token
    assert submission.organization_unit_id == 8
    assert captured.get("committed") is True


def test_required_campaign_question_blocks_empty_submission(monkeypatch):
    import app.services.feedback_service as svc

    class FakeSession:
        def add(self, obj): pass
        def flush(self): pass
        def commit(self): pass
        def rollback(self): pass

    class FakeSubmission:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
            self.id = 1

    class FakeQuestions:
        def order_by(self, *args, **kwargs): return self
        def all(self): return [SimpleNamespace(id=3, is_required=True, question_text="Zorunlu soru", question_type="text")]

    monkeypatch.setattr(svc, "FeedbackSubmission", FakeSubmission)
    monkeypatch.setattr(svc.db, "session", FakeSession())
    monkeypatch.setattr(svc, "campaign_is_open", lambda campaign: True)
    monkeypatch.setattr(svc, "user_can_see_campaign", lambda user, campaign: True)
    monkeypatch.setattr(svc, "has_user_submitted_campaign", lambda user, campaign: False)

    with pytest.raises(ValueError, match="zorunludur"):
        svc.submit_campaign_answers(
            user=SimpleNamespace(id=1, organization_unit_id=1),
            campaign=SimpleNamespace(id=1, is_anonymous=False, allow_multiple_submissions=True, questions=FakeQuestions()),
            form={},
        )
