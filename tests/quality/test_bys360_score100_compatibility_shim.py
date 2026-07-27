from __future__ import annotations

import re
from pathlib import Path

import pytest

from scripts.quality import bys360_quality9_ci_gate as quality9

pytestmark = pytest.mark.ci_safe

ROOT = Path(__file__).resolve().parents[2]
SHIM_REL = "scripts/quality/bys360_score100_quality_gate_v1.py"
WRAPPER_REL = "scripts/windows/repair_bys360_score100_quality_gate_v1.ps1"


def _powershell_code(text: str) -> str:
    code_lines: list[str] = []
    in_block_comment = False
    for line in text.splitlines():
        stripped = line.strip()
        if in_block_comment:
            if "#>" in stripped:
                in_block_comment = False
            continue
        if stripped.startswith("<#"):
            in_block_comment = "#>" not in stripped
            continue
        if not stripped or stripped.startswith("#"):
            continue
        code_lines.append(line)
    return "\n".join(code_lines)


def _wrapper_invokes_shim(text: str) -> bool:
    code = _powershell_code(text)
    script_path = re.search(
        r'(?im)^\s*\$ScriptPath\s*=\s*Join-Path\s+\$ProjectRoot\s+'
        r'["\']scripts[\\/]quality[\\/]bys360_score100_quality_gate_v1\.py["\']\s*$',
        code,
    )
    args_list = re.search(r"(?ims)\$argsList\s*=\s*@\((?P<body>.*?)\)", code)
    invokes_args = re.search(r"(?im)^\s*&\s+\$Python\s+@argsList\s*$", code)
    return bool(
        script_path
        and args_list
        and "$ScriptPath" in args_list.group("body")
        and invokes_args
    )


def test_score100_workflow_and_wrapper_reach_compatibility_shim() -> None:
    workflow_text = (ROOT / ".github" / "workflows" / "bys360-score100-quality-gate-v1.yml").read_text(
        encoding="utf-8"
    )
    commands = [
        command.replace("\\", "/").lower()
        for command in quality9.workflow_run_commands(workflow_text)
    ]
    wrapper_text = (ROOT / WRAPPER_REL).read_text(encoding="utf-8")

    assert any(
        "scripts/windows/repair_bys360_score100_quality_gate_v1.ps1" in command
        for command in commands
    )
    assert _wrapper_invokes_shim(wrapper_text)
    assert (ROOT / SHIM_REL).is_file()


def test_score100_wrapper_comment_only_reference_is_rejected() -> None:
    comment_only = """
    # $ScriptPath = Join-Path $ProjectRoot "scripts\\quality\\bys360_score100_quality_gate_v1.py"
    # $argsList = @($ScriptPath)
    # & $Python @argsList
    """

    assert _wrapper_invokes_shim(comment_only) is False
