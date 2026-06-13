$ErrorActionPreference = "Stop"
cd C:\bys360\project

.\.venv\Scripts\python.exe -m pip install --force-reinstall "pytest==8.4.2"
.\.venv\Scripts\python.exe -m pytest -m "not live and not realdb and not slow" -q -ra