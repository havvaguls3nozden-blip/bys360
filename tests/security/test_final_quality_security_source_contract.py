from __future__ import annotations

from pathlib import Path

from app.refactor.final_quality_security_compliance_contract import (
    PERSONAL_DATA_FLOWS,
    SECURITY_COMPLIANCE_CONTROLS,
)

ROOT = Path(__file__).resolve().parents[2]


def read_if_exists(path: Path) -> str:
    if path.exists() and path.is_file():
        return path.read_text(encoding="utf-8", errors="ignore")
    if path.exists() and path.is_dir():
        snippets: list[str] = []
        for child in sorted(path.rglob("*.py"))[:60]:
            rel = child.relative_to(ROOT).as_posix()
            if "__pycache__" in rel:
                continue
            snippets.append(child.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(snippets)
    return ""


def test_security_controls_have_either_source_path_or_source_token_evidence() -> None:
    project_text = "\n".join(
        read_if_exists(ROOT / path)
        for path in [
            "app/security",
            "app/bootstrap",
            "app/models",
            "app/services",
            "app/admin",
            "app/refactor",
            "docs/ENV.md",
            ".releaseignore",
        ]
    )
    lowered = project_text.lower()
    for control in SECURITY_COMPLIANCE_CONTROLS:
        existing_paths = [source for source in control.required_sources if (ROOT / source).exists()]
        token_hits = [token for token in control.required_tokens if token.lower() in lowered]
        assert existing_paths or token_hits, control.key


def test_personal_data_flow_tables_are_documented_in_live_backbone_or_model_sources() -> None:
    live_doc = read_if_exists(ROOT / "docs/refactor/FINAL_QUALITY_FAZ3.md")
    backbone_contract = read_if_exists(ROOT / "app/refactor/final_quality_live_backbone_contract.py")
    performance_rules = read_if_exists(ROOT / "app/refactor/final_quality_performance_rules.py")
    model_text = read_if_exists(ROOT / "app/models")
    evidence = "\n".join([live_doc, backbone_contract, performance_rules, model_text]).lower()
    for flow in PERSONAL_DATA_FLOWS:
        hits = [table for table in flow.storage_or_log_tables if table.lower() in evidence]
        assert hits, flow.key


def test_security_tests_do_not_call_external_network_or_mutate_database() -> None:
    test_dir = ROOT / "tests" / "security"
    files = sorted(test_dir.glob("test_final_quality_*.py"))
    assert len(files) >= 3
    joined = "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in files)
    forbidden = [
        "db.session" + ".commit(",
        ".create" + "_all(",
        ".drop" + "_all(",
        "requests" + ".get(",
        "url" + "open(",
        "ALTER " + "TABLE",
        "DROP " + "TABLE",
    ]
    for snippet in forbidden:
        assert snippet not in joined
