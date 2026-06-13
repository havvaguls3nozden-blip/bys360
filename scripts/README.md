# BYS360 Scripts

Bu klasör geliştirme, bakım, kontrol ve release hazırlığı için kullanılan yardımcı scriptleri içerir.

Güvenli devir/release zip'i üretirken geçmiş güvenlik bakım scriptleri pakete dahil edilmez. Güncel kaynak içi release komutu:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\build_bys360_secure_release_v1_5.ps1 -ProjectRoot "C:\bys360\project"
```
