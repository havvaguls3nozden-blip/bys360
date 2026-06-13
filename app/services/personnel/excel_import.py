
"""Personel Excel aktarımı preflight ve satır doğrulama servis köprüsü.

Faz 8 kapsamı:
- Excel başlık okuma, zorunlu sütun kontrolü ve satır payload hazırlığını
  servis katmanında toplar.
- Veritabanına yazmaz, commit/rollback çalıştırmaz.
- Mevcut import route davranışını koruyarak sadece doğrulama/okuma yüzeyini
  sadeleştirir.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Callable, Mapping, Sequence

NormalizeFunc = Callable[[Any], str]

PERSONNEL_EXCEL_REQUIRED_HEADERS: dict[str, tuple[str, ...]] = {
    "sicil no": ("sicil no",),
    "ad": ("ad",),
    "soyad": ("soyad",),
    "e-posta": ("e-posta", "eposta", "e posta"),
    "unvan": ("unvan",),
    "birim": ("birim",),
    "üst birim": ("ust birim", "üst birim", "ust_birim", "üst_birim"),
}

PERSONNEL_EXCEL_MANAGER_1_ALIASES: tuple[str, ...] = (
    "yönetici sicil",
    "yonetici sicil",
    "1. amir sicil",
    "1 amir sicil",
    "1. amir",
    "1 amir",
)
PERSONNEL_EXCEL_MANAGER_2_ALIASES: tuple[str, ...] = (
    "ikinci yönetici sicil",
    "ikinci yonetici sicil",
    "2. amir sicil",
    "2 amir sicil",
    "2. amir",
    "2 amir",
)
PERSONNEL_EXCEL_MANAGER_3_ALIASES: tuple[str, ...] = (
    "ucuncu_yonetici_sicil",
    "üçüncü yönetici sicil",
    "ucuncu yonetici sicil",
    "3. amir sicil",
    "3 amir sicil",
    "3. amir",
    "3 amir",
    "üçüncü amir sicil",
    "ucuncu amir sicil",
    "3. yönetici sicil",
    "3 yonetici sicil",
    "new_y3",
    "old_y3",
    "y3",
)
PERSONNEL_EXCEL_ROLE_ALIASES: tuple[str, ...] = ("rol", "role", "rol (opsiyonel)", "role (optional)")
PERSONNEL_EXCEL_CATEGORY_ALIASES: tuple[str, ...] = (
    "kategori",
    "personel kategorisi",
    "performans kategorisi",
    "performance category",
    "personnel category",
)
PERSONNEL_EXCEL_MANAGER_ALIASES: frozenset[str] = frozenset(
    PERSONNEL_EXCEL_MANAGER_1_ALIASES
    + PERSONNEL_EXCEL_MANAGER_2_ALIASES
    + PERSONNEL_EXCEL_MANAGER_3_ALIASES
)


@dataclass(frozen=True, slots=True)
class PersonnelExcelPreflightResult:
    ok: bool
    missing_headers: tuple[str, ...]
    normalized_headers: tuple[str, ...]
    required_header_indexes: dict[str, int]
    column_index: dict[str, int]
    header_count: int
    db_commit: bool = False
    db_rollback: bool = False
    route_contract: str = "preserved"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PersonnelExcelRowPayload:
    sicil_no: str = ""
    ad: str = ""
    soyad: str = ""
    email: str = ""
    unvan: str = ""
    birim: str = ""
    ust_birim: str = ""
    yonetici_sicil: str = ""
    ikinci_yonetici_sicil: str = ""
    ucuncu_yonetici_sicil: str = ""
    raw_role: str = ""
    personnel_category: str = "Diğer"

    @property
    def full_name(self) -> str:
        return f"{self.ad} {self.soyad}".strip()

    @property
    def manager_sicils(self) -> tuple[str, ...]:
        return tuple(
            value
            for value in (
                self.yonetici_sicil,
                self.ikinci_yonetici_sicil,
                self.ucuncu_yonetici_sicil,
            )
            if value
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def excel_scalar(value: Any) -> str:
    """Preserve the existing route scalar conversion behaviour."""
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, int):
        return str(value)
    return str(value).strip()


def _default_normalize(value: Any) -> str:
    return excel_scalar(value).lower()


def normalize_personnel_excel_headers(
    headers: Sequence[Any],
    *,
    normalize_func: NormalizeFunc | None = None,
) -> tuple[str, ...]:
    normalizer = normalize_func or _default_normalize
    normalized: list[str] = []
    for header in headers:
        if header is None:
            normalized.append("")
            continue
        normalized_value = excel_scalar(normalizer(header))
        # BYS360_PERSONNEL_EXCEL_OPTIONAL_HEADER_ALIAS_FIX_V1
        # Şablonda görünen "(opsiyonel)" ibaresi teknik anahtar değildir.
        # Import motoru açık amir / rol sütunlarını doğru tanısın diye başlıktan temizlenir.
        normalized_value = normalized_value.replace(" (opsiyonel)", "").replace("(opsiyonel)", "").strip()
        normalized.append(normalized_value)
    return tuple(normalized)


def build_personnel_excel_column_index(normalized_headers: Sequence[str]) -> dict[str, int]:
    """Return first index for each normalized header, matching legacy behaviour."""
    index: dict[str, int] = {}
    for position, header in enumerate(normalized_headers):
        index.setdefault(header, position)
    return index


def _find_header_index(normalized_headers: Sequence[str], aliases: Sequence[str]) -> int | None:
    for alias in aliases:
        if alias in normalized_headers:
            return list(normalized_headers).index(alias)
    return None


def preflight_personnel_excel_headers(
    headers: Sequence[Any],
    *,
    normalize_func: NormalizeFunc | None = None,
) -> PersonnelExcelPreflightResult:
    """Validate required personnel Excel headers without reading/writing DB."""
    normalized_headers = normalize_personnel_excel_headers(headers, normalize_func=normalize_func)
    required_indexes: dict[str, int] = {}
    missing: list[str] = []
    for display_name, aliases in PERSONNEL_EXCEL_REQUIRED_HEADERS.items():
        found = _find_header_index(normalized_headers, aliases)
        if found is None:
            missing.append(display_name)
        else:
            required_indexes[display_name] = found
    return PersonnelExcelPreflightResult(
        ok=not missing,
        missing_headers=tuple(missing),
        normalized_headers=normalized_headers,
        required_header_indexes=required_indexes,
        column_index=build_personnel_excel_column_index(normalized_headers),
        header_count=len(normalized_headers),
    )


def _row_value(row: Sequence[Any], index: int | None) -> Any:
    if index is None:
        return None
    try:
        return row[index]
    except IndexError:
        return None


def _read_required_cell(row: Sequence[Any], required_indexes: Mapping[str, int], key: str) -> str:
    return excel_scalar(_row_value(row, required_indexes.get(key)))


def _read_first_alias_cell(row: Sequence[Any], column_index: Mapping[str, int], aliases: Sequence[str]) -> str:
    for alias in aliases:
        if alias not in column_index:
            continue
        value = _row_value(row, column_index[alias])
        if value is None:
            continue
        text = excel_scalar(value)
        if text:
            return text
    return ""


def build_personnel_excel_row_payload(
    row: Sequence[Any],
    *,
    header_idx: Mapping[str, int],
    column_index: Mapping[str, int],
) -> PersonnelExcelRowPayload:
    """Read one Excel row into a normalized payload without DB side effects."""
    return PersonnelExcelRowPayload(
        sicil_no=_read_required_cell(row, header_idx, "sicil no"),
        ad=_read_required_cell(row, header_idx, "ad"),
        soyad=_read_required_cell(row, header_idx, "soyad"),
        email=_read_required_cell(row, header_idx, "e-posta").lower(),
        unvan=_read_required_cell(row, header_idx, "unvan"),
        birim=_read_required_cell(row, header_idx, "birim"),
        ust_birim=_read_required_cell(row, header_idx, "üst birim"),
        yonetici_sicil=_read_first_alias_cell(row, column_index, PERSONNEL_EXCEL_MANAGER_1_ALIASES),
        ikinci_yonetici_sicil=_read_first_alias_cell(row, column_index, PERSONNEL_EXCEL_MANAGER_2_ALIASES),
        ucuncu_yonetici_sicil=_read_first_alias_cell(row, column_index, PERSONNEL_EXCEL_MANAGER_3_ALIASES),
        raw_role=_read_first_alias_cell(row, column_index, PERSONNEL_EXCEL_ROLE_ALIASES),
        personnel_category=_read_first_alias_cell(row, column_index, PERSONNEL_EXCEL_CATEGORY_ALIASES) or "Diğer",
    )


def row_has_required_personnel_excel_fields(payload: PersonnelExcelRowPayload) -> bool:
    return bool(
        payload.sicil_no
        and payload.ad
        and payload.soyad
        and payload.email
        and payload.unvan
        and payload.birim
        and payload.ust_birim
    )


def has_explicit_personnel_excel_manager_columns(normalized_headers: Sequence[str]) -> bool:
    return any(header in PERSONNEL_EXCEL_MANAGER_ALIASES for header in normalized_headers if header)


def build_personnel_excel_import_phase8_summary() -> dict[str, Any]:
    return {
        "phase": "personnel_service_faz8",
        "service": "excel_import",
        "preflight_headers": True,
        "row_payload_bridge": True,
        "required_row_validation": True,
        "manager_column_detection": True,
        "db_commit": False,
        "db_rollback": False,
        "route_contract": "preserved",
    }
