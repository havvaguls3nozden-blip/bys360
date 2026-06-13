# BYS360 Technical Debt Cleanup SAFE V18

SAFE V18 yalnızca `app/services/settings/effective_menu.py` dosyasındaki kalan güvenli `manual_fallback_assignment` exception bloklarına log eklemek için hazırlanmıştır.

- Kod dışı dosyalara dokunmaz.
- `.env` ve local SQLite dosyasını silmez.
- Her değişiklikten önce yedek alır.
- Hedef dosyayı her eklemeden sonra compile eder.
- Hata oluşursa son değişikliği geri alır ve devam etmez.
- İsteğe bağlı tüm proje compile + Quality 9 gate çalıştırır.

Önerilen komut:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_technical_debt_cleanup_safe_v18.ps1 -ProjectRoot "C:\bys360\project" -Mode all -OutputRoot "C:\bys360" -MaxPatches 10 -RunCompile
```
