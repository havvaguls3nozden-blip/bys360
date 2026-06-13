# BYS360 P2E — Aktif Mimari Test Kapsamı

Bu paket, `tests/architecture` altındaki tarihsel test birikimini ikiye ayırır:

1. **Aktif kalite kapısı:** Güncel canlı omurga ve mobil API mimari sözleşmesiyle uyumlu testler.
2. **Arşiv/eski sözleşme testleri:** Daha önceki Faz/Faz10/portal/anket/mesaj sözleşmelerine ait, mevcut canlı mimariyle çakışabilen testler.

Varsayılan komut:

```powershell
python -m pytest tests/architecture -q
```

Bu komut artık aktif mimari kapıyı çalıştırır ve eski sözleşme testlerini `skip` olarak raporlar.

Eski testlerin tamamını ayrıca görmek için:

```powershell
$env:BYS360_RUN_LEGACY_ARCHITECTURE_TESTS = "1"
python -m pytest tests/architecture -q
Remove-Item Env:\BYS360_RUN_LEGACY_ARCHITECTURE_TESTS
```

Bu ayrım canlı riskini azaltmak için yapılmıştır; eski testler silinmez, sadece varsayılan CI kalitesinden ayrılır.
