# BYS360 Kurumsal Bilgilendirme Merkezi V3.0 Faz 5

Bu overlay, Kurumsal Bilgilendirme Merkezi için gönderim yönetimi, izlenebilirlik, denetim izi ve yönetici kontrol paneli katmanını ekler.

Eklenenler:
- Yönetici kontrol paneli ve hazırlık puanı.
- Mail altyapısı sağlık kontrolü.
- Görev bazlı gönderim ön izleme.
- Gerçek gönderim öncesi onay uyarısı.
- Denetim izi kayıtları.
- Gönderim geçmişi filtreleri.
- Test Merkezi son işlem özeti.
- Sistem Sağlığı ekranı.

Uygulama:
```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE5_CONTROL_PANEL_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_corporate_information_center_v3_0_phase5_control_panel.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```

Kontrol:
```powershell
C:\bys360\project\.venv\Scripts\python.exe scripts\quality\check_corporate_information_center_v3_0_phase5_control_panel.py
```

Beklenen çıktı:
- BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE5_CONTROL_PANEL_APPLY_OK
- BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE5_CONTROL_PANEL_GATE_OK
- BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE5_CONTROL_PANEL_FINAL_OK
