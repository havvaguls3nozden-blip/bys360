# BYS360 P3C Mobile Personnel/KPI/Communication Response Gate

Bu paket P3B sonrası mobil API kalite zincirini personel, KPI ve iletişim endpointlerine genişletir.

## Kontroller

- `app/api/mobile/routes.py` ince facade olarak kalır.
- Mobil route decorator sayısı 24 olarak korunur.
- Personel, KPI ve iletişim endpointleri domain dosyalarında beklenen method/suffix ile yer alır.
- Flask `app.url_map` üzerinden runtime route haritası doğrulanır.
- `test_client` ile response-code smoke yapılır; 404/405 route kırılmaları yakalanır.
- App factory, secret gate ve hedefli pytest birlikte çalışır.

## Komut

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_claude_score_uplift_p3c_mobile_personnel_kpi_communication_response_gate.ps1 -ProjectRoot "C:\bys360\project" -Mode all -CompileAll -RunAppFactorySmoke -RunSecretGate -RunPytest
```
