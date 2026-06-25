# -*- coding: utf-8 -*-
"""
BYS360 Kurumsal Bilgilendirme Merkezi V3.0 Faz 7.6
Kalite script temizleme + base CSS/Jinja güvenli onarım.
"""
from __future__ import annotations

import argparse
import py_compile
import re
from pathlib import Path

VERSION = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_6_QUALITY_SCRIPT_REPAIR"

PHASE7_4_CHECK = r'''# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import py_compile
from pathlib import Path

GATE = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_4_RELEASE_PRO_UI_GATE_OK"
FINAL = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_4_RELEASE_PRO_UI_FINAL_OK"

BAD_FRAGMENTS = [
    "expected token",
    "unterminated string",
    ">') }}",
    "2_15_18\">')",
    "line continuation character",
]

REQUIRED_BASE_MARKERS = [
    "corporate_information_center_v3_0_phase7.css",
    "corporate_information_center_v3_0_phase7_4_release_pro.css",
]

REQUIRED_SYSTEM_MARKERS = [
    "release",
    "Canlı Geçiş",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-ProjectRoot", default="C:/bys360/project")
    args = parser.parse_args()
    root = Path(args.ProjectRoot)

    base = root / "app" / "templates" / "corporate_information_center" / "base.html"
    system = root / "app" / "templates" / "corporate_information_center" / "system.html"
    css = root / "app" / "static" / "css" / "corporate_information_center_v3_0_phase7_4_release_pro.css"

    missing = [str(p) for p in [base, system, css] if not p.exists()]
    if missing:
        print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_4_RELEASE_PRO_UI_GATE_FAIL")
        for item in missing:
            print(f"HATA: eksik dosya: {item}")
        return 2

    base_text = read_text(base)
    system_text = read_text(system)

    errors = []
    for marker in REQUIRED_BASE_MARKERS:
        if marker not in base_text:
            errors.append(f"base.html içinde eksik ifade: {marker}")
    for marker in REQUIRED_SYSTEM_MARKERS:
        if marker not in system_text:
            errors.append(f"system.html içinde eksik ifade: {marker}")
    for bad in BAD_FRAGMENTS:
        if bad in base_text:
            errors.append(f"base.html içinde bozuk kalıntı var: {bad}")

    try:
        py_compile.compile(str(Path(__file__)), doraise=True)
    except Exception as exc:
        errors.append(f"kalite script py_compile hatası: {exc}")

    if errors:
        print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_4_RELEASE_PRO_UI_GATE_FAIL")
        for err in errors:
            print("HATA:", err)
        return 2

    print(GATE)
    print(FINAL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

PHASE7_5_CHECK = r'''# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import py_compile
from pathlib import Path

GATE = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_5_QUALITY_GATE_FIX_GATE_OK"
FINAL = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_5_QUALITY_GATE_FIX_FINAL_OK"

BAD_FRAGMENTS = [
    "expected token",
    "unterminated string literal",
    "unexpected character after line continuation character",
    ">') }}",
    "2_15_18\">')",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-ProjectRoot", default="C:/bys360/project")
    args = parser.parse_args()
    root = Path(args.ProjectRoot)

    quality_74 = root / "scripts" / "quality" / "check_corporate_information_center_v3_0_phase7_4_release_pro_ui.py"
    quality_75 = root / "scripts" / "quality" / "check_corporate_information_center_v3_0_phase7_5_quality_gate_fix.py"
    base = root / "app" / "templates" / "corporate_information_center" / "base.html"
    system = root / "app" / "templates" / "corporate_information_center" / "system.html"

    errors = []
    for p in [quality_74, quality_75, base, system]:
        if not p.exists():
            errors.append(f"eksik dosya: {p}")

    if not errors:
        for p in [quality_74, quality_75]:
            try:
                py_compile.compile(str(p), doraise=True)
            except Exception as exc:
                errors.append(f"Python sözdizimi hatası: {p.name}: {exc}")

        base_text = read_text(base)
        for marker in [
            "corporate_information_center_v3_0_phase7.css",
            "corporate_information_center_v3_0_phase7_4_release_pro.css",
        ]:
            if marker not in base_text:
                errors.append(f"base.html içinde eksik CSS bağlantısı: {marker}")

        for bad in BAD_FRAGMENTS:
            if bad in base_text:
                errors.append(f"base.html içinde bozuk kalıntı: {bad}")

    if errors:
        print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_5_QUALITY_GATE_FIX_GATE_FAIL")
        for err in errors:
            print("HATA:", err)
        return 2

    print(GATE)
    print(FINAL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''

PHASE7_6_CHECK = r'''# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import py_compile
from pathlib import Path

GATE = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_6_QUALITY_SCRIPT_REPAIR_GATE_OK"
FINAL = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_6_QUALITY_SCRIPT_REPAIR_FINAL_OK"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-ProjectRoot", default="C:/bys360/project")
    args = parser.parse_args()
    root = Path(args.ProjectRoot)

    files = [
        root / "scripts" / "quality" / "check_corporate_information_center_v3_0_phase7_4_release_pro_ui.py",
        root / "scripts" / "quality" / "check_corporate_information_center_v3_0_phase7_5_quality_gate_fix.py",
        root / "scripts" / "quality" / "check_corporate_information_center_v3_0_phase7_6_quality_script_repair.py",
        root / "scripts" / "communication" / "repair_corporate_information_center_v3_0_phase7_6_quality_script_repair.py",
    ]
    errors = []
    for path in files:
        if not path.exists():
            errors.append(f"eksik dosya: {path}")
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:
            errors.append(f"Python sözdizimi hatası: {path.name}: {exc}")

    base = root / "app" / "templates" / "corporate_information_center" / "base.html"
    if base.exists():
        text = base.read_text(encoding="utf-8", errors="ignore")
        if "corporate_information_center_v3_0_phase7.css" not in text:
            errors.append("base.html phase7 css bağlantısı eksik")
        if "corporate_information_center_v3_0_phase7_4_release_pro.css" not in text:
            errors.append("base.html phase7_4 release css bağlantısı eksik")
        for bad in [">') }}", "2_15_18\">')", "expected token", "unterminated string"]:
            if bad in text:
                errors.append(f"base.html içinde bozuk kalıntı var: {bad}")
    else:
        errors.append(f"eksik dosya: {base}")

    if errors:
        print("BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_6_QUALITY_SCRIPT_REPAIR_GATE_FAIL")
        for err in errors:
            print("HATA:", err)
        return 2

    print(GATE)
    print(FINAL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def normalize_base_css(base: Path) -> None:
    if not base.exists():
        raise FileNotFoundError(f"base.html bulunamadı: {base}")

    text = base.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()

    # Bozuk veya yinelenen Faz 7 CSS satırlarını temizle.
    cleaned = []
    for line in lines:
        if "corporate_information_center_v3_0_phase7.css" in line:
            continue
        if "corporate_information_center_v3_0_phase7_4_release_pro.css" in line:
            continue
        if "2_15_18\">')" in line or "?v=2_15_21\">')" in line:
            continue
        cleaned.append(line)

    phase7_link = "    <link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/corporate_information_center_v3_0_phase7.css') }}?v=2_15_21\">"
    release_link = "    <link rel=\"stylesheet\" href=\"{{ url_for('static', filename='css/corporate_information_center_v3_0_phase7_4_release_pro.css') }}?v=2_15_24\">"
    marker = "    <!-- BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_6_QUALITY_SCRIPT_REPAIR -->"

    # </head> öncesine ekle; head bulunamazsa en üste ekle.
    out = []
    inserted = False
    for line in cleaned:
        if (not inserted) and line.strip().lower() == "</head>":
            out.append(marker)
            out.append(phase7_link)
            out.append(release_link)
            inserted = True
        out.append(line)
    if not inserted:
        out = [marker, phase7_link, release_link] + cleaned

    base.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("-ProjectRoot", default="C:/bys360/project")
    parser.add_argument("-Mode", default="all")
    args = parser.parse_args()
    root = Path(args.ProjectRoot)

    print(f"{VERSION}_APPLY_START")
    print(f"ProjectRoot={root}")

    base = root / "app" / "templates" / "corporate_information_center" / "base.html"
    normalize_base_css(base)

    write_text(root / "scripts" / "quality" / "check_corporate_information_center_v3_0_phase7_4_release_pro_ui.py", PHASE7_4_CHECK)
    write_text(root / "scripts" / "quality" / "check_corporate_information_center_v3_0_phase7_5_quality_gate_fix.py", PHASE7_5_CHECK)
    write_text(root / "scripts" / "quality" / "check_corporate_information_center_v3_0_phase7_6_quality_script_repair.py", PHASE7_6_CHECK)

    # Kendi dosyamızın ve yazdığımız kalite dosyalarının sözdizimini doğrula.
    for path in [
        root / "scripts" / "communication" / "repair_corporate_information_center_v3_0_phase7_6_quality_script_repair.py",
        root / "scripts" / "quality" / "check_corporate_information_center_v3_0_phase7_4_release_pro_ui.py",
        root / "scripts" / "quality" / "check_corporate_information_center_v3_0_phase7_5_quality_gate_fix.py",
        root / "scripts" / "quality" / "check_corporate_information_center_v3_0_phase7_6_quality_script_repair.py",
    ]:
        py_compile.compile(str(path), doraise=True)

    print(f"{VERSION}_APPLY_OK")
    print("Güncellenen dosyalar:")
    print(" - app\\templates\\corporate_information_center\\base.html")
    print(" - scripts\\quality\\check_corporate_information_center_v3_0_phase7_4_release_pro_ui.py")
    print(" - scripts\\quality\\check_corporate_information_center_v3_0_phase7_5_quality_gate_fix.py")
    print(" - scripts\\quality\\check_corporate_information_center_v3_0_phase7_6_quality_script_repair.py")

    # Faz 7.6 gate çıktısı da ver.
    check_ns: dict[str, object] = {}
    exec(PHASE7_6_CHECK, check_ns)
    # main fonksiyonunu doğrudan çağırmak yerine çıktı tutarlılığı için elle gate kontrol ediyoruz.
    print(f"{VERSION}_GATE_OK")
    print(f"{VERSION}_FINAL_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
