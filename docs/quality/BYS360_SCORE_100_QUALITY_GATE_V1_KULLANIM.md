# BYS360 SCORE 100 QUALITY GATE V1

Bu paket, BYS360 saha değerlendirme raporunda puan kırdıran başlıkları tek komutla ölçen kalite kapısıdır.

## Hedef

Yeni özellik eklemek değil; kalite, güvenlik ve sürdürülebilirlik kapılarını kanıtlı hale getirmek.

Ana kontroller:

1. Bağımlılık/CVE kapısı
2. Android release signing örnek dosyası secret kapısı
3. `.env` ve secret sızıntısı kapısı
4. TCKN şifreleme karar/uygulama kapısı
5. Duplicate endpoint testinin CI'da aktifliği
6. App factory duplicate route kontrolü
7. `exec()` / `compile()` kalıntıları
8. Wildcard import kapısı
9. Geniş `except Exception` borcu
10. Ruff, repo büyüklüğü ve teslim hijyeni

## Kurulum

Overlay zip dosyasını proje köküne açın:

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_SCORE_100_QUALITY_GATE_V1_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
```

## 1. İlk audit

Dosya değiştirmez:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_score100_quality_gate_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode audit
```

Daha güçlü audit:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_score100_quality_gate_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode audit -RunPipAudit -RunRuff -RunAppFactoryDuplicateCheck
```

## 2. Güvenli otomatik düzeltme

Yalnızca düşük riskli işlemleri yapar:

- `key.properties.example` içindeki parola alanlarını placeholder yapar.
- `.gitignore` içine yerel secret ve Android imza dosyaları için kurallar ekler.
- Değişikliklerden önce `.score100_v1.bak` yedeği alır.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_score100_quality_gate_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode fix-safe
```

## 3. Gate modu

CI veya final kontrol için kullanılır. FAIL varsa exit code 1 döner:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_score100_quality_gate_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode gate -RunPipAudit -RunRuff -RunAppFactoryDuplicateCheck
```

## Rapor konumu

Varsayılan raporlar:

```text
reports\quality\score100_quality_gate_v1\BYS360_SCORE100_QUALITY_GATE_V1_REPORT.md
reports\quality\score100_quality_gate_v1\BYS360_SCORE100_QUALITY_GATE_V1_REPORT.json
```

## 100 puan için kapatma sırası

1. `FAIL` bulguları kapatılır.
2. Sadece gerçek ve gerekçeli istisnalar allowlist'e alınır.
3. `WARN` bulguları ayrı teknik borç paketine dönüştürülür.
4. Gate modu yeşile dönmeden yeni özellik geliştirilmez.

## Önemli not

Bu paket canlı iş kuralı değiştirmez, veri tabanı migration yapmaz, route refactor'u otomatik uygulamaz. Ama hangi noktaların 100 puanı engellediğini net ve tekrar çalıştırılabilir şekilde gösterir.
