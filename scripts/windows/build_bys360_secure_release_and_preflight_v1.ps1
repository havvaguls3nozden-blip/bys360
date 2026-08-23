<#
DEPRECATED (BYS360 deterministic-package-builder hardening, 2026-08-23).

This wrapper called scripts\security\build_bys360_secure_release_v1_5.py and
then scripts\security\bys360_release_zip_preflight_v1.py. The preflight
script no longer exists at that path (moved to
scripts\archive\pre_handover_20260708\security\ by commit 4f41319), so this
wrapper has been broken end-to-end since that commit -- it always threw
"Preflight script bulunamadı" before producing a usable, verified release.

Use the canonical production release builder instead:

  python scripts\release\build_bys360_safe_release.py --root . --output <path\to\release.zip>
  python scripts\release\build_bys360_safe_release.py --verify <path\to\release.zip>

The --verify step performs the equivalent (and stronger: SHA256-checked,
forbidden-path-checked, required-content-checked) role the old preflight
script was meant to provide.
#>
param(
    [string]$ProjectRoot = "C:\bys360\project"
)

throw "DEPRECATED: scripts\windows\build_bys360_secure_release_and_preflight_v1.ps1 kaldirildi/artik desteklenmiyor. Bunun yerine: python scripts\release\build_bys360_safe_release.py --root . --output <zip-yolu>  ardindan  python scripts\release\build_bys360_safe_release.py --verify <zip-yolu>"
