# BYS360 Quality 10/10 P11-B1 — Mobile Routes Split Candidate Analizi

Bu paket kod değiştirmez. `app/api/mobile/routes.py` içindeki route fonksiyonları arasından ilk güvenli split adaylarını belirler.

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P11_B1_MOBILE_ROUTES_SPLIT_CANDIDATES_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p11_b1_mobile_routes_split_candidates.ps1 -ProjectRoot "C:\bys360\project" -Limit 160
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p11_b1_mobile_routes_split_candidates_v1.json
reports/quality/bys360_quality_10_10_p11_b1_mobile_routes_split_candidates_v1.md
```

## Güvenlik

Auth, token, password, personel oluşturma, commit/rollback ve büyük DB işlemleri ilk split kapsamına alınmaz. İlk gerçek split sadece küçük ve düşük riskli route grubu üzerinden yapılmalıdır.
