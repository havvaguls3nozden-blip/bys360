"""Davranışsal testler: app/services/performance/publish_preflight_rules.py.

Bu modül BYS360 performans karnesinin personele yayınlanmadan önce geçmesi
gereken gerçek iş kurallarının tek merkezidir (bkz. modülün kendi docstring'i:
"Yayın butonu, yayın paneli ve toplu yayın aynı kural sonucunu kullanmalıdır.").
9 doğrulanmış çağıran (assignments, chain_contract_gate, manager_rule_guard,
publish_guard, rule_matrix_final_gate, scoring_weight_gate, visibility_guard,
visibility_publication_gate, module_maturity) bu dosyanın kararına güvenir.

`tests/test_performance_publish_preflight_static.py` yalnızca kaynak metnini
substring ile tarar; hiçbir fonksiyonu import etmez/çağırmaz. Bu dosya onun
yerine gerçek genel API'yi (validate_evaluation_for_publish,
is_evaluation_publishable_strict, expected_publish_levels, is_completed_status,
is_president_exempt, PublishFinding/PublishPreflightResult) gerçek/gerçekçi
SimpleNamespace girdileriyle çağırır ve dönen karar nesnesini doğrular.

Not: `validate_evaluation_for_publish`, personel-destek ön onayı ve düşük puan
Başkan onayı için ayrı iki servis modülünü çağırır; her ikisi de canlıda
DB/Flask bağlamı gerektirir ama DB yokken kasıtlı olarak güvenli/deterministik
bir düşüşle (fallback) çalışır (bkz. o servislerdeki `try/except` blokları).
Bu dosyadaki testlerin büyük çoğunluğu bu gerçek düşüş davranışını olduğu gibi
kullanır; yalnızca gerçek DB'ye bağlı SON onay kapısını (personel-destek ön
onayı) simüle etmek gereken birkaç testte, o TEK dış sınır fonksiyonu
`monkeypatch` ile kontrol edilir — test edilen `publish_preflight_rules`
modülünün kendisi hiçbir yerde mock'lanmaz.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import app.services.performance.publish_preflight_rules as ppr

# ---------------------------------------------------------------------------
# Fixtures / factories
# ---------------------------------------------------------------------------


def _period(**overrides: Any) -> SimpleNamespace:
    base: dict[str, Any] = {
        "enable_level_3": False,
        "enable_level_3_scoring": False,
        "level_3_mode": "",
        "require_level_3_completion_for_final": False,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _item(**overrides: Any) -> SimpleNamespace:
    base: dict[str, Any] = {
        "manager_level": 1,
        "criteria_id": 1,
        "score": 3,
        "justification": "Yeterli açıklama metni",
        "comment": "",
        "strength_note": "",
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _evaluation(**overrides: Any) -> SimpleNamespace:
    """'Temiz' bir değerlendirme: tek amir (1. amir) atanmış, tamamlanmış,
    açıklamalı tek kriterli, 70-90 bandında (genel görüş zorunlu değil).

    Testler yalnızca ilgilendikleri alanı override ederek belirli bir kural
    dalını izole eder.
    """
    base: dict[str, Any] = {
        "id": 8181,
        "period_id": 1,
        "employee_id": 1,
        "status": "tamamlandi",
        "employee": SimpleNamespace(role="personel"),
        "final_total_100": 82.0,
        "level_1_evaluator_id": 501,
        "level_2_evaluator_id": None,
        "level_3_evaluator_id": None,
        "level_1_completed": True,
        "level_2_completed": False,
        "level_3_completed": False,
        "level_1_general_comment": "",
        "level_2_general_comment": "",
        "level_3_general_comment": "",
        "items": [_item()],
    }
    base.update(overrides)
    return SimpleNamespace(**base)


def _codes(result: ppr.PublishPreflightResult) -> list[str]:
    return [item.code for item in result.blockers]


# ---------------------------------------------------------------------------
# Yapısal kapılar: eksik veri, Başkan istisnası, tamamlanmamış durum
# ---------------------------------------------------------------------------


def test_missing_evaluation_blocks_with_dedicated_reason():
    result = ppr.validate_evaluation_for_publish(_period(), None)
    assert result.ok is False
    assert result.reason == "Değerlendirme bulunamadı."
    assert _codes(result) == ["missing_evaluation"]


def test_missing_period_blocks_with_dedicated_reason():
    result = ppr.validate_evaluation_for_publish(None, _evaluation())
    assert result.ok is False
    assert result.reason == "Değerlendirme dönemi bulunamadı."
    assert _codes(result) == ["missing_period"]


def test_president_is_exempt_yields_not_ok_but_no_blockers_only_info():
    # Başkan karnesi normal personel yayın akışına hiç girmez. ok=False
    # olmasına rağmen bu bir "blokaj" değildir: blockers boş kalır, yalnızca
    # info seviyesinde president_exempt kaydı düşer ve reason boş string olur.
    evaluation = _evaluation(employee=SimpleNamespace(role="baskan"))
    result = ppr.validate_evaluation_for_publish(_period(), evaluation)
    assert result.ok is False
    assert result.reason == ""
    assert result.blockers == []
    assert [info.code for info in result.infos] == ["president_exempt"]
    assert result.infos[0].severity == "info"


def test_not_completed_status_blocks_publish():
    evaluation = _evaluation(status="draft")
    result = ppr.validate_evaluation_for_publish(_period(), evaluation)
    assert result.ok is False
    assert _codes(result) == ["not_completed"]
    assert result.reason == "Değerlendirme tamamlanmadığı için yayınlanamaz."


# ---------------------------------------------------------------------------
# Amir zinciri: eksik seviyeler, işlem sırası (3 -> 2 -> 1)
# ---------------------------------------------------------------------------


def test_single_missing_manager_level_reports_specific_code_and_level():
    evaluation = _evaluation(level_1_completed=False)
    result = ppr.validate_evaluation_for_publish(_period(), evaluation)
    assert _codes(result) == ["level_1_missing"]
    blocker = result.blockers[0]
    assert blocker.manager_level == 1
    assert blocker.message == "1. amir değerlendirmesi tamamlanmadan yayınlanamaz."
    assert result.reason == blocker.message


def test_multiple_missing_manager_levels_get_combined_plus_individual_blockers():
    # 1. ve 2. amir atanmış ama ikisi de tamamlanmamış. Blokaj mesajı işlem
    # sırasına (3 -> 2 -> 1) göre "2. amir, 1. amir" sırasıyla üretilmeli;
    # yanlışlıkla yalnızca 1. amir gösterilmemeli.
    evaluation = _evaluation(
        level_1_completed=False,
        level_2_evaluator_id=502,
        level_2_completed=False,
    )
    result = ppr.validate_evaluation_for_publish(_period(), evaluation)
    assert _codes(result) == ["manager_steps_missing", "level_2_missing", "level_1_missing"]
    combined = result.blockers[0]
    assert combined.message == (
        "Yayın için eksik amir değerlendirmesi var: 2. amir, 1. amir. "
        "Eksik değerlendirmeler tamamlanmadan personele yayın açılamaz."
    )
    assert [b.manager_level for b in result.blockers[1:]] == [2, 1]


def test_level_3_comment_only_mode_requires_a_comment_when_completed():
    # Dönemde 3. amir yorum modunda (enable_level_3=True, scoring=False).
    # 3. amir tamamlanmış ama ne genel görüş ne de kriter satırı notu var ->
    # puan değil, görüş/yorum eksikliği ayrı bir kodla bloklanmalı.
    period = _period(enable_level_3=True, enable_level_3_scoring=False)
    evaluation = _evaluation(
        level_3_evaluator_id=503,
        level_3_completed=True,
        level_3_general_comment="",
    )
    result = ppr.validate_evaluation_for_publish(period, evaluation)
    assert _codes(result) == ["level_3_comment_required"]
    blocker = result.blockers[0]
    assert blocker.manager_level == 3
    assert blocker.message == "3. amir yorum modunda olduğu için görüş alanı boş bırakılamaz."


def test_completed_level_without_any_score_item_blocks_publish():
    evaluation = _evaluation(items=[])
    result = ppr.validate_evaluation_for_publish(_period(), evaluation)
    assert _codes(result) == ["missing_score_items"]
    blocker = result.blockers[0]
    assert blocker.manager_level == 1
    assert blocker.message == "1. amir için kriter puanı bulunamadı."


def test_level_3_scoring_mode_requires_a_score_item_not_just_completion():
    # Dönemde 3. amir PUAN modunda (enable_level_3_scoring=True). Modülün
    # kendi anayasası: "3. amir puan modundaysa puan adımı tamamlanması
    # aranır." -> yorum modundan farklı olarak kriter satırı şartından muaf
    # DEĞİLDİR; tamamlanmış ama satırsız 3. amir de bloklanmalı.
    period = _period(enable_level_3_scoring=True)
    evaluation = _evaluation(level_3_evaluator_id=503, level_3_completed=True)
    result = ppr.validate_evaluation_for_publish(period, evaluation)
    assert _codes(result) == ["missing_score_items"]
    blocker = result.blockers[0]
    assert blocker.manager_level == 3
    assert blocker.message == "3. amir için kriter puanı bulunamadı."


def test_level_3_comment_only_entirely_missing_uses_distinct_code_and_message():
    # 3. amir yorum modunda hiç tamamlanmamışsa (sadece boş bırakılmamışsa),
    # genel "level_3_missing" değil, özel "level_3_comment_missing" kodu ve
    # "görüş" diliyle yazılmış farklı bir mesaj üretilmeli.
    period = _period(enable_level_3=True, enable_level_3_scoring=False)
    evaluation = _evaluation(level_3_evaluator_id=503, level_3_completed=False)
    result = ppr.validate_evaluation_for_publish(period, evaluation)
    assert _codes(result) == ["level_3_comment_missing"]
    blocker = result.blockers[0]
    assert blocker.manager_level == 3
    assert blocker.message == "3. amir görüşü tamamlanmadan yayınlanamaz."


# ---------------------------------------------------------------------------
# Kriter satırı: 1/5 uç puan açıklama zorunluluğu
# ---------------------------------------------------------------------------


def test_extreme_scores_require_explanation_only_when_actually_missing():
    # Aynı değerlendirmede iki kriter satırı: biri 1 puan ve açıklamasız
    # (bloklanmalı), diğeri 5 puan ama gerekçeli (bloklanmamalı). Kural yalnızca
    # gerçekten eksik olan satırı işaretlemeli.
    evaluation = _evaluation(
        items=[
            _item(criteria_id=101, score=1, justification="", comment="", strength_note=""),
            _item(criteria_id=102, score=5, justification="Gerekçeli açıklama metni"),
        ]
    )
    result = ppr.validate_evaluation_for_publish(_period(), evaluation)
    assert _codes(result) == ["extreme_score_explanation_required"]
    blocker = result.blockers[0]
    assert blocker.criteria_id == 101
    assert blocker.manager_level == 1


# ---------------------------------------------------------------------------
# Nihai puan eşikleri: 70 altı / 90 üstü genel görüş ve düşük puan süreci
# ---------------------------------------------------------------------------


def test_high_score_above_90_requires_general_comment():
    evaluation = _evaluation(final_total_100=95.0)
    result = ppr.validate_evaluation_for_publish(_period(), evaluation)
    assert _codes(result) == ["high_score_general_comment_required"]
    assert result.blockers[0].message == "90 üstü sonuçlarda ayrıntılı genel görüş zorunludur."


def test_low_score_below_70_stacks_general_comment_and_president_approval_blockers():
    # 70 altı sonuç, ayrıntılı genel görüş VE Başkan/Üst Onay şartını aynı anda
    # tetikler (modül docstring'inin vurguladığı iki ayrı kilit kural).
    evaluation = _evaluation(final_total_100=40.0)
    result = ppr.validate_evaluation_for_publish(_period(), evaluation)
    assert _codes(result) == [
        "low_score_general_comment_required",
        "low_score_president_approval_required",
    ]
    assert result.reason == "70 altı sonuçlarda ayrıntılı genel görüş zorunludur."
    president_blocker = result.blockers[1]
    assert president_blocker.message == (
        "Başkan onayı bekliyor. Başkan/Üst Onay tamamlanmadan 70 altı karne "
        "yayınlanamaz. Başkan/Üst Onay Yayın Kilidi"
    )


def test_period_requiring_level_3_completion_flags_missing_chain():
    period_requiring = _period(require_level_3_completion_for_final=True)
    period_not_requiring = _period(require_level_3_completion_for_final=False)
    evaluation = _evaluation()  # yalnızca 1. amir atanmış, 3. amir zinciri yok

    with_requirement = ppr.validate_evaluation_for_publish(period_requiring, evaluation)
    without_requirement = ppr.validate_evaluation_for_publish(period_not_requiring, evaluation)

    assert "period_requires_level_3" in _codes(with_requirement)
    assert "period_requires_level_3" not in _codes(without_requirement)


# ---------------------------------------------------------------------------
# Saf yardımcı fonksiyonlar: expected_publish_levels / durum kontrolleri
# ---------------------------------------------------------------------------


def test_expected_publish_levels_and_basic_status_helpers():
    exempt_employee = SimpleNamespace(role="baskan")
    regular_employee = SimpleNamespace(role="personel")

    # Kimseye amir ataması yapılmamış ve Başkan istisnası da yoksa savunmacı
    # varsayımla en az 1. amir beklenir.
    assert ppr.expected_publish_levels(_period(), SimpleNamespace(employee=regular_employee)) == (1,)

    # Yalnızca 1. ve 3. amir atanmışsa 2. amir gereksiz yere beklenmez
    # (tek/çift amirli istisnaların korunması).
    assigned = SimpleNamespace(employee=regular_employee, level_1_evaluator_id=501, level_3_evaluator_id=503)
    assert ppr.expected_publish_levels(_period(), assigned) == (1, 3)

    # Başkan istisnasında hiç amir ataması yoksa boş zincir üretilir.
    exempt = SimpleNamespace(employee=exempt_employee)
    assert ppr.expected_publish_levels(_period(), exempt) == ()

    assert ppr.is_completed_status(None) is False
    assert ppr.is_completed_status(SimpleNamespace(status="TAMAMLANDI")) is True
    assert ppr.is_completed_status(SimpleNamespace(status="draft")) is False

    assert ppr.is_president_exempt(None) is False
    assert ppr.is_president_exempt(SimpleNamespace(employee=None)) is False
    assert ppr.is_president_exempt(SimpleNamespace(employee=exempt_employee)) is True

    # 3. amir puan modu, "enable_level_3_scoring" bayrağının yanı sıra dönemde
    # ham metin olarak "scoring"/"puan"/"puan_modu" yazılmasıyla da anlaşılır
    # (bkz. _period_level_3_mode). Bu, test_level_3_scoring_mode_* testinin
    # kullandığı bayrak tabanlı yoldan ayrı, kendi başına bir dal olduğu için
    # burada doğrudan doğrulanır.
    assert ppr._period_level_3_mode(_period(level_3_mode="scoring")) == "scoring"
    assert ppr._period_level_3_mode(_period(level_3_mode="puan")) == "scoring"
    assert ppr._period_level_3_mode(_period()) == "off"


def test_strict_wrapper_matches_result_and_dataclasses_serialize():
    ok, reason = ppr.is_evaluation_publishable_strict(_period(), None)
    assert (ok, reason) == (False, "Değerlendirme bulunamadı.")

    finding = ppr.PublishFinding("code_x", "mesaj", severity="warning", manager_level=2, criteria_id=9)
    assert finding.as_dict() == {
        "code": "code_x",
        "message": "mesaj",
        "severity": "warning",
        "manager_level": 2,
        "criteria_id": 9,
    }

    result = ppr.PublishPreflightResult(True, "", blockers=[finding])
    as_dict = result.as_dict()
    assert as_dict["ok"] is True
    assert as_dict["blockers"] == [finding.as_dict()]
    assert as_dict["rule_version"] == ppr.PUBLISH_PREFLIGHT_RULE_VERSION


# ---------------------------------------------------------------------------
# DB'ye bağlı iki alt-servis (gelişim önerisi / personel-destek ön onayı):
# DB/Flask bağlamı olmadan bu servisler güvenli biçimde düşer (fallback).
# Aşağıdaki testler önce o gerçek düşüşü doğrular, sonra publish_preflight_
# rules'ın kendi toplama/öncelik mantığını (predecessor_blocked kablolaması,
# gerçek "onaylandı" durumunda tam yeşil sonuç) tek bir dış sınır noktasından
# kontrol ederek doğrular.
# ---------------------------------------------------------------------------


def test_personnel_support_gate_blocks_when_schema_missing_in_test_env():
    # DB şeması (performance_personnel_support_publish_approvals tablosu) bu
    # test ortamında yok; gerçek servis bunu "hazır değil" kabul edip
    # güvenli tarafta kalarak yayını bloklamalı (fail-closed).
    evaluation = _evaluation()
    result = ppr.validate_evaluation_for_publish(_period(), evaluation)
    assert _codes(result) == ["personnel_support_publish_approval_required"]
    assert result.blockers[0].message == (
        "Personel ve Destek Hizmetleri Grup Başkanı yayın ön onayı hazır olmadan "
        "karne personele açılamaz."
    )


def test_development_recommendation_block_reason_is_surfaced_verbatim(monkeypatch):
    monkeypatch.setattr(
        ppr,
        "get_development_recommendation_publish_block_reason",
        lambda evaluation: "TEST_DEV_BLOCK_REASON",
    )
    evaluation = _evaluation()
    result = ppr.validate_evaluation_for_publish(_period(), evaluation)
    # Gelişim önerisi blokajı, kendisinden sonra çalışacak personel-destek
    # kapısını da "önceki blokaj var" olarak öne geçmeli (predecessor_blocked).
    assert _codes(result) == ["low_score_development_recommendation_required"]
    assert result.blockers[0].message == "TEST_DEV_BLOCK_REASON"


def test_personnel_support_gate_receives_correct_predecessor_blocked_flag(monkeypatch):
    captured: list[bool] = []

    def fake_personnel_support(evaluation, *, ensure=False, predecessor_blocked=False, actor=None):
        captured.append(predecessor_blocked)
        return ""

    monkeypatch.setattr(ppr, "get_personnel_support_publish_block_reason", fake_personnel_support)

    clean_evaluation = _evaluation()
    blocked_evaluation = _evaluation(status="draft", level_1_evaluator_id=None, level_1_completed=False)

    ppr.validate_evaluation_for_publish(_period(), clean_evaluation)
    ppr.validate_evaluation_for_publish(_period(), blocked_evaluation)

    # Temiz kayıtta önceden blokaj yok -> False. Zaten bloklu kayıtta ise
    # personel-destek adımı erkenden oluşturulmamalı -> True.
    assert captured == [False, True]


def test_true_happy_path_publishes_when_every_real_rule_and_gate_clears(monkeypatch):
    # Şema/DB olmadan personel-destek ön onay kapısı gerçekçi biçimde her
    # zaman bloklar (bkz. test_personnel_support_gate_blocks_when_schema_missing_
    # in_test_env). Bu test yalnızca o son DB'ye bağlı kapıyı "Personel ve
    # Destek Hizmetleri Grup Başkanı zaten onayladı" varsayarak, modülün geri
    # kalan TÜM gerçek kural mantığının (seviye tamamlama, kriter açıklaması,
    # genel görüş eşiği, düşük puan süreci, gelişim önerisi) gerçekten yeşile
    # çıktığını doğrular. publish_preflight_rules'ın kendisi mock'lanmaz;
    # yalnızca DB'ye bağlı dış sınır fonksiyonu kontrol edilir.
    monkeypatch.setattr(
        ppr,
        "get_personnel_support_publish_block_reason",
        lambda evaluation, **kwargs: "",
    )
    evaluation = _evaluation()
    result = ppr.validate_evaluation_for_publish(_period(), evaluation)
    assert result.ok is True
    assert result.reason == ""
    assert result.blockers == []
