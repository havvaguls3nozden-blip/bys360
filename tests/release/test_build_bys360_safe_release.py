"""Focused + adversarial tests for scripts/release/build_bys360_safe_release.py
(the canonical, deterministic, git-tracked-only production release builder).

BYS360 deterministic-package-builder hardening wave (2026-08-23). Every test
uses a real, disposable git repository under tmp_path (the established
pattern already used by tests/quality/test_bys360_score_reconcile_v1.py's
test_registry_matches_scored_commit_tree_rejects_parent_scored_child_registry_substitution)
-- no mocking of git or of the builder's own functions. Adapted from Agent 3's
25-scenario adversarial design (this wave's coordinator dispatch), grounded
against the real, implemented function signatures.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import zipfile
from pathlib import Path

import pytest

_MODULE_PATH = (
    Path(__file__).resolve().parents[2] / "scripts" / "release" / "build_bys360_safe_release.py"
)
_spec = importlib.util.spec_from_file_location("build_bys360_safe_release", _MODULE_PATH)
assert _spec is not None
assert _spec.loader is not None
builder = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(builder)


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    )


def _head(cwd: Path) -> str:
    return _git(["rev-parse", "HEAD"], cwd).stdout.strip()


BASE_FILES: dict[str, bytes] = {
    "app/__init__.py": b"# app init\n",
    "app/routes.py": b"# routes\n",
    "templates/index.html": b"<html></html>\n",
    "static/app.js": b"console.log(1);\n",
    "migrations/versions/0001_init.py": b"# migration\n",
    "requirements.txt": b"flask\n",
    "wsgi.py": b"# wsgi\n",
    "run_server.py": b"# run server\n",
    "config.py": b"# config\n",
    "DEPLOYMENT.md": b"# deploy docs\n",
}


def _write_files(root: Path, files: dict[str, bytes]) -> None:
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)


def _init_repo(root: Path, files: dict[str, bytes]) -> str:
    root.mkdir(parents=True, exist_ok=True)
    _git(["init", "-q"], root)
    _git(["config", "user.email", "t@t.com"], root)
    _git(["config", "user.name", "t"], root)
    _write_files(root, files)
    _git(["add", "-A"], root)
    _git(["commit", "-q", "-m", "init"], root)
    return _head(root)


def _commit_all(root: Path, message: str = "update") -> str:
    _git(["add", "-A"], root)
    _git(["commit", "-q", "-m", message], root)
    return _head(root)


@pytest.fixture
def repo(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "repo"
    sha = _init_repo(root, BASE_FILES)
    return root, sha


def _build(root: Path, output: Path, *, source_sha: str | None = None) -> int:
    argv = ["--root", str(root), "--output", str(output)]
    if source_sha is not None:
        argv += ["--source-sha", source_sha]
    return builder.main(argv)


def _verify(zip_path: Path, *, expected_source_sha: str | None = None) -> int:
    argv = ["--verify", str(zip_path)]
    if expected_source_sha is not None:
        argv += ["--expected-source-sha", expected_source_sha]
    return builder.main(argv)


def _names(zip_path: Path) -> set[str]:
    with zipfile.ZipFile(zip_path) as zf:
        return set(zf.namelist())


def _sidecars(output: Path) -> tuple[Path, Path]:
    return builder._default_sidecar_paths(output)


# ---------------------------------------------------------------------------
# 1-3: untracked contamination must have zero effect on output
# ---------------------------------------------------------------------------


def test_untracked_random_file_cannot_enter(repo, tmp_path):
    root, sha = repo
    (root / "random_untracked.txt").write_bytes(b"not tracked\n")
    output = tmp_path / "out1.zip"
    assert _build(root, output) == 0
    assert "random_untracked.txt" not in _names(output)


def test_untracked_coverage_file_cannot_enter(repo, tmp_path):
    root, sha = repo
    (root / ".coverage").write_bytes(b"coverage-binary-data")
    output = tmp_path / "out2.zip"
    assert _build(root, output) == 0
    assert ".coverage" not in _names(output)


def test_untracked_secret_looking_file_cannot_enter(repo, tmp_path):
    root, sha = repo
    (root / ".env").write_bytes(b"SECRET_KEY=untracked-should-never-ship\n")
    output = tmp_path / "out3.zip"
    assert _build(root, output) == 0
    assert ".env" not in _names(output)


# ---------------------------------------------------------------------------
# 4-8: hard-excluded directories
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "rel_path",
    [
        "tests/test_something.py",
        "mobile_flutter/lib/main.dart",
        ".codex/config.toml",
        ".claude/settings.json",
        "reports/quality/some_report.json",
    ],
)
def test_hard_excluded_directory_is_excluded(repo, tmp_path, rel_path):
    root, _ = repo
    _write_files(root, {rel_path: b"content\n"})
    sha = _commit_all(root)
    output = tmp_path / f"out_{rel_path.split('/')[0].strip('.')}.zip"
    assert _build(root, output, source_sha=sha) == 0
    assert rel_path not in _names(output)


# ---------------------------------------------------------------------------
# 9-13: required content survives
# ---------------------------------------------------------------------------


def test_required_content_survives(repo, tmp_path):
    root, sha = repo
    output = tmp_path / "out_required.zip"
    assert _build(root, output, source_sha=sha) == 0
    names = _names(output)
    for expected in (
        "app/__init__.py",
        "app/routes.py",
        "templates/index.html",
        "static/app.js",
        "migrations/versions/0001_init.py",
        "requirements.txt",
        "wsgi.py",
        "run_server.py",
        "config.py",
        "DEPLOYMENT.md",
    ):
        assert expected in names, f"{expected} missing from package"


# ---------------------------------------------------------------------------
# 14: .env / secret path rejected even if (hypothetically) tracked
# ---------------------------------------------------------------------------


def test_tracked_env_file_rejected(repo, tmp_path):
    root, _ = repo
    _write_files(root, {".env": b"SECRET_KEY=should-never-ship\n"})
    sha = _commit_all(root)
    output = tmp_path / "out_env.zip"
    assert _build(root, output, source_sha=sha) == 0
    assert ".env" not in _names(output)


def test_key_and_pem_suffixes_rejected(repo, tmp_path):
    root, _ = repo
    _write_files(root, {"secrets/prod.key": b"key\n", "secrets/prod.pem": b"pem\n"})
    sha = _commit_all(root)
    output = tmp_path / "out_keys.zip"
    assert _build(root, output, source_sha=sha) == 0
    names = _names(output)
    assert "secrets/prod.key" not in names
    assert "secrets/prod.pem" not in names


# ---------------------------------------------------------------------------
# FINAL package required-content blocker closure (2026-08-24): "archive" was
# a bare-segment entry in FORBIDDEN_DIR_PARTS, so it matched ANY path
# segment literally named "archive" -- including the real, git-tracked
# Flask template directory app/templates/performance/archive/ (a live
# feature). Separately, the .env forbidden-name regex matched
# .env.example/.env.docker.example (legitimate operator config templates,
# not secrets), because it only checked for ".env" immediately followed by
# end-of-segment or a literal dot. Both false positives were confirmed via
# a full-repository forensic scan before being fixed -- these tests pin the
# exact repository-grounded fix: "archive" stays forbidden everywhere
# EXCEPT under app/ (docs/archive/, reports/archive/, scripts/archive/ all
# still exist as genuinely historical content and must stay excluded); real
# .env secret files stay forbidden via an explicit basename allowlist for
# the two known-safe templates, not a broadened regex.
# ---------------------------------------------------------------------------


def test_app_performance_archive_templates_included(repo, tmp_path):
    root, _ = repo
    _write_files(root, {
        "app/templates/performance/archive/index.html": b"<html>archive index</html>\n",
        "app/templates/performance/archive/detail.html": b"<html>archive detail</html>\n",
        "app/templates/performance/archive/_premium_styles.html": b"<style></style>\n",
    })
    sha = _commit_all(root)
    output = tmp_path / "out_app_archive.zip"
    assert _build(root, output, source_sha=sha) == 0
    names = _names(output)
    assert "app/templates/performance/archive/index.html" in names
    assert "app/templates/performance/archive/detail.html" in names
    assert "app/templates/performance/archive/_premium_styles.html" in names


def test_docs_archive_storage_still_excluded(repo, tmp_path):
    root, _ = repo
    _write_files(root, {"docs/archive/old_note.md": b"# old\n"})
    sha = _commit_all(root)
    output = tmp_path / "out_docs_archive.zip"
    assert _build(root, output, source_sha=sha) == 0
    assert "docs/archive/old_note.md" not in _names(output)


def test_scripts_archive_storage_still_excluded(repo, tmp_path):
    root, _ = repo
    _write_files(root, {"scripts/archive/old_tool.py": b"# old\n"})
    sha = _commit_all(root)
    output = tmp_path / "out_scripts_archive.zip"
    assert _build(root, output, source_sha=sha) == 0
    assert "scripts/archive/old_tool.py" not in _names(output)


@pytest.mark.parametrize("env_name", [".env", ".env.local", ".env.production"])
def test_real_env_secret_variants_forbidden(repo, tmp_path, env_name):
    root, _ = repo
    _write_files(root, {env_name: b"SECRET_KEY=real-value-should-never-ship\n"})
    sha = _commit_all(root)
    output = tmp_path / f"out_{env_name.replace('.', '_')}.zip"
    assert _build(root, output, source_sha=sha) == 0
    assert env_name not in _names(output)


@pytest.mark.parametrize("env_name", [".env.example", ".env.docker.example"])
def test_env_example_templates_allowed(repo, tmp_path, env_name):
    root, _ = repo
    _write_files(root, {env_name: b"SECRET_KEY=replace-with-a-strong-random-value\n"})
    sha = _commit_all(root)
    output = tmp_path / f"out_{env_name.replace('.', '_')}.zip"
    assert _build(root, output, source_sha=sha) == 0
    assert env_name in _names(output)


def test_full_required_scope_has_zero_missing_files(repo, tmp_path):
    """The exact full file-by-file comparison that caught the original
    defect: every git-tracked file under app/ (plus the other required
    root files) must appear in the package unless it hits an unrelated,
    still-legitimate exclusion rule."""
    root, sha = repo
    _write_files(root, {
        "app/templates/performance/archive/index.html": b"<html></html>\n",
        "app/deep/nested/module.py": b"# module\n",
    })
    sha = _commit_all(root)
    output = tmp_path / "out_full_scope.zip"
    assert _build(root, output, source_sha=sha) == 0
    names = _names(output)
    tracked_app = [
        line for line in _git(["ls-files"], root).stdout.splitlines() if line.startswith("app/")
    ]
    missing = [p for p in tracked_app if p not in names]
    assert missing == []


def test_forbidden_content_scan_zero_after_fix(repo, tmp_path):
    root, _ = repo
    _write_files(root, {
        "app/templates/performance/archive/index.html": b"<html></html>\n",
        "docs/archive/note.md": b"# note\n",
        "scripts/archive/old.py": b"# old\n",
        ".env.example": b"SECRET_KEY=replace-with-a-strong-random-value\n",
        "tests/some_test.py": b"# test\n",
    })
    sha = _commit_all(root)
    output = tmp_path / "out_forbidden_scan.zip"
    assert _build(root, output, source_sha=sha) == 0
    findings = builder.scan_zip(output)
    assert findings == []


def test_secret_gate_still_rejects_actual_secret_material(repo, tmp_path):
    """Not the release builder itself -- confirms the repository's real
    secret gate (bys360_secret_repo_gate.py) still flags a hardcoded secret
    value even in a file whose NAME the release builder now allows through
    (.env.example), proving the packaging-rule fix did not weaken the
    separate, independent secret-content safety net."""
    import importlib.util as _ilu

    secret_gate_path = (
        Path(__file__).resolve().parents[2] / "scripts" / "quality" / "bys360_secret_repo_gate.py"
    )
    spec = _ilu.spec_from_file_location("bys360_secret_repo_gate", secret_gate_path)
    assert spec is not None
    assert spec.loader is not None
    gate = _ilu.module_from_spec(spec)
    spec.loader.exec_module(gate)

    root, _ = repo
    fixture_line = 'SECRET_KEY="a-genuinely-long-hardcoded-secret-value-1234567890"\n'  # hardcoded_secret fixture
    (root / ".env.example").write_text(fixture_line, encoding="utf-8")
    _commit_all(root)
    result = gate.run(root)
    assert result["ok"] is False
    assert result["finding_count"] >= 1


# ---------------------------------------------------------------------------
# 15: unsafe symlink / path traversal fail closed
# ---------------------------------------------------------------------------


def test_is_unsafe_archive_path_rejects_traversal_and_absolute_names():
    unsafe = [
        "../etc/passwd",
        "/etc/passwd",
        "a/../../b",
        "a/../b",
        "C:/windows/system32/x",
        "C:\\windows\\x",
        "..",
        "a/..",
    ]
    for name in unsafe:
        assert builder.is_unsafe_archive_path(name), f"expected unsafe: {name!r}"
    safe = ["app/__init__.py", "a/b/c.txt", "requirements.txt"]
    for name in safe:
        assert not builder.is_unsafe_archive_path(name), f"expected safe: {name!r}"


def test_tracked_symlink_excluded_if_creatable(repo, tmp_path):
    root, _ = repo
    target = root / "app" / "routes.py"
    link = root / "app" / "routes_link.py"
    try:
        os.symlink(target, link)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation not permitted in this environment")
    sha = _commit_all(root)
    # A symlink entry must never appear in the package -- either because it
    # was excluded (is_symlink() check) or because it wasn't a regular file.
    output = tmp_path / "out_symlink.zip"
    assert _build(root, output, source_sha=sha) == 0
    assert "app/routes_link.py" not in _names(output)


# ---------------------------------------------------------------------------
# 16-18: determinism (logical content, manifest, SHA256SUMS ordering)
# ---------------------------------------------------------------------------


def test_repeated_build_logical_content_identical(repo, tmp_path):
    root, sha = repo
    out1 = tmp_path / "out_a.zip"
    out2 = tmp_path / "out_b.zip"
    assert _build(root, out1, source_sha=sha) == 0
    assert _build(root, out2, source_sha=sha) == 0

    manifest1_path, sha256_1 = _sidecars(out1)
    manifest2_path, sha256_2 = _sidecars(out2)
    manifest1 = json.loads(manifest1_path.read_text(encoding="utf-8"))
    manifest2 = json.loads(manifest2_path.read_text(encoding="utf-8"))

    assert manifest1["files"] == manifest2["files"]
    assert manifest1["source_sha"] == manifest2["source_sha"] == sha
    assert sha256_1.read_text(encoding="utf-8") == sha256_2.read_text(encoding="utf-8")
    assert _names(out1) == _names(out2)


def test_manifest_files_are_sorted(repo, tmp_path):
    root, sha = repo
    output = tmp_path / "out_sorted.zip"
    assert _build(root, output, source_sha=sha) == 0
    manifest_path, _ = _sidecars(output)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["files"] == sorted(manifest["files"])


def test_sha256sums_lines_are_sorted_by_path(repo, tmp_path):
    root, sha = repo
    output = tmp_path / "out_sha_sorted.zip"
    assert _build(root, output, source_sha=sha) == 0
    _, sha256_path = _sidecars(output)
    lines = [line for line in sha256_path.read_text(encoding="utf-8").splitlines() if line]
    paths = [line.split("  ", 1)[1] for line in lines]
    assert paths == sorted(paths)
    assert sha256_path.read_text(encoding="utf-8").count("\r\n") == 0  # LF only


# ---------------------------------------------------------------------------
# 19-20: content sensitivity -- tracked change alters hash, excluded/untracked
# change does not alter output
# ---------------------------------------------------------------------------


def test_packaged_tracked_file_modification_changes_hash(repo, tmp_path):
    root, sha1 = repo
    out1 = tmp_path / "out_before.zip"
    assert _build(root, out1, source_sha=sha1) == 0
    _, sha256_1 = _sidecars(out1)
    hashes1 = dict(
        line.split("  ", 1)[::-1] for line in sha256_1.read_text(encoding="utf-8").splitlines() if line
    )

    (root / "app" / "routes.py").write_bytes(b"# routes CHANGED\n")
    sha2 = _commit_all(root, "modify routes")
    out2 = tmp_path / "out_after.zip"
    assert _build(root, out2, source_sha=sha2) == 0
    _, sha256_2 = _sidecars(out2)
    hashes2 = dict(
        line.split("  ", 1)[::-1] for line in sha256_2.read_text(encoding="utf-8").splitlines() if line
    )

    assert hashes1["app/routes.py"] != hashes2["app/routes.py"]


def test_excluded_or_untracked_change_does_not_change_output(repo, tmp_path):
    root, sha = repo
    out1 = tmp_path / "out_stable_1.zip"
    assert _build(root, out1, source_sha=sha) == 0
    _, sha256_1 = _sidecars(out1)
    before = sha256_1.read_text(encoding="utf-8")

    (root / "random_scratch.txt").write_bytes(b"untracked scratch\n")
    out2 = tmp_path / "out_stable_2.zip"
    assert _build(root, out2, source_sha=sha) == 0
    _, sha256_2 = _sidecars(out2)
    after = sha256_2.read_text(encoding="utf-8")

    assert before == after


# ---------------------------------------------------------------------------
# 21-22: fail-closed source integrity
# ---------------------------------------------------------------------------


def test_dirty_tracked_worktree_fails_closed(repo, tmp_path):
    root, sha = repo
    (root / "app" / "routes.py").write_bytes(b"# uncommitted change\n")
    output = tmp_path / "out_dirty.zip"
    rc = _build(root, output, source_sha=sha)
    assert rc != 0
    assert not output.exists() or output.stat().st_size == 0 or not zipfile.is_zipfile(output)


def test_dirty_staged_worktree_fails_closed(repo, tmp_path):
    root, sha = repo
    (root / "app" / "new_staged.py").write_bytes(b"# staged, not committed\n")
    _git(["add", "app/new_staged.py"], root)
    output = tmp_path / "out_staged_dirty.zip"
    rc = _build(root, output, source_sha=sha)
    assert rc != 0


def test_wrong_source_sha_fails_closed(repo, tmp_path):
    root, sha = repo
    wrong_sha = "0" * 40
    output = tmp_path / "out_wrong_sha.zip"
    rc = _build(root, output, source_sha=wrong_sha)
    assert rc != 0


def test_auto_resolved_source_sha_matches_head(repo, tmp_path):
    root, sha = repo
    output = tmp_path / "out_auto.zip"
    assert _build(root, output) == 0
    manifest_path, _ = _sidecars(output)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["source_sha"] == sha


# ---------------------------------------------------------------------------
# Baseline: a genuinely valid package passes --verify
# ---------------------------------------------------------------------------


def test_valid_package_passes_verify(repo, tmp_path):
    root, sha = repo
    output = tmp_path / "out_valid.zip"
    assert _build(root, output, source_sha=sha) == 0
    assert _verify(output, expected_source_sha=sha) == 0


# ---------------------------------------------------------------------------
# 23-25: verify mode adversarial tamper detection
# ---------------------------------------------------------------------------


def _rewrite_zip_with_extra_entry(src: Path, dst: Path, name: str, content: bytes) -> None:
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w") as zout:
        for item in zin.infolist():
            zout.writestr(item, zin.read(item.filename))
        zout.writestr(name, content)


def _rewrite_zip_without_prefix(src: Path, dst: Path, prefix: str) -> None:
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w") as zout:
        for item in zin.infolist():
            if item.filename.startswith(prefix):
                continue
            zout.writestr(item, zin.read(item.filename))


def test_forbidden_path_added_to_package_verify_fails(repo, tmp_path):
    root, sha = repo
    output = tmp_path / "out_tamper1.zip"
    assert _build(root, output, source_sha=sha) == 0
    manifest_path, sha256_path = _sidecars(output)

    tampered = tmp_path / "out_tamper1_tampered.zip"
    _rewrite_zip_with_extra_entry(output, tampered, ".env", b"SECRET_KEY=leaked\n")
    tampered_manifest, tampered_sha256 = _sidecars(tampered)
    tampered_manifest.write_text(manifest_path.read_text(encoding="utf-8"), encoding="utf-8")
    tampered_sha256.write_text(sha256_path.read_text(encoding="utf-8"), encoding="utf-8")

    assert _verify(tampered) != 0


def test_required_path_removed_verify_fails(repo, tmp_path):
    root, sha = repo
    output = tmp_path / "out_tamper2.zip"
    assert _build(root, output, source_sha=sha) == 0
    manifest_path, sha256_path = _sidecars(output)

    tampered = tmp_path / "out_tamper2_tampered.zip"
    _rewrite_zip_without_prefix(output, tampered, "app/")
    tampered_manifest, tampered_sha256 = _sidecars(tampered)
    tampered_manifest.write_text(manifest_path.read_text(encoding="utf-8"), encoding="utf-8")
    tampered_sha256.write_text(sha256_path.read_text(encoding="utf-8"), encoding="utf-8")

    result_rc = _verify(tampered)
    assert result_rc != 0


def test_path_traversal_entry_verify_fails(repo, tmp_path):
    root, sha = repo
    output = tmp_path / "out_tamper3.zip"
    assert _build(root, output, source_sha=sha) == 0
    manifest_path, sha256_path = _sidecars(output)

    tampered = tmp_path / "out_tamper3_tampered.zip"
    _rewrite_zip_with_extra_entry(output, tampered, "../outside.txt", b"escape\n")
    tampered_manifest, tampered_sha256 = _sidecars(tampered)
    tampered_manifest.write_text(manifest_path.read_text(encoding="utf-8"), encoding="utf-8")
    tampered_sha256.write_text(sha256_path.read_text(encoding="utf-8"), encoding="utf-8")

    assert _verify(tampered) != 0


def test_sha256_mismatch_verify_fails(repo, tmp_path):
    root, sha = repo
    output = tmp_path / "out_tamper4.zip"
    assert _build(root, output, source_sha=sha) == 0
    manifest_path, sha256_path = _sidecars(output)

    tampered = tmp_path / "out_tamper4_tampered.zip"
    with zipfile.ZipFile(output) as zin, zipfile.ZipFile(tampered, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "config.py":
                data = b"# TAMPERED CONTENT\n"
            zout.writestr(item, data)
    tampered_manifest, tampered_sha256 = _sidecars(tampered)
    tampered_manifest.write_text(manifest_path.read_text(encoding="utf-8"), encoding="utf-8")
    tampered_sha256.write_text(sha256_path.read_text(encoding="utf-8"), encoding="utf-8")

    assert _verify(tampered) != 0


def test_source_sha_metadata_mismatch_verify_fails(repo, tmp_path):
    root, sha = repo
    output = tmp_path / "out_tamper5.zip"
    assert _build(root, output, source_sha=sha) == 0
    assert _verify(output, expected_source_sha="1" * 40) != 0


def test_verify_missing_manifest_fails(tmp_path):
    fake_zip = tmp_path / "no_manifest.zip"
    with zipfile.ZipFile(fake_zip, "w") as zf:
        zf.writestr("app/__init__.py", b"x")
    assert _verify(fake_zip) != 0


# ---------------------------------------------------------------------------
# FULL build mode (candidate/cutover/rollback architecture wave, 2026-08-25):
# opt-in wheelhouse bundling + manifest schema_version=3. Every test above
# this point exercises the legacy path with zero new flags and must keep
# passing unchanged -- these new tests exercise only the new, additive path.
# ---------------------------------------------------------------------------

import hashlib as _hashlib  # noqa: E402


def _write_migration(root: Path, revision: str, down_revision: str | None) -> None:
    versions_dir = root / "migrations" / "versions"
    versions_dir.mkdir(parents=True, exist_ok=True)
    (versions_dir / f"{revision}_test.py").write_text(
        f'revision = "{revision}"\ndown_revision = {down_revision!r}\n'
        "def upgrade(): pass\ndef downgrade(): pass\n",
        encoding="utf-8",
    )


def _make_wheelhouse_fixture(tmp_path: Path) -> tuple[Path, Path]:
    """Two tiny fake wheels + a matching, genuinely-'ok' build report --
    mirrors the real shape scripts/release/build_bys360_wheelhouse.py
    produces (same field names), without needing a real 51MB wheelhouse in
    a unit test."""
    wheelhouse_dir = tmp_path / "build" / "wheelhouse"
    wheelhouse_dir.mkdir(parents=True)
    manifest_entries = []
    for name, version, content in (
        ("fakepkg_a", "1.0.0", b"fake wheel a content"),
        ("fakepkg_b", "2.0.0", b"fake wheel b content"),
    ):
        filename = f"{name}-{version}-py3-none-any.whl"
        (wheelhouse_dir / filename).write_bytes(content)
        manifest_entries.append({
            "name": name, "version": version, "filename": filename,
            "sha256": _hashlib.sha256(content).hexdigest(),
            "size_bytes": len(content), "pytag": "py3", "abitag": "none", "platform": "any",
        })
    report = {
        "package": "TEST_WHEELHOUSE_BUILDER", "generated_at": "2026-08-25T00:00:00",
        "wheel_count": len(manifest_entries),
        "total_bytes": sum(e["size_bytes"] for e in manifest_entries),
        "wheelhouse_identity_sha256": "0" * 64,
        "manifest": manifest_entries, "ok": True,
    }
    report_path = tmp_path / "reports" / "quality" / "BYS360_WHEELHOUSE_BUILD_REPORT.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report), encoding="utf-8")
    return wheelhouse_dir, report_path


def _full_build_repo(tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "full_repo"
    files = dict(BASE_FILES)
    # BASE_FILES' migrations/versions/0001_init.py is a placeholder comment,
    # not a real Alembic revision file (no revision/down_revision
    # attributes) -- resolve_migration_head() needs a genuine one instead.
    del files["migrations/versions/0001_init.py"]
    files["scripts/windows/prepare_bys360_candidate.ps1"] = b"# candidate\n"
    files["scripts/windows/cutover_bys360_candidate.ps1"] = b"# cutover\n"
    files["scripts/windows/rollback_bys360_candidate.ps1"] = b"# rollback\n"
    files["scripts/release/scan_bys360_release_secrets.py"] = b"# scanner\n"
    files["requirements.lock"] = b"fakepkg-a==1.0.0\nfakepkg-b==2.0.0\n"
    _init_repo(root, files)
    _write_migration(root, "abc123", None)
    sha = _commit_all(root, "add migration")
    _make_wheelhouse_fixture(root)
    return root, sha


def _full_build(root: Path, output: Path, *, source_sha: str | None = None) -> int:
    argv = ["--root", str(root), "--output", str(output), "--wheelhouse-dir", str(root / "build" / "wheelhouse")]
    if source_sha is not None:
        argv += ["--source-sha", source_sha]
    return builder.main(argv)


def test_full_build_bundles_wheelhouse_and_produces_schema_v3_manifest(tmp_path):
    root, sha = _full_build_repo(tmp_path)
    output = tmp_path / "full1.zip"
    assert _full_build(root, output, source_sha=sha) == 0

    names = _names(output)
    assert "wheelhouse/fakepkg_a-1.0.0-py3-none-any.whl" in names
    assert "wheelhouse/fakepkg_b-2.0.0-py3-none-any.whl" in names
    assert "requirements.lock" in names

    manifest_path, _ = _sidecars(output)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 3
    assert manifest["migration_head"] == "abc123"
    assert manifest["python_requirement"] == "3.12"
    assert manifest["platform_target"] == "win_amd64"
    assert manifest["wheelhouse_file_count"] == 2
    assert manifest["wheelhouse_total_bytes"] > 0
    assert manifest["wheelhouse_identity_sha256"] == "0" * 64
    assert len(manifest["requirements_lock_sha256"]) == 64
    assert len(manifest["candidate_script_sha256"]) == 64
    assert len(manifest["cutover_script_sha256"]) == 64
    assert len(manifest["rollback_script_sha256"]) == 64
    assert len(manifest["secret_scanner_sha256"]) == 64
    assert len(manifest["package_integrity_identity_sha256"]) == 64
    assert manifest["package_file_count"] == manifest["included_count"]
    assert manifest["source_short_sha"] == sha[:12]


def test_full_build_rejects_missing_wheel(tmp_path):
    root, sha = _full_build_repo(tmp_path)
    next((root / "build" / "wheelhouse").glob("fakepkg_a*")).unlink()
    output = tmp_path / "full_missing.zip"
    assert _full_build(root, output, source_sha=sha) == 2
    assert not output.exists()


def test_full_build_rejects_extra_unexpected_wheel(tmp_path):
    root, sha = _full_build_repo(tmp_path)
    (root / "build" / "wheelhouse" / "unexpected-9.9.9-py3-none-any.whl").write_bytes(b"intruder")
    output = tmp_path / "full_extra.zip"
    assert _full_build(root, output, source_sha=sha) == 2


def test_full_build_rejects_tampered_wheel_hash(tmp_path):
    root, sha = _full_build_repo(tmp_path)
    victim = next((root / "build" / "wheelhouse").glob("fakepkg_a*"))
    victim.write_bytes(victim.read_bytes() + b"TAMPERED")
    output = tmp_path / "full_tampered.zip"
    assert _full_build(root, output, source_sha=sha) == 2


def test_full_build_rejects_missing_wheelhouse_report(tmp_path):
    root, sha = _full_build_repo(tmp_path)
    (root / "reports" / "quality" / "BYS360_WHEELHOUSE_BUILD_REPORT.json").unlink()
    output = tmp_path / "full_noreport.zip"
    assert _full_build(root, output, source_sha=sha) == 2


def test_full_build_rejects_not_ok_wheelhouse_report(tmp_path):
    root, sha = _full_build_repo(tmp_path)
    report_path = root / "reports" / "quality" / "BYS360_WHEELHOUSE_BUILD_REPORT.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    report["ok"] = False
    report_path.write_text(json.dumps(report), encoding="utf-8")
    output = tmp_path / "full_notok.zip"
    assert _full_build(root, output, source_sha=sha) == 2


def test_full_build_verify_accepts_schema_v3(tmp_path):
    root, sha = _full_build_repo(tmp_path)
    output = tmp_path / "full_verify.zip"
    assert _full_build(root, output, source_sha=sha) == 0
    assert _verify(output, expected_source_sha=sha) == 0


def test_full_build_verify_rejects_wheelhouse_file_count_tamper(tmp_path):
    root, sha = _full_build_repo(tmp_path)
    output = tmp_path / "full_verify_tamper.zip"
    assert _full_build(root, output, source_sha=sha) == 0
    manifest_path, _ = _sidecars(output)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["wheelhouse_file_count"] = 999
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    assert _verify(output, expected_source_sha=sha) != 0


def test_full_build_deterministic_repeat(tmp_path):
    root, sha = _full_build_repo(tmp_path)
    output1 = tmp_path / "full_det1.zip"
    output2 = tmp_path / "full_det2.zip"
    assert _full_build(root, output1, source_sha=sha) == 0
    assert _full_build(root, output2, source_sha=sha) == 0
    assert output1.read_bytes() == output2.read_bytes()

    m1_path, s1_path = _sidecars(output1)
    m2_path, s2_path = _sidecars(output2)
    m1 = json.loads(m1_path.read_text(encoding="utf-8"))
    m2 = json.loads(m2_path.read_text(encoding="utf-8"))
    for key in m1:
        if key in ("generated_at", "sha256sums_file"):  # filename-derived, expected to differ across output names
            continue
        assert m1[key] == m2[key], f"manifest field diverged across identical builds: {key}"
    assert s1_path.read_text(encoding="utf-8") == s2_path.read_text(encoding="utf-8")


def test_legacy_build_without_wheelhouse_flag_stays_schema_v2(repo, tmp_path):
    root, sha = repo
    output = tmp_path / "legacy_still_v2.zip"
    assert _build(root, output, source_sha=sha) == 0
    manifest_path, _ = _sidecars(output)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 2
    assert "wheelhouse_file_count" not in manifest
    assert "wheelhouse/" not in " ".join(_names(output))


# ---------------------------------------------------------------------------
# Automatic assembled-release secret gate (schema-contract-drift wave
# close-out, 2026-08-25, section 5-7: "SECRET SCANNING MUST NOT REMAIN
# MANUAL ONLY"). scan_bys360_release_secrets.py is now wired directly into
# the FULL build path -- run_assembled_tree_secret_scan() extracts the
# just-built zip to a temp dir and scans THAT (the actual bytes that would
# ship), not the source tree. Real fixtures use only synthetic, clearly-fake
# secret material (never anything resembling a real credential).
# ---------------------------------------------------------------------------

def _full_build_repo_with_extra_files(tmp_path: Path, extra_files: dict[str, bytes]) -> tuple[Path, str]:
    """Same shape as _full_build_repo(), plus caller-supplied extra tracked
    files (used to plant secret-shaped or false-positive-shaped content in
    a specific file for one test, without duplicating the whole fixture)."""
    root = tmp_path / "full_repo"
    files = dict(BASE_FILES)
    del files["migrations/versions/0001_init.py"]
    files["scripts/windows/prepare_bys360_candidate.ps1"] = b"# candidate\n"
    files["scripts/windows/cutover_bys360_candidate.ps1"] = b"# cutover\n"
    files["scripts/windows/rollback_bys360_candidate.ps1"] = b"# rollback\n"
    files["scripts/release/scan_bys360_release_secrets.py"] = b"# scanner\n"
    files["requirements.lock"] = b"fakepkg-a==1.0.0\nfakepkg-b==2.0.0\n"
    files.update(extra_files)
    _init_repo(root, files)
    _write_migration(root, "abc123", None)
    sha = _commit_all(root, "add migration")
    _make_wheelhouse_fixture(root)
    return root, sha


def test_full_build_secret_gate_passes_on_clean_repo(tmp_path):
    root, sha = _full_build_repo(tmp_path)
    output = tmp_path / "secretgate_clean.zip"
    assert _full_build(root, output, source_sha=sha) == 0
    manifest_path, _ = _sidecars(output)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["secret_scan_status"] == "PASS"
    assert manifest["secret_scan_findings"] == 0
    assert manifest["secret_scan_scope"] == "assembled_release_tree"


def test_full_build_secret_gate_rejects_planted_secret_key(tmp_path):
    root, sha = _full_build_repo_with_extra_files(tmp_path, {
        "app/planted_config.py": (
            b"SECRET_KEY = 'kx8Qw2vRzT9pL4mN7bJ3dF6hY1sA5eC0'\n"
        ),
    })
    output = tmp_path / "secretgate_secret_key.zip"
    assert _full_build(root, output, source_sha=sha) == 2
    assert not output.exists(), "a package that fails the secret gate must never be left on disk as a deliverable"


def test_full_build_secret_gate_rejects_planted_database_url_password(tmp_path):
    root, sha = _full_build_repo_with_extra_files(tmp_path, {
        "app/planted_settings.py": (
            b"DATABASE_URL = 'postgresql://bys360_user:Tr0ub4dor-Genuine-Secret@dbhost.internal:5432/bys360'\n"
        ),
    })
    output = tmp_path / "secretgate_db_url.zip"
    assert _full_build(root, output, source_sha=sha) == 2
    assert not output.exists()


def test_full_build_secret_gate_rejects_planted_api_token(tmp_path):
    root, sha = _full_build_repo_with_extra_files(tmp_path, {
        "app/planted_integration.py": (
            b"GITHUB_TOKEN = 'ghp_abcdefghijklmnopqrstuvwxyz0123456789AB'\n"
        ),
    })
    output = tmp_path / "secretgate_token.zip"
    assert _full_build(root, output, source_sha=sha) == 2
    assert not output.exists()


def test_full_build_secret_gate_does_not_false_positive_on_powershell_variable_interpolation(tmp_path):
    """The exact class of false positive this scanner's is_placeholder()
    was written to avoid (see scan_bys360_release_secrets.py's docstring,
    which cites these very deploy/candidate scripts): a runtime-constructed
    connection string using PowerShell variable interpolation is CODE, not
    a literal secret, and must not fail the gate."""
    root, sha = _full_build_repo_with_extra_files(tmp_path, {
        "scripts/windows/prepare_bys360_candidate.ps1": (
            b"# candidate\n"
            b'$shadowUrl = "postgresql://$($DbConn.User):$($DbConn.Password)@$($DbConn.HostName):$($DbConn.Port)/$ShadowDbName"\n'
        ),
    })
    output = tmp_path / "secretgate_ps_interpolation.zip"
    assert _full_build(root, output, source_sha=sha) == 0
    manifest_path, _ = _sidecars(output)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["secret_scan_status"] == "PASS"
    assert manifest["secret_scan_findings"] == 0


def test_full_build_secret_gate_allows_env_example_placeholder(tmp_path):
    """A value-free .env.example template (explicitly allowlisted by exact
    basename in both this builder and scan_bys360_release_secrets.py) must
    not fail the gate even though it contains SECRET_KEY=/DATABASE_URL=
    -shaped lines -- they are documentation placeholders, not real values."""
    root, sha = _full_build_repo_with_extra_files(tmp_path, {
        ".env.example": (
            b"SECRET_KEY=change_me_before_production\n"
            b"DATABASE_URL=sqlite:///instance/bys360_local_dev.sqlite3\n"
        ),
    })
    output = tmp_path / "secretgate_env_example.zip"
    assert _full_build(root, output, source_sha=sha) == 0
    manifest_path, _ = _sidecars(output)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["secret_scan_status"] == "PASS"
    assert manifest["secret_scan_findings"] == 0
    assert ".env.example" in _names(output)
