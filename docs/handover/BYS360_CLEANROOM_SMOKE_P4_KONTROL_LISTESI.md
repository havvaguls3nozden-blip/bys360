# BYS360 P4 Temiz Makine / Clean-Room Kontrol Listesi

Oluşturulma zamanı: 2026-06-08T13:08:21

## Amaç
Bu kontrol, P1-P3 ile temizlenmiş kaynak paketin yeni bir makineye veya temiz klasöre devredilebilirliğini doğrulamak için kullanılır.

## Beklenen Geçiş Kriterleri
- Yasaklı klasör/dosya yok: `.env`, `.venv`, `__pycache__`, backup/archive/report/payload kalıntıları.
- Gizli bilgi blocker sayısı: 0.
- Python compileall: başarılı.
- Migration head sayısı: 1.
- Devir teslim dokümanları mevcut.
- İsteğe bağlı app factory smoke testi başarıyla geçer.

## Önerilen Komutlar
```powershell
cd C:\bys360\project
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_cleanroom_smoke_gate_p4.ps1 -ProjectRoot "C:\bys360\releases\BYS360_CLEAN_HANDOVER_SOURCE_P1" -Mode gate
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_cleanroom_smoke_gate_p4.ps1 -ProjectRoot "C:\bys360\releases\BYS360_CLEAN_HANDOVER_SOURCE_P1" -Mode cleanroom -OutputRoot "C:\bys360\releases\BYS360_CLEANROOM_P4"
```
