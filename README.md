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

Desteklenen Python sürümü: **3.12** (CI'daki `actions/setup-python@v5` adımı ve `pyproject.toml` `[tool.mypy] python_version` ile aynı).

```powershell
cd C:\bys360\project
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
copy .env.example .env
```

`requirements-dev.txt`, CI ile birebir aynı sürümlerde kalite araçlarını (ruff, mypy, pytest, pytest-cov, pip-audit) kurar; production bağımlılıklarından (`requirements.txt`) ayrı tutulur. Bu adım atlanırsa aşağıdaki kalite komutları çalışmaz.

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

Aşağıdaki komutlar gerçek, çalışan komutlardır ve CI'daki (`.github/workflows/bys360-ci.yml`) karşılıklarına dayanır. `requirements-dev.txt` kurulmadan hiçbiri çalışmaz (bkz. yukarıdaki Local Kurulum).

```powershell
# Secret / repo hijyen gate'i
python scripts\quality\bys360_secret_repo_gate.py --root .

# Ruff -- CI'daki asıl gate ("Ruff full-select gate"; pyproject.toml [tool.ruff.lint]
# select = E,F,I,UP,B,SIM kapsamını uygular)
python -m ruff check app config.py wsgi.py run.py scripts tests

# mypy -- CI'daki asıl komut ("Type check service layer" adımı)
python -m mypy app tests scripts --ignore-missing-imports --no-error-summary

# pytest -- CI'daki "Run quality tests" adımının sadeleştirilmiş, coverage'lı hali
python -m pytest tests/quality -m "ci_safe" --cov=app --cov-report=term-missing --tb=short -q
```

Bu, ortak kullanım için doğrudan kopyalanıp çalıştırılabilecek bir alt kümedir; CI'nin gerçekte çalıştırdığı tam pytest komutları (entegrasyon/mimari/servis/migration testlerinin tamamı ve coverage ratchet gate'i dahil) çok daha uzundur ve sık değişebilir, bu yüzden burada birebir kopyalanmamıştır -- birebir güncel hali için `.github/workflows/bys360-ci.yml` tek doğru kaynaktır. Adım adım, açıklamalı kurulum ve kalite kontrol akışı (venv, `.env`, seed data, tam kalite koşumu) için `CONTRIBUTING.md` içindeki "Yeni geliştirici başlangıç akışı" bölümüne bakın.

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
