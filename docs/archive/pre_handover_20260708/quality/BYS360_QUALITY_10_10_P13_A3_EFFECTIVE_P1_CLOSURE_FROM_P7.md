# BYS360 Quality 10/10 P13-A3 — Effective P1 Closure From P7

P13-A2 `raw_p1=1591` gibi hatalı sayı ürettiyse bu paket kullanılmalıdır.

## Neden?

Clean audit JSON içinde bazı alanlar sayı/özet olarak karışabildiği için P13-A2 yanlış alanı ham P1 gibi okuyabilir. P13-A3, kaynak doğruluk için doğrudan P7 analiz komutunun stdout çıktısını esas alır:

```text
P1_findings_found=50
45 | TECHNICAL_UI_TERM
4  | LARGE_FILE_HARD
1  | MANY_REPAIR_SCRIPTS
```

## Kullanım

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY_10_10_P13_A3_EFFECTIVE_P1_CLOSURE_FROM_P7_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

python -m compileall app scripts

powershell -ExecutionPolicy Bypass -File .\scripts\windows\analyze_bys360_quality_10_10_p13_a3_effective_p1_closure_from_p7.ps1 -ProjectRoot "C:\bys360\project"
```

## Çıktılar

```text
reports/quality/bys360_quality_10_10_p13_a3_effective_p1_closure_from_p7_v1.json
reports/quality/bys360_quality_10_10_p13_a3_effective_p1_closure_from_p7_v1.md
reports/quality/bys360_quality_10_10_p13_a3_source_p7_stdout_v1.txt
```

## Beklenen

```text
raw_p1=50
45 | TECHNICAL_UI_TERM
4  | LARGE_FILE_HARD
1  | MANY_REPAIR_SCRIPTS
effective_p1=5
```

## Güvenlik

Bu paket kod değiştirmez. Sadece kapanış raporu üretir.
