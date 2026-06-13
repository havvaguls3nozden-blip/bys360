# BYS360 Teknik Borç Temizliği Planı

## P0 — Kaynak depo hijyeni

- Proje kökünden `.venv`, `backups`, `releases`, `reports`, `logs`, `_bys360_overlay_payload`, `.quarantine` ayrılır.
- `.env` ve yerel DB dosyaları kaynak paketinin dışına alınır.
- `.gitignore` runtime/artifact dosyalarını dışlayacak şekilde güçlendirilir.

## P1 — Kod kalite borçları

- `except Exception` kayıtları modül modül ele alınır; sessiz hata yutma yerine özgül hata ve logger kullanılır.
- `print()` kullanımları CLI scriptleri dışında logger veya rapor çıktısına taşınır.
- Kullanıcı ekranlarındaki `phase`, `sync`, `workflow`, `debug`, `endpoint`, `traceback`, `exception`, `raw error` gibi teknik dil temizlenir.

## P2 — Sürdürülebilirlik borçları

- Büyük servis dosyaları parçalanır.
- Eski hotfix ve faz dosyaları arşivlenir.
- Dashboard, performans, personel, iletişim, AI ve mobil tarafı ortak gate raporuna bağlanır.

## Başarı kriteri

- Proje kökü sadece çalışan kaynak kod ve gerekli konfigürasyon örnekleriyle kalır.
- Yeni teslim paketi `.env`, venv, yerel DB, cache, log ve backup içermez.
- Compile/gate temiz döner.
- Teknik borç raporu her sürümde tekrar üretilebilir hale gelir.
