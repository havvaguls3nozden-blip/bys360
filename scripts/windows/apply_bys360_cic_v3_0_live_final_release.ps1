
param(
    [string]$ProjectRoot = "C:\bys360\project",
    [string]$Mode = "all"
)
$ErrorActionPreference = "Stop"
$releaseCode = "BYS360_CIC_V3_0_LIVE_FINAL_RELEASE"
Write-Host "$releaseCode uygulanıyor..."
Write-Host "ProjectRoot=$ProjectRoot"

if (-not (Test-Path $ProjectRoot)) { throw "ProjectRoot bulunamadi: $ProjectRoot" }
$OverlayRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$OverlayZipRoot = Join-Path $OverlayRoot "overlays"
if (-not (Test-Path $OverlayZipRoot)) { throw "Overlay klasoru bulunamadi: $OverlayZipRoot" }

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupRoot = Join-Path $ProjectRoot ("_overlay_backups\" + $releaseCode + "_" + $timestamp)
New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null
$backupTargets = @(
    "app\templates\corporate_information_center",
    "app\static\css",
    "app\communication\corporate_information_center_routes.py",
    "app\services\corporate_information_center.py",
    "app\auth\routes.py",
    "app\main_handlers\auth_handlers.py",
    "app\error_handlers.py",
    "app\routes.py"
)
foreach ($rel in $backupTargets) {
    $src = Join-Path $ProjectRoot $rel
    if (Test-Path $src) {
        $dst = Join-Path $backupRoot $rel
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
        Copy-Item $src $dst -Recurse -Force
    }
}
Write-Host "Yedek alindi: $backupRoot"

$steps = @(
    @{Zip="BYS360_LOGOUT_FORCE_CLEAR_V2_15_12_OVERLAY.zip"; Script="scripts\windows\repair_bys360_logout_force_clear_v2_15_12.ps1"; AllowFail=$false},
    @{Zip="BYS360_LOGOUT_BASE_CLIENT_HOTFIX_V2_15_13_OVERLAY.zip"; Script="scripts\windows\repair_bys360_logout_base_client_hotfix_v2_15_13.ps1"; AllowFail=$false},
    @{Zip="BYS360_CSRF_MAIN_LOGIN_HOTFIX_V2_15_14_OVERLAY.zip"; Script="scripts\windows\repair_bys360_csrf_main_login_hotfix_v2_15_14.ps1"; AllowFail=$false},
    @{Zip="BYS360_CSRF_FORM_TOKEN_AND_REFERRER_HOTFIX_V2_15_15_OVERLAY.zip"; Script="scripts\windows\repair_bys360_csrf_form_token_and_referrer_hotfix_v2_15_15.ps1"; AllowFail=$false},
    @{Zip="BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE2_3_CSRF_RECIPIENT_UX_OVERLAY.zip"; Script="scripts\windows\repair_corporate_information_center_v3_0_phase2_3_csrf_recipient_ux.ps1"; AllowFail=$false},
    @{Zip="BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE3_DISPATCH_OVERLAY.zip"; Script="scripts\windows\repair_corporate_information_center_v3_0_phase3_dispatch.ps1"; AllowFail=$false},
    @{Zip="BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE4_1_REAL_ADVANCED_UI_OVERLAY.zip"; Script="scripts\windows\repair_corporate_information_center_v3_0_phase4_1_real_advanced_ui.ps1"; AllowFail=$false},
    @{Zip="BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE5_CONTROL_PANEL_OVERLAY.zip"; Script="scripts\windows\repair_corporate_information_center_v3_0_phase5_control_panel.ps1"; AllowFail=$true},
    @{Zip="BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE5_2_FLAT_GATE_FIX_OVERLAY.zip"; Script="scripts\windows\repair_corporate_information_center_v3_0_phase5_2_flat_gate_fix.ps1"; AllowFail=$false},
    @{Zip="BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE6_FINAL_UAT_LIVE_READY_OVERLAY.zip"; Script="scripts\windows\repair_corporate_information_center_v3_0_phase6_final_uat_live_ready.ps1"; AllowFail=$false},
    @{Zip="BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE6_1_STAFF_NOON_MESSAGE_OVERLAY.zip"; Script="scripts\windows\repair_corporate_information_center_v3_0_phase6_1_staff_noon_message.ps1"; AllowFail=$false},
    @{Zip="BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_LIVE_RELEASE_USAGE_OVERLAY.zip"; Script="scripts\windows\repair_corporate_information_center_v3_0_phase7_live_release_usage.ps1"; AllowFail=$false},
    @{Zip="BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_7_RELEASE_CLEAN_UI_OVERLAY.zip"; Script="scripts\windows\repair_corporate_information_center_v3_0_phase7_7_release_clean_ui.ps1"; AllowFail=$false},
    @{Zip="BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_8_BASE_HEADER_PRO_OVERLAY.zip"; Script="scripts\windows\repair_corporate_information_center_v3_0_phase7_8_base_header_pro.ps1"; AllowFail=$false},
    @{Zip="BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_9_BASE_REAL_NEWLINES_FIX_OVERLAY.zip"; Script="scripts\windows\repair_corporate_information_center_v3_0_phase7_9_base_real_newlines_fix.ps1"; AllowFail=$false},
    @{Zip="BYS360_CORPORATE_INFORMATION_CENTER_V3_0_PHASE7_12_ALL_TEMPLATE_MACRO_FIX_OVERLAY.zip"; Script="scripts\windows\repair_corporate_information_center_v3_0_phase7_12_all_template_macro_fix.ps1"; AllowFail=$false}
)

foreach ($step in $steps) {
    $zipPath = Join-Path $OverlayZipRoot $step.Zip
    if (-not (Test-Path $zipPath)) { throw "Nested overlay bulunamadi: $($step.Zip)" }
    Write-Host "--- Uygulaniyor: $($step.Zip)"
    Expand-Archive -LiteralPath $zipPath -DestinationPath $ProjectRoot -Force
    $scriptPath = Join-Path $ProjectRoot $step.Script
    if (-not (Test-Path $scriptPath)) { throw "Script bulunamadi: $($step.Script)" }
    & powershell -ExecutionPolicy Bypass -File $scriptPath -ProjectRoot $ProjectRoot -Mode $Mode
    $exit = $LASTEXITCODE
    if ($exit -ne 0) {
        if ($step.AllowFail) {
            Write-Warning "Beklenen/telafi edilebilir gate uyarisi alindi, sonraki düzeltme paketiyle devam ediliyor: $($step.Zip) ExitCode=$exit"
        } else {
            throw "Adim basarisiz: $($step.Zip) ExitCode=$exit"
        }
    }
}

# Final temel kontrol: final makro uyumluluk ve Python compile
$finalCheck = Join-Path $ProjectRoot "scripts\quality\check_corporate_information_center_v3_0_phase7_12_all_template_macro_fix.py"
if (Test-Path $finalCheck) {
    & (Join-Path $ProjectRoot ".venv\Scripts\python.exe") $finalCheck -ProjectRoot $ProjectRoot
    if ($LASTEXITCODE -ne 0) { throw "Final template/makro kontrolu basarisiz." }
} else {
    Write-Warning "Final kontrol scripti bulunamadi: $finalCheck"
}

& (Join-Path $ProjectRoot ".venv\Scripts\python.exe") -m compileall app scripts | Out-Host
if ($LASTEXITCODE -ne 0) { throw "compileall basarisiz." }

Write-Host "BYS360_CIC_V3_0_LIVE_FINAL_RELEASE_GATE_OK"
Write-Host "BYS360_CIC_V3_0_LIVE_FINAL_RELEASE_FINAL_OK"
Write-Host "Yedek klasoru: $backupRoot"
