from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "build",
    "dist",
    "htmlcov",
    ".idea",
    ".vscode",
}

APP_TOP_LEVEL = {"app", "config.py", "wsgi.py", "run.py", "run_server.py"}
TEST_TOP_LEVEL = {"tests", "test"}
MIGRATION_TOP_LEVEL = {"migrations", "alembic", "alembic_versions"}
SCRIPT_TOP_LEVEL = {"scripts", "tools"}
ROOT_CONFIG_FILES = {
    "config.py",
    "wsgi.py",
    "run.py",
    "run_server.py",
    "alembic.ini",
    "pyproject.toml",
    "pytest.ini",
    "requirements.txt",
    "Dockerfile",
    "docker-compose.yml",
    ".env.example",
    ".env.production.example",
    ".env.docker.example",
}

SECRET_PATTERNS = [
    ("password_assignment", re.compile(r"(?i)\b(password|passwd|pwd)\s*=\s*['\"][^'\"]{6,}['\"]")),
    ("secret_assignment", re.compile(r"(?i)\b(secret|secret_key|csrf_secret|jwt_secret)\s*=\s*['\"][^'\"]{8,}['\"]")),
    ("token_assignment", re.compile(r"(?i)\b(token|api[_-]?key|access[_-]?key)\s*=\s*['\"][^'\"]{8,}['\"]")),
    ("postgres_url_with_password", re.compile(r"(?i)postgres(?:ql)?://[^\s:@]+:[^\s@]+@")),
    ("redis_url_with_password", re.compile(r"(?i)redis://:[^\s@]+@")),
    ("private_key_marker", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----")),
]

SAFE_SECRET_FILE_ALLOWLIST = {
    ".env.example",
    ".env.production.example",
    ".env.docker.example",
    "docs/BYS360_OPS_HARDENING_V1_README.md",
    "docs/BYS360_OPS_HARDENING_V1_COMMANDS.md",
}

@dataclass
class PyFinding:
    path: str
    scope: str
    print_calls: int = 0
    broad_except_exception: int = 0
    bare_except: int = 0
    syntax_error: str | None = None
    lines_print: list[int] = field(default_factory=list)
    lines_broad_except: list[int] = field(default_factory=list)
    lines_bare_except: list[int] = field(default_factory=list)

@dataclass
class SecretFinding:
    path: str
    scope: str
    line: int
    kind: str
    snippet: str


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace('\\', '/')
    except ValueError:
        return str(path).replace('\\', '/')


def iter_files(root: Path, suffixes: Iterable[str]) -> Iterable[Path]:
    suffixes = set(suffixes)
    for path in root.rglob('*'):
        if not path.is_file():
            continue
        try:
            relative_parts = path.relative_to(root).parts
        except ValueError:
            relative_parts = path.parts
        if any(part in SKIP_DIRS for part in relative_parts):
            continue
        if path.name.endswith('.bak') or path.name.endswith('.old'):
            continue
        if path.suffix.lower() in suffixes or path.name in suffixes:
            yield path


def classify_scope(path: Path, root: Path) -> str:
    rp = rel(path, root)
    first = rp.split('/', 1)[0]
    name = path.name
    if first == 'app':
        return 'app_live_candidate'
    if first in TEST_TOP_LEVEL or name.startswith('test_') or rp.startswith('tests/'):
        return 'tests'
    if first in MIGRATION_TOP_LEVEL or '/versions/' in rp:
        return 'migrations'
    if first in SCRIPT_TOP_LEVEL:
        return 'scripts_tools'
    if name in ROOT_CONFIG_FILES:
        return 'root_config'
    if first in {'docs', 'reports'}:
        return 'docs_reports'
    return 'other'


def analyze_python(path: Path, root: Path) -> PyFinding:
    finding = PyFinding(path=rel(path, root), scope=classify_scope(path, root))
    try:
        text = path.read_text(encoding='utf-8-sig')
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        finding.syntax_error = f"line {exc.lineno}: {exc.msg}"
        return finding
    except UnicodeDecodeError as exc:
        finding.syntax_error = f"decode error: {exc}"
        return finding
    except OSError as exc:
        finding.syntax_error = f"read error: {exc}"
        return finding

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == 'print':
                finding.print_calls += 1
                finding.lines_print.append(getattr(node, 'lineno', 0))
        elif isinstance(node, ast.ExceptHandler):
            line_no = getattr(node, 'lineno', 0)
            if node.type is None:
                finding.bare_except += 1
                finding.lines_bare_except.append(line_no)
            elif isinstance(node.type, ast.Name) and node.type.id == 'Exception':
                finding.broad_except_exception += 1
                finding.lines_broad_except.append(line_no)
            elif isinstance(node.type, ast.Tuple) and any(isinstance(item, ast.Name) and item.id == 'Exception' for item in node.type.elts):
                finding.broad_except_exception += 1
                finding.lines_broad_except.append(line_no)
    return finding


def mask_line(line: str) -> str:
    line = line.strip()
    line = re.sub(r"(['\"])[^'\"]{4,}\1", r"\1***\1", line)
    line = re.sub(r"://([^:\s/@]+):([^@\s]+)@", r"://***:***@", line)
    if len(line) > 120:
        line = line[:117] + '...'
    return line


def scan_secrets(path: Path, root: Path) -> list[SecretFinding]:
    rp = rel(path, root)
    if rp in SAFE_SECRET_FILE_ALLOWLIST:
        return []
    if path.name in {'.env', '.env.docker.local'}:
        # Never read live env values. Existence is reported separately.
        return [SecretFinding(path=rp, scope=classify_scope(path, root), line=0, kind='live_env_file_present', snippet='Değer okunmadı; dosya canlı/teslim paketinden ayrı tutulmalı.')]
    try:
        text = path.read_text(encoding='utf-8-sig', errors='ignore')
    except OSError:
        return []
    findings: list[SecretFinding] = []
    for i, line in enumerate(text.splitlines(), start=1):
        for kind, pattern in SECRET_PATTERNS:
            if pattern.search(line):
                findings.append(SecretFinding(path=rp, scope=classify_scope(path, root), line=i, kind=kind, snippet=mask_line(line)))
                break
    return findings


def command_exists(name: str) -> bool:
    try:
        subprocess.run([name, '--version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except OSError:
        return False
    return True


def sum_scope(findings: list[PyFinding]) -> dict[str, dict[str, int]]:
    scopes = sorted({f.scope for f in findings} | {'app_live_candidate', 'scripts_tools', 'tests', 'migrations', 'root_config', 'docs_reports', 'other'})
    result = {}
    for scope in scopes:
        bucket = [f for f in findings if f.scope == scope]
        result[scope] = {
            'python_files': len(bucket),
            'syntax_errors': sum(1 for f in bucket if f.syntax_error),
            'print_calls': sum(f.print_calls for f in bucket),
            'broad_except_exception': sum(f.broad_except_exception for f in bucket),
            'bare_except': sum(f.bare_except for f in bucket),
        }
    return result


def build_report(root: Path, mode: str) -> dict:
    py_findings = [analyze_python(path, root) for path in iter_files(root, ['.py'])]
    secret_findings: list[SecretFinding] = []
    secret_suffixes = ['.py', '.env', '.txt', '.toml', '.yml', '.yaml', '.ini', '.cfg', '.json']
    for path in iter_files(root, secret_suffixes):
        secret_findings.extend(scan_secrets(path, root))

    required_files = [
        'Dockerfile',
        '.dockerignore',
        'docker-compose.yml',
        'docker/gunicorn.conf.py',
        'docker/entrypoint.sh',
        '.env.docker.example',
        '.github/workflows/bys360-ci.yml',
    ]
    app_findings = [f for f in py_findings if f.scope == 'app_live_candidate']
    root_findings = [f for f in py_findings if f.scope == 'root_config']
    live_candidate = app_findings + root_findings
    live_secret_findings = [s for s in secret_findings if s.scope in {'app_live_candidate', 'root_config', 'other'}]

    return {
        'package': 'BYS360_OPS_HARDENING_V2_TRIAGE',
        'mode': mode,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'root': str(root),
        'required_files': {name: (root / name).exists() for name in required_files},
        'tooling': {
            'docker_available': command_exists('docker'),
            'git_available': command_exists('git'),
        },
        'scope_totals': sum_scope(py_findings),
        'live_candidate_totals': {
            'python_files': len(live_candidate),
            'syntax_errors': sum(1 for f in live_candidate if f.syntax_error),
            'print_calls': sum(f.print_calls for f in live_candidate),
            'broad_except_exception': sum(f.broad_except_exception for f in live_candidate),
            'bare_except': sum(f.bare_except for f in live_candidate),
            'possible_secret_files': len({s.path for s in live_secret_findings}),
            'possible_secret_hits': len(live_secret_findings),
        },
        'all_totals': {
            'python_files': len(py_findings),
            'syntax_errors': sum(1 for f in py_findings if f.syntax_error),
            'print_calls': sum(f.print_calls for f in py_findings),
            'broad_except_exception': sum(f.broad_except_exception for f in py_findings),
            'bare_except': sum(f.bare_except for f in py_findings),
            'possible_secret_files': len({s.path for s in secret_findings}),
            'possible_secret_hits': len(secret_findings),
        },
        'top_live_print_files': [asdict(f) for f in sorted(live_candidate, key=lambda x: x.print_calls, reverse=True)[:40] if f.print_calls],
        'top_live_except_files': [asdict(f) for f in sorted(live_candidate, key=lambda x: x.broad_except_exception + x.bare_except, reverse=True)[:40] if f.broad_except_exception or f.bare_except],
        'top_all_print_files': [asdict(f) for f in sorted(py_findings, key=lambda x: x.print_calls, reverse=True)[:30] if f.print_calls],
        'top_all_except_files': [asdict(f) for f in sorted(py_findings, key=lambda x: x.broad_except_exception + x.bare_except, reverse=True)[:30] if f.broad_except_exception or f.bare_except],
        'syntax_error_files': [asdict(f) for f in py_findings if f.syntax_error],
        'possible_secret_files': [asdict(s) for s in secret_findings],
        'recommendation_order': [
            '1) Önce possible_secret_files listesini kontrol et; gerçek secret varsa koda/zip içine koyma, .env.docker.local veya sunucu secret alanına taşı.',
            '2) app_live_candidate kapsamındaki print() çağrılarını servis servis logging.getLogger(__name__) kullanımına çevir.',
            '3) app_live_candidate kapsamındaki except Exception bloklarını kritik dosyalardan başlayarak spesifik exception + logger.exception ile ele al.',
            '4) scripts_tools kapsamındaki print/except borcunu canlı risk olarak değil, bakım/temizlik borcu olarak ayrı yönet.',
            '5) Docker kurulu ortamda docker compose config ve image build kontrolünü çalıştır.',
        ],
    }


def md_table_row(*cells: object) -> str:
    return '| ' + ' | '.join(str(c) for c in cells) + ' |'


def to_markdown(report: dict) -> str:
    live = report['live_candidate_totals']
    all_totals = report['all_totals']
    lines: list[str] = [
        '# BYS360 Operasyonel Sağlamlaştırma V2 — Kalite Triage Raporu',
        '',
        f"Üretim zamanı: `{report['generated_at']}`",
        f"Proje kökü: `{report['root']}`",
        '',
        '## 1. Canlı Aday Kod Özeti',
        '',
        'Bu bölüm yalnızca `app/` ve kök çalıştırma/config dosyalarını dikkate alır. Asıl canlı risk bu kapsamdadır.',
        '',
        '| Kontrol | Değer |',
        '|---|---:|',
        md_table_row('Python dosyası', live['python_files']),
        md_table_row('Syntax hatası', live['syntax_errors']),
        md_table_row('print() çağrısı', live['print_calls']),
        md_table_row('except Exception', live['broad_except_exception']),
        md_table_row('bare except', live['bare_except']),
        md_table_row('Olası secret dosyası', live['possible_secret_files']),
        md_table_row('Olası secret eşleşmesi', live['possible_secret_hits']),
        '',
        '## 2. Tüm Repo Özeti',
        '',
        '| Kontrol | Değer |',
        '|---|---:|',
        md_table_row('Python dosyası', all_totals['python_files']),
        md_table_row('Syntax hatası', all_totals['syntax_errors']),
        md_table_row('print() çağrısı', all_totals['print_calls']),
        md_table_row('except Exception', all_totals['broad_except_exception']),
        md_table_row('bare except', all_totals['bare_except']),
        md_table_row('Olası secret dosyası', all_totals['possible_secret_files']),
        md_table_row('Olası secret eşleşmesi', all_totals['possible_secret_hits']),
        '',
        '## 3. Kapsam Bazlı Ayrım',
        '',
        '| Kapsam | Python | Syntax | print() | except Exception | bare except |',
        '|---|---:|---:|---:|---:|---:|',
    ]
    for scope, data in report['scope_totals'].items():
        lines.append(md_table_row(scope, data['python_files'], data['syntax_errors'], data['print_calls'], data['broad_except_exception'], data['bare_except']))

    lines += ['', '## 4. Operasyon Dosyaları', '', '| Dosya | Durum |', '|---|---|']
    for name, ok in report['required_files'].items():
        lines.append(md_table_row(f'`{name}`', 'VAR' if ok else 'EKSİK'))

    if report['syntax_error_files']:
        lines += ['', '## 5. Syntax Hataları', '', '| Dosya | Hata |', '|---|---|']
        for f in report['syntax_error_files'][:80]:
            lines.append(md_table_row(f"`{f['path']}`", f['syntax_error']))

    lines += ['', '## 6. Canlı Aday Kodda En Çok print() İçeren Dosyalar', '', '| Dosya | print() | İlk satırlar |', '|---|---:|---|']
    for f in report['top_live_print_files'][:20]:
        lines.append(md_table_row(f"`{f['path']}`", f['print_calls'], ', '.join(map(str, f.get('lines_print', [])[:8]))))

    lines += ['', '## 7. Canlı Aday Kodda En Çok except Exception İçeren Dosyalar', '', '| Dosya | except Exception | İlk satırlar |', '|---|---:|---|']
    for f in report['top_live_except_files'][:20]:
        count = f['broad_except_exception'] + f['bare_except']
        lines.append(md_table_row(f"`{f['path']}`", count, ', '.join(map(str, (f.get('lines_broad_except', []) + f.get('lines_bare_except', []))[:8]))))

    lines += ['', '## 8. Olası Secret / Hassas Bilgi Bulguları', '', 'Değerler güvenlik nedeniyle maskelendi; canlı secret değeri rapora yazılmaz.', '', '| Dosya | Satır | Tür | Maske |', '|---|---:|---|---|']
    for s in report['possible_secret_files'][:100]:
        lines.append(md_table_row(f"`{s['path']}`", s['line'], s['kind'], f"`{s['snippet']}`"))

    lines += ['', '## 9. Önerilen Uygulama Sırası', '']
    for item in report['recommendation_order']:
        lines.append(f'- {item}')

    lines += ['', '## 10. Yorum', '', 'V2 paketi üretim kodunu otomatik değiştirmez. Amaç önce şişen toplam sayıyı canlı uygulama riski, script/test borcu ve secret riski olarak ayrıştırmaktır. Bu rapora göre V3 paketiyle yalnızca hedef dosyalara kontrollü print/logger ve exception iyileştirmesi uygulanmalıdır.']
    return '\n'.join(lines) + '\n'


def main() -> int:
    parser = argparse.ArgumentParser(description='BYS360 Ops Hardening V2 triage audit')
    parser.add_argument('--root', default='.', help='Project root')
    parser.add_argument('--mode', default='audit')
    parser.add_argument('--report', default='reports/quality/BYS360_OPS_HARDENING_V2_TRIAGE_REPORT.md')
    parser.add_argument('--json-report', default='reports/quality/BYS360_OPS_HARDENING_V2_TRIAGE_REPORT.json')
    parser.add_argument('--max-live-print', type=int, default=10000)
    parser.add_argument('--max-live-except', type=int, default=10000)
    parser.add_argument('--fail-on-secret', action='store_true')
    args = parser.parse_args()

    root = Path(args.root).resolve()
    report = build_report(root, args.mode)
    report_path = root / args.report
    json_path = root / args.json_report
    report_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(to_markdown(report), encoding='utf-8')
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f"BYS360_OPS_TRIAGE_V2_REPORT={report_path}")
    print(f"BYS360_OPS_TRIAGE_V2_JSON={json_path}")
    print(json.dumps(report['live_candidate_totals'], ensure_ascii=False))

    live = report['live_candidate_totals']
    if live['syntax_errors']:
        print('ERROR: Canlı aday kodda syntax hatası var.', file=sys.stderr)
        return 2
    if live['print_calls'] > args.max_live_print:
        print(f"ERROR: Canlı aday print() eşiği aşıldı: {live['print_calls']} > {args.max_live_print}", file=sys.stderr)
        return 3
    if live['broad_except_exception'] + live['bare_except'] > args.max_live_except:
        print(f"ERROR: Canlı aday except eşiği aşıldı: {live['broad_except_exception'] + live['bare_except']} > {args.max_live_except}", file=sys.stderr)
        return 4
    if args.fail_on_secret and live['possible_secret_hits']:
        print('ERROR: Canlı aday kodda olası secret bulgusu var.', file=sys.stderr)
        return 5
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
