# BYS360 Risk ve Süreklilik Planı

## Kritik riskler

| Risk | Etki | Kontrol |
|---|---|---|
| Tek geliştirici bilgisi | Devir zorluğu | Handover dokümanları, testler, modül envanteri |
| Firma/kişi bağımlılığı | Süreklilik riski | Temiz kaynak, kurumsal repo, yedek, dokümantasyon |
| `.env` sızıntısı | Güvenlik ihlali | `.gitignore`, release preflight, secret rotation |
| Eksik test | Canlı hata riski | Integration test ve smoke gate |
| Yetki hatası | Kişisel veri görünürlüğü | Backend guard + menü görünürlüğü + audit log |
| Migration hatası | Canlı kesinti | Backup, staging deneme, rollback planı |
| Teknik borç | Bakım zorluğu | Fazlı refactor, testten sonra bölme |

## Süreklilik ilkesi

BYS360 kişiye veya tek firmaya bağlı kalmayacak şekilde; kaynak kod, dokümantasyon, test, release ve yedekleme disipliniyle devredilebilir olmalıdır.

## 100/100 yaklaşımı

1. Önce güvenli release disiplini.
2. Sonra devir dokümantasyonu.
3. Sonra kritik integration testleri.
4. Sonra modül bazlı refactor.
5. En son büyük god-object parçalama.

## Kabul kriterleri

- Yeni geliştirici temiz makinede sistemi kurabilir.
- Canlıya alma ve rollback adımlarını okuyarak uygulayabilir.
- Kritik güvenlik risklerini bilir.
- Modüllerin nerede başladığını ve hangi veri omurgasını kullandığını bilir.
- Test/gate çalıştırmadan canlıya çıkmaz.
