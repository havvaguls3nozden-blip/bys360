param(
    [string]$ProjectRoot = "C:\bys360\project"
)
$ErrorActionPreference = "Stop"
$Version = "BYS360_LIVE_PORTAL_DB_FIX_AFTER_BYS36043_V1_3"
if (!(Test-Path -LiteralPath $ProjectRoot)) { throw "ProjectRoot bulunamadı: $ProjectRoot" }
$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (!(Test-Path -LiteralPath $Python)) { $Python = "python" }

function Quote-ProcessArg {
    param([string]$Arg)
    if ($null -eq $Arg) { return '""' }
    $escaped = $Arg.Replace('"', '\"')
    return '"' + $escaped + '"'
}

$FixPyCandidates = @(
    (Join-Path $PSScriptRoot "repair_bys360_live_portal_db_after_bys36043_v1_3.py"),
    (Join-Path $ProjectRoot "scripts\windows\repair_bys360_live_portal_db_after_bys36043_v1_3.py")
)
$FixPy = $FixPyCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (!$FixPy) { throw "Ana portal DB V1.3 Python scripti bulunamadı." }

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $Python
$psi.WorkingDirectory = $ProjectRoot
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
try { $psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
try { $psi.StandardErrorEncoding = [System.Text.Encoding]::UTF8 } catch {}
$psi.EnvironmentVariables["PYTHONPATH"] = $ProjectRoot
$psi.EnvironmentVariables["BYS360_PROJECT_ROOT"] = $ProjectRoot
$psi.Arguments = ((@($FixPy, "--project-root", $ProjectRoot) | ForEach-Object { Quote-ProcessArg $_ }) -join " ")
$p = New-Object System.Diagnostics.Process
$p.StartInfo = $psi
[void]$p.Start()
$stdout = $p.StandardOutput.ReadToEnd()
$stderr = $p.StandardError.ReadToEnd()
$p.WaitForExit()
$out = @()
if (![string]::IsNullOrWhiteSpace($stdout)) { $out += ($stdout -split "`r?`n") }
if (![string]::IsNullOrWhiteSpace($stderr)) { $out += ($stderr -split "`r?`n") }
$out | ForEach-Object { if ($_ -ne "") { Write-Host $_ } }
if (($p.ExitCode -ne 0) -or (($out -join "`n") -notmatch "BYS360_LIVE_PORTAL_DB_FIX_AFTER_BYS36043_V1_3_GATE_OK")) { throw "$Version gate başarısız oldu." }
Write-Host "$Version`_GATE_OK" -ForegroundColor Green
