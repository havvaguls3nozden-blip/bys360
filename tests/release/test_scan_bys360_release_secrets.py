"""Regression tests for scripts/release/scan_bys360_release_secrets.py.

Schema-contract-drift wave, real-worktree secret-gate validation
(2026-08-25): wiring this scanner into the FULL release builder as a hard
"0 findings" gate surfaced 825 findings against this project's own real,
fully-assembled release tree -- every one verified (by hand, tracing each
category to its actual source line) to be a false positive, not a real
secret. Root causes: (1) the generic high-entropy rule matched ANY
identifier merely containing the bare substring "key"/"token"/"secret"/
"cred" (permission_key, primary_key, foreign_key, key_name, ...), and (2)
none of the keyword-assignment regexes distinguished a literal value from
a captured CODE fragment (os.environ.get(, secrets.token_urlsafe(32),
a bare variable reference like _raw_secret_key).

These tests lock in the fix: real secrets (planted, fake) must still be
caught (section 3 of the coordinator's fix spec), and the exact diagnosed
false-positive shapes -- including literal excerpts from the real 825 --
must not fire (section 4).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "release" / "scan_bys360_release_secrets.py"
)
_spec = importlib.util.spec_from_file_location("scan_bys360_release_secrets", _MODULE_PATH)
assert _spec is not None and _spec.loader is not None
scanner = importlib.util.module_from_spec(_spec)
# @dataclass (used by Finding below) resolves its own module via
# sys.modules[cls.__module__] on Python 3.14 -- must be registered before
# exec_module() runs the class body, or dataclass() raises AttributeError.
sys.modules[_spec.name] = scanner
_spec.loader.exec_module(scanner)


def _scan_text(tmp_path: Path, text: str, name: str = "sample.py"):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    findings, files_scanned = scanner.scan_path(tmp_path)
    return findings, files_scanned


# ---------------------------------------------------------------------------
# MUST FAIL: real (fake-but-realistic) secrets are still caught.
# ---------------------------------------------------------------------------

def test_real_secret_key_assignment_still_caught(tmp_path):
    findings, _ = _scan_text(tmp_path, 'SECRET_KEY = "kx8Qw2vRzT9pL4mN7bJ3dF6hY1sA5eC0"\n')  # hardcoded_secret fixture
    assert any(f.category == "secret_key" for f in findings)


def test_real_api_key_assignment_still_caught(tmp_path):
    findings, _ = _scan_text(tmp_path, 'API_KEY = "z9Xk3mQ7wR2vL8nT5pJ4bF6hY1sA0eC9dK"\n')  # hardcoded_secret fixture
    assert any(f.category in ("api_token", "generic_high_entropy") for f in findings)


def test_real_api_token_assignment_still_caught(tmp_path):
    findings, _ = _scan_text(tmp_path, 'API_TOKEN = "tK9mZ3xQ7wR2vL8nJ4bF6hY1sA0eC9dP5"\n')  # hardcoded_secret fixture
    assert any(f.category in ("api_token", "generic_high_entropy") for f in findings)


def test_synthetic_openai_style_key_still_caught(tmp_path):
    findings, _ = _scan_text(tmp_path, 'OPENAI_API_KEY = "sk-abcdefghijklmnopqrstuvwxyzABCDEFGH1234"\n')  # hardcoded_secret fixture
    assert any(f.category in ("api_token", "generic_high_entropy") for f in findings)


def test_synthetic_github_token_still_caught(tmp_path):
    findings, _ = _scan_text(tmp_path, 'GITHUB_TOKEN = "ghp_abcdefghijklmnopqrstuvwxyz0123456789AB"\n')  # hardcoded_secret fixture
    assert any(f.category == "api_token" and "github_token" in f.rule_id.lower() for f in findings)


def test_database_url_with_real_password_still_caught(tmp_path):
    findings, _ = _scan_text(tmp_path, 'DATABASE_URL = "postgresql://bys360_user:Tr0ub4dor-Genuine-Secret@dbhost.internal:5432/bys360"\n')  # hardcoded_secret fixture
    assert any(f.category == "database_url" for f in findings)


def test_mail_password_still_caught(tmp_path):
    findings, _ = _scan_text(tmp_path, 'MAIL_PASSWORD = "hK7mQ3xW9vR2nL8bJ4pF6dY1sA0eC9tZ5"\n')  # hardcoded_secret fixture
    assert any(f.category == "password" for f in findings)


def test_private_key_header_still_caught(tmp_path):
    # hardcoded_secret fixture -- synthetic, not a real key. Marker matches
    # the repo-wide convention scripts/quality/bys360_secret_repo_gate.py's
    # REGEX_OR_SCANNER_MARKERS checks for (see tests/quality/test_bys360_
    # secret_repo_gate.py for the same convention used throughout that file).
    findings, _ = _scan_text(tmp_path, "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----\n")  # hardcoded_secret fixture
    assert any(f.category == "private_key" for f in findings)


def test_jwt_like_secret_still_caught(tmp_path):
    findings, _ = _scan_text(
        tmp_path,
        'token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dQw4w9WgXcQmZ8vRb2Nc3Ef4Gh5Ij6Kl7Mn"\n',  # hardcoded_secret fixture
    )
    assert any(f.rule_id == "KNOWN_FORMAT_JWT_LIKE" for f in findings)


def test_aws_access_key_id_still_caught(tmp_path):
    findings, _ = _scan_text(tmp_path, 'aws_key = "AKIAIOSFODNN7EXAMPLE"\n')
    assert any(f.rule_id == "KNOWN_FORMAT_AWS_ACCESS_KEY_ID" for f in findings)


# ---------------------------------------------------------------------------
# MUST PASS: diagnosed false-positive shapes must not fire.
# ---------------------------------------------------------------------------

def test_powershell_variable_interpolation_not_flagged(tmp_path):
    findings, _ = _scan_text(
        tmp_path,
        '$shadowUrl = "postgresql://$($DbConn.User):$($DbConn.Password)@$($DbConn.HostName):$($DbConn.Port)/$ShadowDbName"\n',
        name="sample.ps1",
    )
    assert findings == []


def test_dict_subscript_key_not_flagged(tmp_path):
    findings, _ = _scan_text(tmp_path, 'value = config["key"]\n')
    assert findings == []


def test_dict_literal_key_not_flagged(tmp_path):
    findings, _ = _scan_text(tmp_path, 'payload = {"key": "value_that_is_reasonably_long_but_not_secret"}\n')
    assert findings == []


def test_primary_key_flag_not_flagged(tmp_path):
    findings, _ = _scan_text(tmp_path, "primary_key = True\n")
    assert findings == []


def test_foreign_key_column_not_flagged(tmp_path):
    findings, _ = _scan_text(tmp_path, 'user_id = db.Column(db.Integer, foreign_key="users.id")\n')
    assert findings == []


def test_key_name_variable_reference_not_flagged(tmp_path):
    findings, _ = _scan_text(tmp_path, "key_name = some_other_variable_holding_a_label\n")
    assert findings == []


def test_key_name_field_referencing_a_real_keyword_by_name_not_flagged(tmp_path):
    """A field literally named after a keyword ("API_KEY_NAME") whose value
    is the STRING "OPENAI_API_KEY" (the name of a keyword, not a secret) --
    neither side of the assignment is itself a real secret-shaped keyword
    with a real value."""
    findings, _ = _scan_text(tmp_path, 'API_KEY_NAME = "OPENAI_API_KEY"\n')
    assert findings == []


def test_documentation_mentioning_secret_key_not_flagged(tmp_path):
    findings, _ = _scan_text(
        tmp_path,
        "# See config.py for how SECRET_KEY is resolved from the environment.\n",
    )
    assert findings == []


def test_env_example_placeholder_allowed(tmp_path):
    findings, _ = _scan_text(tmp_path, "SECRET_KEY=CHANGE_ME\n", name=".env.example")
    assert findings == []


# ---- Representative false positives traced from the real 825 findings ----

def test_bare_identifier_reference_not_flagged(tmp_path):
    """Real repro: config.py `SECRET_KEY = _raw_secret_key` -- a bare
    variable reference, not a literal. Low natural-language entropy
    (~3.14 bits/char) is what distinguishes it from a real secret of the
    same alphanumeric-only shape."""
    findings, _ = _scan_text(tmp_path, "SECRET_KEY = _raw_secret_key\n")
    assert findings == []


def test_os_environ_get_call_not_flagged(tmp_path):
    """Real repro: config.py `SECRET_KEY = os.environ.get("FLASK_SECRET")
    or "bys360-local-dev-only-secret"` -- the regex captures the code
    fragment "os.environ.get(" up to the first quote."""
    findings, _ = _scan_text(tmp_path, 'SECRET_KEY = os.environ.get("FLASK_SECRET") or "bys360-local-dev-only-secret"\n')
    assert findings == []


def test_function_call_with_args_not_flagged(tmp_path):
    """Real repro: app/admin/routes.py-style `initial_password =
    generate_secure_password(16)` -- a full call with a closing paren and
    argument, not just a truncated one."""
    findings, _ = _scan_text(tmp_path, "initial_password = generate_secure_password(16)\n")
    assert findings == []


def test_template_permission_key_attribute_not_flagged(tmp_path):
    """Real repro: app/templates/base.html-style Jinja/HTML attributes using
    the common word "key" in a data attribute name -- must not match the
    generic high-entropy rule's keyword list (SECRET_KEY/API_KEY/etc are
    specific, bounded keywords; bare "key" is not one of them)."""
    findings, _ = _scan_text(
        tmp_path,
        '<div data-permission-key="performans_degerlendirme_ekran_gorunurluk_ayari_v3"></div>\n',
        name="sample.html",
    )
    assert findings == []


def test_access_token_local_variable_from_http_response_not_flagged(tmp_path):
    """Real repro: tests/integration-style `access_token =
    response.json()["access_token"]` -- code, not a literal, and (in the
    real file) inside tests/ anyway which the release builder excludes;
    this test only exercises the scanner's own detection logic in
    isolation."""
    findings, _ = _scan_text(tmp_path, 'access_token = response.json()["access_token"]\n')
    assert findings == []
