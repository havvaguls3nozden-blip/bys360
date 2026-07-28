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
        ".env.docker.example",
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


# --- BYS360 Phase 10I: unquoted .env-format assignment scanning ---
# ASSIGN_RE/DICT_ASSIGN_RE above only matched values wrapped in a quote
# character, so a standard unquoted .env-style line (KEY=value -- the
# actual shape of every real .env.example/.env.docker.example line in this
# repo) was never scanned at all. These tests lock in the fix without
# weakening any of the quoted-assignment behavior exercised above.

_UNQUOTED_ENV_SYNTHETIC_SECRET = "sk_live_abcdef1234567890xyz"


def test_unquoted_env_secret_triggers_red(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text(
        f"SECRET_KEY={_UNQUOTED_ENV_SYNTHETIC_SECRET}\n", encoding="utf-8"
    )
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is False
    assert any(
        f["type"] == "hardcoded_secret_value" and f["path"] == ".env.docker.example"
        for f in result["findings"]
    )
    assert _UNQUOTED_ENV_SYNTHETIC_SECRET not in json.dumps(result)


def test_single_quoted_env_secret_triggers_red(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    env_content = f"SECRET_KEY='{_UNQUOTED_ENV_SYNTHETIC_SECRET}'\n"  # hardcoded_secret fixture
    (repo / ".env.docker.example").write_text(env_content, encoding="utf-8")
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is False
    assert any(f["type"] == "hardcoded_secret_value" for f in result["findings"])
    assert _UNQUOTED_ENV_SYNTHETIC_SECRET not in json.dumps(result)


def test_export_prefixed_env_secret_triggers_red(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text(
        f"export SECRET_KEY={_UNQUOTED_ENV_SYNTHETIC_SECRET}\n", encoding="utf-8"
    )
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is False
    assert any(f["type"] == "hardcoded_secret_value" for f in result["findings"])
    assert _UNQUOTED_ENV_SYNTHETIC_SECRET not in json.dumps(result)


def test_unquoted_vs_quoted_same_value_both_trigger_red(tmp_path: Path) -> None:
    """Proves the unquoted-parsing fix produces the same finding type as the
    pre-existing quoted path for an equivalent value -- quote-handling
    alone doesn't change classification."""
    repo = _init_repo(tmp_path)
    quoted_content = f'SECRET_KEY = "{_UNQUOTED_ENV_SYNTHETIC_SECRET}"\n'  # hardcoded_secret fixture
    (repo / "quoted.py").write_text(quoted_content, encoding="utf-8")
    (repo / ".env.docker.example").write_text(
        f"SECRET_KEY={_UNQUOTED_ENV_SYNTHETIC_SECRET}\n", encoding="utf-8"
    )
    _git(["add", "-f", "quoted.py", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    types_by_path = {f["path"]: f["type"] for f in result["findings"]}
    assert types_by_path.get("quoted.py") == "hardcoded_secret_value"
    assert types_by_path.get(".env.docker.example") == "hardcoded_secret_value"


def test_unquoted_env_safe_placeholder_is_pass(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text(
        "SECRET_KEY=replace-with-a-strong-random-value\n", encoding="utf-8"
    )
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0


def test_unquoted_env_empty_sensitive_value_is_pass(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text("SECRET_KEY=\n", encoding="utf-8")
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0


def test_unquoted_env_commented_secret_is_pass(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text(
        f"# SECRET_KEY={_UNQUOTED_ENV_SYNTHETIC_SECRET}\n", encoding="utf-8"
    )
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0


def test_unquoted_env_non_sensitive_key_is_pass(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text(
        f"NORMAL_SETTING={_UNQUOTED_ENV_SYNTHETIC_SECRET}\n", encoding="utf-8"
    )
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0


def test_tracked_env_docker_example_placeholders_stay_green(tmp_path: Path) -> None:
    """Real-file regression: the actual tracked .env.docker.example must
    still scan clean under the new unquoted-assignment path -- this is
    exactly what the PLACEHOLDER_WORDS/DATABASE_URL_KEYS fixes landing
    together with the parser change are meant to guarantee."""
    repo = _init_repo(tmp_path)
    real_content = (Path(__file__).resolve().parents[2] / ".env.docker.example").read_text(
        encoding="utf-8"
    )
    (repo / ".env.docker.example").write_text(real_content, encoding="utf-8")
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0


def test_tracked_env_example_placeholders_stay_green(tmp_path: Path) -> None:
    """Same real-file regression for the repo's other tracked template."""
    repo = _init_repo(tmp_path)
    real_content = (Path(__file__).resolve().parents[2] / ".env.example").read_text(
        encoding="utf-8"
    )
    (repo / ".env.example").write_text(real_content, encoding="utf-8")
    _git(["add", "-f", ".env.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0


def test_unquoted_url_fragment_hash_is_not_treated_as_comment(tmp_path: Path) -> None:
    """A '#' with no preceding whitespace (a URL fragment) must not be
    mistaken for an inline comment marker. CALLBACK_URL isn't a sensitive
    key so it never produces a finding on its own -- asserting the very
    next line's real SECRET_KEY still fires proves the URL line didn't
    swallow anything past it."""
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text(
        f"CALLBACK_URL=https://example.invalid/path#fragment\n"
        f"SECRET_KEY={_UNQUOTED_ENV_SYNTHETIC_SECRET}\n",
        encoding="utf-8",
    )
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert any(
        f["type"] == "hardcoded_secret_value" and f["line"] == 2
        for f in result["findings"]
    )


def test_unquoted_trailing_comment_is_stripped_from_value(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text(
        f"SECRET_KEY={_UNQUOTED_ENV_SYNTHETIC_SECRET} # rotate this before shipping\n",
        encoding="utf-8",
    )
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is False
    assert any(f["type"] == "hardcoded_secret_value" for f in result["findings"])
    assert _UNQUOTED_ENV_SYNTHETIC_SECRET not in json.dumps(result)


def test_unquoted_env_crlf_matches_lf_result(tmp_path: Path) -> None:
    lf_dir = tmp_path / "lf"
    lf_dir.mkdir()
    lf_repo = _init_repo(lf_dir)
    (lf_repo / ".env.docker.example").write_bytes(
        f"SECRET_KEY={_UNQUOTED_ENV_SYNTHETIC_SECRET}\n".encode()
    )
    _git(["add", "-f", ".env.docker.example"], lf_repo)
    _commit(lf_repo)
    lf_result = run(lf_repo)

    crlf_dir = tmp_path / "crlf"
    crlf_dir.mkdir()
    crlf_repo = _init_repo(crlf_dir)
    (crlf_repo / ".env.docker.example").write_bytes(
        f"SECRET_KEY={_UNQUOTED_ENV_SYNTHETIC_SECRET}\r\n".encode()
    )
    _git(["add", "-f", ".env.docker.example"], crlf_repo)
    _commit(crlf_repo)
    crlf_result = run(crlf_repo)

    assert lf_result["ok"] == crlf_result["ok"] is False
    assert lf_result["finding_count"] == crlf_result["finding_count"] == 1


def test_unquoted_env_whitespace_around_key_and_value_is_handled(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text(
        f"  SECRET_KEY   =   {_UNQUOTED_ENV_SYNTHETIC_SECRET}  \n", encoding="utf-8"
    )
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is False
    assert any(f["type"] == "hardcoded_secret_value" for f in result["findings"])


def test_unquoted_env_malformed_lines_do_not_crash(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text(
        "not_an_assignment_line\nA=B=C\n=noKeyHere\n", encoding="utf-8"
    )
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0


def test_unquoted_assignment_scanning_is_scoped_to_env_files(tmp_path: Path) -> None:
    """Python source legitimately contains countless unquoted `key = expr`
    lines (variable assignments, function calls) that are not, and cannot
    be, a literal secret the way an unquoted .env line is -- a real
    hardcoded secret in Python source requires a quoted string literal,
    already covered by ASSIGN_RE. The unquoted path must stay scoped to
    .env/.env.* files only."""
    repo = _init_repo(tmp_path)
    (repo / "config_local.py").write_text(
        "initial_password = get_default_first_login_password()\n", encoding="utf-8"
    )
    _git(["add", "-f", "config_local.py"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0


def test_unquoted_database_url_placeholder_is_not_double_flagged(tmp_path: Path) -> None:
    """DATABASE_URL/SQLALCHEMY_DATABASE_URI values are already fully
    classified by the dedicated embedded-password scan (DB_URL_RE); the
    unquoted-assignment path must not re-evaluate the whole URL string and
    produce a second, redundant/false finding on a safe placeholder URL."""
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text(
        "DATABASE_URL=postgresql://user:password@db:5432/bys360\n", encoding="utf-8"
    )
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0


def test_real_env_file_still_not_tracked() -> None:
    root = Path(__file__).resolve().parents[2]
    tracked = subprocess.run(
        ["git", "ls-files"], cwd=str(root), text=True, capture_output=True, check=True
    ).stdout.splitlines()
    assert ".env" not in tracked
