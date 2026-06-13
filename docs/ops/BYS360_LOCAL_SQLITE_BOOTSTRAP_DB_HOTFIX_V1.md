# BYS360 Local SQLite DB Bootstrap HOTFIX V1

Bu hotfix, yerel geliştirme ortamında Flask uygulaması boş SQLite veritabanıyla açıldığı için login sırasında oluşan `no such table: users` ve `no such table: audit_logs` hatasını gidermek için hazırlanmıştır.

## Güvenlik kapsamı

- Varsayılan olarak yalnızca SQLite üzerinde çalışır.
- PostgreSQL/canlı veritabanına dokunmaz.
- İlk yerel admin oluşturmak için parola komuttan verilmelidir.
- Raporlarda veritabanı bağlantı bilgisi maskelenir.

## Önerilen kullanım

```powershell
cd C:ys360\project
powershell -ExecutionPolicy Bypass -File .\scripts\windowsepair_bys360_local_sqlite_bootstrap_db_hotfix_v1.ps1 -ProjectRoot "C:ys360\project" -Mode all -RunCompile -RunAppFactorySmoke -CreateLocalAdmin -LocalAdminEmail "bys360@ktb.gov.tr" -LocalAdminPassword "<GUCLU_GECICI_YEREL_SIFRE>"
```

Sonra Flask uygulamasını yeniden başlatın.
