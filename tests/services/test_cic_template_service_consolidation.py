from __future__ import annotations

import ast
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from app.services import corporate_information_center
from app.services.cic import (
    cic_context,
    facade,
    misc_context,
    repository,
    save_context,
    send_context,
    template_service,
)

ROOT = Path(__file__).resolve().parents[2]
MOVED_TEMPLATE_FUNCTIONS = {
    "_cic_phase6_item",
    "_cic_phase6_status",
    "_cic_phase6_template_quality",
    "_dashboard_counts",
    "_render_template_text",
    "_render_template_text_base",
    "_user_name",
    "get_template",
    "save_templates",
}
FACADE_TEMPLATE_FUNCTIONS = MOVED_TEMPLATE_FUNCTIONS - {
    "_render_template_text_base",
}


def _top_level_definitions(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_template_functions_have_one_canonical_definition() -> None:
    canonical = ROOT / "app/services/cic/template_service.py"
    assert _top_level_definitions(canonical) >= MOVED_TEMPLATE_FUNCTIONS

    for relative in (
        "app/services/cic/send_context.py",
        "app/services/cic/misc_context.py",
        "app/services/cic/save_context.py",
        "app/services/cic/cic_context.py",
        "app/services/cic/repository.py",
        "app/services/corporate_information_center.py",
    ):
        assert not (
            MOVED_TEMPLATE_FUNCTIONS
            & _top_level_definitions(ROOT / relative)
        )

    source = canonical.read_text(encoding="utf-8")
    assert "corporate_information_center as _legacy" not in source
    assert "_legacy_cic" not in source
    assert "globals()" not in source
    assert "globals()[" not in source
    assert "hasattr(_legacy" not in source
    assert "_P8_LEGACY_NAMES" not in source
    assert "Compatibility guard" not in source


def test_existing_entry_points_use_canonical_template_functions() -> None:
    for name in FACADE_TEMPLATE_FUNCTIONS:
        assert getattr(facade, name) is getattr(template_service, name)

    assert send_context._template_service is template_service
    assert misc_context._template_service is template_service
    assert cic_context._template_service is template_service

    for module in (
        send_context,
        misc_context,
        save_context,
        cic_context,
        repository,
        corporate_information_center,
    ):
        for name in MOVED_TEMPLATE_FUNCTIONS:
            assert not hasattr(module, name), (module.__name__, name)


def test_user_name_preserves_display_fallback_order() -> None:
    assert template_service._user_name(None) == "-"
    assert template_service._user_name(
        SimpleNamespace(
            ad="Ada",
            soyad="Lovelace",
            full_name_cache="Cached",
            email="ada@example.test",
            id=1,
        )
    ) == "Ada Lovelace"
    assert template_service._user_name(
        SimpleNamespace(
            ad="",
            soyad="",
            full_name_cache="Cached Name",
            email="cached@example.test",
            id=2,
        )
    ) == "Cached Name"
    assert template_service._user_name(
        SimpleNamespace(
            ad="",
            soyad="",
            full_name_cache=None,
            email="mail@example.test",
            id=3,
        )
    ) == "mail@example.test"
    assert template_service._user_name(
        SimpleNamespace(
            ad="",
            soyad="",
            full_name_cache=None,
            email=None,
            id=4,
        )
    ) == "Kullanıcı #4"


class _ActiveColumn:
    @staticmethod
    def is_(value: object) -> tuple[str, object]:
        return ("is", value)


class _Query:
    def __init__(self, count: int) -> None:
        self.count_value = count
        self.filters: list[tuple[object, ...]] = []

    def filter(self, *clauses: object) -> _Query:
        self.filters.append(clauses)
        return self

    def count(self) -> int:
        return self.count_value


def test_dashboard_counts_preserve_active_and_status_contract(
    monkeypatch,
) -> None:
    query = _Query(17)
    user_model = SimpleNamespace(is_active=_ActiveColumn(), query=query)
    monkeypatch.setattr(template_service, "User", user_model)
    monkeypatch.setattr(
        template_service,
        "get_setting",
        lambda key, default="": (
            "Son işlem başarılı"
            if key.endswith(".last_status")
            else default
        ),
    )

    result = template_service._dashboard_counts()

    assert result["aktif_personel_sayisi"] == 17
    assert result["son_gonderim_durumu"] == "Son işlem başarılı"
    assert query.filters == [(('is', True),)]
    assert "düzenli izlenmesi" in str(result["gunun_notu"])
    assert "bekleyen görev" in str(result["yarin_yonetici_notu"])


def test_render_template_base_preserves_all_standard_placeholders(
    monkeypatch,
) -> None:
    now = datetime(2026, 7, 20, 14, 35)
    monkeypatch.setattr(
        template_service,
        "get_config",
        lambda: {"location_name": "Çanakkale"},
    )
    monkeypatch.setattr(
        template_service,
        "_weather",
        lambda: {
            "bugun_hava": "Açık",
            "yarin_hava": "Parçalı bulutlu",
            "kiyafet_onerisi": "İnce ceket",
            "yarin_oneri": "Şemsiye",
        },
    )
    monkeypatch.setattr(template_service, "_now", lambda: now)
    monkeypatch.setattr(
        template_service,
        "_dashboard_counts",
        lambda: {
            "aktif_personel_sayisi": 23,
            "son_gonderim_durumu": "Başarılı",
            "gunun_notu": "Kontrol",
            "yarin_yonetici_notu": "Hazırlık",
        },
    )
    user = SimpleNamespace(
        ad="Ayşe",
        soyad="Yılmaz",
        email="ayse@example.test",
    )
    text = (
        "{ad_soyad}|{email}|{tarih}|{saat}|{konum}|"
        "{bugun_hava}|{yarin_hava}|{kiyafet_onerisi}|{yarin_oneri}|"
        "{aktif_personel_sayisi}|{son_gonderim_durumu}|"
        "{gunun_notu}|{yarin_yonetici_notu}|"
        "{bys360_baglanti}|{geri_bildirim_baglantisi}"
    )

    rendered = template_service._render_template_text_base(
        text,
        user,
        "staff_morning",
    )

    assert rendered == (
        "Ayşe Yılmaz|ayse@example.test|20.07.2026|14:35|Çanakkale|"
        "Açık|Parçalı bulutlu|İnce ceket|Şemsiye|23|Başarılı|"
        "Kontrol|Hazırlık|https://bys360.canakkaletarihialan.gov.tr/|"
        "https://bys360.canakkaletarihialan.gov.tr/feedback"
    )


def test_manager_template_does_not_call_weather(monkeypatch) -> None:
    monkeypatch.setattr(
        template_service,
        "get_config",
        lambda: {"location_name": "Çanakkale"},
    )
    monkeypatch.setattr(
        template_service,
        "_weather",
        lambda: (_ for _ in ()).throw(AssertionError("weather called")),
    )
    monkeypatch.setattr(
        template_service,
        "_now",
        lambda: datetime(2026, 7, 20, 8, 0),
    )
    monkeypatch.setattr(
        template_service,
        "_dashboard_counts",
        lambda: {
            "aktif_personel_sayisi": 1,
            "son_gonderim_durumu": "-",
            "gunun_notu": "-",
            "yarin_yonetici_notu": "-",
        },
    )

    rendered = template_service._render_template_text_base(
        "{bugun_hava}|{yarin_hava}|{kiyafet_onerisi}|{yarin_oneri}",
        None,
        "manager_morning",
    )

    assert rendered == "-|-|-|-"


def test_render_template_adds_celebration_placeholders(monkeypatch) -> None:
    from app.services.cic import celebration_service

    monkeypatch.setattr(
        template_service,
        "_render_template_text_base",
        lambda text, _user, _task_key: text.replace("{ad_soyad}", "Ada"),
    )
    monkeypatch.setattr(
        send_context,
        "_cic_v40_special_days_today",
        lambda: [{"name": "Zafer Bayramı"}, {"name": "Kurum Günü"}],
    )
    monkeypatch.setattr(
        celebration_service,
        "_cic_v40_service_year",
        lambda _user: 6,
    )

    rendered = template_service._render_template_text(
        "{ad_soyad}|{ozel_gun_adi}|{hizmet_yili}|{kutlama_notu}",
        SimpleNamespace(id=1),
        "special_day",
    )

    assert rendered.startswith("Ada|Zafer Bayramı, Kurum Günü|6|")
    assert "KVKK uyumlu" in rendered


def test_get_template_preserves_setting_and_default_fallback(monkeypatch) -> None:
    calls: list[tuple[str, str]] = []

    def fake_get_setting(key: str, default: str = "") -> str:
        calls.append((key, default))
        if key.endswith(".subject"):
            return "Özel konu"
        return ""

    monkeypatch.setattr(template_service, "get_setting", fake_get_setting)

    result = template_service.get_template("staff_morning")

    assert result["subject"] == "Özel konu"
    assert result["body"] == template_service.TASK_DEFINITIONS[
        "staff_morning"
    ]["body"]
    assert len(calls) == 2


def test_save_templates_persists_all_task_templates(monkeypatch) -> None:
    calls: list[tuple[str, str, dict[str, Any]]] = []
    commits: list[str] = []
    monkeypatch.setattr(
        template_service,
        "set_setting",
        lambda key, value, **kwargs: calls.append((key, value, kwargs)),
    )
    monkeypatch.setattr(
        template_service,
        "db",
        SimpleNamespace(session=SimpleNamespace(commit=lambda: commits.append("ok"))),
    )

    template_service.save_templates(
        {
            "subject_staff_morning": " Yeni konu ",
            "body_staff_morning": " Yeni gövde ",
        },
        actor_user_id=42,
    )

    assert len(calls) == 2 * len(template_service.TASK_DEFINITIONS)
    subject_call = next(
        call
        for call in calls
        if call[0].endswith(".staff_morning.subject")
    )
    body_call = next(
        call for call in calls if call[0].endswith(".staff_morning.body")
    )
    assert subject_call[1] == "Yeni konu"
    assert subject_call[2]["actor_user_id"] == 42
    assert body_call[1] == "Yeni gövde"
    assert body_call[2]["value_type"] == "text"
    assert commits == ["ok"]


def test_template_quality_preserves_status_and_item_contract() -> None:
    healthy = template_service._cic_phase6_template_quality(
        [{"subject": "Kurum özeti", "body": "A" * 80}]
    )
    assert healthy["status"] == "ok"
    assert healthy["problem_count"] == 0
    assert all(item["status"] == "ok" for item in healthy["items"])

    warning = template_service._cic_phase6_template_quality(
        [{"subject": "", "body": "debug workflow"}]
    )
    assert warning["status"] == "warn"
    assert warning["problem_count"] == 3
    assert [item["status"] for item in warning["items"]] == [
        "warn",
        "warn",
        "warn",
    ]
    assert template_service._cic_phase6_status(False) == "danger"
    assert template_service._cic_phase6_status(False, warn=True) == "warn"
