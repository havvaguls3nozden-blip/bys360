# BYS360 DEPLOYMENT.md

Bu dosya BYS360â€™Ä±n yerel geliÅŸtirme, test, canlÄ±ya alma ve geri dÃ¶nÃ¼ÅŸ adÄ±mlarÄ±nÄ± tek yerde toplar. Gizli bilgi, parola, token veya canlÄ± baÄŸlantÄ± deÄŸeri iÃ§ermez.

## 1. Ortamlar

| Ortam | AmaÃ§ | Not |
|---|---|---|
| Lokal geliÅŸtirme | Kod geliÅŸtirme ve hÄ±zlÄ± smoke test | VarsayÄ±lan port 8000/8003 olabilir. |
| Test / staging | Migration, rol-yetki ve kritik akÄ±ÅŸ denemesi | CanlÄ± veriyle karÄ±ÅŸtÄ±rÄ±lmamalÄ±dÄ±r. |
| CanlÄ± | Kurumsal kullanÄ±m | Windows GÃ¶rev ZamanlayÄ±cÄ± + Waitress omurgasÄ±. |

## 2. Temel baÄŸÄ±mlÄ±lÄ±klar

- Python 3.12
- PostgreSQL 15 veya lokal geliÅŸtirme iÃ§in SQLite
- Redis, kullanÄ±lÄ±yorsa cache / rate-limit / queue iÃ§in
- Windows Server Ã¼zerinde Waitress servis/gÃ¶rev yapÄ±sÄ±
- PowerShell 5+ veya PowerShell 7+

## 3. Ä°lk kurulum

```powershell
cd C:\bys360\project
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Lokal test iÃ§in gerÃ§ek canlÄ± `.env` kopyalanmaz. `.env.example` Ã¼zerinden yeni deÄŸerler oluÅŸturulur.

```powershell
Copy-Item .env.example .env
notepad .env
```

## 4. VeritabanÄ± hazÄ±rlÄ±ÄŸÄ±

```powershell
cd C:\bys360\project
.\.venv\Scripts\Activate.ps1
flask db upgrade
```

Migration Ã¶ncesinde mutlaka yedek alÄ±nÄ±r. Yedek prosedÃ¼rÃ¼ iÃ§in `BACKUP_RUNBOOK.md` dosyasÄ±na bakÄ±lÄ±r.

## 5. Lokal smoke test

```powershell
cd C:\bys360\project
.\.venv\Scripts\Activate.ps1
$env:APP_ENV="development"
python -m compileall app config.py scripts migrations
python run.py
```

AyrÄ± PowerShell penceresinde:

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/login" -UseBasicParsing
```

## 6. CanlÄ±ya alma Ã¶zeti

1. Kod deÄŸiÅŸikliÄŸi temiz branch Ã¼zerinde hazÄ±rlanÄ±r.
2. `python -m compileall app config.py scripts migrations` Ã§alÄ±ÅŸtÄ±rÄ±lÄ±r.
3. Kritik testler Ã§alÄ±ÅŸtÄ±rÄ±lÄ±r.
4. VeritabanÄ± yedeÄŸi alÄ±nÄ±r.
5. Dosya yedeÄŸi alÄ±nÄ±r.
6. Migration varsa stagingâ€™de denenir.
7. CanlÄ± gÃ¶rev durdurulur.
8. Kod aktarÄ±lÄ±r.
9. Migration uygulanÄ±r.
10. CanlÄ± gÃ¶rev baÅŸlatÄ±lÄ±r.
11. `/login`, `/healthz` ve kritik ekranlar kontrol edilir.

## 7. CanlÄ± yeniden baÅŸlatma Ã¶rneÄŸi

```powershell
$ErrorActionPreference = "Stop"
$ProjectRoot = "C:\bys360\project"
$TaskName = "BYS360 Live Waitress 80"

cd $ProjectRoot
.\.venv\Scripts\Activate.ps1

Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue

$owners = Get-NetTCPConnection -LocalPort 80 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty OwningProcess -Unique

foreach ($pid in $owners) {
    $p = Get-Process -Id $pid -ErrorAction SilentlyContinue
    if ($p -and $p.ProcessName -match "python|waitress") {
        Stop-Process -Id $pid -Force
    }
}

Start-ScheduledTask -TaskName $TaskName
Start-Sleep -Seconds 8
Invoke-WebRequest -Uri "http://127.0.0.1/login" -UseBasicParsing
```

## 8. Temiz release Ã¼retimi

DoÄŸrudan proje klasÃ¶rÃ¼nÃ¼ zip yapmak yasaktÄ±r. Ã‡Ã¼nkÃ¼ `.env`, `.git`, `instance`, `logs`, SQLite dosyalarÄ± veya geÃ§ici raporlar pakete girebilir.

GÃ¼venli release iÃ§in:

```powershell
cd C:\bys360\project
.\.venv\Scripts\Activate.ps1
python scripts\security\build_bys360_secure_release_v1_5.py --project-root "C:\bys360\project"
```

Ãœretilen zip ayrÄ±ca preflight ile kontrol edilir:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_release_zip_preflight_v1.ps1 -ZipPath "C:\bys360\project\dist_secure\BYS360_SECURE_RELEASE_V1_5_*.zip"
```

## 9. Rollback

CanlÄ±ya alma sonrasÄ± 5xx, beyaz sayfa, migration hatasÄ± veya yetki bozulmasÄ± gÃ¶rÃ¼lÃ¼rse:

1. CanlÄ± gÃ¶rev durdurulur.
2. Son Ã§alÄ±ÅŸan kod yedeÄŸi geri alÄ±nÄ±r.
3. Gerekirse DB yedeÄŸi restore edilir.
4. CanlÄ± gÃ¶rev baÅŸlatÄ±lÄ±r.
5. `/login`, `/healthz`, performans ana ekranÄ± ve mesaj/anket ekranlarÄ± kontrol edilir.

DetaylÄ± geri dÃ¶nÃ¼ÅŸ prosedÃ¼rÃ¼ `BACKUP_RUNBOOK.md` iÃ§indedir.

## Git Geçmişi ve Kaynak Teslim Notu

Handover kaynak zip paketleri `.git/` klasörü içermez. Teslim doğrulaması manifestteki commit, tag ve SHA256 değerleriyle yapılır. Tam Git geçmişi gerektiğinde kurum Git uzak deposu veya ayrıca üretilecek `git bundle` üzerinden teslim edilir.

