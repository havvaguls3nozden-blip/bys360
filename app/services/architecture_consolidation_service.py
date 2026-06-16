from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


LARGE_ROUTE_THRESHOLD = 50_000
GENERATED_REPORT_PATTERNS = (
    'pilot_',
    'go_live_',
    'rollout_plan',
    'hypercare_',
    'module_expansion_',
    'repository_media_manifest',
    'dashboard_expansion_catalog',
)


@dataclass
class ConsolidationItem:
    name: str
    area: str
    status: str
    evidence: str
    risk: str
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _exists(project_root: Path, relative_path: str) -> bool:
    return (project_root / relative_path).exists()


def _glob_count(project_root: Path, pattern: str) -> int:
    return sum(1 for _ in project_root.glob(pattern))


def _find_generated_reports(project_root: Path) -> list[str]:
    findings: list[str] = []
    for child in sorted(project_root.iterdir()):
        if child.is_file() and any(child.name.startswith(prefix) for prefix in GENERATED_REPORT_PATTERNS):
            findings.append(child.name)
    return findings


def _find_large_route_files(project_root: Path) -> list[str]:
    route_files: list[tuple[int, str]] = []
    app_root = project_root / 'app'
    if not app_root.exists():
        return []
    for path in app_root.rglob('*routes*.py'):
        if path.is_file():
            size = path.stat().st_size
            if size >= LARGE_ROUTE_THRESHOLD:
                route_files.append((size, str(path.relative_to(project_root))))
    route_files.sort(reverse=True)
    return [f"{rel} ({size} bytes)" for size, rel in route_files[:10]]


def _find_root_model_duplicates(project_root: Path) -> list[str]:
    candidates = []
    for rel in [
        'education_models.py',
        'app/education_models.py',
        'app/repository_models.py',
        'app/strategy_models.py',
        'app/models.py',
    ]:
        if _exists(project_root, rel):
            candidates.append(rel)
    return candidates


def build_architecture_consolidation_report(project_root: Path) -> list[ConsolidationItem]:
    items: list[ConsolidationItem] = []

    model_package_exists = (project_root / 'app' / 'models').exists()
    monolith_model_exists = _exists(project_root, 'app/models.py')
    if model_package_exists and monolith_model_exists:
        items.append(ConsolidationItem(
            name='Model katmanı çift yapısı',
            area='architecture',
            status='needs_attention',
            evidence='app/models.py ve app/models/ aynı anda mevcut',
            risk='Yüksek',
            note='Tek kaynak model omurgası belirlenmeli; importlar buna göre sabitlenmeli.',
        ))
    else:
        items.append(ConsolidationItem(
            name='Model katmanı tek kaynak kontrolü',
            area='architecture',
            status='ready',
            evidence='Model kaynakları tek omurgada toplanmış görünüyor',
            risk='Düşük',
            note='Model katmanında fazladan paralel kaynak görünmüyor.',
        ))

    perf_variants = [rel for rel in ['app/services/performance_service.py','app/services/performance','app/services/performance_v2'] if _exists(project_root, rel)]
    items.append(ConsolidationItem(
        name='Performans servis varyantları',
        area='services',
        status='needs_attention' if len(perf_variants) > 1 else 'ready',
        evidence=', '.join(perf_variants) if perf_variants else 'Performans servisi bulunamadı',
        risk='Orta' if len(perf_variants) > 1 else 'Düşük',
        note='Tek “esas” performans servis hattı belirlenmeli ve yeni geliştirme oraya sabitlenmeli.' if len(perf_variants) > 1 else 'Performans servis hattı tekil görünüyor.',
    ))

    large_routes = _find_large_route_files(project_root)
    items.append(ConsolidationItem(
        name='Büyük route dosyaları',
        area='routes',
        status='needs_attention' if large_routes else 'ready',
        evidence='; '.join(large_routes) if large_routes else '50 KB üstü route dosyası bulunmadı',
        risk='Orta' if large_routes else 'Düşük',
        note='Canlı öncesi bir tur daha domain bazlı route küçültme yapılmalı.' if large_routes else 'Route katmanı boyut olarak dengeli görünüyor.',
    ))

    root_duplicates = _find_root_model_duplicates(project_root)
    items.append(ConsolidationItem(
        name='Kök model artık dosyaları',
        area='cleanup',
        status='needs_attention' if len(root_duplicates) > 2 else 'ready',
        evidence=', '.join(root_duplicates) if root_duplicates else 'Ek model artık dosyası bulunmadı',
        risk='Orta' if len(root_duplicates) > 2 else 'Düşük',
        note='app/models/ altı esas alınacaksa kökte ve app altında kalan eski model dosyaları tasfiye edilmeli.' if len(root_duplicates) > 2 else 'Model dosyalarında belirgin artık görünmüyor.',
    ))

    blockers = [rel for rel in ['.venv','.pytest_cache','.env','logs','uploads'] if _exists(project_root, rel)]
    generated_reports = _find_generated_reports(project_root)
    evidence = ', '.join(blockers + generated_reports[:8]) if (blockers or generated_reports) else 'Paket hijyeni temiz görünüyor'
    items.append(ConsolidationItem(
        name='Paket hijyeni',
        area='release',
        status='needs_attention' if blockers or generated_reports else 'ready',
        evidence=evidence,
        risk='Kritik' if blockers else ('Orta' if generated_reports else 'Düşük'),
        note='Temiz release paketinde sanal ortam, .env, log, upload ve üretilmiş raporlar yer almamalı.' if blockers or generated_reports else 'Temiz paket için belirgin gürültü yok.',
    ))

    migration_versions = _glob_count(project_root, 'migrations/versions/*.py')
    items.append(ConsolidationItem(
        name='Migration omurgası',
        area='database',
        status='ready' if migration_versions > 0 and _exists(project_root, 'migrations/env.py') else 'needs_attention',
        evidence=f"migrations/env.py={_exists(project_root, 'migrations/env.py')}, version_count={migration_versions}",
        risk='Kritik' if migration_versions == 0 else 'Düşük',
        note='Canlıya geçişte şema farkları migration ile yönetilmeli; SQL script birikimi tek başına yeterli değil.' if migration_versions == 0 else 'Migration ağacı mevcut, baseline ve son revizyonlar ayrıca kontrol edilmeli.',
    ))

    quality_tests = [rel for rel in ['tests/test_security_headers.py','tests/test_security_audit.py','tests/test_upload_validation.py'] if _exists(project_root, rel)]
    performance_tests = [rel for rel in ['tests/test_performance_assignment.py','tests/test_performance_chain.py','tests/test_leave_delegation.py','tests/test_publish_gate.py'] if _exists(project_root, rel)]
    evidence = 'mevcut kritik testler: ' + (', '.join(quality_tests + performance_tests) if (quality_tests or performance_tests) else 'yok')
    items.append(ConsolidationItem(
        name='Kritik akış test kapsaması',
        area='quality',
        status='needs_attention' if len(performance_tests) < 2 else 'ready',
        evidence=evidence,
        risk='Yüksek' if len(performance_tests) < 2 else 'Düşük',
        note='Özellikle görev üretimi, amir zinciri, 50/50/0, yayın kilidi ve izin-vekalet akışları testlenmeli.' if len(performance_tests) < 2 else 'Kritik akış testleri kabul edilebilir düzeye yaklaşmış.',
    ))

    return items


def build_release_gate(project_root: Path) -> dict[str, Any]:
    items = build_architecture_consolidation_report(project_root)
    open_critical = sum(1 for item in items if item.risk == 'Kritik' and item.status != 'ready')
    open_attention = sum(1 for item in items if item.status != 'ready')
    return {
        'project_root': str(project_root),
        'open_critical': open_critical,
        'open_attention': open_attention,
        'go_live_recommended': open_critical == 0 and open_attention <= 2,
        'items': [item.to_dict() for item in items],
    }