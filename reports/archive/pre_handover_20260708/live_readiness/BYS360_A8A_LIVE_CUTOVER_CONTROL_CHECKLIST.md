# BYS360 A?ama 8A Ger?ek Canl? Ortam Kontroll? Yay?n Checklist?i

Tarih: 2026-06-12T17:21:25

## ?zet

- Local OK: True
- Karar: A8_READY_FOR_REAL_LIVE_VALIDATION
- Guard script: `scripts\windows\a8_live_cutover_guard.ps1`

## Evidence Referanslar?

- A6 evidence zip: `C:\bys360\releases\BYS360_A6_SECURITY_EVIDENCE_20260612_133606.zip`
- A6 SHA256: `450E720885C790F99BA8A250991A8386392C2C0E9C79CF1E97B5E91C56CB51E2`
- A7 evidence zip: `C:\bys360\releases\BYS360_A7_LIVE_READINESS_EVIDENCE_20260612_135815.zip`
- A7 SHA256: `4FB35400A0D9B31F4B48F065539B4A0CDA1679827CDDBD3746F273402D3447A2`
- Eksik local evidence: []

## Canl? Yay?n ?ncesi / Sonras? Zorunlu Kontroller

### 1. Ger?ek canl? env strict gate
- Durum: pending_live
- Zorunlu: True
- Komut: `powershell -ExecutionPolicy Bypass -File .\scripts\windows\a8_live_cutover_guard.ps1 -Mode ValidateEnv -EnvFile '<CANLI_ENV_YOLU>'`
- Beklenen: A6E_OK=True, A6E_FAILED=0, A8_VALIDATE_ENV_EXIT_CODE=0

### 2. Canl? DB yede?i
- Durum: pending_live
- Zorunlu: True
- Komut: `powershell -ExecutionPolicy Bypass -File .\scripts\windows\pre_live_backup_plan.ps1 -Mode Backup -IncludeDbBackup -DatabaseUrl '<CANLI_DATABASE_URL>'`
- Beklenen: pg_dump exit 0, backup summary olu?mal?

### 3. Servis ve zamanlanm?? g?rev yede?i
- Durum: pending_live
- Zorunlu: True
- Komut: `powershell -ExecutionPolicy Bypass -File .\scripts\windows\pre_live_backup_plan.ps1 -Mode Backup`
- Beklenen: service qc ve scheduled tasks kay?tlar? olu?mal?

### 4. Rollback dosyalar?n?n do?rulanmas?
- Durum: pending_live
- Zorunlu: True
- Komut: `Backup klas?r?nde kod zip, servis kayd?, g?rev kayd?, varsa DB dump kontrol edilir.`
- Beklenen: Kod yede?i SHA256 var, DB dump var, servis/g?rev kay?tlar? var

### 5. Yay?n sonras? ger?ek URL smoke test
- Durum: pending_after_publish
- Zorunlu: True
- Komut: `.\.venv\Scripts\python.exe .\scripts\live_readiness\a7d_local_smoke_contract.py --base-url 'https://bys360.canakkaletarihialan.gov.tr'`
- Beklenen: A7D_OK=True, A7D_FAILED=0

### 6. Manuel canl? ak?? kontrol?
- Durum: pending_after_publish
- Zorunlu: True
- Komut: `Admin/login/dashboard/portal/feedback ekranlar? elle kontrol edilir.`
- Beklenen: Giri?, dashboard, portal, geri bildirim, hata sayfalar? ?al???r

## Rollback Plan?

- Canl? smoke test kritik hata verirse servis durdurulur.
- Son al?nan kod yede?i geri a??l?r.
- Veri bozulmas? varsa PostgreSQL dump geri y?klenir.
- Servis/g?rev ayarlar? A8 yede?ine g?re do?rulan?r.
- Tekrar ger?ek URL smoke test yap?l?r.
- Sonu? raporlanmadan yay?n ba?ar?l? say?lmaz.

## Final Not

A8A sonucu: Yerel evidence ve guard script haz?r. Ger?ek canl? yay?n ?ncesi checklist maddeleri canl? ortamda tamamlanmadan yay?n yap?lmamal?.