BYS360_LIVE_FULL_OVERLAY_V2_13_0

Amaç:
- Canlı BYS360 üzerinde geri bildirim/kampanya ekranlarının kurumsal görünümünü güçlendirmek.
- Portal ve iPhone/dar ekran responsive davranışını iyileştirmek.
- Ayarlar, rol matrisi ve personel bazlı rol matrisi ekranlarında açıklayıcı kurumsal rehber paneli eklemek.
- Kullanıcı ekranına sızan teknik ifadeleri azaltmak.
- Instagram/harici akış kartlarını portal görünümünden güvenli şekilde gizlemek.

Bu overlay mevcut iş kurallarını silmez; öncelikle statik CSS + JS katmanı ve güvenli şablon desteği ekler.
Mevcut dosyalar değiştirilmeden önce _backups klasörüne yedeklenir.

Uygulama:
1) Zip dosyasını C:\bys360\project içine açın.
2) PowerShell'i proje kökünde çalıştırın.
3) Aşağıdaki komutu uygulayın:

powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_live_full_overlay_v2_13_0.ps1 -ProjectRoot "C:\bys360\project"

Kontrol:
powershell -ExecutionPolicy Bypass -File .\scripts\windows\check_bys360_live_full_overlay_v2_13_0.ps1 -ProjectRoot "C:\bys360\project"

Geri alma:
powershell -ExecutionPolicy Bypass -File .\scripts\windows\rollback_bys360_live_full_overlay_v2_13_0.ps1 -ProjectRoot "C:\bys360\project"
