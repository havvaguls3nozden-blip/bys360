from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

VERSION = "BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_LIVE_RELEASE_USAGE"


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
    bak = path.with_suffix(path.suffix + ".phase7_live_release.bak")
    if not bak.exists():
        shutil.copy2(path, bak)


def insert_once(text: str, marker: str, needle: str, insert: str, after: bool = True) -> str:
    if marker in text:
        return text
    if needle not in text:
        return text + "\n" + insert + "\n"
    if after:
        return text.replace(needle, needle + "\n" + insert, 1)
    return text.replace(needle, insert + "\n" + needle, 1)


def payload_root(root: Path) -> Path:
    return root / "overlay_payload"


def patch_base(root: Path) -> None:
    path = root / "app" / "templates" / "corporate_information_center" / "base.html"
    if not path.exists():
        raise FileNotFoundError(f"base.html bulunamadı: {path}")
    text = read_text(path)
    backup(path)
    css_link = '<link rel="stylesheet" href="{{ url_for(\'static\', filename=\'css/corporate_information_center_v3_0_phase7.css\') }}?v=2_15_21">'
    text = insert_once(text, "corporate_information_center_v3_0_phase7.css", "corporate_information_center_v3_0_phase6.css", css_link, after=True)
    text = insert_once(text, VERSION, "{# BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE6_FINAL_UAT_LIVE_READY #}", "{# " + VERSION + " #}", after=True)
    text = insert_once(text, "sistem#release", '<a href="/dashboard/kurumsal-bilgilendirme/sistem#uat"><i class="fa-solid fa-clipboard-check"></i> Final UAT</a>', '<a href="/dashboard/kurumsal-bilgilendirme/sistem#release"><i class="fa-solid fa-rocket"></i> Canlı Geçiş</a>', after=True)
    text = insert_once(text, "<span>Release</span>", '<div class="cic-mini-stat"><span>UAT puanı</span><b>{{ stats.phase6_uat_score|default(0) }}</b></div>', '<div class="cic-mini-stat"><span>Release</span><b>Hazır</b></div>', after=True)
    write_text(path, text)


def patch_overview(root: Path) -> None:
    path = root / "app" / "templates" / "corporate_information_center" / "overview.html"
    text = read_text(path)
    backup(path)
    block = '''
  <!-- BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_LIVE_RELEASE_USAGE -->
  <section class="cic-card-v4 span-12 cic-phase7-release">
    <div class="cic-card-header">
      <div><h2>Canlı Geçiş ve Kullanım Hazırlığı</h2><p class="cic-muted-v4">Faz 7 ile modül, pilot gönderimden canlı kullanıma kadar kontrollü release akışına alınır.</p></div>
      <span class="cic-status-pill ok"><i class="fa-solid fa-lock"></i> Release kilidi aktif</span>
    </div>
    <div class="cic-phase7-release-grid">
      <div class="cic-phase7-release-card"><i class="fa-solid fa-vial-circle-check"></i><strong>Önce kuru çalışma</strong><span>Gerçek gönderimden önce test sonucu ve alıcı özeti incelenir.</span></div>
      <div class="cic-phase7-release-card"><i class="fa-solid fa-users-viewfinder"></i><strong>Pilot gönderim</strong><span>İlk canlı deneme küçük ve kontrollü pilot alıcı grubuyla yapılır.</span></div>
      <div class="cic-phase7-release-card"><i class="fa-solid fa-clipboard-list"></i><strong>Log kontrolü</strong><span>Başarılı, hatalı ve atlanan kayıtlar gönderim sonrası doğrulanır.</span></div>
      <div class="cic-phase7-release-card"><i class="fa-solid fa-rotate-left"></i><strong>Geri dönüş planı</strong><span>Beklenmeyen durumda template/CSS yedekleriyle hızlı geri dönüş yapılır.</span></div>
    </div>
  </section>
'''.replace('BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_LIVE_RELEASE_USAGE', VERSION)
    text = insert_once(text, VERSION, '<section class="cic-card-v4 span-12 cic-phase6-command">', block, after=False)
    write_text(path, text)


def patch_test(root: Path) -> None:
    path = root / "app" / "templates" / "corporate_information_center" / "test.html"
    text = read_text(path)
    backup(path)
    block = '''
  <!-- BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_LIVE_RELEASE_USAGE -->
  <section class="cic-card-v4 span-12 cic-phase7-release">
    <div class="cic-card-header"><div><h2>Canlı Gönderim Release Kilidi</h2><p class="cic-muted-v4">Kuru çalışma başarılı olmadan, pilot alıcı kontrolü yapılmadan ve log ekranı izlenmeden toplu gerçek gönderim başlatılmamalıdır.</p></div><span class="cic-status-pill warn"><i class="fa-solid fa-triangle-exclamation"></i> Pilot önce gelir</span></div>
    <div class="cic-phase7-warning"><strong>Uygulama standardı:</strong> İlk canlı denemede yalnızca pilot grup kullanılmalı; kurum geneline gönderim pilot logları temiz görüldükten sonra yapılmalıdır.</div>
  </section>
'''.replace('BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_LIVE_RELEASE_USAGE', VERSION)
    text = insert_once(text, VERSION, '<section class="cic-card-v4 span-12 cic-phase6-live-gate">', block, after=False)
    write_text(path, text)


def patch_system(root: Path) -> None:
    path = root / "app" / "templates" / "corporate_information_center" / "system.html"
    text = read_text(path)
    backup(path)
    block = '''
  <!-- BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_LIVE_RELEASE_USAGE -->
  <section id="release" class="cic-card-v4 span-12 cic-phase7-release">
    <div class="cic-card-header"><div><h2>Faz 7 Canlı Geçiş ve Kullanım Paketi</h2><p class="cic-muted-v4">Canlı geçiş; kuru çalışma, pilot gönderim, log doğrulama, kullanım kılavuzu ve geri dönüş planı ile kontrollü yürütülür.</p></div><span class="cic-status-pill ok"><i class="fa-solid fa-rocket"></i> Canlıya hazırlık paketi</span></div>
    <div class="cic-phase7-timeline">
      <article class="cic-phase7-step"><b>1</b><div><strong>Son local kontrol</strong><p>Faz 6 UAT ve Faz 7 release paneli localde doğrulanır.</p></div><em>Hazır</em></article>
      <article class="cic-phase7-step"><b>2</b><div><strong>Kuru çalışma</strong><p>Gerçek gönderim kapalıyken alıcı, şablon ve log sonucu test edilir.</p></div><em>Öncelikli</em></article>
      <article class="cic-phase7-step warn"><b>3</b><div><strong>Pilot canlı gönderim</strong><p>İlk gerçek mail yalnızca pilot alıcı grubuna gönderilir.</p></div><em>Pilot</em></article>
      <article class="cic-phase7-step"><b>4</b><div><strong>Log doğrulama</strong><p>Başarılı, hatalı ve atlanan kayıtlar log ekranında kontrol edilir.</p></div><em>Kontrol</em></article>
      <article class="cic-phase7-step"><b>5</b><div><strong>Geniş kullanım</strong><p>Pilot temizse görev kapsamı genişletilir ve kullanım kılavuzu paylaşılır.</p></div><em>Onaylı</em></article>
    </div>
    <div class="cic-phase7-doc-grid">
      <a class="cic-phase7-doc" href="#"><i class="fa-solid fa-book-open"></i><div><strong>Kullanım kılavuzu</strong><span>docs/BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_USAGE_GUIDE.md</span></div></a>
      <a class="cic-phase7-doc" href="#"><i class="fa-solid fa-list-check"></i><div><strong>Canlı geçiş kontrol listesi</strong><span>docs/BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_LIVE_RELEASE_CHECKLIST.md</span></div></a>
      <a class="cic-phase7-doc" href="#"><i class="fa-solid fa-rotate-left"></i><div><strong>Geri dönüş planı</strong><span>docs/BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_ROLLBACK_PLAN.md</span></div></a>
    </div>
  </section>
'''.replace('BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_LIVE_RELEASE_USAGE', VERSION)
    text = insert_once(text, VERSION, '<section id="uat" class="cic-card-v4 span-12 cic-phase6-uat-board">', block, after=False)
    write_text(path, text)


def patch_docs_and_css(root: Path) -> None:
    src_css = payload_root(root) / "app" / "static" / "css" / "corporate_information_center_v3_0_phase7.css"
    dst_css = root / "app" / "static" / "css" / "corporate_information_center_v3_0_phase7.css"
    backup(dst_css)
    dst_css.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_css, dst_css)


def run_compile(root: Path) -> None:
    py = root / ".venv" / "Scripts" / "python.exe"
    python = str(py) if py.exists() else sys.executable
    files = [root / "app" / "services" / "corporate_information_center.py", root / "app" / "communication" / "corporate_information_center_routes.py"]
    res = subprocess.run([python, "-m", "py_compile", *[str(f) for f in files if f.exists()]], cwd=str(root), text=True, capture_output=True)
    if res.returncode != 0:
        raise RuntimeError((res.stdout or "") + (res.stderr or ""))


def gate(root: Path) -> list[str]:
    required = {
        root / "app/templates/corporate_information_center/base.html": [VERSION, "corporate_information_center_v3_0_phase7.css", "Canlı Geçiş"],
        root / "app/templates/corporate_information_center/overview.html": [VERSION, "Canlı Geçiş ve Kullanım Hazırlığı", "Release kilidi aktif"],
        root / "app/templates/corporate_information_center/test.html": [VERSION, "Canlı Gönderim Release Kilidi", "Pilot önce gelir"],
        root / "app/templates/corporate_information_center/system.html": [VERSION, "Faz 7 Canlı Geçiş ve Kullanım Paketi", "Geri dönüş planı"],
        root / "app/static/css/corporate_information_center_v3_0_phase7.css": [VERSION, "cic-phase7-release", "cic-phase7-timeline"],
        root / "docs/BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_USAGE_GUIDE.md": [VERSION, "Canlı kullanım sırası"],
        root / "docs/BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_LIVE_RELEASE_CHECKLIST.md": [VERSION, "Canlı öncesi teknik kontrol"],
        root / "docs/BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_ROLLBACK_PLAN.md": [VERSION, "Geri dönüş adımları"],
    }
    errors: list[str] = []
    for path, needles in required.items():
        if not path.exists():
            errors.append(f"Eksik dosya: {path}")
            continue
        text = read_text(path)
        for needle in needles:
            if needle not in text:
                errors.append(f"{path} içinde eksik ifade: {needle}")
    try:
        run_compile(root)
    except Exception as exc:
        errors.append(str(exc))
    return errors


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root_pos", nargs="?", default=None)
    parser.add_argument("--project-root", "-ProjectRoot", dest="project_root", default=None)
    parser.add_argument("--mode", "-Mode", dest="mode", default="all")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.project_root or args.project_root_pos or ".").resolve()
    errors = gate(root)
    if errors:
        print(f"{VERSION}_GATE_FAIL")
        for err in errors:
            print("HATA:", err)
        return 2
    print(f"{VERSION}_GATE_OK")
    print(f"{VERSION}_FINAL_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
