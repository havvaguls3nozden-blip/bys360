from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


LARGE_RULE = "LARGE_FILE_HARD"
REPAIR_RULE = "MANY_REPAIR_SCRIPTS"


REFACTOR_GUIDE = {
    "app/static/js/bys360_assistant_module.js": {
        "risk": "HIGH",
        "phase": "P11-A",
        "title": "BYS360 Asistan JS parçalama",
        "strategy": [
            "Dosya doğrudan bölünmemeli; önce mevcut global davranışların envanteri çıkarılmalı.",
            "Önerilen parçalar: assistant_core.js, assistant_sanitizer.js, assistant_screen_context.js, assistant_weather.js, assistant_ui_render.js.",
            "İlk adım sadece yardımcı fonksiyonları yeni dosyalara almak ve eski dosyada bridge/export bırakmak olmalı.",
            "Her adım sonrası ana sayfa, performans ekranı, destek ekranı ve asistan paneli smoke test edilmelidir.",
        ],
        "tests": [
            "python -m compileall app scripts",
            "Ana sayfada asistan açılıyor mu?",
            "Sayfa değiştirince konuşma/panel kayboluyor mu?",
            "Eski teknik ifadeler kullanıcıya görünüyor mu?",
        ],
    },
    "app/api/mobile/routes.py": {
        "risk": "HIGH",
        "phase": "P11-B",
        "title": "Mobil API ana route dosyası parçalama",
        "strategy": [
            "Tek seferde bölünmemeli; önce endpoint envanteri ve prefix grupları çıkarılmalı.",
            "Önerilen parçalar: auth_routes.py, dashboard_routes.py, personnel_routes.py, support_routes.py, communication_routes.py.",
            "Mevcut blueprint adı ve URL prefix korunmalı; dış mobil uygulama davranışı değişmemeli.",
            "Taşıma sonrası import döngüsü ve route çakışması kontrol edilmelidir.",
        ],
        "tests": [
            "flask routes veya mevcut route listesi kontrolü",
            "Mobil login",
            "Mobil dashboard",
            "Mobil personel/destek/iletişim smoke",
        ],
    },
    "app/api/mobile/performance_routes.py": {
        "risk": "HIGH",
        "phase": "P11-C",
        "title": "Mobil performans route dosyası parçalama",
        "strategy": [
            "Önce okuma-only endpointler ile işlem yapan endpointler ayrılmalı.",
            "Önerilen parçalar: performance_summary_routes.py, performance_tasks_routes.py, performance_scorecard_routes.py, performance_admin_routes.py.",
            "Mobil Flutter tarafındaki /api/mobile/performance/... yolları aynen korunmalı.",
            "Başkan onayı, yayın ön onayı ve risk analizi route davranışları ayrı smoke test edilmeli.",
        ],
        "tests": [
            "Mobil performans ana ekran",
            "Puanlama formu endpointi",
            "Başkan/Üst Onayları",
            "Riskli Personel Analizi",
            "flutter analyze",
        ],
    },
    "app/menu_registry.py": {
        "risk": "MEDIUM_HIGH",
        "phase": "P11-D",
        "title": "Menü kayıt defteri domain parçalama",
        "strategy": [
            "Önce salt veri listeleri domain dosyalarına ayrılmalı; davranış fonksiyonları en son taşınmalı.",
            "Önerilen parçalar: menu_core.py, menu_performance.py, menu_settings.py, menu_ai.py, menu_support.py.",
            "Mevcut menu_key değerleri kesinlikle değişmemeli.",
            "Rol matrisi ve kişi bazlı menü görünürlüğü özel regresyon testine alınmalı.",
        ],
        "tests": [
            "Admin menü görünürlüğü",
            "Başkan rolünde Başkan Onayları sekmesi",
            "Yetkisiz kullanıcıda menü gizlenmesi",
            "Rol matrisi kaydetme",
        ],
    },
    "app/services/settings/effective_menu.py": {
        "risk": "MEDIUM_HIGH",
        "phase": "P11-E",
        "title": "Etkili menü yetki servisi parçalama",
        "strategy": [
            "Önce saf hesaplama fonksiyonları ayrılmalı; veritabanı erişimi aynı dosyada kalabilir.",
            "Önerilen parçalar: effective_menu_calculator.py, effective_menu_policy.py, effective_menu_repository.py.",
            "Kişi bazlı görünürlük, rol bazlı görünürlük ve fallback davranışı ayrı test edilmeli.",
        ],
        "tests": [
            "Kişi bazlı menü işaretle/kaydet",
            "Ayarlar sayfası erişimi",
            "Performans menüleri rol bazlı görünürlük",
        ],
    },
    "app/templates/settings.html": {
        "risk": "MEDIUM",
        "phase": "P11-F",
        "title": "Ayarlar şablonu partial yapıya alma",
        "strategy": [
            "Jinja partial extraction yapılmalı; backend route değiştirilmemeli.",
            "Önerilen partiallar: _settings_header.html, _role_matrix.html, _menu_visibility.html, _system_security.html.",
            "Form id/name alanları korunmalı.",
        ],
        "tests": [
            "Ayarlar sayfası açılışı",
            "Rol matrisi kaydetme",
            "Kişi bazlı ayarlar kaydetme",
        ],
    },
    "app/templates/evaluation_form.html": {
        "risk": "MEDIUM",
        "phase": "P11-G",
        "title": "Değerlendirme formu şablon parçalama",
        "strategy": [
            "Önce sadece görsel bloklar partial yapılmalı.",
            "Önerilen partiallar: _evaluation_header.html, _criteria_table.html, _score_inputs.html, _manager_notes.html.",
            "Puan input name/id değerleri değişmemeli.",
        ],
        "tests": [
            "Değerlendirme formu açılışı",
            "1-5 puan açıklama zorunluluğu",
            "70 altı ve 90 üstü genel görüş zorunluluğu",
            "Form submit",
        ],
    },
    "app/static/css/performance_phase3.css": {
        "risk": "MEDIUM",
        "phase": "P11-H",
        "title": "Performans CSS parçalama",
        "strategy": [
            "Önce CSS dosyası import mantığıyla bölünmeli; sınıf adları değişmemeli.",
            "Önerilen parçalar: performance_layout.css, performance_cards.css, performance_tables.css, performance_mobile.css.",
            "Görsel regresyon kontrolü manuel yapılmalı.",
        ],
        "tests": [
            "Performans dashboard görünümü",
            "Scorecard sayfası",
            "Mobil responsive kontrol",
        ],
    },
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def collect_findings(data: Any, level: str = "P1") -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    level = level.upper()

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            sev = str(x.get("severity") or x.get("level") or x.get("priority") or x.get("rank") or "").upper()
            rule = str(x.get("rule") or x.get("code") or x.get("type") or x.get("category") or x.get("check") or "")
            path = str(x.get("path") or x.get("file") or x.get("filename") or x.get("rel_path") or x.get("relative_path") or "")
            line = x.get("line") or x.get("line_number") or x.get("lineno") or ""
            msg = str(x.get("message") or x.get("detail") or x.get("description") or x.get("reason") or "")
            if sev == level and (path or rule or msg):
                findings.append({
                    "severity": sev,
                    "rule": rule,
                    "path": path.replace("\\", "/").lstrip("./"),
                    "line": line,
                    "message": msg,
                })
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)

    walk(data)

    seen = set()
    uniq = []
    for item in findings:
        key = (item["rule"], item["path"], str(item["line"]), item["message"])
        if key not in seen:
            seen.add(key)
            uniq.append(item)
    return uniq


def line_count(path: Path) -> int:
    if not path.exists() or not path.is_file():
        return 0
    return len(path.read_text(encoding="utf-8", errors="ignore").splitlines())


def script_inventory(project_root: Path) -> dict[str, Any]:
    scripts = project_root / "scripts"
    if not scripts.exists():
        return {"count": 0, "files": []}

    terms = ("repair", "fix", "hotfix")
    files = []
    for p in scripts.rglob("*"):
        if p.is_file() and any(t in p.name.lower() for t in terms):
            files.append(str(p.relative_to(project_root)).replace("\\", "/"))
    return {"count": len(files), "files": sorted(files)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--limit", type=int, default=160)
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    clean_report = project_root / "reports" / "quality" / "bys360_quality_10_10_audit_v1_clean.json"
    decision_report = project_root / "reports" / "quality" / "bys360_quality_10_10_p10_2_final_p1_decision_v1.json"

    if not clean_report.exists():
        raise SystemExit(f"REPORT_NOT_FOUND: {clean_report}")

    findings = collect_findings(load_json(clean_report), "P1")
    large = [f for f in findings if f["rule"] == LARGE_RULE]
    repair = [f for f in findings if f["rule"] == REPAIR_RULE]

    large_items = []
    for f in large:
        rel = f["path"]
        guide = REFACTOR_GUIDE.get(rel, {
            "risk": "REVIEW",
            "phase": "P11-X",
            "title": "Refactor planı incelenecek",
            "strategy": ["Dosya için özel refactor planı hazırlanmalı."],
            "tests": ["Dosyaya özel smoke test belirlenmeli."],
        })
        large_items.append({
            **f,
            "line_count_actual": line_count(project_root / rel),
            **guide,
        })

    inv = script_inventory(project_root)
    decision = {}
    if decision_report.exists():
        decision = load_json(decision_report)

    p11 = {
        "project_root": str(project_root),
        "source_clean_report": str(clean_report),
        "source_decision_report": str(decision_report) if decision_report.exists() else None,
        "raw_p1": len(findings),
        "p10_2_summary": {
            "accepted_false_positive": decision.get("accepted_false_positive"),
            "planned_p1_items": decision.get("planned_p1_items"),
            "active_review_items": decision.get("active_review_items"),
        } if isinstance(decision, dict) else {},
        "large_file_refactor_items": large_items,
        "repair_script_plan": {
            "raw_findings": repair,
            "inventory": inv,
            "recommended_action": [
                "Canlı geliştirmede kullanılan en güncel gate/check scriptleri scripts/windows altında kalmalı.",
                "Tek seferlik repair/fix/hotfix scriptleri scripts/archive veya docs/quality/changelog altında arşivlenmeli.",
                "Release pipeline tek komutta compile, audit, flutter analyze ve smoke adımlarını çalıştırmalı.",
                "Eski scriptler silinmeden önce zip checkpoint alınmalı.",
            ],
        },
    }

    output_dir = project_root / "reports" / "quality"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_out = output_dir / "bys360_quality_10_10_p11_refactor_plan_v1.json"
    md_out = output_dir / "bys360_quality_10_10_p11_refactor_plan_v1.md"
    json_out.write_text(json.dumps(p11, ensure_ascii=False, indent=2), encoding="utf-8")

    md = []
    md.append("# BYS360 Quality 10/10 P11 Refactor Planı")
    md.append("")
    md.append("## Mevcut Durum")
    md.append("")
    md.append(f"- Raw P1: {len(findings)}")
    if isinstance(decision, dict):
        md.append(f"- Accepted false-positive: {decision.get('accepted_false_positive')}")
        md.append(f"- Planned P1 items: {decision.get('planned_p1_items')}")
        md.append(f"- Active review items: {decision.get('active_review_items')}")
    md.append("")
    md.append("## Büyük Dosya Refactor Planı")
    md.append("")
    for item in sorted(large_items, key=lambda x: x.get("phase", "")):
        md.append(f"### {item['phase']} — {item['title']}")
        md.append("")
        md.append(f"- Dosya: `{item['path']}`")
        md.append(f"- Gerçek satır sayısı: {item['line_count_actual']}")
        md.append(f"- Risk: {item['risk']}")
        md.append(f"- Audit mesajı: {item['message']}")
        md.append("")
        md.append("Önerilen strateji:")
        for s in item["strategy"]:
            md.append(f"- {s}")
        md.append("")
        md.append("Kontrol listesi:")
        for t in item["tests"]:
            md.append(f"- {t}")
        md.append("")
    md.append("## Repair/Fix/Hotfix Script Planı")
    md.append("")
    md.append(f"- Envanterde bulunan repair/fix/hotfix script sayısı: {inv['count']}")
    md.append("")
    md.append("Önerilen aksiyon:")
    for s in p11["repair_script_plan"]["recommended_action"]:
        md.append(f"- {s}")
    md.append("")
    md.append("## Uygulama Sırası")
    md.append("")
    md.append("1. P11-A: Asistan JS için envanter ve yardımcı modül çıkarma.")
    md.append("2. P11-B/C: Mobil route dosyalarında endpoint envanteri, sonra domain parçalama.")
    md.append("3. P11-D/E: Menü registry ve effective menu servislerinde veri/policy ayrımı.")
    md.append("4. P11-F/G/H: Template ve CSS partial parçalama.")
    md.append("5. Script arşiv/CI düzeni.")
    md.append("")
    md.append("Bu plan doğrudan kod değiştirmez; refactor başlamadan önce güvenli sıralama ve test kapsamı oluşturur.")
    md_out.write_text("\n".join(md) + "\n", encoding="utf-8")

    print("BYS360_QUALITY_10_10_P11_REFACTOR_PLAN_START")
    print(f"project_root={project_root}")
    print(f"raw_p1={len(findings)}")
    print(f"large_file_items={len(large_items)}")
    print(f"repair_script_findings={len(repair)}")
    print(f"repair_script_inventory_count={inv['count']}")
    print("BYS360_QUALITY_10_10_P11_REFACTOR_ITEMS")
    for item in sorted(large_items, key=lambda x: x.get("phase", "")):
        print(f"{item['phase']} | risk={item['risk']} | lines={item['line_count_actual']} | {item['path']} | {item['title']}")
    print(f"refactor_plan_json={json_out}")
    print(f"refactor_plan_md={md_out}")
    print("BYS360_QUALITY_10_10_P11_REFACTOR_PLAN_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
