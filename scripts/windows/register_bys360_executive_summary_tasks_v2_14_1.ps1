param([string]$ProjectRoot = "C:\bys360\project")
$ErrorActionPreference = "Stop"

# ------------------------------------------------------------------------
# DEPRECATED (v2_14_1): Bu script artik KENDI Scheduled Task action'ini
# KURMAZ. Onceki halinde, bu script ile register_bys360_executive_summary_
# tasks_v2_14_3.ps1 AYNI TaskName'leri ("BYS360 Executive Summary 0001" /
# "BYS360 Executive Summary 0830") FARKLI mekanizmalarla kuruyordu:
#   - v2_14_1 (eski): launcher'siz, inline "-Command" ile python'u dogrudan
#     cagiran bir Action uretiyordu (Assert-LauncherReady / icerik-sozlesmesi
#     kontrolu YOKTU).
#   - v2_14_3 (kanonik): kaynak kontrollu run_executive_summary_0001.ps1 /
#     run_executive_summary_0830.ps1 launcher dosyalarina "-File" ile baglanan,
#     Test-Path + ParseFile + icerik-sozlesmesi (Assert-LauncherReady) ile
#     korunan bir Action uretiyor.
# Hangisi son calistirilirse TaskName'in Action'i O OLUYORDU -> ongorulemeyen
# production davranisi. Bu artik MUMKUN DEGIL: bu script kendi Action'ini
# URETMEZ, sadece kanonik register_bys360_executive_summary_tasks_v2_14_3.ps1
# dosyasina DELEGE EDER. Tek TaskName -> Tek Action tanimi (v2_14_3) garanti
# edilir. Bu dosya sadece geriye-donuk uyumluluk (eski calistirma
# aliskanliklari/runbook referanslari) icin tutuluyor; SILINMEDI.
# ------------------------------------------------------------------------

Write-Host "BYS360_EXECUTIVE_SUMMARY_TASKS_V2_14_1_DEPRECATED: bu script artik dogrudan Scheduled Task kurmuyor."
Write-Host "Kanonik registrasyona (register_bys360_executive_summary_tasks_v2_14_3.ps1) yonlendiriliyor..."
Write-Host "ProjectRoot=$ProjectRoot"

$CanonicalScript = Join-Path $PSScriptRoot "register_bys360_executive_summary_tasks_v2_14_3.ps1"
if (!(Test-Path $CanonicalScript)) {
    throw "Kanonik registrasyon scripti bulunamadi (v2_14_1 artik kendi basina kurulum yapmiyor, bu dosyaya bagimli): $CanonicalScript"
}

& $CanonicalScript -ProjectRoot $ProjectRoot

Write-Host "BYS360_EXECUTIVE_SUMMARY_TASKS_V2_14_1_DELEGATED_TO_V2_14_3_OK"
