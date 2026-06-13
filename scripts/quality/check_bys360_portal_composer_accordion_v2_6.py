from __future__ import annotations

import sys
from pathlib import Path

MARKER = "BYS360_PORTAL_COMPOSER_ACCORDION_V2_6"

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)

def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    composer = root / "app" / "templates" / "portal" / "_composer.html"
    css = root / "app" / "static" / "css" / "bys360_portal.css"
    js = root / "app" / "static" / "js" / "bys360_portal.js"
    require(composer.exists(), "_composer.html bulunamadı")
    require(css.exists(), "bys360_portal.css bulunamadı")
    require(js.exists(), "bys360_portal.js bulunamadı")
    ct, cs, jt = read_text(composer), read_text(css), read_text(js)
    require(MARKER in ct, "Composer akordeon marker bulunamadı")
    require("<details" in ct and "<summary" in ct, "Akordeon details/summary yapısı bulunamadı")
    require("portal-composer-summary" in ct, "Kompakt paylaşım başlığı bulunamadı")
    require("portal-composer-form" in ct, "Paylaşım formu bulunamadı")
    require('enctype="multipart/form-data"' in ct, "Fotoğraf yükleme için multipart form eksik")
    require('name="portal_images"' in ct, "Fotoğraf yükleme alanı eksik")
    require('name="video_url"' in ct, "Video bağlantısı alanı eksik")
    require(MARKER in cs, "CSS akordeon marker bulunamadı")
    require("portal-composer-accordion" in cs, "CSS akordeon sınıfı bulunamadı")
    require(MARKER in jt, "JS akordeon marker bulunamadı")
    require("data-portal-composer-details" in jt, "JS details kontrolü bulunamadı")
    print("BYS360_PORTAL_COMPOSER_ACCORDION_V2_6_GATE_OK")
    print("BYS360_PORTAL_COMPOSER_ACCORDION_V2_6_QUALITY_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
