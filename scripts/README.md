# BYS360 Scripts

Bu klasör geliştirme, bakım, kontrol ve release hazırlığı için kullanılan yardımcı scriptleri içerir.

Güvenli devir/release zip'i üretirken geçmiş güvenlik bakım scriptleri pakete dahil edilmez. Tek
yetkili (canonical) release komutu:

```powershell
python scripts\release\build_bys360_safe_release.py --root . --output "C:\bys360\dist\bys360_release.zip"
python scripts\release\build_bys360_safe_release.py --verify "C:\bys360\dist\bys360_release.zip"
```

(`scripts\security\build_bys360_secure_release_v1_5.py` ve ona bağlı eski PowerShell
sarmalayıcıları DEPRECATED'dır.)
