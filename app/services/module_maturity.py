from __future__ import annotations



from dataclasses import asdict, dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class MaturityCheck:
    label: str
    weight: float
    ok: bool
    note: str = ""


@dataclass(frozen=True)
class ModuleMaturity:
    key: str
    label: str
    score: float
    level: str
    checks: tuple[MaturityCheck, ...]

    def as_dict(self) -> dict:
        return {"key": self.key, "label": self.label, "score": self.score, "level": self.level, "checks": [asdict(c) for c in self.checks]}


def _exists(path: str) -> bool:
    return (PROJECT_ROOT / path).exists()


def _contains(path: str, *tokens: str) -> bool:
    file_path = PROJECT_ROOT / path
    if not file_path.exists():
        return False
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    return all(token in text for token in tokens)


def _score(checks: list[MaturityCheck]) -> float:
    total = sum(c.weight for c in checks) or 1
    earned = sum(c.weight for c in checks if c.ok)
    return round((earned / total) * 10, 1)


def _level(score: float) -> str:
    if score >= 9.5:
        return "10/10 hedefe hazır"
    if score >= 8.5:
        return "canlıya uygun / ileri"
    if score >= 7.0:
        return "pilot güçlü"
    return "güçlendirme gerekli"


def _module(key: str, label: str, checks: list[MaturityCheck]) -> ModuleMaturity:
    score = _score(checks)
    return ModuleMaturity(key, label, score, _level(score), tuple(checks))


def build_module_maturity_report() -> dict:
    modules = [
        _module("security", "Kimlik, güvenlik ve yetki", [
            MaturityCheck("Rol ve menü guard", 1.5, _exists("app/security/decorators.py") and _exists("app/view_helpers.py")),
            MaturityCheck("CSRF ve güvenlik başlıkları", 1.0, _exists("app/security_headers.py") and _contains("app/__init__.py", "csrf.init_app")),
            MaturityCheck("Paylaşımlı rate-limit", 2.0, _contains("app/security/rate_limit_store.py", "Redis.from_url", "record_bucket_hit")),
            MaturityCheck("Captcha entegrasyonu", 1.0, _exists("app/security/captcha_guard.py")),
            MaturityCheck("HTTP smoke testi", 1.5, _exists("tests/integration/test_http_core_smoke.py")),
            MaturityCheck("CI kalite kapısı", 1.5, _exists(".github/workflows/bys360-quality.yml")),
            MaturityCheck("Ortam ayarları", 1.5, _contains("config.py", "REDIS_URL", "SESSION_COOKIE_HTTPONLY", "AUTO_REPAIR_SCHEMA")),
        ]),
        _module("performance", "Performans Yönetimi", [
            MaturityCheck("Merkezi zincir motoru", 2.0, _exists("app/services/performance/chain_rule_engine.py")),
            MaturityCheck("Görev üretim kapısı", 1.5, _exists("app/services/performance/assignment_rule_audit.py")),
            MaturityCheck("Görünürlük kilidi", 1.5, _exists("app/services/performance/visibility_guard.py")),
            MaturityCheck("Yayın ön kontrol", 1.5, _exists("app/services/performance/publish_preflight_rules.py")),
            MaturityCheck("Personel Analizi adı", 1.0, _contains("app/templates/team_compare.html", "Personel Analizi")),
            MaturityCheck("Çekirdek sağlık paneli", 1.5, _exists("app/services/performance/core_health_panel.py") and _exists("app/performance/core_health_routes.py")),
            MaturityCheck("Davranış/statik testler", 1.0, _exists("tests/test_performance_chain_constitution.py") and _exists("tests/test_performance_visibility_constitution_static.py")),
        ]),
        _module("hr", "Personel, izin, devamsızlık ve vekâlet", [
            MaturityCheck("İK route sahipliği", 1.5, _exists("app/institutional/routes.py")),
            MaturityCheck("İzin gerçek kayıt akışı", 2.0, _contains("app/institutional/routes.py", "PersonnelLeave", "LeaveBalance")),
            MaturityCheck("Devamsızlık gerçek kayıt akışı", 1.5, _contains("app/institutional/routes.py", "AttendanceException")),
            MaturityCheck("Vekâlet entegrasyonu", 1.5, _contains("app/institutional/routes.py", "DelegationAssignment")),
            MaturityCheck("Rapor şablonu korunmuş", 1.0, _exists("app/templates/hr_reports.html")),
            MaturityCheck("HR statik kapı", 1.0, _exists("tests/test_hr_leave_attendance_real_post_static.py")),
            MaturityCheck("Dashboard/menü çakışma testi", 1.5, _exists("tests/test_no_admin_org_units_duplicate_static.py") and _exists("tests/test_hr_reports_template_no_unpack_static.py")),
        ]),
        _module("communication", "İletişim, anket ve geri bildirim", [
            MaturityCheck("Mesajlaşma route ailesi", 1.2, _exists("app/communication/messages_routes.py")),
            MaturityCheck("Anket route ailesi", 1.2, _exists("app/communication/surveys_routes.py")),
            MaturityCheck("Geri bildirim service", 1.4, _exists("app/services/feedback_service.py")),
            MaturityCheck("Anonim nabız gizliliği", 1.8, _contains("app/services/feedback_service.py", "_build_pulse_risk_users_from_rows", "is_anonymous")),
            MaturityCheck("Paylaşımlı nabız cache", 1.4, _contains("app/services/feedback_service.py", "_shared_cache_get_json", "feedback:pulse")),
            MaturityCheck("Geri bildirim davranış testi", 1.5, _exists("tests/test_feedback_pulse_privacy_behavior.py")),
            MaturityCheck("Route contract testleri", 1.5, _exists("tests/communication/test_feedback_contracts.py") and _exists("tests/communication/test_communication_route_contracts.py")),
        ]),
        _module("operations", "Operasyon, test ve devredilebilirlik", [
            MaturityCheck("GitHub Actions", 2.0, _exists(".github/workflows/bys360-quality.yml")),
            MaturityCheck("HTTP entegrasyon testi", 2.0, _exists("tests/integration/test_http_core_smoke.py")),
            MaturityCheck("Redis-ready altyapı", 1.5, _exists("app/services/shared_cache_store.py")),
            MaturityCheck("Kalite kapısı scripti", 1.5, _exists("scripts/check_advanced_maturity_gate.py")),
            MaturityCheck("Production config", 1.0, _exists("gunicorn.conf.py") and _exists("Procfile")),
            MaturityCheck("Test konfigürasyonu", 1.0, _exists("pytest.ini") and _exists("pyproject.toml")),
        ]),
    ]
    overall = round(sum(m.score for m in modules) / len(modules), 1)
    return {"overall_score": overall, "overall_level": _level(overall), "modules": [m.as_dict() for m in modules]}


__all__ = ["build_module_maturity_report"]
