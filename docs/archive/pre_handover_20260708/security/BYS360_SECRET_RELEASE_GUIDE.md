# BYS360 Güvenli Release ve Secret Temizliği

Bu paket BYS360 kaynak kodunun paylaşım, yedekleme ve devir teslim sırasında gizli bilgi taşımamasını sağlar.

## Kapsam

- `.env` ve `.env.*` dosyaları release paketlerine girmez.
- `.env.example` gerçek değer içermeyen örnek dosya olarak oluşturulur.
- `.gitignore` gizli dosya, log, cache, dump, veritabanı ve arşiv çıktıları için güncellenir.
- Kod içinde yeni kullanıcı başlangıç şifresi olarak `123456` kalıntısı aranır.
- Yeni kullanıcılar için merkezi `generate_initial_password()` yardımcı fonksiyonu kullanılır.
- Güvenli release zip’i `dist_secure/` altında üretilir.

## Uygulama

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_SECURE_RELEASE_SECRET_CLEAN_V1_Overlay.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\security\repair_bys360_secure_release_secret_clean_v1.ps1 -ProjectRoot "C:\bys360\project"
python -m compileall app config.py scripts
powershell -ExecutionPolicy Bypass -File .\scripts\security\check_bys360_secure_release_secret_clean_v1.ps1 -ProjectRoot "C:\bys360\project"
```

Beklenen sonuç:

```text
BYS360_SECURE_RELEASE_SECRET_CLEAN_V1_GATE_OK
```

## Güvenli release zip üretimi

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\build_bys360_secure_release_v1.ps1 -ProjectRoot "C:\bys360\project"
```
