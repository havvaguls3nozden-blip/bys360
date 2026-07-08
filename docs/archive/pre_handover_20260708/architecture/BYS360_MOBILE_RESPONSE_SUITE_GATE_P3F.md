# BYS360 P3F Mobile Response Suite Gate

P3F, P3A-P3E arasındaki mobil API response/smoke kapılarını tek runner altında toplar.

## Kapsam

- P3A: mobil request scenario + runtime route map
- P3B V3: auth, dashboard, BYS360 Asistanı response-code smoke
- P3C V2: personel, KPI, iletişim response-code smoke
- P3D: destek, anket, bildirim response-code smoke
- P3E: performans response-code smoke

## Amaç

Canlı veriye yazmadan, Flask test ortamında mobil API route kırılmalarını, yanlış method kayıtlarını ve 404/405 risklerini yakalamak.

## Komut

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_claude_score_uplift_p3f_mobile_response_suite_gate.ps1 -ProjectRoot "C:\bys360\project" -Mode all -CompileAll -RunAppFactorySmoke -RunSecretGate -RunPytest
```

## Rapor

`reports/architecture/BYS360_MOBILE_RESPONSE_SUITE_GATE_P3F_REPORT.json`
