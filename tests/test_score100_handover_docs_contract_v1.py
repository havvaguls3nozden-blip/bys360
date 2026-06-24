from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = [
    "DEPLOYMENT.md",
    "BACKUP_RUNBOOK.md",
    "SECURITY.md",
    "docs/handover/README.md",
    "docs/handover/BYS360_DEVIR_PAKETI_V1.md",
    "docs/handover/BYS360_KURULUM_REHBERI.md",
    "docs/handover/BYS360_CANLIYA_ALMA_REHBERI.md",
    "docs/handover/BYS360_BAKIM_RUNBOOK.md",
    "docs/handover/BYS360_GUVENLIK_KVKK_NOTLARI.md",
    "docs/handover/BYS360_MODUL_ENVANTERI.md",
    "docs/handover/BYS360_RISK_VE_SUREKLILIK_PLANI.md",
]


def test_handover_document_set_exists_and_is_substantial() -> None:
    missing = []
    too_short = []
    for rel in REQUIRED_DOCS:
        path = ROOT / rel
        if not path.exists():
            missing.append(rel)
            continue
        if len(path.read_text(encoding="utf-8", errors="ignore").strip()) < 400:
            too_short.append(rel)
    assert missing == []
    assert too_short == []


def test_security_docs_lock_release_and_secret_rules() -> None:
    security = (ROOT / "SECURITY.md").read_text(encoding="utf-8", errors="ignore")
    deployment = (ROOT / "DEPLOYMENT.md").read_text(encoding="utf-8", errors="ignore")
    backup = (ROOT / "BACKUP_RUNBOOK.md").read_text(encoding="utf-8", errors="ignore")

    assert ".env" in security
    assert "Release" in security
    assert "AI karar vermez" in security
    assert "Temiz release" in deployment
    assert "Rollback" in deployment
    assert "Restore" in backup


def test_handover_docs_do_not_contain_obvious_real_secret_assignments() -> None:
    joined = "\n".join(
        (ROOT / rel).read_text(encoding="utf-8", errors="ignore") for rel in REQUIRED_DOCS
    )
    forbidden_literals = [
        "DATABASE_URL=postgresql",
        "SECRET_KEY=",
        "PASSWORD=",
        "TOKEN=",
        "API_KEY=",
    ]
    # Documentation may mention names or placeholders, but should not assign real values.
    for literal in forbidden_literals:
        assert literal not in joined
