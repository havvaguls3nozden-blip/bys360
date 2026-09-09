"""Behavior contract for app/file_center/services.py -- upload security and
data-integrity guarantees.

This module has real production risk: it is the only gate between an
arbitrary uploaded file and this app's disk/DB (extension allow/deny lists,
size limits, double-extension detection, quarantine, storage-path
containment, per-user quota enforcement, and the audit trail). Before writing
any test here the full ~1270-line module was read function-by-function; every
assertion below is pinned to what the code ACTUALLY does (confirmed by
executing the relevant snippets directly), not to what "secure_filename +
size cap" would conventionally look like. Two notable, deliberately-tested
findings from that reading:

  * `secure_file_path()` does NOT call `werkzeug.secure_filename` at all. Its
    only traversal defense is resolving `item.storage_path` to an absolute
    path and requiring it be `.relative_to(storage_root())` -- any path
    (however it was constructed) that resolves outside the storage root is
    rejected with ValueError. See
    test_secure_file_path_rejects_path_outside_storage_root.

  * `_has_double_extension_risk()` flags a risky marker extension only when
    something follows it in the (dot-normalized) filename -- i.e. it catches
    a HIDDEN risky extension embedded before the final suffix (e.g.
    "invoice.exe.pdf"), not a risky extension that is itself the final
    suffix (e.g. "invoice.pdf.exe" returns False from this helper). The
    latter shape is instead caught earlier by `validate_upload_request()`'s
    direct `blocked_extensions()` check on the real final suffix. Both shapes
    are tested explicitly below, each pinned to its real, distinct code path.

Uses a dedicated, module-scoped Flask app with its own throwaway SQLite DB
file and its own throwaway `FILE_CENTER_STORAGE_ROOT` directory (never the
project's real configured storage root) -- see `_build_app()`. Module scope
(not per-test) is used purely for speed (this repo's `create_app()` is heavy
per call); every test still gets full logical isolation because every row
and file it touches is keyed off a fresh, uniquely-generated user id/action
name created inside that test, so accumulated state from earlier tests in
this module can never be read back by a later assertion. `tmp_path` is
deliberately NOT used -- pytest's built-in `tmp_path` fixture throws
PermissionError on this machine because of Turkish characters in the Windows
user profile path (documented in tests/conftest.py and
tests/quality/test_rollback_live_release_contract_v1.py); `tempfile.mkdtemp()`
is used directly instead, matching the established workaround.
"""
from __future__ import annotations

import hashlib
import io
import itertools
import shutil
import tempfile
import uuid
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from werkzeug.datastructures import FileStorage

pytest_plugins: list[str] = []

_counter = itertools.count(1)


def _unique(prefix: str) -> str:
    return f"{prefix}{next(_counter):05d}{uuid.uuid4().hex[:6]}"


# ---------------------------------------------------------------------------
# Module-scoped isolated app (own SQLite file, own storage root)
# ---------------------------------------------------------------------------

_STATE: dict[str, Any] = {}


def _build_app():
    db_dir = Path(tempfile.mkdtemp(prefix="bys360_filecenter_db_"))
    storage_root_dir = Path(tempfile.mkdtemp(prefix="bys360_filecenter_storage_"))
    _STATE["db_dir"] = db_dir
    _STATE["storage_root"] = storage_root_dir
    db_path = db_dir / f"{uuid.uuid4().hex}.sqlite3"
    db_uri = "sqlite:///" + db_path.as_posix()

    # This fixture is module-scoped, so it cannot request pytest's own
    # function-scoped `monkeypatch` fixture (ScopeMismatch); a manually
    # owned pytest.MonkeyPatch() instance is used instead for every mutation
    # below -- both the Config class attributes and every os.environ
    # assignment -- so the single mp.undo() in the `app` fixture's teardown
    # restores all of them, not just the Config attributes.
    mp = pytest.MonkeyPatch()
    mp.setenv("APP_ENV", "testing")
    mp.setenv("FLASK_ENV", "testing")
    mp.setenv("TESTING", "true")
    mp.setenv("SECRET_KEY", "bys360-file-center-contract-secret-key-2026-min")
    mp.setenv("DATABASE_URL", db_uri)
    mp.setenv("FILE_CENTER_STORAGE_ROOT", str(storage_root_dir))
    mp.setenv("WTF_CSRF_ENABLED", "false")
    mp.setenv("MAIL_SUPPRESS_SEND", "true")
    mp.setenv("SCHEDULER_ENABLED", "false")
    mp.setenv("FLASK_SKIP_SCHEMA_VALIDATION", "1")
    mp.setenv("AUTO_REPAIR_SCHEMA", "false")
    mp.setenv("STRICT_SCHEMA_CHECK", "false")
    mp.setenv("REQUIRE_DOTENV_FILE", "false")
    mp.setenv("STRICT_ENV_VALIDATION", "false")
    # Leave FILE_CENTER_CLAMAV_ENABLED unset on purpose: several tests below
    # rely on the real, supported "ClamAV not configured" degrade path
    # (clamav_enabled() -> False) rather than mocking the scan subprocess.

    from app import create_app
    from config import Config

    mp.setattr(Config, "APP_ENV", "testing")
    mp.setattr(Config, "SQLALCHEMY_DATABASE_URI", db_uri)
    mp.setattr(Config, "SQLALCHEMY_ENGINE_OPTIONS", {})

    application = create_app()
    application.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SQLALCHEMY_DATABASE_URI=db_uri,
        FILE_CENTER_STORAGE_ROOT=str(storage_root_dir),
    )

    from app.extensions import db

    with application.app_context():
        db.create_all()

    _STATE["monkeypatch"] = mp
    return application


@pytest.fixture(scope="module")
def app():
    application = _build_app()
    yield application
    mp = _STATE.get("monkeypatch")
    if mp is not None:
        mp.undo()
    for key in ("storage_root", "db_dir"):
        path = _STATE.get(key)
        if path is not None:
            shutil.rmtree(path, ignore_errors=True)


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _create_user(app, *, role="personel"):
    from app.extensions import db
    from app.models import User

    with app.app_context():
        tag = _unique("fc")
        user = User(
            sicil_no=tag,
            email=f"{tag}@filecenter.contract.test",
            ad="FileCenter",
            soyad="Contract",
            role=role,
            is_active=True,
            must_change_password=False,
            must_set_security_question=False,
        )
        user.set_password("FileCenterContract1!")
        db.session.add(user)
        db.session.commit()
        return user.id


def _make_file_storage(filename, content=b"BYS360 file center contract payload", content_type="application/pdf"):
    return FileStorage(stream=io.BytesIO(content), filename=filename, content_type=content_type)


def _seed_quota_usage(app, user_id, *, used_bytes, file_count=1):
    from app.extensions import db
    from app.models.file_center_models import FileQuotaUsage

    with app.app_context():
        row = FileQuotaUsage(user_id=user_id, used_bytes=used_bytes, file_count=file_count)
        db.session.add(row)
        db.session.commit()


def _seed_user_quota_policy(app, user_id, *, max_storage_gb, hard_stop_enabled, label="Contract test policy"):
    from app.extensions import db
    from app.models.file_center_models import FileQuotaPolicy

    with app.app_context():
        policy = FileQuotaPolicy(
            scope_type="user",
            scope_value=str(user_id),
            label=label,
            max_storage_gb=max_storage_gb,
            max_single_file_gb=5,
            max_transfer_gb=20,
            warning_threshold_percent=80,
            hard_stop_enabled=hard_stop_enabled,
            is_active=True,
        )
        db.session.add(policy)
        db.session.commit()


# ---------------------------------------------------------------------------
# validate_upload_request()
# ---------------------------------------------------------------------------


def test_validate_upload_request_accepts_allowed_file_within_limit(app):
    """Positive path: a normal, allowed file with no oversized declared
    Content-Length passes cleanly."""
    from app.file_center.services import validate_upload_request

    with app.test_request_context("/file-center/upload", method="POST"):
        fs = _make_file_storage("Annual_Report_2026.pdf")
        ok, message = validate_upload_request(fs)

    assert ok is True
    assert message == "OK"


def test_validate_upload_request_rejects_blocked_extension(app):
    from app.file_center.services import validate_upload_request

    with app.test_request_context("/file-center/upload", method="POST"):
        fs = _make_file_storage("malware.exe", content_type="application/octet-stream")
        ok, message = validate_upload_request(fs)

    assert ok is False
    assert message == "Bu dosya türü güvenlik nedeniyle yüklenemez: .exe"


def test_validate_upload_request_rejects_oversized_declared_content_length(app):
    """The size gate here reads the real Flask `request.content_length`
    (the incoming HTTP request's declared size), not any attribute on the
    FileStorage object -- confirmed by reading the source line-by-line."""
    from app.file_center.services import validate_upload_request

    max_bytes = 1000
    with app.test_request_context("/file-center/upload", method="POST", content_length=max_bytes + 1):
        fs = _make_file_storage("video.mp4", content_type="video/mp4")
        ok, message = validate_upload_request(fs, max_bytes=max_bytes)

    assert ok is False
    assert message == "Dosya boyutu izin verilen sınırı aşıyor."


def test_validate_upload_request_accepts_when_declared_length_within_limit(app):
    from app.file_center.services import validate_upload_request

    max_bytes = 1000
    with app.test_request_context("/file-center/upload", method="POST", content_length=max_bytes - 1):
        fs = _make_file_storage("small.pdf")
        ok, message = validate_upload_request(fs, max_bytes=max_bytes)

    assert (ok, message) == (True, "OK")


def test_validate_upload_request_rejects_extension_outside_per_request_allowlist(app):
    """A file-request-scoped allowlist (allowed_extensions=".docx") rejects
    an otherwise-fine, non-blocked extension (.pdf) that isn't on that
    specific list."""
    from app.file_center.services import validate_upload_request

    with app.test_request_context("/file-center/upload", method="POST"):
        fs = _make_file_storage("report.pdf")
        ok, message = validate_upload_request(fs, allowed_extensions=".docx")

    assert ok is False
    assert message == "Bu dosya türü bu talep için kabul edilmiyor: .pdf"


def test_validate_upload_request_accepts_extension_on_per_request_allowlist(app):
    from app.file_center.services import validate_upload_request

    with app.test_request_context("/file-center/upload", method="POST"):
        fs = _make_file_storage("report.docx", content_type="application/vnd.openxmlformats")
        ok, message = validate_upload_request(fs, allowed_extensions="pdf,docx")  # no leading dots

    assert (ok, message) == (True, "OK")


@pytest.mark.parametrize("file_storage_factory", [lambda: None, lambda: _make_file_storage("")])
def test_validate_upload_request_rejects_missing_file_or_empty_filename(app, file_storage_factory):
    from app.file_center.services import validate_upload_request

    with app.test_request_context("/file-center/upload", method="POST"):
        ok, message = validate_upload_request(file_storage_factory())

    assert ok is False
    assert message == "Dosya seçilmedi."


@pytest.mark.parametrize("filename", ["README", ".gitignore", ".env"])
def test_validate_upload_request_accepts_extension_less_filenames(app, filename):
    """Documented current behavior, not a recommendation: a filename with no
    real suffix (Path(...).suffix == "") is not rejected by any branch of
    validate_upload_request() when no allowlist is configured."""
    from app.file_center.services import validate_upload_request

    with app.test_request_context("/file-center/upload", method="POST"):
        fs = _make_file_storage(filename, content_type="text/plain")
        ok, message = validate_upload_request(fs)

    assert (ok, message) == (True, "OK")


def test_validate_upload_request_accepts_unusually_long_filename_without_crashing(app):
    """No filename-length guard exists anywhere in this function; a 300+
    character filename with an allowed extension must not raise and must
    still evaluate the real tuple contract."""
    from app.file_center.services import validate_upload_request

    long_name = ("a" * 300) + ".pdf"
    with app.test_request_context("/file-center/upload", method="POST"):
        fs = _make_file_storage(long_name)
        ok, message = validate_upload_request(fs)

    assert (ok, message) == (True, "OK")


# ---------------------------------------------------------------------------
# _extension_allowed_for_request() -- pure function, no app needed
# ---------------------------------------------------------------------------


def test_extension_allowed_for_request_normalizes_dots_and_separators():
    from app.file_center.services import _extension_allowed_for_request

    assert _extension_allowed_for_request(".pdf", None) is True
    assert _extension_allowed_for_request(".pdf", "") is True
    assert _extension_allowed_for_request(".pdf", "pdf,docx") is True  # leading dot optional in the list
    assert _extension_allowed_for_request(".PDF", ".pdf;.docx") is True  # caller ext case-normalized inside
    assert _extension_allowed_for_request(".pdf", ".docx;.xlsx") is False


# ---------------------------------------------------------------------------
# _has_double_extension_risk()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "filename",
    [
        "invoice.exe.pdf",       # risky marker hidden before the real final suffix
        "invoice.exe.txt",
        "quarterly_report.js.pdf",
        "photo.PDF.SCR.jpg",     # case-insensitive, marker not at the very end
    ],
)
def test_has_double_extension_risk_detects_hidden_marker_extension(filename):
    from app.file_center.services import _has_double_extension_risk

    assert _has_double_extension_risk(filename) is True


@pytest.mark.parametrize("filename", ["annual_report_2026_final.pdf", "photo.jpg", "notes.txt", None, ""])
def test_has_double_extension_risk_allows_benign_filenames(filename):
    from app.file_center.services import _has_double_extension_risk

    assert _has_double_extension_risk(filename) is False


def test_has_double_extension_risk_does_not_flag_marker_only_as_final_suffix():
    """Pinned, documented current behavior: when the risky marker IS the
    final suffix (nothing follows it after dot-normalization), this specific
    helper returns False -- that shape is caught elsewhere, by
    validate_upload_request()'s direct blocked_extensions() check on the
    real final suffix, not by this double-extension heuristic."""
    from app.file_center.services import _has_double_extension_risk

    assert _has_double_extension_risk("invoice.pdf.exe") is False
    assert _has_double_extension_risk("malware.exe") is False


# ---------------------------------------------------------------------------
# is_admin_like() -- pure function, no app needed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "user",
    [
        SimpleNamespace(role="admin", role_label="", username="x"),
        SimpleNamespace(role="sistem_yoneticisi", role_label="", username="x"),
        SimpleNamespace(role="personel", role_label="Yönetici", username="x"),
        SimpleNamespace(role="personel", role_label="", username="admin"),
    ],
)
def test_is_admin_like_matches_documented_admin_signals(user):
    from app.file_center.services import is_admin_like

    assert is_admin_like(user) is True


def test_is_admin_like_false_for_regular_personnel():
    from app.file_center.services import is_admin_like

    regular = SimpleNamespace(role="personel", role_label="Personel", username="user123")
    assert is_admin_like(regular) is False


# BYS360 DEFECT AQ: is_admin_like() önceden "admin" in role / "yönetici" in
# label biçiminde alt dize eşleştirmesi kullanıyordu -- aşağıdaki testler bu
# davranışın KALDIRILDIĞINI kilitler (önceki test sürümünde bu iki senaryo
# "documented admin signals" olarak True bekleniyordu; bu, düzeltilen
# güvenlik açığının kendisiydi).
@pytest.mark.parametrize(
    "user",
    [
        SimpleNamespace(role="birim_admin_full", role_label="", username="x"),
        SimpleNamespace(role="personel", role_label="İnsan Kaynakları Yöneticisi", username="x"),
        SimpleNamespace(role="personel", role_label="Yönetici Yardımcısı", username="x"),
        SimpleNamespace(role="office-admin", role_label="", username="x"),
    ],
)
def test_is_admin_like_denies_substring_lookalikes(user):
    from app.file_center.services import is_admin_like

    assert is_admin_like(user) is False


# ---------------------------------------------------------------------------
# blocked_extensions() / max_file_bytes() -- documented security defaults
# ---------------------------------------------------------------------------


def test_blocked_extensions_returns_documented_dangerous_defaults(app):
    from app.file_center.services import blocked_extensions

    with app.app_context():
        blocked = blocked_extensions()

    for dangerous in {".exe", ".bat", ".cmd", ".ps1", ".vbs", ".scr", ".dll", ".msi", ".js", ".jar", ".com", ".pif"}:
        assert dangerous in blocked


def test_max_file_bytes_defaults_to_five_gigabytes(app):
    from app.file_center.services import max_file_bytes

    with app.app_context():
        limit = max_file_bytes()

    assert limit == 5 * 1024 * 1024 * 1024


# ---------------------------------------------------------------------------
# save_uploaded_file()
# ---------------------------------------------------------------------------


def test_save_uploaded_file_writes_real_file_with_correct_hash_and_updates_quota(app):
    from app.extensions import db
    from app.file_center.services import save_uploaded_file, upload_root_for_user
    from app.models.file_center_models import FileAuditLog, FileQuotaUsage, FileSecurityScan

    user_id = _create_user(app)
    content = b"BYS360 file center behavioral contract payload." * 40

    with app.test_request_context("/file-center/upload", method="POST"):
        fs = _make_file_storage("Contract Report.pdf", content=content)
        item = save_uploaded_file(fs, user_id)
        item_id, storage_path = item.id, Path(item.storage_path)
        db.session.commit()

        # Read while still inside this request context: db.session.commit()
        # above expires item's attributes (expire_on_commit=True by
        # default), and exiting test_request_context() tears down /
        # removes the scoped session entirely -- reading `item.xxx` after
        # that point raises DetachedInstanceError rather than transparently
        # re-querying.
        assert item.size_bytes == len(content)
        assert item.sha256_hash == hashlib.sha256(content).hexdigest()
        assert item.status == "ready"
        assert item.scan_status == "pending"
        assert item.original_filename == "Contract Report.pdf"
        assert item.extension == ".pdf"

    assert storage_path.is_file()
    assert storage_path.read_bytes() == content

    with app.app_context():
        assert FileSecurityScan.query.filter_by(file_id=item_id, status="pending").count() == 1
        assert FileAuditLog.query.filter_by(file_id=item_id, action="file_uploaded").count() == 1
        usage = FileQuotaUsage.query.filter_by(user_id=user_id).one()
        assert usage.used_bytes == len(content)
        assert usage.file_count == 1
        assert list(upload_root_for_user(user_id).glob("*")) == [storage_path]


def test_save_uploaded_file_rejects_stream_exceeding_max_bytes_and_removes_partial_file(app):
    """The size cap enforced here is based on the ACTUAL bytes streamed off
    disk (accumulated while reading file_storage.stream), not any declared
    Content-Length header -- this defeats a spoofed or absent
    Content-Length. A rejected file must leave no partial file behind."""
    from app.file_center.services import save_uploaded_file, upload_root_for_user
    from app.models.file_center_models import FileStorageItem

    user_id = _create_user(app)
    content = b"x" * 5000

    with app.test_request_context("/file-center/upload", method="POST"):
        fs = _make_file_storage("huge.bin", content=content, content_type="application/octet-stream")
        with pytest.raises(ValueError, match="Dosya boyutu izin verilen sınırı aşıyor."):
            save_uploaded_file(fs, user_id, max_bytes=1000)

    with app.app_context():
        assert FileStorageItem.query.filter_by(owner_user_id=user_id).count() == 0
        assert list(upload_root_for_user(user_id).glob("*")) == []


def test_save_uploaded_file_raises_and_persists_nothing_when_quota_hard_stop_blocks(app):
    """Proves exceeding quota with hard_stop_enabled actually BLOCKS the
    upload (raises before any bytes are written), not merely records a
    number for later reporting."""
    from app.file_center.services import save_uploaded_file, upload_root_for_user
    from app.models.file_center_models import FileStorageItem

    user_id = _create_user(app)
    _seed_quota_usage(app, user_id, used_bytes=10_000_000, file_count=1)
    _seed_user_quota_policy(app, user_id, max_storage_gb=0.001, hard_stop_enabled=True)  # ~1.07MB cap

    with app.test_request_context("/file-center/upload", method="POST"):
        fs = _make_file_storage("new.pdf")
        with pytest.raises(
            ValueError,
            match="Depolama kotası dolduğu için dosya yüklenemedi. Kota artırımı için sistem yöneticisine başvurun.",
        ):
            save_uploaded_file(fs, user_id)

    with app.app_context():
        assert FileStorageItem.query.filter_by(owner_user_id=user_id).count() == 0
        assert list(upload_root_for_user(user_id).glob("*")) == []


# ---------------------------------------------------------------------------
# check_user_quota_for_upload() -- does exceeding quota actually block?
# ---------------------------------------------------------------------------


def test_check_user_quota_for_upload_blocks_when_hard_stop_enabled_and_over_limit(app):
    from app.file_center.services import check_user_quota_for_upload

    user_id = _create_user(app)
    _seed_quota_usage(app, user_id, used_bytes=10_000_000, file_count=3)
    _seed_user_quota_policy(app, user_id, max_storage_gb=0.001, hard_stop_enabled=True)

    with app.app_context():
        ok, message = check_user_quota_for_upload(user_id, estimated_bytes=0)

    assert ok is False
    assert message == "Depolama kotası dolduğu için dosya yüklenemedi. Kota artırımı için sistem yöneticisine başvurun."


def test_check_user_quota_for_upload_allows_when_hard_stop_disabled_despite_over_limit(app):
    """Same over-limit usage as the blocking test above, but
    hard_stop_enabled=False -- proves the quota system can be configured to
    only ever "record a number" (report over-limit via user_quota_summary)
    without actually blocking new uploads."""
    from app.file_center.services import check_user_quota_for_upload

    user_id = _create_user(app)
    _seed_quota_usage(app, user_id, used_bytes=10_000_000, file_count=3)
    _seed_user_quota_policy(app, user_id, max_storage_gb=0.001, hard_stop_enabled=False)

    with app.app_context():
        ok, message = check_user_quota_for_upload(user_id, estimated_bytes=0)

    assert ok is True
    assert message == "Kota kontrolü uygun."


def test_check_user_quota_for_upload_allows_unknown_user_id(app):
    """Guard-clause branch: a user_id with no matching User row is not
    treated as an error -- the quota check is explicitly passed through."""
    from app.file_center.services import check_user_quota_for_upload

    with app.app_context():
        ok, message = check_user_quota_for_upload(999_999_999, estimated_bytes=10)

    assert ok is True
    assert message == "Kullanıcı bulunamadı; kota kontrolü pas geçildi."


# ---------------------------------------------------------------------------
# update_quota_for_user()
# ---------------------------------------------------------------------------


def test_update_quota_for_user_sums_only_non_deleted_files(app):
    from app.extensions import db
    from app.core.datetime_utils import utc_now
    from app.file_center.services import update_quota_for_user
    from app.models.file_center_models import FileQuotaUsage, FileStorageItem

    user_id = _create_user(app)

    def _item(size, deleted=False):
        return FileStorageItem(
            owner_user_id=user_id,
            original_filename=f"f-{size}.pdf",
            stored_filename=f"f-{size}.pdf",
            storage_path=f"placeholder-{uuid.uuid4().hex}",
            extension=".pdf",
            size_bytes=size,
            sha256_hash=uuid.uuid4().hex + uuid.uuid4().hex,
            status="ready",
            scan_status="pending",
            is_deleted=deleted,
            deleted_at=utc_now() if deleted else None,
            deleted_by_user_id=user_id if deleted else None,
        )

    with app.app_context():
        db.session.add(_item(1000))
        db.session.add(_item(2500))
        db.session.add(_item(9999, deleted=True))
        db.session.commit()

        update_quota_for_user(user_id)
        db.session.commit()

        usage = FileQuotaUsage.query.filter_by(user_id=user_id).one()
        assert usage.used_bytes == 3500
        assert usage.file_count == 2


def test_update_quota_for_user_updates_existing_row_without_duplicating(app):
    from app.extensions import db
    from app.file_center.services import update_quota_for_user
    from app.models.file_center_models import FileQuotaUsage, FileStorageItem

    user_id = _create_user(app)

    with app.app_context():
        db.session.add(FileStorageItem(
            owner_user_id=user_id, original_filename="a.pdf", stored_filename="a.pdf",
            storage_path=f"placeholder-{uuid.uuid4().hex}", extension=".pdf", size_bytes=1000,
            sha256_hash=uuid.uuid4().hex + uuid.uuid4().hex, status="ready", scan_status="pending",
        ))
        db.session.commit()
        update_quota_for_user(user_id)
        db.session.commit()
        assert FileQuotaUsage.query.filter_by(user_id=user_id).count() == 1
        assert FileQuotaUsage.query.filter_by(user_id=user_id).one().used_bytes == 1000

        db.session.add(FileStorageItem(
            owner_user_id=user_id, original_filename="b.pdf", stored_filename="b.pdf",
            storage_path=f"placeholder-{uuid.uuid4().hex}", extension=".pdf", size_bytes=4000,
            sha256_hash=uuid.uuid4().hex + uuid.uuid4().hex, status="ready", scan_status="pending",
        ))
        db.session.commit()
        update_quota_for_user(user_id)
        db.session.commit()

        assert FileQuotaUsage.query.filter_by(user_id=user_id).count() == 1  # still one row, not two
        refreshed = FileQuotaUsage.query.filter_by(user_id=user_id).one()
        assert refreshed.used_bytes == 5000
        assert refreshed.file_count == 2


# ---------------------------------------------------------------------------
# secure_file_path()
# ---------------------------------------------------------------------------


def test_secure_file_path_returns_resolved_path_for_file_inside_storage_root(app):
    from app.extensions import db
    from app.file_center.services import save_uploaded_file, secure_file_path

    user_id = _create_user(app)
    with app.test_request_context("/file-center/upload", method="POST"):
        fs = _make_file_storage("inside.pdf")
        item = save_uploaded_file(fs, user_id)
        db.session.commit()
        item_id = item.id

    with app.app_context():
        from app.models.file_center_models import FileStorageItem
        refreshed = FileStorageItem.query.get(item_id)
        resolved = secure_file_path(refreshed)
        assert resolved == Path(refreshed.storage_path).resolve()
        assert resolved.is_file()


@pytest.mark.parametrize(
    "build_storage_path",
    [
        lambda root, user_id: str(Path(tempfile.gettempdir()) / "bys360_outside_root_probe" / "secret.txt"),
        lambda root, user_id: str(root / "uploads" / str(user_id) / ".." / ".." / ".." / ".." / "outside_traversal.txt"),
    ],
    ids=["different_absolute_directory", "dot_dot_traversal_style_path"],
)
def test_secure_file_path_rejects_path_outside_storage_root(app, build_storage_path):
    """The real path-safety mechanism here is containment (relative_to the
    resolved storage root), not filename sanitization -- confirmed by
    reading the function: it never calls secure_filename. Any storage_path
    that resolves outside the root, whatever shape produced it, is
    rejected with ValueError BEFORE any filesystem existence check, so no
    real file needs to exist at the traversal target for this to fire."""
    from app.file_center.services import secure_file_path, storage_root
    from app.models.file_center_models import FileStorageItem
    from app.extensions import db

    user_id = _create_user(app)
    with app.app_context():
        root = storage_root()
        outside_path = build_storage_path(root, user_id)
        item = FileStorageItem(
            owner_user_id=user_id, original_filename="secret.txt", stored_filename="secret.txt",
            storage_path=outside_path, extension=".txt", size_bytes=10,
            sha256_hash=uuid.uuid4().hex + uuid.uuid4().hex, status="ready", scan_status="pending",
        )
        db.session.add(item)
        db.session.commit()

        with pytest.raises(ValueError):
            secure_file_path(item)


def test_secure_file_path_raises_filenotfound_when_physically_missing(app):
    from app.extensions import db
    from app.file_center.services import secure_file_path, storage_root, upload_root_for_user
    from app.models.file_center_models import FileStorageItem

    user_id = _create_user(app)
    with app.app_context():
        missing_path = upload_root_for_user(user_id) / "ghost_file.pdf"
        item = FileStorageItem(
            owner_user_id=user_id, original_filename="ghost.pdf", stored_filename="ghost_file.pdf",
            storage_path=str(missing_path), extension=".pdf", size_bytes=10,
            sha256_hash=uuid.uuid4().hex + uuid.uuid4().hex, status="ready", scan_status="pending",
        )
        db.session.add(item)
        db.session.commit()

        with pytest.raises(FileNotFoundError, match="Dosya fiziksel depoda bulunamadı."):
            secure_file_path(item)


# ---------------------------------------------------------------------------
# run_security_scan() -- integration of _has_double_extension_risk(),
# _global_extension_allowed(), quarantine, and clamav's real disabled path
# ---------------------------------------------------------------------------


def test_run_security_scan_quarantines_file_with_hidden_double_extension(app):
    """End-to-end: a file saved with an allowed final extension (.pdf) but a
    risky marker hidden earlier in the original filename ("invoice.exe.pdf")
    must be quarantined by the real scan, and the physical file must
    actually be moved into the quarantine area on disk (not just a status
    flag flip)."""
    from app.extensions import db
    from app.file_center.services import run_security_scan, save_uploaded_file
    from app.models.file_center_models import FileAuditLog, FileStorageItem

    user_id = _create_user(app)
    with app.test_request_context("/file-center/upload", method="POST"):
        fs = _make_file_storage("invoice.exe.pdf")
        item = save_uploaded_file(fs, user_id)
        db.session.commit()
        item_id = item.id
        original_path = Path(item.storage_path)
        assert original_path.is_file()

        scan = run_security_scan(item, actor_user_id=user_id, force=True)
        db.session.commit()

        # Read while still inside this request context -- see the comment
        # in test_save_uploaded_file_writes_real_file_with_correct_hash_and_updates_quota
        # above: exiting test_request_context() removes the scoped session,
        # and the preceding commit() already expired scan's attributes.
        assert scan.status == "quarantined"
        assert scan.result_message == "Dosya adında çift uzantı/riskli uzantı izi bulundu."

    with app.app_context():
        refreshed = FileStorageItem.query.get(item_id)
        assert refreshed.scan_status == "quarantined"
        assert refreshed.status == "quarantined"
        assert not original_path.exists()  # moved away from its original location
        new_path = Path(refreshed.storage_path)
        assert new_path.is_file()
        assert "quarantine" in new_path.parts
        assert FileAuditLog.query.filter_by(file_id=item_id, action="file_quarantined").count() == 1


def test_run_security_scan_quarantines_blocked_extension_independently(app):
    """save_uploaded_file() itself does NOT enforce blocked_extensions() (that
    is validate_upload_request()'s job at the route layer) -- so a .exe can
    genuinely land in storage. This proves run_security_scan() is a real,
    independent second line of defense that still catches it."""
    from app.extensions import db
    from app.file_center.services import run_security_scan, save_uploaded_file
    from app.models.file_center_models import FileStorageItem

    user_id = _create_user(app)
    with app.test_request_context("/file-center/upload", method="POST"):
        fs = _make_file_storage("tool.exe", content_type="application/x-msdownload")
        item = save_uploaded_file(fs, user_id)
        db.session.commit()
        item_id = item.id

        scan = run_security_scan(item, actor_user_id=user_id, force=True)
        db.session.commit()

        assert scan.status == "quarantined"
        assert scan.result_message == "Riskli dosya uzantısı engellendi: .exe"
    with app.app_context():
        refreshed = FileStorageItem.query.get(item_id)
        assert refreshed.scan_status == "quarantined"


def test_run_security_scan_marks_clean_via_heuristic_when_clamav_genuinely_disabled(app):
    """Uses the real, supported "ClamAV not configured" degrade path
    (clamav_enabled() reading its real False default in this test env)
    rather than mocking the scan subprocess, per this module's own
    documented design for environments without a clamav binary."""
    from app.extensions import db
    from app.file_center.services import clamav_enabled, run_security_scan, save_uploaded_file
    from app.models.file_center_models import FileAuditLog, FileStorageItem

    user_id = _create_user(app)
    with app.app_context():
        assert clamav_enabled() is False  # confirms the real disabled gate, not an assumption

    with app.test_request_context("/file-center/upload", method="POST"):
        fs = _make_file_storage("clean_document.pdf")
        item = save_uploaded_file(fs, user_id)
        db.session.commit()
        item_id = item.id

        scan = run_security_scan(item, actor_user_id=user_id, force=True)
        db.session.commit()

        assert scan.status == "clean"
        assert scan.scanner == "file_center_heuristic_v1l"
    with app.app_context():
        refreshed = FileStorageItem.query.get(item_id)
        assert refreshed.status == "ready"
        assert refreshed.scan_status == "clean"
        assert FileAuditLog.query.filter_by(file_id=item_id, action="file_security_scan_clean").count() == 1


# ---------------------------------------------------------------------------
# log_audit() / log_access()
# ---------------------------------------------------------------------------


def test_log_audit_persists_row_with_explicit_actor_and_request_metadata(app):
    from app.extensions import db
    from app.file_center.services import log_audit
    from app.models.file_center_models import FileAuditLog

    user_id = _create_user(app)
    action_name = _unique("contract_audit_action_")

    with app.test_request_context(
        "/file-center/anything",
        method="POST",
        headers={"X-Forwarded-For": "203.0.113.7", "User-Agent": "BYS360-Contract-Agent/1.0"},
    ):
        log_audit(action_name, file_id=None, message="contract audit message", actor_user_id=user_id)
        db.session.commit()

    with app.app_context():
        row = FileAuditLog.query.filter_by(action=action_name).one()
        assert row.actor_user_id == user_id
        assert row.message == "contract audit message"
        assert row.ip_address == "203.0.113.7"
        assert row.user_agent == "BYS360-Contract-Agent/1.0"


def test_log_audit_falls_back_to_anonymous_current_user_when_actor_not_given(app):
    """Distinct branch from the explicit-actor test above: with no
    actor_user_id passed and no logged-in session, the current_user
    fallback must resolve to an anonymous user (actor stays None) rather
    than raising."""
    from app.extensions import db
    from app.file_center.services import log_audit
    from app.models.file_center_models import FileAuditLog

    action_name = _unique("contract_audit_anonymous_")

    with app.test_request_context("/file-center/anything", method="POST"):
        log_audit(action_name, file_id=None, message="anonymous actor path")
        db.session.commit()

    with app.app_context():
        row = FileAuditLog.query.filter_by(action=action_name).one()
        assert row.actor_user_id is None


def test_log_access_persists_row_with_detail_and_request_metadata(app):
    from app.extensions import db
    from app.file_center.services import log_access
    from app.models.file_center_models import FileAccessLog

    user_id = _create_user(app)
    action_name = _unique("contract_access_action_")

    with app.test_request_context(
        "/file-center/anything",
        method="GET",
        headers={"X-Forwarded-For": "198.51.100.9", "User-Agent": "BYS360-Contract-Access/1.0"},
    ):
        log_access(action_name, file_id=None, detail="contract access detail", actor_user_id=user_id)
        db.session.commit()

    with app.app_context():
        row = FileAccessLog.query.filter_by(action=action_name).one()
        assert row.actor_user_id == user_id
        assert row.detail == "contract access detail"
        assert row.ip_address == "198.51.100.9"
        assert row.user_agent == "BYS360-Contract-Access/1.0"
