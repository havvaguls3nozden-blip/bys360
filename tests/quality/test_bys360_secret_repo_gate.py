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

_UNQUOTED_ENV_SYNTHETIC_SECRET = "sk_live_abcdef1234567890xyz"  # hardcoded_secret fixture


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


# --- BYS360 Phase 10J: bare SECRET suffix coverage expansion ---
# config.py reads FLASK_SECRET (a real runtime env var, used as the Flask
# secret-key fallback, loaded at app-factory startup) whose name ends in
# bare SECRET, not SECRET_KEY -- this was confirmed by evidence (not
# speculation) to be invisible to every prior scan path. These tests lock
# in the fix and, more importantly, lock in that PUBLIC_KEY/*_PATH/*_NAME/
# *_ID-shaped metadata fields are never caught purely by containing the
# word SECRET or KEY -- these metadata guards are independent of exactly
# which sensitive suffix triggered them and must hold regardless of future
# key-list changes.

_BARE_SECRET_SYNTHETIC = "sk_live_abcdef1234567890xyz"  # hardcoded_secret fixture


def test_flask_secret_quoted_triggers_red(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    quoted_content = f'FLASK_SECRET = "{_BARE_SECRET_SYNTHETIC}"\n'  # hardcoded_secret fixture
    (repo / "settings_local.py").write_text(quoted_content, encoding="utf-8")
    _git(["add", "-f", "settings_local.py"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is False
    assert any(f["type"] == "hardcoded_secret_value" for f in result["findings"])
    assert _BARE_SECRET_SYNTHETIC not in json.dumps(result)


def test_flask_secret_unquoted_env_triggers_red(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text(
        f"FLASK_SECRET={_BARE_SECRET_SYNTHETIC}\n", encoding="utf-8"
    )
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is False
    assert any(
        f["type"] == "hardcoded_secret_value" and f["path"] == ".env.docker.example"
        for f in result["findings"]
    )
    assert _BARE_SECRET_SYNTHETIC not in json.dumps(result)


def test_flask_secret_export_prefixed_triggers_red(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text(
        f"export FLASK_SECRET={_BARE_SECRET_SYNTHETIC}\n", encoding="utf-8"
    )
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is False
    assert any(f["type"] == "hardcoded_secret_value" for f in result["findings"])
    assert _BARE_SECRET_SYNTHETIC not in json.dumps(result)


def test_flask_secret_single_quoted_triggers_red(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    env_content = f"FLASK_SECRET='{_BARE_SECRET_SYNTHETIC}'\n"  # hardcoded_secret fixture
    (repo / ".env.docker.example").write_text(env_content, encoding="utf-8")
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is False
    assert any(f["type"] == "hardcoded_secret_value" for f in result["findings"])
    assert _BARE_SECRET_SYNTHETIC not in json.dumps(result)


def test_bare_secret_dict_style_triggers_red(tmp_path: Path) -> None:
    """DICT_ASSIGN_RE requires the quoted JSON key to exactly equal one of
    the sensitive alternatives (no compound-name prefix tolerance, unlike
    ASSIGN_RE/UNQUOTED_ASSIGN_RE) -- a pre-existing, key-name-independent
    limitation (also true for e.g. "PASSWORD" today) that this phase does
    not change. This test exercises the new bare SECRET entry through the
    exact-match case DICT_ASSIGN_RE actually supports; compound dict keys
    like "FLASK_SECRET" are a separate, out-of-scope gap (see Phase 10J
    coordinator report)."""
    repo = _init_repo(tmp_path)
    dict_content = f'{{"SECRET": "{_BARE_SECRET_SYNTHETIC}"}}\n'  # hardcoded_secret fixture
    (repo / "config_dump.json").write_text(dict_content, encoding="utf-8")
    _git(["add", "-f", "config_dump.json"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is False
    assert any(f["type"] == "hardcoded_secret_value" for f in result["findings"])
    assert _BARE_SECRET_SYNTHETIC not in json.dumps(result)


def test_bare_secret_suffix_compound_name_triggers_red(tmp_path: Path) -> None:
    """Proves the new bare SECRET entry inherits the existing unanchored
    suffix-matching behavior (like SMTP_PASSWORD already does for PASSWORD)
    rather than only matching the exact word SECRET."""
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text(
        f"BYS360_SESSION_SECRET={_BARE_SECRET_SYNTHETIC}\n", encoding="utf-8"
    )
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is False
    assert any(f["type"] == "hardcoded_secret_value" for f in result["findings"])


def test_flask_secret_lowercase_key_name_triggers_red(tmp_path: Path) -> None:
    """Case-insensitive matching (re.I) is pre-existing policy, not a new
    decision made in this phase; this locks in that it still applies to the
    newly-added bare SECRET suffix."""
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text(
        f"flask_secret={_BARE_SECRET_SYNTHETIC}\n", encoding="utf-8"
    )
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is False
    assert any(f["type"] == "hardcoded_secret_value" for f in result["findings"])


def test_flask_secret_safe_placeholder_is_pass(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text(
        "FLASK_SECRET=replace-with-a-strong-random-value\n", encoding="utf-8"
    )
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0


def test_flask_secret_empty_value_is_pass(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text("FLASK_SECRET=\n", encoding="utf-8")
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0


def test_flask_secret_commented_is_pass(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text(
        f"# FLASK_SECRET={_BARE_SECRET_SYNTHETIC}\n", encoding="utf-8"
    )
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0


def test_flask_secret_env_reference_is_warning_not_finding(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    py_content = 'FLASK_SECRET = os.environ.get("FLASK_SECRET")\n'
    (repo / "settings_local.py").write_text(py_content, encoding="utf-8")
    _git(["add", "-f", "settings_local.py"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0


# --- Metadata/public-field guards (key-list-independent, durable) ---


def test_public_key_never_flagged_by_key_name_alone(tmp_path: Path) -> None:
    """PUBLIC_KEY must never produce a hardcoded_secret_value finding purely
    from its name -- neither SECRET_KEY, PASSWORD, TOKEN, API_KEY, nor the
    new bare SECRET entry end with the bare word KEY, so PUBLIC_KEY (which
    ends in KEY, not any of those full suffixes) does not match. This test
    is a durable regression lock against ever adding a bare KEY entry."""
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text(
        "PUBLIC_KEY=ssh-ed25519-example-public-material-not-secret\n", encoding="utf-8"
    )
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0


def test_private_key_path_is_not_treated_as_key_material(tmp_path: Path) -> None:
    """PRIVATE_KEY_PATH is a filesystem path reference, not the key content
    itself. PRIVATE_KEY is not a sensitive suffix in this repo (no evidenced
    runtime usage -- see Phase 10J coordinator report), so this is safe
    today; the test still locks in that a _PATH suffix breaks the required
    immediate assignment-operator adjacency, in case PRIVATE_KEY is ever
    added later."""
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text(
        "PRIVATE_KEY_PATH=/run/secrets/private-key.pem\n", encoding="utf-8"
    )
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0


def test_key_id_metadata_is_pass(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text(
        "KEY_ID=example-key-id\n", encoding="utf-8"
    )
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0


def test_client_secret_name_metadata_is_pass(tmp_path: Path) -> None:
    """CLIENT_SECRET_NAME is a name/label, not a secret value. The _NAME
    suffix sits after SECRET and before '=', breaking the same adjacency
    that protects every other metadata-suffixed field."""
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text(
        "CLIENT_SECRET_NAME=oauth-client-secret\n", encoding="utf-8"
    )
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0


def test_secret_rotation_id_metadata_is_pass(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text(
        "SECRET_ROTATION_ID=abc123\n", encoding="utf-8"
    )
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0


def test_secret_immediately_followed_by_more_identifier_chars_is_pass(tmp_path: Path) -> None:
    """Boundary-collision guard: a sensitive suffix immediately followed by
    MORE identifier characters with no separator (SECRETKEYSTORE, not
    SECRET_KEYSTORE) must not match either -- the assignment operator still
    has to appear immediately after the matched suffix."""
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text(
        "SECRETKEYSTORE_ENABLED=true\n", encoding="utf-8"
    )
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0


def test_multiple_new_and_metadata_keys_in_one_file_count_correctly(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text(
        f"FLASK_SECRET={_BARE_SECRET_SYNTHETIC}\n"
        "PUBLIC_KEY=not-a-secret\n"
        "PRIVATE_KEY_PATH=/run/secrets/private-key.pem\n"
        "KEY_ID=example-key-id\n"
        "CLIENT_SECRET_NAME=oauth-client-secret\n",
        encoding="utf-8",
    )
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is False
    assert result["finding_count"] == 1
    assert result["findings"][0]["line"] == 1


def test_flask_secret_crlf_matches_lf_result(tmp_path: Path) -> None:
    lf_dir = tmp_path / "lf"
    lf_dir.mkdir()
    lf_repo = _init_repo(lf_dir)
    (lf_repo / ".env.docker.example").write_bytes(
        f"FLASK_SECRET={_BARE_SECRET_SYNTHETIC}\n".encode()
    )
    _git(["add", "-f", ".env.docker.example"], lf_repo)
    _commit(lf_repo)
    lf_result = run(lf_repo)

    crlf_dir = tmp_path / "crlf"
    crlf_dir.mkdir()
    crlf_repo = _init_repo(crlf_dir)
    (crlf_repo / ".env.docker.example").write_bytes(
        f"FLASK_SECRET={_BARE_SECRET_SYNTHETIC}\r\n".encode()
    )
    _git(["add", "-f", ".env.docker.example"], crlf_repo)
    _commit(crlf_repo)
    crlf_result = run(crlf_repo)

    assert lf_result["ok"] == crlf_result["ok"] is False
    assert lf_result["finding_count"] == crlf_result["finding_count"] == 1


def test_flask_secret_whitespace_around_key_and_value_is_handled(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text(
        f"  FLASK_SECRET   =   {_BARE_SECRET_SYNTHETIC}  \n", encoding="utf-8"
    )
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is False
    assert any(f["type"] == "hardcoded_secret_value" for f in result["findings"])


def test_flask_secret_trailing_comment_is_stripped(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / ".env.docker.example").write_text(
        f"FLASK_SECRET={_BARE_SECRET_SYNTHETIC} # rotate before shipping\n",
        encoding="utf-8",
    )
    _git(["add", "-f", ".env.docker.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is False
    assert any(f["type"] == "hardcoded_secret_value" for f in result["findings"])
    assert _BARE_SECRET_SYNTHETIC not in json.dumps(result)


def test_bare_secret_unquoted_scanning_is_scoped_to_env_files(tmp_path: Path) -> None:
    """A Python variable ending in _SECRET assigned to an unquoted
    expression (not a string literal) is ordinary code, not a leaked
    credential -- the unquoted-assignment path must stay scoped to
    .env/.env.* files, exactly as it already was before this phase."""
    repo = _init_repo(tmp_path)
    (repo / "config_local.py").write_text(
        "session_secret = derive_session_secret_from_master_key()\n", encoding="utf-8"
    )
    _git(["add", "-f", "config_local.py"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0


def test_tracked_env_docker_example_still_green_after_secret_expansion(tmp_path: Path) -> None:
    """Re-verifies the real tracked .env.docker.example (which has no
    FLASK_SECRET or other *_SECRET line) stays clean after the bare SECRET
    suffix is added -- catches any future accidental *_SECRET addition to
    that file without a safe placeholder."""
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


def test_tracked_env_example_still_green_after_secret_expansion(tmp_path: Path) -> None:
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


# --- BYS360 Phase 5 secret-gate closure (2026-08-02): Bölüm 3C Ajan 3 ---
# tests/security/test_phase13b_setup_admin.py posts realistic-looking
# passwords ("AttackerPass123!", "OperatorStrongPass1!", "SecondAdminPass1!")
# to exercise setup-admin bootstrap negative/positive assertions. These are
# not real secrets, but the gate previously had no way to tell that apart
# from a genuinely leaked credential and flagged all three as
# hardcoded_secret_value (finding_count=3). The fix renamed the fixture
# values to obviously-fake, still-valid (>= 8 chars, the only requirement
# enforced by _MIN_PASSWORD_LENGTH in app/main_handlers/auth_handlers.py)
# values containing "Test" -- which the gate's own PRE-EXISTING
# PLACEHOLDER_WORDS list ("test" was already in it) downgrades to a warning.
# No new gate mechanism, no tests/-wide exemption, no allowlist: the below
# tests prove the classification comes from the *value's content*, not from
# a blanket "this file/folder is a test" carve-out.


def test_phase13b_style_fixture_password_is_warning_not_finding(tmp_path: Path) -> None:
    """Reproduces the exact dict-literal POST-data shape used in
    tests/security/test_phase13b_setup_admin.py with the real, current
    fixture value, inside an isolated tests/ tree. Must be a warning, not a
    finding."""
    repo = _init_repo(tmp_path)
    (repo / "tests" / "security").mkdir(parents=True)
    fixture_content = (
        "def test_example():\n"
        "    data = {\n"
        '        "password": "AttackerTestFixtureOnly123!",\n'
        "    }\n"
    )
    (repo / "tests" / "security" / "test_example_fixture.py").write_text(
        fixture_content, encoding="utf-8"
    )
    _git(["add", "-f", "tests/security/test_example_fixture.py"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0
    assert any(
        w["path"] == "tests/security/test_example_fixture.py" for w in result["warnings"]
    )


def test_phase13b_fixture_pattern_without_test_marker_still_fails(tmp_path: Path) -> None:
    """Controlled negative for the test above (and the durable proof that
    the gate does NOT broadly ignore the tests/ folder): identical
    dict-literal shape, identical tests/ path, but a realistic value that
    contains none of PLACEHOLDER_WORDS (no "test", "local", "dev", ...).
    This must still be a finding."""
    repo = _init_repo(tmp_path)
    (repo / "tests" / "security").mkdir(parents=True)
    realistic_value = "Xk9#mQ7vBzR2pL5w"  # hardcoded_secret fixture
    fixture_content = (
        "def test_example():\n"
        "    data = {\n"
        '        "password": "Xk9#mQ7vBzR2pL5w",\n'  # hardcoded_secret fixture
        "    }\n"
    )
    (repo / "tests" / "security" / "test_example_fixture.py").write_text(
        fixture_content, encoding="utf-8"
    )
    _git(["add", "-f", "tests/security/test_example_fixture.py"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is False
    assert any(
        f["type"] == "hardcoded_secret_value"
        and f["path"] == "tests/security/test_example_fixture.py"
        for f in result["findings"]
    )
    assert realistic_value not in json.dumps(result)


def test_real_phase13b_setup_admin_test_file_scans_clean(tmp_path: Path) -> None:
    """Direct regression lock on the actual tracked file: copies the real,
    current tests/security/test_phase13b_setup_admin.py content into an
    isolated repo and asserts zero findings -- the real-world instance of
    the fixture-rename fix above."""
    repo = _init_repo(tmp_path)
    real_content = (
        Path(__file__).resolve().parents[2]
        / "tests"
        / "security"
        / "test_phase13b_setup_admin.py"
    ).read_text(encoding="utf-8")
    (repo / "tests" / "security").mkdir(parents=True)
    (repo / "tests" / "security" / "test_phase13b_setup_admin.py").write_text(
        real_content, encoding="utf-8"
    )
    _git(["add", "-f", "tests/security/test_phase13b_setup_admin.py"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0


# --- BYS360 Phase 5 secret-gate closure: raw PEM/OpenSSH/PGP private-key material ---
# Confirmed by direct reproduction (a tmp_path repo containing only a
# "-----BEGIN PRIVATE KEY-----" header, no KEY="value" wrapper) that
# finding_count was 0 before PRIVATE_KEY_HEADER_RE existed: none of
# ASSIGN_RE/DICT_ASSIGN_RE/UNQUOTED_ASSIGN_RE can ever see a bare PEM header
# line since it has no sensitive KEY name followed by an assignment
# operator. The new check matches the header line independently of that
# machinery, still routed through the same looks_regex_or_scanner() escape
# hatch used everywhere else in this file for scanner/test source code.

_FAKE_PEM_BODY = "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcw\n-----END PRIVATE KEY-----\n"  # hardcoded_secret fixture -- synthetic, not a real key


def test_raw_private_key_header_triggers_red(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    (repo / "id_rsa_leaked.txt").write_text(_FAKE_PEM_BODY, encoding="utf-8")
    _git(["add", "-f", "id_rsa_leaked.txt"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is False
    assert any(
        f["type"] == "hardcoded_private_key_material" and f["path"] == "id_rsa_leaked.txt"
        for f in result["findings"]
    )


def test_rsa_and_openssh_and_pgp_private_key_variants_trigger_red(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    rsa_body = "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA\n-----END RSA PRIVATE KEY-----\n"  # hardcoded_secret fixture
    openssh_body = "-----BEGIN OPENSSH PRIVATE KEY-----\nb3BlbnNzaC1rZXk\n-----END OPENSSH PRIVATE KEY-----\n"  # hardcoded_secret fixture
    pgp_body = "-----BEGIN PGP PRIVATE KEY BLOCK-----\nlQOYBF\n-----END PGP PRIVATE KEY BLOCK-----\n"  # hardcoded_secret fixture
    (repo / "rsa_key.txt").write_text(rsa_body, encoding="utf-8")
    (repo / "openssh_key.txt").write_text(openssh_body, encoding="utf-8")
    (repo / "pgp_key.txt").write_text(pgp_body, encoding="utf-8")
    _git(["add", "-f", "rsa_key.txt", "openssh_key.txt", "pgp_key.txt"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is False
    flagged_paths = {
        f["path"] for f in result["findings"] if f["type"] == "hardcoded_private_key_material"
    }
    assert flagged_paths == {"rsa_key.txt", "openssh_key.txt", "pgp_key.txt"}


def test_private_key_pattern_in_own_regex_source_is_not_flagged(tmp_path: Path) -> None:
    """A quality-gate script that documents the PEM header as a regex
    literal (exactly the pre-existing pattern in
    scripts/quality/bys360_score100_quality_gate_v1.py) must not be
    flagged -- looks_regex_or_scanner() already exempts any line containing
    a "re.compile" marker; this locks that same exemption in for the new
    private-key check."""
    repo = _init_repo(tmp_path)
    (repo / "scripts" / "quality").mkdir(parents=True)
    content = (
        "import re\n"
        'PATTERN = re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA |)?PRIVATE KEY-----")\n'
    )
    (repo / "scripts" / "quality" / "some_gate.py").write_text(content, encoding="utf-8")
    _git(["add", "-f", "scripts/quality/some_gate.py"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0


def test_tracked_repo_has_no_private_key_material_anywhere() -> None:
    """Full real-repo regression: confirms no tracked/staged/untracked file
    in this actual repository contains PEM/OpenSSH/PGP private-key material
    now that the check exists (including this test file's own synthetic
    fixtures above, which are marked so they don't self-flag)."""
    root = Path(__file__).resolve().parents[2]
    result = run(root)

    assert not any(f["type"] == "hardcoded_private_key_material" for f in result["findings"])


# --- BYS360 Phase 5 secret-gate closure: Sentry DSN real-value / empty-template regression ---


def test_sentry_dsn_real_value_triggers_red(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    real_dsn = "https://abcdef1234567890abcdef1234567890@o123456.ingest.sentry.io/6789012"  # hardcoded_secret fixture
    (repo / "config_local.py").write_text(
        f'SENTRY_DSN = "{real_dsn}"\n',  # hardcoded_secret fixture
        encoding="utf-8",
    )
    _git(["add", "-f", "config_local.py"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is False
    assert any(
        f["type"] == "hardcoded_secret_value" and f["path"] == "config_local.py"
        for f in result["findings"]
    )
    assert real_dsn not in json.dumps(result)


def test_env_example_empty_sentry_dsn_is_pass(tmp_path: Path) -> None:
    """Regression: an empty SENTRY_DSN= line in a template .env file (the
    actual, current shape of the tracked .env.example) must stay accepted."""
    repo = _init_repo(tmp_path)
    (repo / ".env.example").write_text("SENTRY_DSN=\n", encoding="utf-8")
    _git(["add", "-f", ".env.example"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is True
    assert result["finding_count"] == 0


def test_real_env_example_sentry_dsn_line_is_empty() -> None:
    """Confirms the actual tracked .env.example still uses the accepted
    empty-value shape (SENTRY_DSN=) rather than a real value -- a source-file
    regression guard, independent of the gate itself."""
    root = Path(__file__).resolve().parents[2]
    env_example = (root / ".env.example").read_text(encoding="utf-8")
    sentry_lines = [
        line for line in env_example.splitlines() if line.strip().upper().startswith("SENTRY_DSN")
    ]
    assert sentry_lines, "SENTRY_DSN satırı .env.example içinde bulunamadı"
    assert all(line.strip() == "SENTRY_DSN=" for line in sentry_lines)


# --- BYS360 Phase 5 secret-gate closure: API-key-like value (dedicated regression) ---
# API_KEY is already covered indirectly by test_staged_new_secret_triggers_red
# above; this is a direct, dedicated regression requested explicitly by the
# Phase 5 secret-gate closure checklist.


def test_api_key_like_value_triggers_red(tmp_path: Path) -> None:
    repo = _init_repo(tmp_path)
    realistic_key = "ak_prod_5f4e3d2c1b0a9988776655443322"  # hardcoded_secret fixture
    (repo / "integration_config.py").write_text(
        f'API_KEY = "{realistic_key}"\n',  # hardcoded_secret fixture
        encoding="utf-8",
    )
    _git(["add", "-f", "integration_config.py"], repo)
    _commit(repo)

    result = run(repo)

    assert result["ok"] is False
    assert any(
        f["type"] == "hardcoded_secret_value" and f["path"] == "integration_config.py"
        for f in result["findings"]
    )
    assert realistic_key not in json.dumps(result)
