from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

VERSION = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE5_CONTROL_PANEL"


def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1254", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def backup(path: Path) -> None:
    if not path.exists():
        return
    bak = path.with_suffix(path.suffix + ".phase5_control_panel.bak")
    if not bak.exists():
        shutil.copy2(path, bak)


def remove_service_block(text: str) -> str:
    pattern = r"\n?#\s*" + re.escape(VERSION) + r"_BEGIN.*?#\s*" + re.escape(VERSION) + r"_END\n?"
    return re.sub(pattern, "\n", text, flags=re.DOTALL)


def overlay_payload_root(project_root: Path) -> Path:
    return project_root / "overlay_payload"


def patch_service(root: Path) -> None:
    path = root / "app" / "services" / "corporate_information_center.py"
    block_path = overlay_payload_root(root) / "service_blocks" / "phase5_service_block.py.txt"
    if not path.exists():
        raise FileNotFoundError(f"Kurumsal bilgilendirme service dosyası bulunamadı: {path}")
    if not block_path.exists():
        raise FileNotFoundError(f"Faz 5 service bloğu bulunamadı: {block_path}")
    text = read_text(path)
    if "def send_task(" not in text or "def context(" not in text:
        raise RuntimeError("Beklenen send_task/context fonksiyonları bulunamadı; dosya yapısı kontrol edilmeli.")
    backup(path)
    block = read_text(block_path).strip()
    text = remove_service_block(text).rstrip() + "\n\n" + block + "\n"
    write_text(path, text)


def patch_routes(root: Path) -> None:
    path = root / "app" / "communication" / "corporate_information_center_routes.py"
    if not path.exists():
        return
    text = read_text(path)
    backup(path)
    if VERSION not in text:
        marker = "from __future__ import annotations\n"
        if marker in text:
            text = text.replace(marker, marker + f"# {VERSION}\n", 1)
        else:
            text = f"# {VERSION}\n" + text
    write_text(path, text)


def copy_payload_file(src: Path, dst: Path) -> None:
    if not src.exists():
        raise FileNotFoundError(f"Payload dosyası bulunamadı: {src}")
    backup(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def patch_templates(root: Path) -> None:
    payload = overlay_payload_root(root) / "app" / "templates" / "corporate_information_center"
    target = root / "app" / "templates" / "corporate_information_center"
    if not payload.exists():
        raise FileNotFoundError(f"Faz 5 template payload bulunamadı: {payload}")
    for name in ["base.html", "overview.html", "tasks.html", "recipients.html", "templates.html", "test.html", "logs.html", "system.html"]:
        copy_payload_file(payload / name, target / name)
    copy_payload_file(
        overlay_payload_root(root) / "app" / "static" / "css" / "corporate_information_center_v3_0_phase5.css",
        root / "app" / "static" / "css" / "corporate_information_center_v3_0_phase5.css",
    )


def run_compile(root: Path) -> None:
    py = root / ".venv" / "Scripts" / "python.exe"
    python = str(py) if py.exists() else sys.executable
    files = [root / "app" / "services" / "corporate_information_center.py", root / "app" / "communication" / "corporate_information_center_routes.py"]
    res = subprocess.run([python, "-m", "py_compile", *[str(f) for f in files if f.exists()]], cwd=str(root), text=True, capture_output=True)
    if res.returncode != 0:
        raise RuntimeError((res.stdout or "") + (res.stderr or ""))


def gate(root: Path) -> list[str]:
    checks: list[str] = []
    required = {
        root / "app/services/corporate_information_center.py": [VERSION, "def _cic_phase5_mail_health", "def _cic_phase5_readiness", "phase5.audit", "def context("],
        root / "app/templates/corporate_information_center/base.html": [VERSION, "corporate_information_center_v3_0_phase5.css", "Planla, denetle, güvenle gönder"],
        root / "app/templates/corporate_information_center/overview.html": [VERSION, "Yönetici Kontrol Paneli", "Görev Bazlı Gönderim Ön İzleme"],
        root / "app/templates/corporate_information_center/tasks.html": [VERSION, "Görev Yönetimi ve Çalıştırma Kontrolü", "data-confirm-real"],
        root / "app/templates/corporate_information_center/recipients.html": [VERSION, "Canlı Alıcı Özeti", "missingMailCount"],
        root / "app/templates/corporate_information_center/templates.html": [VERSION, "İçerik Kontrolü", "data-template-quality"],
        root / "app/templates/corporate_information_center/test.html": [VERSION, "Test ve Gönderim Merkezi", "realSendWarning"],
        root / "app/templates/corporate_information_center/logs.html": [VERSION, "Gönderim Geçmişi", "logType"],
        root / "app/templates/corporate_information_center/system.html": [VERSION, "Sistem Sağlığı ve Denetim", "Denetim İzi"],
        root / "app/static/css/corporate_information_center_v3_0_phase5.css": [VERSION, "cic-readiness-ring", "cic-phase5-checklist"],
    }
    for path, needles in required.items():
        if not path.exists():
            checks.append(f"Eksik dosya: {path}")
            continue
        text = read_text(path)
        for needle in needles:
            if needle not in text:
                checks.append(f"{path} içinde eksik ifade: {needle}")
    try:
        run_compile(root)
    except Exception as exc:
        checks.append(str(exc))
    return checks


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    print("BYS360 Kurumsal Bilgilendirme Merkezi Faz 5 uygulanıyor...")
    print(f"ProjectRoot={root}")
    patch_service(root)
    patch_routes(root)
    patch_templates(root)
    errors = gate(root)
    if errors:
        print(f"{VERSION}_GATE_FAIL")
        for err in errors:
            print("HATA:", err)
        return 2
    print(f"{VERSION}_APPLY_OK")
    print(f"{VERSION}_GATE_OK")
    print(f"{VERSION}_FINAL_OK")
    print("Güncellenen dosyalar:")
    for rel in [
        "app/services/corporate_information_center.py",
        "app/communication/corporate_information_center_routes.py",
        "app/templates/corporate_information_center/base.html",
        "app/templates/corporate_information_center/overview.html",
        "app/templates/corporate_information_center/tasks.html",
        "app/templates/corporate_information_center/recipients.html",
        "app/templates/corporate_information_center/templates.html",
        "app/templates/corporate_information_center/test.html",
        "app/templates/corporate_information_center/logs.html",
        "app/templates/corporate_information_center/system.html",
        "app/static/css/corporate_information_center_v3_0_phase5.css",
    ]:
        print(" -", rel)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
