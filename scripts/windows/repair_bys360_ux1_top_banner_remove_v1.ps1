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

function Copy-IfDifferentPath([string]$Source, [string]$Target) {
    $srcFull = (Resolve-Path -LiteralPath $Source).Path
    $targetFull = $Target
    if (Test-Path -LiteralPath $Target) { $targetFull = (Resolve-Path -LiteralPath $Target).Path }
    if ($srcFull -ieq $targetFull) {
        Write-Host "Skip same file: $Target"
        return
    }
    New-Item -ItemType Directory -Force -Path (Split-Path $Target) | Out-Null
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}

$ProjectRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$OverlayRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
$BasePath = Join-Path $ProjectRoot "app\templates\base.html"
$JsSource = Join-Path $OverlayRoot "app\static\js\bys360_ux1_simple_screen_guide.js"
$CssSource = Join-Path $OverlayRoot "app\static\css\bys360_ux1_simple_screen_guide.css"
$JsTarget = Join-Path $ProjectRoot "app\static\js\bys360_ux1_simple_screen_guide.js"
$CssTarget = Join-Path $ProjectRoot "app\static\css\bys360_ux1_simple_screen_guide.css"
$ReportDir = Join-Path $ProjectRoot "reports\quality"
$ReportPath = Join-Path $ReportDir "BYS360_UX1_TOP_BANNER_REMOVE_V1_REPORT.json"

Write-Host "BYS360 UX-1 Top Banner Remove V1"
Write-Host "ProjectRoot=$ProjectRoot"
Write-Host "Mode=$Mode"

function Apply-Fix {
    Write-Step "1) UX-1 top banner kaldirma JS/CSS dosyalari uygulanıyor"
    if (!(Test-Path -LiteralPath $JsSource)) { throw "JS kaynak bulunamadi: $JsSource" }
    if (!(Test-Path -LiteralPath $CssSource)) { throw "CSS kaynak bulunamadi: $CssSource" }
    Copy-IfDifferentPath -Source $JsSource -Target $JsTarget
    Copy-IfDifferentPath -Source $CssSource -Target $CssTarget

    Write-Step "2) base.html UX-1 asset cache versiyonu guncelleniyor"
    if (!(Test-Path -LiteralPath $BasePath)) { throw "base.html bulunamadi: $BasePath" }
    $base = Get-Content -LiteralPath $BasePath -Raw -Encoding UTF8

    $cssBlock = @'
<!-- BYS360_UX1_SIMPLE_SCREEN_GUIDE_CSS -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/bys360_ux1_simple_screen_guide.css') }}?v=ux1-top-banner-remove-v1">
<!-- /BYS360_UX1_SIMPLE_SCREEN_GUIDE_CSS -->
'@
    $jsBlock = @'
<!-- BYS360_UX1_SIMPLE_SCREEN_GUIDE_JS -->
<script src="{{ url_for('static', filename='js/bys360_ux1_simple_screen_guide.js') }}?v=ux1-top-banner-remove-v1" defer></script>
<!-- /BYS360_UX1_SIMPLE_SCREEN_GUIDE_JS -->
'@

    $cssPattern = '(?s)<!-- BYS360_UX1_SIMPLE_SCREEN_GUIDE_CSS -->.*?<!-- /BYS360_UX1_SIMPLE_SCREEN_GUIDE_CSS -->'
    $jsPattern = '(?s)<!-- BYS360_UX1_SIMPLE_SCREEN_GUIDE_JS -->.*?<!-- /BYS360_UX1_SIMPLE_SCREEN_GUIDE_JS -->'

    if ($base -match $cssPattern) {
        $base = [regex]::Replace($base, $cssPattern, $cssBlock)
    } elseif ($base -match '(?s)(\{% block extra_head %\})') {
        $base = [regex]::Replace($base, '(?s)(\{% block extra_head %\})', ($cssBlock + "`r`n" + '$1'), 1)
    } else {
        $base = [regex]::Replace($base, '(?s)(</head>)', ($cssBlock + "`r`n" + '$1'), 1)
    }

    if ($base -match $jsPattern) {
        $base = [regex]::Replace($base, $jsPattern, $jsBlock)
    } else {
        $base = [regex]::Replace($base, '(?s)(</body>)', ($jsBlock + "`r`n" + '$1'), 1)
    }

    Set-Content -LiteralPath $BasePath -Value $base -Encoding UTF8
}

function Verify-Fix {
    Write-Step "3) UX-1 top banner remove kontrat kontrolu"
    $checks = [ordered]@{}
    $base = Get-Content -LiteralPath $BasePath -Raw -Encoding UTF8
    $js = Get-Content -LiteralPath $JsTarget -Raw -Encoding UTF8
    $css = Get-Content -LiteralPath $CssTarget -Raw -Encoding UTF8

    $checks.base_uses_ux1_js = $base.Contains("bys360_ux1_simple_screen_guide.js")
    $checks.base_uses_ux1_css = $base.Contains("bys360_ux1_simple_screen_guide.css")
    $checks.base_cache_busts_v1 = $base.Contains("ux1-top-banner-remove-v1")
    $checks.js_exports_contract = $js.Contains("window.BYS360UX1SimpleScreenGuide")
    $checks.js_top_banner_disabled = $js.Contains("topBannerEnabled: false") -and $js.Contains("removeGlobalQuickLogicCard")
    $checks.js_does_not_inject_top_banner_buttons = (-not $js.Contains("data-ux1-toggle-details")) -and (-not $js.Contains("data-ux1-ask-guide")) -and (-not $js.Contains("bys360-ux1-steps"))
    $checks.js_keeps_long_text_simplifier = $js.Contains("simplifyLongTextBlocks") -and $js.Contains("bys360-ux1-more") -and $js.Contains("is-collapsed")
    $checks.css_hides_quick_logic_card = $css.Contains("BYS360_UX1_TOP_BANNER_REMOVE_V1") -and $css.Contains(".bys360-ux1-quick-logic") -and $css.Contains("display: none !important")

    $ok = $true
    foreach ($key in $checks.Keys) { if (-not $checks[$key]) { $ok = $false } }

    New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
    $result = [ordered]@{
        package = "BYS360_UX1_TOP_BANNER_REMOVE_V1"
        generated_at = (Get-Date).ToString("s")
        ok = $ok
        checks = $checks
        rule = "UX-1 global top banner must not render; smaller page-level AI guide and long-text simplification may remain."
    }
    $result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
    $result | ConvertTo-Json -Depth 6
    if (-not $ok) { throw "UX-1 top banner remove contract verify failed." }
}

if ($Mode -in @("apply","all")) { Apply-Fix }
if ($Mode -in @("verify","all")) { Verify-Fix }

if ($RunCompile) {
    Write-Step "4) Python compile kontrolu"
    $py = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (!(Test-Path -LiteralPath $py)) { $py = "python" }
    & $py -m compileall app scripts tests | Out-Host
}

Write-Host ""
Write-Host "UX-1 top banner remove V1 OK."
Write-Host "RAPOR: $ReportPath"
