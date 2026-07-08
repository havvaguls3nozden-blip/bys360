# BYS360 Quality 10/10 P7 — P1 Analiz Paketi

P0 sıfırlandıktan sonra P1 bulgularına kör patch uygulanmamalıdır. Bu paket `reports/quality/bys360_quality_10_10_audit_v1_clean.json` dosyasını okuyup P1 bulgularını kural ve dosya bazında gruplar.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P7_P1_ANALYSIS_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p7_findings.ps1 -ProjectRoot "C:\bys360\project" -Level P1 -Limit 120
```

## Çıktı

Konsolda şunları üretir:

- P1 toplam sayısı
- Kural bazlı dağılım
- Dosya bazlı dağılım
- İlk bulgular listesi
- Muhtemel güvenli kural grupları

Ayrıca JSON raporu üretir:

```text
reports/quality/bys360_quality_10_10_p1_analysis_v1.json
```

Bu çıktıdan sonra P1 düzeltmeleri güvenli, orta riskli ve refactor gerektiren olarak ayrılmalıdır.
