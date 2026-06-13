# BYS360 Quality 10/10 P14-B — Assistant JS Split Decision

Bu paket kod değiştirmez. P14-A envanterinden sonra `app/static/js/bys360_assistant_module.js` için daha güvenli split karar raporu üretir.

## Neden P14-B?

P14-A regex tabanlı envanterde `if`, `for`, `setTimeout` gibi sahte fonksiyon adayları da görünebilir. P14-B daha seçici davranır:

- Sadece gerçek isimli `function`, `const/let/var = function`, `const/let/var = (...) => {}` yapılarını inceler.
- API, CSRF/token, DOM yazma, event listener, storage ve asistan/chat akışı içeren blokları erteler.
- Küçük ve riskli akışa bağlı olmayan yardımcı fonksiyonları düşük riskli aday olarak ayırır.
- Kod taşımaz.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P14_B_ASSISTANT_JS_SPLIT_DECISION_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p14_b_assistant_js_split_decision.ps1 -ProjectRoot "C:\bys360\project" -Limit 240
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p14_b_assistant_js_split_decision_v1.json
reports/quality/bys360_quality_10_10_p14_b_assistant_js_split_decision_v1.md
```

## Güvenlik

Bu aşamada parçalama yoktur. P14-C gerekirse yalnızca dry-run split planı üretmelidir.
