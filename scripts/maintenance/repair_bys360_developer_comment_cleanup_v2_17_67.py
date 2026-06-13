from __future__ import annotations

import argparse
import ast
import json
import py_compile
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

VERSION = "V2.17.67"
TARGET_FILES = [
    "app/admin/ops_routes.py",
    "app/performance/admin_core_routes.py",
    "app/performance/task_routes.py",
    "app/services/mail_feedback.py",
]

# Bu kelimeler yalnızca yorum/docstring temizlik raporu için kullanılır.
# Kod davranışını belirleyen stringlerde otomatik geniş temizlik yapılmaz.
PERSONAL_MARKERS = [
    "Havva",
    "Miley",
    "kahve",
    "kafam",
    "ters ters",
    "yorgun",
    "gece 02",
    "saat 20",
    "saat 21",
    "15 Subat 2026",
    "22 Mart 2026",
    "insan gibi",
    "simdilik dokunmuyorum",
]

PATCHES: dict[str, list[tuple[str, str, str]]] = {
    "app/admin/ops_routes.py": [
        (
            "personal dated header docstring",
            '''"""Phase 47 admin operasyon route ailesi.\n\nHavva – 22 Mart 2026, saat 20:12.\nAdmin tarafinda kalan tek tuk agir isleri de buraya cektim. Her seyi tek bir\nroutes.py'de tutunca kafamda kaliyor sanmistim ama artik dosya bana ters ters\nbakiyordu. Yine de biraz kahve izi kalsin diye asiri steril yapmadim.\n"""''',
            '''"""Admin operasyon route ailesi.\n\nBu dosya admin toplu işlemleri, personel profil/aksiyonları ve\nhiyerarşi yardımcı rotalarını modüler yapı altında toplar.\n"""''',
        ),
        (
            "legacy note corporate wording",
            '''LEGACY_NOTE = (\n    "Phase 47 ile admin toplu islemler, personel profil/aksiyonlari ve bazi "\n    "hiyerarsi yardimci route'lari app.admin.ops_routes altina tasindi."\n)''',
            '''LEGACY_NOTE = (\n    "Admin toplu işlemleri, personel profil/aksiyonları ve hiyerarşi "\n    "yardımcı rotaları app.admin.ops_routes altında çalışır."\n)''',
        ),
    ],
    "app/performance/admin_core_routes.py": [
        (
            "personal dated header docstring",
            '''"""Performans yonetimi admin cekirdek route'lari.\n\nHavva – 22 Mart 2026, saat 21:05.\nKriter / donem / gorev uretimi blogu ana routes.py icinde cok fazla yer kapliyordu.\nBurayi ayirdim ama fazla steril etmedim; biraz yorgun gecelerin izi kalsin istedim.\n"""''',
            '''"""Performans yönetimi admin çekirdek rotaları.\n\nBu dosya değerlendirme kriterleri, dönem yönetimi ve görev üretimi\nakışlarını modüler yapı altında yönetir.\n"""''',
        ),
        (
            "personal inline comments before criteria route",
            '''# TODO: bulk period archive belki isteriz ama simdilik dokunmuyorum.\n# Havva – 15 Subat 2026, gece 02:50 – Miley klavyeye oturdu yine.\n''',
            '''# Dönem arşivleme ihtiyacı ayrıca değerlendirilecektir.\n''',
        ),
        (
            "personal inline comment after assignment generation",
            '''# Havva – 22 Mart 2026, saat 21:18 – kriter ve donem tarafi artik biraz daha nefes aliyor.''',
            '''# Kriter ve dönem yönetimi akışı modüler yapı altında sürdürülür.''',
        ),
    ],
    "app/performance/task_routes.py": [
        (
            "personal dated header docstring",
            '''"""Phase 45 modular performance task management route family.\n\nHavva – 15 Subat 2026, gece 02:50 – Miley klavyeye oturdu yine.\nBu tarafi daha once sadece route wrapper olarak ayirmistim. Simdi artik govde de burada.\n"""''',
            '''"""Performans görev yönetimi route ailesi.\n\nBu dosya performans görev yönetimi ekranlarının istek/yanıt akışını\nmodüler yapı altında yönetir.\n"""''',
        ),
        (
            "phase helper docstring corporate wording",
            '''"""Faz C: görev yönetimi yardımcıları service katmanına taşındı.\nBu route dosyası artık sadece istek/yanıt akışını yönetir.\n"""''',
            '''"""Görev yönetimi yardımcıları service katmanında çalışır.\nBu route dosyası yalnızca istek/yanıt akışını yönetir.\n"""''',
        ),
    ],
    "app/services/mail_feedback.py": [
        (
            "personal mail helper comment",
            '''# Havva – 22 Mart 2026, 23:48 – mail tarafini da biraz insan gibi toparladim; SMTP kapaliysa bari duzgun konussun.''',
            '''# Mail geri bildirim yardımcıları kurumsal bildirim akışı için kullanılır.''',
        ),
    ],
}


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def rel(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("\\", "/")


def ensure_reports(root: Path) -> Path:
    reports = root / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    return reports


def count_markers_in_text(text: str) -> dict[str, int]:
    return {marker: text.count(marker) for marker in PERSONAL_MARKERS if marker in text}


def audit_targets(root: Path) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    missing: list[str] = []
    total_marker_count = 0
    for rel_path in TARGET_FILES:
        path = root / rel_path
        if not path.exists():
            missing.append(rel_path)
            items.append({"file": rel_path, "exists": False, "markers": {}, "marker_count": 0})
            continue
        text = read_text(path)
        markers = count_markers_in_text(text)
        marker_count = sum(markers.values())
        total_marker_count += marker_count
        items.append({"file": rel_path, "exists": True, "markers": markers, "marker_count": marker_count})
    return {
        "target_count": len(TARGET_FILES),
        "missing_count": len(missing),
        "missing": missing,
        "target_personal_marker_count": total_marker_count,
        "items": items,
    }


def py_quality(paths: list[Path]) -> dict[str, Any]:
    ast_errors: list[dict[str, str]] = []
    compile_errors: list[dict[str, str]] = []
    for path in paths:
        if not path.exists() or path.suffix != ".py":
            continue
        try:
            ast.parse(read_text(path), filename=str(path))
        except Exception as exc:  # noqa: BLE001
            ast_errors.append({"file": str(path), "error": str(exc)})
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:  # noqa: BLE001
            compile_errors.append({"file": str(path), "error": str(exc)})
    return {
        "ast_error_count": len(ast_errors),
        "ast_errors": ast_errors,
        "py_compile_error_count": len(compile_errors),
        "py_compile_errors": compile_errors,
        "ok": not ast_errors and not compile_errors,
    }


def make_backup(path: Path, root: Path, backup_root: Path) -> None:
    target = backup_root / rel(path, root)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, target)


def apply_patches(root: Path) -> dict[str, Any]:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_root = root / "backups" / f"developer_comment_cleanup_v2.17.67_{stamp}"
    changes: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []

    for rel_path, patches in PATCHES.items():
        path = root / rel_path
        if not path.exists():
            errors.append({"file": rel_path, "error": "Dosya bulunamadı"})
            continue
        original = read_text(path)
        text = original
        applied_reasons: list[str] = []
        for reason, old, new in patches:
            if old in text:
                text = text.replace(old, new)
                applied_reasons.append(reason)
        if text != original:
            make_backup(path, root, backup_root)
            write_text(path, text)
            for reason in applied_reasons:
                changes.append({"file": rel_path, "reason": reason})

    return {
        "changed_count": len({item["file"] for item in changes}),
        "changes": changes,
        "errors": errors,
        "backup_root": str(backup_root) if changes else None,
    }


def run_compileall(root: Path) -> dict[str, Any]:
    cmd = [sys.executable, "-m", "compileall", "-q", "app", "scripts", "config.py", "run.py", "wsgi.py"]
    proc = subprocess.run(cmd, cwd=str(root), text=True, capture_output=True)
    return {
        "ran": True,
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
    }


def write_reports(root: Path, result: dict[str, Any]) -> tuple[str, str]:
    reports = ensure_reports(root)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = reports / f"bys360_developer_comment_cleanup_v2_17_67_{result['mode']}_{stamp}.json"
    md_path = reports / f"bys360_developer_comment_cleanup_v2_17_67_{result['mode']}_{stamp}.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    before_count = result.get("before", {}).get("target_personal_marker_count")
    after_count = result.get("after", {}).get("target_personal_marker_count")
    lines = [
        "# BYS360 Developer Comment Cleanup V2.17.67",
        "",
        f"Mode: `{result['mode']}`",
        f"ProjectRoot: `{result['project_root']}`",
        f"OK: `{result['ok']}`",
        "",
        "## Özet",
        "",
        f"- Önce kişisel/tarihli marker sayısı: `{before_count}`",
        f"- Sonra kişisel/tarihli marker sayısı: `{after_count}`",
        f"- Değişen dosya sayısı: `{result.get('fix', {}).get('changed_count', 0)}`",
        f"- AST hata sayısı: `{result.get('quality', {}).get('ast_error_count')}`",
        f"- py_compile hata sayısı: `{result.get('quality', {}).get('py_compile_error_count')}`",
    ]
    if result.get("compileall", {}).get("ran"):
        lines.append(f"- compileall: `{result['compileall'].get('ok')}`")
    lines.extend(["", "## Değişiklikler", ""])
    changes = result.get("fix", {}).get("changes", [])
    if changes:
        for item in changes:
            lines.append(f"- `{item['file']}` — {item['reason']}")
    else:
        lines.append("- Değişiklik yapılmadı.")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return rel(json_path, root), rel(md_path, root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["audit", "all"], default="audit")
    parser.add_argument("--compileall", action="store_true")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    before = audit_targets(root)
    fix: dict[str, Any] = {"changed_count": 0, "changes": [], "errors": [], "backup_root": None}
    if args.mode == "all":
        fix = apply_patches(root)
    after = audit_targets(root)
    target_paths = [root / p for p in TARGET_FILES]
    quality = py_quality(target_paths)
    compileall_result: dict[str, Any] = {"ran": False}
    if args.compileall:
        compileall_result = run_compileall(root)

    ok = (
        after.get("missing_count") == 0
        and after.get("target_personal_marker_count") == 0
        and not fix.get("errors")
        and quality.get("ok") is True
        and (not compileall_result.get("ran") or compileall_result.get("ok") is True)
    )
    result: dict[str, Any] = {
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(root),
        "before": before,
        "fix": fix,
        "after": after,
        "quality": quality,
        "compileall": compileall_result,
        "ok": ok,
    }
    json_report, md_report = write_reports(root, result)
    result["json_report"] = json_report
    result["md_report"] = md_report
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
