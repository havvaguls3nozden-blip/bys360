# BYS360_CSRF_FORM_TOKEN_AND_REFERRER_HOTFIX_V2_15_15

Amaç:
- Kurumsal Bilgilendirme Merkezi POST formlarına Flask-WTF CSRF token alanını ekler.
- Mail Test Merkezi formundaki "The CSRF token is missing" hatasını kapatır.
- CSRF süresi dolarsa kullanıcıyı ana sayfaya savurmak yerine geldiği kurumsal ekrana geri döndürür.
- `auth.login/login` BuildError zincirini önlemek için `main.login` önceliğini korur.

Local uygulama:
```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_CSRF_FORM_TOKEN_AND_REFERRER_HOTFIX_V2_15_15_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_csrf_form_token_and_referrer_hotfix_v2_15_15.ps1 -ProjectRoot "C:\bys360\project" -Mode all
```

Kontrol:
```powershell
C:\bys360\project\.venv\Scripts\python.exe scripts\quality\check_bys360_csrf_form_token_and_referrer_hotfix_v2_15_15.py
```
