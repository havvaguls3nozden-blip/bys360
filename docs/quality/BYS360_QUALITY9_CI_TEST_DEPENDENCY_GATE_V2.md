# BYS360 Quality 9 CI Test Dependency Gate V2

Bu hotfix, Quality 9 paketinde yerel test calistirma sirasinda gorulen iki sorunu kapatir:

1. PowerShell scripti artik proje icindeki `.venv\Scripts\python.exe` dosyasini otomatik kullanir.
2. `-RunTests` kullanildiginda `pytest`, `sqlalchemy` ve `flask_sqlalchemy` bagimliliklari kontrol edilir; eksikse requirements uzerinden kurulur.
3. Native komutlarin exit code degeri artik denetlenir. Pytest hata verirse script "tamamlandi" diyerek basarili kapanmaz.
4. `pytest.ini` marker kayitlari eklendi; `source_smoke` ve `uat` uyarilari temizlendi.
5. CI tarafinda test bagimlilikleri dogrulama adimi ve `pip-audit` kurulumu eklendi.

## Yerel calistirma

```powershell
cd C:\bys360\project

Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_QUALITY9_CI_TEST_DEPENDENCY_GATE_V2_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force

powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_quality9_ci_tests_threshold_auth_session.ps1 -ProjectRoot "C:\bys360\project" -Mode all -RunTests
```

Bagimlilikleri zorla yeniden kurmak gerekirse:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_quality9_ci_tests_threshold_auth_session.ps1 -ProjectRoot "C:\bys360\project" -Mode all -RunTests -InstallDeps
```
