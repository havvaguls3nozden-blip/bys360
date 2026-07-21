from __future__ import annotations

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

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import current_app

DEFAULT_CONFIG_RELATIVE = Path("config") / "hierarchy_templates_v1.json"


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
    is_active: bool = True
    source: str = "db"
    raw: dict[str, Any] = field(default_factory=dict)


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


class HierarchyRuleEngineService:
    def __init__(self, config_path: str | Path | None = None):
        self.config_path = Path(config_path) if config_path else self._default_config_path()
        self.config = self._load_config()

    @staticmethod
    def _default_config_path() -> Path:
        root = Path(current_app.root_path).parent if current_app else Path.cwd()
        return root / DEFAULT_CONFIG_RELATIVE

    def _load_config(self) -> dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Hierarchy config not found: {self.config_path}")
        return json.loads(self.config_path.read_text(encoding="utf-8"))

    def save_config(self, payload: dict[str, Any]) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self.config = payload

    def resolve_many(self, users: Iterable[UserRow]) -> list[dict[str, Any]]:
        user_list = [u for u in users if u.is_active]
        index_by_sicil = {u.sicil_no: u for u in user_list if u.sicil_no}
        rows = []
        for user in user_list:
            chain = self.resolve_user(user, user_list, index_by_sicil)
            rows.append({**user.raw, **chain.as_dict()})
        return rows

    def resolve_user(self, user: UserRow, users: list[UserRow], by_sicil: dict[str, UserRow]) -> ChainResolution:
        rule = self._match_rule(user)
        if not rule:
            return ChainResolution(rule_key="unmatched", chain_type="none", order=[], warnings=["Uygun zincir kuralı bulunamadı."])

        res = ChainResolution(rule_key=rule["rule_key"], chain_type=rule.get("chain_type", "none"), order=rule.get("order", []))
        levels = rule.get("levels", {})

        if res.chain_type == "none":
            res.info.append("Bu kayıt için değerlendirici üretilmez.")
            return res

        m1 = self._resolve_level(levels.get("1"), user, users, by_sicil)
        m2 = self._resolve_level(levels.get("2"), user, users, by_sicil)
        m3 = self._resolve_level(levels.get("3"), user, users, by_sicil)

        if m1:
            res.manager_1_sicil, res.manager_1_name = m1.sicil_no, m1.full_name
        elif levels.get("1"):
            res.warnings.append("1. amir bulunamadı.")

        if m2:
            res.manager_2_sicil, res.manager_2_name = m2.sicil_no, m2.full_name
        elif levels.get("2"):
            res.warnings.append("2. amir bulunamadı.")

        third_mode = (levels.get("3") or {}).get("mode", self.config.get("third_manager_defaults", {}).get("mode", "comment_only"))
        if m3:
            res.manager_3_sicil, res.manager_3_name = m3.sicil_no, m3.full_name
            res.info.append(f"3. amir modu: {third_mode}")
        elif levels.get("3") and user.ucuncu_yonetici_sicil:
            res.warnings.append("3. amir sicili yazılı ama kullanıcı bulunamadı.")

        if rule.get("rule_key") == "law_staff":
            res.info.append("Hukuk personelinde tek amir kuralı uygulandı.")
            # tek amir kuralı için 2. amir warning üretmeyelim
            res.warnings = [w for w in res.warnings if w != "2. amir bulunamadı."]

        if rule.get("rule_key") == "regular_personnel" and not res.manager_2_sicil:
            res.info.append("Koordinatör bulunamazsa kaydı önizlemede manuel kontrol edin.")

        return res

    def _match_rule(self, user: UserRow) -> dict[str, Any] | None:
        for rule in self.config.get("rules", []):
            match = rule.get("match", {})
            if self._matches(match, user):
                return rule
        return None

    @staticmethod
    def _matches(match: dict[str, Any], user: UserRow) -> bool:
        def norm(value: str) -> str:
            return (value or "").strip().upper()

        role = norm(user.role)
        unvan = norm(user.unvan)
        birim = norm(user.birim)

        if match.get("role") and role not in {norm(v) for v in match["role"]}:
            return False
        if match.get("birim") and birim not in {norm(v) for v in match["birim"]}:
            return False
        if match.get("unvan_contains"):
            if not any(norm(k) in unvan for k in match["unvan_contains"]):
                return False
        return True

    def _resolve_level(
        self,
        level_config: dict[str, Any] | None,
        user: UserRow,
        users: list[UserRow],
        by_sicil: dict[str, UserRow],
    ) -> UserRow | None:
        if not level_config:
            return None
        source = level_config.get("source")
        if source == "fixed_role":
            wanted_role = (level_config.get("role") or "").strip().upper()
            return self._first(users, lambda u: u.role.strip().upper() == wanted_role)
        if source == "law_counselor_in_same_unit":
            return self._first(
                users,
                lambda u: u.birim.strip().upper() == user.birim.strip().upper() and (
                    "HUKUK MÜŞAVİRİ" in u.unvan.upper() or "SORUMLU HUKUK MÜŞAVİRİ" in u.unvan.upper()
                ),
            )
        if source == "group_manager_by_parent_unit":
            return self._first(
                users,
                lambda u: u.role.strip().upper() == "GRUP_BASKANI" and u.birim.strip().upper() == user.ust_birim.strip().upper(),
            )
        if source == "coordinator_by_unit":
            return self._first(
                users,
                lambda u: u.role.strip().upper() == "KOORDINATOR" and u.birim.strip().upper() == user.birim.strip().upper() and u.ust_birim.strip().upper() == user.ust_birim.strip().upper(),
            )
        if source == "explicit_third_manager":
            if user.ucuncu_yonetici_sicil:
                return by_sicil.get(user.ucuncu_yonetici_sicil)
            return None
        return None

    @staticmethod
    def _first(users: list[UserRow], predicate) -> UserRow | None:
        for row in users:
            if predicate(row):
                return row
        return None