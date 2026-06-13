# BYS360 Kurumsal Bilgilendirme Merkezi V3.0 Faz 3

Bu overlay Kurumsal Bilgilendirme Merkezi için gönderim akışını güvenli hale getirir.

Eklenenler:
- Kuru çalışma sonucu ekranda kişi bazlı özetlenir.
- Gerçek mail gönderimi öncesinde açık uyarı gösterilir.
- Alıcı boşsa gönderim durdurulur ve anlaşılır uyarı verilir.
- Dry-run ve gerçek gönderimlerde mail log kaydı oluşur.
- Son işlem özeti Test Merkezi ekranında gösterilir.
- Gönderim Geçmişi kuru çalışma / gerçek gönderim ayrımıyla görünür.
- Mail sunucu hataları teknik dil yerine sade Türkçe gösterilir.

Local uygulama:
```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE3_DISPATCH_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_corporate_information_center_v3_0_phase3_dispatch.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```

Kontrol:
```powershell
C:\bys360\project\.venv\Scripts\python.exe scripts\quality\check_corporate_information_center_v3_0_phase3_dispatch.py
```

Beklenen çıktı:
- `BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE3_DISPATCH_APPLY_OK`
- `BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE3_DISPATCH_GATE_OK`
- `BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE3_DISPATCH_FINAL_OK`
