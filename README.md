# BYS360 Bütünleşik Yönetim Sistemi

BYS360, kurum içi yönetim süreçlerini tek merkezde toplayan; personel, performans, iletişim, anket, destek, raporlama, KPI/hedef ve karar destek süreçlerini modüler şekilde yöneten kurumsal dijital yönetim platformudur.

## Ana Modüller

- Personel Yönetimi
- Performans Yönetimi
- İletişim ve Anket Yönetimi
- Destek / Yardım Merkezi
- Sistem Ayarları ve Yetkilendirme
- AI Karar Destek
- BYS360 Sanal Asistan
- Dashboard ve Raporlama
- Mobil istemci / Flutter altyapısı

## Teknik Özet

- Backend: Python / Flask
- Veritabanı: PostgreSQL; local geliştirme için SQLite kullanılabilir
- Sunum: Waitress / Windows servis veya görev zamanlayıcı yapısı
- Mobil: Flutter istemci altyapısı
- CI: Ruff, mypy, pytest, pip-audit ve özel secret/security gate kontrolleri

## Local Kurulum

```powershell
cd C:\bys360\project
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

`.env` dosyasını local ortama göre doldurun. Gerçek gizli değerler repoya eklenmez.

## Local Çalıştırma

```powershell
cd C:\bys360\project
.\.venv\Scripts\Activate.ps1
$env:FLASK_ENV = "development"
$env:APP_ENV = "development"
python run.py
```

Alternatif Waitress/local çalıştırma için proje içindeki güncel deployment dokümanına bakın.

## Test ve Kalite Kontrol

```powershell
ruff check .
python -m pytest tests/security tests/critical tests/architecture
mypy app
```

CI'da kullanılan özel kalite ve secret gate scriptleri `.github/workflows/bys360-ci.yml` içinde listelenir.

## Doküman Haritası

- `README.md`: Projeye giriş ve hızlı kurulum
- `ARCHITECTURE.md`: Mimari kararlar ve modül yapısı
- `STATUS.md`: Güncel durum ve son kararlar
- `CONTRIBUTING.md`: Geliştirme kuralları
- `SECURITY.md`: Güvenlik, secret ve paketleme kuralları
- `DEPLOYMENT.md`: Yayına alma ve servis çalıştırma notları
- `BACKUP_RUNBOOK.md`: Yedekleme ve geri dönüş prosedürü

## Kaynak Paket Kuralları

Kaynak pakete şu dosyalar girmez:

- `.git/`
- `.env`, `.env.local`, gerçek secret içeren ortam dosyaları
- `backups/`, `logs/`, local `instance/*.sqlite*`
- `.bak`, `.tmp`, cache ve derleme kalıntıları
- iç içe `project/project/` kopyaları

## Geliştirme İlkesi

Yeni geliştirmeler geçici overlay/hotfix kalıntısı üretmeden, mevcut dosyalar üzerinde normal commit akışıyla yapılır. Tek kullanımlık scriptler ana ağaçta bırakılmaz; gerekiyorsa arşiv branch'i veya dokümante edilmiş `docs/archive/` alanı kullanılır.
