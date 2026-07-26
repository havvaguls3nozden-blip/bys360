from __future__ import annotations

from pathlib import Path

import pytest

from scripts.quality.bys360_secret_repo_gate import scan_blocked_repo_artifacts

pytestmark = pytest.mark.ci_safe


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

    findings: list[dict[str, object]] = []
    scan_blocked_repo_artifacts(tmp_path, findings)
    blocked_paths = {
        str(finding["path"])
        for finding in findings
        if finding["type"] == "blocked_repo_file_name"
    }

    assert blocked_paths == {".env.local"}
