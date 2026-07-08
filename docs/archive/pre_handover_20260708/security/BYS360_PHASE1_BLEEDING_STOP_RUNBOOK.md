# BYS360 Phase 1 — Kanamayı Durdurma SAFE V1

Bu paket Aşama 1 için hazırlanmıştır. Amaç yeni özellik eklemek değil, canlıya ve teslim paketlerine gidebilecek kritik riskleri durdurmaktır.

## Kapsam

1. `app/bootstrap/operational_logging.py` içinde logging filtresinin kendi içinden tekrar log basarak `RecursionError` üretme riskini kaldırır.
2. `scripts/quality/bys360_secret_repo_gate.py` içine repo/paket hijyen kontrolü ekler:
   - `instance/`
   - `*.sqlite3`, `*.sqlite`, `*.db`, `*.dump`
   - `.env`, `.env.*` gerçek dosyaları
   - `*.bak`, `*.bak_*`, `.gitignore.bak_*`, `*.disabled_by_rollback`
   - keystore/key/pem/pfx/jks gibi hassas dosyalar
3. `scripts/release/build_bys360_safe_release.py` ekler. Mümkünse `git archive` kullanır; üretilen zip içinde yasaklı dosya varsa paketi başarısız sayar.
4. `seeds/fake_seed.py` ekler. Gerçek personel verisi yerine `example.gov.tr` domainli sahte CSV üretir.
5. CI içine güvenli release audit adımı ekler.

## Uygulama

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_PHASE1_BLEEDING_STOP_SAFE_V1_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_phase1_bleeding_stop_safe_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode all -RunCompile
```

## Güvenli paket üretme

Önce gerçek DB dosyasını proje klasöründen çıkarın veya karantinaya alın. Sonra:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_phase1_bleeding_stop_safe_v1.ps1 -ProjectRoot "C:\bys360\project" -Mode audit -RunSecretGate -BuildSafeRelease -OutputRoot "C:\bys360\releases"
```

## Fake seed üretme

```powershell
.\.venv\Scripts\python.exe .\seeds\fake_seed.py --count 322 --output .\seeds\fake_users_seed.csv
```

`@ktb.gov.tr` domaini özellikle engellenmiştir. Fake veride gerçek kurum domaini kullanılmamalıdır.

## Beklenen sonuç

- Logging recursion riski kapanır.
- Secret/repo gate artık SQLite/instance/bak dosyalarını yakalar.
- Teslim zipi kontrollü üretilir.
- Geliştirme/pilot için gerçek personel verisi yerine sahte veri kullanılabilir.
