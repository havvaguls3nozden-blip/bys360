# BYS360 Local SQLite Persistent DB HOTFIX V2

Bu hotfix local geliştirme ortamında `sqlite:///:memory:` nedeniyle her Flask başlatmada sıfırlanan veritabanını kalıcı SQLite dosyasına yönlendirmek için hazırlanmıştır.

Varsayılan DB dosyası:

`instance/bys360_local_dev.sqlite3`

Canlı/PostgreSQL veritabanına dokunmaz.

Başlatma için:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\windows\start_bys360_local_sqlite_persistent.ps1 -ProjectRoot "C:\bys360\project" -Port 8000
```
