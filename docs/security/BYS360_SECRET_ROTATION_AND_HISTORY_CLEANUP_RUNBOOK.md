# BYS360 Secret Rotation ve Git History Temizliği Runbook

Bu doküman, production `.env` veya benzeri gerçek gizli değerler repoya girmişse uygulanacak güvenli süreci tanımlar.
Gerçek parola, token, anahtar veya bağlantı dizesi bu dokümana yazılmamalıdır.

## 1. Hemen rotate edilecek değerler

- Veritabanı kullanıcı parolası
- `SECRET_KEY`
- `TCKN_ENCRYPTION_KEY`
- Harici API tokenları
- Sentry DSN / izleme anahtarları
- Mail SMTP parolaları veya uygulama şifreleri
- Redis / broker parolaları varsa ilgili değerler

## 2. Yeni çalışma kuralı

- Gerçek `.env` sadece sunucuda veya geliştiricinin kendi makinesinde durur.
- Repo içinde yalnızca `.env.example`, `.env.production.example`, `.env.docker.example` gibi örnek dosyalar bulunur.
- Örnek dosyalarda yalnızca `CHANGE_ME`, `<SECRET>`, `DB_CONNECTION_STRING_SUPPLIED_BY_ENVIRONMENT` gibi placeholder değerler bulunur.

## 3. Git geçmişinden temizleme

Temiz bir dalda ve yedek alındıktan sonra:

```powershell
cd C:\bys360\project
python -m pip install git-filter-repo

git status

git filter-repo --path .env --path-glob ".env.*" --invert-paths --force

git push --force --all
git push --force --tags
```

> Not: Bu işlem ekipteki herkesin repoyu yeniden klonlamasını gerektirebilir. Kurumsal repo üzerinde uygulanmadan önce yetkili birimle teyit edilmelidir.

## 4. Tracked `.env` dosyası varsa hızlı düzeltme

```powershell
git rm --cached .env -f
git rm --cached .env.docker.local -f
git add .gitignore .dockerignore .env.example .env.production.example .env.docker.example
git commit -m "security: remove local env files from tracked source"
```

## 5. Kontrol komutları

```powershell
python scripts\quality\bys360_secret_repo_gate.py --root C:\bys360\project

git ls-files | findstr /R /C:"^\.env" /C:"\.bak" /C:"\.backup" /C:"\.orig"
```

Bu komutlar temiz geçmeden proje devredilebilir kaynak kod paketi olarak kabul edilmemelidir.
