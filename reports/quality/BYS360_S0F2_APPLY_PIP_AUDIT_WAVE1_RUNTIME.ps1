$ErrorActionPreference = "Stop"
cd C:\bys360\project

Write-Host "S0F2 Wave1 runtime dependency update başlıyor..."
Write-Host "Önce mevcut paket listesi yedekleniyor..."
.\.venv\Scripts\python.exe -m pip freeze | Set-Content -Path ".\reports\quality\BYS360_S0F2_PRE_UPDATE_PIP_FREEZE.txt" -Encoding UTF8

Write-Host "Wave1 runtime paketleri güncelleniyor..."
.\.venv\Scripts\python.exe -m pip install --upgrade "cryptography>=46.0.7" "flask>=3.1.3" "pillow>=12.2.0" "python-dotenv>=1.2.2" "waitress>=3.0.1"

Write-Host "Kurulum sonrası freeze alınıyor..."
.\.venv\Scripts\python.exe -m pip freeze | Set-Content -Path ".\reports\quality\BYS360_S0F2_POST_UPDATE_PIP_FREEZE.txt" -Encoding UTF8

Write-Host "S0F2 sonrası compile/test/audit kanıtı için bir sonraki doğrulama scripti çalıştırılmalı."