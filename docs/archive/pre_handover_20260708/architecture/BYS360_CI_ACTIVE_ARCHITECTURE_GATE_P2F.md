# BYS360 P2F — CI Active Architecture Gate

Bu paket P2A–P2E ile kurulan mobil mimari kalite kapılarını tek CI komutu altında toplar.

## Kapsam

- Aktif `tests/architecture` kapsamı
- Mobil route facade sınırı
- Mobil endpoint sözleşme sayısı
- App factory smoke
- Secret gate
- Gerçek pytest çalıştırması

## Varsayılan komut

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_claude_score_uplift_p2f_ci_active_architecture_gate.ps1 -ProjectRoot "C:\bys360\project" -Mode all -CompileAll -RunAppFactorySmoke -RunSecretGate -RunPytest
```

## CI için sade komutlar

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest tests/architecture -q
python scripts/quality/bys360_secret_repo_gate.py --root .
python -c "from app import create_app; app=create_app(); print('APP_FACTORY_OK')"
```

Eski/arşiv mimari sözleşmeleri silinmez. Gerektiğinde şu ortam değişkeniyle ayrıca koşturulabilir:

```powershell
$env:BYS360_RUN_LEGACY_ARCHITECTURE_TESTS = "1"
python -m pytest tests/architecture -q
Remove-Item Env:\BYS360_RUN_LEGACY_ARCHITECTURE_TESTS
```
