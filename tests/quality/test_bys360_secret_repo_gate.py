from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from scripts.quality.bys360_secret_repo_gate import (
    GitCandidateListError,
    _resolve_candidate,
    collect_repository_candidate_files,
    main,
    run,
    scan_blocked_repo_artifacts,
)

pytestmark = pytest.mark.ci_safe

# BYS360 Phase 5 secret-gate scope correction (2026-07-26): the gate used to
# walk the physical filesystem with its own hand-written ignore-name lists,
# so local gitignored runtime noise (logs/, caches, coverage working files)
# could turn the gate red even though none of it could ever reach a commit or
# a push. These tests exercise the new Git-native candidate model (tracked +
# staged + untracked-non-ignored) against real, isolated throwaway git repos
# so the assertions reflect actual `git` behavior rather than a mock of it.


def _git(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=str(cwd), text=True, capture_output=True, check=True
    )


def _init_repo(tmp_path: Path) -> Path:
    _git(["init", "-q"], tmp_path)
    _git(["config", "user.email", "bys360-test@example.com"], tmp_path)
    _git(["config", "user.name", "BYS360 Test"], tmp_path)
    return tmp_path


def _commit(repo: Path, message: str = "init") -> None:
    _git(["-c", "commit.gpgsign=false", "commit", "-q", "-m", message], repo)


def test_env_templates_are_allowed_but_runtime_env_files_are_blocked(
    tmp_path: Path,
) -> None:
    allowed = [
        ".env.example",
        ".env.production.example",
        ".env.sample",
        ".env.template",
    ]
    for name in allowed:
        (tmp_path / name).write_text("# placeholder only\n", encoding="utf-8")
    (tmp_path / ".env.local").write_text("# placeholder only\n", encoding="utf-8")

    candidates = {p.name: p for p in tmp_path.iterdir()}
    findings: list[dict[str, object]] = []
    scan_blocked_repo_artifacts(candidates, findings)
    blocked_paths = {
        str(finding["path"])
        for finding in findings
        if finding["type"] == "blocked_repo_file_name"
    }

    assert blocked_paths == {".env.local"}


# Senaryo A: git tarafından takip edilen (committed) bir dosyada gerçek secret.
def test_tracked_real_secret_triggers_red(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    secret_value = "sk_live_abcdef1234567890xyz"
    (repo / "config_secrets.py").write_text(
        f'SECRET_KEY = "{secret_value}"\n', encoding="utf-8"
    )
    _git(["add", "-f", "config_secrets.py"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is False
    assert any(
        f["type"] == "hardcoded_secret_value" and f["path"] == "config_secrets.py"
        for f in result["findings"]
    )
    assert secret_value not in json.dumps(result)


# Senaryo B: HEAD'de olmayan ama stage edilmiş yeni bir dosyada gerçek secret.
def test_staged_new_secret_triggers_red(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    _git(["add", "-f", "README.md"], repo)
    _commit(repo)

    secret_value = "abcdef1234567890secretlivevalue"
    (repo / "new_secret.py").write_text(
        f'API_KEY = "{secret_value}"\n', encoding="utf-8"
    )
    _git(["add", "-f", "new_secret.py"], repo)  # staged, not committed

    result = run(repo)

    assert result["ok"] is False
    assert any(f["path"] == "new_secret.py" for f in result["findings"])
    assert secret_value not in json.dumps(result)


# Senaryo C: gitignore kapsamında olmayan, hiç stage edilmemiş yeni bir dosyada secret.
def test_untracked_non_ignored_secret_triggers_red(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    _git(["add", "-f", "README.md"], repo)
    _commit(repo)

    secret_value = "supersecretpassword1234567890"
    # "hardcoded_secret" fixture marker below keeps this literal template line
    # (not the file it writes) recognized as scanner/test code by the gate's
    # own looks_regex_or_scanner() when this test module itself is scanned.
    fixture_line = f'DATABASE_URL = "postgresql://admin:{secret_value}@dbhost:5432/prod"\n'  # hardcoded_secret fixture
    (repo / "loose_secret.py").write_text(fixture_line, encoding="utf-8")
    # kasıtlı olarak git add çağrılmadı: tamamen untracked

    result = run(repo)

    assert result["ok"] is False
    assert any(f["path"] == "loose_secret.py" for f in result["findings"])
    assert secret_value not in json.dumps(result)


# Senaryo D: .gitignore kapsamındaki runtime log dosyası taranmamalı ve gate'i kırmızı yapmamalı.
def test_ignored_runtime_log_is_not_scanned(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / ".gitignore").write_text("logs/\n", encoding="utf-8")
    _git(["add", "-f", ".gitignore"], repo)
    _commit(repo)

    (repo / "logs").mkdir()
    log_fixture = 'SECRET_KEY = "shouldneverbescanned1234567890"\n'  # hardcoded_secret fixture
    (repo / "logs" / "example.log").write_text(log_fixture, encoding="utf-8")

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0
    candidate_info = collect_repository_candidate_files(repo)
    assert "logs/example.log" not in candidate_info["candidates"]


# Senaryo E: bir .log dosyası gerçekten tracked ise, sırf uzantısı yüzünden muaf tutulmamalı.
def test_tracked_log_file_is_still_hygiene_flagged(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "app.log").write_text("startup ok\n", encoding="utf-8")
    _git(["add", "-f", "app.log"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is False
    assert any(
        f["type"] == "blocked_repo_file" and f["path"] == "app.log"
        for f in result["findings"]
    )


# Senaryo F: ignored bir coverage çalışma dosyası repository aday kapsamına hiç girmemeli.
def test_ignored_coverage_artifact_is_not_scanned(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / ".gitignore").write_text(".coverage\ncoverage.xml\n", encoding="utf-8")
    _git(["add", "-f", ".gitignore"], repo)
    _commit(repo)

    (repo / ".coverage").write_bytes(b"\x00\x01sqlite-like-binary-payload")
    (repo / "coverage.xml").write_text(
        '<?xml version="1.0"?><coverage></coverage>\n', encoding="utf-8"
    )

    result = run(repo)

    assert result["ok"] is True
    candidate_info = collect_repository_candidate_files(repo)
    assert ".coverage" not in candidate_info["candidates"]
    assert "coverage.xml" not in candidate_info["candidates"]


# Senaryo G: mevcut placeholder/template sınıflandırması (uyarı, bulgu değil) korunmalı.
def test_placeholder_secret_reference_is_warning_not_finding(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "settings.py").write_text('SECRET_KEY = "changeme"\n', encoding="utf-8")
    _git(["add", "-f", "settings.py"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0
    assert any(
        w["type"] == "secret_reference_or_placeholder" and w["path"] == "settings.py"
        for w in result["warnings"]
    )


# Senaryo H: git aday listesi üretilemezse gate sahte PASS vermemeli, açık hata + non-zero exit vermeli.
def test_git_candidate_list_failure_raises(tmp_path: Path) -> None:
    not_a_repo = tmp_path / "not-a-git-repo"
    not_a_repo.mkdir()

    with pytest.raises(GitCandidateListError):
        collect_repository_candidate_files(not_a_repo)


def test_main_reports_git_failure_without_fake_pass(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    not_a_repo = tmp_path / "not-a-git-repo"
    not_a_repo.mkdir()

    exit_code = main(["--root", str(not_a_repo)])
    captured = capsys.readouterr()

    assert exit_code != 0
    assert '"ok": true' not in captured.out
    assert "git" in captured.err.lower()


# Senaryo I: repo dışına çıkan (path traversal) bir aday yol reddedilmeli, dışarıdaki dosya okunmamalı.
def test_path_traversal_candidate_is_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("should never be read", encoding="utf-8")

    resolved = _resolve_candidate(repo, "../outside.txt")

    assert resolved is None


def test_symlink_escaping_repo_root_is_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "repo2"
    repo.mkdir()
    outside = tmp_path / "outside_target.txt"
    symlink_fixture = 'SECRET_KEY = "shouldneverbereadviasymlink1234"\n'  # hardcoded_secret fixture
    outside.write_text(symlink_fixture, encoding="utf-8")
    link = repo / "escape_link.py"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("bu ortamda symlink oluşturma izni yok")

    resolved = _resolve_candidate(repo, "escape_link.py")

    assert resolved is None


# Senaryo J: aynı yol tracked + staged listelerinde tekrar ediyorsa bir kez taranmalı.
def test_duplicate_path_across_lists_is_scanned_once(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "shared.py").write_text('SECRET_KEY = "changeme"\n', encoding="utf-8")
    _git(["add", "-f", "shared.py"], repo)
    _commit(repo)

    (repo / "shared.py").write_text('SECRET_KEY = "changeme-again"\n', encoding="utf-8")
    _git(["add", "-f", "shared.py"], repo)  # tracked dosyada stage edilmiş değişiklik

    info = collect_repository_candidate_files(repo)

    assert info["tracked_candidate_count"] == 1
    assert info["staged_candidate_count"] == 1
    assert info["unique_scanned_candidate_count"] == 1
    assert "shared.py" in info["candidates"]


def test_candidate_classification_counts_are_reported(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "tracked.py").write_text("x = 1\n", encoding="utf-8")
    _git(["add", "-f", "tracked.py"], repo)
    _commit(repo)

    (repo / "untracked.py").write_text("y = 2\n", encoding="utf-8")

    result = run(repo)
    classification = result["git_candidate_classification"]

    assert classification["tracked_candidate_count"] >= 1
    assert classification["untracked_non_ignored_candidate_count"] >= 1
    assert classification["unique_scanned_candidate_count"] == result["scanned_file_count"]
