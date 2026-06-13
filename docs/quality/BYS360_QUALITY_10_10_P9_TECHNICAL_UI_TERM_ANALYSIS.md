# BYS360 Quality 10/10 P9 — TECHNICAL_UI_TERM Analiz Paketi

P1 içinde kalan `TECHNICAL_UI_TERM` bulguları kör patch ile düzeltilmemelidir. Çünkü bazıları gerçek kullanıcı ekranı metni, bazıları test/kontrat/dahili kod olabilir.

Bu paket:

- `TECHNICAL_UI_TERM` bulgularını okur,
- satırın gerçek içeriğini çıkarır,
- kullanıcıya görünen metin adayı mı yoksa iç teknik kod mu sınıflandırır,
- rapor üretir.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P9_TECHNICAL_UI_TERM_ANALYSIS_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p9_technical_ui_terms.ps1 -ProjectRoot "C:\bys360\project" -Limit 220
```

Tüm satırları görmek için:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p9_technical_ui_terms.ps1 -ProjectRoot "C:\bys360\project" -Limit 260 -ShowLines
```

## Üretilen rapor

```text
reports/quality/bys360_quality_10_10_p9_technical_ui_analysis_v1.json
```

Bir sonraki P9.1 paketi bu rapora göre yalnızca gerçek kullanıcı ekranı metinlerini temizlemelidir.
