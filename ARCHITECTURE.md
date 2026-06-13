# BYS360 ARCHITECTURE


<!-- PHASE2C6_ARCHITECTURE_20260613 -->

## Mimari Karar Kaydı - 2026-06-13 - Faz 2C Wildcard Import Temizliği

### Bağlam

Faz 2C boyunca wildcard import borcu kontrollü ve test kapılı şekilde azaltılmıştır. Mobil API alanında pp.api.mobile.shared kaynaklı wildcard importlar domain dosyalarında açık importa dönüştürülmüş, pp/api/mobile/routes.py ise facade/aggregator rolü nedeniyle bilinçli istisna olarak bırakılmıştır.

### Alınan Kararlar

- pp/api/mobile/routes.py içindeki rom app.api.mobile.shared import * satırı bilinçli facade istisnasıdır.
- Bu dosya doğrudan açık importa çevrildiğinde mobil route map ve auth guard testleri kırıldığı için mevcut hali korunmuştur.
- Faz 2C5 ile düşük riskli 4 ek wildcard import kalıcı olarak temizlenmiştir.
- pp/institutional/hr_scope_helpers.py otomatik açık import için güvenli değildir; manuel refactor gerektirir.
- Kalan wildcard importlar artık “toplu otomatik temizlik” yerine “dosya bazlı refactor” olarak ele alınacaktır.

### Yeni Geliştirme Disiplini

Bundan sonra:

- Yeni kalite scripti üretmek yerine mevcut kalite modülleri güncellenecek.
- Yeni README/manifest üretmek yerine ARCHITECTURE.md ve STATUS.md güncellenecek.
- V_SAFE_NN, HOTFIX_V..., OVERLAY... adlandırma kültürü bırakılacak.
- Değişiklikler normal git commit / PR analizi mantığıyla takip edilecek.
- Deploy ve migration yardımcıları korunacak; eski kalite/onarım scriptleri Faz 2Y kapsamında arşive alınacaktır.

### Faz 2Y İçin Bekleyen Temizlik

- scripts/quality envanteri çıkarılacak.
- Aktif kullanılan kalite/deploy/migration yardımcıları ayrılacak.
- Kullanılmayan scriptler scripts/archive/quality/ altına taşınacak.
- Dağınık rapor ve dokümanlar docs/archive/ ve eports/archive/ altında toplanacak.
- Güncel mimari bilgi ARCHITECTURE.md, güncel durum bilgisi STATUS.md içinde tutulacak.

