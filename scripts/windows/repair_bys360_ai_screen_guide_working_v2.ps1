param(
    [string]$ProjectRoot = "C:\bys360\project",
    [ValidateSet("apply","verify","all")]
    [string]$Mode = "all",
    [switch]$RunCompile
)

$ErrorActionPreference = "Stop"

function Write-Step([string]$Text) {
    Write-Host ""
    Write-Host "=== $Text ==="
}

$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$OverlayRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
$BasePath = Join-Path $ProjectRoot "app\templates\base.html"
$JsSource = Join-Path $OverlayRoot "app\static\js\bys360_ai_everywhere_v2.js"
$CssSource = Join-Path $OverlayRoot "app\static\css\bys360_ai_everywhere_v2.css"
$JsTarget = Join-Path $ProjectRoot "app\static\js\bys360_ai_everywhere_v2.js"
$CssTarget = Join-Path $ProjectRoot "app\static\css\bys360_ai_everywhere_v2.css"
$ReportDir = Join-Path $ProjectRoot "reports\quality"
$ReportPath = Join-Path $ReportDir "BYS360_AI_SCREEN_GUIDE_WORKING_V2_REPORT.json"

Write-Host "BYS360 AI Ekran Rehberi Working V2"
Write-Host "ProjectRoot=$ProjectRoot"
Write-Host "Mode=$Mode"

function Apply-Fix {
    Write-Step "1) V2 JS/CSS dosyalari kopyalaniyor"
    New-Item -ItemType Directory -Force -Path (Split-Path $JsTarget) | Out-Null
    New-Item -ItemType Directory -Force -Path (Split-Path $CssTarget) | Out-Null
    Copy-Item -LiteralPath $JsSource -Destination $JsTarget -Force
    Copy-Item -LiteralPath $CssSource -Destination $CssTarget -Force

    Write-Step "2) base.html AI rehber include V2 surumune aliniyor"
    if (!(Test-Path -LiteralPath $BasePath)) { throw "base.html bulunamadi: $BasePath" }
    $base = Get-Content -LiteralPath $BasePath -Raw -Encoding UTF8

    $cssBlock = @'
<!-- BYS360_AI_EVERYWHERE_V2_CSS -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/bys360_ai_everywhere_v2.css') }}?v=ai-everywhere-v2-working">
<!-- /BYS360_AI_EVERYWHERE_V2_CSS -->
'@
    $jsBlock = @'
<!-- BYS360_AI_EVERYWHERE_V2_JS -->
<script src="{{ url_for('static', filename='js/bys360_ai_everywhere_v2.js') }}?v=ai-everywhere-v2-working" defer></script>
<!-- /BYS360_AI_EVERYWHERE_V2_JS -->
'@

    $cssPatternV1 = '(?s)<!-- BYS360_AI_EVERYWHERE_V1_CSS -->.*?<!-- /BYS360_AI_EVERYWHERE_V1_CSS -->'
    $jsPatternV1 = '(?s)<!-- BYS360_AI_EVERYWHERE_V1_JS -->.*?<!-- /BYS360_AI_EVERYWHERE_V1_JS -->'
    $cssPatternV2 = '(?s)<!-- BYS360_AI_EVERYWHERE_V2_CSS -->.*?<!-- /BYS360_AI_EVERYWHERE_V2_CSS -->'
    $jsPatternV2 = '(?s)<!-- BYS360_AI_EVERYWHERE_V2_JS -->.*?<!-- /BYS360_AI_EVERYWHERE_V2_JS -->'

    if ($base -match $cssPatternV2) { $base = [regex]::Replace($base, $cssPatternV2, $cssBlock) }
    elseif ($base -match $cssPatternV1) { $base = [regex]::Replace($base, $cssPatternV1, $cssBlock) }
    else { $base = $base -replace '(?s)(\{% block extra_head %\})', ($cssBlock + "`r`n" + '$1') }

    if ($base -match $jsPatternV2) { $base = [regex]::Replace($base, $jsPatternV2, $jsBlock) }
    elseif ($base -match $jsPatternV1) { $base = [regex]::Replace($base, $jsPatternV1, $jsBlock) }
    else { $base = $base -replace '(?s)(</body>)', ($jsBlock + "`r`n" + '$1') }

    Set-Content -LiteralPath $BasePath -Value $base -Encoding UTF8
}

function Verify-Fix {
    Write-Step "3) Kontrat kontrolu"
    $checks = [ordered]@{}
    $base = Get-Content -LiteralPath $BasePath -Raw -Encoding UTF8
    $js = Get-Content -LiteralPath $JsTarget -Raw -Encoding UTF8
    $css = Get-Content -LiteralPath $CssTarget -Raw -Encoding UTF8

    $checks.base_uses_v2_js = $base.Contains("bys360_ai_everywhere_v2.js")
    $checks.base_uses_v2_css = $base.Contains("bys360_ai_everywhere_v2.css")
    $checks.base_no_v1_ai_everywhere_include = (-not $base.Contains("bys360_ai_everywhere_v1.js")) -and (-not $base.Contains("bys360_ai_everywhere_v1.css"))
    $checks.js_exports_v2 = $js.Contains("window.BYS360AIEverywhereV2")
    $checks.js_has_inline_answer = $js.Contains("data-ai-everywhere-answer") -and $js.Contains("renderInlineAnswer")
    $checks.js_uses_canonical_assistant_api = $js.Contains("window.BYS360AssistantModule.open")
    $checks.css_has_answer_style = $css.Contains(".bys360-ai-everywhere-answer")

    $ok = $true
    foreach ($key in $checks.Keys) { if (-not $checks[$key]) { $ok = $false } }

    New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
    $result = [ordered]@{
        package = "BYS360_AI_SCREEN_GUIDE_WORKING_V2"
        generated_at = (Get-Date).ToString("s")
        ok = $ok
        checks = $checks
        rule = "AI destekli ekran rehberi sadece gorsel kart degil; soru tiklandiginda kart icinde cevap uretmeli ve kanonik BYS360 Asistani paneline soruyu aktarabilmelidir."
    }
    $result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
    $result | ConvertTo-Json -Depth 6
    if (-not $ok) { throw "AI ekran rehberi V2 kontrat kontrolu basarisiz." }
}

if ($Mode -in @("apply","all")) { Apply-Fix }
if ($Mode -in @("verify","all")) { Verify-Fix }

if ($RunCompile) {
    Write-Step "4) Python compile kontrolu"
    $py = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (!(Test-Path -LiteralPath $py)) { $py = "python" }
    & $py -m compileall app | Out-Host
}

Write-Host ""
Write-Host "AI EKRAN REHBERI V2 TAMAM: Kart artik kendi icinde cevap uretir ve BYS360 Asistanina soru aktarir."
Write-Host "RAPOR: $ReportPath"
