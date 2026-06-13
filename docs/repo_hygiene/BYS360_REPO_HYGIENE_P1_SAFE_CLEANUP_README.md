# BYS360 Repo Hijyeni P1 Safe Cleanup V1

Bu overlay, BYS360 kod tabanını bozmadan ilk teknik borç toparlama adımını atmak için hazırlanmıştır.

## Ne yapar?

- `.bak`, `.bak_*`, `.orig`, `.old`, `.tmp`, `.save` ve kökte duran `local_emergency_*.py`, `local_fix_*.py` dosyalarını tespit eder.
- `except/pass`, broad `except`, üretim `print()` ve büyük Python dosyalarını raporlar.
- İstenirse yedek/acil yama kalıntılarını silmez; `C:\bys360\archive\...` altına karantinaya taşır.
- `.gitignore` içine repo hijyeni kurallarını ekleyebilir.
- `reports/repo_hygiene/...` altında JSON ve Markdown rapor üretir.

## Ne yapmaz?

- Çalışan iş kodunu refactor etmez.
- Büyük route/service dosyalarını otomatik bölmez.
- `except/pass` bloklarını otomatik değiştirmez.
- Veritabanına dokunmaz.
- Canlı veri veya `.env` içeriğini okumaz/yazmaz.

## Çalıştırma

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_REPO_HYGIENE_P1_SAFE_CLEANUP_V1_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_repo_hygiene_p1_safe_cleanup_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode audit
```

Rapor düzgünse güvenli temizlik:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_repo_hygiene_p1_safe_cleanup_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode clean
```

Sonra tekrar kirlenmeyi önlemek için:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_repo_hygiene_p1_safe_cleanup_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode gitignore
```

Hepsini birlikte ve compileall ile çalıştırmak için:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_repo_hygiene_p1_safe_cleanup_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode all -CompileAll
```

## Sonraki faz

P1 sonrası önerilen sıra:

1. P2: En riskli 50 `except/pass` bloğunu logger tabanlı hale getirme.
2. P3: Üretim `print()` çağrılarını `current_app.logger` veya modül logger'ına taşıma.
3. P4: En büyük route/service dosyaları için davranış testleri yazma.
4. P5: `corporate_information_center`, `mobile/routes`, `admin/routes` parçalama planı.
