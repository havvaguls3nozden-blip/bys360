# BYS360 Kurumsal Bilgilendirme Merkezi V3.0 Faz 6 — Final UAT ve Canlı Hazırlık

Bu overlay, Kurumsal Bilgilendirme Merkezi için final UAT senaryo kapısı ve canlıya hazırlık kontrollerini ekler.

## Eklenen ana başlıklar
- 10 senaryo Final UAT kontrol paneli
- Canlıya hazırlık puanı
- Gerçek gönderim son kontrol kapısı
- Alıcı veri kalitesi özeti
- Şablon canlı yayın kontrolü
- Denetim ve izlenebilirlik özeti
- Sistem ekranında canlı öncesi kritik uyarılar
- UAT rapor dokümanı

## Uygulama
```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE6_FINAL_UAT_LIVE_READY_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_corporate_information_center_v3_0_phase6_final_uat_live_ready.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```

## Kontrol
```powershell
C:\bys360\project\.venv\Scripts\python.exe scripts\quality\check_corporate_information_center_v3_0_phase6_final_uat_live_ready.py -ProjectRoot "C:\bys360\project"
```

## Beklenen çıktı
- BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE6_FINAL_UAT_LIVE_READY_APPLY_OK
- BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE6_FINAL_UAT_LIVE_READY_GATE_OK
- BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE6_FINAL_UAT_LIVE_READY_FINAL_OK
