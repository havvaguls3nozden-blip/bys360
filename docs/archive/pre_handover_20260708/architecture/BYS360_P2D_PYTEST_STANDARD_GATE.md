# BYS360 P2D Pytest Standard Gate

Bu paket P2A/P2B/P2C ile kurulan mobil API mimari ve davranış smoke kapılarını gerçek pytest standardına bağlar.

## Yapılanlar

- `requirements-dev.txt` içinde `pytest>=8,<9` standardı tanımlanır.
- `pytest.ini` yoksa güvenli temel konfigürasyon oluşturulur.
- `tests/architecture/test_pytest_standard_p2d.py` eklenir.
- P2A/P2B/P2C mimari testleri gerçek `python -m pytest` ile çalıştırılır.
- App factory smoke ve secret gate opsiyonel olarak aynı raporda doğrulanır.

## Not

Local ortamda pytest yoksa komut `-InstallPytest` parametresiyle çalıştırılmalıdır. CI ortamında `pip install -r requirements-dev.txt` sonrası `python -m pytest tests/architecture -q` çalıştırılabilir.
