# BYS360 Performans Tamamlama Faz 2 — Personel Kategori ve Grup Altyapısı

## Amaç

Bu paket Faz 2 kapanışını tek merkeze bağlar. Hedef, Güvenlik, Temizlik, İdari Personel, Teknik Personel, Deneme Süreli Personel ve Diğer kategorilerinin personel kartı, toplu import, performans kapsamı ve raporlama tarafında aynı kurumsal sözleşmeyle çalışmasıdır.

## Kapanış kapsamı

- Personel kartında kategori alanı kurumsal veri olarak tutulur.
- Toplu personel import dosyasında kategori / personel kategorisi / performans kategorisi sütunları desteklenir.
- Performans raporlarında kategori filtresi aktif kalır.
- Kategori ortalaması kişi detayı göstermeden hesaplanır.
- Kategori dönem/kapsam hazırlığı V2.1.4, V2.1.5 ve V2.1.6 ekranlarıyla uyumlu çalışır.
- Varsayılan kategori seti tek merkezden yönetilir.

## Varsayılan kategoriler

| Anahtar | Görünen ad |
|---|---|
| `guvenlik` | Güvenlik |
| `temizlik` | Temizlik |
| `idari_personel` | İdari Personel |
| `teknik_personel` | Teknik Personel |
| `deneme_sureli_personel` | Deneme Süreli Personel |
| `diger` | Diğer |

## Kontrol komutu

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_performance_completion_phase2_category_center.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```

Başarı çıktısı:

```text
BYS360_PERFORMANCE_COMPLETION_PHASE2_CATEGORY_CENTER_APPLY_OK
```

## Canlı kapanış testi

1. Personel ekleme/düzenleme ekranında kategori alanı görünüyor olmalı.
2. Excel import şablonunda kategori sütunu okunmalı.
3. Bir personele Güvenlik veya Temizlik kategorisi atanmalı.
4. `/performance/v2-1-3-personnel-category-card` ekranında atama görünmeli.
5. `/performance/v2-1-4-category-scope` ekranında kategori özeti kişi detayı sızdırmadan görünmeli.
6. `/performance/v2-1-5-category-period-scope` ekranında kategoriye özel dönem kapsamı hazırlanmalı.
7. `/performance/v2-1-6-category-period-integration` ekranında plan dönem bağlantısı ön kontrolü yapılmalı.
8. Raporlarda kategori ortalaması yalnızca özet bilgi olarak görünmeli; kişi listesi gösterilmemeli.

## Rollback

Paket çekirdek personel tablosundaki mevcut kayıtları silmez. Geri almak gerekirse overlay ile gelen şu dosyalar önceki yedekten döndürülebilir:

- `app/services/performance/phase2_category_center.py`
- `app/services/personnel/categories.py`
- `scripts/performance/check_bys360_performance_completion_phase2_category_center.py`
- `scripts/performance/repair_bys360_performance_completion_phase2_category_center.py`
- `scripts/windows/repair_bys360_performance_completion_phase2_category_center.ps1`
