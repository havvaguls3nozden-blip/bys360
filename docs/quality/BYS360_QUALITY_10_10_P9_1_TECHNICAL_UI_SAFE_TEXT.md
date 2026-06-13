# BYS360 Quality 10/10 P9.1 — Güvenli Teknik Dil Metni Temizliği

Bu paket, P9 analizinde görülen `TECHNICAL_UI_TERM` bulgularının yalnızca güvenli ve kullanıcıya görünen küçük bir bölümünü temizler.

Dokunulan alanlar:

- Kullanıcıya görünen `endpoint`, `debug`, `Teknik Özet`, `Endpoint aktif/eksik` gibi ifadeler
- Mobil hata mesajlarında yanlış/teknik bağlantı ifadeleri
- Asistan metin temizleme listelerinde ham teknik kelimeler
- Bazı Jinja satırlarında `debug` ve `endpoint` kelimelerinin kaynakta düz görünmesini önleyen güvenli anahtar erişimleri

Bu paket API yol mantığını, gerçek rota adreslerini ve veri çağrılarını değiştirmez.

## Uygulama

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P9_1_TECHNICAL_UI_SAFE_TEXT_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p9_1_technical_ui_safe_text.ps1 -ProjectRoot "C:\bys360\project" -DryRun

powershell -ExecutionPolicy Bypass -File .\scripts\windows\apply_bys360_quality_10_10_p9_1_technical_ui_safe_text.ps1 -ProjectRoot "C:\bys360\project"

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_quality_10_10_p3_clean_audit.ps1 -ProjectRoot "C:\bys360\project" -FailOn never

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p7_findings.ps1 -ProjectRoot "C:\bys360\project" -Level P1 -Limit 160
```

Beklenen:

- P0 sıfır kalır.
- P1 düşer.
- `TECHNICAL_UI_TERM` azalır.
