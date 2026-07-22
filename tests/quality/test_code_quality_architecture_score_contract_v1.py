from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def test_no_plain_tckn_like_model_field_exists() -> None:
    """BYS360 personel omurgası Sicil No esaslıdır; açık TCKN model alanı tutulmamalıdır."""
    models_dir = PROJECT_ROOT / "app" / "models"
    assert models_dir.exists()

    pattern = re.compile(r"\b(tckn|tc_kimlik|kimlik_no)\b", re.IGNORECASE)
    hits: list[str] = []

    for path in models_dir.glob("*.py"):
        text = _read(path)
        for match in pattern.finditer(text):
            line_no = text[: match.start()].count("\n") + 1
            hits.append(f"{path.relative_to(PROJECT_ROOT)}:{line_no}:{match.group(0)}")

    assert hits == []


def test_mobile_routes_do_not_use_exec_facades() -> None:
    """Mobil API route katmanında exec tabanlı facade kalmamalıdır."""
    mobile_dir = PROJECT_ROOT / "app" / "api" / "mobile"
    assert mobile_dir.exists()

    pattern = re.compile(r"\bexec\s*\(", re.IGNORECASE)
    hits: list[str] = []

    for path in mobile_dir.rglob("*.py"):
        text = _read(path)
        for match in pattern.finditer(text):
            line_no = text[: match.start()].count("\n") + 1
            hits.append(f"{path.relative_to(PROJECT_ROOT)}:{line_no}")

    assert hits == []


def test_assistant_js_split_score100_contract_files_exist() -> None:
    """Score100 için bölünen asistan JS varlıkları kalıcı sözleşmedir."""
    expected = [
        "app/static/js/bys360_assistant_module.js",
        "app/static/js/bys360_assistant_module_engines_v12_v19.js",
        "app/static/js/bys360_assistant_module_screen_agents_v20_v23.js",
        "app/static/js/bys360_assistant_module_memory_v30.js",
    ]

    missing = [item for item in expected if not (PROJECT_ROOT / item).exists()]
    assert missing == []

    for item in expected:
        size_kb = (PROJECT_ROOT / item).stat().st_size / 1024
        assert size_kb < 250, f"{item} is too large: {size_kb:.1f} KB"
