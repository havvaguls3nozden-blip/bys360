
"""BYS360 canlı omurga smoke test ve endpoint gate.

Bu servis canlı davranış değiştirmez. Kaynak kod üzerinde statik rota sözleşmesini
kontrol eder ve isteğe bağlı olarak çalışan lokal uygulama üzerinde temel GET
endpoint'lerini yoklar. DB yazma, migration veya veri değişikliği yapmaz.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

GATE_VERSION = "2026-04-21-live-core-smoke-endpoint-gate"

ROUTE_RE = re.compile(r"@[^\n]*?\.route\(\s*([\"'])(?P<path>/[^\"']*)\1", re.UNICODE)
URL_FOR_RE = re.compile(r"url_for\(\s*([\"'])(?P<endpoint>[^\"']+)\1", re.UNICODE)

REQUIRED_STATIC_ENDPOINTS: tuple[tuple[str, str, str], ...] = (
    ("auth", "Giriş ekranı", "/login"),
    ("dashboard", "Ana dashboard", "/dashboard"),
    ("dashboard", "Performans dashboard", "/performance/dashboard"),
    ("personnel", "Personel yönetimi", "/hr-management"),
    ("personnel", "İzin ve devamsızlık", "/hr-management/leave"),
    ("personnel", "Personel raporları", "/hr-management/reports"),
    ("performance", "Performans görev yönetimi", "/performance/task-management"),
    ("performance", "Performans görev sağlık", "/performance/task-management/health"),
    ("messages", "Mesajlar", "/messages"),
    ("messages", "Yeni mesaj", "/messages/new"),
    ("notifications", "Bildirimler", "/notifications"),
    ("notifications", "Bildirim rozet sayacı", "/notifications/unread-count"),
    ("support", "Yardım merkezi", "/support"),
    ("support", "Destek talebi oluşturma", "/support/new"),
    ("support", "Destek taleplerim", "/support/my-tickets"),
    ("surveys", "Anket kullanıcı ekranı", "/surveys"),
    ("surveys", "Anket yönetimi", "/survey-manage"),
    ("ai", "AI karar destek merkezi", "/admin/ai-center"),
    ("ai", "AI işlem logları", "/admin/ai-requests"),
)

HTTP_SMOKE_ENDPOINTS: tuple[tuple[str, str], ...] = (
    ("Giriş ekranı", "/login"),
    ("Ana dashboard", "/dashboard"),
    ("Performans dashboard", "/performance/dashboard"),
    ("Personel yönetimi", "/hr-management"),
    ("İzin ve devamsızlık", "/hr-management/leave"),
    ("Performans görev yönetimi", "/performance/task-management"),
    ("Mesajlar", "/messages"),
    ("Bildirim rozet sayacı", "/notifications/unread-count"),
    ("Yardım merkezi", "/support"),
    ("Anketler", "/surveys"),
    ("AI karar destek merkezi", "/admin/ai-center"),
)

# Bu pattern'ler sadece base.html / ana navigasyon içinde aranır. Eski modüllerin
# kod kalıntısı olabilir; canlı riski menüde görünür olmasıdır.
FORBIDDEN_NAV_PATTERNS: tuple[tuple[str, str], ...] = (
    ("Eğitim ana menüsü", r"href=[\"'][^\"']*/education(?:/|[\"'#?])"),
    ("İSG ana menüsü", r"href=[\"'][^\"']*/isg(?:/|[\"'#?])"),
    ("Strateji ana menüsü", r"href=[\"'][^\"']*/strategy(?:/|[\"'#?])"),
    ("Belge-medya deposu ana menüsü", r"href=[\"'][^\"']*/repository(?:/|[\"'#?])"),
    ("İç portal ana menüsü", r"href=[\"'][^\"']*/portal(?:/|[\"'#?])"),
)

REQUIRED_NAV_TERMS: tuple[str, ...] = (
    "Personel Yönetimi",
    "Performans Yönetimi",
    "Yardım Merkezi",
    "Mesaj",
    "Anket",
    "AI Karar Destek",
)

@dataclass
class GateItem:
    status: str
    code: str
    message: str
    detail: str = ""


@dataclass
class SmokeReport:
    version: str
    generated_at: str
    project_root: str
    base_url: str
    http_required: bool
    ok: list[GateItem] = field(default_factory=list)
    errors: list[GateItem] = field(default_factory=list)
    warnings: list[GateItem] = field(default_factory=list)
    discovered_routes: int = 0
    discovered_url_for: int = 0

    def passed(self) -> bool:
        return not self.errors

    def add_ok(self, code: str, message: str, detail: str = "") -> None:
        self.ok.append(GateItem("OK", code, message, detail))

    def add_error(self, code: str, message: str, detail: str = "") -> None:
        self.errors.append(GateItem("HATA", code, message, detail))

    def add_warning(self, code: str, message: str, detail: str = "") -> None:
        self.warnings.append(GateItem("UYARI", code, message, detail))


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig", errors="replace")
    except OSError:
        return ""


def _iter_code_files(root: Path) -> list[Path]:
    targets: list[Path] = []
    for rel in ("app", "scripts"):
        base = root / rel
        if base.exists():
            targets.extend(p for p in base.rglob("*.py") if "__pycache__" not in p.parts)
    return sorted(targets)


def discover_routes(root: Path) -> tuple[set[str], set[str]]:
    routes: set[str] = set()
    endpoints: set[str] = set()
    for path in _iter_code_files(root):
        text = _read_text(path)
        routes.update(match.group("path") for match in ROUTE_RE.finditer(text))
        endpoints.update(match.group("endpoint") for match in URL_FOR_RE.finditer(text))
    return routes, endpoints


def _find_base_template(root: Path) -> Path | None:
    candidates = (
        root / "app" / "templates" / "base.html",
        root / "templates" / "base.html",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def check_static_contract(report: SmokeReport, root: Path) -> None:
    routes, endpoints = discover_routes(root)
    report.discovered_routes = len(routes)
    report.discovered_url_for = len(endpoints)

    if not routes:
        report.add_error("route.discovery", "Hiç Flask route bulunamadı", "app/**/*.py taraması boş döndü")
        return
    report.add_ok("route.discovery", f"Flask route keşfi yapıldı: {len(routes)} route")

    missing: list[str] = []
    for category, label, route_path in REQUIRED_STATIC_ENDPOINTS:
        if route_path in routes:
            report.add_ok(f"static.{category}", f"{label} route mevcut", route_path)
        else:
            missing.append(f"{label}: {route_path}")
    if missing:
        report.add_error("static.required_routes", "Canlı omurga için zorunlu route eksikleri var", " | ".join(missing))

    base_template = _find_base_template(root)
    if base_template is None:
        report.add_warning("nav.base_template", "base.html bulunamadı; ana menü görünürlük kontrolü atlandı")
        return

    base_text = _read_text(base_template)
    for label, pattern in FORBIDDEN_NAV_PATTERNS:
        if re.search(pattern, base_text, flags=re.IGNORECASE | re.UNICODE):
            report.add_error("nav.removed_scope", f"Canlı kapsam dışı menü bağlantısı görünüyor: {label}", pattern)
        else:
            report.add_ok("nav.removed_scope", f"Canlı kapsam dışı menü bağlantısı yok: {label}")

    for term in REQUIRED_NAV_TERMS:
        if term.lower() in base_text.lower():
            report.add_ok("nav.required_term", f"Ana menü/üst menü terimi mevcut: {term}")
        else:
            report.add_warning("nav.required_term", f"Ana menü terimi doğrudan bulunamadı: {term}")

    if "Ekip Kıyas" in base_text:
        report.add_error("nav.legacy_label", "Eski 'Ekip Kıyas' etiketi base.html içinde kalmış", "Beklenen ifade: Personel Analizi")
    else:
        report.add_ok("nav.legacy_label", "Eski 'Ekip Kıyas' etiketi ana şablonda yok")


def _http_get_status(url: str, timeout: float) -> tuple[int | None, str]:
    request = urllib.request.Request(
        url,
        method="GET",
        headers={
            "User-Agent": "BYS360-Live-Core-Smoke-Gate/1.0",
            "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310 - internal smoke test
            return int(response.status), response.geturl()
    except urllib.error.HTTPError as exc:
        return int(exc.code), url
    except (urllib.error.URLError, TimeoutError) as exc:
        return None, str(exc)


def check_http_smoke(report: SmokeReport, base_url: str, require_http: bool) -> None:
    normalized = base_url.rstrip("/")
    timeout = float(os.environ.get("BYS360_SMOKE_TIMEOUT", "4"))
    any_connection_error = False

    for label, path in HTTP_SMOKE_ENDPOINTS:
        status, detail = _http_get_status(f"{normalized}{path}", timeout=timeout)
        if status is None:
            any_connection_error = True
            report.add_warning("http.unreachable", f"HTTP smoke erişemedi: {label}", f"{path} | {detail}")
            continue
        if status in {200, 204, 301, 302, 303, 307, 308, 401, 403}:
            report.add_ok("http.endpoint", f"HTTP endpoint cevap verdi: {label}", f"{path} -> {status}")
            continue
        if status == 404:
            report.add_error("http.not_found", f"HTTP endpoint bulunamadı: {label}", f"{path} -> 404")
        elif status >= 500:
            report.add_error("http.server_error", f"HTTP endpoint 5xx verdi: {label}", f"{path} -> {status}")
        else:
            report.add_warning("http.unexpected_status", f"HTTP endpoint beklenmeyen durum döndürdü: {label}", f"{path} -> {status}")

    if any_connection_error and require_http:
        report.add_error(
            "http.required",
            "HTTP smoke zorunlu ama çalışan uygulamaya ulaşılamadı",
            f"Base URL: {normalized}. Önce Waitress'i aç: python -m waitress --listen=0.0.0.0:8000 --threads=12 --no-log-socket-errors wsgi:app",
        )
    elif any_connection_error:
        report.add_warning("http.optional", "HTTP smoke isteğe bağlıydı; erişilemeyen endpointler hata sayılmadı")


def build_live_core_smoke_report(root: Path, base_url: str | None = None, require_http: bool | None = None) -> SmokeReport:
    base_url = base_url or os.environ.get("BYS360_SMOKE_BASE_URL", "http://127.0.0.1:8000")
    if require_http is None:
        require_http = os.environ.get("BYS360_SMOKE_REQUIRE_HTTP", "0").strip().lower() in {"1", "true", "yes", "evet"}

    report = SmokeReport(
        version=GATE_VERSION,
        generated_at=datetime.now(UTC).isoformat(),
        project_root=str(root),
        base_url=base_url,
        http_required=require_http,
    )
    check_static_contract(report, root)
    check_http_smoke(report, base_url, require_http)
    return report


def _item_to_dict(item: GateItem) -> dict[str, str]:
    return {"status": item.status, "code": item.code, "message": item.message, "detail": item.detail}


def report_to_dict(report: SmokeReport) -> dict[str, object]:
    return {
        "version": report.version,
        "generated_at": report.generated_at,
        "project_root": report.project_root,
        "base_url": report.base_url,
        "http_required": report.http_required,
        "passed": report.passed(),
        "summary": {
            "ok": len(report.ok),
            "errors": len(report.errors),
            "warnings": len(report.warnings),
            "discovered_routes": report.discovered_routes,
            "discovered_url_for": report.discovered_url_for,
        },
        "ok": [_item_to_dict(item) for item in report.ok],
        "errors": [_item_to_dict(item) for item in report.errors],
        "warnings": [_item_to_dict(item) for item in report.warnings],
    }


def write_live_core_smoke_reports(report: SmokeReport, root: Path) -> dict[str, str]:
    report_dir = root / "reports" / "refactor"
    doc_dir = root / "docs" / "refactor" / "generated"
    report_dir.mkdir(parents=True, exist_ok=True)
    doc_dir.mkdir(parents=True, exist_ok=True)

    data = report_to_dict(report)
    json_path = report_dir / "live_core_smoke_endpoint_gate.json"
    md_path = report_dir / "live_core_smoke_endpoint_gate.md"
    doc_path = doc_dir / "live_core_smoke_endpoint_gate.md"

    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    md = format_live_core_smoke_report(report, markdown=True)
    md_path.write_text(md, encoding="utf-8")
    doc_path.write_text(md, encoding="utf-8")
    return {"json": str(json_path), "md": str(md_path), "doc": str(doc_path)}


def format_live_core_smoke_report(report: SmokeReport, markdown: bool = False) -> str:
    status = "PASS" if report.passed() else "FAIL"
    lines: list[str] = []
    if markdown:
        lines.append(f"# BYS360 Canlı Omurga Smoke / Endpoint Gate — {status}")
        lines.append("")
        lines.append(f"- version: `{report.version}`")
        lines.append(f"- base_url: `{report.base_url}`")
        lines.append(f"- http_required: `{report.http_required}`")
        lines.append(f"- discovered_routes: `{report.discovered_routes}`")
        lines.append(f"- OK: `{len(report.ok)}`")
        lines.append(f"- HATA: `{len(report.errors)}`")
        lines.append(f"- UYARI: `{len(report.warnings)}`")
        sections = (("Hatalar", report.errors), ("Uyarılar", report.warnings), ("Başarılı Kontroller", report.ok))
        for title, items in sections:
            lines.append("")
            lines.append(f"## {title}")
            if not items:
                lines.append("- Yok")
            for item in items:
                detail = f" — {item.detail}" if item.detail else ""
                lines.append(f"- **{item.code}**: {item.message}{detail}")
        return "\n".join(lines) + "\n"

    lines.append(f"BYS360 Canlı Omurga Smoke / Endpoint Gate | {status}")
    lines.append(f"version={report.version}")
    lines.append(f"base_url={report.base_url} | http_required={report.http_required}")
    lines.append(f"OK={len(report.ok)} HATA={len(report.errors)} UYARI={len(report.warnings)} route={report.discovered_routes}")
    if report.errors:
        lines.append("\nHatalar:")
        for item in report.errors:
            detail = f" | {item.detail}" if item.detail else ""
            lines.append(f"- HATA | {item.code} | {item.message}{detail}")
    if report.warnings:
        lines.append("\nUyarılar:")
        for item in report.warnings[:12]:
            detail = f" | {item.detail}" if item.detail else ""
            lines.append(f"- UYARI | {item.code} | {item.message}{detail}")
        if len(report.warnings) > 12:
            lines.append(f"- UYARI | truncated | {len(report.warnings) - 12} uyarı daha raporda")
    if report.passed():
        lines.append("\nLIVE_CORE_SMOKE_ENDPOINT_GATE_OK")
    return "\n".join(lines)
