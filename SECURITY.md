# BYS360 SECURITY.md

BYS360 kurumsal veri, personel, performans, iletişim, anket, destek, log ve karar destek süreçlerini içerdiği için güvenlik yaklaşımı kod, veri, yetki, dokümantasyon ve release paketini birlikte ele alır.

## 1. Gizli bilgi kuralı

Aşağıdaki dosya ve değerler git’e veya release zipine konulmaz:

- `.env`, `.env.local`, `.env.production`
- canlı `DATABASE_URL`
- gerçek parola, token, API anahtarı, özel anahtar
- `instance/*.sqlite3`, `*.db`, `*.dump`
- canlı loglar
- Android/iOS imzalama anahtarları
- kişisel veri içeren test çıktıları

## 2. `.env` yönetimi

`.env` yalnızca ilgili ortamda bulunur. Paylaşılacak örnek dosyalar gerçek değer içermez.

```powershell
git ls-files .env .env.local .env.production
```

Bu komut çıktı verirse `.env` izleniyor demektir ve düzeltilmelidir.

```powershell
git rm --cached .env
Add-Content .gitignore "`n.env`n.env.local`n.env.production"
git add .gitignore
git commit -m "chore: keep local env files out of git"
```

## 3. Git geçmişi kontrolü

```powershell
git rev-list --objects --all | Select-String -Pattern "(^|/)\.env($|\.)|\.sqlite|\.db|\.dump"
```

Geçmişte gerçek `.env` veya canlı sır varsa önce bütün sırlar döndürülür, sonra git geçmişi temizlenir. Git geçmişi temizliği ekip koordinasyonu gerektirir.

Önerilen yöntem:

```powershell
python -m pip install git-filter-repo
git filter-repo --path .env --invert-paths
git filter-repo --path .env.production --invert-paths
```

Bu işlem uzak repo ve ekip kopyalarını etkiler. Önce tam yedek alınmadan çalıştırılmaz.

## 4. Release paket kuralı

Proje klasörü doğrudan zip yapılmaz. Release yalnızca tek yetkili (canonical) builder ile
üretilir: `scripts\release\build_bys360_safe_release.py`. Kaynak dosya listesi yalnızca
Git-tracked dosyalardan gelir (fiziksel dizin taramasına geri düşüş yoktur), ve build,
HEAD ile çalışma ağacı arasında herhangi bir uyuşmazlık/kirlilik varsa başarısız olur.

```powershell
python scripts\release\build_bys360_safe_release.py --root . --output "C:\bys360\dist\bys360_release.zip"
python scripts\release\build_bys360_safe_release.py --verify "C:\bys360\dist\bys360_release.zip"
```

`--verify` FAIL verirse zip paylaşılmaz. (`scripts\security\build_bys360_secure_release_v1_5.py`
ve ona bağlı eski preflight akışı artık DEPRECATED'dır -- companion preflight betiği
arşivlenmiştir ve o akış zaten çalışmamaktadır.)

## 5. Yetki ve görünürlük

- Menü görünürlüğü tek başına güvenlik değildir; backend route yetkisi de kontrol edilir.
- Personel yalnızca kendi verisini ve yetki verilen özetleri görür.
- Amir yalnızca değerlendirme görevi ve yetki kapsamındaki personeli görür.
- Başkan/Admin geniş görünürlük alır; bu görünürlük audit log ile desteklenir.
- Yetkisiz erişimde beyaz sayfa yerine kurumsal erişim engeli gösterilir.

## 6. Performans verisi güvenliği

- Yayın/onay tamamlanmadan personel kendi sonucunu göremez.
- 70 altı sonuçlar onay zinciri tamamlanmadan kesinleşmez.
- Amir görüşleri, puanlar ve süreç geçmişi rol bazlı korunur.
- Sahte bekleme, sahte onay ve gerçek olmayan görev üretimi güvenlik/iş kuralı hatası sayılır.

## 7. AI karar destek güvenliği

- AI karar vermez; yalnızca özet, öneri veya dikkat notu üretir.
- Hassas veri minimizasyonu uygulanır.
- AI çıktısı idari karar yerine geçmez.
- AI istek/yanıt kayıtları ve öneri kullanımı denetlenebilir olmalıdır.

## 8. Güvenlik olayı halinde

1. Etkilenen release veya erişim kapatılır.
2. İlgili token/parola döndürülür.
3. Loglar ve audit kayıtları korunur.
4. Olay zamanı, etki alanı, alınan aksiyon ve kalıcı önlem raporlanır.
5. Gerekirse KVKK/bilgi güvenliği sorumlularına bildirim yapılır.
