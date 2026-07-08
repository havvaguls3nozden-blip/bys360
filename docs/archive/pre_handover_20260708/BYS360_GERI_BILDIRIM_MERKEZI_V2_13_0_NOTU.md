# BYS360 Geri Bildirim Merkezi V2.13.0

Bu overlay, BYS360 içinde kullanıcıların ekran hatası, eksik/geliştirme önerisi, kullanım kolaylığı önerisi, tebrik ve teşekkür kayıtlarını kolayca gönderebildiği kurumsal geri bildirim sayfasını ekler.

## Eklenenler

- `/feedback/gonder` yeni geri bildirim gönderim ekranı
- `/feedback/gonderildi/<id>` kayıt sonrası teşekkür ve takip ekranı
- Mevcut Destek & Talep Yönetimi tablolarını kullanan izlenebilir kayıt üretimi
- Ekran görüntüsü / belge ekleme desteği
- Sayfa bağlantısı alanı
- Son geri bildirimlerim paneli
- Geri bildirim panelindeki ana butonun yeni sayfaya yönlenmesi

## Veri yaklaşımı

Ayrı ve kopuk bir tablo oluşturulmadı. Kayıtlar mevcut `support_tickets`, `support_ticket_messages`, `support_ticket_status_history` ve ek varsa `support_ticket_attachments` omurgasına yazılır. Böylece yetkili kullanıcılar kayıtları mevcut talep takip ekranlarından görebilir, atayabilir ve durumunu güncelleyebilir.

## Kurulum

```powershell
cd C:\bys360\project
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\BYS360_GERI_BILDIRIM_MERKEZI_V2_13_0_OVERLAY.zip" -DestinationPath "C:\bys360\project" -Force
powershell -ExecutionPolicy Bypass -File .\scripts\windows\repair_bys360_feedback_center_v2_13_0.ps1 -ProjectRoot "C:\bys360\project"
```

## Kontrol

```powershell
cd C:\bys360\project
.\.venv\Scripts\python.exe .\scripts\check_bys360_feedback_center_v2_13_0.py --project-root "C:\bys360\project"
python -m compileall app config.py scripts
```
