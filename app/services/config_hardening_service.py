from __future__ import annotations

import json
import secrets
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class Finding:
    category: str
    severity: str
    code: str
    title: str
    detail: str
    file_path: str = ""
    line_hint: str = ""


_PLACEHOLDER_TOKENS = {
    "changeme",
    "change-me",
    "replace-me",
    "example",
    "placeholder",
    "secret-key",
    "secret",
    "development-only",
    "dev-only",
    "dummy",
    "test",
}


def _load_env(env_path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not env_path.exists():
        return values
    for raw in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _looks_placeholder(value: str) -> bool:
    normalized = value.strip().strip('"').strip("'").lower()
    if not normalized:
        return True
    if len(normalized) < 24:
        return True
    return any(token in normalized for token in _PLACEHOLDER_TOKENS)


def _upsert_env_line(text: str, key: str, value: str) -> str:
    lines = text.splitlines()
    replaced = False
    new_lines: List[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f"{key}="):
            new_lines.append(f"{key}={value}")
            replaced = True
        else:
            new_lines.append(line)
    if not replaced:
        if new_lines and new_lines[-1] != "":
            new_lines.append("")
        new_lines.append(f"{key}={value}")
    return "\n".join(new_lines) + "\n"


def build_safe_env_patch(env_path: Path, *, apply_safe_env: bool = False) -> Tuple[List[Finding], Dict[str, str]]:
    findings: List[Finding] = []
    suggestions: Dict[str, str] = {}
    env = _load_env(env_path)

    strict_env = env.get("STRICT_ENV_VALIDATION", "")
    if strict_env.lower() != "true":
        findings.append(
            Finding(
                category="config",
                severity="critical",
                code="STRICT_ENV_VALIDATION_NOT_TRUE",
                title="STRICT_ENV_VALIDATION güvenli değil",
                detail="STRICT_ENV_VALIDATION canlı için True olmalı.",
                file_path=str(env_path),
            )
        )
        suggestions["STRICT_ENV_VALIDATION"] = "True"

    secret_key = env.get("SECRET_KEY", "")
    if _looks_placeholder(secret_key):
        findings.append(
            Finding(
                category="config",
                severity="warning",
                code="SECRET_KEY_PLACEHOLDER",
                title="SECRET_KEY zayıf veya örnek görünüyor",
                detail="SECRET_KEY canlı için güçlü ve benzersiz bir değerle değiştirilmeli.",
                file_path=str(env_path),
            )
        )
        suggestions["SECRET_KEY"] = secrets.token_urlsafe(48)

    if apply_safe_env and env_path.exists() and suggestions:
        current = env_path.read_text(encoding="utf-8", errors="ignore")
        updated = current
        if "STRICT_ENV_VALIDATION" in suggestions:
            updated = _upsert_env_line(updated, "STRICT_ENV_VALIDATION", suggestions["STRICT_ENV_VALIDATION"])
        # SECRET_KEY kullanıcının incelemesine bırakılır; otomatik yazılmaz.
        env_path.write_text(updated, encoding="utf-8")

    return findings, suggestions


def write_env_recommendation_file(project_root: Path, suggestions: Dict[str, str]) -> Optional[Path]:
    if not suggestions:
        return None
    out_dir = project_root / "reports" / "faz3_1"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"faz3_1_env_recommendations_{ts}.env"
    lines = [
        "# Faz 3.1 önerilen canlı ayarları",
        "# SECRET_KEY satırını gözden geçirip sonra .env içine kopyalayın.",
        "",
    ]
    for key, value in suggestions.items():
        lines.append(f"{key}={value}")
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path


def export_findings_json(findings: List[Finding], path: Path, extra: Optional[dict] = None) -> None:
    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "finding_count": len(findings),
        "findings": [asdict(item) for item in findings],
    }
    if extra:
        payload.update(extra)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
