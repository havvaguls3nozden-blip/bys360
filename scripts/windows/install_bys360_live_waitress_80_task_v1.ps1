<#
BYS360 Live Waitress 80 - Scheduled Task Installer (plan/apply v1)
====================================================================

Amac: Canli "BYS360 Live Waitress 80" Windows Scheduled Task'ini guvenli
sekilde kurmak/guncellemek icin PARAMETRIK bir installer (TD-034).

GUVENLIK SOZLESMESI (repodaki eski install_*.ps1 ornekelerinden FARKLI ve
DAHA KATI):
  1) VARSAYILAN calisma modu SADECE PLAN/DRY-RUN'dir. -Apply verilmedikce
     Register-ScheduledTask / Set-ScheduledTask / Start-ScheduledTask /
     Stop-ScheduledTask / Unregister-ScheduledTask / schtasks CAGRILMAZ.
     Varsayilan calistirma sadece kurulacak gorevin PLANINI yazdirir ve
     hicbir sey degistirmeden (exit code 0) biter.
  2) CARPISMA KORUMASI: -Apply verildiginde, ayni isimde bir gorev zaten
     var mi diye kontrol edilir (Get-ScheduledTask). Varsa, mevcut gorevin
     ozeti yazdirilir ve installer SESSIZCE UZERINE YAZMAZ; degistirmek
     icin AYRICA -ConfirmReplace verilmesi gerekir. Bu, repodaki eski
     Install-BysTask deseninden (mevcut gorevi sessizce guncelleyen) BILINCLI
     bir sapmadir: canli, port 80 uzerinden servis veren bir gorev icin
     sessiz uzerine yazma kabul edilemez.
  3) Hicbir parola/kimlik bilgisi parametresi YOKTUR ve hicbir gizli/sifre
     benzeri deger stdout'a veya loga yazilmaz.
  4) Fail-fast: $ErrorActionPreference = "Stop"; on-kosullar (python.exe ve
     run_server.py varligi) dogrulanir, eksikse aciklayici `throw` ile durulur.

Bu script, run_server.py'yi (KOK dizindeki canonical Waitress giris noktasi)
calistirir. Gelistirme-icin-sadece giris noktasi ASLA kullanilmaz. run_server.py,
APP_ENV production/staging oldugunda Waitress'i devreye sokar; APP_PORT
ortam degiskenini (varsayilan 8000) okur. Bu installer, gercek .env
icerigini VARSAYMAZ/OKUMAZ; kendi -Port parametresini (varsayilan 80, gorev
adiyla/dokumantasyonla tutarli) Scheduled Task Action'inin kendi
$env:APP_PORT atamasi araciligiyla acikca gecirir.
#>

param(
    [string]$ProjectRoot = "C:\bys360\project",
    [string]$PythonExe = (Join-Path $ProjectRoot ".venv\Scripts\python.exe"),
    [int]$Port = 80,
    [string]$TaskName = "BYS360 Live Waitress 80",
    [string]$WorkingDirectory = $ProjectRoot,
    [string]$LogPath = (Join-Path "C:\bys360\logs" "bys360_live_waitress_80.log"),
    [switch]$Apply,
    [switch]$ConfirmReplace
)

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# On-kosullar (dry-run modunda dahi dogrulanir; hicbir Scheduled Task
# cagirisi yapilmadan once fail-fast davranmaliyiz).
# ---------------------------------------------------------------------------

if (!(Test-Path $PythonExe)) {
    throw "Python bulunamadi (venv): $PythonExe"
}

$RunServerScript = Join-Path $ProjectRoot "run_server.py"
if (!(Test-Path $RunServerScript)) {
    throw "run_server.py bulunamadi: $RunServerScript (gelistirme-icin-sadece giris noktasi degil - bu installer sadece run_server.py'yi kullanir)"
}

# ---------------------------------------------------------------------------
# Scheduled Task Action tanimini olustur. Task Scheduler action'lari icin
# native bir "environment variable" alani yoktur; bu yuzden bir powershell.exe
# katmani ile once $env:APP_PORT atanir, sonra venv python'u run_server.py
# ile calistirilir. Cikti (stdout+stderr) LogPath'e eklenir (append).
#
# PYTHONUTF8/PYTHONIOENCODING de ayni katmanda aciyla atanir: Windows
# Scheduled Task altinda redirected stdout varsayilan olarak sistem ANSI
# codepage'ini (genellikle cp1252) kullanir, ve bu codepage run_server.py'nin
# Turkce baslangic mesajini (or. "s,"/"i" iceren karakterler) encode edemez --
# canli "BYS360 Live Waitress 80" gorevinde dogrulanan gercek kok neden.
# run_server.py kendi icinde stdout/stderr'i UTF-8'e reconfigure eder (bkz.
# run_server.py:_ensure_utf8_stdio), ama PYTHONIOENCODING'i burada, proses
# baslamadan once acikca ayarlamak ikinci, bagimsiz bir savunma katmanidir:
# Python yorumlayicisinin ilk stdio codec secimini de kapsar, boylece
# _ensure_utf8_stdio calismadan once calisan herhangi bir import-zamanli
# cikti bile etkilenmez.
# ---------------------------------------------------------------------------

$InnerCommand = "`$env:APP_PORT = '$Port'; `$env:PYTHONUTF8 = '1'; `$env:PYTHONIOENCODING = 'utf-8'; & '$PythonExe' '$RunServerScript' *>> '$LogPath'"
$ActionArgument = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command `"$InnerCommand`""

Write-Host "==================================================================="
Write-Host "BYS360 Live Waitress 80 - Scheduled Task Installer (plan/apply v1)"
Write-Host "==================================================================="
Write-Host "TaskName          : $TaskName"
Write-Host "ProjectRoot       : $ProjectRoot"
Write-Host "WorkingDirectory  : $WorkingDirectory"
Write-Host "PythonExe         : $PythonExe"
Write-Host "run_server.py     : $RunServerScript"
Write-Host "Port (APP_PORT)   : $Port"
Write-Host "LogPath           : $LogPath"
Write-Host "Action Execute    : powershell.exe"
Write-Host "Action Argument   : $ActionArgument"
Write-Host "Trigger           : Sistem baslangicinda (AtStartup)"
Write-Host "Principal         : SYSTEM (LogonType=ServiceAccount, RunLevel=Highest)"
Write-Host ""

if ($Apply) {
    Write-Host "APPLY modu: Scheduled Task gercekten kurulacak/guncellenecek."

    $Existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($Existing) {
        Write-Host "UYARI: '$TaskName' adinda bir gorev zaten mevcut. Mevcut ozet:"
        $Existing | Select-Object TaskName, State, TaskPath | Format-List | Out-String | Write-Host

        if (-not $ConfirmReplace) {
            throw "Gorev '$TaskName' zaten mevcut; sessizce uzerine yazilmaz. Degistirmek icin -Apply ile birlikte -ConfirmReplace de gerekli."
        }

        Write-Host "-ConfirmReplace verildi: mevcut gorev guncellenecek."
    }

    # Log dizini yalnizca gercekten APPLY edilecekse (ve carpisma korumasi
    # gecildiyse) olusturulur; dry-run hicbir dosya sistemi degisikligi
    # yapmaz.
    $LogDir = Split-Path -Path $LogPath -Parent
    if ($LogDir -and !(Test-Path $LogDir)) {
        New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
    }

    $Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $ActionArgument -WorkingDirectory $WorkingDirectory
    $Trigger = New-ScheduledTaskTrigger -AtStartup
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    # BYS360 DEFECT Y: explicit unattended-service principal. Without this,
    # Register-ScheduledTask/Set-ScheduledTask default to the CURRENT
    # INTERACTIVE caller's identity with an interactive logon type -- a
    # canli, port-80-serving AtStartup task must run whether or not anyone
    # is logged on, so it needs the well-known SYSTEM service identity with
    # an explicit ServiceAccount logon type (no stored credential needed) and
    # Highest run level (required to bind to a privileged port at boot).
    $Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

    if ($Existing) {
        Set-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal | Out-Null
        Write-Host "Mevcut gorev guncellendi: $TaskName"
    } else {
        Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Description "BYS360 canli Waitress web sunucusu (port $Port), run_server.py uzerinden calisir." | Out-Null
        Write-Host "Yeni gorev olusturuldu: $TaskName"
    }

    Write-Host "BYS360_LIVE_WAITRESS_80_INSTALLER_APPLY_OK"
} else {
    Write-Host "DRY-RUN modu (varsayilan davranis): -Apply verilmedi."
    Write-Host "Hicbir Scheduled Task cagirisi yapilmadi (Register/Set/Get/Unregister-ScheduledTask CAGRILMADI)."
    Write-Host "Mevcut gorev durumu bu modda kontrol edilmez (yan etkisiz plan cikisi)."
    Write-Host "Gercekten kurmak icin: -Apply ekleyin."
    Write-Host "Ayni isimde bir gorev zaten varsa, ayrica -ConfirmReplace de gerekecek."
    Write-Host "BYS360_LIVE_WAITRESS_80_INSTALLER_PLAN_OK"
}
