# BYS360 LIVE FULL OVERLAY V2.17.60

Bu overlay, yüklenen son BYS360 proje paketi üzerinde görülen canlı kritiklerini tek pakette toparlamak için hazırlanmıştır.

## Kapsam

- `base.html` kuyruk yapısını temizler: bölünmüş `</body>` etiketi, `</html>` sonrası kalan script/link parçaları ve mükerrer canlı blokları toparlanır.
- POST formları için CSRF meta + form senkronizasyon katmanı ekler.
- CSRF süresi dolduğunda korumayı kapatmadan kullanıcıyı geldiği ekrana güvenli şekilde döndürür.
- Logout akışında istemci cache/session temizleme davranışını korur.
- Syntax probe raporunda görülen UTF-8 BOM kaynaklı Python dosyalarını temizler.
- Canlı UI için küçük responsive/taşma koruma CSS katmanı ekler.
- Kontrol scripti raporu `reports/quality/bys360_live_full_overlay_v2_17_60_report.*` olarak üretir.

## Uygulama

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_LIVE_FULL_OVERLAY_V2_17_60.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_live_full_overlay_v2_17_60.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```

## Kontrol

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_live_full_overlay_v2_17_60.ps1 -ProjectRoot "C:\bys360\project"
```

## Geri alma

Uygulama çıktısında yedek klasörü yazılır.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\rollback_bys360_live_full_overlay_v2_17_60.ps1 -ProjectRoot "C:\bys360\project" -BackupRoot "C:\bys360\backups\BYS360_LIVE_FULL_V2.17.60_YYYYMMDD_HHMMSS"
```

## Not

Bu paket `.env`, şifre, canlı veritabanı bağlantısı veya kullanıcı verisi içermez. Mevcut iş kurallarını gevşetmez; CSRF ve yetki kontrolleri korunur.
