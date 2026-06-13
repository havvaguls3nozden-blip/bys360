param(
    [string]$ProjectRoot = (Get-Location).Path,
    [string]$Mode = "audit",
    [switch]$CompileAll
)

$ErrorActionPreference = "Stop"

Write-Host "BYS360 LIVE FULL OVERLAY V2.17.61 kontrolu basliyor..."
Write-Host "ProjectRoot=$ProjectRoot"
Write-Host "Mode=$Mode"

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
    throw "ProjectRoot bulunamadi: $ProjectRoot"
}

# Normal flat overlay konumu
$ScriptPath = Join-Path $ProjectRoot "scripts\live\check_bys360_live_full_overlay_v2_17_61.py"

# Kullanici zipi klasorlu acarsa, scriptin kendi klasorune gore fallback yap.
if (-not (Test-Path -LiteralPath $ScriptPath)) {
    $SelfDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $OverlayRoot = Split-Path -Parent (Split-Path -Parent $SelfDir)
    $FallbackScriptPath = Join-Path $OverlayRoot "scripts\live\check_bys360_live_full_overlay_v2_17_61.py"
    if (Test-Path -LiteralPath $FallbackScriptPath) {
        $ScriptPath = $FallbackScriptPath
    }
}

if (-not (Test-Path -LiteralPath $ScriptPath)) {
    throw "Python kontrol scripti bulunamadi: $ScriptPath"
}

$PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $PythonExe)) {
    $PythonExe = "python"
}

$argsList = @(
    $ScriptPath,
    "--project-root", $ProjectRoot,
    "--mode", $Mode
)

if ($CompileAll) {
    $argsList += "--compile-all"
}

& $PythonExe @argsList
if ($LASTEXITCODE -ne 0) {
    throw "V2.17.61 kontrol scripti hata kodu dondurdu: $LASTEXITCODE"
}
