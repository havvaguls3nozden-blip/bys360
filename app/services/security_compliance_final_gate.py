from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import ast
import json
import os
import re
from typing import Iterable
import logging
logger = logging.getLogger(__name__)

VERSION = "2026-04-21-security-compliance-final-gate"
REPORT_STEM = "security_compliance_final_gate"

TEXT_SUFFIXES = {
    ".py", ".html", ".jinja", ".jinja2", ".js", ".css", ".txt", ".md", ".yml", ".yaml", ".ps1", ".json", ".toml", ".ini", ".cfg", ".example"
}
SKIP_DIRS = {".git", ".venv", "venv", "env", "node_modules", "__pycache__", ".pytest_cache", ".pytest_runtime", ".mypy_cache", "dist", "build", "archive", "release", "overlay", "logs", "instance", "uploads", "data", "reports", "static", "generated"}
ALLOWED_ROOTS = {"app", "scripts", "docs", "config", "migrations", "deploy", "deployment", "ops", ".github"}

@dataclass
class Finding:
    level: str
    code: str
    title: str
    detail: str = ""
    path: str = ""

@dataclass
class SecurityComplianceReport:
    version: str
    generated_at: str
    root: str
    ok: int
    hata: int
    uyari: int
    findings: list[Finding]
    locked_scope: list[str]

    def passed(self) -> bool:
        return self.hata == 0


def _iter_text_files(root: Path) -> Iterable[Path]:
    emitted = 0
    max_files = 900
    for child in root.iterdir():
        if child.is_file() and (child.suffix.lower() in TEXT_SUFFIXES or child.name.endswith(".example")):
            yield child
            emitted += 1
            if emitted >= max_files:
                return

    priority_dirs = ["app/config", "app/security", "app/auth", "app/services", "app/models", "app/admin", "app/performance", "app/communication", "app/support", "app/templates", "scripts", "docs/refactor", "config", "migrations", "ops/security", ".github/workflows"]
    for rel_base in priority_dirs:
        base = root / rel_base
        if not base.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            current = Path(dirpath)
            for filename in filenames:
                path = current / filename
                if not (path.suffix.lower() in TEXT_SUFFIXES or path.name.endswith(".example")):
                    continue
                try:
                    if path.stat().st_size > 500_000:
                        continue
                except OSError:
                    __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/security_compliance_final_gate.py:69)")
                    continue
                yield path
                emitted += 1
                if emitted >= max_files:
                    return


def _read_text(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            text = path.read_text(encoding="latin-1", errors="ignore")
    except OSError:
        return ""
    return text[:200_000]


def _relative(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _all_text(root: Path) -> tuple[str, dict[str, str]]:
    files = {}
    chunks = []
    total = 0
    max_combined = 3_000_000
    for path in _iter_text_files(root):
        rel = _relative(root, path)
        text = _read_text(path)
        files[rel] = text
        if total < max_combined:
            piece = f"\n\n# FILE: {rel}\n{text}"
            chunks.append(piece)
            total += len(piece)
    return "".join(chunks), files


def _add(findings: list[Finding], level: str, code: str, title: str, detail: str = "", path: str = "") -> None:
    findings.append(Finding(level=level, code=code, title=title, detail=detail, path=path))


def _contains_any(haystack: str, needles: Iterable[str]) -> bool:
    lower = haystack.lower()
    return any(n.lower() in lower for n in needles)


def _grep_files(files: dict[str, str], needles: Iterable[str]) -> list[str]:
    out = []
    lowered_needles = [n.lower() for n in needles]
    for rel, text in files.items():
        low = text.lower()
        if any(n in low for n in lowered_needles):
            out.append(rel)
            if len(out) >= 8:
                break
    return out


def _load_json_if_exists(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(_read_text(path))
    except Exception:
        logger.exception("BYS360 V6B guarded exception | file=app/services/security_compliance_final_gate.py | line=142")
        return None


def _json_report_passed(data: dict | None) -> bool | None:
    if data is None:
        return None
    if isinstance(data.get("hata"), int):
        return data.get("hata") == 0
    if isinstance(data.get("errors"), int):
        return data.get("errors") == 0
    if isinstance(data.get("passed"), bool):
        return bool(data.get("passed"))
    status = str(data.get("status") or data.get("result") or "").upper()
    if status:
        return status in {"PASS", "OK", "PASSED"}
    return None


def _check_compile(root: Path, files: dict[str, str], findings: list[Finding]) -> None:
    py_files = [root / rel for rel in files if rel.endswith(".py")]
    bad = []
    for path in py_files:
        try:
            ast.parse(_read_text(path))
        except SyntaxError as exc:
            bad.append(f"{_relative(root, path)}:{exc.lineno}")
    runtime_bad = [b for b in bad if b.startswith("app/") and "security_compliance_final_gate.py" not in b]
    non_runtime_bad = [b for b in bad if b not in runtime_bad]
    if runtime_bad:
        _add(findings, "HATA", "python.syntax", "Çalışma zamanı Python sözdizimi hatası var", "; ".join(runtime_bad[:12]))
    elif non_runtime_bad:
        _add(findings, "UYARI", "python.syntax", "Çalışma zamanı dışı Python sözdizimi uyarısı var", "; ".join(non_runtime_bad[:12]))
    else:
        _add(findings, "OK", "python.syntax", f"Python sözdizimi statik kontrolü temiz", f"dosya={len(py_files)}")


def _check_env_and_secret_hygiene(root: Path, files: dict[str, str], findings: list[Finding]) -> None:
    env_files = [p for p in root.glob(".env*") if p.is_file() and not p.name.endswith(".example") and p.name not in {".env.example", ".env.production.example", ".env.security.example"}]
    if env_files:
        _add(findings, "UYARI", "secret.env_file_present", "Yerel .env dosyası görüldü", "Canlı overlay içine alınmamalı; sadece sunucuda kalmalı.", ", ".join(p.name for p in env_files))
    else:
        _add(findings, "OK", "secret.no_env_file", ".env dosyası paket içinde görünmüyor")

    risky = []
    secret_url = re.compile(r"postgresql\+psycopg2://[^\s'\"<>]+:[^\s'\"<>]+@", re.I)
    generic_secret = re.compile(r"(?i)(SECRET_KEY|DATABASE_URL|SQLALCHEMY_DATABASE_URI|MAIL_PASSWORD|TCKN_ENCRYPTION_KEY)\s*=\s*['\"][^'\"]{8,}['\"]")
    for rel, text in files.items():
        if rel.endswith(".example") or ".env.example" in rel or ".env.production.example" in rel or ".env.security.example" in rel:
            continue
        if secret_url.search(text) or generic_secret.search(text):
            risky.append(rel)
    if risky:
        _add(findings, "UYARI", "secret.hardcoded", "Kod içinde olası sır/bağlantı kalıbı bulundu; canlı parola olmadığını doğrula", ", ".join(sorted(set(risky))[:12]))
    else:
        _add(findings, "OK", "secret.hardcoded", "Kod içinde açık veritabanı/sır URL kalıbı bulunmadı")

    if any(name in files for name in [".env.example", ".env.production.example", ".env.security.example"]):
        _add(findings, "OK", "secret.env_examples", "Örnek ortam dosyaları mevcut; gerçek sırlar örnek dosyaya yazılmamalı")
    else:
        _add(findings, "UYARI", "secret.env_examples", "Örnek ortam dosyaları görünmedi", "Canlı kurulum standardı için .env.example/.env.production.example tutulması önerilir.")


def _check_auth_session_security(text: str, files: dict[str, str], findings: list[Finding]) -> None:
    checks = [
        ("auth.password_hash", ["password_hash", "generate_password_hash", "check_password_hash"], "Parola hash kullanımı izleri mevcut"),
        ("auth.failed_login_captcha", ["failed_login_attempts", "captcha_required"], "Başarısız giriş ve CAPTCHA alanları mevcut"),
        ("auth.login_required", ["login_required", "current_user"], "Oturum/kimlik doğrulama kullanımı mevcut"),
        ("auth.csrf", ["CSRFProtect", "csrf", "csrf_token"], "CSRF koruması mevcut"),
        ("session.secure_cookie", ["SESSION_COOKIE_SECURE", "REMEMBER_COOKIE_SECURE"], "Güvenli cookie ayarları mevcut"),
        ("session.cookie_flags", ["SESSION_COOKIE_HTTPONLY", "SESSION_COOKIE_SAMESITE"], "Cookie HTTPOnly/SameSite ayarları mevcut"),
    ]
    for code, needles, title in checks:
        matches = _grep_files(files, needles)
        if matches:
            _add(findings, "OK", code, title, ", ".join(matches[:5]))
        else:
            level = "HATA" if code in {"auth.password_hash", "auth.csrf", "auth.login_required"} else "UYARI"
            _add(findings, level, code, title + " bulunamadı")


def _check_access_control_and_audit(files: dict[str, str], findings: list[Finding]) -> None:
    checks = [
        ("access.menu_permissions", ["user_menu_permissions", "role_menu_defaults", "unit_menu_profiles"], "Kişi/rol/birim menü yetki blokları korunuyor"),
        ("access.role_required", ["role_required", "admin_required", "permission"], "Rol/yetki kontrol izleri mevcut"),
        ("audit.audit_logs", ["audit_logs", "AuditLog", "audit_log"], "Denetim izi/audit log izleri mevcut"),
        ("audit.settings_change_logs", ["settings_change_logs", "SettingsChangeLog", "settings_change"], "Ayar değişiklik logları mevcut"),
        ("audit.mail_logs", ["mail_logs", "MailLog"], "Mail log yapısı mevcut"),
    ]
    for code, needles, title in checks:
        matches = _grep_files(files, needles)
        if matches:
            _add(findings, "OK", code, title, ", ".join(matches[:6]))
        else:
            _add(findings, "UYARI", code, title + " doğrudan bulunamadı")


def _check_secure_runtime(files: dict[str, str], findings: list[Finding]) -> None:
    text = "\n".join(files.values())
    if _contains_any(text, ["Content-Security-Policy", "CSP_REPORT_ONLY", "csp", "Talisman"]):
        _add(findings, "OK", "headers.csp", "CSP / güvenlik başlığı izi mevcut")
    else:
        _add(findings, "UYARI", "headers.csp", "CSP / güvenlik başlığı izi doğrudan bulunamadı")

    if _contains_any(text, ["Supheli tarama", "suspicious", "/.env", "rate_limit", "retry_after", "security_audit"]):
        _add(findings, "OK", "runtime.scan_block", "Şüpheli tarama/rate-limit/güvenlik audit izleri mevcut")
    else:
        _add(findings, "UYARI", "runtime.scan_block", "Şüpheli tarama/rate-limit izi doğrudan bulunamadı")

    drop_all = []
    for rel, ftext in files.items():
        if rel.startswith("tests/") or rel.startswith("scripts/") or rel.startswith("docs/") or "test" in rel.lower() or rel.endswith("security_compliance_final_gate.py"):
            continue
        if "drop_all(" in ftext or "db.drop_all" in ftext:
            drop_all.append(rel)
    if drop_all:
        _add(findings, "UYARI", "db.drop_all.runtime", "Çalışma zamanı kodunda drop_all metin izi bulundu; gerçek çağrı olmadığını doğrula", ", ".join(drop_all[:10]))
    else:
        _add(findings, "OK", "db.drop_all.runtime", "Çalışma zamanı kodunda db.drop_all izi bulunmadı")

    debug_true = []
    for rel, ftext in files.items():
        if rel.startswith("tests/") or rel.startswith("scripts/") or rel.endswith("security_compliance_final_gate.py"):
            continue
        if re.search(r"debug\s*=\s*True", ftext):
            debug_true.append(rel)
    if debug_true:
        _add(findings, "UYARI", "runtime.debug_true", "debug=True izi bulundu", ", ".join(debug_true[:8]))
    else:
        _add(findings, "OK", "runtime.debug_true", "Çalışma zamanı dosyalarında debug=True izi bulunmadı")


def _check_kvkk_privacy(files: dict[str, str], findings: list[Finding]) -> None:
    text = "\n".join(files.values())
    if _contains_any(text, ["sicil_no", "Sicil No", "sicil no"]):
        _add(findings, "OK", "kvkk.sicil_no", "Kimlikleme tarafında Sicil No kullanımı mevcut")
    else:
        _add(findings, "UYARI", "kvkk.sicil_no", "Sicil No kullanımı doğrudan bulunamadı")

    tckn_hits = []
    for rel, ftext in files.items():
        if rel.startswith("docs/") or rel.endswith(".md") or rel.endswith(".txt") or rel.endswith("security_compliance_final_gate.py"):
            continue
        if re.search(r"(?i)\b(tckn|tc kimlik|t\.c\.)\b", ftext):
            tckn_hits.append(rel)
    if tckn_hits:
        _add(findings, "UYARI", "kvkk.tckn_trace", "TC/TCKN yazılı izi bulundu; canlı ekranda Sicil No kuralı korunmalı", ", ".join(tckn_hits[:12]))
    else:
        _add(findings, "OK", "kvkk.tckn_trace", "Çalışma zamanı dosyalarında TC/TCKN terimi görünmüyor")

    if _contains_any(text, ["security_answer_hash", "profile_photo", "redaction", "mask", "anonym", "privacy"]):
        _add(findings, "OK", "kvkk.data_minimization", "Kişisel veri saklama/maskeleme/hash izleri mevcut")
    else:
        _add(findings, "UYARI", "kvkk.data_minimization", "Maskeleme/hash/minimizasyon izi zayıf görünüyor")


def _check_iso27001(files: dict[str, str], findings: list[Finding]) -> None:
    text = "\n".join(files.values())
    controls = [
        ("iso27001.access_control", ["role_required", "admin_required", "user_menu_permissions"], "Erişim kontrolü"),
        ("iso27001.logging", ["audit_logs", "security_audit", "mail_logs"], "Loglama ve izlenebilirlik"),
        ("iso27001.change_management", ["alembic", "migrations", "settings_change_logs"], "Değişiklik/migration yönetimi"),
        ("iso27001.incident", ["5xx yanit", "error_handlers", "request_id", "security_audit"], "Hata/olay izleme"),
        ("iso27001.backup", ["backup", "pg_dump", "restore"], "Yedekleme/geri dönüş izleri"),
    ]
    for code, needles, title in controls:
        if _contains_any(text, needles):
            _add(findings, "OK", code, f"TS 27001 kontrol izi mevcut: {title}")
        else:
            _add(findings, "UYARI", code, f"TS 27001 kontrol izi zayıf: {title}")


def _check_iso42001(files: dict[str, str], findings: list[Finding]) -> None:
    text = "\n".join(files.values())
    controls = [
        ("iso42001.ai_logs", ["ai_request_logs", "AIRequestLog", "ai_feedback_logs"], "AI işlem ve geri bildirim logları"),
        ("iso42001.redaction", ["ai_redaction_rules", "redaction", "mask"], "AI veri maskeleme/redaksiyon kuralları"),
        ("iso42001.cache", ["ai_summary_cache", "AISummaryCache"], "AI özet önbelleği ve izlenebilirlik"),
        ("iso42001.recommendations", ["ai_recommendations", "AIRecommendation"], "AI öneri kaydı"),
        ("iso42001.human_decision", ["karar destek", "ön değerlendirme", "onay", "kontrollü"], "AI'nin karar destek olarak konumlanması"),
    ]
    for code, needles, title in controls:
        if _contains_any(text, needles):
            _add(findings, "OK", code, f"ISO 42001 kontrol izi mevcut: {title}")
        else:
            _add(findings, "UYARI", code, f"ISO 42001 kontrol izi zayıf: {title}")


def _check_live_core_and_prior_gates(root: Path, findings: list[Finding]) -> None:
    expected_tables = [
        "users", "organization_units", "user_menu_permissions", "role_menu_defaults", "unit_menu_profiles",
        "system_settings", "module_settings", "settings_change_logs", "audit_logs", "notifications",
        "support_tickets", "attendance_events", "leave_requests", "delegation_assignments",
        "performance_criteria", "performance_periods", "evaluation_assignments", "performance_evaluations",
        "performance_result_snapshots", "messages", "message_threads", "surveys", "survey_assignments",
        "ai_feedback_logs", "ai_recommendations", "ai_redaction_rules", "ai_request_logs", "ai_summary_cache",
    ]
    all_text, files = _all_text(root)
    missing = [t for t in expected_tables if t.lower() not in all_text.lower()]
    if missing:
        _add(findings, "UYARI", "live_core.tables", "Canlı omurga tablo izlerinden bazıları doğrudan bulunamadı", ", ".join(missing[:12]))
    else:
        _add(findings, "OK", "live_core.tables", "Canlı omurga tablo izleri korunuyor", f"adet={len(expected_tables)}")

    reports = {
        "post_sql_refactor_core_gate": root / "reports" / "refactor" / "post_sql_refactor_core_gate.json",
        "live_core_smoke_endpoint_gate": root / "reports" / "refactor" / "live_core_smoke_endpoint_gate.json",
        "performance_manager_rules_final_gate": root / "reports" / "refactor" / "performance_manager_rules_final_gate.json",
    }
    for name, path in reports.items():
        data = _load_json_if_exists(path)
        status = _json_report_passed(data)
        if status is True:
            _add(findings, "OK", f"prior_gate.{name}", f"Önceki gate raporu PASS: {name}", path=str(path))
        elif status is False:
            _add(findings, "UYARI", f"prior_gate.{name}", f"Önceki gate raporu temiz değil: {name}", path=str(path))
        else:
            _add(findings, "UYARI", f"prior_gate.{name}", f"Önceki gate raporu bulunamadı/okunamadı: {name}", path=str(path))


def build_security_compliance_report(root: Path | str) -> SecurityComplianceReport:
    root = Path(root).resolve()
    findings: list[Finding] = []
    if not (root / "app").exists():
        _add(findings, "HATA", "project.app_missing", "app klasörü bulunamadı", path=str(root / "app"))
    if not (root / "scripts").exists():
        _add(findings, "HATA", "project.scripts_missing", "scripts klasörü bulunamadı", path=str(root / "scripts"))

    text, files = _all_text(root)
    _check_compile(root, files, findings)
    _check_env_and_secret_hygiene(root, files, findings)
    _check_auth_session_security(text, files, findings)
    _check_access_control_and_audit(files, findings)
    _check_secure_runtime(files, findings)
    _check_kvkk_privacy(files, findings)
    _check_iso27001(files, findings)
    _check_iso42001(files, findings)
    _check_live_core_and_prior_gates(root, findings)

    ok = sum(1 for f in findings if f.level == "OK")
    hata = sum(1 for f in findings if f.level == "HATA")
    uyari = sum(1 for f in findings if f.level == "UYARI")
    return SecurityComplianceReport(
        version=VERSION,
        generated_at=datetime.now(timezone.utc).isoformat(),
        root=str(root),
        ok=ok,
        hata=hata,
        uyari=uyari,
        findings=findings,
        locked_scope=[
            "KVKK / KVKK-GDPR eşdeğeri teknik kontrol başlıkları",
            "TS 27001 güvenlik işletim kontrol izleri",
            "ISO 42001 AI yönetişim ve loglama kontrol izleri",
            "Canlı omurga: kimlik-yetki-ayarlar, personel, izin/vekâlet, performans, mesaj, anket, destek, AI karar destek",
        ],
    )


def format_security_compliance_report(report: SecurityComplianceReport) -> str:
    status = "PASS" if report.passed() else "FAIL"
    lines = [
        f"BYS360 Güvenlik ve Uyum Final Gate | {status}",
        f"version={report.version}",
        f"OK={report.ok} HATA={report.hata} UYARI={report.uyari}",
        "",
        "Kilitlenen uyum başlıkları:",
    ]
    for item in report.locked_scope:
        lines.append(f"- {item}")
    lines.append("")
    if report.hata:
        lines.append("Hatalar:")
        for f in report.findings:
            if f.level == "HATA":
                detail = f" | {f.detail}" if f.detail else ""
                path = f" | {f.path}" if f.path else ""
                lines.append(f"- HATA | {f.code} | {f.title}{detail}{path}")
    if report.uyari:
        lines.append("Uyarılar:")
        for f in report.findings:
            if f.level == "UYARI":
                detail = f" | {f.detail}" if f.detail else ""
                path = f" | {f.path}" if f.path else ""
                lines.append(f"- UYARI | {f.code} | {f.title}{detail}{path}")
    if report.passed():
        lines.append("")
        lines.append("SECURITY_COMPLIANCE_FINAL_GATE_OK")
    return "\n".join(lines)


def _to_json(report: SecurityComplianceReport) -> dict:
    return {
        "version": report.version,
        "generated_at": report.generated_at,
        "root": report.root,
        "status": "PASS" if report.passed() else "FAIL",
        "ok": report.ok,
        "hata": report.hata,
        "uyari": report.uyari,
        "locked_scope": report.locked_scope,
        "findings": [asdict(f) for f in report.findings],
    }


def _to_md(report: SecurityComplianceReport) -> str:
    status = "PASS" if report.passed() else "FAIL"
    rows = []
    for f in report.findings:
        rows.append(f"| {f.level} | `{f.code}` | {f.title.replace('|', '/')} | {f.detail.replace('|', '/') if f.detail else ''} | {f.path.replace('|', '/') if f.path else ''} |")
    return "\n".join([
        f"# BYS360 Güvenlik ve Uyum Final Gate",
        "",
        f"- Durum: **{status}**",
        f"- Sürüm: `{report.version}`",
        f"- Üretilme: `{report.generated_at}`",
        f"- OK/HATA/UYARI: **{report.ok}/{report.hata}/{report.uyari}**",
        "",
        "## Kapsam",
        "",
        *[f"- {item}" for item in report.locked_scope],
        "",
        "## Bulgular",
        "",
        "| Seviye | Kod | Başlık | Detay | Yol |",
        "|---|---|---|---|---|",
        *rows,
        "",
        "## Not",
        "",
        "Bu gate teknik hazırlık ve kanıt izi kontrolüdür. Resmî KVKK/TS 27001/ISO 42001 belgelendirme veya hukukî görüş yerine geçmez.",
    ])


def write_security_compliance_reports(report: SecurityComplianceReport, root: Path | str) -> dict[str, str]:
    root = Path(root).resolve()
    report_dir = root / "reports" / "refactor"
    doc_dir = root / "docs" / "refactor" / "generated"
    report_dir.mkdir(parents=True, exist_ok=True)
    doc_dir.mkdir(parents=True, exist_ok=True)
    json_path = report_dir / f"{REPORT_STEM}.json"
    md_path = report_dir / f"{REPORT_STEM}.md"
    doc_path = doc_dir / f"{REPORT_STEM}.md"
    json_path.write_text(json.dumps(_to_json(report), ensure_ascii=False, indent=2), encoding="utf-8")
    md = _to_md(report)
    md_path.write_text(md, encoding="utf-8")
    doc_path.write_text(md, encoding="utf-8")
    return {"json": str(json_path), "md": str(md_path), "doc": str(doc_path)}
