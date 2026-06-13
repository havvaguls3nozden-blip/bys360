# BYS360 Quality 10/10 P10 — Kalan P1 Final Triage

P9.4 sonrası durum:

- P0: 0
- P1: 59
- Flutter analyze: No issues found
- Kalan P1 dağılımı: TECHNICAL_UI_TERM 50, LARGE_FILE_HARD 8, MANY_REPAIR_SCRIPTS 1

Bu aşamada kör patch yapılmamalıdır. Kalan teknik ifadelerin çoğu gerçek kullanıcı metni değil, çekirdek kod / API sözleşmesi / template route anahtarıdır.

Bu paket düzeltme yapmaz. Kalan P1 kayıtlarını şu kararlara ayırır:

- `INTERNAL_CODE_FALSE_POSITIVE`
- `LIKELY_FALSE_POSITIVE`
- `TEXT_REVIEW`
- `DOMAIN_TERM_REVIEW`
- `REFACTOR_PLAN`
- `PROCESS_PLAN`

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P10_REMAINING_P1_TRIAGE_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p10_remaining_p1_triage.ps1 -ProjectRoot "C:\bys360\project" -Limit 160
```

## Üretilen rapor

```text
reports/quality/bys360_quality_10_10_p10_remaining_p1_triage_v1.json
```

## Sonraki karar

Triage çıktısına göre:

1. Gerçek kullanıcı metni kalan varsa küçük P10.1 metin patch'i yapılır.
2. False-positive ağırlıktaysa kalite audit kuralı UI kapsamına göre iyileştirilir.
3. `LARGE_FILE_HARD` için ayrı refactor planı hazırlanır, doğrudan parçalama yapılmaz.
4. `MANY_REPAIR_SCRIPTS` için eski repair/hotfix scriptlerini arşiv/CI düzenine alma planı yapılır.
