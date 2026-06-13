from __future__ import annotations

import argparse
from pathlib import Path

VERSION = "BYS360_GERI_BILDIRIM_KAMPANYA_FORMU_V2_13_2"

CHECKS = {
    "hazir_sablonlar": "data-preset=\"screen\"",
    "ekran_hatalari_sablonu": "BYS360 ekran hataları ve eksikler geri bildirim kampanyası",
    "mobil_sablonu": "BYS360 mobil / APK kullanım deneyimi geri bildirimi",
    "form_title": "name=\"title\"",
    "form_campaign_type": "name=\"campaign_type\"",
    "form_question_type": "name=\"question_type\"",
    "form_questions": "name=\"question_texts\"",
    "form_target_scope": "name=\"target_scope\"",
    "form_target_value": "name=\"target_value\"",
    "form_anonymous": "name=\"is_anonymous\"",
    "form_multiple": "name=\"allow_multiple_submissions\"",
    "form_comment": "name=\"allow_comment\"",
    "kurumsal_not": "Güvenli kullanım notu",
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=f"{VERSION} kontrol scripti")
    parser.add_argument("--project-root", default=".", help="BYS360 proje kökü")
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()

    template_path = project_root / "app" / "templates" / "feedback" / "campaign_form.html"
    route_path = project_root / "app" / "communication" / "feedback_routes.py"
    if not template_path.exists():
        raise FileNotFoundError(f"Şablon bulunamadı: {template_path}")
    if not route_path.exists():
        raise FileNotFoundError(f"Route dosyası bulunamadı: {route_path}")

    template = read_text(template_path)
    route_text = read_text(route_path)

    missing = [name for name, marker in CHECKS.items() if marker not in template]
    if missing:
        raise RuntimeError("Kampanya formu güncel değil. Eksik kontroller: " + ", ".join(missing))
    if "/feedback/admin/campaigns/new" not in route_text or "feedback_campaign_new" not in route_text:
        raise RuntimeError("Kampanya formu route bağlantısı bulunamadı.")

    print(f"{VERSION}_GATE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
