# BYS360 Repo Hygiene P0.2 V2.17.3 Notes

Bu paket uygulama kodunu değiştirmez. V2.17.2 health kontrolünde oluşabilen hatalı `app_factory_ok=false` sonucunu daha net ölçmek için sağlık kontrol scriptini günceller.

## Değişiklikler

- `_local_quarantine`, `.venv`, cache, build, reports ve nested `project/` ağacı aktif teknik borç sayımından ayrıldı.
- `create_app` testi manuel doğrulanan yöntemle çalıştırılır.
- `compileall` ve app factory çıktı kuyrukları rapora yazılır.
- Secret değerleri rapora yazılmaz; yalnızca dosya/satır lokasyonu gösterilir.

## Komutlar

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_repo_hygiene_p0_2_active_audit_health_v2_17_3.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```
