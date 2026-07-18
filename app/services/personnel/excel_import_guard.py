
"""BYS360 personel Excel import guvenlik ve veri butunlugu on kontrolu.

Bu servis gerçek kayıt yazmadan önce çalışır. Amaç hatalı başlık, bozuk
encoding, mükerrer sütun veya eksik zorunlu alan yüzünden sessiz yanlış veri
oluşmasını engellemektir.
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata
from typing import Any, Iterable, Sequence

MOJIBAKE_MARKERS = ("\u00c3", "\u00c4", "\u00c5", "\ufffd", "\u00d0", "\u00f0", "\u00fe", "\u00de", "\u00dd", "\u00fd")

REQUIRED_CANONICAL_FIELDS = ("sicil_no", "ad", "soyad", "email", "unvan", "birim")

_HEADER_ALIASES: dict[str, tuple[str, ...]] = {
    "sicil_no": ("sicil_no", "sicil no", "sicil", "sicil numarasi", "sicil numarası", "personel sicil", "sicilno"),
    "ad": ("ad", "adi", "adı", "isim", "personel adi", "personel adı"),
    "soyad": ("soyad", "soyadi", "soyadı", "soy isim", "soyisim", "personel soyadi", "personel soyadı"),
    "email": ("email", "e-mail", "e posta", "e-posta", "eposta", "mail", "kurum maili", "kurumsal mail"),
    "unvan": ("unvan", "ünvan", "gorev", "görev", "gorev unvani", "görev unvanı"),
    "birim": ("birim", "calisma grubu", "çalışma grubu", "bagli birim", "bağlı birim"),
    "ust_birim": ("ust_birim", "ust birim", "üst birim", "grup baskanligi", "grup başkanlığı"),
    "role": ("role", "rol", "yetki", "kullanici rolu", "kullanıcı rolü"),
    "is_active": ("is_active", "aktif", "durum", "aktif mi", "aktiflik"),
    "yonetici_sicil": (
        "yonetici_sicil", "yonetici sicil", "yönetici sicil", "1. amir sicil", "1 amir sicil",
        "birinci amir sicil", "1. yönetici sicil", "1 yonetici sicil", "1. amir", "1 amir", "birinci amir",
    ),
    "ikinci_yonetici_sicil": (
        "ikinci_yonetici_sicil", "ikinci yonetici sicil", "ikinci yönetici sicil", "2. amir sicil", "2 amir sicil",
        "ikinci amir sicil", "2. yönetici sicil", "2 yonetici sicil", "2. amir", "2 amir", "ikinci amir",
    ),
    "ucuncu_yonetici_sicil": (
        "ucuncu_yonetici_sicil", "ucuncu yonetici sicil", "üçüncü yönetici sicil", "ucuncu yönetici sicil",
        "3. amir sicil", "3 amir sicil", "üçüncü amir sicil", "ucuncu amir sicil", "3. yönetici sicil",
        "3 yonetici sicil", "3. amir", "3 amir", "üçüncü amir", "ucuncu amir", "new_y3",
    ),
    "personnel_category": (
        "personnel_category", "kategori", "personel kategori", "personel kategorisi", "performans kategori",
        "performans kategorisi", "grup", "personel grubu",
    ),
}

_ALIAS_TO_CANONICAL: dict[str, str] = {}
for canonical, aliases in _HEADER_ALIASES.items():
    for alias in aliases:
        _ALIAS_TO_CANONICAL[alias] = canonical


@dataclass(slots=True)
class ExcelImportPreflightResult:
    ok: bool
    errors: list[str]
    warnings: list[str]
    canonical_headers: list[str]
    column_index: dict[str, int]
    row_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "canonical_headers": list(self.canonical_headers),
            "column_index": dict(self.column_index),
            "row_count": self.row_count,
        }


def _strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def normalize_import_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip().replace("\ufeff", "")
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("İ", "i").replace("I", "i").lower()
    text = _strip_accents(text)
    text = re.sub(r"[\s\-./]+", " ", text)
    text = re.sub(r"[^0-9a-z_ çğıöşü]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    text = text.replace(" ", "_") if text in {"sicil no", "ust birim"} else text
    return text


def _canonical_header(value: object) -> str:
    raw = normalize_import_text(value)
    raw_space = raw.replace("_", " ")
    return _ALIAS_TO_CANONICAL.get(raw) or _ALIAS_TO_CANONICAL.get(raw_space) or raw


def _cell_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value)).strip()
    return str(value).strip()


def _looks_like_mojibake(value: object) -> bool:
    text = _cell_text(value)
    return bool(text and any(marker in text for marker in MOJIBAKE_MARKERS))


def _is_blank_row(row: Sequence[Any] | None) -> bool:
    if not row:
        return True
    return all(_cell_text(value) == "" for value in row)


def _get(row: Sequence[Any], index: int | None) -> str:
    if index is None or index < 0 or index >= len(row):
        return ""
    return _cell_text(row[index])


def validate_personnel_import_rows_for_commit(rows: Iterable[Sequence[Any]], *, max_errors: int = 120) -> dict[str, Any]:
    """Validate workbook rows before any DB write.

    Returns a plain dict so both old route families can use it without coupling.
    """
    row_list = list(rows or [])
    errors: list[str] = []
    warnings: list[str] = []
    if not row_list:
        return ExcelImportPreflightResult(False, ["Excel dosyası boş."], [], [], {}, 0).to_dict()

    raw_headers = list(row_list[0] or [])
    if not raw_headers or all(_cell_text(h) == "" for h in raw_headers):
        return ExcelImportPreflightResult(False, ["Excel başlık satırı boş. Şablondaki başlıklar korunmalıdır."], [], [], {}, 0).to_dict()

    canonical_headers: list[str] = [_canonical_header(h) for h in raw_headers]
    column_index: dict[str, int] = {}
    duplicate_headers: dict[str, list[str]] = {}

    for idx, (raw, canonical) in enumerate(zip(raw_headers, canonical_headers, strict=False)):
        if _looks_like_mojibake(raw):
            errors.append(f"Başlıkta bozuk karakter/encoding tespit edildi: {raw!r}")
        if not canonical:
            continue
        if canonical in column_index and canonical in set(_HEADER_ALIASES.keys()):
            duplicate_headers.setdefault(canonical, []).append(_cell_text(raw))
            continue
        column_index.setdefault(canonical, idx)

    for canonical, raws in duplicate_headers.items():
        errors.append(f"Mükerrer sütun eşleşmesi var: {canonical} -> {', '.join(raws)}. Aynı alan tek sütun olmalıdır.")

    for field in REQUIRED_CANONICAL_FIELDS:
        if field not in column_index:
            errors.append(f"Zorunlu sütun eksik: {field}")

    unknown_nonempty = [str(raw_headers[i]).strip() for i, h in enumerate(canonical_headers) if h and h not in _HEADER_ALIASES]
    if unknown_nonempty:
        warnings.append("Şablonda tanınmayan ek sütunlar var; bu sütunlar işlenmeyecek: " + ", ".join(unknown_nonempty[:12]))

    seen_sicil: dict[str, int] = {}
    nonblank_count = 0
    email_index = column_index.get("email")
    sicil_index = column_index.get("sicil_no")

    for row_number, row in enumerate(row_list[1:], start=2):
        row = tuple(row or ())
        if _is_blank_row(row):
            continue
        nonblank_count += 1
        if any(_looks_like_mojibake(value) for value in row[: min(len(row), 12)]):
            errors.append(f"Satır {row_number}: bozuk karakter/encoding tespit edildi. Dosyayı UTF-8 uyumlu şablondan yeniden kaydedin.")
        for field in REQUIRED_CANONICAL_FIELDS:
            value = _get(row, column_index.get(field))
            if not value:
                errors.append(f"Satır {row_number}: zorunlu alan boş: {field}")
        email = _get(row, email_index)
        if email and ("@" not in email or email.startswith("@") or email.endswith("@")):
            errors.append(f"Satır {row_number}: e-posta biçimi geçersiz: {email}")
        sicil = _get(row, sicil_index)
        if sicil:
            if sicil in seen_sicil:
                errors.append(f"Satır {row_number}: aynı Excel içinde mükerrer Sicil No var: {sicil} (ilk satır {seen_sicil[sicil]})")
            else:
                seen_sicil[sicil] = row_number
        if len(errors) >= max_errors:
            errors.append(f"Hata sayısı {max_errors} sınırını geçti; kalan satırlar işlenmedi. Önce şablonu düzeltin.")
            break

    if nonblank_count <= 0:
        errors.append("Excel dosyasında aktarılacak dolu personel satırı bulunamadı.")

    return ExcelImportPreflightResult(
        ok=not errors,
        errors=errors,
        warnings=warnings,
        canonical_headers=canonical_headers,
        column_index=column_index,
        row_count=nonblank_count,
    ).to_dict()
