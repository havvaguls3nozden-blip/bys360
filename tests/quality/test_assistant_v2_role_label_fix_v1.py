"""BYS360 Assistant V2 -- role-label defect (post-production live defect,
narrow follow-up to the zero-arg dispatch fix at cdefd99e).

Root cause (proven mechanically, not assumed -- see conversation record for
the full trace): `mali_musavir` is a real, separately-valid, actively-used
system role throughout this codebase (personnel sync, communication
routing, account visibility, AI visibility gating,
`app.admin.routes.ROLE_CHOICES`) -- NOT obsolete, NOT simply a mislabeled
key. `hukuk_musaviri` is never a real, storable `User.role` value anywhere
in this system; it is a job-title (unvan) token used only inside the
performance/hierarchy-chain matching subsystem
(`app/services/performance_v2/rules.py`'s `normalize_role_token()`). A
real person who carries the job title "Hukuk Müşaviri" has
`role='mali_musavir'` in the database -- proven by this codebase's own
`tests/behavior/test_hierarchy_rulebook_manager_chain_resolution_contract.py`
(`infer_role_from_profile(unvan='Hukuk Müşaviri', ...) ==
('mali_musavir', 'Mali Müşavir')`).

Given this, blindly renaming `mali_musavir` -> "Hukuk Müşaviri" everywhere
(or renaming the internal key) would break the correct, consistent label
used elsewhere for every OTHER `mali_musavir`-role person. The user
confirmed (after this mechanical evidence was presented) the intended fix:
change ONLY the Assistant role matrix's own display label for
`mali_musavir` from "Mali Müşavir" to "Hukuk Müşaviri" -- the internal
role key is untouched, and the centralized
`app.services.role_display.ROLE_DISPLAY_LABELS` /
`app.admin.routes.ROLE_CHOICES` sources (used everywhere else) are
deliberately left untouched.

A second, related bug was found and fixed in the same pass:
`response_composer._format_virtual_assistant_role_matrix` resolved
`visible_roles` labels via the generic, centralized `ROLE_CHOICES` instead
of `ASSISTANT_POLICY_ROLE_OPTIONS` (the list `build_assistant_role_matrix()`
itself is built from) -- silently bypassing the Assistant-specific label
entirely. Fixed to read from the correct source.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.ci_safe

_PASSWORD = "Assist_v2_Test_Pw_1!"


def _mk_user(db, User, *, sicil_no, role):
    existing = User.query.filter_by(sicil_no=sicil_no).first()
    if existing is not None:
        return existing
    user = User(
        sicil_no=sicil_no, email=f"{sicil_no}@ktb.gov.tr", ad="Role", soyad="Label",
        role=role, is_active=True, must_change_password=False, must_set_security_question=False,
    )
    user.set_password(_PASSWORD)
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def admin(app):
    # Deliberately does NOT write a RoleMenuDefault row: `ai_agent_panel`
    # (this capability's permission_key) is already broadly granted to
    # every authenticated role by real policy default (confirmed earlier
    # in this engagement's zero-arg dispatch work), so no explicit seed is
    # needed. Writing one would trigger the separate, already-known,
    # deliberately-deferred BYS360_SETTINGS_ROLE_MENU_PARTIAL_OVERRIDE_RESOLVER_DEFECT
    # (menu_profile_access.py -- out of scope for this mandate): once ANY
    # explicit RoleMenuDefault row exists for a role, static/policy
    # fallback stops applying to every OTHER menu key for that role for
    # the rest of the test session, breaking unrelated later tests.
    from app.extensions import db
    from app.models import User

    with app.app_context():
        yield _mk_user(db, User, sicil_no="role_label_fix_admin", role="admin")


# ---------------------------------------------------------------------------
# Live query, end to end
# ---------------------------------------------------------------------------


def test_live_role_matrix_query_shows_hukuk_musaviri_not_mali_musavir(app, admin):
    from app.services.assistant_v2.service import AssistantV2Service

    with app.app_context(), app.test_request_context():
        answer = AssistantV2Service().ask(admin, "Sanal Asistan rol matrisini açıkla")
    assert answer.status == "DATA_FOUND"
    assert answer.capability_key == "virtual_assistant_explain_role_matrix"
    assert "Hukuk Müşaviri" in answer.answer
    assert "Mali Müşavir" not in answer.answer


def test_response_composer_formatter_directly():
    from app.services.assistant_v2 import response_composer
    from app.services.assistant_v2.result_contract import (
        AssistantCapabilityResult,
        AssistantResultStatus,
    )

    result = AssistantCapabilityResult(
        status=AssistantResultStatus.DATA_FOUND, message="ok",
        capability_key="virtual_assistant_explain_role_matrix", module_key="virtual_assistant",
        data={"visible_roles": ["admin", "mali_musavir", "koordinator"]},
        source_label="Asistan Rol Matrisi",
    )
    composed = response_composer.compose_response(result)
    assert "Hukuk Müşaviri" in composed.answer_text
    assert "Mali Müşavir" not in composed.answer_text


# ---------------------------------------------------------------------------
# Scope discipline: internal key unchanged, centralized sources untouched
# ---------------------------------------------------------------------------


def test_internal_role_key_unchanged():
    """The internal role key `mali_musavir` must still be the key used --
    only its Assistant-matrix display label changed."""
    from app.services.assistant_role_matrix_service import ASSISTANT_POLICY_ROLE_OPTIONS

    keys = [key for key, _label in ASSISTANT_POLICY_ROLE_OPTIONS]
    assert "mali_musavir" in keys
    assert "hukuk_musaviri" not in keys
    labels = dict(ASSISTANT_POLICY_ROLE_OPTIONS)
    assert labels["mali_musavir"] == "Hukuk Müşaviri"


def test_centralized_role_display_labels_untouched():
    """The shared, centralized role-display source used everywhere else
    must still say "Mali Müşavir" for mali_musavir -- it is still correct
    there, and only the Assistant-specific list was changed."""
    from app.services.role_display import ROLE_DISPLAY_LABELS

    assert ROLE_DISPLAY_LABELS["mali_musavir"] == "Mali Müşavir"
    assert ROLE_DISPLAY_LABELS["hukuk_musaviri"] == "Hukuk Müşaviri"


def test_centralized_role_choices_untouched():
    from app.admin.routes import ROLE_CHOICES

    assert dict(ROLE_CHOICES)["mali_musavir"] == "Mali Müşavir"


def test_build_assistant_role_matrix_data_contract_unchanged():
    """build_assistant_role_matrix()'s own returned data must still use
    the real role_key 'mali_musavir' internally -- only the composer's
    rendered PROSE label changed, never the machine-readable data."""
    from app.services.assistant_role_matrix_service import build_assistant_role_matrix

    data = build_assistant_role_matrix()
    role_keys = {row["role_key"] for row in data["roles"]}
    assert "mali_musavir" in role_keys
    assert "hukuk_musaviri" not in role_keys


def test_role_matrix_capability_authorization_unchanged():
    from app.services.assistant_v2.capability_registry import get_capability

    entry = get_capability("virtual_assistant_explain_role_matrix")
    assert entry is not None
    assert entry.permission_key == "ai_agent_panel"
    assert entry.is_self_describing is False
