# BYS360 Dosya Merkezi Canlı Sertleştirme V1L

Bu paket Dosya Merkezi modülünü canlıya daha güvenli taşımak için hazırlanmıştır.

## Kapsam

- Windows sabit depolama yolu kaldırıldı; canlıda `FILE_CENTER_STORAGE_ROOT` zorunlu hale getirildi.
- Misafir indirme/yükleme uçlarında beklenmeyen teknik hata mesajları kullanıcıya sızdırılmaz; audit log'a yazılır.
- Flask-Limiter uygulama başlangıcına bağlandı ve Dosya Merkezi uçlarına endpoint bazlı limit eklendi.
- Tek bakım döngüsü eklendi: süresi dolan link/istek kapatma, kota yeniden hesaplama, bekleyen güvenlik taraması ve disk kullanım alarmı.
- Opsiyonel ClamAV entegrasyonu eklendi. Kapalıysa güvenlik ekranında açık uyarı gösterilir.
- `.env` / secret hygiene denetimi ve backup içi `.env` taşıma scriptleri eklendi.
- Statik güvenlik testleri eklendi.

## Uygulama

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_FILE_CENTER_LIVE_HARDENING_V1L_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\install_file_center_live_hardening_v1l.ps1 -ProjectRoot "C:\bys360\project" -SecretHygiene -InstallScheduledTask
```

## Canlı ortam değişkenleri

```env
FILE_CENTER_STORAGE_ROOT=D:/bys360_storage/file_center
FILE_CENTER_ENABLED=true
FILE_CENTER_GUEST_LINKS_ENABLED=true
FILE_CENTER_GUEST_UPLOADS_ENABLED=true
FILE_CENTER_SECURITY_SCAN_ENABLED=true
FILE_CENTER_AUTO_SCAN_ON_UPLOAD=true
FILE_CENTER_REQUIRE_CLEAN_BEFORE_DOWNLOAD=true
FILE_CENTER_CLAMAV_ENABLED=false
FILE_CENTER_CLAMAV_COMMAND=clamscan --no-summary --infected
FILE_CENTER_DISK_ALERT_PERCENT=85
ENABLE_API_RATE_LIMIT=true
RATELIMIT_STORAGE_URI=memory://
```

Redis varsa `RATELIMIT_STORAGE_URI=redis://127.0.0.1:6379/1` önerilir. ClamAV kurulunca `FILE_CENTER_CLAMAV_ENABLED=true` yapılabilir.

## Kontrol

```powershell
cd C:\bys360\project
.\.venv\Scripts\Activate.ps1
python -m pytest tests\security\test_file_center_v1l_hardening_static.py -q
python scripts\local\audit_file_center_secret_hygiene_v1l.py
python scripts\local\file_center_ops_tick_v1l.py
```

## Önemli güvenlik notu

Bu paket `.env` dosyalarını release dışına iter ve backup kopyalarını karantinaya taşıyabilir; ancak daha önce paylaşılmış gerçek DB/SMTP bilgileri varsa bunların kurum tarafında değiştirilmesi gerekir. Script, sızmış parolayı otomatik güvenli hale getiremez.
