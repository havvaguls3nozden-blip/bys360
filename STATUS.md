# STATUS.md Güncelleme Taslağı

## 2026-07-08 — Devredilebilirlik Temizliği ve Kaynak Paket Standardı

### Özet

BYS360 kaynak ağacında devredilebilirliği düşüren tek kullanımlık script, iç içe proje kopyası, backup/log/instance kalıntısı ve eski overlay raporlarının ayrıştırılması başlatıldı.

### Kararlar

- Aktif `scripts/` alanında yalnızca CI/test/doküman tarafından kullanılan veya elle onaylanmış scriptler kalacak.
- Referanssız `ARCHIVE_CANDIDATE` scriptleri Task Scheduler kontrolünden sonra `scripts/archive/pre_handover_YYYYMMDD/` altına taşınacak.
- `project/project/`, `backups/`, `logs/`, `instance/*.sqlite*`, `.bak` ve gerçek `.env` dosyaları kaynak paketten çıkarılacak.
- README proje tanıtımı ve hızlı kurulum dokümanı olarak yeniden yazılacak.
- STATUS güncel durumun tek kaynağı olarak sürdürülecek; her temizlik/geliştirme turunda yeni rapor yığını yerine bu dosya güncellenecek.

### Sayısal Durum

- Script envanteri: 365 kayıt
- KEEP: 49
- REVIEW: 27
- ARCHIVE_CANDIDATE: 90
- ALREADY_ARCHIVED: 199

### Sonraki İşler

1. Task Scheduler raporu ile `ARCHIVE_CANDIDATE` listesini karşılaştır.
2. Güvenli olan adayları `git mv` ile arşivle.
3. Repo gürültüsünü temizle.
4. README ve STATUS değişikliklerini normal commit olarak işle.
5. CI ve temel smoke testleri çalıştır.
