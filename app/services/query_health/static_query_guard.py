
"""BYS360 Maintenance Faz 6 - statik sorgu sagligi tarayicisi.

Bu tarayici veritabanina baglanmaz. Servis/route dosyalarinda yavas liste ekranina
sebep olabilecek pattern'leri uyarı olarak raporlar. Bulgu üretmesi tek başına
build'i düşürmez; kritik yavaşlık analizinde nereden başlanacağını gösterir.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

IGNORED_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache", ".pytest_runtime",
    ".mypy_cache", ".ruff_cache", "archive", "release", "overlay", "_overlay_backups",
    "node_modules", "dist", "build", "migrations",
}

SCAN_ROOTS = (
    "app/services",
    "app/performance",
    "app/communication",
    "app/institutional",
    "app/admin",
    "app/support",
)


@dataclass(frozen=True)
class QueryRiskFinding:
    severity: str
    code: str
    path: str
    line: int
    detail: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _is_ignored(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.parts)


def _iter_python_files(root: Path):
    for rel in SCAN_ROOTS:
        base = root / rel
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if not _is_ignored(path.relative_to(root)):
                yield path


def collect_query_risk_findings(root: Path) -> list[QueryRiskFinding]:
    findings: list[QueryRiskFinding] = []
    for path in _iter_python_files(root):
        rel = path.relative_to(root).as_posix()
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for index, line in enumerate(lines, start=1):
            stripped = line.strip()
            if "phase6-ok" in stripped or "noqa: phase6" in stripped:
                continue
            if ".all()" in stripped and "paginate(" not in stripped:
                findings.append(
                    QueryRiskFinding(
                        severity="UYARI",
                        code="query.all",
                        path=rel,
                        line=index,
                        detail=".all() kullanimi listede bellek yukunu artirabilir; pagination veya sinirli scope kontrol edilmeli.",
                    )
                )
            if "len(" in stripped and ".all()" in stripped:
                findings.append(
                    QueryRiskFinding(
                        severity="UYARI",
                        code="len.all",
                        path=rel,
                        line=index,
                        detail="len(query.all()) yerine count()/exists()/limit kullanimi degerlendirilmeli.",
                    )
                )
            if stripped.startswith("for "):
                window = "\n".join(lines[index : min(len(lines), index + 8)])
                if ".query" in window or "Query(" in window:
                    findings.append(
                        QueryRiskFinding(
                            severity="UYARI",
                            code="possible.n_plus_one",
                            path=rel,
                            line=index,
                            detail="Dongu icinde sorgu olasiligi var; selectinload/joinedload veya toplu sorgu kontrol edilmeli.",
                        )
                    )
    return findings


def summarize_findings(findings: list[QueryRiskFinding]) -> dict[str, int]:
    summary: dict[str, int] = {}
    for item in findings:
        key = item.code
        summary[key] = summary.get(key, 0) + 1
    return summary
