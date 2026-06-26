param(
    [string]$ProjectRoot = "C:\bys360\project",
    [string]$Mode = "all",
    [switch]$RunCompile
)

$ErrorActionPreference = "Stop"

Write-Host "BYS360 effective_menu facade V1"
Write-Host "ProjectRoot=$ProjectRoot"
Write-Host "Mode=$Mode"

Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) { $Python = "python" }

$Transform = @'
from __future__ import annotations

from pathlib import Path

root = Path.cwd()
target = root / "app" / "services" / "settings" / "effective_menu.py"
parts_dir = root / "app" / "services" / "settings" / "effective_menu_parts"
runtime = parts_dir / "runtime_policy_context.py"

text = target.read_text(encoding="utf-8-sig")
manual_marker = "# BYS360_SETTINGS_MANUAL_V1_EFFECTIVE_MENU_BEGIN"
wrapper_marker = "# BYS360_PERFORMANCE_V2_1_3C_EFFECTIVE_MENU_FORCE_BEGIN"
if manual_marker not in text:
    raise SystemExit(f"Beklenen marker bulunamadi: {manual_marker}")
if wrapper_marker not in text:
    raise SystemExit(f"Beklenen marker bulunamadi: {wrapper_marker}")

start = text.index(manual_marker)
end = text.index(wrapper_marker)
pre = text[:start]
block = text[start:end]
post = text[end:]

# The extracted block was originally top-level code in effective_menu.py. It must now
# mutate effective_menu globals passed as ns, not runtime_policy_context globals.
block = block.replace("globals()", "ns")

prelude = '''from __future__ import annotations\n\nfrom typing import Any\n\n\ndef apply_runtime_policy_blocks(ns: dict[str, Any], *, logging: Any) -> None:\n    """Apply effective_menu runtime policy blocks to caller globals.\n\n    This module keeps app.services.settings.effective_menu as a small facade while\n    preserving the original import-time policy mutation order. The caller passes\n    its globals() mapping as ns.\n    """\n    CORE_MENU_VISIBILITY_POLICY = ns["CORE_MENU_VISIBILITY_POLICY"]\n    ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS = ns["ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS"]\n    PHASE3_PERFORMANCE_MENU_POLICY = ns.get("PHASE3_PERFORMANCE_MENU_POLICY")\n    PHASE3_2_PERFORMANCE_MENU_POLICY = ns.get("PHASE3_2_PERFORMANCE_MENU_POLICY")\n    PHASE3_2_MANAGER_VISIBLE_KEYS = ns.get("PHASE3_2_MANAGER_VISIBLE_KEYS")\n    PHASE3_2_GENERAL_VISIBLE_KEYS = ns.get("PHASE3_2_GENERAL_VISIBLE_KEYS")\n    PERFORMANCE_ROLE_MATRIX_KEYS = ns.get("PERFORMANCE_ROLE_MATRIX_KEYS")\n\n'''
indented = "".join("    " + line if line.strip() else line for line in block.splitlines(True))
epilogue = '''\n    for _name, _value in list(locals().items()):\n        if _name.startswith("_BYS360_") or _name in {\n            "CORE_MENU_VISIBILITY_POLICY",\n            "ROLE_MATRIX_RUNTIME_AUTHORITY_KEYS",\n            "PORTAL_MENU_VISIBILITY_POLICY",\n            "PORTAL_ROLE_MATRIX_V2_12_KEYS",\n            "PORTAL_ROLE_MATRIX_V2_12_DEFAULTS",\n        }:\n            ns[_name] = _value\n'''

runtime.write_text(prelude + indented + epilogue, encoding="utf-8", newline="\n")

facade_call = '''# Phase4J EFFECTIVE_MENU_FACADE_V1 runtime policy blocks\nfrom app.services.settings.effective_menu_parts.runtime_policy_context import (\n    apply_runtime_policy_blocks,\n)\n\napply_runtime_policy_blocks(globals(), logging=logging)\n\n'''
new_text = pre + facade_call + post

target.write_text(new_text, encoding="utf-8", newline="\n")

print(f"effective_menu.py lines: {len(new_text.splitlines())}")
print(f"runtime_policy_context.py lines: {len((prelude + indented + epilogue).splitlines())}")
'@
$TransformPath = Join-Path $ProjectRoot "_effective_menu_facade_v1_transform.py"
Set-Content -LiteralPath $TransformPath -Value $Transform -Encoding UTF8

try {
    Write-Host "`n=== 1) effective_menu facade refactor uygulanıyor ==="
    & $Python $TransformPath
}
finally {
    Remove-Item -LiteralPath $TransformPath -Force -ErrorAction SilentlyContinue
}

$Verify = @'
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

root = Path.cwd()
target = root / "app" / "services" / "settings" / "effective_menu.py"
runtime = root / "app" / "services" / "settings" / "effective_menu_parts" / "runtime_policy_context.py"
report_dir = root / "reports" / "quality"
report_dir.mkdir(parents=True, exist_ok=True)
report = report_dir / "BYS360_EFFECTIVE_MENU_FACADE_V1_REPORT.json"

eff_text = target.read_text(encoding="utf-8")
runtime_text = runtime.read_text(encoding="utf-8")

checks = {
    "effective_menu_under_400_lines": len(eff_text.splitlines()) < 400,
    "runtime_policy_context_exists": runtime.exists(),
    "runtime_policy_context_under_800_lines": len(runtime_text.splitlines()) < 800,
    "facade_imports_runtime_policy_blocks": "apply_runtime_policy_blocks" in eff_text,
    "effective_menu_keeps_build_public_api": "build_menu_visibility_map" in eff_text,
    "runtime_has_no_exec_call": "exec(" not in runtime_text and "eval(" not in runtime_text,
    "runtime_exports_bys360_constants_to_caller": "_name.startswith(\"_BYS360_\")" in runtime_text,
}
result = {
    "package": "BYS360_EFFECTIVE_MENU_FACADE_V1",
    "generated_at": datetime.now().isoformat(timespec="seconds"),
    "ok": all(checks.values()),
    "effective_menu_lines": len(eff_text.splitlines()),
    "runtime_policy_context_lines": len(runtime_text.splitlines()),
    "checks": checks,
    "rule": "effective_menu.py facade olmalı; büyük runtime politika blokları effective_menu_parts altına taşınmalı.",
}
report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
if not result["ok"]:
    raise SystemExit("effective_menu facade kontrat kontrolu basarisiz.")
'@
$VerifyPath = Join-Path $ProjectRoot "_effective_menu_facade_v1_verify.py"
Set-Content -LiteralPath $VerifyPath -Value $Verify -Encoding UTF8
try {
    Write-Host "`n=== 2) Facade kontrat kontrolü ==="
    & $Python $VerifyPath
}
finally {
    Remove-Item -LiteralPath $VerifyPath -Force -ErrorAction SilentlyContinue
}

if ($RunCompile -or $Mode -eq "all") {
    Write-Host "`n=== 3) Python compile kontrolü ==="
    & $Python -m compileall app\services\settings tests\quality
}

Write-Host "`neffective_menu facade V1 OK."
Write-Host "RAPOR: $ProjectRoot\reports\quality\BYS360_EFFECTIVE_MENU_FACADE_V1_REPORT.json"
