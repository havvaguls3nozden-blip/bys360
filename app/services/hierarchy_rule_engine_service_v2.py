from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from flask import current_app

from .hierarchy_position_registry_service import HierarchyPositionRegistryService

# --- BYS360 third-manager Excel import compatibility patch ---


THIRD_MANAGER_STANDARD_KEY = "ucuncu_yonetici_sicil"
THIRD_MANAGER_HEADER_ALIASES = [
    "ucuncu_yonetici_sicil",
    "üçüncü yönetici sicil",
    "ucuncu yonetici sicil",
    "3. amir sicil",
    "3 amir sicil",
    "new_y3",
]

DEFAULT_CONFIG_RELATIVE = Path("config") / "hierarchy_templates_v2.json"
ROLE_ALIASES = {
    "baskan": "baskan",
    "başkan": "baskan",
    "baskan_yardimcisi": "baskan_yardimcisi",
    "başkan_yardımcısı": "baskan_yardimcisi",
    "grup_baskani": "grup_baskani",
    "group_baskani": "grup_baskani",
    "grup başkanı": "grup_baskani",
    "koordinator": "koordinator",
    "koordinatör": "koordinator",
    "birim_sorumlusu": "birim_sorumlusu",
    "birim amiri": "birim_sorumlusu",
    "personel": "personel",
    "admin": "admin",
}


@dataclass
class UserRow:
    id: int | None
    sicil_no: str
    full_name: str
    role: str
    unvan: str
    birim: str
    ust_birim: str
    yonetici_sicil: str = ""
    ikinci_yonetici_sicil: str = ""
    ucuncu_yonetici_sicil: str = ""
    override_manager_1_sicil: str = ""
    override_manager_2_sicil: str = ""
    override_manager_3_sicil: str = ""
    is_active: bool = True
    source: str = "db"
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def normalized_role(self) -> str:
        raw = (self.role or "").strip().lower()
        return ROLE_ALIASES.get(raw, raw)


@dataclass
class ChainResolution:
    rule_key: str
    chain_type: str
    order: list[int]
    manager_1_sicil: str = ""
    manager_2_sicil: str = ""
    manager_3_sicil: str = ""
    manager_1_name: str = ""
    manager_2_name: str = ""
    manager_3_name: str = ""
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "rule_key": self.rule_key,
            "chain_type": self.chain_type,
            "order": self.order,
            "manager_1_sicil": self.manager_1_sicil,
            "manager_2_sicil": self.manager_2_sicil,
            "manager_3_sicil": self.manager_3_sicil,
            "manager_1_name": self.manager_1_name,
            "manager_2_name": self.manager_2_name,
            "manager_3_name": self.manager_3_name,
            "warnings": self.warnings,
            "info": self.info,
        }


class HierarchyRuleEngineServiceV2:
    def __init__(self, config_path: str | Path | None = None, registry_relative_path: str = "config/hierarchy_position_registry_v1.json"):
        self.config_path = Path(config_path) if config_path else self._default_config_path()
        self.registry_service = HierarchyPositionRegistryService(config_relative_path=registry_relative_path)
        self.config = json.loads(self.config_path.read_text(encoding="utf-8"))

    @staticmethod
    def _default_config_path() -> Path:
        root = Path(current_app.root_path).parent if current_app else Path.cwd()
        return root / DEFAULT_CONFIG_RELATIVE

    def resolve_many(self, users: Iterable[UserRow]) -> list[dict[str, Any]]:
        user_list = [u for u in users if u.is_active]
        by_sicil = {u.sicil_no: u for u in user_list if u.sicil_no}
        rows = []
        for user in user_list:
            chain = self.resolve_user(user, user_list, by_sicil)
            rows.append({**user.raw, **chain.as_dict()})
        return rows

    def resolve_user(self, user: UserRow, users: list[UserRow], by_sicil: dict[str, UserRow]) -> ChainResolution:
        rule = self._match_rule(user)
        if not rule:
            return ChainResolution(rule_key="unmatched", chain_type="none", order=[], warnings=["Uygun zincir kuralı bulunamadı."])
        result = ChainResolution(rule_key=rule["rule_key"], chain_type=rule.get("chain_type", "none"), order=rule.get("order", []))
        levels = rule.get("levels", {})
        if result.chain_type == "none":
            result.info.append("Bu kayıt için değerlendirici üretilmez.")
            return result

        # override sicilleri yalnızca istisna alanıdır
        for level_no, override_value in [(1, user.override_manager_1_sicil), (2, user.override_manager_2_sicil), (3, user.override_manager_3_sicil)]:
            if override_value:
                row = by_sicil.get(override_value)
                if row:
                    self._set_level(result, level_no, row)
                    result.info.append(f"{level_no}. amir override sicili uygulandı.")

        for level_no, cfg in [(1, levels.get("1")), (2, levels.get("2")), (3, levels.get("3"))]:
            if getattr(result, f"manager_{level_no}_sicil") or not cfg:
                continue
            row = self._resolve_level(cfg, user, users, by_sicil)
            if row:
                self._set_level(result, level_no, row)
            elif level_no in (1, 2):
                result.warnings.append(f"{level_no}. amir bulunamadı.")

        if rule.get("rule_key") in {"law_staff", "special_presidency_president_only", "vice_president"}:
            result.warnings = [w for w in result.warnings if w != "2. amir bulunamadı."]
            if rule.get("rule_key") != "vice_president":
                result.info.append("Özel tek amir kuralı uygulandı.")
        if rule.get("rule_key") == "president":
            result.warnings.clear()
            result.info.append("Üst yönetim düğümü istisnası.")
        if result.manager_3_sicil:
            mode = (levels.get("3") or {}).get("mode", self.config.get("third_manager_defaults", {}).get("mode", "comment_only"))
            result.info.append(f"3. amir modu: {mode}")
        return result

    def _match_rule(self, user: UserRow) -> dict[str, Any] | None:
        for rule in self.config.get("rules", []):
            if self._matches(rule.get("match", {}), user):
                return rule
        return None

    def _matches(self, match: dict[str, Any], user: UserRow) -> bool:
        def norm(v):
            return (v or "").strip().upper()
        role = norm(user.normalized_role)
        unvan = norm(user.unvan)
        birim = norm(user.birim)
        if match.get("role"):
            allowed = {norm(ROLE_ALIASES.get(v.lower(), v.lower())) for v in match["role"]}
            if role not in allowed:
                return False
        if match.get("birim") and birim not in {norm(v) for v in match["birim"]}:
            return False
        return not (match.get("unvan_contains") and not any(norm(k) in unvan for k in match["unvan_contains"]))

    def _resolve_level(self, level_config: dict[str, Any], user: UserRow, users: list[UserRow], by_sicil: dict[str, UserRow]) -> UserRow | None:
        source = level_config.get("source")
        if source == "fixed_role":
            wanted_role = ROLE_ALIASES.get((level_config.get("role") or "").strip().lower(), (level_config.get("role") or "").strip().lower())
            return self._first(users, lambda u: u.normalized_role == wanted_role)
        if source == "law_counselor_in_same_unit_or_registry":
            row = self._first(users, lambda u: u.birim.strip().upper() == user.birim.strip().upper() and ("HUKUK MÜŞAVİRİ" in u.unvan.upper() or "SORUMLU HUKUK MÜŞAVİRİ" in u.unvan.upper()))
            if row:
                return row
            ov = self.registry_service.find_unit_override(user.birim, user.ust_birim) or {}
            return by_sicil.get((ov.get("law_counselor_sicil") or "").strip())
        if source == "group_manager_by_parent_unit_or_registry":
            row = self._first(users, lambda u: u.normalized_role == "grup_baskani" and u.birim.strip().upper() == user.ust_birim.strip().upper())
            if row:
                return row
            ov = self.registry_service.find_unit_override(user.birim, user.ust_birim) or {}
            return by_sicil.get((ov.get("group_manager_sicil") or "").strip())
        if source == "coordinator_by_unit_or_registry":
            row = self._first(users, lambda u: u.normalized_role == "koordinator" and u.birim.strip().upper() == user.birim.strip().upper() and u.ust_birim.strip().upper() == user.ust_birim.strip().upper())
            if row:
                return row
            ov = self.registry_service.find_unit_override(user.birim, user.ust_birim) or {}
            return by_sicil.get((ov.get("coordinator_sicil") or "").strip())
        if source == "explicit_third_manager":
            sicil = (user.override_manager_3_sicil or user.ucuncu_yonetici_sicil or "").strip()
            if sicil:
                return by_sicil.get(sicil)
            ov = self.registry_service.find_unit_override(user.birim, user.ust_birim) or {}
            return by_sicil.get((ov.get("third_manager_default_sicil") or "").strip())
        return None

    @staticmethod
    def _first(users: list[UserRow], predicate) -> UserRow | None:
        for row in users:
            if predicate(row):
                return row
        return None

    @staticmethod
    def _set_level(result: ChainResolution, level_no: int, row: UserRow) -> None:
        setattr(result, f"manager_{level_no}_sicil", row.sicil_no)
        setattr(result, f"manager_{level_no}_name", row.full_name)