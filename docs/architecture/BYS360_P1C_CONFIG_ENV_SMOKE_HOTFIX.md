# BYS360 P1C Config Env Smoke HOTFIX

Bu paket P1C domain split sonrasında app factory smoke sırasında görülen `SECRET_KEY` yokken `.strip()` hatasını düzeltir.

Düzeltme gerçek gizli değer eklemez. Sadece environment variable yoksa import/app factory aşamasında `None.strip()` hatası oluşmasını engeller.

Canlı ve local çalışma için gerçek `SECRET_KEY`, `DATABASE_URL` ve ilgili değerler kaynak koda yazılmadan dış ortamdan sağlanmalıdır.
