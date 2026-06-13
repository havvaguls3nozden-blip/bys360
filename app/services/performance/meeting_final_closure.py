# -*- coding: utf-8 -*-

"""BYS360 Toplantı İstekleri Final Kapanış Gate servisi."""
from __future__ import annotations

from pathlib import Path
from typing import Any

FINAL_CLOSURE_VERSION = '2026-04-30-meeting-final-closure-gate'
ROOT = Path(__file__).resolve().parents[3]

FINAL_REQUIRED_GATES = [
    'check_performance_meeting_development_overlay.py',
    'check_performance_meeting_development_faz2.py',
    'check_performance_meeting_development_faz3.py',
    'check_performance_meeting_development_faz4.py',
    'check_performance_meeting_rule_import_fix.py',
    'check_performance_meeting_rule_enforcement.py',
    'check_performance_meeting_p0_completion.py',
    'check_performance_meeting_p1_faz7.py',
    'check_performance_meeting_p2_faz8.py',
    'check_performance_meeting_p3_faz9.py',
    'check_performance_meeting_p4_faz10.py',
    'check_performance_meeting_final_closure.py',
]

FINAL_CLOSURE_P0_ITEMS = [
    '70 altı Başkan onayı ve genel açıklama kuralı',
    '1 ve 5 puan açıklama zorunluluğunun sistem ayarına bağlanması',
    'Personel/grup kategorileri',
    'Koordinatör ve Grup Başkanı kapsam görünürlüğü',
    'Personelin kendi karnesi ve kişi detayı olmayan kendi grup/kategori ortalaması',
    '10 senaryolu P0 gate kontrolü',
]

FINAL_CLOSURE_P1_ITEMS = [
    '3. amir sütununun opsiyonel görünürlüğü',
    '3. amir yorum/puan görev dili ayrımı',
    'Karne okunabilirliği ve teknik dil hijyeni',
    'Birden fazla dönem ve kapsam tipi altyapısı',
    'Dönem kapsam etiketi ve seçilmiş personel/kategori kapsamı',
    'Otomatik hatırlatma ve aksatan amir bildirim altyapısı',
]

FINAL_CLOSURE_P2_ITEMS = [
    'Geçmiş yıl karne/puan arşivi',
    'Ara dönem performans notları',
    'Ara notların puanlama sırasında hatırlatılması ve otomatik puan üretmemesi',
    'Performans içinde gelişim önerisi altyapısı',
    'Sanal asistan rehber bağlantısı',
    'AI karar destek sınırlarının güvenli şekilde çizilmesi',
]

FINAL_FORBIDDEN_UI_TERMS = ['Faz 3 senkronu', 'phase sync', 'workflow state', 'scorecard_pending', 'president_pending', 'blocked_president_pending']

FINAL_REQUIRED_FILES = [
    'app/performance/meeting_development_routes.py',
    'app/performance/meeting_test_routes.py',
    'app/performance/meeting_development_faz3_routes.py',
    'app/performance/meeting_development_faz4_routes.py',
    'app/performance/meeting_rule_enforcement_routes.py',
    'app/performance/meeting_p0_completion_routes.py',
    'app/performance/meeting_p1_scope_routes.py',
    'app/performance/meeting_p2_archive_notes_routes.py',
    'app/performance/meeting_p3_reminders_routes.py',
    'app/performance/meeting_p4_development_guidance_routes.py',
    'app/performance/meeting_final_closure_routes.py',
    'app/services/performance/meeting_final_closure.py',
    'app/templates/performance/meeting_final_closure.html',
]

FINAL_MENU_KEYS = [
    'performance_meeting_development', 'performance_meeting_test_scenarios', 'performance_meeting_development_faz3',
    'performance_meeting_final_gate', 'performance_meeting_rule_enforcement', 'performance_meeting_p0_completion',
    'performance_meeting_p1_scope', 'performance_meeting_p2_archive_notes', 'performance_meeting_p3_reminders',
    'performance_meeting_p4_development_guidance', 'performance_meeting_final_closure',
]

FINAL_BASE_KEYS = [
    'meeting-development', 'meeting-development-tests', 'meeting-development-faz3', 'meeting-development-final-gate',
    'meeting-development-rules', 'meeting-development-p0', 'meeting-development-p1', 'meeting-development-p2',
    'meeting-development-faz9', 'meeting-development-faz10', 'meeting-development-final-closure',
]


def _read(rel: str) -> str:
    path = ROOT / rel
    if not path.exists():
        return ''
    for enc in ('utf-8', 'utf-8-sig', 'cp1254'):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            __import__("logging").getLogger(__name__).exception("BYS360 kalite denetimi: except bloğu loglandı (app/services/performance/meeting_final_closure.py:93)")
            continue
    return path.read_text(encoding='utf-8', errors='ignore')


def _exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def final_closure_checks() -> list[dict[str, Any]]:
    run_all = _read('scripts/run_performance_meeting_development_all_gates.py')
    menu_text = _read('app/menu_registry.py')
    base_text = _read('app/templates/base.html')
    init_text = _read('app/performance/__init__.py')
    checks: list[dict[str, Any]] = []
    for rel in FINAL_REQUIRED_FILES:
        checks.append({'group': 'Dosya', 'title': rel, 'ok': _exists(rel), 'detail': 'Dosya mevcut' if _exists(rel) else 'Dosya eksik'})
    for gate in FINAL_REQUIRED_GATES:
        checks.append({'group': 'Gate Zinciri', 'title': gate, 'ok': gate in run_all and _exists('scripts/' + gate), 'detail': 'Zincirde ve dosyada mevcut' if gate in run_all and _exists('scripts/' + gate) else 'Gate zinciri veya dosyası eksik'})
    for key in FINAL_MENU_KEYS:
        checks.append({'group': 'Menü Registry', 'title': key, 'ok': key in menu_text, 'detail': 'Menü registry kaydı var' if key in menu_text else 'Menü registry kaydı eksik'})
    for key in FINAL_BASE_KEYS:
        checks.append({'group': 'Sol Menü', 'title': key, 'ok': key in base_text, 'detail': 'Sol menü işareti var' if key in base_text else 'Sol menü işareti eksik'})
    checks.append({'group': 'Route Import', 'title': 'BYS360_MEETING_FINAL_CLOSURE_ROUTES_IMPORT', 'ok': 'BYS360_MEETING_FINAL_CLOSURE_ROUTES_IMPORT' in init_text, 'detail': 'Final kapanış route import kaydı var' if 'BYS360_MEETING_FINAL_CLOSURE_ROUTES_IMPORT' in init_text else 'Final kapanış route import kaydı eksik'})
    for rel in ['app/templates/performance/meeting_final_closure.html','app/templates/performance/meeting_p4_development_guidance.html','app/templates/performance/meeting_p3_reminders.html','app/templates/performance/meeting_p2_archive_notes.html','app/templates/performance/meeting_p1_scope.html','app/templates/performance/meeting_p0_completion.html','app/templates/performance/meeting_rule_enforcement.html']:
        text = _read(rel)
        leaked = [term for term in FINAL_FORBIDDEN_UI_TERMS if term in text]
        checks.append({'group': 'Teknik Dil Hijyeni', 'title': rel, 'ok': not leaked, 'detail': 'Teknik ifade sızıntısı yok' if not leaked else 'Sızan ifadeler: ' + ', '.join(leaked)})
    return checks


def final_closure_summary() -> dict[str, Any]:
    checks = final_closure_checks()
    total = len(checks)
    ok_count = sum(1 for item in checks if item['ok'])
    return {'total': total, 'ok_count': ok_count, 'missing_count': total - ok_count, 'ok': ok_count == total}


def build_final_closure_context(viewer: Any | None = None) -> dict[str, Any]:
    checks = final_closure_checks()
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in checks:
        grouped.setdefault(item['group'], []).append(item)
    return {
        'title': 'Toplantı İstekleri Final Kapanış Gate', 'version': FINAL_CLOSURE_VERSION,
        'summary': final_closure_summary(), 'groups': grouped,
        'p0_items': FINAL_CLOSURE_P0_ITEMS, 'p1_items': FINAL_CLOSURE_P1_ITEMS, 'p2_items': FINAL_CLOSURE_P2_ITEMS,
        'viewer': viewer,
    }


def run_final_closure_check() -> dict[str, Any]:
    checks = final_closure_checks()
    missing = [f"{item['group']} | {item['title']} | {item['detail']}" for item in checks if not item['ok']]
    ok = not missing
    return {'ok': ok, 'message': 'Toplantı istekleri final kapanış kontrolleri tamam.' if ok else 'Toplantı istekleri final kapanış kontrollerinde eksik var.', 'missing': missing, 'summary': final_closure_summary()}
