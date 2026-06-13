from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

try:
    from faker import Faker  # type: ignore
except Exception:  # Faker zorunlu degil; yoksa guvenli fallback kullanilir.
    Faker = None

DEFAULT_DOMAIN = "example.gov.tr"
UNITS = [
    "Personel ve Destek Hizmetleri",
    "Bilgi Teknolojileri",
    "Egitim ve Performans",
    "Kurumsal Iletisim",
    "Idari Isler",
]
TITLES = ["Memur", "Isci", "Uzman", "Teknik Personel", "Koordinator", "Grup Baskani"]
CATEGORIES = ["Guvenlik", "Temizlik", "Idari Personel", "Teknik Personel", "Deneme Sureli Personel", "Diger"]
FIRST_NAMES = ["Ayse", "Fatma", "Elif", "Zeynep", "Mehmet", "Ahmet", "Mustafa", "Ali", "Can", "Deniz"]
LAST_NAMES = ["Yilmaz", "Kaya", "Demir", "Sahin", "Celik", "Aydin", "Arslan", "Dogan", "Kilic", "Ozkan"]


def fallback_name(i: int) -> tuple[str, str]:
    return FIRST_NAMES[i % len(FIRST_NAMES)], LAST_NAMES[(i * 3) % len(LAST_NAMES)]


def slug(value: str) -> str:
    tr_map = str.maketrans({"ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u", "Ç": "c", "Ğ": "g", "İ": "i", "Ö": "o", "Ş": "s", "Ü": "u"})
    cleaned = value.translate(tr_map).lower()
    return "".join(ch if ch.isalnum() else "." for ch in cleaned).strip(".")


def random_date(start_year: int, end_year: int) -> str:
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return (start + timedelta(days=random.randint(0, delta))).isoformat()


def generate_rows(count: int, domain: str) -> list[dict[str, str]]:
    fake = Faker("tr_TR") if Faker else None
    rows: list[dict[str, str]] = []
    for i in range(1, count + 1):
        if fake:
            first = fake.first_name()
            last = fake.last_name()
        else:
            first, last = fallback_name(i)
        sicil = f"TST{i:05d}"
        email = f"{slug(first)}.{slug(last)}.{i:05d}@{domain}"
        rows.append({
            "sicil_no": sicil,
            "ad": first,
            "soyad": last,
            "ad_soyad": f"{first} {last}",
            "email": email,
            "dogum_tarihi": random_date(1970, 2002),
            "ise_giris_tarihi": random_date(2008, 2026),
            "birim": random.choice(UNITS),
            "unvan": random.choice(TITLES),
            "kategori": random.choice(CATEGORIES),
            "aktif": "1",
            "not": "SAHTE TEST VERISI - GERCEK PERSONEL VERISI DEGILDIR",
        })
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="BYS360 icin gercek personel verisi kullanmadan guvenli fake seed CSV uretir.")
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--domain", default=DEFAULT_DOMAIN)
    parser.add_argument("--output", default="seeds/fake_users_seed.csv")
    args = parser.parse_args()

    if args.domain.lower().endswith("ktb.gov.tr"):
        raise SystemExit("Guvenlik nedeniyle gercek kurum domaini fake seed icin kullanilamaz. example.gov.tr gibi sahte domain kullanin.")

    rows = generate_rows(args.count, args.domain)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Fake seed CSV olusturuldu: {out} ({len(rows)} kayit)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
