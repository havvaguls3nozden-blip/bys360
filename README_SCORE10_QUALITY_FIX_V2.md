# BYS360 Score10 Quality Fix V2

Bu paket V1 sonrası gerçek pytest çıktısında kalan kalite sözleşmesi senkronlarını kapatır.

## Kapsam

- Mobil API gate scriptlerinde eski `24 route` beklentisi güncel `28 route` sözleşmesine çekildi.
- Route snapshot baseline, mevcut kontrollü route haritası olan `1049` sözleşme anahtarına güncellendi.
- Android responsive P5A/P5B evidence raporları eklendi.
- Phase2 evidence gate test modunda çalışma alanı kirli olduğu için yanlış negatif üretmeyecek şekilde ayrıştırıldı; CLI modunda git temizliği korunur.
- CI workflow adı test sözleşmesiyle uyumlu hale getirildi: `name: Run tests`.

## Uygulama sonrası önerilen kontroller

```powershell
$env:BYS360_RUN_LEGACY_ARCHITECTURE_TESTS="1"
$env:SECRET_KEY="bys360-local-test-secret-key"
pytest
ruff check app
```
