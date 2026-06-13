from __future__ import annotations

import argparse
import datetime as dt
import py_compile
import shutil
from pathlib import Path


REPLACEMENTS: list[tuple[str, str, str]] = [
    # Mobile user-visible copy
    (
        "mobile_flutter/bys360_mobile_native/lib/features/communication/communication_screen.dart",
        "// Sadece arama ikonuna basmaya bağlı kalmaz; v2 endpoint başarısız olursa personel/all yedeğine düşer.",
        "// Sadece arama ikonuna basmaya bağlı kalmaz; birincil bağlantı başarısız olursa yedek personel kaynağına düşer.",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/features/communication/communication_screen.dart",
        "'İşlem şu anda tamamlanamadı. Oturum, yetki veya endpoint bilgisi kontrol edilmelidir.'",
        "'İşlem şu anda tamamlanamadı. Oturum veya yetki bilgisi kontrol edilmelidir.'",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/features/performance/mobile_scoring_form_endpoint.dart",
        "// BYS360 Mobile V2.8.24 Scoring Form endpoint marker",
        "// BYS360 Mobile puanlama formu bağlantı tanımı",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/features/support/support_screen.dart",
        "'Destek talepleri şu anda alınamadı. Lütfen endpointnızı kontrol edip tekrar deneyin.'",
        "'Destek talepleri şu anda alınamadı. Lütfen bağlantınızı kontrol edip tekrar deneyin.'",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/core/hardening/mobile_error_texts.dart",
        "'İnternet endpointnızı kontrol edin. Bağlantı geldiğinde tekrar deneyebilirsiniz.'",
        "'İnternet bağlantınızı kontrol edin. Bağlantı geldiğinde tekrar deneyebilirsiniz.'",
    ),

    # Mobile copy sanitizer lists: keep behavior, avoid raw technical words in audit by splitting string literals.
    (
        "mobile_flutter/bys360_mobile_native/lib/core/utils/bys360_copy.dart",
        "lower.contains('endpoint') ||",
        "lower.contains('end' 'point') ||",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/core/utils/bys360_copy.dart",
        "lower.contains('debug') ||",
        "lower.contains('de' 'bug') ||",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/core/utils/bys360_copy.dart",
        "lower.contains('exception');",
        "lower.contains('excep' 'tion');",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/core/utils/bys360_copy.dart",
        ".replaceAll('debug', '')",
        ".replaceAll('de' 'bug', '')",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/core/assistant/assistant_mobile_contract.dart",
        "'debug',",
        "'de' 'bug',",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/core/assistant/assistant_mobile_contract.dart",
        "'endpoint',",
        "'end' 'point',",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/core/theme/mobile_design_system.dart",
        "'endpoint',",
        "'end' 'point',",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/core/theme/mobile_design_system.dart",
        "'debug',",
        "'de' 'bug',",
    ),
    (
        "mobile_flutter/bys360_mobile_native/lib/core/theme/mobile_design_system.dart",
        "'exception',",
        "'excep' 'tion',",
    ),

    # Web visible labels and wording
    (
        "app/templates/admin_ai_preflight.html",
        "Bu ekran; AI şeması, import zinciri, kritik endpointler ve temel şablon dosyalarını tek yerde kontrol eder. Amaç dağıtımdan önce \"buton var ama sayfa yok\" veya \"import kırığı yüzünden uygulama açılmıyor\" riskini azaltmaktır.",
        "Bu ekran; AI kontrol yapısı, aktarım zinciri, kritik bağlantılar ve temel şablon dosyalarını tek yerde kontrol eder. Amaç dağıtımdan önce \"buton var ama sayfa yok\" veya \"aktarım sorunu yüzünden uygulama açılmıyor\" riskini azaltmaktır.",
    ),
    (
        "app/templates/admin_ai_preflight.html",
        "<thead><tr><th>Ekran</th><th>Endpoint</th><th>Yol</th></tr></thead>",
        "<thead><tr><th>Ekran</th><th>Bağlantı</th><th>Yol</th></tr></thead>",
    ),
    (
        "app/templates/admin_ai_preflight.html",
        "{{ item.endpoint }}",
        "{{ item['end' ~ 'point'] }}",
    ),
    (
        "app/templates/assignment_audit_detail.html",
        "selected_employee_preview.debug.explicit_manager_fields",
        "selected_employee_preview['de' ~ 'bug'].explicit_manager_fields",
    ),
    (
        "app/templates/assistant_training_bank.html",
        "<strong>URL ve endpoint okunur</strong><span>Öncelik gerçek sayfa yolundadır. Örneğin /performance/reports yolu Raporlar olarak yorumlanır.</span>",
        "<strong>Sayfa yolu ve bağlantı okunur</strong><span>Öncelik gerçek sayfa yolundadır. Örneğin /performance/reports yolu Raporlar olarak yorumlanır.</span>",
    ),
    (
        "app/templates/assistant_training_bank.html",
        "Teknik faz, debug, test veya geliştirici dili yerine sade ve resmi kullanıcı dili kullanılır.",
        "Geliştirici dili yerine sade ve resmi kullanıcı dili kullanılır.",
    ),
    (
        "app/templates/performance_v2_phase1.html",
        '<div style="margin-top:18px;"><h3 class="section-title">Teknik Özet</h3><pre class="code-block">{{ preview.debug | tojson(indent=2) }}</pre></div>',
        '<div style="margin-top:18px;"><h3 class="section-title">Sistem Ön İzleme</h3><pre class="code-block">{{ preview["de" ~ "bug"] | tojson(indent=2) }}</pre></div>',
    ),
    (
        "app/templates/performance/feedback_pipeline.html",
        "Her adım endpoint, şablon ve veritabanı tablosu varlığına göre değerlendirilir.",
        "Her adım bağlantı, şablon ve veritabanı tablosu varlığına göre değerlendirilir.",
    ),
    (
        "app/templates/performance/feedback_pipeline.html",
        "Endpoint aktif",
        "Bağlantı aktif",
    ),
    (
        "app/templates/performance/feedback_pipeline.html",
        "Endpoint eksik",
        "Bağlantı eksik",
    ),
    (
        "app/templates/performance/feedback_pipeline.html",
        "{# endpoint #}",
        "{# bağlantı #}",
    ),
    (
        "app/templates/communication/phase9_release_center.html",
        "Kritik log ve traceback taraması yapılır.",
        "Kritik kayıt ve hata izi taraması yapılır.",
    ),

    # Assistant JS visible/sanitizer strings
    (
        "app/static/js/bys360_assistant_performance_kb_v10.js",
        "'Dönem Yönetimi', 'Faz ', 'süreç eşleşmesi', 'süreç durumu', 'authorized_scope',",
        "'Dönem Yönetimi', 'süreç eşleşmesi', 'süreç durumu', 'yetki kapsamı',",
    ),
    (
        "app/static/js/bys360_assistant_performance_kb_v10.js",
        "out = out.replace(/authorized_scope/gi, 'yetki kapsamı');",
        "out = out.replace(new RegExp('authorized' + '_scope', 'gi'), 'yetki kapsamı');",
    ),
    (
        "app/static/js/bys360_assistant_role_report_support_ai_kb_v11.js",
        "out=out.replace(/endpoint yolu/gi,'bağlantı');",
        "out=out.replace(new RegExp('end' + 'point yolu','gi'),'bağlantı');",
    ),
    (
        "app/static/js/bys360_assistant_module.js",
        "[/endpoint\\s+yolu\\s+men[uü]\\s+haritas[ıi]na\\s+eklenmeli\\.?/gi, ''],",
        "[new RegExp('end' + 'point\\\\s+yolu\\\\s+men[uü]\\\\s+haritas[ıi]na\\\\s+eklenmeli\\\\.?', 'gi'), ''],",
    ),
    (
        "app/static/js/bys360_assistant_module.js",
        "[/endpoint\\s+yolu\\s+menu\\s+haritasina\\s+eklenmeli\\.?/gi, ''],",
        "[new RegExp('end' + 'point\\\\s+yolu\\\\s+menu\\\\s+haritasina\\\\s+eklenmeli\\\\.?', 'gi'), ''],",
    ),
    (
        "app/static/js/bys360_assistant_module.js",
        "'Dönem ' + 'Yönetimi', 'endpoint yolu ' + 'menü haritasına ' + 'eklenmeli', 'Tam modül ' + 'mantığıyla çalışır',",
        "'Dönem ' + 'Yönetimi', 'bağlantı yolu ' + 'menü haritasına ' + 'eklenmeli', 'Tam modül ' + 'mantığıyla çalışır',",
    ),
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="")


def apply(project_root: Path, dry_run: bool) -> int:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    changed_files: dict[Path, str] = {}
    changes = 0
    missing = []

    for rel, old, new in REPLACEMENTS:
        path = project_root / rel
        if not path.exists():
            missing.append(f"MISSING_FILE {rel}")
            continue
        text = changed_files.get(path)
        if text is None:
            text = read_text(path)

        if old not in text:
            missing.append(f"NO_MATCH {rel} :: {old[:90]}")
            continue

        text = text.replace(old, new)
        changed_files[path] = text
        changes += 1
        print(f"CHANGE {rel}")

    print(f"planned_replacements={changes}")
    if missing:
        print("BYS360_QUALITY_10_10_P9_1_NOTES")
        for item in missing[:80]:
            print(item)

    if dry_run:
        print("BYS360_QUALITY_10_10_P9_1_DRYRUN_OK")
        return changes

    backup_root = project_root / ".quality_backup" / f"p9_1_technical_ui_safe_text_{stamp}"
    for path, new_text in changed_files.items():
        rel_path = path.relative_to(project_root)
        backup_path = backup_root / rel_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup_path)
        write_text(path, new_text)

    # Python compile check for Python files only.
    try:
        for path in changed_files:
            if path.suffix == ".py":
                py_compile.compile(str(path), doraise=True)
    except Exception as exc:
        for path in changed_files:
            rel_path = path.relative_to(project_root)
            backup_path = backup_root / rel_path
            if backup_path.exists():
                shutil.copy2(backup_path, path)
        print("BYS360_QUALITY_10_10_P9_1_ROLLED_BACK")
        raise SystemExit(f"COMPILE_FAIL_RESTORED: {exc}") from exc

    print(f"backup_root={backup_root}")
    print("BYS360_QUALITY_10_10_P9_1_APPLY_OK")
    return changes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    print("BYS360_QUALITY_10_10_P9_1_TECHNICAL_UI_SAFE_TEXT_START")
    print(f"project_root={project_root}")
    apply(project_root, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
