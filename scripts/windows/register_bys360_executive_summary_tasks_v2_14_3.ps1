# ------------------------------------------------------------------------
# KANONIK registrasyon scripti: "BYS360 Executive Summary 0001" / "BYS360
# Executive Summary 0830" Scheduled Task'lari icin TEK gecerli Action kaynagi
# budur. register_bys360_executive_summary_tasks_v2_14_1.ps1 artik kendi
# Action'ini uretmiyor; SADECE bu dosyaya delege eder (bkz. o dosyadaki
# DEPRECATED basligi). Ayni TaskName'in iki farkli mekanizmayla kurulmasi
# artik mumkun degil.
# ------------------------------------------------------------------------
param(
    [string]$ProjectRoot = "C:\bys360\project"
)

$ErrorActionPreference = "Stop"
$python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (!(Test-Path $python)) { throw "Python bulunamadı: $python" }

$logDir = Join-Path $ProjectRoot "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

$morningScript = Join-Path $ProjectRoot "scripts\windows\run_executive_summary_0830.ps1"
$nightScript = Join-Path $ProjectRoot "scripts\windows\run_executive_summary_0001.ps1"

# GUVENLIK KONTRATI: Bu script launcher dosyalarinin ICERIGINI ASLA
# URETMEZ/UZERINE YAZMAZ (Set-Content/Out-File KULLANILMAZ). Launcher'lar
# kaynak kontrollu, elle incelenmis kanonik dosyalardir. Bu script sadece
# mevcut, gecerli launcher'lari Scheduled Task tanimina baglar.
function Assert-LauncherReady {
    param([string]$Path, [string]$Label, [string]$ExpectedFragment)
    if (!(Test-Path $Path)) {
        throw "$Label launcher bulunamadi (bu script bunu URETMEZ; repoda onceden var olmasi gerekir): $Path"
    }
    $ParseErrors = $null
    $null = [System.Management.Automation.Language.Parser]::ParseFile($Path, [ref]$null, [ref]$ParseErrors)
    if ($ParseErrors.Count -gt 0) {
        throw "$Label launcher gecersiz PowerShell sozdizimine sahip: $Path ($($ParseErrors.Count) parse hatasi)"
    }
    $text = Get-Content -Path $Path -Raw
    if (-not $text.Contains($ExpectedFragment)) {
        throw "$Label launcher beklenen icerigi referans etmiyor ('$ExpectedFragment' bulunamadi icinde): $Path"
    }
}

Assert-LauncherReady -Path $morningScript -Label "Executive Summary 0830" -ExpectedFragment "--type morning"
Assert-LauncherReady -Path $nightScript -Label "Executive Summary 0001" -ExpectedFragment "--type night"

# BYS360 DEFECT Y: explicit unattended-service principal -- without this,
# Register-ScheduledTask defaults to the current interactive caller's
# identity/logon type. "BYS360 Executive Summary 0001" fires at 00:01, when
# no operator is realistically logged on -- both tasks need SYSTEM.
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

$actionMorning = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$morningScript`"" -WorkingDirectory $ProjectRoot
$triggerMorning = New-ScheduledTaskTrigger -Daily -At 08:30
Register-ScheduledTask -TaskName "BYS360 Executive Summary 0830" -Action $actionMorning -Trigger $triggerMorning -Principal $Principal -Description "BYS360 Günaydın Yönetici Özeti otomatik mail görevi" -Force | Out-Null

$actionNight = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$nightScript`"" -WorkingDirectory $ProjectRoot
$triggerNight = New-ScheduledTaskTrigger -Daily -At 00:01
Register-ScheduledTask -TaskName "BYS360 Executive Summary 0001" -Action $actionNight -Trigger $triggerNight -Principal $Principal -Description "BYS360 Gece Sistem Kontrolü otomatik mail görevi" -Force | Out-Null

Write-Host "BYS360_EXECUTIVE_SUMMARY_TASKS_REGISTERED"
Get-ScheduledTask -TaskName "BYS360 Executive Summary 0830","BYS360 Executive Summary 0001" | Select-Object TaskName, State
