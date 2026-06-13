# -*- coding: utf-8 -*-
"""
BYS360 Kurumsal Bilgilendirme Merkezi V3.0 Faz 7.3
Flat CSS/Jinja link düzeltmesi.

Amaç:
- app/templates/corporate_information_center/base.html içindeki bozuk/çiftlenmiş
  corporate_information_center CSS link satırlarını temizlemek.
- Tek ve geçerli Jinja url_for satırını bırakmak.
- Faz 7 içeriklerini geri almamak.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import shutil
import sys
from pathlib import Path

MARKER = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_3_FLAT_CSS_LINK_FIX"
CSS_FILE = "css/corporate_information_center_v3_0_phase7.css"
CLEAN_LINK = "<link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/corporate_information_center_v3_0_phase7.css') }}?v=2_15_23\">"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def backup_file(root: Path, path: Path) -> Path:
    stamp = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = root / "backups" / "corporate_information_center_phase7_3_css_link_fix" / stamp
    backup_dir.mkdir(parents=True, exist_ok=True)
    rel = path.relative_to(root)
    target = backup_dir / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)
    return target


def normalize_base_html(root: Path) -> dict:
    base = root / "app" / "templates" / "corporate_information_center" / "base.html"
    if not base.exists():
        raise FileNotFoundError(f"base.html bulunamadi: {base}")

    backup = backup_file(root, base)
    text = read_text(base)
    original = text

    # Hem eski phase4/phase5 linklerini hem de bozulmuş phase7 link satırlarını yakalar.
    # Sadece Kurumsal Bilgilendirme Merkezi özel CSS linkleri temizlenir; genel base CSS'lere dokunulmaz.
    lines = text.splitlines()
    new_lines: list[str] = []
    inserted_css = False
    removed_css_lines = 0

    for line in lines:
        lower = line.lower()
        is_cic_css_line = (
            "corporate_information_center_v3_0_phase" in line
            and ".css" in line
            and ("stylesheet" in lower or "url_for" in line)
        )
        if is_cic_css_line:
            removed_css_lines += 1
            if not inserted_css:
                new_lines.append(CLEAN_LINK)
                inserted_css = True
            continue
        new_lines.append(line)

    text = "\n".join(new_lines)
    if original.endswith("\n"):
        text += "\n"

    if not inserted_css:
        # CSS satırı hiç yoksa </head> öncesine ekle, yoksa dosya başına güvenli şekilde koy.
        if "</head>" in text:
            text = text.replace("</head>", f"    {CLEAN_LINK}\n</head>", 1)
        else:
            text = f"{CLEAN_LINK}\n" + text

    if MARKER not in text:
        # Jinja yorum işareti kullanıyoruz; kullanıcı ekranında görünmez.
        marker_line = "{# " + MARKER + " #}"
        if text.startswith("{% extends"):
            first_newline = text.find("\n")
            if first_newline != -1:
                text = text[: first_newline + 1] + marker_line + "\n" + text[first_newline + 1 :]
            else:
                text = text + "\n" + marker_line + "\n"
        else:
            text = marker_line + "\n" + text

    # En çok görülen bozuk kırıntıları temizle.
    broken_fragments = [
        "\">') }}?v=2_15_18\"",
        "\">') }}?v=2_15_18",
        "') }}?v=2_15_18\"",
        "') }}?v=2_15_18",
        "\">')",
    ]
    for frag in broken_fragments:
        text = text.replace(frag, "\">")

    # Jinja parse kontrolü: syntax hatası varsa burada yakalanır.
    try:
        from jinja2 import Environment

        Environment().parse(text)
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(f"Jinja syntax kontrolu basarisiz: {exc}") from exc

    write_text(base, text)

    css_path = root / "app" / "static" / CSS_FILE
    if not css_path.exists():
        css_path.parent.mkdir(parents=True, exist_ok=True)
        write_text(css_path, "/* BYS360 Kurumsal Bilgilendirme Merkezi Faz 7 CSS dosyasi */\n")

    return {
        "base": str(base),
        "backup": str(backup),
        "removed_css_lines": removed_css_lines,
        "css": str(css_path),
    }


def gate(root: Path) -> None:
    base = root / "app" / "templates" / "corporate_information_center" / "base.html"
    text = read_text(base)

    required = [
        MARKER,
        "corporate_information_center_v3_0_phase7.css",
        "url_for('static', filename='css/corporate_information_center_v3_0_phase7.css')",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        for item in missing:
            print(f"HATA: base.html icinde eksik ifade: {item}")
        raise SystemExit(2)

    forbidden = [
        "expected token",
        "got 'static'",
        "?v=2_15_21\">') }}?v=2_15_18",
        "phase7.css') }}?v=2_15_21\">')",
        "\">') }}?v=2_15_18",
    ]
    bad = [item for item in forbidden if item in text]
    if bad:
        for item in bad:
            print(f"HATA: base.html icinde bozuk ifade kaldi: {item}")
        raise SystemExit(3)

    if text.count("corporate_information_center_v3_0_phase7.css") != 1:
        print("HATA: phase7 CSS linki tekil degil. Sayim=", text.count("corporate_information_center_v3_0_phase7.css"))
        raise SystemExit(4)

    try:
        from jinja2 import Environment

        Environment().parse(text)
    except Exception as exc:
        print(f"HATA: Jinja syntax kontrolu basarisiz: {exc}")
        raise SystemExit(5)

    print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_3_FLAT_CSS_LINK_FIX_GATE_OK")
    print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_3_FLAT_CSS_LINK_FIX_FINAL_OK")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-ProjectRoot", default="C:\\bys360\\project")
    parser.add_argument("-Mode", default="all")
    args = parser.parse_args(argv)

    root = Path(args.ProjectRoot).resolve()
    print("BYS360 Kurumsal Bilgilendirme Merkezi Faz 7.3 flat CSS link fix uygulanıyor...")
    print(f"ProjectRoot={root}")

    result = normalize_base_html(root)
    print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_3_FLAT_CSS_LINK_FIX_APPLY_OK")
    print("Guncellenen dosyalar:")
    print(" - app\\templates\\corporate_information_center\\base.html")
    print("Yedek:", result["backup"])
    gate(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
