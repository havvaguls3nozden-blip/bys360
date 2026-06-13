param(
    [string]$ProjectRoot = "C:\bys360\project"
)
$ErrorActionPreference = "Stop"

$js = Join-Path $ProjectRoot "app\static\pwa\ios_pwa_performance_mobile_v3_1.js"
$routes = Join-Path $ProjectRoot "app\support\routes.py"
$tabs = Join-Path $ProjectRoot "app\templates\support\_tabs.html"
$list = Join-Path $ProjectRoot "app\templates\support\list.html"

foreach ($p in @($js, $routes, $tabs, $list)) {
    if (!(Test-Path $p)) { throw "Dosya bulunamadı: $p" }
}

$j = Get-Content $js -Raw -Encoding UTF8
$r = Get-Content $routes -Raw -Encoding UTF8
$t = Get-Content $tabs -Raw -Encoding UTF8
$l = Get-Content $list -Raw -Encoding UTF8

if ($j -notmatch 'BYS360_IOS_PWA_V3_1_DASHBOARD_DOM_GUARD_V1') { throw 'Dashboard DOM guard marker yok' }
if ($j -notmatch 'isDashboardPage') { throw 'Dashboard hariç tutma değişkeni yok' }
if ($j -notmatch 'if \(!isPerformancePage \|\| isDashboardPage\) return;') { throw 'Dashboard sayfasında iOS/PWA mobil dönüştürücü durdurulmuyor' }

if ($r -notmatch 'def _can_use_assigned_support_view') { throw 'Bana Atananlar kişi bazlı yetki helper yok' }
if ($r -notmatch 'can_access_menu\(current_user, "support_assigned"\)') { throw 'support_assigned menü haritası yetkisi yok' }
if ($r -notmatch 'def _can_use_all_support_view') { throw 'Tüm Talepler kişi bazlı yetki helper yok' }
if ($r -notmatch 'can_access_menu\(current_user, "support_all"\)') { throw 'support_all menü haritası yetkisi yok' }
if ($r -match 'def support_assigned\(\):\s*\r?\n\s*if not is_manager_family_user\(current_user\):') { throw 'support_assigned eski manager-only kontrolü duruyor' }
if ($r -match 'def support_all\(\):\s*\r?\n\s*if not is_manager_family_user\(current_user\):') { throw 'support_all eski manager-only kontrolü duruyor' }
if ($r -match 'def support_status\(ticket_id: int\):\s*\r?\n\s*if not is_manager_family_user\(current_user\):') { throw 'support_status eski manager-only kontrolü duruyor' }
if ($r -match 'def support_assign\(ticket_id: int\):\s*\r?\n\s*if not is_manager_family_user\(current_user\):') { throw 'support_assign eski manager-only kontrolü duruyor' }
if ($r -notmatch 'can_manage=_can_use_all_support_view\(\)') { throw 'Talep detay can_manage support_all yetkisine bağlı değil' }
if ($r -notmatch 'assignable_users = .*_can_use_all_support_view\(\)') { throw 'Atanabilir kullanıcı listesi support_all yetkisine bağlı değil' }

if ($t -notmatch "support_menu_map.get\('support_all'") { throw 'Destek sekmeleri support_all menü haritasına bağlı değil' }
if ($t -notmatch "support_menu_map.get\('support_assigned'") { throw 'Destek sekmeleri support_assigned menü haritasına bağlı değil' }
if ($l -notmatch 'Yetkili talep görünümü' -and $l -notmatch 'BYS360_SOURCE_SYNC_SUPPORT_ALL_MARKER_V1_2') { throw 'Tüm talepler liste ekranı kaynak markerı yok' }

python -m py_compile $routes
Write-Host "BYS360_LIVE_FIXES_SOURCE_SYNC_V1_2_OK"
