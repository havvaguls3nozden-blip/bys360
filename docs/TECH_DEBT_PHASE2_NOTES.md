# BYS360 Teknik Borç Faz 2 Notları

Faz 2'nin temel prensibi: önce ölç, sonra küçük ve geri alınabilir dalgalarla temizle.

## Öncelik mantığı

- P0: secret sinyali, canlı/yerel adres riski, güvenlik veya veri sızıntısı ihtimali
- P1: kullanıcıya görünen teknik dil, büyük route/god-object dosyaları, ciddi mimari kalabalık
- P2: print kullanımı, broad except azaltımı, script/rapor arşiv düzeni

## Bu overlay ne yapar?

- Sadece audit yapar.
- Rapor, JSON ve CSV üretir.
- App kodunu değiştirmez.
- Canlıya dokunmaz.

## Faz 2 sonrası beklenen karar

Rapor incelendikten sonra ilk uygulama paketi şu üçünden biri olmalıdır:

1. reports/quality arşiv temizliği
2. UI teknik dil temizliği
3. scripts aktif/legacy ayrımı
