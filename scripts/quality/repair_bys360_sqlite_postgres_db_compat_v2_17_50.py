# -*- coding: utf-8 -*-
"""
BYS360 SQLite/PostgreSQL DB uyumluluk ve temiz proje sonrası veritabanı probu V2.17.50.

Amaç:
- app/services/assistant_module_access.py içindeki PostgreSQL'e özgü information_schema.columns sorgusunun
  SQLite local/test ortamında hata logu üretmesini engellemek.
- Temiz kaynak kopyasına geçildikten sonra uygulamanın hangi DB diyalektiyle açıldığını ve ana tabloların varlığını raporlamak.

Bu script gerçek veritabanı şifresi yazmaz/raporlamaz, tablo oluşturmaz, veri değiştirmez.
"""
from __future__ import annotations

import argparse
import ast
import datetime as _dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

VERSION = "V2.17.50"
REPORT_STEM = "bys360_sqlite_postgres_db_compat_v2_17_50_report"

NEW_TABLE_COLUMNS = '''def _table_columns(session, table_name: str) -> set[str]:
    """Tablo kolonlarını DB motoruna göre güvenli okur.

    Not:
    - PostgreSQL tarafında information_schema.columns kullanılabilir.
    - SQLite local/test ortamında information_schema yoktur; PRAGMA table_info kullanılır.
    - Hata logunu spamlememek için beklenen dialect uyumsuzlukları exception olarak loglanmaz.
    """
    if text is None or session is None:
        return set()

    table = str(table_name or "").strip()
    if not table or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", table):
        return set()

    bind = None
    dialect_name = ""
    try:
        bind = session.get_bind() if hasattr(session, "get_bind") else getattr(session, "bind", None)
        dialect_name = str(getattr(getattr(bind, "dialect", None), "name", "") or "").lower()
    except Exception:
        bind = None
        dialect_name = ""

    if dialect_name == "sqlite":
        try:
            rows = session.execute(text(f'PRAGMA table_info("{table}")')).fetchall()
            return {str(row[1]) for row in rows if len(row) > 1}
        except Exception:
            return set()

    if dialect_name in {"postgresql", "postgres"}:
        try:
            rows = session.execute(
                text("select column_name from information_schema.columns where table_name = :t"),
                {"t": table},
            ).fetchall()
            return {str(row[0]) for row in rows}
        except Exception:
            return set()

    try:
        from sqlalchemy import inspect  # type: ignore
        if bind is not None:
            return {str(col.get("name")) for col in inspect(bind).get_columns(table) if col.get("name")}
    except Exception:
        pass

    try:
        rows = session.execute(text(f'PRAGMA table_info("{table}")')).fetchall()
        return {str(row[1]) for row in rows if len(row) > 1}
    except Exception:
        return set()

'''


def _now_stamp() -> str:
    return _dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def _run(cmd: list[str], cwd: Path, timeout: int = 120) -> dict:
    try:
        p = subprocess.run(cmd, cwd=str(cwd), text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
        return {"ok": p.returncode == 0, "returncode": p.returncode, "stdout_tail": p.stdout[-6000:], "stderr_tail": p.stderr[-6000:]}
    except Exception as exc:
        return {"ok": False, "returncode": None, "stdout_tail": "", "stderr_tail": str(exc)}


def _syntax_ok(path: Path) -> dict:
    if not path.exists():
        return {"exists": False, "ok": False, "error": "dosya yok"}
    try:
        ast.parse(path.read_text(encoding="utf-8-sig"))
        return {"exists": True, "ok": True, "error": ""}
    except Exception as exc:
        return {"exists": True, "ok": False, "error": str(exc)}


def patch_assistant_module_access(project_root: Path, mode: str) -> dict:
    target = project_root / "app" / "services" / "assistant_module_access.py"
    result = {
        "target": str(target.relative_to(project_root)) if target.exists() else str(target),
        "exists": target.exists(),
        "changed": False,
        "backup": "",
        "error": "",
        "before_compile": _syntax_ok(target),
        "after_compile": {},
    }
    if not target.exists():
        result["error"] = "assistant_module_access.py bulunamadi"
        return result
    src = target.read_text(encoding="utf-8-sig")
    if "BYS360_SQLITE_POSTGRES_DB_COMPAT_V2_17_50" in src:
        result["after_compile"] = _syntax_ok(target)
        return result
    pattern = re.compile(r"def _table_columns\(session, table_name: str\) -> set\[str\]:\n.*?(?=\ndef _candidate_keys\(\) -> set\[str\]:)", re.S)
    if not pattern.search(src):
        result["error"] = "_table_columns blok bulunamadi"
        return result
    new_block = "# BYS360_SQLITE_POSTGRES_DB_COMPAT_V2_17_50\n" + NEW_TABLE_COLUMNS
    patched = pattern.sub(new_block, src, count=1)
    if mode == "audit":
        result["after_compile"] = result["before_compile"]
        return result
    quarantine = project_root / "_local_quarantine" / f"bys360_sqlite_postgres_db_compat_{_now_stamp()}" / "app" / "services"
    quarantine.mkdir(parents=True, exist_ok=True)
    backup = quarantine / "assistant_module_access.py.before_v2_17_50"
    shutil.copy2(target, backup)
    result["backup"] = str(backup.relative_to(project_root))
    target.write_text(patched, encoding="utf-8")
    result["changed"] = True
    result["after_compile"] = _syntax_ok(target)
    if not result["after_compile"].get("ok"):
        shutil.copy2(backup, target)
        result["changed"] = False
        result["error"] = "syntax bozuldu; rollback yapildi"
        result["after_compile"] = _syntax_ok(target)
    return result


def db_probe(project_root: Path) -> dict:
    code = r'''
import json
out={"app_create_ok":False,"dialect":"","database_uri_kind":"","tables":[],"required":{},"error":""}
try:
    from app import create_app
    app=create_app()
    out["app_create_ok"]=True
    with app.app_context():
        try:
            from app.extensions import db
            bind = db.engine
            out["dialect"] = getattr(bind.dialect, "name", "")
            uri = str(app.config.get("SQLALCHEMY_DATABASE_URI", ""))
            if uri.startswith("sqlite"):
                out["database_uri_kind"] = "sqlite"
            elif uri.startswith("postgres"):
                out["database_uri_kind"] = "postgresql"
            elif uri:
                out["database_uri_kind"] = uri.split(":",1)[0]
            from sqlalchemy import inspect
            tables = sorted(inspect(bind).get_table_names())
            out["tables"] = tables[:300]
            req = ["users","system_settings","module_settings","role_menu_defaults","user_menu_permissions"]
            out["required"] = {t: (t in tables) for t in req}
        except Exception as e:
            out["error"] = str(e)
except Exception as e:
    out["error"] = str(e)
print(json.dumps(out, ensure_ascii=False))
'''
    res = _run([sys.executable, "-c", code], project_root, timeout=90)
    parsed = {}
    if res.get("stdout_tail"):
        try:
            parsed = json.loads(res["stdout_tail"].strip().splitlines()[-1])
        except Exception as exc:
            parsed = {"parse_error": str(exc), "raw": res.get("stdout_tail", "")[-1000:]}
    return {"process": res, "parsed": parsed}


def write_report(project_root: Path, payload: dict) -> tuple[str, str]:
    reports = project_root / "reports" / "quality"
    reports.mkdir(parents=True, exist_ok=True)
    json_path = reports / f"{REPORT_STEM}.json"
    md_path = reports / f"{REPORT_STEM}.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    dbp = payload.get("db_probe", {}).get("parsed", {}) or {}
    required = dbp.get("required", {}) or {}
    required_rows = "\n".join([f"| `{k}` | {v} |" for k, v in required.items()]) or "| - | - |"
    patch = payload.get("patch", {})
    health = payload.get("health_summary", {})
    conclusion = []
    if dbp.get("database_uri_kind") == "sqlite" and not all((required or {"_": False}).values()):
        conclusion.append("Uygulama SQLite ile açılıyor ve canlı/temel tablolar eksik görünüyor. Temiz kaynak kopyası veritabanı değildir; PostgreSQL .env veya DB yedeği geri alınmalıdır.")
    if patch.get("changed"):
        conclusion.append("assistant_module_access.py SQLite/PostgreSQL uyumlu kolon okuma mantığına alındı.")
    if not conclusion:
        conclusion.append("Kod ve DB probu tamamlandı; rapordaki tablo durumunu kontrol edin.")

    md = f"""# BYS360 SQLite/PostgreSQL DB Uyumluluk ve Temiz Proje DB Probu {VERSION}

Bu rapor temiz proje dosyası değişimi sonrası görülen veritabanı hatasını ayırmak için üretilmiştir. Uygulama verisi değiştirilmez.

## Teşhis

- Logdaki `information_schema.columns` hatası PostgreSQL'e özgü kolon sorgusunun SQLite local/test ortamında çalışmasından kaynaklanır.
- Logdaki `no such table: users` hatası, uygulamanın boş/eksik SQLite veritabanıyla açıldığını gösterir.
- Temiz kaynak paketleri genellikle `.env`, canlı PostgreSQL bağlantısı ve gerçek veritabanı içeriği taşımaz.

## Patch

| Alan | Değer |
|---|---|
| target | `{patch.get('target','')}` |
| changed | {patch.get('changed')} |
| backup | `{patch.get('backup','')}` |
| error | `{patch.get('error','')}` |

## DB Probu

| Alan | Değer |
|---|---|
| app_create_ok | {dbp.get('app_create_ok')} |
| dialect | `{dbp.get('dialect','')}` |
| database_uri_kind | `{dbp.get('database_uri_kind','')}` |
| table_count | {len(dbp.get('tables', []) or [])} |
| probe_error | `{dbp.get('error','')}` |

## Zorunlu Tablo Kontrolü

| Tablo | Var mı? |
|---|---|
{required_rows}

## Sağlık Kontrolü

| Alan | Değer |
|---|---|
| target_compile_ok | {health.get('target_compile_ok')} |
| compileall_ok | {health.get('compileall_ok')} |
| app_factory_ok | {health.get('app_factory_ok')} |
| overall_code_ok | {health.get('overall_code_ok')} |
| database_ready | {health.get('database_ready')} |

## Sonuç

""" + "\n".join([f"- {x}" for x in conclusion]) + """

## Önerilen Sonraki Adım

1. Eğer hedef canlı/gerçek proje ise `.env` içindeki `DATABASE_URL` PostgreSQL bağlantısını eski çalışan projeden geri alın.
2. Veritabanı yedeği PostgreSQL tarafında duruyorsa uygulamayı SQLite ile değil PostgreSQL ile açın.
3. Lokal SQLite test yapılacaksa önce migration/seed çalıştırılmalı; aksi halde `users` gibi temel tablolar bulunmaz.
4. `python -m compileall app config.py scripts` ve `python -c \"from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))\"` ile tekrar kontrol edin.
"""
    md_path.write_text(md, encoding="utf-8")
    return str(json_path.relative_to(project_root)), str(md_path.relative_to(project_root))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--mode", choices=["audit", "all"], default="all")
    args = parser.parse_args()
    project_root = Path(args.project_root).resolve()
    patch = patch_assistant_module_access(project_root, args.mode)
    target_compile = _syntax_ok(project_root / "app" / "services" / "assistant_module_access.py")
    compileall = _run([sys.executable, "-m", "compileall", "app", "config.py", "scripts"], project_root, timeout=180) if args.mode == "all" else {"ok": None}
    app_factory = _run([sys.executable, "-c", "from app import create_app; app=create_app(); print('BYS360_APP_CREATE_OK', len(app.blueprints))"], project_root, timeout=90)
    probe = db_probe(project_root)
    dbp = probe.get("parsed", {}) or {}
    required = dbp.get("required", {}) or {}
    database_ready = bool(required) and all(required.values())
    health = {
        "target_compile_ok": bool(target_compile.get("ok")),
        "compileall_ok": compileall.get("ok"),
        "app_factory_ok": app_factory.get("ok"),
        "overall_code_ok": bool(target_compile.get("ok")) and (compileall.get("ok") in {True, None}) and bool(app_factory.get("ok")),
        "database_ready": database_ready,
    }
    payload = {
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(project_root),
        "patch": patch,
        "target_compile": target_compile,
        "compileall": compileall,
        "app_factory": app_factory,
        "db_probe": probe,
        "health_summary": health,
    }
    json_report, md_report = write_report(project_root, payload)
    print(json.dumps({
        "version": VERSION,
        "mode": args.mode,
        "patch_changed": patch.get("changed"),
        "compileall_ok": compileall.get("ok"),
        "app_factory_ok": app_factory.get("ok"),
        "database_ready": database_ready,
        "db_dialect": dbp.get("dialect"),
        "database_uri_kind": dbp.get("database_uri_kind"),
        "json_report": json_report,
        "md_report": md_report,
    }, ensure_ascii=False, indent=2))
    print("BYS360_SQLITE_POSTGRES_DB_COMPAT_V2_17_50_REPORT_OK")
    if health["overall_code_ok"]:
        print("BYS360_SQLITE_POSTGRES_DB_COMPAT_V2_17_50_CODE_HEALTH_OK")
    if not database_ready:
        print("BYS360_SQLITE_POSTGRES_DB_COMPAT_V2_17_50_DATABASE_NEEDS_RESTORE_OR_MIGRATION")
    print("BYS360_SQLITE_POSTGRES_DB_COMPAT_V2_17_50_OK")
    return 0 if health["overall_code_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
