# BYS360 Kurulum Rehberi

## 1. Temiz kaynakla başlama

Release zipi `C:\bys360\project` içine açılır. Proje klasöründe `.env`, `.git`, log veya SQLite dosyası varsa bu release paketi temiz değildir.

## 2. Sanal ortam

```powershell
cd C:\bys360\project
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Geliştirme testleri için:

```powershell
pip install -r requirements-dev.txt
```

## 3. Ortam değişkenleri

`.env.example` varsa örnek alınır; gerçek değerler kurum güvenli kanalıyla tanımlanır.

Zorunlu örnekler:

- `DATABASE_URL`
- `SECRET_KEY`
- `APP_ENV`
- SMTP ayarları, kullanılacaksa
- Redis/cache ayarları, kullanılacaksa

## 4. Veritabanı

```powershell
flask db upgrade
```

Migration öncesinde yedek zorunludur.

## 5. İlk kontrol

```powershell
python -m compileall app config.py scripts migrations
pytest tests/integration/test_http_core_smoke.py
```

## 6. Çalıştırma

```powershell
python run.py
```

Tarayıcı:

```text
http://127.0.0.1:8000/login
```

## 7. Sık hata kontrolleri

| Belirti | Kontrol |
|---|---|
| Login açılmıyor | `DATABASE_URL`, port, app factory hatası |
| Beyaz sayfa | template hatası, eksik tablo, yetki guard |
| Migration hatası | DB bağlantısı, alembic head, eksik kolon |
| Statik dosya bozuk | cache, static path, base template |
| Yetki görünmüyor | rol matrisi, menü görünürlüğü, backend guard |
