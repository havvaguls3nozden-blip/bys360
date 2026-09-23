"""Phase 12A route/endpoint conflict runtime contract.

Bu test, `tests/quality/test_app_factory_registers_routes_without_duplicate_endpoints.py`
testinin YAKALAYAMADIĞI bir sınıf hatayı kapatır: aynı URL rule'una, aynı (veya
kesişen) HTTP method ile, FARKLI endpoint adlarının bağlanması. Mevcut duplicate
testi yalnızca (endpoint, rule, methods) üçlüsü birebir aynıysa yakalar; endpoint
adı farklıysa (bizim asıl senaryomuz) sessizce geçer.

Bu dosya iki şeyi kilitler:
1. Runtime `app.url_map`'te bulunan gerçek overlapping-method çakışmalarının seti,
   aşağıdaki insan-tarafından-incelenmiş KNOWN_CONFLICTS baseline'ı ile TAM
   eşleşmeli (ne yeni bir çakışma, ne de sessizce "iyileşmiş" bir çakışma; ikisi
   de kasıtlı, incelenmiş bir baseline güncellemesi gerektirir).
2. Her bilinen çakışmada HANGİ endpoint'in kazandığı (Werkzeug insertion-order
   tie-break) sabit kalmalı. Kazananın sessizce değişmesi (ör. bir import sırası
   refactor'ünde) CI'da FAIL üretmeli — Phase 12A denetiminde tespit edilen en
   kritik risk budur.

Yeni bir çakışma bulunması BAŞARISIZLIK değildir; incelenmesi ve KNOWN_CONFLICTS'e
bilinçli olarak eklenmesi (veya kaynağın düzeltilmesi) gerektiği anlamına gelir.
Bu dosya hiçbir route'u değiştirmez, hiçbir POST çalıştırmaz.
"""
from __future__ import annotations

import re
from collections import defaultdict
from typing import TypedDict

import pytest

pytestmark = pytest.mark.ci_safe

_AUTOMATIC_METHODS = {"HEAD", "OPTIONS"}

_CONVERTER_SAMPLES = {
    "int": "1",
    "float": "1.5",
    "uuid": "00000000-0000-0000-0000-000000000000",
    "path": "x",
    "string": "x",
    "default": "x",
}
_DYNAMIC_SEGMENT_RE = re.compile(
    r"<(?:(?P<converter>[a-zA-Z_][a-zA-Z0-9_]*)(?:\([^)]*\))?:)?(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)>"
)

class _KnownConflict(TypedDict):
    methods: list[str]
    endpoints: list[str]
    winners: dict[str, str]
    note: str


# BYS360_PHASE12A_ROUTE_CONFLICT_KNOWN_BASELINE_START
# İnsan tarafından incelenmiş, gerekçeli ratchet. Otomatik yükseltilmez.
# Her girdi Phase 12A (Koordinatör + 3 ajan) tarafından runtime `app.url_map`
# + `MapAdapter.match()` ile bağımsız doğrulandı (3/3 ajan aynı sonucu üretti).
KNOWN_CONFLICTS: dict[str, _KnownConflict] = {
    # BYS360 DEFECT AQ: /performans/baskan-onaylari kaydı burada kapatıldı --
    # app/performance/president_low_score_card_routes.py'nin bu URL için
    # kendi route kaydı kaldırıldı (fonksiyon ve yardımcıları korunarak),
    # çünkü zaten hiçbir HTTP isteğinde seçilmiyordu. Artık bu URL için tek
    # endpoint (main.performance_president_approvals) kayıtlı, bu yüzden
    # aşağıdaki dedektör bu URL'yi çakışma olarak görmüyor -- bilinçli
    # baseline güncellemesi.
    "/performans/baskan-onaylari/<int:approval_id>/karne": {
        "methods": ["GET"],
        "endpoints": [
            "main.performance_president_approval_scorecard",
            "main.performance_president_card_review",
            "main.president_low_score_report_card",
        ],
        "winners": {"GET": "main.performance_president_approval_scorecard"},
        "note": (
            "app/performance/president_approval_card_routes.py:19 kazanıyor (çekirdek import "
            "listesinde process_engine_phase6_president_approvals_routes'tan önce). Kazanan "
            "handler'da 70-altı skor filtre kapısı YOK; kısmen gölgelenen "
            "main.performance_president_card_review'da (hâlâ /performance/president-approvals/"
            "<id>/card alias'ı üzerinden canlı) bu kapı VAR -> gerçek iş kuralı farkı, ürün "
            "kararı olmadan konsolide edilmez (Durum C/F)."
        ),
    },
    "/performance/president-approvals/<int:approval_id>/scorecard": {
        "methods": ["GET"],
        "endpoints": [
            "main.performance_president_approval_scorecard",
            "main.performance_president_card_review",
        ],
        "winners": {"GET": "main.performance_president_approval_scorecard"},
        "note": "Yukarıdaki karne çakışmasıyla aynı kök neden ve aynı iş-kuralı farkı.",
    },
    "/performans/stratejik/kpi-dashboard": {
        "methods": ["GET"],
        "endpoints": ["main.sp1_kpi_dashboard_tr", "strategic_performance.kpi_dashboard"],
        "winners": {"GET": "main.sp1_kpi_dashboard_tr"},
        "note": (
            "Phase 12B: DISTINCT_BUSINESS_FLOW. main winner sabit performance_targets/SP1C "
            "pipeline'ını, shadowed handler dinamik tablo/kolon, aktiflik, ağırlıklı başarı "
            "ve risk grupları içeren SP3A pipeline'ını kullanır. Aynı template'e farklı veri "
            "sözleşmeleri verirler; ürün sahipliği kararı olmadan silinemez veya birleştirilemez."
        ),
    },
    "/performans/stratejik/hedefler": {
        "methods": ["GET"],
        "endpoints": ["main.sp1_kpi_targets_tr", "strategic_performance.target_list"],
        "winners": {"GET": "main.sp1_kpi_targets_tr"},
        "note": (
            "Phase 12B: ROUTE_OWNERSHIP_AMBIGUOUS. İki handler aynı liste servisini kullanır "
            "ancak main safe_render, strategic doğrudan render uygular; template create/edit "
            "bağlantıları strategic endpoint'lerine giderken liste request'ini main kazanır."
        ),
    },
    "/performans/stratejik/yetkinlik-kutuphanesi": {
        "methods": ["GET"],
        "endpoints": ["main.sp1_competency_library_tr", "strategic_performance.competency_library"],
        "winners": {"GET": "main.sp1_competency_library_tr"},
        "note": (
            "Phase 12B: SHADOWED_BUT_NOT_SAFE_TO_REMOVE. Ortak guard/template'e rağmen "
            "safe_render ve doğrudan render hata davranışları farklıdır; menü ayrıca shadowed "
            "strategic endpoint adını referans eder."
        ),
    },
    "/performans/stratejik/oz-degerlendirme": {
        "methods": ["GET", "POST"],
        "endpoints": ["main.sp1_self_review_tr", "strategic_performance.self_review"],
        "winners": {"GET": "main.sp1_self_review_tr", "POST": "main.sp1_self_review_tr"},
        "note": (
            "Phase 12B: SHADOWED_BUT_NOT_SAFE_TO_REMOVE. POST gövdeleri kayıt yapmasa da "
            "main İngilizce /performance/self-review alias'ına, strategic Türkçe endpoint'e "
            "redirect eder; render hata davranışları da farklıdır."
        ),
    },
    "/performans/stratejik/ai-kpi-analiz": {
        "methods": ["GET"],
        "endpoints": ["main.sp1_ai_kpi_analysis_tr", "strategic_performance.ai_kpi_analysis"],
        "winners": {"GET": "main.sp1_ai_kpi_analysis_tr"},
        "note": (
            "Phase 12B: LEGACY_ALIAS. /ai-kpi-analiz kaydını main kazanır; aynı strategic "
            "handler /performans/stratejik/kpi-analiz üzerinden canlıdır. AI/deep-link "
            "kaynakları iki URL'yi de kullandığı için alias ürün kararı olmadan kaldırılamaz."
        ),
    },
    "/manifest.webmanifest": {
        "methods": ["GET"],
        "endpoints": ["main.bys360_pwa_manifest", "pwa.manifest_webmanifest"],
        "winners": {"GET": "main.bys360_pwa_manifest"},
        "note": (
            "Phase 12B: MANIFEST_CONTRACTS_DIFFER. Mevcut dosyada gövde, status, MIME ve "
            "cache-control eşittir; ham Pragma/X-Content-Type-Options, ETag/path çözümleme ve "
            "eksik dosyada main=404, pwa=fallback-200 davranışları farklıdır. main winner "
            "response kontratı kilitlenmeden registration silinemez."
        ),
    },
}
# BYS360_PHASE12A_ROUTE_CONFLICT_KNOWN_BASELINE_END


def _normalize_methods(methods) -> frozenset[str]:
    return frozenset((methods or set()) - _AUTOMATIC_METHODS)


def _sample_path_for_rule(rule_string: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        converter = match.group("converter") or "default"
        return _CONVERTER_SAMPLES.get(converter, "x")

    return _DYNAMIC_SEGMENT_RE.sub(_replace, rule_string)


def _collect_rule_groups(rules) -> dict[str, list[tuple[str, frozenset[str]]]]:
    """rule.rule -> [(endpoint, normalized_methods), ...] (her Rule nesnesi için bir giriş)."""
    groups: dict[str, list[tuple[str, frozenset[str]]]] = defaultdict(list)
    for rule_string, endpoint, methods in rules:
        groups[rule_string].append((endpoint, _normalize_methods(methods)))
    return groups


def _find_overlapping_conflicts(
    groups: dict[str, list[tuple[str, frozenset[str]]]],
) -> dict[str, dict[str, list[str]]]:
    """Aynı URL + kesişen method + FARKLI endpoint gruplarını döndürür.

    Disjoint method'lu (ör. GET vs POST, ortak method yok) veya tek-endpoint'li
    (alias) gruplar dahil edilmez.
    """
    conflicts: dict[str, dict[str, list[str]]] = {}
    for rule_string, entries in groups.items():
        per_endpoint_methods: dict[str, set[str]] = defaultdict(set)
        for endpoint, methods in entries:
            per_endpoint_methods[endpoint] |= methods

        if len(per_endpoint_methods) < 2:
            continue

        endpoint_items = list(per_endpoint_methods.items())
        overlapping_methods: set[str] = set()
        for i in range(len(endpoint_items)):
            for j in range(i + 1, len(endpoint_items)):
                overlapping_methods |= endpoint_items[i][1] & endpoint_items[j][1]

        if overlapping_methods:
            conflicts[rule_string] = {
                "methods": sorted(overlapping_methods),
                "endpoints": sorted(per_endpoint_methods),
            }
    return conflicts


@pytest.fixture(scope="module")
def runtime_app():
    from app import create_app

    return create_app()


@pytest.fixture(scope="module")
def runtime_rules(runtime_app):
    return [
        (rule.rule, rule.endpoint, rule.methods) for rule in runtime_app.url_map.iter_rules()
    ]


@pytest.fixture(scope="module")
def runtime_conflicts(runtime_rules):
    return _find_overlapping_conflicts(_collect_rule_groups(runtime_rules))


def test_runtime_conflict_set_matches_reviewed_baseline(runtime_conflicts):
    actual_keys = set(runtime_conflicts)
    baseline_keys = set(KNOWN_CONFLICTS)
    missing = sorted(baseline_keys - actual_keys)
    added = sorted(actual_keys - baseline_keys)
    assert not missing and not added, {
        "message": (
            "Runtime route çakışma seti değişti. 'added_beyond_baseline' yeni/önceden "
            "bilinmeyen bir çakışmadır — kaynağı incele, import sırasını gözden geçir, "
            "kasıtlıysa KNOWN_CONFLICTS'e gerekçeli olarak ekle. 'missing_from_actual' "
            "bir çakışmanın kaybolduğunu (muhtemelen iyi haber) gösterir — kasıtlı bir "
            "düzeltme yapıldıysa KNOWN_CONFLICTS bilinçli olarak güncellenmelidir."
        ),
        "missing_from_actual": missing,
        "added_beyond_baseline": added,
    }


def test_runtime_conflict_shape_matches_reviewed_baseline(runtime_conflicts):
    mismatches = []
    for rule_string, expected in KNOWN_CONFLICTS.items():
        actual = runtime_conflicts.get(rule_string)
        if actual is None:
            continue  # üstteki set testi zaten bunu raporlayacak
        if actual["methods"] != list(expected["methods"]):
            mismatches.append({"rule": rule_string, "field": "methods", "expected": expected["methods"], "actual": actual["methods"]})
        if actual["endpoints"] != sorted(expected["endpoints"]):
            mismatches.append({"rule": rule_string, "field": "endpoints", "expected": sorted(expected["endpoints"]), "actual": actual["endpoints"]})
    assert not mismatches, mismatches


def test_known_conflict_winners_have_not_silently_changed(runtime_app):
    adapter = runtime_app.url_map.bind("localhost", url_scheme="http")
    drifted = []
    for rule_string, expected in KNOWN_CONFLICTS.items():
        path = _sample_path_for_rule(rule_string)
        for method, expected_winner in expected["winners"].items():
            try:
                endpoint, _view_args = adapter.match(path, method=method)
            except Exception as exc:  # NotFound/MethodNotAllowed/RequestRedirect
                drifted.append({"rule": rule_string, "method": method, "error": repr(exc)})
                continue
            if endpoint != expected_winner:
                drifted.append(
                    {
                        "rule": rule_string,
                        "method": method,
                        "expected_winner": expected_winner,
                        "actual_winner": endpoint,
                    }
                )
    assert not drifted, drifted


def test_sample_path_substitutes_dynamic_segments():
    assert _sample_path_for_rule("/performans/baskan-onaylari") == "/performans/baskan-onaylari"
    assert (
        _sample_path_for_rule("/performans/baskan-onaylari/<int:approval_id>/karne")
        == "/performans/baskan-onaylari/1/karne"
    )
    assert _sample_path_for_rule("/x/<name>/y") == "/x/x/y"


def test_detector_flags_exact_overlapping_conflict():
    rules = [
        ("/synthetic/dup", "main.synthetic_a", {"GET"}),
        ("/synthetic/dup", "main.synthetic_b", {"GET"}),
    ]
    conflicts = _find_overlapping_conflicts(_collect_rule_groups(rules))
    assert conflicts == {
        "/synthetic/dup": {"methods": ["GET"], "endpoints": ["main.synthetic_a", "main.synthetic_b"]}
    }


def test_detector_does_not_flag_disjoint_methods():
    rules = [
        ("/synthetic/split", "main.synthetic_get", {"GET"}),
        ("/synthetic/split", "main.synthetic_post", {"POST"}),
    ]
    conflicts = _find_overlapping_conflicts(_collect_rule_groups(rules))
    assert conflicts == {}


def test_detector_normalizes_automatic_head_and_options():
    rules = [
        ("/synthetic/get-only", "main.synthetic_get", {"GET", "HEAD", "OPTIONS"}),
    ]
    conflicts = _find_overlapping_conflicts(_collect_rule_groups(rules))
    assert conflicts == {}


def test_detector_does_not_flag_endpoint_alias():
    rules = [
        ("/synthetic/alias-a", "main.synthetic_shared", {"GET"}),
        ("/synthetic/alias-b", "main.synthetic_shared", {"GET"}),
    ]
    conflicts = _find_overlapping_conflicts(_collect_rule_groups(rules))
    assert conflicts == {}
