#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# BYS360 Mobile V2.8.80 Portal + Home patcher.
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import shutil
from pathlib import Path

MARKER_HOME = "BYS360_MOBILE_PORTAL_HOME_ENTRY_V2_8_80"
MARKER_DRAWER = "BYS360_MOBILE_PORTAL_DRAWER_TILE_V2_8_80"
MARKER_ROUTE = "BYS360_MOBILE_PORTAL_ROUTE_V2_8_80"

PORTAL_DART = r'''// BYS360 Mobile V2.8.80 Portal entegrasyonu
// Bu dosya overlay tarafindan uretilmistir. Manuel silmeyin.

import 'package:flutter/material.dart';

class Bys360PortalRoutes {
  static const String home = '/portal';
  static const String feed = '/portal/feed';
  static const String people = '/portal/people';
  static const String posts = '/portal/posts';
  static const String profileMe = '/portal/profile/me';
  static const String support = '/support';
  static const String assistant = '/assistant';
}

const Color _bys360Red = Color(0xFF8B0000);
const Color _bys360SoftBg = Color(0xFFF7F3F2);
const Color _bys360Border = Color(0xFFE8DCDC);

class Bys360PortalHomeEntryCard extends StatelessWidget {
  const Bys360PortalHomeEntryCard({super.key});

  @override
  Widget build(BuildContext context) {
    // BYS360_MOBILE_PORTAL_HOME_ENTRY_V2_8_80
    return Card(
      elevation: 0,
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(22),
        side: const BorderSide(color: _bys360Border),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(22),
        onTap: () => Navigator.of(context).push(
          MaterialPageRoute<void>(
            builder: (_) => const Bys360PortalHomeScreen(),
          ),
        ),
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(22),
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0xFFFFFFFF), Color(0xFFFFF8F8)],
            ),
          ),
          padding: const EdgeInsets.all(18),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 52,
                height: 52,
                decoration: BoxDecoration(
                  color: _bys360Red.withOpacity(0.10),
                  borderRadius: BorderRadius.circular(18),
                ),
                child: const Icon(Icons.public, color: _bys360Red, size: 28),
              ),
              const SizedBox(width: 14),
              const Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'BYS360 Portal',
                      style: TextStyle(
                        fontSize: 17,
                        fontWeight: FontWeight.w800,
                        color: Color(0xFF2B2020),
                      ),
                    ),
                    SizedBox(height: 6),
                    Text(
                      'Kurumsal paylaşımlar, personel alanı, duyurular ve hızlı yönlendirmeler.',
                      style: TextStyle(
                        fontSize: 13.5,
                        height: 1.35,
                        color: Color(0xFF6D5D5D),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              const Icon(Icons.chevron_right, color: _bys360Red),
            ],
          ),
        ),
      ),
    );
  }
}

class Bys360PortalDrawerTile extends StatelessWidget {
  const Bys360PortalDrawerTile({super.key});

  @override
  Widget build(BuildContext context) {
    // BYS360_MOBILE_PORTAL_DRAWER_TILE_V2_8_80
    return ListTile(
      leading: const Icon(Icons.public, color: _bys360Red),
      title: const Text(
        'Portal',
        style: TextStyle(fontWeight: FontWeight.w700),
      ),
      subtitle: const Text('Kurumsal portal ana alanı'),
      onTap: () {
        final navigator = Navigator.of(context);
        if (navigator.canPop()) {
          navigator.pop();
        }
        navigator.push(
          MaterialPageRoute<void>(
            builder: (_) => const Bys360PortalHomeScreen(),
          ),
        );
      },
    );
  }
}

class Bys360PortalHomeScreen extends StatelessWidget {
  const Bys360PortalHomeScreen({super.key});

  void _openRoute(BuildContext context, String route, String title) {
    try {
      Navigator.of(context).pushNamed(route);
    } catch (_) {
      showDialog<void>(
        context: context,
        builder: (dialogContext) => AlertDialog(
          title: Text(title),
          content: const Text(
            'Bu portal alanı APK menüsüne eklendi. İlgili ekran rotası projede farklı adla tanımlıysa, portal bağlantısı o rota adına göre eşleştirilmelidir.',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(dialogContext).pop(),
              child: const Text('Tamam'),
            ),
          ],
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _bys360SoftBg,
      appBar: AppBar(
        backgroundColor: _bys360Red,
        foregroundColor: Colors.white,
        elevation: 0,
        title: const Text('BYS360 Portal'),
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 28),
          children: [
            _PortalHeaderCard(),
            const SizedBox(height: 14),
            const _PortalSectionTitle(
              title: 'Portal işlemleri',
              subtitle: 'Kurum içi paylaşım ve yönlendirme alanları',
            ),
            const SizedBox(height: 10),
            _PortalActionCard(
              icon: Icons.campaign_outlined,
              title: 'Duyurular ve Paylaşımlar',
              description: 'Portal akışındaki kurumsal duyuru ve paylaşımları görüntüleyin.',
              onTap: () => _openRoute(context, Bys360PortalRoutes.posts, 'Duyurular ve Paylaşımlar'),
            ),
            _PortalActionCard(
              icon: Icons.groups_2_outlined,
              title: 'Personel Portalı',
              description: 'Personel rehberi, birim görünümü ve profil bağlantılarına hızlı erişim.',
              onTap: () => _openRoute(context, Bys360PortalRoutes.people, 'Personel Portalı'),
            ),
            _PortalActionCard(
              icon: Icons.person_outline,
              title: 'Profilim',
              description: 'Kendi portal profilinizi ve görünür bilgilerinizi kontrol edin.',
              onTap: () => _openRoute(context, Bys360PortalRoutes.profileMe, 'Profilim'),
            ),
            _PortalActionCard(
              icon: Icons.support_agent_outlined,
              title: 'Destek Taleplerim',
              description: 'Portal veya uygulama kullanımıyla ilgili destek kayıtlarına gidin.',
              onTap: () => _openRoute(context, Bys360PortalRoutes.support, 'Destek Taleplerim'),
            ),
            _PortalActionCard(
              icon: Icons.smart_toy_outlined,
              title: 'BYS360 Asistanı',
              description: 'Portal ve BYS360 içinde doğru ekrana yönlendirme desteği alın.',
              onTap: () => _openRoute(context, Bys360PortalRoutes.assistant, 'BYS360 Asistanı'),
            ),
            const SizedBox(height: 14),
            _PortalInfoNote(),
          ],
        ),
      ),
    );
  }
}

class _PortalHeaderCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        border: Border.all(color: _bys360Border),
        boxShadow: [
          BoxShadow(
            blurRadius: 24,
            offset: const Offset(0, 10),
            color: Colors.black.withOpacity(0.05),
          ),
        ],
      ),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.public, color: _bys360Red, size: 30),
              SizedBox(width: 10),
              Expanded(
                child: Text(
                  'Kurumsal Portal',
                  style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w900,
                    color: Color(0xFF2B2020),
                  ),
                ),
              ),
            ],
          ),
          SizedBox(height: 10),
          Text(
            'BYS360 portalı; kurumsal duyuru, paylaşım, profil ve personel yönlendirmelerini mobil uygulama içinde tek merkezde toplar.',
            style: TextStyle(
              fontSize: 14.5,
              height: 1.45,
              color: Color(0xFF5E5252),
            ),
          ),
        ],
      ),
    );
  }
}

class _PortalSectionTitle extends StatelessWidget {
  const _PortalSectionTitle({required this.title, required this.subtitle});

  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w900,
            color: Color(0xFF2B2020),
          ),
        ),
        const SizedBox(height: 4),
        Text(
          subtitle,
          style: const TextStyle(fontSize: 13.5, color: Color(0xFF7A6B6B)),
        ),
      ],
    );
  }
}

class _PortalActionCard extends StatelessWidget {
  const _PortalActionCard({
    required this.icon,
    required this.title,
    required this.description,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String description;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      margin: const EdgeInsets.only(bottom: 10),
      color: Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
        side: const BorderSide(color: _bys360Border),
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
        leading: Container(
          width: 46,
          height: 46,
          decoration: BoxDecoration(
            color: _bys360Red.withOpacity(0.08),
            borderRadius: BorderRadius.circular(16),
          ),
          child: Icon(icon, color: _bys360Red),
        ),
        title: Text(
          title,
          style: const TextStyle(
            fontSize: 15.5,
            fontWeight: FontWeight.w800,
            color: Color(0xFF2B2020),
          ),
        ),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 5),
          child: Text(
            description,
            style: const TextStyle(height: 1.35, color: Color(0xFF6D5D5D)),
          ),
        ),
        trailing: const Icon(Icons.chevron_right, color: _bys360Red),
        onTap: onTap,
      ),
    );
  }
}

class _PortalInfoNote extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFFFFBF3),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFF0DFBE)),
      ),
      child: const Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(Icons.info_outline, color: Color(0xFF9A6A00), size: 22),
          SizedBox(width: 10),
          Expanded(
            child: Text(
              'Portal ekranı yetki sınırlarına bağlı çalışmalıdır. Hassas içerik ve kişi detayları yalnızca kullanıcının mevcut BYS360 yetkisi kadar gösterilmelidir.',
              style: TextStyle(
                fontSize: 13.5,
                height: 1.35,
                color: Color(0xFF6A4B12),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
'''


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def find_mobile_root(project_root: Path) -> Path:
    candidates = [
        project_root / "mobile_flutter" / "bys360_mobile_native",
        project_root / "mobile_flutter" / "bys360_mobile",
        project_root / "bys360_mobile_native",
        project_root,
    ]
    for c in candidates:
        if (c / "pubspec.yaml").exists() and (c / "lib").exists():
            return c.resolve()
    for pubspec in project_root.rglob("pubspec.yaml"):
        if (pubspec.parent / "lib").exists():
            return pubspec.parent.resolve()
    raise SystemExit("Flutter mobil proje kok dizini bulunamadi. Beklenen: mobile_flutter/bys360_mobile_native")


def get_package_name(mobile_root: Path) -> str:
    pubspec = read_text(mobile_root / "pubspec.yaml")
    m = re.search(r"^\s*name\s*:\s*([A-Za-z0-9_]+)\s*$", pubspec, flags=re.M)
    return m.group(1) if m else "bys360_mobile_native"


def backup_file(path: Path, backup_root: Path, mobile_root: Path) -> None:
    try:
        dest = backup_root / path.resolve().relative_to(mobile_root.resolve())
    except Exception:
        dest = backup_root / path.name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)


def add_import(text: str, import_line: str) -> str:
    if import_line.strip() in text:
        return text
    lines = text.splitlines()
    last_import = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("import "):
            last_import = i
    if last_import >= 0:
        lines.insert(last_import + 1, import_line.rstrip())
        return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    return import_line + "\n" + text


def insert_after_children(text: str, snippet: str, marker: str) -> str | None:
    if marker in text:
        return text
    m = re.search(r"children\s*:\s*\[", text)
    if not m:
        return None
    insert_pos = m.end()
    return text[:insert_pos] + "\n" + snippet + text[insert_pos:]


def insert_after_scoped_children(text: str, snippet: str, marker: str, scope_keyword: str) -> str | None:
    if marker in text:
        return text
    scope_pos = text.find(scope_keyword)
    if scope_pos < 0:
        return None
    scoped = text[scope_pos:]
    m = re.search(r"children\s*:\s*\[", scoped)
    if not m:
        return None
    insert_pos = scope_pos + m.end()
    return text[:insert_pos] + "\n" + snippet + text[insert_pos:]


def patch_home_files(mobile_root: Path, lib: Path, import_line: str, backup_root: Path) -> list[str]:
    files = [p for p in lib.rglob("*.dart") if p.name != "bys360_mobile_portal_v2_8_80.dart"]
    scored = []
    for p in files:
        name = p.name.lower()
        text = read_text(p)
        score = 0
        if "home" in name or "ana" in name:
            score += 8
        if "dashboard" in name:
            score += 7
        if name == "main.dart":
            score += 2
        if "Ana Sayfa" in text or "Dashboard" in text or "Ana sayfa" in text:
            score += 4
        if "Widget build" in text and "children" in text:
            score += 2
        if MARKER_HOME in text or "Bys360PortalHomeEntryCard" in text:
            score = -100
        if score > 0:
            scored.append((score, p))
    scored.sort(key=lambda x: (-x[0], len(str(x[1]))))
    snippet = f'''
            const Bys360PortalHomeEntryCard(), // {MARKER_HOME}
            const SizedBox(height: 12),
'''
    patched = []
    for _, p in scored[:3]:
        text = read_text(p)
        new = insert_after_scoped_children(text, snippet, MARKER_HOME, "body:") or insert_after_children(text, snippet, MARKER_HOME)
        if new and new != text:
            new = add_import(new, import_line)
            backup_file(p, backup_root, mobile_root)
            write_text(p, new)
            patched.append(str(p))
            break
    return patched


def patch_drawer_files(mobile_root: Path, lib: Path, import_line: str, backup_root: Path) -> list[str]:
    candidates = []
    for p in lib.rglob("*.dart"):
        if p.name == "bys360_mobile_portal_v2_8_80.dart":
            continue
        text = read_text(p)
        low_name = p.name.lower()
        score = 0
        if "drawer" in low_name or "menu" in low_name or "shell" in low_name or "navigation" in low_name:
            score += 5
        if "Drawer(" in text:
            score += 8
        if "ListTile(" in text:
            score += 3
        if "Ana Sayfa" in text or "Dashboard" in text or "Destek" in text:
            score += 2
        if MARKER_DRAWER in text or "Bys360PortalDrawerTile" in text:
            score = -100
        if score >= 8:
            candidates.append((score, p))
    candidates.sort(key=lambda x: (-x[0], len(str(x[1]))))
    snippet = f'''
            const Bys360PortalDrawerTile(), // {MARKER_DRAWER}
'''
    patched = []
    for _, p in candidates[:5]:
        text = read_text(p)
        new = insert_after_scoped_children(text, snippet, MARKER_DRAWER, "Drawer(") or insert_after_children(text, snippet, MARKER_DRAWER)
        if new and new != text:
            new = add_import(new, import_line)
            backup_file(p, backup_root, mobile_root)
            write_text(p, new)
            patched.append(str(p))
            break
    return patched


def patch_routes(mobile_root: Path, import_line: str, backup_root: Path) -> list[str]:
    main = mobile_root / "lib" / "main.dart"
    if not main.exists():
        return []
    text = read_text(main)
    if MARKER_ROUTE in text or "Bys360PortalRoutes.home" in text:
        return []
    m = re.search(r"routes\s*:\s*\{", text)
    if not m:
        return []
    snippet = f"\n          Bys360PortalRoutes.home: (context) => const Bys360PortalHomeScreen(), // {MARKER_ROUTE}\n"
    new = text[:m.end()] + snippet + text[m.end():]
    new = add_import(new, import_line)
    backup_file(main, backup_root, mobile_root)
    write_text(main, new)
    return [str(main)]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    args = ap.parse_args()
    project_root = Path(args.project_root).resolve()
    mobile_root = find_mobile_root(project_root)
    lib = mobile_root / "lib"
    package_name = get_package_name(mobile_root)
    import_line = f"import 'package:{package_name}/bys360_mobile_portal_v2_8_80.dart';"

    ts = _dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = mobile_root / ".backup" / f"mobile_v2_8_80_portal_home_{ts}"
    backup_root.mkdir(parents=True, exist_ok=True)

    portal_file = lib / "bys360_mobile_portal_v2_8_80.dart"
    if portal_file.exists():
        backup_file(portal_file, backup_root, mobile_root)
    write_text(portal_file, PORTAL_DART)

    home_patched = patch_home_files(mobile_root, lib, import_line, backup_root)
    drawer_patched = patch_drawer_files(mobile_root, lib, import_line, backup_root)
    route_patched = patch_routes(mobile_root, import_line, backup_root)

    report = {
        "version": "BYS360_MOBILE_V2_8_80_PORTAL_HOME_APK",
        "mobile_root": str(mobile_root),
        "package_name": package_name,
        "portal_file": str(portal_file),
        "route_patched": route_patched,
        "home_patched": home_patched,
        "drawer_patched": drawer_patched,
        "backup_root": str(backup_root),
        "notes": [
            "Ana sayfa karti eklendi: home_patched bos degilse APK ana sayfada Portal karti gorunur.",
            "Drawer tile eklendi: drawer_patched bos degilse sol menude Portal gorunur.",
            "Route map bulunduysa /portal named route eklendi.",
            "Proje farkli router kullaniyorsa portal ekrani MaterialPageRoute ile drawer/home kartindan yine acilir.",
        ],
    }
    report_path = mobile_root / "mobile_portal_v2_8_80_patch_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if not home_patched:
        raise SystemExit("Ana sayfa/home/dashboard dosyasi otomatik patch edilemedi. Portal dosyasi olustu ancak ana sayfa karti icin manuel yerlestirme gerekir.")
    if not (drawer_patched or route_patched):
        raise SystemExit("Portal menu veya route otomatik patch edilemedi. Portal dosyasi olustu ancak APK navigasyon baglantisi icin manuel yerlestirme gerekir.")


if __name__ == "__main__":
    main()
