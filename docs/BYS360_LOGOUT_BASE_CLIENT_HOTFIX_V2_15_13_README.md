# BYS360 Logout Base Client Hotfix V2.15.13

Bu küçük hotfix, V2.15.12 paketinden sonra gate içinde eksik görünen `base.html` istemci çıkış bloğunu tamamlar.

Düzeltir:
- `app/templates/base.html` içine güvenli logout formu eklenir.
- `bys360LogoutForceClearForm` eklenir.
- `window.submitLogoutForm = postLogout` eşlemesi eklenir.
- CSRF veya JS aksamasında `/logout` fallback yönlendirmesi eklenir.
- Eski istemci logout blokları temizlenip tek blok bırakılır.

Uygulama:

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_LOGOUT_BASE_CLIENT_HOTFIX_V2_15_13_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_logout_base_client_hotfix_v2_15_13.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```

Beklenen sonuç:
- `BYS360_LOGOUT_FORCE_CLEAR_V2_15_12_GATE_OK`
- `BYS360_LOGOUT_BASE_CLIENT_HOTFIX_V2_15_13_FINAL_OK`
