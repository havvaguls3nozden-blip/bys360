# BYS360 Geliştirici Katkı Rehberi

## Temel kurallar

- Gerçek `.env`, parola, token, anahtar veya bağlantı dizesi repoya eklenmez.
- Geliştirme yedekleri `.bak`, `.orig`, `.old` olarak kaynak kod ağacında tutulmaz; git branch/stash kullanılır.
- Route dosyaları iş mantığı taşımaz; servis katmanı çağırır.
- Kullanıcı ekranında teknik faz, debug, endpoint, raw exception veya geliştirici notu gösterilmez.
- Her overlay tek amaçlı, geri alınabilir ve raporlu olmalıdır.

## Kalite kontrol

```powershell
python -m compileall -q app config.py wsgi.py run.py scripts
python scripts\quality\bys360_secret_repo_gate.py --root .
python -m ruff check app config.py wsgi.py run.py scripts --select E9,F63,F7,F82
python -m pytest tests/quality -m "ci_safe" --tb=short -q
```

## Devir teslim paketi

Temiz kaynak paketinde şunlar bulunmamalıdır:

- `.env`, `.env.*` gerçek dosyaları
- `.venv`, `venv`, `env`
- `backups`, `archive`, `payload`, `overlay_payload`
- `.bak`, `.backup`, `.orig`, `.tmp`
- veritabanı dump, log, upload veya runtime dosyaları
