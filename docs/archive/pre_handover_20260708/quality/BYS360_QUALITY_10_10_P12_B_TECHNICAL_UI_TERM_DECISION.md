# BYS360 Quality 10/10 P12-B — Technical UI Term Decision

Bu paket uygulama kodunu değiştirmez. P12-A1 tarafından bulunan 45 teknik UI terimini karar raporuna bağlar.

## Ne yapar?

- Gerçek kullanıcı metni olmayan import, endpoint sabiti, ApiException/ApiClient kodu, debug bayrağı, Jinja endpoint değişkeni gibi satırları kabul edilen false positive olarak ayırır.
- Manuel inceleme gerektiren satırları listeler.
- Etkili P1 tahminini hesaplar.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P12_B_TECHNICAL_UI_TERM_DECISION_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p12_b_technical_ui_term_decision.ps1 -ProjectRoot "C:\bys360\project"
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p12_b_technical_ui_term_decision_v1.json
reports/quality/bys360_quality_10_10_p12_b_technical_ui_term_decision_v1.md
```

## Güvenlik

Bu aşamada kod patch’i yapılmaz. Çünkü görünen 45 bulgunun büyük kısmı kullanıcı metni değil, kalite kuralı false-positive sonucudur. Endpoint URL değerleri ve sınıf/import isimleri otomatik değiştirilmemelidir.
