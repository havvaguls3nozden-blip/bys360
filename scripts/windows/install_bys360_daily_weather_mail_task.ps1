param(
    [string]$ProjectRoot = "C:\bys360\project",
    [int]$WeatherHour = 8,
    [int]$WeatherMinute = 15,
    [int]$PulseHour = 13,
    [int]$PulseMinute = 0
)

$ErrorActionPreference = "Stop"
Write-Host "BYS360 gunluk personel bilgilendirme maili gorevi V1.4 kuruluyor..."
Write-Host "ProjectRoot=$ProjectRoot"

if (!(Test-Path $ProjectRoot)) { throw "ProjectRoot bulunamadi: $ProjectRoot" }
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (!(Test-Path $Python)) { throw "Python bulunamadi: $Python" }

$WeatherRunner = Join-Path $ProjectRoot "scripts\communication\send_daily_weather_personnel_mail.py"
$PulseRunner = Join-Path $ProjectRoot "scripts\communication\send_daily_pulse_check_mail.py"
if (!(Test-Path $WeatherRunner)) { throw "Weather runner bulunamadi: $WeatherRunner" }
if (!(Test-Path $PulseRunner)) { throw "Pulse runner bulunamadi: $PulseRunner" }

$LogDir = "C:\bys360\logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Install-BysTask {
    param([string]$TaskName,[string]$Runner,[string]$Launcher,[string]$LogPath,[int]$Hour,[int]$Minute,[string]$Description)

    # GUVENLIK KONTRATI: Bu fonksiyon launcher dosyasinin ICERIGINI ASLA
    # URETMEZ/UZERINE YAZMAZ (Set-Content/Out-File KULLANILMAZ). Launcher'lar
    # kaynak kontrollu, elle incelenmis kanonik dosyalardir (orn.
    # scripts\communication\run_daily_weather_personnel_mail.ps1). Bu fonksiyon
    # sadece mevcut, gecerli bir launcher'i Scheduled Task tanimina baglar.
    if (!(Test-Path $Launcher)) {
        throw "Launcher bulunamadi (installer bunu URETMEZ; repoda onceden var olmasi gerekir): $Launcher"
    }

    $ParseErrors = $null
    $null = [System.Management.Automation.Language.Parser]::ParseFile($Launcher, [ref]$null, [ref]$ParseErrors)
    if ($ParseErrors.Count -gt 0) {
        throw "Launcher gecersiz PowerShell sozdizimine sahip: $Launcher ($($ParseErrors.Count) parse hatasi)"
    }

    $LauncherText = Get-Content -Path $Launcher -Raw
    $RunnerLeaf = Split-Path -Path $Runner -Leaf
    if (-not $LauncherText.Contains($RunnerLeaf)) {
        throw "Launcher beklenen runner scriptini referans etmiyor ($RunnerLeaf bulunamadi icinde): $Launcher"
    }

    $Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Launcher`"" -WorkingDirectory $ProjectRoot
    $TriggerTime = (Get-Date).Date.AddHours($Hour).AddMinutes($Minute)
    $Trigger = New-ScheduledTaskTrigger -Daily -At $TriggerTime
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    $Existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($Existing) {
        Set-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings | Out-Null
        Write-Host "Mevcut gorev guncellendi: $TaskName"
    } else {
        Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description $Description | Out-Null
        Write-Host "Yeni gorev olusturuldu: $TaskName"
    }
    Write-Host "Saat: $($Hour.ToString('00')):$($Minute.ToString('00')) | Log: $LogPath"
}

Install-BysTask -TaskName "BYS360 Daily Weather Personnel Mail" -Runner $WeatherRunner -Launcher (Join-Path $ProjectRoot "scripts\communication\run_daily_weather_personnel_mail.ps1") -LogPath (Join-Path $LogDir "daily_weather_personnel_mail.log") -Hour $WeatherHour -Minute $WeatherMinute -Description "BYS360 secili alicilara sabah hava durumu maili gonderir."
Install-BysTask -TaskName "BYS360 Daily Pulse Check Mail" -Runner $PulseRunner -Launcher (Join-Path $ProjectRoot "scripts\communication\run_daily_pulse_check_mail.ps1") -LogPath (Join-Path $LogDir "daily_pulse_check_mail.log") -Hour $PulseHour -Minute $PulseMinute -Description "BYS360 secili alicilara gun ortasi kontrol maili gonderir."

Write-Host "BYS360_DAILY_MAIL_TASKS_V1_4_INSTALL_OK"
