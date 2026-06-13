param(
    [string]$ProjectRoot = "C:\bys360\project"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location $ProjectRoot
& .\.venv\Scripts\python.exe .\scripts\quality\check_claude_phase7_final_gate.py
exit $LASTEXITCODE
