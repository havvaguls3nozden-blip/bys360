from __future__ import annotations

import argparse
import ast
import csv
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

PACKAGE = "BYS360_TECH_DEBT_CLEANUP_SAFE_V10"
VERSION = "V10"

EXCEPTION_TARGETS = [
    "app/services/corporate_information_center.py",
    "app/services/settings/effective_menu.py",
    "app/menu_registry.py",
    "app/main_handlers/account_settings_helpers.py",
    "app/institutional/hr_personnel_operations_routes.py",
    "app/services/ai_agent/service.py",
    "app/ai/routes.py",
    "app/services/menu_visibility.py",
    "app/institutional/hr_common.py",
    "app/main_handlers/account_communication_helpers.py",
]

UI_TARGETS = [
    "app/static/js/bys360_assistant_module.js",
    "app/templates/survey_create.html",
    "app/templates/survey_edit.html",
    "app/templates/announcement_new.html",
    "app/templates/hr_attendance.html",
    "app/templates/hr_leave.html",
    "app/templates/notifications_list.html",
    "app/static/css/performance_completion_phase12_final_gate.css",
    "app/templates/task_management.html",
    "app/templates/assistant_training_bank.html",
]

TECH_TERMS = [
    "api", "json", "debug", "traceback", "exception", "endpoint", "workflow", "phase",
    "sync", "unauthorized", "unauthorized_scope", "gate", "token", "payload", "stack",
    "null", "undefined", "console", "raw", "dev", "developer", "log", "error code",
    "route", "handler", "service", "module", "fallback", "cache", "timeout",
]

USER_FRIENDLY_MAP = {
    "api": "servis bağlantısı",
    "json": "veri yanıtı",
    "debug": "teknik kontrol",
    "traceback": "hata ayrıntısı",
    "exception": "hata",
    "endpoint": "bağlantı noktası",
    "workflow": "süreç akışı",
    "phase": "aşama",
    "sync": "eşitleme",
    "unauthorized": "yetki bulunmuyor",
    "unauthorized_scope": "yetki kapsamı dışında",
    "gate": "kontrol adımı",
    "token": "oturum anahtarı",
    "payload": "veri içeriği",
    "stack": "hata izi",
    "null": "boş değer",
    "undefined": "tanımsız değer",
    "console": "teknik konsol",
    "raw": "ham veri",
    "dev": "geliştirme",
    "developer": "geliştirici",
    "log": "kayıt",
    "route": "sayfa yolu",
    "handler": "işlem yöneticisi",
    "service": "servis",
    "module": "modül",
    "fallback": "yedek işlem",
    "cache": "önbellek",
    "timeout": "zaman aşımı",
}

EXCLUDE_DIR_PARTS = {
    ".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", "node_modules", "backups", "releases", "archive", ".quarantine",
}

@dataclass
class ExceptionContext:
    path: str
    lineno: int
    kind: str
    statement_count: int
    snippet: list[str]

@dataclass
class UiContext:
    path: str
    lineno: int
    term: str
    channel: str
    sample: str
    suggestion: str


def relpath(path: Path, root: Path) -> str:
    return str(path.relative_to(root)).replace("/", "\\")


def should_skip(path: Path) -> bool:
    return any(part in EXCLUDE_DIR_PARTS for part in path.parts)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="cp1254", errors="replace")


def line_snippet(lines: list[str], lineno: int, before: int = 3, after: int = 5) -> list[str]:
    start = max(1, lineno - before)
    end = min(len(lines), lineno + after)
    out = []
    for no in range(start, end + 1):
        prefix = ">>" if no == lineno else "  "
        out.append(f"{prefix} {no}: {lines[no-1].rstrip()[:220]}")
    return out


def classify_handler(handler: list[ast.stmt]) -> str:
    if not handler:
        return "empty"
    if len(handler) == 1:
        node = handler[0]
        if isinstance(node, ast.Pass):
            return "pass_only"
        if isinstance(node, ast.Return):
            return "return_only"
        if isinstance(node, ast.Continue):
            return "continue_only"
        if isinstance(node, ast.Break):
            return "break_only"
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and node.value.value is Ellipsis:
            return "ellipsis_only"
    has_log = any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in {"exception", "error", "warning", "info", "debug"}
        for stmt in handler for n in ast.walk(stmt)
    )
    if has_log:
        return "already_logged"
    return "manual_review"


def is_broad_exception(handler: ast.ExceptHandler) -> bool:
    if handler.type is None:
        return True
    if isinstance(handler.type, ast.Name) and handler.type.id == "Exception":
        return True
    return False


def exception_contexts(project_root: Path) -> tuple[list[dict[str, Any]], list[ExceptionContext]]:
    summaries = []
    contexts: list[ExceptionContext] = []
    for rel in EXCEPTION_TARGETS:
        path = project_root / rel
        if not path.exists():
            summaries.append({"path": rel.replace("/", "\\"), "exists": False})
            continue
        text = read_text(path)
        lines = text.splitlines()
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError as exc:
            summaries.append({"path": rel.replace("/", "\\"), "exists": True, "syntax_error": str(exc)})
            continue
        broad = silent = already_logged = manual = 0
        by_kind: dict[str, int] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and is_broad_exception(node):
                broad += 1
                kind = classify_handler(node.body)
                by_kind[kind] = by_kind.get(kind, 0) + 1
                if kind == "already_logged":
                    already_logged += 1
                elif kind in {"pass_only", "return_only", "continue_only", "break_only", "ellipsis_only", "empty"}:
                    silent += 1
                else:
                    manual += 1
                contexts.append(ExceptionContext(
                    path=rel.replace("/", "\\"),
                    lineno=getattr(node, "lineno", 0),
                    kind=kind,
                    statement_count=len(node.body),
                    snippet=line_snippet(lines, getattr(node, "lineno", 1)),
                ))
        summaries.append({
            "path": rel.replace("/", "\\"),
            "exists": True,
            "broad_except_count": broad,
            "silent_or_simple_count": silent,
            "already_logged_count": already_logged,
            "manual_review_count": manual,
            "by_kind": by_kind,
        })
    contexts.sort(key=lambda c: (EXCEPTION_TARGETS.index(c.path.replace("\\", "/")) if c.path.replace("\\", "/") in EXCEPTION_TARGETS else 999, c.lineno))
    return summaries, contexts


def html_visible_candidates(text: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for idx, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("<!--"):
            continue
        # Visible text between tags or common user-facing attributes.
        no_tags = re.sub(r"<[^>]+>", " ", stripped)
        if no_tags.strip():
            out.append((idx, no_tags.strip()))
        for attr in ["title", "placeholder", "aria-label", "data-title", "data-message"]:
            for m in re.finditer(attr + r"\s*=\s*(['\"])(.*?)\1", stripped, flags=re.I):
                out.append((idx, m.group(2)))
    return out


def js_string_candidates(text: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    # Conservative line-based string literal extraction. This is report-only.
    pattern = re.compile(r"(['\"`])((?:\\.|(?!\1).){2,240})\1")
    for idx, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("/*"):
            continue
        for m in pattern.finditer(line):
            val = m.group(2)
            # Skip likely identifiers, CSS selectors, URLs, asset paths, import names.
            low = val.lower().strip()
            if not low or len(low) < 3:
                continue
            if re.fullmatch(r"[a-z0-9_\-.:/#]+", low) and not any(ch.isspace() for ch in low):
                continue
            out.append((idx, val))
    return out


def css_comment_candidates(text: str) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for idx, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        if "/*" in stripped or "content:" in stripped:
            out.append((idx, stripped))
    return out


def ui_contexts(project_root: Path) -> tuple[list[dict[str, Any]], list[UiContext]]:
    summaries = []
    contexts: list[UiContext] = []
    term_re = re.compile(r"\b(" + "|".join(re.escape(t) for t in sorted(TECH_TERMS, key=len, reverse=True)) + r")\b", re.I)
    for rel in UI_TARGETS:
        path = project_root / rel
        if not path.exists():
            summaries.append({"path": rel.replace("/", "\\"), "exists": False})
            continue
        text = read_text(path)
        suffix = path.suffix.lower()
        candidates: list[tuple[int, str]] = []
        channel = "raw"
        if suffix in {".html", ".jinja", ".jinja2"}:
            candidates = html_visible_candidates(text)
            channel = "html_visible_or_attr"
        elif suffix == ".js":
            candidates = js_string_candidates(text)
            channel = "js_string_literal"
        elif suffix == ".css":
            candidates = css_comment_candidates(text)
            channel = "css_comment_or_content"
        else:
            candidates = list(enumerate(text.splitlines(), 1))
        count = 0
        term_counts: dict[str, int] = {}
        for lineno, sample in candidates:
            for m in term_re.finditer(sample):
                term = m.group(1)
                count += 1
                key = term.lower()
                term_counts[key] = term_counts.get(key, 0) + 1
                if len(contexts) < 500:
                    contexts.append(UiContext(
                        path=rel.replace("/", "\\"),
                        lineno=lineno,
                        term=term,
                        channel=channel,
                        sample=sample.strip()[:300],
                        suggestion=USER_FRIENDLY_MAP.get(key, "kurumsal Türkçe karşılık"),
                    ))
        summaries.append({
            "path": rel.replace("/", "\\"),
            "exists": True,
            "candidate_count": count,
            "term_counts": dict(sorted(term_counts.items(), key=lambda kv: kv[1], reverse=True)[:20]),
        })
    return summaries, contexts


def audit_metrics(project_root: Path) -> dict[str, Any]:
    py_files = []
    python_lines = 0
    broad = silent = 0
    for path in project_root.rglob("*.py"):
        if should_skip(path.relative_to(project_root)):
            continue
        py_files.append(path)
        text = read_text(path)
        python_lines += text.count("\n") + 1
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and is_broad_exception(node):
                broad += 1
                if classify_handler(node.body) in {"pass_only", "return_only", "continue_only", "break_only", "ellipsis_only", "empty"}:
                    silent += 1
    return {
        "python_files": len(py_files),
        "python_lines": python_lines,
        "broad_except_count": broad,
        "silent_broad_except_count": silent,
        "env_file_count": 1 if (project_root / ".env").exists() else 0,
        "local_db_count": len(list((project_root / "instance").glob("*.sqlite*"))) if (project_root / "instance").exists() else 0,
    }


def compile_project(project_root: Path) -> dict[str, Any]:
    errors = []
    checked = 0
    for path in project_root.rglob("*.py"):
        try:
            rel = path.relative_to(project_root)
        except ValueError:
            rel = path
        if should_skip(rel):
            continue
        checked += 1
        proc = subprocess.run([sys.executable, "-m", "py_compile", str(path)], cwd=str(project_root), capture_output=True, text=True)
        if proc.returncode != 0:
            errors.append({"path": str(rel).replace("/", "\\"), "error": (proc.stderr or proc.stdout)[-2000:]})
    return {"ok": not errors, "checked_python_files": checked, "error_count": len(errors), "errors": errors[:20]}


def run_quality9(project_root: Path) -> dict[str, Any] | None:
    script = project_root / "scripts" / "quality" / "bys360_quality9_ci_gate.py"
    if not script.exists():
        return None
    proc = subprocess.run([sys.executable, str(script), "--project-root", str(project_root)], cwd=str(project_root), capture_output=True, text=True)
    return {
        "returncode": proc.returncode,
        "stdout_tail": (proc.stdout or "")[-1200:],
        "stderr_tail": (proc.stderr or "")[-1200:],
    }


def write_reports(project_root: Path, out_dir: Path, stamp: str, data: dict[str, Any]) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f"{PACKAGE}_{stamp}.json"
    md_path = out_dir / f"{PACKAGE}_{stamp}_TARGETED_MANUAL_PLAN.md"
    exception_csv = out_dir / f"{PACKAGE}_{stamp}_EXCEPTION_CONTEXTS.csv"
    ui_csv = out_dir / f"{PACKAGE}_{stamp}_UI_VISIBLE_TERMS.csv"

    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    with exception_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["path", "lineno", "kind", "statement_count", "snippet"])
        w.writeheader()
        for c in data["exception_contexts"]:
            w.writerow({**{k: c[k] for k in ["path", "lineno", "kind", "statement_count"]}, "snippet": "\n".join(c["snippet"])})

    with ui_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["path", "lineno", "term", "channel", "sample", "suggestion"])
        w.writeheader()
        for c in data["ui_contexts"]:
            w.writerow(c)

    md = []
    md.append(f"# {PACKAGE} — Hedefli Manuel Temizlik Planı\n")
    md.append(f"Tarih: {datetime.now().isoformat(timespec='seconds')}\n")
    md.append("## Özet\n")
    md.append("Bu V10 paketi kod değiştirmez. Kalan borç artık otomatik patch için riskli olduğundan, hedef dosyalar için satır bağlamı ve güvenli V11 planı üretir.\n")
    md.append("## Audit Metrikleri\n")
    for k, v in data["audit_metrics"].items():
        md.append(f"- {k}: {v}")
    md.append("\n## Exception hedef dosya özeti\n")
    for s in data["exception_summaries"]:
        md.append(f"- `{s.get('path')}`: broad={s.get('broad_except_count')}, silent/simple={s.get('silent_or_simple_count')}, logged={s.get('already_logged_count')}, manual={s.get('manual_review_count')}, kinds={s.get('by_kind')}")
    md.append("\n## İlk exception bağlamları\n")
    for c in data["exception_contexts"][:80]:
        md.append(f"\n### {c['path']}:{c['lineno']} — {c['kind']}\n")
        md.append("```text")
        md.extend(c["snippet"])
        md.append("```")
    md.append("\n## UI hedef dosya özeti\n")
    for s in data["ui_summaries"]:
        md.append(f"- `{s.get('path')}`: candidate_count={s.get('candidate_count')}, terms={s.get('term_counts')}")
    md.append("\n## İlk UI görünür teknik dil adayları\n")
    for c in data["ui_contexts"][:120]:
        md.append(f"- `{c['path']}:{c['lineno']}` [{c['channel']}] `{c['term']}` → öneri: **{c['suggestion']}** | {c['sample']}")
    md.append("\n## V11 için önerilen sıra\n")
    md.append("1. `app/static/js/bys360_assistant_module.js` içindeki kullanıcıya görünen string literal metinleri kurumsal Türkçeye çevir.")
    md.append("2. `survey_create.html`, `survey_edit.html`, `announcement_new.html` görünür teknik metinlerini temizle.")
    md.append("3. Exception tarafında önce `corporate_information_center.py`, sonra `effective_menu.py`, sonra `menu_registry.py` için dosya özelinde elle düzenlenmiş patch uygula.")
    md.append("4. Her dosya patchinden sonra tek dosya compile + tam compile + Quality 9 çalıştır.")
    md_path.write_text("\n".join(md), encoding="utf-8")

    return {
        "targeted_manual_plan": str(md_path),
        "json_report": str(json_path),
        "exception_contexts_csv": str(exception_csv),
        "ui_visible_terms_csv": str(ui_csv),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-root", required=True)
    ap.add_argument("--mode", default="all")
    ap.add_argument("--output-root", default="C:\\bys360")
    ap.add_argument("--run-compile", action="store_true")
    args = ap.parse_args()

    project_root = Path(args.project_root).resolve()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = project_root / "reports" / "technical_debt"

    metrics = audit_metrics(project_root)
    exception_summaries, exception_ctx_objs = exception_contexts(project_root)
    ui_summaries, ui_ctx_objs = ui_contexts(project_root)

    data: dict[str, Any] = {
        "ok": True,
        "package": PACKAGE,
        "version": VERSION,
        "mode": args.mode,
        "project_root": str(project_root),
        "code_changed": False,
        "reason": "Kalan exception ve UI borcu otomatik patch için riskli; V10 sadece hedefli manuel bağlam raporu üretir.",
        "audit_metrics": metrics,
        "exception_summaries": exception_summaries,
        "exception_contexts": [asdict(c) for c in exception_ctx_objs],
        "ui_summaries": ui_summaries,
        "ui_contexts": [asdict(c) for c in ui_ctx_objs],
        "security_hygiene": {
            "env_files": [".env"] if (project_root / ".env").exists() else [],
            "env_examples": [".env.example"] if (project_root / ".env.example").exists() else [],
            "local_dbs": [str(p.relative_to(project_root)).replace("/", "\\") for p in (project_root / "instance").glob("*.sqlite*")] if (project_root / "instance").exists() else [],
        },
    }

    if args.run_compile:
        compile_result = compile_project(project_root)
        quality9 = run_quality9(project_root)
        data["quality_gate"] = {
            "compile_requested": True,
            "compile_ok": compile_result["ok"],
            "compile_detail": compile_result,
            "existing_quality_gate": str(project_root / "scripts" / "quality" / "bys360_quality9_ci_gate.py") if (project_root / "scripts" / "quality" / "bys360_quality9_ci_gate.py").exists() else None,
            "quality9_run": quality9,
        }
        data["ok"] = bool(compile_result["ok"] and (quality9 is None or quality9.get("returncode") == 0))
    else:
        data["quality_gate"] = {"compile_requested": False}

    reports = write_reports(project_root, report_dir, stamp, data)
    data["reports"] = reports

    compact = {
        "ok": data["ok"],
        "package": PACKAGE,
        "version": VERSION,
        "mode": args.mode,
        "code_changed": False,
        "audit_metrics": metrics,
        "exception_summaries_top3": exception_summaries[:3],
        "ui_summaries_top5": ui_summaries[:5],
        "security_hygiene": data["security_hygiene"],
        "quality_gate": data["quality_gate"],
        "reports": reports,
        "next_step": "V11 dosya özel patch: önce asistan JS görünür metinleri, sonra survey/announcement HTML, ardından ilk 3 exception hotspot dosyası.",
    }
    print(json.dumps(compact, ensure_ascii=False, indent=2))
    return 0 if data["ok"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
